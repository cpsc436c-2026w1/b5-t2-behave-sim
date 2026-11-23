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

   You should see it finish without an error. Its last lines list the packages it installed, or say that it audited
   them; the names and numbers may differ. The first run downloads behave, DuckDB, Pydantic and pytest.

4. For A5 and B5 you need your coding assistant. For A5, connect it to the course server as in B5T1. For B5, also
   have your team repo cloned next to this one, with a small sample of your data (your data set's preview file, or
   about 20 rows) in it.

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

What you should see, at the end: the example under `Errored scenarios`, `undefined` in the `steps` line, and one
snippet for each undefined step. One run's output, for example:

```text
Errored scenarios:
  features/js01_trips_per_zone.feature:68  One request delivered twice

0 features passed, 0 failed, 1 error, 0 skipped
0 rules passed, 0 failed, 1 error, 5 skipped
0 scenarios passed, 0 failed, 1 error, 10 skipped
0 steps passed, 0 failed, 40 skipped, 3 undefined

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

What you should see: the example passed, with no failed and no undefined step. One run's output, for example:

```text
1 feature passed, 0 failed, 0 skipped
1 rule passed, 0 failed, 5 skipped
1 scenario passed, 0 failed, 10 skipped
3 steps passed, 0 failed, 40 skipped
```

### A4. Run the other examples that use the same steps

The same three steps serve every example of R010, RF010 and RF020 written with a table. The `When` and `Then` you
wrote also serve the two examples that read a simulated data set; their `Given` (`Given the simulated data set
SIM01 "rush-hour"` and `… SIM02 "quiet-zone"`) is already in `features/steps/data_steps.py`:

```bash
uv run behave --no-snippets --tags=@R010,@RF010,@RF020
```

What you should see: one example under `Errored scenarios`, no failed scenario, and every other example passed. One
run's output, for example:

```text
Errored scenarios:
  features/js01_trips_per_zone.feature:12  Three requests in one period

0 features passed, 0 failed, 1 error, 3 skipped
2 rules passed, 0 failed, 1 error, 11 skipped
5 scenarios passed, 0 failed, 1 error, 17 skipped
21 steps passed, 0 failed, 64 skipped, 3 undefined
```

The one error is R010's first example, "Three requests in one period": its `When the period … ends` and
`Then within 30 s …` have no step code in this repository. Writing them is the same work as A2, which you do with
your assistant in A5.

### A5. The rest of R010, with your assistant

**Where.** This repository, in a terminal at its root, with your coding assistant started there and connected to
the course server as in B5T1, Step 1. This repository has the same example files: `.mcp.json.example` for Claude
Code, `.kiro/settings/mcp.json.example` for Kiro. Your copy of either does not show in `git status`.

**First, commit your A2 steps.** They stay on your `main`. Then `git status` and `git diff` show only what your
assistant changes:

```bash
git add -A
git commit -m "my A2 steps"
```

You should see a line with `my A2 steps`; `git status` then says `nothing to commit, working tree clean`. If git
asks who you are, run the two `git config --global` lines it prints, with your name and email, and commit again.

**What.** Ask your assistant for the rest of the step code of rule R010: the two examples of
`features/js01_trips_per_zone.feature` under `@R010`. One of them already passes with your A2 steps. Paste the
prompt of [`prompts/steps.md`](prompts/steps.md). When the assistant says it is done, run the four checks under
"Check what it wrote" on that page yourself, in that order. Do not take the assistant's word that the scenarios
pass.

What you should see, check by check:

1. `git status --short` lists files in `features/steps/` only.
2. The dry run's last lines have `untested` and no `undefined`.
3. Both R010 scenarios pass, none fail.
4. With the boundary bug in, `A request at the end of a period is in the next period` is under
   `Failing scenarios`; after `git restore`, `git status --short` lists no file in `src/`.

**If your assistant fails a check or refuses,** keep its attempt on a branch of its own, then take our step code:

```bash
git switch -c assistant-try
git add -A
git commit --allow-empty -m "assistant attempt"
git switch main
git restore --source origin/steps-example -- features/steps/
```

`git switch main` brings back your A2 commit, without the assistant's changes. `git restore --source` puts our
step code in `features/steps/`. Run checks 2 to 4 of `prompts/steps.md` on it. To see what your assistant wrote,
compare its branch with your A2 commit, then read our step code in `features/steps/` beside it:

```bash
git diff main assistant-try -- features/steps/
```

**After A5,** on either path, commit the step code, so that Part C starts from a clean `git status`:

```bash
git add -A
git commit -m "R010 steps"
```

With these steps in place, A4's command shows no error: R010's first example passes too.

## Part B: simulate your own incoming batch

**Goal.** A simulated data set that you can trust: the same command writes the same files, every line matches your
event models, and the truth says what happened, so that a `Then` can state its value before the run. Read
[`docs/simulation-standards.md`](docs/simulation-standards.md) first: these steps check SIM01 of the rides example
against it, then your own.

### B1. Generate SIM01 and check it

```bash
uv run python -m sim.generate
```

What you should see: one line for each of SIM01, SIM02 and SIM03, with its events, deliveries and fault records.
One run's output, for example:

```text
SIM01 rush-hour: 2511 events, 2515 deliveries, 6 fault records (late, twice) -> sim/data/SIM01/
SIM02 quiet-zone: 2331 events, 2331 deliveries, 1 fault records (quiet) -> sim/data/SIM02/
SIM03 double-accept: 60 events, 60 deliveries, 10 fault records (later-first) -> sim/data/SIM03/
```

```bash
uv run python sim/check.py SIM01
```

What you should see: every check line starts with `ok`, and the last two lines are
`OK: SIM01 follows the simulation standards (0 problems)` and a digest. One run's output, for example:

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
the `recount` table: why does `trip_requested` have more lines than truth events? Find the answer in the fault
lines, then check that the `lines` line adds up the same way.

<details>
<summary>Check your answer</summary>

The `twice` line: each of those requests is delivered once more, so `lines` has one extra line for each. The
`lines` check says the same for all deliveries: lines = truth events − `never` + `twice`.

</details>

### B2. Run the generator again: the same files

```bash
uv run python -m sim.generate
uv run python sim/check.py SIM01
```

What you should see: the same output as B1, with the same digest on the last line as your B1 run. The generator
uses one seeded random generator, so it writes the same files each time.

### B3. The Parquet step

```bash
uv run python sim/check.py SIM01 --parquet
```

What you should see, before the `OK` line: a `parquet` line whose row count equals its line count. One run's
output, for example:

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

What you should see: the generator's line, then every check line `ok` and the `OK` line. One run's output, for
example:

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

B5 runs in your team repo, next to this one. Move your terminal there (`cd ../<your team repo>`) and start your
assistant at its root. Part C runs back in this repository.

1. Copy three files from this repository into your team repo: `docs/simulation-standards.md` to `docs/`, and
   `sim/check.py` and `sim/query.py` to `sim/`. On macOS or Linux, from your team repo root:

   ```bash
   mkdir -p docs sim
   cp ../b5-t2-behave-sim/docs/simulation-standards.md docs/
   cp ../b5-t2-behave-sim/sim/check.py ../b5-t2-behave-sim/sim/query.py sim/
   ```

2. Add the two packages. If your team repo root has no `pyproject.toml` yet, run `uv init --bare` there first. Then:

   ```bash
   uv add duckdb pydantic
   ```

3. The prompt reads the section Data of your team's `docs/design.md`, from Checkpoint 1. If your team repo has no
   `docs/design.md`, create it with a heading `## Data` and one line that names your sample file.
