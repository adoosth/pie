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
/* A record the laws almost reach is a question, never a ✓ (admin, 2026-11-12):
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
   between two stages (admin, 2026-11-12). */
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
  "the machinery note is gone (admin, 2026-11-12)");
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
assert.ok(ladderWords.includes("nṓkʷθs → nṓkʷ"),
  "a switched-off law still says what it would have done");
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
  "the W is a serifed glyph now, not a monoline stroke (admin, 2026-11-12)");
assert.ok(!/class="recorddot[^>]*>“/.test(pgsRung),
  "the old quotation mark glyph is gone from the mark");
assert.ok(!pgsRung.includes("M12 6.6C10.4"), "the book glyph is gone");
assert.ok(pgsRung.indexOf('class="recword"') < pgsRung.indexOf(">nahts<")
          && pgsRung.indexOf(">nahts<") < pgsRung.indexOf(TAG),
  "the mark is on the recorded word itself");
assert.ok(pgsRung.indexOf("náhwθs") < pgsRung.indexOf(">nahts<"),
  "the reconstructed form is read before its record");
assert.ok(pgsRung.indexOf("náhwθs") < pgsRung.indexOf('data-edit="gem-pro"')
          && pgsRung.indexOf('data-edit="gem-pro"') < pgsRung.indexOf('class="recword"'),
  "the edit control follows the reconstructed word, not the record");
assert.ok(!pgsRung.includes(">edit<"), "the edit control is an icon, not the word 'edit'");
assert.ok(/class="editbtn icon"[^>]*aria-label="Edit the form for Proto-Germanic"/.test(pgsRung),
  "the pencil names the form it edits for a reader who cannot see it");
const pgsStart = ladder.slice(ladder.indexOf('class="recword"', ladder.indexOf('data-stage="ine-pro"')),
  ladder.indexOf('data-stage="gem-pro"'));
assert.ok(!pgsStart.includes(TAG),
  "a form with no recorded page carries no mark at all (admin, 2026-11-12)");
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

/* Two recorded pages are two doors on the same corner (admin, 2026-11-12):
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
assert.equal(bookTop.split("bʰeh₂g").length - 1, 1,
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
assert.equal(agreeBottom.split("bōk").length - 1, 1, "a matching form is printed once");
assert.ok(/class="form[^"]*matched[^"]*"/.test(agreeBottom), "a matching form glows as matched");
assert.ok(agreeBottom.includes("✓"), "the match carries a ✓, not only a colour");
/* The ✓ is a disc on the corner of the word box, not a glyph in the line:
   it is the last thing inside the matched form and nothing precedes the word. */
assert.match(agreeBottom, /class="form[^"]*matched[^"]*"[^>]*>bōk<i class="matchdot"[^>]*>✓<\/i><\/span>/,
  "the ✓ sits on the corner of the matched word, after it");
