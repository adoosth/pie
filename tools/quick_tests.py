#!/usr/bin/env python3
"""The everyday test run: the fast modules, under a hard wall-clock budget.

The repo is in development, so a change answers to the tests it touches, not to
all of them (2026-11-13: never test for more than a minute unless a longer run
is asked for by name).  This runner is the everyday gate: a curated list of modules
that pin the engine, the read models, the web contract and the data rules, run
in one process, with a budget it will not cross.

    python3 tools/quick_tests.py              # run the list, fail if over budget
    python3 tools/quick_tests.py --list       # what runs, and why
    python3 tools/quick_tests.py --budget 30  # a tighter budget
    python3 tools/quick_tests.py tests.test_web tests.test_lexicon   # by name

The full suite (``python3 -m unittest discover -s tests``) is for a release or
for a run asked for by name; it takes many minutes and proves nothing more
about an ordinary change.  Adding a module here costs that budget: measure it, and
only add what pins a rule (see docs/DECISIONS.md, "Process").
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Module -> why it is in the everyday set.  Keep it short: every line is time.
QUICK = {
    "tests.test_syntax": "the tree parses on Python 3.10 (no 3.12-only f-strings)",
    "tests.test_engine": "the rule engine itself: matching, tiers, refusals",
    "tests.test_notation": "one alphabet per stage; folds and quoted spellings",
    "tests.test_categories": "the six bands and the verdict behind them",
    "tests.test_attestation": "attested / recorded / proposed / non-existent",
    "tests.test_senses": "one spelling, several words: the sense groups",
    "tests.test_glossary_pages": "the paged glossary: pages, clamps, dressing",
    "tests.test_web": "the word page and the cognate table contract",
    "tests.test_repo_size": "the docs and AGENTS.md stay inside their caps",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("modules", nargs="*", help="modules to run instead of the list")
    parser.add_argument("--list", action="store_true", help="print the set and exit")
    parser.add_argument("--budget", type=float, default=60.0,
                        help="wall-clock seconds the run must stay inside (default 60)")
    args = parser.parse_args(argv)

    modules = args.modules or list(QUICK)
    if args.list:
        for name in modules:
            print(f"{name:34} {QUICK.get(name, '')}")
        return 0

    missing = [m for m in modules if not (ROOT / (m.replace('.', '/') + '.py')).exists()]
    if missing:
        print("no such module: " + ", ".join(missing), file=sys.stderr)
        return 2

    start = time.time()
    proc = subprocess.run([sys.executable, "-m", "unittest", "-q", *modules],
                          cwd=ROOT, env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"})
    elapsed = time.time() - start
    status = "green" if proc.returncode == 0 else "RED"
    print(f"\n{len(modules)} modules, {elapsed:.1f}s of a {args.budget:.0f}s budget — {status}")
    if elapsed > args.budget:
        print("over budget: this set has grown; move a module out before adding another",
              file=sys.stderr)
        return 1
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
