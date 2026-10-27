from datetime import datetime, timezone
from typing import Dict, List, Tuple

from app.schemas import NormalizedActual, NormalizedForecast
from app.services.forecasting import select_decision_time_forecast
from app.services.metrics import mae, rmse, mean_bias, compute_errors


def build_hourly_comparison(
    forecasts: List[NormalizedForecast],
    actuals: List[NormalizedActual],
    decision_cutoff_utc: datetime,
) -> Dict:
    """Hourly alignment: only :00 delivery timestamps present in both."""
    # Filter to hourly (:00)
    forecasts_h = [f for f in forecasts if f.delivery_start.minute == 0]
    actuals_h = [a for a in actuals if a.delivery_start.minute == 0]
    
    # Index actuals by delivery_start (latest publish if duplicates)
    actual_by_start: Dict[datetime, NormalizedActual] = {}
    for a in actuals_h:
        if a.delivery_start not in actual_by_start:
            actual_by_start[a.delivery_start] = a
        else:
            # if we have publish times, prefer latest
            existing = actual_by_start[a.delivery_start]
            if a.publish_time and existing.publish_time and a.publish_time > existing.publish_time:
                actual_by_start[a.delivery_start] = a
            elif a.publish_time and not existing.publish_time:
                actual_by_start[a.delivery_start] = a
    
    matched = []
    exclusions = {
        "no_forecast_eligible": 0,
        "no_actual": 0,
        "half_hour_actuals_excluded": 0,
    }
    # count half-hour actuals excluded
    exclusions["half_hour_actuals_excluded"] = sum(1 for a in actuals if a.delivery_start.minute != 0)
    
    forecast_values = []
    actual_values = []
    
    # Check each forecast hourly interval
    # Group forecasts by delivery_start
    from collections import defaultdict
    fcasts_by_start: Dict[datetime, List[NormalizedForecast]] = defaultdict(list)
    for f in forecasts_h:
        fcasts_by_start[f.delivery_start].append(f)
    
    for start, fcast_list in fcasts_by_start.items():
        selected = select_decision_time_forecast(fcast_list, start, decision_cutoff_utc)
        if not selected:
            exclusions["no_forecast_eligible"] += 1
            continue
        if start not in actual_by_start:
            exclusions["no_actual"] += 1
            continue
        actual = actual_by_start[start]
        if selected.generation is None or actual.generation is None:
            exclusions["no_actual"] += 1
            continue
        forecast_values.append(selected.generation)
        actual_values.append(actual.generation)
        matched.append({
            "delivery_start": start.isoformat(),
            "forecast_generation": selected.generation,
            "actual_generation": actual.generation,
            "forecast_publish_time": selected.publish_time.isoformat(),
            "actual_publish_time": actual.publish_time.isoformat() if actual.publish_time else None,
            "error": selected.generation - actual.generation,
        })
    
    errors = compute_errors(forecast_values, actual_values)
    
    return {
        "matched_count": len(matched),
        "forecast_intervals_available": len(fcasts_by_start),
        "actual_intervals_available_hourly": len(actual_by_start),
        "exclusions": exclusions,
        "metrics": {
            "mae": mae(errors),
            "rmse": rmse(errors),
            "mean_forecast_error": mean_bias(errors),
            "unit": "MW (reported)",
            "error_sign_convention": "forecast - actual (positive = overforecast)",
        },
        "intervals": matched,
    }
