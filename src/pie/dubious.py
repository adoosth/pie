"""Words whose recorded ancestry needs a human before it may count.

Wiktionary is a record of what editors wrote, not a verdict.  Its etymology
templates sometimes name an etymon the literature never proposed, sometimes
name one PIE form while the entry's own cognate set names another, sometimes
assert a chain the prose hedges, and sometimes give a word a sense the claimed
root does not have.  Persian باران "rain" is the worked example: the entry
derives it from PIE ``*weh₁r-`` "water" while its cognate set is
``ine-pro:wódr̥``, the family's ordinary word for water.

This module finds those rows and parks them.  It never repairs one: a word in
the backlog is *not* counted as explained until somebody re-reads the source
and decides, which is the rule in ``docs/PROGRAMME.md``.  Nothing here changes
a derivation or a published number — ``tools/coverage.py`` is untouched.

Four kinds are computed, each only from data the corpus already holds:

``etymon_missing``
    the PIE ancestor named in ``anc`` is not a headword in the PIE glossary
    (``data/lexicon/ine-pro.jsonl.gz``); an entry with no PIE row is checked
    against the oldest ancestor a modelled stage of its own chain names.  The
    lookup is the engine's own: ``normalise_etymon`` against the lemma index
    built the way ``pie.service`` builds it (lower-cased headwords), so a
    capital ``H`` in ``*priHós`` is not mistaken for a missing word.

``cognate_conflict``
    the entry carries ``cog`` (a set id such as ``ine-pro:wódr̥``) and the PIE
    form of that set is not the PIE ancestor in ``anc``.

``hedged_ancestry``
    the entry has ancestry rows and its ``etym`` prose hedges the origin —
    "uncertain", "unknown", "possibly", "perhaps", "probably", "disputed",
    "doubtful".  The data asserts a chain the source itself is unsure of.

``sense_mismatch``
    the gloss of the entry shares no content word with the gloss of the
    claimed PIE etymon and none with the gloss of its cognate set.  Only
    compared where a gloss exists on both sides, so an entry with no gloss and
    a root with no gloss are never flagged.  Semantic development is ordinary
    and broad, so this kind is deliberately the noisiest: it is a reading list,
    not a finding.

Two limitations are stated rather than hidden.  A missing PIE headword can be
a gap in our own glossary instead of a bad etymon — the PIE lexicon holds a
subset of the reconstructions the corpus cites — so ``etymon_missing`` mixes
both and the reviewer tells them apart.  And an entry whose ancestors are all
in unmodelled languages (Arabic, Syriac, an unattested register) cannot be
checked at all: it produces no finding, because there is nothing to compare.

``suspects()`` returns every finding; ``payload()`` caps each kind and records
how many rows it dropped, ``render()`` writes the human page, and
``is_stale()`` is the comparison behind ``tools/backlog.py --check``.
"""
from __future__ import annotations

import re
import time
from collections import defaultdict
from functools import lru_cache

from . import data
from .service import (_ancestry_triples, _comparison_key, _pie_form,
                      cognate_index, normalise_etymon)

KINDS: dict[str, str] = {
    "etymon_missing": (
        "the PIE (or oldest modelled) ancestor named in anc is not a headword "
        "in that stage's glossary"
    ),
    "cognate_conflict": (
        "the entry's cognate set names a different PIE form from the PIE "
        "ancestor in anc"
    ),
    "hedged_ancestry": (
        "ancestry is asserted although the source's own etymology hedges it "
        "(uncertain, unknown, possibly, perhaps, probably, disputed, doubtful)"
    ),
    "sense_mismatch": (
        "the entry's gloss shares no content word with the claimed etymon's "
        "gloss or with its cognate set's gloss"
    ),
}

KIND_ORDER: tuple[str, ...] = tuple(KINDS)

#: A reading list, not a corpus dump: the contradictions come first and in
#: greater number, the noisy reading-aid last.  The numbers are a size budget,
#: not a ranking of importance — the file stays around a megabyte — and every
#: omitted finding remains available from ``suspects()`` and is counted in the
#: file's header.
CAPS: dict[str, int] = {
    "cognate_conflict": 1500,
    "etymon_missing": 1200,
    "hedged_ancestry": 800,
    "sense_mismatch": 400,
}

