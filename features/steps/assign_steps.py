"""Steps for trip assignment (rule R080, RF030): one accept, and two accepts received at the same time."""
import threading

from behave import given, then, when

from rides.assign import ASSIGNED, REFUSED, Trips


def accept_together(trips: Trips, accepts: list[tuple[str, str]]) -> dict:
    """Send the accepts from one thread each, released at the same moment. Returns {(trip, driver): answer}."""
    gate, answers = threading.Barrier(len(accepts)), {}

    def send(trip_id, driver_id):
        gate.wait()
        answers[(trip_id, driver_id)] = trips.accept(trip_id, driver_id)

    threads = [threading.Thread(target=send, args=a) for a in accepts]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return answers


@given("trip {trip_id} is requested")
def step_requested(context, trip_id):
    context.trips = Trips()
    context.trips.request(trip_id)
    context.answers = {}


@given("driver {driver_id} accepts trip {trip_id}")
@when("driver {driver_id} accepts trip {trip_id}")
def step_accept(context, driver_id, trip_id):
    context.answers[(trip_id, driver_id)] = context.trips.accept(trip_id, driver_id)


@when("these accepts are received at the same time:")
def step_accept_table(context):
    accepts = [(row["trip_id"], row["driver_id"]) for row in context.table]
    context.answers.update(accept_together(context.trips, accepts))


@when("the two accepts of every trip are received at the same time")
def step_accept_data_set(context):
    context.trips, context.answers, context.pairs = Trips(), {}, {}
    for d in context.deliveries:
        if d["event_type"] == "trip_requested":
            context.trips.request(d["trip_id"])
        else:
            context.pairs.setdefault(d["trip_id"], []).append(d["driver_id"])
    for trip_id, drivers in context.pairs.items():
        context.answers.update(accept_together(context.trips, [(trip_id, driver) for driver in drivers]))


@then("driver {driver_id} is refused")
def step_refused(context, driver_id):
    answers = [a for (_, driver), a in context.answers.items() if driver == driver_id]
    assert answers == [REFUSED], f"driver {driver_id}: expected refused, the system answered {answers}"


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
