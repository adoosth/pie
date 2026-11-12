#!/usr/bin/env python3
"""Check that every source link in ``data/sources.yaml`` resolves (2026-11-09).

A citation is only a citation if it leads somewhere.  A reader reported a DOI
on a Persian word page that returned 404; the entry had been written from a
working list and never tested.  This tool tests the links the project ships:

* a ``doi.org`` link must resolve through doi.org (a 404 is a broken DOI);
* any other URL is fetched and must answer below 400 (403/429 are reported as
  *blocked*, not broken — a publisher refusing a bot does not mean the page is
  gone);
* with ``--crossref``, a DOI's registered title, journal and year are compared
  with the source's own title, so a DOI that resolves to the *wrong* paper is
  caught too.

Exit code 1 when something is broken, so a release check can rely on it.

    python3 tools/check_sources.py
    python3 tools/check_sources.py --crossref --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data  # noqa: E402

UA = "pie-source-check/1.0 (+https://github.com/adoosth/pie)"
DOI_RE = re.compile(r"doi\.org/(10\.[^\s?#]+)", re.I)


def _open(url: str, timeout: float = 15) -> tuple[int | None, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.geturl(), ""
    except urllib.error.HTTPError as error:
        return error.code, url, str(error)
    except Exception as error:  # noqa: BLE001 - report, never crash the sweep
        return None, url, str(error)


def _crossref(doi: str, timeout: float = 15) -> dict | None:
    request = urllib.request.Request(f"https://api.crossref.org/works/{doi}",
                                     headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)["message"]
    except Exception:  # noqa: BLE001
        return None


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zāēīōūáéíóúàèìòùäöüß]+", (text or "").lower())
            if len(w) > 2}


def check(crossref: bool = False) -> list[dict]:
    rows = []
    for source in data.sources().values():
        url = str(source.get("url") or "").strip()
        if not url:
            continue
        status, final, error = _open(url)
        row = {"id": source.get("id"), "url": url, "status": status,
               "final": final, "error": error, "verdict": ""}
        if status is None:
            row["verdict"] = "unreachable"
        elif status == 404:
            row["verdict"] = "broken"
        elif status in (401, 403, 429):
            row["verdict"] = "blocked"
        elif status >= 400:
            row["verdict"] = "broken"
        else:
            row["verdict"] = "ok"
        doi = DOI_RE.search(url)
        if doi and crossref and row["verdict"] == "ok":
            meta = _crossref(doi.group(1))
            if meta:
                title = " ".join(meta.get("title") or [])
                year = ((meta.get("issued") or {}).get("date-parts") or [[None]])[0][0]
                row["crossref"] = {"title": title, "year": year,
                                   "container": " ".join(meta.get("container-title") or [])}
                mine = _words(source.get("title") or "")
                theirs = _words(title)
                row["crossref_match"] = bool(mine and theirs and len(mine & theirs) >= 2)
                if not row["crossref_match"]:
                    row["verdict"] = "wrong-target"
            else:
                row["crossref"] = None
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crossref", action="store_true",
                        help="verify DOI metadata against Crossref")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    rows = check(args.crossref)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for row in rows:
            line = f"{row['verdict']:<13} {row['status'] or '—':>3}  {row['id']:<22} {row['url']}"
            if row.get("crossref"):
                line += f"\n              ↳ {row['crossref']['title']} ({row['crossref']['year']})"
            print(line)
    bad = [row for row in rows if row["verdict"] in ("broken", "unreachable", "wrong-target")]
    print(f"\n{len(rows)} source URL(s); {len(bad)} broken/wrong-target", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
