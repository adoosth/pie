/* A DOM stub, enough to exercise the front end's pure renderers in Node.
 *
 * The word-page regression this catches: `skipped` is an *empty array* for
 * every modelled language, and an empty array is truthy in JavaScript — so a
 * plain `!r.skipped` filter dropped the whole "all languages" table and listed
 * every modelled stage as a gap. */
"use strict";
const fs = require("fs");
const path = require("path");
const assert = require("assert");
const vm = require("vm");

const WEB = path.join(__dirname, "..", "src", "pie", "app", "web");

const el = () => ({
  addEventListener() {}, setAttribute() {}, getAttribute() { return null; }, focus() {},
  classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
  querySelectorAll: () => [], querySelector: () => el(), appendChild() {}, replaceWith() {},
  innerHTML: "", value: "", dataset: {}, style: {}, onclick: null, offsetWidth: 0,
  parentElement: null,
});
const context = {
  console, setTimeout, clearTimeout, setInterval: () => 0, clearInterval: () => {},
  URL, URLSearchParams, JSON, Math, Date, Promise, Intl,
  document: {
    querySelector: () => el(), querySelectorAll: () => [], addEventListener() {},
    createElement: () => el(), body: el(),
  },
  navigator: { clipboard: {} },
  location: { hash: "", origin: "http://localhost" },
  history: { replaceState() {} },
  window: { addEventListener() {}, matchMedia: () => ({ matches: false }),
            location: { hash: "", origin: "http://localhost" } },
  fetch: async () => ({ json: async () => ({}) }),
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(WEB, "app.js"), "utf8"), context);

const row = (over) => Object.assign({
  kind: "attested", steps: 1, tiers: ["established"], laws: [], skipped: [], recorded: null,
  evidence: "strong", confidence: "high", show_reading: false,
}, over);

/* Assertions about wording run on the text, so a nested <span> for the IPA
   cannot make a label look missing. */
const plain = (h) => h.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");
/* The family below a stage is a tree, not a flat table (2026-11-08): only the direct children are listed, and each one opens into its
   own children. Every form is a door, and a row that reaches a record opens
   the record — a ✓ must not lead to "nothing is recorded here". */
const branchNode = (over) => Object.assign({
  kind: "attested", steps: 1, tiers: ["established"], laws: [], skipped: [],
  recorded: null, evidence: "strong", confidence: "high", show_reading: false,
  form_known: false, children: [], depth: 0, branch: "Indo-Iranian (Iranian)",
}, over);
const branch = {
  source: { lang: "ira-pro", lang_name: "Proto-Iranian", form: "jrˈayah" },
  counts: { direct: 2, languages: 4, match: 1, differs: 0, new: 3, gaps: 0, steps: 7,
            strong: 3, weak: 0 },
  tree: [
    branchNode({ l: "ave", lang_name: "Avestan", form: "zrayō", steps: 3 }),
    branchNode({ l: "peo", lang_name: "Old Persian", form: "drˈayah", status: "match",
      evidence: "attested", steps: 1,
      recorded: { w: "𐎭𐎼𐎹", via: "origin", evidence: "attested", ipa: "", reading: "drayaʰ",
                  show_reading: false, known: true },
      children: [
        branchNode({ l: "pal", lang_name: "Middle Persian", form: "drˈay", depth: 1, steps: 2,
          children: [branchNode({ l: "fa", lang_name: "Persian", form: "dray", depth: 2 })] }),
      ] }),
  ],
};
const branchHtml = context.renderBranch(branch, { via: "peo/𐎭𐎼𐎹", claim: true });
const branchText = plain(branchHtml);
assert.ok(branchText.includes("Establish Pathways"), branchText.slice(0, 200));
assert.ok(branchText.includes("2 direct descendants"), "the counts stay, quietly, in the heading");
assert.ok(branchText.includes("4 languages below in all"), "the whole branch is counted, not listed");
assert.ok(branchHtml.includes('<details class="branchnode" data-l="peo"'),
  "a node with children is a disclosure");
assert.ok(!branchHtml.includes('<details class="branchnode" data-l="ave"'),
  "a leaf has nothing to disclose");
assert.ok(branchHtml.indexOf('data-l="pal"') > branchHtml.indexOf('data-l="peo"'),
  "Middle Persian sits inside Old Persian, not beside it");
assert.ok(branchHtml.indexOf('data-l="fa"') > branchHtml.indexOf('data-l="pal"'),
  "Persian sits inside Middle Persian");
assert.ok(!/<details[^>]*data-l="fa"/.test(branchHtml), "Persian has no children to open");
/* A ✓ row opens the record, not the prediction. */
assert.match(branchHtml, /<a class="formlink" href="#\/word\/peo\/%F0%90%8E%AD[^"]*"/,
  "the matching row's form links to the recorded word's page");
assert.ok(branchHtml.includes("dráyah"), "the laws' own form is still what is shown, printed with an acute");
/* A record the laws almost reach is a question, never a ✓ (2026-11-12):
   Persian کبود *kabud* where the laws give *kabūde*. The row shows the record,
   a yellow ⚠ and the words, and it must not wear the ✓ or count as a match. */
const nearRow = context.renderBranch({
  source: { lang: "peo", lang_name: "Old Persian", form: "kapautakˈah" },
  counts: { direct: 1, languages: 1, match: 0, unverified: 1, differs: 0, new: 0,
            gaps: 0, steps: 2, strong: 1, weak: 0 },
  tree: [branchNode({ l: "fa", lang_name: "Persian", form: "kabūde", status: "unverified",
    recorded: { w: "کبود", via: "near", evidence: "attested", ipa: "ka.ˈboːd",
                reading: "kabud", show_reading: true, known: true, unverified: true,
                review: { form: "kabūde", record: "kabud" } } })],
}, { via: "peo/𐎣𐎱𐎢𐎫𐎣", claim: true });
const nearText = plain(nearRow);
assert.ok(nearText.includes("match not verified"), nearText.slice(0, 300));
assert.ok(nearRow.includes('class="unmatchdot"'), "the ⚠ disc marks the unverified row");
assert.ok(!nearRow.includes('aria-label="matches the record"'), "no ✓ on an unverified match");
assert.ok(nearRow.includes("1 unverified match"), "the heading counts them apart from matches");

/* Ghost mode: the colours come from the payload, which never says attested for
   a form that is not a recorded etymon; the count badge must not claim green. */
const ghostHtml = context.renderBranch(branch, { via: "peo/𐎭𐎼𐎹", claim: false });
assert.ok(!/class="badge attested"/.test(ghostHtml),
  "a ghost page's count is not badged as a match");

/* Non-Latin scripts always come with a pronunciation. */
/* `const` bindings are lexical in the vm context, so expressions are
   evaluated inside it rather than read off the context object. */
const evaluate = (expr) => vm.runInContext(expr, context);
const persian = evaluate('form("پدر", "fa", { ev: "attested", ipa: "pa.ˈdar", show: true })');
assert.ok(persian.includes('class="form rtl ev-attested"'), persian);
assert.ok(persian.includes("/pa.ˈdar/"), "Persian must carry its IPA");

