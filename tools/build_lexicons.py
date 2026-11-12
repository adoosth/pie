#!/usr/bin/env python3
"""Build compact per-language glossaries and the cross-language link graph.

Input: kaikki.org / Wiktextract JSONL dumps (one file per language) in
``--src`` (default /tmp/kaikki).  Output, under ``data/``:

  lexicon/<lang>.jsonl.gz    one record per lemma: word, POS, glosses,
                             etymology, ancestry chain, cognate-set id
  cognate_sets/ine-pro.jsonl.gz  one record per PIE etymon with its descendants
  graph/edges.jsonl.gz       child → parent word links

The ancestry data is Wiktionary's own machine-readable inheritance information
(``{{inh}}``, ``{{der}}``, ``{{bor}}`` templates), not a guess of ours.
"""
from __future__ import annotations

import argparse
import gzip
import html
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pie import etymtext  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

TREE_NAMES: set[str] = set()
_lex = ROOT / "data" / "language_names.json"
if _lex.exists():
    TREE_NAMES = {v["name"] for v in json.loads(_lex.read_text(encoding="utf-8"))["languages"].values()}

# kaikki dump name → our language id
DUMP_TO_ID = {
    "ProtoIndoEuropean": "ine-pro",
    "ProtoIndoIranian": "iir-pro",
    "ProtoIranian": "ira-pro",
    "ProtoIndoAryan": "inc-pro",
    "ProtoGermanic": "gem-pro",
    "ProtoWestGermanic": "gmw-pro",
    "ProtoCeltic": "cel-pro",
    "ProtoSlavic": "sla-pro",
    "ProtoBaltoSlavic": "ine-bsl-pro",
    "ProtoTocharian": "ine-toc-pro",
    "OldHighGerman": "goh",
    "MiddleHighGerman": "gmh",
    "OldEnglish": "ang",
    "MiddleEnglish": "enm",
    "Gothic": "got",
    "OldNorse": "non",
    "OldPersian": "peo",
    "Persian": "fa",
    "Sanskrit": "sa",
    "AncientGreek": "grc",
    "Greek": "el",
    "Latin": "la",
    "Italian": "it",
    "German": "de",
    "English": "en",
    "Hittite": "hit",
    "Oscan": "osc",
    "OldIrish": "sga",
    "OldChurchSlavonic": "chu",
    "Lithuanian": "lt",
    "TocharianB": "txb",
    "Armenian": "hy",
    "OldArmenian": "xcl",
    "Albanian": "sq",
}

PROTO = {
    "ine-pro", "iir-pro", "ira-pro", "inc-pro", "gem-pro", "gmw-pro", "cel-pro",
    "sla-pro", "ine-bsl-pro", "ine-toc-pro", "ine-ana-pro", "itc-pro", "grk-pro",
    "ira-mid-pro", "ira-wn-pro", "gem-nor-pro",
}

#: ``uder`` is the older "From the Arabic X" template: it names a source
#: language and a form without saying whether the word was borrowed or
#: inherited, so it is kept as *derived* — the relation the record is sure of
#: (251 Persian entries, 2026-11-10).
ANCESTRY_TEMPLATES = {"inh", "inh+", "der", "der+", "bor", "bor+", "lbor", "slbor",
                      "cal", "calque", "uder"}
TAG_RE = re.compile(r"<[^>]+>")


def is_reconstruction(entry: dict) -> bool:
    """Whether Wiktionary keeps this entry in its Reconstruction: namespace.

    A reconstructed word is not a word a text spells, and the interface must
    never colour it green (2026-11-08: Old Persian *madu is a
    reconstruction on Wiktionary and was shown as attested here). Wiktextract
    carries the flag twice — the sense tag and the ``*`` headword — and either
    is enough. All 237 Latin-titled Old Persian entries are reconstructions,
    which is why the script test alone could not tell them apart from
    transliterations of cuneiform words.
    """
    for sense in entry.get("senses") or []:
        if "reconstruction" in (sense.get("tags") or []):
            return True
    for tpl in entry.get("head_templates") or []:
        if str(tpl.get("expansion") or "").startswith("*"):
            return True
    return False


