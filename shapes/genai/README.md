# Generative AI shape: a set of questions with their answers known

The system is an assistant that answers questions about research papers. Its eval needs cases whose answers are
known before any model runs: here each answer comes from the sample. What it must get right: a question sent twice
is answered once, and a question whose title arrives cut short is still answered, or flagged.

**SIM01 Paper questions** 40 questions about 20 OpenAlex works of 2024 on cloud computing, two for each work: how
many authors it lists, and whether it is a journal article or a conference paper. The expected answers, from the
sample, are in `_truth/answers.jsonl`. The questions arrive between 14:00 and 15:00 UTC on 2026-11-23, 1 to 5 s
after they are asked: 42 deliveries. 2 questions are sent again 10 to 60 s later (`twice`), and in 1 the title loses
its last word (`changed`, field `question`). Seed 436.

| File | What it is |
|---|---|
| `sample/openalex_works_sample.csv`, `sample/LICENCE.md` | 20 works of the OpenAlex preview (CC0), without author names |
| `extract_sample.py` | the query that wrote the sample |
| `events.py` | the model `question_asked`, and `Answer` for a line of `answers.jsonl` |
| `generate.py` | writes `data/SIM01/questions/dt=<day>/hour=<hour>/deliveries.jsonl` and `data/SIM01/_truth/`, with `answers.jsonl` |

From the repository root:

```bash
uv run python shapes/genai/generate.py
uv run python sim/check.py SIM01 --root shapes/genai
uv run python sim/query.py SIM01 --root shapes/genai "SELECT question_id, answer FROM answers ORDER BY 1 LIMIT 3"
```

The eval of `evals/pickup_place/` in this repository has the same structure: cases with reference values, and a
checker that compares each reply with its reference.
