@JS01
Feature: Yesterday's completed trips in one table
  Covers the second part of JS01 (operations analyst): each morning, yesterday's completed trips in one table.
  A simulated data set is named by its id and described in docs/design.md, section Data, part (d).
  Each example starts with tables trips_curated and trips_rejected empty.

  @R040
  Rule: When the file of a day's completed trips arrives, its rows are loaded into table trips_curated

    Example: File for 2026-11-22
      Given the simulated data set SIM04 "trips-day"
      When the file for 2026-11-22 arrives at 2026-11-23T05:10:00Z
      Then before 2026-11-23T06:00:00Z table trips_curated has 18590 rows for 2026-11-22

  @R050
  Rule: If a completed trip in the file does not have a fare above 0, it is left out of trips_curated and written to trips_rejected with the reason

    Example: File with one trip without a fare
      Given a file of completed trips with these rows:
        | trip_id | driver_id | dropoff_zone_id | trip_miles | trip_time_s | fare  | driver_pay | event_time           |
        | t-0401  | d-0046    | 68              | 0.86       | 462         | 9.11  | 6.56       | 2026-11-22T12:11:21Z |
        | t-0402  | d-0131    | 230             | 1.62       | 731         |       | 31.49      | 2026-11-22T14:30:00Z |
      When the file arrives at 2026-11-23T05:10:00Z
      Then before 2026-11-23T06:00:00Z table trips_curated has 1 row for 2026-11-22
      And table trips_rejected has trip t-0402 with reason "no fare"

    Example: File with 3 trips without a fare
      Given the simulated data set SIM04 "trips-day"
      When the file for 2026-11-22 arrives at 2026-11-23T05:10:00Z
      Then before 2026-11-23T06:00:00Z table trips_rejected has 3 rows for 2026-11-22

  @RF040 @live
  Rule: The count by zone over 30 days stays fast while the stream adds a small file to raw/ every minute

    Example: Thirty days of small files
      Given the simulated data set SIM05 "raw-30-days"
      When the data set is copied to the bucket
      And the count by zone over 30 days runs 5 times in Athena
      Then the median run time is under 5 s