def is_form_only(entry: dict) -> bool:
    """Whether every sense of this entry is an inflected form of another word.

    Wiktextract stores inflected forms as their own entries (``book`` "simple
    past of bake"), and an inflected form is not a word of the vocabulary: the
    lemma it belongs to is.  Keeping them would count one lexeme many times in
    the coverage bands and put a second *book* on the page of the first
    (2026-11-09).
    """
    senses = entry.get("senses") or []
    return bool(senses) and all(s.get("form_of") or s.get("alt_of") for s in senses)


def clean(text: str | None, limit: int = 400) -> str:
    if not text:
        return ""
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


#: How an {{etymon}} keyword names a relation.  The template is the modern,
#: machine-readable etymology (``{{etymon|ira-pro|inh|iir-pro>*dáwkšati|inh|
#: ine-pro>*déwk-s-eti}}``) and it states the *chain*, not just one hop.
_ETYMON_REL = {
    "inh": "inherit", "inh+": "inherit", "inherited": "inherit",
    "der": "derived", "der+": "derived", "derived": "derived",
    "bor": "borrow", "bor+": "borrow", "lbor": "borrow", "slbor": "borrow",
    "obor": "borrow", "ubor": "borrow", "cal": "calque", "calque": "calque",
    "root": "root",
}

#: The templates that build a word out of pieces.  ``1`` is the language the
#: *product* is written in, ``2`` the first piece, ``3`` the next, and a gloss
#: for the piece in arg ``n`` sits in ``t{n-1}`` / ``pos{n-1}`` (the numbering
#: starts at the second argument, which is why ``t1`` describes arg 2).
#: The construction keywords an ``{{ety}}`` line may name in place of a chain.
_ETY_CONSTRUCTION = {
    "af": "affix", "affix": "affix", "com": "compound", "compound": "compound",
    "suf": "suffix", "suffix": "suffix", "pre": "prefix", "prefix": "prefix",
    "infix": "infix",
}

_FORMATION_TEMPLATES = {
    "suf": "suffix", "suffix": "suffix", "af": "affix", "affix": "affix",
    "prefix": "prefix", "pre": "prefix", "compound": "compound",
    "com": "compound", "infix": "infix",
}


def _split_term(text: str) -> tuple[str, str]:
    """``iir-pro:*dáwkšati`` → ``("iir-pro", "*dáwkšati")``; ``<id:fire>`` dropped."""
    lang, _, word = str(text).partition(":")
    word = re.sub(r"<[^>]*>", "", word).strip()
    return lang.strip(), word.strip()


def _etymon_chain(args: dict, own: str = "") -> list[list[str]]:
    """The whole ``{{etymon}}`` chain, one triple per hop.

    The template alternates a keyword (``:inh``, ``:der``, ``:bor`` …) with a
    value that may itself nest the rest of the chain
    (``pal:𐭓𐭐𐭃<ety:inh<peo:𐎱𐎡𐎫𐎠>>``), so the value is read by
    ``etymtext.parse_chain`` and the keyword argument is the default relation
    for a hop that names none.
    """
    out: list[list[str]] = []
    keyword = ""
    n = 2
    while f"{n}" in args:
        value = str(args.get(f"{n}") or "").strip()
        n += 1
        if not value:
            continue
        if value.startswith(":"):
            keyword = value[1:].rstrip("+")
            continue
        default = _ETYMON_REL.get(keyword.replace("+", ""), "inherit")
        for row in etymtext.parse_chain(value, own, keyword):
            if row["pieces"]:
                continue
            out.append([row["lang"], row["term"], _ETYMON_REL.get(row["rel"], default)])
    return out


