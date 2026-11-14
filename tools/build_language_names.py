#!/usr/bin/env python3
"""Build ``data/language_names.json``: Wiktionary's English names for every
language code that appears in the cognate sets, plus a branch for grouping.

Cognate sets carry Wiktionary language *codes* (``xcl``, ``gem-pro``, ``yms``).
The interface must show names, and a code we have no registry row for would
otherwise surface as a raw code with the branch "Other". Wiktionary's
descendant trees record the name next to every code, so we harvest those.

Branch assignment: the registry wins; otherwise the nearest ancestor in the
descendant tree that has a branch; otherwise a keyword table below (a code's
own name is the last resort). Everything unmatched stays "Other".

Usage:
    python3 tools/build_language_names.py --src $HOME/kaikki
"""
from __future__ import annotations

import argparse
import os
import json
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Ordered: the first keyword that occurs in the language name wins. Longer,
# more specific names come before the families they belong to.
BRANCH_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("Anatolian", ("Hittite", "Luwian", "Lycian", "Lydian", "Carian", "Palaic",
                   "Milyan", "Mysian", "Pisidian", "Sidetic", "Anatolian")),
    ("Tocharian", ("Tocharian",)),
    ("Armenian", ("Armenian",)),
    ("Albanian", ("Albanian", "Arbëresh")),
    ("Palaeo-Balkan", ("Phrygian", "Thracian", "Dacian", "Illyrian", "Messapic",
                       "Venetic", "Paeonian", "Ancient Macedonian", "Elymian",
                       "Liburnian", "Sicel")),
    ("Balto-Slavic", ("Baltic", "Lithuanian", "Latvian", "Prussian", "Sudovian",
                      "Curonian", "Latgalian", "Samogitian", "Slavic", "Russian",
                      "Polish", "Czech", "Slovak", "Slovene", "Slovenian",
                      "Bulgarian", "Macedonian", "Serbian", "Croatian", "Bosnian",
                      "Ukrainian", "Belarusian", "Sorbian", "Ruthenian",
                      "Slovincian", "Kashubian", "Church Slavonic")),
    ("Celtic", ("Irish", "Gaelic", "Welsh", "Breton", "Cornish", "Manx", "Gaulish",
                "Celtiberian", "Lepontic", "Brythonic", "Pictish", "Celtic")),
    ("Germanic", ("German", "Dutch", "English", "Norse", "Swedish", "Danish",
                  "Norwegian", "Icelandic", "Frisian", "Gothic", "Frankish",
                  "Lombardic", "Yiddish", "Afrikaans", "Scots", "Saxon",
                  "Bavarian", "Alemannic", "Luxembourgish", "Cimbrian",
                  "Elfdalian", "Norn", "Gutnish", "Flemish", "Germanic")),
    ("Italic", ("Latin", "Italian", "French", "Spanish", "Portuguese", "Catalan",
                "Occitan", "Romanian", "Galician", "Umbrian", "Oscan", "Faliscan",
                "Picene", "Marrucinian", "Paelignian", "Volscian", "Marsian",
                "Sabine", "Osco-Umbrian", "Italic", "Romance")),
    ("Indo-Iranian", ("Persian", "Iranian", "Avestan", "Kurdish", "Pashto",
                      "Ossetian", "Sogdian", "Bactrian", "Khwarezmian", "Parthian",
                      "Median", "Baluchi", "Gilaki", "Mazanderani", "Tati",
                      "Luri", "Shughni", "Yaghnobi", "Saka", "Khotanese", "Wakhi",
                      "Ishkashimi", "Sarikoli", "Talysh", "Dari", "Zazaki",
                      "Gorani", "Prakrit", "Sanskrit", "Hindi", "Urdu", "Bengali",
                      "Gujarati", "Marathi", "Punjabi", "Nepali", "Sinhala",
                      "Romani", "Kashmiri", "Sindhi", "Odia", "Assamese",
                      "Malayalam", "Telugu", "Indo-Aryan", "Nuristani", "Dardic",
                      "Pashayi", "Kalasha", "Khowar", "Palula", "Indo-Iranian",
                      "Khunsari", "Sivandi", "Semnani", "Larestani", "Karingani",
                      "Ashtiani", "Harzani", "Vafsi", "Tatic", "Parthian")),
    ("Hellenic", ("Greek", "Hellenic")),
    ("Contact / non-IE", ("Arabic", "Aramaic", "Syriac", "Semitic", "Akkadian",
                          "Hebrew", "Coptic", "Egyptian", "Berber", "Turkish",
                          "Turkic", "Hungarian", "Finnish", "Estonian", "Sami",
                          "Uralic", "Mari", "Mordvin", "Komi", "Udmurt", "Khanty",
                          "Basque", "Kartvelian", "Georgian", "Chechen", "Ingush",
                          "Tsez", "Caucasian", "Chinese", "Etruscan", "Elamite",
                          "Urartian", "Hurrian", "Hunnic", "Xiongnu", "Yeniseian",
                          "Afroasiatic", "Sumerian", "Mandaic", "Translingual")),
]


def branch_for(name: str, fallback: str = "Other") -> str:
    lowered = (name or "").lower()
    for branch, keys in BRANCH_KEYWORDS:
        for key in keys:
            if key.lower() in lowered:
                return branch
    return fallback


def harvest(rows: list, names: dict[str, str], branches: dict[str, str],
            inherited: str | None = None) -> None:
    for row in rows or []:
        code = row.get("lang_code")
        name = row.get("lang")
        branch = inherited
        if code:
            if name and code not in names:
                names[code] = name
            if branch:
                # The tree edge is an inheritance link, so the parent's branch
                # describes the child unless the child's own name says otherwise.
                branches.setdefault(code, branch_for(name or code, branch))
            else:
                branches.setdefault(code, branch_for(name or code, "Other"))
            branch = branches.get(code, branch)
        harvest(row.get("descendants") or [], names, branches, branch)


def main() -> int:
    ap = argparse.ArgumentParser()
    dump = os.environ.get("PIE_KAIKKI", str(Path.home() / "kaikki"))
    ap.add_argument("--src", default=dump)
    ap.add_argument("--out", default=str(DATA / "language_names.json"))
    args = ap.parse_args()

    registry = {row["id"]: row for row in yaml.safe_load((DATA / "languages.yaml").open(encoding="utf-8"))}
    names: dict[str, str] = {}
    branches: dict[str, str] = {}
    pie = Path(args.src) / "ProtoIndoEuropean.jsonl"
    if not pie.exists():
        raise SystemExit(f"missing {pie}")
    with pie.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            harvest(entry.get("descendants") or [], names, branches)

    out = {}
    for code, name in names.items():
        row = registry.get(code, {})
        out[code] = {
            "name": row.get("name") or name,
            "branch": row.get("branch") or branches.get(code) or branch_for(name),
        }
    payload = {
        "generated": date.today().isoformat(),
        "source": "Wiktionary descendant trees (kaikki.org), registry overrides",
        "languages": dict(sorted(out.items())),
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print(f"{len(out)} language codes -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
