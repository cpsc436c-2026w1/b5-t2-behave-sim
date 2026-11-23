"""Ask DuckDB a question about one simulated data set, before the system runs: the expected answer of a Then.

    uv run python sim/query.py SIM01 "SELECT pickup_zone_id, count(*) AS trips FROM truth WHERE event_type = 'trip_requested' GROUP BY 1 ORDER BY 1"
    uv run python sim/query.py SIM01 "SELECT * FROM faults"
    uv run python sim/query.py SIM01 --root shapes/genai "SELECT * FROM answers LIMIT 3"

Tables: `truth` (_truth/events.jsonl), `faults` (_truth/faults.jsonl), `deliveries` (every deliveries.jsonl of the
data set, with the folder of its source in `source`) and, when the file exists, `answers` (_truth/answers.jsonl).
One file, no import from this repository: copy it to your team repo beside check.py.
"""
import argparse
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
ap.add_argument("sim_id")
ap.add_argument("sql")
ap.add_argument("--root", type=Path, help="a shape folder: its data/ is read")
ap.add_argument("--data", type=Path, help="the folder that holds <SIM>/ (default sim/data)")
args = ap.parse_args()
folder = (args.data or (args.root / "data" if args.root else ROOT / "sim" / "data")) / args.sim_id
db = duckdb.connect()
nd = "format='newline_delimited', union_by_name=true, hive_partitioning=false"
db.execute(f"CREATE VIEW truth AS SELECT * FROM read_json('{folder}/_truth/events.jsonl', {nd})")
faults = folder / "_truth" / "faults.jsonl"
if faults.exists() and faults.stat().st_size:
    db.execute(f"CREATE VIEW faults AS SELECT * FROM read_json('{faults}', {nd})")
else:
    db.execute("CREATE VIEW faults AS SELECT NULL::VARCHAR AS fault, NULL::VARCHAR AS event_id WHERE false")
db.execute(f"CREATE VIEW deliveries AS SELECT *, regexp_extract(filename, '/([^/]+)/dt=', 1) AS source "
           f"FROM read_json('{folder}/[!_]*/dt=*/hour=*/deliveries.jsonl', {nd}, filename=true)")
if (folder / "_truth" / "answers.jsonl").exists():
    db.execute(f"CREATE VIEW answers AS SELECT * FROM read_json('{folder}/_truth/answers.jsonl', {nd})")
db.sql(args.sql).show(max_width=120)