HEDGES = re.compile(
    r"\b(uncertain|unknown|possibly|perhaps|probably|disputed|doubtful)\b",
    re.IGNORECASE,
)

STOPWORDS = frozenset("""
a an the of to in and or with for from by on at as is are was were be been
being this that these those one ones something someone somebody person people
who whom whose which what when where why how not no nor but if then than also
used use using usually especially chiefly now often sometimes rare archaic
informal literally figuratively form forms word words term terms name names
sense senses meaning means other another same such only just very more most
including include includes e g i cf see also one's
""".split())

_TOKEN = re.compile(r"[^\W\d_]+", re.UNICODE)


def attested_languages() -> list[str]:
    """Languages the registry calls attested and that have a glossary."""
    registry = data.languages()
    return [
        lang for lang, _size in data.available_lexicons()
        if registry.get(lang, {}).get("kind") == "attested"
    ]


@lru_cache(maxsize=None)
def _glossary(stage: str) -> dict[str, dict]:
    """A stage's glossary keyed the way the engine keys it: notation-free, lower-case.

    ``pie.service._lemma_index`` lower-cases the headword before normalising
    it, so its keys are ``prihós`` and not ``priHós``.  This index is built the
    same way so that a form written with a laryngeal's capital ``H`` is looked
    up as the engine looks it up, and not reported missing for its case.
    """
    out: dict[str, dict] = {}
    for word, rows in data.lexicon_index(stage).items():
        out.setdefault(normalise_etymon(word).lower(), rows[0])
    return out


def _has_headword(stage: str, form: str) -> bool:
    key = normalise_etymon(form).lower()
    return bool(key) and key in _glossary(stage)


def _tokens(glosses) -> set[str]:
    """The content words of a gloss list, lower-cased and stripped of function words."""
    out: set[str] = set()
    for gloss in glosses if isinstance(glosses, (list, tuple)) else [glosses]:
        for word in _TOKEN.findall(str(gloss or "").lower()):
            if len(word) >= 3 and word not in STOPWORDS:
                out.add(word)
    return out


def _quote(text: str, start: int, end: int, width: int = 60) -> str:
    """A one-line excerpt of ``text`` around ``start``, for a reviewer to re-read."""
    piece = " ".join(text[max(0, start - width):end + width].split())
    return f"…{piece}…" if piece != " ".join(text.split()) else piece


def _raw_form(triples, form: str) -> str:
    """The form as the record writes it, when the normalised one came from it.

    The engine works on ``weh₁r``; the entry writes ``*weh₁r-``.  A reviewer
    reads the backlog next to the source, so the row names the source's string
    and falls back to the normalised form when no ancestry row matches it.
    """
    key = normalise_etymon(form).lower()
    for _lang, raw, _rel in triples:
        if normalise_etymon(raw or "").lower() == key:
            return raw
    return form


def _oldest_modelled(triples, chain: list[str]):
    """The root-most ancestor the entry names at a modelled stage of its own chain."""
    mapped = []
    for order, (lang, form, _rel) in enumerate(triples):
        stage = data.stage_of(lang)
        if not form or stage not in chain or not _glossary(stage):
            continue
        mapped.append((chain.index(stage), order, stage, form))
    if not mapped:
        return None
    mapped.sort()
    _index, _order, stage, form = mapped[0]
    return stage, form


