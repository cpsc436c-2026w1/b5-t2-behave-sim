"""Lakehouse shape: the daily readings of weather stations, one event per station, day and element."""
from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, field_validator


class ReadingReported(BaseModel):
    """A station's reading for one day: TMAX and TMIN in tenths of °C, PRCP in tenths of mm (GHCN units)."""
    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: Literal["reading_reported"]
    event_time: AwareDatetime          # the start of the day the reading is for, 00:00 UTC
    station_id: str                    # the entity key
    element: Literal["TMAX", "TMIN", "PRCP"]
    value: int

    @field_validator("event_time")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("must be UTC (end the time with Z)")
        return value


EVENTS = {"reading_reported": ReadingReported}
