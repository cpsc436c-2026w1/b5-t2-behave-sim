"""Operational shape, SIM01 "lunch-hour": one hour of pickup orders at 30 downtown cafes and restaurants, as a stream.

    uv run python shapes/operational/generate.py

Reads sample/overture_places_sample.csv (30 places). Makes 300 orders between 12:00 and 13:00 UTC on 2026-11-23,
each with order_placed and, 3 to 15 minutes later, order_ready: 600 events, each received 1 to 3 s after it
happens. Writes, under shapes/operational/data/SIM01/:

    orders/dt=<day>/hour=<hour>/deliveries.jsonl   what the system receives, in the order received
    _truth/events.jsonl                            each event once
    _truth/faults.jsonl                            4 twice (order_placed sent again 2 to 30 s later),
                                                   3 late (order_placed received 5 to 10 minutes late),
                                                   1 never (an order_ready that is not sent)
"""
import csv
import json
import random
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from events import EVENTS               # noqa: E402

SEED, SIM_ID, SOURCE = 436, "SIM01", "orders"
ORDERS, START = 300, datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
FAULTS = {"twice": 4, "late": 3, "never": 1}


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    rng = random.Random(SEED)
    with open(HERE / "sample" / "overture_places_sample.csv", newline="") as f:
        places = [row["place_id"] for row in csv.DictReader(f)]
    events = []
    for n in range(1, ORDERS + 1):
        placed = START + timedelta(seconds=rng.randrange(3600))
        ready = placed + timedelta(seconds=rng.randint(180, 900))
        order, place = f"o-{n:04d}", rng.choice(places)
        events.append(dict(event_type="order_placed", event_time=placed, order_id=order, place_id=place,
                           items=rng.randint(1, 5), total_cad=round(rng.uniform(4, 60), 2)))
        events.append(dict(event_type="order_ready", event_time=ready, order_id=order, place_id=place,
                           prep_s=int((ready - placed).total_seconds())))
    events.sort(key=lambda e: (e["event_time"], e["order_id"], e["event_type"]))
    for n, e in enumerate(events, 1):
        e["event_id"] = f"ev-{n:05d}"
        e["event_time"] = iso(e["event_time"])
        EVENTS[e["event_type"]].model_validate(e)

    def at(e: dict, seconds: int) -> str:
        return iso(datetime.fromisoformat(e["event_time"].replace("Z", "+00:00")) + timedelta(seconds=seconds))

    placed = [e for e in events if e["event_type"] == "order_placed"]
    ready = [e for e in events if e["event_type"] == "order_ready"]
    picked = rng.sample(placed, FAULTS["twice"] + FAULTS["late"])
    twice, late = {e["event_id"] for e in picked[:FAULTS["twice"]]}, {e["event_id"] for e in picked[FAULTS["twice"]:]}
    never = {e["event_id"] for e in rng.sample(ready, FAULTS["never"])}
    deliveries, faults = [], []
    for e in events:
        if e["event_id"] in never:
            faults.append(dict(fault="never", event_id=e["event_id"]))
            continue
        if e["event_id"] in late:
            deliveries.append({**e, "received_time": at(e, rng.randint(300, 600))})
            faults.append(dict(fault="late", event_id=e["event_id"]))
            continue
        first = rng.randint(1, 3)
        deliveries.append({**e, "received_time": at(e, first)})
        if e["event_id"] in twice:
            deliveries.append({**e, "received_time": at(e, first + rng.randint(2, 30))})
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
    print(f"{SIM_ID} lunch-hour: {len(events)} events, {len(deliveries)} deliveries, {len(faults)} fault records "
          f"-> {folder.relative_to(HERE.parent.parent)}/")


if __name__ == "__main__":
    main()
