"""Keep an etymology tree's relation labels apart from the words they join.

Wiktionary renders an etymology as a column of (language, term) blocks with a
small label sitting on the connector between two blocks: ``der.`` ("derived
terms"), ``bor.`` ("borrowed"), ``lbor.`` ("learned borrowing"), ``inh.`` and so
on.  The labels are ``abbrev`` entries of ``Module:etymon/data`` and none of
them is a suffix: ``der.`` says that the next block is *derived from* this one.

Wiktextract flattens that column into a single string, and the label's span
touches the term's span, so the dump reads ``… *peh₂-der. Proto-Germanic …``:
root and relation welded into one token.  Nothing in that string says where the
word ends, so a reader — and a search — sees a Proto-Indo-European suffix
``-der`` that never existed.

``split_labels`` brackets every label, and only inside the tree block.  A word
that merely ends in ``-der.`` in the prose that follows the tree (``related to
yonder.``, ``sono- + -graph.``) is never touched.
"""

from __future__ import annotations

import re

MARK = "Etymology tree"

#: ``abbrev`` → the glossary phrase it stands for, as the tree's own tooltip
#: spells it in ``Module:etymon/data`` (``export.keywords``).
LABELS: dict[str, str] = {
    "der.": "derived terms",
    "bor.": "borrowed",
    "lbor.": "learned borrowing",
    "slbor.": "semi-learned borrowing",
    "obor.": "obsolete borrowing",
    "ubor.": "unadapted borrowing",
    "calq.": "calque",
    "pcalq.": "partial calque",
    "psm.": "phono-semantic matching",
    "influ.": "influence",
    "redup.": "reduplication",
    "vṛd.": "vṛddhi derivative",
    "denom.": "denominal",
    "deverb.": "deverbal",
    "aph.": "apheretic",
    "bf.": "back-formation",
    "clip.": "clipping",
    "ellip.": "ellipsis",
    "nom.": "nominalization",
    "translit.": "transliteration",
    "abbr.": "abbreviation",
    "syl. abbr.": "syllabic abbreviation",
    "univ.": "univerbation",
    "init.": "initialism",
    "meta.": "metathesis",
    "sl.": "semantic loan",
}

#: The two labels the module spells without a full stop.
DOTLESS = {"acronym": "acronym", "blend": "blend"}

_ALL = sorted(list(LABELS) + list(DOTLESS), key=len, reverse=True)
_LABEL_RE = re.compile(
    r"(?<=\S)(" + "|".join(re.escape(a) for a in _ALL) + r")(\?)?(?=[\s,;)\]”\"]|$)"
)
_TOKEN_RE = re.compile(r"\S+")



def label_at(text: str, at: int) -> str:
    """The label that starts exactly at ``at``, or ``""``."""
    for name in _ALL:
        if text.startswith(name, at):
            return name
    return ""


def split_token(token: str) -> tuple[str, str]:
    """``'*peh₂-der.'`` → ``('*peh₂-', 'der.')``; a bare word comes back whole."""
    for name in _ALL:
        for suffix in ("", "?"):
            tail = name + suffix
            if token.endswith(tail) and len(token) > len(tail):
                return token[: -len(tail)], tail
    return token, ""


def _token(text: str, pos: int) -> re.Match | None:
    while pos < len(text) and text[pos] == " ":
        pos += 1
    if pos >= len(text):
        return None
    return _TOKEN_RE.match(text, pos)


def _capitalised(token: str) -> bool:
    return bool(token) and token[0].isupper()


def _name_in(text: str, pos: int, names) -> bool:
    head = text[pos:]
    return any(head.startswith(n) and (len(head) == len(n) or head[len(n)] == " ")
               for n in names)


def _block(text: str, pos: int, first: bool = False) -> tuple[int, int]:
    """Parse one ``<language name> <term>`` block.

    Returns ``(end of the term, offset of the next block)``, or ``(-1, -1)``
    when no block starts here.  ``first`` accepts a tree whose opening node is
    not capitalised (``the BMAC substrate``).
    """
    while True:  # a ▲ root marker sits between two branches
        run = _token(text, pos)
        if not run or run.group() != "▲":
            break
        pos = run.end()
    if not run or not (_capitalised(run.group()) or first):
        return -1, -1
    pos = run.end()
    while True:  # a language name may be several words long
        nxt = _token(text, pos)
        if nxt and _capitalised(nxt.group()):
            pos = nxt.end()
            continue
        break
    if not nxt:
        return pos, pos
    end = nxt.end()  # the term
    gloss = _token(text, end)
    if gloss and gloss.group().startswith("("):
        for _ in range(6):
            end = gloss.end()
            if gloss.group().endswith(")"):
                break
            gloss = _token(text, end)
            if not gloss or _capitalised(gloss.group()):
                break
    return end, end


