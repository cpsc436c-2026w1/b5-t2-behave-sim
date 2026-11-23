# CPSC 436C B5T2: simulation scenarios with behave and simulated data for your project

By the end of this tutorial, you’ll be able to turn a project requirement into a behave scenario that runs against real project code. 
We created infra for tests for you, so you are not dealing with AWS, just creating scenarios and simulated data.

You’ll test one rule of the rides app from the lecture ([EXAMPLE.md](EXAMPLE.md), its Checkpoint 1 submission):
count each trip request once, even if it arrives twice. First you’ll check it on three rows you can count by hand.
Then you’ll run it on a simulated hour of deliveries, with the expected counts taken from the data's ground truth
before the run. Finally, you’ll turn off duplicate checking and see your test catch the wrong count. After the
section, you use the same steps to generate a repeatable batch of simulated data for your own project.

| Part | What you do |
|---|---|
| [A: step code for one rule](#part-a-write-the-step-code-for-one-rule) | write three steps by hand until one example passes; then have your assistant write a second rule's steps and check them |
| [B: simulate an incoming batch](#part-b-simulate-an-incoming-batch-and-check-it) | generate the rides example's SIM01, look at it and check it |
| [B5: your own SIM01](#b5-have-your-assistant-write-your-projects-sim01-then-check-it) (after the section) | your assistant writes the generator of your project's data set; a worked example shows the way first |
| [C: run a scenario on a simulated data set](#part-c-run-a-scenario-on-a-simulated-data-set) | a scenario on SIM01 with its expected value from the truth; break it and read the failure |
| [D: send it to AWS (needs a lease)](#part-d-send-sim01-to-aws-and-read-it-back) | replay SIM01 to S3, read it back, clean up |

| File | What it is |
|---|---|
| [`docs/simulation-standards.md`](docs/simulation-standards.md) | the seven conventions we recommend for simulated data (guidance, not required) |
| [`prompts/simulate.md`](prompts/simulate.md) | the prompt for Part B: your assistant writes your generator |
| [`sim/check.py`](sim/check.py), [`sim/query.py`](sim/query.py) | the check of a data set, and DuckDB questions about it; one file each, to copy to your team repo |
| [`shapes/`](shapes/README.md) | worked examples of Part B for three project shapes: lakehouse, operational, generative AI |
| [`features/`](features/), [`src/rides/`](src/rides/), [`sim/generate.py`](sim/generate.py) | the rides example: features, local code, the generator of SIM01 to SIM03 |

Do the steps under [In the section](#in-the-section) in the tutorial section, in order: each needs only the steps
before it. [After the section](#after-the-section) has the rest, to do at home. Nothing is handed in: what to
take to your project is listed [at the end](#what-to-take-to-your-project).

On the course companion: the [behave guide](https://cpsc436c-2026w1.github.io/lecture-reviews/project-behave.html)
(rules, examples and step functions), the [Checkpoint 1 page](https://cpsc436c-2026w1.github.io/lecture-reviews/project-checkpoint1.html)
(the rides example's requirements and features), and [project datasets](https://cpsc436c-2026w1.github.io/lecture-reviews/project-datasets.html)
(the preview files B5 can use as your sample).

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

4. For A4 and B5 you use your coding assistant (A4 has a fallback without one). For A4, connecting it to the
   course server as in B5T1 is optional. For B5, also have your team repo cloned next to this one, with a small
   sample of your data (your data set's preview file from
   [project datasets](https://cpsc436c-2026w1.github.io/lecture-reviews/project-datasets.html), or about 20 rows) in it.

Every command below runs in the root of this repository, unless a step says your team repo.

## In the section

### Part A: write the step code for one rule

**Goal.** One example of rule RF010 runs against the local code in [`src/rides/counting.py`](src/rides/counting.py).
RF010 says: "the system shall count every trip request exactly once, even when the stream delivers its event
twice". behave runs an example by matching each of its lines to a step function, in Python, in
[`features/steps/`](features/steps/). Three of those functions are missing from this repository: you write them.
In this example, `Given` loads three rows, `When` runs the counting code, and `Then` checks that it counted two
trips: one request appears twice, with the same `event_id`.

#### A1. Run the example: three steps are missing

Run the example before you write any code:

```bash
uv run behave features/js01_trips_per_zone.feature --name "One request delivered twice"
```

What you should see, at the end: the example under `Errored scenarios`, `undefined` in the `steps` line, and one
snippet for each undefined step. `undefined` means that no step function matches the line.

> [!NOTE]
> The run ends with an error (exit status 1) because three steps have no code yet. That is the expected result of
> A1, not a setup problem. Do not paste the snippets: A2 gives you the code.

<details>
<summary>Example output</summary>

One run's output, for example:

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

</details>

<details>
<summary>What happens when you do this step</summary>

The example is in [`features/js01_trips_per_zone.feature`](features/js01_trips_per_zone.feature), under `@RF010`:

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

`--name` runs only the example with that name. The `Given` puts data in front of the system. The `When` makes the
system act. The `Then` compares what the system shows with a number written in the example, before the run.

For each undefined step, behave prints a snippet: the decorator and the text it must match. The snippets are only
skeletons: each one raises `StepNotImplementedError`.

</details>

<details>
<summary>Why this tutorial runs one scenario at a time</summary>

This tutorial always runs one scenario or one tag. A plain `uv run behave` also runs the example's other rules,
whose step code is not written yet. That run ends with failed and errored scenarios, which is expected here.

</details>

#### A2. Implement the three missing steps so the example runs

Paste the code of the three steps into the two step files.

1. In your editor, open [`features/steps/data_steps.py`](features/steps/data_steps.py). Replace the comment that
   starts with `# B5T2 Part A` (all of its lines that start with `#`) with the `Given` below. Each row of the table
   becomes one delivery.

   ```python
   @given("only these trip requests are received:")
   def step_requests_table(context):
       for row in context.table:
           delivery = dict(zip(context.table.headings, row.cells))
           delivery["event_type"] = "trip_requested"
           context.deliveries.append(delivery)
   ```

2. Open [`features/steps/count_steps.py`](features/steps/count_steps.py). Replace its comment that starts with
   `# B5T2 Part A` (all of its `#` lines) with the `When` and the `Then` below.

   ```python
   @when("the counts are read at {time}")
   def step_read(context, time):
       context.counts = count_requests(context.deliveries, read_at=time)


   @then("zone {zone:d} shows {expected:d} trip requested between {start} and {end}")
   @then("zone {zone:d} shows {expected:d} trips requested between {start} and {end}")
   def step_count(context, zone, expected, start, end):
       actual = count_between(context.counts, zone, start_of(start), start_of(end))
       assert actual == expected, (f"{label(zone, start_of(start))}: expected {expected} trips requested, "
                                   f"the system counted {actual}{switch_note()}")
   ```

What you should see: your editor shows no `# B5T2 Part A` comment lines in either file.

<details>
<summary>Why the code looks like this</summary>

`{time}` and `{zone:d}` are parameters: behave passes the text in that place of the line to the function, and `:d`
makes it a number. The `Then` has two decorators so that `1 trip` and `2 trips` both match: the first says
`trip requested`, the second `trips requested`.

`count_requests`, `count_between`, `start_of`, `label` and `switch_note` are already imported or defined in
`count_steps.py`. `count_between` adds up what our code's `show` gives for the zone in each period from `start` up
to `end`: the `Then` uses every value its line names.

</details>

#### A3. Run the example again: it passes

Run the same command as in A1:

```bash
uv run behave features/js01_trips_per_zone.feature --name "One request delivered twice"
```

What you should see: the example passed, with no failed and no undefined step.

<details>
<summary>Example output</summary>

One run's output, for example:

```text
1 feature passed, 0 failed, 0 skipped
1 rule passed, 0 failed, 5 skipped
1 scenario passed, 0 failed, 10 skipped
3 steps passed, 0 failed, 40 skipped
```

</details>

<details>
<summary>If it fails with a NameError</summary>

The `Given` goes in `data_steps.py`, which imports `given`. Pasted into `count_steps.py`, it stops with a
`NameError`. Move it to `data_steps.py` and run the command again.

</details>

#### A4. Ask your assistant for the steps of rule R010, then check them

**Goal.** Your coding assistant writes the step code of a second rule, and you check its work yourself. Rule R010 is
in the same feature: when a 5-minute period ends, the system shall store one count of requested trips for each
pickup zone that had a request in the period ([`docs/requirements.md`](docs/requirements.md)). Its two examples
reuse your A2 steps. One of them already passes with your A2 steps; the other needs two more steps, which your
assistant writes.

> [!TIP]
> No assistant, or it fails? Use the fallback at the end of this step: "If your assistant fails or is not available:
> use our steps".

**First, commit your A2 steps.** They stay on your `main`. Then `git status` and `git diff` show only what your
assistant changes:

```bash
git add -A
git commit -m "my A2 steps"
```

What you should see: a line with `my A2 steps`; `git status` then says `nothing to commit, working tree clean`.

**Then ask your assistant for the step code of rule R010**: the two examples under `@R010` in
[`features/js01_trips_per_zone.feature`](features/js01_trips_per_zone.feature). Start your coding assistant in a
terminal at the root of this repository. Paste the prompt of [`prompts/steps.md`](prompts/steps.md), the text block
under its title, into your assistant. The connection to the course server is optional.

**When the assistant says it is done, check its work.** Run the four checks under "Check what it wrote" in
[`prompts/steps.md`](prompts/steps.md) yourself, in that order. Do not take the assistant's word that the scenarios
pass. What you should see, check by check:

1. `git status --short` lists only files in [`features/steps/`](features/steps/) and, if the assistant changed it,
   [`features/environment.py`](features/environment.py) (that file is already in this repository).
2. The dry run's last lines have `untested` and no `undefined`.
3. Both R010 scenarios pass, none fail.
4. With the boundary bug in, `A request exactly at the end of a period (09:05:00)` is under
   `Failing scenarios`; after `git restore`, `git status --short` lists no file in `src/`.

Then read each `Then` step it wrote, as the end of `prompts/steps.md` says: the expected number comes from the line
of the feature, the actual number from our code.

**After A4, on either path, commit the step code**, so that Part C starts from a clean `git status`:

```bash
git add -A
git commit -m "R010 steps"
```

What you should see: a line with `R010 steps`.

<details>
<summary>Which steps each example of R010 uses</summary>

| Example of rule R010, in `features/js01_trips_per_zone.feature` | Steps it uses |
|---|---|
| A request exactly at the end of a period (09:05:00), line 22 | only steps you already have: your A2 steps and the supplied `shows no data` step (it may pass before you ask) |
| Three requests in one period, line 12 | your A2 table `Given`, plus two new steps: `When the period between … and … ends` and `Then within … s zone … has … trips requested between … and …` |

With these steps in place, A5's command, after the section, shows no error: R010's first example passes too.

</details>

<details>
<summary>If you want to connect your assistant to the course server (optional)</summary>

The assistant can write the steps from this repository alone. Connected, it can also read the course's pages. To
connect it, do as in
[B5T1, Step 1](https://github.com/cpsc436c-2026w1/b5-t1-mcp-evals/blob/main/mcp/README.md#step-1-connect-your-assistant).
This repository has the same example files: `.mcp.json.example` for Claude Code,
[`.kiro/settings/mcp.json.example`](.kiro/settings/mcp.json.example) for Kiro. Your copy of either does not show in
`git status`. If your assistant cannot connect to the course server, run A4 without the server.

</details>

<details>
<summary>If git asks who you are</summary>

Run the two `git config --global` lines it prints, with your name and email, and commit again.

</details>

<details>
<summary>If check 1 lists a file in src/ or a .feature file</summary>

The assistant changed the system or the test. Read and undo the change as check 1 of
[`prompts/steps.md`](prompts/steps.md) says, then go on with check 2.

</details>

<details>
<summary>If your assistant fails or is not available: use our steps</summary>

Take our step code if you have no assistant, or if it does not start, fails check 2, 3 or 4 (after any undo of
check 1), refuses, or is still working when your TA moves the section on. Commit your A2 steps first, as above.

1. Stop the assistant, if it is running: cancel its run (in Claude Code, press Esc). Wait until it shows no
   running command, so that it changes no more files.
2. Keep its attempt on a branch of its own, and take our step code:

   ```bash
   git switch -c assistant-try
   git add -A
   git commit --allow-empty -m "assistant attempt"
   git switch main
   git restore --source origin/steps-example -- features/steps/
   ```

   The first three lines take the assistant's changes, new files included, to the branch `assistant-try` and
   commit them there. `git switch main` brings back your A2 commit, without the assistant's changes.
   `git restore --source` puts our step code in `features/steps/`. `git status --short` now lists those step files
   as changed, and the commit after A4 takes them. If git says your branch is ahead of `origin/main`, that is
   expected: your commits stay on your laptop.
3. Run checks 2 to 4 of `prompts/steps.md` on our step code. Check 1 is not needed: the changed files are ours.
4. To see what your assistant wrote, compare its branch with your A2 commit (with no assistant, the diff is empty).
   Then open our [`features/steps/count_steps.py`](features/steps/count_steps.py) in your editor and compare it with
   the diff:

   ```bash
   git diff main assistant-try -- features/steps/ features/environment.py
   ```

Then commit the step code, as in "After A4" above.

</details>

### Part B: simulate an incoming batch and check it

- **Deliveries**: what the system receives, in the order it arrives, repeats and late arrivals included.
- **Truth** (`_truth/`): the generator's answer key: each event once, as it happened, and the faults it injected.
  You compute the expected result from the truth before you run anything; the system never reads it.

**Goal.** A simulated data set that you can trust: the same command writes the same files, every line matches your
event models, and the truth says what happened, so that a `Then` can state its value before the run. In the section
you look at SIM01 of the rides example, the data set of Part C, and check it. Your own project's data set comes
after the section, in [B5](#b5-have-your-assistant-write-your-projects-sim01-then-check-it), which starts with a
worked example on another project's data.

#### B1. Generate SIM01, read its files, and check it

Generate the rides example's data sets:

```bash
uv run python -m sim.generate
```

What you should see: one line for each of SIM01, SIM02 and SIM03, with its events, deliveries and fault records.

<details>
<summary>Example output</summary>

One run's output, for example:

```text
SIM01 rush-hour: 2511 events, 2515 deliveries, 6 fault records (late, twice) -> sim/data/SIM01/
SIM02 quiet-zone: 2331 events, 2331 deliveries, 1 fault records (quiet) -> sim/data/SIM02/
SIM03 double-accept: 60 events, 60 deliveries, 10 fault records (later-first) -> sim/data/SIM03/
```

</details>

Now look at SIM01 in your editor, one idea at a time.

1. **The bullet.** In [`docs/design.md`](docs/design.md), section Data, read the bullet **SIM01 Rush hour**. What
   you should see: its events and deliveries are the numbers on the generator's SIM01 line, and its faults by kind
   add up to that line's fault records.
2. **What the system receives, and what happened.** Open
   `sim/data/SIM01/trip-events/dt=2026-11-23/hour=09/deliveries.jsonl` and `sim/data/SIM01/_truth/events.jsonl`,
   and compare their first lines. What you should see: the same `event_id` with the same fields, and the delivery
   has one field more, `received_time`, at or after its `event_time`.
3. **The faults.** Open `sim/data/SIM01/_truth/faults.jsonl`. There are four kinds of fault:
   - `twice`: the event is delivered one more time.
   - `late`: the event takes longer to arrive than any event not marked `late`.
   - `never`: the event is in the truth and is not delivered.
   - `changed`: a delivery differs from the truth in one field.

   What you should see: one line for each fault, its kind (`fault`) and its `event_id`; SIM01 has only `twice` and
   `late` lines, as many of each as the bullet says.
4. **The model.** Open [`src/rides/events.py`](src/rides/events.py) and read the class `TripRequested` and the class
   `Event` it extends. What you should see: the fields of `Event` and `TripRequested` are the fields of the truth
   line you opened in 2.

<details>
<summary>Why look at these four files</summary>

1. The design says what a data set holds before it is made: the sample it comes from, the seed, the size and the
   faults by kind and count.
2. The two first lines are the same event, as the system receives it and as it happened. The folders `dt=` and
   `hour=` are the day and hour of `received_time`.
3. Each fault the generator put in is written down with the event it is about, so a `Then` can count with it.
4. There is one Pydantic model for each event type, shared: the generator checks every event against it before it
   writes a file, and the check below validates every line against it. So a wrong field stops the generator before
   it reaches the system.

</details>

Then check the whole data set:

```bash
uv run python sim/check.py SIM01
```

What you should see: every check line starts with `ok`, and the last two lines are
`OK: SIM01 follows the simulation standards (0 problems)` and a digest.

Read the `recount` table: why does `trip_requested` have more lines than truth events? Find the answer in the fault
lines, then check that the `lines` line adds up the same way.

<details>
<summary>Example output</summary>

Every `ok` line is one check of the standards; a check that fails prints `PROBLEM` and the lines that break it. One
run's output, for example:

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

</details>

<details>
<summary>Check your answer</summary>

The `twice` line: each of those requests is delivered once more, so `lines` has one extra line for each. The
`lines` check says the same for all deliveries: lines = truth events − `never` + `twice`.

</details>

#### B2. Generate SIM01 again: the digest is the same

Run the generator and the check a second time:

```bash
uv run python -m sim.generate
uv run python sim/check.py SIM01
```

What you should see: the same output as B1, with the same digest on the last line as your B1 run.

[`docs/simulation-standards.md`](docs/simulation-standards.md) sums up what you just saw on SIM01 (the models, the
two folders, the bullet and its faults, the seed) as seven conventions, for your own data set in B5.

<details>
<summary>Why the digest is the same</summary>

The generator uses one seeded random generator (the seed is in the bullet), so it writes the same files each time.

</details>

### Part C: run a scenario on a simulated data set

**Goal.** A scenario that reads a generated folder, with its `Then` values taken from the truth before the run.
Then you break the system and read the failure. Its scenario reuses your A2 `When`. Part C runs in the tutorial repo
root: your terminal is still there.

<details>
<summary>Which steps Part C uses</summary>

This part uses SIM01 of the rides example. Its scenario reuses your A2 `When`. The `Given` that reads a generated
folder and the `Then` for several zones are already in [`features/steps/`](features/steps/).

</details>

#### C1. Count each zone's trips in the truth: these are your expected values

Count the trips requested in each zone, from the truth:

```bash
uv run python sim/query.py SIM01 "
  SELECT pickup_zone_id, count(*) AS trips
  FROM truth
  WHERE event_type = 'trip_requested'
  GROUP BY 1 ORDER BY 1"
```

What you should see: a table with one row for each of the zones 48, 161 and 230, and the number of trips requested
in it. Write the three numbers in your notes: C2 needs them.

<details>
<summary>Why these numbers are the expected values</summary>

These are the trips requested in each zone, each once, from `_truth/events.jsonl`. The system never reads that
folder.

</details>

#### C2. Write a scenario with those values and run it

In your editor, create `features/sim01_by_zone.feature` with the text below. In its last line, replace `<n48>`,
`<n161>` and `<n230>` with your three numbers from C1:

```gherkin
Feature: Trips requested in each zone, on our simulated hour
  B5T2 Part C: one scenario that reads the generated folder sim/data/SIM01/. Each Then value was taken from
  sim/data/SIM01/_truth/ with sim/query.py before the run.

  Scenario: The deliveries of SIM01
    Given the deliveries of SIM01
    When the counts are read at 2026-11-23T10:11:00Z
    Then zones 48, 161 and 230 show <n48>, <n161> and <n230> trips requested between 09:00 and 10:00
```

Run it:

```bash
uv run behave --no-snippets features/sim01_by_zone.feature
```

What you should see: the scenario passed, with no failed or undefined step.

Now make it wrong on purpose. In the last line, change one of your three numbers (any one) by one, and run the same
command. What you should see: the scenario under `Failing scenarios`, and an `ASSERT FAILED` line that names the zone
you changed. Put the number back, run it again, and check that it passes.

> [!NOTE]
> Do not commit the new feature file: C3 runs it (and C4, after the section). `git status --short` lists it as `??`,
> which is expected.

<details>
<summary>What the Given reads</summary>

`Given the deliveries of SIM01` reads `sim/data/SIM01/trip-events/`, the deliveries in the order received.

</details>

#### C3. Turn off the duplicate check: the scenario fails

`DEDUPE=off` turns off the line of [`src/rides/counting.py`](src/rides/counting.py) that skips an `event_id` already
counted. First list SIM01's faults, with the zone of each, from the truth:

```bash
uv run python sim/query.py SIM01 "
  SELECT f.fault, f.event_id, t.pickup_zone_id
  FROM faults f JOIN truth t USING (event_id)
  ORDER BY 1, 2"
```

What you should see: one row for each fault record, with its kind (`late` or `twice`), its event and its zone.

**Predict**, in your notes, before you run the next command: with the duplicate check off, which zones' counts
change, up or down, and which fault rows explain each change?

On Windows PowerShell, open "If you use Windows PowerShell" below before you run the command.

```bash
DEDUPE=off uv run behave --no-snippets features/sim01_by_zone.feature
```

What you should see: the scenario under `Failing scenarios`, after an `ASSERT FAILED` line that names a zone, the
count you expected and the count the system gave.

<details>
<summary>If you use Windows PowerShell</summary>

Run `$env:DEDUPE = 'off'` first, then the same command without `DEDUPE=off`. Run `Remove-Item Env:DEDUPE` after
this step.

</details>

<details>
<summary>Check your prediction</summary>

Each `twice` request is counted once more, so a zone goes up by its number of `twice` rows; a zone without one does
not move. The `late` rows do not change the count: they are received before the counts are read. The failure names
one zone only, because the step stops at the first zone that fails; the fault rows say which other zone would fail
too.

</details>

## After the section

### A5. Run every example that uses your steps: all pass

Run every example of R010, RF010 and RF020:

```bash
uv run behave --no-snippets --tags=@R010,@RF010,@RF020
```

What you should see, with the A4 steps committed: no failed and no errored scenario, every example passed.

<details>
<summary>Example output</summary>

One run's output, for example:

```text
1 feature passed, 0 failed, 4 skipped
3 rules passed, 0 failed, 11 skipped
6 scenarios passed, 0 failed, 18 skipped
24 steps passed, 0 failed, 67 skipped
```

</details>

<details>
<summary>Why the same steps serve every example</summary>

The same three steps of A2 serve every example of R010, RF010 and RF020 written with a table. The `When` and `Then`
you wrote also serve the two examples that read a simulated data set. Their `Given` (`Given the simulated data set
SIM01 "rush-hour"` and `… SIM02 "quiet-zone"`) is already in
[`features/steps/data_steps.py`](features/steps/data_steps.py).

</details>

<details>
<summary>If "Three requests in one period" is under Errored scenarios</summary>

If R010's first example, "Three requests in one period", is under `Errored scenarios`, its `When the period … ends`
and `Then within 60 s …` have no step code: they are the steps of A4.

</details>

### B3. Write SIM01 as Parquet: rows equal lines

Run the check with the Parquet step:

```bash
uv run python sim/check.py SIM01 --parquet
```

What you should see, before the `OK` line: a `parquet` line whose row count equals its line count.

<details>
<summary>Example output</summary>

One run's output, for example:

```text
ok   parquet: sim/parquet/SIM01/trip-events.parquet 2515 rows = 2515 lines
```

</details>

<details>
<summary>What the Parquet step does</summary>

DuckDB reads the JSON Lines and writes one Parquet file for each source, then counts the rows of the file. The
JSON Lines stay as they are: Parquet is a separate step.

</details>

### B4. Generate and check the shape nearest your project

Pick the shape folder nearest your project ([`shapes/`](shapes/README.md)):

- `lakehouse`: a batch of files for each day.
- `operational`: a stream of events with arrival times.
- `genai`: questions with their answers known.

Read its README ([`lakehouse`](shapes/lakehouse/README.md), [`operational`](shapes/operational/README.md),
[`genai`](shapes/genai/README.md)) and its `generate.py`. Then run it. For the lakehouse shape:

```bash
uv run python shapes/lakehouse/generate.py
uv run python sim/check.py SIM01 --root shapes/lakehouse
```

For another shape, put `operational` or `genai` in place of `lakehouse` in both lines.

What you should see, for any shape: the generator's line, then every check line `ok` and the `OK` line.

<details>
<summary>Example output</summary>

One run's output for the lakehouse shape, for example:

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

</details>

### B5. Have your assistant write your project's SIM01, then check it

**Goal.** Your assistant writes the generator of your project's SIM01, in your team repo, and you check it. First, a
worked example in this repository fills in the prompt for another project: the lakehouse shape of B4 (weather
stations, one batch file a night), from one requirement to the expected result of its scenario.

**The four lines of the prompt** ([`prompts/simulate.md`](prompts/simulate.md)), filled in for the worked example:

| Line | Filled in |
|---|---|
| `Our sample:` | `shapes/lakehouse/sample/ghcn_daily_sample.csv`. It is one weather station's reading of one element (TMAX, TMIN or PRCP) for one day. |
| `SIM01 shows:` | R500: when a batch file sends a reading that an earlier batch file already sent, the system shall store the reading once. |
| `Its shape:` | a batch of files for each day (lakehouse) |
| `Faults:` | 3 twice |

<details>
<summary>Worked example, step by step: requirement, sample, fault, expected result, scenario</summary>

Run `uv run python shapes/lakehouse/generate.py` first, unless you ran the lakehouse shape in B4.

1. **Requirement**, written as in Checkpoint 1 (the IDs are the weather team's, not the rides example's):
   **R500** WHEN a batch file sends a reading that an earlier batch file already sent THE SYSTEM SHALL store the
   reading once.
2. **Sample**: [`shapes/lakehouse/sample/ghcn_daily_sample.csv`](shapes/lakehouse/sample/ghcn_daily_sample.csv). One
   row is one weather station's reading of one element (TMAX, TMIN or PRCP) for one day.
3. **Fault** that the requirement is about: `twice`: 3 readings, each sent again in the next batch file (the seed
   fixes the count, as the shape's README says). The shape's SIM01 also has `late`, `never` and `changed` faults,
   for its other requirements.
4. **Expected result**, from the truth, before any run: the readings stored for each station. A `never` reading is
   not delivered, so the system cannot store it: the query leaves it out.

   ```bash
   uv run python sim/query.py SIM01 --root shapes/lakehouse "
     SELECT t.station_id, count(*) AS readings, count(f.fault) AS sent_twice
     FROM truth t LEFT JOIN faults f ON f.event_id = t.event_id AND f.fault = 'twice'
     WHERE t.event_id NOT IN (SELECT event_id FROM faults WHERE fault = 'never')
     GROUP BY 1 ORDER BY 1"
   ```

   What you should see: one row for each station of the sample; the `sent_twice` values add up to the 3 `twice`
   faults. A system that stores a reading again when it is sent twice shows `readings` + `sent_twice` for that
   station, more than `readings`.
5. **Scenario** it becomes, with any one station whose `sent_twice` is above 0 in place of `<station>`, and its
   `readings` in place of `<n>`:

   ```gherkin
   Scenario: The batch files of SIM01
     Given the deliveries of SIM01
     When every batch file of SIM01 is loaded
     Then station <station> has <n> readings stored
   ```

   This repository has no lakehouse system and no step code for these lines, so you do not run this scenario here.
   In a team repo, it runs like C2, with the three steps that "What to take to your project" describes.

</details>

For your project, do the same with one of your Checkpoint 1 requirements: fill in the same four lines, as the
worked example's callout shows step by step.

<details>
<summary>If your data set has more than one event type</summary>

Add `AND t.event_type = '<your type>'` at the end of the `WHERE` line of the query of item 4.

</details>

**Then SIM01 for your project, in your team repo.** The rest of B5 runs in your team repo, next to this one. Move
your terminal there (`cd ../<your team repo>`) and start your assistant at its root. C4 runs back in this repository.

1. Copy three files from this repository into your team repo: [`docs/simulation-standards.md`](docs/simulation-standards.md)
   to [`docs/`](docs/), and [`sim/check.py`](sim/check.py) and [`sim/query.py`](sim/query.py) to [`sim/`](sim/). On macOS or Linux,
   from your team repo root:

   ```bash
   mkdir -p docs sim
   cp ../b5-t2-behave-sim/docs/simulation-standards.md docs/
   cp ../b5-t2-behave-sim/sim/check.py ../b5-t2-behave-sim/sim/query.py sim/
   ```

2. Add the two packages. If your team repo root has no [`pyproject.toml`](pyproject.toml) yet, run `uv init --bare` there first. Then:

   ```bash
   uv add duckdb pydantic
   ```

3. The prompt reads the section Data of your team's [`docs/design.md`](docs/design.md), from Checkpoint 1. If `docs/design.md` does
   not exist, create it. If it has no `## Data` section, add one, with a line that names your sample file (for
   example `Our sample: data/preview.csv, 20 rows of our data set.`). A new file with only these two lines is
   enough:

   ```markdown
   ## Data

   Our sample: data/preview.csv, 20 rows of our data set.
   ```

4. Open [`prompts/simulate.md`](prompts/simulate.md) and copy its text block into your assistant's chat; do not edit
   the file itself. In the chat, fill in the four lines that start with `Our sample:`, `SIM01 shows:`, `Its shape:`
   and `Faults:`, as the worked example's table does: replace each placeholder, its angle brackets and the `e.g.`
   example inside them included, with your own project's words. The `Our sample:` line has two: the path, and what
   one row is. For `SIM01 shows:`, the requirement of your worked example is enough; add another requirement only if
   you want its fault in the same data set. For `Faults:`, the kinds those requirements need, from the four kinds of
   the standards, with 2 or 3 of each. Send the prompt to your assistant.
5. When the assistant says it is done, run the check yourself:

   ```bash
   uv run python sim/check.py SIM01
   ```

What you should see: `OK: SIM01 follows the simulation standards (0 problems)` and a digest. Run
`uv run python sim/generate.py` and `uv run python sim/check.py SIM01` a second time: the two digests should be the
same. Then compare SIM01's bullet in your `docs/design.md` with the check's output: its event and delivery totals
with the `recount` table, and its fault counts with the fault lines (`twice`, `never`, `late`, `changed`; a kind
that the bullet does not name counts as 0, and its fault line says `none`). They should be equal.

<details>
<summary>If the check stops with "FAILED: expected one src/&lt;package&gt;/events.py"</summary>

If the check stops with `FAILED: expected one src/<package>/events.py, found 2` (or a larger number), your team repo
has more than one package with an `events.py`. Name the one with SIM01's models: add
`--events src/<package>/events.py` to every `sim/check.py` command of this step, with your package's folder name in
place of `<package>` (for a package `retail`: `uv run python sim/check.py SIM01 --events src/retail/events.py`). If
it says `found 0`, there is no model file yet: ask your assistant to do step 1 of the prompt (`events.py` in your
package under `src/`). `--events` only names a file that exists.

</details>

The new files belong to your team repo. Commit them there, from its root:

```bash
printf '\n__pycache__/\n.venv/\nsim/data/\n' >> .gitignore
git status --short
git add -A
git commit -m "SIM01 generator and check"
```

What you should see: `git status --short` lists `.gitignore`, the three files you copied, `pyproject.toml` and
`uv.lock` if they are new, and the assistant's files in [`src/`](src/), `sim/` (not `sim/data/`) and `docs/`.

<details>
<summary>Why the first line</summary>

The first line keeps Python's cache folders and the generated data out of the commit: [`sim/generate.py`](sim/generate.py) writes the
data again, the same each time.

</details>

<details>
<summary>If you use Windows</summary>

Instead of the `printf` line, add the lines `__pycache__/`, `.venv/` and `sim/data/` to `.gitignore` in your editor.

</details>

<details>
<summary>If your team works on branches with pull requests</summary>

Run `git switch -c sim01` before `git add`, then push the branch and open a pull request.

</details>

### C4. Find a planted bug from the failing scenarios

C4 runs in the tutorial repo root: if you did B5 just before, run `cd ../b5-t2-behave-sim` first. The branch
`bug-late` differs from `main` in one line of [`src/rides/counting.py`](src/rides/counting.py). You take only that
file from it and find the bug from the failing output, before you read the line.

First run the rules that use your steps as they are. Rule R020, late requests, has its step code in
[`features/steps/count_steps.py`](features/steps/count_steps.py) already:

```bash
uv run behave --no-snippets --tags=@R010,@R020,@RF010,@RF020
```

What you should see: no failed and no errored scenario.

Put in the planted bug and run the same rules again:

```bash
git restore --source origin/bug-late -- src/rides/counting.py
uv run behave --no-snippets --tags=@R010,@R020,@RF010,@RF020
```

What you should see: some scenarios under `Failing scenarios`, each after its `ASSERT FAILED` line. Find the bug
from what you see, not from the code that changed:

1. Every request has two times: `event_time`, when it happened, and `received_time`, when it reached the system. A
   request that happened at 09:04 and arrived at 09:11 is not seen by a read at 09:10; once it arrives, it belongs
   to the 09:00–09:05 period. Which rule's examples fail, and which rules pass? In
   [`features/js01_trips_per_zone.feature`](features/js01_trips_per_zone.feature), compare the `event_time` and
   `received_time` columns of a failing example with those of a passing one (any of each).
2. Run one failing example alone (any one of them), with its name in the quotes:

   ```bash
   uv run behave --no-snippets --name "<its name>"
   ```
3. See what the system counted. In `features/steps/count_steps.py`, find the `Then` that failed: `def
   step_stored`, under the two decorators `zone {zone:d} has …`. Add `print(context.counts)` as the first line of
   its body, right below the `def` line and indented like the line under it. Run that example again with
   `--no-capture` added:

   ```bash
   uv run behave --no-snippets --no-capture --name "<its name>"
   ```

   behave then shows what the step prints: a line that starts with `{`, right below the `Then` line of the example
   and above its `ASSERT FAILED` line. Which period holds the request: the one of its `event_time`, or the one of
   its `received_time`?
4. In `src/rides/counting.py`, read `count_requests` and find the line that decides which period a request is
   counted in.
5. Run the query below, then **predict**, in your notes, before you run the scenario: does your C2 scenario on
   SIM01 pass or fail with this bug? Ask yourself: if a request moves from one 5-minute period to another within the
   same hour, does the hour's total change? Decide from the times of SIM01's late requests, in the truth:

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

What you should see: one changed line in the diff. After the restore, `git status --short` lists only your
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

The branch `solution` has the step code of A2 and A4, and the scenario of Part C with its numbers.

### Part D: send SIM01 to AWS and read it back

**Goal.** The rides SIM01 you made in B1 arrives in AWS in the order it was received. This part needs your team's
AWS lease; Parts A to C need no AWS.

The course recipe [`simulated-runs`](https://github.com/cpsc436c-2026w1/recipes/tree/main/simulated-runs) has the
replayer. Clone it next to this repository and try the replay on your laptop first; it calls no AWS service:

```bash
git clone https://github.com/cpsc436c-2026w1/recipes ../recipes
cd ../recipes/simulated-runs
uv sync
uv run python sim/replay.py SIM01 --run-id b5t2-try1 \
  --to local --target replay:discard \
  --data-dir ../../b5-t2-behave-sim/sim/data
```

**What you should see:** a last line ending in `2515 sent, 0 failed`: every delivery line of SIM01 was sent, in the
order received.

<details><summary>Send it to AWS, read it back, clean up</summary>

With your lease's credentials active, follow the recipe's
[Replay your own SIM01](https://github.com/cpsc436c-2026w1/recipes/tree/main/simulated-runs#replay-your-own-sim01)
section: the same command with `--to s3 --target <your bucket>` (or `--to kinesis --target <your stream>` for a
streaming project). Read the objects back with Athena or DuckDB and compare the count with `sim/check.py`'s recount
of SIM01: they should be equal. Then run the recipe's clean-up as its README says: a plain run lists what it would
delete, `--yes` deletes. The recipe's README gives the costs.

</details>

## What to take to your project

- One step file of your own for one rule of your features, written like A2.
- Your SIM01: `src/<package>/events.py`, [`sim/generate.py`](sim/generate.py) and its bullet in [`docs/design.md`](docs/design.md). If your team follows
  the simulation standards (they are guidance, not required), also [`sim/check.py`](sim/check.py) printing `OK`.
- One scenario like C2, with its `Then` values taken from your truth with [`sim/query.py`](sim/query.py). To run it on your own
  deliveries, write the three steps in your team repo, as you did in A2: a `Given` that reads every
  `deliveries.jsonl` under your `sim/data/SIM01/`, in the order of their `received_time`, and not `_truth/` (the tutorial's
  `Given the deliveries of SIM01`, in [`features/steps/data_steps.py`](features/steps/data_steps.py), reads only the rides data); a `When` that runs
  your code on them (if your team has no code for it yet, the scenario waits for that code); a `Then` that compares
  what your code gives with the number from your truth. Then run it with
  `uv run behave --no-snippets features/<your feature file>` (run `uv add behave` first if your team repo's
  [`pyproject.toml`](pyproject.toml) does not list behave).
