"""Loading of the language registry, rule files and lexicons."""

from __future__ import annotations

import gzip
import hashlib
import json
import mmap
import os
import pickle
import re
import threading
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping

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
    cache key, so a file edited is read again on the next call
    without a restart (2026-11-12).
    """
    try:
        stat = path.stat()
    except OSError:
        return _compose_yaml(path, -1, -1)
    return _compose_yaml(path, stat.st_size, stat.st_mtime_ns)


#: `yaml.CSafeLoader` (libyaml) when the wheel carries it, else the
#: pure-Python loader — same document, same result.
_YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


@lru_cache(maxsize=256)
def _compose_yaml(path: Path, size: int, mtime: int):
    if size < 0:
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as fh:
        # libyaml's loader parses the same document in a tenth of the time;
        # a page reads a dozen law and morphology files, and the pure-Python
        # parser was 0.35 s of the first page (2026-11-13).
        return yaml.load(fh, Loader=_YAML_LOADER)


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
    a cache directory and read back — a restart costs a decompression,
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
            rows.append(_canonical_entry(lang, labels, json.loads(line)))
            if limit and len(rows) >= limit:
                break
    return rows


def _canonical_entry(lang: str, labels: dict, entry: dict) -> dict:
    """One glossary row as every reader sees it, notation and labels applied."""
    label = labels.get(entry.get("word") or "")
    if label:
        if not entry.get("pos"):
            entry["pos"] = label["pos"]
        entry["pos_label"] = label["pos_label"]
        if label["structure"]:
            entry["structure"] = dict(label["structure"])
    # One word, one spelling: a stage that states a standard alphabet
    # (data/notation/) is read in it, whoever wrote the row (
    # 2026-11-13: jaw and ǰaw were two entries for "barley").
    word = notation.canonical(lang, entry.get("word") or "")
    if word:
        entry["word"] = word
    # An ancestor is named in *its own* stage's notation: a Persian row that
    # names Middle Persian *jaw* must draw the glossary's ǰaw, or one page
    # would print two spellings of one word (2026-11-13: "consistent for
    # the entire language's romanizations").
    for pair in entry.get("anc") or []:
        if (isinstance(pair, list) and len(pair) >= 2
                and isinstance(pair[1], str) and pair[1]):
            pair[1] = notation.canonical(str(pair[0]), pair[1])
    return entry


@lru_cache(maxsize=64)
def lexicon_index(lang: str) -> dict[str, list[dict]]:
    idx: dict[str, list[dict]] = {}
    for entry in lexicon(lang):
        idx.setdefault(entry["word"].lower(), []).append(entry)
    return idx


#: A gloss in parentheses at the very end of a form: ``*per- (fare)``.
#: Only a trailing one is dictionary apparatus; a parenthesis inside the form
#: is the movable s (``*(s)pend-``) and is handled below.
_TRAILING_GLOSS = re.compile(r"\s*\([^()]*\)\s*$")
#: A parenthetical that is one or two *sounds* is optional notation, and its
#: letters are part of the form: Middle Persian pādixšā(y) is pādixšāy, and the
#: rung printed pādixšā with a stray «y» as its gloss (critic batch 08,
#: 2026-11-13).
_TRAILING_SOUND = re.compile(r"\s*\(([^\W\d_]{1,2})\)\s*$", re.UNICODE)


def normalise_etymon(form: str) -> str:
    """Strip the notation that belongs to a dictionary, not to a derivation.

    ``*bʰeh₂g-`` → ``*bʰeh₂g``; ``*(s)pend-`` → ``*spend`` (the movable s is
    treated as present); ``(*kʷ)`` style brackets are dropped.

    Three pieces of dictionary apparatus are removed whole rather than merged
    into the form, because each would otherwise become part of a word that no
    dictionary holds: a sense label after a hash (``*kʷís#Determiner`` →
    ``*kʷís``), a gloss in trailing parentheses (``*per- (fare)`` → ``*per``),
    and the second member of an alternation (``*ḱḗr ~ *kr̥d-`` → ``*ḱḗr``, the
    first member being the one the entry names first).  A genuine two-word
    lemma such as ``newe founde`` carries none of these and is left whole: a
    space is a word boundary, never a label.
    """
    form = form.strip()
    # The overwhelmingly common case is a plain glossary headword, and this
    # ran once per entry when a language's lemma index was built (164k Persian
    # headwords): nothing to strip, nothing to compose (2026-11-12).
    if not any(ch in form for ch in "#()~*") and form[:1] != "-" and form[-1:] != "-":
        return form
    if "#" in form:
        form = form.split("#", 1)[0]
    sound = _TRAILING_SOUND.search(form)
    if sound:
        form = form[: sound.start()] + sound.group(1)
    form = _TRAILING_GLOSS.sub("", form)
    if "~" in form:
        form = form.split("~", 1)[0]
    form = form.strip().strip("*").strip()
    form = form.replace("(", "").replace(")", "")
    return form.strip("-").strip()


#: Bumped when the shape of the row store changes.  The hundreds place is the
#: parsed-glossary shape it copies, so a change to `_canonical_entry` retires
#: the row text with the parse cache instead of leaving rows of the old shape.
ROW_STORE_VERSION = LEXICON_VERSION * 100 + 1


def _lexicon_source(lang: str) -> tuple[Path, object] | None:
    """The glossary file a stage is read from, gzip preferred over plain."""
    packed = LEXICON_DIR / f"{lang}.jsonl.gz"
    if packed.exists():
        return packed, gzip.open
    plain = LEXICON_DIR / f"{lang}.jsonl"
    if plain.exists():
        return plain, open
    return None


def lexicon_source(lang: str) -> Path | None:
    """The file a stage's glossary is read from, or ``None`` if it has none."""
    source = _lexicon_source(lang)
    return source[0] if source else None


