from datetime import datetime, timezone

from app.schemas import NormalizedForecast
from app.services.forecasting import select_decision_time_forecast


def test_select_latest_forecast_before_cutoff():
    delivery = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    cutoff = datetime(2026, 1, 2, 11, 0, tzinfo=timezone.utc)
    forecasts = [
        NormalizedForecast(delivery_start=delivery, publish_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc), generation=100),
        NormalizedForecast(delivery_start=delivery, publish_time=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc), generation=120),
        NormalizedForecast(delivery_start=delivery, publish_time=datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc), generation=130),  # after cutoff
    ]
    selected = select_decision_time_forecast(forecasts, delivery, cutoff)
    assert selected is not None
    assert selected.generation == 120  # latest <= cutoff


def test_exclude_forecast_after_cutoff():
    delivery = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    cutoff = datetime(2026, 1, 2, 11, 0, tzinfo=timezone.utc)
    forecasts = [
        NormalizedForecast(delivery_start=delivery, publish_time=datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc), generation=130),
    ]
    selected = select_decision_time_forecast(forecasts, delivery, cutoff)
    assert selected is None
