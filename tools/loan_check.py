#!/usr/bin/env python3
"""Audit the words a record says were borrowed from one donor language.

The project's 2026-11-09 request: a Persian word whose etymology states
"borrowed from Arabic" should say so on its page, and it stays in the non-PIE
band.  This tool answers, for one donor and one target language:

* how many stored words state that borrowing in their **leading** ancestry row
  (the row Wiktionary writes for the nearest ancestor, which is the statement
  "this word was borrowed from X");
* whether the page agrees — every one of them must come back ``non_pie`` from
  `pie.service.word`, the same verdict the coverage counter uses;
* whether the contact window in `data/loan_periods.yaml` covers them.

    python tools/loan_check.py --lang fa --donor ar
    python tools/loan_check.py --lang fa --donor ar --sample 120 --markdown /tmp/fa-ar-loans.md
    python tools/loan_check.py --lang fa --donor ar --check   # exit 1 on any disagreement

The sample is a plain alphabetical first-N, not a claim that other words are
different: the counts are over every word, the table is a reading list.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, loans, service          # noqa: E402
from pie.textio import enable_utf8_stdio      # noqa: E402


def stating(entry: dict, donor: str) -> bool:
    """True when the *leading* row is a borrowing from ``donor``."""
    full = loans._full_rows(entry)
    if not full:
        return False
    code, _form, rel = full[0]
    return code == donor and rel in loans.BORROW_RELATIONS


def main() -> int:
    enable_utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="fa")
    ap.add_argument("--donor", default="ar")
    ap.add_argument("--sample", type=int, default=120,
                    help="how many words to print (0 = all)")
    ap.add_argument("--markdown", default="", help="also write the table to this file")
    ap.add_argument("--check", action="store_true",
                    help="fail when a page does not say non_pie, or no window is recorded")
    args = ap.parse_args()

    target, donor = args.lang, args.donor
    meta = loans.sources().get(donor) or {}
    window = loans.period(donor, target)
    rows = [e for e in data.lexicon(target) if stating(e, donor)]
    print(f"{target} words whose record borrows from {donor} ({meta.get('name', donor)}): "
          f"{len(rows):,} of {len(list(data.lexicon(target))):,} stored")
    print(f"contact window: " + (f"{window['from']}–{window['to']} ({window['label']})"
                                 if window else "none recorded"))

    problems = []
    homographs = 0
    shown = rows[:args.sample] if args.sample else rows
    if args.check:
        index = service.word_index()
        for entry in rows:
            # A word page is keyed by spelling and shows the first stored
            # entry; a second entry with the same spelling is a homograph the
            # page does not show yet (docs/archive/UI_PLAN-2026-11.md.gz).  Its own band is
            # not what the page says, so it is counted apart, not as a
            # disagreement (2026-11-09).
            first = (index.get((target, entry["word"])) or [entry])[0]
            if first is not entry:
                homographs += 1
                continue
            page = service.word(target, entry["word"])
            if not page or (page.get("category") or {}).get("category") != "non_pie":
                problems.append(f"{entry['word']} → "
                                f"{((page or {}).get('category') or {}).get('category')}")
        if window is None:
            problems.append("no contact window on file")
        print(f"pages checked: {len(rows) - homographs:,} · disagreements: {len(problems):,}"
              + (f" · homograph entries not shown on any page: {homographs:,}"
                 if homographs else ""))
        for problem in problems[:12]:
            print(f"  ! {problem}")

    print()
    print(f"{'word':<16}{'gloss':<28}{'donor form':<18}band")
    for entry in shown:
        dossier = loans.donor(entry, target) or {}
        gloss = "; ".join(entry.get("gloss") or [])[:26]
        print(f"{entry['word']:<16}{gloss:<28}{dossier.get('form', ''):<18}non-PIE")

    if args.markdown:
        window_line = (
            f"The contact window ({window['from']}–{window['to']}, {window['label']}) is the "
            "period in which the two languages were in contact. It is a window, not a date for "
            "the word: the dictionary says *that* the word was borrowed and never *when*."
        ) if window else "No contact window is recorded for this pair."
        lines = [
            f"# {meta.get('name', donor)} loans in {data.languages().get(target, {}).get('name', target)}",
            "",
            f"Every word below states a borrowing from {meta.get('name', donor)} in the leading",
            "row of its recorded ancestry. The band is the same for all of them — **non-PIE**,",
            "dark grey — whatever the sound laws can do with the form: the word did not come",
            "from Proto-Indo-European, so the model does not get credit for it.",
            "",
            window_line,
            "",
            f"**{len(rows):,} words** in the glossary state this borrowing; the table shows the first "
            f"{len(shown):,}.",
            "",
            "| word | gloss | donor form | band |",
            "|---|---|---|---|",
        ]
        for entry in shown:
            dossier = loans.donor(entry, target) or {}
            gloss = "; ".join(entry.get("gloss") or []).replace("|", "\\|")[:60]
            lines.append(f"| {entry['word']} | {gloss} | {dossier.get('form', '')} | non-PIE |")
        Path(args.markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n→ {args.markdown}")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
