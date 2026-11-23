"""Check one simulated data set against the simulation standards (docs/simulation-standards.md).

    uv run python sim/check.py SIM01                          # validate every line, recount the truth
    uv run python sim/check.py SIM01 --parquet                # and write Parquet with DuckDB, with its row-count check
    uv run python sim/check.py SIM01 --root shapes/lakehouse  # a shape folder: its events.py, data/ and parquet/

One file, no import from this repository: copy it to `sim/check.py` of your team repo and run it there. It needs
`duckdb` and `pydantic` (`uv add duckdb pydantic`). What it reads, by default from the repository root:

    src/<package>/events.py      the Pydantic models, one per event type (found by their `event_type` Literal)
    sim/data/<SIM>/<source>/dt=<day>/hour=<hour>/deliveries.jsonl   what the system receives
    sim/data/<SIM>/_truth/events.jsonl                               each event once
    sim/data/<SIM>/_truth/faults.jsonl                               each injected fault
    sim/data/<SIM>/_truth/answers.jsonl                              optional: expected answers, one per event_id

What it checks, and the fault kinds it recounts (other kinds are listed, not checked):

    validate   every delivery line is a model plus `received_time`; every truth line is a model; times are UTC
    folders    every delivery is in the dt=/hour= folder of its received_time
    truth      each event_id once in _truth/events.jsonl; every delivered event_id is in the truth
    twice      the event is delivered one more time for each `twice` record
    never      the event is in the truth and is not delivered
    late       the event's delay (event_time to first delivery) is longer than every event not marked late
    changed    a delivery of the event differs from the truth in the record's `field`; no other delivery differs
    lines      delivery lines = truth events - never + twice
    parquet    (with --parquet) sim/parquet/<SIM>/<source>.parquet has as many rows as its JSON Lines

Exit code 0 when there is no problem, 1 otherwise. The last line is a digest of the data set's files: run the
generator twice, and the digest is the same both times when the generator is deterministic.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import typing
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import duckdb
from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parent.parent
CHECKED = ("twice", "never", "late", "changed")
SHOW = 5                                   # problems shown for each check; the count is always given


def load_models(path: Path) -> dict[str, type[BaseModel]]:
    """Every Pydantic model in the file whose `event_type` field is a Literal of one value, by that value."""
    spec = importlib.util.spec_from_file_location("events_under_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    models = {}
    for obj in vars(module).values():
        if isinstance(obj, type) and issubclass(obj, BaseModel) and "event_type" in obj.model_fields:
            values = typing.get_args(obj.model_fields["event_type"].annotation)
            if len(values) == 1:
                models[values[0]] = obj
    return models


def find_events_file() -> Path:
    found = sorted(ROOT.glob("src/*/events.py"))
    if len(found) != 1:
        sys.exit(f"FAILED: expected one src/<package>/events.py, found {len(found)}; name the file with --events")
    return found[0]


def utc(value) -> datetime | None:
    """A UTC time written as 2026-11-23T09:00:00Z (or +00:00), else None."""
    try:
        t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.utcoffset() is not None and t.utcoffset().total_seconds() == 0 else None


def read_jsonl(path: Path, problems: list) -> list[dict]:
    rows = []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            problems.append(f"{path}:{n}: not JSON ({e.msg})")
    return rows


class Report:
    def __init__(self):
        self.problems = 0

    def check(self, name: str, problems: list[str], ok_text: str):
        if problems:
            self.problems += len(problems)
            print(f"PROBLEM {name}: {len(problems)}")
            for p in problems[:SHOW]:
                print(f"  {p}")
            if len(problems) > SHOW:
                print(f"  ... and {len(problems) - SHOW} more")
        else:
            print(f"ok   {name}: {ok_text}")


def digest(folder: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        h.update(str(path.relative_to(folder)).encode() + b"\0" + path.read_bytes())
    return h.hexdigest()[:16]


def pl(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def dur(seconds: float) -> str:
    """391 s as '391 s', 6000 s as '100 min', 108000 s as '30 h'."""
    if seconds < 600:
        return f"{seconds:.0f} s"
    return f"{seconds / 60:.0f} min" if seconds < 3 * 3600 else f"{seconds / 3600:.0f} h"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("sim_id", help="the data set's id, e.g. SIM01")
    ap.add_argument("--root", type=Path, help="a folder with events.py, data/ and parquet/ (a shape folder)")
    ap.add_argument("--events", type=Path, help="the file with the Pydantic models (default src/<package>/events.py)")
    ap.add_argument("--data", type=Path, help="the folder that holds <SIM>/ (default sim/data)")
    ap.add_argument("--parquet", action="store_true", help="also write Parquet with DuckDB and check its row count")
    args = ap.parse_args()

    events_file = args.events or (args.root / "events.py" if args.root else find_events_file())
    data = args.data or (args.root / "data" if args.root else ROOT / "sim" / "data")
    parquet_dir = (args.root / "parquet" if args.root else ROOT / "sim" / "parquet") / args.sim_id
    folder = data / args.sim_id
    if not (folder / "_truth" / "events.jsonl").exists():
        sys.exit(f"FAILED: {rel(folder)}/_truth/events.jsonl not found: run your generator first")
    models = load_models(events_file)
    if not models:
        sys.exit(f"FAILED: no Pydantic model with an `event_type` Literal in {rel(events_file)}")
    print(f"{args.sim_id}: {rel(folder)}/ (models in {rel(events_file)}: {', '.join(sorted(models))})")
    report = Report()

    # Folders: every folder of the data set except _truth is a source.
    sources = sorted(p.name for p in folder.iterdir() if p.is_dir() and not p.name.startswith("_"))
    files = {s: sorted((folder / s).glob("dt=*/hour=*/deliveries.jsonl")) for s in sources}
    stray = [rel(p) for s in sources for p in (folder / s).rglob("*") if p.is_file() and p not in files[s]]
    parse_problems, deliveries = [], []    # (source, path, line number, row)
    for s in sources:
        for path in files[s]:
            for n, row in enumerate(read_jsonl(path, parse_problems), 1):
                deliveries.append((s, path, n, row))
    truth = read_jsonl(folder / "_truth" / "events.jsonl", parse_problems)
    faults_path = folder / "_truth" / "faults.jsonl"
    faults = read_jsonl(faults_path, parse_problems) if faults_path.exists() else []
    report.check("JSON", parse_problems, "every line is one JSON object")

    folder_problems = [f"{rel(folder)}/: no source folder with dt=<day>/hour=<hour>/deliveries.jsonl"] if not deliveries else []
    folder_problems += [f"{p}: not dt=<day>/hour=<hour>/deliveries.jsonl" for p in stray]
    for s, path, n, row in deliveries:
        t = utc(row.get("received_time"))
        day, hour = path.parts[-3].removeprefix("dt="), path.parts[-2].removeprefix("hour=")
        if t is not None and (f"{t:%Y-%m-%d}", f"{t:%H}") != (day, hour):
            folder_problems.append(f"{rel(path)}:{n}: received_time {row['received_time']} is not in dt={day}/hour={hour}")
    n_files = sum(len(f) for f in files.values())
    report.check("folders", folder_problems,
                 f"{pl(len(sources), 'source')} ({', '.join(sources)}), {pl(n_files, 'file')}, every line in the folder of its received_time")

    # Validate: each line against the model of its event_type.
    def validate(row: dict, where: str, delivered: bool) -> str | None:
        event = dict(row)
        if delivered:
            if "received_time" not in event:
                return f"{where}: no received_time"
            if utc(event.pop("received_time")) is None:
                return f"{where}: received_time {row['received_time']!r} is not a UTC time like 2026-11-23T09:00:00Z"
        model = models.get(event.get("event_type"))
        if model is None:
            return f"{where}: event_type {event.get('event_type')!r} has no model in {events_file.name}"
        try:
            model.model_validate(event)
        except ValidationError as e:
            err = e.errors()[0]
            return f"{where}: {'.'.join(map(str, err['loc'])) or 'line'}: {err['msg']}"
        if utc(event.get("event_time")) is None:
            return f"{where}: event_time {event.get('event_time')!r} is not a UTC time like 2026-11-23T09:00:00Z"
        return None

    invalid = [p for s, path, n, row in deliveries if (p := validate(row, f"{rel(path)}:{n}", True))]
    invalid += [p for n, row in enumerate(truth, 1) if (p := validate(row, f"_truth/events.jsonl:{n}", False))]
    report.check("validate", invalid,
                 f"{len(deliveries)} delivery lines and {len(truth)} truth events match their models")

    # Truth: each event once; every delivered event is in it; every fault names a real event.
    truth_ids = Counter(e.get("event_id") for e in truth)
    by_id = {e.get("event_id"): e for e in truth}
    truth_problems = [f"_truth/events.jsonl: {i} is there {n} times" for i, n in truth_ids.items() if n > 1]
    truth_problems += sorted({f"{rel(path)}:{n}: {row.get('event_id')} is not in _truth/events.jsonl"
                              for s, path, n, row in deliveries if row.get("event_id") not in by_id})
    kinds = Counter(f.get("fault") for f in faults)
    for n, f in enumerate(faults, 1):
        if f.get("fault") in CHECKED and f.get("event_id") not in by_id:
            truth_problems.append(f"_truth/faults.jsonl:{n}: {f.get('fault')} names {f.get('event_id')!r}, not in the truth")
        if f.get("fault") == "changed" and not f.get("field"):
            truth_problems.append(f"_truth/faults.jsonl:{n}: a changed record needs the field that changed")
    answers_path = folder / "_truth" / "answers.jsonl"
    answers_note = ""
    if answers_path.exists():
        answers = read_jsonl(answers_path, truth_problems)
        answer_ids = Counter(a.get("event_id") for a in answers)
        truth_problems += [f"_truth/answers.jsonl: {i} is not in _truth/events.jsonl" for i in answer_ids if i not in by_id]
        truth_problems += [f"_truth/answers.jsonl: {i} has {n} answers" for i, n in answer_ids.items() if n > 1]
        answers_note = f"; {len(answers)} expected answers, each for one event"
    report.check("truth", truth_problems, f"each of {len(truth)} event_ids once, every delivery is in it{answers_note}")

    # Recount with DuckDB: truth and delivery lines by event type, and deliveries per event_id.
    db = duckdb.connect()
    cols = {"event_id": "VARCHAR", "event_type": "VARCHAR", "event_time": "VARCHAR", "received_time": "VARCHAR"}
    db.execute("CREATE TABLE truth AS SELECT * FROM read_json(?, format='newline_delimited', columns=?)",
               [str(folder / "_truth" / "events.jsonl"), {k: v for k, v in cols.items() if k != "received_time"}])
    db.execute("CREATE TABLE deliveries AS SELECT * FROM read_json(?, format='newline_delimited', columns=?)",
               [[str(p) for s in sources for p in files[s]], cols])
    db.execute("CREATE TABLE faults (fault VARCHAR, event_id VARCHAR)")
    db.executemany("INSERT INTO faults VALUES (?, ?)", [(f.get("fault"), f.get("event_id")) for f in faults])
    print("recount (DuckDB):")
    print(f"  {'event_type':<24}{'truth':>8}{'lines':>8}")
    for event_type, t, d in db.sql("""
            SELECT coalesce(t.event_type, d.event_type), coalesce(t.n, 0), coalesce(d.n, 0)
            FROM (SELECT event_type, count(*) n FROM truth GROUP BY 1) t
            FULL JOIN (SELECT event_type, count(*) n FROM deliveries GROUP BY 1) d USING (event_type)
            ORDER BY 1""").fetchall():
        print(f"  {event_type:<24}{t:>8}{d:>8}")

    # twice and never: deliveries of each event = (0 if never else 1) + its twice records.
    mismatched = db.sql("""
        WITH want AS (
            SELECT t.event_id,
                   CASE WHEN bool_or(f.fault = 'never') THEN 0 ELSE 1 END + count(*) FILTER (WHERE f.fault = 'twice') AS n
            FROM truth t LEFT JOIN faults f USING (event_id) GROUP BY t.event_id),
        got AS (SELECT event_id, count(*) AS n FROM deliveries GROUP BY event_id)
        SELECT w.event_id, w.n, coalesce(g.n, 0) FROM want w LEFT JOIN got g USING (event_id)
        WHERE w.n <> coalesce(g.n, 0) ORDER BY 1""").fetchall()
    never_ids = {f.get("event_id") for f in faults if f.get("fault") == "never"}
    twice_ids = {f.get("event_id") for f in faults if f.get("fault") == "twice"}
    unmarked = [f"{i}: delivered {g} times, the faults say {w}" for i, w, g in mismatched if i not in never_ids | twice_ids]
    report.check("twice", [f"{i}: delivered {g} times, the faults say {w}" for i, w, g in mismatched if i in twice_ids],
                 f"{pl(kinds['twice'], 'record')}, each event delivered once more" if kinds["twice"] else "none")
    report.check("never", [f"{i}: delivered {g} times, marked never" for i, w, g in mismatched if i in never_ids],
                 f"{pl(kinds['never'], 'event')} in the truth and not delivered" if kinds["never"] else "none")
    if unmarked:
        report.check("unmarked", unmarked, "")

    # late: the delay (event_time to first delivery) of each late event is longer than every other event's.
    delays = dict(db.sql("""
        SELECT d.event_id, min(epoch(d.received_time::TIMESTAMPTZ) - epoch(t.event_time::TIMESTAMPTZ))
        FROM deliveries d JOIN truth t USING (event_id) GROUP BY 1""").fetchall())
    late_ids = {f.get("event_id") for f in faults if f.get("fault") == "late"} & delays.keys()
    early = [f"{i}: received {dur(-delays[i])} before its event_time" for i in sorted(delays) if delays[i] < 0]
    report.check("received after event", early, "every delivery has received_time >= event_time")
    if late_ids:
        on_time = [v for i, v in delays.items() if i not in late_ids]
        slowest = max(on_time, default=0)
        late_problems = [f"{i}: first delivered {dur(delays[i])} after event_time, not later than an on-time "
                         f"event ({dur(slowest)})" for i in sorted(late_ids) if delays[i] <= slowest]
        low, high = min(delays[i] for i in late_ids), max(delays[i] for i in late_ids)
        report.check("late", late_problems, f"{pl(kinds['late'], 'event')} first delivered "
                     f"{dur(low) if low == high else dur(low) + ' to ' + dur(high)} after event_time; "
                     f"every other event within {dur(slowest)}")
    else:
        report.check("late", [], "none")

    # changed: a delivery differs from the truth only in the fields of a changed record.
    changed = defaultdict(set)
    for f in faults:
        if f.get("fault") == "changed":
            changed[f.get("event_id")].add(f.get("field"))
    seen_change, change_problems = defaultdict(set), []
    for s, path, n, row in deliveries:
        event = by_id.get(row.get("event_id"))
        if event is None:
            continue
        diff = {k for k in set(row) | set(event) if k != "received_time" and row.get(k) != event.get(k)}
        seen_change[row.get("event_id")] |= diff
        if diff - changed.get(row.get("event_id"), set()):
            change_problems.append(f"{rel(path)}:{n}: {row.get('event_id')} differs from the truth in "
                                   f"{', '.join(sorted(diff))} without a changed record")
    change_problems += [f"{i}: marked changed in {', '.join(sorted(fs - seen_change[i]))}, but no delivery differs"
                        for i, fs in changed.items() if fs - seen_change[i]]
    report.check("changed", change_problems,
                 f"{pl(kinds['changed'], 'record')}, each delivery differs in its field only" if kinds["changed"]
                 else "none: every delivery equals its truth event")

    lines_want = len(truth) - kinds["never"] + kinds["twice"]
    report.check("lines", [f"{len(deliveries)} delivery lines, truth - never + twice = {lines_want}"]
                 if len(deliveries) != lines_want else [],
                 f"{len(deliveries)} = {len(truth)} truth - {kinds['never']} never + {kinds['twice']} twice")
    other = {k: n for k, n in kinds.items() if k not in CHECKED}
    print(f"--   other fault kinds, not checked here: "
          f"{', '.join(f'{k} {n}' for k, n in sorted(other.items())) if other else 'none'}")

    if args.parquet:                       # the separate DuckDB step: JSON Lines in, one Parquet file per source
        parquet_dir.mkdir(parents=True, exist_ok=True)
        pq_problems, written = [], []
        for s in sources:
            out = parquet_dir / f"{s}.parquet"
            paths = [str(p) for p in files[s]]
            db.execute(f"COPY (SELECT * FROM read_json(?, format='newline_delimited', union_by_name=true, "
                       f"hive_partitioning=false)) TO '{out}' (FORMAT parquet)", [paths])
            rows = db.execute("SELECT count(*) FROM read_parquet(?)", [str(out)]).fetchone()[0]
            lines = sum(1 for _, path, _, _ in deliveries if path.parent.parent.parent.name == s)
            if rows != lines:
                pq_problems.append(f"{rel(out)}: {rows} rows, {lines} JSON lines")
            written.append(f"{rel(out)} {rows} rows = {lines} lines")
        report.check("parquet", pq_problems, "; ".join(written))

    if report.problems:
        print(f"FAILED: {args.sim_id} has {report.problems} problems")
    else:
        print(f"OK: {args.sim_id} follows the simulation standards (0 problems)")
    print(f"digest {digest(folder)}")
    return 1 if report.problems else 0


if __name__ == "__main__":
    sys.exit(main())
