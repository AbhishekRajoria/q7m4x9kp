from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.services.elexon import ElexonClient
from app.services.normalization import normalize_fuelhh_wind, normalize_windfor
from app.services.pipeline import build_hourly_comparison

router = APIRouter()
client = ElexonClient(settings.elexon_base_url)


@router.get("/health")
def health():
    return {"status": "ok", "service": "windsight-backend", "cutoff_hour_utc": settings.decision_cutoff_hour_utc}


@router.get("/overview")
async def overview(
    decision_date: str = Query(..., description="YYYY-MM-DD for decisions made on this date"),
    cutoff_hour_utc: int = Query(default=None, description="Override cutoff hour UTC (provisional)"),
):
    try:
        # Parse decision date
        dec_date = datetime.strptime(decision_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision_date format, use YYYY-MM-DD")
    
    cutoff_hour = cutoff_hour_utc if cutoff_hour_utc is not None else settings.decision_cutoff_hour_utc
    cutoff = dec_date.replace(hour=cutoff_hour, minute=0, second=0, microsecond=0)
    
    # Fetch data - need to be careful about windows; fetch around decision/delivery
    # For simplicity in this milestone, fetch publish windows covering likely forecasts
    publish_from = dec_date - timedelta(days=2)
    publish_to = dec_date + timedelta(days=2)
    
    try:
        fuelhh_raw = await client.fetch_dataset_chunked("FUELHH", publish_from, publish_to)
        windfor_raw = await client.fetch_dataset_chunked("WINDFOR", publish_from, publish_to)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    
    actuals = normalize_fuelhh_wind(fuelhh_raw)
    forecasts = normalize_windfor(windfor_raw)
    
    result = build_hourly_comparison(forecasts, actuals, cutoff)
    return {
        "decision_date": decision_date,
        "cutoff_utc": cutoff.isoformat(),
        "cutoff_hour_utc": cutoff_hour,
        "provisional_cutoff": True,
        "alignment": "hourly :00 only (no interpolation/duplication)",
        **result,
    }


@router.get("/accuracy")
async def accuracy(
    decision_date: str = Query(...),
    cutoff_hour_utc: int = Query(default=None),
):
    ov = await overview(decision_date=decision_date, cutoff_hour_utc=cutoff_hour_utc)
    return {
        "decision_date": ov["decision_date"],
        "cutoff_utc": ov["cutoff_utc"],
        "matched_count": ov["matched_count"],
        "mae": ov["metrics"]["mae"],
        "rmse": ov["metrics"]["rmse"],
        "mean_forecast_error": ov["metrics"]["mean_forecast_error"],
        "exclusions": ov["exclusions"],
        "unit": ov["metrics"]["unit"],
        "error_sign_convention": ov["metrics"]["error_sign_convention"],
    }


@router.get("/forecast-history")
async def forecast_history(
    start_time: str = Query(..., description="Delivery startTime ISO format"),
    publish_from: str = Query(default=None),
    publish_to: str = Query(default=None),
):
    try:
        st = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid start_time")
    
    pf = datetime.fromisoformat(publish_from.replace('Z', '+00:00')) if publish_from else st - timedelta(days=3)
    pt = datetime.fromisoformat(publish_to.replace('Z', '+00:00')) if publish_to else st + timedelta(days=1)
    
    try:
        windfor_raw = await client.fetch_dataset_chunked("WINDFOR", pf, pt)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    
    forecasts = normalize_windfor(windfor_raw)
    history = [
        {"delivery_start": f.delivery_start.isoformat(), "publish_time": f.publish_time.isoformat(), "generation": f.generation}
        for f in forecasts
        if f.delivery_start == st
    ]
    history.sort(key=lambda x: x["publish_time"])
    return {"start_time": start_time, "revisions": history}
