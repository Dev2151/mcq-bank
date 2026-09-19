#!/usr/bin/env python3
"""
mcq_generator.py - Generate a synthetic MCQ dataset (5,000 questions).

Each question has four options (A-D) with exactly one correct answer.
The correct option is placed UNIFORMLY at random (no forced bias):
any deviation from 25% per letter in the output is sampling noise, not
design. Deterministic via a fixed PRNG seed.

For the older version that deliberately biased the key toward B and C
(70.4% B+C), see git tag `biased-v1`.

Outputs (under data/):
  mcqs.txt    - human-readable question bank (primary artifact)
  mcqs.jsonl  - machine-readable mirror, one JSON object per line

Usage:
  python3 mcq_generator.py
"""

from __future__ import annotations

import csv
import json
import random
from collections import Counter
from pathlib import Path

TOTAL_QUESTIONS = 5_000
SEED = 20260918

# Uniform answer placement: every letter equally likely. Override here to
# experiment (e.g. (15, 35, 35, 15) reproduces the biased-v1 dataset).
ANSWER_WEIGHTS = (25, 25, 25, 25)  # A, B, C, D
UNIFORM = True
LETTERS = ("A", "B", "C", "D")

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

# ---------------------------------------------------------------------------
# Fact banks: item -> correct fact string
# ---------------------------------------------------------------------------

SOLAR_SYSTEM = {
    "Mercury": "38%", "Venus": "95%", "Mars": "53%", "Jupiter": "1,121%",
    "Saturn": "945%", "Uranus": "400%", "Neptune": "388%", "Ganymede": "41%",
    "Titan": "40%", "Callisto": "24%", "Io": "29%", "the Moon": "27%",
    "Europa": "16%", "Triton": "21%", "Pluto": "19%", "Ceres": "7%",
    "Eris": "19%", "Haumea": "11%", "Makemake": "11%", "Vesta": "42%",
    "Pallas": "41%", "Enceladus": "4%", "Mimas": "3%", "Rhea": "12%",
    "Iapetus": "12%", "Dione": "9%", "Tethys": "9%", "Oberon": "12%",
    "Titania": "12%", "Charon": "10%",
}

WORLD_CAPITALS = {
    "Canberra": "1927", "Ankara": "1923", "Brasilia": "1960", "Abuja": "1991",
    "Astana": "1997", "Naypyidaw": "2005", "Gaborone": "1966", "Dodoma": "1996",
    "Yamoussoukro": "1983", "Islamabad": "1967",
    "Colombo (Sri Jayawardenepura Kotte)": "1982",
    "Belmopan": "1970", "Malabo": "1973", "Ngerulmud": "2006",
    "Almaty (former capital era)": "1929", "Kyiv": "1917", "Tallinn": "1918",
    "Riga": "1918", "Vilnius": "1918", "Warsaw": "1918", "Prague": "1918",
    "Bratislava": "1993", "Ljubljana": "1991", "Zagreb": "1991",
    "Sarajevo": "1992", "Skopje": "1991", "Tirana": "1912", "Podgorica": "2006",
    "Chisinau": "1991", "Minsk": "1919", "Yerevan": "1918", "Tbilisi": "1918",
    "Baku": "1918", "Ashgabat": "1991", "Tashkent": "1991", "Bishkek": "1991",
    "Dushanbe": "1991", "Ulaanbaatar": "1924", "Phnom Penh": "1953",
    "Vientiane": "1975", "Bandar Seri Begawan": "1984", "Suva": "1970",
    "Port Moresby": "1975", "Apia": "1962", "Nuku'alofa": "1970",
    "Port Vila": "1980", "Honiara": "1978", "Tarawa": "1979",
    "Majuro": "1986", "Palikir": "1989", "Funafuti": "1978",
}

