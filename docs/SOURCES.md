# Sources and licences

## Corpus
- **Wiktionary** (CC BY-SA 4.0) — glosses, etymologies, ancestry chains,
  descendant trees.
- **Wiktextract / kaikki.org** — machine-readable dumps of Wiktionary used to
  build `data/lexicon/` and `data/cognate_sets/`. Regenerate with
  `tools/build_lexicons.py`.
- **MacKenzie, A Concise Pahlavi Dictionary** — Middle Persian glosses, converted
  from a PDF with the SAIA Docling service (`tools/docling_convert.py`).

## Literature cited by the rule files
See `data/sources.yaml` for the authoritative list; the core references are
Ringe (2006) and Ringe & Taylor (2014) for Germanic, Fortson (2010) and Beekes
(2011) for the family, Mayrhofer (1986) for Indo-Iranian, Hoffmann & Forssman
(2004) and Skjærvø (2009) for Avestan, Kent (1953) for Old Persian,
MacKenzie (1971) and Skjærvø (2009) for Middle Persian, Meiser (1998) and
Lejeune (1972) for Italic and Greek, and the original articles for the named
laws (Grimm 1822, Verner 1877, Grassmann 1863, Bartholomae 1882).

## Licence
Code: GPL-3.0-or-later (repository licence). Wiktionary-derived data keeps its
CC BY-SA 4.0 terms; cite Wiktionary and this repository if you redistribute it.
