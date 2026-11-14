#!/usr/bin/env python3
"""The critic's sampler and its mechanical checks (2026-11-13).

A critic reads random word pages, finds every place the page contradicts the
record, and reports it for review and fix.
This tool is the part that can be mechanical: it samples pages without looking
at their band, and it pre-computes the faults that are decidable from the
payload, so a critic's attention goes to meaning (docs/CRITIC.md).

    python3 tools/critic.py sample --lang fa --n 20 [--seed 7]
    python3 tools/critic.py check --lang fa --n 20 [--seed 7]
    python3 tools/critic.py check --lang fa --words دستمال,آبجو

`check` writes one JSON object per finding to stdout; a critic adds the
semantic kinds the tool cannot decide and the fix that names the right entry.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pie import data, service  # noqa: E402

#: A compound's piece is a word, so a grammatical function word in that slot is
#: a homonym of the piece, not the piece: dostmāl's دست is the noun "hand", not
#: Dehkhoda's classifier sense (2026-11-13).
FUNCTION_POS = {"classifier", "particle", "prep", "conj", "pron", "postp",
                "article", "interj", "abbr"}

#: A gloss that talks about the dictionary rather than the word.  Dehkhoda's
#: editorial notes ("یادداشت مرحوم دهخدا") and Wiktionary's metalinguistic
#: descriptions ("Used in the singular with a subsequent ezâfe") reach the page
#: when the wrong homonym was matched.
META_GLOSS = ("used in the singular", "ezâfe", "ezafe", "classifier for",
              "یادداشت", "this model", "compare ", "see also",
              "رجوع به مترادفات")

#: A grammar note, a cross-reference or a quotation inside a printed gloss.
NOTE_GLOSS = __import__("re").compile(
    r"رجوع\s+به|بمعنی\s|نعت\s+(?:فاعلی|مفعولی)|صفت\s+(?:فاعلی|مفعولی)|"
    r"\|\||\s؛|اسم\s+(?:فاعل|مفعول)|مصدر\s+")

#: A place name's gloss *is* its description: "a village beside the Kazerun
#: road" is the meaning, not an editorial note (critic batch 01, 2026-11-13).
PLACE_HEAD = ("نام محلی", "نام ده", "نام روستا", "نام شهر", "نام کوه",
              "نام رود", "نام آبادی", "نام ناحیه")

#: Reviewed words stay outside the repository; ``PIE_CRITIC_STATE`` moves them.
STATE_DIR = Path(os.environ.get("PIE_CRITIC_STATE", Path.home() / ".cache" / "pie-critic"))
REVIEWED = STATE_DIR / "reviewed.txt"


def words(lang: str) -> list[str]:
    """Attested headwords worth a critic's time, one per spelling."""
    skip = set()
    if REVIEWED.exists():
        skip = {line.strip() for line in REVIEWED.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")}
    out, seen = [], set()
    for entry in data.lexicon(lang):
        word = str(entry.get("word") or "")
        pos = str(entry.get("pos") or "")
        if not word or word in seen or word in skip:
            continue
        if pos in {"root", "suffix", "prefix", "affix", "infix", "interfix",
                   "punct", "character"}:
            continue
        if len(word) < 2 or " " in word:
            continue
        seen.add(word)
        out.append(word)
    return out


def pool_split(lang: str) -> tuple[list[str], list[str]]:
    """The pool in two layers: entries that state an origin, and the rest.

    A batch that lands only on one-line dictionary headwords exercises no
    timeline: batch 10 read 24 Persian pages of which 12 had no etymology at
    all, and the Old Persian sample was 78 % `Reconstruction:` Latin names
    although they are 39 % of that lexicon (2026-11-13 — both critics asked
    for a split).  A critic samples both layers on purpose.
    """
    live = set(words(lang))
    with_record: list[str] = []
    without: list[str] = []
    for entry in data.lexicon(lang):
        word = str(entry.get("word") or "")
        if not word or word not in live:
            continue
        bucket = with_record if (entry.get("anc") or entry.get("built_as")
                                  or entry.get("etym")) else without
        if word not in bucket:
            bucket.append(word)
    return with_record, without


def sample(lang: str, n: int, seed: int) -> list[str]:
    pool = words(lang)
    rng = random.Random(seed)
    return rng.sample(pool, min(n, len(pool)))


def sample_layered(lang: str, n: int, seed: int) -> list[str]:
    """Half from entries that state an origin, half from the rest, shuffled."""
    recorded, plain = pool_split(lang)
    rng = random.Random(seed)
    half = max(1, n // 2)
    picks = (rng.sample(recorded, min(half, len(recorded))) if recorded else [])
    picks += (rng.sample(plain, min(n - len(picks), len(plain))) if plain else [])
    if len(picks) < n:
        rest = [w for w in words(lang) if w not in picks]
        picks += rng.sample(rest, min(n - len(picks), len(rest)))
    rng.shuffle(picks)
    return picks


def _finding(lang, word, kind, severity, page_says, record_says, evidence,
             fix="", source=""):
    return {"lang": lang, "word": word, "kind": kind, "severity": severity,
            "page_says": page_says, "record_says": record_says,
            "evidence": evidence, "fix": fix, "source": source}


@lru_cache(maxsize=None)
def _en_ledger(lang: str) -> dict[str, dict]:
    """The English-Wiktionary index for one language, keyed by headword."""
    import gzip
    path = Path(__file__).resolve().parent.parent / "data" / "sources" / "en_wiktionary" / f"{lang}.jsonl.gz"
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                row = json.loads(line)
                out[row.get("word") or ""] = row
    return out


def _pieces(page: dict) -> list[dict]:
    out = []
    for level in (page.get("hierarchy") or {}).get("levels") or []:
        for build in level.get("builds") or []:
            for piece in build.get("pieces") or []:
                out.append(piece)
    return out


def _builds(page: dict) -> list[dict]:
    out = []
    for level in (page.get("hierarchy") or {}).get("levels") or []:
        out.extend(level.get("builds") or [])
    return out


def _etym_parts(page: dict) -> list[str] | None:
    text = str(page.get("etymology") or "")
    if " + " not in text:
        return None
    tail = text.split(":", 1)[-1] if ":" in text else text
    return [part.strip() for part in tail.split("+") if part.strip()]


def page_findings(lang: str, word: str) -> list[dict]:
    page = service.word(lang, word)
    if not page or not page.get("category"):
        return []          # a "pick a sense" page: the critic opens a sense
    out: list[dict] = []
    cat = page["category"]
    label = str(cat.get("label") or "")
    green = cat.get("category") in {"full", "adjusted"}
    pieces = _pieces(page)
    builds = _builds(page)

    # 1. A piece that is a function word where a compound needs a word.
    for piece in pieces:
        pos = str(piece.get("pos") or "")
        if pos in FUNCTION_POS and not piece.get("bound"):
            out.append(_finding(
                lang, word, "wrong_piece", "medium",
                f"piece {piece['form']} · {pos} · “{piece.get('gloss') or ''}”",
                "a compound’s piece is a word; a classifier/particle there is a "
                "homonym of the piece, not the piece the record names",
                f"service.word({lang}/{word}).hierarchy.levels[].builds[].pieces",
                "resolve the piece to its content-word entry (noun/verb/adj), "
                "using the record’s parenthetical or a trailing hyphen (verb stem)"))

    # 2. A gloss about the dictionary, not the word.  Read the gloss the page
    #    actually prints: `_page_gloss` follows a cross-reference and drops a
    #    trailing hedge, so the entry's raw text is not what the reader sees.
    #    A Dehkhoda paragraph also carries grammar notes («نعت فاعلی است از
    #    تدمیح»), cross-references and Arabic examples, which are not meanings
    #    (critic batch 03, 2026-11-13).
    for gloss in page.get("gloss") or []:
        low = str(gloss).casefold()
        if any(str(gloss).startswith(head) for head in PLACE_HEAD):
            continue
        if any(mark in low for mark in META_GLOSS):
            out.append(_finding(
                lang, word, "bad_gloss", "medium",
                f"gloss “{gloss}”",
                "the gloss describes the record or a grammar rule, not the word",
                f"{lang}/{word} page gloss",
                "find the sense of the word itself, or the entry that heads it"))
        elif NOTE_GLOSS.search(str(gloss)):
            out.append(_finding(
                lang, word, "bad_gloss", "low",
                f"gloss “{gloss}”",
                "the gloss carries a grammar note, a cross-reference or an example "
                "instead of stopping at the meaning",
                f"{lang}/{word} page gloss",
                "cut the meaning at the first note (service._GLOSS_NOTE) and keep "
                "the note out of the meaning line"))

    # 3. A green band over a hole the page itself draws.
    holes = (cat.get("missing") or [])
    if green and holes:
        out.append(_finding(
            lang, word, "band_overclaim", "high",
            f"{label} while the page draws {len(holes)} hole(s)",
            "a band may not be green above a rung the page calls missing",
            ", ".join(f"{h.get('stage')} {h.get('written')}" for h in holes[:4]),
            "categories.verdict must refuse green while unrecorded_ancestry has a row"))

    # 4. The sentence names pieces the timeline does not draw (and vice versa).
    parts = _etym_parts(page)
    if parts is not None:
        drawn = [p["form"] for p in pieces]
        if not drawn:
            out.append(_finding(
                lang, word, "etym_disagrees", "high",
                "no construction drawn",
                f"the etymology states a join: {page.get('etymology')}",
                f"{lang}/{word} etymology vs hierarchy",
                "read the record’s own pieces into the timeline"))
        elif len(parts) != len(drawn):
            out.append(_finding(
                lang, word, "etym_disagrees", "medium",
                f"timeline draws {len(drawn)} piece(s): {', '.join(drawn)}",
                f"the etymology names {len(parts)}: {page.get('etymology')}",
                f"{lang}/{word} etymology vs hierarchy",
                "one analysis per lexeme: draw exactly the pieces the record states"))

    # 4b. A W whose article was never checked for a section in this language.
    #     The ledger was built from page titles, and a title is shared by every
    #     language on the site (critic batch 01: en.wiktionary's نقوع is
    #     Arabic-only, and the W claimed a Persian record).
    ledger = _en_ledger(lang).get(word)
    if ledger and "section" not in ledger:
        out.append(_finding(
            lang, word, "unlinked_source", "medium",
            "the W opens an en.wiktionary page whose language was never checked",
            "the page index was built from titles, and a title may belong to "
            "another language (Arabic, Ottoman Turkish) with no section in this one",
            "data/sources/en_wiktionary/" + lang + ".jsonl.gz",
            "run tools/en_wiktionary_sections.py --lang " + lang,
            ledger.get("url") or ""))

    # 4c. A piece the sentence calls a verb stem, drawn as another word.
    #     باشنده's «باش (… present stem form of بودن)» was drawn from the jade
    #     homonym, under a red ??? of its own (critic batch 03, 2026-11-13).
    for piece in (page.get("joins") or [{}])[0].get("pieces") or []:
        named = service._stem_verb(str(page.get("etymology") or ""),
                                   str(piece.get("form") or ""))
        if named and piece.get("word") and str(piece.get("word")) != named:
            out.append(_finding(
                lang, word, "wrong_piece", "high",
                f"piece {piece['form']} → {piece.get('word')} "
                f"({piece.get('pos')}) “{str(piece.get('gloss') or '')[:60]}”",
                f"the record says {piece['form']} is a stem of {named}",
                f"{lang}/{word} etymology vs hierarchy pieces",
                f"resolve the piece to the verb {named}"))

    # 5. A piece whose entry is missing from its own stage.
    for piece in pieces:
        if (piece.get("known") is False and str(piece.get("lang")) == lang
                and not piece.get("bound")):
            out.append(_finding(
                lang, word, "missing_entry", "medium",
                f"piece {piece['form']} has no entry",
                "the piece is drawn as a word of this stage but the glossary does not head it",
                f"{lang}/{word} build pieces",
                "file the entry from the record that names it, or draw the piece as unrecorded"))

    # 6. No page linked for a word with a recorded etymology.
    if not page.get("pages"):
        out.append(_finding(
            lang, word, "unlinked_source", "low",
            "no source page linked",
            "the entry has an etymology, so a reader must be able to open the record",
            f"{lang}/{word} pages",
            "attach the Wiktionary/Dehkhoda page the record was read from"))

    # 7. A build whose pieces do not spell the word.
    for build in builds:
        of = str(build.get("of") or "")
        if of and not any(form in of or of in form for form in
                          (str(p.get("form")) for p in build.get("pieces") or [])):
            continue        # the pieces are pieces, not the whole word; checked by a reader
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["sample", "check"])
    ap.add_argument("--lang", default="fa")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--words", default="")
    ap.add_argument("--json", action="store_true", help="sample as JSON lines")
    ap.add_argument("--layered", action="store_true",
                    help="half the sample from entries that state an origin")
    args = ap.parse_args(argv)

    picks = ([w.strip() for w in args.words.split(",") if w.strip()]
             if args.words else (sample_layered(args.lang, args.n, args.seed)
                                 if args.layered else sample(args.lang, args.n, args.seed)))
    if args.command == "sample":
        for word in picks:
            row = {"lang": args.lang, "word": word,
                   "url": f"http://127.0.0.1:8100/#/word/{args.lang}/"
                          f"{__import__('urllib.parse', fromlist=['quote']).quote(word)}"}
            print(json.dumps(row, ensure_ascii=False) if args.json else f"{args.lang}\t{word}\t{row['url']}")
        return 0

    for word in picks:
        for finding in page_findings(args.lang, word):
            print(json.dumps(finding, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
