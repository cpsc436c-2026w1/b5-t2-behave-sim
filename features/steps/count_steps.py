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


@then("every zone and period shows the count computed from the data set's record of events")
def step_all_counts(context):
    """The expected counts come from _truth/events.jsonl with a few lines written for the test, not from the handler."""
    expected = {}
    for event in context.data_set["events"]:
        if event["event_type"] == "trip_requested":
            minute = int(event["event_time"][14:16])
            start = f'{event["event_time"][:14]}{minute - minute % 5:02d}:00Z'
            key = (event["pickup_zone_id"], start)
            expected[key] = expected.get(key, 0) + 1
    for zone, start in sorted(set(expected) | set(context.counts)):
        want = expected.get((zone, start), NO_DATA)
        got = show(context.counts, zone, start)
        assert got == want, (f"{label(zone, start)}: expected {want} trips requested, "
                             f"the system counted {got}{switch_note()}")
