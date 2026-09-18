# MCQ Bank — 5,000 Questions with a Built-In Answer-Key Bias

A deterministic, dependency-free dataset of **exactly 5,000 multiple-choice questions**
(4 options each, A–D) across 6 subjects — where the correct answer is deliberately
skewed toward **B and C** (70.4% of the key) instead of A and D (29.6%).

Useful for testing quiz/eval pipelines, LLM answer-bias probes, spreadsheet loaders,
and bias-detection demos.

## Headline stats

| Letter | Count | Share |
|---|---:|---:|
| A | 723 | 14.5% |
| **B** | **1,750** | **35.0%** |
| **C** | **1,770** | **35.4%** |
| D | 757 | 15.1% |

**B + C = 70.4%** · **A + D = 29.6%** · B or C is ~2.4× more likely to be correct than A or D.

![Answer distribution](stats/charts/answers.svg)

![Answer-key share](stats/charts/answers_donut.svg)

## Questions per subject

Six subjects at ~833 questions each (exact numbers in [`data/counts.csv`](data/counts.csv)):
Astronomy, Geography, Biology, Computer Science, History, Physics.

![Questions per subject](stats/charts/subjects.svg)

## The bias holds inside every subject

![Answer distribution within each subject](stats/charts/subject_by_answer.svg)

## Count & full summary

- **The count:** [`data/counts.csv`](data/counts.csv) — per-letter and per-subject totals with % shares, plus [`data/subject_answer_matrix.csv`](data/subject_answer_matrix.csv) for the subject × answer cross-tab.
- **Written summary with all charts:** [`stats/summary.md`](stats/summary.md).

## Files

| Path | What it is |
|---|---|
| `data/mcqs.txt` | All 5,000 MCQs, human-readable (7 lines per question) |
| `data/mcqs.jsonl` | Same data, one JSON object per line: `{id, subject, question, options[4], answer}` |
| `data/counts.csv` | **The count** — per-subject and per-answer totals with shares |
| `data/subject_answer_matrix.csv` | Subject × answer cross-tab |
| `stats/summary.md` | Full written summary with charts |
| `stats/charts/*.svg` | Standalone charts (render directly on GitHub — no JS) |
| `mcq_generator.py` | Deterministic generator (seed `20260918`) |
| `make_stats.py` | Recomputes counts and regenerates every chart from the JSONL |

## Reproduce

```bash
python3 mcq_generator.py   # -> data/mcqs.txt + data/mcqs.jsonl
python3 make_stats.py      # -> counts CSVs + stats/summary.md + stats/charts/*.svg
```

Python 3.10+ standard library only — zero third-party packages. The fixed seed makes
every run byte-identical.

## Format

Each question in `mcqs.txt` looks like:

```
Q00001. [History] The start of the Cold War took place in which century (as commonly dated)?
   A) 18th century
   B) 20th century
   C) 14th century
   D) 5th century BCE
   Answer: B
```

## Notes

- Questions are **synthetic**, template-generated from a textbook-fact bank. Great for
  pipeline testing and bias experiments; not a study reference.
- The B/C skew is intentional and configurable — `ANSWER_WEIGHTS = (15, 35, 35, 15)` at
  the top of `mcq_generator.py`. Set `(25, 25, 25, 25)` for a uniform key.

## License

[MIT](LICENSE)