HUMAN_BIOLOGY = {
    "brain": "15%", "kidneys": "22%", "liver": "27%", "heart muscle": "4%",
    "skeletal muscle at rest": "15%", "skin": "6%", "spleen": "4%",
    "pancreas": "2%", "adrenal glands": "1%", "thyroid": "2%",
    "bone marrow": "5%", "bronchial circulation": "2%",
    "stomach wall": "2%", "intestinal mucosa": "10%", "retina": "1%",
    "cornea": "1%", "inner ear": "1%", "pituitary gland": "1%",
    "prostate": "1%", "uterus (non-pregnant)": "2%",
    "placenta (late term)": "15%", "fetal brain (late term)": "50%",
    "coronary arteries": "4%", "renal cortex": "20%", "renal medulla": "7%",
    "hepatic artery": "8%", "portal triad": "6%", "gallbladder": "1%",
    "esophagus": "1%", "tongue": "2%", "larynx": "1%", "tracheal wall": "1%",
    "diaphragm": "3%", "intercostal muscles": "2%", "spinal cord": "2%",
    "sciatic nerve": "1%", "femoral head": "3%", "knee cartilage": "1%",
    "meniscus": "1%", "Achilles tendon": "1%", "scalp": "4%", "lips": "1%",
    "dental pulp": "1%", "gingiva": "1%", "salivary glands": "2%",
    "lacrimal gland": "1%", "nasal mucosa": "1%", "eustachian tube": "1%",
    "semicircular canals": "1%", "optic nerve": "2%", "olfactory bulb": "1%",
}

COMPLEXITIES = {
    "dynamic array": "O(1)", "singly linked list": "O(n)",
    "hash table (average)": "O(1)", "balanced binary search tree": "O(log n)",
    "skip list (average)": "O(log n)", "doubly linked list": "O(n)",
    "circular buffer": "O(1)", "Fibonacci heap (find-min)": "O(1)",
    "min-heap (find-min)": "O(1)", "min-heap (extract-min)": "O(log n)",
    "B-tree": "O(log n)", "trie (key lookup)": "O(k)",
    "van Emde Boas tree": "O(log log U)",
    "union-find (with path compression)": "O(alpha(n))",
    "segment tree": "O(log n)", "Fenwick tree": "O(log n)",
    "sparse table (range queries)": "O(1)", "unordered map (worst case)": "O(n)",
    "sorted array (binary search)": "O(log n)",
    "adjacency list (vertex scan)": "O(V)",
    "adjacency matrix (edge check)": "O(1)", "deque (at the ends)": "O(1)",
    "priority queue (peek)": "O(1)", "hash set (average lookup)": "O(1)",
    "AVL tree": "O(log n)", "red-black tree": "O(log n)",
    "treap (expected)": "O(log n)", "splay tree (amortized)": "O(log n)",
    "suffix array (binary search)": "O(log n)", "rope": "O(log n)",
}

CENTURIES = {
    "Battle of Marathon": "5th century BCE", "Fall of Rome (West)": "5th century",
    "Battle of Hastings": "11th century", "Magna Carta signing": "13th century",
    "Black Death peak in Europe": "14th century",
    "Fall of Constantinople": "15th century", "Columbus's first voyage": "15th century",
    "Protestant Reformation start": "16th century", "Spanish Armada defeat": "16th century",
    "Thirty Years' War": "17th century", "English Civil War": "17th century",
    "Great Fire of London": "17th century", "Peter the Great's reign": "17th-18th century",
    "American Revolution": "18th century", "French Revolution": "18th century",
    "Napoleon's final defeat at Waterloo": "19th century",
    "Industrial Revolution in Britain": "18th-19th century",
    "Meiji Restoration": "19th century", "American Civil War": "19th century",
    "Scramble for Africa peak": "19th century", "World War I": "20th century",
    "Russian Revolution": "20th century", "World War II": "20th century",
    "start of the Cold War": "20th century", "Moon landing": "20th century",
    "Fall of the Berlin Wall": "20th century", "Dissolution of the USSR": "20th century",
    "Indian independence": "20th century", "Boxer Rebellion": "20th century",
    "Russo-Japanese War": "20th century", "Boer War": "19th-20th century",
    "Suez Crisis": "20th century", "end of the Vietnam War": "20th century",
    "Iranian Revolution": "20th century", "Falklands War": "20th century",
    "Chernobyl disaster": "20th century", "Gulf War": "20th century",
    "Rwandan genocide": "20th century", "Good Friday Agreement": "20th century",
    "Euro introduction": "20th-21st century", "September 11 attacks": "21st century",
    "Arab Spring": "21st century", "Brexit referendum": "21st century",
    "COVID-19 pandemic": "21st century", "Paris Climate Agreement": "21st century",
    "Higgs boson discovery": "21st century", "First CRISPR edit in humans": "21st century",
    "New Horizons Pluto flyby": "21st century", "First image of a black hole": "21st century",
    "James Webb Space Telescope launch": "21st century",
}