class _RowStore:
    """One stage's rows on disk, read by offset instead of all at once.

    A word page asks every language of the family for one spelling, and
    loading each 16 MB glossary to answer that was the cold-page cost: 31
    gzip pickles in, a handful of rows out.  The row text is kept as one plain
    file and the index as `word -> byte offset`, so a lookup is a dictionary
    hit and one `json.loads`, and the whole stage never becomes a Python dict
    (2026-11-13).
    """

    def __init__(self, rows_path: Path, index: dict) -> None:
        self.words: dict[str, int] = index["words"]
        self.more: dict[str, tuple[int, ...]] = index.get("more") or {}
        self.lemmas: dict[str, str] = index.get("lemmas") or {}
        # One page asks for the same handful of spellings again and again
        # (the cognate row, its senses, its evidence); a bounded memo keeps the
        # repeated decodes without ever becoming the whole glossary.
        self._cache: dict[str, list[dict]] = {}
        # Mapping from the descriptor keeps the text readable after the
        # descriptor closes, so a page holds no open file per language.
        with rows_path.open("rb") as fh:
            if fh.seek(0, os.SEEK_END):
                self._mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
            else:
                self._mm = None

    def _row(self, offset: int) -> dict:
        if self._mm is None:
            raise ValueError("empty row store")
        end = self._mm.find(b"\n", offset)
        if end < 0:
            end = len(self._mm)
        return json.loads(self._mm[offset:end].decode("utf-8"))

    def rows(self, word: str) -> list[dict]:
        hit = self._cache.get(word)
        if hit is not None:
            return hit
        first = self.words.get(word)
        if first is None:
            return []
        rows = [self._row(first), *(self._row(off) for off in self.more.get(word, ()))]
        if len(self._cache) >= 512:
            self._cache.clear()
        self._cache[word] = rows
        return rows


class _LemmaRows(Mapping):
    """``lemma -> its stage row``, decoding the one row a lookup asks for."""

    def __init__(self, store: _RowStore) -> None:
        self._store = store
        self._lemmas = store.lemmas

    def __getitem__(self, key: str) -> dict:
        rows = self._store.rows(self._lemmas[key])
        if not rows:
            raise KeyError(key)
        return rows[0]

    def get(self, key: str, default=None):
        word = self._lemmas.get(key)
        if word is None:
            return default
        rows = self._store.rows(word)
        return rows[0] if rows else default

    def __iter__(self):
        return iter(self._lemmas)

    def __len__(self) -> int:
        return len(self._lemmas)


_ROW_STORES: dict[str, tuple[tuple, _RowStore]] = {}
_ROW_SOURCES: dict[str, tuple[Path, object]] = {}
_ROW_LOCK = threading.Lock()


def _structure_stat() -> tuple[int, int]:
    try:
        st = (DATA / "dehkhoda" / "structure.jsonl.gz").stat()
    except OSError:
        return (0, 0)
    return (st.st_size, st.st_mtime_ns)


