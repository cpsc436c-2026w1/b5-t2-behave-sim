Feature: Trips requested in each zone, on our simulated hour
  B5T2 Part C: one scenario that reads the generated folder sim/data/SIM01/. Each Then value was taken from
  sim/data/SIM01/_truth/ with sim/query.py before the run.

  Scenario: Every request of SIM01 counted once
    Given the deliveries of SIM01
    When the counts are read at 2026-11-23T10:11:00Z
    Then zones 48, 161 and 230 show 304, 191 and 342 trips requested between 09:00 and 10:00