4. Open [`prompts/simulate.md`](prompts/simulate.md). Fill in the four lines that start with `Our sample:`,
   `SIM01 shows:`, `Its shape:` and `Faults:` (each placeholder in angle brackets on them), and send the prompt to
   your assistant.
5. When the assistant says it is done, run the check yourself:

   ```bash
   uv run python sim/check.py SIM01
   ```

What you should see: `OK: SIM01 follows the simulation standards (0 problems)` and a digest. Run
`uv run python sim/generate.py` and `uv run python sim/check.py SIM01` a second time: the two digests should be the
same. Then compare SIM01's bullet in your `docs/design.md` with the check's output: its event and delivery totals
with the `recount` table, and its fault counts with the fault lines (`twice`, `never`, `late`, `changed`). They
should be equal.

## Part C: run a scenario on a simulated data set

**Goal.** A scenario that reads a generated folder, with its `Then` values taken from the truth before the run.
Then you break the system and read the failure. This part uses SIM01 of the rides example. Its scenario reuses your
A2 `When`; the `Given` that reads a generated folder and the `Then` for several zones are already in
`features/steps/`.

Back in the tutorial repo root: B5 left your terminal in your team repo, so `cd` back to `b5-t2-behave-sim`.

### C1. The expected values, from the truth

```bash
uv run python sim/query.py SIM01 "
  SELECT pickup_zone_id, count(*) AS trips
  FROM truth
  WHERE event_type = 'trip_requested'
  GROUP BY 1 ORDER BY 1"
```

You should see a table with one row for each of the zones 48, 161 and 230, and the number of trips requested in
it. Write the three numbers in your notes: C2 needs them.

These are the trips requested in each zone, each once, from `_truth/events.jsonl`. The system never reads that
folder.

### C2. Write the scenario and run it

In your editor, create `features/sim01_by_zone.feature` with the text below. In its last line, replace `<n48>`,
`<n161>` and `<n230>` with your three numbers from C1:

```gherkin
Feature: Trips requested in each zone, on our simulated hour
  B5T2 Part C: one scenario that reads the generated folder sim/data/SIM01/. Each Then value was taken from
  sim/data/SIM01/_truth/ with sim/query.py before the run.

  Scenario: Every request of SIM01 counted once
    Given the deliveries of SIM01
    When the counts are read at 2026-11-23T10:11:00Z
    Then zones 48, 161 and 230 show <n48>, <n161> and <n230> trips requested between 09:00 and 10:00
```