def ancestry(entry: dict) -> list[list[str]]:
    out: list[list[str]] = []
    own = entry.get("lang_code")
    for tpl in entry.get("etymology_templates") or []:
        name = tpl.get("name", "")
        args = tpl.get("args") or {}
        if not isinstance(args, dict):
            continue
        if name in ANCESTRY_TEMPLATES:
            # ``{{inh|ira-pro|ine-pro||*déwk-s-eti}}`` writes the form in arg 4
            # because arg 3 is the (empty) on-page term. Reading only arg 3
            # dropped the very link the entry states: dáwxšati lost both its
            # Proto-Indo-Iranian and its Proto-Indo-European ancestors and the
            # ladder started at the root *dewk- instead (2026-11-09).
            src_lang = args.get("2") or args.get("1")
            # ``{{inh|fa|pal|tr=z’hm|ts=zaxm}}`` puts the ancestor in the
            # dictionary's own transliteration (``tr``) and its transcription
            # (``ts``) instead of in argument 3 — Middle Persian زخم, تره,
            # خروس and about sixty more were dropped for that reason
            # (2026-11-10).  The transcription is the form the laws can run on
            # and the spelling is what the page prints.
            src_word = args.get("3") or args.get("4") or args.get("ts") or args.get("tr")
            rel = ("borrow" if name.startswith(("bor", "lbor", "slbor"))
                   else "calque" if name in {"cal", "calque"}
                   else "inherit" if name.startswith("inh") else "derived")
            if src_lang and src_word:
                word = clean(etymtext.visible_term(str(src_word)), 60)
                if word and word != "-" and not word.startswith(":") and src_lang != own:
                    out.append([src_lang, word, rel])
        elif name in ("etymon", "ety"):
            # ``{{ety|fa|:bor|ar:حَلَال}}`` is the single-line form of an
            # ``{{etymon}}`` tree, and it is the most common one on Persian
            # pages: the keyword and the term alternate in arguments 2, 3, 4 …
            # (2026-11-09).  Reading only ``etymon`` dropped 2,492 Persian
            # words whose origin Wiktionary states plainly.
            for lang, word, rel in _etymon_chain(args, own or ""):
                # A same-stage link is kept: a Proto-Indo-European word built
                # on a Proto-Indo-European root states a base the construction
                # parser checks against, even though no rung can hold it. A
                # link to the word itself is not a statement (2026-11-09).
                if not word or word.startswith(":") or word == entry.get("word"):
                    continue
                out.append([lang, clean(word, 60), rel])
        elif name == "root":
            # {{root|en|ine-pro|*ph₂tḗr}} — arg 1 is the *entry* language.
            src_lang, src_word = args.get("2"), args.get("3")
            if src_lang == own:
                src_lang, src_word = args.get("3"), args.get("4")
            if src_lang and src_word and src_word != entry.get("word"):
                word = clean(etymtext.visible_term(str(src_word)), 60)
                if word and not word.startswith(":"):
                    out.append([src_lang, word, "root"])
    # de-duplicate, keep order
    seen = set()
    uniq = []
    for item in out:
        key = tuple(item)
        if key not in seen:
            seen.add(key)
            uniq.append(item)
    return uniq


def etymon_records_origin(entry: dict) -> bool:
    """Whether an ``{{etymon}}`` template states where the word comes from.

    The corpus is "glossaries of words that record an origin". An ``{{etymon}}``
    tree is such a record even when it names no ancestor at a modelled stage —
    English *lexicography* is ``lexico- + -graphy``, and a Middle Persian word
    whose origin is a named but unmodelled variety is still a word with a
    stated etymology. Reading the template's own chain (not just its first two
    arguments) is what makes this test true of the entries the tree really
    covers, and false of an entry with no etymology at all (2026-11-09).

    A bare ``{{af}}``/``{{compound}}`` template is not used as the test: it
    applies to a quarter of a million English entries and would redefine the
    corpus rather than keep it whole.
    """
    own = entry.get("lang_code")
    for tpl in entry.get("etymology_templates") or []:
        if tpl.get("name") != "etymon":
            continue
        args = tpl.get("args") or {}
        if not isinstance(args, dict):
            continue
        for n in range(2, 12):
            value = str(args.get(f"{n}") or "").strip()
            if not value or value.startswith(":"):
                continue
            if any(row["term"] for row in etymtext.parse_terms(value, own or "")):
                return True
    return False


