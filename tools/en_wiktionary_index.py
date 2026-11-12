#!/usr/bin/env python3
"""Record which glossary headwords have a page on the English Wiktionary.

The W on a recorded word is a door: it opens the word's own Wiktionary entry.
A word whose entry was read from Wiktionary already carries that page in its
`url`, but the Persian glossary comes from Dehkhoda and records no Wiktionary
page — and many words do have one (کبود is read at
en.wiktionary.org/wiki/کبود).  This tool writes, per language, the headwords
that really have a page, so the word page can link them without the network
being called while a reader waits:

    python tools/en_wiktionary_index.py --all          # every glossary
    python tools/en_wiktionary_index.py --lang fa pal  # a few languages
    python tools/en_wiktionary_index.py --report       # what is recorded

The answer comes from the site's own list of page titles
(`enwiktionary-latest-all-titles.gz`, ~40 MB, downloaded once into
`data/sources/en_wiktionary/` and kept out of git): reading it is a minute of
work and covers every headword, where asking page by page is hours and gets
rate-limited.  An attested word is a namespace-0 title and a reconstruction is
a namespace-118 one (`Proto-Germanic/nahts`), which is how Wiktionary files
its `Reconstruction:` pages.

Only a page that exists is written (`data/sources/en_wiktionary/<lang>.jsonl.gz`);
a word absent from the ledger has no *recorded* page, and the interface shows no
icon for it — which is what the admin asked for on 2026-11-12 ("if the source
page is not recorded, simply don't show the icon").
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, service  # noqa: E402

DUMP = ("https://dumps.wikimedia.org/enwiktionary/latest/"
        "enwiktionary-latest-all-titles.gz")
UA = ("pie-lexicon/0.17 (https://github.com/adoosth/pie; page index; "
      "contact adoosth@gwdg.de)")
OUT = ROOT / "data" / "sources" / "en_wiktionary"
#: Namespace 0 holds attested headwords; the reconstruction pages live in the
#: Reconstruction namespace, whose 118 titles read ``Proto-Germanic/nahts``.
NS_HEADWORD, NS_RECON = "0", "118"


def ledger_path(lang: str) -> Path:
    return OUT / f"{lang}.jsonl.gz"


def dump_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    path = OUT / "enwiktionary-latest-all-titles.gz"
    if not path.exists():
        OUT.mkdir(parents=True, exist_ok=True)
        print(f"downloading {DUMP}", file=sys.stderr)
        req = urllib.request.Request(DUMP, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=300) as resp, \
                path.open("wb") as fh:
            while chunk := resp.read(1 << 20):
                fh.write(chunk)
    return path


def candidates(lang: str) -> dict[str, tuple[str, str]]:
    """Every headword of this stage → (namespace, title it would be read at)."""
    path = ROOT / "data" / "lexicon" / f"{lang}.jsonl.gz"
    out: dict[str, tuple[str, str]] = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            entry = json.loads(line)
            word = (entry.get("word") or "").strip()
            if not word or word in out:
                continue
            if entry.get("url") and service._is_wiktionary_url(entry["url"]):
                # The page was recorded when the entry was read; nothing to ask.
                continue
            title = service._wiktionary_title({**entry, "lang": lang})
            if not title:
                continue
            recon = title.startswith("Reconstruction:")
            out[word] = (NS_RECON, title.split(":", 1)[1]) if recon \
                else (NS_HEADWORD, title)
    return out


def build(langs: list[str], dump: str | None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wanted: dict[tuple[str, str], tuple[str, str]] = {}
    for lang in langs:
        try:
            rows = candidates(lang)
        except FileNotFoundError:
            print(f"{lang}: no glossary", file=sys.stderr)
            continue
        for word, key in rows.items():
            wanted[key] = (lang, word)
        print(f"{lang}: {len(rows)} headwords looking for a page", file=sys.stderr)
    if not wanted:
        return
    source = dump_path(dump)
    found: dict[str, list[dict]] = {lang: [] for lang in langs}
    checked = str(date.today())
    seen: set[tuple[str, str]] = set()
    with gzip.open(source, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            ns, _, title = line.rstrip("\n").partition("\t")
            key = (ns, title)
            if key not in wanted or key in seen:
                continue
            seen.add(key)
            lang, word = wanted[key]
            page = title if ns == NS_HEADWORD else f"Reconstruction:{title}"
            found[lang].append({
                "lang": lang, "word": word, "title": page, "status": "found",
                "url": "https://en.wiktionary.org/wiki/"
                       + urllib.parse.quote(page.replace(" ", "_"), safe=":/"),
                "checked": checked,
            })
    for lang, rows in found.items():
        with gzip.open(ledger_path(lang), "wt", encoding="utf-8") as fh:
            for row in sorted(rows, key=lambda r: r["word"]):
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{lang}: {len(rows)} pages recorded", file=sys.stderr)


def report() -> None:
    for path in sorted(glob.glob(str(OUT / "*.jsonl.gz"))):
        lang = Path(path).name.split(".")[0]
        print(f"{lang}: {len(wiktionary_pages(lang))} pages recorded")


def wiktionary_pages(lang: str) -> dict[str, str]:
    from pie import wiktionary
    wiktionary.en_pages.cache_clear()
    return wiktionary.en_pages(lang)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lang", nargs="*", default=None,
                    help="language codes to check (default: every glossary)")
    ap.add_argument("--all", action="store_true", help="every glossary at once")
    ap.add_argument("--dump", default=None,
                    help="a local enwiktionary-latest-all-titles.gz")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.report:
        return report()
    if args.lang and not args.all:
        langs = args.lang
    else:
        langs = sorted(Path(p).name.split(".")[0]
                       for p in glob.glob(str(ROOT / "data" / "lexicon" / "*.jsonl.gz")))
    build(langs, args.dump)


if __name__ == "__main__":
    main()