/* Language names in the cognate table are links; the forms are plain text. */
const cogTable = context.renderCognateTable({ forms: [
  { l: "grc", w: "πατήρ", r: "patḗr", ipa: "pa.tɛ̌ːr", lang_name: "Greek", branch: "Greek",
    kind: "attested", evidence: "attested", known: true, show_reading: true },
  { l: "grk-pro", w: "*patēr", r: "", lang_name: "Proto-Hellenic", branch: "Greek",
    kind: "proto", evidence: "literary", known: false, show_reading: false },
] }, "grc", "πατήρ");
assert.ok(cogTable.includes('<a href="#/word/grc/'), "a known word links from its language name");
assert.ok(cogTable.includes('<a href="#/search?q=*pat'));
assert.ok(cogTable.includes("/pa.tɛ̌ːr/"), "the Greek form carries its IPA");
assert.ok(!/<a [^>]*><span class="form/.test(cogTable), "cognate forms are not links");
assert.ok(cogTable.includes('ev-literary'), "a proto form is gold, not green");

console.log("ui render ok");

/* ---------------------------------------------------------------- */
/* the word-page ladder                                             */
/* ---------------------------------------------------------------- */
/* The ancestor comes first, the word last, with the date of each stage; each
   step lists the laws that moved the form, and a law switched off stays
   visible so it can be switched back on. */
const level = (over) => Object.assign({
  era: [0, 0], era_label: "c. 0", era_mid: 0, kind: "attested", branch: "Germanic",
  form: "", baseline: "", changed: false, status: "derived", evidence: "strong",
  show_reading: false, recorded: null, rules: [], transition: null,
}, over);
const hierarchy = {
  start: "ine-pro", start_name: "Proto-Indo-European", etymon: "nókʷts", root: false,
  switched_off: 1, missing: [], total_steps: 2, earlier: [],
  exact: { stage: "enm", name: "Middle English", form: "nighte", steps: 1, via_translit: false },
  result: { status: "differs", form: "nˈæhwθ", target: "night", match: false,
            match_via_translit: false, ipa: "naɪ̯t", reading: "" },
  levels: [
    level({ stage: "ine-pro", name: "Proto-Indo-European", era_label: "c. 4500–2500 BCE",
            era_mid: -3500, kind: "proto", form: "nókʷts", baseline: "nókʷts", status: "start",
            evidence: "literary",
            recorded: { w: "nókʷts", more: [], evidence: "literary", ipa: "", reading: "",
                        show_reading: false, matches: true } }),
    level({ stage: "gem-pro", name: "Proto-Germanic", era_label: "c. 500 BCE – 1 CE",
            era_mid: -250, kind: "proto", form: "nˈahwθs", baseline: "nˈahwt", changed: true,
            evidence: "weak",
            recorded: { w: "nahts", more: ["naht"], evidence: "literary", ipa: "", reading: "",
                        show_reading: false, matches: false,
                        pages: [{ id: "wiktionary", title: "Wiktionary", kind: "wiktionary",
                                  url: "https://en.wiktionary.org/wiki/Reconstruction:Proto-Germanic/nahts" }] },
            transition: { from: "ine-pro", to: "gem-pro", missing: false, fired: 1, silent: 40,
                          switched_off: 1 },
            rules: [
              { key: "ine-pro~gem-pro:grimm_t", id: "grimm_t", name: "Grimm: *t → *þ",
                tier: "established", before: "nókʷts", after: "nˈōkʷθs", fired: true, disabled: false },
              { key: "ine-pro~gem-pro:hw", id: "hw", name: "hw notation", tier: "established",
                before: "nˈōkʷθs", after: "nˈōkʷθs", would: "nˈōkʷ",
                fired: false, disabled: true },
            ] }),
  ],
};
const ladder = context.renderHierarchy(hierarchy, { lang: "en", lang_name: "English" });
const ladderWords = plain(ladder);
assert.ok(ladder.includes('data-stage="ine-pro"'), "the ladder starts at the ancestor");
assert.ok(ladder.indexOf("ine-pro") < ladder.indexOf("gem-pro"), "oldest stage first");
assert.ok(ladderWords.includes("c. 4500–2500 BCE"), "the date of each stage is shown");
assert.ok(ladder.includes("--gap:"), "the rail is spaced by the dates");
/* A gap is a length. The rail segment above a rung is drawn with
   `calc(-1 * var(--gap))`, and a bare `0` makes that declaration invalid: the
   segment loses its top, the rung draws no line, and the column vanishes
   between two stages (2026-11-12). */
const gapValues = [...ladder.matchAll(/--gap:\s*([^;"\s]+)/g)].map((m) => m[1]);
assert.ok(gapValues.length, "the ladder writes its spacing as a variable");
assert.ok(gapValues.every((v) => /^(\d*\.?\d+)(px|rem|em)$/.test(v)),
  "every --gap is a length the rail's calc() can use, never a bare number");
/* The layout (2026-11-07): the language name sits on the left
   of the timeline, above the date, and the word itself on the right. */
const firstRung = ladder.slice(ladder.indexOf('data-stage="ine-pro"'), ladder.indexOf('data-stage="gem-pro"'));
assert.match(firstRung,
  /<div class="when">\s*<span class="when-name kind-proto"[^>]*>Proto-Indo-European<\/span>\s*<span class="when-era">/,
  "the language name is above the date in the timeline column");
assert.ok(firstRung.indexOf("when-name") < firstRung.indexOf("when-era"), "name above the date");
assert.ok(firstRung.indexOf("when-era") < firstRung.indexOf('class="rung-body"'),
  "the word and its laws stand to the right of the timeline");
assert.ok(!firstRung.includes("rung-era-inline"), "the name is not repeated in the rung body");
/* 2026-11-07: "attested language" / "reconstructed stage" left the rung body.
   The name in the timeline carries it — green attested, gold reconstructed —
   and says it in words when hovered, so colour is never the only cue. */
assert.ok(!ladderWords.includes("attested language") && !ladderWords.includes("reconstructed stage"),
  "no worded kind badge on the right of the timeline");
assert.ok(!ladder.includes('class="rung-head"'), "the reconstruction is the top-most thing on the right");
assert.match(firstRung, /<div class="rung-body">\s*<div class="rung-forms">/,
  "the form opens the rung body");
assert.ok(firstRung.includes("kind-proto"), "a reconstructed stage's name is marked as one");
assert.ok(/when-name kind-proto"[^>]*data-tip="Reconstructed stage[^"]*"/.test(firstRung),
  "hovering a reconstructed name says so in words");
assert.ok(firstRung.includes("Branch: Germanic") && firstRung.includes("In use c. 4500–2500 BCE"),
  "the language tooltip carries its branch and era");
const withEnglish = Object.assign({}, hierarchy, {
  levels: [...hierarchy.levels, level({
    stage: "en", name: "English", era_label: "since c. 1500", era_mid: 1600,
    form: "nˈæhwθ", status: "differs", evidence: "weak",
  })],
});
const enHtml = context.renderHierarchy(withEnglish, { lang: "en", lang_name: "English" });
const englishRung = enHtml.slice(enHtml.indexOf('data-stage="en"'));
assert.ok(/when-name kind-attested"[^>]*data-tip="Attested language[^"]*"/.test(englishRung),
  "an attested language is coloured and explained as one");
assert.ok(englishRung.includes('class="when-here"') && plain(englishRung).includes("this word"),
  "the word being read is named in the timeline column");
assert.ok(!englishRung.includes('class="rung-head"'),
  "the word's own rung opens with the form, not with a badge");
assert.ok(ladder.includes('class="law on"') && ladder.includes('class="law off"'),
  "a law has an on and an off state");
assert.ok(ladder.includes('data-off="ine-pro~gem-pro:grimm_t"'), "a law is addressable");
assert.ok(ladder.includes('href="#/rule/ine-pro~gem-pro%3Agrimm_t"'),
  "a law named on a page opens its own page (2026-11-08)");
assert.match(ladder, /aria-pressed="false"/, "a switched-off law says so to a reader");
assert.ok(ladderWords.includes("1 law is switched off"), "the page counts the switched-off laws");
/* 2026-11-12: a rung whose form the etymology names but no glossary entry
   holds is not a word of that stage.  It prints dark red, wears no ✓ and no
   halo, and says plainly that there is no entry — it is never "gold, matched",
   and the page never explains transliteration machinery in its place. */
const unheld = { ...hierarchy, levels: [level({
  stage: "ira-pro", name: "Proto-Iranian", era_label: "c. 2000–1000 BCE",
  era_mid: -1500, kind: "proto", form: "kapawtakˈah", baseline: "kapawtakˈah",
  status: "match", evidence: "literary",
  recorded: { w: "kapawtakáh", more: [], evidence: "literary", ipa: "", reading: "",
              show_reading: false, matches: true, same: true, known: false },
})] };
const unheldHtml = context.renderHierarchy(unheld, { lang: "peo", lang_name: "Old Persian" });
const unheldRung = unheldHtml.slice(unheldHtml.indexOf('data-stage="ira-pro"'));
assert.ok(/class="form[^"]*ev-missing/.test(unheldRung),
  "a form no entry holds is dark red, whatever the literature calls it");
assert.ok(!unheldRung.includes("matchdot"), "a non-existent form wears no ✓");
assert.ok(!/class="form[^"]*matched/.test(unheldRung), "and no halo box either");
assert.ok(plain(unheldRung).includes("no entry for this word"),
  "it says in words that the glossary has no entry");
assert.ok(!plain(unheldHtml).includes("transliteration only"),
  "the machinery note is gone (2026-11-12)");
assert.ok(!unheldRung.includes("ev-literary"), "gold would claim a word the stage does not hold");
/* 2026-11-12: a row may spell the word without a sign the headword carries
   (Old Persian 𐎼𐎢𐎨 for 𐎼𐎢𐎨𐏃).  It is the same word, so the rung shows
   its meaning and opens the glossary's own spelling, never a ghost page. */
const alias = { ...hierarchy, levels: [level({
  stage: "ira-pro", name: "Proto-Iranian", era_label: "c. 2000–1000 BCE",
  era_mid: -1500, kind: "proto", form: "raučah", baseline: "raučah",
  status: "match", evidence: "attested",
  recorded: { w: "𐎼𐎢𐎨", headword: "𐎼𐎢𐎨𐏃", more: [], evidence: "attested",
              ipa: "", reading: "raučah", show_reading: false, matches: true,
              same: true, known: true, pos: "noun", gloss: "day" },
})] };
const aliasHtml = context.renderHierarchy(alias, { lang: "peo", lang_name: "Old Persian" });
const aliasRung = aliasHtml.slice(aliasHtml.indexOf('data-stage="ira-pro"'));
assert.ok(plain(aliasRung).includes("day"), "the headword's meaning is printed");
assert.ok(!plain(aliasRung).includes("no entry for this word"),
  "a word the glossary holds is never called missing");
assert.ok(aliasRung.includes(encodeURIComponent("𐎼𐎢𐎨𐏃")),
  "the rung opens the glossary's own spelling of the word");
/* 2026-11-08: the laws of a step sit on the rail *between* the two
   forms — a row of the timeline above the rung they produced, never a list
   under it. */
const stepAt = ladder.indexOf('class="lawstep"');
assert.ok(stepAt > 0, "the laws of a step have their own row on the timeline");
assert.ok(ladder.indexOf('data-stage="ine-pro"') < stepAt && stepAt < ladder.indexOf('data-stage="gem-pro"'),
  "the laws stand between the form they were run on and the form they produced");
/* The words must not only be in that order: the chips have to *sit* in the gap,
   with room above and below, or they read as a footnote to the word above
   (2026-11-08). The step takes the upper half of the space between
   two rungs, the rung below the lower half. */
assert.match(ladder, /class="lawstep" style="--gap:\d+px"/,
  "the law row owns part of the gap between the two words");
assert.match(ladder, /data-stage="gem-pro" style="--gap:(\d+)px/,
  "the rung that follows the laws leaves the other half of that gap");
const gemRung = ladder.slice(ladder.indexOf('data-stage="gem-pro"'), ladder.indexOf('data-stage="gem-pro"') + 4000);
assert.ok(!gemRung.split('class="branchtree"')[0].includes('class="lawlist"'),
  "the rung body no longer carries the law list");
assert.ok(ladder.includes('data-reset="1"'), "there is a way back to the full rule set");
assert.ok(ladder.includes('class="was"') && ladderWords.includes("náhwt"),
  "a stage changed by a switch shows the form it had");
assert.ok(ladderWords.includes("*nṓkʷθs → *nṓkʷ"),
  "a switched-off law still says what it would have done, with the star the stage writes");
/* 2026-11-08: the record is a second word, marked by a small glyph
   on its top-right corner instead of a RECORDED badge under it — an open book,
   because a record is a form written down somewhere — and the edit control is
   a pencil right after the form the laws produced, never after the record. */
const pgsRung = ladder.slice(ladder.indexOf('data-stage="gem-pro"'));
const TAG = 'class="recorddot';
assert.ok(pgsRung.includes(TAG), "the recorded form is marked as a record");
assert.ok(!pgsRung.includes(">recorded</a>"), "the record is a glyph, not the word 'recorded'");
assert.ok(pgsRung.includes('class="wmark"') && /class="wmark"[^>]*>W</.test(pgsRung),
  "the glyph is Wiktionary's W: a source's initial, not a quotation mark");
assert.ok(!pgsRung.includes('stroke="currentColor"'),
  "the W is a serifed glyph now, not a monoline stroke (2026-11-12)");
assert.ok(!/class="recorddot[^>]*>“/.test(pgsRung),
  "the old quotation mark glyph is gone from the mark");
assert.ok(!pgsRung.includes("M12 6.6C10.4"), "the book glyph is gone");
assert.ok(pgsRung.indexOf('class="recword"') < pgsRung.indexOf(">*nahts<")
          && pgsRung.indexOf(">*nahts<") < pgsRung.indexOf(TAG),
  "the mark is on the recorded word itself");
assert.ok(pgsRung.indexOf("náhwθs") < pgsRung.indexOf(">*nahts<"),
  "the reconstructed form is read before its record");
/* 2026-11-12: every form of a reconstructed stage carries the asterisk the
   literature writes it with — the rung the laws produced as well as the record
   beside it.  The star used to come from whichever renderer drew the form, so
   the same word could be /gem-pro/*anda- in a link and `anda-` on the rung. */
assert.ok(ladder.includes(">*nókʷts<") && ladder.includes(">*náhwθs<"),
  "a proto rung and its record print the reconstruction's star");
assert.ok(!/>nókʷts</.test(ladder) && !/>náhwθs</.test(ladder),
  "no form of a reconstructed stage is printed bare");
assert.ok(pgsRung.indexOf("náhwθs") < pgsRung.indexOf('data-edit="gem-pro"')
          && pgsRung.indexOf('data-edit="gem-pro"') < pgsRung.indexOf('class="recword"'),
  "the edit control follows the reconstructed word, not the record");
assert.ok(!pgsRung.includes(">edit<"), "the edit control is an icon, not the word 'edit'");
assert.ok(/class="editbtn icon"[^>]*aria-label="Edit the form for Proto-Germanic"/.test(pgsRung),
  "the pencil names the form it edits for a reader who cannot see it");
const pgsStart = ladder.slice(ladder.indexOf('class="recword"', ladder.indexOf('data-stage="ine-pro"')),
  ladder.indexOf('data-stage="gem-pro"'));
assert.ok(!pgsStart.includes(TAG),
  "a form with no recorded page carries no mark at all (2026-11-12)");
assert.ok(!/recorddot[^>]*href="#\/word/.test(pgsRung),
  "the mark never opens an internal word page in place of a source");
assert.ok(!pgsRung.includes("Open where it was recorded"),
  "the tooltip names the source but never instructs the reader to click (2026-11-08)");
assert.ok(!ladderWords.includes("the laws differ") && !ladderWords.includes("the laws reproduce"),
  "no verdict sentence on the rung");
assert.ok(!pgsRung.includes("ev-weak") || pgsRung.includes("nahts"),
  "the derived form keeps its own evidence colour");
assert.ok(ladderWords.includes("Middle English nighte"), "an exact chain further down is named");

/* A source the server resolved to its own page: the record mark is a door to
   it, in a new tab, so hovering tells the reader where the word was read and
   clicking takes them there (2026-11-08). The tooltip itself says
   nothing about clicking — the mark is visibly a link. */
const citedLevel = level(Object.assign({}, hierarchy.levels[1], {
  recorded: Object.assign({}, hierarchy.levels[1].recorded, {
    pages: [{ id: "wiktionary", title: "Wiktionary", kind: "wiktionary",
              url: "https://en.wiktionary.org/wiki/Reconstruction:Proto-Germanic/nahts" }],
  }),
}));
const citedHtml = context.renderHierarchy(Object.assign({}, hierarchy, {
  levels: [hierarchy.levels[0], citedLevel],
}), { lang: "en", lang_name: "English" });
assert.match(citedHtml,
  /<a class="recorddot wikt"[^>]*href="https:\/\/en\.wiktionary\.org\/wiki\/Reconstruction:Proto-Germanic\/nahts"[^>]*target="_blank" rel="noopener"/,
  "the record mark opens the page the record was read on");
assert.ok(/class="recorddot wikt"[^>]*data-tip="The Proto-Germanic record of this word/.test(citedHtml),
  "hovering the mark says where the record comes from");
assert.ok(citedHtml.indexOf("Open where it was recorded") < 0,
  "a linked source adds no 'open where it was recorded' sentence to the tooltip");

/* Two recorded pages are two doors on the same corner (2026-11-12):
   the W for the Wiktionary article and the book for the dictionary's own entry
   for the word, each opening its own page, and the site's front page is never
   one of them. */
const twoPages = context.renderHierarchy(Object.assign({}, hierarchy, {
  levels: [hierarchy.levels[0], level(Object.assign({}, hierarchy.levels[1], {
    recorded: Object.assign({}, hierarchy.levels[1].recorded, {
      pages: [
        { id: "dehkhoda", title: "Dehkhoda", kind: "dictionary",
          url: "https://vajehyab.com/dehkhoda/%DA%A9%D8%A8%D9%88%D8%AF" },
        { id: "wiktionary", title: "Wiktionary", kind: "wiktionary",
          url: "https://en.wiktionary.org/wiki/%DA%A9%D8%A8%D9%88%D8%AF" },
      ],
    }),
  }))],
}), { lang: "en", lang_name: "English" });
assert.equal((twoPages.match(/class="recorddot/g) || []).length, 2,
  "one mark per recorded page");
assert.match(twoPages, /class="recorddot wikt"[^>]*href="https:\/\/en\.wiktionary\.org\/wiki\//,
  "the W opens the Wiktionary article");
assert.match(twoPages, /class="recorddot"[^>]*href="https:\/\/vajehyab\.com\/dehkhoda\/%DA%A9/,
  "the book opens the dictionary's entry for the word itself");
assert.ok(twoPages.indexOf('class="recorddot wikt"') < twoPages.indexOf('href="https://vajehyab.com'),
  "the W stands first, then the book");

/* 2026-11-08: the law engine writes stress as ˈ, but the page prints it the
   way a dictionary does — an acute on whatever vowel carries it — and every
   form on the ladder opens its own page. */
const pretty = evaluate('pf("drˈayah")');
assert.equal(pretty, "dráyah", "a stressed a is written á");
assert.equal(evaluate('pf("xˈē")'), "xḗ", "a long vowel keeps its macron and takes the acute");
assert.equal(evaluate('pf("nˈōkʷθs")'), "nṓkʷθs", "any vowel, not only a");
assert.equal(evaluate('pf("ˈi ˈu ˈo ˈe")'), "í ú ó é", "every vowel is covered, each in place");
assert.equal(evaluate('pf("ˈr̥")'), "ŕ̥", "a syllabic sonorant carries the acute like a vowel");
assert.equal(evaluate('pf("ˈk")'), "ˈk", "an ordinary consonant is left alone");
assert.ok(firstRung.includes('class="formlink"'),
  "a word on the ladder opens a page of its own");
assert.ok(firstRung.includes("#/word/ine-pro/n%C3%B3k%CA%B7ts"),
  "the recorded form links to its own word page");
assert.ok(!pgsRung.includes('class="formlink"') || !pgsRung.includes("#/word/en/"),
  "the word being read is not linked to itself");
assert.ok(ladder.includes('data-tip="'), "every form explains its colour on hover");
assert.ok(!ladder.includes("legend"), "no colour key anywhere on the word page");
assert.ok(ladder.includes('class="badge changed"'), "a changed stage is worded, not only coloured");

/* Editing a rung and storing the path (2026-11-07). Every rung but the
   word itself offers "edit"; a typed start is marked as a hypothesis; and when
   it lands on the attested word the page offers to store the pathway. */
/* 2026-11-08: a reconstruction is editable at any point — the
   ancestors, the word itself, and any rung the timeline was carried into. */
assert.equal((ladder.match(/data-edit="/g) || []).length, hierarchy.levels.length,
  "every rung can be edited, the word itself included");
assert.ok(!ladder.includes("data-cut="), "nothing can be cut while the timeline is the word's own ancestry");
assert.ok(!ladder.includes("data-store-pathway"),
  "a path that does not land on the word cannot be stored");

const edited = Object.assign({}, hierarchy, {
  start: "enm", start_name: "Middle English", start_form: "nighte",
  edited: { stage: "enm", form: "nighte", name: "Middle English" },
  earlier: [], switched_off: 0,
  stored_pathway: null,
  pathways: [{ id: "abc123", lang: "en", word: "night", created: "2026-11-07T12:00:00Z",
               start: { stage: "enm", name: "Middle English", form: "nighte" },
               laws: [{ step: "enm→en", id: "x", name: "y", tier: "established" }], note: "" }],
  result: { status: "match", form: "night", target: "night", match: true,
            match_via_translit: false, ipa: "naɪ̯t", reading: "", attested: true },
  levels: [level({ stage: "enm", name: "Middle English", era_label: "c. 1100–1500",
                   era_mid: 1300, form: "nighte", baseline: "nighte", status: "start",
                   evidence: "edited", edited: true }),
           level({ stage: "en", name: "English", era_label: "since c. 1500", era_mid: 1900,
                   form: "night", baseline: "night", status: "match", evidence: "attested",
                   recorded: { w: "night", more: [], evidence: "attested", ipa: "naɪ̯t",
                               reading: "", show_reading: false, matches: true } })],
});
const editedHtml = context.renderHierarchy(edited, { lang: "en", lang_name: "English" });
const editedWords = plain(editedHtml);
assert.ok(editedHtml.includes("edited-bar") && editedWords.includes("edited start"),
  "a typed start is labelled, never presented as recorded ancestry");
assert.ok(editedHtml.includes('data-unedit="1"'), "the recorded ancestry can be restored");
assert.ok(editedHtml.includes('class="badge edited"'), "the edited rung says so in words");
assert.ok(editedHtml.includes('class="form ev-edited"'), "a typed form is not coloured as evidence");
assert.ok(editedHtml.includes("data-store-pathway"),
  "a path that lands on the attested word offers 'store pathway'");
assert.ok(editedWords.includes("store pathway"), "the option is spelled out, not only a colour");
assert.ok(editedHtml.includes("Stored pathways"), "stored pathways are listed for the word");
assert.ok(editedHtml.includes('data-load-pathway="abc123"'), "a stored path can be loaded again");

const already = context.renderHierarchy(Object.assign({}, edited, { stored_pathway: "abc123" }),
                                      { lang: "en", lang_name: "English" });
assert.ok(!already.includes("data-store-pathway"), "the same path is not stored twice");
assert.ok(already.includes("pathway stored"), "the page says it is already recorded");
console.log("editable ladder ok");

/* ---------------------------------------------------------------- */
/* the etymon rung is a record, not a blank                          */
/* ---------------------------------------------------------------- */
/* English *book* reaches PIE only through its cognate set. The root's own
   record — form, part of speech and gloss — belongs on the top rung, and the
   rung must not claim "nothing recorded" beside a cognate section that quotes
   the root's meaning (2026-11-07). */
const book = {
  start: "ine-pro", start_name: "Proto-Indo-European", etymon: "bʰeh₂g", root: true,
  etymon_record: { w: "bʰeh₂g", pos: "root", gloss: "to divide, distribute, allot" },
  linked_by_set: true, set_start: true, set_is_root: true,
  set_source: "*bʰóh₂g-s ~ *bʰéh₂g-s",
  ancestry_top: { stage: "gem-pro", name: "Proto-Germanic" }, off_chain: [],
  switched_off: 0, missing: [], total_steps: 1, earlier: [],
  exact: null,
  result: { status: "differs", form: "būk", target: "book", match: false,
            match_via_translit: false, ipa: "", reading: "", attested: false },
  levels: [
    level({ stage: "ine-pro", name: "Proto-Indo-European", era_label: "c. 4500–2500 BCE",
            era_mid: -3500, kind: "proto", form: "bʰeh₂g", baseline: "bʰeh₂g", status: "start",
            evidence: "literary",
            recorded: { w: "bʰeh₂g", more: [], evidence: "literary", ipa: "", reading: "",
                        show_reading: false, matches: false, same: true, pos: "root",
                        gloss: "to divide, distribute, allot", origin: "glossary" } }),
    level({ stage: "en", name: "English", era_label: "since c. 1500", era_mid: 1900,
            form: "būk", baseline: "būk", status: "differs", evidence: "weak",
            recorded: { w: "book", more: [], evidence: "attested", ipa: "", reading: "",
                        show_reading: false, matches: false, pos: "noun",
                        gloss: "A collection of sheets of paper bound together",
                        origin: "word",
                        pages: [{ id: "wiktionary", title: "Wiktionary", kind: "wiktionary",
                                  url: "https://en.wiktionary.org/wiki/book" }] } }),
  ],
};
const bookHtml = context.renderHierarchy(book, { lang: "en", lang_name: "English" });
const bookWords = plain(bookHtml);
const bookTop = bookHtml.slice(bookHtml.indexOf('data-stage="ine-pro"'), bookHtml.indexOf('data-stage="en"'));
assert.ok(bookTop.includes("bʰeh₂g"), "the root's recorded form is on the top rung");
assert.ok(!plain(bookTop).includes("nothing recorded at this stage"),
  "a rung with a record must never say nothing is recorded");
assert.ok(plain(bookTop).includes("root · “to divide, distribute, allot”"),
  "the root's part of speech and meaning are realised on the top rung");
assert.ok(!bookWords.includes("starting point") && !plain(bookTop).includes("✓ the laws reproduce"),
  "the start rung no longer says the obvious 'starting point' (2026-11-08)");
assert.equal(plain(bookTop).split("bʰeh₂g").length - 1, 1,
  "the root is printed once: the record sits on the form line, not under it");
assert.ok(bookWords.includes("cognate set"), "the page says how the PIE rung was linked");
assert.ok(bookWords.includes("*bʰóh₂g-s ~ *bʰéh₂g-s"),
  "a derived PIE-stage form recorded in the cognate set is named");
assert.ok(bookWords.includes("this repo's own reconstruction"),
  "picking one alternant is declared as this repo's choice, not a record");
assert.ok(bookWords.includes("root") && bookWords.includes("to divide, distribute, allot"),
  "the root note names the root's meaning");
/* proposals/010: a set-linked word whose etymon is a root must name the root
   as a relation and start at its own recorded ancestor, not at the root. */
const lowered = Object.assign({}, book, {
  start: "gem-pro", start_name: "Proto-Germanic", start_form: "bōks",
  set_start: false, set_is_root: true,
  levels: [
    level({ stage: "gem-pro", name: "Proto-Germanic", form: "bōks", baseline: "bōks",
            status: "start", kind: "proto", evidence: "literary",
            recorded: { w: "bōks", more: [], evidence: "literary", ipa: "", reading: "",
                        show_reading: false, matches: false, same: true, pos: "noun",
                        gloss: "letter, book", origin: "ancestry", starts: true } }),
    book.levels[1],
  ],
});
const loweredWords = plain(context.renderHierarchy(lowered, { lang: "en", lang_name: "English" }));
assert.ok(loweredWords.includes("relates it to the PIE root")
          && loweredWords.includes("a relation, not an ancestor row"),
  "a root etymon is described as a relation, not an inherited ancestor");
assert.ok(loweredWords.includes("starts at the recorded") && loweredWords.includes("bōks"),
  "the page names the recorded ancestor the ladder actually starts from");
assert.ok(loweredWords.includes("to divide, distribute, allot"),
  "and still quotes the root's own recorded meaning");
assert.ok(!loweredWords.includes("The ancestor this ladder starts from is a root"),
  "the old root-is-the-start sentence must not appear when the start is a word");

const bookBottom = bookHtml.slice(bookHtml.indexOf('data-stage="en"'));
assert.ok(plain(bookBottom).includes("noun · “A collection"),
  "every rung carries the sense the dictionary records for it");
assert.ok(bookBottom.indexOf("būk") < bookBottom.indexOf(">book<")
          && bookBottom.indexOf(">book<") < bookBottom.indexOf(TAG),
  "a miss shows the record under the reconstruction, with its badge below it");

/* A rung where the two agree is printed once, glowing, with a ✓ — the
   protoword bōk of Proto-West Germanic is the case that prompted this. */
const agree = {
  start: "gem-pro", start_name: "Proto-Germanic", etymon: "bōks", root: false,
  linked_by_set: false, switched_off: 0, missing: [], total_steps: 1, earlier: [],
  exact: null,
  result: { status: "match", form: "bōk", target: "bōk", match: true,
            match_via_translit: false, ipa: "", reading: "", attested: false },
  levels: [
    level({ stage: "gem-pro", name: "Proto-Germanic", form: "bōks", baseline: "bōks",
            status: "start", kind: "proto", evidence: "literary",
            recorded: { w: "bōks", more: [], evidence: "literary", ipa: "", reading: "",
                        show_reading: false, matches: false, starts: true, same: true,
                        pos: "noun", gloss: "letter, written message", origin: "ancestry" } }),
    level({ stage: "gmw-pro", name: "Proto-West Germanic", kind: "proto", form: "bōk",
            baseline: "bōk", status: "match", evidence: "literary",
            recorded: { w: "bōk", more: [], evidence: "literary", ipa: "", reading: "",
                        show_reading: false, matches: true, same: true, pos: "noun",
                        gloss: "book", origin: "ancestry" } }),
  ],
};
const agreeHtml = context.renderHierarchy(agree, { lang: "en", lang_name: "English" });
const agreeBottom = agreeHtml.slice(agreeHtml.indexOf('data-stage="gmw-pro"'));
assert.equal(plain(agreeBottom).split("bōk").length - 1, 1, "a matching form is printed once");
assert.ok(/class="form[^"]*matched[^"]*"/.test(agreeBottom), "a matching form glows as matched");
assert.ok(agreeBottom.includes("✓"), "the match carries a ✓, not only a colour");
/* The ✓ is a disc on the corner of the word box, not a glyph in the line:
   it is the last thing inside the matched form and nothing precedes the word. */
assert.match(agreeBottom, /class="form[^"]*matched[^"]*"[^>]*>\*bōk<i class="matchdot"[^>]*>✓<\/i><\/span>/,
  "the ✓ sits on the corner of the matched word, after it");
assert.ok(!/class="tick/.test(agreeBottom), "no tick glyph standing in the line");
assert.ok(!agreeBottom.includes("rectag"), "no second copy of the same form");
const agreeTop = agreeHtml.slice(agreeHtml.indexOf('data-stage="gem-pro"'),
                                agreeHtml.indexOf('data-stage="gmw-pro"'));
assert.equal(plain(agreeTop).split("bōks").length - 1, 1, "a starting rung prints its recorded form once");
/* The first rung has no law above it, so `matches` stays false; `starts` is
   what makes it glow — it is the record the ladder starts from (2026-11-08). */
assert.match(agreeTop, /class="form[^"]*matched[^"]*"[^>]*>\*bōks<i class="matchdot"[^>]*>✓<\/i>/,
  "the starting rung glows as the record the ladder starts from");
assert.ok(agreeTop.includes("The ladder starts from this record"),
  "and its hover text says why it is lit");

/* When the cognate set names an etymon the stage's glossary does not hold, the
   rung says that plainly instead of claiming the word has no origin. */
const unrecorded = Object.assign({}, book, {
  levels: [Object.assign({}, book.levels[0], { recorded: null }), book.levels[1]],
});
const unrecordedWords = plain(context.renderHierarchy(unrecorded, { lang: "en", lang_name: "English" }));
assert.ok(unrecordedWords.includes("no form for this etymon"),
  "an etymon missing from the glossary is described as such");

/* A loanword's ancestry is off the chain (color through Latin and Old
   French): the page must not present the Germanic steps as its inheritance. */
const borrowed = context.renderHierarchy(Object.assign({}, book, {
  off_chain: [{ stage: "xno", name: "xno" }, { stage: "fro", name: "Old French" },
              { stage: "la", name: "Latin" }],
}), { lang: "en", lang_name: "English" });
const borrowedWords = plain(borrowed);
assert.ok(borrowedWords.includes("Latin, Old French"),
  "the borrowing languages are named, not a bare code");
assert.ok(borrowedWords.includes("languages outside the English chain"),
  "the page says the ancestry lies outside the chain it walks");
console.log("etymon rung ok");

/* ---------------------------------------------------------------- */
/* a word in Proto-Indo-European: one rung, and the stages below it */
/* ---------------------------------------------------------------- */
/* Proto-Indo-European has nothing above it, so its page is a ladder with one
   rung — the etymon itself — and the daughter stages stand under it as the
   next step: one click each, the same ladder every other word page draws
   (2026-11-12: no *reconstruct into* selector). The rung carries what
   the stage may be built with, so a root is a place to construct from. */
const pieLevel = (over) => Object.assign({
  stage: "ine-pro", name: "Proto-Indo-European", short: "PIE", kind: "proto",
  branch: "Indo-European", script: "reconstructed", era: [-4500, -2500],
  era_label: "c. 4500–2500 BCE", era_mid: -3500, form: "ters-", baseline: "ters-",
  changed: false, status: "start", edited: false, evidence: "literary",
  show_reading: false, form_known: true, matched_form: null, rules: [],
  formation: null, built_as: null, builds: [], built: null, transition: null,
  recorded: { w: "ters-", evidence: "literary", kind: "proto", script: "reconstructed",
              pos: "root", gloss: "dry", known: true, starts: true, sources: [], pages: [] },
}, over);
const pieRoot = {
  lang: "ine-pro", word: "ters-", start: "ine-pro", start_name: "Proto-Indo-European",
  start_variety: "", start_recorded: null, starts: [], etymon: null, etymon_record: null,
  linked_by_set: false, set_start: false, set_is_root: false, ancestry_top: null,
  off_chain: [], set_source: null, root: false, levels: [pieLevel()],
  path: [], can_extend: true, exact: null, category: null, steps_differ: [],
  mismatched_steps: [], backlog: [], earlier: [], edited: false, disabled: [],
  enabled: [], switched_off: [], pathway: null, pathway_available: false,
  target_name: "Proto-Indo-European", start_form: "ters-", hypothesis: null,
  build: null, build_at: null, build_above: null, formed: null,
  missing: [], total_steps: 0, pathways: [], stored_pathway: null,
  result: { status: "start", form: "ters-", match: false },
  next: [{ l: "iir-pro", lang_name: "Proto-Indo-Iranian", branch: "Indo-Iranian",
           era_label: "c. 2500–2000 BCE", form: "tarš", steps: 2,
           skipped: [], status: "new", recorded: null }],
  build_options: { "ine-pro": {
    stage: "ine-pro", stage_name: "Proto-Indo-European",
    suffixes: [{ id: "no", form: "-nó-", gloss: "verbal adjective or passive participle",
                 law: false, kind: "suffix" },
               { id: "os-acute", form: "-ós", gloss: "oxytone nominative",
                 law: false, kind: "ending" }],
    endings: [{ id: "-ós", form: "-ós", gloss: "thematic nominative singular", law: false }],
  } },
};
const piePage = { lang: "ine-pro", word: "ters-", is_root: true,
                  lang_name: "Proto-Indo-European" };
const pieHtml = context.renderHierarchy(pieRoot, piePage, {});
const pieWords = plain(pieHtml);
assert.ok(pieHtml.includes('data-stage="ine-pro"'), "the etymon is a rung of the timeline");
assert.ok(pieWords.includes("this word"), "and the rung says which word the page is");
assert.ok(pieWords.includes("top of the family"),
  "the family begins here, and the page says so instead of calling it a gap");
assert.ok(!pieHtml.includes("recon-lang") && !pieWords.includes("Reconstruct into"),
  "no *reconstruct into* selector: the timeline is the way down");
assert.ok(/class="nextgrid"/.test(pieHtml) && pieHtml.includes('data-next="iir-pro"'),
  "each daughter stage is a step of the timeline, one click away");
assert.ok(pieWords.includes("Proto-Indo-Iranian"), "the stage below is named where it stands");
/* The construct: the dot beside a word is a door, and the row it opens is the
   form builder — no button and no pills (2026-11-12). */
assert.ok(/class="rdot"[^>]*data-cstage="ine-pro"/.test(pieHtml)
  || /data-cstage="ine-pro"[^>]*class="rdot"/.test(pieHtml),
  "the rung's dot opens a construction row");
assert.ok(pieHtml.includes('aria-label="Construct a word from'),
  "the door says what it does, for a reader who cannot see the dot");
assert.ok(!pieWords.includes("construct…") && !pieHtml.includes("buildopen"),
  "the old button is gone");
assert.ok(!pieHtml.includes("buildchips") && !pieHtml.includes("buildpanel"),
  "and so are the pills and the typing panel");
assert.equal(typeof context.openDraft, "function", "clicking the dot opens the row");
const menu = context.draftMenu("ine-pro", pieRoot.build_options);
assert.ok(menu.includes('value="suffix:no"'), "the menu offers the recorded suffix");
assert.ok(menu.includes("verbal adjective or passive participle"),
  "with what the suffix does beside it");
assert.ok(menu.includes('value="ending:-ós"'), "and the endings under their own heading");
assert.ok(!/label="suffix"[\s\S]*value="suffix:os-acute"/.test(menu),
  "a grammatical ending is not filed as a derivational suffix");

/* A construct above the etymon: *ters- + *-nó- is *tr̥s-nó-s, and the step says
   which grade the formation puts the root in. */
const builtLevel = pieLevel({
  form: "tr̥snˈos", baseline: "tr̥snˈos",
  built: { stage: "ine-pro", kind: "suffix", form: "tr̥snˈos",
           pieces: [{ form: "ters-", word: "ters-", lang: "ine-pro",
                      lang_name: "Proto-Indo-European", gloss: "dry", pos: "root",
                      known: true, grade: "zero", grade_label: "zero grade",
                      grade_note: "*-nó- is oxytone, so the root stands in zero grade." },
                    { form: "-nó-", word: "no", lang: "ine-pro",
                      lang_name: "Proto-Indo-European",
                      gloss: "verbal adjective or passive participle",
                      pos: "suffix", known: true, affix: true }],
           steps: [], note: "A suffix is added to the word's stem." },
});
const builtPieHtml = context.renderHierarchy(
  Object.assign({}, pieRoot, { levels: [pieLevel(), builtLevel] }), piePage, {});
const builtPieWords = plain(builtPieHtml);
assert.ok(builtPieHtml.includes('class="buildstep"') || builtPieHtml.includes("BUILT HERE")
  || builtPieWords.includes("built here"), "the built rung is a step of the timeline");
assert.ok(builtPieHtml.includes("*-nó-") || builtPieHtml.includes("-nó-"),
  "the suffix that built it is printed on the step");
assert.ok(builtPieWords.includes("zero grade"),
  "the grade the formation puts the root in is stated, not left as a changed vowel");
assert.ok(builtPieHtml.indexOf("ters-") < builtPieHtml.indexOf("tr̥sn"),
  "the pieces stand above the word they build");

/* A formation may be one word, not a join: *h₂entó- is "a combining form or
   allative formation from … *h₂énts", and the step that made it is its whole
   history (2026-11-12).  The piece is a word with a construction of its
   own (*h₂ent- + *-s), which is drawn above it — so the timeline reads
   *h₂entó- → construction from *h₂énts → *h₂ent- + *-s, one rung each. */
const singlePiece = pieLevel({
  form: "h₂entó-", baseline: "h₂entó-",
  builds: [{ kind: "combining", lang: "ine-pro", lang_name: "Proto-Indo-European",
    of: "h₂entó", source: "record",
    pieces: [{ form: "*h₂énts", gloss: "forehead", pos: "noun", known: true,
      lang: "ine-pro", bound: false,
      branch: { lang: "ine-pro", lang_name: "Proto-Indo-European", short: "PIE",
        form: "*h₂énts", kind: "proto", era_label: "c. 4500–2500 BCE",
        gloss: "forehead", pos: "noun", known: true, terminal: "pie", parents: [],
        builds: [{ kind: "suffix", lang: "ine-pro",
          lang_name: "Proto-Indo-European", of: "h₂énts", source: "record",
          pieces: [
            { form: "*h₂ent-", gloss: "face", pos: "root", known: true,
              lang: "ine-pro", bound: false, branch: null },
            { form: "*s", gloss: "", pos: "", known: false, lang: "ine-pro",
              bound: true, branch: null }] }] } }] }],
});
const singleHtml = context.renderHierarchy(
  Object.assign({}, pieRoot, { levels: [singlePiece] }), piePage, {});
const singleWords = plain(singleHtml);
assert.ok(singleWords.includes("combining form"),
  "a one-word formation is named for what it is, not left as a bare word");
assert.ok(singleHtml.includes("*h₂énts"), "the word it was formed from stands on the step");
assert.ok(singleHtml.includes("*h₂ent-"),
  "and that word's own construction is drawn above it");
const singleTree = singleHtml.slice(singleHtml.indexOf('class="btrees"'));
assert.ok(singleTree.indexOf("*h₂ent-") < singleTree.indexOf("*h₂énts"),
  "oldest first: the pieces of the piece come before the formation that used it");

/* ---------------------------------------------------------------- */
/* the written form is a separate claim                              */
/* ---------------------------------------------------------------- */
/* When the writing conventions (data/spelling/) land on the recorded word,
   the last rung says so — and only then. It is a spelling, not a law, so the
   rung keeps its "differs" status and the chip is worded ("written"), never a
   second ✓ that would read as a reconstruction (2026-11-08). */
const pond = {
  lang: "en", word: "pond", disabled: [], pathways: [], stored_pathway: null,
  start: "enm", start_name: "Middle English", etymon: "pound", root: false,
  linked_by_set: false, ancestry_top: null, off_chain: [], set_source: null,
  switched_off: 0, missing: [], total_steps: 1, earlier: [], exact: null,
  result: { status: "differs", form: "pɔnd", target: "pond", match: false,
            match_via_translit: false, ipa: "pɒnd", reading: "", attested: false,
            written: "pond", written_match: true },
  levels: [
    level({ stage: "enm", name: "Middle English", era_label: "c. 1100–1500", era_mid: 1300,
            form: "pond", baseline: "pond", status: "start", evidence: "attested",
            recorded: { w: "pond", more: [], evidence: "attested", ipa: "", reading: "",
                        show_reading: false, gloss: "pond", pos: "noun" } }),
    level({ stage: "en", name: "English", era_label: "since c. 1500", era_mid: 1700,
            form: "pɔnd", baseline: "pɔnd", status: "differs", evidence: "weak",
            written: "pond", written_match: true, written_rules: 3,
            recorded: { w: "pond", more: [], evidence: "attested", ipa: "pɒnd", reading: "",
                        show_reading: false, gloss: "pond", pos: "noun" } }),
  ],
};
const pondHtml = context.renderHierarchy(pond, { lang: "en", word: "pond" });
assert.ok(pondHtml.includes("written"), "a spelling that lands must be worded on the rung");
assert.ok(/written\s*<span class="mono">pond</.test(pondHtml), "the written form itself must appear");
assert.ok(pondHtml.includes("pɔnd"),
  "the phonemic form the laws produce must stay on the rung");
assert.ok(!/class="form matched[^"]*"[^>]*>\s*<span[^>]*>pond/.test(pondHtml),
  "a spelling match must not be printed as a glowing reconstruction");
assert.ok(pondHtml.includes("data-tip"), "the written chip must explain itself on hover");
console.log("written form ok");

/* ---------------------------------------------------------------- */
/* a word's own pathway                                             */
/* ---------------------------------------------------------------- */
/* English *wolf* (2026-11-08): the last law lowers the vowel to *ɔ,
   which changes the phonological form but not the written word. The word
   records that the law never applied to it, and the page opens with that law
   switched off — named, reasoned, and reversible. */
const wolf = Object.assign({}, hierarchy, {
  switched_off: 1, disabled: ["enm~en:short_o_lowering"],
  pathway: { id: "995c741a92cb", note: "Middle English ⟨o⟩ here spells /u/, not /ɔ/.",
             created: "2026-11-08T10:51:06Z", disabled: ["enm~en:short_o_lowering"],
             references: ["carney-1994", "scragg-1974"] },
  result: { status: "match", form: "wˈolf", target: "wolf", match: true,
            match_via_translit: false, ipa: "wʊlf", reading: "", attested: true,
            written: "wolf", written_match: true },
});
const wolfHtml = context.renderHierarchy(wolf, { lang: "en", word: "wolf" });
const wolfWords = plain(wolfHtml);
assert.ok(wolfWords.includes("recorded pathway"), "the word's own pathway is named");
assert.ok(wolfHtml.includes('class="ladder-badges"') &&
  wolfHtml.indexOf(">recorded pathway<") > wolfHtml.indexOf('class="ladder-badges"'),
  "the pathway badge sits on the heading's line, not in a bar underneath");
assert.ok(!wolfWords.includes("apply the law anyway"),
  "there is no button to force the law: the switch on the law itself is the control");
assert.ok(wolfWords.includes("Middle English"), "the reason stored with it is printed");
assert.ok(wolfWords.includes("carney-1994"), "its sources are named beside it");
assert.ok(!wolfWords.includes("1 law is switched off"),
  "the pathway is explained once, not counted again as a reader's switch");
assert.ok(wolfWords.includes("exact"), "the ladder completes");
console.log("pathway ok");

/* When no pathway applies, a spelled word says so instead of reading as a
   failure: "differs — the worklist" is for a word nothing explains. */
assert.ok(pondHtml.includes("spelled"), "a written match is a claim of its own on the badge");
assert.ok(!plain(pondHtml).includes("differs — the worklist"),
  "a word the writing conventions spell is not called a worklist miss");
console.log("spelled badge ok");

/* ---------------------------------------------------------------- */
/* reading a script, and carrying the timeline on                    */
/* ---------------------------------------------------------------- */
/* 2026-11-13: 𐎺𐎼𐎣 is read vr̥kaʰ.  The laws reach *wˈarkah*, which is a
   different reading of the same signs, so the rung prints the romanisation the
   laws produce on the left and the script with its own reading and sign
   transliteration beside it — and wears no ✓, because the two are not the
   same reading.  Below the word, the direct descendants of Old
   Persian are buttons that add a rung each. */
const read = {
  start: "ine-pro", start_name: "Proto-Indo-European", etymon: "wĺ̥kʷos", root: false,
  switched_off: 0, missing: [], total_steps: 5, earlier: [], exact: null,
  path: ["pal"], can_extend: true,
  result: { status: "differs", form: "vr̥g", target: "𐎺𐎼𐎣", match: false,
            match_via_script: true, match_via_translit: false, ipa: "", reading: "",
            attested: true },
  levels: [
    level({ stage: "ipe", name: "Proto-Indo-European", short: "PIE", kind: "proto",
            era_label: "c. 4500–2500 BCE", era_mid: -3500, form: "wĺ̥kʷos", baseline: "wĺ̥kʷos",
            status: "start", evidence: "literary" }),
    level({ stage: "peo", name: "Old Persian", short: "OP", era_label: "c. 525–300 BCE",
            era_mid: -412, form: "wˈarkah", display: "", baseline: "wˈarkah", status: "differs",
            evidence: "weak",
            recorded: { w: "𐎺𐎼𐎣", more: [], evidence: "attested", ipa: "", reading: "vr̥kaʰ",
                        signs: "v-r-k", pos: "noun", gloss: "wolf", notation: "v-r-k",
                        show_reading: true, matches: false, via: null, known: true,
                        fit: { ok: true, translit: "v-r-k", logogram: false,
                               filler: [1], unwritten: ["h"] } } }),
    level({ stage: "pal", name: "Middle Persian", short: "MP", era_label: "c. 224–650",
            era_mid: 435, form: "vr̥g", baseline: "vr̥g", status: "derived", evidence: "weak",
            recorded: null }),
  ],
  next: [Object.assign(row({ l: "fa", lang_name: "Persian", branch: "Indo-Iranian (Iranian)",
                              short: "fa", era_label: "since c. 900", form: "gˈurg", steps: 2,
                              status: "match", evidence: "attested" }),
                        { recorded: { w: "گرگ", reading: "gurg", evidence: "attested" } })],
};
const readHtml = context.renderHierarchy(read, { lang: "peo", word: "𐎺𐎼𐎣", lang_name: "Old Persian" });
const readWords = plain(readHtml);
assert.ok(readWords.includes("wárkah"), "the laws' romanisation is the rung's own form");
assert.ok(readWords.includes("𐎺𐎼𐎣"), "the script the record writes is printed beside it");
assert.ok(readWords.includes("vr̥kaʰ"), "with the reading the dictionary records");
assert.ok(readWords.includes("v-r-k"), "and the sign transliteration, one letter per sign");
assert.ok(readWords.includes("noun · “wolf”"), "the rung's sub-line carries the sense");
assert.ok(!readWords.includes("read v-r-k"),
  "the rung does not explain the sign reading below a form the reader can already read");
assert.ok(!readWords.includes("the writing allows it"),
  "nor repeats that the record reads the signs another way");
assert.ok(!readWords.includes("exact, read from the script"),
  "a different reading of the same signs is not a match");
assert.ok(!readHtml.includes("matchdot"), "and it wears no ✓");
assert.ok(!readWords.includes("leaves h unwritten"),
  "what the script leaves unwritten is not explained under the transcription");
assert.ok(!readWords.includes("a vowel sign carries a bare consonant"),
  "nor is the filler-vowel convention repeated");
assert.ok(!readWords.includes("spelled v-r-k"),
  "and the spelling note is not printed under the rung either");
/* A rung whose form is the spelling itself (a word the record gives no
   ancestor for) prints its reading on the left and the script beside it. */
const scripted = {
  start: "peo", start_name: "Old Persian", etymon: null, root: false,
  switched_off: 0, missing: [], total_steps: 0, earlier: [], exact: null,
  path: [], can_extend: true,
  result: { status: "start", form: "𐎠𐎼𐎲𐎠𐎹", target: "𐎠𐎼𐎲𐎠𐎹", match: false,
            match_via_script: false, match_via_translit: false, ipa: "", reading: "Arabāya",
            attested: true },
  levels: [
    level({ stage: "peo", name: "Old Persian", short: "OP", era_label: "c. 525–300 BCE",
            era_mid: -412, form: "𐎠𐎼𐎲𐎠𐎹", display: "Arabāya", baseline: "𐎠𐎼𐎲𐎠𐎹",
            status: "start", evidence: "attested",
            recorded: { w: "𐎠𐎼𐎲𐎠𐎹", more: [], evidence: "attested", ipa: "",
                        reading: "Arabāya", signs: "a-r-b-a-y", show_reading: false,
                        matches: false, starts: true, via: null, known: true } }),
  ],
  next: [],
};
const scriptedHtml = context.renderHierarchy(scripted, { lang: "peo", word: "𐎠𐎼𐎲𐎠𐎹", lang_name: "Old Persian" });
const scriptedWords = plain(scriptedHtml);
assert.ok(scriptedWords.includes("Arabāya"), "a rung written in its own script is shown by its reading");
assert.ok(scriptedWords.includes("a-r-b-a-y"), "and the signs stand beside it");
/* 2026-11-13: the pencil seeds the form the server says the rung prints
   (`level.edit`), never the recorded writing.  Wˈarkānah is the reconstructed
   form, so the pencil must offer it even though its `ˈ` is a modifier letter;
   a rung whose own form is a writing carries its reading in `edit`.  When a
   server predates `edit`, the display or the form is still a safe fallback. */
const peoEdit = { stage: "peo", name: "Old Persian", form: "𐎺𐎼𐎣𐎠𐎴𐎡𐎹",
                  display: "Vạrkāniya", edit: "Vạrkāniya", spoken: "" };
assert.equal(context.editSeed(peoEdit), "Vạrkāniya",
  "the edit input is seeded with level.edit");
assert.ok(!/[\u{103A0}-\u{103DF}]/u.test(context.editSeed(peoEdit)),
  "the edit input never contains the language's own script");
assert.equal(context.editSeed({ ...peoEdit, form: "Wˈarkānah", display: "Vr̥kānaʰ",
                                edit: "Wˈarkānah" }), "Wárkānah",
  "the seed is the form as printed: the stress token ˈ becomes the acute (2026-11-14)");
assert.equal(context.editSeed({ ...peoEdit, edit: "", spoken: "vr̥kaʰ" }), "Vạrkāniya",
  "a server without level.edit falls back to the display");
assert.equal(context.editSeed({ ...peoEdit, edit: "", display: "", form: "Wˈarkānah" }),
  "Wárkānah", "and then to the form the rung prints");
assert.equal(context.editSeed({ ...peoEdit, edit: "drˈayah", display: "", form: "drˈayah" }),
  "dráyah", "a syllabic rung seeds the acute the page prints, not the engine token");
assert.ok(readHtml.includes('data-edit="pal"'), "a rung the timeline was carried into is editable");
assert.ok(readHtml.includes('data-cut="pal"'), "and it can be cut off again");
assert.ok(!readHtml.includes('data-cut="peo"'), "the word's own rung is not a carried one");
assert.ok(readHtml.includes('data-next="fa"'), "the direct descendants of the last rung are buttons");
/* 2026-11-08: the carry-on box carries no heading and no
   explanation — the timeline's rail runs into it, and it holds only the next
   stage's languages and the forms they would be reconstructed to. */
assert.ok(!readWords.includes("Carry Middle Persian on"), "the carry-on box has no heading text");
assert.ok(!readWords.includes("Each button is one transition"), "and no explanation");
assert.ok(/<li class="rung nextrung">/.test(readHtml), "the box is the next rung of the timeline");
assert.ok(readHtml.indexOf("nextrung") < readHtml.indexOf("</ol>"),
  "it sits inside the timeline list, under the last rung");
assert.ok(readWords.includes("Persian") && readWords.includes("since c. 900"),
  "each button names the language and its era");
assert.ok(readHtml.includes("✓"), "a child that reaches a record says so on its button");
/* 2026-11-11: a rung whose form is a writing with no reading recorded cannot
   be derived at all. The page says that in words — it does not print the
   script again below and call the word unreached. */
const unread = Object.assign({}, read, {
  levels: [Object.assign({}, read.levels[0], {
    transition: { from: "peo", to: "pal", missing: false, unreadable: true,
                  fired: 0, silent: 0, switched_off: 0 },
    rules: [], status: "differs",
  })],
});
const unreadWords = plain(context.renderHierarchy(unread, { lang: "peo", word: "𐎼𐎢𐎨" }));
assert.ok(unreadWords.includes("no reading is recorded"),
  "a rung the laws cannot start from says why");
assert.ok(unreadWords.includes("they rewrite sounds, never signs"),
  "and states the reason the engine refused it");
const plainNext = context.renderHierarchy(Object.assign({}, read, { next: [], path: [], can_extend: false }),
                                          { lang: "peo", word: "𐎺𐎼𐎣" });
assert.ok(!plainNext.includes("nextgrid"), "a language with no modelled children shows no buttons");
/* 2026-11-08: the coverage page printed the law cell's markup as
   text — `<span class="rid mono">final_z_loss</span> …` — because the markup
   was handed to `lawLink`, which escapes what it is given. */
const covCell = context.lawCell({ id: "final_z_loss", name: "Word-final *-z is lost",
                                  from: "gmw-pro", to: "ang" });
assert.ok(covCell.includes('<span class="rid mono">final_z_loss</span>'),
  "the coverage cell is markup, not escaped markup");
assert.ok(!covCell.includes("&lt;span"), "and no tag is printed as text");
assert.ok(covCell.includes('href="#/rule/gmw-pro~ang%3Afinal_z_loss"'), "the cell opens the law");
console.log("script reading and timeline ok");


/* A construction is one tree in the timeline, not a line under the word and
   not a set of inset pictures (2026-11-12): a diamond sits on the main
   rail, a 2px line leaves it to the right and touches `𐎨𐎡𐏂 čiçaʰ`, then
   `+`, then `*farnah`; above each piece its own timeline rises, drawn exactly
   like the ladder below — same rail, same language-and-years column on the
   left, same type size — and a piece is never labelled with its own language,
   because it is a word of the stage the step belongs to.  This is the reader's
   own example page, peo/Ciçafarnāh. */
const origin = (over) => Object.assign({ kind: "attested", lang: "peo",
  lang_name: "Old Persian", short: "OP", form: "", rel: "", known: true,
  gloss: "", reading: "", era_label: "c. 525–300 BCE", terminal: "", parents: [] }, over);
const buildOf = (pieces, over) => Object.assign({ kind: "affix", lang: "peo",
  lang_name: "Old Persian", of: "Ciçafarnāh", source: "record", pieces }, over);
const caus = buildOf([
  { form: "𐎨𐎡𐏂", gloss: "shining; appearance; lineage", reading: "čiçaʰ", known: true,
    lang: "peo", bound: false, branch: origin({ form: "𐎨𐎡𐏂", reading: "čiçaʰ",
      gloss: "shining; appearance; lineage", parents: [origin({
        lang: "ira-pro", lang_name: "Proto-Iranian", short: "PIr.", form: "*čiθráh",
        kind: "proto", era_label: "c. 2000–1000 BCE", pos: "adj",
        rel: "inherit", gloss: "visible", parents: [origin({
          lang: "iir-pro", lang_name: "Proto-Indo-Iranian", short: "PIIr.",
          kind: "proto", era_label: "c. 2500–2000 BCE",
          form: "*čitrás", rel: "inherit", parents: [origin({
            lang: "ine-pro", lang_name: "Proto-Indo-European", short: "PIE",
            kind: "proto", era_label: "c. 4500–2500 BCE",
            form: "*kit-ró-s", rel: "inherit", known: false,
            terminal: "pie" })] })] })] }) },
  { form: "*farnah", gloss: "glory", reading: "", known: true, lang: "peo", bound: false,
    branch: origin({ form: "*farnah", gloss: "glory", parents: [origin({
      lang: "xme-old", lang_name: "Old Median", short: "OMed.", form: "*farnah",
      era_label: "c. 700–300 BCE",
      rel: "borrow", known: false, terminal: "borrowed" })] }) },
], { of: "Ciçafarnāh" });
const causLevel = {
  form: "Ciçafarnāh", stage: "peo", name: "Old Persian",
  built_as: caus, builds: [caus],
};
const builtHtml = context.constructStep(causLevel, 0,
  (stage, w, known) => `#/word/${stage}/${encodeURIComponent(w)}`);
const builtText = plain(builtHtml);
/* The step's blocks, so an assertion can say what is inside one of them. */
const chunk = (html, cls) => (html.match(new RegExp(`<div class="${cls}[^"]*"[\\s\\S]*?<\\/div>`, "g")) || []);
/* One column, from its own div to the next: a column nests rows inside rows, so
   a regex that stopped at the first `</div>` would cut it short. */
const columns = (html) => html.split('<div class="cpiece').slice(1);
const terms = chunk(builtHtml, "cterm");
assert.ok(builtHtml.includes('class="constructstep"'), "the construction is a ladder step");
assert.ok(!builtHtml.includes('<div class="rail" aria-hidden="true"><i class="cdiamond"></i></div>'),
  "the mark stands in the tree, not on a block of its own");
assert.ok(!builtText.includes("CONSTRUCTION"), "no CONSTRUCTION line under the word any more");
assert.ok(builtText.includes("construction"),
  "the diamond's row says what it is — the word stands beside the diamond, not under the tree");
/* One tree: the first word stands immediately right of the diamond — the
   diamond is its mark, so no wire and no second dot sit between them — and the
   line leaves the word's own right edge for `+` and the next piece
   (2026-11-12). */
assert.equal((builtHtml.match(/class="btree"/g) || []).length, 1, "one construction is one tree");
assert.ok(!builtHtml.includes('class="bnode') && !builtHtml.includes('class="bcol'),
  "no inset columns survive: nothing is drawn in a thinner sub-timeline");
assert.equal(terms.length, 2, "both pieces stand on the tree's own line");
assert.equal((builtHtml.match(/class="cplus"/g) || []).length, 1, "one + between two pieces");
assert.ok(!builtHtml.includes('class="cwire"'),
  "no redundant wire: the first word starts at the diamond");
assert.ok(/class="cterm first"/.test(terms[0]),
  "the first piece is the one the diamond marks");
assert.ok(terms[0].includes('class="crail mark"') && terms[0].includes('<i class="cdiamond"></i>'),
  "the first piece's own rail carries the step's diamond, on the pieces' line");
assert.ok(/class="cterm[^"]*"[^>]*>\s*<span class="cwhen lead"><\/span><span class="crail" aria-hidden="true"><i><\/i><\/span>/
  .test(terms[1]),
  "the next piece is met by an empty label cell, then the rail and the dot of its own column");
assert.ok(!/class="cterm[^"]*"[^>]*>\s*<span class="cwhen"><span class="cwhen-name/.test(terms[1]),
  "a later piece carries no language of its own: it is a word of the step's stage");
assert.ok(builtHtml.indexOf('class="cterm first"') < builtHtml.indexOf(">+<"),
  "the + comes after the first word, from its right side");
assert.ok(builtHtml.indexOf(">+<") < builtHtml.indexOf('class="cplus"', builtHtml.indexOf(">+<")) + 1
  || builtHtml.indexOf(">+<") > builtHtml.indexOf('class="cterm first"'),
  "the + sits between the two pieces");
/* The pieces are words, not labels: word size, no language of their own. */
assert.ok(terms[0].includes('class="cform term'), "a piece is written at word size");
assert.ok(!terms[0].includes("Old Persian") && !terms[1].includes("Old Persian"),
  "a piece is not labelled with the language of the step: it is a word of it");
/* The first word's row is the diamond's row, so its left column says what the
   diamond marks — the formation — on the diamond's own line, not under the
   tree (2026-11-12: "the word construction ... should be next to the
   diamond not below it"). */
assert.ok(/class="cwhen"><span class="cwhen-name cwhen-build">construction<\/span><span class="cwhen-era">affix<\/span>/
  .test(terms[0]),
  "the diamond's own row names the construction and the kind of formation, in its left column");
assert.ok(!builtHtml.includes('class="when"'),
  "the step prints no label of its own under the tree any more");
assert.ok(terms[0].includes('<span class="creadstack"><i class="cread">čiçaʰ</i></span>'),
  "the piece's reading is stacked under it, not printed beside it");
assert.ok(!terms[0].split('<span class="creadstack">')[0].includes('<i class="cread"'),
  "no reading layer stands inside the word row");
/* The meaning stands under the word, the way the headword's own line carries
   it — `name · “a male given name”` — and the hover still says where it opens
   (2026-11-12). */
assert.ok(terms[0].includes('<span class="cgloss">“shining; appearance; lineage”</span>'),
  "the piece's meaning is written under it, not left on hover");
assert.ok(terms[1].includes('<span class="cgloss">“glory”</span>'),
  "every piece of the line carries its meaning");
assert.ok(terms[0].includes('<span class="cwordrow">'),
  "the word keeps its own band on the line, with the meaning beneath it");
assert.ok(terms[0].includes("data-tip=\"“shining; appearance; lineage” — open the word page\""),
  "the first piece's meaning is on hover, with the page it opens");
assert.ok(terms[0].includes('href="#/word/peo/%F0%90%8E%A8%F0%90%8E%A1%F0%90%8F%82"'),
  "the first piece opens its own word page");
assert.ok(terms[1].includes('href="#/word/peo/*farnah"'), "the second piece too");
assert.ok(builtHtml.includes('href="#/word/ira-pro/*%C4%8Di%CE%B8r%C3%A1h"'),
  "each piece's ancestors are doors of their own");
/* Every piece climbs its own column, one step per row, oldest at the top, and
   every row is one step high — so two words of the same stage land on one
   horizontal line (2026-11-12).  The first piece's descent is no longer
   a set of ladder rungs above the step: it is the same kind of row as the
   donor's, because it has to line up with it. */
const cols = columns(builtHtml);
assert.equal(cols.length, 2, "one column per piece");
const rowCount = (html) => (html.match(/<div class="cnode[^"]*"/g) || []).length;
assert.equal(rowCount(cols[0]), 3,
  "𐎨𐎡𐏂 climbs three steps: Proto-Iranian, Proto-Indo-Iranian, Proto-Indo-European");
assert.equal(rowCount(cols[1]), 1, "the borrowed word's donor stands in its own column");
assert.ok(cols[0].indexOf("Proto-Indo-European") < cols[0].indexOf("Proto-Indo-Iranian")
  && cols[0].indexOf("Proto-Indo-Iranian") < cols[0].indexOf("Proto-Iranian"),
  "oldest first: a column is read from the top down to the piece");
/* The stage stands to the left of the word, with its years under it, exactly
   as a rung of the timeline writes it (2026-11-12: "the language names
   should be shown to the left along with the est. dates").  A short code
   beside the word is not a label and does not replace the column. */
assert.ok(cols[0].includes('<span class="cwhen"><span class="cwhen-name kind-proto">Proto-Indo-European</span><span class="cwhen-era">c. 4500–2500 BCE</span></span>'),
  "an ancestor names its language in full and dates it, in the row's left column");
assert.ok(cols[1].includes('class="cwhen-name kind-attested">Old Median<'),
  "and a donor stage keeps the attested colour the ladder gives it");
assert.ok(!builtHtml.includes('class="cstage'),
  "no stage code is written beside the word any more");
assert.ok(cols[1].includes("Old Median *farnah — the record says the word was borrowed from here"),
  "a borrowed donor ends the other trunk and says so");
assert.ok(cols[0].includes("c. 4500–2500 BCE"),
  "the years it was in use are on the row's hover");
/* Proto-Indo-European is the top of the family, not an unexplained form: the
   climb ends there without a ??? (2026-11-12). */
assert.ok(cols[0].includes("*kit-ró-s"), "the climb ends at a Proto-Indo-European word");
assert.ok(cols[0].includes("the top of the family"), "and says that it is the end of the trail");
assert.ok(!builtHtml.includes("cunknown"), "nothing in this tree is unexplained");
assert.ok(cols[0].includes('<span class="cwhen"><span class="cwhen-name kind-proto">Proto-Indo-European<\/span>'),
  "the language stands in the left column, not beside the word");
/* Every word of the timeline says what it means, ancestors included (
   2026-11-12): the row above a construction carries its dictionary sense the
   way the headword's own line carries its own. */
assert.ok(cols[0].includes('<span class="cgloss">adj · “visible”</span>'),
  "an ancestor prints the category and the sense under its word");

/* The reader's own example (2026-11-12): *anda- climbs *h₂entó- →
   "construction from *h₂énts" → "*h₂ent- + *-s", while *swarō climbs to
   *swer-.  *h₂entó- and *swer- are both Proto-Indo-European, so they must
   stand on one horizontal line — each is the row immediately above its own
   piece, and every column's rows share one height, so a column with three
   ancestors rises three equal rows above the two-row column beside it. */
const pieWord = (form, over) => origin(Object.assign({ lang: "ine-pro",
  lang_name: "Proto-Indo-European", short: "PIE", kind: "proto",
  era_label: "c. 4500–2500 BCE", form, terminal: "pie", parents: [] }, over));
const h2ento = pieWord("h₂entó-", { gloss: "against", pos: "combining form",
  built_as: singlePiece.builds[0], builds: singlePiece.builds });
const alignPieces = [
  { form: "*anda-", gloss: "facing", pos: "prefix", reading: "", known: true,
    lang: "gem-pro", bound: false, branch: origin({ lang: "gem-pro",
      lang_name: "Proto-Germanic", short: "PGmc.", kind: "proto", form: "*anda-",
      gloss: "facing", pos: "prefix", parents: [h2ento] }) },
  { form: "*swarō", gloss: "oath", pos: "noun", reading: "", known: true,
    lang: "gem-pro", bound: false, branch: origin({ lang: "gem-pro",
      lang_name: "Proto-Germanic", short: "PGmc.", kind: "proto", form: "*swarō",
      gloss: "oath", pos: "noun",
      parents: [pieWord("swer-", { gloss: "to ache", pos: "root" })] }) },
];
const alignBuild = buildOf(alignPieces, { lang: "gem-pro",
  lang_name: "Proto-Germanic", of: "andaswarō" });
const alignHtml = context.constructStep({ form: "andaswarō", stage: "gem-pro",
  name: "Proto-Germanic", kind: "proto", built_as: alignBuild, builds: [alignBuild] },
  0, (stage, w) => `#/word/${stage}/${encodeURIComponent(w)}`);
const alignCols = columns(alignHtml);
assert.equal(alignCols.length, 2, "two pieces, two columns");
/* Oldest first in each column, and the shared stage last — the row next to the
   piece line. */
const chainRows = (col) => col.split(/<div class="(?:cnode|cbuild)/).slice(1);
assert.equal(chainRows(alignCols[0]).length, 3,
  "*anda-'s column climbs three rows: two formations, then *h₂entó-");
assert.equal((alignCols[0].match(/class="cbuild"/g) || []).length, 2,
  "two of those rows are constructions of their own");
/* Every diamond of the climb says what it is, on its own line: the label used
   to be printed once, under the tree, so only the last construction carried it
   (2026-11-12: "it should show it for all of the constructions, and it
   should be next to the diamond not below it"). */
const cbuildRows = alignCols[0].split('<div class="cbuild').slice(1);
assert.equal(cbuildRows.length, 2, "two built rows to label");
assert.ok(cbuildRows.every((row) => /^[^>]*>\s*<span class="cwhen"><span class="cwhen-name cwhen-build">construction<\/span>/.test(row)),
  "each built row names its construction in the left column, before its diamond");
assert.ok(cbuildRows.every((row) => row.indexOf("cwhen-build") < row.indexOf("cdiamond")),
  "and the label stands beside the diamond, not under the tree");
assert.ok(alignCols[0].includes('<span class="cwhen-name cwhen-build">construction</span><span class="cwhen-era">combining form</span>'),
  "the kind of formation the record states is under the word construction");
assert.ok(!/class="cwhen-name cwhen-build">construction<\/span><span class="cwhen-era">[^<]*Old Persian/.test(alignCols[0]),
  "a construction is never labelled with the language of its pieces");
assert.equal(chainRows(alignCols[1]).length, 1, "*swarō's column climbs one row");
assert.ok(chainRows(alignCols[0]).slice(-1)[0].includes("*h₂entó-"),
  "*h₂entó- is the last row of its column, the one next to *anda-");
assert.ok(chainRows(alignCols[1]).slice(-1)[0].includes("*swer-"),
  "*swer- is the last row of its column, the one next to *swarō");
assert.ok(chainRows(alignCols[0]).slice(-1)[0].includes(">Proto-Indo-European<")
  && chainRows(alignCols[1]).slice(-1)[0].includes(">Proto-Indo-European<"),
  "both name Proto-Indo-European in the left column, and so they are read on one line");
assert.ok(alignCols[0].indexOf("*h₂ent-") < alignCols[0].indexOf("*h₂énts")
  && alignCols[0].indexOf('class="cbuild"') < alignCols[0].indexOf("*h₂entó-"),
  "the climb above *anda- reads *h₂ent- + *-s, then *h₂énts, then *h₂entó-");
/* The one height and the bottom anchor are the sheet's job, and they are the
   whole of the invariant: every row is `--crow` tall, and a column hangs from
   the piece line rather than from the top of the tree. */
const sheet = fs.readFileSync(path.join(WEB, "style.css"), "utf8");
assert.ok(/\.cnode, \.cbuild, \.cterm \{[^}]*height: var\(--crow\)/.test(sheet),
  "one row height for an ancestor, a built ancestor and the piece");
assert.ok(/\.bline \{[^}]*align-items: flex-end/.test(sheet),
  "the columns are anchored at the pieces' own line");
assert.ok(/\.cpiece \{[^}]*justify-content: flex-end/.test(sheet),
  "and a column hangs from its bottom, whatever stands above it");
/* The spine is one unbroken line from the oldest form of the tree to the word
   the step builds.  It is drawn in segments that have to meet: the rail above
   the tree, the first column's own lead and rows *inside* the tree's scroll
   box (so the line scrolls with the word it belongs to), the first piece's
   mark, and the rail under the tree that carries it over the meaning strip to
   the rung below.  v0.17.10 blanked the mark's track and hid the step rail
   outright on a step with nothing above it, so *andaswarō lost the line from
   the diamond above *anda- down to its own rung (2026-11-12: "the line
   on the left has disappeared"). */
assert.ok(!/\.crail\.mark::before[^{]*\{[^}]*display: none/.test(sheet),
  "the mark keeps the line coming down from the row above: the diamond stands on the spine");
assert.ok(/\.cterm > \.crail\.mark::after \{[^}]*display: none/.test(sheet),
  "only the sideways stub into the word is dropped — the word stands at the diamond");
assert.ok(/\.cpiece\.first > \.cterm > \.crail::before \{[^}]*bottom: 0/.test(sheet),
  "the first piece's mark runs down to the bottom of its own row");
assert.ok(/\.constructstep \.rail\.top::before \{[^}]*top: calc\(-1 \* var\(--gap, 0px\) - 12px\)/.test(sheet),
  "the rail above the tree starts at the rung it comes from");
assert.ok(/\.constructstep \.rail\.foot \{[^}]*height: calc\(var\(--bpad\) \+ var\(--sbar\)\)/.test(sheet)
  && /\.constructstep \.rail\.foot::before \{[^}]*top: 0; bottom: 0/.test(sheet),
  "the rail under the tree always carries the line across the meaning strip to its rung");
assert.ok(/\.constructstep:first-child \.rail\.top::before \{[^}]*display: none/.test(sheet),
  "with nothing above it only that upper segment goes: the lower one is never hidden");
assert.ok(/\.clead > \.crail::before \{[^}]*top: 0; bottom: 0/.test(sheet),
  "the first column brings the line down from the tree's top to its oldest row");
assert.ok(/\.constructstep:first-child \.cpiece\.first:has\(> \.cchain > \.cnode\.unknown:first-child\) > \.clead > \.crail::before \{[^}]*display: none/
    .test(sheet),
  "and hangs no line over a ??? that has nothing above it");
assert.ok(/\.clead \{[^}]*flex: 1 1 auto/.test(sheet),
  "and what is left of the column above its rows is that lead");
/* The left column of the climb is the ladder's own: 156px, a 14px gap, a 20px
   rail track — so the first piece's rail is the step's rail and a word of the
   climb begins where every rung's word begins (2026-11-12). */
assert.ok(/\.cnode, \.cbuild, \.cterm \{[^}]*grid-template-columns: var\(--clabel\) var\(--crail\) auto/.test(sheet),
  "every row of the climb is label | rail | word");
assert.ok(/\.constructstep \{[^}]*--clabel: 156px; --crail: 20px/.test(sheet),
  "the label column and the rail track are the ladder's own two widths");
assert.ok(/\.constructstep \{[^}]*grid-template-columns: 156px 20px minmax\(0, 1fr\)/.test(sheet),
  "the step keeps the ladder's own tracks, so the tab row and the word land where a rung's do");
assert.ok(/\.bstep-tabs \{[^}]*grid-column: 3/.test(sheet),
  "and the analyses' tabs stand in the word's column");
assert.ok(/\.cwhen \{[^}]*align-items: flex-end[^}]*height: var\(--termh\)/.test(sheet),
  "the label is right-aligned against the rail and centred on the word's own band");
assert.ok(/\.cwordrow \{[^}]*height: var\(--termh\)/.test(sheet),
  "the word keeps its term band, so the pieces stay centred on the rail");
assert.ok(/\.creadstack \{[^}]*flex-direction: column/.test(sheet),
  "the reading and sign layers stack vertically under the word");
assert.ok(/\.creadstack \.cread \{[^}]*display: block; margin-left: 0/.test(sheet),
  "each layer takes its own line, flush under the word");
assert.ok(/\.cwhen-name \{[^}]*font-size: 13px/.test(sheet)
  && /\.cwhen-era \{[^}]*font-size: 11\.5px/.test(sheet),
  "and it is set at the ladder's own sizes, name over years");
assert.ok(!/\.cstage/.test(sheet), "the short stage code beside a word is gone for good");
assert.ok(/\.btrees \{[^}]*padding: var\(--treegap, 6px\) 2px var\(--bpad\) 0/.test(sheet),
  "the tree starts at the page's own left edge, so its first column is the label column");
assert.ok(/\.cterm > \.cwhen\.lead::before \{[^}]*top: calc\(var\(--termh\) \/ 2 - 1px\)/.test(sheet),
  "an unlabelled row keeps the line from the + to its dot unbroken");
/* The `+` is a row of the staircase like any other cell, but its content is
   the *term* band, the 46px a word stands in — otherwise centring it in a
   90px cell put it (and its two stubs) half a meaning-line under the words
   either side (2026-11-12: "the line around the + is shifted"). */
/* The timeline ends in a circle and the line to the picker leaves that circle:
   the rail's centre, the circle's centre and the horizontal line are one
   point, and the line starts at the circle's own right edge (
   2026-11-12: "the line isn't connected to the white circle"). */
const circle = sheet.match(/\.nextrung \.rail i \{ top: (\d+)px; \}/);
const junction = sheet.match(/\.nextrung \.rail::after \{[^}]*top: (\d+)px;[^}]*left: calc\(50% \+ (\d+)px\)/);
assert.ok(circle && junction, "the end circle and the line to the picker are both in the sheet");
assert.equal(Number(circle[1]) + 5, Number(junction[1]) + 1,
  "the circle is centred on the line: its 10px box hangs 5px above the top of a 2px line");
assert.equal(Number(junction[2]), 5,
  "and the line starts at the circle's right edge, not inside it");
/* The closing circle is also the ladder's last rung, so
   `.rung:last-child .rail::before { height: 14px }` ties on specificity with a
   plain `.nextrung .rail::before` — and wins on order, because it is written
   earlier in the sheet.  The rail has to be written as `.rung.nextrung` (same
   specificity, later) or the line stops at the top of the rail box, 7px above
   the ring (measured on the page, 2026-11-12). */
const endRail = sheet.match(/\.rung\.nextrung \.rail::before \{[^}]*height: calc\(var\(--gap, 14px\) \+ 12px\)/);
assert.ok(endRail, "the end rail is written as .rung.nextrung, so last-child's 14px cannot cut it");
assert.ok(sheet.indexOf(".rung.nextrung .rail::before") > sheet.indexOf(".rung:last-child .rail::before"),
  "and it is written after the last-rung rule that used to win");
assert.equal(Number(circle[1]) + 5, 12,
  "the ring's centre is 12px below the rail's top, where the rail's line now ends");
assert.ok(/\.cplus \{[^}]*padding-bottom: calc\(var\(--crow\) - var\(--clabelh\) - var\(--termh\)\)/.test(sheet),
  "the + and its stubs are centred on the words' own line, not on the meaning row");
assert.ok(!/\.cplus \{[^}]*padding-bottom: var\(--foot\)/.test(sheet),
  "and not on the meaning strip under it");
/* The tree is the step's last row: the horizontal line sits above the word it
   builds, so where the step ends is where its spine has to be measured from. */
const bodyHtml = builtHtml.slice(builtHtml.indexOf('class="btrees"'));
assert.ok(!builtHtml.includes('class="steprow"'),
  "nothing but the tree stands in the step: the card that repeated its pieces is gone");
assert.ok(bodyHtml.trim().endsWith('</li>'),
  "the tree closes the step, so the spine is the step's own bottom");
assert.ok(builtHtml.indexOf('class="btrees"') < builtHtml.indexOf('rail foot'),
  "and the rail under the tree comes after it, never through it");
assert.ok(/class="bstep-radio"[\s\S]*class="btrees"/.test(builtHtml)
  || !builtHtml.includes('class="bstep-radio"'),
  "the tab radios stay the tree's own siblings: the CSS switches the tree without script");

/* Every word of a reconstructed stage carries its stage's star, wherever the
   page prints it (2026-11-12).  The reader's example was *anda-
   "facing" in the construction of *andaswarō: the piece linked to
   /gem-pro/*anda- while the timeline drew it bare, because each renderer
   tested for the asterisk itself.  One test now answers for all of them. */
const andaBuild = buildOf([
  { form: "*anda-", gloss: "facing", pos: "prefix", reading: "", known: true,
    lang: "gem-pro", bound: false, branch: origin({ lang: "gem-pro",
      lang_name: "Proto-Germanic", short: "PGmc.", form: "*anda-", kind: "proto",
      gloss: "facing", pos: "prefix", era_label: "c. 500 BCE – 1 CE",
      terminal: "end", parents: [] }) },
  /* written without a star on purpose: the record's spelling is not the
     renderer's job, and a stage that reconstructs its words writes one. */
  { form: "swarō", gloss: "oath", pos: "noun", reading: "", known: true,
    lang: "gem-pro", bound: false, branch: origin({ lang: "gem-pro",
      lang_name: "Proto-Germanic", short: "PGmc.", form: "*swarō", kind: "proto",
      gloss: "oath", pos: "noun", era_label: "c. 500 BCE – 1 CE",
      terminal: "end", parents: [] }) },
], { lang: "gem-pro", lang_name: "Proto-Germanic", of: "andaswarō" });
const andaLevel = { form: "andaswarō", stage: "gem-pro", name: "Proto-Germanic",
  kind: "proto", built_as: andaBuild, builds: [andaBuild] };
const andaHtml = context.constructStep(andaLevel, 0,
  (stage, w) => `#/word/${stage}/${encodeURIComponent(w)}`);
const andaText = plain(andaHtml);
assert.ok(andaText.includes("*anda-") && andaText.includes("*swarō"),
  "both pieces of a proto construction are written as the stage writes them");
assert.ok(!/(^|\s)anda-(?=\s|$)/.test(andaText), "no piece of a reconstructed stage is printed bare");
assert.ok(!/(^|\s)swarō(?=\s|$)/.test(andaText), "a piece the record spells without a star still gets one");
assert.ok(andaHtml.includes('href="#/word/gem-pro/*anda-"'),
  "the door keeps the record's own spelling of the piece");

/* "Words built on it" is a list of that stage's words, so a proto stage's list
   carries the asterisks as well. */
const builtList = context.renderBuiltFrom({ lang: "gem-pro", kind: "proto",
  lang_name: "Proto-Germanic", built_from: [
    { word: "swarō", pos: "noun", gloss: "oath", suffixes: [] },
  ] });
assert.ok(plain(builtList).includes("*swarō"), "a word built at a proto stage is starred");

/* A word of a family language whose record states no origin hangs under a ???
   — it may have come from somewhere, and where is not known.  A bound morpheme
   is not a word and gets no trunk of its own; a word of a language outside the
   family begins its own trail. */
const unknownPiece = buildOf([
  { form: "𐎨𐎡𐏂", gloss: "", reading: "čiçaʰ", known: true, lang: "peo", bound: false,
    branch: origin({ form: "𐎨𐎡𐏂", terminal: "end", parents: [] }) },
  { form: "ـدار", gloss: "", reading: "", known: false, lang: "fa", bound: true,
    branch: null },
], { kind: "affix", of: "Ciçafarnāh" });
const unknownHtml = context.constructStep(Object.assign({}, causLevel,
  { built_as: unknownPiece, builds: [unknownPiece] }), 0, () => "#/x");
assert.ok(unknownHtml.includes('<span class="cunknown">???</span>'),
  "an ancestor whose origin is not recorded ends in a ???");
assert.ok(/<div class="cnode unknown">\s*<span class="cwhen"><\/span>\s*<span class="crail"/.test(unknownHtml),
  "a ??? row keeps an empty label cell: nothing says which stage it is of");
assert.equal((unknownHtml.match(/class="cunknown"/g) || []).length, 1,
  "and only a word gets one: a bound morpheme has no line above it");
assert.ok(unknownHtml.includes("No record says where this word came from"),
  "and the ??? says what it means");
assert.ok(unknownHtml.includes("a bound morpheme with no entry of its own"),
  "a bound morpheme is drawn as itself, with no trunk");
assert.ok(!unknownHtml.includes('href="#/x"><span'), 
  "and it opens no page when the stage holds no affix entry for it");
/* A bound morpheme has no word's sense, so its gloss is a description of what
   it does; it is printed as that description rather than quoted as a meaning
   (2026-11-12). */
const suffixPiece = buildOf([
  { form: "*keyt-", gloss: "to shine, glow", pos: "root", reading: "", known: true,
    lang: "ine-pro", bound: false, branch: null },
  { form: "*-rós", gloss: "Forms adjectives from Caland system roots", pos: "suffix",
    reading: "", known: true, lang: "ine-pro", bound: true, branch: null },
]);
const suffixHtml = context.constructStep(Object.assign({}, causLevel,
  { built_as: suffixPiece, builds: [suffixPiece] }), 0, () => "#/x");
assert.ok(suffixHtml.includes('<span class="cgloss">Forms adjectives from Caland system roots</span>'),
  "a suffix says what it does under itself, unquoted");
assert.ok(suffixHtml.includes('href="#/x"'),
  "a suffix the stage's glossary holds as an affix opens its own page (2026-11-13)");
assert.ok(suffixHtml.includes('<span class="cgloss">“to shine, glow”</span>'),
  "a root's sense is quoted, and a root names no category it has not got");
assert.ok(!columns(unknownHtml)[1].includes("has-chain"),
  "the bound piece keeps no climb of its own");
/* A dot marks a word whose own line continues above it.  A bound morpheme has
   no line above it, so it wears none — the line reaches it from the `+` and
   stops.  Its cell still holds the rail column, or the word would slide into
   the 18px track and off the shared line (2026-11-12). */
const dots = (html) => (html.match(/class="crail" aria-hidden="true"><i><\/i><\/span>/g) || []).length;
assert.equal(dots(suffixHtml), 0, "no dot is drawn before a suffix");
assert.ok(suffixHtml.includes('<span class="crail blank" aria-hidden="true"></span>'),
  "the suffix's cell keeps the rail column, empty");
assert.equal(dots(chunk(builtHtml, "cterm").join("")), 1,
  "only the piece with a line above it wears the dot, not the one the line ends on");
/* A suffix's gloss is a sentence, not a word: it is neither cut short nor
   forced onto one line that runs into the next piece (2026-11-12). */
const longSuffix = buildOf([
  { form: "*sekʷ-", gloss: "to follow", pos: "root", reading: "", known: true,
    lang: "ine-pro", bound: false, branch: null },
  { form: "*-éh₂", pos: "suffix", known: true, lang: "ine-pro", bound: true, branch: null,
    gloss: "Creates collective nouns and mass nouns, corresponding to thematic "
      + "formations with accent on the suffix." },
]);
const longHtml = context.constructStep(Object.assign({}, causLevel,
  { built_as: longSuffix, builds: [longSuffix] }), 0, () => "#/x");
assert.ok(longHtml.includes("accent on the suffix"), "the whole of a long gloss is in the markup");
assert.ok(!longHtml.includes("…"), "and none of it is replaced by an ellipsis");

/* A root that stands in another grade in this formation says so beside itself
   and carries the handbook's reason on its hover — *ters- above *tr̥s-tó-s
   (2026-11-12, on why the *-e- becomes *r̥). */
const gradedPiece = buildOf([
  { form: "*ters-", gloss: "dry", pos: "root", reading: "", known: true,
    lang: "ine-pro", bound: false, branch: null, grade: "zero",
    grade_label: "zero grade",
    grade_note: "The *-tó- verbal adjective is oxytone, so the root stands in zero grade." },
  { form: "*-tós", gloss: "verbal adjective", pos: "suffix", reading: "", known: true,
    lang: "ine-pro", bound: true, branch: null },
]);
const gradedHtml = context.constructStep(Object.assign({}, causLevel,
  { built_as: gradedPiece, builds: [gradedPiece] }), 0, () => "#/x");
assert.ok(gradedHtml.includes('<span class="cgrade" data-tip="The *-tó- verbal adjective is oxytone, so the root stands in zero grade.">zero grade</span>'),
  "the root's grade stands beside it, with the reason on hover");
assert.equal((gradedHtml.match(/class="cgrade"/g) || []).length, 1,
  "and only the root is graded, not the suffix that selects the grade");

/* A word in the chain that was itself built keeps its construction above it —
   *kit-ró-s is *keyt- + *-rós — in the same grammar, one size down: the
   diamond, the first piece beside it, the line, the `+`, the rest (
   2026-11-12: keep going up and up).  The peo page used to stop at the word
   because the row lives in *čitrás's article, not in an article for *kit-ró-s. */
const kitros = {
  kind: "affix", lang: "ine-pro", lang_name: "Proto-Indo-European",
  of: "kit-ró-s", source: "record",
  pieces: [
    { form: "*keyt-", gloss: "to shine, glow", reading: "", known: true,
      lang: "ine-pro", bound: false, branch: null },
    { form: "*-rós", gloss: "", reading: "", known: false,
      lang: "ine-pro", bound: true, branch: null },
  ],
};
const nestedLevel = Object.assign({}, causLevel, {
  built_as: buildOf([
    { form: "𐎨𐎡𐏂", gloss: "", reading: "čiçaʰ", known: true, lang: "peo", bound: false,
      branch: origin({ form: "𐎨𐎡𐏂", parents: [origin({
        lang: "ira-pro", lang_name: "Proto-Iranian", kind: "proto", form: "*čiθráh",
        parents: [origin({ lang: "iir-pro", lang_name: "Proto-Indo-Iranian",
          kind: "proto", form: "*čitrás", parents: [origin({
            lang: "ine-pro", lang_name: "Proto-Indo-European", kind: "proto",
            form: "*kit-ró-s", terminal: "pie", known: false,
            builds: [kitros], built_as: kitros })] })] })] }) },
    { form: "*farnah", gloss: "glory", reading: "", known: true, lang: "peo",
      bound: false, branch: null },
  ]),
});
nestedLevel.builds = [nestedLevel.built_as];
const nestedHtml = context.constructStep(nestedLevel, 0, () => "#/x");
const nestedText = plain(nestedHtml);
assert.equal((nestedHtml.match(/class="constructstep/g) || []).length, 1,
  "the built ancestor is a row of the piece's own climb, not a second step");
assert.equal((nestedHtml.match(/class="cbuild"/g) || []).length, 1,
  "its construction is drawn in that row");
assert.ok(nestedHtml.includes('class="cdiamond mini"'),
  "and the row is marked with the diamond, as a construction is");
assert.ok(nestedText.indexOf("*keyt-") < nestedText.indexOf("*-rós")
          && nestedText.indexOf("*-rós") < nestedText.indexOf("*kit-ró-s"),
  "the pieces stand above the word they built");
assert.ok(nestedHtml.indexOf('class="cbuild"') < nestedHtml.indexOf("*kit-ró-s"),
  "and the row is drawn above that word, never beside it");

/* A piece whose own branch runs through a word that was built keeps that
   construction inside the piece's column, one grammar and one size down:
   `.cbuild` — the diamond, the first piece beside it, the line, the `+`. */
const columnLevel = Object.assign({}, causLevel, {
  built_as: buildOf([
    { form: "𐎨𐎡𐏂", gloss: "", reading: "čiçaʰ", known: true, lang: "peo", bound: false,
      branch: null },
    { form: "*x", gloss: "", reading: "", known: true, lang: "peo", bound: false,
      branch: origin({ form: "*x", parents: [origin({
        lang: "ine-pro", lang_name: "Proto-Indo-European", kind: "proto",
        form: "*kit-ró-s", terminal: "pie", known: false,
        builds: [kitros], built_as: kitros })] }) },
  ]),
});
columnLevel.builds = [columnLevel.built_as];
const columnHtml = context.constructStep(columnLevel, 0, () => "#/x");
assert.equal((columnHtml.match(/class="cbuild"/g) || []).length, 1,
  "a built word inside a piece's column keeps its construction");
assert.equal((columnHtml.match(/class="cstrip"/g) || []).length, 1,
  "the nested pieces are one line");
assert.ok(columnHtml.includes('class="cdiamond mini"'),
  "the nested step wears a smaller diamond");

/* A word of a language outside the family is the start of its own trail: no
   ??? claims an Indo-European ancestry it never had, while a family word whose
   record states no origin does hang under a ??? (2026-11-12). */
const outsideHtml = context.constructStep(Object.assign({}, causLevel, {
  built_as: buildOf([
    { form: "کتاب", gloss: "book", reading: "", known: true, lang: "fa", bound: false,
      branch: origin({ lang: "fa", form: "کتاب", gloss: "book", parents: [origin({
        lang: "ar", lang_name: "Arabic", short: "AR", form: "كِتَاب",
        rel: "borrow", terminal: "borrowed" })] }) },
    { form: "كِتَاب", gloss: "book", reading: "", known: true, lang: "ar", bound: false,
      branch: origin({ lang: "ar", lang_name: "Arabic", short: "AR", form: "كِتَاب",
        terminal: "outside", parents: [] }) },
    { form: "خانه", gloss: "house", reading: "", known: true, lang: "fa", bound: false,
      branch: origin({ form: "خانه", terminal: "end", parents: [] }) },
  ], { lang: "fa", lang_name: "Persian", kind: "compound" }),
  builds: null,
}), 0, () => "#/x");
assert.ok(outsideHtml.includes("a language outside the family: its own trail begins here"),
  "an outside-family piece says the trail begins there");
assert.ok(outsideHtml.includes("the record says the word was borrowed from here"),
  "a borrowed piece names its donor");
assert.equal((outsideHtml.match(/class="cunknown"/g) || []).length, 1,
  "only the family word without an origin gets a ???");

/* A word the record states more than one way gets one tab per construction
   (2026-11-12), and the reader — not the page — chooses. */
const altA = buildOf([{ form: "on", known: true, bound: false, branch: null },
  { form: "būtan", known: true, bound: false, branch: null }],
{ lang: "ang", lang_name: "Old English", of: "abūtan" });
const altB = buildOf([{ form: "be", known: true, bound: false, branch: null },
  { form: "ūtan", known: true, bound: false, branch: null }],
{ lang: "ang", lang_name: "Old English", of: "abūtan" });
const tabHtml = context.constructStep({ form: "abūtan", stage: "ang", name: "Old English",
  built_as: altA, builds: [altA, altB] }, 0, () => "#/x");
assert.ok(tabHtml.includes('class="bstep-tabs"') && tabHtml.includes('role="tablist"'),
  "several constructions are tabs");
assert.equal((tabHtml.match(/class="btab"/g) || []).length, 2, "one tab per construction");
assert.equal((tabHtml.match(/class="btree"/g) || []).length, 2, "and one tree behind each");
assert.ok(tabHtml.includes('id="bs-ang-0-0"') && tabHtml.includes('id="bs-ang-0-1"'),
  "the radios the tabs switch are named per step");
assert.ok(!context.constructStep(Object.assign({}, causLevel), 0, () => "#/x")
  .includes('class="bstep-tabs"'), "one construction needs no tabs");

/* The step stands above the form it builds: the timeline runs old (top) to
   new (bottom), so the pieces come first and the word under them. */
const builtLadder = context.renderHierarchy({
  levels: [
    level({ stage: "ine-pro", name: "Proto-Indo-European", status: "start",
            form: "*déwk-s-eti", baseline: "*déwk-s-eti", kind: "proto",
            builds: [], built_as: null }),
    level({ stage: "ira-pro", name: "Proto-Iranian", form: "dáwxšati",
            baseline: "dáwxšati",
            builds: [buildOf([{ form: "*dewk-", known: true, bound: false, branch: null },
              { form: "*-seti", known: false, bound: true, branch: null }],
            { lang: "ira-pro", lang_name: "Proto-Iranian", kind: "suffix", of: "dáwxšati" })],
            built_as: null }),
  ],
  result: { status: "differs" }, missing: [], earlier: [], switched_off: 0,
}, { lang: "ira-pro", lang_name: "Proto-Iranian" });
assert.ok(builtLadder.indexOf('class="constructstep"') <
  builtLadder.indexOf('data-stage="ira-pro"'),
  "the construction is drawn above the word it builds, never below it");

/* One icon per recorded page, under the headword: a W for a Wiktionary
   article, a book for a dictionary's entry for the word, and nothing at all
   for a word whose page is not recorded (2026-11-12). */
const sourcesHtml = context.sourceRow({ word: "آب", lang: "fa", evidence: "attested",
  pages: [
    { id: "dehkhoda", kind: "dictionary", title: "Dehkhoda",
      url: "https://vajehyab.com/dehkhoda/%D8%A2%D8%A8" },
    { id: "wiktionary", kind: "wiktionary", title: "Wiktionary",
      url: "https://en.wiktionary.org/wiki/%D8%A2%D8%A8" }] });
assert.equal((sourcesHtml.match(/class="srcicon/g) || []).length, 2, "one icon per recorded page");
assert.ok(sourcesHtml.includes('class="srcicon wikt"'), "the Wiktionary page keeps its mark");
assert.ok(sourcesHtml.includes('class="wmark"') && !sourcesHtml.includes("“"),
  "the mark is the W, not a quotation mark");
assert.ok(sourcesHtml.includes("vajehyab.com/dehkhoda/%D8%A2%D8%A8"),
  "the book opens the word's own dictionary entry, not the site");
assert.equal(context.sourceRow({ word: "x", lang: "en", evidence: "attested", pages: [] }), "",
  "a word with no recorded page has no icons");

/* A compound's pieces are drawn in the timeline, never in a section of their
   own (2026-11-13: the "WHERE THE PIECES COME FROM" block is gone from
   every word page, because the timeline already draws it). */
assert.equal(typeof context.renderJoin, "undefined", "the piece section is gone");
assert.ok(!/<h2>Where the pieces come from/i.test(
  fs.readFileSync(path.join(WEB, "app.js"), "utf8")),
  "no renderer prints the section's heading");

/* The coverage table separates what the record says from what the model
   explains, and draws both as bars (2026-11-09). */
const covHtml = context.coverageTable({
  fa: { name: "Persian", glossary: 1000, identified: 300, borrowed: 500, outside: 100,
        unlinked: 100, exact: 20, pathway: 0, orthographic: 40, script: 0, explained: 60,
        joined: 41 },
  en: { name: "English", glossary: 1000, identified: 400, borrowed: 500, outside: 80,
        unlinked: 20, exact: 100, pathway: 2, orthographic: 10, script: 0, explained: 112 },
}, 10);
assert.ok(covHtml.includes("b-exact") && covHtml.includes("b-orth"), "each layer has its own colour");
assert.ok(covHtml.includes("b-inherited") && covHtml.includes("b-borrowed"),
  "the record's own composition is a second bar");
assert.ok(covHtml.includes("11.2%"), "the explained share is printed");
assert.ok(covHtml.includes("built from pieces"), "a join is named beside the record, not counted as explained");
assert.ok(covHtml.includes("covbar prog") && covHtml.includes("b-part")
  && covHtml.includes("b-recon"),
  "progress is measured over the words with a recorded ancestor: full, other layers, recorded reconstruction, open");
assert.ok(covHtml.includes("25.0%</strong> full"), "English's full share is printed (100 of 400 identified)");

/* A transition with no rule file is a gap in the model, and the row says so
   instead of leaving the zero unexplained (2026-11-09). */
const gapHtml = context.coverageTable({
  chu: { name: "Old Church Slavonic", glossary: 1000, identified: 600, borrowed: 0,
         outside: 0, unlinked: 400, exact: 0, explained: 0, gaps: ["sla-pro → chu"] },
}, 5);
assert.ok(gapHtml.includes("no rule file: sla-pro → chu"),
  "a language whose transition does not exist names the missing step");

/* The laws may produce a form of the word and the dictionary cite its stem
   (Sanskrit देव devá- vs the nominative deváḥ).  That is the citation, not a
   sound law, so it is its own colour and its own column (2026-11-09). */
const citeHtml = context.coverageTable({
  sa: { name: "Sanskrit", glossary: 1000, identified: 800, borrowed: 0, outside: 0,
        unlinked: 10, exact: 0, pathway: 0, orthographic: 60, lemma: 120,
        explained: 180 },
}, 10);
assert.ok(citeHtml.includes("b-lemma"), "the citation gets its own colour");
assert.ok(citeHtml.includes("cited as its stem"), "and its own legend entry");
assert.ok(citeHtml.includes("120"), "the number is printed");

/* The row of "start from any recorded ancestor" chips is gone (2026-11-09): the payload may still carry `starts`, but the ladder renders
   none of it — no bar, no chips, no buttons. */
const withStarts = Object.assign({}, hierarchy, {
  levels: [hierarchy.levels[0], hierarchy.levels[1]],
  earlier: [], edited: null, start_recorded: null,
  starts: [
    { stage: "ine-pro", name: "Proto-Indo-European", form: "nókʷts", output: "nˈaht",
      steps: 4, missing: [], match: true, via_translit: false, via_script: false,
      unreadable: false, current: true },
    { stage: "gem-pro", name: "Proto-Germanic", form: "nahts", output: "naht",
      steps: 2, missing: [], match: false, via_translit: false, via_script: false,
      unreadable: false, current: false },
  ],
});
const startsHtml = context.renderHierarchy(withStarts, { lang: "en", lang_name: "English" });
assert.ok(!startsHtml.includes("starts-bar"), "no start bar on the word page");
assert.ok(!startsHtml.includes("startchip"), "and no per-language start buttons");
assert.ok(!startsHtml.includes("data-start-stage"), "the chips are gone from the markup entirely");
assert.ok(startsHtml.includes(">Timeline<"), "the ladder itself still renders, under one plain heading");

/* A recorded start says so in words and offers the way back. */
const recStarted = Object.assign({}, withStarts, {
  start: "gem-pro", start_name: "Proto-Germanic",
  start_recorded: { stage: "gem-pro", name: "Proto-Germanic", form: "nahts" },
  earlier: [{ id: "ine-pro", name: "Proto-Indo-European", era_label: "c. 4500–2500 BCE" }],
});
const recHtml = plain(context.renderHierarchy(recStarted, { lang: "en", lang_name: "English" }));
assert.ok(recHtml.includes("the record names"), "the start is called a record");
assert.ok(recHtml.includes("listed, not derived"), "the stages above it are not claimed as its history");
console.log("recorded starts ok");


/* One bar for the whole corpus: every explained layer is a segment and the
   rest of the glossary is what is still open (2026-11-09). */
const overallHtml = context.coverageOverall({
  glossary: 1000, identified: 600, borrowed: 300, outside: 60, exact: 40,
  pathway: 2, orthographic: 30, lemma: 5, identity: 8, bound_form: 3,
  script: 12, explained: 100,
});
assert.ok(overallHtml.includes("covstack big"), "the overall bar is drawn");
assert.ok((overallHtml.match(/<i class="b-/g) || []).length >= 7,
  "one segment per layer that has a number");
assert.ok(overallHtml.includes("10.0%"), "the share is printed");
assert.ok(overallHtml.includes("covstack thin"), "the record's own composition is a second bar");
assert.equal(context.coverageOverall({}), "", "no totals, no bar");
console.log("overall progress bar ok");

console.log("join timeline and coverage buckets ok");

/* A word borrowed from outside the family is drawn as a normal ladder, with
   the donor language as its top rung (2026-11-09): the horizontal
   contact bar is gone, the borrowing is a step row between two rungs, and the
   word itself is the last rung, record mark and all. */
const loanPage = {
  word: "آخرت", lang: "fa", lang_name: "Persian", era_label: "since c. 800",
  pos: "noun", gloss: ["hereafter"], evidence: "attested",
  sources: [{ id: "wiktionary", title: "Wiktionary, etymology sections (CC BY-SA 4.0)",
              url: "https://en.wiktionary.org", entry: "https://en.wiktionary.org/wiki/%D8%A2%D8%AE%D8%B1%D8%AA" }],
  pages: [{ id: "wiktionary", title: "Wiktionary", kind: "wiktionary",
            url: "https://en.wiktionary.org/wiki/%D8%A2%D8%AE%D8%B1%D8%AA" }],
  loan: { code: "ar", name: "Arabic", family: "Semitic", form: "آخِرة", relation: "borrow",
    period: { from: 633, to: 1100 } },
  ancestry: [{ lang: "ar", lang_name: "Arabic", form: "آخِرة", rel: "borrow",
               kind: "attested", evidence: "attested", ipa: "", reading: "",
               show_reading: false, reading_auto: false, reading_note: "", known: false }],
};
const loanHtml = context.renderLoanLadder(loanPage);
assert.ok(loanHtml.includes(">Timeline<"), "the loan is a timeline too, under the same plain heading");
assert.ok(loanHtml.includes('data-stage="ar"'), "the donor language is a rung");
assert.ok(loanHtml.includes("borrowed from Arabic into Persian"), "the borrowing is a step row");
assert.ok(loanHtml.includes('class="rung here"'), "the word is the last rung");
assert.match(loanHtml, /<a class="recorddot[^"]*"[^>]*href="https:\/\/en\.wiktionary\.org/,
  "the word keeps its record mark, opening its Wiktionary page");
assert.ok(!loanHtml.includes("loantrack"), "no horizontal contact bar");
assert.ok(!loanHtml.includes("loanbox"), "no separate loan panel");
assert.ok(!loanHtml.includes("does not date this word"),
  "the timeline carries the window badge, never a paragraph about the contact");
console.log("loan ladder ok");

/* A link that knows which word it means names the sense, the first one
   included. `#/word/peo/ciθrah` holds two words, and its first card used to
   point back at the list itself — so clicking it did nothing (2026-11-10). A link that names no sense still opens the list. */
assert.equal(evaluate('wordHref("peo", "ciθrah", true, "", 1)'),
             "#/word/peo/ci%CE%B8rah?sense=1", "the first word is named in its link");
assert.equal(evaluate('wordHref("peo", "ciθrah", true, "", 2)'),
             "#/word/peo/ci%CE%B8rah?sense=2", "the second word is named too");
assert.equal(evaluate('wordHref("peo", "ciθrah", true, "")'),
             "#/word/peo/ci%CE%B8rah", "a link that names no word opens the list");
console.log("sense links ok");

/* ---------------------------------------------------------------- */
/* attested / recorded / proposed, beside the band                     */
/* ---------------------------------------------------------------- */
/* The badge is a claim about the word itself, so it sits next to "fully
   explained" — which is a claim about its ancestry — and a reconstruction
   prints its asterisk in the headword (2026-11-11). */
const attestedBadge = evaluate(
  'attestBadge({status:"attested",label:"attested",definition:"A text writes it."})');
assert.ok(/class="badge attest attested"/.test(attestedBadge), attestedBadge);
assert.ok(plain(attestedBadge).includes("attested"));
const recordedBadge = evaluate(
  'attestBadge({status:"recorded",label:"recorded",definition:"Reconstructed."})');
assert.ok(/class="badge attest literary"/.test(recordedBadge),
  "a reconstruction is gold, the colour the site already uses for a record");
assert.ok(plain(recordedBadge).includes("recorded"));
assert.ok(!plain(recordedBadge).includes("(*)"), "the asterisk is on the word, not in the label");
const noneBadge = evaluate('attestBadge({status:"non-existent",label:"non-existent"})');
assert.ok(/class="badge attest warn"/.test(noneBadge), noneBadge);
assert.strictEqual(evaluate('attestBadge(null)'), "", "no status, no badge");
assert.strictEqual(evaluate('attestedWord({word:"madu",attestation:{written:"*madu"}})'),
  "*madu", "a recorded word is printed with its asterisk");

/* ---------------------------------------------------------------- */
/* the title is a sentence, not a row of pills (2026-11-11)            */
/* ---------------------------------------------------------------- */
/* The pills go: the record and the band are
   written side by side in the title's own size, the language and its years
   stand in the left margin, the category beside the meaning, and the review
   note trails them all, smaller.  A `badge` class anywhere in the title would
   bring the pill back, so every renderer here is checked for the absence of
   one. */
const note = evaluate('attestNote({status:"recorded",label:"recorded",definition:"Reconstructed."})');
assert.ok(note.includes('class="know literary"'), note);
assert.ok(!note.includes("badge"), "the record is not a pill in the title");
assert.ok(plain(note).includes("recorded"));
assert.ok(!plain(note).includes("(*)"), "no asterisk in the record's label");

const titleLine = evaluate(`standing({category:{category:"full",label:"fully explained",colour:"#1b5e20"},
  attestation:{status:"attested",label:"attested",definition:"A text writes it."}})`.replace(/\n/g, " "));
const titleText = plain(titleLine);
assert.ok(titleText.includes("fully explained"), titleText);
assert.ok(titleText.includes("attested"), "how the word is known is beside where it stands");
assert.ok(titleText.indexOf("fully explained") < titleText.indexOf("attested"),
  "the band comes first, then the record");

/* A corpus count of a handful is the news; the plain word says less
   (2026-11-14). */
const twoAttestations = plain(evaluate(
  'attestNote({status:"attested",label:"attested",definition:"A text writes it.",count:2})')).trim();
assert.strictEqual(twoAttestations, "2 attestations", twoAttestations);
assert.strictEqual(plain(evaluate(
  'attestNote({status:"attested",label:"attested",definition:"A text writes it.",count:1})')).trim(),
  "1 attestation",
  "one occurrence is one attestation, not one attestations");
assert.strictEqual(plain(evaluate(
  'attestNote({status:"attested",label:"attested",definition:"A text writes it.",count:102})')).trim(),
  "attested", "a large count stays the plain word");
assert.strictEqual(plain(evaluate(
  'attestNote({status:"recorded",label:"recorded",definition:"Reconstructed.",count:2})')).trim(),
  "recorded", "a count never rewrites a recorded or proposed word");
assert.ok(!titleLine.includes("badge"), titleLine);
assert.ok(titleLine.includes('class="standsep"'), "the two claims are set apart without a box");

const backlogged = evaluate('reviewNote({lang:"peo",backlog:[{kind:"etymon_missing",detail:"no headword"}]})');
assert.ok(backlogged.includes('class="backlognote"'), backlogged);
assert.ok(backlogged.includes("review backlog · 1"), "the count is the note");
assert.ok(backlogged.includes("#/backlog?lang=peo"), "it opens the backlog for this language");
assert.ok(!backlogged.includes("badge"), "the review note is not a pill either");
assert.strictEqual(evaluate('reviewNote({lang:"peo",backlog:[]})'), "", "nothing in the backlog, no note");

/* A page is what the server recorded, never a guess at a site (
   2026-11-12). A Persian word records Dehkhoda's entry and, when one was
   found, its Wiktionary article; the corner and the source row open both. */
const dehkhodaOnly = evaluate(`recordTag({pages:[
  {id:"dehkhoda",title:"Dehkhoda",kind:"dictionary",url:"https://vajehyab.com/dehkhoda/%DA%A9%D8%A8%D9%88%D8%AF"}]},null,"Persian")`);
assert.ok(dehkhodaOnly.includes('href="https://vajehyab.com/dehkhoda/%DA%A9%D8%A8%D9%88%D8%AF"'),
  "the book opens the word's own entry");
assert.ok(!dehkhodaOnly.includes('class="wmark"'),
  "a dictionary page is not painted with the Wiktionary W");
const noPage = evaluate(`recordTag({pages:[]},null,"Middle Persian")`);
assert.strictEqual(noPage, "", "no recorded page, no mark");
const english = evaluate(`recordTag({pages:[
  {id:"wiktionary",title:"Wiktionary",kind:"wiktionary",url:"https://en.wiktionary.org/wiki/foot"}]},null,"English")`);
assert.ok(english.includes('href="https://en.wiktionary.org/wiki/foot"') && english.includes('class="wmark"'));

const rail = evaluate('langRail({lang_name:"Old Persian",era_label:"c. 525–300 BCE"})');
assert.ok(rail.includes('class="raillang"') && rail.includes('class="railera"'), rail);
assert.ok(plain(rail).includes("Old Persian") && plain(rail).includes("c. 525–300 BCE"),
  "the language and its years share the margin");
assert.ok(!rail.includes("badge"), "no pill in the margin");
const cat = evaluate('catRail({pos:"name",lang:"peo"})');
assert.ok(cat.includes('<span class="railcat"'), cat);
assert.ok(plain(cat).includes("name"), "the category stands in the margin");
assert.strictEqual(evaluate('catRail({pos:"",lang:"peo"})'), "", "no category, no margin line");
assert.ok(evaluate('catRail({pos:"noun",lang:"fa"})').includes("tabsabove"),
  "Persian's category drops past the source tabs to sit beside the meaning");
assert.strictEqual(evaluate('catRail({pos:"",lang:"fa"})'), "");

/* ---------------------------------------------------------------- */
/* transcription and transliteration (2026-11-13)              */
/* ---------------------------------------------------------------- */
/* A transcribed word keeps its spellings beside it in the same mono line
   as a recorded reading, and says on hover that they are writing, not
   pronunciation. */
const spellingsHtml = evaluate(
  'wordMeta({word:"garm", spellings:["glm","g03lm"], script:"Pahlavi (Book Pahlavi), Manichaean"}, [], null, "pal")');
assert.ok(spellingsHtml.includes('class="translit spellings"'), spellingsHtml);
assert.ok(plain(spellingsHtml).includes("glm, g03lm"), "the spellings follow the headword");
assert.ok(!plain(spellingsHtml).includes("·"), "a spellings-only line opens with no dangling dot (2026-11-14)");
/* With a reading in front of them the spellings are a second layer of the same
   word, and the dot is what keeps the two layers apart. */
const readingThenSpellings = evaluate(
  'wordMeta({word:"garm", reading:"garm", spellings:["glm","g03lm"]}, [], null, "pal")');
assert.ok(plain(readingThenSpellings).trim().startsWith("garm"), plain(readingThenSpellings));
assert.ok(plain(readingThenSpellings).includes("garm · glm, g03lm"),
  "the reading comes first, then the dot, then the writing");
assert.ok(spellingsHtml.includes("Pahlavi") && spellingsHtml.includes("not pronunciations"),
  "hovering the spellings says they are written forms, not sounds");
assert.strictEqual(evaluate('wordMeta({word:"garm"}, [], null, "pal")'), "",
  "a word with no recorded spellings keeps the line absent");
const manySpellings = evaluate(
  'wordMeta({word:"garm", spellings:["glm","g03lm","hwʾb","fourth"]}, [], null, "pal")');
assert.ok(plain(manySpellings).includes("glm, g03lm, hwʾb, …"), "three spellings, then an ellipsis");
assert.ok(!plain(manySpellings).includes("fourth"), "the fourth spelling is not printed");

const transcribedStanding = evaluate(`standing({
  attestation:{status:"attested",label:"attested",definition:"A text writes it."},
  attested_how:"transcription"})`);
assert.match(transcribedStanding,
  /data-tip="[^"]*The form above is the record's transcription[^"]*rather than its writing\."/,
  "the status tooltip names the transcription, not a writing");

/* The optional glossary columns appear only when a row has something that is
   not already the form cell.  The renderer is driven with fixtures, so this
   needs no server. */
(async () => {
  const overview = {
    languages: [
      { id: "peo", name: "Old Persian", words: 1 },
      { id: "pal", name: "Middle Persian", words: 1 },
    ],
    coverage: { definitions: { full: { label: "fully explained", definition: "Every step is cited." } } },
  };
  const rows = {
    pal: [{ word: "garm", written: "garm", transcription: "garm", transliteration: "",
            attestation: "attested", pos: "adjective", gloss: ["warm"], band: "full", senses: 1 }],
    peo: [{ word: "vr̥kaʰ", written: "𐎺𐎼𐎣", transcription: "vr̥kaʰ", transliteration: "v-r-k",
            attestation: "attested", pos: "noun", gloss: ["wolf"], band: "full", senses: 1 }],
  };
  const oldFetch = context.fetch;
  context.fetch = async (url) => {
    const u = new URL(String(url));
    const body = u.pathname === "/api/overview" ? overview : {
      rows: rows[u.searchParams.get("lang")] || [], total: 1, headwords: 1,
      stage_total: 1, banded: 1, page: 1, pages: 1, first: 1, last: 1,
      counts: {}, statuses: { attested: "A text writes this word." },
    };
    return { ok: true, status: 200, json: async () => body };
  };
  try {
    await context.viewGlossary(new URLSearchParams("lang=pal&band=all"));
    const emptyHtml = evaluate("app.innerHTML");
    assert.ok(!emptyHtml.includes(">transcription</th>"),
      "a transcription equal to the form adds no column");
    assert.ok(!emptyHtml.includes(">transliteration</th>"),
      "an empty transliteration adds no column");
    assert.ok(!emptyHtml.includes('class="glossmore"'),
      "with no optional value there is no phone line either");

    await context.viewGlossary(new URLSearchParams("lang=peo&band=all"));
    const fullHtml = evaluate("app.innerHTML");
    const formCol = fullHtml.indexOf(">form</th>");
    const soundCol = fullHtml.indexOf(">transcription</th>");
    const writeCol = fullHtml.indexOf(">transliteration</th>");
    const statusCol = fullHtml.indexOf(">status</th>");
    assert.ok(formCol >= 0 && formCol < soundCol && soundCol < writeCol && writeCol < statusCol,
      "the two columns sit after the form, transcription before transliteration");
    assert.ok(fullHtml.includes('<th class="glossopt" data-tip="Transcription — how the word sounds'),
      "the transcription header explains the column");
    assert.ok(fullHtml.includes('<th class="glossopt" data-tip="Transliteration — how the word is written'),
      "the transliteration header explains the column");
    assert.ok(fullHtml.includes('<td class="sub glossopt">vr̥kaʰ</td>'),
      "the row prints how the word sounds");
    assert.ok(fullHtml.includes('<td class="sub glossopt">v-r-k</td>'),
      "the row prints how the word is written");
    assert.ok(plain(fullHtml).includes("transcription vr̥kaʰ · transliteration v-r-k"),
      "the phone line keeps both facts under the form");
    console.log("transcription and transliteration ok");
  } catch (e) {
    console.error(e);
    process.exitCode = 1;
  } finally {
    context.fetch = oldFetch;
  }
})();
