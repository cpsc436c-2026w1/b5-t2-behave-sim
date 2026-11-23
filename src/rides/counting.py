"""Trips requested in each pickup zone for each 5-minute period (R010, RF010, RF020).

Local code for the studio's worked example. On AWS the same rule runs in the function `t00-count-requests`.
"""
import os
from datetime import datetime, timedelta

PERIOD = timedelta(minutes=5)
NO_DATA = "no data"


def parse(time: str) -> datetime:
    return datetime.fromisoformat(time.replace("Z", "+00:00"))


def period_start(event_time: str) -> str:
    """Start of the 5-minute period that holds the time: 09:13:40 is in the period between 09:10 and 09:15.

    A period holds the times from its start up to, and not including, its end: 09:15:00 is in the next period.
    """
    t = parse(event_time)
    start = t.replace(minute=0, second=0, microsecond=0)
    while not (start <= t < start + PERIOD):
        start += PERIOD
    return start.strftime("%Y-%m-%dT%H:%M:%SZ")


def dedupe_is_on() -> bool:
    """DEDUPE=off in the environment turns the duplicate check off (the studio's prediction step)."""
    return os.environ.get("DEDUPE", "on").lower() != "off"


def count_requests(deliveries: list[dict], read_at: str | None = None, dedupe: bool | None = None) -> dict:
    """Counts by (pickup zone, period start) from the deliveries received up to read_at.

    A zone and period without a request does not get an entry: there is nothing to tell 0 trips from a broken feed.
    """
    dedupe = dedupe_is_on() if dedupe is None else dedupe
    seen, counts = set(), {}
    for d in deliveries:
        if d["event_type"] != "trip_requested":
            continue
        if read_at is not None and parse(d["received_time"]) > parse(read_at):
            continue
        if dedupe:
            if d["event_id"] in seen:          # the same id again is the same event
                continue
            seen.add(d["event_id"])
        key = (int(d["pickup_zone_id"]), period_start(d["received_time"]))
        counts[key] = counts.get(key, 0) + 1
    return counts


def show(counts: dict, zone: int, start: str):
    """What a reader sees for one zone and period: the count, or `no data`."""
    return counts.get((zone, start), NO_DATA)
