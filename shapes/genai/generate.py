"""Generative AI shape, SIM01 "paper-questions": 40 questions about 20 papers, with the answers known.

    uv run python shapes/genai/generate.py

Reads sample/openalex_works_sample.csv (20 works). For each work, two questions: how many authors it lists, and
whether it is a journal article or a conference paper. The answer of each comes from the sample, before any model
runs. The questions arrive over one hour on 2026-11-23, 1 to 5 s after they are asked. Writes, under
shapes/genai/data/SIM01/:

    questions/dt=<day>/hour=<hour>/deliveries.jsonl   what the assistant receives, in the order received
    _truth/events.jsonl                               each question once
    _truth/answers.jsonl                              the expected answer of each question (the eval's reference)
    _truth/faults.jsonl                               2 twice (the user sends the question again 10 to 60 s later),
                                                      1 changed (the title in the question loses its last word)
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
from events import EVENTS, Answer       # noqa: E402

SEED, SIM_ID, SOURCE = 436, "SIM01", "questions"
START = datetime(2026, 11, 23, 14, 0, tzinfo=timezone.utc)
FAULTS = {"twice": 2, "changed": 1}
KIND = {"article": "a journal article", "conference-paper": "a conference paper"}


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    rng = random.Random(SEED)
    with open(HERE / "sample" / "openalex_works_sample.csv", newline="") as f:
        works = list(csv.DictReader(f))
    cases = []
    for w in works:
        cases.append((w["work_id"], f'How many authors does the paper "{w["title"]}" list?', int(w["authors"])))
        cases.append((w["work_id"], f'Is "{w["title"]}" a journal article or a conference paper?', KIND[w["type"]]))
    times = sorted(START + timedelta(seconds=rng.randrange(3600)) for _ in cases)
    rng.shuffle(cases)
    events, answers = [], []
    for n, ((work, question, answer), t) in enumerate(zip(cases, times), 1):
        e = dict(event_id=f"ev-{n:04d}", event_type="question_asked", event_time=iso(t), question_id=f"q-{n:03d}",
                 work_id=work, question=question)
        EVENTS[e["event_type"]].model_validate(e)
        events.append(e)
        answers.append(Answer(event_id=e["event_id"], question_id=e["question_id"], answer=answer).model_dump())

    def at(e: dict, seconds: int) -> str:
        return iso(datetime.fromisoformat(e["event_time"].replace("Z", "+00:00")) + timedelta(seconds=seconds))

    picked = rng.sample(events, FAULTS["twice"] + FAULTS["changed"])
    twice, changed = {e["event_id"] for e in picked[:FAULTS["twice"]]}, {e["event_id"] for e in picked[FAULTS["twice"]:]}
    deliveries, faults = [], []
    for e in events:
        first = rng.randint(1, 5)
        if e["event_id"] in changed:                     # the title in the question loses its last word
            title_end = e["question"].rindex('"')
            cut = e["question"].rindex(" ", 0, title_end)
            deliveries.append({**e, "question": e["question"][:cut] + e["question"][title_end:],
                               "received_time": at(e, first)})
            faults.append(dict(fault="changed", event_id=e["event_id"], field="question"))
            continue
        deliveries.append({**e, "received_time": at(e, first)})
        if e["event_id"] in twice:
            deliveries.append({**e, "received_time": at(e, first + rng.randint(10, 60))})
            faults.append(dict(fault="twice", event_id=e["event_id"]))
    deliveries.sort(key=lambda d: (d["received_time"], d["event_id"]))

    folder = HERE / "data" / SIM_ID
    shutil.rmtree(folder, ignore_errors=True)
    files: dict[Path, list[dict]] = {}
    for d in deliveries:
        t = d["received_time"]
        files.setdefault(folder / SOURCE / f"dt={t[:10]}" / f"hour={t[11:13]}" / "deliveries.jsonl", []).append(d)
    files[folder / "_truth" / "events.jsonl"] = events
    files[folder / "_truth" / "answers.jsonl"] = answers
    files[folder / "_truth" / "faults.jsonl"] = sorted(faults, key=lambda f: (f["fault"], f["event_id"]))
    for path, lines in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(line) + "\n" for line in lines))
    print(f"{SIM_ID} paper-questions: {len(events)} questions with {len(answers)} answers, {len(deliveries)} deliveries, "
          f"{len(faults)} fault records -> {folder.relative_to(HERE.parent.parent)}/")


if __name__ == "__main__":
    main()
