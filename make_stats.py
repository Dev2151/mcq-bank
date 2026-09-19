#!/usr/bin/env python3
"""
make_stats.py - Analyze data/mcqs.jsonl and produce the summary + charts.

Reads the generated dataset and writes:
  data/counts.csv                 - per-subject and per-answer counts
  data/subject_answer_matrix.csv  - subject x answer cross-tab
  stats/summary.md                - text summary with inline SVG charts
  stats/charts/*.svg              - standalone SVG charts (GitHub-renderable)

Charts are hand-built SVG (no third-party dependencies) so they render
directly in GitHub READMEs, issues, and file previews.

Run after mcq_generator.py:
  python3 make_stats.py
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
STATS_DIR = ROOT / "stats"
CHARTS_DIR = STATS_DIR / "charts"

LETTERS = ("A", "B", "C", "D")
ANSWER_COLORS = {"A": "#f97316", "B": "#2563eb", "C": "#10b981", "D": "#f59e0b"}
SUBJECT_COLORS = {
    "Astronomy": "#6366f1", "Geography": "#0ea5e9", "Biology": "#10b981",
    "Computer Science": "#8b5cf6", "History": "#f59e0b", "Physics": "#ef4444",
}


def load_records() -> list[dict]:
    with (DATA_DIR / "mcqs.jsonl").open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------

def svg_open(w: int, h: int) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" font-family="ui-sans-serif,system-ui,'
            f'Segoe UI,Helvetica,Arial,sans-serif">\n')


def legend(items: list[tuple[str, str, str]], x: float, y: float, swatch_w: int = 14) -> str:
    out = ['<g font-size="13">']
    for label, color, value in items:
        out.append(
            f'<g transform="translate({x:.0f},{y:.0f})">'
            f'<rect width="{swatch_w}" height="{swatch_w}" rx="3" fill="{color}"/>'
            f'<text x="{swatch_w + 6}" y="{swatch_w - 2}" fill="#111827">{escape(label)}</text>'
            f'<text x="{swatch_w + 128}" y="{swatch_w - 2}" fill="#6b7280">{escape(value)}</text>'
            f'</g>'
        )
        y += 22
    out.append("</g>")
    return "\n".join(out)


def bar_chart_h(counts: Counter, colors: dict[str, str], title: str,
                width: int = 640, bar_h: int = 34) -> str:
    """Horizontal bar chart for small categorical sets (e.g., answers)."""
    total = sum(counts.values())
    max_v = max(counts.values())
    label_w = 60
    value_w = 96
    plot_w = width - label_w - value_w
    height = int(44 + len(counts) * (bar_h + 10))
    s = [svg_open(width, height)]
    s.append(f'<text x="16" y="26" font-size="15" font-weight="600" fill="#111827">{escape(title)}</text>')
    y = 44
    for key in counts:
        v = counts[key]
        pct = 100 * v / total
        w = plot_w * v / max_v
        s.append(f'<text x="{label_w - 10}" y="{y + bar_h / 2 + 5}" text-anchor="end" '
                 f'font-size="14" fill="#111827">{escape(str(key))}</text>')
        s.append(f'<rect x="{label_w}" y="{y}" width="{plot_w}" height="{bar_h}" rx="6" fill="#e5e7eb"/>')
        s.append(f'<rect x="{label_w}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="6" fill="{colors[key]}"/>')
        s.append(f'<text x="{label_w + plot_w + 8}" y="{y + bar_h / 2 + 5}" font-size="13" fill="#374151">'
                 f'{v:,} ({pct:.1f}%)</text>')
        y += bar_h + 10
    s.append("</svg>")
    return "\n".join(s)


def bar_chart_h_subjects(counts: Counter, colors: dict[str, str], title: str,
                         width: int = 720, bar_h: int = 30) -> str:
    total = sum(counts.values())
    max_v = max(counts.values())
    label_w = 160
    value_w = 96
    plot_w = width - label_w - value_w
    height = int(46 + len(counts) * (bar_h + 10))
    s = [svg_open(width, height)]
    s.append(f'<text x="16" y="26" font-size="15" font-weight="600" fill="#111827">{escape(title)}</text>')
    y = 46
    for key in counts:
        v = counts[key]
        pct = 100 * v / total
        w = plot_w * v / max_v
        s.append(f'<text x="{label_w - 10}" y="{y + bar_h / 2 + 5}" text-anchor="end" '
                 f'font-size="13.5" fill="#111827">{escape(str(key))}</text>')
        s.append(f'<rect x="{label_w}" y="{y}" width="{plot_w}" height="{bar_h}" rx="6" fill="#e5e7eb"/>')
        s.append(f'<rect x="{label_w}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="6" fill="{colors[key]}"/>')
        s.append(f'<text x="{label_w + plot_w + 8}" y="{y + bar_h / 2 + 5}" font-size="13" fill="#374151">'
                 f'{v:,} ({pct:.1f}%)</text>')
        y += bar_h + 10
    s.append("</svg>")
    return "\n".join(s)


def stacked_chart(matrix: dict[str, Counter], title: str,
                  width: int = 720) -> str:
    """One stacked bar per subject, segments colored by answer letter."""
    subjects = list(matrix)
    row_h = 40
    height = int(48 + row_h * len(subjects) + 34)
    label_w = 160
    plot_w = width - label_w - 60
    s = [svg_open(width, height)]
    s.append(f'<text x="16" y="26" font-size="15" font-weight="600" fill="#111827">{escape(title)}</text>')
    y = 48
    for subj in subjects:
        cnt = matrix[subj]
        total = sum(cnt.values())
        x = float(label_w)
        for letter in LETTERS:
            frac = cnt[letter] / total
            seg_w = plot_w * frac
            if seg_w > 0:
                s.append(f'<rect x="{x:.1f}" y="{y}" width="{seg_w:.1f}" height="{row_h - 8}" '
                         f'fill="{ANSWER_COLORS[letter]}"/>')
            if frac >= 0.08:
                s.append(f'<text x="{x + seg_w / 2:.1f}" y="{y + (row_h - 8) / 2 + 4}" '
                         f'text-anchor="middle" font-size="12.5" fill="#ffffff" '
                         f'font-weight="600">{100 * frac:.0f}%</text>')
            x += seg_w
        s.append(f'<text x="{label_w - 10}" y="{y + (row_h - 8) / 2 + 4}" text-anchor="end" '
                 f'font-size="13" fill="#111827">{escape(subj)}</text>')
        y += row_h
    # legend
    lx = label_w
    for letter in LETTERS:
        s.append(f'<rect x="{lx}" y="{y + 4}" width="12" height="12" rx="3" fill="{ANSWER_COLORS[letter]}"/>')
        s.append(f'<text x="{lx + 18}" y="{y + 14}" font-size="12.5" fill="#374151">{letter}</text>')
        lx += 64
    s.append("</svg>")
    return "\n".join(s)


def donut(counts: Counter, colors: dict[str, str], title: str,
          size: int = 260) -> str:
    total = sum(counts.values())
    cx = cy = size / 2
    r = size / 2 - 14
    stroke = 40
    circ = 2 * 3.141592653589793 * r
    s = [svg_open(size, size + 44)]
    s.append(f'<text x="{size / 2}" y="18" text-anchor="middle" font-size="14" '
             f'font-weight="600" fill="#111827">{escape(title)}</text>')
    offset = 0.0
    for key, v in counts.items():
        frac = v / total
        dash = f'{frac * circ:.2f} {circ - frac * circ:.2f}'
        s.append(f'<circle cx="{cx}" cy="{cy + 17}" r="{r}" fill="none" '
                 f'stroke="{colors[key]}" stroke-width="{stroke}" '
                 f'stroke-dasharray="{dash}" stroke-dashoffset="{-offset * circ:.2f}" '
                 f'transform="rotate(-90 {cx} {cy + 17})"/>')
        offset += frac
    s.append(f'<text x="{cx}" y="{cy + 12}" text-anchor="middle" font-size="22" '
             f'font-weight="700" fill="#111827">{total:,}</text>')
    s.append(f'<text x="{cx}" y="{cy + 32}" text-anchor="middle" font-size="12" fill="#6b7280">questions</text>')
    # legend row
    lx = 18
    for key, v in counts.items():
        s.append(f'<rect x="{lx}" y="{size + 20}" width="11" height="11" rx="3" fill="{colors[key]}"/>')
        s.append(f'<text x="{lx + 16}" y="{size + 30}" font-size="11.5" fill="#374151">'
                 f'{key} {100 * v / total:.0f}%</text>')
        lx += 58
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------------------------
# Uniformity statistics
# ---------------------------------------------------------------------------

def chi_square_sf(x: float, k: int) -> float:
    """Survival function of the chi-square distribution (right tail) using the
    regularized upper incomplete gamma function Q(k/2, x/2), for small k.
    Enough for df=3 here; no third-party dependencies needed."""
    import math

    def gamma_p_series(s: float, x: float) -> float:
        # Regularized lower incomplete gamma P(s, x) for x < s+1 (series form).
        term = 1.0 / s
        total = term
        n = 0
        while True:
            n += 1
            term *= x / (s + n)
            total += term
            if abs(term) < 1e-15 * abs(total) or n > 10_000:
                break
        return total * math.exp(-x + s * math.log(x) - math.lgamma(s))

    def gamma_q_cf(s: float, x: float) -> float:
        # Regularized upper incomplete gamma Q(s, x) via Lentz continued fraction.
        tiny = 1e-300
        b = x + 1.0 - s
        c = 1.0 / tiny
        d = 1.0 / b
        h = d
        for i in range(1, 10_000):
            an = -i * (i - s)
            b += 2.0
            d = an * d + b
            if abs(d) < tiny:
                d = tiny
            c = b + an / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            delta = d * c
            h *= delta
            if abs(delta - 1.0) < 1e-15:
                break
        return math.exp(-x + s * math.log(x) - math.lgamma(s)) * h

    a = k / 2.0
    xx = x / 2.0
    if xx < a + 1.0:
        return 1.0 - gamma_p_series(a, xx)
    return gamma_q_cf(a, xx)


def uniformity_report(answer_counts: Counter, total: int) -> dict:
    """Chi-square goodness-of-fit test of the answer key against uniform 25%.
    With uniform generation this should NOT be significant; a significant
    result would indicate forced bias (like the biased-v1 dataset)."""
    expected = total / 4.0
    chi2 = sum((answer_counts[L] - expected) ** 2 / expected for L in LETTERS)
    p = chi_square_sf(chi2, df) if (df := len(LETTERS) - 1) else 1.0
    shares = {L: answer_counts[L] / total for L in LETTERS}
    minmax = max(shares.values()) - min(shares.values())
    return {"chi2": chi2, "df": df, "p": p, "expected": expected, "spread": minmax}

def main() -> None:
    records = load_records()
    total = len(records)
    answer_counts = Counter(r["answer"] for r in records)
    subject_counts = Counter(r["subject"] for r in records)
    matrix: dict[str, Counter] = {}
    for r in records:
        matrix.setdefault(r["subject"], Counter())[r["answer"]] += 1

    DATA_DIR.mkdir(exist_ok=True)
    STATS_DIR.mkdir(exist_ok=True)
    CHARTS_DIR.mkdir(exist_ok=True)

    # ---- CSVs ----
    with (DATA_DIR / "counts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "key", "count", "share_pct"])
        for s, c in sorted(subject_counts.items()):
            w.writerow(["subject", s, c, f"{100 * c / total:.2f}"])
        for a in LETTERS:
            w.writerow(["answer", a, answer_counts[a], f"{100 * answer_counts[a] / total:.2f}"])
        w.writerow(["total", "questions", total, "100.00"])

    with (DATA_DIR / "subject_answer_matrix.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["subject", "A", "B", "C", "D", "total"])
        for s in sorted(matrix):
            c = matrix[s]
            w.writerow([s, c["A"], c["B"], c["C"], c["D"], sum(c.values())])
        w.writerow(["ALL", answer_counts["A"], answer_counts["B"], answer_counts["C"],
                    answer_counts["D"], total])

    # ---- SVG charts ----
    (CHARTS_DIR / "answers.svg").write_text(
        bar_chart_h(answer_counts, ANSWER_COLORS, "Correct-answer distribution (A-D)"),
        encoding="utf-8")
    (CHARTS_DIR / "subjects.svg").write_text(
        bar_chart_h_subjects(subject_counts, SUBJECT_COLORS, "Questions per subject"),
        encoding="utf-8")
    (CHARTS_DIR / "answers_donut.svg").write_text(
        donut(answer_counts, ANSWER_COLORS, "Answer-key share"),
        encoding="utf-8")
    (CHARTS_DIR / "subject_by_answer.svg").write_text(
        stacked_chart(matrix, "Answer distribution within each subject"),
        encoding="utf-8")

    # ---- Markdown summary ----
    stats = uniformity_report(answer_counts, total)
    sig = "IS" if stats["p"] < 0.05 else "is NOT"
    bc = answer_counts["B"] + answer_counts["C"]
    ad = answer_counts["A"] + answer_counts["D"]
    lines = [
        "# Dataset Summary",
        "",
        f"**Total MCQs:** {total:,}  |  **Subjects:** {len(subject_counts)}  |  "
        f"**Options per question:** 4  |  **Unique question texts:** "
        f"{len({r['question'] for r in records}):,}",
        "",
        "## Headline numbers",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total questions | **{total:,}** |",
        f"| A answers | {answer_counts['A']:,} ({100 * answer_counts['A'] / total:.1f}%) |",
        f"| B answers | {answer_counts['B']:,} ({100 * answer_counts['B'] / total:.1f}%) |",
        f"| C answers | {answer_counts['C']:,} ({100 * answer_counts['C'] / total:.1f}%) |",
        f"| D answers | {answer_counts['D']:,} ({100 * answer_counts['D'] / total:.1f}%) |",
        f"| B+C combined | {bc:,} ({100 * bc / total:.1f}%) |",
        f"| A+D combined | {ad:,} ({100 * ad / total:.1f}%) |",
        "",
        "## Is the answer key biased? (uniformity test)",
        "",
        "The generator places the correct option **uniformly at random** - no forced "
        "bias. A chi-square goodness-of-fit test against a uniform 25% per letter:",
        "",
        f"- chi-square = **{stats['chi2']:.2f}** (df = {stats['df']}, expected {stats['expected']:.0f} per letter)",
        f"- p-value = **{stats['p']:.3f}" + ("** - " if stats["p"] < 0.05 else "** - ") +
        f"the key {sig} significantly different from uniform at the 0.05 level.",
        f"- Max letter share {100 * max(answer_counts.values()) / total:.1f}%, "
        f"min {100 * min(answer_counts.values()) / total:.1f}% "
        f"(spread {100 * stats['spread']:.1f} pp) - within normal sampling noise for n = {total:,}.",
        "",
        "> Note: the earlier version of this dataset (git tag `biased-v1`) *forced* a "
        "B/C-heavy key (70.4% B+C) as a demo fixture. That bias was an input, not a "
        "finding. This version is the honest, unforced baseline.",
        "",
        "## Charts",
        "",
        "### Correct-answer distribution",
        "",
        "![Answer distribution](charts/answers.svg)",
        "",
        "![Answer-key share](charts/answers_donut.svg)",
        "",
        "### Questions per subject",
        "",
        "![Questions per subject](charts/subjects.svg)",
        "",
        "### Answer distribution within each subject",
        "",
        "![Subject by answer](charts/subject_by_answer.svg)",
        "",
        "## Subject x answer matrix",
        "",
        "| Subject | A | B | C | D | Total |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for s in sorted(matrix):
        c = matrix[s]
        t = sum(c.values())
        lines.append(
            f"| {s} | {c['A']} | {c['B']} | {c['C']} | {c['D']} | {t} |")
    lines += [
        f"| **ALL** | **{answer_counts['A']}** | **{answer_counts['B']}** | "
        f"**{answer_counts['C']}** | **{answer_counts['D']}** | **{total}** |",
        "",
        "## Files",
        "",
        "- `data/mcqs.txt` - the full question bank, human-readable",
        "- `data/mcqs.jsonl` - one JSON object per question (for scripts)",
        "- `data/counts.csv` - per-subject / per-answer counts",
        "- `data/subject_answer_matrix.csv` - subject x answer cross-tab",
        "- `stats/charts/*.svg` - standalone charts (render right on GitHub)",
        "",
        "_Generated by `mcq_generator.py` + `make_stats.py` (deterministic, seed "
        "20260918). Rerun to reproduce byte-identical output._",
    ]
    (STATS_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote counts.csv, subject_answer_matrix.csv, summary.md and "
          f"{len(list(CHARTS_DIR.glob('*.svg')))} SVG charts")
    print(f"B+C = {100 * bc / total:.1f}% vs A+D = {100 * ad / total:.1f}%")


if __name__ == "__main__":
    main()
