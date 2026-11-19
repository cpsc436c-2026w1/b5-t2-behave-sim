"""The local handlers: the count with its duplicate check and its switch, and the conditional accept."""
import threading

from rides.assign import ASSIGNED, REFUSED, Trips
from rides.counting import NO_DATA, count_requests, dedupe_is_on, period_start, show

P = "2026-11-23T09:10:00Z"


def request(event_id, zone, event_time, received_time):
    return dict(event_type="trip_requested", event_id=event_id, pickup_zone_id=zone, event_time=event_time,
                received_time=received_time)


TWICE = [request("ev-1", 161, "2026-11-23T09:11:00Z", "2026-11-23T09:11:01Z"),
         request("ev-2", 161, "2026-11-23T09:12:30Z", "2026-11-23T09:12:31Z"),
         request("ev-1", 161, "2026-11-23T09:11:00Z", "2026-11-23T09:12:40Z")]


def test_period_start_includes_the_start_and_not_the_end():
    assert period_start("2026-11-23T09:10:00Z") == P
    assert period_start("2026-11-23T09:14:59Z") == P
    assert period_start("2026-11-23T09:15:00Z") == "2026-11-23T09:15:00Z"


def test_duplicate_is_counted_once():
    assert count_requests(TWICE, dedupe=True) == {(161, P): 2}


def test_without_the_check_the_duplicate_is_counted_twice():
    assert count_requests(TWICE, dedupe=False) == {(161, P): 3}


def test_switch_in_the_environment(monkeypatch):
    monkeypatch.delenv("DEDUPE", raising=False)
    assert dedupe_is_on() and count_requests(TWICE) == {(161, P): 2}
    monkeypatch.setenv("DEDUPE", "off")
    assert not dedupe_is_on() and count_requests(TWICE) == {(161, P): 3}
    monkeypatch.setenv("DEDUPE", "on")
    assert count_requests(TWICE) == {(161, P): 2}


def test_only_what_was_received_by_the_time_of_reading_counts():
    assert count_requests(TWICE, read_at="2026-11-23T09:12:00Z", dedupe=True) == {(161, P): 1}


def test_other_event_types_are_not_counted():
    accept = dict(event_type="trip_accepted", event_id="ev-9", event_time="2026-11-23T09:11:05Z",
                  received_time="2026-11-23T09:11:06Z")
    assert count_requests([accept]) == {}


def test_a_period_without_a_request_is_no_data_not_zero():
    counts = count_requests(TWICE, dedupe=True)
    assert show(counts, 161, P) == 2
    assert show(counts, 48, P) == NO_DATA
    assert show(counts, 161, "2026-11-23T09:15:00Z") == NO_DATA


def test_second_accept_is_refused():
    trips = Trips()
    trips.request("t-1")
    assert trips.accept("t-1", "d-1") == ASSIGNED
    assert trips.accept("t-1", "d-2") == REFUSED
    assert trips.driver_of("t-1") == "d-1"


def test_accept_of_a_trip_that_was_not_requested_is_refused():
    assert Trips().accept("t-9", "d-1") == REFUSED


def two_accepts_before_either_write(conditional):
    """Both accepts read the trip, then both write: neither has an answer when the other's write is sent."""
    trips, answers, gate = Trips(), [], threading.Barrier(2)
    trips.request("t-1")

    def send(driver):
        answers.append((driver, trips.accept("t-1", driver, before_write=gate.wait, conditional=conditional)))

    threads = [threading.Thread(target=send, args=(d,)) for d in ("d-1", "d-2")]
    [t.start() for t in threads]
    [t.join() for t in threads]
    return trips, answers


def test_two_accepts_at_once_give_one_driver():
    for _ in range(200):
        trips, answers = two_accepts_before_either_write(conditional=True)
        assert sorted(a for _, a in answers) == [ASSIGNED, REFUSED]
        assert trips.driver_of("t-1") == next(d for d, a in answers if a == ASSIGNED)


def test_without_the_condition_both_drivers_are_told_assigned():
    """The same two accepts with a check in the function and a plain write: the race the condition prevents."""
    for _ in range(200):
        _, answers = two_accepts_before_either_write(conditional=False)
        assert sorted(a for _, a in answers) == [ASSIGNED, ASSIGNED]


def test_batch_received_again_is_counted_once():
    first, second = TWICE[0], TWICE[1]
    assert count_requests([first, first, second], dedupe=True) == {(161, P): 2}
