"""The trip events of docs/design.md, section Data, Event format: one Pydantic model for each event type.

The generator (sim/generate.py) checks every event against these models before it writes a file, and
sim/check.py validates every line it reads against them. `extra="forbid"`: a field that is not listed here is an
error, so a typo in a field name stops the generator instead of reaching the system.
"""
from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, field_validator


class Event(BaseModel):
    """Fields that every event has. Times are UTC, written as 2026-11-23T09:00:00Z."""
    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_time: AwareDatetime
    trip_id: str                      # the entity key: the trip the event is about

    @field_validator("event_time")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("must be UTC (end the time with Z)")
        return value


class TripRequested(Event):
    event_type: Literal["trip_requested"]
    rider_id: str
    pickup_zone_id: int
    dropoff_zone_id: int
    quoted_fare: float


class TripAccepted(Event):
    event_type: Literal["trip_accepted"]
    driver_id: str


class TripCompleted(Event):
    event_type: Literal["trip_completed"]
    driver_id: str
    dropoff_zone_id: int
    trip_miles: float
    trip_time_s: int
    fare: float
    driver_pay: float


EVENTS = {"trip_requested": TripRequested, "trip_accepted": TripAccepted, "trip_completed": TripCompleted}


def validate(event: dict) -> BaseModel:
    """The model for the event's type, filled from the event; raises pydantic.ValidationError when a field is wrong."""
    return EVENTS[event["event_type"]].model_validate(event)