def flags(entry: dict, chain: list[str] | None = None) -> list[dict]:
    """Every backlog finding one glossary entry produces.

    The entry is read, never written: the caller gets ``{kind, etymon, detail,
    evidence}`` rows without ``lang`` or ``word``, which :func:`suspects` adds
    from the record itself.
    """
    lang = entry.get("lang") or ""
    chain = list(chain) if chain is not None else data.derivation_chain(lang)
    triples = _ancestry_triples(entry)
    if not triples:
        return []
    pie = _pie_form(entry)
    claimed = _raw_form(triples, pie) if pie else ""
    out: list[dict] = []

    pie_rows = [(form, rel) for stage_lang, form, rel in triples
                if data.stage_of(stage_lang) == "ine-pro" and form]
    if pie_rows:
        named = claimed or pie_rows[0][0]
        rel = next((rel for form, rel in pie_rows if form == named),
                   pie_rows[0][1])
        if not _has_headword("ine-pro", named):
            out.append({
                "kind": "etymon_missing",
                "etymon": named,
                "detail": f"ancestry names {named} at ine-pro; the PIE glossary "
                          f"has no headword {normalise_etymon(named).lower()}",
                "evidence": f"anc row: ine-pro {named} ({rel or 'inherit'})",
            })
    else:
        oldest = _oldest_modelled(triples, chain)
        if oldest and not _has_headword(*oldest):
            stage, form = oldest
            out.append({
                "kind": "etymon_missing",
                "etymon": form,
                "detail": f"ancestry names {form} at {stage}; the {stage} glossary "
                          f"has no headword {normalise_etymon(form).lower()}",
                "evidence": f"anc row: {stage} {form}; no PIE ancestor is named",
            })

    cog = entry.get("cog") or ""
    record = cognate_index().get(cog) if cog else None
    if record and pie and record.get("pie"):
        if _comparison_key(record["pie"]) != _comparison_key(pie):
            gloss = f" ({record['gloss']})" if record.get("gloss") else ""
            out.append({
                "kind": "cognate_conflict",
                "etymon": claimed,
                "detail": f"cognate set {cog} has PIE {record['pie']}; "
                          f"ancestry names {claimed}",
                "evidence": f"cog = {cog} (PIE {record['pie']}{gloss}) vs anc {claimed}",
            })

    etym = entry.get("etym") or ""
    match = HEDGES.search(etym)
    if match and triples:
        out.append({
            "kind": "hedged_ancestry",
            "etymon": claimed,
            "detail": f"the etymology hedges the origin with “{match.group(1).lower()}”",
            "evidence": 'etym: "' + _quote(etym, match.start(), match.end()) + '"',
        })

    if pie:
        entry_tokens = _tokens(entry.get("gloss") or [])
        if entry_tokens:
            etymon_row = _glossary("ine-pro").get(normalise_etymon(pie).lower())
            etymon_tokens = _tokens((etymon_row or {}).get("gloss") or [])
            set_tokens = _tokens(record.get("gloss") or "") if record else set()
            sides = [(name, toks) for name, toks in
                     (("etymon", etymon_tokens), ("cognate set", set_tokens)) if toks]
            if sides and all(not (entry_tokens & toks) for _name, toks in sides):
                shown = "; ".join(
                    f"{name} gloss " + ", ".join(sorted(toks)[:4]) for name, toks in sides)
                out.append({
                    "kind": "sense_mismatch",
                    "etymon": claimed,
                    "detail": "the entry's gloss and the claimed origin's gloss "
                              "share no content word",
                    "evidence": "gloss " + ", ".join(sorted(entry_tokens)[:4])
                                + " vs " + shown,
                })
    return out


def _row(lang: str, word: str, finding: dict) -> dict:
    return {
        "lang": lang,
        "word": word,
        "etymon": finding["etymon"],
        "kind": finding["kind"],
        "detail": finding["detail"],
        "evidence": finding["evidence"],
    }


def suspects(lang: str | None = None, include_reconstructed: bool = False) -> list[dict]:
    """Every glossary entry whose recorded ancestry needs a second reader.

    ``lang`` restricts the pass to one language code.  ``include_reconstructed``
    adds the proto stages (``*-pro``) whose lexicons carry ancestry too; the
    default is attested languages only, because an unattested reconstruction
    has a different question to answer — which forms the literature records —
    and that is left for later, as ``docs/PROGRAMME.md`` says.

    A word with several parts of speech that produce the same finding is one
    row: the backlog is a list of words to re-read, not of entries.
    """
    registry = data.languages()
    langs = [lang] if lang else attested_languages()
    if include_reconstructed and not lang:
        langs += [
            code for code, _size in data.available_lexicons()
            if registry.get(code, {}).get("kind") == "proto" and code != "ine-pro"
            and code not in langs
        ]
    rows: dict[tuple[str, str, str, str], dict] = {}
    for code in langs:
        chain = data.derivation_chain(code)
        for entry in data.lexicon(code):
            word = str(entry.get("word") or "")
            if not word:
                continue
            for finding in flags(entry, chain):
                key = (finding["kind"], code, word, finding["etymon"])
                rows.setdefault(key, _row(code, word, finding))
    order = {kind: index for index, kind in enumerate(KIND_ORDER)}
    return sorted(rows.values(),
                  key=lambda r: (order.get(r["kind"], len(order)), r["lang"],
                                 r["word"], r["etymon"]))


