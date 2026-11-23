# Three shapes of simulated data

Each folder is a worked example of Part B for one project shape: a small sample from a course data set preview,
the Pydantic models, a generator for SIM01 and its design bullet. Pick the shape nearest your project, read its
generator, and run it and the check. All three pass the same `sim/check.py`.

| Folder | Shape | Sample (course preview) | SIM01 |
|---|---|---|---|
| [`lakehouse/`](lakehouse/README.md) | a batch of files for each day | GHCN-Daily weather readings, 156 rows | one week of nightly batch files, with all four fault kinds |
| [`operational/`](operational/README.md) | a stream of events with arrival times | Overture Maps places, 30 cafes and restaurants | one hour of pickup orders, `twice`, `late`, `never` |
| [`genai/`](genai/README.md) | a set of questions with their answers known | OpenAlex works, 20 papers | 40 questions with their answers, `twice`, `changed` |

Each `extract_sample.py` is the query that wrote the sample from the preview over HTTPS; you do not need to run it.
