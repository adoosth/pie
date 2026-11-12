"""Fold the per-word Dehkhoda cache into shards, and say what it weighs.

`data/meanings/fa/` holds one small gzip per word — 153,206 of them, 83 MB of
text that takes 612 MB on disk because every file rounds up to a 4 KB block.
The dictionary is not heavy; the blocks are.  `--pack` writes the same rows into
256 shards of about 600 words each (`data/meanings/packs/fa-NNN.jsonl.gz`), each
shard written beside its destination and renamed, and only then removes the
loose files.  A word read after the pack is a loose file again and still wins
over its shard, so packing is always safe to repeat.

**The loose files are deleted, not moved aside** (2026-11-12): the first run
moved 601 MB to `/tmp`, on the same filesystem, and reclaimed nothing at all.
Before anything is deleted the shards are read back and every word the run
wrote has to be there — verified, then removed.

    python3 tools/pack_meanings.py --status
    python3 tools/pack_meanings.py --pack
    python3 tools/pack_meanings.py --pack --keep /tmp/pie-meanings-loose   # keep a copy
"""
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import sys
import zlib
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import meanings  # noqa: E402

LOOSE = meanings.CACHE / "fa"
PACKS = meanings.PACKS


def read_shard(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("w"):
                    out[row["w"]] = row.get("row") or {}
    except OSError:
        pass
    return out


def loose_rows() -> list[tuple[Path, str, dict]]:
    rows = []
    for path in sorted(LOOSE.glob("*.json.gz")):
        word = unquote(path.name[: -len(".json.gz")])
        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                row = json.load(fh)
        except (OSError, ValueError):
            continue
        rows.append((path, word, row))
    return rows


def blocks(paths) -> int:
    return sum(p.stat().st_blocks * 512 for p in paths if p.exists())


def status() -> None:
    loose = list(LOOSE.glob("*.json.gz")) if LOOSE.exists() else []
    shards = list(PACKS.glob("*.jsonl.gz")) if PACKS.exists() else []
    loose_bytes = sum(p.stat().st_size for p in loose)
    shard_bytes = sum(p.stat().st_size for p in shards)
    print(f"loose   {len(loose):>7,} files  {loose_bytes/1e6:7.1f} MB of text  "
          f"{blocks(loose)/1e6:7.1f} MB on disk")
    print(f"packs   {len(shards):>7,} files  {shard_bytes/1e6:7.1f} MB of text  "
          f"{blocks(shards)/1e6:7.1f} MB on disk")
    words = sum(len(read_shard(p)) for p in shards) if shards else 0
    print(f"words   {words + len(loose):>7,} (packed {words:,} + loose {len(loose):,})")


def pack(keep: Path) -> int:
    rows = loose_rows()
    if not rows:
        print("nothing loose to pack")
        return 0
    by_shard: dict[int, dict[str, dict]] = {}
    for _path, word, row in rows:
        by_shard.setdefault(zlib.crc32(word.encode("utf-8")) % meanings.PACK_SHARDS, {})[word] = row
    PACKS.mkdir(parents=True, exist_ok=True)
    written = 0
    for index, fresh in sorted(by_shard.items()):
        path = PACKS / f"fa-{index:03d}.jsonl.gz"
        merged = read_shard(path)
        merged.update(fresh)
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as stream:
                for word in sorted(merged):
                    stream.write(json.dumps({"w": word, "row": merged[word]},
                                            ensure_ascii=False,
                                            separators=(",", ":")).encode("utf-8") + b"\n")
        tmp.replace(path)
        written += 1
    # Read the shards back before letting go of the loose files: a word that
    # is in a shard is fetched from there, so a shard that lost it would turn
    # a cached entry into a network request without anyone noticing.
    written_words = {word for _p, word, _row in rows}
    present = set()
    for index in sorted(by_shard):
        present.update(read_shard(PACKS / f"fa-{index:03d}.jsonl.gz"))
    missing = sorted(written_words - present)
    if missing:
        print(f"NOT removing the loose files: {len(missing)} words are not in a shard "
              f"(first: {missing[:5]})")
        status()
        return 1
    if keep is not None:
        keep.mkdir(parents=True, exist_ok=True)
        moved = 0
        for path, _word, _row in rows:
            target = keep / path.name
            if target.exists():
                target = keep / f"{moved}-{path.name}"
            shutil.move(str(path), str(target))
            moved += 1
        print(f"packed {len(rows):,} words into {written} shards, verified; "
              f"moved {moved:,} loose files to {keep}")
    else:
        removed = 0
        for path, _word, _row in rows:
            path.unlink(missing_ok=True)
            removed += 1
        print(f"packed {len(rows):,} words into {written} shards, verified; "
              f"removed {removed:,} loose files")
    status()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pack", action="store_true", help="fold the loose files into shards")
    ap.add_argument("--status", action="store_true", help="say what the cache weighs")
    ap.add_argument("--keep", type=Path, default=None,
                    help="move the loose files here instead of deleting them")
    args = ap.parse_args()
    if args.pack:
        return pack(args.keep)
    status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
