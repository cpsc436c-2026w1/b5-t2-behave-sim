# Simulation standards

These are the conventions we recommend for every simulated data set (SIM01, SIM02 …) of your project. Staff read
them as guidance at Checkpoint 2: a data set that follows them is quick to read and check, and `sim/check.py` can
check it for you. They are not required. Parquet is optional.

The prompt of the B5T2 tutorial (`prompts/simulate.md` in the tutorial repository) asks your coding assistant to
read this file first, so that the generator it writes for you follows it.

Each standard below has the rule, then how the rides example of the B5T2 tutorial repository follows it.

## 1. Events as JSON Lines, with a Pydantic model for each event type

One event per line. Every event has `event_id`, `event_type`, `event_time` (UTC, ISO 8601, written like
`2026-11-23T09:00:00Z`) and the key of the thing it is about (the entity key, such as `trip_id`). Write one Pydantic
model for each event type in `src/<package>/events.py`, with `extra="forbid"`, and import it in the generator and in
the code that reads the events. `extra="forbid"` turns a misspelled field into an error.
`event_time` is when the event happened in the world; `received_time` (standard 2) is when your system got it. A
value that the event is about, such as the month a price is for, is a field of its own.

Rides: `src/rides/events.py` has `TripRequested`, `TripAccepted` and `TripCompleted`; the entity key is `trip_id`.
One line of SIM01:

```json
{"event_type": "trip_requested", "trip_id": "t-0001", "rider_id": "p-52201", "pickup_zone_id": 48, "dropoff_zone_id": 1, "quoted_fare": 86.45, "event_time": "2026-11-23T09:00:00Z", "event_id": "ev-000001", "received_time": "2026-11-23T09:00:01Z"}
```

`sim/check.py` finds the models by their `event_type` field, which is a `Literal` with one value
(`event_type: Literal["trip_requested"]`): declare it in each event type's model, not in a shared base class.

## 2. Two folders: what the system receives, and the truth

What the system receives goes in arrival order, each line with the time it was received, `received_time`:

```text
sim/data/<SIM>/<source>/dt=<day>/hour=<hour>/deliveries.jsonl
```

`dt` and `hour` are the day and hour of `received_time`, the folders a stream writes to in your bucket. A batch
that arrives once a day is one file in one `hour=` folder of its day. The truth goes beside it:

```text
sim/data/<SIM>/_truth/events.jsonl    each event once, as it happened (no received_time)
sim/data/<SIM>/_truth/faults.jsonl    each injected fault, one line each
```

The system never reads `_truth/`. Expected answers that are not events, such as the reference answers of eval
cases, can go in `_truth/answers.jsonl`, one line for each event, with its `event_id`.

Rides: `sim/data/SIM01/trip-events/dt=2026-11-23/hour=09/deliveries.jsonl` and the `_truth/` folder beside it.

## 3. A name and a bullet for each data set

Name each data set (SIM01 …) and give it a bullet in `docs/design.md`, section Data: the sample it is made from, the
seed, the size, the time window, and the faults by kind and count. The four kinds of fault, each a line in
`_truth/faults.jsonl` with the `event_id` it is about:

| Kind | What happens | What `sim/check.py` recounts |
|---|---|---|
| `twice` | the event is delivered one more time | the event's deliveries = 1 + its `twice` lines |
| `late` | the event is received later than usual | its delay, from `event_time` to its first `received_time`, is longer than the delay of every delivered event not marked `late` |
| `never` | the event happened and is not delivered | it is in the truth and has no delivery |
| `changed` | a delivery has a different value in one field; the line names it in `field` | a delivery differs from the truth in that field, and no delivery differs anywhere else |

A fault of another kind, one that your system needs, gets its own name; `sim/check.py` lists it and does not check
it. Describe it in the bullet.

Rides, SIM01: "One morning hour from DS01: the 837 trips requested in zones 48, 161 and 230 on 2024-03-14 between
08:00 and 09:00 New York time, moved to 09:00 to 10:00 UTC on 2026-11-23 … 2,511 events sent as 2,515 deliveries: 4
requests arrive twice (`twice`), and 2 arrive 6 to 10 minutes late (`late`). Seed 436." SIM02 has a fault of its own
kind, `quiet`: ten minutes of one zone without trips.

## 4. Seeded and deterministic

The same command writes the same files, byte for byte. Use one seeded random generator (`random.Random(436)`), and
sort what you write. Commit a small seed sample (under 1 MB, with its licence stated beside it); make larger data
sets with a size setting, not by committing them.

Rides: seed 436 in `sim/datasets.py`, the sample `sim/seed/ds01_sample.csv` (837 rows, 74 KB) and the query that
wrote it, `tools/extract_seed.sql`. `sim/check.py` prints a digest of the data set's files as its last line: run the
generator twice, and the two digests are the same.

## 5. Expected answers come from the truth, before the run

A `Then` states a value that you know before the system runs: compute it from `_truth/`, not from the system's
output.

Rides: the trip counts in SIM01's `Then` are the requests in `_truth/events.jsonl`, counted by zone:

```bash
uv run python sim/query.py SIM01 "
  SELECT pickup_zone_id, count(*) AS trips
  FROM truth
  WHERE event_type = 'trip_requested'
  GROUP BY 1 ORDER BY 1"
```

## 6. Parquet is a separate step, with a row-count check

Keep the generator's output as JSON Lines. If you want Parquet, make it in a second step with DuckDB
(`COPY (SELECT * FROM read_json(…)) TO '….parquet'`) and check that the Parquet file has as many rows as the JSON
Lines it came from.

Rides: `uv run python sim/check.py SIM01 --parquet` writes `sim/parquet/SIM01/trip-events.parquet` and prints
`2515 rows = 2515 lines`.

## 7. Laptop-sized, synthetic ids, no real personal data

Thousands of events, not millions, unless a requirement needs more (then use the size setting). No real personal
data. Ids that a source does not have are made up (`d-0042`, `p-52201`).

Rides: DS01 has no drivers or riders, so `driver_id` and `rider_id` are made up by the generator.

## Check a data set

```bash
uv run python sim/check.py SIM01
```

The check validates every line against your models, recounts the truth and each fault kind with DuckDB, and ends
with `OK: SIM01 follows the simulation standards (0 problems)` or `FAILED: …` and the lines that break a standard.
`OK` covers the checks it prints. The sample's licence, the absence of personal data, the bullet of standard 3 and
that the system never reads `_truth/` are yours to check. If `src/` has more than one `events.py`, name the file of
the data set's models: `uv run python sim/check.py SIM01 --events src/<package>/events.py`.
`sim/check.py` and `sim/query.py` are single files: copy them to `sim/` of your team repo, and add `duckdb` and
`pydantic` (`uv add duckdb pydantic`).
