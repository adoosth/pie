#!/usr/bin/env python3
"""Read Kroonen's Etymological Dictionary of Proto-Germanic into the model.

Input is the text of the book; either the PDF's own text layer (``pdftotext
-layout``) or a Tesseract pass.  The parser only *finds* entries: a headword in
that text has lost every macron (the ClearScan layer has no long vowels at
all), so the spelling that goes into the glossary is always the one the
project already holds for that lemma.  An entry is attached to a PGmc lemma
when the OCR stem and the lemma agree (length-blind, prefix-tolerant) and the
protomeaning overlaps the lemma's gloss; otherwise it is reported, not
imported.

    pdftotext -layout "Etymological Dictionary of Proto-Germanic - Guus Kroonen.pdf" kroonen.txt
    python tools/ingest_kroonen.py kroonen.txt -o data/lexicon/_supplement/gem-pro.jsonl.gz

Output rows carry ``source: kroonen-2013``, a page-precise ``ref`` (the
citation the word page shows), Kroonen's protomeaning as an extra gloss, and
the pre-Germanic proto-form as a quotation in ``etym``.  Nothing is invented:
a row without a matched lemma is not written.
"""
from __future__ import annotations

import argparse
import difflib
import gzip
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SOURCE = "kroonen-2013"

POS_RE = re.compile(
    r"^(?:n|m|f|c|adj|adv|prep|conj|pron|num|v|w\.v|s\.v|pret\.-pres|pret\.|int|part)\.,?"
)
HEAD_RE = re.compile(r"^[*•·]\s*(?P<head>[^\s']{1,40}?)(?:\s+(?P<n>\d)\b)?\s+(?P<rest>.*)$")
GLOSS_RE = re.compile(r"'([^']{1,120})'")
ARROW_RE = re.compile(r"(?:\uFFFD|=>|<=|::::>|⇒|→|<-|<)\s*\*?\s*(?P<pre>[A-Za-zāēīōūǭąę0-9()\-]{2,40})"
                      r"\s*\((?P<dist>[A-Za-z?]{2,5})\)")
RUNHEAD_RE = re.compile(r"^(?:\*[^\s]+\s+)?(\d{1,4})\s*$|^(\d{1,4})\s+\*[^\s]+\s*$")

POS_FAMILY = {
    "n": "noun", "m": "noun", "f": "noun", "c": "noun",
    "adj": "adj", "adv": "adv", "prep": "prep", "conj": "conj", "pron": "pron",
    "num": "num", "v": "verb", "w.v": "verb", "s.v": "verb", "pret.-pres": "verb",
    "pret.": "verb", "int": "interj", "part": "particle",
}
STOP = {"to", "the", "a", "an", "of", "and", "or", "in", "on", "with", "for", "that",
        "be", "being", "one", "id", "something", "sb", "sth", "into", "from", "by"}