def _blocks_ahead(text: str, pos: int, names) -> bool:
    """Two consecutive known-language blocks start at ``pos``."""
    for index in range(2):
        start = pos
        run = _token(text, start)
        if not run or not _name_in(text, run.start(), names):
            return False
        end, nxt = _block(text, start)
        if end < 0:
            return False
        pos = nxt
    return True


def tree_end(text: str, start: int, names=()) -> int:
    """Offset just past the last block of a ``<language name> <term>`` tree.

    A block opens with the language's name — always capitalised — and closes
    with one term, plus a gloss in parentheses when the entry gives a reading.
    The next block either follows directly (``English web English wiki``) or
    after a further term of the same block (``*welk- /*wilk-``, ``via strāta``).
    The second case is only accepted when two known-language blocks resume
    there, which is what separates a tree from the sentence after it:
    ``from English border.`` has one "block" and no continuation, ``… /*wilk-der.
    Proto-Slavic … Old Church Slavonic …`` has two.
    """
    pos = start
    end = start
    first = True
    while True:
        stop, nxt = _block(text, pos, first)
        if stop < 0:
            break
        first = False
        end = pos = stop
        skip = pos
        for _ in range(6):
            following = _token(text, skip)
            if not following or _capitalised(following.group()):
                break
            skip = following.end()
            probe = skip
            while probe < len(text) and text[probe] == " ":
                probe += 1
            if names and _blocks_ahead(text, probe, names):
                end = pos = probe
                break
    return end


def split_labels(text: str, names=()) -> str:
    """Bracket the relation labels inside ``text``'s etymology tree."""
    if not text or MARK not in text:
        return text
    at = text.index(MARK) + len(MARK)
    stop = tree_end(text, at, names)
    if stop <= at:
        return text
    tree = text[at:stop]

    def repl(m: re.Match) -> str:
        return f" [{m.group(1)}{m.group(2) or ''}]"

    return text[:at] + _LABEL_RE.sub(repl, tree) + text[stop:]


def gloss_of(label: str) -> str:
    """The glossary phrase behind a label, for a tooltip."""
    label = label.rstrip("?")
    bare = label[:-1] if label.endswith(".") else label
    return LABELS.get(label) or DOTLESS.get(bare, "")


# --- the {{etymon}} chain, as Wiktextract writes it in one argument ---------
#
# The template packs a whole etymology tree into ``3=``: the form, then the
# relation that produced it from the next form, nested as markup —
#
#   ``pal:𐭓𐭐𐭃<ety:inh<peo:𐎱𐎡𐎫𐎠<ety:inh<ira-pro:*pHtā́>>>``
#   ``ine-pro:<alt:*moldʰéyeti><ety:af<*meldʰ-><*-éyeti>>``
#
# A regular expression cannot read that (an inner ``>`` closes an inner tag),
# and stripping the tags welded markup onto the word: Persian پدر carried an
# ancestor form "𐭓𐭐𐭃 >" and the Middle Persian rung stopped matching its own
# record (2026-11-09). ``parse_chain`` reads the structure.

_HEAD_RE = re.compile(r"[^<>]*")
_TAG_NAME_RE = re.compile(r"[a-z]+")

#: The relations that build a word from pieces rather than from an ancestor.
PIECE_RELATIONS = {"af", "suf", "pre", "prefix", "suffix", "com", "compound",
                   "infix", "affix"}


def _one(text: str, pos: int) -> tuple[dict, int]:
    """Parse one node — a head and its tags — returning it and the next offset."""
    head = _HEAD_RE.match(text, pos).group(0)
    pos += len(head)
    lang, sep, term = head.partition(":")
    node = {"lang": lang.strip() if sep else "",
            "term": (term if sep else head).strip(), "tags": []}
    while pos < len(text) and text[pos] == "<":
        colon = text.find(":", pos)
        if colon < 0:
            break
        name = text[pos + 1:colon]
        if not _TAG_NAME_RE.fullmatch(name):
            break
        pos = colon + 1
        if name == "ety":
            start = text.find("<", pos)
            key = (text[pos:start] if start >= 0 else text[pos:]).strip()
            pos = start if start >= 0 else len(text)
            children: list[dict] = []
            while pos < len(text) and text[pos] == "<":
                child, pos = _one(text, pos + 1)
                children.append(child)
                if pos < len(text) and text[pos] == ">":
                    pos += 1
            node["tags"].append({"name": "ety", "key": key, "children": children})
            continue
        depth, start = 0, pos
        while pos < len(text):
            if text[pos] == "<":
                depth += 1
            elif text[pos] == ">":
                if depth == 0:
                    break
                depth -= 1
            pos += 1
        body = text[start:pos].strip()
        pos += 1
        if name == "alt":
            # ``<alt:*moldʰéyeti>``: how the form is written when the term
            # itself is empty.
            node["term"] = node["term"] or body
        else:
            node["tags"].append({"name": name, "body": body})
    return node, pos