`Given the deliveries of SIM01` reads `sim/data/SIM01/trip-events/`, the deliveries in the order received. Run it:

```bash
uv run behave --no-snippets features/sim01_by_zone.feature
```

You should see the scenario passed, with no failed or undefined step.

Now make it wrong on purpose: in the last line, change one of your three numbers by one, and run the same command.
You should see the scenario under `Failing scenarios`, and an `ASSERT FAILED` line that names the zone you changed.
Put the number back, run it again, and check that it passes.

### C3. Break it: turn the duplicate check off

`DEDUPE=off` turns off the line of `src/rides/counting.py` that skips an `event_id` already counted. First list
SIM01's faults, with the zone of each, from the truth:

```bash
uv run python sim/query.py SIM01 "
  SELECT f.fault, f.event_id, t.pickup_zone_id
  FROM faults f JOIN truth t USING (event_id)
  ORDER BY 1, 2"
```

You should see one row for each fault record: its kind (`late` or `twice`), its event and its zone.

**Predict**, in your notes, before you run the next command: with the duplicate check off, which zones' counts go
up, and is each one up by about the number of `twice` faults in that zone?

```bash
DEDUPE=off uv run behave --no-snippets features/sim01_by_zone.feature
```

On Windows PowerShell, run `$env:DEDUPE = 'off'` first, then the same command without `DEDUPE=off`, and
`Remove-Item Env:DEDUPE` after this step.

You should see the scenario under `Failing scenarios`, after an `ASSERT FAILED` line that names a zone, the count
you expected and the count the system gave.

<details>
<summary>Check your prediction</summary>

Each `twice` request is counted once more, so a zone goes up by its number of `twice` rows; a zone without one does
not move. The `late` rows do not change the count: they are received before the counts are read. The failure names
one zone only, because the step stops at the first zone that fails; the fault rows say which other zone would fail
too.

</details>

### C4. Find a planted bug

On Monday and Tuesday, do C4 at home. The branch `bug-late` differs from `main` in one line of
`src/rides/counting.py`. You take only that file from it and find the bug from the failing output, before you read
the line.

First run the rules that use your steps as they are. Rule R020, late requests, has its step code in
`features/steps/count_steps.py` already:

```bash
uv run behave --no-snippets --tags=@R010,@R020,@RF010,@RF020
```

You should see no failed and no errored scenario.

Put in the planted bug and run the same rules again:

```bash
git restore --source origin/bug-late -- src/rides/counting.py
uv run behave --no-snippets --tags=@R010,@R020,@RF010,@RF020
```

You should see some scenarios under `Failing scenarios`, each after its `ASSERT FAILED` line. Find the bug from what
you see, not from the code that changed:

1. Which rule's examples fail, and which rules pass? In `features/js01_trips_per_zone.feature`, compare the
   `event_time` and `received_time` columns of a failing example with those of a passing one.
2. Run one failing example alone, with `--name` and its name in quotes, as in A1.
3. See what the system counted. In `features/steps/count_steps.py`, add `print(context.counts)` as the first line
   of the `Then` that failed (`step_stored`, under `zone {zone:d} has …`). Run that example again with
   `--no-capture` added: behave then shows what the step prints. Which period holds the request: the one of its
   `event_time`, or the one of its `received_time`?
4. In `src/rides/counting.py`, find the line that decides which period a request is counted in.
5. **Predict**, in your notes, before you run it: does your C2 scenario on SIM01 pass or fail with this bug? Use
   SIM01's late requests, from the truth:

   ```bash
   uv run python sim/query.py SIM01 "
     SELECT t.event_id, t.pickup_zone_id,
            strftime(timezone('UTC', t.event_time), '%H:%M:%S') AS event_utc,
            strftime(timezone('UTC', d.received_time), '%H:%M:%S') AS received_utc
     FROM faults f JOIN truth t USING (event_id) JOIN deliveries d USING (event_id)
     WHERE f.fault = 'late'"
   ```

   Then run it:

   ```bash
   uv run behave --no-snippets features/sim01_by_zone.feature
   ```

When you have your answer, see the one line that differs, then take the bug and your `print` out:

```bash
git diff -- src/
git restore src/rides/counting.py features/steps/count_steps.py
git status --short
```

You should see one changed line in the diff. After the restore, `git status --short` lists only your
`features/sim01_by_zone.feature`.

<details>
<summary>Check your answer</summary>

The examples of R020 fail; R010, RF010 and RF020 pass. Every R020 example has a request received in a later period
than its `event_time`; in the examples that pass, each request is received a second after its event, in the same
period. The printed counts hold the late request under the period of its `received_time`. The bug is in
`count_requests`: the key of a count is made with `period_start(d["received_time"])` instead of
`period_start(d["event_time"])`. The C2 scenario still passes: each late request of SIM01 is received in a later
period of the same hour, and the scenario adds up the whole hour. A `Then` for one 5-minute period that holds a late
request would catch it.

</details>

The branch `solution` has the step code of Part A and A5, and the scenario of Part C with its numbers.

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
