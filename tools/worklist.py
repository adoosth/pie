#!/usr/bin/env python3
"""Write the priorisited worklist to ``docs/WORKLIST.md`` and ``data/worklist.json``.

    python tools/worklist.py                 # sample per language, fast
    python tools/worklist.py --full          # every eligible word
    python tools/worklist.py --lang en       # one language, printed

The rendering lives in ``pie.worklist`` so the CLI (``pie worklist``) and this
tool share one implementation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import worklist as wl                # noqa: E402
from pie.textio import enable_utf8_stdio      # noqa: E402


def main() -> int:
    enable_utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=12000, help="sample per language (0 = all)")
    ap.add_argument("--full", action="store_true", help="audit every eligible word")
    ap.add_argument("--lang", action="append", help="restrict to a language (repeatable)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of writing")
    ap.add_argument("--write", action="store_true", help="write docs/WORKLIST.md and data/worklist.json")
    args = ap.parse_args()
    limit = None if args.full else (args.limit or None)
    report = wl.run(limit, args.lang)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1, default=str))
        return 0
    text = wl.render(report)
    if args.write:
        md_tmp = wl.OUT_MD.with_name(wl.OUT_MD.name + ".tmp")
        json_tmp = wl.OUT_JSON.with_name(wl.OUT_JSON.name + ".tmp")
        md_tmp.write_text(text, encoding="utf-8")
        md_tmp.replace(wl.OUT_MD)
        json_tmp.write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str) + "\n",
                            encoding="utf-8")
        json_tmp.replace(wl.OUT_JSON)
        print(f"wrote {wl.OUT_MD.relative_to(wl.ROOT)} and {wl.OUT_JSON.relative_to(wl.ROOT)}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
