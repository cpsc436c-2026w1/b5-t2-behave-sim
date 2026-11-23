"""sim/check.py: SIM01 as written passes, and one injected error for each check makes that check, and only it, fail."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from sim import generate as g

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "src" / "rides" / "events.py"


@pytest.fixture
def sim01(tmp_path):
    shutil.copytree(g.generate("SIM01"), tmp_path / "SIM01")
    return tmp_path


def run(data: Path, *extra) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "sim" / "check.py"), "SIM01", "--data", str(data),
                           "--events", str(EVENTS), *extra], capture_output=True, text=True)


def failing(result) -> set[str]:
    return {line.split()[1].rstrip(":") for line in result.stdout.splitlines() if line.startswith("PROBLEM")}


def first_file(data: Path) -> Path:
    return sorted((data / "SIM01" / "trip-events").glob("dt=*/hour=*/deliveries.jsonl"))[0]


def rewrite(path: Path, change):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows = change(rows)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_sim01_passes(sim01):
    result = run(sim01, "--parquet")
    assert result.returncode == 0, result.stdout
    assert "OK: SIM01" in result.stdout and "2515 = 2511 truth - 0 never + 4 twice" in result.stdout


def test_a_field_with_a_typo_fails_validate(sim01):
    def typo(rows):
        rows[0]["pickup_zone"] = rows[0].pop("pickup_zone_id", 0)
        return rows
    rewrite(first_file(sim01), typo)
    assert failing(run(sim01)) >= {"validate"}


def test_a_local_time_fails_validate(sim01):
    def local(rows):
        rows[0]["event_time"] = rows[0]["event_time"].replace("Z", "-08:00")
        return rows
    rewrite(first_file(sim01), local)
    assert "validate" in failing(run(sim01))


def test_a_line_in_the_wrong_hour_folder_fails_folders(sim01):
    def later(rows):
        rows[0]["received_time"] = rows[0]["received_time"][:11] + "23:00:00Z"
        return rows
    rewrite(first_file(sim01), later)
    assert "folders" in failing(run(sim01))


def test_a_second_copy_without_a_fault_record_fails(sim01):
    rewrite(first_file(sim01), lambda rows: rows + [rows[0]])
    assert failing(run(sim01)) == {"unmarked", "lines"}


def test_a_twice_record_without_its_copy_fails_twice(sim01):
    faults = sim01 / "SIM01" / "_truth" / "faults.jsonl"
    rewrite(faults, lambda rows: rows + [{"fault": "twice", "event_id": "ev-000001"}])
    assert failing(run(sim01)) == {"twice", "lines"}


def test_a_never_record_for_a_delivered_event_fails_never(sim01):
    faults = sim01 / "SIM01" / "_truth" / "faults.jsonl"
    rewrite(faults, lambda rows: rows + [{"fault": "never", "event_id": "ev-000001"}])
    assert failing(run(sim01)) == {"never", "lines"}


def test_a_late_record_for_an_on_time_event_fails_late(sim01):
    faults = sim01 / "SIM01" / "_truth" / "faults.jsonl"
    rewrite(faults, lambda rows: rows + [{"fault": "late", "event_id": "ev-000001"}])
    assert failing(run(sim01)) == {"late"}


def test_a_changed_value_without_a_record_fails_changed(sim01):
    def change(rows):
        rows[0]["event_time"] = rows[0]["event_time"][:17] + "59Z"
        return rows
    rewrite(first_file(sim01), change)
    assert failing(run(sim01)) == {"changed"}


def test_an_event_twice_in_the_truth_fails_truth(sim01):
    rewrite(sim01 / "SIM01" / "_truth" / "events.jsonl", lambda rows: rows + [rows[0]])
    assert "truth" in failing(run(sim01))
