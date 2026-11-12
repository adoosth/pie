#!/usr/bin/env python3
"""Park the words whose recorded ancestry needs a second reader.

The detector lives in ``pie.dubious``; this tool is the file interface.

    python3 tools/backlog.py --write      # regenerate data/review_backlog.yaml
                                          # and docs/REVIEW_BACKLOG.md
    python3 tools/backlog.py --list       # the table, optionally filtered
    python3 tools/backlog.py --check      # exit 1 when the stored file is stale

``--check`` compares the stored kinds, caps and rows with a fresh pass and
ignores the ``generated`` timestamp, so a file written a minute ago is not
reported as stale.  It is the check a commit hook or a review can run: the
backlog is generated from the corpus, so it may not drift from it.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import yaml                                    # noqa: E402

from pie import dubious                        # noqa: E402
from pie.textio import enable_utf8_stdio       # noqa: E402

YAML_PATH = ROOT / "data" / "review_backlog.yaml"
DOC_PATH = ROOT / "docs" / "REVIEW_BACKLOG.md"


def load() -> dict | None:
    if not YAML_PATH.exists():
        return None
    with YAML_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def dump(report: dict) -> str:
    """The report as YAML, one flow mapping per word.

    A block mapping per row costs about 70 more bytes than a flow one, and the
    file has thousands of rows; the header stays block-form because it is read
    by people, the rows are flow because they are searched by machine and read
    in the table of ``docs/REVIEW_BACKLOG.md``.
    """
    header = {key: value for key, value in report.items() if key != "words"}
    lines = [yaml.safe_dump(header, allow_unicode=True, sort_keys=False,
                            width=10000).rstrip("\n"), "words:"]
    for row in report["words"]:
        one = yaml.safe_dump([row], allow_unicode=True, default_flow_style=True,
                             width=10000).strip()
        lines.append("- " + one[1:-1].strip())
    return "\n".join(lines) + "\n"


def write(report: dict) -> None:
    yaml_tmp = YAML_PATH.with_name(YAML_PATH.name + ".tmp")
    doc_tmp = DOC_PATH.with_name(DOC_PATH.name + ".tmp")
    yaml_tmp.write_text(dump(report), encoding="utf-8")
    yaml_tmp.replace(YAML_PATH)
    doc_tmp.write_text(dubious.render(report), encoding="utf-8")
    doc_tmp.replace(DOC_PATH)


def table(report: dict, kind: str | None, lang: str | None, limit: int) -> str:
    rows = report.get("words") or []
    if kind:
        rows = [row for row in rows if row["kind"] == kind]
    if lang:
        rows = [row for row in rows if row["lang"] == lang]
    lines = [f"{len(rows)} rows in {YAML_PATH.relative_to(ROOT)}"
             + (f" (kind {kind})" if kind else "")
             + (f" (language {lang})" if lang else "")]
    lines.append(f"{'lang':6} {'word':22} {'etymon':18} {'kind':17} detail")
    for row in rows[:limit]:
        lines.append(
            f"{row['lang']:6} {row['word'][:22]:22} {row['etymon'][:18]:18} "
            f"{row['kind']:17} {row['detail'][:80]}")
    if len(rows) > limit:
        lines.append(f"… {len(rows) - limit} more (raise --limit)")
    return "\n".join(lines)


def main() -> int:
    enable_utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true",
                    help="regenerate data/review_backlog.yaml and docs/REVIEW_BACKLOG.md")
    ap.add_argument("--list", action="store_true", help="print the stored backlog")
    ap.add_argument("--kind", help="restrict --list to one kind")
    ap.add_argument("--lang", help="restrict --list to one language code")
    ap.add_argument("--limit", type=int, default=40, help="rows printed by --list (default 40)")
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero when the stored backlog is stale")
    args = ap.parse_args()

    if not (args.write or args.list or args.check):
        ap.print_help()
        return 2

    if args.check:
        stored = load()
        if stored is None:
            print(f"{YAML_PATH.relative_to(ROOT)} is missing; run --write", file=sys.stderr)
            return 1
        fresh = dubious.payload()
        reason = dubious.is_stale(stored, fresh)
        if reason:
            print(f"stale: {reason}; run --write", file=sys.stderr)
            return 1
        print(f"{YAML_PATH.relative_to(ROOT)} is current ({len(stored.get('words') or []):,} rows)")
        return 0

    if args.write:
        report = dubious.payload()
        write(report)
        counts: dict[str, int] = {}
        for row in report["words"]:
            counts[row["kind"]] = counts.get(row["kind"], 0) + 1
        print(f"wrote {YAML_PATH.relative_to(ROOT)} ({len(report['words']):,} rows) "
              f"and {DOC_PATH.relative_to(ROOT)}")
        for kind, count in counts.items():
            extra = report["truncated"].get(kind)
            print(f"  {kind:17} {count:6,}" + (f"  (+{extra:,} omitted by the cap)" if extra else ""))

    if args.list:
        stored = load()
        if stored is None:
            print(f"{YAML_PATH.relative_to(ROOT)} is missing; reading a fresh pass instead",
                  file=sys.stderr)
            stored = dubious.payload()
        print(table(stored, args.kind, args.lang, args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