# ---------------------------------------------------------------------------
# Phrasing variants: prefix x body combinations keep questions unique
# without changing the underlying fact.
# ---------------------------------------------------------------------------

PREFIXES = [
    "",
    "According to standard references, ",
    "As commonly cited in textbooks, ",
    "In most introductory courses, ",
    "Per widely used reference tables, ",
    "In typical classroom materials, ",
    "As generally reported, ",
]

BODIES = {
    "Astronomy": [
        "what percentage of Earth's equatorial radius (6,371 km) is the equatorial radius of {name}?",
        "roughly how large is the equatorial radius of {name}, expressed as a percentage of Earth's equatorial radius (6,371 km)?",
        "if Earth's equatorial radius is scaled to 100%, what approximate percentage does the equatorial radius of {name} represent?",
        "relative to Earth's equatorial radius (6,371 km), what percent does the equatorial radius of {name} measure?",
    ],
    "Geography": [
        "in which year did {name} first serve as a seat of national government in the modern era?",
        "in what year did {name} begin functioning as the seat of national government in the modern era?",
        "during which year did {name} start serving as a modern national seat of government?",
    ],
    "Biology": [
        "roughly what share of a resting adult's cardiac output goes to the {name}?",
        "approximately what fraction of resting cardiac output is directed to the {name}?",
        "about what percentage of a resting adult's cardiac output supplies the {name}?",
    ],
    "Computer Science": [
        "what is the time complexity of the given operation on a {name}?",
        "what is the asymptotic time complexity of the stated operation on a {name}?",
        "which time complexity class describes the given operation on a {name}?",
        "in big-O terms, what is the cost of the described operation on a {name}?",
    ],
    "History": [
        "the {name} took place in which century (as commonly dated)?",
        "in which century (as commonly dated) did the {name} occur?",
        "the {name} is commonly dated to which century?",
    ],
}

FACT_BANKS = {
    "Astronomy": SOLAR_SYSTEM,
    "Geography": WORLD_CAPITALS,
    "Biology": HUMAN_BIOLOGY,
    "Computer Science": COMPLEXITIES,
    "History": CENTURIES,
}

DISTRACTOR_POOLS = {
    "Astronomy": ["4%", "11%", "19%", "27%", "38%", "42%", "53%", "72%", "88%", "120%"],
    "Geography": ["before 1800", "1800-1875", "1875-1920", "1920-1950",
                  "1950-1975", "1975-1990", "1990-2000", "after 2000"],
    "Biology": ["1%", "4%", "8%", "12%", "18%", "25%", "33%", "45%", "60%", "75%"],
    "Computer Science": ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n^2)", "O(2^n)"],
    "History": ["5th century BCE", "5th century", "11th century", "13th century",
                "14th century", "15th century", "16th century", "17th century",
                "18th century", "19th century", "20th century", "21st century"],
}


def physics_bank() -> list[tuple[str, str, list[str]]]:
    """(question, correct, distractors) tuples for physics work questions."""
    out: list[tuple[str, str, list[str]]] = []
    # 17 masses x 7 accelerations x 7 times = 833 unique questions,
    # exactly one subject's share of the 5,000-question bank.
    for mm in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 20, 25):
        for a in (2, 3, 4, 5, 6, 8, 10):
            for t in (2, 3, 4, 5, 6, 8, 10):
                d = 0.5 * a * t * t
                w = int(round(mm * a * d))
                q = (f"A {mm}-kg cart accelerates at {a} m/s^2 for {t} s starting "
                     f"from rest. How much work is done on it (nearest J)?")
                correct = f"{w} J"
                distractors = {f"{round(w * 0.5)} J", f"{round(w * 1.5)} J",
                               f"{round(w * 2)} J"}
                distractors.discard(correct)
                out.append((q, correct, sorted(distractors)))
    # Dedupe by question text, keeping first occurrence.
    seen: set[str] = set()
    unique: list[tuple[str, str, list[str]]] = []
    for q, correct, ds in out:
        if q not in seen:
            seen.add(q)
            unique.append((q, correct, ds))
    return unique