def skeleton(text: str) -> str:
    """Length-blind, diacritic-blind letters of a form."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("ii", "u").replace("ü", "u").replace("ö", "o").replace("ä", "a")
    return "".join(c for c in text.lower() if c.isalpha())


def gloss_tokens(text: str) -> set[str]:
    words = [w for w in re.findall(r"[a-z]+", (text or "").lower()) if w not in STOP and len(w) > 2]
    return {w[:5] for w in words}


def clean(text: str) -> str:
    text = text.replace("\xad", "").replace("�", " ")
    return re.sub(r"\s+", " ", text).strip()


def body_pages(text: str) -> list[tuple[int | None, list[str]]]:
    pages = []
    for raw in text.split("\f"):
        lines = raw.splitlines()
        page = None
        for line in lines[:2] + lines[-2:]:
            m = RUNHEAD_RE.match(line.strip())
            if m:
                page = int(m.group(1) or m.group(2))
                break
        pages.append((page, lines))
    return pages


def is_entry(line: str) -> bool:
    m = HEAD_RE.match(line)
    if not m or m.group("head").isdigit():
        return False
    rest = re.sub(r"^[.,;]\s*", "", m.group("rest"))
    if not POS_RE.match(rest):
        return False
    return bool(GLOSS_RE.search(rest[:90]))


def parse(text: str) -> list[dict]:
    rows: list[dict] = []
    cur: dict | None = None
    for page, lines in body_pages(text):
        for line in lines:
            if is_entry(line):
                if cur:
                    rows.append(cur)
                m = HEAD_RE.match(line)
                rest = m.group("rest")
                pos = POS_RE.match(re.sub(r"^[.,;]\s*", "", rest))
                raw_gloss = GLOSS_RE.search(rest[:140])
                gloss = clean(raw_gloss.group(1)) if raw_gloss else ""
                gloss = re.split(r"\s+[-–—]\s+", gloss)[0]
                cur = {
                    "head": clean(m.group("head").strip("*")),
                    "pos": (pos.group(0).rstrip(".,") if pos else ""),
                    "gloss": gloss,
                    "page": page,
                    "text": clean(rest),
                }
                continue
            if cur is not None:
                cur["text"] += " " + clean(line)
    if cur:
        rows.append(cur)
    for row in rows:
        m = ARROW_RE.search(row["text"])
        row["pre"] = clean(m.group("pre")) if m else ""
        row["dist"] = (m.group("dist") if m else "")
        row["text"] = row["text"][:600]
    return rows


def load_lexicon(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def index_by_skeleton(entries: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        key = skeleton(entry.get("word", ""))
        if key:
            out[key].append(entry)
    return out


def score(entry: dict, lemma: dict) -> float:
    """How well Kroonen's protomeaning matches the lemma's own gloss."""
    a = gloss_tokens(entry["gloss"])
    if not a:
        return 0.0
    b: set[str] = set()
    for gloss in lemma.get("gloss") or []:
        b |= gloss_tokens(gloss)
    if not b:
        return 0.0
    hit = len(a & b)
    base = hit / min(len(a), len(b)) if hit else 0.0
    # A gloss recorded only by Wiktionary's etymology often carries the meaning
    # there; it is weaker evidence, so it counts half.
    if hit < 2 and entry["pos"] and lemma.get("pos"):
        if POS_FAMILY.get(entry["pos"]) == lemma["pos"]:
            base += 0.1
    return base


def candidates(entry: dict, index: dict[str, list[dict]], limit: int = 40) -> list[tuple[float, dict]]:
    key = skeleton(entry["head"])
    if len(key) < 3:
        return []
    found: list[tuple[float, dict]] = []
    for cand_key, lemmas in index.items():
        if len(cand_key) < 3 or cand_key[:2] != key[:2]:
            continue
        if not (cand_key.startswith(key) or key.startswith(cand_key)):
            continue
        for lemma in lemmas:
            found.append((score(entry, lemma), lemma))
    found.sort(key=lambda x: (-x[0], len(x[1].get("word", ""))))
    return found[:limit]


def fuzzy_candidates(entry: dict, index: dict[str, list[dict]], cutoff: float = 0.82) -> list[tuple[float, dict]]:
    """Second chance for a stem the OCR mangled (``agalaitja-`` for *-ijaz-).

    Only forms that are already close on a length-blind skeleton are tried, and
    the protomeaning must still agree — an edit distance by itself is never
    evidence that two words are the same word.
    """
    key = skeleton(entry["head"])
    if len(key) < 3:
        return []
    near = difflib.get_close_matches(key, list(index), n=6, cutoff=cutoff)
    found = [(score(entry, lemma), lemma) for cand in near for lemma in index[cand]]
    found.sort(key=lambda x: (-x[0], len(x[1].get("word", ""))))
    return found


def best_match(entry: dict, index: dict[str, list[dict]]) -> tuple[dict | None, float, str]:
    for how, rows in (("stem", candidates(entry, index)), ("fuzzy", fuzzy_candidates(entry, index))):
        if not rows:
            continue
        top_score, top = rows[0]
        # A second lemma with the same score and the same word is a homograph
        # (two parts of speech); taking the first is safe. Anything else at the
        # same score is a real ambiguity and is left to the reader.
        rivals = [l for s, l in rows[1:] if s == top_score and l.get("word") != top.get("word")]
        floor = 0.34 if how == "stem" else 0.5
        if top_score >= floor and not rivals:
            return top, top_score, how
        return None, top_score, how
    return None, 0.0, ""


def build(rows: list[dict], lex_path: Path) -> tuple[list[dict], dict]:
    lexicon = load_lexicon(lex_path)
    index = index_by_skeleton(lexicon)
    out: list[dict] = []
    report = {"parsed": len(rows), "matched": 0, "fuzzy": 0, "weak": [], "unmatched": [], "preforms": 0}
    seen: set[tuple[str, str]] = set()
    for entry in rows:
        lemma, sc, how = best_match(entry, index)
        if not lemma:
            (report["weak"] if sc else report["unmatched"]).append(
                {"head": entry["head"], "pos": entry["pos"], "gloss": entry["gloss"],
                 "page": entry["page"], "score": round(sc, 2)})
            continue
        word = lemma["word"]
        page = f"Kroonen 2013: {entry['page']}" if entry["page"] else "Kroonen 2013"
        ref = f"{page}, s.v. *{entry['head']}"
        # The pre-Germanic proto-form is a quotation from the entry, so it sits
        # in the citation, not in `etym`: the etymology field drives the
        # construction and reading parsers, which read Wiktionary's prose, and
        # an OCR'd sentence must not be fed to them.
        if entry["pre"]:
            ref += f" (from {entry['pre']}" + (f", {entry['dist']}" if entry["dist"] else "") + ")"
            report["preforms"] += 1
        row = {
            "word": word,
            "lang": "gem-pro",
            "gloss": [entry["gloss"]] if entry["gloss"] else [],
            "source": SOURCE,
            "ref": ref,
            "page": entry["page"],
            "kroonen_head": entry["head"],
            "match_score": round(sc, 2),
            "match_how": how,
        }
        if lemma.get("pos"):
            row["pos"] = lemma["pos"]
        if entry["pre"]:
            row["kroonen_pre"] = f"{entry['pre']}" + (f" ({entry['dist']})" if entry["dist"] else "")
        key = (word, entry["gloss"])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
        report["matched"] += 1
        report["fuzzy"] += how == "fuzzy"
    return out, report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("-o", "--out", default=str(ROOT / "data" / "lexicon" / "_supplement" / "gem-pro.jsonl.gz"))
    ap.add_argument("--lexicon", default=str(ROOT / "data" / "lexicon" / "gem-pro.jsonl.gz"))
    ap.add_argument("--report", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--audit", default="", help="write a TSV of every match for review")
    args = ap.parse_args()
    rows = parse(Path(args.text).read_text(encoding="utf-8", errors="replace"))
    out, report = build(rows, Path(args.lexicon))
    print(f"{report['parsed']} entries parsed, {report['matched']} matched to a glossary lemma "
          f"({report['fuzzy']} through the fuzzy pass), "
          f"{report['preforms']} carry a pre-Germanic form, "
          f"{len(report['weak'])} weak, {len(report['unmatched'])} unmatched")
    if args.report:
        Path(args.report).write_text(json.dumps({"report": {k: v for k, v in report.items()
                                                            if k in ("parsed", "matched", "fuzzy", "preforms")},
                                                 "weak": report["weak"][:400],
                                                 "unmatched": report["unmatched"][:400]},
                                                ensure_ascii=False, indent=1), encoding="utf-8")
    if args.audit:
        with open(args.audit, "w", encoding="utf-8") as fh:
            fh.write("book_head\tword\tscore\thow\tpage\tgloss\n")
            for row in out:
                fh.write(f"{row['kroonen_head']}\t{row['word']}\t{row['match_score']}\t"
                         f"{row['match_how']}\t{row.get('page', '')}\t{row['gloss'][0]}\n")
    if args.dry_run:
        return 0
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_path, "wt", encoding="utf-8") as fh:
        for row in out:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{len(out)} rows → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
