"""A queue of matches the engine could not verify, for a person to judge.

A branch row may meet a record that reproduces every sound of a form except
its ending — Persian کبود *kabud* where the registered laws give *kabūde*.  The
page refuses to call that a match (no ✓, a yellow ⚠, "match not verified") and
the row lands here, so the pile is a real list someone can work through with
the two readings and both meanings in front of them, instead of a hundred
pages nobody will ever look at again (admin, 2026-11-12).

The journal is working state, not data: it lives beside the runtime meaning
cache under ``data/review/``, is skipped by git, and losing it costs nothing
but the list (`pie unverified` prints what has been recorded).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from . import data

REVIEW_DIR = data.DATA / "review"
JOURNAL = REVIEW_DIR / "unverified_matches.jsonl"

_lock = threading.Lock()
_seen: set[tuple] | None = None


def _key(row: dict) -> tuple:
    return (row.get("lang"), row.get("form"), row.get("word"), row.get("reading"))


def _load_seen() -> set[tuple]:
    global _seen
    if _seen is not None:
        return _seen
    seen: set[tuple] = set()
    try:
        with JOURNAL.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    seen.add(_key(json.loads(line)))
                except ValueError:
                    continue
    except OSError:
        pass
    _seen = seen
    return seen


def record(rows: list[dict], *, source: dict | None = None) -> None:
    """Append the rows nobody has recorded before; failures are silent.

    A page must never fail because its review queue could not be written, so
    every error here is swallowed — the page itself already says the match is
    unverified.
    """
    if not rows:
        return
    with _lock:
        seen = _load_seen()
        fresh = []
        for row in rows:
            key = _key(row)
            if key in seen:
                continue
            seen.add(key)
            fresh.append({**row, "from": source or {}})
        if not fresh:
            return
        try:
            REVIEW_DIR.mkdir(parents=True, exist_ok=True)
            with JOURNAL.open("a", encoding="utf-8") as fh:
                for row in fresh:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError:
            pass


def entries(lang: str | None = None) -> list[dict]:
    """Everything recorded so far, newest last, optionally for one language."""
    out: list[dict] = []
    try:
        with JOURNAL.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if lang and row.get("lang") != lang:
                    continue
                out.append(row)
    except OSError:
        return []
    return out


def path() -> Path:
    """Where the journal lives, for the command that prints it."""
    return JOURNAL
