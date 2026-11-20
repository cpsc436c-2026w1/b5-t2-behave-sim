"""Steps for the counts of trips requested (rules RF010 and RF020)."""
from behave import then, when

from rides.counting import NO_DATA, count_requests, dedupe_is_on, show

DAY = "2026-11-23T"


def start_of(hhmm: str) -> str:
    return f"{DAY}{hhmm}:00Z"


def label(zone, start: str) -> str:
    """zone 161, between 09:10 and 09:15"""
    hour, minute = int(start[11:13]), int(start[14:16]) + 5
    end = f"{hour + minute // 60:02d}:{minute % 60:02d}"
    return f"zone {zone}, between {start[11:16]} and {end}"


def switch_note() -> str:
    return "" if dedupe_is_on() else " (DEDUPE=off: the duplicate check is off)"


@when("the counts are read at {time}")
def step_read(context, time):
    context.counts = count_requests(context.deliveries, read_at=time)


@then("zone {zone:d} shows {expected:d} trip requested between {start} and {end}")
@then("zone {zone:d} shows {expected:d} trips requested between {start} and {end}")
def step_count(context, zone, expected, start, end):
    actual = show(context.counts, zone, start_of(start))
    assert actual == expected, (f"{label(zone, start_of(start))}: expected {expected} trips requested, "
                                f"the system counted {actual}{switch_note()}")


@then("zone {zone:d} shows no data between {start} and {end}")
def step_no_data(context, zone, start, end):
    actual = show(context.counts, zone, start_of(start))
    assert actual == NO_DATA, f"{label(zone, start_of(start))}: expected no data, the system shows {actual}"


@then("zones {zones} show {totals} trips requested between {start} and {end}")
def step_totals(context, zones, totals, start, end):
    """zones 48, 161 and 230 show 304, 191 and 342 trips requested between 09:00 and 10:00: the sum of the zone's
    counts over the periods that start in that time."""
    zone_list = [int(z) for z in zones.replace(" and ", ", ").split(", ")]
    total_list = [int(n) for n in totals.replace(" and ", ", ").split(", ")]
    assert len(zone_list) == len(total_list), f"{len(zone_list)} zones and {len(total_list)} totals"
    first, last = start_of(start), start_of(end)
    for zone, want in zip(zone_list, total_list):
        got = sum(n for (z, s), n in context.counts.items() if z == zone and first <= s < last)
        assert got == want, (f"zone {zone}, between {start} and {end}: expected {want} trips requested, "
                             f"the system counted {got}{switch_note()}")