def _fair_sample(rows: list[dict], cap: int) -> list[dict]:
    """Keep ``cap`` rows, taking one language at a time so no language fills it.

    Rows arrive sorted by kind, language and word, so taking the head would
    keep whatever language sorts first and hide every other one.  The kept set
    is still written back in that sort order; only the choice of *which* rows
    survive is spread over the languages.
    """
    if len(rows) <= cap:
        return rows
    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        buckets[row["lang"]].append(row)
    langs = sorted(buckets)
    cursor = {code: 0 for code in langs}
    kept: list[dict] = []
    while len(kept) < cap:
        progressed = False
        for code in langs:
            if len(kept) >= cap:
                break
            index = cursor[code]
            if index < len(buckets[code]):
                kept.append(buckets[code][index])
                cursor[code] = index + 1
                progressed = True
        if not progressed:
            break
    return kept


def payload(generated: str | None = None, rows: list[dict] | None = None) -> dict:
    """The backlog document: the header, the kinds, the caps and the rows.

    ``truncated`` records, per kind, how many rows the cap dropped — the count
    a reader needs to know that the file is a reading list and not the whole
    finding.  ``counts`` holds the totals of the *uncapped* pass, by kind and
    by language, so the page reports how much of the corpus each kind really
    touches instead of how much survived the cap.  ``generated`` is the only
    field :func:`is_stale` ignores.
    """
    rows = suspects() if rows is None else rows
    found = time.strftime("%Y-%m-%d")
    words: list[dict] = []
    truncated: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    by_language: dict[str, dict[str, int]] = {}
    for row in rows:
        by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1
        bucket = by_language.setdefault(row["lang"], {})
        bucket[row["kind"]] = bucket.get(row["kind"], 0) + 1
    for kind in KIND_ORDER:
        of_kind = [row for row in rows if row["kind"] == kind]
        cap = CAPS.get(kind)
        if cap and len(of_kind) > cap:
            truncated[kind] = len(of_kind) - cap
            of_kind = _fair_sample(of_kind, cap)
        for row in of_kind:
            words.append({**row, "status": "open", "found": found})
    return {
        "generated": generated or time.strftime("%Y-%m-%d %H:%M"),
        "kinds": dict(KINDS),
        "counts": {"by_kind": by_kind, "by_language": by_language},
        "truncated": truncated,
        "words": words,
    }


def is_stale(on_disk: dict, fresh: dict) -> str | None:
    """Why the stored backlog differs from a fresh run, or ``None`` when it agrees.

    ``generated`` is a timestamp and is ignored: a file that is regenerated a
    minute later is not stale.  ``kinds``, ``counts``, ``truncated`` and
    ``words`` are the comparison — a changed definition, a changed cap or a
    changed row all mean the file must be written again.
    """
    for field in ("kinds", "counts", "truncated", "words"):
        if (on_disk or {}).get(field) != (fresh or {}).get(field):
            return f"{field} differs from a fresh run"
    return None


def _cell(text: str, width: int) -> str:
    text = " ".join(str(text or "").split()).replace("|", "/")
    return text if len(text) <= width else text[: width - 1] + "…"


