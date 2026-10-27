from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NormalizedActual(BaseModel):
    delivery_start: datetime  # UTC
    publish_time: Optional[datetime] = None  # UTC
    generation: Optional[float] = None
    fuel_type: str = "WIND"
    source: str = "FUELHH"
    settlement_date: Optional[str] = None
    settlement_period: Optional[int] = None


class NormalizedForecast(BaseModel):
    delivery_start: datetime  # UTC
    publish_time: datetime  # UTC
    generation: Optional[float] = None
    source: str = "WINDFOR"
    dataset_id: Optional[str] = None
