#!/usr/bin/env python3
"""Rewrite each rule example's `out` with the result of applying that rule alone.

The examples in the rule files are documentation of one rule at a time; this
script keeps them honest after a rule's `match`/`replace`/`env` changes.
Curated, independent etymology pairs live in `tests/etymologies/`, not here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie.phonology import detokenize, tokenize  # noqa: E402
from pie.rules import Rule, apply_ruleset  # noqa: E402


def main() -> int:
    for path in sorted((ROOT / "data" / "rules").glob("*.yaml")):
        src, _, dst = path.stem.partition("__")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        changed = False
        for raw in data.get("rules", []):
            if not raw.get("examples"):
                continue
            change = raw.get("change") or {}
            rule = Rule(
                id=raw["id"], name=raw.get("name", ""), order=int(raw.get("order", 0)),
                source=src, change="", source_stage=src, target_stage=dst,
                tier=raw.get("tier", "established"), match=raw.get("match") or change.get("in") or "",
                replace=raw.get("replace") if raw.get("replace") is not None else change.get("out", ""),
                left=(raw.get("env") or {}).get("left"),
                right=(raw.get("env") or {}).get("right"),
                transform=raw.get("transform", "") or "",
                params=raw.get("params", {}) or {},
                unstressed_left=bool(raw.get("unstressed_left", False)),
            ).compile()
            for ex in raw["examples"]:
                got = apply_ruleset(ex["in"], type("RS", (), {"rules": [rule], "target_stage": ""})())[0]
                if detokenize(tokenize(ex.get("out", ""))) != got:
                    print(f"{src}__{dst} {raw['id']}: {ex['in']} -> {got}  (was {ex.get('out')})")
                    ex["out"] = got
                    changed = True
        if changed:
            path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