def make_options(fact: str, distractor_pool: list[str], rng: random.Random):
    """Pick 3 unique distractors and place the fact at a random index
    (uniform by default - see ANSWER_WEIGHTS)."""
    pool = sorted({d for d in distractor_pool if d != fact})
    rng.shuffle(pool)
    distractors = pool[:3]
    key_index = rng.choices(range(4), weights=ANSWER_WEIGHTS, k=1)[0]
    options = distractors + [fact]
    options[key_index], options[3] = options[3], options[key_index]
    return options, key_index


def question_pairs(subject: str) -> list[tuple[str, str]]:
    """All (question, fact) combinations for a subject, in deterministic order."""
    pairs: list[tuple[str, str]] = []
    for item, fact in FACT_BANKS[subject].items():
        for body in BODIES[subject]:
            for prefix in PREFIXES:
                text = prefix + body.format(name=item)
                if not prefix:
                    text = text[0].upper() + text[1:]
                pairs.append((text, fact))
    return pairs


def build_records() -> list[dict]:
    """Assemble exactly TOTAL_QUESTIONS records, balanced across subjects."""
    rng = random.Random(SEED)
    physics = physics_bank()

    subjects = list(FACT_BANKS) + ["Physics"]
    base_quota = TOTAL_QUESTIONS // len(subjects)          # 833
    extras = TOTAL_QUESTIONS - base_quota * len(subjects)  # 2

    records: list[dict] = []
    physics_cursor = 0

    def add_physics(n: int) -> None:
        nonlocal physics_cursor
        for _ in range(n):
            if physics_cursor >= len(physics):
                return
            q, correct, ds = physics[physics_cursor]
            physics_cursor += 1
            options, key_idx = make_options(correct, ds, rng)
            records.append({
                "id": "",
                "subject": "Physics",
                "question": q,
                "options": options,
                "answer": LETTERS[key_idx],
            })

    for i, subject in enumerate(subjects):
        quota = base_quota + (1 if i < extras else 0)
        if subject == "Physics":
            add_physics(quota)
            continue
        pairs = question_pairs(subject)
        made = 0
        for text, fact in pairs:
            if made >= quota:
                break
            options, key_idx = make_options(fact, DISTRACTOR_POOLS[subject], rng)
            records.append({
                "id": "",
                "subject": subject,
                "question": text,
                "options": options,
                "answer": LETTERS[key_idx],
            })
            made += 1
        # Top up any shortfall from the physics pool.
        if made < quota:
            add_physics(quota - made)

    # Shuffle deterministically so subjects are interleaved, then assign IDs.
    rng.shuffle(records)
    for idx, r in enumerate(records, start=1):
        r["id"] = f"Q{idx:05d}"
    return records


def write_outputs(records: list[dict]) -> Counter:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with (DATA_DIR / "mcqs.txt").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(f"{r['id']}. [{r['subject']}] {r['question']}\n")
            for letter, opt in zip(LETTERS, r["options"]):
                f.write(f"   {letter}) {opt}\n")
            f.write(f"   Answer: {r['answer']}\n\n")

    with (DATA_DIR / "mcqs.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    subject_counts = Counter(r["subject"] for r in records)
    answer_counts = Counter(r["answer"] for r in records)
    with (DATA_DIR / "counts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "key", "count", "share_pct"])
        for s, c in sorted(subject_counts.items()):
            w.writerow(["subject", s, c, f"{100 * c / TOTAL_QUESTIONS:.2f}"])
        for a in LETTERS:
            w.writerow(["answer", a, answer_counts[a], f"{100 * answer_counts[a] / TOTAL_QUESTIONS:.2f}"])
        w.writerow(["total", "questions", len(records), "100.00"])

    return answer_counts


def main() -> None:
    records = build_records()

    assert len(records) == TOTAL_QUESTIONS, f"expected {TOTAL_QUESTIONS}, got {len(records)}"
    assert len({r["question"] for r in records}) == TOTAL_QUESTIONS, "duplicate questions found"
    for r in records:
        assert len(r["options"]) == 4 and len(set(r["options"])) == 4, f"bad options in {r['id']}"
        assert r["answer"] in LETTERS

    answer_counts = write_outputs(records)
    subject_counts = Counter(r["subject"] for r in records)

    print(f"Generated {len(records)} MCQs ({len({r['question'] for r in records})} unique)")
    print(f"Subjects: {dict(sorted(subject_counts.items()))}")
    print(f"Answer distribution: {dict(sorted(answer_counts.items()))}")


if __name__ == "__main__":
    main()
