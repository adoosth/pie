#!/usr/bin/env python3
"""Save every language name Wiktionary defines to a small source snapshot.

`data/language_names.json` is harvested from the Proto-Indo-European
descendant tree, which reaches only the languages of that family (plus the
borrowers its entries happen to name).  A word page can name any language at
all — Old Median, Old Northern French, Brokskat — and a bare code on a rung is
not a name.  This tool reads Wiktionary's own tables and writes
``data/sources/wiktionary_language_names.json.gz``:

  Module:languages/data/*                 every language Wiktionary knows
  Module:etymology languages/data         the etymology-only codes (ang-ang, fro-nor)
  Module:families/data                    family codes used as ancestors (aav, gem)

The name is the first field of each table row (``m["xme-old"] = {"Old
Median", …}``).  Nothing else is stored: this snapshot answers "what is this
code called", and the model's own registry and the descendant-tree table keep
answering branch, kind and era.

Usage:
    python3 tools/build_wiktionary_names.py
    python3 tools/build_wiktionary_names.py --cache /tmp/wikt_modules.json
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import subprocess
import time
import urllib.parse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
API = "https://en.wiktionary.org/w/api.php"
USER_AGENT = "seanet-pie/0.16 (language-name harvest)"

#: The first field of a table row is the name.  Some rows carry a comment
#: between the key and the opening brace, so the pattern allows one.
ROW = re.compile(r'm\["([^"]+)"\]\s*=\s*\{(?:\s*\n)?\s*"((?:[^"\\]|\\.)*)"')

PAGES = ["Module:languages/data/2"]
PAGES += [f"Module:languages/data/{size}/{letter}"
          for size in (3,) for letter in "abcdefghijklmnopqrstuvwxyz"]
PAGES += [f"Module:languages/data/{size}/{letter}/extra"
          for size in (3,) for letter in "abcdefghijklmnopqrstuvwxyz"]
PAGES += ["Module:languages/data/2/extra", "Module:languages/data/exceptional",
          "Module:languages/data/exceptional/extra", "Module:languages/data/all",
          "Module:languages/data/all/additional",
          "Module:etymology languages/data", "Module:families/data"]


def fetch(titles: list[str]) -> dict[str, str]:
    """The wikitext of each page, in batches the API accepts."""
    out: dict[str, str] = {}
    for start in range(0, len(titles), 40):
        batch = titles[start:start + 40]
        query = urllib.parse.urlencode({
            "action": "query", "prop": "revisions", "rvprop": "content",
            "rvslots": "main", "titles": "|".join(batch), "format": "json",
            "formatversion": "2"})
        raw = subprocess.check_output(
            ["curl", "-s", "-m", "90", "-A", USER_AGENT, f"{API}?{query}"])
        answer = json.loads(raw)
        for page in answer.get("query", {}).get("pages", []):
            if page.get("missing"):
                continue
            text = page.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("content")
            if text:
                out[page["title"]] = text
        time.sleep(1)
    return out


def harvest(modules: dict[str, str]) -> dict[str, str]:
    names: dict[str, str] = {}
    for text in modules.values():
        for code, name in ROW.findall(text):
            names.setdefault(code, name)
    return dict(sorted(names.items()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", help="a JSON file of {page: wikitext} fetched earlier")
    ap.add_argument("--out", default=str(DATA / "sources" / "wiktionary_language_names.json.gz"))
    args = ap.parse_args()

    if args.cache:
        modules = json.loads(Path(args.cache).read_text(encoding="utf-8"))
    else:
        modules = fetch(PAGES)

    names = harvest(modules)
    payload = {
        "source": "en.wiktionary.org Module:languages/data, "
                  "Module:etymology languages/data, Module:families/data",
        "retrieved": date.today().isoformat(),
        "pages": sorted(modules),
        "names": names,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=False,
                     separators=(",", ":")).encode("utf-8")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as fh:
        with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
            gz.write(raw)
    print(f"{len(names):,} names from {len(modules)} pages -> {out} "
          f"({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
