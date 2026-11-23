"""Steps for the counts of trips requested (rules R010, R020, RF010 and RF020)."""
from datetime import timedelta

from behave import then, when

from rides.counting import NO_DATA, count_requests, dedupe_is_on, parse, show

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


@when("the period between {start} and {end} ends")
def step_period_ends(context, start, end):
    """The period ends at its end time; the Then that follows says how long after that the count is read."""
    context.period_end = start_of(end)


@then("zone {zone:d} shows {expected:d} trip requested between {start} and {end}")
@then("zone {zone:d} shows {expected:d} trips requested between {start} and {end}")
def step_count(context, zone, expected, start, end):
    actual = show(context.counts, zone, start_of(start))
    assert actual == expected, (f"{label(zone, start_of(start))}: expected {expected} trips requested, "
                                f"the system counted {actual}{switch_note()}")


@then("within {seconds:d} s zone {zone:d} has {expected:d} trip requested between {start} and {end}")
@then("within {seconds:d} s zone {zone:d} has {expected:d} trips requested between {start} and {end}")
def step_count_within(context, seconds, zone, expected, start, end):
    """The count read `seconds` after the period ended, from the requests received by then. The local code has no
    clock: this checks which requests the count holds at that time, not how long the system took (R010's latency
    target is measured on AWS)."""
    assert start_of(end) == context.period_end, f"the example ended the period at {context.period_end}, not at {end}"
    read_at = (parse(context.period_end) + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
    actual = show(count_requests(context.deliveries, read_at=read_at), zone, start_of(start))
    assert actual == expected, (f"{label(zone, start_of(start))}, {seconds} s after the period ended: expected "
                                f"{expected} trips requested, the system counted {actual}{switch_note()}")


@then("zone {zone:d} shows no data between {start} and {end}")
def step_no_data(context, zone, start, end):
    actual = show(context.counts, zone, start_of(start))
    assert actual == NO_DATA, f"{label(zone, start_of(start))}: expected no data, the system shows {actual}"


@when("the time is {time}")
def step_time_is(context, time):
    """R020: the stored counts at that time, from the requests received by then, late ones included."""
    context.counts = count_requests(context.deliveries, read_at=time)


@then("zone {zone:d} has {expected:d} trip requested between {start} and {end}")
@then("zone {zone:d} has {expected:d} trips requested between {start} and {end}")
def step_stored(context, zone, expected, start, end):
    actual = show(context.counts, zone, start_of(start))
    assert actual == expected, (f"{label(zone, start_of(start))}: expected {expected} trips stored, "
                                f"the system has {actual}{switch_note()}")


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
