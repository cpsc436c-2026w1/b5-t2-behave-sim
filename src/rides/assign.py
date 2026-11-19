"""One driver for each trip (R070, R080, RF030).

Local code for the studio's worked example. The trip is assigned by a write with a condition: "the trip is not
assigned yet". On AWS that is one DynamoDB UpdateItem with a ConditionExpression on table `t00-trips`; here a lock
makes the check and the write one step.
"""
import threading

ASSIGNED, REFUSED = "assigned", "refused"


class Trips:
    def __init__(self):
        self._driver = {}                      # trip_id -> driver_id, or None while the trip is not assigned
        self._lock = threading.Lock()

    def request(self, trip_id: str) -> None:
        self._driver.setdefault(trip_id, None)

    def accept(self, trip_id: str, driver_id: str) -> str:
        with self._lock:                       # check and write together: the conditional write
            if self._driver.get(trip_id) is not None:
                return REFUSED
            self._driver[trip_id] = driver_id
            return ASSIGNED

    def driver_of(self, trip_id: str):
        return self._driver.get(trip_id)
