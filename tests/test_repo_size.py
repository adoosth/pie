"""The repo stays a repo: a budget on what git carries and on the cache (2026-11-12).

The Dehkhoda cache grew to 153,206 files and 612 MB on disk without one test
noticing, because every file was small and the cache is not tracked.  These
checks are deliberately blunt: tracked bytes, the largest tracked file, and how
many loose cache files are allowed to exist at once.  A budget that trips is a
question, not a verdict — raise the number here in the same commit that raises
it for real, so the growth is a decision someone wrote down.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Measured 2026-11-12 after the meanings cache was packed: 459 tracked files,
# 55.9 MB, the largest being data/lexicon/en.jsonl.gz at 12.4 MB.  The
# Wiktionary-page ledgers added 2.6 MB over 37 files (v0.17.1).
TRACKED_MB = 70
ONE_FILE_MB = 15
LOOSE_FILES = 2000
CACHE_MB = 60


def tracked() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    return [ROOT / name for name in out.split("\0") if name]


class TestTheRepoSize(unittest.TestCase):
    def test_the_tree_stays_under_its_budget(self):
        files = [(p.stat().st_size, p) for p in tracked() if p.is_file()]
        total = sum(size for size, _ in files) / 1e6
        self.assertLess(total, TRACKED_MB,
                        f"{total:.1f} MB tracked; the budget is {TRACKED_MB} MB. "
                        "Pack or compress before adding more data.")
        largest = max(files)[1] if files else None
        size = max(files)[0] / 1e6 if files else 0
        self.assertLess(size, ONE_FILE_MB,
                        f"{largest.relative_to(ROOT)} is {size:.1f} MB; the budget for one "
                        f"file is {ONE_FILE_MB} MB")

    def test_the_meaning_cache_stays_packed(self):
        """`data/meanings/fa/` is a write-through cache: it may be loose, not fat."""
        loose = ROOT / "data" / "meanings" / "fa"
        if not loose.exists():
            return
        files = list(loose.glob("*.json.gz"))
        self.assertLess(len(files), LOOSE_FILES,
                        f"{len(files)} loose cache files; run tools/pack_meanings.py --pack")
        size = sum(p.stat().st_size for p in files) / 1e6
        self.assertLess(size, CACHE_MB,
                        f"the loose cache holds {size:.1f} MB of text; pack it")


if __name__ == "__main__":
    unittest.main()
