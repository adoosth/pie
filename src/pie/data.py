"""Loading of the language registry, rule files and lexicons."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import yaml

from . import notation
from .rules import RuleSet

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RULE_DIR = DATA / "rules"
LEXICON_DIR = DATA / "lexicon"
COGNATE_DIR = DATA / "cognate_sets"

if not DATA.is_dir():
    raise RuntimeError(
        f"pie data directory not found at {DATA}. The dataset lives in the repository, "
        "so install it in editable mode from the repository root: pip install -e ."
    )


def measurement_inputs(lexicon_dir: Path | None = None,
                        rules_dir: Path | None = None) -> dict[str, str]:
    """A cheap fingerprint of the files a coverage measurement reads.

    The measurement takes minutes, so its artifacts are cached and published;
    comparing names, sizes and modification times is enough to say whether the
    data they describe has changed since (`tools/coverage.py`).
    """
    def digest(directory: Path, pattern: str) -> str:
        rows = []
        for path in sorted(directory.glob(pattern)):
            try:
                stat = path.stat()
            except OSError:
                continue
            rows.append(f"{path.name}\t{stat.st_size}\t{stat.st_mtime_ns}")
        return hashlib.sha1("\n".join(rows).encode("utf-8")).hexdigest()

    return {
        "lexicon": digest(Path(lexicon_dir or LEXICON_DIR), "*.jsonl.gz"),
        "rules": digest(Path(rules_dir or RULE_DIR), "*.yaml"),
    }


def inputs_stale(stored, current: dict[str, str] | None = None) -> bool:
    """Whether ``stored`` names different inputs from the current data.

    An artifact written before inputs were recorded has nothing to compare,
    and is treated as not stale rather than crashing the reader.
    """
    if not isinstance(stored, dict) or not stored:
        return False
    return dict(stored) != (measurement_inputs() if current is None else current)


def _load_yaml(path: Path):
    """A YAML file, composed once and reused until the file itself changes.

    Composing a rule or morphology file costs milliseconds each, and a page
    reads a handful of them for every rung of the ladder.  The mtime is the
    cache key, so a file the admin edits is read again on the next call
    without a restart (2026-11-12).
    """
    try:
        stat = path.stat()
    except OSError:
        return _compose_yaml(path, -1, -1)
    return _compose_yaml(path, stat.st_size, stat.st_mtime_ns)


@lru_cache(maxsize=256)
def _compose_yaml(path: Path, size: int, mtime: int):
    if size < 0:
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


#: Where derived structures may be kept between runs.  Nothing here is part of
#: the repository: a glossary is parsed once and its indexes are built once,
#: however many times the server restarts (2026-11-12).  Every file is keyed by
#: the size and modification time of the data it was built from, so editing a
#: word or a rule file invalidates it with no command to remember; the version
#: tag is bumped when the shape of the value itself changes.
CACHE_DIR = Path(os.environ.get("PIE_CACHE_DIR")
                 or (Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
                     / "pie"))


def cache_stamp(*paths: Path | str) -> str:
    """The identity of the files a cached value was built from."""
    rows = []
    for path in paths:
        if not path:
            continue
        path = Path(path)
        try:
            stat = path.stat()
        except OSError:
            rows.append(f"{path.name}\t-")
        else:
            rows.append(f"{path.name}\t{stat.st_size}\t{stat.st_mtime_ns}")
    return hashlib.sha1("\n".join(rows).encode("utf-8")).hexdigest()[:20]


def cached(name: str, version: int, sources: Iterable[Path | str], build):
    """A value built from data files, kept on disk until those files change.

    The first request after a restart used to re-parse 591k glossary rows and
    rebuild every index; a word page took ten seconds.  The parsed rows and the
    indexes built from them are the same on every run, so they are written to
    the user's cache directory and read back — a restart costs a decompression,
    not a re-derivation.  A cache that cannot be written is not an error: the
    value is built and returned exactly as before.
    """
    key = f"{name}-v{version}-{cache_stamp(*sources)}.pickle.gz"
    file = CACHE_DIR / key
    try:
        with gzip.open(file, mode="rb") as fh:
            return pickle.load(fh)
    except (OSError, EOFError, pickle.UnpicklingError, ValueError, AttributeError):
        pass
    value = build()
    tmp: Path | None = None
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = file.with_name(f"{file.name}.{os.getpid()}.tmp")
        with gzip.open(tmp, mode="wb", compresslevel=1) as fh:
            pickle.dump(value, fh, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(file)
    except OSError:
        if tmp is not None:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
    return value


@lru_cache(maxsize=1)
def languages() -> dict[str, dict]:
    rows = _load_yaml(DATA / "languages.yaml")
    return {row["id"]: row for row in rows}


@lru_cache(maxsize=1)
def varieties() -> dict[str, dict]:
    """Registers of a modelled stage, by the code a record may name them with.

    A Late Latin or Vulgar Latin form is a Latin form: ``stage_of`` reads the
    variety at its base stage, so the laws out of that stage apply unchanged
    and no chain step is invented.  The file states which codes are registers
    (``data/language_varieties.yaml``); a different language is never one.
    """
    path = DATA / "language_varieties.yaml"
    if not path.exists():
        return {}
    return _load_yaml(path).get("varieties") or {}


@lru_cache(maxsize=1)
def language_names() -> dict[str, dict]:
    """Wiktionary's names for the codes in its descendant trees.

    The cognate sets carry codes the registry has no row for (``xcl``,
    ``yms``, ``hyx-pro`` …).  `tools/build_language_names.py` harvests a name
    and a branch for each from Wiktionary's descendant trees; this is that
    table, keyed by code.
    """
    path = DATA / "language_names.json"
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return raw.get("languages") or {}


@lru_cache(maxsize=1)
def wiktionary_language_names() -> dict[str, str]:
    """Every language, etymology-language and family name Wiktionary defines.

    `data/language_names.json` only reaches the codes in the PIE descendant
    tree; a borrowing can name any language at all (Old Median, Brokskat,
    Old Northern French).  `tools/build_wiktionary_names.py` saves
    Wiktionary's own tables here, so a code a record prints can always be
    given the name Wiktionary gives it (2026-11-12).
    """
    path = DATA / "sources" / "wiktionary_language_names.json.gz"
    if not path.exists():
        return {}
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError):
        return {}
    return raw.get("names") or {}


@lru_cache(maxsize=1)
def language_name_extras() -> dict[str, dict]:
    """Display names for codes the descendant-tree harvest never reached.

    A borrowed word's ancestry can run through a language that is not in the
    PIE descendant tree at all (Middle Chinese, Yiddish, Portuguese), and a
    rung of its ladder must name the language rather than print its code.
    Display only: this file never classifies a language — membership in
    `data/non_ie_sources.yaml` does that (2026-11-09).
    """
    path = DATA / "language_names_extra.yaml"
    if not path.exists():
        return {}
    return _load_yaml(path).get("names") or {}


@lru_cache(maxsize=1)
def non_ie_sources() -> dict[str, dict]:
    """The register of donor languages outside the Indo-European family.

    Membership in this file is what makes a loan ``non_ie``; the name beside
    the code is also the name a rung prints when no other table has one.
    """
    path = DATA / "non_ie_sources.yaml"
    if not path.exists():
        return {}
    return (_load_yaml(path) or {}).get("sources") or {}


def language_name(code: str) -> str:
    """The English name of a language code, or the code when nothing names it.

    One resolver for every place a code could reach a reader: the word page's
    ancestry rows, the loan badge ("borrowed from …"), the ladder's rungs and
    the construction pieces.  The registry wins; then the names harvested from
    the descendant trees; then the display names for borrowers outside the
    tree; then Wiktionary's full language table; then a register of a modelled
    stage; then the donor register.

    Two shapes the records write are read here too: a comma-joined set of
    codes (``ru,uk``) is named part by part, and the abbreviated Latin stages
    some etymology trees use (``ML.``, ``LL.``, ``NL.``, ``VL.``, ``EL.``)
    are named in full.  A code no table names still comes back as the code —
    the guard test in `tests/test_language_names.py` is what keeps that from
    happening for a code the data actually refers to (2026-11-12).
    """
    text = str(code or "").strip()
    if not text:
        return ""
    if "," in text:
        parts = [part.strip() for part in text.split(",") if part.strip()]
        names = [language_name(part) for part in parts]
        return " / ".join(dict.fromkeys(name for name in names if name))
    abbr = LATIN_STAGE_ABBREVIATIONS.get(text)
    if abbr:
        return language_name(abbr)
    row = languages().get(text)
    if row and row.get("name"):
        return str(row["name"])
    named = language_names().get(text) or {}
    if named.get("name"):
        return str(named["name"])
    extra = language_name_extras().get(text) or {}
    if extra.get("name"):
        return str(extra["name"])
    full = wiktionary_language_names().get(text)
    if full:
        return str(full)
    variety = varieties().get(text) or {}
    if variety.get("name") and variety.get("of") and variety["of"] != text:
        return str(variety["name"])
    donor = non_ie_sources().get(text) or {}
    if donor.get("name"):
        return str(donor["name"])
    return text


#: The abbreviations a few etymology sources print for Latin's own stages.
LATIN_STAGE_ABBREVIATIONS = {
    "ML.": "la-med", "LL.": "la-lat", "NL.": "la-new",
    "VL.": "la-vul", "EL.": "la-ecc",
}


def stage_of(lang: str) -> str:
    """The stage a recorded language code is read at (itself if not a variety)."""
    row = varieties().get(lang)
    return (row or {}).get("of") or lang


@lru_cache(maxsize=1)
def sources() -> dict[str, dict]:
    rows = _load_yaml(DATA / "sources.yaml")
    return {row["id"]: row for row in rows}


def ancestor_chain(lang: str) -> list[str]:
    """Walk `ancestor` links from ``lang`` back to the root."""
    chain = [lang]
    seen = set(chain)
    while True:
        parent = languages().get(chain[-1], {}).get("ancestor")
        if not parent or parent in seen:
            break
        chain.append(parent)
        seen.add(parent)
    return list(reversed(chain))


def derivation_chain(lang: str) -> list[str]:
    """The stage chain used to derive ``lang`` from Proto-Indo-European."""
    row = languages().get(lang, {})
    if row.get("chain"):
        return list(row["chain"])
    return ancestor_chain(lang)


def descendants(lang: str) -> list[str]:
    return [k for k, v in languages().items() if v.get("ancestor") == lang]


#: Bumped when the shape of a compiled rule changes.
RULESET_VERSION = 1


@lru_cache(maxsize=1)
def rulesets() -> dict[tuple[str, str], RuleSet]:
    """Every registered transition's laws, compiled once.

    Forty-three YAML files of prose take a couple of seconds to compose, and
    the result is the same for every request until a rule file changes.  The
    compiled sets are therefore kept beside the parsed glossaries, stamped on
    the rule files' own names, sizes and times (2026-11-12).
    """
    files = sorted(RULE_DIR.glob("*.yaml"))
    return cached("rulesets", RULESET_VERSION, files, lambda: _parse_rulesets(files))


def _parse_rulesets(files: list[Path]) -> dict[tuple[str, str], RuleSet]:
    out: dict[tuple[str, str], RuleSet] = {}
    for path in files:
        src, _, dst = path.stem.partition("__")
        if not dst:
            continue
        data = _load_yaml(path)
        out[(src, dst)] = RuleSet.from_dict(data, src, dst)
    return out


def rulesets_for_chain(chain: list[str]) -> list[RuleSet]:
    rs = rulesets()
    return [rs[(a, b)] for a, b in zip(chain, chain[1:]) if (a, b) in rs]


def missing_stages(chain: list[str]) -> list[tuple[str, str]]:
    rs = rulesets()
    return [(a, b) for a, b in zip(chain, chain[1:]) if (a, b) not in rs]


@lru_cache(maxsize=1)
def structures() -> dict[str, dict[str, dict]]:
    """Grammar labels a dictionary prints beside its own headwords.

    ``data/dehkhoda/structure.jsonl.gz`` is Dehkhoda's parenthetical for every
    headword — ``(اِ مرکب)``, ``(ص نسبی)``, ``(اِخ)`` — read from the cached
    entry pages by `tools/dehkhoda_structure.py`.  It is a *record of what the
    dictionary says the word is*, not an etymology, so it is kept apart from
    `anc` and joins the entry as `pos` (only when the entry has none),
    `pos_label` (verbatim) and `structure` (the flags the label states).  A
    language with no such file shows nothing (2026-11-10).

    The key is `fa` because Dehkhoda is a dictionary *of Persian*: the file has
    no language column, and a second dictionary gets its own reader and its own
    key rather than being folded in here (review, 2026-11-10).
    """
    out: dict[str, dict[str, dict]] = {}
    path = DATA / "dehkhoda" / "structure.jsonl.gz"
    if not path.exists():
        return out
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            word = row.get("word")
            if not word:
                continue
            entry = {"pos": row.get("pos") or "", "pos_label": row.get("label") or "",
                     "structure": {k: True for k in
                                   ("compound", "relational", "diminutive",
                                    "huzvarish", "affix", "name") if row.get(k)}}
            out.setdefault("fa", {})[word] = entry
    return out


#: Bumped when the shape of a parsed glossary row changes.
LEXICON_VERSION = 3  # 3: headwords and the ancestors they name are folded
# into the stage's standard notation (data/notation/)


def lexicon_paths() -> list[Path]:
    """Every glossary file, for naming a cache that reads the whole corpus."""
    return [path for path in sorted(LEXICON_DIR.iterdir())
            if path.name.endswith((".jsonl.gz", ".jsonl"))]


@lru_cache(maxsize=64)
def lexicon(lang: str, limit: int | None = None) -> list[dict]:
    path = LEXICON_DIR / f"{lang}.jsonl.gz"
    plain = LEXICON_DIR / f"{lang}.jsonl"
    if path.exists():
        opener = gzip.open
        file = path
    elif plain.exists():
        opener = open
        file = plain
    else:
        return []
    if limit is None:
        # The parsed rows are the same on every run until the file changes: a
        # restart reads them back instead of decompressing and parsing half a
        # million JSON lines again (2026-11-12).
        return cached(f"lexicon-{lang}", LEXICON_VERSION,
                      [file, DATA / "dehkhoda" / "structure.jsonl.gz"],
                      lambda: _parse_lexicon(file, opener, lang))
    return _parse_lexicon(file, opener, lang, limit=limit)


def _parse_lexicon(file: Path, opener, lang: str, limit: int | None = None) -> list[dict]:
    labels = structures().get(lang) or {}
    rows: list[dict] = []
    with opener(file, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            label = labels.get(entry.get("word") or "")
            if label:
                if not entry.get("pos"):
                    entry["pos"] = label["pos"]
                entry["pos_label"] = label["pos_label"]
                if label["structure"]:
                    entry["structure"] = dict(label["structure"])
            # One word, one spelling: a stage that states a standard alphabet
            # (data/notation/) is read in it, whoever wrote the row (admin,
            # 2026-11-13: jaw and ǰaw were two entries for "barley").
            word = notation.canonical(lang, entry.get("word") or "")
            if word:
                entry["word"] = word
            # An ancestor is named in *its own* stage's notation: a Persian
            # row that names Middle Persian *jaw* must draw the glossary's
            # ǰaw, or one page would print two spellings of one word (admin,
            # 2026-11-13: "consistent for the entire language's romanizations").
            for pair in entry.get("anc") or []:
                if (isinstance(pair, list) and len(pair) >= 2
                        and isinstance(pair[1], str) and pair[1]):
                    pair[1] = notation.canonical(str(pair[0]), pair[1])
            rows.append(entry)
            if limit and len(rows) >= limit:
                break
    return rows


@lru_cache(maxsize=64)
def lexicon_index(lang: str) -> dict[str, list[dict]]:
    idx: dict[str, list[dict]] = {}
    for entry in lexicon(lang):
        idx.setdefault(entry["word"].lower(), []).append(entry)
    return idx


def available_lexicons() -> list[tuple[str, int]]:
    out = []
    for path in sorted(LEXICON_DIR.glob("*.jsonl*")):
        lang = path.name.split(".")[0]
        out.append((lang, path.stat().st_size))
    return out


def cognate_sets() -> list[dict]:
    out: list[dict] = []
    for path in sorted(COGNATE_DIR.glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    return out
