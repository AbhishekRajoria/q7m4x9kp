from datetime import datetime, timezone
from typing import List, Optional

from app.schemas import NormalizedForecast


def select_decision_time_forecast(
    forecasts: List[NormalizedForecast],
    delivery_start: datetime,
    decision_cutoff_utc: datetime,
) -> Optional[NormalizedForecast]:
    """Select latest forecast published at or before decision_cutoff_utc for delivery_start.
    Prevents hindsight bias.
    """
    eligible = [
        f
        for f in forecasts
        if f.delivery_start == delivery_start
        and f.publish_time <= decision_cutoff_utc
    ]
    if not eligible:
        return None
    # latest publish_time
    return max(eligible, key=lambda f: f.publish_time)
