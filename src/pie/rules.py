"""Compiled sound laws: matching, application, and derivation traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from . import pattern as pat
from . import translit
from .phonology import detokenize, tokenize
from .transforms import TRANSFORMS

TIERS = ("established", "proposed", "custom", "formation", "orthographic")

#: The spelling layer is not a historical claim, so its rules carry their own
#: tier and are never mixed into the "established" count of a sound-law file.
#:
#: ``formation`` is a different kind of rule: it does not change a sound, it
#: *adds a cited morpheme* (the animal suffix *-ka- of Persian گربه).  A
#: formation is therefore registered **switched off** (``off_by_default``) and
#: only applies to the words whose own pathway turns it on, so it can never
#: quietly rewrite a word that does not use that suffix.


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


@dataclass
class Rule:
    id: str
    name: str
    order: int
    source: str
    change: str
    source_stage: str
    target_stage: str
    tier: str = "established"
    optional: bool = False
    weight: float = 1.0
    notes: str = ""
    references: list[str] = field(default_factory=list)
    examples: list[dict] = field(default_factory=list)
    match: str = ""
    left: str | None = None
    right: str | None = None
    replace: str = ""
    iterative: bool = False
    unstressed_left: bool = False
    #: A rule that must not apply unless the word it is run on asks for it.
    default_off: bool = False
    transform: str = ""
    params: dict = field(default_factory=dict)
    _match: list | None = field(default=None, repr=False)
    _left: list | None = field(default=None, repr=False)
    _right: list | None = field(default=None, repr=False)
    _replace: list[str] = field(default_factory=list, repr=False)

    def compile(self) -> "Rule":
        if self.transform:
            if self.transform not in TRANSFORMS:
                raise ValueError(f"rule {self.id}: unknown transform {self.transform}")
            self._match = []
            self._left = self._right = None
            self._replace = []
            return self
        self._match = pat.parse(self.match)
        self._left = pat.parse(self.left)
        self._right = pat.parse(self.right)
        self._replace = [t for t in tokenize(self.replace)]
        if self._match is None and not self.transform:
            raise ValueError(f"rule {self.id}: empty match pattern")
        if self.tier not in TIERS:
            self.tier = "established"
        return self

    def positions(self, tokens: list[str]) -> list[tuple[int, int]]:
        if self.transform:
            new, changed = TRANSFORMS[self.transform](tokens, self.params)
            return [(i, i + 1) for i in changed]
        hits: list[tuple[int, int]] = []
        i = 0
        while i < len(tokens):
            end = pat.match_at(self._match, tokens, i)  # type: ignore[arg-type]
            if end is None:
                i += 1
                continue
            if self.unstressed_left and not _left_is_unstressed(tokens, i):
                i += 1
                continue
            if pat.match_left(self._left, tokens, i) and pat.match_right(self._right, tokens, end):
                hits.append((i, end))
                i = max(end, i + 1)
            else:
                i += 1
        return hits

    def apply(self, tokens: list[str]) -> tuple[list[str], list[int]]:
        if self.transform:
            return TRANSFORMS[self.transform](tokens, self.params)
        out = list(tokens)
        changed: list[int] = []
        offset = 0
        for start, end in self.positions(tokens):
            at = start + offset
            out[at : at + (end - start)] = list(self._replace)
            offset += len(self._replace) - (end - start)
            changed.append(at)
        return out, changed

    def explain(self, form: str) -> dict | None:
        tokens = tokenize(form)
        if not self.positions(tokens):
            return None
        new, changed = self.apply(tokens)
        return {"before": detokenize(tokens), "after": detokenize(new), "positions": changed}


def _left_is_unstressed(tokens: list[str], idx: int) -> bool:
    """True when the syllable immediately left of ``idx`` carries no stress.

    Used by Verner's law and similar accent-conditioned rules.  A form with no
    stress marking at all is treated as *unknown* and the rule does not fire.
    """
    if "ˈ" not in tokens:
        return False
    k = idx - 1
    if k < 0 or not pat_is_vowel(tokens[k]):
        # Verner's law voices a fricative that directly follows the vowel of an
        # unstressed syllable; a fricative in a cluster (*dukθ-) is not affected.
        return False
    j = k - 1
    while j >= 0 and tokens[j] not in {"ˈ", "ˌ"} and not pat_is_vowel(tokens[j]):
        j -= 1
    return not (j >= 0 and tokens[j] in {"ˈ", "ˌ"})


def pat_is_vowel(seg: str) -> bool:
    from .phonology import is_vowel

    return is_vowel(seg)


@dataclass
class RuleSet:
    """All rules for one stage transition, in application order."""

    source_stage: str
    target_stage: str
    rules: list[Rule] = field(default_factory=list)
    name: str = ""
    date_start: int | None = None
    date_end: int | None = None
    description: str = ""
    references: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict, source_stage: str, target_stage: str) -> "RuleSet":
        meta = data.get("stage", {}) or {}
        rules: list[Rule] = []
        for idx, raw in enumerate(data.get("rules", [])):
            change = raw.get("change") or {}
            match = raw.get("match") or change.get("in") or ""
            replace = raw.get("replace") if raw.get("replace") is not None else change.get("out", "")
            env = raw.get("env") or {}
            rule = Rule(
                id=raw.get("id", f"{target_stage}_{idx}"),
                name=raw.get("name", raw.get("id", "")),
                order=int(raw.get("order", idx * 10)),
                source=meta.get("name", source_stage),
                change=raw.get("description", "") or raw.get("name", ""),
                source_stage=source_stage,
                target_stage=target_stage,
                tier=raw.get("tier", "established"),
                optional=bool(raw.get("optional", False)),
                weight=float(raw.get("weight", 1.0)),
                notes=raw.get("notes", "") or "",
                references=_as_list(raw.get("references") or meta.get("references")),
                examples=raw.get("examples", []) or [],
                match=str(match),
                left=env.get("left") if isinstance(env, dict) else None,
                right=env.get("right") if isinstance(env, dict) else None,
                replace=str(replace),
                iterative=bool(raw.get("iterative", False)),
                transform=str(raw.get("transform", "") or ""),
                params=raw.get("params", {}) or {},
                unstressed_left=bool(raw.get("unstressed_left", False)),
                default_off=bool(raw.get("off_by_default", False)),
            ).compile()
            rules.append(rule)
        rules.sort(key=lambda r: (r.order, r.id))
        return cls(
            source_stage=source_stage,
            target_stage=target_stage,
            rules=rules,
            name=meta.get("name", f"{source_stage} → {target_stage}"),
            date_start=meta.get("date_start"),
            date_end=meta.get("date_end"),
            description=meta.get("description", ""),
            references=_as_list(meta.get("references")),
        )


@dataclass
class Step:
    rule_id: str
    rule_name: str
    tier: str
    before: str
    after: str
    stage: str


@dataclass
class Derivation:
    input: str
    chain: list[str]
    forms: list[str]
    steps: list[Step]
    skipped: list[str] = field(default_factory=list)
    #: True when the laws were given a *writing* instead of a phonological
    #: form and refused to run (see ``derive_detailed``).  Nothing was derived,
    #: and the input is carried down unchanged.
    unreadable: bool = False

    @property
    def output(self) -> str:
        return self.forms[-1] if self.forms else self.input

    def to_dict(self) -> dict:
        return {
            "input": self.input,
            "chain": self.chain,
            "forms": self.forms,
            "output": self.output,
            "steps": [s.__dict__ for s in self.steps],
            "skipped": self.skipped,
            "unreadable": self.unreadable,
        }


def rule_key(ruleset, rule_id: str) -> str:
    """A rule's id, scoped to its transition.

    Rule ids are not globally unique (``hl_loss`` occurs in two Germanic
    transitions), so switching a law off on the word page must name the
    transition as well. The plain id stays accepted for the CLI.
    """
    src = getattr(ruleset, "source_stage", "") or ""
    dst = getattr(ruleset, "target_stage", "") or ""
    return f"{src}~{dst}:{rule_id}" if src and dst else rule_id


def apply_ruleset_verbose(
    form: str,
    ruleset: RuleSet,
    disabled: Iterable[str] = (),
    tiers: set[str] | None = None,
    enabled: Iterable[str] = (),
) -> tuple[str, list[Step], list[dict]]:
    """Apply one transition and report on **every** registered rule.

    Returns ``(output, steps, report)``. ``report`` has one row per rule in the
    transitions's ruleset, whether or not it applied: the word page's ladder shows
    the laws that did apply at each level, and a law switched off further up the
    chain has to stay visible (and switchable back on) even when it no longer
    applies. ``blocked`` marks a rule excluded by ``tiers`` or by being off by
    default; ``enabled`` is how a word's own pathway turns such a rule on
    (2026-11-08: a suffix is a formation law, off unless the word uses it).
    """
    disabled = set(disabled)
    enabled = set(enabled)
    tokens = tokenize(form)
    steps: list[Step] = []
    report: list[dict] = []
    for rule in ruleset.rules:
        before = detokenize(tokens)
        key = rule_key(ruleset, rule.id)
        switched_off = key in disabled or rule.id in disabled
        switched_on = key in enabled or rule.id in enabled
        blocked = (tiers is not None and rule.tier not in tiers) or (
            rule.default_off and not switched_on)
        if switched_off or blocked:
            # Still say what the law *would* do, so a switched-off rule can be
            # judged before it is switched back on. Nothing is committed.
            would = None
            if switched_off and not blocked:
                new, changed = rule.apply(tokens)
                if changed:
                    would = detokenize(new)
            report.append({
                "key": key, "id": rule.id, "name": rule.name, "tier": rule.tier,
                "before": before, "after": before, "would": would,
                "fired": False, "disabled": switched_off, "blocked": blocked,
                "default_off": rule.default_off,
            })
            continue
        new, changed = rule.apply(tokens)
        if changed:
            after = detokenize(new)
            steps.append(Step(rule.id, rule.name, rule.tier, before, after, ruleset.target_stage))
            tokens = new
        else:
            after = before
        report.append({
            "key": key, "id": rule.id, "name": rule.name, "tier": rule.tier,
            "before": before, "after": after,
            "fired": bool(changed), "disabled": False, "blocked": False,
            "default_off": rule.default_off,
        })
    return detokenize(tokens), steps, report


def apply_ruleset(
    form: str,
    ruleset: RuleSet,
    disabled: Iterable[str] = (),
    tiers: set[str] | None = None,
    enabled: Iterable[str] = (),
) -> tuple[str, list[Step]]:
    out, steps, _report = apply_ruleset_verbose(form, ruleset, disabled, tiers, enabled)
    return out, steps


@dataclass
class Level:
    """One stage-to-stage hop, with the form it produced and the laws tried."""

    src: str
    dst: str
    form: str
    rules: list[dict] = field(default_factory=list)
    missing: bool = False
    #: The hop never ran because its input was a script's signs, not sounds.
    unreadable: bool = False


def derive_detailed(
    form: str,
    chain: list[str],
    rulesets: dict[tuple[str, str], RuleSet],
    disabled: Iterable[str] = (),
    tiers: set[str] | None = None,
    enabled: Iterable[str] = (),
) -> tuple[Derivation, list[Level]]:
    """``derive`` plus a per-transition report, for the word-page ladder.

    ``forms`` always has one entry per chain stage, including stages whose rule
    file is missing (the form simply does not change there), so a caller may
    index ``forms`` and ``chain`` together.

    A form *written in a script* is refused outright: the laws are rewrites
    over segments, and cuneiform, Pahlavi or Greek letters are signs, not
    segments.  Feeding them in produced a ladder whose top rung was the script
    and whose lower rungs were that same script copied down, reported as
    "differs from the record" although no law had been given a chance to run
    (2026-11-11, Middle Persian lwc).  The caller must hand over the *reading*
    — ``service._phonological_form`` is what finds it — and a form with no
    recorded reading says so through ``unreadable`` instead of pretending the
    laws were silent.
    """
    if translit.is_scripted(form):
        return (
            Derivation(input=form, chain=list(chain), forms=[form] * len(chain),
                       steps=[], unreadable=True),
            [Level(src, dst, form, [], False, True) for src, dst in zip(chain, chain[1:])],
        )
    disabled = set(disabled)
    enabled = set(enabled)
    current = form
    forms = [current]
    steps: list[Step] = []
    skipped: list[str] = []
    levels: list[Level] = []
    for src, dst in zip(chain, chain[1:]):
        ruleset = rulesets.get((src, dst))
        if ruleset is None:
            skipped.append(f"{src}→{dst}")
            levels.append(Level(src, dst, current, [], True))
            forms.append(current)
            continue
        current, stage_steps, report = apply_ruleset_verbose(
            current, ruleset, disabled, tiers, enabled)
        steps.extend(stage_steps)
        levels.append(Level(src, dst, current, report, False))
        forms.append(current)
    return (
        Derivation(input=form, chain=list(chain), forms=forms, steps=steps, skipped=skipped),
        levels,
    )


def derive(
    form: str,
    chain: list[str],
    rulesets: dict[tuple[str, str], RuleSet],
    disabled: Iterable[str] = (),
    tiers: set[str] | None = None,
    enabled: Iterable[str] = (),
) -> Derivation:
    derivation, _levels = derive_detailed(form, chain, rulesets, disabled, tiers, enabled)
    return derivation
