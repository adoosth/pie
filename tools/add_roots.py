#!/usr/bin/env python3
"""Give every root a construction names a glossary entry of its own.

The dictionary records a root inside another entry's etymology ("possibly
nominalized from root *h₂retḱ- (“to damage, harm”)") long before it gives that
root a page, and Wiktionary has no page for many of them at all. The word page
prints the root in the construction line, so it must be a door: this writes the
root into ``data/lexicon/_supplement/ine-pro.jsonl.gz`` as a reconstructed
entry whose citation is the entry that names it (2026-11-08).

    PYTHONPATH=src python3 tools/add_roots.py            # report and write
    PYTHONPATH=src python3 tools/add_roots.py --check    # report only

The rows are reconstructions and say so: ``recon`` marks them gold, ``ref``
quotes the sentence, ``url`` is the page where the root was read, and
``cited_by`` names the word whose construction printed it. Nothing is glossed
unless the entry glossed it.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, service  # noqa: E402

SUPPLEMENT = ROOT / "data" / "lexicon" / "_supplement" / "ine-pro.jsonl.gz"

#: Bases that are printed but are not root headwords: a case form, a suffix, a
#: pronoun stem or an adposition. A root page for one of these would claim the
#: dictionary records a word it does not (2026-11-08).
NOT_A_ROOT = {
    "(é)-os": "the stem-formative of an s-stem, not a base",
    "-eh₂": "a suffix",
    "déh₃-n̥-s": "a formed noun, not the base it is formed from",
    "h₂us-és": "a genitive form",
    "téwh₂os": "a whole s-stem word, not a base",
    "ǵʰém": "a locative form",
    "ǵʰéy-ōm": "an accusative form",
    "kʷí-": "a pronominal stem",
    "kʷó-": "a pronominal stem",
    "tó-": "a pronominal stem",
    "í-": "a pronominal stem",
    "h₁e-": "a pronominal stem",
    "h₁en": "an adposition",
    "(h₁)én": "an adposition",
    "h₂en": "an adposition",
    "h₂ep": "an adposition",
    "úp": "an adposition",
    "ménes-": "an s-stem stem, not a root headword",
}


def page(word: str) -> str:
    return ("https://en.wiktionary.org/wiki/Reconstruction:Proto-Indo-European/"
            + quote(word, safe=""))


def rows(mine: set[str] | None = None) -> dict[str, dict]:
    """One supplement row per construction base that is a root.

    ``mine`` names the roots this tool wrote before: they are in the glossary
    now, but the row is regenerated from the entry it was read from so a
    corrected quote reaches the build instead of being frozen on first write.
    """
    mine = mine or set()
    out: dict[str, dict] = {}
    for entry in data.lexicon("ine-pro"):
        for row in service.constructions(entry, "ine-pro"):
            base = row["base"]
            word = base["form"]
            if (base.get("known") and word not in mine) or word in NOT_A_ROOT:
                continue
            if "(" in word[1:] or " " in word:
                continue
            host = entry["word"]
            quote_text = (row.get("etym") or "").strip().rstrip(".")
            gloss = (base.get("gloss") or "").strip()
            if word in out:
                out[word]["cited_by"].append(host)
                continue
            out[word] = {
                "word": word,
                "lang": "ine-pro",
                "pos": "root",
                "gloss": [gloss] if gloss else [],
                "recon": True,
                "source": "wiktionary",
                "sources": ["wiktionary"],
                "ref": (f"Named in the etymology of {host}"
                        + (f": “{quote_text}”" if quote_text else " as this word's base")
                        + "."),
                "url": page(host),
                "cited_by": [host],
            }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args()
    existing: dict[str, dict] = {}
    if SUPPLEMENT.exists():
        with gzip.open(SUPPLEMENT, "rt", encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                existing[row["word"]] = row
    mine = {word for word, row in existing.items() if row.get("pos") == "root"}
    fresh = rows(mine)
    added = [word for word in fresh if word not in existing]
    filled = [word for word in fresh if word in existing]
    print(f"{len(fresh)} roots named by a construction, {len(added)} new")
    for word in sorted(added):
        print(f"  + {word:14} {fresh[word]['gloss'] or ''} ← {fresh[word]['cited_by'][0]}")
    if args.check:
        return 0
    for word in fresh:
        existing[word] = fresh[word]
    data.DATA.joinpath("lexicon", "_supplement").mkdir(parents=True, exist_ok=True)
    with gzip.open(SUPPLEMENT, "wt", encoding="utf-8") as fh:
        for word in sorted(existing):
            fh.write(json.dumps(existing[word], ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{len(existing)} rows → {SUPPLEMENT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
