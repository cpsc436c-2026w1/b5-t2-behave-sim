"""Operational shape: pickup orders at cafes and restaurants, two events per order."""
from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, field_validator


class OrderEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_time: AwareDatetime
    order_id: str                      # the entity key
    place_id: str                      # an Overture place id from the sample

    @field_validator("event_time")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("must be UTC (end the time with Z)")
        return value


class OrderPlaced(OrderEvent):
    event_type: Literal["order_placed"]
    items: int
    total_cad: float


class OrderReady(OrderEvent):
    event_type: Literal["order_ready"]
    prep_s: int


EVENTS = {"order_placed": OrderPlaced, "order_ready": OrderReady}
