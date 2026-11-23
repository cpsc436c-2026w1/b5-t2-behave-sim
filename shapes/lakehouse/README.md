# Lakehouse shape: a batch of files for each day

The system receives one file a night with the day before's readings of eight weather stations, and loads it into
the lake. What it must get right: a reading sent again in a later file is stored once, a reading that arrives a day
late is stored for its own day, and a value sent in the wrong unit is caught.

**SIM01 Late batches** One week of daily readings (TMAX, TMIN, PRCP) of eight GHCN-Daily stations around Vancouver,
2025-11-03 to 2025-11-09, moved to 2026-11-16 to 2026-11-22: 156 readings, sent as 157 deliveries in 7 batch files,
each at 06:00 UTC the day after. 3 readings are sent again in the next batch (`twice`), 2 arrive in the batch two
days later (`late`), 2 are in no batch (`never`), and 2 are sent in hundredths instead of tenths (`changed`,
field `value`). Seed 436.

| File | What it is |
|---|---|
| `sample/ghcn_daily_sample.csv`, `sample/LICENCE.md` | 156 rows of the GHCN-Daily preview (CC0) |
| `extract_sample.py` | the query that wrote the sample |
| `events.py` | the model: `reading_reported` |
| `generate.py` | writes `data/SIM01/readings/dt=<day>/hour=06/deliveries.jsonl` and `data/SIM01/_truth/` |

From the repository root:

```bash
uv run python shapes/lakehouse/generate.py
uv run python sim/check.py SIM01 --root shapes/lakehouse
```
