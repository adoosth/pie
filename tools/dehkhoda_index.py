#!/usr/bin/env python3
"""The headwords Dehkhoda's dictionary has, read from vajehyab's sitemaps.

vajehyab.com publishes one sitemap per dictionary, and ``words-dehkhoda-N.xml``
lists every entry it serves: about 10,000 URLs per file, 35 files.  Reading the
sitemaps is one request per file — the polite way to learn the dictionary's
inventory — instead of guessing spellings or reading 300,000 pages.

The tool downloads the sitemaps into ``data/dehkhoda/sitemaps`` (kept out of
git: they are the site's files, not ours) and writes one flat list of
headwords, deduplicated, to ``data/dehkhoda/heads.txt``.  Nothing here is a
definition and nothing here is evidence about a word's origin: this is an
index, and the meanings are read per word when a page asks for them.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import unquote

from pie import data

INDEX = "https://vajehyab.com/sitemap.xml"
UA = ("pie-lexicon/0.16 (+https://github.com/adoosth/pie; sitemap index; "
      "contact adoosth@gwdg.de)")
OUT = data.DATA / "dehkhoda"
LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>")


def _get(url: str, timeout: float = 30.0) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, "replace")


def sitemaps() -> list[str]:
    index = _get(INDEX)
    return [url for url in LOC.findall(index) if "words-dehkhoda-" in url]


def fetch(pause: float = 0.4) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    saved = []
    urls = sitemaps()
    print(f"{len(urls)} dehkhoda sitemaps", flush=True)
    for n, url in enumerate(urls, 1):
        name = url.rsplit("/", 1)[-1]
        path = OUT / "sitemaps" / name
        if path.exists() and path.stat().st_size > 1000:
            saved.append(path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = _get(url)
        except (urllib.error.URLError, OSError) as exc:
            print(f"  ! {name}: {exc}", flush=True)
            continue
        path.write_text(text, encoding="utf-8")
        saved.append(path)
        print(f"  {n}/{len(urls)} {name} {len(text)/1024:.0f} kB", flush=True)
        time.sleep(pause)
    return saved


def heads() -> list[str]:
    files = sorted((OUT / "sitemaps").glob("words-dehkhoda-*.xml"))
    seen: dict[str, None] = {}
    for path in files:
        for url in LOC.findall(path.read_text(encoding="utf-8")):
            if "/dehkhoda/" not in url:
                continue
            word = unquote(url.split("/dehkhoda/", 1)[1]).strip()
            if word:
                seen.setdefault(word, None)
    return list(seen)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true", help="download the sitemaps")
    ap.add_argument("--pause", type=float, default=0.4)
    args = ap.parse_args(argv)
    if args.fetch:
        fetch(args.pause)
    words = heads()
    if not words:
        print("no sitemaps read yet; pass --fetch", file=sys.stderr)
        return 1
    (OUT / "heads.txt").write_text("\n".join(words) + "\n", encoding="utf-8")
    print(f"{len(words)} headwords -> {OUT / 'heads.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
