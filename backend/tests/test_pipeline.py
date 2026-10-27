from datetime import datetime, timezone

from app.schemas import NormalizedActual, NormalizedForecast
from app.services.pipeline import build_hourly_comparison


def test_hourly_alignment_excludes_half_hour():
    delivery_h = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    delivery_hh = datetime(2026, 1, 2, 12, 30, tzinfo=timezone.utc)
    cutoff = datetime(2026, 1, 2, 11, 0, tzinfo=timezone.utc)
    
    forecasts = [
        NormalizedForecast(delivery_start=delivery_h, publish_time=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc), generation=100),
    ]
    actuals = [
        NormalizedActual(delivery_start=delivery_h, publish_time=datetime(2026, 1, 2, 12, 30, tzinfo=timezone.utc), generation=90),
        NormalizedActual(delivery_start=delivery_hh, publish_time=datetime(2026, 1, 2, 13, 0, tzinfo=timezone.utc), generation=95),
    ]
    result = build_hourly_comparison(forecasts, actuals, cutoff)
    assert result["matched_count"] == 1
    assert result["exclusions"]["half_hour_actuals_excluded"] == 1


def test_missing_actual_excluded():
    delivery_h = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    cutoff = datetime(2026, 1, 2, 11, 0, tzinfo=timezone.utc)
    
    forecasts = [
        NormalizedForecast(delivery_start=delivery_h, publish_time=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc), generation=100),
    ]
    actuals = []
    result = build_hourly_comparison(forecasts, actuals, cutoff)
    assert result["matched_count"] == 0
    assert result["exclusions"]["no_actual"] == 1


def test_duplicate_resolution_deterministic():
    delivery_h = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    cutoff = datetime(2026, 1, 2, 11, 0, tzinfo=timezone.utc)
    
    forecasts = [
        NormalizedForecast(delivery_start=delivery_h, publish_time=datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc), generation=100),
    ]
    actuals = [
        NormalizedActual(delivery_start=delivery_h, publish_time=datetime(2026, 1, 2, 12, 30, tzinfo=timezone.utc), generation=90),
        NormalizedActual(delivery_start=delivery_h, publish_time=datetime(2026, 1, 2, 13, 0, tzinfo=timezone.utc), generation=92),  # later publish
    ]
    result = build_hourly_comparison(forecasts, actuals, cutoff)
    assert result["matched_count"] == 1
    assert result["intervals"][0]["actual_generation"] == 92  # latest publish used
