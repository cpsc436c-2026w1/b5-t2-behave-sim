"""Steps for trip assignment (rule R080, RF030): one accept, and two accepts sent before either has an answer."""
import threading
import time
from datetime import datetime

from behave import given, then, when

from rides.assign import ASSIGNED, REFUSED, Trips


def accept_together(trips: Trips, accepts: list[tuple[str, str]]) -> dict:
    """Send the accepts from one thread each. Returns {(trip, driver): answer}.

    Every accept reads the trip and then waits at the gate until all of them have read it. So each write is sent
    before any other accept has an answer, and the conditional write decides.
    """
    gate, answers = threading.Barrier(len(accepts)), {}

    def send(trip_id, driver_id):
        answers[(trip_id, driver_id)] = trips.accept(trip_id, driver_id, before_write=gate.wait)

    threads = [threading.Thread(target=send, args=a) for a in accepts]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return answers


def trips_of(context) -> Trips:
    """The trips table of the example: every trip of the requests received so far is requested and not assigned."""
    if context.trips is None:
        context.trips = Trips()
        for d in context.deliveries:
            if d["event_type"] == "trip_requested":
                context.trips.request(d["trip_id"])
    return context.trips


@given("this accept is received:")
@when("this accept is received:")
def step_accept_row(context):
    """One accept, one request to our API; the time taken is measured around it."""
    (row,) = list(context.table)
    started = time.monotonic()
    context.answers[(row["trip_id"], row["driver_id"])] = trips_of(context).accept(row["trip_id"], row["driver_id"])
    context.received, context.took_s = row["received_time"], time.monotonic() - started


@when("these accepts are sent together, each before the other has an answer:")
def step_accept_table(context):
    accepts = [(row["trip_id"], row["driver_id"]) for row in context.table]
    context.answers.update(accept_together(trips_of(context), accepts))


@when("the two accepts of every trip are sent together, each before the other has an answer")
def step_accept_data_set(context):
    context.trips, context.answers, context.pairs = Trips(), {}, {}
    for d in context.deliveries:
        if d["event_type"] == "trip_requested":
            context.trips.request(d["trip_id"])
        else:
            context.pairs.setdefault(d["trip_id"], []).append(d["driver_id"])
    for trip_id, drivers in context.pairs.items():
        context.answers.update(accept_together(context.trips, [(trip_id, driver) for driver in drivers]))


@then("by {deadline} driver {driver_id} has the answer that the accept is refused")
def step_refused_by(context, deadline, driver_id):
    """The time allowed is the deadline less the time of receipt; the time taken is measured around the accept."""
    allowed_s = (datetime.fromisoformat(deadline[:-1]) - datetime.fromisoformat(context.received[:-1])).total_seconds()
    answers = [a for (_, driver), a in context.answers.items() if driver == driver_id]
    assert answers == [REFUSED], f"driver {driver_id}: expected refused, the system answered {answers}"
    assert context.took_s <= allowed_s, f"driver {driver_id}: answer after {context.took_s:.2f} s, allowed {allowed_s:.0f} s"


@then("trip {trip_id} is assigned to driver {driver_id}")
def step_assigned(context, trip_id, driver_id):
    actual = context.trips.driver_of(trip_id)
    assert actual == driver_id, f"trip {trip_id}: expected driver {driver_id}, the system has {actual}"


@then("trip {trip_id} is assigned to exactly one of drivers {first} and {second}")
def step_one_of(context, trip_id, first, second):
    told = [driver for driver in (first, second) if context.answers[(trip_id, driver)] == ASSIGNED]
    assert len(told) == 1, f"trip {trip_id}: expected 1 driver told assigned, the system told {len(told)}: {told}"
    assert context.trips.driver_of(trip_id) == told[0], f"trip {trip_id}: the table has {context.trips.driver_of(trip_id)}"


@then("every trip is assigned to exactly one of its two drivers")
def step_every_trip(context):
    for trip_id, drivers in context.pairs.items():
        told = [driver for driver in drivers if context.answers[(trip_id, driver)] == ASSIGNED]
        assert len(told) == 1, f"trip {trip_id}: expected 1 driver told assigned, the system told {len(told)}: {told}"
        assert context.trips.driver_of(trip_id) == told[0], f"trip {trip_id}: the table has {context.trips.driver_of(trip_id)}"


@then("{n:d} accept is refused")
@then("{n:d} accepts are refused")
def step_count_refused(context, n):
    refused = sum(1 for a in context.answers.values() if a == REFUSED)
    assert refused == n, f"expected {n} accepts refused, the system refused {refused}"
