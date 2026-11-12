#!/usr/bin/env python3
"""Count what each attested vocabulary is made of, by origin.

The six categories the project fixed on 2026-11-09 separate a word's *origin*
from whether the sound laws reproduce it.  This report measures the origin
side only, over every attested glossary in ``data/lexicon/``:

* ``non_ie``    — the recorded pathway leaves the Indo-European family
                  (Arabic into Persian, Turkic into German, Hebrew into
                  English); the donor is read from ``data/non_ie_sources.yaml``
                  through ``pie.loans.classify``.
* ``ie_loan``   — borrowed, but from an Indo-European language (Latin and
                  French into English, Greek into Latin).
* ``inherited`` — the leading ancestry row is an Indo-European language.
* ``no_ancestry`` — the glossary entry records no ancestor at all; the project's
                  "unexplained" category.
* ``unplaced``  — the entry records an ancestry row that names no language: a
                  translingual scientific name (``mul``) or an affix row.  It
                  is kept apart rather than counted as Indo-European.
* ``mixed``     — not a category but a review count: the entry records an
                  Indo-European inheritance *and* an outside ancestor.  The
                  categories above count such an entry once, by its leading
                  row; the count says how many words would move if the two
                  lexemes were split, which is the data-quality task the
                  one-pathway rule asks for.

``inherited`` is a statement about where the word came from, not a claim that
the laws reconstruct it: the exact/reconstruction split lives in
``tools/coverage.py``.

    python tools/loan_report.py
    python tools/loan_report.py --top 5
    python tools/loan_report.py --json data/loan_report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, loans                     # noqa: E402
from pie.textio import enable_utf8_stdio        # noqa: E402

COLUMNS = ("glossary", "inherited", "ie_loan", "non_ie", "no_ancestry", "unplaced")


def bucket(entry: dict) -> str:
    """The origin category of one glossary entry."""
    kind = loans.classify(entry)
    if kind:
        return kind
    if not entry.get("anc"):
        return "no_ancestry"
    recs = loans.rows(entry)
    if not recs or recs[0][0] in loans.NON_LANGUAGE:
        return "unplaced"
    return "inherited"


def is_mixed(entry: dict) -> bool:
    """Whether an entry records an inheritance beside an outside ancestor."""
    recs = loans.rows(entry)
    register = loans.sources()
    return bool(recs and recs[0][1] == "inherit" and recs[0][0] not in register
                and any(code in register for code, _rel in recs))


def measure(lang: str) -> dict:
    """Count one language's glossary by origin, with its donors."""
    counts: Counter[str] = Counter()
    donors: Counter[str] = Counter()
    mixed = 0
    entries = data.lexicon(lang)
    for entry in entries:
        kind = bucket(entry)
        counts[kind] += 1
        if is_mixed(entry):
            mixed += 1
        if kind == "non_ie":
            code = loans.source_language(entry)
            if code:
                donors[code] += 1
    row = {"lang": lang, "name": data.languages().get(lang, {}).get("name", lang)}
    row["glossary"] = len(entries)
    row.update({column: counts[column] for column in COLUMNS[1:]})
    row["mixed"] = mixed
    row["sources"] = dict(donors.most_common())
    return row


def attested() -> list[str]:
    """Every attested language the model holds a glossary for."""
    return [lang for lang, meta in data.languages().items()
            if meta.get("kind") == "attested" and data.lexicon(lang)]


def table(rows: list[dict]) -> str:
    """The per-language table, widest glossary first."""
    head = ["lang", "name", "glossary", *COLUMNS[1:], "mixed"]
    body = [[row["lang"], row["name"], str(row["glossary"]),
             *(str(row[c]) for c in COLUMNS[1:]), str(row["mixed"])] for row in rows]
    widths = [max(len(head[i]), *(len(line[i]) for line in body)) for i in range(len(head))]
    lines = ["  ".join(cell.ljust(widths[i]) for i, cell in enumerate(head)).rstrip(),
             "  ".join("-" * widths[i] for i in range(len(head)))]
    for line in body:
        lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(line)).rstrip())
    return "\n".join(lines)


def donor_lines(rows: list[dict], top: int) -> list[str]:
    """The largest outside donors of each language that has any."""
    lines = []
    for row in rows:
        if not row["sources"]:
            continue
        picks = list(row["sources"].items())[:top]
        lines.append(f"  {row['lang']:<6} {row['name']:<22} " +
                     "  ".join(f"{code} {n}" for code, n in picks))
    return lines


def main(argv: list[str] | None = None) -> int:
    enable_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=Path, help="write the same numbers as JSON")
    parser.add_argument("--top", type=int, default=3, help="donors to name per language")
    args = parser.parse_args(argv)

    rows = sorted((measure(lang) for lang in attested()),
                  key=lambda row: (-row["glossary"], row["lang"]))
    totals = Counter()
    for row in rows:
        for column in COLUMNS:
            totals[column] += row[column]
    totals["glossary"] = sum(row["glossary"] for row in rows)
    totals["mixed"] = sum(row["mixed"] for row in rows)

    print("Attested languages by origin of the recorded pathway\n")
    print(table(rows))
    print("\n  " + "  ".join(f"{column} {totals[column]}"
                             for column in ("glossary", *COLUMNS[1:])))
    print(f"  mixed {totals['mixed']} (subset of inherited; review for lexeme splitting)")
    print("\nLargest non-Indo-European donors, per target language\n")
    print("\n".join(donor_lines(rows, max(1, args.top))))

    if args.json:
        payload = {"languages": rows,
                   "totals": {column: totals[column]
                              for column in ("glossary", *COLUMNS[1:], "mixed")}}
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
