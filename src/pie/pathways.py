"""Derivation pathways recorded by the person using the interface.

The word page can start from a form the reader typed instead of from the
recorded ancestry. When such a path lands exactly on the attested word, the
reader may store it: this module keeps those paths, one JSON object per line,
so a word page can list them again and the CLI can print them.

The file lives in ``data/pathways.jsonl`` by default (part of the dataset, so
it can be committed and shared) and honours ``PIE_PATHWAYS`` for tests or an
alternative data directory.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from . import data


def store_path() -> Path:
    """Where recorded pathways are appended."""
    override = os.environ.get("PIE_PATHWAYS")
    return Path(override) if override else data.DATA / "pathways.jsonl"


def signature(lang: str, word: str, start_stage: str, start_form: str,
              disabled=()) -> str:
    """A stable id for one path, so storing it twice does not duplicate it."""
    key = json.dumps(
        [lang, word, start_stage, start_form, sorted({d for d in disabled if d})],
        ensure_ascii=False, separators=(",", ":"),
    )
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def load() -> list[dict]:
    """Every stored pathway, oldest first; malformed lines are skipped."""
    path = store_path()
    if not path.exists():
        return []
    out: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict) and record.get("id") and record.get("lang"):
            out.append(record)
    return out


def for_word(lang: str, word: str) -> list[dict]:
    return [r for r in load() if r.get("lang") == lang and r.get("word") == word]


def default_for(lang: str, word: str) -> dict | None:
    """The pathway that is this word's own, applied whenever its page opens.

    A stored path is normally a proposal the reader loads by hand.  A path
    marked ``default`` is different: it states something about the word — that
    a registered law does not apply to it, because the sound the law changes is
    not the sound this word has (Middle English ``wolf`` spells /u/, so the
    lowering of short *o to *ɔ never reaches it).  The newest record wins, so a
    corrected pathway supersedes an older one without editing the file.
    """
    for record in reversed(load()):
        if (record.get("lang") == lang and record.get("word") == word
                and record.get("default")):
            return record
    return None


def defaults() -> dict[tuple[str, str], dict]:
    """Every default pathway, keyed by ``(lang, word)`` for whole-corpus work."""
    out: dict[tuple[str, str], dict] = {}
    for record in load():
        if record.get("default"):
            out[(record.get("lang", ""), record.get("word", ""))] = record
    return out


def find(lang: str, word: str, start_stage: str, start_form: str, disabled=()) -> str | None:
    """The id of this exact path if it was already stored."""
    wanted = signature(lang, word, start_stage, start_form, disabled)
    for record in load():
        if record.get("id") == wanted:
            return wanted
    return None


def store(record: dict) -> tuple[dict, bool]:
    """Append a pathway; returns ``(record, created)``.

    Appending one line keeps concurrent readers safe on local file systems and
    leaves the file easy to diff and to commit.
    """
    path = store_path()
    if any(r.get("id") == record["id"] for r in load()):
        return record, False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record, True


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