def formations(entry: dict, anc: list[list[str]]) -> list[dict]:
    """The pieces a record says a *form* is built from, at the form's own stage.

    ``dáwxšati`` is not built from *dewk-: the entry's PIE ancestor
    *déwk-s-eti is (``{{suf|ine-pro|*dewk-|t1=to pull, draw|*seti}}``).  The
    timeline can only say so if the record keeps the formation beside the form
    it builds, so each row names ``lang``, the ``of`` form it produces when
    that can be identified, and the ordered pieces with the dictionary's own
    gloss of each.  Nothing is inferred from prose: only a template that
    states the pieces makes a row (2026-11-09).
    """
    own = entry.get("lang_code")
    word = str(entry.get("word") or "")
    out: list[dict] = []
    for tpl in entry.get("etymology_templates") or []:
        if tpl.get("name") != "etymon":
            continue
        args = tpl.get("args") or {}
        if not isinstance(args, dict):
            continue
        for n in range(2, 12):
            value = str(args.get(f"{n}") or "").strip()
            if not value or value.startswith(":"):
                continue
            terms = etymtext.parse_terms(value, own or "")
            pieces = [[t["term"], ""] for t in terms if t["term"]]
            # Only a construction this entry's own word wears.  The first term
            # of a nested tree is the form it builds (or the ancestor); the
            # pieces follow it, and a two-piece row needs no guess about which.
            if len(pieces) >= 3 and terms[0]["term"] and terms[0]["lang"] == own:
                out.append({"lang": own, "kind": "affix", "of": word,
                            "pieces": pieces[1:]})
    for tpl in entry.get("etymology_templates") or []:
        name = tpl.get("name", "")
        if name == "ety":
            # ``{{ety|fa|:af|ایتالیا|ـیی}}`` is the single-line spelling of an
            # affix construction, and it was read as a chain (which a bare
            # Persian piece never is) and then dropped: ایتالیایی, زیستشناسی
            # and 1,088 more Persian words that state their own pieces were
            # missing from the glossary (2026-11-10).
            args = tpl.get("args") or {}
            if not isinstance(args, dict):
                continue
            kind = ""
            pieces: list[list[str]] = []
            n = 2
            while f"{n}" in args:
                value = str(args.get(f"{n}") or "").strip()
                n += 1
                if not value:
                    continue
                if value.startswith(":"):
                    kind = _ETY_CONSTRUCTION.get(value[1:].rstrip("+"), "")
                    continue
                if not kind:
                    continue
                form = clean(etymtext.visible_term(value), 60)
                if not form:
                    continue
                pieces.append([form, clean(str(args.get(f"t{n - 2}") or ""), 80)])
            own_lang = str(args.get("1") or "").strip()
            row = {"lang": own, "kind": kind, "of": word, "pieces": pieces}
            # The dump repeats an etymology line once per sense, and the same
            # construction must not be counted twice on the page.
            if kind and pieces and own_lang in ("", own) and row not in out:
                out.append(row)
            continue
        kind = _FORMATION_TEMPLATES.get(name)
        if not kind:
            continue
        args = tpl.get("args") or {}
        if not isinstance(args, dict):
            continue
        lang = str(args.get("1") or "").strip()
        pieces: list[list[str]] = []
        n = 2
        while f"{n}" in args:
            form = clean(str(args.get(f"{n}") or ""), 60)
            if form:
                gloss = clean(str(args.get(f"t{n - 1}") or args.get(f"pos{n - 1}") or ""), 80)
                pieces.append([form, gloss])
            n += 1
        if lang != own and len(pieces) < 2:
            # A "suffix" with one piece in another language states nothing the
            # record does not already say as ancestry.
            continue
        if len(pieces) < 2:
            continue
        # Which form does this build?  In the word's own language it is the
        # headword; above it, the one ancestor the record keeps for that stage
        # that is not a bare root.
        of = word
        if lang != own:
            candidates = [w for lg, w, rel in anc if lg == lang and rel != "root"]
            of = candidates[0] if len(candidates) == 1 else ""
        out.append({"lang": lang, "kind": kind, "of": of,
                    "pieces": pieces})
    return out


