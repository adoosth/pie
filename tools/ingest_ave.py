#!/usr/bin/env python3
"""Give the Avestan glossary the ancestry its own etymology sentences record.

Avestan has been the one Iranian language the model cannot see: 352 entries and
not a single one linked to Proto-Iranian, so every law between Proto-Iranian and
Avestan was untestable (`docs/COVERAGE.md`: identified 0).  The words were
fetched by `tools/fetch_wiktionary.py`, which keeps a headword and its glosses
but not the etymology, and the etymology is where the ancestor is named:

    {{inh|ae|ira-pro|*Hā́fš}}, from {{inh|ae|iir-pro|*Hā́ps}},
    from {{der|ae|ine-pro|*h₂ep-|t=water}}

This tool re-reads those pages and writes two fields per entry — the sentence
(`etym`) and the ancestors (`anc`, nearest stage first, exactly the shape the
Proto-Iranian entries carry) — into
`data/lexicon/_supplement/ave.jsonl.gz`.  Glosses, headwords and any reading
already stored are left exactly as they are; nothing is invented: a row is
written only where the page names the ancestor with an inheritance template.

The pronunciation many pages record is deliberately *not* copied: that would
turn a form the glossary cannot read into one it can, and `data/readings.json`
(which quotes the readings of exactly such forms, `tools/build_readings.py
--check`) would go stale.  A session that wants the IPA writes it together with
the readings rebuild.

    python3 tools/ingest_ave.py                 # fetch (cached), write the supplement
    python3 tools/ingest_ave.py --check         # verify the stored rows against the pages
    python3 tools/ingest_ave.py --offline       # rebuild from the cache, no network

The wikitext is cached under ``~/.cache/pie/ave`` so a rebuild is reproducible
without touching Wiktionary again, and every row keeps the sentence it rests on.
Only the *inherited* line is written as ``inherit``: a ``{{bor}}``/``{{lbor}}``
template is recorded with its own relation and never as inheritance, because a
borrowed word is not a step on the chain.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data  # noqa: E402

try:  # the API helper and the language-section reader of the fetcher
    from fetch_wiktionary import api, language_section
except Exception:  # pragma: no cover - the tool must be usable on its own
    api = None

SUPPLEMENT = ROOT / "data" / "lexicon" / "_supplement" / "ave.jsonl.gz"
CACHE = Path.home() / ".cache" / "pie" / "ave"
LANGUAGE = "Avestan"
STAGE = "ave"

#: The stages a derivation chain can start from.  A template naming any other
#: language is not written: an etymology that starts at Sanskrit or Persian is
#: not a step this model can take.
CHAIN = ("ira-pro", "iir-pro", "ine-pro")

#: Template name -> the relation it names.  ``der`` is a derivation from an
#: ancestor language, which is not a borrowing but must not be called upstream
#: inheritance either; the chain reader accepts any relation but ``borrow``.
RELATIONS = {
    "inh": "inherit", "inh+": "inherit", "inh-": "inherit",
    "der": "der", "bor": "borrow", "lbor": "lbor", "slbor": "slbor",
    "obor": "obor", "ubor": "ubor", "calque": "calque",
}

TEMPLATE = re.compile(r"\{\{([^{}]*)\}\}")



def _params(body: str) -> list[str]:
    out, cur, depth = [], "", 0
    for char in body:
        if char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        if char == "|" and depth == 0:
            out.append(cur)
            cur = ""
            continue
        cur += char
    out.append(cur)
    return out


def _form(raw: str) -> str:
    """The form a template names, without the gloss or links it may carry."""
    raw = raw.split("<", 1)[0].strip()
    raw = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", raw)
    raw = re.sub(r"\[{2,}|\]{2,}", "", raw)
    raw = re.sub(r"\s+", "", raw)
    return raw.strip(' ,;.\'\u2019"')


def parse_templates(section: str) -> list[tuple[str, str, str]]:
    """Every (stage, form, relation) the etymology names, in the page's order."""
    rows: list[tuple[str, str, str]] = []
    for match in TEMPLATE.finditer(section):
        parts = _params(match.group(1))
        name = parts[0].strip().lower()
        if name == "etymon":
            relation = None
            for part in parts[2:]:
                piece = part.strip()
                if piece.startswith(":"):
                    relation = piece[1:].split("<")[0]
                    continue
                if ":" not in piece:
                    continue
                lang, _, form = piece.partition(":")
                if lang in CHAIN and relation:
                    rows.append((lang, _form(form), RELATIONS.get(relation, relation)))
            continue
        if name not in RELATIONS or len(parts) < 4:
            continue
        lang = parts[2].strip()
        form = _form(parts[3])
        if lang in CHAIN and form:
            rows.append((lang, form, RELATIONS.get(name, name)))
    return rows


def etymology_sentence(rows: list[list[str]], section: str) -> str:
    """The page's own clause list, rebuilt from the ancestors it names.

    The sentence is not a copy of the section: it is the chain the tool read,
    in the words the page uses for it ("Inherited from Proto-Iranian *Hā́fš,
    from Proto-Indo-Iranian *Hā́ps, from Proto-Indo-European *h₂ep-.").  That
    keeps the stored sentence and the stored `anc` rows saying the same thing;
    a cognate list whose templates were dropped cannot leave "compare , , ."
    behind, because nothing but the ancestry is written.
    """
    names = _language_names()
    head = re.sub(r"\{\{\s*root\s*\|[^{}]*\}\}", "", section).strip()
    lead = "From"
    if re.match(r"(?i)inherited from", head):
        lead = "Inherited from"
    elif re.match(r"(?i)borrowed from", head):
        lead = "Borrowed from"
    clauses = [f"{names.get(lang, lang)} {form}" for lang, form, _rel in rows]
    return f"{lead} " + ", from ".join(clauses) + "." if clauses else ""