def parse_terms(value: str, own: str = "") -> list[dict]:
    """Every term in one ``{{etymon}}`` argument, outermost first, with its language."""
    out: list[dict] = []

    def walk(node: dict, lang: str) -> None:
        if node["term"]:
            out.append({"lang": node["lang"] or lang, "term": node["term"]})
        here = node["lang"] or lang
        for tag in node["tags"]:
            if tag["name"] == "ety":
                for kid in tag["children"]:
                    walk(kid, here)

    node, _ = _one(str(value or ""), 0)
    walk(node, node["lang"] or own)
    return out


def parse_chain(value: str, own: str = "", keyword: str = "") -> list[dict]:
    """Every hop one ``{{etymon}}`` argument states, the word first.

    Each row is ``{"lang", "term", "rel", "pieces"}``.  ``rel`` names how the
    row's term relates to the term above it — the ``keyword`` the caller passed
    (``inh``, ``der``, ``bor`` …) for the argument's own term, and the nested
    tag's own keyword below it.  ``pieces`` holds the sub-terms of a
    construction, each with its own ``rel``.  A term written without a language
    is in ``own``, the language the template was written for.

    A plain ``fr:livre`` is one hop, not nothing: the term an argument names is
    the ancestor it names, and only its *children* are further hops (2026-11-09:
    every ``{{etymon|en|:bor|fr:livre}}`` had been dropped from the corpus).
    """
    out: list[dict] = []

    def walk(node: dict, lang: str, rel: str, emit_self: bool) -> None:
        here = node["lang"] or lang
        # A term with no language of its own is a piece of the entry's word
        # ({{etymon|en|:af|non-|-sense}}), never an ancestor. One *with* a
        # language is where the word comes from even when that is the entry's
        # own stage: Proto-Indo-European *dl̥h₁gʰós is built on the
        # Proto-Indo-European stem *delh₁gʰ-, and the construction parser needs
        # that stated to recognise the base (2026-11-09).
        if emit_self and node["term"] and node["lang"]:
            out.append({"lang": here, "term": node["term"], "rel": rel,
                        "pieces": []})
        for tag in node["tags"]:
            if tag["name"] != "ety":
                continue
            kids = tag["children"]
            if tag["key"] in PIECE_RELATIONS:
                pieces = [{"lang": kid["lang"] or here, "term": kid["term"],
                           "rel": tag["key"]} for kid in kids if kid["term"]]
                if pieces:
                    out.append({"lang": here, "term": node["term"], "rel": "",
                                "pieces": pieces})
                for kid in kids:
                    walk(kid, here, tag["key"], False)
                continue
            for kid in kids:
                walk(kid, here, tag["key"], True)

    node, _ = _one(str(value or ""), 0)
    walk(node, node["lang"] or own, keyword, True)
    return out


_TAG = re.compile(r"<[^<>]*(?:<[^<>]*>[^<>]*)*>")


def visible_term(value: str) -> str:
    """The word a template argument names, without its markup.

    ``{{bor|en|la|<alt:tripod-><ng:stem of <i>tripūs, tripodis</i>>}}`` states
    the Latin form the English word was borrowed from, and the markup says it
    is that form's *stem*.  The visible word is what remains once the tags are
    gone — never a stray ``>`` welded to the end of it, which is what a plain
    ``re.sub("<[^>]*>")`` leaves behind (2026-11-09: English *tripod* carried
    the ancestor form ``tripūs, tripodis>``).

    ``<ng:…>`` is preferred when present: an ``<alt:…>`` beside it is a display
    variant (``tripod-``) and the plain text is a gloss.
    """
    text = str(value or "")
    found = re.search(r"<ng:((?:[^<>]|<i[^<>]*>|</i>)*)>", text)
    if found:
        text = found.group(1)
    else:
        alt = re.search(r"<alt:([^<>]*)>", text)
        if alt and not _TAG.sub("", text).replace(alt.group(1), "").strip():
            text = alt.group(1)
    text = _TAG.sub("", text)
    # A note may describe the form rather than name it: "<ng:stem of …>".
    text = re.sub(r"^(?:the\s+)?(?:stem|genitive|oblique|plural|singular|"
                  r"accusative|dative|ablative|participle|form)\s+of\s+", "", text.strip())
    return text.strip().strip("<>").strip()