def _row_store_paths(lang: str, stamp: str) -> Path:
    return Path(str(CACHE_DIR / f"lexicon-rows-{lang}-v{ROW_STORE_VERSION}-{stamp}")
                + ".jsonl")


def _write_row_store(lang: str, rows_path: Path) -> dict:
    """Write the plain row text and return the offset index built beside it."""
    words: dict[str, int] = {}
    more: dict[str, list[int]] = {}
    lemmas: dict[str, str] = {}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = rows_path.with_name(f"{rows_path.name}.{os.getpid()}.tmp")
    offset = 0
    try:
        with tmp.open("wb") as out:
            # `lexicon()` is the parsed glossary every other reader uses, and
            # its cache already paid the notation pass; re-reading the source
            # here made a rebuild twice as expensive (2026-11-13).
            for entry in lexicon(lang):
                word = str(entry["word"])
                if word in words:
                    more.setdefault(word, []).append(offset)
                else:
                    words[word] = offset
                    # `data.lexicon_index` groups spellings case-insensitively;
                    # the lemma keys keep that behaviour while the row index
                    # keeps the exact headword `service.lang_index` uses.
                    lower = word.lower()
                    lemma = normalise_etymon(lower)
                    lemmas.setdefault(lemma, word)
                    lemmas.setdefault(lemma.casefold(), word)
                    quoted = str(entry.get("translit_quoted") or "")
                    if quoted:
                        lemmas.setdefault(normalise_etymon(quoted), word)
                    if "\u200c" in lower:
                        lemmas.setdefault(
                            normalise_etymon(lower.replace("\u200c", "")), word)
                data = json.dumps(entry, ensure_ascii=False,
                                  separators=(",", ":")).encode("utf-8")
                out.write(data)
                out.write(b"\n")
                offset += len(data) + 1
        tmp.replace(rows_path)
    except BaseException:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return {"version": ROW_STORE_VERSION, "words": words,
            "more": {word: tuple(offsets) for word, offsets in more.items()},
            "lemmas": lemmas}


def _row_store(lang: str) -> _RowStore | None:
    """The stage's row store, or ``None`` when the cache cannot be used."""
    source = _ROW_SOURCES.get(lang)
    if source is None:
        source = _lexicon_source(lang)
        if source is None:
            return None
        _ROW_SOURCES[lang] = source
    file = source[0]
    try:
        stat = file.stat()
    except OSError:
        _ROW_SOURCES.pop(lang, None)
        return None
    key = (stat.st_size, stat.st_mtime_ns, *_structure_stat())
    hit = _ROW_STORES.get(lang)
    if hit and hit[0] == key:
        return hit[1]
    # The daemon prewarm and a reader can meet here; one build at a time keeps
    # them from writing the same temporary file.
    with _ROW_LOCK:
        hit = _ROW_STORES.get(lang)
        if hit and hit[0] == key:
            return hit[1]
        sources = [file, DATA / "dehkhoda" / "structure.jsonl.gz"]
        stamp = cache_stamp(*sources)
        rows_path = _row_store_paths(lang, stamp)
        try:
            index = cached(f"lexicon-rows-{lang}", ROW_STORE_VERSION, sources,
                           lambda: _write_row_store(lang, rows_path))
            if not rows_path.exists():
                # An index without its row text cannot answer; rewrite both.
                index = _write_row_store(lang, rows_path)
            store = _RowStore(rows_path, index)
        except (OSError, ValueError):
            return None
        _ROW_STORES[lang] = (key, store)
        return store


