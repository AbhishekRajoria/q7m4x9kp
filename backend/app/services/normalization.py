from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas import NormalizedActual, NormalizedForecast


def parse_iso_z(dt_str: str) -> datetime:
    # Handle Z suffix
    if dt_str.endswith('Z'):
        dt_str = dt_str[:-1] + '+00:00'
    dt = datetime.fromisoformat(dt_str.replace('+00:00', ''))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def normalize_fuelhh_wind(records: List[Dict[str, Any]]) -> List[NormalizedActual]:
    out: List[NormalizedActual] = []
    for r in records:
        if r.get('fuelType') != 'WIND':
            continue
        try:
            out.append(
                NormalizedActual(
                    delivery_start=parse_iso_z(r['startTime']),
                    publish_time=parse_iso_z(r['publishTime']) if r.get('publishTime') else None,
                    generation=float(r['generation']) if r.get('generation') is not None else None,
                    fuel_type='WIND',
                    source='FUELHH',
                    settlement_date=r.get('settlementDate'),
                    settlement_period=r.get('settlementPeriod'),
                )
            )
        except (KeyError, ValueError, TypeError):
            continue
    return out


def normalize_windfor(records: List[Dict[str, Any]]) -> List[NormalizedForecast]:
    out: List[NormalizedForecast] = []
    for r in records:
        try:
            out.append(
                NormalizedForecast(
                    delivery_start=parse_iso_z(r['startTime']),
                    publish_time=parse_iso_z(r['publishTime']) if r.get('publishTime') else datetime.now(timezone.utc),
                    generation=float(r['generation']) if r.get('generation') is not None else None,
                    source='WINDFOR',
                    dataset_id=r.get('dataset'),
                )
            )
        except (KeyError, ValueError, TypeError):
            continue
    return out
