# CPSC 436C B5T2: behave and simulated data for your project

Write step code that makes one behave example run, simulate an incoming batch of your own project's data with the
help of a coding assistant, check it against the simulation standards, and run a scenario on it whose expected
value you know before the run. The provided scripts run on your laptop and call neither AWS nor a model. In Part B, your coding assistant writes
your generator, and the assistant itself may call a remote model.

The repository is the rides example of Checkpoint 1 ([EXAMPLE.md](EXAMPLE.md)), with the tools of this tutorial
added.

| Part | What you do |
|---|---|
| [A: step code for one rule](#part-a-step-code-for-one-rule) | write the three steps of one example; run it to `1 passed` |
| [B: simulate your own incoming batch](#part-b-simulate-your-own-incoming-batch) | generate SIM01, check it, then have your assistant write your own SIM01 |
| [C: run a scenario on a simulated data set](#part-c-run-a-scenario-on-a-simulated-data-set) | a scenario on SIM01 with its expected value from the truth; break it and read the failure |
| [D: send it to AWS (at home, needs a lease)](#part-d-at-home-send-it-to-aws) | replay SIM01 to S3, read it back, clean up |

| File | What it is |
|---|---|
| [`docs/simulation-standards.md`](docs/simulation-standards.md) | the seven conventions we recommend for simulated data (guidance, not required) |
| [`prompts/simulate.md`](prompts/simulate.md) | the prompt for Part B: your assistant writes your generator |
| [`sim/check.py`](sim/check.py), [`sim/query.py`](sim/query.py) | the check of a data set, and DuckDB questions about it; one file each, to copy to your team repo |
| [`shapes/`](shapes/README.md) | worked examples of Part B for three project shapes: lakehouse, operational, generative AI |
| `features/`, `src/rides/`, `sim/generate.py` | the rides example: features, local code, the generator of SIM01 to SIM03 |

## Before the tutorial

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and git.
2. In a terminal on your laptop, clone this repository and go into it:

   ```bash
   git clone https://github.com/cpsc436c-2026w1/b5-t2-behave-sim.git
   cd b5-t2-behave-sim
   ```

3. Install the packages:

   ```bash
   uv sync
   ```

   You should see the last line `+ typing-inspection==…` or `Audited … packages`. The first run downloads behave,
   DuckDB, Pydantic and pytest.

4. For Part B on your own project: a coding assistant (Claude Code or Kiro, as in B5T1) and your team repo cloned
   next to this one, with a small sample of your data in it (your data set's preview file, or about 20 rows of your
   own data, under 1 MB).

Every command below runs in the root of this repository, unless a step says your team repo.

## Part A: step code for one rule

**Goal.** One example of rule RF010 ("every trip request is counted exactly once, even when the stream delivers its
event twice") runs against the local code in `src/rides/counting.py`. behave runs an example by matching each line
to a step function, in Python, in `features/steps/`. Three of those functions are missing from this repository:
you write them.

### A1. Run the example and see its undefined steps

```bash
uv run behave features/js01_trips_per_zone.feature --name "One request delivered twice"
```

This tutorial always runs one scenario or one tag. A plain `uv run behave` also runs the example's other rules,
whose step code is not written yet, so it ends with failed and errored scenarios: that is expected here.

What you should see, at the end:

```text
Errored scenarios:
  features/js01_trips_per_zone.feature:68  One request delivered twice

0 features passed, 0 failed, 1 error, 0 skipped
0 rules passed, 0 failed, 1 error, 5 skipped
0 scenarios passed, 0 failed, 1 error, 10 skipped
0 steps passed, 0 failed, 40 skipped, 3 undefined
Took 0min 0.000s

You can implement step definitions for undefined steps with these snippets:

from behave.api.pending_step import StepNotImplementedError
@given(u'only these trip requests are received:')
def step_impl(context):
    raise StepNotImplementedError(u'Given only these trip requests are received:')


@when(u'the counts are read at 2026-11-23T09:15:30Z')
def step_impl(context):
    raise StepNotImplementedError(u'When the counts are read at 2026-11-23T09:15:30Z')


@then(u'zone 161 shows 2 trips requested between 09:10 and 09:15')
def step_impl(context):
    raise StepNotImplementedError(u'Then zone 161 shows 2 trips requested between 09:10 and 09:15')
```

`undefined` means no step function matches the line. behave prints a snippet for each: the decorator and the text it
must match.

<details>
<summary>What happens when you do this step</summary>

The example is in `features/js01_trips_per_zone.feature`, under `@RF010`:

```gherkin
    Example: One request delivered twice
      Given only these trip requests are received:
        | event_id  | trip_id | pickup_zone_id | event_time           | received_time        |
        | ev-000101 | t-0101  | 161            | 2026-11-23T09:11:00Z | 2026-11-23T09:11:01Z |
        | ev-000102 | t-0102  | 161            | 2026-11-23T09:12:30Z | 2026-11-23T09:12:31Z |
        | ev-000101 | t-0101  | 161            | 2026-11-23T09:11:00Z | 2026-11-23T09:12:40Z |
      When the counts are read at 2026-11-23T09:15:30Z
      Then zone 161 shows 2 trips requested between 09:10 and 09:15
```

`--name` runs only the example with that name. The `Given` puts data in front of the system, the `When` makes the
system act, the `Then` compares what the system shows with a number written in the example, before the run.

</details>

### A2. Write the three steps

In your editor, open `features/steps/data_steps.py` and replace the comment lines that start at `# B5T2 Part A` with
the `Given`. Each row of the table becomes one delivery:

```python
@given("only these trip requests are received:")
def step_requests_table(context):
    for row in context.table:
        delivery = dict(zip(context.table.headings, row.cells))
        delivery["event_type"] = "trip_requested"
        context.deliveries.append(delivery)
```

Open `features/steps/count_steps.py` and replace its comment lines that start at `# B5T2 Part A` with the `When` and the `Then`.
`{time}` and `{zone:d}` are parameters: behave passes the text in that place of the line to the function, and `:d`
makes it a number. The `Then` has two decorators so that `1 trip` and `2 trips` both match:

```python
@when("the counts are read at {time}")
def step_read(context, time):
    context.counts = count_requests(context.deliveries, read_at=time)


@then("zone {zone:d} shows {expected:d} trip requested between {start} and {end}")
@then("zone {zone:d} shows {expected:d} trips requested between {start} and {end}")
def step_count(context, zone, expected, start, end):
    actual = show(context.counts, zone, start_of(start))
    assert actual == expected, (f"{label(zone, start_of(start))}: expected {expected} trips requested, "
                                f"the system counted {actual}{switch_note()}")
```

`count_requests`, `show`, `start_of`, `label` and `switch_note` are already imported or defined in `count_steps.py`.
The `Given` goes in `data_steps.py`, which imports `given`; pasted into `count_steps.py`, it stops with a `NameError`.

### A3. Run it again

```bash
uv run behave features/js01_trips_per_zone.feature --name "One request delivered twice"
```

What you should see:

```text
1 feature passed, 0 failed, 0 skipped
1 rule passed, 0 failed, 5 skipped
1 scenario passed, 0 failed, 10 skipped
3 steps passed, 0 failed, 40 skipped
Took 0min 0.000s
```

### A4. Run the other examples that use the same steps

The same three steps serve every example of R010, RF010 and RF020 written with a table, and the two that read a
simulated data set (`Given the simulated data set SIM01 "rush-hour"` and `… SIM02 "quiet-zone"`):

```bash
uv run behave --no-snippets --tags=@R010,@RF010,@RF020
```

What you should see:

```text
Errored scenarios:
  features/js01_trips_per_zone.feature:12  Three requests in one period

0 features passed, 0 failed, 1 error, 3 skipped
2 rules passed, 0 failed, 1 error, 11 skipped
5 scenarios passed, 0 failed, 1 error, 17 skipped
21 steps passed, 0 failed, 64 skipped, 3 undefined
Took 0min 0.000s
```

The one error is R010's first example, "Three requests in one period": its `When the period … ends` and
`Then within 30 s …` have no step code in this repository. Writing them is the same work as A2, if you want more.

## Part B: simulate your own incoming batch

**Goal.** A simulated data set that you can trust: the same command writes the same files, every line matches your
event models, and the truth says what happened, so that a `Then` can state its value before the run. Read
[`docs/simulation-standards.md`](docs/simulation-standards.md) first: these steps check SIM01 of the rides example
against it, then your own.

### B1. Generate SIM01 and check it

```bash
uv run python -m sim.generate
```

What you should see:

```text
SIM01 rush-hour: 2511 events, 2515 deliveries, 6 fault records (late, twice) -> sim/data/SIM01/
SIM02 quiet-zone: 2331 events, 2331 deliveries, 1 fault records (quiet) -> sim/data/SIM02/
SIM03 double-accept: 60 events, 60 deliveries, 10 fault records (later-first) -> sim/data/SIM03/
```

```bash
uv run python sim/check.py SIM01
```

What you should see:

```text
SIM01: sim/data/SIM01/ (models in src/rides/events.py: trip_accepted, trip_completed, trip_requested)
ok   JSON: every line is one JSON object
ok   folders: 1 source (trip-events), 3 files, every line in the folder of its received_time
ok   validate: 2515 delivery lines and 2511 truth events match their models
ok   truth: each of 2511 event_ids once, every delivery is in it
recount (DuckDB):
  event_type                 truth   lines
  trip_accepted                837     837
  trip_completed               837     837
  trip_requested               837     841
ok   twice: 4 records, each event delivered once more
ok   never: none
ok   received after event: every delivery has received_time >= event_time
ok   late: 2 events first delivered 391 s to 405 s after event_time; every other event within 1 s
ok   changed: none: every delivery equals its truth event
ok   lines: 2515 = 2511 truth - 0 never + 4 twice
--   other fault kinds, not checked here: none
OK: SIM01 follows the simulation standards (0 problems)
digest 69f9adeb63e7a6da
```

Every `ok` line is one check of the standards; a broken standard prints `PROBLEM` and the lines that break it. Read
the `recount` table: 841 request lines for 837 requests, because 4 requests are delivered twice. That is the
`lines` check: 2515 = 2511 - 0 + 4.

### B2. Run the generator again: the same files

```bash
uv run python -m sim.generate
uv run python sim/check.py SIM01
```

What you should see: the same output as B1, with the same digest on the last line, `69f9adeb63e7a6da`. The generator
uses one seeded random generator, so it writes the same files each time.

### B3. The Parquet step

```bash
uv run python sim/check.py SIM01 --parquet
```

What you should see, before the `OK` line:

```text
ok   parquet: sim/parquet/SIM01/trip-events.parquet 2515 rows = 2515 lines
```

DuckDB reads the JSON Lines and writes one Parquet file for each source, then counts the rows of the file. The
JSON Lines stay as they are: Parquet is a separate step.

### B4. One shape near your project

Pick the shape folder nearest your project ([`shapes/`](shapes/README.md)): `lakehouse` (a batch of files for each
day), `operational` (a stream of events with arrival times) or `genai` (questions with their answers known). Read its
README and `generate.py`, then run it. For the lakehouse shape:

```bash
uv run python shapes/lakehouse/generate.py
uv run python sim/check.py SIM01 --root shapes/lakehouse
```

What you should see:

```text
SIM01 late-batches: 156 readings, 157 deliveries in 7 batch files, 9 fault records -> shapes/lakehouse/data/SIM01/
SIM01: shapes/lakehouse/data/SIM01/ (models in shapes/lakehouse/events.py: reading_reported)
ok   JSON: every line is one JSON object
ok   folders: 1 source (readings), 7 files, every line in the folder of its received_time
ok   validate: 157 delivery lines and 156 truth events match their models
ok   truth: each of 156 event_ids once, every delivery is in it
recount (DuckDB):
  event_type                 truth   lines
  reading_reported             156     157
ok   twice: 3 records, each event delivered once more
ok   never: 2 events in the truth and not delivered
ok   received after event: every delivery has received_time >= event_time
ok   late: 2 events first delivered 54 h after event_time; every other event within 30 h
ok   changed: 2 records, each delivery differs in its field only
ok   lines: 157 = 156 truth - 2 never + 3 twice
--   other fault kinds, not checked here: none
OK: SIM01 follows the simulation standards (0 problems)
digest 766ba0c5f3b3cfe2
```

This data set has all four fault kinds of the standards. For the other shapes, replace `lakehouse` with
`operational` or `genai`; both end with `OK: SIM01 follows the simulation standards (0 problems)`.

### B5. Your own SIM01, with your assistant

In a terminal, in your team repo root:

1. Copy `docs/simulation-standards.md` from this repository to `docs/` of your team repo, and `sim/check.py` and
   `sim/query.py` to `sim/`.
2. Add the two packages. If your team repo has no `pyproject.toml` yet, run `uv init --bare` in its root first;
   then:

   ```bash
   uv add duckdb pydantic
   ```

3. Open [`prompts/simulate.md`](prompts/simulate.md), fill in its four lines in angle brackets (your sample, what
   SIM01 shows, its shape, its faults), and send the prompt to your assistant.
4. When the assistant says it is done, run the check yourself:

   ```bash
   uv run python sim/check.py SIM01
   ```

What you should see: `OK: SIM01 follows the simulation standards (0 problems)` and a digest. Run
`uv run python sim/generate.py` and `uv run python sim/check.py SIM01` a second time and compare the two digests:
they should be the same. Then read SIM01's bullet in your `docs/design.md` against the check's
`recount` table: every count in the bullet should be one the check printed.

## Part C: run a scenario on a simulated data set

**Goal.** A scenario that reads a generated folder, with its `Then` value taken from the truth before the run. Then
you break the system and read the failure. This part uses SIM01 of the rides example and the steps of Part A.

### C1. The expected value, from the truth

```bash
uv run python sim/query.py SIM01 "SELECT pickup_zone_id, count(*) AS trips FROM truth WHERE event_type = 'trip_requested' GROUP BY 1 ORDER BY 1"
```

What you should see:

```text
┌────────────────┬───────┐
│ pickup_zone_id │ trips │
│     int64      │ int64 │
├────────────────┼───────┤
│             48 │   304 │
│            161 │   191 │
│            230 │   342 │
└────────────────┴───────┘
```

These are the trips requested in each zone, each once, from `_truth/events.jsonl`. The system never reads that
folder.

### C2. Write the scenario and run it

In your editor, create `features/sim01_by_zone.feature` with:

```gherkin
Feature: Trips requested in each zone, on our simulated hour
  B5T2 Part C: one scenario that reads the generated folder sim/data/SIM01/. Each Then value was taken from
  sim/data/SIM01/_truth/ with sim/query.py before the run.

  Scenario: Every request of SIM01 counted once
    Given the deliveries of SIM01
    When the counts are read at 2026-11-23T10:11:00Z
    Then zones 48, 161 and 230 show 304, 191 and 342 trips requested between 09:00 and 10:00
```

`Given the deliveries of SIM01` reads `sim/data/SIM01/trip-events/`, the deliveries in the order received; its step
is in `features/steps/data_steps.py`. Run it:

```bash
uv run behave --no-snippets features/sim01_by_zone.feature
```

What you should see:

```text
1 feature passed, 0 failed, 0 skipped
1 scenario passed, 0 failed, 0 skipped
3 steps passed, 0 failed, 0 skipped
Took 0min 0.019s
```

### C3. Break it: turn the duplicate check off

`DEDUPE=off` turns off the line of `src/rides/counting.py` that skips an `event_id` already counted. Before you run
it, write down which zones you expect to fail, and by how much.

```bash
DEDUPE=off uv run behave --no-snippets features/sim01_by_zone.feature
```

On Windows PowerShell, run `$env:DEDUPE = 'off'` first, then the same command without `DEDUPE=off`, and
`Remove-Item Env:DEDUPE` after this step.

What you should see:

```text
ASSERT FAILED: zone 48, between 09:00 and 10:00: expected 304 trips requested, the system counted 307 (DEDUPE=off: the duplicate check is off)

Failing scenarios:
  features/sim01_by_zone.feature:5  Every request of SIM01 counted once

0 features passed, 1 failed, 0 skipped
0 scenarios passed, 1 failed, 0 skipped
2 steps passed, 1 failed, 0 skipped
Took 0min 0.018s
```

Find the deliveries that cause it, from the truth:

```bash
uv run python sim/query.py SIM01 "SELECT f.fault, f.event_id, t.pickup_zone_id FROM faults f JOIN truth t USING (event_id) ORDER BY 1, 2"
```

What you should see:

```text
┌─────────┬───────────┬────────────────┐
│  fault  │ event_id  │ pickup_zone_id │
│ varchar │  varchar  │     int64      │
├─────────┼───────────┼────────────────┤
│ late    │ ev-000103 │            230 │
│ late    │ ev-001276 │             48 │
│ twice   │ ev-000100 │             48 │
│ twice   │ ev-000358 │             48 │
│ twice   │ ev-001144 │             48 │
│ twice   │ ev-001955 │            161 │
└─────────┴───────────┴────────────────┘
```

Three of the four `twice` requests are in zone 48: 304 + 3 = 307. The check stops at the first zone that fails;
zone 161 would show 192.

### C4. Find a planted bug

Branch `bug-boundary` has Part A's steps and Part C's scenario, and one wrong character in `src/rides/`. Put your
changes aside, then switch to it:

```bash
git stash -u
git switch bug-boundary
uv run behave --no-snippets --tags=@R010,@RF010,@RF020
```

What you should see, among the lines:

```text
ASSERT FAILED: zone 161, between 09:05 and 09:10: expected 1 trips requested, the system counted no data

Failing scenarios:
  features/js01_trips_per_zone.feature:22  A request at the end of a period is in the next period

Errored scenarios:
  features/js01_trips_per_zone.feature:12  Three requests in one period

0 features passed, 0 failed, 1 error, 4 skipped
2 rules passed, 0 failed, 1 error, 11 skipped
4 scenarios passed, 1 failed, 1 error, 18 skipped
19 steps passed, 1 failed, 68 skipped, 3 undefined
Took 0min 0.000s
```

Find the bug from the failure alone: which example fails, what is special about its event time, and which function
of `src/rides/counting.py` decides the period of a time. `uv run pytest -q` also points at it: read the name of the test that fails. When you have it,
compare with `main`:

```bash
git diff main bug-boundary -- src/
```

Then come back to your own work:

```bash
git switch main
git stash pop
```

The branch `solution` has the code of Part A and the scenario of Part C.

## Part D (at home): send it to AWS

This part needs an AWS lease, and the course's replay recipe. When both are available: replay SIM01's deliveries to
an S3 prefix of your bucket (and, for a streaming project, to a Kinesis stream) in the order received, read them back
with Athena or DuckDB, compare the counts with `sim/check.py`'s recount, and delete what you created. The recipe's
page will have the commands and their costs. Keep the generated data on your laptop until then: Parts A to C need no
AWS.

## What to take to your project

- One step file of your own for one rule of your features, written like A2.
- Your SIM01: `src/<package>/events.py`, `sim/generate.py` and its bullet in `docs/design.md`. If your team follows
  the simulation standards (they are guidance, not required), also `sim/check.py` printing `OK`.
- One scenario like C2, with its `Then` values taken from your truth with `sim/query.py`.