assert.ok(!/class="tick/.test(agreeBottom), "no tick glyph standing in the line");
assert.ok(!agreeBottom.includes("rectag"), "no second copy of the same form");
const agreeTop = agreeHtml.slice(agreeHtml.indexOf('data-stage="gem-pro"'),
                                agreeHtml.indexOf('data-stage="gmw-pro"'));
assert.equal(agreeTop.split("bōks").length - 1, 1, "a starting rung prints its recorded form once");
/* The first rung has no law above it, so `matches` stays false; `starts` is
   what makes it glow — it is the record the ladder starts from (2026-11-08). */
assert.match(agreeTop, /class="form[^"]*matched[^"]*"[^>]*>bōks<i class="matchdot"[^>]*>✓<\/i>/,
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
/* a word in the root language: reconstruct it into the family      */
/* ---------------------------------------------------------------- */
/* Proto-Indo-European has nothing above it, so the page must not draw an
   ancestry ladder. It offers a language instead, and shows what the
   registered laws make of the etymon on the way there (2026-11-07). */
const rootPage = {
  is_root: true, lang: "ine-pro", lang_name: "Proto-Indo-European", word: "nókʷts",
  rebuilds: { rows: [
    row({ l: "en", lang_name: "English", branch: "Germanic", form: "nˈæhwθ", status: "differs",
          evidence: "weak", recorded: { w: "night", r: "", evidence: "attested", ipa: "naɪ̯t" } }),
    row({ l: "de", lang_name: "German", branch: "Germanic", form: "nˈahwt", status: "new" }),
    row({ l: "sq", lang_name: "Albanian", branch: "Albanian", form: "nókʷts",
          skipped: ["ine-pro→sq"] }),
  ] },
  /* A PIE word has no ladder, but it still has a family below it: the page
     must draw the same expandable branch every other word page draws. */
  descendants: {
    source: { lang: "ine-pro", lang_name: "Proto-Indo-European", form: "nókʷts" },
    counts: { direct: 1, languages: 2, match: 0, differs: 0, new: 2, gaps: 0, steps: 2,
              strong: 0, weak: 2 },
    tree: [branchNode({ l: "gem-pro", lang_name: "Proto-Germanic", form: "nˈahwθs",
      children: [branchNode({ l: "en", lang_name: "English", form: "nˈæhwθ", depth: 1 })] })],
  },
};
const rootHtml = context.renderRoot(rootPage, "de");
const rootWords = plain(rootHtml);
assert.ok(rootHtml.includes('id="recon-lang"'), "the root page offers a language selector");
assert.ok(rootHtml.includes('<option value="de" selected>'), "the requested language is preselected");
assert.ok(rootHtml.includes('<optgroup label="Germanic">') && rootHtml.includes('<optgroup label="Albanian">'),
  "the languages are grouped by branch, alphabetically");
assert.ok(rootHtml.indexOf('label="Albanian"') < rootHtml.indexOf('label="Germanic"'),
  "branches are ordered, not left in row order");
assert.ok(rootHtml.includes("Albanian · chain incomplete"),
  "a language whose chain has a gap says so in the list");
assert.ok(rootWords.includes("Reconstruct the word into any descendant language"),
  "the page says what the selector does, in one line");
/* 2026-11-08: a fresh page reconstructs into nothing — the word
   and the INTO selector, no English derivation nobody asked for. */
const freshRoot = context.renderRoot(rootPage, "");
assert.ok(freshRoot.includes('<option value="" selected>'),
  "nothing is reconstructed until a language is chosen");
assert.ok(!freshRoot.includes('<option value="en" selected>'),
  "English is no longer the default");
assert.ok(!rootHtml.includes('id="recon-out"') === false, "the output slot exists");
assert.ok(rootHtml.includes('aria-live="polite"'), "the output is announced to a screen reader");
assert.ok(!rootHtml.includes("Where it comes from"), "no ancestry section on a root word");
assert.ok(rootWords.includes("Establish Pathways"), "a PIE word opens into its pathways");
assert.ok(rootHtml.includes('<details class="branchnode" data-l="gem-pro"'),
  "the etymon's daughter is expandable, like on every other word page");
assert.ok(rootHtml.indexOf("Establish Pathways") > rootHtml.indexOf('id="rootpanel"'),
  "the one-path panel comes first and the family tree follows it");

/* Grammar sits directly under the title as the word's construction
   (2026-11-08): the base, then the suffix it wears, then a (+).
   The old "as it stands" chip row is gone. */
rootPage.morphology = { suffixes: [
  { id: "eh2", form: "-eh₂", gloss: "feminine or collective", note: "…", sources: ["fortson-2004"] },
  { id: "kos", form: "-ko-", gloss: "relational adjective", note: "…", sources: ["fortson-2004"] },
] };
const plainRoot = Object.assign({}, rootPage, { construction: null });
const bareHtml = context.constructHtml(plainRoot, rootPage.morphology, "");
assert.ok(bareHtml.includes('class="cadd"'), "a word with no suffix still offers the (+)");
assert.ok(!bareHtml.includes("as it stands"), "the old '(as it stands)' wording is gone");
assert.ok(!bareHtml.includes('class="suffixline"'), "and so is the chip row beside the title");
const sufHtml = context.constructHtml(plainRoot, rootPage.morphology, "eh2");
assert.ok(sufHtml.includes('class="csuf"') && sufHtml.includes("-eh₂"),
  "the chosen suffix is printed in the construction line");
assert.ok(sufHtml.includes('data-mode="replace"'), "clicking it opens the suffix picker");
assert.ok(sufHtml.includes('id="sufmenu"'), "the picker has a place to open");
const menu = context.suffixMenuHtml(rootPage.morphology, "replace", "choose");
assert.ok(menu.includes('data-csuf="eh2"') && menu.includes("feminine or collective"),
  "every cited suffix is offered with its meaning");

/* The picker is the stage's whole recorded morphology, and a row says what the
   morpheme means, how many words wear it, and — when the dictionary keeps an
   entry for it — opens that entry (2026-11-08: *-ós* must explain
   itself, and a suffix recorded on one root must be selectable on the others). */
const richMorph = { suffixes: [
  { id: "ós", form: "-ós", gloss: "thematic nominative singular of an oxytone stem",
    detail: "*-ó- + *-s", recorded: 31, examples: ["nisdós", "dl̥h₁gʰós"],
    entry: "#/word/ine-pro/-%C3%B3s", kind: "ending" },
  { id: "iskos", form: "-iskos", gloss: "diminutive or belonging adjective",
    recorded: 0, entry: "#/word/ine-pro/-iskos", kind: "suffix" },
  { id: "n", form: "-n̥", gloss: "", recorded: 2, kind: "suffix" },
] };
const richMenu = context.suffixMenuHtml(richMorph, "replace", "choose");
assert.ok(richMenu.includes("-ós") && richMenu.includes("31 words"),
  "a recorded suffix says how many words wear it");
assert.ok(richMenu.includes("thematic nominative singular of an oxytone stem"),
  "and what it means");
assert.ok(richMenu.includes('class="suf-page"') && richMenu.includes("#/word/ine-pro/-%C3%B3s"),
  "and opens the dictionary entry for it");
assert.ok(richMenu.includes("no meaning recorded yet"),
  "a piece no source glosses says so instead of showing an empty cell");
assert.ok(richMenu.indexOf("-ós") < richMenu.indexOf("-iskos"),
  "the suffixes the corpus records most stand first");

/* An i-stem is *-i- plus the athematic nominative *-s: every letter of
   *h₂wl̥pís has to be accounted for, and the stated construction shows the
   composed word at once (2026-11-09). */
const pieStemC = {
  base: { form: "h₂wl̥p-", known: true, link: "#/word/ine-pro/h%E2%82%82wl%CC%A5p-" },
  members: [],
  suffixes: [{ form: "-i-", gloss: "i-stem — the stem-formative the record names",
               ending: "s", ending_name: "athematic nominative singular", kind: "stem" }],
  composed: "h₂wl̥pís",
};
const pieStemPage = Object.assign({}, rootPage, { word: "h₂wl̥pís", construction: pieStemC });
const pieStemHtml = context.constructHtml(pieStemPage, { suffixes: [] }, "");
assert.ok(pieStemHtml.includes("-i-"), "the stem-formative is printed");
assert.ok(pieStemHtml.includes(">-s<") || pieStemHtml.includes(">-s</"),
  "the nominative -s sits beside it, not out of nowhere");
assert.ok(pieStemHtml.includes("athematic nominative singular"),
  "the ending says what it is");
assert.ok(pieStemHtml.includes("composed") && pieStemHtml.includes("h₂wl̥pís"),
  "the composed word is shown before any law runs");

/* A suffix with an entry is a door even where the picker is closed: an
   attested word's construction cannot be recomposed, but it can be explained. */
const plainC = { base: { form: "delh₁gʰ-", known: true, link: "" },
                 suffixes: [{ form: "-ós", gloss: "thematic nominative singular",
                              entry: "#/word/ine-pro/-%C3%B3s", recorded: 31 }],
                 confidence: "stated", source: "the entry", etym: "From the stem *delh₁gʰ-" };
const plainPage = Object.assign({}, rootPage, { is_root: false, construction: plainC });
const plainHtml = context.constructHtml(plainPage, { suffixes: [] }, "");
assert.ok(plainHtml.includes('class="csuf plain link"'),
  "the suffix links to its entry when it cannot be chosen");
assert.ok(plainHtml.includes("31 words"), "the hover says where it is recorded");

/* A suffix recorded on a PIE root must be selectable on the others: the
   picker follows the construction, not the word's own suffix list. */
const otherC = Object.assign({}, plainC, { suffixes: [] });
const otherPage = Object.assign({}, rootPage, { is_root: false, construction: otherC });
assert.ok(context.constructHtml(otherPage, richMorph, "").includes('class="cadd"'),
  "a non-root word with a construction still offers the (+)");

/* One word may state several constructions (2026-11-08): the one
   it wears stays first and keeps the picker; the rivals follow, read-only,
   labelled with their confidence and hoverable to the sentence they came from. */
const primaryC = { base: { form: "kers-", known: true, link: "#/word/ine-pro/kers-" },
                   suffixes: [{ form: "-nós", id: null, gloss: "" }],
                   confidence: "stated", source: "the entry",
                   etym: "From *kers- + *-nós or *ker-s- + *-nós." };
const rivalC = { base: { form: "ker-s-", known: false, link: "" },
                 suffixes: [{ form: "-nós", id: null, gloss: "" }],
                 confidence: "argued", source: "the entry",
                 etym: "From *kers- + *-nós or *ker-s- + *-nós." };
const multi = Object.assign({}, rootPage, {
  word: "kr̥snós", construction: primaryC, constructions: [primaryC, rivalC],
});
const multiHtml = context.constructHtml(multi, rootPage.morphology, "");
/* A chain keeps its middle pieces: *dus- + *ménes- + *-s must read as three
   parts, or the row does not build the word (2026-11-08). */
const chainC = { base: { form: "dus-", known: false, link: "", gloss: "bad" },
                 members: [{ form: "ménes-", known: false, link: "", gloss: "mind, thought" }],
                 suffixes: [{ form: "-s", id: null, gloss: "" }],
                 confidence: "stated", source: "the entry",
                 etym: "From *dus- (“bad”) + *ménes- (“mind, thought”) + *-s." };
const chainHtml = context.constructHtml(Object.assign({}, rootPage, { word: "dusmenēs", construction: chainC }),
                                       rootPage.morphology, "");
assert.ok(chainHtml.includes('class="cmem"'), "the compound's middle piece is printed");
const chainText = plain(chainHtml);
assert.ok(chainText.indexOf("dus-") < chainText.indexOf("ménes-")
  && chainText.indexOf("ménes-") < chainText.indexOf("-s"),
  "the row reads base + member + suffix, in that order: " + chainText);
assert.ok(multiHtml.includes('class="construct-alt"'), "a rival construction sits under the main one");
assert.ok(plain(multiHtml).includes("also argued"), "and says how sure the entry is of it");
assert.ok(multiHtml.includes('data-tip="From *kers- + *-nós or *ker-s-'),
  "the sentence it was read from is on hover");
assert.ok(multiHtml.indexOf("kers-") < multiHtml.indexOf("ker-s-"),
  "the entry's own construction comes first");
assert.equal((multiHtml.match(/id="csuf"/g) || []).length, 1,
  "only the construction the word wears is a picker");
assert.equal((multiHtml.match(/id="cadd"/g) || []).length, 1, "and only one (+)");
/* The composed form is the construction's last line, inside the panel — not a
   loose line under the header (2026-11-08: the block must read as
   one section). */
assert.ok(multiHtml.includes('id="composed-line"'), "the composed form belongs to the construction panel");
assert.ok(multiHtml.indexOf('class="construct-row"') < multiHtml.indexOf('id="composed-line"'),
  "it follows the pieces it composes");
assert.ok(multiHtml.indexOf('id="composed-line"') < multiHtml.indexOf('class="construct-alt"'),
  "and sits above the rival analyses");
/* A word the entry only *suggests* a root for wears that root as a possible
   construction (2026-11-08): h₂ŕ̥tḱos, "possibly nominalized from
   root *h₂retḱ-". The label says who is sure — argued — and the pieces print
   the root with the stem-formative the word itself carries. */
const hedgedC = { base: { form: "h₂retḱ-", known: false, link: "", gloss: "to damage, harm" },
                  suffixes: [{ form: "-o-", id: null,
                               gloss: "o-stem — the stem-formative this form carries" }],
                  confidence: "argued", source: "the entry",
                  etym: "possibly nominalized from root *h₂retḱ- (“to damage, harm”)" };
const hedgedPage = Object.assign({}, rootPage, {
  is_root: false, word: "h₂ŕ̥tḱos", construction: hedgedC, constructions: [hedgedC],
});
const hedgedHtml = context.constructHtml(hedgedPage, { suffixes: [] }, "");
assert.ok(plain(hedgedHtml).includes("construction argued"),
  "a hedged derivation is labelled as argued");
assert.ok(hedgedHtml.includes("h₂retḱ-") && hedgedHtml.includes("-o-"),
  "the root and the stem-formative it carries are both printed");
assert.ok(hedgedHtml.includes("data-tip=\"“to damage, harm”"),
  "the entry's own gloss of the root is on hover");
const bareBaseC = { base: { form: "mer-", known: true, link: "#/word/ine-pro/mer-" },
                    suffixes: [], confidence: "argued", source: "the entry",
                    etym: "perhaps from a root *mer- (“sea, lake, wetland”)." };
const bareBaseHtml = context.constructHtml(
  Object.assign({}, hedgedPage, { word: "móri", construction: bareBaseC, constructions: [bareBaseC] }),
  { suffixes: [] }, "");
assert.ok(!bareBaseHtml.includes('class="cplus"'),
  "a derivation that names no suffix prints no suffix");
assert.ok(bareBaseHtml.includes('class="cbase link"'), "its root is still a door to its page");
const wordOnly = Object.assign({}, rootPage, { is_root: false, construction: null });
assert.ok(!context.constructHtml(wordOnly, rootPage.morphology, "").includes("composed-line"),
  "a descendant's page composes nothing here");

/* A word the dictionary builds from another one shows the base as a door and
   the suffix it wears, whether or not a picker exists for the stage. */
const derived = Object.assign({}, rootPage, {
  word: "wl̥kʷíh₂s", is_root: true,
  construction: { base: { form: "wĺ̥kʷos", known: true, link: "#/word/ine-pro/wĺ̥kʷos" },
                  suffixes: [{ form: "-íh₂s", id: null, gloss: "" }],
                  etym: "From *wĺ̥kʷos + *-íh₂s." },
});
/* The label is a heading on its own line above the pieces, so it cannot read
   as a word glued to the base (2026-11-08). */
assert.ok(bareHtml.includes('<span class="construct-label">construction(s)</span>'),
  "with nothing stated the panel still reads as the place constructions live");
assert.ok(bareHtml.indexOf('class="construct-label"') < bareHtml.indexOf('class="construct-row"'),
  "the label sits on its own line, before the pieces");
const stemPage = Object.assign({}, rootPage, {
  word: "h₂wl̥pís",
  construction: { kind: "stem", base: { form: "h₂wl̥p-", known: true, link: "#/word/ine-pro/h₂wl̥p-" },
                  suffixes: [{ form: "-i-", id: null,
                               gloss: "i-stem — the stem-formative the record names" }],
                  etym: "An i-stem noun built on the root *h₂wl̥p-." },
});
const stemHtml = context.constructHtml(stemPage, rootPage.morphology, "");
assert.ok(stemHtml.includes('<span class="construct-label">construction</span>'),
  "a stated stem class is a construction");
assert.ok(stemHtml.includes('data-tip="-i- · i-stem'),
  "the stem-formative carries its gloss on hover");
assert.ok(stemHtml.indexOf("h₂wl̥p-") < stemHtml.indexOf("-i-"), "root first, then the stem-formative");

const dHtml = context.constructHtml(derived, rootPage.morphology, "");
assert.ok(dHtml.includes('href="#/word/ine-pro/wĺ̥kʷos"'), "the base links to its own page");
assert.ok(dHtml.includes("-íh₂s"), "the suffix the word wears is printed");
assert.ok(dHtml.indexOf("wĺ̥kʷos") < dHtml.indexOf("-íh₂s"), "base first, then the suffix");

const recon = context.renderReconstruct({
  source: { form: "nókʷts", name: "Proto-Indo-European" },
  lang: "en", lang_name: "English", branch: "Germanic", kind: "attested",
  form: "nˈæhwθ", steps: 2, tiers: ["established"], skipped: [],
  status: "differs", evidence: "weak", same: false,
  recorded: { w: "night", r: "", evidence: "attested", ipa: "naɪ̯t", show_reading: false,
              pos: "noun", gloss: "the dark part of the day",
              pages: [{ id: "wiktionary", title: "Wiktionary", kind: "wiktionary",
                        url: "https://en.wiktionary.org/wiki/night" }] },
  levels: [
    { src: "ine-pro", dst: "gem-pro", src_name: "Proto-Indo-European", dst_name: "Proto-Germanic",
      form: "nˈahwθs", missing: false, registered: 41, fired: 1,
      rules: [{ key: "ine-pro~gem-pro:grimm_t", id: "grimm_t", name: "Grimm: *t → *þ",
                tier: "established", before: "nókʷts", after: "nˈōkʷθs",
                fired: true, disabled: false }] },
    { src: "gem-pro", dst: "en", src_name: "Proto-Germanic", dst_name: "English",
      form: "nˈæhwθ", missing: false, registered: 10, fired: 0, rules: [] },
  ],
});
const reconWords = plain(recon);
assert.ok(recon.indexOf("nǽhwθ") < recon.indexOf(">night<") && recon.indexOf(">night<") < recon.indexOf(TAG),
  "the reconstruction and the record are two words, and the record mark is on the record");
assert.ok(!reconWords.includes("applicable law"), "no count of applicable laws on a step");
assert.ok(!reconWords.includes("Proto-Indo-European → Proto-Germanic"),
  "no stage → stage label on a step");
assert.ok(reconWords.includes("Grimm: *t → *þ"), "a fired law is named");
assert.ok(reconWords.includes("differs from the record"), "the verdict is worded, not only coloured");
assert.ok(reconWords.includes("noun · “the dark part of the day”"), "the record carries its sense");
/* 2026-11-08: the counts and tiers belonged to the summary no
   more than the timeline needs them — it shows which laws applied itself. */
assert.ok(!reconWords.includes("laws fired between"), "no summary count of laws above the timeline");
assert.ok(!reconWords.includes("Tiers used"), "the tier list is gone from the summary");
/* The reconstruction is a ladder now, not a list of steps (2026-11-08): the
   starting stage is a rung with its date, the target is the last rung. */
assert.ok(/<ol class="ladder recon-ladder">/.test(recon), "the reconstruction is drawn as a ladder");
assert.ok(recon.includes('<span class="when-name kind-proto">Proto-Indo-European</span>'),
  "the first rung is the starting stage");
assert.ok(reconWords.includes("English") && reconWords.includes("here"),
  "the last rung is the target language");
assert.equal((recon.match(/class="rung /g) || []).length, 3,
  "one rung per stage plus the starting stage");

/* 2026-11-08: "why can't I edit the reconstructed words in the
   timeline shown here?" Every rung of a reconstruction is editable where it
   stands — the starting stage and the target included — and a rung the reader
   rewrote is marked as a hypothesis, with one button to put the laws' form
   back. */
assert.ok(recon.includes('data-edit="gem-pro"'), "a reconstruction rung carries the pencil");
assert.ok(recon.includes('data-edit="en"'), "the target stage is editable too");
const reconEdited = context.renderReconstruct({
  source: { form: "nókʷts", name: "Proto-Indo-European", kind: "proto", stage: "ine-pro" },
  lang: "en", lang_name: "English", branch: "Germanic", kind: "attested",
  form: "nˈæhwθ", steps: 2, tiers: ["established"], skipped: [],
  status: "differs", evidence: "weak", same: false,
  edited: { stage: "gem-pro", form: "nahts", name: "Proto-Germanic" },
  recorded: { w: "night", r: "", evidence: "attested", ipa: "naɪ̯t", show_reading: false },
  levels: [
    { src: "ine-pro", dst: "gem-pro", src_name: "Proto-Indo-European", dst_name: "Proto-Germanic",
      form: "nahts", missing: false, registered: 41, fired: 0, edited: true, rules: [] },
    { src: "gem-pro", dst: "en", src_name: "Proto-Germanic", dst_name: "English",
      form: "nˈæht", missing: false, registered: 10, fired: 0, rules: [] },
  ],
});
assert.ok(/class="rung recon-rung edited"/.test(reconEdited),
  "the rewritten rung is marked as edited");
assert.ok(reconEdited.includes('data-edit="gem-pro"') && reconEdited.includes('data-stage="gem-pro"'),
  "it is still editable, and the pencil knows which rung it is on");
assert.ok(reconEdited.includes("data-recon-unedit"),
  "one button puts the laws' form back");
assert.ok(/class="recon-badges"[\s\S]*>edited</.test(reconEdited),
  "the edited state is a chip on the heading's line, and says the rung is a hypothesis");
const editedRung = reconEdited.slice(reconEdited.indexOf('data-stage="gem-pro"') - 200,
                                     reconEdited.indexOf('data-stage="en"'));
assert.ok(!editedRung.includes("laws-head"),
  "an edited rung has no fired law to report");

/* Every law on a step is a switch (2026-11-08: the laws on the
   etymon page could not be disabled): the click re-derives the chain without
   it, and a switched-off law still says what it would have done. */
assert.ok(/class="lawswitch"[^>]*data-off="ine-pro~gem-pro:grimm_t"/.test(recon),
  "a law on a reconstruction step is a switch");
assert.ok(/data-off="ine-pro~gem-pro:grimm_t" aria-pressed="true"/.test(recon),
  "a fired law starts pressed");
const reconOff = context.renderReconstruct({
  source: { form: "nókʷts", name: "Proto-Indo-European" },
  lang: "en", lang_name: "English", kind: "attested", form: "nˈæhwt", steps: 1,
  tiers: ["established"], skipped: [], status: "differs", evidence: "weak", same: false,
  disabled: ["ine-pro~gem-pro:grimm_t"],
  recorded: { w: "night", r: "", evidence: "attested", ipa: "naɪ̯t", show_reading: false },
  levels: [{ src: "ine-pro", dst: "gem-pro", src_name: "Proto-Indo-European",
             dst_name: "Proto-Germanic", form: "nˈahwts", missing: false,
             registered: 41, fired: 0, switched_off: 1,
             rules: [{ key: "ine-pro~gem-pro:grimm_t", id: "grimm_t", name: "Grimm: *t → *þ",
                       tier: "established", before: "nókʷts", after: "nókʷts",
                       would: "nˈōkʷθs", fired: false, disabled: true }] }],
});
assert.ok(/data-off="ine-pro~gem-pro:grimm_t" aria-pressed="false"/.test(reconOff),
  "a switched-off law is pressed-off");
assert.ok(!plain(reconOff).includes("1 switched off"),
  "the rung no longer repeats a switch count; the chip on the head says it once");
assert.ok(plain(reconOff).includes("1 law is switched off"), "the page states it above the ladder");
assert.ok(reconOff.includes("data-recon-reset"), "and one button puts them all back");
assert.ok(reconOff.includes("nṓkʷθs"),
  "the switched-off law still says what it would have done, printed the dictionary way");

/* A match is printed once, glowing, with the corner ✓ — same rule as a rung. */
const reconMatch = context.renderReconstruct({
  source: { form: "nókʷts", name: "Proto-Indo-European" },
  lang: "la", lang_name: "Latin", kind: "attested", form: "nox", steps: 3,
  tiers: ["established"], skipped: [], status: "match", evidence: "attested", same: true,
  recorded: { w: "nox", r: "", evidence: "attested", ipa: "", reading: "", show_reading: false },
  levels: [{ src: "ine-pro", dst: "la", src_name: "Proto-Indo-European", dst_name: "Latin",
             form: "nox", missing: false, registered: 12, fired: 3,
             rules: [{ key: "ine-pro~la:x", id: "x", name: "A law", tier: "established",
                       before: "nókʷts", after: "nox", fired: true, disabled: false }] }],
});
const reconFormsStart = reconMatch.lastIndexOf('class="rung-forms"');
const reconForms = reconMatch.slice(reconFormsStart,
  reconMatch.indexOf("</div>", reconFormsStart));
assert.equal((reconForms.match(/>nox</g) || []).length, 1,
  "a matching reconstruction is printed once (its link and tooltip are not a second copy)");
assert.ok(/class="form[^"]*matched[^"]*"[^>]*>nox<i class="matchdot"/.test(reconMatch),
  "the match carries the corner ✓ disc");
assert.ok(!reconForms.includes("rectag"), "no second copy, so no 'recorded' tag");

/* 2026-11-08: a green recorded word is a door to its own page, the
   pencil follows the reconstruction and not the record, and the page glyph is
   pinned to the word's own corner — not to a wider reading under it (بازو is
   25 px, its IPA 72 px). */
const reconBazu = context.renderReconstruct({
  source: { form: "bʰeh₂ǵʰús", name: "Proto-Indo-European", stage: "ine-pro" },
  lang: "fa", lang_name: "Persian", kind: "attested", form: "baHdoš", steps: 2,
  tiers: ["established"], skipped: [], status: "differs", evidence: "weak", same: false,
  recorded: { w: "بازو", r: "bâzu", evidence: "attested", ipa: "baː.ˈzuː",
              reading: "bâzu", show_reading: true, known: true, sources: [] },
  levels: [{ src: "ine-pro", dst: "fa", src_name: "Proto-Indo-European",
             dst_name: "Persian", form: "baHdoš", missing: false,
             registered: 2, fired: 2, rules: [] }],
});
const rbz = reconBazu.lastIndexOf('class="rung-forms"');
const rbzSeg = reconBazu.slice(rbz, reconBazu.indexOf("</div>", rbz));
assert.ok(rbzSeg.indexOf("baHdoš") < rbzSeg.indexOf('data-edit="fa"')
          && rbzSeg.indexOf('data-edit="fa"') < rbzSeg.indexOf("بازو"),
  "the pencil follows the reconstructed form, not the recorded word");
assert.match(rbzSeg, /<a class="formlink" href="#\/word\/fa\/[^"]*"[^>]*><span class="form rtl/,
  "the recorded word opens its own page");
assert.ok(rbzSeg.includes("بازو") && !rbzSeg.includes('class="recorddot"'),
  "a record with no page keeps the word and takes no mark");

/* A missing rule file is a gap, not a silent no-op. */
const reconGap = context.renderReconstruct({
  source: { form: "nókʷts", name: "Proto-Indo-European" },
  lang: "sq", lang_name: "Albanian", kind: "attested", form: "nókʷts", steps: 0,
  tiers: [], skipped: ["ine-pro→sq"], status: "new", evidence: "weak", same: false,
  recorded: null,
  levels: [{ src: "ine-pro", dst: "sq", src_name: "Proto-Indo-European", dst_name: "Albanian",
             form: "nókʷts", missing: true, registered: 0, fired: 0, rules: [] }],
});
const gapWords = plain(reconGap);
assert.ok(gapWords.includes("The chain is incomplete"), "the gap is named");
assert.ok(gapWords.includes("No rule file exists for Proto-Indo-European → Albanian"),
  "the missing rule file is named at its step");
assert.ok(!gapWords.includes("applicable laws"),
  "a step with no rule file carries no law count at all");

/* 2026-11-08: a rung is coloured by what is known about the *form*,
   not by whether its language is attested. The OP rung *warpíš* has no record,
   so it is red and still a door; its page says "not recorded here". */
const reconUnrecorded = context.renderReconstruct({
  source: { form: "h₂wl̥pís", name: "Proto-Indo-European" },
  lang: "fa", lang_name: "Persian", kind: "attested", form: "gorbeš",
  form_known: false, steps: 2, tiers: ["proposed"], skipped: [], status: "new",
  evidence: "weak", same: false, recorded: null,
  levels: [{ src: "ira-pro", dst: "peo", src_name: "Proto-Iranian", dst_name: "Old Persian",
             kind: "attested", era_label: "c. 525–300 BCE", form: "warpˈiš",
             form_known: false, status: "derived", evidence: "weak", recorded: null,
             same: false, missing: false, registered: 10, fired: 2, rules: [] },
           { src: "peo", dst: "fa", src_name: "Old Persian", dst_name: "Persian",
             kind: "attested", era_label: "since c. 800", form: "gorbeš",
             form_known: false, status: "derived", evidence: "weak", recorded: null,
             same: false, missing: false, registered: 10, fired: 1, rules: [] }],
});
const unrecordedPEO = reconUnrecorded;
assert.ok(unrecordedPEO.includes("ev-weak"), "an unrecovered law rung is not green");
assert.ok(!unrecordedPEO.includes("ev-attested"), "its language being attested is not evidence");
assert.ok(unrecordedPEO.includes("ghost=1") && unrecordedPEO.includes("warp%CB%88i%C5%A1"),
  "the rung is still a door to its own page");
assert.ok(reconUnrecorded.includes('href="#/word/fa/gorbe%C5%A1?ghost=1'),
  "the target form is a door too, even when nothing records it");

/* A green rung carries its citation, and an OP record shows the cuneiform
   spelling — never a Latin transliteration dressed as attested. */
const reconRecord = context.renderReconstruct({
  source: { form: "deywós", name: "Proto-Indo-European" },
  lang: "fa", lang_name: "Persian", kind: "attested", form: "dīw", form_known: false,
  steps: 1, tiers: ["proposed"], skipped: [], status: "new", evidence: "weak",
  same: false, recorded: null,
  levels: [{ src: "ira-pro", dst: "peo", src_name: "Proto-Iranian", dst_name: "Old Persian",
             kind: "attested", era_label: "c. 525–300 BCE", form: "daiwˈah",
             form_known: false, status: "differs", evidence: "weak", same: false,
             missing: false, registered: 10, fired: 1, rules: [],
             recorded: { w: "𐎭𐎡𐎺", evidence: "attested", in_script: true,
                         script: "Old Persian cuneiform", reading: "daivaʰ", show_reading: true,
                         notation: "v/w", known: true, ipa: "",
                         pages: [{ id: "wiktionary", title: "Wiktionary", kind: "wiktionary",
                                   url: "https://en.wiktionary.org/wiki/%F0%90%8E%AD%F0%90%8E%A1%F0%90%8E%BA" }] } },
           { src: "peo", dst: "fa", src_name: "Old Persian", dst_name: "Persian",
             kind: "attested", era_label: "since c. 800", form: "dīw",
             form_known: false, status: "derived", evidence: "weak", recorded: null,
             same: false, missing: false, registered: 10, fired: 1, rules: [] }],
});
const recPEO = reconRecord.slice(reconRecord.indexOf("Old Persian"));
assert.ok(recPEO.includes("𐎭𐎡𐎺") && recPEO.includes("ev-attested"),
  "the record is shown in its own script");
assert.ok(recPEO.includes("Source: Wiktionary"), "a green rung names its source in the tooltip");
assert.ok(!plain(recPEO).includes("Source:"),
  "the citation is not printed on a line under the word any more");
assert.ok(recPEO.includes("spelled v/w"), "a transcription difference is explained");

/* A Reconstruction: namespace entry is gold and says so; it is not a
   transliteration of a written word, so the script note must stay away
   (2026-11-08). */
const reconLiterary = context.renderReconstruct({
  source: { form: "mádu", name: "Proto-Indo-European" },
  lang: "fa", lang_name: "Persian", kind: "attested", form: "mey", form_known: false,
  steps: 1, tiers: ["established"], skipped: [], status: "new", evidence: "weak",
  same: false, recorded: null,
  levels: [{ src: "ira-pro", dst: "peo", src_name: "Proto-Iranian", dst_name: "Old Persian",
             kind: "attested", era_label: "c. 525–300 BCE", form: "madˈu", form_known: false,
             status: "differs", evidence: "weak", same: false, missing: false,
             registered: 10, fired: 1, rules: [],
             recorded: { w: "madu", evidence: "literary", recon: true, in_script: false,
                         script: "Old Persian cuneiform", reading: "", show_reading: false,
                         known: true, ipa: "",
                         sources: [{ title: "Wiktionary", url: "https://en.wiktionary.org" }] } },
           { src: "peo", dst: "fa", src_name: "Old Persian", dst_name: "Persian",
             kind: "attested", era_label: "since c. 800", form: "mey",
             form_known: false, status: "derived", evidence: "weak", recorded: null,
             same: false, missing: false, registered: 10, fired: 1, rules: [] }],
});
assert.ok(reconLiterary.includes("ev-attested") === false,
  "a reconstruction in an attested language is never green");
assert.ok(reconLiterary.includes("ev-literary"), "it is gold instead");
assert.ok(!reconLiterary.includes("no spelling in"),
  "a reconstruction is not described as a transliteration");
console.log("root word ok");

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
/* 2026-11-08: 𐎺𐎼𐎣 is *wárkah*. The syllabary writes va-ra-ka
   and leaves the final /h/ unwritten, so the laws' form is a reading of the
   record — a match, with the signs printed beside it. Below the word, the
   direct descendants of Old Persian are buttons that add a rung each. */
const read = {
  start: "ine-pro", start_name: "Proto-Indo-European", etymon: "wĺ̥kʷos", root: false,
  switched_off: 0, missing: [], total_steps: 5, earlier: [], exact: null,
  path: ["pal"], can_extend: true,
  result: { status: "match", form: "wˈarkah", target: "𐎺𐎼𐎣", match: true,
            match_via_script: true, match_via_translit: false, ipa: "", reading: "",
            attested: true },
  levels: [
    level({ stage: "ipe", name: "Proto-Indo-European", short: "PIE", kind: "proto",
            era_label: "c. 4500–2500 BCE", era_mid: -3500, form: "wĺ̥kʷos", baseline: "wĺ̥kʷos",
            status: "start", evidence: "literary" }),
    level({ stage: "peo", name: "Old Persian", short: "OP", era_label: "c. 525–300 BCE",
            era_mid: -412, form: "wˈarkah", baseline: "wˈarkah", status: "match",
            evidence: "attested",
            recorded: { w: "𐎺𐎼𐎣", more: [], evidence: "attested", ipa: "", reading: "",
                        show_reading: true, matches: true, via: null,
                        fit: { ok: true, translit: "va-ra-ka", logogram: false,
                               filler: [1], unwritten: ["h"] } } }),
    level({ stage: "pal", name: "Middle Persian", short: "MP", era_label: "c. 224–650",
            era_mid: 435, form: "gˈurg", baseline: "gˈurg", status: "match", evidence: "attested",
            recorded: { w: "𐭢𐭥𐭫𐭢", more: [], evidence: "attested", ipa: "", reading: "gurg",
                        show_reading: true, matches: true } }),
  ],
  next: [Object.assign(row({ l: "fa", lang_name: "Persian", branch: "Indo-Iranian (Iranian)",
                              short: "fa", era_label: "since c. 900", form: "gˈurg", steps: 2,
                              status: "match", evidence: "attested" }),
                        { recorded: { w: "گرگ", reading: "gurg", evidence: "attested" } })],
};
const readHtml = context.renderHierarchy(read, { lang: "peo", word: "𐎺𐎼𐎣", lang_name: "Old Persian" });
const readWords = plain(readHtml);
assert.ok(readWords.includes("exact, read from the script"),
  "a match through the writing system says how it was made");
assert.ok(readWords.includes("read va-ra-ka"), "the signs the record writes are printed");
assert.ok(readWords.includes("leaves h unwritten"), "and what the script does not write");
assert.ok(readWords.includes("a vowel sign carries a bare consonant"),
  "the filler vowel is explained, not hidden");
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

/* The construction picker is a menu of sections (2026-11-08): the morphemes
   the word itself wears come first, in the colour of a record, and every other
   recorded form hangs in a submenu under the heading its own record gives it.
   The sections come from the read model (`service.morphology`), never from the
   front end's taste. */
const morphMenu = {
  language: "ine-pro", note: "",
  sections: [
    { id: "derivation-noun", name: "noun-forming", count: 1 },
    { id: "ending", name: "inflectional endings", count: 2 },
  ],
  suffixes: [
    { id: "ter", form: "-tēr-", gloss: "agent and kinship noun", kind: "suffix",
      section: "derivation-noun", section_name: "noun-forming", recorded: 21,
      entry: "#/word/ine-pro/-t%C4%93r-", curated: true },
    { id: "os", form: "-os", gloss: "o- and s-stem nom./acc. sg.", kind: "ending",
      section: "ending", section_name: "inflectional endings", recorded: 4, entry: "" },
    { id: "os-acute", form: "-ós", gloss: "oxytone nominative", kind: "ending",
      section: "ending", section_name: "inflectional endings", recorded: 31, entry: "" },
  ],
};
const menuHtml = context.suffixMenuHtml(morphMenu, "add", "attach another cited suffix",
                                        [{ id: "os-acute", form: "-ós" }]);
assert.ok(menuHtml.includes('class="sufworn"'), "the worn morphemes have a block of their own");
assert.ok(/class="sufrow worn"/.test(menuHtml), "and its rows are marked as worn");
assert.ok(menuHtml.indexOf("sufworn") < menuHtml.indexOf("sufsecs"),
  "the worn morphemes stand at the top, before the sections");
assert.ok(menuHtml.includes('data-sec="derivation-noun"') && menuHtml.includes('data-sec="ending"'),
  "every section with rows gets a heading");
assert.equal((menuHtml.match(/class="sufsub"/g) || []).length, 2,
  "each section has its own submenu");
assert.ok(/aria-haspopup="menu"/.test(menuHtml), "a heading announces that it opens a menu");
assert.ok(menuHtml.indexOf("agent and kinship noun") > menuHtml.indexOf('data-sec="derivation-noun"'),
  "a section's forms live inside its submenu, after its heading");
assert.ok(menuHtml.indexOf("oxytone nominative") < menuHtml.indexOf('data-sec="ending"'),
  "the worn copy is printed first, the full list later");
assert.ok((menuHtml.match(/-ós/g) || []).length >= 2,
  "a worn morpheme also keeps its place in its own section");
const looseMenu = context.suffixMenuHtml({ suffixes: morphMenu.suffixes }, "add", "choose");
assert.ok(looseMenu.includes("all recorded forms"),
  "a payload without sections still lists its forms under one heading");
console.log("construction menu ok");

/* A construction is one tree in the timeline, not a line under the word and
   not a set of inset pictures (admin, 2026-11-12): a diamond sits on the main
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
const terms = chunk(builtHtml, "cterm");
assert.ok(builtHtml.includes('class="constructstep"'), "the construction is a ladder step");
assert.ok(builtHtml.includes('<div class="rail" aria-hidden="true"><i class="cdiamond"></i></div>'),
  "the diamond marks the step on the main rail itself");
assert.ok(!builtText.includes("CONSTRUCTION"), "no CONSTRUCTION line under the word any more");
assert.ok(builtText.includes("construction"), "the step names itself in the margin");
/* One tree: the first word stands immediately right of the diamond — the
   diamond is its mark, so no wire and no second dot sit between them — and the
   line leaves the word's own right edge for `+` and the next piece (admin,
   2026-11-12). */
assert.equal((builtHtml.match(/class="btree"/g) || []).length, 1, "one construction is one tree");
assert.ok(!builtHtml.includes('class="bnode') && !builtHtml.includes('class="bcol'),
  "no inset columns survive: nothing is drawn in a thinner sub-timeline");
assert.equal(terms.length, 2, "both pieces stand on the tree's own line");
assert.equal((builtHtml.match(/class="cplus"/g) || []).length, 1, "one + between two pieces");
assert.ok(!builtHtml.includes('class="cwire"'),
  "no redundant wire: the first word starts at the diamond");
assert.ok(/class="cterm first"/.test(terms[0]),
  "the first piece is the one the diamond marks");
assert.ok(!terms[0].includes('class="cline"') && !terms[0].includes('class="crail"'),
  "it carries no line and no dot of its own");
assert.ok(terms[1].includes('class="cline"'),
  "the next piece is met by the line that left the first word");
assert.ok(builtHtml.indexOf('class="cterm first"') < builtHtml.indexOf(">+<"),
  "the + comes after the first word, from its right side");
assert.ok(builtHtml.indexOf(">+<") < builtHtml.indexOf('class="cplus"', builtHtml.indexOf(">+<")) + 1
  || builtHtml.indexOf(">+<") > builtHtml.indexOf('class="cterm first"'),
  "the + sits between the two pieces");
/* The pieces are words, not labels: word size, no language of their own. */
assert.ok(terms[0].includes('class="cform term'), "a piece is written at word size");
assert.ok(!terms[0].includes("Old Persian") && !terms[1].includes("Old Persian"),
  "a piece is not labelled with the language of the step: it is a word of it");
assert.ok(terms[0].includes("čiçaʰ"), "the piece's reading is printed beside it");
/* The meaning stands under the word, the way the headword's own line carries
   it — `name · “a male given name”` — and the hover still says where it opens
   (admin, 2026-11-12). */
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
/* The first piece's own descent is the ladder's own rows, on the page's rail:
   same left column, same language-and-years column, same sizes (admin,
   2026-11-12: the top of the tree is where the timeline gets tight). */
const roots = builtHtml.split('<li class="rung croot"').slice(1);
assert.equal(roots.length, 3, "three ancestors climb over 𐎨𐎡𐏂, as ladder rungs");
assert.ok(roots[0].includes('class="when-name kind-proto"') && roots[0].includes("Proto-Indo-European"),
  "the trunk is labelled with the ancestor's language, as in the ladder");
assert.ok(roots[0].includes("c. 4500–2500 BCE"), "and with the years it was in use");
assert.ok(roots[0].includes('class="rail"') && roots[0].includes('class="rung-body"'),
  "a root row is a rung, not a thinner sub-timeline");
/* Proto-Indo-European is the top of the family, not an unexplained form: the
   trail ends there without a ??? (2026-11-12). */
assert.ok(roots[0].includes("*kit-ró-s"), "the trunk ends at a Proto-Indo-European word");
assert.ok(!roots[0].includes("cunknown"), "and gets no ??? above it");
assert.ok(roots[0].includes("the top of the family"),
  "the row says which ending it is");
assert.ok(!builtHtml.includes('style="--gap:0"'),
  "a root rung takes its spacing from the sheet, not from a unitless zero");
assert.ok(!builtHtml.includes('class="cunknown"'),
  "nothing in this tree is unexplained");
/* A piece's *own* branch — the donor of a borrowed word, say — keeps the
   column form, because its language label stands beside the piece itself. */
const chain = chunk(builtHtml, "cnode");
assert.equal(chain.length, 1, "the borrowed piece's donor keeps its column above it");
assert.ok(chain[0].includes("kind-attested") && chain[0].includes("Old Median"),
  "a donor stage keeps the attested colour the ladder gives it");
assert.ok(chain[0].includes("Old Median *farnah — the record says the word was borrowed from here"),
  "a borrowed donor ends the other trunk and says so");
assert.ok(!/<span class="cwhen"><\/span>/.test(builtHtml),
  "the piece's own row carries no language label");
/* Every word of the timeline says what it means, ancestors included (admin,
   2026-11-12): the rung under a construction carries its dictionary sense the
   way the headword's own line carries its own, and a bound morpheme carries a
   description of what it does instead of a part of speech. */
const senseRung = roots.find((h) => h.includes("Proto-Iranian"));
assert.ok(senseRung && senseRung.includes('<span class="sense">adj · “visible”</span>'),
  "an ancestor rung prints the category and the sense under its word");
/* The tree is the step's last row: the horizontal line sits above the word it
   builds, so where the step ends is where its spine has to be measured from. */
const bodyHtml = builtHtml.slice(builtHtml.indexOf('class="buildbody">'));
assert.ok(!builtHtml.includes('class="steprow"'),
  "nothing but the tree stands in the step: the card that repeated its pieces is gone");
assert.ok(bodyHtml.includes('class="btrees"'),
  "the tree closes the step, so the spine is the step's own bottom");

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
assert.equal((unknownHtml.match(/class="cunknown"/g) || []).length, 1,
  "and only a word gets one: a bound morpheme has no line above it");
assert.ok(unknownHtml.includes("No record says where this word came from"),
  "and the ??? says what it means");
assert.ok(unknownHtml.includes("a suffix the stage's own registry lists, not a word"),
  "a bound morpheme is drawn as itself, with no trunk");
/* A bound morpheme has no word's sense, so its gloss is a description of what
   it does; it is printed as that description rather than quoted as a meaning
   (admin, 2026-11-12). */
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
assert.ok(suffixHtml.includes('<span class="cgloss">“to shine, glow”</span>'),
  "a root's sense is quoted, and a root names no category it has not got");
assert.ok(chunk(unknownHtml, "cpiece")[0].includes("has-chain") === false,
  "the bound piece keeps no branch column of its own");
/* A dot marks a word whose own line continues above it.  A bound morpheme has
   no line above it, so it wears none — the line reaches it from the `+` and
   stops.  Its cell still holds the rail column, or the word would slide into
   the 18px track and off the shared line (admin, 2026-11-12). */
const dots = (html) => (html.match(/class="crail" aria-hidden="true"><i><\/i><\/span>/g) || []).length;
assert.equal(dots(suffixHtml), 0, "no dot is drawn before a suffix");
assert.ok(suffixHtml.includes('<span class="crail" aria-hidden="true"></span>'),
  "the suffix's cell keeps the rail column, empty");
assert.equal(dots(chunk(builtHtml, "cterm").join("")), 1,
  "only the piece with a line above it wears the dot, not the one the line ends on");
/* A suffix's gloss is a sentence, not a word: it is neither cut short nor
   forced onto one line that runs into the next piece (admin, 2026-11-12). */
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
   (admin, 2026-11-12, on why the *-e- becomes *r̥). */
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
   diamond, the first piece beside it, the line, the `+`, the rest (admin,
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
assert.equal((nestedHtml.match(/class="constructstep/g) || []).length, 2,
  "the built ancestor keeps its own construction step");
assert.ok(nestedHtml.includes('class="cdiamond"'),
  "a nested step is marked with the diamond too");
assert.ok(nestedText.indexOf("*keyt-") < nestedText.indexOf("*-rós")
          && nestedText.indexOf("*-rós") < nestedText.indexOf("*kit-ró-s"),
  "the pieces stand above the word they built");
assert.ok(nestedHtml.indexOf('class="constructstep') < nestedHtml.indexOf("*kit-ró-s"),
  "and the step is drawn above its word, never beside it");

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
   record states no origin does hang under a ??? (admin, 2026-11-12). */
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
   (admin, 2026-11-12), and the reader — not the page — chooses. */
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
   for a word whose page is not recorded (admin, 2026-11-12). */
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

/* A compound draws its pieces as a join (2026-11-09): the two origins meet
   only at the headword, and each piece's chain keeps its own language. */
const joinHtml = context.renderJoin({
  word: "astronaut", lang: "en", lang_name: "English",
  joins: [{ etym: "From astro- + -naut", pieces: [
    { form: "astro-", word: "astro-", lang: "en", gloss: "stars", pos: "prefix",
      ancestry: [{ lang: "grc", lang_name: "Ancient Greek", branch: "Greek", form: "ἄστρον" }] },
    { form: "-naut", word: "-naut", lang: "en", gloss: "traveller", pos: "suffix",
      ancestry: [{ lang: "grc", lang_name: "Ancient Greek", branch: "Greek", form: "ναύτης" }] },
  ] }],
});
assert.ok(joinHtml.includes("astro-") && joinHtml.includes("-naut"), "both pieces are printed");
assert.ok(joinHtml.includes("Ancient Greek"), "each piece names where it came from");
assert.ok(joinHtml.includes("astronaut"), "the join ends at the word itself");
assert.equal((joinHtml.match(/class="jrow"/g) || []).length, 2, "one row per piece");

/* A piece with no recorded ancestry is a source of its own: book + house is
   not "both from Middle Persian" when only the house has an ancestor. */
const mixedJoin = context.renderJoin({
  word: "کتابخانه", lang: "fa", lang_name: "Persian",
  joins: [{ etym: "From کتاب + خانه", pieces: [
    { form: "کتاب", word: "کتاب", lang: "fa", gloss: "book", pos: "noun", ancestry: [] },
    { form: "خانه", word: "خانه", lang: "fa", gloss: "house", pos: "noun",
      ancestry: [{ lang: "pal", lang_name: "Middle Persian", branch: "Iranian", form: "𐭡𐭩𐭲𐭠" }] },
  ] }],
});
assert.ok(mixedJoin.includes("and an unrecorded source"),
  "an unrecorded piece is named, not folded into the other piece's origin");
assert.ok(!mixedJoin.includes("both from Middle Persian"),
  "two pieces are never called one origin");

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
    period: { from: 633, to: 1100, window_note: "The dictionary does not date this word.",
              landmarks: [{ from: 633, to: 651, title: "Islamic conquest of Iran", note: "" }] } },
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
/* The admin asked for the pills to go: the record and the band are
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
assert.ok(!titleLine.includes("badge"), titleLine);
assert.ok(titleLine.includes('class="standsep"'), "the two claims are set apart without a box");

const backlogged = evaluate('reviewNote({lang:"peo",backlog:[{kind:"etymon_missing",detail:"no headword"}]})');
assert.ok(backlogged.includes('class="backlognote"'), backlogged);
assert.ok(backlogged.includes("review backlog · 1"), "the count is the note");
assert.ok(backlogged.includes("#/backlog?lang=peo"), "it opens the backlog for this language");
assert.ok(!backlogged.includes("badge"), "the review note is not a pill either");
assert.strictEqual(evaluate('reviewNote({lang:"peo",backlog:[]})'), "", "nothing in the backlog, no note");

/* A page is what the server recorded, never a guess at a site (admin,
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
