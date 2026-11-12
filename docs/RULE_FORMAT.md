# Sound-law file format

One YAML file per stage transition, named `<source>__<target>.yaml` using the
language ids in `data/languages.yaml` (e.g. `ine-pro__gem-pro.yaml`).

```yaml
stage:
  name: Proto-Indo-European → Proto-Germanic
  date_start: -800          # approximate, negative = BCE
  date_end: -200
  description: What this file models.
  references: [ringe-2006]  # keys from data/sources.yaml

rules:
  - id: grimm_p            # unique within the file, snake_case
    order: 100             # application order; rules run low → high
    name: "Grimm: *p > *f"
    match: p               # segments to rewrite (see pattern language)
    replace: f             # replacement segments ("" deletes)
    env:                   # optional context
      left: "#"            # word-initial
      right: V             # before a vowel
    tier: established      # established | proposed | custom
    optional: false        # UI may toggle optional rules
    unstressed_left: false # Verner-style: preceding syllable must be unstressed
    description: One sentence of prose.
    references: [grimm-1822]
    examples:
      - {in: "*pṓds", out: "*fōts", gloss: "foot"}
```

## The law's own page

Every rule registered here is reachable as `#/rule/<source>~<target>:<id>`
(`service.rule_page`, `/api/rule`). The page shows the change and its
environment, the examples this file cites, the sources by title, how many exact
derivations the law appears in, and the rules before and after it in the same
transition. Nothing new has to be written for it: the page reads the same file
and the same `data/sources.yaml` keys. Two consequences for authors — give every
new rule a `description` and at least one example (the page shows what you
wrote, including a gap), and cite `references` from `data/sources.yaml` by id,
never a bare author name.

## Terms

* **match / replace** are written in the notation of the stage they operate on.
  Segments are split with the tokeniser: `kʷʰ`, `h₂`, `r̥`, `i̯` are single
  segments, and an acute accent on a vowel is turned into a stress token `ˈ`.
* **env.left / env.right** are patterns anchored to the target: `left` must
  match the *end* of everything before it, `right` the *start* of everything
  after it.
* **tier** is the epistemic status. Only `established` rules may be used when
  reproducing a cited reconstruction; `proposed` and `custom` rules are shown
  separately and can be toggled off in the interface.

## Pattern language

| Atom | Meaning |
|------|---------|
| `p`, `kʷ`, `h₂` | one literal segment |
| `V` | any vowel |
| `C` | any consonant |
| `!V` | any segment that is not a vowel |
| `#` | word edge |
| `.` | any single segment |
| `V?` | optional |
| `(s\|t)` | alternation |

Class names: `V C STOP PSTOP BSTOP ASP FRIC SIB NAS LIQ RES GLIDE LARYN SYL
LONG SHORT VF VB HIGH LOW VLOW ROUND LAB DENT VEL PAL PALATAL LABIOVEL VOICED
VOICELESS ACC STRESS`.

## Ordering

Rules apply in `order`, and each rule sees the output of the previous one. Put
colouring before deletion, Grimm before Verner, and lengthening between them.
When two rules share an order, the `id` breaks the tie.

## Testing a rule file

```bash
python3 -m pie.cli check-rules            # schema + example verification
python3 -m pie.cli derive --chain en "*pṓds"   # full derivation trace
```
