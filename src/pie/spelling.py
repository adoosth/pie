"""The orthographic layer: how a stage's words are actually written.

The sound laws stop at a phonemic form (``*pṓds → fˈūt``); a dictionary writes
``foot``.  The step from the phonemic form to the written word is not a sound
change, so it is kept in its own layer with its own files
(``data/spelling/<lang>.yaml``) and its own tier (``orthographic``).  Coverage
therefore reports two numbers: how much the **laws** explain, and how much the
laws **plus the writing conventions** explain.  The historical baseline is
never inflated by the second one.

A spelling file is an ordinary ordered rule list — same pattern language, same
examples, same verification as a sound law — applied once, after the language's
last phonological stage, with the letters as replacements.  Ordering is what
lets context survive: rules that depend on a phoneme (German ``ʃ → s`` before
``p t``) run before the vowel letters are written.

    >>> from pie.spelling import spell
    >>> spell("fˈūt", "en")
    'fut'
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from . import data, writing
from .rules import RuleSet, apply_ruleset
from .phonology import is_vowel, tokenize

SPELLING_DIR = data.DATA / "spelling"


@lru_cache(maxsize=None)
def ruleset(lang: str) -> RuleSet | None:
    """The spelling ruleset for ``lang``, or ``None`` when none is written."""
    path = SPELLING_DIR / f"{lang}.yaml"
    if not path.exists():
        return None
    raw = data._load_yaml(path)
    rs = RuleSet.from_dict(raw, f"{lang}~", f"{lang}#spelling")
    rs.name = (raw.get("stage") or {}).get("name", f"{lang} spelling")
    # A spelling replacement is a *letter string*, not a phonological form: the
    # tokeniser would read ⟨þ⟩ back as θ (its philological alias) and silently
    # undo the rule.  Keep the letters exactly as the file writes them.
    written = {row.get("id"): row.get("replace") for row in (raw.get("rules") or [])}
    for rule in rs.rules:
        rep = written.get(rule.id)
        if isinstance(rep, str):
            rule._replace = list(rep)
    return rs


def available() -> list[str]:
    return sorted(p.stem for p in SPELLING_DIR.glob("*.yaml")) if SPELLING_DIR.is_dir() else []


def spell(form: str, lang: str, disabled=()) -> str:
    """Write a phonemic form as ``lang`` spells it (identity if no file)."""
    rs = ruleset(lang)
    if rs is None:
        return form
    out, _steps = apply_ruleset(form, rs, disabled)
    return out


def steps(form: str, lang: str, disabled=()) -> list:
    """The spelling rules that applied, for the word page and the CLI."""
    rs = ruleset(lang)
    if rs is None:
        return []
    _out, steps = apply_ruleset(form, rs, disabled)
    return steps


def applies(lang: str) -> bool:
    return ruleset(lang) is not None


def matches(form: str, target: str, lang: str) -> bool:
    """True when the spelled form equals the attested word."""
    return bool(target) and spell(form, lang) == target


def check(rs: RuleSet) -> list[str]:
    """Validate a spelling file's examples against the whole file.

    Unlike a sound law, an orthographic rule is normally *one step of a
    convention* (θ → th, /æ/ → a), so an example that showed only that step
    would be unreadable.  Every example therefore gives a complete phonemic
    form and the word it is written as, and the whole file is applied.
    """
    problems: list[str] = []
    for rule in rs.rules:
        for ex in rule.examples:
            got = apply_ruleset(ex["in"], rs)[0]
            if got != ex["out"]:
                problems.append(
                    f"spelling {rs.target_stage}: example of {rule.id}: "
                    f"{ex['in']} → {got} (expected {ex['out']})"
                )
    return problems


#: Transcription variants that are **the same segment written twice**, not a
#: claim about the language: the IPA letter g has two code points (``ɡ``/``g``),
#: a rhotic is written ``r ɾ ɹ ʁ ʀ`` by different dictionaries for the one
#: phoneme, and a glottal stop is a phonetic detail that no rule models.
#: Combining marks (syllabic ``n̩``, non-syllabic ``ɪ̯``, lowered ``ɛ̝``, the
#: tie bar of ``t͡s``) and syllable dots carry no segment either.
_IPA_FOLD = {
    "ɡ": "g", "ɹ": "r", "ɾ": "r", "ʁ": "r", "ʀ": "r", "ʔ": "",
    # Aspiration is written as a modifier letter by the IPA (ɡʱ) and as a
    # superscript by the philological transcription the laws use (gʰ); one
    # segment written twice must not look like two consonants (2026-11-09).
    "ʱ": "h", "ʰ": "h",
    # The palatals and retroflexes have an IPA letter and a Sanskritist letter:
    # ɕ is ś, ʂ is ṣ, ɖ is ḍ and so on.  Folding one to the other changes no
    # segment, only its alphabet (2026-11-09).
    "ɕ": "ś", "ʂ": "ṣ", "ɖ": "ḍ", "ʈ": "ṭ", "ɳ": "ṇ", "ɭ": "ḷ", "ɲ": "ñ",
    "ɟ": "j", "ʈ": "ṭ", "ɐ": "a",
    # Two more letters the IPA uses for one segment: ɦ is h (Sanskrit aham is
    # /ɐ.ɦɐm/) and ʋ is the labial glide the philological notation writes w or v.
    "ɦ": "h", "ʋ": "v",
    # The IPA's esh and ezh are the philological š and ž.
    "ʃ": "š", "ʒ": "ž", "ʧ": "č", "ʤ": "ǰ",
}


def _readable(text: str) -> str:
    """Drop transcription detail that carries no segment.

    This is *notation* normalisation for the guard only: it never rewrites a
    rule's output.  Removing a combining mark from ``n̩`` leaves ``n``; removing
    it from ``ɪ̯`` leaves ``ɪ``, still one nucleus; removing the tie bar turns
    ``t͡s`` into ``t s``; and ``ɡ`` becomes the same letter as ``g``.
    """
    # A tied affricate is one segment: the tie bar is a mark, but the two
    # letters it joins are a single phoneme the laws write c or j.
    text = (text.replace("t\u0361\u0255", "c").replace("d\u0361\u0291", "j")
                .replace("t\u0361\u0283", "č").replace("d\u0361\u0292", "ǰ")
                # A dictionary often writes an affricate without the tie bar;
                # it is still one segment the laws write č / ǰ (Persian چ).
                .replace("tʃ", "č").replace("dʒ", "ǰ"))
    kept: list[str] = []
    for ch in text:
        if ch == "\u0329":            # syllabic mark: /n̩/ is a nucleus
            if kept:
                kept.insert(len(kept) - 1, "\u0259")
            continue
        if unicodedata.category(ch) == "Mn" or ch in ".|\u203f":
            continue
        kept.append(_IPA_FOLD.get(ch, ch))
    return "".join(kept)


def _skeleton(form: str) -> tuple[list[str], int]:
    """Consonant sequence, and the number of vowel nuclei.

    Adjacent identical vowels are one nucleus (``bɔɔk`` and ``bʊk`` both have
    one), so a long vowel written twice in the phonemic layer is not counted as
    two syllables.
    """
    toks = [t for t in tokenize(form) if t not in {"ˈ", "ˌ"}]
    cons: list[str] = []
    for tok in toks:
        if is_vowel(tok) or tok in {"ː", "ˑ"}:
            continue
        # A dictionary may write one consonant where the phonemic layer has two
        # (German /ˈbɪtn̩/ for bitten).  Gemination is not what this guard tests.
        if cons and cons[-1] == tok:
            continue
        cons.append(tok)
    nuclei = 0
    last = None
    for tok in toks:
        if not is_vowel(tok):
            last = None
            continue
        if tok != last:
            nuclei += 1
        last = tok
    return cons, nuclei


@lru_cache(maxsize=None)
def reading_folds(lang: str | None) -> tuple[tuple[str, str], ...]:
    """The notation folds the reading guard applies for ``lang``.

    A language may write one segment with more than one letter, and its
    dictionary may write that segment a third way.  Greek writes the long
    close vowels /eː oː/ with the digraphs ει and ου, its ζ with the cluster
    /zd/, and the nasal before a velar with ŋ while the letter the laws
    produce is one n: a guard that compared the letters would reject a
    spelling whose letters are right (measured 2026-11-09: 32 of the 263 Greek
    words the writing layer spells).  The table is declared in the language's
    spelling file under a top-level ``guard:`` key, is applied to **both**
    sides of the comparison, and never rewrites a rule's output.
    """
    if not lang:
        return ()
    path = SPELLING_DIR / f"{lang}.yaml"
    if not path.exists():
        return ()
    raw = data._load_yaml(path)
    table = (raw.get("guard") or {}).get("equivalences") or {}
    pairs = [(str(k), str(v)) for k, v in table.items() if str(k)]
    return tuple(sorted(pairs, key=lambda kv: len(kv[0]), reverse=True))


def _apply_folds(text: str, folds: tuple[tuple[str, str], ...]) -> str:
    if not folds:
        return text
    out: list[str] = []
    i = 0
    while i < len(text):
        for key, value in folds:
            if text.startswith(key, i):
                out.append(value)
                i += len(key)
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _guard_table(lang: str | None) -> dict:
    if not lang:
        return {}
    path = SPELLING_DIR / f"{lang}.yaml"
    if not path.exists():
        return {}
    return data._load_yaml(path).get("guard") or {}


@lru_cache(maxsize=None)
def reading_of(lang: str | None) -> str:
    """The reader a language declares for records that carry no IPA.

    A corpus may record a word only in its own writing: 313 of the 352 Avestan
    entries have no IPA, so the orthographic layer's guard had nothing to check
    a phonemic form against and confirmed none of them.  A writing that is an
    *alphabet* with a known value for every letter is its own reading, so the
    language may declare one under ``guard: {reading: <name>}`` and the guard
    then compares against the word as its letters spell it (2026-11-09).
    """
    return str(_guard_table(lang).get("reading") or "")


#: The readers a spelling file may declare.  Each is a function from a written
#: word to the phonemes its letters carry, and each is tested against the
#: letter table it inverts, so a declaration cannot drift from the writer.
READERS = {"avestan": writing.avestan_reading}


def record_reading(word: str, ipa: str = "", lang: str | None = None) -> str:
    """The pronunciation the record itself carries, for the guard to compare.

    The dictionary's IPA when the entry has one; otherwise the reading its own
    letters give, when the language declares a reader.  Nothing is invented: a
    language that declares none, or a word with a letter the reader does not
    own, gets an empty reading and so cannot be confirmed.
    """
    if ipa and re.sub(r"[/\[\]() ]", "", ipa):
        return ipa
    name = reading_of(lang)
    reader = READERS.get(name)
    if reader is None:
        return ""
    return reader(word or "") if _readable_by(name, word) else ""


def _readable_by(name: str, word: str) -> bool:
    if name == "avestan":
        return writing.avestan_readable_word(word or "")
    return True


def confirms(form: str, word: str, ipa: str = "", lang: str | None = None) -> bool:
    """Whether the record's own pronunciation confirms this phonemic form.

    The one call every layer makes, so the word page and the counter can never
    read the same word two ways (2026-11-09).
    """
    return plausible(form, record_reading(word, ipa, lang), lang)


def plausible(form: str, ipa: str, lang: str | None = None) -> bool:
    """Is the phonemic form a plausible reading of the recorded pronunciation?

    Spelling is a mapping from *phonemes* to letters, so it can only be trusted
    when the phonemes are right.  Without this guard two wrong vowels can
    concatenate into the right letters (``æʌnt`` → "aunt", ``liqʌid`` →
    "liquid") and be reported as a success; that is a coincidence of the letter
    table, not evidence about the language.  A spelling match is therefore only
    counted when the derived form has the same consonant skeleton as the
    dictionary's own IPA and a vowel count equal to it — a deliberately loose test on quality but a strict one on
    shape, because the last law stage is pre-orthographic and its vowels are
    expected to be approximate, while its consonants and syllables are not.

    The comparison is made in *segments*, not in letters: ``_readable`` folds
    the IPA's transcription variants (``ɡ``/``g``, a rhotic written ``r ɾ ɹ ʁ``,
    a glottal stop, syllabic and non-syllabic marks, the tie bar) and the
    skeleton ignores gemination, so a dictionary's notation cannot decide the
    count.  Folding a letter never adds or removes a consonant.  A language
    whose *orthography* writes one segment with two letters declares the
    equivalences in its spelling file (``guard:``, see ``reading_folds``), and
    they are applied to both sides before the comparison.
    """
    ipa = re.sub(r"[/\[\]() ]", "", ipa or "")
    if not ipa or not form:
        return False
    folds = reading_folds(lang)
    form_cons, form_vowels = _skeleton(_apply_folds(_readable(form), folds))
    ipa_cons, ipa_vowels = _skeleton(_apply_folds(_readable(ipa), folds))
    return form_cons == ipa_cons and form_vowels == ipa_vowels


def tokens(form: str) -> list[str]:
    return tokenize(form)
