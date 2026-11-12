#!/usr/bin/env python3
"""Ask the Persian Wiktionary about Persian words, and keep every answer.

The glossary's Persian words come from Dehkhoda, which gives a gloss and a
grammar label but has no page on the English Wiktionary to point at. The Persian
Wiktionary does, so this tool walks the glossary, asks fa.wiktionary.org for each
word's page, and writes the answer into `data/sources/fa_wiktionary.jsonl.gz`:

    python tools/fa_wiktionary.py --limit 250          # the next 250 words
    python tools/fa_wiktionary.py --report             # how far the pass has gone
    python tools/fa_wiktionary.py --words آب پدر --refresh

A page that exists is stored with its address, its revision and the etymology
the page prints; a word with no page is stored as *missing*, and no later pass
asks again. The pass is resumable and deterministic: words are taken in the
glossary's own order, striding across the alphabet so a run of 250 is a sample
of the dictionary rather than its first letter.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, wiktionary  # noqa: E402

API = "https://fa.wiktionary.org/w/api.php"
SITE = "fa.wiktionary.org"
UA = "pie-etymology-build/0.1 (https://github.com/adoosth/pie; adoosth@gwdg.de)"
BATCH = 20


def api(params: dict, tries: int = 5) -> dict:
    params = {"format": "json", "formatversion": "2", **params}
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503):
                wait = 5 * (attempt + 1)
                print(f"{exc.code}, waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except urllib.error.URLError as exc:
            wait = 5 * (attempt + 1)
            print(f"{exc.reason}, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError("the site kept refusing")


def words(lang: str) -> list[str]:
    """Every headword of a glossary, in the glossary's own order."""
    seen: list[str] = []
    have: set[str] = set()
    for name in (f"{lang}.jsonl.gz", f"{lang}-*.jsonl.gz"):
        for path in sorted(glob.glob(str(data.LEXICON_DIR / name))):
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    word = row.get("word")
                    if word and word not in have:
                        have.add(word)
                        seen.append(word)
    return seen


def page_url(title: str) -> str:
    return f"https://{SITE}/wiki/{urllib.parse.quote(title.replace(' ', '_'), safe='')}"


def fetch(titles: list[str]) -> dict[str, dict]:
    """One batch: title → {missing | content, revid, revised, page}."""
    out: dict[str, dict] = {}
    for start in range(0, len(titles), BATCH):
        chunk = titles[start:start + BATCH]
        params = {
            "action": "query", "titles": "|".join(chunk), "redirects": "1",
            "prop": "revisions", "rvprop": "content|ids|timestamp", "rvslots": "main",
        }
        payload = api(params)
        query = payload.get("query") or {}
        # A redirect answers under another title; the word asked about is the
        # page a reader would land on, so keep the target's address.
        redirected = {row["from"]: row["to"] for row in query.get("redirects") or []}
        for page in query.get("pages") or []:
            title = page.get("title") or ""
            if page.get("missing"):
                out[title] = {"missing": True}
                continue
            revs = page.get("revisions") or [{}]
            rev = revs[0]
            content = ((rev.get("slots") or {}).get("main") or {}).get("content") or ""
            out[title] = {"content": content, "revid": rev.get("revid"),
                          "revised": rev.get("timestamp") or "", "page": title}
        for old, new in redirected.items():
            if new in out:
                out[old] = out[new]
        time.sleep(0.5)
    return out


def rows_for(batch: list[str], lang: str, today: str) -> list[dict]:
    pages = fetch(batch)
    rows = []
    for word in batch:
        page = pages.get(word) or {"missing": True}
        if page.get("missing"):
            rows.append({"lang": lang, "word": word, "status": "missing",
                         "site": SITE, "checked": today})
            continue
        heading, text = wiktionary.etymology(page.get("content") or "")
        rows.append({
            "lang": lang, "word": word, "status": "found", "site": SITE,
            "title": page.get("page") or word,
            "url": page_url(page.get("page") or word),
            "revid": page.get("revid"), "revised": page.get("revised") or "",
            "etym": text, "etym_heading": heading, "checked": today,
        })
    return rows


def write(rows: list[dict]) -> None:
    """Merge into the ledger: one row per word, newest check wins."""
    kept: dict[tuple[str, str], dict] = dict(wiktionary.ledger())
    for row in rows:
        kept[(row["lang"], row["word"])] = row
    path = wiktionary.LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        for key in sorted(kept, key=lambda k: (k[0], k[1])):
            fh.write(json.dumps(kept[key], ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    # The module caches the ledger for the app; a tool that just wrote it must
    # not read its own old answer back.
    wiktionary.ledger.cache_clear()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lang", default="fa")
    ap.add_argument("--limit", type=int, default=250,
                    help="how many new words to ask about (default 250)")
    ap.add_argument("--stride", type=int, default=0,
                    help="take every Nth word of the glossary (default: the "
                         "stride that spreads --limit across the whole glossary)")
    ap.add_argument("--words", nargs="*", help="ask about exactly these words")
    ap.add_argument("--refresh", action="store_true",
                    help="ask again about words already in the ledger")
    ap.add_argument("--report", action="store_true", help="print the tally and stop")
    args = ap.parse_args()

    if args.report:
        print(json.dumps(wiktionary.tally(), indent=1))
        return 0

    today = date.today().isoformat()
    if args.words:
        picked = list(dict.fromkeys(args.words))
    else:
        every = words(args.lang)
        known = wiktionary.ledger()
        fresh = [w for w in every if args.refresh or (args.lang, w) not in known]
        stride = args.stride or max(1, len(fresh) // max(1, args.limit))
        picked = fresh[::stride][:args.limit]
    if not picked:
        print("nothing new to ask about — the ledger already covers these words")
        return 0

    print(f"asking {SITE} about {len(picked)} words")
    rows: list[dict] = []
    for start in range(0, len(picked), BATCH):
        batch = picked[start:start + BATCH]
        rows.extend(rows_for(batch, args.lang, today))
        done = len(rows)
        found = sum(1 for r in rows if r["status"] == "found")
        etym = sum(1 for r in rows if r.get("etym"))
        print(f"  {done}/{len(picked)} · {found} pages · {etym} with an etymology",
              flush=True)
        write(rows)
    write(rows)
    found = sum(1 for r in rows if r["status"] == "found")
    etym = sum(1 for r in rows if r.get("etym"))
    print(f"ledger now: {json.dumps(wiktionary.tally(), ensure_ascii=False)}")
    print(f"this run: {found} of {len(rows)} have a page, {etym} carry an etymology")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
