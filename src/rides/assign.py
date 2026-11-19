"""One driver for each trip (R070, R080, RF030).

Local code for the studio's worked example. `Trips` stands in for the DynamoDB table `t00-trips`, and `accept` for
the function `t00-assign-trip`, which runs once for each accept. The trip is assigned by a write with a condition:
"the trip does not have a driver yet". On AWS that is one UpdateItem with a ConditionExpression; here a lock inside
the table makes the check and the write one step.
"""
import threading

ASSIGNED, REFUSED = "assigned", "refused"


class Trips:
    """The table: trip_id -> driver_id, or None while the trip is not assigned."""

    def __init__(self):
        self._driver = {}
        self._lock = threading.Lock()

    def request(self, trip_id: str) -> None:
        self._driver.setdefault(trip_id, None)

    def driver_of(self, trip_id: str):
        return self._driver.get(trip_id)

    def assign_if_not_assigned(self, trip_id: str, driver_id: str) -> bool:
        """The conditional write. The table checks and writes in one step, whoever else is writing."""
        with self._lock:
            if trip_id not in self._driver or self._driver[trip_id] is not None:
                return False
            self._driver[trip_id] = driver_id
            return True

    def assign(self, trip_id: str, driver_id: str) -> None:
        """A write without a condition: the last writer wins. Used only by the test that shows why it is wrong."""
        self._driver[trip_id] = driver_id

    def accept(self, trip_id: str, driver_id: str, before_write=None, conditional: bool = True) -> str:
        """One run of the function for one accept. Returns the driver's answer.

        before_write is a pause between the function's read and its write. The examples with two drivers use it to
        hold each accept until both have read the trip, so that both writes are sent before either is finished.
        """
        seen_driver = self.driver_of(trip_id)                  # what this run read: None for both of two accepts
        if before_write is not None:
            before_write()
        if conditional:                                        # the table decides
            return ASSIGNED if self.assign_if_not_assigned(trip_id, driver_id) else REFUSED
        if seen_driver is not None:                            # the function decides from what it read: a race
            return REFUSED
        self.assign(trip_id, driver_id)
        return ASSIGNED
