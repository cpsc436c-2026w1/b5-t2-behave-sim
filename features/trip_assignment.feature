@JS02 @JS03
Feature: One driver for each trip
  Covers JS02 (driver): whether the trip I accepted is mine.
  Covers JS03 (rider): which driver is coming.
  A table holds the only accepts of its example. A simulated data set is named by its id and described in
  docs/design.md, section Data, part (d).

  @R070
  Rule: When a driver accepts a trip that is requested and not assigned, the trip is assigned to that driver

    Example: One driver accepts
      Given trip t-0301 is requested
      When driver d-0046 accepts trip t-0301 at 2026-11-23T09:20:05Z
      Then by 2026-11-23T09:20:07Z driver d-0046 has the answer that the trip is assigned to them

  @R080 @RF030
  Rule: If a driver accepts a trip that is already assigned, the accept is refused and the trip stays with its driver

    Example: Second driver accepts 4 seconds later
      Given trip t-0302 is requested
      And driver d-0046 accepts trip t-0302
      When driver d-0131 accepts trip t-0302
      Then driver d-0131 is refused
      And trip t-0302 is assigned to driver d-0046

    Example: Two drivers accept at the same time
      Given trip t-0303 is requested
      When these accepts are received at the same time:
        | event_id  | trip_id | driver_id | event_time           | received_time        |
        | ev-000311 | t-0303  | d-0046    | 2026-11-23T09:20:05Z | 2026-11-23T09:20:06Z |
        | ev-000312 | t-0303  | d-0131    | 2026-11-23T09:20:04Z | 2026-11-23T09:20:06Z |
      Then trip t-0303 is assigned to exactly one of drivers d-0046 and d-0131
      And 1 accept is refused

    Example: Twenty trips, two drivers each
      Given the simulated data set SIM03 "double-accept"
      When the two accepts of every trip are received at the same time
      Then every trip is assigned to exactly one of its two drivers
      And 20 accepts are refused

    # Question (Q020): which driver gets the trip when two accept at the same moment?

  @R090
  Rule: While a trip is assigned and not completed, the rider is shown the trip's driver

    Example: Rider looks after the accept
      Given trip t-0304 is requested
      And driver d-0046 accepts trip t-0304
      When the rider of trip t-0304 asks who is coming
      Then the rider is shown driver d-0046