def render(report: dict) -> str:
    """The human page for ``docs/REVIEW_BACKLOG.md``."""
    words = report.get("words") or []
    lines: list[str] = []
    add = lines.append
    add("# Review backlog")
    add("")
    add("Words whose recorded ancestry has to be re-read before it may be counted.")
    add("Wiktionary records what an editor wrote; a word parked here is **not**")
    add("counted as explained, and none of its ancestry is used as evidence, until")
    add("someone opens the cited source and decides. The list is generated by")
    add("`python3 tools/backlog.py --write` from the corpus itself — no entry here is")
    add("typed by hand, and an entry that disagrees with its source leaves the file")
    add("only by a change in the data.")
    add("")
    add(f"Generated {report.get('generated', '')}.")
    add("")
    languages = len((report.get("counts") or {}).get("by_language") or {}) or \
        len({row["lang"] for row in words})
    found = sum(((report.get("counts") or {}).get("by_kind") or {}).values()) or len(words)
    add(f"One pass over **{languages}** attested glossaries found **{found:,}** suspect rows;")
    add(f"this file keeps **{len(words):,}** of them and counts the rest as omitted.")
    add("")
    add("## Kinds")
    add("")
    add("| kind | means |")
    add("|---|---|")
    for kind, definition in (report.get("kinds") or KINDS).items():
        add(f"| `{kind}` | {definition} |")
    add("")
    example = [row for row in words
               if row["lang"] == "fa" and row["word"] == "باران"]
    if example:
        add("## The worked example")
        add("")
        add("Persian باران *rain* is the word that started this list: the entry names")
        add("PIE `*weh₁r-` as its origin while its own cognate set is the family's")
        add("ordinary word for water. What follows is exactly as the data wrote it,")
        add("and every row stays `open` until somebody re-reads the source.")
        add("")
        for row in example:
            add(f"- `{row['kind']}` — {row['detail']}. Evidence: {row['evidence']}.")
        add("")
    add("## Counts")
    add("")
    truncated = report.get("truncated") or {}
    counts = report.get("counts") or {}
    by_kind = dict(counts.get("by_kind") or {})
    by_language = {lang: dict(kinds) for lang, kinds in
                   (counts.get("by_language") or {}).items()}
    if not by_kind:
        for row in words:
            by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1
            bucket = by_language.setdefault(row["lang"], {})
            bucket[row["kind"]] = bucket.get(row["kind"], 0) + 1
    add("| kind | found in the corpus | in this file | omitted by the cap |")
    add("|---|---|---|---|")
    for kind in (report.get("kinds") or KINDS):
        kept = sum(1 for row in words if row["kind"] == kind)
        add(f"| `{kind}` | {by_kind.get(kind, 0):,} | {kept:,} "
            f"| {truncated.get(kind, 0):,} |")
    add(f"| **total** | **{sum(by_kind.values()):,}** | **{len(words):,}** "
        f"| **{sum(truncated.values()):,}** |")
    add("")
    if truncated:
        add("A capped kind keeps a fair share of every language; the count in the")
        add("last column is how many findings the file does not list. The full")
        add("finding is always `pie.dubious.suspects()`, which returns every row.")
        add("")
    add("## Per language")
    add("")
    header = "| language | " + " | ".join(f"`{k}`" for k in (report.get("kinds") or KINDS)) + " | total |"
    add(header)
    add("|---" * (len(report.get("kinds") or KINDS) + 2) + "|")
    for lang, kinds in sorted(by_language.items(),
                              key=lambda kv: (-sum(kv[1].values()), kv[0])):
        cells = " | ".join(str(kinds.get(kind, 0)) for kind in (report.get("kinds") or KINDS))
        add(f"| `{lang}` | {cells} | {sum(kinds.values())} |")
    add("")
    if words:
        add("## First ten of each kind")
        add("")
        add("| lang | word | etymon | kind | detail | evidence |")
        add("|---|---|---|---|---|---|")
        shown: list[dict] = []
        for kind in (report.get("kinds") or KINDS):
            shown.extend([row for row in words if row["kind"] == kind][:10])
        for row in shown:
            add(f"| `{row['lang']}` | {_cell(row['word'], 24)} | {_cell(row['etymon'], 20)} "
                f"| `{row['kind']}` | {_cell(row['detail'], 60)} | {_cell(row['evidence'], 60)} |")
        add("")
    add("## What the kinds cannot say")
    add("")
    add("`etymon_missing` applies when the named ancestor is not a headword in our")
    add("glossary, and that can be a gap in the glossary rather than a bad etymon:")
    add("the PIE lexicon holds a subset of the reconstructions the corpus cites, and")
    add("a proto-stage lexicon is smaller still. The reviewer's job is exactly that")
    add("distinction — open the source, and either the etymon is recorded (the")
    add("glossary needs the word) or it is not (the entry is wrong).")
    add("")
    add("`sense_mismatch` compares glosses only where both sides have one, and")
    add("semantic development is broad, so it over-reports metaphor and metonymy.")
    add("It is a reading list, not a verdict, and no count of it belongs in a")
    add("published coverage number.")
    add("")
    return "\n".join(lines)
