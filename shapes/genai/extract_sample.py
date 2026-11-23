"""Write sample/openalex_works_sample.csv: 20 works of 2024 on cloud computing, with the fields the questions use.

    uv run python shapes/genai/extract_sample.py                 # reads the course preview over HTTPS (87 MB file)
    uv run python shapes/genai/extract_sample.py <parquet file>  # or a downloaded works.parquet

Source: the course preview of OpenAlex works, topic Cloud Computing and Resource Management, 2015 to 2025.
Author names are left out: the sample keeps their number only. Licence: sample/LICENCE.md.
"""
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
PREVIEW = "https://436c-2026w1-project-data.s3.ca-central-1.amazonaws.com/preview/openalex/works.parquet"
src = sys.argv[1] if len(sys.argv) > 1 else PREVIEW
duckdb.sql(f"""
COPY (
  SELECT id AS work_id, title, publication_year, type, len(authorships) AS authors, cited_by_count
  FROM read_parquet('{src}')
  WHERE publication_year = 2024 AND type IN ('article', 'conference-paper')
    AND title IS NOT NULL AND length(title) BETWEEN 30 AND 110 AND title NOT LIKE '%"%'
    AND len(authorships) BETWEEN 1 AND 12
  ORDER BY cited_by_count DESC, id
  LIMIT 20
) TO '{HERE / "sample" / "openalex_works_sample.csv"}' (HEADER)
""")
print(duckdb.sql(f"SELECT count(*) AS rows FROM '{HERE / 'sample' / 'openalex_works_sample.csv'}'").fetchall()[0][0], "rows")