def romanisations(entry: dict) -> list[str]:
    """Wiktionary's own transliterations, which the rule engine can compare with.

    Persian پدر, Greek πατήρ and Armenian հայր are written in their own script,
    but the sound laws produce Latin-script phonology; without a romanisation the
    word page could never show a match even when the derivation is exact.
    """
    out: list[str] = []
    for form in entry.get("forms") or []:
        if "romanization" not in (form.get("tags") or []):
            continue
        value = clean(form.get("form"), 80)
        if not value or any(ch in value for ch in " ,;") or value in out:
            continue
        out.append(value)
    return out


def glosses(entry: dict, limit: int = 3) -> list[str]:
    out: list[str] = []
    for sense in entry.get("senses") or []:
        for g in sense.get("glosses") or []:
            g = clean(g, 120)
            if g and g not in out:
                out.append(g)
            if len(out) >= limit:
                return out
    return out


def walk_descendants(rows: list, path: list[str]):
    """Yield (lang, word, roman, sense, path) from a PIE descendants tree."""
    for row in rows or []:
        lang = row.get("lang_code")
        word = row.get("word")
        if not lang or not word:
            continue
        here = path + [f"{lang}:{word}"]
        yield lang, word, row.get("roman"), row.get("sense"), here
        yield from walk_descendants(row.get("descendants") or [], here)


def mark_reconstructions(src: Path, only: list[str] | None = None) -> bool:
    """Backfill ``recon`` on the built glossaries without rebuilding them.

    A full rebuild re-reads 7.8 GB of Wiktextract; this pass reads each dump
    once, keeps only the words the glossary already has, and rewrites the
    glossary rows that Wiktionary keeps in its Reconstruction: namespace. It is
    idempotent, and ``build_lexicons.py`` now writes the same flag itself, so a
    later rebuild agrees with the backfilled data.
    """
    total = 0
    for dump, lang in DUMP_TO_ID.items():
        if only and lang not in only:
            continue
        if lang in PROTO:
            # Already gold by definition; see the build loop below.
            continue
        path = src / f"{dump}.jsonl"
        out_path = DATA / "lexicon" / f"{lang}.jsonl.gz"
        if not path.exists() or not out_path.exists():
            continue
        with gzip.open(out_path, "rt", encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh]
        # Match on word *and* part of speech: a homograph that is attested in
        # one part of speech (Old English *ne* adv, conj) must not take the
        # reconstruction tag from a homograph that is reconstructed (noun
        # **nē*). The flag is recomputed from scratch so a wrong one cannot
        # survive a corrected pass.
        keys = {(row["word"], row.get("pos") or "") for row in rows}
        flagged: set[tuple[str, str]] = set()
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if '"reconstruction"' not in line and '"*' not in line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = (entry.get("word"), entry.get("pos") or "")
                if key in keys and is_reconstruction(entry):
                    flagged.add(key)
        changed = 0
        for row in rows:
            want = (row["word"], row.get("pos") or "") in flagged
            if want and not row.get("recon"):
                row["recon"] = True
                changed += 1
            elif not want and row.pop("recon", None):
                changed += 1
        if changed:
            with gzip.open(out_path, "wt", encoding="utf-8") as fh:
                for row in rows:
                    fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        total += changed
        if changed or lang in ("peo", "la", "ang"):
            print(f"{lang:<10} {changed:>5} reconstruction-only entries flagged "
                  f"({len(flagged)} in the dump / {len(rows)} in the glossary)")
    print(f"total flagged: {total}")
    return True


