"""Write sample/overture_places_sample.csv: 30 cafes and restaurants in a small part of downtown Vancouver.

    uv run python shapes/operational/extract_sample.py                 # reads the course preview over HTTPS
    uv run python shapes/operational/extract_sample.py <parquet file>  # or a downloaded overture_places.parquet

Source: the course preview of Overture Maps places (release 2026-10-21.0), Vancouver cut. Licence: sample/LICENCE.md.
"""
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
PREVIEW = "https://436c-2026w1-project-data.s3.ca-central-1.amazonaws.com/preview/maps/overture_places.parquet"
src = sys.argv[1] if len(sys.argv) > 1 else PREVIEW
duckdb.sql(f"""
COPY (
  SELECT id AS place_id, name, basic_category, round(lon, 5) AS lon, round(lat, 5) AS lat
  FROM read_parquet('{src}')
  WHERE basic_category IN ('restaurant', 'cafe', 'coffee_shop')
    AND lon BETWEEN -123.125 AND -123.115 AND lat BETWEEN 49.280 AND 49.286
    AND name IS NOT NULL AND confidence >= 0.9
  ORDER BY id
  LIMIT 30
) TO '{HERE / "sample" / "overture_places_sample.csv"}' (HEADER)
""")
print(duckdb.sql(f"SELECT count(*) AS rows FROM '{HERE / 'sample' / 'overture_places_sample.csv'}'").fetchall()[0][0], "rows")
