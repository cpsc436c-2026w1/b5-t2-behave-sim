# Operational shape: a stream of events with arrival times

The system receives pickup orders from 30 cafes and restaurants as they happen, and keeps each order's state for an
API. What it must get right: an order sent twice is one order, an order received minutes late still counts for the
time it was placed, and an order whose `order_ready` never arrives stays open.

**SIM01 Lunch hour** 300 pickup orders at 30 cafes and restaurants in downtown Vancouver (Overture Maps places)
between 12:00 and 13:00 UTC on 2026-11-23: each an `order_placed` and, 3 to 15 minutes later, an `order_ready`; 600
events sent as 603 deliveries, each received 1 to 3 s after it happens. 4 `order_placed` events arrive a second time
2 to 30 s later (`twice`), 3 are received 5 to 10 minutes late (`late`), and 1 `order_ready` is not sent (`never`).
Seed 436. The orders are made up: the sample gives the places only.

| File | What it is |
|---|---|
| `sample/overture_places_sample.csv`, `sample/LICENCE.md` | 30 places of the Overture Maps preview (CDLA-Permissive-2.0) |
| `extract_sample.py` | the query that wrote the sample |
| `events.py` | the models: `order_placed`, `order_ready` |
| `generate.py` | writes `data/SIM01/orders/dt=<day>/hour=<hour>/deliveries.jsonl` and `data/SIM01/_truth/` |

From the repository root:

```bash
uv run python shapes/operational/generate.py
uv run python sim/check.py SIM01 --root shapes/operational
```
