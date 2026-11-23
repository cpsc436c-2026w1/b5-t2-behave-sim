"""Lakehouse shape, SIM01 "late-batches": a nightly batch file of yesterday's station readings, for one week.

    uv run python shapes/lakehouse/generate.py

Reads sample/ghcn_daily_sample.csv (156 readings, 2025-11-03 to 2025-11-09) and moves the week to 2026-11-16 to
2026-11-22. Each day's readings arrive in one file at 06:00 UTC the next day. Writes, under shapes/lakehouse/data/SIM01/:

    readings/dt=<day>/hour=06/deliveries.jsonl   the batch files, in the order received
    _truth/events.jsonl                          each reading once
    _truth/faults.jsonl                          3 twice (sent again in the next batch), 2 late (in the batch two
                                                 days later), 2 never (not in any batch), 2 changed (value sent in
                                                 hundredths, not tenths)
"""
import csv
import json
import random
import shutil
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from events import EVENTS               # noqa: E402

SEED, SIM_ID, SOURCE = 436, "SIM01", "readings"
FAULTS = {"twice": 3, "late": 2, "never": 2, "changed": 2}
MOVE = date(2026, 11, 16) - date(2025, 11, 3)          # the sample's week, moved to the week before the tutorial


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    rng = random.Random(SEED)
    with open(HERE / "sample" / "ghcn_daily_sample.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    events = []
    for n, row in enumerate(rows, 1):
        day = date.fromisoformat(row["date"]) + MOVE
        events.append(dict(event_id=f"rd-{n:05d}", event_type="reading_reported",
                           event_time=iso(datetime(day.year, day.month, day.day, tzinfo=timezone.utc)),
                           station_id=row["station_id"], element=row["element"], value=int(row["value"])))
    for e in events:
        EVENTS[e["event_type"]].model_validate(e)

    def batch(e: dict, days_after: int) -> datetime:      # 06:00 UTC, days_after the reading's day
        return datetime.fromisoformat(e["event_time"].replace("Z", "+00:00")) + timedelta(days=days_after, hours=6)

    picked = rng.sample(events, sum(FAULTS.values()))
    kinds = [k for k, n in FAULTS.items() for _ in range(n)]
    fault_of = {e["event_id"]: k for e, k in zip(picked, kinds)}
    deliveries, faults = [], []
    for e in events:
        kind = fault_of.get(e["event_id"])
        if kind == "never":
            faults.append(dict(fault="never", event_id=e["event_id"]))
            continue
        if kind == "late":
            deliveries.append({**e, "received_time": iso(batch(e, 2))})
            faults.append(dict(fault="late", event_id=e["event_id"]))
            continue
        if kind == "changed":
            deliveries.append({**e, "value": e["value"] * 10, "received_time": iso(batch(e, 1))})
            faults.append(dict(fault="changed", event_id=e["event_id"], field="value"))
            continue
        deliveries.append({**e, "received_time": iso(batch(e, 1))})
        if kind == "twice":
            deliveries.append({**e, "received_time": iso(batch(e, 2))})
            faults.append(dict(fault="twice", event_id=e["event_id"]))
    deliveries.sort(key=lambda d: (d["received_time"], d["event_id"]))

    folder = HERE / "data" / SIM_ID
    shutil.rmtree(folder, ignore_errors=True)
    files: dict[Path, list[dict]] = {}
    for d in deliveries:
        t = d["received_time"]
        files.setdefault(folder / SOURCE / f"dt={t[:10]}" / f"hour={t[11:13]}" / "deliveries.jsonl", []).append(d)
    files[folder / "_truth" / "events.jsonl"] = events
    files[folder / "_truth" / "faults.jsonl"] = sorted(faults, key=lambda f: (f["fault"], f["event_id"]))
    for path, lines in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(line) + "\n" for line in lines))
    print(f"{SIM_ID} late-batches: {len(events)} readings, {len(deliveries)} deliveries in "
          f"{len(files) - 2} batch files, {len(faults)} fault records -> {folder.relative_to(HERE.parent.parent)}/")


if __name__ == "__main__":
    main()