def lexicon_rows(lang: str, word: str) -> list[dict]:
    """The rows one spelling has in one stage, without loading the stage."""
    store = _row_store(lang)
    if store is not None:
        return store.rows(word)
    source = _lexicon_source(lang)
    if source is None:
        return []
    file, opener = source
    labels = structures().get(lang) or {}
    rows: list[dict] = []
    with opener(file, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entry = _canonical_entry(lang, labels, json.loads(line))
                if entry["word"] == word:
                    rows.append(entry)
    return rows


def lexicon_words(lang: str):
    """Every headword exactly as the glossary spells it, in glossary order."""
    store = _row_store(lang)
    if store is not None:
        return store.words.keys()
    out: dict[str, None] = {}
    for entry in lexicon(lang):
        out.setdefault(entry["word"], None)
    return out.keys()


def lexicon_spellings(lang: str):
    """Every headword key of `lexicon_index`, lower-cased and de-duplicated."""
    store = _row_store(lang)
    if store is not None:
        def lower_keys():
            seen: set[str] = set()
            for word in store.words:
                lower = word.lower()
                if lower not in seen:
                    seen.add(lower)
                    yield lower
        return lower_keys()
    return lexicon_index(lang).keys()


def lexicon_lemma_rows(lang: str) -> Mapping[str, dict]:
    """A stage's first row per notation-free lemma, read on demand."""
    store = _row_store(lang)
    if store is not None:
        return _LemmaRows(store)
    # No cache directory: the old full index still answers, just slowly.
    out: dict[str, dict] = {}
    for word, rows in lexicon_index(lang).items():
        out.setdefault(normalise_etymon(word), rows[0])
        out.setdefault(normalise_etymon(word).casefold(), rows[0])
        quoted = rows[0].get("translit_quoted") or ""
        if quoted:
            out.setdefault(normalise_etymon(quoted), rows[0])
        if "\u200c" in word:
            out.setdefault(normalise_etymon(word.replace("\u200c", "")), rows[0])
    return out


# Longer kind first: `lexicon` would otherwise match the head of
# `lexicon-rows-en` and leave a language called "-rows-en".
_ARTEFACT = re.compile(r"^(lexicon-rows|lexicon)-(.+)-v(\d+)-([0-9a-f]{20})"
                       r"\.(?:pickle\.gz|jsonl)$")


def prune_cache(remove_all: bool = False) -> tuple[int, int]:
    """Delete the cached artefacts no reader can ask for again.

    Every artefact is named after the version that shaped it and the stamp of
    the files it was built from, so a file whose name no longer matches the
    current ones is dead: the version moved, a glossary was edited, a language
    was removed.  Only the two glossary artefacts are judged — other caches are
    cheap, and guessing at their inputs here would duplicate the code that
    wrote them.  Returns (files removed, bytes).
    """
    files = removed = 0
    try:
        paths = sorted(CACHE_DIR.iterdir())
    except OSError:
        return 0, 0
    for path in paths:
        if not path.is_file():
            continue
        if remove_all:
            dead = True
        else:
            match = _ARTEFACT.match(path.name)
            if not match:
                continue
            kind, lang, version, stamp = match.groups()
            want = LEXICON_VERSION if kind == "lexicon" else ROW_STORE_VERSION
            if int(version) != want:
                dead = True
            else:
                source = _lexicon_source(lang)
                inputs = [source[0]] if source else []
                if kind == "lexicon-rows":
                    inputs.append(DATA / "dehkhoda" / "structure.jsonl.gz")
                dead = not inputs or cache_stamp(*inputs) != stamp
        if not dead:
            continue
        try:
            size = path.stat().st_size
            path.unlink()
        except OSError:
            continue
        files += 1
        removed += size
    return files, removed


_LEXICONS: dict = {"key": None, "rows": []}


def _lexicon_dir_key() -> tuple:
    """One `stat` of the folder: adding or removing a glossary moves it."""
    try:
        st = LEXICON_DIR.stat()
        return (st.st_mtime_ns,)
    except OSError:
        return ()


def available_lexicons() -> list[tuple[str, int]]:
    """Every glossary file: its language and its size in bytes.

    A word page asked this once per headword it drew, and each answer stat'ed
    every glossary file — 17,000 words cost 640,000 `stat` calls and six
    seconds a glossary request (2026-11-13).  The folder's own stamp is the
    key now, so adding or removing a glossary still shows up at once, while the
    per-file sizes are read once.  Editing a file in place keeps its size in
    this list, which only orders "the largest stages" — the rows themselves
    come from `lexicon()`, whose cache does check the file.
    """
    key = _lexicon_dir_key()
    if _LEXICONS["key"] != key:
        rows = []
        for path in sorted(LEXICON_DIR.glob("*.jsonl*")):
            try:
                size = path.stat().st_size
            except OSError:
                continue
            rows.append((path.name.split(".")[0], size))
        _LEXICONS.update(key=key, rows=rows)
    return list(_LEXICONS["rows"])


def cognate_sets() -> list[dict]:
    out: list[dict] = []
    for path in sorted(COGNATE_DIR.glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    return out