def _text_writer(path: Path):
    """A text handle to a gzip file whose header carries no clock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return io.TextIOWrapper(gzip.GzipFile(filename=str(path), mode="wb", mtime=0),
                            encoding="utf-8", write_through=True)


def _write_gzip(path: Path, rows) -> None:
    """Write one JSON object per line, gzip stamp set to zero.

    The header timestamp is the only thing that differs between two builds of
    the same rows, and a data file that changes only because the clock moved
    buries the real diff (2026-11-08: folding one supplement rewrote the seven
    other glossaries byte for byte).
    """
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
            for row in rows:
                gz.write((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                         .encode("utf-8"))


def merge_supplements() -> None:
    """Fold ``data/lexicon/_supplement/*.jsonl.gz`` into the built glossaries.

    A supplement never overwrites an entry: it adds the words the dump does not
    have, and fills fields a matching entry lacks. Homographs are kept — the
    glossary counts entries, not headwords, so two ``Hhucráwāh`` rows (different
    parts of speech) are both a row and both a word to measure (2026-11-08).
    """
    supp_dir = DATA / "lexicon" / "_supplement"
    if not supp_dir.exists():
        return
    for sp in sorted(supp_dir.glob("*.jsonl.gz")):
        lang = sp.name.split(".")[0]
        out_path = DATA / "lexicon" / f"{lang}.jsonl.gz"
        rows: list[dict] = []
        first: dict[str, dict] = {}
        if out_path.exists():
            with gzip.open(out_path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    row = json.loads(line)
                    rows.append(row)
                    first.setdefault(row["word"], row)
        before = json.dumps(rows, ensure_ascii=False, sort_keys=True)
        added = 0
        with gzip.open(sp, "rt", encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                word = row.get("word")
                if not word:
                    continue
                cur = first.get(word)
                if cur is None:
                    rows.append(row)
                    first[word] = row
                    added += 1
                    continue
                gl = cur.setdefault("gloss", [])
                if cur.get("source") == row.get("source") == "dehkhoda":
                    # The dictionary's own line is re-read as the reader is
                    # corrected, so the newest reading replaces the old one
                    # instead of piling a second, staler gloss beside it
                    # (2026-11-10).
                    cur["gloss"] = list(row.get("gloss") or [])
                    gl = cur["gloss"]
                for gloss in row.get("gloss") or []:
                    if gloss not in gl:
                        gl.append(gloss)
                # `borrowed_from` is a dictionary's own mark on a word that
                # states no ancestry (Dehkhoda's (ع) beside an Arabic headword),
                # so it fills an empty field like the rest; `classify` ignores it
                # whenever the entry has a chain of its own (2026-11-10).
                for key in ("translit", "pos", "ipa", "etym", "ref",
                            "borrowed_from", "source_note"):
                    if row.get(key) and not cur.get(key):
                        cur[key] = row[key]
                # A citation is not a value to fill: the curated supplement
                # owns the sentence a record is quoted from, and a corrected
                # ref (a page that moved, a quote that was recut) has to land
                # on the next build instead of being ignored (2026-11-08).
                if row.get("ref"):
                    cur["ref"] = row["ref"]
                if row.get("url"):
                    cur["url"] = row["url"]
                # A supplement is the curated record, so a `formed` statement it
                # carries replaces an older one instead of being ignored on the
                # second build (otherwise a corrected note never lands).
                if row.get("formed"):
                    cur["formed"] = row["formed"]
                # Alternative readings are a list for the same reason as
                # ancestry: Wiktionary's template may yield one reading while the
                # language's own entry records another (روباه is rōbāh in the
                # English entry and [ruːˈbɒːh] in the Persian one), and the sound
                # laws may produce either.
                if row.get("translit_alt"):
                    alts = cur.setdefault("translit_alt", [])
                    if not isinstance(alts, list):
                        alts = cur["translit_alt"] = [alts]
                    for alt in row["translit_alt"]:
                        if alt and alt not in alts:
                            alts.append(alt)
                # Ancestry is a list of links, not a value: a supplement may know
                # a stage Wiktionary's own template did not yield (گربه ← pal
                # gwlbk, whose term field is empty in the wikitext), so links
                # are unioned instead of only filled when the list is missing.
                if row.get("anc"):
                    cur_anc = cur.setdefault("anc", [])
                    seen_anc = {tuple(a) for a in cur_anc if isinstance(a, (list, tuple))}
                    # A stage the entry's own record already names is *its* to
                    # state: the supplement may write that stage in another
                    # notation (گرگ ← pal 𐭢𐭥𐭫𐭢 from the template, pal gwlg
                    # from MacKenzie), and unioning both put two Middle Persian
                    # links in one chain — the ladder then started from the
                    # wrong one (2026-11-09).
                    stages = {a[0] for a in seen_anc if isinstance(a, (list, tuple)) and a}
                    for link in row["anc"]:
                        if tuple(link) in seen_anc or (link and link[0] in stages):
                            continue
                        cur_anc.append(link)
                        seen_anc.add(tuple(link))
                        if link:
                            stages.add(link[0])
                cur.setdefault("sources", [])
                for src in [cur.get("source"), row.get("source")]:
                    if src and src not in cur["sources"]:
                        cur["sources"].append(src)
        if json.dumps(rows, ensure_ascii=False, sort_keys=True) == before:
            # Nothing in this glossary changed: leave the file (and its bytes)
            # alone, so a diff shows the language that moved and nothing else.
            print(f"{lang:<10}   unchanged")
            continue
        _write_gzip(out_path, rows)
        print(f"{lang:<10} +{added:>5} supplement entries → {out_path.stat().st_size/1048576:.2f} MB")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="/tmp/kaikki")
    ap.add_argument("--only", nargs="*", help="language ids to rebuild")
    ap.add_argument("--min-ancestry", type=int, default=1)
    ap.add_argument("--supplements-only", action="store_true",
                    help="only fold data/lexicon/_supplement/ into the built glossaries")
    ap.add_argument("--mark-reconstructions", action="store_true",
                    help="flag reconstruction-only entries in the built glossaries")
    args = ap.parse_args()
    if args.supplements_only:
        merge_supplements()
        return 0
    if args.mark_reconstructions:
        return 0 if mark_reconstructions(Path(args.src), args.only) else 1

    src = Path(args.src)
    (DATA / "lexicon").mkdir(parents=True, exist_ok=True)
    (DATA / "cognate_sets").mkdir(parents=True, exist_ok=True)
    (DATA / "graph").mkdir(parents=True, exist_ok=True)

    # ---- 1. PIE cognate sets and the edge graph -------------------------
    pie_path = src / "ProtoIndoEuropean.jsonl"
    cognate_of: dict[tuple[str, str], str] = {}
    edges: list[dict] = []
    sets_written = 0
    if pie_path.exists():
        # Written with a zero mtime: a build that changes nothing must leave
        # the file byte-for-byte alone, or every run buries the real diff
        # (2026-11-09: rebuilding two glossaries rewrote both generated files).
        with _text_writer(DATA / "cognate_sets" / "ine-pro.jsonl.gz") as fh:
            for line in pie_path.open(encoding="utf-8"):
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                word = entry.get("word")
                if not word:
                    continue
                desc = entry.get("descendants") or []
                if not desc:
                    continue
                forms = []
                for lang, dword, roman, sense, path in walk_descendants(desc, []):
                    forms.append({"l": lang, "w": dword, "r": roman or "", "s": sense or "", "p": path})
                    cognate_of.setdefault((lang, dword), f"ine-pro:{word}")
                    if len(path) > 1:
                        parent = path[-2].split(":", 1)
                        edges.append({"c": [lang, dword], "p": [parent[0], parent[1]], "set": f"ine-pro:{word}"})
                rec = {
                    "id": f"ine-pro:{word}",
                    "pie": word,
                    "gloss": "; ".join(glosses(entry, 2)),
                    "pos": entry.get("pos", ""),
                    "forms": forms,
                }
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                sets_written += 1
    print(f"cognate sets: {sets_written}, descendant links: {len(cognate_of)}")

    # ---- 1b. proto-language entries give us (proto form → PIE etymon) ----
    for dump, lang in DUMP_TO_ID.items():
        if lang not in PROTO:
            continue
        path = src / f"{dump}.jsonl"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                word = entry.get("word")
                if not word or (lang, word) in cognate_of:
                    continue
                for anc_lang, anc_word, _rel in ancestry(entry):
                    if anc_lang == "ine-pro":
                        cognate_of[(lang, word)] = f"ine-pro:{anc_word}"
                        break
    print(f"proto links: {sum(1 for k in cognate_of if k[0] in PROTO)}")

    # ---- 2. per-language lexicons ---------------------------------------
    for dump, lang in DUMP_TO_ID.items():
        if args.only and lang not in args.only:
            continue
        path = src / f"{dump}.jsonl"
        if not path.exists() or path.stat().st_size == 0:
            continue
        kept = 0
        total = 0
        out_path = DATA / "lexicon" / f"{lang}.jsonl.gz"
        tmp_path = out_path.with_name(out_path.name + ".tmp")
        with _text_writer(tmp_path) as fh:
            for line in path.open(encoding="utf-8"):
                total += 1
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                word = entry.get("word")
                if not word:
                    continue
                # An inflected form is a form of a word, not a word: the lemma
                # keeps the row (2026-11-09).
                if is_form_only(entry):
                    continue
                anc = ancestry(entry)
                built = formations(entry, anc)
                # ``--min-ancestry`` keeps entries that record where they come
                # from. A word built from named pieces records that too, even
                # when no single ancestor stage can be derived from it
                # (English lexicography = lexico- + -graphy). Without this the
                # corpus would silently shrink whenever a template is read
                # correctly (2026-11-09).  A named construction is such a
                # record, so it keeps the entry as well: Old Persian
                # *Haxāmaniš* "from *haxā- + manah-" states its origin even
                # though no stage above it is modelled here.
                if (lang not in PROTO and len(anc) < args.min_ancestry
                        and not built and not etymon_records_origin(entry)):
                    continue
                gl = glosses(entry)
                if not gl:
                    continue
                rec = {
                    "word": word,
                    "lang": lang,
                    "pos": entry.get("pos", ""),
                    "gloss": gl,
                }
                # A proto-language row is a reconstruction by definition, and
                # the interface already treats every proto form as gold. The
                # flag exists for attested languages, where Wiktionary keeps
                # reconstructed words in a separate namespace and the glossary
                # would otherwise claim a text spells them (2026-11-08).
                if lang not in PROTO and is_reconstruction(entry):
                    rec["recon"] = True
                etym = clean(entry.get("etymology_text"), 300)
                if etym:
                    # A tree's relation labels (der., bor., lbor. …) arrive
                    # welded to the term they follow; bracket them so no reader
                    # takes one for a suffix (see pie.etymtext).
                    rec["etym"] = etymtext.split_labels(etym, TREE_NAMES)
                if anc:
                    rec["anc"] = anc
                if built:
                    # ``built_as``: the pieces a *recorded form* is made of.
                    # Not the same statement as ``formed`` (a hand-curated
                    # note that a link is a derivation, not an inheritance).
                    rec["built_as"] = built
                ipa = [s.get("ipa") for s in (entry.get("sounds") or []) if s.get("ipa")]
                if ipa:
                    rec["ipa"] = ipa[0]
                roman = romanisations(entry)
                if roman:
                    rec["translit"] = roman[0]
                    if len(roman) > 1:
                        rec["translit_alt"] = roman[1:]
                cog = cognate_of.get((lang, word))
                if not cog:
                    for anc_lang, anc_word, _rel in anc:
                        if (anc_lang, anc_word) in cognate_of:
                            cog = cognate_of[(anc_lang, anc_word)]
                            break
                if cog:
                    rec["cog"] = cog
                if entry.get("descendants"):
                    rec["desc"] = len(entry["descendants"])
                fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
                kept += 1
        tmp_path.replace(out_path)
        print(f"{lang:<10} {kept:>7} / {total:>8} entries  → {out_path.stat().st_size/1048576:.1f} MB")

    # ---- 2b. supplement lexicons (hand-curated / non-kaikki sources) -----
    merge_supplements()

    # ---- 3. edge graph ---------------------------------------------------
    seen = set()
    with _text_writer(DATA / "graph" / "edges.jsonl.gz") as fh:
        for e in edges:
            key = (tuple(e["c"]), tuple(e["p"]))
            if key in seen:
                continue
            seen.add(key)
            fh.write(json.dumps(e, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"edges: {len(seen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