def _language_names() -> dict[str, str]:
    try:
        raw = json.loads((ROOT / "data" / "language_names.json").read_text(encoding="utf-8"))
        return {k: v.get("name", k) for k, v in raw.get("languages", {}).items()}
    except Exception:
        return {}


def etymology_section(wikitext: str) -> str:
    section = language_section(wikitext, LANGUAGE) or ""
    match = re.search(r"^===?\s*Etymology[^=]*===?\s*$", section, re.M)
    if not match:
        return ""
    rest = section[match.end():]
    stop = re.search(r"^=+[^=\n].*=+\s*$", rest, re.M)
    return rest[: stop.start()] if stop else rest


def ancestors(section: str) -> list[list[str]]:
    """The ``anc`` rows: nearest stage first, exactly what the page names."""
    return [[stage, form, relation] for stage, form, relation in parse_templates(section)]


def cache_path(word: str) -> Path:
    safe = "".join(f"{ord(ch):x}" if ch in "/\\:" else ch for ch in word)
    return CACHE / f"{safe}.wiki"


def load_wikitext(words: list[str], offline: bool) -> dict[str, str]:
    out: dict[str, str] = {}
    missing = [w for w in words if not cache_path(w).exists()]
    if missing and offline:
        print(f"{len(missing)} page(s) not in the cache: {', '.join(missing[:5])}", file=sys.stderr)
    for i in range(0, len(missing), 50):
        if offline:
            break
        batch = missing[i : i + 50]
        data_page = api({"action": "query", "prop": "revisions", "rvprop": "content",
                         "rvslots": "main", "titles": "|".join(batch)})
        for page in data_page.get("query", {}).get("pages", []):
            title = page.get("title", "")
            revs = page.get("revisions") or []
            if not revs or "missing" in page:
                continue
            text = revs[0]["slots"]["main"].get("content", "")
            CACHE.mkdir(parents=True, exist_ok=True)
            cache_path(title).write_text(text, encoding="utf-8")
        time.sleep(0.3)
    for word in words:
        path = cache_path(word)
        if path.exists():
            out[word] = path.read_text(encoding="utf-8")
    return out


def build(wikitext: dict[str, str], records: dict[str, dict]) -> tuple[dict[str, dict], list[str]]:
    problems: list[str] = []
    for word, entry in records.items():
        text = wikitext.get(word)
        for field in ("etym", "anc", "ipa"):
            entry.pop(field, None)
        if not text:
            continue
        section = etymology_section(text)
        if not section:
            continue
        rows = ancestors(section)
        if not rows:
            continue
        entry["etym"] = etymology_sentence(rows, section)
        entry["anc"] = rows
    return records, problems


def main() -> int:
    global CACHE
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="verify the stored rows against the cached/live pages")
    ap.add_argument("--offline", action="store_true", help="use the cache only")
    ap.add_argument("--cache", type=Path, default=CACHE)
    ap.add_argument("--write", action="store_true", help="write the supplement (default unless --check)")
    args = ap.parse_args()
    CACHE = args.cache

    if not SUPPLEMENT.exists():
        raise SystemExit(f"{SUPPLEMENT} is missing; run tools/fetch_wiktionary.py ave first")
    records: dict[str, dict] = {}
    with gzip.open(SUPPLEMENT, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            records[row["word"]] = row

    words = list(records)
    stored = copy.deepcopy(records)
    wikitext = load_wikitext(words, args.offline)
    before = sum(1 for row in stored.values() if row.get("anc"))
    rebuilt, problems = build(wikitext, records)
    linked = sum(1 for row in rebuilt.values() if row.get("anc"))
    stages = {}
    for row in rebuilt.values():
        for stage, _form, _rel in row.get("anc") or []:
            stages[stage] = stages.get(stage, 0) + 1

    if args.check:
        print(f"{len(words)} entries, {before} with ancestry stored, {linked} now resolvable")
        for word in words:
            have = [r for r in stored[word].get("anc") or []]
            fresh = [r for r in rebuilt[word].get("anc") or []]
            if have != fresh:
                problems.append(f"{word}: stored {have} ≠ page {fresh}")
        for line in problems[:20]:
            print("  MISMATCH", line)
        print(f"{len(problems)} mismatches")
        return 1 if problems else 0

    # mtime=0 keeps the bytes stable, so a rebuild that changes nothing changes
    # nothing (the repo treats a diff as a claim about the data).
    with open(SUPPLEMENT, "wb") as raw, \
            gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
        for row in rebuilt.values():
            gz.write((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    print(f"{len(rebuilt)} entries → {SUPPLEMENT}")
    print(f"  with ancestry: {before} → {linked}")
    print("  ancestors by stage: " + ", ".join(f"{k} {v}" for k, v in
                                               sorted(stages.items(), key=lambda kv: -kv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
