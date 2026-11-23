"""Write sample/ghcn_daily_sample.csv: one week of daily readings from eight weather stations around Vancouver.

    uv run python shapes/lakehouse/extract_sample.py            # reads the course preview over HTTPS
    uv run python shapes/lakehouse/extract_sample.py <folder>   # or a folder with data_0.parquet and stations.parquet

Source: the course preview of GHCN-Daily (NOAA), Canada cut, year 2025. Licence: sample/LICENCE.md.
"""
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
PREVIEW = "https://436c-2026w1-project-data.s3.ca-central-1.amazonaws.com/preview/ghcn"
src = sys.argv[1] if len(sys.argv) > 1 else PREVIEW
daily = f"{src}/data_0.parquet" if len(sys.argv) > 1 else f"{src}/daily/year=2025/data_0.parquet"
duckdb.sql(f"""
COPY (
  SELECT d.station_id, s.name AS station_name, d.date, d.element, d.value
  FROM read_parquet('{daily}') d JOIN read_parquet('{src}/stations.parquet') s ON s.id = d.station_id
  WHERE d.station_id IN ('CAN01108395', 'CAN01108380', 'CAN01108824', 'CAN01105658',
                         'CAN01106CL2', 'CAN01102425', 'CAN01101708', 'CAN01108910')
    AND d.date BETWEEN DATE '2025-11-03' AND DATE '2025-11-09'
    AND d.element IN ('TMAX', 'TMIN', 'PRCP')
    AND d.q_flag IS NULL
  ORDER BY d.date, d.station_id, d.element
) TO '{HERE / "sample" / "ghcn_daily_sample.csv"}' (HEADER)
""")
print(duckdb.sql(f"SELECT count(*) AS rows FROM '{HERE / 'sample' / 'ghcn_daily_sample.csv'}'").fetchall()[0][0], "rows")
