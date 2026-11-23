# Prompt: write the generator of your SIM01

Copy the block below into your coding assistant's chat, started in your team repo root. First fill in the four
lines in angle brackets. Leave the folder names in angle brackets of step 2 (`<source>`, `<day>`, `<hour>`) as
they are: the assistant fills them in. Before you send it, copy these three files from the tutorial repo into your
team repo: `docs/simulation-standards.md` to `docs/`, and `sim/check.py` and `sim/query.py` to `sim/`.

```text
Write the generator of our simulated data set SIM01, following docs/simulation-standards.md. Read that file in
full first, then the section Data of docs/design.md.

Our sample: <path of the sample file in this repo, e.g. sim/seed/sample.csv>. It is <what one row is, e.g. one
weather station's reading for one day>. Do not change it. If the repo has no sample yet, stop and ask me.

SIM01 shows: <the requirement IDs and, in a sentence, what the data set is for, e.g. RF010: a reading delivered
twice is stored once>.
Its shape: <one of: a batch of files for each day (lakehouse) / a stream of events with arrival times
(operational) / a set of questions with their answers known (generative AI)>.
Faults: <kinds and counts from the standards, e.g. 3 twice, 2 late>.

Do these steps, in order, and show me what each one wrote:
1. Write events.py in our package under src/ (if src/ has no package yet, make one named after our project):
   one Pydantic model for each event type, extra="forbid", event_type as a Literal, event_time a UTC time.
   List the fields in docs/design.md, Event format, if they are not there yet.
2. Write sim/generate.py. It reads only the sample, uses one random.Random with a fixed seed, imports the models
   of step 1 and validates every event with them, and writes sim/data/SIM01/<source>/dt=<day>/hour=<hour>/
   deliveries.jsonl, sim/data/SIM01/_truth/events.jsonl and sim/data/SIM01/_truth/faults.jsonl, as the standards
   say. It is run as: uv run python sim/generate.py
3. Add or update SIM01's bullet in docs/design.md, section Data: sample, seed, size, time window, faults by kind and
   count, with the counts the generator really wrote.
4. Run uv run python sim/generate.py, then uv run python sim/check.py SIM01. Do not edit sim/check.py. If the check
   prints PROBLEM lines, fix the generator, not the check, and run both again until the last lines are OK and the
   digest.
5. Run both commands a second time and show me that the digest is the same.
Do not add dependencies other than duckdb and pydantic. Do not call AWS or any network service.
```

## What you should see

The assistant shows you `events.py`, `generate.py` and the bullet, then the output of `sim/check.py`, which ends
with:

```text
OK: SIM01 follows the simulation standards (0 problems)
digest <16 characters>
```

and the same digest after the second run. Read the bullet against the check's `recount` table and its fault lines:
the numbers must agree. If they do not, the bullet is wrong, or the generator is.
