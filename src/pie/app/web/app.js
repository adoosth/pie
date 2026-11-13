/* pie — small, dependency-free front end. */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const app = $("#app");

const BRANCH_COLORS = {
  Germanic: "var(--germanic)", Italic: "var(--italic)", Greek: "var(--greek)",
  "Indo-Iranian": "var(--indo-iranian)", "Balto-Slavic": "var(--balto-slavic)",
  Celtic: "var(--celtic)", Anatolian: "var(--anatolian)",
  Armenian: "var(--armenian)", Tocharian: "var(--tocharian)", Albanian: "var(--albanian)",
  Hellenic: "var(--greek)", "Palaeo-Balkan": "var(--palaeo-balkan)",
  "Contact / non-IE": "var(--other)", Other: "var(--other)",
};
const colorFor = (branch = "") => {
  const key = Object.keys(BRANCH_COLORS).find((k) => branch.startsWith(k));
  return BRANCH_COLORS[key] || "var(--other)";
};

/* A page load asks for the overview from three routes and for the word page
   on every click; the overview does not change while the tab is open.  Caching
   the promise means the second, third and fourth route render instantly, and
   a failed request is retried rather than remembered. */
const apiCache = new Map();
async function api(path, params) {
  const url = new URL(path, location.origin);
  Object.entries(params || {}).forEach(([k, v]) => v != null && v !== "" && url.searchParams.set(k, v));
  const key = url.pathname + url.search;
  const cached = apiCache.get(key);
  if (cached) return cached;
  /* A 500 answers JSON too, and the old code cached that answer like any
     other: one bad request coloured the tab for as long as it stayed open.
     Only a successful reply is remembered, and the failure is thrown so the
     caller can say so (2026-11-12). */
  const pending = fetch(url).then((res) => {
    if (!res.ok) {
      const err = new Error(`${path} answered ${res.status}`);
      err.status = res.status;
      throw err;
    }
    return res.json();
  });
  apiCache.set(key, pending);
  try {
    return await pending;
  } catch (e) {
    apiCache.delete(key);
    throw e;
  }
}

async function post(path, body) {
  try {
    const res = await fetch(new URL(path, location.origin), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    const out = await res.json();
    /* A POST changes what a GET would answer — a stored pathway, a law
       switched off — and the page re-reads with the same URL, which the cache
       would answer from before the change.  Storing a pathway looked like a
       dead button for exactly this reason (2026-11-12, critic P1-6). */
    if (res.ok) apiCache.clear();
    return out;
  } catch (e) {
    return { error: String(e) };
  }
}

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
/* Words are written in their own script: Persian and Armenian read right to
   left, cuneiform and Greek do not. `dir="auto"` lets the browser run the bidi
   algorithm per word instead of forcing a left-to-right box around it. */
const RTL_CHARS = /[\u0590-\u05FF\u0600-\u06FF\u0700-\u074F\u0750-\u077F\u08A0-\u08FF\uFB1D-\uFDFF\uFE70-\uFEFF]/;
const isRTL = (s) => RTL_CHARS.test(String(s ?? ""));
/* Old Persian cuneiform is written left to right, but its signs are stacks of
   wedges drawn for print: a synthesised oblique at 21px smears three signs into
   one shape.  Upright and slightly apart is how the signs stay signs. */
const CUNEIFORM_CHARS = /[\u{103A0}-\u{103DF}]/u;
const scriptClass = (s) => (isRTL(s) ? "rtl" : CUNEIFORM_CHARS.test(String(s ?? "")) ? "cunei" : "");
/* Evidence is the whole point of the colour scheme (2026-11-07):
     attested  green, glowing — the word is in a text or a dictionary;
     literary  gold  — reconstructed in the literature, normally written *so;
     strong    orange — this repo rebuilt it, not in the literature, and every
                        law that applied is established;
     weak      red   — rebuilt here from a proposed/custom law, from no law at
                        all, or it contradicts a recorded cognate;
     missing   dark red — no glossary entry is spelled this way, so the form is
                        no word of the stage at all — it is only a form an
                        etymology row names (2026-11-12). */
/* A colour is a claim about how we know a word, so the claim is spelled out
   when the reader hovers the word itself (2026-11-07: no legend under
   the word any more — every form explains its own colour). */
const EVIDENCE_TEXT = {
  attested: "Attested.",
  literary: "Reconstructed in the literature — no text attests it; normally written with an asterisk (*).",
  strong: "Rebuilt by this repo — no recorded cognate here, but every law behind it is established.",
  weak: "Rebuilt by this repo — a proposed or custom law is behind it, or it contradicts a recorded form.",
  missing: "No entry for this word — nothing in the stage's glossary is spelled this way, so it is not a word of the stage.",
};
const EVIDENCE_WORD = {
  attested: "attested",
  literary: "reconstructed (*)",
  strong: "rebuilt here",
  weak: "rebuilt · tentative",
  missing: "no entry",
};
const evidenceTip = (ev) => EVIDENCE_TEXT[ev] || "";
/* The rule engine marks stress with the IPA token ˈ (and ˌ) before the
   syllable, while a dictionary writes the stressed vowel with an acute:
   Proto-Iranian *jráyah*, but the chain's own output for Old Persian came out
   drˈayah. A page is read, not computed, so every form is printed the
   dictionary way — for every vowel, long vowels included — while the server
   keeps the token it applies the laws to (2026-11-08). */
const STRESSED = "aeiouyæœøəɛɔɨɤɯɪʊɐɑɒɵʌʉɘ";
/* A syllabic sonorant is a syllable's nucleus too (r̥, l̩), so a dictionary
   puts the acute on it — Proto-Iranian *wŕ̥kah* for the engine's wˈr̥kah
   (2026-11-08). */
const SYLLABIC = "\u0325\u0329";
const pf = (w) => String(w == null ? "" : w)
  /* NFD first, so a long vowel (ō, ē, ā) is its base letter when the stress
     mark is matched; the acute goes after the vowel's own marks, because they
     share a combining class and would otherwise recompose to the wrong glyph
     (o + acute + macron is not ṓ; o + macron + acute is). */
  .normalize("NFD")
  .replace(new RegExp(`([ˈˌ])([${STRESSED}])([\\u0300-\\u036f]*)`, "g"),
    (_m, mark, vowel, marks) => vowel + marks + (mark === "ˈ" ? "\u0301" : "\u0300"))
  .replace(new RegExp(`([ˈˌ])([rlmnŋ])([${SYLLABIC}][\\u0300-\\u036f]*)`, "g"),
    (_m, mark, consonant, marks) => consonant + marks + (mark === "ˈ" ? "\u0301" : "\u0300"))
  .normalize("NFC");
/* A form opens its own page: the word page when a glossary holds it, and the
   "not recorded here" page otherwise (2026-11-08). */
const wordHref = (lang, w, known, via, sense) => {
  const qs = new URLSearchParams();
  if (!known) qs.set("ghost", "1");
  if (via) qs.set("via", via);
  /* A spelling may hold more than one word; a link that knows which one adds
     the sense, and one that does not lands on the page that lists them
     (2026-11-09). */
  if (sense && Number(sense) > 0) qs.set("sense", String(sense));
  const tail = qs.toString();
  /* `'` survives encodeURIComponent, and this href is written inside an
     onclick attribute in single quotes — so it is escaped here, once. */
  return `#/word/${encodeURIComponent(lang)}/${encodeURIComponent(w)}${tail ? `?${tail}` : ""}`
    .replace(/'/g, "%27");
};
/* A word of a reconstructed stage is a reconstruction, and the literature
   writes it with a leading asterisk — on the word itself, not only on the label.
   One test answers for every renderer (admin, 2026-11-12): the stage's own
   `kind` from the registry, a stage whose script is reconstructed, and only as a
   last resort the code's `-pro` suffix.  When each renderer tested for itself,
   the same word printed with its star in one place and bare in another — a
   piece linked to /gem-pro/*anda- beside a rung that read `andaswarō`.
   `written()` in src/pie/attestation.py is the same rule on the server, so the
   page title, the record and the pieces cannot disagree. */
const reconStage = (lang, kind, script) => kind === "proto"
  || script === "reconstructed" || /-pro$/.test(String(lang || ""));
const starred = (w, lang, kind, script) => {
  const s = String(w == null ? "" : w);
  if (!s || s.startsWith("*")) return s;
  return reconStage(lang, kind, script) ? "*" + s : s;
};
/* A law is a claim, so it opens: every law named on a page — established or
   proposed — is a link to its own page (2026-11-08). The key names
   the transition as well as the rule, because rule ids repeat across stages. */
const lawHref = (key, id, from, to) => {
  const k = key || (id && from && to ? `${from}~${to}:${id}` : id || "");
  return k ? `#/rule/${encodeURIComponent(k)}` : "";
};
const lawLink = (name, key, id, from, to, cls = "lawname") => {
  const href = lawHref(key, id, from, to);
  return href ? `<a class="${cls}" href="${href}" data-tip="Open this law's page">${esc(name)}</a>`
    : `<span class="${cls}">${esc(name)}</span>`;
};
/* The coverage table prints a law as its id and its one-line claim, so it
   hands `lawLink` markup — which `lawLink` escapes, correctly, because a law's
   name may contain a `<`. Build that cell here instead (2026-11-08: the page
   was printing the raw `<span class="rid mono">…`). */
function lawCell(r) {
  const body = `<span class="rid mono">${esc(r.id)}</span> <span class="sub">${esc(r.name)}</span>`;
  const href = lawHref(null, r.id, r.from, r.to);
  return href ? `<a class="lawopen" href="${href}" data-tip="Open this law's page">${body}</a>` : body;
}
const form = (w, lang, opts = {}) => {
  const proto = reconStage(lang, opts.kind, opts.script) && !String(w).startsWith("*");
  /* `matched` marks the form the registered laws hit exactly: it glows, and a
     small ✓ disc on the corner of the word says so in a way colour alone
     cannot (2026-11-07). The disc lives inside the form box, so it pins itself
     to that form's top-right corner whatever the line does. */
  const cls = ["form", proto ? "recon" : "", scriptClass(w), opts.ev ? `ev-${opts.ev}` : "",
               opts.matched ? "matched" : ""]
    .filter(Boolean).join(" ");
  const tip = opts.tip || evidenceTip(opts.ev);
  const attrs = [
    `class="${cls}"`, 'dir="auto"',
    tip ? `data-tip="${esc(tip)}"` : "",
    opts.focus && !opts.href ? 'tabindex="0"' : "",
  ].filter(Boolean).join(" ");
  const disc = opts.cornerTick
    ? `<i class="matchdot" aria-label="matches the record">✓</i>`
    : opts.cornerWarn
      ? `<i class="unmatchdot" aria-label="match not verified">⚠</i>` : "";
  /* `mark` is the piece a formation law added (the animal suffix, the *-nah
     of دیوانه): it is printed in the accent colour, so the morpheme a law gave
     the word is visible inside the word itself (2026-11-08). */
  const shown = pf(starred(w, lang, opts.kind, opts.script));
  const at = opts.mark ? shown.indexOf(opts.mark) : -1;
  const text = at < 0
    ? esc(shown)
    : `${esc(shown.slice(0, at))}<i class="affix" data-tip="added by a formation law">${esc(opts.mark)}</i>${esc(shown.slice(at + opts.mark.length))}`;
  const box = `<span ${attrs}>${text}${disc}</span>`;
  const linked = opts.href
    ? `<a class="formlink" href="${esc(opts.href)}"${opts.hrefTip ? ` title="${esc(opts.hrefTip)}"` : ""}>${box}</a>`
    : box;
  /* The corner mark belongs to the word, not to the stack: a recorded word's
     reading can be wider than the word itself, so anchoring the mark to the
     whole stack floated it off an RTL word (2026-11-08). The word
     and its mark share one inline box; the reading sits outside it. */
  const marked = opts.markHtml
    ? `<span class="formblock">${linked}${opts.markHtml}</span>` : linked;
  return opts.stack
    ? `<span class="formstack">${marked}${readingOf(opts)}</span>`
    : `${marked}${readingOf(opts)}`;
};
/* A form written in a script prints its **romanisation** — how the word is read,
   which is the layer linguists cite — and, beside it, the **transliteration**
   of the signs (g-r-g for گرگ, v-r-k-a-n for 𐎺𐎼𐎣𐎠𐎴, admin
   2026-11-13).  IPA used to stand in for the romanisation, which put a phonetic
   transcription of a dead language where the standard reading belongs; it is
   optional, it is stored per word, and a timeline never prints it.  A scripted
   form is never printed bare, and an automatic reading keeps its own colour so
   a reader can tell what a dictionary states from what the signs spell. */
const readingOf = (o) => {
  if (!o) return "";
  const tip = o.note || (o.auto
    ? "No reading recorded — read from the script automatically."
    : "Romanisation — recorded for this word");
  const bits = [];
  /* `show === false` suppresses the *reading* (the rung already prints it, or
     the word is a Latin form whose reading would repeat it).  The sign layer
     is a different fact and always prints for a scripted word: a script with
     no transliteration is unreadable (admin, 2026-11-13). */
  if (o.reading && o.show !== false) {
    bits.push(`<span class="reading${o.auto ? " auto" : ""}" data-tip="${esc(tip)}">${esc(o.reading)}</span>`);
  }
  /* What the signs spell: not a pronunciation, so it is printed smaller and
     never as “the” reading.  A sign layer that repeats the romanisation says
     nothing and is dropped. */
  if (o.signs && o.signs !== o.reading) {
    bits.push(`<span class="reading signs" data-tip="Transliteration — what the signs spell, sign by sign. It is not a pronunciation.">${esc(o.signs)}</span>`);
  }
  /* IPA is a third, optional layer: a phonetic note the dictionary adds to a
     word, never a substitute for its reading.  A rung does not ask for it. */
  if (o.ipa) {
    bits.push(`<span class="reading ipa" data-tip="IPA — recorded for this word">/${esc(String(o.ipa).replace(/^\/|\/$/g, ""))}/</span>`);
  }
  return bits.join("");
};
const formOpts = (f) => ({
  ev: f.evidence,
  reading: f.reading || (f.r && f.r !== f.w ? f.r : ""),
  /* The second Latin layer travels with the form, and so does the optional
     IPA; a rung simply never passes one (admin, 2026-11-13). */
  signs: f.signs || "",
  ipa: f.ipa || "",
  auto: !!f.reading_auto,
  note: f.reading_note || "",
  show: f.show_reading !== false || (f.r && f.r !== f.w),
});
const badge = (tier) => `<span class="badge ${tier}">${tier}</span>`;

/* One tooltip element for the whole page: native `title` cannot be styled and
   is clipped by the scroll boxes around wide tables, so hovered forms are
   explained by a single fixed layer instead. Created lazily, so the render
   tests can load this file without a browser. */
let tipEl = null;
function showTip(target) {
  if (!tipEl) {
    tipEl = document.createElement("div");
    tipEl.className = "tip";
    tipEl.setAttribute("role", "tooltip");
    document.body.appendChild(tipEl);
  }
  tipEl.textContent = target.dataset.tip;
  tipEl.classList.add("on");
  const r = target.getBoundingClientRect();
  const w = tipEl.offsetWidth, h = tipEl.offsetHeight;
  const x = Math.min(Math.max(8, r.left + r.width / 2 - w / 2), window.innerWidth - w - 8);
  const below = r.bottom + 12 + h < window.innerHeight;
  tipEl.style.left = `${Math.round(x)}px`;
  tipEl.style.top = `${Math.round(below ? r.bottom + 12 : r.top - h - 12)}px`;
}
function hideTip() { if (tipEl) tipEl.classList.remove("on"); }
const tipTarget = (e) => (e.target && e.target.closest ? e.target.closest("[data-tip]") : null);
document.addEventListener("pointerover", (e) => { const t = tipTarget(e); if (t && !pinned) showTip(t); });
document.addEventListener("pointerout", (e) => { if (tipTarget(e) && !pinned) hideTip(); });
document.addEventListener("focusin", (e) => { const t = tipTarget(e); if (t) showTip(t); });
document.addEventListener("focusout", hideTip);
/* A tap is not a hover: on a touch screen ``pointerover`` and ``pointerout``
   fire together, so the sentence vanished before it was read, and most of the
   spans that carry one cannot take focus.  A tap now pins the tip until the
   next tap on something else (2026-11-12, critic P1-5). */
let pinned = null;
document.addEventListener("pointerdown", (e) => {
  const t = tipTarget(e);
  if (e.pointerType === "mouse" && !t) return;
  if (pinned && pinned !== t) { pinned = null; hideTip(); }
  if (!t) return;
  if (pinned === t) { pinned = null; hideTip(); return; }
  pinned = t;
  showTip(t);
});
window.addEventListener("scroll", hideTip, true);

/* ------------------------------------------------------------------ */
/* routing                                                             */
/* ------------------------------------------------------------------ */
const routes = [
  [/^\/$/, () => viewHome()],
  [/^\/search\/?$/, (m, q) => viewSearch(q)],
  [/^\/word\/([^/]+)\/(.+)$/, (m, q, p) => viewWord(decodeURIComponent(m[1]), decodeURIComponent(m[2]), p)],
  [/^\/tree\/?$/, () => viewTree()],
  [/^\/glossary\/?$/, (m, q, p) => viewGlossary(p)],
  [/^\/rules\/?$/, (m, q, p) => viewRules(p)],
  [/^\/rule\/(.+)$/, (m, q, p) => viewRule(decodeURIComponent(m[1]))],
  [/^\/lab\/?$/, (m, q, p) => viewLab(p)],
  [/^\/cognates\/?$/, (m, q, p) => viewCognates(p)],
  [/^\/cognate\/(.+)$/, (m, q, p) => viewCognate(decodeURIComponent(m[1]))],
  [/^\/compare\/?$/, (m, q, p) => viewCompare(p)],
  [/^\/coverage\/?$/, () => viewCoverage()],
  [/^\/backlog\/?$/, (m, q) => viewBacklog(q)],
  [/^\/about\/?$/, () => viewAbout()],
];

function parseQuery(s) { return new URLSearchParams(s || ""); }

/* Wide tables scroll inside their own box, so a phone never scrolls sideways. */
function wrapTables(root) {
  root.querySelectorAll("table").forEach((t) => {
    if (t.parentElement && t.parentElement.classList.contains("tablewrap")) return;
    const wrap = document.createElement("div");
    wrap.className = "tablewrap";
    t.replaceWith(wrap);
    wrap.appendChild(t);
  });
}

let lastWordKey = "";
let pendingScroll = null;
let lastHref = "";

async function route() {
  lastHref = location.href;
  const raw = location.hash.slice(1) || "/";
  const [path, qs] = raw.split("?");
  const params = parseQuery(qs);
  for (const [re, fn] of routes) {
    const m = path.match(re);
    if (m) {
      const navKey = path.split("/")[1] || "search";
      document.querySelectorAll("#nav a").forEach((a) => a.classList.toggle("active", a.dataset.route === navKey));
      app.classList.remove("enter");
      app.setAttribute("aria-busy", "true");
      /* A look-up should feel immediate: show the shape of the page while the
         derivation is computed instead of leaving the previous page frozen.
         Switching a law off re-renders the same word, so it must not flash. */
      const wordKey = /^\/word\//.test(path) ? path : "";
      if (wordKey && wordKey !== lastWordKey) {
        app.innerHTML = `<div class="skeleton" aria-hidden="true">
          <i style="width:32%;height:14px"></i>
          <i style="width:46%;height:44px;margin-top:14px"></i>
          <i style="width:24%"></i>
          <i style="width:78%"></i><i style="width:64%"></i><i style="width:70%"></i>
          <i style="width:52%"></i><i style="width:84%"></i><i style="width:38%"></i>
        </div>`;
      }
      try { await fn(m, params, params); } catch (e) { app.innerHTML = `<p class="error">${esc(e)}</p>`; }
      lastWordKey = wordKey;
      app.setAttribute("aria-busy", "false");
      wrapTables(app);
      /* Restart the page transition even when the route does not change. */
      void app.offsetWidth;
      app.classList.add("enter");
      /* A law switch re-renders in place: keep the reader where they were. */
      if (pendingScroll != null) { window.scrollTo(0, pendingScroll); pendingScroll = null; }
      else window.scrollTo(0, 0);
      return;
    }
  }
  app.innerHTML = `<p class="empty">Not found.</p>`;
}
/* Hash links and the Back button both land here. Some browsers fire
   `hashchange` *and* `popstate` when history entries differ only by a hash, so
   the duplicate is dropped: a page never renders twice for one navigation. */
const routeOnce = () => { if (location.href !== lastHref) route(); };
window.addEventListener("hashchange", routeOnce);
window.addEventListener("popstate", () => {
  /* Back to another state of the same word — a law switched on or off, an
     edited form — should keep the reader where they were. */
  if (/#\/word\//.test(location.hash) && /#\/word\//.test(lastHref)) {
    pendingScroll = window.scrollY;
  }
  routeOnce();
});
window.addEventListener("DOMContentLoaded", route);

/* A tab keeps the script it was loaded with, so a fix published while a page
   is open is invisible to the reader — a link that used to do nothing keeps
   doing nothing until a reload. Ask the server for the build once a minute and
   say so; when the tab is in the background, reload it there and then. */
let buildStamp = "";
async function checkBuild() {
  try {
    const r = await fetch("/api/version", { cache: "no-store" });
    const v = (await r.json()).app;
    /* The stamp names the script *and* the measurement, so a rerun of
       tools/coverage.py reaches an open tab too: the cached /api/coverage and
       /api/glossary payloads are dropped and the page is redrawn instead of
       showing yesterday's colours until a reload (2026-11-12, critic P1-6). */
    if (buildStamp && v !== buildStamp) apiCache.clear();
    if (!buildStamp) { buildStamp = v; return; }
    if (v === buildStamp) return;
    if (document.hidden) { location.reload(); return; }
    const chip = $("#buildrefresh");
    if (chip) { chip.hidden = false; chip.onclick = () => location.reload(); }
  } catch (e) { /* offline, or an older server: nothing to do */ }
}
checkBuild();
setInterval(checkBuild, 60000);
document.addEventListener("visibilitychange", () => { if (!document.hidden) checkBuild(); });

$("#q").addEventListener("keydown", (e) => {
  if (e.key === "Enter") { location.hash = `#/search?q=${encodeURIComponent(e.target.value)}`; }
});
document.addEventListener("keydown", (e) => {
  if (e.key === "/" && document.activeElement !== $("#q") && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) {
    e.preventDefault(); $("#q").focus(); $("#q").select();
  }
});

/* Light is the default; the toggle flips the attribute the palette hangs on and
   remembers the choice. The button shows the theme it will switch *to*. */
function paintThemeButton() {
  const btn = $("#theme");
  if (!btn) return;
  const root = document.documentElement || {};
  const dark = ((root.dataset || {}).theme) === "dark";
  btn.classList.toggle("is-dark", dark);
  btn.title = dark ? "Switch to light" : "Switch to dark";
  btn.setAttribute("aria-pressed", String(dark));
}
function wireTheme() {
  const btn = $("#theme");
  if (!btn) return;
  paintThemeButton();
  btn.onclick = () => {
    const el = document.documentElement;
    const next = el.dataset.theme === "dark" ? "light" : "dark";
    el.dataset.theme = next;
    try { localStorage.setItem("pie-theme", next); } catch (e) { /* nothing to save to */ }
    paintThemeButton();
  };
}
wireTheme();

/* ------------------------------------------------------------------ */
/* home                                                                */
/* ------------------------------------------------------------------ */
/* The home page is one search box and a few real destinations under it
   (2026-11-08: "a big section like 'search for any word' … and some
   examples below it but nothing else"). Each example is a page that already
   works — a word, a PIE etymon, a Persian word — so the interface teaches by
   landing somewhere true rather than by explaining itself. */
const HOME_EXAMPLES = [
  { href: "#/word/en/night", word: "night", note: "English · PIE *nókʷts" },
  { href: "#/word/ine-pro/wĺ̥kʷos", word: "wĺ̥kʷos", note: "PIE · the wolf" },
  { href: "#/word/fa/گربه", word: "گربه", note: "Persian · “cat”" },
  { href: "#/word/fa/گرگ", word: "گرگ", note: "Persian · “wolf”" },
];

async function viewHome() {
  const o = await api("/api/overview");
  const s = o.stats;
  const langs = Object.fromEntries((o.languages || []).map((l) => [l.id, l]));
  app.innerHTML = `
    <section class="home">
      <h1>Search for any word</h1>
      <p class="home-lede">${(s.words || 0).toLocaleString()} words in ${s.languages} languages and
        stages, from Proto-Indo-European down. A word, a proto-form, or a meaning.</p>
      <form class="homeseek" id="home-form" role="search" autocomplete="off">
        <input id="home-q" name="q" dir="auto" aria-label="Search for any word"
               placeholder="foot · *pṓds · پدر · water">
        <button class="primary" type="submit" aria-label="Search">Search</button>
      </form>
      <div id="home-suggest" class="suggest" role="listbox" aria-label="Suggestions"></div>
      <div class="home-examples">
        ${HOME_EXAMPLES.map((e) => `<a class="home-example" href="${esc(e.href)}">
          <span class="he-word" dir="auto">${esc(e.word)}</span>
          <span class="he-note">${esc(e.note)}</span></a>`).join("")}
      </div>
    </section>`;
  const input = $("#home-q");
  const list = $("#home-suggest");
  const go = (q) => { location.hash = `#/search?q=${encodeURIComponent(q)}`; };
  $("#home-form").onsubmit = (e) => { e.preventDefault(); if (input.value.trim()) go(input.value.trim()); };
  let seq = 0;
  let timer = null;
  let rows = [];
  let active = -1;
  const paint = () => {
    if (!rows.length) { list.innerHTML = ""; list.classList.remove("on"); return; }
    list.classList.add("on");
    list.innerHTML = rows.map((r, i) => {
      const names = langs[r.lang] || {};
      return `<a class="sug${i === active ? " active" : ""}" role="option" aria-selected="${i === active}"
        href="${esc(wordHref(r.lang, r.word, true, "", r.senses > 1 ? r.sense : 0))}" data-i="${i}">
        <span class="sug-word" dir="auto">${esc(r.word)}</span>
        <span class="sug-lang">${esc(names.name || r.lang)}</span>
        <span class="sug-gloss">${esc(r.gloss || "")}</span></a>`;
    }).join("");
  };
  const ask = async () => {
    const q = input.value.trim();
    active = -1;
    if (q.length < 1) { rows = []; paint(); return; }
    const mine = ++seq;
    let out = [];
    try { out = await api("/api/suggest", { q, limit: 7 }); } catch (e) { out = []; }
    if (mine !== seq) return;
    rows = Array.isArray(out) ? out : [];
    paint();
  };
  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(ask, 110);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { rows = []; paint(); return; }
    if (!rows.length) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      active = (active + (e.key === "ArrowDown" ? 1 : rows.length - 1)) % rows.length;
      paint();
    } else if (e.key === "Enter" && active >= 0) {
      e.preventDefault();
      location.hash = wordHref(rows[active].lang, rows[active].word, true, "", rows[active].senses > 1 ? rows[active].sense : 0);
    }
  });
  input.focus();
}

/* ------------------------------------------------------------------ */
/* search                                                              */
/* ------------------------------------------------------------------ */
async function viewSearch(params) {
  const q = params.get("q") || "";
  const lang = params.get("lang") || "";
  const o = await api("/api/overview");
  const langs = o.languages.filter((l) => l.words > 0).sort((a, b) => a.name.localeCompare(b.name));
  app.innerHTML = `
    <h1>Words</h1>
    <p class="sub">Search ${o.stats.words.toLocaleString()} glossary entries by form or meaning.</p>
    <div class="searchbox">
      <input id="sq" dir="auto" value="${esc(q)}" placeholder="word or meaning">
      <select id="slang"><option value="">all languages</option>
        ${langs.map((l) => `<option value="${l.id}" ${l.id === lang ? "selected" : ""}>${esc(l.name)}</option>`).join("")}
      </select>
      <button class="primary" id="sgo">Search</button>
    </div>
    <div id="results"></div>`;
  const run = async () => {
    const query = $("#sq").value.trim();
    if (!query) return;
    history.replaceState(null, "", `#/search?q=${encodeURIComponent(query)}&lang=${$("#slang").value}`);
    const rows = await api("/api/search", { q: query, lang: $("#slang").value, limit: 60 });
    $("#results").innerHTML = rows.length ? `
      <table><thead><tr><th>form</th><th>language</th><th>pos</th><th>meaning</th></tr></thead><tbody>
      ${rows.map((r, i) => `<tr class="click reveal" style="--i:${Math.min(i, 16)}" tabindex="0"
        onclick="location.hash='${esc(wordHref(r.lang, r.word, true, "", r.senses > 1 ? r.sense : 0))}'"
        onkeydown="if(event.key==='Enter')location.hash='${esc(wordHref(r.lang, r.word, true, "", r.senses > 1 ? r.sense : 0))}'">
        <td>${form(r.written || r.word, r.lang, { ...formOpts(r), href: wordHref(r.lang, r.word, true, "", r.senses > 1 ? r.sense : 0) })}${r.senses > 1 ? `<span class="sense no" data-tip="Word ${r.sense} of ${r.senses} with this spelling">${r.sense}</span>` : ""}</td><td>${esc(langName(o, r.lang))}</td>
        <td class="sub">${esc(r.pos)}</td><td>${esc((r.gloss || []).join("; "))}</td></tr>`).join("")}
      </tbody></table>` : `<p class="empty">Nothing found for “${esc(query)}”.</p>`;
    wrapTables($("#results"));
    void $("#results").offsetWidth;
    $("#results").classList.add("enter");
  };
  $("#sgo").onclick = run;
  $("#sq").addEventListener("keydown", (e) => { if (e.key === "Enter") run(); });
  if (q) run();
}
const langName = (o, id) => (o.languages.find((l) => l.id === id) || {}).name || id;

/* ------------------------------------------------------------------ */
/* glossary: one stage's headwords, each a door to its word page         */
/* ------------------------------------------------------------------ */
/* This replaces the separate cognate-set page (2026-11-08): a
   word or root glossary that opens the word view again. Roots come first for
   Proto-Indo-European, because a root is what the family is built on. */
async function viewGlossary(params) {
  const lang = (params && params.get("lang")) || "ine-pro";
  /* The default view leaves non-PIE words out (2026-11-09).  "All
     words" is an explicit choice, so it is written into the address as
     `band=all`; a missing `band` means the default, not "everything". */
  const rawBand = params && params.get("band");
  const band = rawBand === "all" ? "" : (rawBand || "pie");
  const o = await api("/api/overview");
  const langs = o.languages.filter((l) => l.words > 0).sort((a, b) => a.name.localeCompare(b.name));
  const q = (params && params.get("q")) || "";
  /* A stage of 17,000 words is read in pages (admin, 2026-11-13): the address
     carries which one, so a page can be linked, bookmarked and stepped back
     from with the browser's Back button like any other view. */
  const page = Math.max(1, parseInt((params && params.get("page")) || "1", 10) || 1);
  const g = await api("/api/glossary", { lang, limit: 400, band: band || null, q: q || null, page });
  const rows = g.rows || [];
  /* Transcription and transliteration are optional columns: a stage that
     writes its words as they sound (Middle Persian) has nothing to add beside
     the form, and a stage whose spelling is the form itself needs no second
     copy of it (admin, 2026-11-13). */
  const formCell = (r) => r.written || r.word || "";
  const optValue = (r, field) => {
    const value = r[field] || "";
    return value && value !== formCell(r) ? value : "";
  };
  const showTranscription = rows.some((r) => optValue(r, "transcription"));
  const showTransliteration = rows.some((r) => optValue(r, "transliteration"));
  const transcriptionTip = "Transcription — how the word sounds, as the record transcribes it. It is not the recorded spelling.";
  const transliterationTip = "Transliteration — how the word is written in Latin letters. It is not a pronunciation.";
  /* On a phone the two columns are hidden; the same facts stand on a second
     line under the form instead, so the table never widens the page. */
  const phoneNotes = (r) => {
    const parts = [];
    if (showTranscription && optValue(r, "transcription")) {
      parts.push(`<span data-tip="${esc(transcriptionTip)}"><span class="glossmore-label">transcription</span> ${esc(optValue(r, "transcription"))}</span>`);
    }
    if (showTransliteration && optValue(r, "transliteration")) {
      parts.push(`<span data-tip="${esc(transliterationTip)}"><span class="glossmore-label">transliteration</span> ${esc(optValue(r, "transliteration"))}</span>`);
    }
    return parts.length ? `<span class="glossmore">${parts.join("<i> · </i>")}</span>` : "";
  };
  /* The same six colours as the coverage page (2026-11-09): every
     headword is painted with its band, read from the published measurement so
     the list and the numbers cannot disagree.  A proto stage has no band, and
     the counts beside the legend are over the whole stage, not the page. */
  const defs = (o.coverage && o.coverage.definitions) || {};
  const bandLabel = (k) => (k === "pie" ? "PIE words"
    : ((defs[k] || CAT_FALLBACK[k] || {}).label) || k);
  const bandTip = (k) => {
    if (k === "pie") return "PIE words — every headword the record keeps inside the Indo-European family. "
      + "Words borrowed from outside it (Arabic, Turkic, Semitic…) are hidden; choose all words to see them.";
    const d = defs[k] || CAT_FALLBACK[k] || {};
    return d.label && d.definition ? `${d.label} — ${d.definition}` : bandLabel(k);
  };
  const counts = g.counts || {};
  const stageTotal = g.stage_total || g.total || 0;
  const pieCount = Math.max(0, stageTotal - (counts.non_pie || 0));
  const legendKeys = ["full", "adjusted", "partial", "unexplained", "non_pie", "ie_loan", "built"]
    .filter((k) => counts[k]);
  const bandOptions = [...legendKeys, ...Object.keys(counts).filter((k) => !legendKeys.includes(k))];
  const goto = (nextLang, nextBand) => {
    const q = [`lang=${encodeURIComponent(nextLang)}`];
    q.push(`band=${encodeURIComponent(nextBand || "all")}`);
    location.hash = `#/glossary?${q.join("&")}`;
  };
  /* The pager: the same list, one page further on.  A new language, band or
     spelling filter starts again at the first page; only `next`/`previous`
     carry `page`. */
  const pageHref = (n) => {
    const parts = [`lang=${encodeURIComponent(lang)}`, `band=${encodeURIComponent(band || "all")}`];
    if (q) parts.push(`q=${encodeURIComponent(q)}`);
    if (n > 1) parts.push(`page=${n}`);
    return `#/glossary?${parts.join("&")}`;
  };
  const pager = () => {
    const pages = g.pages || 1;
    const cur = g.page || 1;
    if (pages <= 1) return "";
    const step = (n, label) => (n < 1 || n > pages)
      ? `<span class="pagebtn off">${label}</span>`
      : `<a class="pagebtn" href="${esc(pageHref(n))}">${label}</a>`;
    return `<nav class="glosspager" aria-label="Pages of the glossary">
      ${step(1, "first")}${step(cur - 1, "previous")}
      <span class="pagepos">page <b>${cur.toLocaleString()}</b> of ${pages.toLocaleString()}
        · words ${(g.first || 0).toLocaleString()}–${(g.last || 0).toLocaleString()}
        of ${(g.total || 0).toLocaleString()}</span>
      ${step(cur + 1, "next")}${step(pages, "last")}</nav>`;
  };
  app.innerHTML = `
    <h1>Glossary</h1>
    <p class="sub">Every headword of one stage, each opening its own page — the ladder, the branch below it
      and the laws that carried it. ${g.roots ? `${g.roots} roots are listed first.` : ""}</p>
    <div class="searchbox">
      <input id="gq" dir="auto" value="${esc(q)}" placeholder="filter by spelling" aria-label="Filter the glossary by spelling">
      <select id="glang" aria-label="Language">
        ${langs.map((l) => `<option value="${esc(l.id)}"${l.id === lang ? " selected" : ""}>${esc(l.name)}</option>`).join("")}
      </select>
      ${bandOptions.length ? `<select id="gband" aria-label="Word category">
        <option value="pie"${band === "pie" ? " selected" : ""} title="${esc(bandTip("pie"))}">PIE words · ${pieCount.toLocaleString()}</option>
        <option value="all"${band ? "" : " selected"} title="Every headword of this stage, non-PIE words included.">all words · ${stageTotal.toLocaleString()}</option>
        ${bandOptions.map((k) => `<option value="${esc(k)}"${k === band ? " selected" : ""} title="${esc(bandTip(k))}">${esc(bandLabel(k))} · ${(counts[k] || 0).toLocaleString()}</option>`).join("")}
      </select>` : ""}
    </div>
    <p class="sub gloss-count">${(g.total || 0).toLocaleString()} words${
      g.headwords && g.headwords !== g.total
        ? ` · ${g.headwords.toLocaleString()} spellings, a few of them holding more than one word` : ""}${
      band === "pie" && bandOptions.length ? " · PIE words only, non-PIE hidden"
        : band ? ` · ${esc(bandLabel(band).toLowerCase())}` : ""}${
      q ? ` · filtered to “${esc(q)}”` : ""}${
      g.banded && rows.length > g.banded ? ` · ${(rows.length - g.banded).toLocaleString()} not banded (reconstructions, and forms the counter leaves out)` : ""}</p>
    ${legendKeys.length ? `<p class="glosslegend" title="Each word is painted with its coverage band, from the same measurement as the coverage page. The numbers count words of this whole stage. A spelling that carries several words is listed once per word, numbered; the coverage page counts them the same way">${legendKeys.map((k) => `<span><i class="${bandClass(k)}"></i>${esc(bandLabel(k))} <b>${(counts[k] || 0).toLocaleString()}</b></span>`).join("")}</p>` : ""}
    ${pager()}
    ${rows.length ? `<table class="glosslist"><thead><tr><th>form</th>${
      showTranscription ? `<th class="glossopt" data-tip="${esc(transcriptionTip)}">transcription</th>` : ""
    }${
      showTransliteration ? `<th class="glossopt" data-tip="${esc(transliterationTip)}">transliteration</th>` : ""
    }<th>status</th><th>pos</th><th>meaning</th></tr></thead><tbody>
      ${rows.map((r, i) => `<tr class="click reveal" style="--i:${Math.min(i, 16)}" tabindex="0"
        onclick="location.hash='${wordHref(lang, r.word, true, "", r.senses > 1 ? r.sense : 0)}'"
        onkeydown="if(event.key==='Enter')location.hash='${wordHref(lang, r.word, true, "", r.senses > 1 ? r.sense : 0)}'">
        <td><a class="mono glossword" href="${esc(wordHref(lang, r.word, true, "", r.senses > 1 ? r.sense : 0))}" dir="auto"${r.band ? ` style="--band:var(${bandVar(r.band)})" data-tip="${esc(bandTip(r.band))}"` : ""}>${esc(r.written || r.word)}</a>${r.senses > 1 ? `<span class="sense no" data-tip="This spelling is ${r.senses} words; this row is the ${r.sense}${r.sense === 1 ? "st" : r.sense === 2 ? "nd" : r.sense === 3 ? "rd" : "th"}.">${r.sense}</span>` : ""}
          ${!showTranscription && r.show_reading && r.reading ? `<span class="sub reading${r.reading_auto ? " auto" : ""}"${r.reading_auto ? ` data-tip="${esc(r.reading_note || "")}"` : ""}> ${esc(r.reading)}</span>` : ""}${phoneNotes(r)}</td>
        ${showTranscription ? `<td class="sub glossopt">${esc(optValue(r, "transcription") || "—")}</td>` : ""}
        ${showTransliteration ? `<td class="sub glossopt">${esc(optValue(r, "transliteration") || "—")}</td>` : ""}
        <td><span class="glstatus ${esc(ATTEST_BADGE[r.attestation] || "")}"
          data-tip="${esc((g.statuses || {})[r.attestation] || "")}">${esc(r.attestation || "—")}</span></td>
        <td class="sub">${esc(r.pos || "—")}</td>
        <td>${esc((r.gloss || []).join("; "))}</td></tr>`).join("")}
    </tbody></table>` : `<p class="empty">${band ? `No ${esc(bandLabel(band).toLowerCase())} in this stage.` : "This stage has no glossary entries."}</p>`}
    ${pager()}`;
  $("#glang").onchange = (e) => goto(e.target.value, band);
  /* The list is 92,000 words long; finding one by spelling is what the
     server's `q` is for, and until now the address could not carry it
     (2026-11-12). */
  const gq = $("#gq");
  const goq = () => {
    const parts = [`lang=${encodeURIComponent(lang)}`, `band=${encodeURIComponent(band || "all")}`];
    if (gq.value.trim()) parts.push(`q=${encodeURIComponent(gq.value.trim())}`);
    location.hash = `#/glossary?${parts.join("&")}`;
  };
  if (gq) {
    gq.addEventListener("keydown", (e) => { if (e.key === "Enter") goq(); });
    gq.addEventListener("change", goq);
  }
  const bs = $("#gband");
  if (bs) bs.onchange = (e) => goto(lang, e.target.value === "all" ? "" : e.target.value);
}

/* A spelling that holds several words shows them as a strip under the
   headword: the reader sees which one is open and can cross to another
   without going back through the list (2026-11-09). */
function senseStrip(d, lang) {
  const list = d.sense_list || [];
  if (list.length < 2) return "";
  return `<nav class="senses" aria-label="Which of these words">${
    list.map((s) => {
      const on = s.sense === d.sense;
      const label = (s.gloss || []).slice(0, 2).join("; ") || s.pos || "";
      return `<a class="sensesel${on ? " on" : ""}" href="${esc(wordHref(lang, d.word, true, "", s.sense))}"${
        on ? ' aria-current="true"' : ""} data-tip="${esc(`${s.sense} of ${list.length} · ${s.pos}`)}">
        <i>${s.sense}</i><span>${esc(label)}</span></a>`;
    }).join("")}</nav>`;
}

/* The landing page of a homograph: a reconstruction links to the spelling, and
   the record holds more than one word under it. Nothing is guessed — every
   sense is a door with its own meaning, part of speech, band and Wiktionary
   page (2026-11-09). */
function viewPick(d) {
  const defs = CAT_FALLBACK;
  const label = (k) => ((defs[k] || {}).label) || k;
  const card = (s, i) => {
    const band = s.band
      ? `<span class="senband" style="--band:var(${bandVar(s.band)})"><i></i>${esc(label(s.band))}</span>` : "";
    const meta = [s.reading ? `<span class="translit">${esc(s.reading)}</span>` : "",
                  s.ipa ? `<span class="ipa">/${esc(s.ipa.replace(/^\/|\/$/g, ""))}/</span>` : "",
                  s.pos ? `<span class="badge">${esc(s.pos)}</span>` : "",
                  s.recon ? `<span class="badge literary">reconstruction</span>` : ""]
      .filter(Boolean).join(" ");
    return `<li class="reveal" style="--i:${Math.min(i, 10)}">
      <a class="sensecard" href="${esc(wordHref(d.lang, d.word, true, "", s.sense))}">
        <span class="senseno">${s.sense}</span>
        <span class="sensebody">
          <span class="sensegloss">${esc((s.gloss || []).join("; ") || "—")}</span>
          <span class="sensemeta">${meta}</span>
        </span>
        ${band}
      </a>
      ${s.etym ? `<p class="sub senseetym">${esc(s.etym)}</p>` : ""}
    </li>`;
  };
  app.innerHTML = `
    <div class="wordgrid reveal">
      ${langRail(d)}
      <header class="wordhead">
        <div class="wordmain">
          <div class="headline">
            <span class="formblock headblock">
              <h1 id="headword" class="headword ${d.rtl ? "rtl" : ""}" dir="auto" lang="${esc(d.lang)}">${esc(attestedWord(d))}</h1>
            </span>
            ${attestNote(d.attestation)}
          </div>
          <div class="wordmeta">
            <span class="metaplain">${d.variants} words share this spelling</span>
          </div>
          ${sourceRow(d)}
        </div>
        <button class="ghost copy" data-copy="${esc(d.word)}" title="Copy this word">copy</button>
      </header>
    </div>
    <p class="gloss reveal" style="--i:1">This spelling is more than one word, pick one.</p>
    <ul class="senselist">${(d.senses || []).map(card).join("")}</ul>`;
  wireCopy();
}

/* ------------------------------------------------------------------ */
/* word page                                                           */
/* ------------------------------------------------------------------ */
async function viewWord(lang, w, params) {
  const off = ((params && params.get("off")) || "").split(",").filter(Boolean);
  const fromStage = (params && params.get("from")) || "";
  const fromForm = (params && params.get("form")) || "";
  /* The start was picked from the ancestors the word's own record names, not
     typed: `recorded=1` keeps it a record on the server and in the URL
     (2026-11-09). */
  const fromRecorded = !!((params && params.get("recorded") === "1") && fromStage && fromForm);
  const ghost = !!(params && params.get("ghost") === "1");
  const via = (params && params.get("via")) || "";
  /* A word may carry its own recorded pathway — a registered law that never
     applied to it. It is applied by default; `pathway=0` shows the laws
     unfiltered, and the page keeps that choice in the URL (2026-11-08). */
  const pathway = !(params && params.get("pathway") === "0");
  /* Which of the words this spelling carries (2026-11-09).  Absent means the
     link did not know — a reconstruction rung, a cognate row — and the server
     answers with the page that lists them. */
  const sense = Number((params && params.get("sense")) || 0) || 0;
  /* A suffix the reader tries on the timeline (`?suffix=eh2`) is sent with the
     first request, so the page opens straight on the hypothetical ladder. */
  const suffix = (params && params.get("suffix")) || "";
  const path = ((params && params.get("path")) || "").split(",").filter(Boolean);
  /* A formation the reader asked for at one stage (`?build=fa:join:خانه@آب`),
     sent with the first request so the page opens on the built ladder. */
  const build = (params && params.get("build")) || "";
  /* A word no glossary holds answers 404, and that is a page of its own
     ("no entry for …"), not a red line: only a real failure is rethrown
     (2026-11-12). */
  let d;
  try {
    d = await api("/api/word", {
    lang, w, off: off.join(","),
    from: fromStage || null, form: fromForm || null,
    recorded: fromRecorded ? "1" : null,
    ghost: ghost ? "1" : null, via: via || null,
    pathway: pathway ? null : "0",
    suffix: suffix || null,
    path: path.length ? path.join(",") : null,
    sense: sense || null,
    build: build || null,
  });
  } catch (e) {
    if (e.status !== 404) throw e;
    app.innerHTML = `<p class="empty">No entry for <b dir="auto">${esc(w)}</b> in ${esc(lang)}.
      <a href="#/search?q=${encodeURIComponent(w)}">Search for it</a>.</p>`;
    return;
  }
  if (d.error) {
    app.innerHTML = `<p class="empty">No entry for ${esc(w)} in ${esc(lang)}.</p>`;
    return;
  }
  if (d.ghost) { ladderState = null; viewGhost(d); return; }
  if (d.pick) { ladderState = null; viewPick(d); return; }
  /* One word, one address.  A spelling the stage writes another way (Middle
     Persian jaw for ǰaw, a Pahlavi transliteration for the reading it was
     quoted under) opens the entry, and the address follows the entry's own
     spelling, so the link a reader copies names the word the glossary holds
     (admin, 2026-11-13). */
  if (d.word && d.word !== w) {
    const tail = location.hash.split("?")[1];
    const url = `#/word/${encodeURIComponent(lang)}/${encodeURIComponent(d.word)}${tail ? `?${tail}` : ""}`;
    if (location.hash !== url) {
      history.replaceState(null, "", url);
      lastHref = location.href;
    }
  }
  /* The ladder is stateful: laws and the starting form are edited in place,
     and only the ladder re-renders — never the page. Proto-Indo-European has
     no ancestor, but it has a ladder all the same: one rung for the etymon,
     and below it the daughter stages each click carries it into (admin,
     2026-11-12). */
  const morph = d.morphology || { suffixes: [] };
  const fromSuffix = (params && params.get("suffix")) || "";
  ladderState = {
    lang, word: d.word, sense: d.sense || 0, off: new Set(off), pathway,
    /* How many words this spelling carries: the sense goes into the address
       only when there is a choice to keep (a spelling that is one word needs
       no `?sense=`, and a spelling that is several must keep the one open —
       the first included, or its link would open the list again). */
    variants: d.variants || 1,
    /* The stages the reader carried the timeline into, in order
       (`?path=pal,fa`); empty is the word's own ancestry only. */
    path: ((params && params.get("path")) || "").split(",").filter(Boolean),
    edit: fromStage && fromForm && !fromRecorded ? { stage: fromStage, form: fromForm } : null,
    /* A start the record itself names (the Proto-Iranian form the entry
       quotes): a record, not a hypothesis, so no edited badge. */
    record: fromRecorded ? { stage: fromStage, form: fromForm } : null,
    /* A suffix the reader picked on the timeline: the ladder then shows what
       the laws give with that morpheme instead of the word's own record
       (2026-11-08). */
    suffix: (params && params.get("suffix")) || "",
    /* A formation the reader asked for at one stage (`?build=fa:join:خانه@آب`):
       two words joined, or a word with a suffix or ending (2026-11-10). */
    build: (params && params.get("build")) || "",
    /* The construction row lives in the timeline now, so the ladder needs the
       language's morphology to redraw it after a law is switched (admin,
       2026-11-12). */
    morph, fromSuffix,
    data: d.hierarchy, context: d,
  };
  const cog = d.cognates;
  /* Keep Wiktionary's own order but mark the reading the sound laws produce:
     that is the one the ladder below compares against. */
  const matched = d.derivation && d.derivation.matched_form;
  /* A reading that repeats the headword adds nothing but a second copy of the
     title: Middle Persian garm *is* its reading, so the header printed "garm"
     beside "garm" (admin, 2026-11-13). */
  const readings = [d.translit, ...(d.translit_alt || [])]
    .filter((r) => r && r !== d.word && r !== d.written);
  const ev = d.evidence || "attested";
  /* The asterisk in front of a reconstructed word means one thing, so hovering
     it says one thing (admin, 2026-11-12): no text spells this word.  The long
     explanation is on the status beside it, which is where a reader asks what
     "recorded" means. */
  const starred = d.attestation && ["recorded", "proposed"].includes(d.attestation.status);
  const evTip = starred
    ? "No text spells this word."
    : (evidenceTip(ev) || "Recorded in a dictionary.");
  /* The headword carries the record mark too (2026-11-09): every word
     the record has a page for opens it from the title's own top-right corner,
     and a word the laws reproduce exactly wears its ✓ *below* that mark — the
     link and the match are two facts, so neither hides the other.  Before this
     the ✓ replaced the mark on a matched word and the entry became unreachable
     from the word itself. */
  /* The ✓ says the registered laws reproduce the word, so it may only appear
     when the ladder on this page says so.  A green band can also be earned by
     the writing layer (a spelling convention, not a law), and 221 pages wore a
     ✓ above a ladder that said "differs" — the band and the tick are two
     claims and both have to be true (2026-11-12, critic P0-2). */
  const headExact = ["full", "adjusted"].includes((d.category || {}).category)
    && !!(d.derivation && d.derivation.match);
  /* The ✓ says how the word was reached: letter for letter, or through the
     word's own signs when the record keeps a reading rather than a writing. */
  const tickTip = (d.category && d.category.via_script)
    ? "The laws reach a form the word's own signs allow, and the dictionary's reading agrees with it."
    : "The registered laws reproduce this word as the record writes it.";
  const headTick = headExact
    ? `<i class="matchdot headtick" data-tip="${esc(tickTip)}"
         aria-label="the laws reproduce this word">✓</i>` : "";
  app.innerHTML = `
    <div class="wordgrid reveal">
      ${langRail(d)}
      <header class="wordhead">
        <div class="wordmain">
          <div class="headline">
            <span class="formblock headblock">
              <h1 id="headword" class="headword ${d.rtl ? "rtl" : ""} ev-${esc(ev)}" dir="auto" tabindex="0"
                  lang="${esc(lang)}" data-tip="${esc(evTip)}"
                  ${d.script ? `title="${esc(d.script)}"` : ""}>${esc(attestedWord(d))}</h1>${headTick}
            </span>
            ${standing(d)}
            ${reviewNote(d)}
          </div>
          ${wordMeta(d, readings, matched, lang)}
          ${senseStrip(d, lang)}
          ${stepsNote(d)}
          ${sourceRow(d)}
        </div>
        <button class="ghost copy" data-copy="${esc(d.word)}" title="Copy this word">copy</button>
      </header>
      ${catRail(d)}
      ${meaningsBlock(d)}
      ${d.etymology ? `<div class="etym reveal" style="--i:2">
        <p class="sub"><span class="etym-label">Etymology</span>${esc(d.etymology)}</p>
        ${donorLine(d)}</div>` : ""}
      ${wiktionaryLine(d)}
    </div>

    ${/* One timeline for every word, Proto-Indo-European included. A borrowed
         word has two rungs and no sound laws — whether the donor is outside the
         family (Arabic into Persian) or inside it (English into Persian: the
         entry records a root *inside the donor's* etymology, and running this
         language's chain from it invented a PIE ladder for دایناسور; 2026-11-10). */
      `<section id="ladder" class="ladderbox">${d.loan && d.loan.name && (d.loan.kind || (d.category || {}).category === "non_pie")
          ? renderLoanLadder(d)
          : renderHierarchy(d.hierarchy, d, { d, morph, fromSuffix })}</section>
         <p id="ladder-status" class="sronly" role="status" aria-live="polite"></p>
         ${d.descendants ? renderBranch(d.descendants, { via: `${d.lang}/${d.word}`, claim: true }) : ""}`}
    ${(d.built_from || []).length ? renderBuiltFrom(d) : ""}
    ${cog ? `
      <details class="cogfold reveal">
        <summary><h2>Cognates <span class="sub" style="text-transform:none;letter-spacing:0">· ${form(cog.pie, "ine-pro", { ev: "literary" })} “${esc(cog.gloss)}” · ${cog.forms.length} forms in ${cog.branches} branches</span></h2></summary>
        ${renderCognateTable(cog, lang, d.word)}
      </details>
    ` : (d.is_root || (d.loan && d.loan.name)) ? ""
        : `<p class="sub" style="margin-top:18px">No Proto-Indo-European cognate set is recorded for this word.</p>`}
  `;
  wireLadder();
  wireMeanings(d);
  wireCopy();
}

/* What the Persian Wiktionary says about the word, kept visibly apart from
   this model's own etymology: the glossary's Persian words come from Dehkhoda,
   and the Persian Wiktionary is the page a reader can open. The quote is the
   site's sentence, never this model's analysis (admin, 2026-11-11). */
function wiktionaryLine(d) {
  const w = d.wiktionary;
  if (!w || !w.found) return "";
  const link = w.url
    ? ` <a class="metalink" href="${esc(w.url)}" target="_blank" rel="noopener"
         data-tip="${esc(`The page on ${w.site || "fa.wiktionary.org"} this word was read on${w.revised ? `, as it stood on ${String(w.revised).slice(0, 10)}` : ""}`)}">the page</a>`
    : "";
  if (!w.etym) {
    return `<p class="sub wiktline reveal" style="--i:2"><span class="etym-label">Persian Wiktionary</span>Has a page for this word; it prints no etymology.${link}</p>`;
  }
  /* The page's sentence, shown as a quotation and cut where a page-long
     essay would crowd out the word itself; the whole of it stays in the
     ledger, and the link opens the page it was read on. */
  const full = String(w.etym).trim();
  const shown = full.length > 300 ? `${full.slice(0, 300).replace(/[\s،,]+$/, "")}…` : full;
  return `<div class="etym reveal wikttext" style="--i:2">
    <p class="sub" data-tip="The Persian Wiktionary page's own words, quoted. A dictionary's etymology is a record; it explains nothing here until this model's cited laws reproduce it.">
      <span class="etym-label">Persian Wiktionary</span>“${esc(shown)}”${link}</p></div>`;
}

/* Meanings, one tab per source (2026-11-10).  Wiktionary's glosses are
   already in the answer; Dehkhoda's own entry is read from vajehyab.com on
   demand and cached on the server.  A tab is a *source*, never a claim about a
   form: nothing here feeds a band or a derivation. */
function meaningsBlock(d) {
  const gloss = esc((d.gloss || []).join("; "));
  const fa = d.lang === "fa";
  /* The first tab is the source the gloss was actually read from: nearly every
     Persian word takes its definition from Dehkhoda, and calling that tab
     "Wiktionary" misattributed the text and its licence (2026-11-12). */
  const glossTab = d.gloss_source === "wiktionary" ? "Wiktionary"
    : d.gloss_source === "dehkhoda" ? "دهخدا (Dehkhoda)" : "Glossary";
  /* The panel's key is the *source*, not a guess at it: the first panel holds
     whatever the glossary read the meaning from, and calling its key
     "wiktionary" put Dehkhoda's Persian text under a Wiktionary tab on almost
     every Persian word (2026-11-12). */
  const tabs = fa
    ? `<div class="mtabs" role="tablist" aria-label="Meanings by source">
         <button class="mtab on" id="mtab-gloss" data-src="gloss" role="tab"
           aria-selected="true" aria-controls="mpanel-gloss" tabindex="0">${esc(glossTab)}</button>
         <button class="mtab" id="mtab-dehkhoda" data-src="dehkhoda" role="tab"
           aria-selected="false" aria-controls="mpanel-dehkhoda" tabindex="-1" lang="fa">دهخدا</button>
       </div>`
    : "";
  return `<div class="meanings reveal" style="--i:1" data-word="${esc(d.word)}"
      data-lang="${esc(d.lang)}" data-sense="${esc(String(d.sense || ""))}">
      ${tabs}
      <div class="mpanel" id="mpanel-gloss" data-src="gloss"
        ${fa ? 'role="tabpanel" aria-labelledby="mtab-gloss" tabindex="0"' : ""}><p class="gloss">${gloss}</p></div>
      ${fa ? `<div class="mpanel" id="mpanel-dehkhoda" data-src="dehkhoda" role="tabpanel"
        aria-labelledby="mtab-dehkhoda" tabindex="0" hidden dir="rtl" lang="fa"><p class="sub">Loading Dehkhoda …</p></div>` : ""}
    </div>`;
}

function wireMeanings(d) {
  const box = app.querySelector(".meanings");
  if (!box || d.lang !== "fa") return;
  const tabs = [...box.querySelectorAll(".mtab")];
  const panels = [...box.querySelectorAll(".mpanel")];
  const show = (src, focus) => {
    tabs.forEach((t) => {
      const on = t.dataset.src === src;
      t.classList.toggle("on", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
      /* One tab stop for the whole strip, and the arrow keys move within it:
         six tab stops for two tabs is what the roles promised and did not
         deliver (2026-11-12, critic P2). */
      t.tabIndex = on ? 0 : -1;
      if (on && focus) t.focus();
    });
    panels.forEach((p) => { p.hidden = p.dataset.src !== src; });
  };
  const panel = box.querySelector('.mpanel[data-src="dehkhoda"]');
  const sense = box.dataset.sense;
  const open = (t, focus) => {
    show(t.dataset.src, focus);
    if (t.dataset.src === "dehkhoda") load();
  };
  tabs.forEach((t, i) => {
    t.onclick = () => open(t);
    t.onkeydown = (e) => {
      const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!step) return;
      e.preventDefault();
      const next = tabs[(i + step + tabs.length) % tabs.length];
      open(next, true);
    };
  });
  /* The dictionary is asked for when its tab is first opened, not on every
     page view: a cache miss costs up to six requests to vajehyab.com, and the
     panel is hidden until then anyway (2026-11-12, critic P1-8). */
  let loaded = null;
  const load = () => {
    if (loaded) return loaded;
    panel.innerHTML = `<p class="sub">Loading Dehkhoda …</p>`;
    loaded = api("/api/meanings", { lang: d.lang, w: d.word, sense: sense || null })
    .then((m) => {
      const deh = (m.sources || []).find((s) => s.id === "dehkhoda");
      if (!deh) { panel.innerHTML = `<p class="sub">No second source for this word.</p>`; return; }
      if (!(deh.entries || []).length) {
        panel.innerHTML = `<p class="sub">${esc(deh.note || "No entry.")}
          <a class="dlink" href="${esc(deh.url)}" rel="noopener" target="_blank">open vajehyab</a></p>`;
        return;
      }
      const rows = deh.entries.map((e, i) => `<div class="mentry">
          <span class="mnum">${i + 1}</span>
          <div class="mtext">${e.text.split(/\n{2,}/).map((p) =>
            p.split("\n").map((line) => `<p>${esc(line)}</p>`).join("")).join("")}</div>
          <a class="msrc" href="${esc(e.url)}" rel="noopener" target="_blank">${esc(e.head)} ↗</a>
        </div>`).join("");
      panel.innerHTML = `${rows}<p class="sub msrc-line">Source: <a class="dlink" href="${esc(deh.url)}"
        rel="noopener" target="_blank">vajehyab.com</a> — Dehkhoda's entry, as printed there.</p>`;
    })
    .catch(() => {
      panel.innerHTML = `<p class="sub">vajehyab.com could not be reached; the source tab is unaffected.</p>`;
    });
    return loaded;
  };
}

/* What the *donor's* own entry says above it (2026-11-10).  A word
   borrowed from English borrowed a finished English word; the Greek pieces of
   dinosaur belong to English's record, not to Persian's ladder, so they are a
   line of the etymology with a door into the donor's page — never a rung. */
function donorLine(d) {
  const l = d.loan || {};
  const above = (l.above || []).filter((a) => a && a.form);
  if (!above.length) return "";
  const pieces = above.map((a) => {
    return `<a href="${esc(wordHref(a.lang, a.form, true))}" class="dlink">${esc(a.form)}</a>${
      a.lang_name ? ` <span class="sub">(${esc(a.lang_name)})</span>` : ""}`;
  }).join(", ");
  const donor = l.name || l.code;
  const link = l.form ? wordHref(l.code, l.form, true) : "";
  return `<p class="sub donorline" data-tip="The donor word's own etymology, from ${esc(donor)}'s entry — not a stage of this word, which borrowed the finished form.">
    <span class="etym-label">Above the donor</span>${esc(donor)}${l.form
      ? ` <a href="${esc(link)}" class="dlink">${esc(l.form)}</a>` : ""} comes from ${pieces}${
      l.donor_joined && above.length > 1 ? " (joined from those pieces)" : ""}.</p>`;
}

function wireCopy() {
  app.querySelectorAll(".copy").forEach((b) => {
    b.onclick = async () => {
      try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = "copied ✓"; b.classList.add("done"); }
      catch (e) { b.textContent = "copy failed"; }
      setTimeout(() => { b.textContent = "copy"; b.classList.remove("done"); }, 1400);
    };
  });
}

/* ------------------------------------------------------------------ */
/* a form no glossary records                                          */
/* ------------------------------------------------------------------ */
/* A word on a ladder is a door (2026-11-08). Clicking one usually opens the
   dictionary's own page; when the stage has no entry — a reconstruction the
   laws produced, or a record Wiktionary's ancestry gives that this repo's
   glossary does not hold — the page must still open, say plainly that nothing
   is recorded here, and follow the form into the languages below it, so a red
   or gold word is never a dead end. */
function viewGhost(d) {
  const desc = d.descendants || {};
  const origin = d.origin;
  const via = origin ? `${origin.lang}/${origin.word}` : `${d.lang}/${d.word}`;
  const back = origin
    ? `<a href="${wordHref(origin.lang, origin.word, true)}">${esc(origin.word)}</a> (${esc(origin.lang_name)})`
    : "";
  const here = (d.origin_recorded || []).length
    ? `<p class="sub reveal" style="--i:2">On that word's own ladder this stage is recorded as
        ${(d.origin_records && d.origin_records.length ? d.origin_records : d.origin_recorded.map((w) => ({ w })))
          .map((r) => form(r.w, d.lang, {
            ev: r.evidence, show: r.show_reading === undefined ? true : r.show_reading,
            reading: r.reading, auto: !!r.reading_auto, note: r.reading_note })).join(" · ")}
        — but this stage's <b>glossary</b> has no entry for it, so there is no word page of its own.</p>`
    : "";
  app.innerHTML = `
    <div class="wordgrid reveal">
      ${langRail(d, d.kind === "proto" ? "reconstructed stage" : "attested language")}
      <header class="wordhead">
        <div class="wordmain">
          <h1 class="headword ev-weak" dir="auto" tabindex="0"
              data-tip="No entry in ${esc(d.lang_name)}'s glossary is spelled this way. The page carries the form down into the branch below it.">${esc(pf(starred(d.word, d.lang, d.kind, d.script)))}</h1>
          <div class="wordmeta">
            ${attestNote(d.attestation, d.recorded_elsewhere
              ? "The word you came from records this form at this stage; this stage's glossary simply has no entry of its own for it."
              : "")}
          </div>
        </div>
        <button class="ghost copy" data-copy="${esc(pf(d.word))}" title="Copy this form">copy</button>
      </header>
    </div>
    <p class="gloss reveal" style="--i:1">This form has no dictionary entry of its own in ${esc(d.lang_name)}.
      It is still a word you can follow: below is what the registered sound laws make of it in the
      languages that descend from this stage, one direct child at a time — no lookups, nothing filled in.</p>
    ${origin ? `<p class="sub reveal" style="--i:2">You came here from ${back}.</p>` : ""}
    ${here}
    ${renderBranch(desc, { via: via, claim: false })}
  `;
  wireCopy();
}

/* The family below a stage: a branch, not a table (2026-11-08).
   Only the **direct** children of the stage appear at first; each one carries
   a disclosure triangle that opens its own direct children, and so on to the
   leaves, like a folder tree. Every form on it is a door to its own page, and
   a row that reaches a recorded form quotes it — the record is never hidden
   behind the prediction. */
function renderBranch(desc, opts = {}) {
  const tree = (desc && desc.tree) || [];
  const c = (desc && desc.counts) || {};
  const src = (desc && desc.source) || {};
  const via = opts.via || "";
  const claim = opts.claim !== false;
  const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
  if (!tree.length) {
    /* A stage with no reading is not a stage with no descendants: the branch
       cannot start from a spelling, and saying "nothing descends" would be a
       claim about the family instead of about the form (critic peo-02,
       2026-11-13). */
    const why = desc && desc.note
      ? esc(desc.note)
      : `No modelled language descends directly from ${esc(src.lang_name || "this stage")},
        so this form cannot be carried further.`;
    return `<h2 class="reveal">Below this stage</h2>
      <p class="sub">${why}</p>`;
  }
  const laws = (r) => {
    const extra = (r.tiers || []).filter((t) => t !== "established");
    return `${r.steps} ${r.steps === 1 ? "law" : "laws"}${extra.length ? ` · ${extra.join(" + ")}` : ""}`;
  };
  /* What this stage records, said next to what the laws made of the form.
     A match quotes the record; a miss names it; nothing recorded is said in
     words so colour is never the only cue. */
  const state = (r) => {
    if ((r.skipped || []).length) {
      return `<span class="branchstate sub" data-tip="No rule file exists for this transition yet, so the form cannot be carried across it.">no rule file for ${esc((r.skipped || []).join(", "))}</span>`;
    }
    const rec = r.recorded;
    if (!rec) {
      return `<span class="branchstate sub" data-tip="Nothing in this stage's glossary or the record you came from is spelled like this form.">no recorded form</span>`;
    }
    const label = rec.via === "glossary"
      ? "This language's glossary has a headword with exactly this form — a form match, not a claim that it is this word."
      : rec.via === "reading"
      ? "This language writes the word in another script; its recorded romanisation is exactly this form. A reading match, not a second attestation."
      : "The word page you came from records this form at this stage.";
    /* A ✓ is a claim that this is a word of the stage, so it may only sit
       beside a record the stage's glossary holds; a form the etymology names
       but no entry spells is dark red here as on the ladder (admin,
       2026-11-12). */
    const held = rec.known !== false;
    const word = form(rec.w, r.l, {
      ev: held ? rec.evidence : "missing", reading: rec.reading,
      signs: rec.signs || "",
      show: rec.show_reading,
      auto: !!rec.reading_auto, note: rec.reading_note,
      href: rec.known ? wordHref(r.l, rec.headword || rec.w, true) : "",
      hrefTip: rec.known ? `Open ${rec.headword || rec.w} in ${r.lang_name}` : "",
    });
    if (r.status === "unverified" && held) {
      /* The record reproduces every sound of the form but its ending (کبود
         *kabud* for the laws' *kabūde*). No law accounts for the difference,
         so it is neither a ✓ nor a plain miss: a yellow ⚠ says a person has
         to look, and the row says so in words too (admin, 2026-11-12). */
      return `<span class="branchstate unverified" data-tip="${esc(
        (rec.review && rec.review.basis === "letters"
          ? `The letters of this entry agree with the form the laws produce, but the glossary records no reading for the word: an abjad leaves the vowels out, so k-b-d spells کبد, کبود and کبوده at once. Nothing can be verified from the letters alone — the match is kept here for review.`
          : `This form and the record agree on every sound but the ending: the entry is read ${(rec.review && rec.review.record) || rec.reading || rec.w}, the laws give ${r.form}. No registered law accounts for the difference, so the match is not verified — it is kept here for review.`))}"><i class="unmatchdot" aria-label="match not verified">⚠</i> ${word} <span class="unverifiedword">match not verified</span></span>`;
    }
    return r.status === "match" && held
      ? `<span class="branchstate" data-tip="${esc(label)}"><i class="matchdot" aria-label="matches the record">✓</i> ${word}</span>`
      : `<span class="branchstate" data-tip="${esc(label)}">≠ recorded ${word}</span>`;
  };
  const node = (r) => {
    const kids = r.children || [];
    /* A row that reaches the record opens the record: a ✓ means "this is a
       word", so clicking it must not land on "nothing is recorded here"
       (2026-11-08). */
    const rec = r.recorded;
    /* An unverified match is still the reader's way into the record: the ⚠
       must not be a dead end when the word it names has a page. */
    const toRecord = (r.status === "match" || r.status === "unverified") && rec && rec.known;
    const href = toRecord ? wordHref(r.l, rec.headword || rec.w, true)
      : wordHref(r.l, r.form, r.form_known, via);
    const hrefTip = toRecord ? `Open ${rec.w} in ${r.lang_name}`
      : r.form_known ? `Open ${r.form} in ${r.lang_name}`
      : `Open this form — no entry in ${r.lang_name} is spelled this way`;
    const row = `
      <span class="branchname">${esc(r.lang_name)}<i class="branchbranch">${esc(r.branch || "")}</i></span>
      <span class="branchform">${form(r.form, r.l, {
        ev: r.evidence, href: href, hrefTip: hrefTip,
      })}</span>
      ${state(r)}
      <span class="branchlaws sub">${esc(laws(r))}</span>`;
    return kids.length
      ? `<details class="branchnode" data-l="${esc(r.l)}"><summary class="branchrow">${row}</summary>
          <div class="branchkids">${kids.map(node).join("")}</div></details>`
      : `<div class="branchnode leaf" data-l="${esc(r.l)}"><div class="branchrow">${row}</div></div>`;
  };
  return `
    <h2 class="reveal">Establish Pathways
      <span class="sub" style="text-transform:none;letter-spacing:0">· ${plural(c.direct == null ? tree.length : c.direct, "direct descendant", "direct descendants")},
      ${plural(c.languages == null ? tree.length : c.languages, "language", "languages")} below in all</span></h2>
    <p class="sub rebuild-lede reveal">Each row denotes the transition to each direct daughter language.
      Open a branch to follow it into that language's own children. A form the dictionaries hold is quoted
      beside the prediction.</p>
    <div class="chips reveal">
      <span class="badge strong">${c.strong || 0} confident</span>
      <span class="badge weak">${c.weak || 0} tentative</span>
      ${c.match ? `<span class="badge ${claim ? "attested" : ""}">${c.match} reach${c.match === 1 ? "es" : ""} a recorded form</span>` : ""}
      ${c.unverified ? `<span class="badge unverified">${c.unverified} unverified match${c.unverified === 1 ? "" : "es"}</span>` : ""}
      ${c.new ? `<span class="badge">${c.new} with no recorded form</span>` : ""}
      ${c.gaps ? `<span class="badge warn">${c.gaps} chain${c.gaps === 1 ? "" : "s"} incomplete</span>` : ""}
    </div>
    <div class="branchtree reveal">${tree.map(node).join("")}</div>`;
}

/* ------------------------------------------------------------------ */
/* the ladder                                                          */
/* ------------------------------------------------------------------ */
/* The topmost recorded ancestor at the top, the searched word at the bottom,
   the years each stage was in use beside it, and at every step the laws that
   carried the form down. A law can be switched off; the whole chain is then
   recomputed, so every rung below it shows the altered result. These two are
   what replace the old separate "sound-law derivation" section. */

const eraScale = (year) => (year < 0 ? -1 : 1) * Math.pow(Math.abs(year) / 1000, 0.42);

/* Deep time is not linear: 3,000 years before PIE and 600 years of English
   would otherwise make the tree unusably tall. A compressed scale keeps the
   order exact and the spacing readable. */
function eraGap(prev, cur) {
  if (prev == null || cur == null) return 20;
  return Math.max(6, Math.min(88, Math.round(Math.abs(eraScale(cur) - eraScale(prev)) * 62)));
}

function lawChip(r, citedAdd, aboveStage) {
  const state = r.disabled ? "off" : "on";
  const adds = citedAdd || addedText(r.before, r.after);
  /* The strings a law rewrites are forms of the stage it rewrites them at, so
     a law between two reconstructed rungs prints them with the star too
     (admin, 2026-11-12).  The stage is the one above the law, never this
     rung's: a law into English rewrites Middle English, not English. */
  const before = pf(starred(r.before, aboveStage));
  const after = pf(starred(r.fired ? r.after : r.would, aboveStage));
  return `<li class="law ${state}">
      <button class="lawswitch" type="button" data-off="${esc(r.key)}" aria-pressed="${r.disabled ? "false" : "true"}"
        aria-label="${esc(r.disabled ? `Switch ${r.name} back on` : `Switch off ${r.name}`)}"
        title="${esc(r.disabled ? "Switch this law back on" : "Switch this law off — the stages below are recomputed without it")}">
        <span class="knob" aria-hidden="true"></span><span class="sronly">${r.disabled ? "switched off" : "applied"}</span>
      </button>
      <span class="lawform mono">${esc(before)}${r.fired || r.would ? ` → ${esc(after)}` : ""}</span>
      ${lawLink(r.name, r.key)}
      ${badge(r.tier)}${r.fired && adds && (citedAdd || adds.length > 1) ? `<span class="lawadd" data-tip="The morpheme this law adds to the word">+ ${esc(adds)}</span>` : ""}
    </li>`;
}

/* The laws of a step belong on the rail between the two forms they changed,
   not under the second one (2026-11-08): reading down the timeline
   you meet a form, then the laws it went through, then the form they made.
   They must also *look* like they stand between the two words, not in the
   shadow of the one above: the space between two rungs is split, the step
   taking the upper half and the rung it leads to the lower half, so the chips
   sit in the middle of the gap with room on both sides (2026-11-08, seeing them still hugging the word above). */
const stepGap = (gap) => Math.max(7, Math.round((gap || 14) / 2));
/* A formation on the timeline (2026-11-10). A rung may be *built*
   rather than inherited: two words of one stage joined, or a word plus a
   cited suffix or ending. It stands on the rail between the form it started
   from and the form it produced, and it says what was added — never that a
   sound law did it. */
function buildStep(level) {
  const b = level.built;
  if (!b) return "";
  const kind = { compound: "compound", suffix: "derivation", inflection: "inflection" }[b.kind] || "formation";
  const piece = (p, i) => {
    const form = String(p.form || "");
    /* A word of the formation keeps its own spelling, hyphen and all (*ters-,
       not *ters), and a reconstructed stage writes the leading star the rest
       of the page writes — the step names the pieces, so they read exactly as
       they do on the word's own page (2026-11-12). */
    const spelled = p.affix || !p.known || !p.word ? form : String(p.word);
    const hyphened = p.affix && spelled && !spelled.startsWith("-") ? "-" + spelled : spelled;
    const written = starred(hyphened, p.lang || b.lang);
    const href = p.known ? wordHref(p.lang, p.word || p.form, true) : "";
    const body = href
      ? `<a class="bpiece mono" href="${esc(href)}" data-tip="${esc(`Open ${p.form} in ${p.lang_name || ""}`)}">${esc(pf(written))}</a>`
      : `<span class="bpiece mono">${esc(pf(written))}</span>`;
    /* The piece stands in the grade the formation takes it in: *ters- beside
       *-nó- is *tr̥s- (#ters- → #tr̥s-), and that is morphology, not a sound
       change (admin, 2026-11-12). */
    const grade = p.grade_label
      ? ` <span class="cgrade" data-tip="${esc(p.grade_note || p.grade_label)}">${esc(p.grade_label)}</span>`
      : "";
    return `${i ? `<i class="bplus">+</i>` : ""}${body}${grade}${
      p.gloss ? ` <span class="bgloss sub">“${esc(p.gloss)}”</span>` : ""}`;
  };
  const pieces = (b.pieces || []).map(piece).join(" ");
  return `<li class="lawstep buildstep"><div class="when" aria-hidden="true"></div>
    <div class="rail" aria-hidden="true"><i></i></div>
    <div class="buildbody">
      <span class="buildtag">built here</span>
      <span class="bkind sub">${esc(kind)} in ${esc(b.stage_name || "")}</span>
      ${pieces} <i class="barrow">→</i> <span class="mono">${esc(pf(
        starred(level.form, b.stage)))}</span>
      <span class="bnote sub">${esc(b.note || "")}</span>
    </div></li>`;
}

/* The construction row (admin, 2026-11-12): the dot beside a word is a door,
   not a decoration.  Clicking it opens a row above the word — marked with a
   diamond, because it is a formation and not a sound change — holding the word
   itself and a menu: join another word of the same stage, add a cited suffix,
   or add an ending.  Nothing is typed here: the edit button is for typing, and
   every addition is composed by the stage's own morphology and says what grade
   it puts the stem in. */
const stageWords = new Map();
function loadStageWords(stage) {
  if (!stageWords.has(stage)) {
    stageWords.set(stage, api("/api/words", { lang: stage, limit: 4000 })
      .then((row) => (row && row.words) || []).catch(() => []));
  }
  return stageWords.get(stage);
}

/* The menu: the stage's suffixes and endings straight from the morphology
   table, and its words fetched once per stage. */
function draftMenu(stage, opts) {
  const o = (opts || {})[stage] || {};
  const suf = (o.suffixes || []).filter((x) => x.kind !== "ending");
  const end = o.endings || [];
  const group = (label, rows) => rows.length
    ? `<optgroup label="${esc(label)}">${rows.join("")}</optgroup>` : "";
  return `<option value="">add a word, a suffix or an ending…</option>`
    + group("suffix", suf.map((x) =>
        `<option value="suffix:${esc(x.id)}">${esc(x.form)} — ${esc(x.gloss)}</option>`))
    + group("ending", end.map((x) =>
        `<option value="ending:${esc(x.form)}">${esc(x.form)} — ${esc(x.gloss)}</option>`));
}

function addWordGroup(sel, stage) {
  if (!sel || sel.querySelector('[data-words]')) return;
  loadStageWords(stage).then((words) => {
    if (!words.length || sel.querySelector('[data-words]')) return;
    const g = document.createElement("optgroup");
    g.label = "word";
    g.dataset.words = "1";
    g.innerHTML = words.map((w) =>
      `<option value="join:${esc(w.word)}">${esc(w.word)}${w.gloss ? ` — ${esc(w.gloss)}` : ""}</option>`).join("");
    sel.append(g);
  });
}

/* One piece of the draft line: a word-sized string with the star its stage
   writes, its grade when the formation puts the stem in one, and its meaning
   on hover (a bound suffix's gloss is what the suffix does). */
function draftPieceHtml(stage, piece) {
  const form = String(piece.form || "");
  const hyphened = piece.affix && form && !form.startsWith("-") ? "-" + form : form;
  const shown = starred(hyphened, stage);
  const grade = piece.grade_label
    ? ` <span class="cgrade" data-tip="${esc(piece.grade_note || piece.grade_label)}">${esc(piece.grade_label)}</span>` : "";
  return `<span class="dadd"><i class="dplus" aria-hidden="true">+</i><span class="dpiece mono"${
    piece.gloss ? ` data-tip="${esc(piece.gloss)}"` : ""}>${esc(pf(shown))}</span>${grade}</span>`;
}

function draftBuiltHtml(row, stage, orig, spec) {
  const pieces = (row.pieces || []).slice(1).map((p) => draftPieceHtml(stage, p)).join("");
  const href = `#/word/${encodeURIComponent(stage)}/${encodeURIComponent(orig)}?build=${encodeURIComponent(spec)}`;
  return `${pieces} <i class="barrow" aria-hidden="true">→</i>
    <a class="dresult formlink" href="${esc(href)}" data-tip="Open this built word in the timeline: the formation stands above it and the laws carry it down.">${esc(pf(
      starred(row.form, stage)))}</a>`;
}

/* Two spellings are one word when they differ only in the stress the engine
   writes as a token and the dictionary writes as an acute. */
const plainForm = (form) => String(form || "").replace(/[ˈˌ]/g, "");

function openDraft(btn) {
  const L = ladderState;
  const rung = btn.closest("li.rung");
  if (!L || !rung) return;
  const open = rung.previousElementSibling && rung.previousElementSibling.classList.contains("builddraft");
  if (open) {
    rung.previousElementSibling.remove();
    btn.classList.remove("on");
    return;
  }
  const stage = btn.dataset.cstage || "";
  const wordForm = btn.dataset.cform || "";
  const name = btn.dataset.cname || stage;
  const level = (L.data.levels || [])[Number(rung.dataset.rung || 0)] || {};
  const li = document.createElement("li");
  li.className = "rung builddraft";
  li.innerHTML = `<div class="when">
      <span class="when-name kind-${esc(level.kind === "attested" ? "attested" : "proto")}">${esc(name)}</span>
      <span class="when-era">${esc(level.era_label || "")}</span>
      <span class="when-here">construction</span>
    </div>
    <div class="rail"><i class="diamond" aria-hidden="true"></i></div>
    <div class="rung-body">
      <div class="draftline">
        <span class="draftterm">${form(wordForm, stage,
          { ev: level.recorded && level.recorded.known === false
              && level.recorded.modelled !== false ? "missing" : (level.evidence || "") })}</span>
        <span class="draftpieces"></span>
        <select class="dsel" aria-label="Add a word, a suffix or an ending to ${esc(wordForm)}">${draftMenu(stage, L.data.build_options)}</select>
        <button class="dclose ghost" type="button" aria-label="Close this construction row">×</button>
      </div>
      <p class="draftnote sub">Nothing has changed yet — choose a word to join, a suffix or an ending.</p>
    </div>`;
  rung.parentNode.insertBefore(li, rung);
  btn.classList.add("on");
  const sel = li.querySelector(".dsel");
  const pieces = li.querySelector(".draftpieces");
  const note = li.querySelector(".draftnote");
  addWordGroup(sel, stage);
  li.querySelector(".dclose").onclick = () => { li.remove(); btn.classList.remove("on"); };
  let current = wordForm;
  let chain = 0;
  sel.onchange = () => {
    const pick = sel.value || "";
    const at = pick.indexOf(":");
    if (at < 0) return;
    const kind = pick.slice(0, at);
    const arg = pick.slice(at + 1);
    const spec = `${stage}:${kind}:${arg}@${current}`;
    sel.disabled = true;
    api("/api/build", { spec }).then((row) => {
      sel.disabled = false;
      if (!row || row.error || !row.form) {
        note.hidden = false;
        note.textContent = `The morphology of ${name} does not build that from ${current}.`;
        sel.value = "";
        return;
      }
      /* An ending the word already wears is not a step: adding *-os to *tr̥snós
         used to print *tr̥snós again and call it a second piece (admin,
         2026-11-12).  The row says why nothing changed instead. */
      if (plainForm(row.form) === plainForm(current)) {
        note.hidden = false;
        note.textContent = `${pf(current)} already has that piece — the formed word is the same word.`;
        sel.value = "";
        return;
      }
      chain += 1;
      /* The stem's grade belongs beside the word it changed: *ters- is *tr̥s-
         in this formation, and the row says so in the same words the timeline
         does (admin, 2026-11-12). */
      const lead = (row.pieces || [])[0] || {};
      if (chain === 1 && lead.grade_label) {
        li.querySelector(".draftterm").insertAdjacentHTML("beforeend",
          ` <span class="cgrade" data-tip="${esc(lead.grade_note || lead.grade_label)}">${esc(lead.grade_label)}</span>`);
      }
      pieces.insertAdjacentHTML("beforeend", draftBuiltHtml(row, stage, wordForm, spec));
      current = row.form;
      note.hidden = false;
      note.textContent = chain === 1
        ? `${row.note || "The stage's own formation."} Add another piece, or open the result to follow it down the laws.`
        : `Another piece on the same line; the row is one formation, not a sound law.`;
      sel.value = "";
    }).catch(() => {
      sel.disabled = false;
      sel.value = "";
    });
  };
}

const lawStep = (body, gap = 14) => body
  ? `<li class="lawstep" style="--gap:${stepGap(gap)}px"><div class="when" aria-hidden="true"></div>
      <div class="rail" aria-hidden="true"><i></i></div>
      <div class="lawbody">${body}</div></li>`
  : "";

/* What one law inserted: the middle that is neither shared prefix nor shared
   suffix. A formation law adds a morpheme, and the page shows which one. */
function addedText(before, after) {
  if (!before || !after || before === after) return "";
  let head = 0;
  while (head < before.length && head < after.length && before[head] === after[head]) head += 1;
  let tail = 0;
  while (tail < before.length - head && tail < after.length - head
         && before[before.length - 1 - tail] === after[after.length - 1 - tail]) tail += 1;
  return after.slice(head, after.length - tail);
}

function renderLaws(level, prevName, aboveStage = "") {
  const t = level.transition;
  if (!t) return "";
  /* A formation law's chip names the suffix the record cites (-nás), not the
     letters that happen to differ between the two forms. */
  const citedAdd = (level.formation && level.formation.surface) || "";
  const formationLaw = (level.formation && level.formation.law) || "";
  if (t.missing) {
    return `<p class="notice laws-missing">No rule file exists for ${esc(prevName)} → ${esc(level.name)} yet,
      so the form is carried over unchanged.</p>`;
  }
  /* The laws rewrite sounds, never signs.  A rung whose form is a writing with
     no reading recorded cannot be derived at all, and the page says that
     instead of printing a red copy of the script and calling it unreached
     (2026-11-11: Middle Persian lwc started its ladder on cuneiform). */
  if (t.unreadable) {
    return `<p class="notice laws-missing">This rung is written in its own script and no
      reading is recorded for it, so the sound laws have nothing to start from —
      they rewrite sounds, never signs.</p>`;
  }
  const fired = level.rules.filter((r) => r.fired);
  const off = level.rules.filter((r) => r.disabled);
  if (!fired.length && !off.length) {
    return "";
  }
  return `<div class="laws">
    <ul class="lawlist">${fired.map((r) => lawChip(r, r.key === formationLaw ? citedAdd : "", aboveStage)).join("")}${off.map((r) => lawChip(r, "", aboveStage)).join("")}</ul>
  </div>`;
}

/* The suffix a word wears, printed on the rung where the formation law adds it,
   beside the other cited suffixes registered for that stage. A suffix is a
   formation law, so choosing one asks the same ladder for the word built with
   that morpheme instead — changing it in the timeline view
   (2026-11-08). */
function formationLine(level, current) {
  const f = level.formation;
  const rows = [`<button type="button" class="chip${current ? "" : " on"}" data-rung-suffix=""
      aria-pressed="${current ? "false" : "true"}"
      data-tip="The suffix this word's own record says it wears"><span class="chip-form">as it stands</span></button>`];
  (f.options || []).forEach((o) => rows.push(
    `<button type="button" class="chip${current === o.id ? " on" : ""}" data-rung-suffix="${esc(o.id)}"
       aria-pressed="${current === o.id ? "true" : "false"}"
       data-tip="${esc(`${o.form} · ${o.gloss}${o.law ? " (registered formation law)" : " (composed here)"}`)}">
       <span class="chip-form mono">${esc(o.form)}</span>
       <span class="sronly">${esc(o.gloss)}</span>${
         o.law ? `<span class="chip-law">law</span>` : ""}</button>`));
  return `<div class="suffixline rung-suffix" role="group"
      aria-label="Derivational suffix registered for ${esc(level.name)}">
      <span class="sub">suffix</span>${rows.join("")}</div>`;
}

/* A root is an entry, not a dead end (2026-11-08): its page lists
   the words the dictionary builds on it, each with the suffix it adds. This is
   the construction line read from the other end, so the base a word page names
   is a page that names the word back. */

/* A rung's form may be a construction, and the record says so: the Proto-Iranian
   word dáwxšati inherits a Proto-Indo-European *déwk-s-eti which is *dewk- +
   *-seti.  The ladder starts at the whole form; this step says how the whole
   form came to be, at the stage where it was built.
   It is a step of the timeline, not a line under the word, and it stands
   **above** the form it produces — the timeline runs from old (top) to new
   (bottom), so the pieces and their own histories come first and the word they
   make is the rung under them (admin, 2026-11-12).  The diamond on the rail
   marks the step, `𐎨𐎡𐏂 čiçaʰ` sits on the base line beside `+ *farnah`, and
   each piece climbs its own branch upward — to a Proto-Indo-European word, to
   the donor it was borrowed from, or to a `???` where nothing explains it.
   A record may state the same word more than one way (English *about* is
   `on + be + out` and `on + but`): each analysis gets its own tab, because
   choosing one for the reader would hide the other. */
function constructStep(level, i, linkTo, opts) {
  const builds = ((level.builds && level.builds.length) ? level.builds
    : [level.built_as]).filter((b) => b && (b.pieces || []).length);
  if (!builds.length) return "";
  const uid = `bs-${String(level.stage || "x").replace(/[^a-z0-9-]/gi, "")}-${i}`;
  const link = (lang, form, known) => (linkTo ? linkTo(lang, form, known) : "");
  const kindOf = (b) => ({ suffix: "suffix", prefix: "prefix", compound: "compound",
    affix: "affix", infix: "infix", combining: "combining form",
    derivation: "derivation", reduplication: "reduplication" }[b.kind] || "formation");
  /* The construction is one tree, not a set of inset pictures (admin,
     2026-11-12): the first word stands immediately right of the diamond (no
     line, no second mark — the diamond *is* its mark), the line then leaves
     the right of that word for `+` and the next piece, and above each piece
     its own climb rises, one row per step (see `climbOf`). */
  const eraOf = (n) => (n && n.era_label) || "date unknown";
  /* What a word on the timeline means, in the same wording the headword's own
     line uses — `adj · “visible”` — so a rung is a word with a sense and not
     only a string of letters (admin, 2026-11-12).  A bound morpheme has no
     part of speech to name and its gloss is already a description of what it
     does (`forms adjectives from Caland-system roots`), so it is printed as
     that description rather than quoted as a meaning. */
  const meaningOf = (pos, gloss, bound) => {
    const g = String(gloss || "").trim().replace(/[.;]\s*$/, "");
    if (!g) return "";
    /* A bound morpheme's gloss is a description of what it does and can run
       long: the sheet wraps it to two lines and the whole of it is on the
       element's own hover, so the line under the word is never lost to a
       truncation and never runs into the next piece (admin, 2026-11-12). */
    if (bound) return esc(g);
    const p = String(pos || "").trim();
    return `${p && p !== "suffix" && p !== "root" ? esc(p) + " · " : ""}“${esc(g)}”`;
  };
  const langKind = (n) => (n && n.kind === "proto" ? "kind-proto" : "kind-attested");
  /* The colour is the stage's evidence *and* whether the stage holds the
     word: a form no glossary entry spells is non-existent, and it prints dark
     red whatever the literature reconstructs it from (admin, 2026-11-12). */
  const evOf = (n) => {
    if (!n || n.unknown) return "ev-weak";
    /* A rung the laws reach between two recorded stages is the ladder's own
       "derived" rung — a form no glossary records, but not a hole either: the
       model derived it, and the word's own page prints it in this colour
       (admin, 2026-11-13: a piece brings its whole timeline with it). */
    if (n.derived) return "ev-weak";
    /* A word of a language outside the family is not a missing entry: the
       model simply holds no glossary there (admin, 2026-11-13). */
    if (n.outside) return "ev-outside";
    if (n.known === false) return "ev-missing";
    if (n.terminal === "pie" || n.kind === "proto"
        || String(n.form || "").startsWith("*")) return "ev-literary";
    return "ev-attested";
  };
  const saidOf = (n) => (n.terminal === "missing"
    ? `${n.lang_name} ${n.form} — the record names this form, but the glossary has no entry for it, so nothing here says where it came from.`
    : n.terminal === "outside"
      ? `${n.lang_name} ${n.form} — a language outside the family: its own trail begins here${n.gloss ? ` “${n.gloss}”` : ""}.`
      : n.terminal === "pie"
        ? `${n.lang_name} ${n.form} — the top of the family: nothing above Proto-Indo-European is modelled.${n.gloss ? ` “${n.gloss}”` : ""}${n.known ? "" : " (No glossary entry for this form.)"}`
        : n.terminal === "borrowed"
          ? `${n.lang_name} ${n.form} — the record says the word was borrowed from here${
              n.known ? " — open the donor word's page."
                : n.outside ? "; a non-PIE word, so this model holds no glossary for it."
                  : "; the donor word has no glossary entry."}`
          : `${n.gloss ? `“${n.gloss}” — ` : ""}${n.known ? "open the word page"
              : n.derived ? "no glossary entry at this stage"
                : "no glossary entry"}`);
  /* The word itself, at the ladder's size, in its own evidence colour, its
     reading underneath it — the ladder's own stack. */
  const wordHtml = (n, tip, extra = "") => `<span class="formstack">${
    (n.known ? `<a class="formlink" href="${esc(link(n.lang, n.form, true))}" title="${esc(`Open ${n.form} in ${n.lang_name || n.lang}`)}">` : "<span>")}${form(n.form || n.lang, n.lang, {
      ev: evOf(n).replace(/^ev-/, ""), tip,
    })}${n.known ? "</a>" : "</span>"}${
    n.reading ? `<span class="reading">${esc(n.reading)}</span>` : ""}${
    n.signs && n.signs !== n.reading ? `<span class="reading signs">${esc(n.signs)}</span>` : ""}</span>${extra}`;
  /* One row of a piece's own timeline, inside its column: the language and its
     years against the rail on the left, the word on the right — the ladder's
     own rung, at the ladder's own sizes, because the climb above a construction
     has to read as the same timeline that continues below it (admin,
     2026-11-12: "the language names should be shown to the left along with the
     est. dates").  Every row of every column is exactly one step high
     (`--crow`), so the ancestors of two pieces that stand in the same language
     land on the same line — *h₂entó- and *swer-, a PIE word above each piece of
     *andaswarō (admin, 2026-11-12). */
  /* The laws of one step of a piece's climb.  Every row of the tree is a word
     the ladder would have carried down by called laws, so the row carries the
     same chips the ladder prints — with the same switches, because a reader
     who can turn a law off on one timeline must be able to do it on all of
     them (admin, 2026-11-13). */
  const stepLaws = (step, stage) => {
    const rules = (step && step.rules) || [];
    if (!rules.length) return "";
    return `<div class="claws"><ul class="lawlist">${
      rules.map((r) => lawChip(r, "", stage || "")).join("")}</ul></div>`;
  };
  const chainRow = (n) => n && n.unknown
    ? `<div class="cnode unknown">
      <span class="cwhen"></span>
      <span class="crail" aria-hidden="true"><i></i></span>
      <span class="cstack"><span class="cwordrow"><span class="cform ev-weak" data-tip="No record says where this word came from — it may have come from somewhere, but where is not known."><span class="cunknown">???</span></span></span></span>
    </div>`
    : `<div class="cnode" data-tip="${esc(`${n.lang_name || n.lang || ""}${eraOf(n) ? ` · ${eraOf(n)}` : ""} — ${saidOf(n)}`)}">
      <span class="cwhen"><span class="cwhen-name ${langKind(n)}">${esc(n.lang_name || n.lang || "")}</span><span class="cwhen-era">${esc(eraOf(n))}</span></span>
      <span class="crail" aria-hidden="true"><i></i></span>
      <div class="cstack"><span class="cwordrow"><span class="cform ${scriptClass(n.form)} ${evOf(n)}">${
        n.known ? `<a class="cword" href="${esc(link(n.lang, n.form, true))}">${esc(pf(starred(n.form, n.lang, n.kind, n.script)))}</a>`
          : `<span class="cword">${esc(pf(starred(n.form, n.lang, n.kind, n.script)))}</span>`}${
        n.reading ? `<i class="cread">${esc(n.reading)}</i>` : ""}${
        n.signs && n.signs !== n.reading ? `<i class="cread signs">${esc(n.signs)}</i>` : ""}</span></span>${
        meaningOf(n.pos, n.gloss, false)
          ? `<span class="cgloss">${meaningOf(n.pos, n.gloss, false)}</span>`
          : n.derived
            /* A rung the laws produce between two recorded stages is still a
               form no glossary heads: the hover said «no glossary entry» while
               the line said «a form the laws produce», and the reader was told
               two things at once (admin, 2026-11-13: ناراحت's Middle Persian,
               Old Persian and Proto-Iranian rungs).  Say what is missing first,
               then how the row got here. */
            ? `<span class="cgloss"><span class="norec">no entry for this word</span></span>`
          : n.known === false
            ? `<span class="cgloss"><span class="${n.outside ? "coutside" : "norec"}">${
                n.outside ? "non-PIE word" : "no entry for this word"}</span></span>` : ""}${
        stepLaws(n.step, n.parents && n.parents[0] ? n.parents[0].lang : "")}</div>
    </div>`;
  /* Where the line above a word goes: its recorded parent, or — for a word
     whose entry records no origin, or a form no entry holds — a ??? hanging
     over it.  A Proto-Indo-European word is the top of the trail, and a donor
     is the end of a borrowing, so neither gets a ??? above it. */
  const parentsOf = (n) => {
    if (!n) return [];
    if (n.terminal === "end" || n.terminal === "missing") return [{ unknown: true }];
    return n.parents || [];
  };
  /* A piece's climb, nearest first: one row per step, never two steps crammed
     into one.  A word whose own record states a construction is that
     construction — a row of its own — and the climb goes on through the word
     it was made from, so every row of every column is the same height and two
     pieces' ancestors at the same distance stand on one line (admin,
     2026-11-12). */
  const climbOf = (p) => {
    const rows = [];
    /* A piece climbs when it has a branch — the entry it resolved to has a
       history of its own.  Being *bound* does not take that away: باش is a
       stem of بودن, and بودن reaches PIE *bʰewH- (critic batch 07,
       2026-11-13: the column was empty).  A morpheme that is only a suffix
       has no branch at all, and still stands with no column. */
    let cur = p.branch || null;
    let guard = 0;
    while (cur && guard++ < 12) {
      if (cur.builds && cur.builds.length) {
        rows.push({ build: cur.builds[0], word: cur });
        const first = cur.builds[0].pieces[0];
        cur = first ? (first.branch || null) : null;
        continue;
      }
      const parent = parentsOf(cur)[0];
      if (!parent) break;
      if (parent.unknown) { rows.push({ unknown: true }); break; }
      rows.push(parent);
      cur = parent;
    }
    return rows;
  };
  /* A word on the construction's line: word size, its reading below it.  The
     first word needs no mark of its own — the diamond beside it is its mark —
     so its label is the step's own: *construction*, and the kind of formation
     the record states, printed on the diamond's line instead of under the tree
     (admin, 2026-11-12).  A later piece is not labelled: it is a word *of* the
     step's own stage, and the line from the `+` runs on to its dot through the
     empty label cell. */
  const labelCell = (name, era, kind) => `<span class="cwhen"><span class="cwhen-name ${kind}">${esc(name)}</span>${
    era ? `<span class="cwhen-era">${esc(era)}</span>` : ""}</span>`;
  /* The kind says "reduplication"; which formation it is — the perfect/stative
     (o-grade, *-e) or an i-reduplicated present (zero grade) — is what tells
     the reader *why* the root's vowel changed, so it stands beside it
     (admin, 2026-11-12: the reduplicated stative is a formation, name it). */
  const formationOf = (b) => {
    const kind = kindOf(b);
    const type = String(b.formation || "").trim();
    return type && type !== kind ? `${kind} · ${type}` : kind;
  };
  const constructionLabel = (b) => labelCell("construction",
    `${formationOf(b)}${b.source === "ours" ? " · our reading" : ""}`, "cwhen-build");
  const termCell = (b, p, k, opts) => {
    const formText = String(p.form || "");
    /* A suffix carries its hyphen after the reconstruction's star: *-tós, not
       -*-tós (2026-11-12).  The star itself comes from the one test above, so a
       piece that carries none in the record still prints as its stage writes
       it (admin, 2026-11-12). */
    const hyphened = b.kind === "suffix" && k > 0 && !formText.replace(/^\*/, "").startsWith("-")
      ? formText.replace(/^\*/, "*-") : formText;
    const show = starred(hyphened, b.lang);
    /* A bound morpheme opens no *word* page — the letter that happens to share
       its signs is not its entry.  It opens its own page when the stage's
       glossary holds an affix entry for it, which is the right page for a
       suffix (admin, 2026-11-13: a suffix must open the suffix's own page, or
       none). */
    const href = p.bound && !p.known ? "" : link(b.lang, p.form, p.known);
    const said = p.bound
      ? `${p.known ? "a suffix the stage's own registry lists" : "a bound morpheme with no entry of its own"}${p.gloss ? ` — ${p.gloss}` : ""}`
      : p.gloss ? `“${p.gloss}”` : `a word of ${b.lang_name}`;
    const tip = p.bound ? said + (href ? " — open its page" : "")
      : p.branch && p.branch.terminal === "outside"
        ? `${said} — a language outside the family: its own trail begins here${href ? " — open the word page" : ""}`
        : href ? `${said} — open the word page` : said;
    const ev = p.bound ? (formText.startsWith("*") ? "ev-literary" : "ev-attested")
      : p.branch ? evOf(p.branch) : (p.known ? "ev-attested" : "ev-missing");
    const body = href
      ? `<a class="cword" href="${esc(href)}">${esc(pf(show))}</a>`
      : `<span class="cword">${esc(pf(show))}</span>`;
    /* The piece says how it is read, and — for a script — what its signs
       spell: a bound morpheme with no entry has only these two, and the
       adjectival suffix used to stand with neither (admin, 2026-11-13). */
    const reading = (p.reading ? `<i class="cread">${esc(p.reading)}</i>` : "")
      + (p.signs && p.signs !== p.reading ? `<i class="cread signs">${esc(p.signs)}</i>` : "");
    /* A root that stands in another grade in this formation says so beside
       itself — *ters- under *tr̥s-tó-s is e-grade beside the word's r̥ — and the
       hover gives the reason the handbooks give (admin, 2026-11-12). */
    const grade = p.grade_label
      ? `<span class="cgrade" data-tip="${esc(p.grade_note || p.grade_label)}">${esc(p.grade_label)}</span>`
      : "";
    /* Every word on the tree says what it means; the one that says nothing
       because no entry holds it says that instead (admin, 2026-11-12). */
    /* A piece the glossary does not head says so whatever its shape — 134 of
       Old Persian's 529 entries draw such a piece, and a bare word with a `???`
       above it reads as an entry with no origin instead of as a hole (critic
       batch peo-01, 2026-11-13). */
    const meaning = meaningOf(p.pos, p.gloss, p.bound)
      || (p.known === false && !(p.gloss || "").trim()
        ? (p.branch && p.branch.outside
          ? `<span class="coutside">non-PIE word</span>`
          : `<span class="norec">no entry for this word</span>`) : "");
    /* The word and its meaning are one cell: the word sits on the line the
       `+` draws, and the meaning hangs under it without ever moving that line
       (admin, 2026-11-12). */
    /* A piece of the tree keeps the rail track, because that is where its
       column's line runs and where the mark that stands for it sits: the
       first piece wears the diamond — the step's own mark, in the row of the
       piece it builds, so it is on the pieces' line by construction — a later
       piece wears the dot, and a bound morpheme wears nothing (the line
       reaches it from the `+`).  A piece inside a nested formation
       (`◇ *h₂ent- + *-s`) is met by the `+` beside it and has no rail at all. */
    const mark = opts.first ? " mark" : p.bound ? " blank" : "";
    const rail = !opts.rail ? ""
      : `<span class="crail${mark}" aria-hidden="true">${
          opts.first ? '<i class="cdiamond"></i>' : p.bound ? "" : "<i></i>"}</span>`;
    /* Only the first piece of the tree carries a label: it is the row the
       step's diamond marks, so its label is the step's.  A later piece is met
       by the `+` and its empty label cell is crossed by the line to its dot; a
       piece inside a nested formation (`◇ *h₂ent- + *-s`) has no cell at all,
       because its row's label is the `construction` it stands in. */
    const label = !opts.rail ? "" : opts.first ? constructionLabel(b)
      : `<span class="cwhen lead"></span>`;
    return `<div class="cterm${opts.rail ? "" : " instrip"}${p.bound ? " bound" : ""}${opts.first ? " first" : ""}" data-tip="${esc(tip)}">
        ${label}${rail}
        <div class="cstack">
          <span class="cwordrow"><span class="cform term ${scriptClass(p.form)} ${ev}">${body}${reading}</span>${grade}</span>
          ${meaning ? `<span class="cgloss">${meaning}</span>` : ""}${
          stepLaws(p.branch && p.branch.step,
            p.branch && p.branch.parents && p.branch.parents[0]
              ? p.branch.parents[0].lang : "")}
        </div>
      </div>`;
  };
  /* A word that is itself a construction — *h₂entó- is a combining form from
     *h₂énts, and *h₂énts is *h₂ent- + *-s — keeps that step in its column, one
     row high like every other step, so the climb never stops at a piece the
     record explains (admin, 2026-11-12).  It is a row of the one staircase,
     not a smaller staircase of its own: the diamond sits on the column's own
     rail, at the size every other row has. */
  const buildRow = (item) => {
    const bb = item.build;
    const rest = bb.pieces.slice(1).map((p, k) => `<span class="cplus" aria-hidden="true"><i>+</i></span>${
      termCell(bb, p, k + 1, { first: false, rail: false })}`).join("");
    return `<div class="cbuild" data-tip="${esc(tipOf(bb))}">${constructionLabel(bb)}<span class="crail" aria-hidden="true"><i class="cdiamond mini"></i></span><div class="cstrip">${
      termCell(bb, bb.pieces[0], 0, { first: true, rail: false })}${rest}</div></div>`;
  };

  /* `source: ours` means the record says nothing and this model read the seam
     (2026-11-10).  The two are different claims and must not share one label:
     the record's rows quote the dictionary, and ours says so. */
  const ours = builds.length === 1 && builds[0].source === "ours";
  const joinedOf = (b) => b.pieces.map((p) => p.form).join(" + ");
  const tipOf = (b) => (b.source === "ours"
    ? `The dictionary records no construction for this word; this model reads the seam ${joinedOf(b)} → ${b.of || level.form}. A formation is not a sound law.`
    : `The record states this ${formationOf(b)}: ${joinedOf(b)} → ${b.of || level.form}. A formation is not a sound law.`);
  /* A tab only exists when the record states two different formations.  Its
     label is the formation itself — `on + būtan` against `be + ūtan` — because
     `affix 1` / `affix 2` says nothing a reader can choose by (admin,
     2026-11-12: the tabs were meaningless). */
  const tabs = builds.length > 1
    ? `<div class="bstep-tabs" role="tablist">${builds.map((b, k) => `<label for="${uid}-${k}"
         class="btab" role="tab" data-tip="${esc(tipOf(b))}">${esc(joinedOf(b))}</label>`).join("")}</div>`
    : "";
  const radios = builds.length > 1
    ? builds.map((_, k) => `<input class="bstep-radio" type="radio" name="${uid}" id="${uid}-${k}"${k ? "" : " checked"} aria-label="construction ${k + 1}">`).join("")
    : "";
  /* One tree per analysis: a column per piece.  The first word stands at the
     rail's right — the diamond is its mark — and the line runs from its own
     right edge through `+` to the next piece; above each piece stands its own
     climb, one step per row, so two pieces that come from the same stage of
     the family share a line instead of drifting apart (admin, 2026-11-12:
     *h₂entó- and *swer- on one horizontal line). */
  const tree = (b) => {
    const climbs = b.pieces.map((p) => climbOf(p));
    /* A column that carries a step's laws needs one more band of room under
       every word, in every column, or two pieces' ancestors stop sharing a
       line — and that line is the timeline's whole argument (admin,
       2026-11-12).  So the tree, not the row, decides the height. */
    const hasLaws = climbs.some((rows, k) => rows.some(
      (item) => item.step && item.step.rules && item.step.rules.length))
      || b.pieces.some((p) => p.branch && p.branch.step
        && p.branch.step.rules && p.branch.step.rules.length);
    return `<div class="btree${hasLaws ? " has-laws" : ""}"><div class="bline">${
      b.pieces.map((p, k) => {
        const rows = climbs[k];
        return `${k ? `<span class="cplus" aria-hidden="true"><i>+</i></span>` : ""}${
          `<div class="cpiece${rows.length ? " has-chain" : ""}${k === 0 ? " first" : ""}${k < b.pieces.length - 1 ? " continues" : ""}">${
            k === 0 ? `<div class="clead" aria-hidden="true"><span class="cwhen"></span><span class="crail"></span></div>` : ""}${
            rows.length ? `<div class="cchain">${[...rows].reverse().map((item) => item.build ? buildRow(item) : chainRow(item)).join("")}</div>` : ""}${
            termCell(b, p, k, { first: k === 0, rail: true })}</div>`}`;
      }).join("")}</div></div>`;
  };
  const trees = `<div class="btrees">${builds.map(tree).join("")}</div>`;
  /* The page's own construction machinery — the base, the suffix the word
     wears, the picker that tries another cited suffix, and the composed form —
     belongs to the step that draws the pieces, not to the space under the
     title (admin, 2026-11-12).  It is printed once, on the rung of the word's
     own stage, because that is the formation whose pieces these are. */
  /* The card that used to stand here — "suffix it wears", its chips and its
     picker — repeated what the tree below already draws, piece by piece
     (admin, 2026-11-12: "that is denoted as part of the timeline").  The
     composition tools live on the rung's own `build…` control. */
  return `<li class="constructstep${ours ? " ours" : ""}${builds.length > 1 ? " multi" : ""}"
      data-tip="${esc(builds.length > 1 ? `${builds.length} constructions are recorded for this form; each tab is one of them, and none is preferred over another.` : tipOf(builds[0]))}">
    <div class="rail top" aria-hidden="true"></div>
    ${radios}${tabs}${trees}
    <div class="rail foot" aria-hidden="true"></div>
  </li>`;
}

/* A compound's pieces are drawn once, in the timeline (admin, 2026-11-13:
   "I thought we completely got rid of the WHERE THE PIECES COME FROM section.
   Please remove this section from all word pages entirely; what it wants to
   show is already shown in the timeline").  The section between the header and
   the timeline — each piece with its own chain, meeting again at the headword —
   was a second copy of the construction step, and it appeared exactly when the
   step and the join did not agree, so the reader got two analyses of one word.
   The payload keeps `joins` and `seam_join`: the timeline's step and the band's
   reading are built from them. */

function renderBuiltFrom(d) {
  const rows = (d.built_from || []).map((r) => {
    const suffixes = (r.suffixes || []).length
      ? `<span class="built-suffix">${r.suffixes.map((s) => `+ <span class="mono">${esc(s)}</span>`).join(" ")}</span>`
      : "";
    /* A formation whose root grade the handbooks fix says so here too: the
       root of *tr̥stós stands in zero grade because *-tó- carries the accent
       (2026-11-12). */
    const grade = r.grade && r.grade.label
      ? `<span class="cgrade" data-tip="${esc(r.grade.note || r.grade.label)}">${esc(r.grade.label)}</span>`
      : "";
    return `<li><a class="builtword" href="${wordHref(d.lang, r.word, true)}">${esc(pf(starred(r.word, d.lang, d.kind, d.script)))}</a>
      ${suffixes}${grade}<span class="sub">${esc([r.pos, r.gloss ? `“${r.gloss}”` : ""].filter(Boolean).join(" · "))}</span>
      ${r.confidence && r.confidence !== "stated" ? `<span class="badge">${esc(r.confidence)}</span>` : ""}</li>`;
  });
  return `<section class="builtfrom reveal">
    <h2>Words built on it <span class="sub count">· ${rows.length}</span></h2>
    <ul class="builtlist">${rows.join("")}</ul>
  </section>`;
}

/* Where a record was read. The server resolves each source: a hand-built
   supplement may cite a source with a link of its own (a dictionary, an
   article), and a Wiktionary row carries the entry's own page. The badge is a
   door to the citation, never a claim about the form (2026-11-08). */
const recordSources = (rec) => ((rec && rec.sources) || []).filter((s) => s && (s.title || s.url));
const isWiktionary = (s) => /wiktionary/i.test(`${(s && s.id) || ""} ${(s && s.title) || ""} ${(s && s.url) || ""}`);
/* A link is a page, not a site (admin, 2026-11-12): the server hands over one
   row per page that is *recorded* — a Wiktionary article, Dehkhoda's own entry
   for the word — and a word with no recorded page has none, so no icon is
   drawn.  An icon that opens nothing said nothing. */
const recordPages = (rec) => ((rec && rec.pages) || []).filter((p) => p && p.url);
/* The citation lives in the record's own tooltip, not on a printed line under
   every word (2026-11-08): hovering the RECORDED badge (or the
   record the laws reproduce) names where the word was read. */
const recordSourceText = (rec) => {
  const rows = recordPages(rec);
  /* Name the page the word was read on, not the site: "Wiktionary" alone is a
     link to a front page and says nothing about this word (2026-11-08).  A
     dictionary's own entry is named the same way — Dehkhoda's page for کبود,
     not "vajehyab.com" (admin, 2026-11-12). */
  const named = (s) => {
    try {
      const parts = decodeURIComponent(new URL(s.url).pathname).split("/").filter(Boolean);
      const page = (parts[parts.length - 1] || "").replace(/_/g, " ");
      if (!page) return s.title || "";
      if (s.kind === "wiktionary") return `Wiktionary entry “${page}”`;
      return `${(s.title || "the dictionary").split(",")[0]} entry “${page}”`;
    } catch (e) { return s.title || ""; }
  };
  const titles = [...new Set(rows.map(named).filter(Boolean))].join(" · ");
  const ref = rows.map((s) => s.ref).filter(Boolean).join(" ").trim().replace(/\.+$/, "");
  if (!titles && !ref) return "";
  return ` Source: ${titles || "the dictionary"}${ref ? ` — ${ref}` : ""}.`;
};
const recordSourceTip = (rec, langName) => {
  const how = rec && rec.evidence === "literary"
    ? "a reconstruction kept in the literature — no text attests it"
    : "attested in a text or a dictionary";
  /* The tooltip names the source; it does not instruct the reader to click
     (2026-11-08: the sentence telling them to open the record is
     gone). The mark is plainly a link, so the words were only noise on every
     recorded word. */
  return `The ${langName} record of this word: ${how}.` + recordSourceText(rec);
};
/* The record is marked, not labelled (2026-11-08): a mark on the recorded
   word's top-right corner — where the ✓ of a match sits — and it opens where
   the word was read. The mark is Wiktionary's own initial W, set in a serif
   face like Wikipedia's globe-W: the monoline W read as a generic letter, and
   a serifed W says "Wiktionary" without saying "Wikipedia" (admin,
   2026-11-12). A real glyph, not a drawing, so the serifs survive at 11 px,
   where a stroked path would blur into a zigzag. */
const wiktionaryIcon = `<span class="wmark" aria-hidden="true">W</span>`;
const bookGlyph = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"
  fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
  stroke-linejoin="round"><path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H19v14.5H6a2 2 0 0 0-2 2V4.5Z"/><path d="M19 17.5V21H6a2 2 0 0 1-2-2"/></svg>`;
const pageGlyph = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"
  fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
  stroke-linejoin="round"><path d="M6 3h8l5 5v13H6V3Z"/><path d="M14 3v5h5"/></svg>`;
const pageMark = (p) => (p.kind === "wiktionary" ? wiktionaryIcon
  : p.kind === "dictionary" ? bookGlyph : pageGlyph);
/* The corner mark is the door, and it is one per recorded page (admin,
   2026-11-12): the W of the word's Wiktionary article and the book of its
   Dehkhoda entry stand side by side on the recorded word's corner, each opening
   its own page.  No page recorded, no mark. */
const recordTag = (rec, stage, langName, label = "recorded", tipOverride = "") => {
  if (!rec) return "";
  const tip = esc(tipOverride || recordSourceTip(rec, langName));
  const marks = recordPages(rec).sort((a, b) =>
    (a.kind === "wiktionary" ? 0 : 1) - (b.kind === "wiktionary" ? 0 : 1));
  if (!marks.length) return "";
  const links = marks.map((p) => {
    const ext = /^https?:/i.test(p.url) ? ' target="_blank" rel="noopener"' : "";
    const name = p.kind === "wiktionary" ? "Wiktionary"
      : (p.title || "the dictionary").split(",")[0];
    return `<a class="recorddot${p.kind === "wiktionary" ? " wikt" : ""}" href="${esc(p.url)}"${ext}
      data-tip="${tip}" aria-label="${esc(`${label} — open ${name}`)}">${pageMark(p)}</a>`;
  }).join("");
  return `<span class="recordmarks">${links}</span>`;
};
/* A recorded word is a form with its record mark on the word's own corner and
   its reading underneath. The mark opens where the word was read; the word
   itself stays a link to its page. */
const recordWord = (rec, stage, langName, opts = {}, label = "recorded", tipOverride = "") =>
  `<span class="recword">${form(rec.w, stage, { ...opts, stack: true,
    markHtml: recordTag(rec, stage, langName, label, tipOverride) })}</span>`;
/* Every rung is editable, and the control is a pencil rather than the word
   "edit", so it reads as a tool on the form it changes (2026-11-08). */
const editIcon = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 20h4L19 9l-4-4L4 16v4Z"/><path d="M13.5 6.5l4 4"/></svg>`;
const editButton = (stage, name) => `<button class="editbtn icon" type="button" data-edit="${esc(stage)}"
     title="Type a different form for ${esc(name)} and re-derive every stage below it"
     aria-label="Edit the form for ${esc(name)}">${editIcon}</button>`;

function renderHierarchy(h, d, opts) {
  if (!h) {
    return `<h2>Where it comes from</h2>
      <p class="sub">No recorded ancestry for this word — it may be an early borrowing, a derivation, or not analysed yet.</p>`;
  }
  const r = h.result || {};
  const status = r.match
    ? `<span class="badge established" data-tip="${esc(r.match_via_script
        ? "A registered law chain produces a form that is one of the readings the word's own script allows; the record beside it is what the text writes."
        : "A registered law chain reproduces the word exactly.")}">${
        r.match_via_script ? "exact, read from the script"
          : r.match_via_translit ? "exact, via its reading" : "exact"}</span>`
    : r.written_match
      /* The laws stop at a phonemic form and the writing conventions spell it
         exactly (data/spelling/). That is a *spelling* match, counted in the
         orthographic layer and never in the sound-law figure — so the badge
         says which claim it is instead of calling a spelled word a failure
         (2026-11-08: wɔ́lf is not a different word). */
      ? `<span class="badge orthographic" data-tip="The sound laws stop at ${esc(pf(r.form))}; the writing conventions of ${esc(d ? d.lang_name : "this language")} spell that exactly as the recorded word. Spelling is a separate layer and is scored apart from the sound laws (see coverage).">spelled — ${esc(r.written)}</span>`
      : r.cited_stem
        /* The laws end where the recorded ancestor ends, and the ancestor is an
           inflected form while the dictionary cites the stem (Sanskrit देव
           devá- against the nominative deváḥ). That is the citation, not a
           sound law, so the badge states both forms and claims neither as an
           exact reconstruction (2026-11-09). */
        ? `<span class="badge orthographic" data-tip="The laws produce ${esc(pf(r.cited_stem.output))}, an inflected form of the word; the dictionary cites the stem ${esc(pf(r.cited_stem.stem))}, which it writes ${esc(r.cited_stem.written)}. The difference is the citation form (data/citation/), counted apart from the sound laws.">cited as its stem — ${esc(r.cited_stem.written)}${
          r.cited_stem.cited_as
            ? `, for the ${esc(pf(r.cited_stem.output))} of the paradigm (stem-final ${esc(r.cited_stem.cited_as)})`
            : `, from ${esc(pf(r.cited_stem.stem))} + ${esc(r.cited_stem.ending)}`}</span>`
        /* A word whose record names no ancestor is not a near miss: the
           ladder starts at the word itself, so "differs" would accuse a word
           of failing a test it never took.  It says what is actually true
           (2026-11-10). */
        /* Proto-Indo-European has no ancestor to record: the model stops
           there, and saying "no origin recorded" would report a gap where the
           family simply begins (2026-11-12). */
        : r.status === "start" && h.levels && h.levels[0] && h.levels[0].stage === "ine-pro"
          ? `<span class="badge" data-tip="Proto-Indo-European is the top of the family this model covers: nothing above it is modelled, and an ancestor would be outside the family.">top of the family</span>`
        /* A word the record builds out of pieces has an origin — the step
           above it — so it must not be called unexplained (2026-11-12). */
        : r.status === "start" && (h.levels || []).some((l) => (l.builds || []).length)
          ? `<span class="badge" data-tip="The record states how this word was made: the construction stands above it, and its pieces carry their own timelines.">built from recorded pieces</span>`
        : r.status === "start"
          ? `<span class="badge" data-tip="The record names no ancestor for this word: the ladder starts here. A seam below, when there is one, says what the word is made of, and a formation is not a derivation.">no origin recorded</span>`
        /* A stage the reader carried the etymon into is a reading of the
           laws, not a verdict on the etymon: the word's own standing is above
           it, on its own rung (admin, 2026-11-12). */
        : (d && d.is_root && (h.path || []).length)
          ? `<span class="badge" data-tip="This stage is where the registered laws carry the etymon; it is a reconstruction, and the etymon's own record stands above it.">descended by the laws</span>`
          : `<span class="badge warn" data-tip="The laws do not reach the attested form yet. The missing step is the worklist in docs/COVERAGE.md.">differs — the worklist</span>`;
  /* A word's own pathway: a registered law that never applied to it. The bar
     names the law, quotes the reason stored with it, and offers the plain
     law-only view — the page never hides that a law was left out. */
  const pw = h.pathway;
  const pwOff = new Set((pw && pw.disabled) || []);
  /* A pathway may also switch a law ON. A formation law (the animal suffix
     *-ka-) is registered off for every word because it adds a morpheme; the
     word whose record says it wears the suffix turns it on here, and the bar
     says so rather than leaving the reader to wonder why this word climbs
     from Proto-Indo-European when its neighbours do not (2026-11-08). */
  const pwOn = new Set((pw && pw.enabled) || []);
  const lawNames = (keys) => [...keys]
    .map((k) => `<span class="mono">${esc(k.split(":").pop())}</span>`).join(", ");
  const pathwayBadge = pw
    ? `<span class="badge established">recorded pathway</span>`
    : h.pathway_available && ladderState && ladderState.pathway === false
      ? `<span class="badge">laws unfiltered</span>` : "";
  const pathwayBar = pw
    ? `<div class="laws-bar pathway-bar reveal">
        <span class="sub">${esc(pw.note || "this word has its own law chain")}
          ${pwOff.size ? `${lawNames(pwOff)} ${pwOff.size === 1 ? "is" : "are"} switched off for this word.` : ""}
          ${pwOn.size ? `The formation law ${lawNames(pwOn)} is switched <b>on</b> for this word — it adds a
            cited morpheme and is off for every word whose record does not wear that suffix.` : ""}
          ${(pw.references || []).length ? `Sources: ${pw.references.map((r) => `<span class="mono">${esc(r)}</span>`).join(", ")}.` : ""}</span>
      </div>`
    : h.pathway_available && ladderState && ladderState.pathway === false
      ? `<div class="laws-bar pathway-bar reveal">
          <span class="sub">${h.pathway_enables
            ? "The laws are shown as registered, without the formation law this word's own pathway switches on."
            : "The laws are shown as registered, including the one this word's own pathway leaves out."}</span>
          <button class="ghost" type="button" data-apply-pathway="1">use this word's pathway</button>
        </div>` : "";
  /* Laws the reader switched off themselves. A page without the list (an
     older payload, or the render fixtures) falls back to the count. */
  const myselfOff = Array.isArray(h.disabled)
    ? h.disabled.filter((k) => !pwOff.has(k)).length
    : Math.max(0, (h.switched_off || 0) - pwOff.size);
  const offBadge = myselfOff
    ? `<span class="badge warn">${myselfOff} ${myselfOff === 1 ? "law is" : "laws are"} switched off</span>` : "";
  const switched = myselfOff
    ? `<div class="laws-bar reveal">
        <button class="ghost" type="button" data-reset="1">Switch them all back on</button>
      </div>` : "";
  const formed = h.formed;
  const stageName = (id) => {
    const hit = [...(h.levels || []), ...(h.earlier || [])].find((x) => (x.stage || x.id) === id);
    return (hit && hit.name) || id;
  };
  /* A word the dictionary records as a formation (گربه = PIE *h₂wl̥pís + *-ka-)
     is not inherited sound by sound, and no law may add a suffix. The note says
     so once, names the base and the suffix, and keeps the cited sentence the
     record rests on (2026-11-08, de Vaan 2000). */
  const formedNote = formed
    ? `this word is <b>formed</b>, not inherited sound by sound: `
      + `${(formed.from || []).map(([stage, word]) => `${esc(stageName(stage))} ${form(word, stage, { ev: "literary" })}`).join(", ")}`
      + `${formed.suffix ? ` plus the suffix <span class="mono">${esc(formed.suffix)}</span>` : ""}. `
      + `${esc(formed.note || "")} `
      + `${(formed.sources || []).length ? `Sources: ${formed.sources.map((s) => `<span class="mono">${esc(s)}</span>`).join(", ")}.` : ""}`
    : "no form of this word is linked to them in the data.";
  const earlier = (h.earlier || []).length
    ? (h.start_recorded
      ? `<p class="sub ladder-note">You asked this ladder to start at the
          <b>${esc(h.start_name)}</b> form the record names. The stages above it —
          ${h.earlier.map((e) => `${esc(e.name)}${e.era_label ? ` (${esc(e.era_label)})` : ""}`).join(", ")}
          — are listed, not derived: nothing here claims they led to this form.</p>`
      : h.build && h.build.base_chosen
      ? `<p class="sub ladder-note">You began the timeline at <b>${esc(h.build.stage_name)}</b>
          <span class="mono">${esc(pf(h.build.base || ""))}</span>, a word of that stage in its own right.
          ${(h.build_above || []).length
            ? `The stages above it — ${h.build_above.map((e) => esc(e.name)).join(", ")} —
               belong to that word's own history, not to this join.`
            : `The stages above that word are its own history, not this join's.`}</p>`
      /* The stages above a word are no longer announced under the heading:
         the timeline itself is the statement, and when a branch ends in a ???
         a paragraph saying "earlier stages exist" only repeats it (admin,
         2026-11-12). */
      : "") : "";
  /* A record may name a register of the stage the form is read at ("inherited
     from Late Latin"): the rung is called Latin because that is the stage the
     laws run from, and the page says which register the record actually named
     (data/language_varieties.yaml, 2026-11-09). */
  const varietyNote = (!h.start_recorded && h.start_variety)
    ? `<p class="sub ladder-note">The record names this form <b>${esc(h.start_variety)}</b>;
        it is read at the <b>${esc(h.start_name)}</b> stage, so the laws out of
        ${esc(h.start_name)} apply to it unchanged.</p>`
    : "";

  /* Every form is a door to its own page (2026-11-08). The page being read is
     already open, so *that word's own form* stays plain; every other form opens
     its word page when a glossary holds it and the "not recorded here" page
     when it does not.  The exclusion used to cover the whole language, which
     left the pieces of a construction — another word, the same language — with
     no door at all (admin, 2026-11-12). */
  const via = d && d.word ? `${d.lang}/${d.word}` : "";
  const linkTo = (stage, w, known) => (!d || !w
    || (stage === d.lang && w === d.word) ? "" : wordHref(stage, w, known, via));
  const rungs = h.levels.map((level, i) => {
    const prev = i ? h.levels[i - 1] : null;
    const gap = i ? eraGap(prev.era_mid, level.era_mid) : 0;
    const here = level.stage === d.lang;
    /* The colour claim comes first, then this rung's own situation, so a
       hover always answers "is this word attested?" before anything else. */
    const tip = (level.edited
      ? "The form you typed to start this path. It is a hypothesis, not a record. "
      : level.status === "start"
      ? "The topmost recorded ancestor this ladder starts from. "
      : level.status === "match"
        ? "The registered laws reproduce a recorded form at this stage. "
        : level.status === "cited"
          ? "The registered laws produce an inflected form of this word; the dictionary cites its stem. "
        : level.status === "differs"
          ? "The registered laws produce this form, but a different form is recorded here. "
          : "Nothing is recorded for this word at this stage; this is what the laws produce. ")
      + evidenceTip(level.evidence);
    const rec = level.recorded;
    /* A record is a word only when the stage's glossary holds it.  A form the
       etymology row names but no entry spells is not a word of that stage: the
       page prints it dark red, gives it no ✓ and no halo, and says plainly that
       there is no entry for it (admin, 2026-11-12). */
    /* A stage this model holds no glossary for (Proto-Italic, Proto-Hellenic)
       is not a hole in a word's record: the rung quotes the form and the page
       says the model describes no glossary there (2026-11-13). */
    const unmodelled = !!(rec && rec.modelled === false && rec.known !== true);
    const held = !!(rec && (rec.known !== false || unmodelled));
    /* The record belongs beside the reconstruction, not below it: what the laws
       produce and what that stage's glossary or text has are shown on one line.
       When they are the same form it is printed once, glowing, with a ✓ — so a
       match reads as a match and a miss shows both forms (2026-11-07). */
    const same = !!(rec && rec.same);
    /* Two ways a printed form can be the record: the laws derived it
       (`matches`), or it is the record the ladder starts from (`starts`).
       The first rung has no law above it, so it used to stay unlit beside the
       derived form below it and read as less certain than its own descendant
       (2026-11-08, Old Persian 𐎭𐎼𐎹).  A form no glossary holds can be
       neither: there is nothing for the laws to have matched. */
    const matched = held && !!(rec && (rec.matches || rec.starts));
    const recTip = rec && !held
      ? `No entry in ${level.name}'s glossary is spelled ${rec.w}. The etymology names this form, and the laws run from it, but the glossary does not hold it — so it is no word of the stage here.`
      : rec
      ? `Recorded form for ${level.name}${rec.evidence === "literary"
          ? " in the literature — no text attests it."
          : " in a text or a dictionary — attested."}`
        + (rec.headword && rec.headword !== rec.w
            ? ` The glossary heads this word ${rec.headword}; the row quoted here spells it ${rec.w}, and the two are one reading.`
            : "")
        + (rec.starts
            ? " The ladder starts from this record: it is what the laws below are run on, not something derived."
            : matched
              ? (rec.via && rec.via !== rec.w
                  ? ` The registered laws produce its recorded reading “${rec.via}”.`
                  : " The registered laws produce exactly this form.")
              : rec.notation
                /* One consonant, two letters: the source transcribes the
                   sign with v, the laws write *w. Explained, never counted as
                   a match (2026-11-08: 𐎭𐎡𐎺). */
                ? ` The letters differ only in ${rec.notation}: the source transcribes one sign, the laws write the other consonant. That is the transcription, not the word — it is not counted as a match.`
                : "")
        + recordSourceText(rec)
      : "";
    /* A record quoted without a sign the headword carries is the same word:
       the glossary's own spelling is its door (service._record_block sets
       `headword`), so the rung never links to a spelling no page holds
       (2026-11-12). */
    const recHref = rec ? linkTo(level.stage, rec.headword || rec.w, rec.known) : "";
    const madeHref = linkTo(level.stage, level.form, level.form_known);
    /* Only a formation law puts a morpheme into a word, so only it gets a
       highlight: the cited suffix's surface (-nás appears as -nah). An
       ordinary sound change is a different colour claim and must not look like
       an affix (2026-11-08: suffixes in another colour). */
    const cited = (level.formation && level.formation.surface) || "";
    const added = cited ? cited.replace(/^-/, "") : "";
    /* What the left column of the rung prints.  A word written in its own
       script is shown by its reading — the layer a reconstruction is made
       from — and the script stands beside it in the record (admin,
       2026-11-13).  `level.form` stays the recorded form: it is what the page
       links to and what an edit changes. */
    const shownForm = level.display || level.form;
    const recOpts = rec ? {
      /* A form with no entry is non-existent, whatever the literature says
         about it: dark red, like every other form the glossary does not hold
         (admin, 2026-11-12). */
      ev: held ? rec.evidence : "missing",
      reading: rec.reading, signs: rec.signs || "", show: rec.show_reading,
      auto: !!rec.reading_auto, note: rec.reading_note,
      /* When the laws' form and the record agree, this is the only line printed
         for the rung, so the suffix the formation law added is still marked. */
      mark: same ? (added || undefined) : undefined,
      tip: recTip, matched, cornerTick: matched && !rec.unverified,
      cornerWarn: !!rec.unverified, focus: same,
      href: recHref, hrefTip: rec.known
        ? `Open ${rec.headword || rec.w} in ${level.name}` : `Open this form — nothing in ${level.name}'s glossary records it`,
    } : {};
    const recForm = rec ? form(rec.w, level.stage, { ...recOpts, stack: true }) : "";
    /* One glowing form when the two agree; otherwise the produced form and the
       recorded form, each marked on its own top-right corner — ✓ for a match,
       the page glyph for a record (2026-11-08). */
    /* A formation law's morpheme is printed in the accent colour on the rung
       where the law applied, so the suffix can be seen inside the word. */
    const madeForm = () => form(shownForm, level.stage, {
      ev: level.evidence, tip, focus: true, href: madeHref,
      mark: added || undefined,
      hrefTip: level.form_known
        ? `Open ${level.form} in ${level.name}`
        : `Open this form — nothing in ${level.name}'s glossary records it`,
    });
    /* The pencil sits where the reading starts: on a rung that also records a
       word it follows the form the laws produced, never the record, so it is
       clear which form an edit changes (2026-11-08). The record is a
       second word and stands under the reconstruction with its own badge. */
    const baseRung = !!(h.hypothesis && i === 0);
    const formsLine = !rec
      ? `${madeForm()}${editButton(level.stage, level.name)}`
      : same
        ? `${recForm}${editButton(level.stage, level.name)}`
        : `${madeForm()}${editButton(level.stage, level.name)}${recordWord(rec,
             level.stage, level.name, recOpts, baseRung ? "base" : "recorded",
             baseRung ? "The dictionary's form for the base this suffix was added to; the form on the left is that base composed with the suffix you chose."
               + recordSourceText(rec) : "")}`;
    const more = rec && (rec.more || []).length
      ? `<span class="sub">also ${rec.more.map((w) => esc(pf(starred(w, level.stage, level.kind)))).join(" · ")}</span>` : "";
    /* What the dictionary says the form meant at that stage, so a rung is a
       word with a sense and not only a string of letters. */
    const sense = rec && rec.gloss
      ? `<span class="sense">${rec.pos ? `${esc(rec.pos)} · ` : ""}“${esc(rec.gloss)}”</span>` : "";
    const notation = rec && rec.notation
      ? `<span class="sub notation" data-tip="The source transcribes the Old Persian sign 𐎺 with v, the sound laws write the same consonant *w. Spelling, not phonology: not counted as a match.">spelled ${esc(rec.notation)}</span>`
      : "";
    /* What the script writes when the record is in another script: the laws'
       form is one of the readings the signs allow, and the page prints the
       signs so the reader can check the fit (2026-11-08: 𐎺𐎼𐎣). */
    const fit = rec && rec.fit;
    const fitWords = [];
    if (fit) {
      if ((fit.unwritten || []).length) fitWords.push(`the script leaves ${fit.unwritten.map((u) => `<span class="mono">${esc(u)}</span>`).join(" ")} unwritten`);
      if (!fit.logogram && (fit.filler || []).length) fitWords.push("a vowel sign carries a bare consonant");
      /* A sign that writes the end of a word without a sound of its own is a
         convention of the script, so the rung says which one it used instead
         of leaving the extra glyph unexplained (2026-11-08). */
      if (fit.convention && fit.convention.name) fitWords.push(esc(fit.convention.name));
      if (fit.logogram) fitWords.push("one sign for the whole word");
    }
    const fitNote = fit
      ? `<span class="sub readfit" data-tip="${esc(`Reading the signs: the word is written ${fit.translit}. A syllabary writes consonants and some vowels, so the string a dictionary spells is not the same string as the signs; this form is a reading they allow.`)}"
          >read <span class="mono">${esc(fit.translit)}</span>${fitWords.length ? ` · ${fitWords.join(" · ")}` : ""}</span>`
      : "";
    /* A green rung is a claim about a written word, so the record itself names
       its citation — in the tooltip of the form or its RECORDED badge, never on
       a printed line under every word (2026-11-08). */
    /* What a rung says under its form is one of two things: what the word
       means (the sense line above), or that the glossary has no entry for it.
       "Transliteration only" explained the machinery instead of the word, and
       it fired exactly where no entry exists — the case the reader should read
       as "no entry for this word" (admin, 2026-11-12). */
    const entryNote = rec && !held
      ? (level.non_ie
        /* A stage outside the family has no glossary in this model, and that is
           a fact about the model, not about the word: it says "non-PIE word"
           rather than "no entry" (admin, 2026-11-13). */
        ? `<span class="sub coutside" data-tip="${esc(`${level.name} is outside the Indo-European family: the form is quoted from the record, and this model keeps no ${level.name} glossary — nothing is missing.`)}">non-PIE word</span>`
        : `<span class="sub norec" data-tip="Nothing in ${esc(level.name)}'s glossary is spelled ${esc(rec.w)}: no headword, no reading of the signs, no entry. The form here is the one the etymology names, and nothing else in this stage records it.">no entry for this word</span>`)
      : (unmodelled
        ? `<span class="sub norec" data-tip="This model holds no ${esc(level.name)} glossary, so the form is quoted from the record and is not linked: nothing is missing from the word's own stage, only from a stage the model does not describe.">no ${esc(level.name)} glossary in this model</span>`
        : "");
    /* The laws' form is one reading of the signs the record writes, and the
       record itself reads them another way — an abjad's l-w-c can stand for
       rōč and rōz, and the dictionary says rōz. The rung prints both readings
       instead of leaving a red form beside a green word unexplained
       (2026-11-11). */
    const readDiffers = (level.status === "differs" && rec && rec.reading && rec.fit)
      ? `<span class="sub readfit" data-tip="${esc(`The laws produce a form the writing ${rec.fit.translit || ""} can stand for, but the dictionary reads this spelling ${rec.reading}; the difference is the record's, not a gap in the laws.`)}">the writing allows it — the record reads ${esc(rec.reading)}</span>`
      : "";
    /* A near miss is a question, not a verdict: the record is shown, and the
       rung says in words that nobody has verified the match yet (admin,
       2026-11-12). */
    const unverifiedNote = rec && rec.unverified
      ? `<span class="sub unverifiednote" data-tip="${esc(
          rec.review && rec.review.basis === "letters"
            ? `The letters of this entry agree with the form the laws produce, but no reading is recorded for it, and an abjad writes no vowels: the letters alone cannot verify a match, so it is kept for review instead of being counted.`
            : `The record is read ${rec.review && rec.review.record ? rec.review.record : rec.reading || rec.w}; the laws give ${level.form}. Every sound but the ending agrees, and no registered law accounts for that difference — so the match is kept for review instead of being counted.`)}">match not verified</span>`
      : "";
    const meta = [sense, more, notation, fitNote, readDiffers, entryNote, unverifiedNote].filter(Boolean).join(" ");
    /* Whether a stage is a written language or a reconstruction is a claim
       about the language, not a badge on the word: the name in the timeline
       carries it in its colour, and says it in words on hover, with the
       branch and script the registry records (2026-11-07). */
    const languageTip = (level.kind === "proto"
      ? `Reconstructed stage — no text or speaker records it; its forms are rebuilt from the languages descended from it, and normally written with a leading *.`
      : `Attested language — its words survive in texts, inscriptions or a dictionary, so forms can be checked against the record.`)
      + (level.branch ? ` Branch: ${level.branch}.` : "")
      + (level.era_label ? ` In use ${level.era_label}.` : "")
      /* "reconstructed" is the transcription's own script, not a writing
         system a reader can picture, so it is left out. */
      + (level.script && level.script !== "reconstructed" ? ` Script: ${level.script}.` : "");
    /* The laws go above this rung, in the timeline between it and the form
       they were run on (2026-11-08). */
    const laws = level.edited ? "" : renderLaws(level, prev ? prev.name : "", prev ? prev.stage : "");
    return `${level.built ? buildStep(level) : lawStep(laws, gap)}${constructStep(level, i, linkTo, opts)}<li class="rung${here ? " here" : ""}${level.changed ? " changed" : ""}"
        data-stage="${esc(level.stage)}" style="--gap:${laws ? stepGap(gap) : gap}px;--i:${i}" data-rung="${i}">
      <div class="when">
        <span class="when-name kind-${esc(level.kind === "proto" ? "proto" : "attested")}"
              data-tip="${esc(languageTip)}" tabindex="0">${esc(level.name)}</span>
        <span class="when-era">${esc(level.era_label || "date unknown")}</span>
        ${here ? `<span class="when-here">this word</span>` : ""}
        ${(h.path || []).includes(level.stage)
          ? `<button class="change" type="button" data-cut="${esc(level.stage)}"
               title="Choose another language here: ${esc(level.name)} and every stage below it leave the timeline">change</button>` : ""}
      </div>
      <div class="rail"><i aria-hidden="true"></i><button class="rdot" type="button"
        data-cstage="${esc(level.stage)}" data-cform="${esc(level.form)}"
        data-cname="${esc(level.name)}"
        aria-label="Construct a word from ${esc(level.form)} in ${esc(level.name)}"
        data-tip="Construct: open a row above this word and add a word, a suffix or an ending to it."></button></div>
      <div class="rung-body">
        <div class="rung-forms">
          ${formsLine}
          ${level.edited ? `<span class="badge edited" data-tip="You typed this form; nothing attests it unless it is also recorded.">edited</span>` : ""}
          ${level.built ? `<span class="badge built" data-tip="This rung is a formation you asked for — words joined or a morpheme added at this stage. A formation is not a sound law, and the word's own band is unchanged.">built here</span>` : ""}
          ${level.changed ? `<span class="badge changed" data-tip="A switched-off law changed this form.">changed</span>` : ""}
          ${level.changed ? `<span class="was">was <span class="mono">${esc(pf(level.baseline))}</span></span>` : ""}
          ${level.written ? `<span class="written" data-tip="${esc(`The laws stop at the phonemic form ${level.form}; the writing conventions in data/spelling/${level.stage}.yaml spell it exactly as the dictionary records it. Spelling is a separate layer and is not a sound law.`)}">
             written <span class="mono">${esc(level.written)}</span></span>` : ""}
        </div>
        ${rec
          ? (meta ? `<div class="rung-rec">${meta}</div>` : "")
          /* A rung nothing records says so on hover, not in a sentence under
             every such form (2026-11-08). The one exception is a
             ladder that starts from the word's cognate set: that is not the
             same fact as "nothing here", and it is not in the hover text. */
          : level.status === "start" && h.linked_by_set
            ? `<div class="rung-rec"><span class="nosrc">no form for this etymon in the
                 ${esc(level.name)} glossary — the ladder starts from the word's cognate set</span></div>`
            : ""}
        ${level.edited || !level.formation ? "" : formationLine(level, (h.hypothesis && h.hypothesis.suffix.id) || "")}
      </div>
    </li>`;
  }).join("");

  const notes = [];
  /* «The laws do reach the word exactly» is said only when the word's own
     rung reproduces its record.  A form the signs allow but the record reads
     otherwise (𐎺𐎼𐎣 read vr̥kaʰ, the laws' wˈarkah) is not exact, and the
     rung already prints both readings (admin, 2026-11-13). */
  if (h.exact && !r.match && !h.edited && h.exact.reproduces !== false) {
    notes.push(`The full path from ${esc(h.start_name)} differs, but the laws do reach the word exactly from
      <b>${esc(h.exact.name)} ${esc(pf(starred(h.exact.form, h.exact.stage)))}</b> (${h.exact.steps} ${h.exact.steps === 1 ? "law" : "laws"} below it);
      the gap is in the steps above.`);
  }
  if (r.match && r.match_via_translit) {
    notes.push(`The laws produce <span class="mono">${esc(pf(starred(r.form, (d || {}).lang)))}</span>, the romanisation the dictionary records
      for ${esc(r.target)}. Spelling is a separate layer.`);
  }
  /* The etymon is a root and the ladder starts there. When the ladder starts
     below it instead (a set-linked word), the note under it says why; this one
     would be false, because the top rung is a word, not the root. */
  if (h.root && !h.edited && (!h.linked_by_set || h.set_start)) {
    const rec = h.etymon_record;
    const gloss = rec && rec.gloss
      ? ` — <span class="mono">${esc(pf(starred(rec.w, h.start)))}</span>, ${rec.pos ? `${esc(rec.pos)} ` : ""}“${esc(rec.gloss)}”`
      : ` (<span class="mono">${esc(pf(starred(h.etymon || "", h.start)))}</span>)`;
    notes.push(`The ancestor this ladder starts from is a <b>root</b>, not a full word${gloss},
      so these steps are rougher than a whole etymon's.`);
  }
  /* English *book* reaches PIE only through its cognate set: Wiktionary's own
     ancestry rows stop at Proto-Germanic. The page says which link it used. */
  if (h.linked_by_set && !h.edited && h.set_start) {
    /* A code with no English name in the registry is left out rather than
       printed bare (``xno`` for Anglo-Norman is one such). */
    const off = (h.off_chain || []).filter((x) => x.name && x.name !== x.stage)
      .map((x) => x.name).reverse();
    if (off.length) {
      notes.push(`Wiktionary traces this word through <b>${off.slice(0, 4).join(", ")}</b> — languages
        outside the ${esc(d.lang_name)} chain modelled here. The <b>${esc(h.start_name)}</b> rung is the
        etymon recorded in the word's <b>cognate set</b>, and the steps below follow that chain — a cognate
        comparison, not this word's own inheritance path.`);
    } else {
      notes.push(`This word's own Wiktionary ancestry stops at <b>${esc((h.ancestry_top || {}).name || "a lower stage")}</b>.
        The <b>${esc(h.start_name)}</b> rung is the etymon recorded in the word's <b>cognate set</b> — a recorded
        link, but not a row in its inheritance chain.`);
    }
  }
  /* The set names a bare root: the ladder keeps the word's own record and the
     root stays above it, related rather than inherited (proposals/010). */
  if (h.linked_by_set && !h.edited && !h.set_start) {
    const stop = (h.ancestry_top || {}).name || "a lower stage";
    const rec = h.etymon_record;
    const root = rec
      ? `${rec.pos === "root" ? "root " : ""}<span class="mono">${esc(pf(starred(rec.w, h.start)))}</span>${rec.gloss ? ` “${esc(rec.gloss)}”` : ""}`
      : `<span class="mono">${esc(pf(starred(h.etymon || "", h.start)))}</span>`;
    const off = (h.off_chain || []).filter((x) => x.name && x.name !== x.stage)
      .map((x) => x.name).reverse();
    const via = off.length
      ? ` Its own path runs through <b>${off.slice(0, 4).join(", ")}</b>, outside the ${esc(d.lang_name)} chain modelled here.`
      : "";
    /* The stages above that ancestor are drawn now, when its own article has
       them: the note says where *this* record starts, not where the column
       does (admin, 2026-11-12). */
    const climbs = (h.levels || []).some((l) => l.climbed);
    notes.push(`This word's own ancestry stops at <b>${stop}</b>.${via} The cognate set relates it to the
      PIE <b>${root}</b>, but a root carries no word's morphology: it is a relation, not an ancestor row.
      The ladder therefore starts at the recorded <b>${esc(h.start_name)}</b>
      <span class="mono">${esc(pf(starred(h.start_form || "", h.start)))}</span>${
        climbs ? ", and the rungs above it are that word's own ladder" : ""}.`);
  }
  /* When the set also records a derived PIE-stage form on the way down (book:
     *bʰóh₂g-s ~ *bʰéh₂g-s, "allotment", above Proto-Germanic *bōks), name it:
     that is why the ladder can only start from the root. */
  /* …unless the timeline already carries that PIE form as a rung of its own:
     the climb went through it, and a note saying it is not a rung would
     contradict the column above (admin, 2026-11-12). */
  const bare = (w) => String(w || "").replace(/^\*/, "").replace(/-/g, "");
  const setShown = (h.levels || []).some((l) => l.climbed
    && l.form && h.set_source && bare(l.form) === bare(h.set_source));
  if (h.set_source && !h.edited && h.ancestry_top && !setShown) {
    const top = h.levels.find((l) => l.stage === h.ancestry_top.stage) || {};
    notes.push(`The cognate set also records <span class="mono">${esc(h.set_source)}</span> at the
      PIE stage above <b>${esc(h.ancestry_top.name)}</b>${top.recorded
        ? ` <span class="mono">${esc(pf(starred(top.recorded.w, top.stage)))}</span>` : ""} — the derived word the root
      belongs to. It stays a record, not a rung: the ladder starts from the word's own ancestor, and
      picking one alternant of that form would be this repo's own reconstruction.`);
  }
  if ((h.missing || []).length) {
    notes.push(`No rule file yet for ${h.missing.map(esc).join(", ")}.`);
  }

  /* An edited start is a hypothesis, and the page says so before the ladder. */
  const editedBadge = h.edited ? `<span class="badge edited">edited start</span>` : "";
  const editedBar = h.edited
    ? `<div class="laws-bar edited-bar reveal">
        <span class="sub">A form you typed for <b>${esc(h.edited.name)}</b>. The stages above it are the
          laws' own work; every stage below is what they make of this form, and each still quotes its own
          record beside it.</span>
        <button class="ghost" type="button" data-unedit="1">reset to recorded ancestry</button>
      </div>` : "";
  /* The formation the reader asked for, said in one line at the top: what was
     joined to what, at which stage, and that it is a formation and not a law.
     The word's own band is untouched, so the bar says that too. */
  const buildBar = h.build
    ? `<div class="laws-bar build-bar reveal">
        <span class="sub">You built the <b>${esc(h.build.stage_name)}</b> form as
          ${h.build.kind === "compound"
            ? "a compound of its own words"
            : h.build.kind === "inflection" ? "an inflected form of a word" : "a word with a suffix"}:
          <span class="mono">${esc(pf(h.build.form))}</span>. A formation is not a sound law — the
          composed form is carried down by the same laws, and the word's own band is unchanged.</span>
        <button class="ghost" type="button" data-unbuild="1">back to the word's record</button>
      </div>` : "";
  /* A path may be stored only when the edit lands exactly on the attested
     word: that is the project's rule, and it is checked again on the server. */
  const canStore = h.edited && r.match && r.attested;
  const storedBadge = canStore && h.stored_pathway
    ? `<span class="badge attested">pathway stored</span>` : "";
  const storeBar = canStore
    ? `<div class="laws-bar store-bar reveal">
        ${h.stored_pathway
          ? `<span class="sub">This exact path is already recorded for <b>${esc(h.word)}</b>.</span>`
          : `<button class="storepath" type="button" data-store-pathway="1">store pathway</button>
             <span class="sub">Your edited path reproduces the attested <b>${esc(h.word)}</b> exactly.
               Store it as a new pathway for this word.</span>`}
      </div>` : "";

  const paths = h.pathways || [];
  const pathwayBlock = paths.length ? `<div class="pathways reveal">
    <h3>Stored pathways <span class="sub">· ${paths.length} for this word</span></h3>
    <ul>${paths.map((p) => `<li>
      <button class="ghost" type="button" data-load-pathway="${esc(p.id)}">load</button>
      <span class="mono pathform">${esc(pf(starred(p.start.form, p.start.stage)))}</span>
      <span class="sub">${esc(p.start.name)} → ${esc(h.word)}</span>
      <span class="sub">· ${(p.laws || []).length} ${(p.laws || []).length === 1 ? "law" : "laws"}
        · ${esc((p.created || "").slice(0, 10))}</span>
      ${p.note ? `<span class="sub">· ${esc(p.note)}</span>` : ""}
    </li>`).join("")}</ul>
  </div>` : "";

  const hypothesisBadge = h.hypothesis ? `<span class="badge hypothesis">another suffix</span>` : "";
  const hypothesisBar = h.hypothesis
    ? `<div class="laws-bar hypothesis-bar reveal">
        <span class="sub">This is not <b>${esc(h.word)}</b> as recorded: the ladder starts from
          <span class="mono">${esc(pf(h.hypothesis.base))}</span> plus
          <span class="mono">${esc(h.hypothesis.suffix.form)}</span>${
            h.hypothesis.law
              ? `, by the registered formation law ${lawLink(h.hypothesis.law.name, h.hypothesis.law.key)}`
              : ", composed here"}. The laws then run as usual and every rung keeps quoting the record.</span>
        <button class="ghost" type="button" data-rung-suffix="">the word as recorded</button>
      </div>${(h.hypothesis.options || []).length ? formationLine({
        name: h.hypothesis.stage_name,
        formation: { options: h.hypothesis.options, suffix: h.hypothesis.suffix.form,
                     surface: h.hypothesis.suffix.surface || "" },
      }, h.hypothesis.suffix.id) : ""}` : "";

  /* The heading states the transition; every chip that qualifies it sits on the
     right of that line, not in bars underneath (2026-11-08). */
  const badges = [status, pathwayBadge, editedBadge, storedBadge, hypothesisBadge, offBadge]
    .filter(Boolean).join("");
  return `<div class="ladder-head reveal" style="--i:3">
    <h2>${h.build ? `Built at ${esc(h.build.stage_name)}` : "Timeline"}</h2>
    <div class="ladder-badges">${badges}</div>
    </div>
    ${buildBar}${hypothesisBar}${editedBar}${storeBar}${pathwayBar}
    ${earlier}${varietyNote}${switched}
    <ol class="ladder reveal" style="--i:4">${rungs}${renderNext(h)}</ol>
    ${notes.length ? `<div class="ladder-notes">${notes.map((n) => `<p class="sub">${n}</p>`).join("")}</div>` : ""}
    ${pathwayBlock}`;
}

/* Carry the timeline on. Every rung has children in the registry; the ones the
   reader may add are the direct descendants of the last rung only, each with
   the form its own transition produces. One click appends a rung and the
   buttons below it become that rung's children, so a word in Old Persian can be
   followed into Middle Persian and Persian without pretending to be a PIE
   etymon (2026-11-08). */
function renderNext(h, fromName) {
  const next = h.next || [];
  if (!next.length) return "";
  const last = (h.levels || []).slice(-1)[0] || {};
  const from = fromName || last.name || "it";
  const state = (r) => {
    if ((r.skipped || []).length) return `<span class="nextstate miss">no rule chain yet</span>`;
    if (r.status === "match" && r.recorded) return `<span class="nextstate hit">✓ ${esc(pf(r.recorded.w))}</span>`;
    if (r.recorded) return `<span class="nextstate miss">≠ ${esc(pf(r.recorded.w))}</span>`;
    return `<span class="nextstate">nothing recorded</span>`;
  };
  /* The rail of the timeline runs straight into the box, and the box is only
     the languages one stage below: no heading, no explanation. One click adds
     a rung and the box moves down to that language's own children
     (2026-11-08). A language with no modelled child ends the
     timeline: this function then returns nothing at all. */
  return `<li class="rung nextrung">
    <div class="rail" aria-hidden="true"><i></i></div>
    <div class="rung-body">
      <div class="nextbox" role="group" aria-label="Carry ${esc(from)} on into a direct descendant">
        <div class="nextgrid">${next.map((r) => `
          <button type="button" class="nextbtn" data-next="${esc(r.l)}"
                  data-tip="${esc(`${r.lang_name}${r.branch ? ` · ${r.branch}` : ""}${r.era_label ? ` · ${r.era_label}` : ""}`)}">
            <span class="nextname">${esc(r.lang_name)}</span>
            <span class="nextera">${esc(r.era_label || "")}</span>
            <span class="nextform mono" dir="auto">${esc(pf(starred(r.form, r.l)))}</span>
            ${state(r)}
          </button>`).join("")}</div>
      </div>
    </div>
  </li>`;
}

/* The ladder is edited in place. Switching a law or typing a starting form
   asks the server for the same word's ladder again and swaps only this
   section: no reload, no scroll jump, no page fade. Changed rungs pulse, the
   law switch flips under the finger at once, and the URL is kept in step
   through pushState so a state is still a link and Back still undoes it. */
let ladderState = null;
let ladderRequest = 0;

function syncLadderUrl() {
  const L = ladderState;
  if (!L) return;
  const qs = new URLSearchParams();
  if (L.sense > 0 && L.variants > 1) qs.set("sense", String(L.sense));
  if (L.off.size) qs.set("off", [...L.off].sort().join(","));
  if (L.edit) { qs.set("from", L.edit.stage); qs.set("form", L.edit.form); }
  if (L.record) {
    qs.set("from", L.record.stage); qs.set("form", L.record.form); qs.set("recorded", "1");
  }
  if (L.suffix) qs.set("suffix", L.suffix);
  if (L.build) qs.set("build", L.build);
  if (L.path.length) qs.set("path", L.path.join(","));
  if (L.pathway === false) qs.set("pathway", "0");
  const tail = qs.toString();
  const url = `#/word/${encodeURIComponent(L.lang)}/${encodeURIComponent(L.word)}${tail ? `?${tail}` : ""}`;
  if (location.hash !== url) {
    history.pushState({ ladder: true }, "", url);
    lastHref = location.href;
  }
}

function paintLadder(h) {
  const L = ladderState;
  const box = $("#ladder");
  if (!L || !box) return;
  const before = {};
  ((L.data && L.data.levels) || []).forEach((level) => { before[level.stage] = level.form; });
  const active = document.activeElement;
  const focusLaw = active && active.dataset ? active.dataset.off : null;
  box.classList.add("live");
  box.innerHTML = renderHierarchy(h, L.context, { d: L.context, morph: L.morph, fromSuffix: L.fromSuffix });
  L.data = h;
  let changed = 0;
  box.querySelectorAll(".rung").forEach((li) => {
    const now = h.levels[Number(li.dataset.rung || 0)];
    if (!now || before[now.stage] == null || before[now.stage] === now.form) return;
    changed += 1;
    li.classList.add("pulse");
    li.addEventListener("animationend", () => li.classList.remove("pulse"), { once: true });
  });
  // A short sentence for screen readers: the visual pulse is not theirs.
  const status = $("#ladder-status");
  if (status) {
    status.textContent = changed
      ? `Ladder updated: ${changed} ${changed === 1 ? "form" : "forms"} changed.`
      : "Ladder updated.";
  }
  wireLadder();
  // Keyboard readers keep their place: the same switch is focused again.
  const again = focusLaw && [...box.querySelectorAll(".lawswitch")].find((b) => b.dataset.off === focusLaw);
  if (again) again.focus({ preventScroll: true });
}

async function updateLadder(showStage) {
  const L = ladderState;
  if (!L) return;
  const box = $("#ladder");
  const id = ++ladderRequest;
  if (box) box.setAttribute("aria-busy", "true");
  const params = { lang: L.lang, w: L.word, off: [...L.off].sort().join(","),
    sense: L.sense > 1 ? L.sense : null };
  if (L.edit) { params.from = L.edit.stage; params.form = L.edit.form; }
  if (L.record) {
    params.from = L.record.stage; params.form = L.record.form; params.recorded = "1";
  }
  if (L.suffix) params.suffix = L.suffix;
  if (L.build) params.build = L.build;
  if (L.path.length) params.path = L.path.join(",");
  if (L.pathway === false) params.pathway = "0";
  let h;
  try { h = await api("/api/hierarchy", params); } catch (e) { h = { error: String(e) }; }
  if (id !== ladderRequest) return;  // a newer edit won
  if (box) box.setAttribute("aria-busy", "false");
  if (!h || h.error) {
    paintLadder(L.data);  // put the switches back where the server has them
    const warn = document.createElement("p");
    warn.className = "notice";
    warn.textContent = `Could not re-derive: ${(h && h.error) || "network error"}. The path is unchanged.`;
    if (box) box.insertBefore(warn, box.firstChild);
    return;
  }
  paintLadder(h);
  syncLadderUrl();
  /* A rung the reader just added is where they are looking: bring it into
     view without touching the rest of the page. */
  if (showStage) {
    const rung = (box && box.querySelector(`.rung[data-stage="${showStage}"]`)) || null;
    if (rung) rung.scrollIntoView({ block: "center", behavior: "smooth" });
  }
}

function startEdit(stage) {
  const L = ladderState;
  const box = $("#ladder");
  if (!L || !box) return;
  const li = [...box.querySelectorAll(".rung")].find((row) => row.dataset.stage === stage);
  const level = (L.data.levels || []).find((row) => row.stage === stage);
  if (!li || !level) return;
  const holder = li.querySelector(".rung-forms");
  holder.innerHTML = `<form class="editform" data-stage="${esc(stage)}">
      <label class="sronly" for="ef-${esc(stage)}">Starting form for ${esc(level.name)}</label>
      <input id="ef-${esc(stage)}" class="editform-input mono" type="text" dir="auto" value="${esc(pf(level.form))}"
        autocomplete="off" spellcheck="false">
      <button class="ghost" type="submit">derive ↓</button>
      <button class="ghost" type="button" data-cancel="1">cancel</button>
    </form>`;
  const input = holder.querySelector("input");
  input.focus();
  input.select();
  holder.querySelector("form").onsubmit = (event) => {
    event.preventDefault();
    const value = input.value.trim();
    if (!value) { input.setAttribute("aria-invalid", "true"); return; }
    L.edit = { stage, form: value };
    updateLadder();
  };
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") { event.preventDefault(); paintLadder(L.data); }
  });
  holder.querySelector("[data-cancel]").onclick = () => paintLadder(L.data);
}

async function storePathway(button) {
  const L = ladderState;
  if (!L || !L.edit) return;
  const label = button.textContent;
  button.disabled = true;
  button.textContent = "storing…";
  const res = await post("/api/pathway", {
    lang: L.lang, word: L.word, from: L.edit.stage, form: L.edit.form, off: [...L.off],
  });
  if (!res || res.error) {
    button.disabled = false;
    button.textContent = label;
    const why = document.createElement("span");
    why.className = "miss";
    why.textContent = ` ${res && res.error ? res.error : "could not store this path"}`;
    button.after(why);
    return;
  }
  await updateLadder();
}

function wireLadder() {
  const L = ladderState;
  const box = $("#ladder");
  if (!L || !box) return;
  box.querySelectorAll(".lawswitch").forEach((b) => {
    b.onclick = () => {
      const key = b.dataset.off;
      if (L.off.has(key)) L.off.delete(key); else L.off.add(key);
      // The reader is now testing the laws themselves; the word's own pathway
      // would put its law straight back, so it steps aside for this view.
      // Exception: a pathway that only *switches a law on* (the animal suffix)
      // keeps the ladder where it is, so the experiment still starts from PIE.
      const pw = (L.data && L.data.pathway) || {};
      if (((pw.disabled) || []).length) L.pathway = false;
      // Immediate feedback: the knob moves now, the forms follow a beat later.
      b.setAttribute("aria-pressed", L.off.has(key) ? "false" : "true");
      const law = b.closest(".law");
      if (law) law.classList.toggle("off", L.off.has(key));
      updateLadder();
    };
  });
  box.querySelectorAll("[data-edit]").forEach((b) => { b.onclick = () => startEdit(b.dataset.edit); });
  /* Carrying the timeline on: append the chosen child's stage and re-derive
     from the last rung. An edit made on a rung the new path does not reach is
     dropped with it. */
  box.querySelectorAll("[data-next]").forEach((b) => {
    b.onclick = () => {
      const stage = b.dataset.next;
      if (!L.path.includes(stage)) L.path.push(stage);
      updateLadder(stage);
    };
  });
  /* Cutting a carried stage drops it and everything below it — and an edit made
     on one of those rungs goes with it. */
  box.querySelectorAll("[data-cut]").forEach((b) => {
    b.onclick = () => {
      const at = L.path.indexOf(b.dataset.cut);
      if (at < 0) return;
      const dropped = L.path.slice(at);
      L.path = L.path.slice(0, at);
      if (L.edit && dropped.includes(L.edit.stage)) L.edit = null;
      updateLadder();
    };
  });
  /* Choosing a suffix on the timeline re-asks for the ladder with that
     morpheme; it starts from the recorded base, so an edited start is dropped. */
  box.querySelectorAll("[data-rung-suffix]").forEach((b) => {
    b.onclick = () => { L.suffix = b.dataset.rungSuffix || ""; L.edit = null; updateLadder(); };
  });
  /* The construction row: the dot beside a word opens it (2026-11-12). */
  box.querySelectorAll(".rdot").forEach((b) => { b.onclick = () => openDraft(b); });
  const unbuild = box.querySelector("[data-unbuild]");
  if (unbuild) unbuild.onclick = () => { L.build = ""; updateLadder(); };
  const reset = box.querySelector("[data-reset]");
  if (reset) reset.onclick = () => { L.off = new Set(); L.pathway = false; updateLadder(); };
  const back = box.querySelector("[data-apply-pathway]");
  if (back) back.onclick = () => { L.off = new Set(); L.pathway = true; updateLadder(); };
  const unedit = box.querySelector("[data-unedit]");
  if (unedit) unedit.onclick = () => { L.edit = null; L.record = null; updateLadder(); };
  const store = box.querySelector("[data-store-pathway]");
  if (store) store.onclick = () => storePathway(store);
  box.querySelectorAll("[data-load-pathway]").forEach((b) => {
    b.onclick = () => {
      const record = (L.data.pathways || []).find((p) => p.id === b.dataset.loadPathway);
      if (!record) return;
      L.edit = { stage: record.start.stage, form: record.start.form };
      L.off = new Set(record.disabled || []);
      updateLadder();
    };
  });
}


const pct = (x) => {
  const p = 100 * (x || 0);
  if (!p) return "0%";
  if (p < 0.01) return `${p.toFixed(4)}%`;
  if (p < 1) return `${p.toFixed(2)}%`;
  return `${p.toFixed(1)}%`;
};

function covBar(parts, total, tip) {
  // A stacked bar: one segment per layer, widths over the whole glossary.
  // The layers are exclusive — a word counted as reconstructed by the laws is
  // not counted again as spelled — so the segments never overlap.
  const sum = parts.reduce((n, p) => n + (p[0] || 0), 0);
  const rest = Math.max(0, (total || 0) - sum);
  const seg = (n, cls) => {
    const w = total ? 100 * (n || 0) / total : 0;
    return w > 0 ? `<i class="${cls}" style="width:${w}%"></i>` : "";
  };
  return `<span class="covbar" data-tip="${esc(tip)}">
    ${seg(parts[0][0], "b-exact")}${seg(parts[1][0], "b-pathway")}
    ${seg(parts[2][0], "b-orth")}${seg(parts[3][0], "b-script")}
    ${seg(rest, "b-rest")}</span>`;
}

function originBar(r) {
  const total = r.glossary || 0;
  const seg = (n, cls) => {
    const w = total ? 100 * (n || 0) / total : 0;
    return w > 0 ? `<i class="${cls}" style="width:${w}%"></i>` : "";
  };
  const unlinked = (r.unlinked || 0) + (r.no_etym || 0);
  return `<span class="covbar origin" data-tip="What the record says: ${[
      `${(r.identified || 0).toLocaleString()} inherited through a modelled stage`,
      `${(r.borrowed || 0).toLocaleString()} recorded as borrowed`,
      `${(r.outside || 0).toLocaleString()} another recorded source outside the chain`,
      `${unlinked.toLocaleString()} no ancestor recorded`].join(" · ")}">
    ${seg(r.identified, "b-inherited")}${seg(r.borrowed, "b-borrowed")}
    ${seg(r.outside, "b-outside")}${seg(unlinked, "b-none")}</span>`;
}

/* Progress on the question the model is actually asked: of the words whose
   record names an ancestor in the family, how many do the laws reproduce
   completely, how many are explained in some layer, how many are the
   glossary's own reconstructions (not yet reproduced), and what is still open.
   Borrowed and non-IE words are not in the denominator; counting them as
   failures would make the bar measure the dictionary, not the model. */
function progressBar(r, tip) {
  const id = r.identified || 0;
  if (!id) return `<span class="sub">no modelled ancestor</span>`;
  const exact = Math.min(r.exact || 0, id);
  const any = Math.min(Math.max(exact, r.explained || 0), id);
  const partial = Math.max(0, any - exact);
  const recon = Math.max(0, Math.min((r.reconstruction || 0) - (r.reconstruction_exact || 0),
                                     id - any));
  const open = Math.max(0, id - any - recon);
  const seg = (n, cls) => n > 0
    ? `<i class="${cls}" style="width:${(100 * n / id).toFixed(4)}%"></i>` : "";
  return `<span class="covbar prog" data-tip="${esc(tip)}">
    ${seg(exact, "b-exact")}${seg(partial, "b-part")}${seg(recon, "b-recon")}${seg(open, "b-rest")}</span>
    <span class="sub"><strong>${pct(exact / id)}</strong> full · ${pct(any / id)} any</span>`;
}

/* The six categories the project defined (2026-11-09), plus the one facet that
   sits beside them.  Labels and colours come from the measurement's own
   `definitions`, so the page cannot drift from the counter; the fallback only
   covers a coverage.json written before the categories existed. */
/* Band keys are snake_case (`non_pie`, `ie_loan`) and the stylesheet's colour
   variables are hyphenated, so both spellings existed in the markup: the
   non-PIE and IE-loan swatches came out unstyled.  One mapping now, used by
   every swatch, bar segment and coloured word (2026-11-09). */
const bandClass = (k) => `cat-${String(k).replace(/_/g, "-")}`;
const bandVar = (k) => `--cat-${String(k).replace(/_/g, "-")}`;

const CAT_FALLBACK = {
  full: { label: "fully explained", colour: "#1b5e20" },
  adjusted: { label: "fully explained, with adjustments", colour: "#8bc34a" },
  partial: { label: "partially explained", colour: "#e0a800" },
  unexplained: { label: "unexplained", colour: "#c62828" },
  non_pie: { label: "non-PIE", colour: "#4a4a4a" },
  unidentified: { label: "unidentified", colour: "#bdbdbd" },
  ie_loan: { label: "loan from another IE language", colour: "#607d8b" },
  built: { label: "built from its own words", colour: "#8d6e63" },
};

function categoryKeys(c, defs) {
  const counts = (c && c.counts) || {};
  const extra = Object.keys(counts).filter((k) => !["unidentified"].includes(k)
    && !["full", "adjusted", "partial", "unexplained", "non_pie"].includes(k));
  return [...["full", "adjusted", "partial", "unexplained", "non_pie"], ...extra]
    .filter((k) => counts[k] != null || (defs || {})[k]);
}

function categoryBar(c, defs) {
  const total = (c && c.total) || 0;
  if (!total) return `<span class="sub">not categorised</span>`;
  const counts = c.counts || {};
  const tip = categoryKeys(c, defs)
    .map((k) => `${(counts[k] || 0).toLocaleString()} ${((defs || {})[k] || {}).label || k}`)
    .join(" · ");
  const segs = categoryKeys(c, defs).map((k) => {
    const n = counts[k] || 0;
    return n ? `<i class="${bandClass(k)}" style="width:${(100 * n / total).toFixed(4)}%"></i>` : "";
  }).join("");
  const explained = (c.explained || 0).toLocaleString();
  return `<span class="covbar covcat" data-tip="${esc(tip)}">${segs}</span>
    <span class="sub"><strong>${explained}</strong> / ${total.toLocaleString()} ·
      ${pct((c.explained_rate || 0) / 100)}</span>`;
}

function categoryLegend(defs, includeExtra) {
  const keys = [...["full", "adjusted", "partial", "unexplained", "non_pie", "unidentified"],
    ...(includeExtra ? ["ie_loan", "built"] : [])];
  return keys.map((k) => {
    const d = (defs || {})[k] || CAT_FALLBACK[k] || {};
    return `<span><i class="${bandClass(k)}"></i>${esc(d.label || k)}</span>`;
  }).join("");
}

function categoryOverview(c, defs) {
  if (!c || !c.total) return `<p class="sub">The categories have not been measured yet
    — run <span class="mono">tools/coverage.py</span>.</p>`;
  const tip = categoryKeys(c, defs)
    .map((k) => `${(c.counts[k] || 0).toLocaleString()} ${((defs || {})[k] || {}).label || k}`)
    .join(" · ");
  return `<div class="covoverall">
    <div class="covoverall-head">
      <span class="covoverall-num">${pct((c.explained_rate || 0) / 100)}</span>
      <span class="sub">of <b>${c.total.toLocaleString()}</b> attested words are fully
        explained (${(c.counts.full || 0).toLocaleString()} exact,
        ${(c.counts.adjusted || 0).toLocaleString()} with an approved adjustment);
        ${(c.counts.partial || 0).toLocaleString()} are partial, the rest are
        unexplained, non-PIE or loans.</span>
    </div>
    <div class="covstack big" data-tip="${esc(tip)}">${categoryBarSegments(c, defs)}</div>
    <p class="covlegend">${categoryLegend(defs, true)}</p>
    <div class="catdefs">
      ${categoryKeys(c, defs).filter((k) => k !== "unidentified").map((k) => {
        const d = (defs || {})[k] || CAT_FALLBACK[k] || {};
        return `<div><i class="${bandClass(k)}"></i><b>${esc(d.label || k)}</b>
          <span class="sub">${esc(d.definition || "")}</span></div>`;
      }).join("")}
    </div>
  </div>`;
}

function categoryBarSegments(c, defs) {
  const total = c.total || 0;
  const counts = c.counts || {};
  return categoryKeys(c, defs).map((k) => {
    const n = counts[k] || 0;
    return n ? `<i class="${bandClass(k)}" style="width:${(100 * n / total).toFixed(4)}%"></i>` : "";
  }).join("");
}

function categoryTable(cov, defs, limit) {
  const rows = Object.entries(cov || {})
    .filter(([, r]) => r.categories && r.categories.total)
    .sort((a, b) => (b[1].categories.explained_rate || 0) - (a[1].categories.explained_rate || 0)
                 || (b[1].categories.total || 0) - (a[1].categories.total || 0))
    .slice(0, limit || 60);
  if (!rows.length) return `<p class="sub">Not measured yet.</p>`;
  return `<table class="covtable cattable"><thead><tr>
      <th>language</th>
      <th title="every attested word in the glossary falls in exactly one band, plus the IE-loan facet">categories</th>
      <th title="fully explained plus fully explained with approved adjustments">explained</th>
      <th title="dark green">full</th><th title="light green">adjusted</th>
      <th title="yellow">partial</th><th title="red">unexplained</th>
      <th title="dark grey">non-PIE</th><th title="blue grey, reported beside the six">IE loan</th>
      <th title="words whose recorded chain contradicts itself (an etymon the literature does not have, a cognate set naming another PIE form, a hedged ancestry, a sense the root does not carry). They keep their band — the form was still reproduced — but they are read by a human before they count.">in review</th>
      <th>stored</th><th title="words the language is estimated to have that this glossary does not hold yet — an estimate, never a count, and never in a bar">not held yet</th></tr></thead><tbody>
    ${rows.map(([lang, r]) => {
      const c = r.categories;
      const n = c.counts || {};
      return `<tr><td>${esc(r.name || lang)} <span class="sub mono">${esc(lang)}</span></td>
      <td>${categoryBar(c, defs)}</td>
      <td><strong>${(c.explained || 0).toLocaleString()}</strong></td>
      <td class="sub">${(n.full || 0).toLocaleString()}</td>
      <td class="sub">${(n.adjusted || 0).toLocaleString()}</td>
      <td class="sub">${(n.partial || 0).toLocaleString()}</td>
      <td class="sub">${(n.unexplained || 0).toLocaleString()}</td>
      <td class="sub">${(n.non_pie || 0).toLocaleString()}</td>
      <td class="sub">${(n.ie_loan || 0).toLocaleString()}</td>
      <td class="sub">${r.review ? `<a href="#/backlog" title="open the review backlog">${r.review.toLocaleString()}</a>` : "—"}</td>
      <td class="sub">${(c.total || 0).toLocaleString()}</td>
      <td class="sub">${r.estimate ? `<span class="est" data-tip="${esc(`${estFigure(r.estimate)} estimated — ${r.estimate.counts} (${r.estimate.basis})${r.estimate.words_note ? `. ${r.estimate.words_note}` : ""}. Source: ${r.estimate.source}${r.estimate.year ? `, ${r.estimate.year}` : ""}. ${r.estimate.quote || ""}`.trim())}">${(r.estimate.unidentified || 0).toLocaleString()}</span>` : "—"}</td></tr>`;
    }).join("")}
  </tbody></table>
  <p class="covlegend">${categoryLegend(defs, true)}
    <span class="sub">· every stored word is in one band; unidentified is an estimate of
    words the glossary does not hold yet, so it is never in the counts</span></p>`;
}

/* What each language is thought to hold, with the sentence behind the number.
   A grey band is somebody's figure for how many words exist, not a measurement
   of this glossary, so the page prints the source beside it rather than asking
   the reader to trust a ratio (2026-11-09). */
/* The figure an estimate row is measured against, as plain text: a dictionary's
   entries are not all words (Dehkhoda heads 180,492 phrases), so a row that
   carries its own `words` count says so (2026-11-10). */
function estFigure(e) {
  if (!e.words) return Number(e.total || 0).toLocaleString();
  return `${Number(e.words).toLocaleString()} words (of ${Number(e.total).toLocaleString()} entries)`;
}

/* The dictionary's grammar labels are abbreviations on purpose — they save
   space in print and cost a reader who does not know them.  This says what the
   tag means in words, token by token, and never guesses: a token outside the
   map is left out rather than glossed (2026-11-10). */
const SAY = {
  "اِ": "noun", "اِخ": "proper name", "ص": "adjective", "ص نسبی": "relative adjective",
  "ص لیاقت": "\"fit to\" adjective", "ق": "adverb", "مص": "infinitive",
  "حامص": "verbal noun", "اِمص": "verbal noun", "نف": "present participle",
  "ن مف": "past participle", "صوت": "interjection", "ع": "Arabic",
  "معرب": "Arabicized", "هزوارش": "huzvarish", "پسوند": "suffix", "پیشوند": "prefix",
  "مصغر": "diminutive", "مرکب": "compound", "ترکیب اضافی": "izafet compound",
};
function sayLabel(label) {
  const tokens = String(label || "").replace(/[،/]/g, " ").split(/\s+/).filter(Boolean);
  const out = [];
  /* The tags are two or three words long ("ص نسبی", "ن مف مرکب"), so the
     longest phrase the map knows is taken first and the rest is read after it;
     an unknown word is skipped, never glossed. */
  for (let i = 0; i < tokens.length;) {
    let took = 1;
    for (let n = Math.min(3, tokens.length - i); n >= 1; n -= 1) {
      const said = SAY[tokens.slice(i, i + n).join(" ")];
      if (said) {
        if (!out.includes(said)) out.push(said);
        took = n;
        break;
      }
    }
    i += took;
  }
  return out.length ? out.join(" · ") : "";
}

/* What the verbatim tag adds beyond the part of speech already printed beside
   it — "compound" for ص مرکب, "Arabic" for ع اِ — so the two badges never say
   the same word twice (2026-11-10). */
const POS_WORD = { noun: "noun", adj: "adjective", verb: "infinitive", adv: "adverb",
  name: "proper name", intj: "interjection", suffix: "suffix", prefix: "prefix" };
function saidExtra(d) {
  const said = sayLabel(d.pos_label);
  if (!said) return "";
  const want = POS_WORD[d.pos] || "";
  return said.split(" · ").filter((x) => x !== want).join(" · ");
}

function estimateTable(cov) {

  const rows = Object.entries(cov)
    .filter(([, r]) => r.estimate)
    .sort((a, b) => (b[1].estimate.band_base || b[1].estimate.total || 0)
                  - (a[1].estimate.band_base || a[1].estimate.total || 0));
  if (!rows.length) return "";
  const basis = { dictionary: "a dictionary's headwords", floor: "a dictionary's core — a floor",
    upper: "includes phrases or inflected forms — an upper bound" };
  const figure = (e) => e.words
    ? `${Number(e.words).toLocaleString()} words <span class="sub">(of ${Number(e.total).toLocaleString()} entries)</span>`
    : Number(e.total || 0).toLocaleString();
  return `<h2>What a language is thought to hold</h2>
    <p class="sub">The grey band is this figure minus the words we store. It is an estimate of a
      different kind of thing from every other number on this page: a dictionary's headword count
      is what one dictionary collected, not how many words a language has. Each row names its
      source and quotes it; a language with no cited figure shows no grey band at all, and a
      language whose glossary already holds more words than its figure shows <b>0</b> — the figure
      is one dictionary's floor, never a ceiling
      (<span class="mono">data/vocabulary_estimates.yaml</span>).</p>
    <div class="card"><table class="covtable"><thead><tr><th>language</th><th>estimated</th>
      <th>stored</th><th>not held yet</th><th>what the figure counts</th><th>source</th></tr></thead><tbody>
    ${rows.map(([lang, r]) => {
      const e = r.estimate;
      const base = e.band_base || e.total || 0;
      const share = base ? Math.min(100, 100 * ((r.categories || {}).total || 0) / base) : 0;
      return `<tr><td>${esc(r.name || lang)} <span class="sub mono">${esc(lang)}</span></td>
      <td>${figure(e)}</td>
      <td class="sub">${((r.categories || {}).total || 0).toLocaleString()}</td>
      <td>${(e.unidentified || 0).toLocaleString()} <span class="sub">· ${share.toFixed(1)}% held</span></td>
      <td class="sub">${esc(e.counts || "")} <span class="badge">${esc(basis[e.basis] || e.basis || "")}</span>
        ${e.words_note ? `<div class="estquote">${esc(e.words_note)}</div>` : ""}
        <div class="estquote">“${esc(e.quote || "")}”</div></td>
      <td class="sub"><a href="${esc(e.url || "")}" target="_blank" rel="noopener">${esc(e.source || "")}</a>${e.year ? `, ${e.year}` : ""}</td></tr>`;
    }).join("")}
    </tbody></table></div>`;
}

function coverageTable(cov, limit) {
  const rows = Object.entries(cov)
    .sort((a, b) => (b[1].explained || 0) - (a[1].explained || 0)
                 || (b[1].glossary || 0) - (a[1].glossary || 0))
    .slice(0, limit || 50);
  if (!rows.length) return `<p class="sub">Not measured yet.</p>`;
  return `<table class="covtable"><thead><tr>
      <th>language</th><th>what the record says</th><th title="share of the words with a recorded ancestor that the laws reproduce completely, and share explained in any layer">progress</th>
      <th>full</th><th>spelled</th><th title="the laws produce another form of the same word and the dictionary cites the stem">stem</th><th title="the ancestor needed no change and the form already equals the record; no rule demonstrated anything, so it is counted apart">unchanged</th><th title="the record writes the same form as a bound morpheme, with a hyphen the laws never write">bound</th><th title="rows the glossary itself marks as reconstructions, and how many of them the laws reproduce">recon. rows</th><th>glossary</th></tr></thead><tbody>
    ${rows.map(([lang, r]) => {
      const total = r.glossary || 0;
      const explained = r.explained || 0;
      const tip = [
        `${(r.identified || 0).toLocaleString()} words have a recorded ancestor in the family: this bar is a share of those`,
        `${(r.exact || 0).toLocaleString()} reconstructed exactly by the sound laws`,
        `${(r.pathway || 0).toLocaleString()} through a stored pathway (a recorded law switched off)`,
        `${(r.orthographic || 0).toLocaleString()} spelled exactly by the writing conventions`,
        `${(r.lemma || 0).toLocaleString()} the same word cited as its stem (the laws give another form)`,
        `${(r.identity || 0).toLocaleString()} unchanged (the ancestor needed no change)`,
        `${(r.bound_form || 0).toLocaleString()} the same form written as a bound morpheme`,
        `${(r.script || 0).toLocaleString()} matched through the language's own script`,
        `${Math.max(0, (r.identified || 0) - explained).toLocaleString()} of the identified still open`].join(" · ");
      return `<tr><td>${esc(r.name || lang)} <span class="sub mono">${esc(lang)}</span></td>
      <td>${originBar(r)}
        <span class="sub">${(r.identified || 0).toLocaleString()} with a modelled ancestor ·
          ${(r.non_ie || 0).toLocaleString()} non-IE ·
          ${(r.borrowed || 0).toLocaleString()} borrowed${r.joined ? ` ·
          ${(r.joined || 0).toLocaleString()} built from pieces` : ""}</span>
        ${(r.gaps || []).length ? `<span class="badge" data-tip="No sound-law file exists for this step, so no word of this language can be derived from PIE yet. A gap in the model, not a failure of the words.">no rule file: ${esc(r.gaps.join(" · "))}</span>` : ""}</td>
      <td>${progressBar(r, tip)}
        <span class="sub">${explained.toLocaleString()} explained${r.identified ? ` of ${(r.identified || 0).toLocaleString()} identified` : ""} · ${pct(total ? explained / total : 0)} of the glossary${r.reconstruction ? ` · record: ${(r.reconstruction || 0).toLocaleString()} reconstructions, ${(r.reconstruction_exact || 0).toLocaleString()} reproduced` : ""}</span></td>
      <td><strong>${(r.exact || 0).toLocaleString()}</strong></td>
      <td class="sub">${(r.orthographic || 0).toLocaleString()}</td>
      <td class="sub">${(r.lemma || 0).toLocaleString()}</td>
      <td class="sub">${(r.identity || 0).toLocaleString()}</td>
      <td class="sub">${(r.bound_form || 0).toLocaleString()}</td>
      <td class="sub">${r.reconstruction ? `${(r.reconstruction_exact || 0).toLocaleString()}/${r.reconstruction.toLocaleString()}` : "—"}</td>
      <td class="sub">${total.toLocaleString()}</td></tr>`;
    }).join("")}
  </tbody></table>
  <p class="covlegend">
    <span><i class="b-exact"></i> reconstructed by the laws</span>
    <span><i class="b-part"></i> explained in another layer</span>
    <span><i class="b-recon"></i> recorded reconstruction, not reproduced</span>
    <span><i class="b-pathway"></i> stored pathway</span>
    <span><i class="b-orth"></i> spelled by convention</span>
    <span><i class="b-lemma"></i> cited as its stem</span>
    <span><i class="b-ident"></i> unchanged (no law needed)</span>
    <span><i class="b-bound"></i> bound form</span>
    <span><i class="b-script"></i> through its script</span>
    <span><i class="b-rest"></i> still open</span>
    <span class="sub">· record: <i class="b-inherited"></i> inherited <i class="b-borrowed"></i> borrowed <i class="b-outside"></i> other source <i class="b-none"></i> none</span>
  </p>`;
}

/* One bar for the whole corpus (2026-11-09, the project asked for a progress
   bar that shows actual progress).  Every layer is a segment of the same bar,
   in the order the page explains them, and the last segment is what is still
   open.  The record's own composition is the thin bar above it: the two answer
   different questions and must not be read as one. */
function coverageOverall(t) {
  if (!t || !t.glossary) return "";
  const total = t.glossary || 0;
  const explained = t.explained || 0;
  const layers = [
    [t.exact, "b-exact", "reconstructed by the sound laws"],
    [t.pathway, "b-pathway", "stored pathway"],
    [t.orthographic, "b-orth", "spelled by convention"],
    [t.lemma, "b-lemma", "cited as its stem"],
    [t.identity, "b-ident", "unchanged (no law needed)"],
    [t.bound_form, "b-bound", "bound form"],
    [t.script, "b-script", "through its script"],
  ].filter(([n]) => n);
  const parts = layers.map(([n, cls]) => [n, cls]);
  parts.push([Math.max(0, total - explained), "b-rest"]);
  const tip = layers.map(([n, , label]) => `${(n || 0).toLocaleString()} ${label}`).join(" · ")
    + ` · ${Math.max(0, total - explained).toLocaleString()} still open`;
  const origin = [
    [t.identified, "b-inherited"], [t.borrowed, "b-borrowed"],
    [t.outside, "b-outside"],
    [Math.max(0, total - (t.identified || 0) - (t.borrowed || 0) - (t.outside || 0)), "b-none"],
  ];
  const id = t.identified || 0;
  const identExact = Math.min(t.exact || 0, id);
  const identAny = Math.min(Math.max(identExact, explained), id);
  const identPartial = Math.max(0, identAny - identExact);
  const identRecon = Math.max(0, Math.min((t.reconstruction || 0) - (t.reconstruction_exact || 0),
                                          id - identAny));
  const identOpen = Math.max(0, id - identAny - identRecon);
  const iseg = (n, cls) => n > 0
    ? `<i class="${cls}" style="width:${(100 * n / id).toFixed(4)}%"></i>` : "";
  return `<div class="covoverall">
    <div class="covoverall-head">
      <span class="covoverall-num">${pct(id ? identExact / id : 0)}</span>
      <span class="sub">of the <b>${id.toLocaleString()}</b> words with a recorded ancestor are
        reconstructed by the laws alone; ${pct(id ? identAny / id : 0)} are explained in some layer
        (${identAny.toLocaleString()}). ${(t.non_ie || 0).toLocaleString()} words have a non-IE origin.</span>
    </div>
    <div class="covstack big prog" data-tip="${esc([
      `${identExact.toLocaleString()} reconstructed exactly`,
      `${identPartial.toLocaleString()} explained in another layer`,
      `${identRecon.toLocaleString()} the record itself marks as a reconstruction, not yet reproduced`,
      `${identOpen.toLocaleString()} still open`].join(" · "))}">
      ${iseg(identExact, "b-exact")}${iseg(identPartial, "b-part")}${iseg(identRecon, "b-recon")}${iseg(identOpen, "b-rest")}</div>
    <div class="covoverall-head whole">
      <span class="covoverall-num small">${pct(total ? explained / total : 0)}</span>
      <span class="sub">of all ${total.toLocaleString()} words are explained
        (<b>${explained.toLocaleString()}</b>), borrowed and non-IE included. The thin bar is the
        record's own account.</span>
    </div>
    <div class="covstack big">${parts.map(([n, cls]) => n
      ? `<i class="${cls}" style="width:${(100 * n / total).toFixed(4)}%"></i>` : "").join("")}</div>
    <div class="covstack thin" data-tip="What the record says: ${(t.identified || 0).toLocaleString()} inherited, ${(t.borrowed || 0).toLocaleString()} borrowed, ${(t.outside || 0).toLocaleString()} other source, ${Math.max(0, total - (t.identified || 0) - (t.borrowed || 0) - (t.outside || 0)).toLocaleString()} none">
      ${origin.map(([n, cls]) => n ? `<i class="${cls}" style="width:${(100 * n / total).toFixed(4)}%"></i>` : "").join("")}</div>
    <p class="sub covoverall-tip" data-tip="${esc(tip)}">Sound laws ${(t.exact || 0).toLocaleString()}
      · spelling ${(t.orthographic || 0).toLocaleString()}
      · unchanged ${(t.identity || 0).toLocaleString()}
      · bound ${(t.bound_form || 0).toLocaleString()}
      · script ${(t.script || 0).toLocaleString()}
      · pathway ${(t.pathway || 0).toLocaleString()}
      · stem ${(t.lemma || 0).toLocaleString()}</p>
    ${(t.joined || 0) ? `<p class="sub covoverall-tip">${(t.joined || 0).toLocaleString()}
      words are recorded formations of two pieces (astronaut, کتابخانه).</p>` : ""}
  </div>`;
}

function coverageStats(t, langs) {
  if (!t) return "";
  const nlangs = Object.values(langs || {}).filter((r) => (r.glossary || 0) > 0).length;
  return `<div class="grid g3">
    <div class="card"><div class="stat">${(t.exact || 0).toLocaleString()}</div>
      <div class="stat-label">reconstructed exactly · ${pct(t.exact_rate)} of ${(t.glossary || 0).toLocaleString()} words</div></div>
    <div class="card"><div class="stat">${(t.identified || 0).toLocaleString()}</div>
      <div class="stat-label">identified · ${pct(t.identified_rate)} · ${(t.explained || 0).toLocaleString()} explained in all layers</div></div>
    <div class="card"><div class="stat">${(t.non_ie || 0).toLocaleString()}</div>
      <div class="stat-label">recorded non-IE origins · ${(t.borrowed || 0).toLocaleString()} borrowed in all</div></div>
    <div class="card"><div class="stat">${(t.reconstruction_exact || 0).toLocaleString()}<span class="sub">/${(t.reconstruction || 0).toLocaleString()}</span></div>
      <div class="stat-label">recorded reconstructions reproduced by the laws · the rest are the corpus's own star-forms, not yet derived</div></div>
  </div>`;
}

/* A word whose record contradicts itself or names an etymology the literature
   does not have is parked, not counted.  The page lists the generated backlog
   (`data/review_backlog.yaml`); a row is a question for a reader, never a
   repaired derivation (2026-11-09). */
const BACKLOG_KINDS = {
  cognate_conflict: "the entry's cognate set names a different PIE form from the ancestry",
  etymon_missing: "the named ancestor is not a headword in that stage's glossary",
  hedged_ancestry: "the ancestry is asserted although the source hedges it",
  sense_mismatch: "the gloss shares no content word with the claimed etymon",
  unverified_match: "a branch row reproduces every sound of a record but its ending, and no registered law explains the difference",
};

/* The band badge sits beside the headword itself (2026-11-09), in the
   title's own size: the reader should not have to read a grey pill under the
   word to learn where the word stands.  The label is the band's name alone —
   "partially explained" needs no gloss, and the phrases that used to follow it
   ("no rule applied", "cited as a stem") said more about the engine than about
   the word.  The reason stays in the tooltip and in the ladder, for the reader
   who wants it.  A borrowed word names its donor instead: "borrowed from
   Arabic", not a bare "non-PIE" (the band is still non-PIE and the dot still
   carries the dark grey); a loan from a sister branch reads "borrowed from
   English" in its own blue grey, which says the same thing the ladder does
   (2026-11-10). */
/* How the word itself is known — attested, recorded or proposed — printed
   beside the band, because "fully explained" answers a different question:
   how much of the word's ancestry the laws reproduce, not whether a text
   wrote the word at all (2026-11-11). */
const ATTEST_BADGE = { attested: "attested", recorded: "literary", proposed: "proposed", "non-existent": "warn" };
function attestBadge(a, extra) {
  if (!a || !a.status) return "";
  const tip = [a.definition, a.reason && a.reason !== a.definition ? a.reason : "", extra || ""]
    .filter(Boolean).join(" ");
  return `<span class="badge attest ${esc(ATTEST_BADGE[a.status] || "")}"
    data-tip="${esc(tip)}" title="${esc(a.label || a.status)}">${esc(a.label || a.status)}</span>`;
}
const attestedWord = (d) => (d && d.attestation && d.attestation.written) || (d && d.word) || "";

/* The same claim, in the title's own voice (2026-11-11): "partially
   explained, recorded (*)" is one sentence about one word, so the record is
   written beside the band in the band's size and italic, in the colour the
   site already gives that record — never in a pill of its own.  The badge is
   still what a list row wears; a title is read, not scanned. */
function attestNote(a, extra) {
  if (!a || !a.status) return "";
  const tip = [a.definition, a.reason && a.reason !== a.definition ? a.reason : "", extra || ""]
    .filter(Boolean).join(" ");
  return `<span class="know ${esc(ATTEST_BADGE[a.status] || "")}"
    data-tip="${esc(tip)}" title="${esc(a.label || a.status)}">${esc(a.label || a.status)}</span>`;
}

/* The title line as a sentence: where the word stands in the model, then how
   it is known.  A hairline dot between them keeps the two claims apart
   without giving either one a box. */
function standing(d) {
  const band = bandBadge(d);
  /* A Middle Persian headword is the record's transcription, not its writing:
     the status tooltip says which layer the form above belongs to. */
  const how = d.attested_how === "transcription"
    ? "The form above is the record's transcription — how the word sounds — rather than its writing."
    : "";
  const know = attestNote(d.attestation, [recordSourceText(d), how].filter(Boolean).join(" "));
  if (!band && !know) return "";
  return `<span class="standing">${band}${band && know ? `<i class="standsep">·</i>` : ""}${know}</span>`;
}

/* The readings line under the title.  It is built as a list and printed only
   when there is something in it: an empty div still keeps its own top margin,
   which left the source icons floating a hand's width under the word
   (2026-11-12). */
function wordMeta(d, readings, matched, lang) {
  const bits = [];
  /* The recorded spellings are writing, not pronunciation: print them in the
     same mono line as a recorded reading, with the writing named on hover
     (admin, 2026-11-13). */
  const spellings = [...new Set((d.spellings || []).filter(Boolean))];
  if (spellings.length) {
    const shown = spellings.slice(0, 3).join(", ") + (spellings.length > 3 ? ", …" : "");
    const tip = `The spellings the record writes${d.script ? ` in ${d.script}` : ""} — transliterations, not pronunciations.`;
    bits.push(`<span class="translit spellings" data-tip="${esc(tip)}"><i>· </i>${esc(shown)}</span>`);
  }
  /* One romanisation per reading, printed once (admin, 2026-11-13): a record
     that gives the same string twice gave one reading, and the header used to
     print «Vr̥kānaʰ · Vr̥kānaʰ».  The alternatives stay in the payload; this is
     the set the reader sees. */
  const uniq = [...new Set(readings.filter(Boolean))];
  if (d.reading && !uniq.includes(d.reading)) uniq.unshift(d.reading);
  if (uniq.length) {
    bits.push(`<span class="translit">${uniq.map((r) => {
      const cls = [r === matched ? "hit" : "",
                   r === d.reading && d.reading_auto ? "auto" : ""].filter(Boolean).join(" ");
      const tip = r === d.reading && d.reading_auto
        ? ` data-tip="${esc(d.reading_note || "No reading recorded — read from the script automatically.")}"`
        : (r === matched ? ' title="matches the sound laws"' : "");
      return `<span${cls ? ` class="${cls}"` : ""}${tip}>${esc(r)}</span>`;
    }).join("<i> · </i>")}</span>`);
  }
  /* What the signs spell, always shown beside a non-Roman script (admin,
     2026-11-13): g-r-g for گرگ, v-r-k-a-n for 𐎺𐎼𐎣𐎠𐎴.  It is the
     transliteration, not a second pronunciation. */
  if (d.signs && !uniq.includes(d.signs)) {
    bits.push(`<span class="translit signs" data-tip="Transliteration — what the signs spell, sign by sign. It is not a pronunciation.">${esc(d.signs)}</span>`);
  }
  /* IPA is optional and belongs here, beside the word, where a reader can see
     it is a phonetic note and not the word's citation form (admin, 2026-11-13). */
  if (d.ipa) bits.push(`<span class="ipa">/${esc(d.ipa.replace(/^\/|\/$/g, ""))}/</span>`);
  /* The status already says how a transcribed word is known; a second note
     under the title saying "transliteration only" said the same thing again
     in a worse way (admin, 2026-11-12). */
  if (d.pos_label) {
    bits.push(`<span class="metaplain" data-tip="${esc(`The dictionary's own label for this word, printed verbatim beside the headword: «${d.pos_label}». It states the part of speech and, where it says so, that the word is a compound (مرکب) or a relative adjective (نسبی). It is a grammar label, not an etymology.`)}">«${esc(d.pos_label)}»</span>${saidExtra(d) ? `<span class="sub said-gloss">${esc(saidExtra(d))}</span>` : ""}`);
  }
  if (d.variants > 1) {
    bits.push(`<a class="metalink" href="#/word/${encodeURIComponent(lang)}/${encodeURIComponent(d.word)}" data-tip="This spelling is ${d.variants} words — open the list">${d.variants} words · see all</a>`);
  }
  return bits.length ? `<div class="wordmeta">${bits.join("")}</div>` : "";
}

/* Where the record was read, as icons under the headword (admin, 2026-11-12):
   the quotation mark used to sit on the word's corner, where it read as a mark
   *on the word* rather than a door to its source, and a second source had no
   place at all.  One icon per source now stands on the rule under the title:
   the W for a Wiktionary entry and a book or a page for the rest; a source
   with no page of its own stays an icon with a tooltip, never a dead link. */
const bookIcon = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"
  fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"
  stroke-linejoin="round"><path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H19v14.5H6a2 2 0 0 0-2 2V4.5Z"/><path d="M19 17.5V21H6a2 2 0 0 1-2-2"/></svg>`;
const pageIcon = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"
  fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"
  stroke-linejoin="round"><path d="M6 3h8l5 5v13H6V3Z"/><path d="M14 3v5h5"/></svg>`;
function sourceRow(d) {
  const rows = recordPages(d);
  const seen = new Set();
  const items = [];
  for (const s of rows) {
    if (!s.url || seen.has(s.url)) continue;
    seen.add(s.url);
    const wikt = s.kind === "wiktionary";
    const name = wikt ? "Wiktionary" : (s.title || "the dictionary").split(",")[0];
    const tip = wikt ? `Open the Wiktionary entry for this word`
      : `${name} — the word's own entry${s.note ? ` · ${s.note}` : ""}`;
    const glyph = wikt ? wiktionaryIcon : (s.kind === "dictionary" ? bookIcon : pageIcon);
    const ext = /^https?:/i.test(s.url) ? ' target="_blank" rel="noopener"' : "";
    items.push(`<a class="srcicon${wikt ? " wikt" : ""}" href="${esc(s.url)}"${ext}
      data-tip="${esc(tip)}" aria-label="${esc(tip)}">${glyph}</a>`);
  }
  if (!items.length) return "";
  return `<div class="sourcerow">${items.join("")}</div>`;
}

/* The language and the years it was in use stand in the left margin
   (2026-11-11), beside the headword itself: a reader learns what the word is
   and when it was spoken in one glance, without a row of pills under it. */
function langRail(d, note) {
  if (!d || !d.lang_name) return "";
  return `<div class="wordrail">
    <span class="raillang" data-tip="${esc(`The language this word is recorded in${d.script ? `; written in ${d.script}` : ""}.`)}">${esc(d.lang_name)}</span>
    ${d.era_label ? `<span class="railera" data-tip="The years this stage of the language was in use, from the language registry — the word's own date, where the record gives one, is in its entry.">${esc(d.era_label)}</span>` : ""}
    ${note ? `<span class="railera">${esc(note)}</span>` : ""}
  </div>`;
}

/* The word's category, in the same margin, level with its meaning: the part
   of speech belongs beside what the word means, not beside how it is spelled
   (2026-11-11). */
function catRail(d) {
  const cat = (d && (d.pos || d.pos_label)) || "";
  if (!cat) return "";
  const said = d.pos_label && d.pos_label !== cat ? ` The dictionary's own label: «${d.pos_label}».` : "";
  /* Persian's meaning block opens with the source tabs, so the category drops
     a line to stay level with the meaning itself. */
  const drop = d.lang === "fa" ? " tabsabove" : "";
  return `<div class="wordrail catrail${drop}">
    <span class="railcat" data-tip="${esc(`The dictionary's category for this word.${said}`)}">${esc(cat)}</span>
  </div>`;
}

function bandBadge(d) {
  const c = d.category;
  if (!c || !c.category) return "";
  const loan = d.loan && d.loan.name
    && (c.category === "non_pie" || c.category === "ie_loan") ? d.loan : null;
  const label = loan ? `borrowed from ${loan.name}` : c.label;
  const tip = [c.definition, c.reason ? `Measured as: ${c.reason}.` : "",
    loan ? `The dictionary records a borrowing from ${loan.name}${loan.form ? ` (${loan.form})` : ""}; ${
      c.category === "non_pie"
        ? "it is still counted outside the Indo-European family."
        : "it is recorded and inside the family, but the laws here do not derive it, so it stays beside the six bands and never counts as green."}` : ""]
    .filter(Boolean).join(" ");
  return `<span class="catlead" data-tip="${esc(tip)}"
    style="--band:${esc(c.colour || "#888")}">${esc(label)}</span>`;
}

/* The review backlog rides the title line too (2026-11-11), smaller and
   pushed to the right: it is a note about the entry, not about the word, so
   it trails the two claims in front of it and never gets a pill of its own. */
function reviewNote(d) {
  if (!(d.backlog || []).length) return "";
  const why = d.backlog.map((b) => `${b.kind}: ${b.detail}`).join(" — ");
  return `<a class="backlognote" href="#/backlog?lang=${encodeURIComponent(d.lang)}"
    data-tip="${esc(why)}" title="${esc(why)}">review backlog · ${d.backlog.length}</a>`;
}

/* Why a word that reproduces exactly is still not dark green: a recorded
   intermediate stage is not the form our laws write there (the project's rule,
   2026-11-09).  The ladder carries the full comparison; this line says which
   stages disagree, so the band is explained where it is shown. */
function stepsNote(d) {
  const rows = d.steps_differ || [];
  if (!rows.length) return "";
  const shown = rows.slice(0, 3);
  const more = rows.length - shown.length;
  const tip = rows.map((r) => `${r.name || r.stage}: recorded ${r.recorded || "—"}, laws ${r.derived || "—"}`).join("\n");
  const items = shown.map((r) => `<span class="stepdiff"><b>${esc(r.name || r.stage)}</b>
    <span class="mono" dir="auto">${esc(r.recorded ? starred(r.recorded, r.stage) : "—")}</span>
    <i>→</i> <span class="mono" dir="auto">${esc(r.derived ? starred(r.derived, r.stage) : "—")}</span></span>`).join('<span class="stepsep">·</span>');
  return `<p class="sub stepsdiff" data-tip="${esc(tip)}">recorded step differs:
    ${items}${more > 0 ? `<span class="stepsep">·</span><span class="stepdiff">+${more} more</span>` : ""}</p>`;
}

/* A word from outside the family is drawn as a ladder, not a bar (2026-11-09): the recorded ancestry runs from the donor language at the top
   down to the word, every rung a stage the record names, and the row between
   two rungs says how the word travelled between them — "borrowed from Arabic
   into Persian" is a step on the same rail as any sound law.  The contact
   window stays a note underneath, never a second timeline. */
function renderLoanLadder(d) {
  const l = d.loan || {};
  const p = l.period || null;
  const window = p ? `${p.from}–${p.to}` : "";
  /* A root is a relation, not an ancestor (the project's rule), so it is not a
     rung; every other recorded row is a stage the word passes through.  The
     record lists the nearest ancestor first, so the ladder reads it backwards. */
  let rows = (d.ancestry || [])
    .filter((a) => a && a.lang && a.rel !== "root")
    .map((a) => ({ ...a }))
    .reverse();
  if (!rows.some((r) => r.lang === l.code) && l.code) {
    rows.unshift({ lang: l.code, lang_name: l.name, form: l.form, rel: l.relation || "borrow",
                   kind: "attested", evidence: "attested", known: false, era_label: "" });
  }
  const name = (r) => r.lang_name || r.lang;
  const readOpts = (r) => ({
    ev: r.evidence, reading: r.reading, signs: r.signs || "",
    show: r.show_reading, auto: !!r.reading_auto, note: r.reading_note,
  });
  const BORROW = new Set(["borrow", "borrowed", "lbor", "slbor", "obor", "ubor"]);
  /* What the record says about the move from one rung to the one below it:
     the relation is the row's own (the nearest ancestor's row describes how
     the word came from it), and it is worded, not printed as a code. */
  const move = (rel, above, below) => {
    if (BORROW.has(rel)) return `borrowed from ${above} into ${below}`;
    if (rel === "derived" || rel === "derive") return `derived in ${below} from ${above}`;
    if (rel === "inherit" || rel === "inh") return `inherited into ${below} from ${above}`;
    if (rel === "calque") return `calqued on ${above} in ${below}`;
    return `continued into ${below} from ${above}`;
  };
  const items = rows.map((r, i) => {
    const below = i + 1 < rows.length ? name(rows[i + 1]) : d.lang_name;
    const isLoan = BORROW.has(r.rel) || r.lang === l.code;
    const era = (r.lang === l.code && window) ? window : (r.era_label || "date unknown");
    const link = wordHref(r.lang, r.form, !!r.known, `${d.lang}/${d.word}`);
    const rung = `<li class="rung" data-stage="${esc(r.lang)}">
      <div class="when">
        <span class="when-name kind-${r.kind === "proto" ? "proto" : "attested"}"
              data-tip="${esc(`${name(r)}${r.branch ? ` · ${r.branch}` : ""}${r.era_label ? ` · in use ${r.era_label}` : ""}`)}"
              tabindex="0">${esc(name(r))}</span>
        <span class="when-era">${esc(era)}</span>
      </div>
      <div class="rail" aria-hidden="true"><i></i></div>
      <div class="rung-body">
        <div class="rung-forms">${form(r.form, r.lang, { ...readOpts(r), href: link,
          hrefTip: r.known ? `Open ${r.form} in ${name(r)}`
                           : `Open this form — nothing in ${name(r)}'s glossary records it` })}</div>
        <div class="rung-rec">${r.gloss
          ? `<span class="sense">${esc(r.pos ? `${r.pos} · ` : "")}“${esc(r.gloss)}”</span>` : ""}<span class="sub">${i === 0
          ? (r.lang === l.code
            ? (r.form ? "the donor form the record names" : "the donor language the record names")
            : (r.form ? "the oldest form the record names" : "the oldest stage the record names"))
          : "the form the record names at this stage"}</span></div>
      </div>
    </li>`;
    const step = `<li class="lawstep" style="--gap:9px">
      <div class="when" aria-hidden="true"></div>
      <div class="rail" aria-hidden="true"><i></i></div>
      <div class="lawbody"><div class="laws"><ul class="lawlist">
        <li class="law${isLoan ? " on" : ""}">
          <span class="lawname">${esc(move(r.rel, name(r), below))}</span>
        </li></ul></div></div>
    </li>`;
    return rung + step;
  }).join("");
  const rec = { w: d.word, evidence: d.evidence, sources: d.sources || [],
                pages: d.pages || [],
                reading: d.reading, signs: d.signs || "",
                show_reading: d.show_reading,
                reading_auto: d.reading_auto, reading_note: d.reading_note };
  const opts = readOpts(rec);
  const word = `<li class="rung here" data-stage="${esc(d.lang)}">
      <div class="when">
        <span class="when-name kind-attested"
              data-tip="${esc(`${d.lang_name} — the language of this glossary`)}">${esc(d.lang_name)}</span>
        <span class="when-era">${esc(d.era_label || "this word")}</span>
        <span class="when-here">this word</span>
      </div>
      <div class="rail" aria-hidden="true"><i></i></div>
      <div class="rung-body">
        <div class="rung-forms">${recordPages(rec).length
          ? recordWord(rec, d.lang, d.lang_name, opts)
          : form(d.word, d.lang, opts)}</div>
        <div class="rung-rec"><span class="sense">${d.pos ? `${esc(d.pos)} · ` : ""}“${esc((d.gloss || [])[0] || "")}”</span></div>
      </div>
    </li>`;
  /* The page is the meaning, the timeline and the sources (2026-11-13): the
     borrowing is the ladder's own step rows, and the contact window one badge.
     No paragraph of background prose under them. */
  return `<div class="ladder-head reveal" style="--i:3">
      <h2>Timeline</h2>
      <div class="ladder-badges"><span class="badge loan">borrowed</span>${
        window ? `<span class="badge" data-tip="The window in which ${esc(l.name || "the donor")} reached ${esc(d.lang_name)} — the contact, never a date for this word.">${esc(window)}</span>` : ""}</div>
    </div>
    <ol class="ladder reveal" style="--i:4">${items}${word}</ol>`;
}

async function viewBacklog(params = new URLSearchParams()) {
  const b = await api("/api/backlog");
  const rows = b.words || [];
  const byKind = (b.counts || {}).by_kind || {};
  const truncated = b.truncated || {};
  let kind = params.get("kind") || "";
  let lang = params.get("lang") || "";
  let shown = 150;
  const langs = [...new Set(rows.map((r) => r.lang))].sort();
  const count = (k) => (byKind[k] || 0).toLocaleString();
  app.innerHTML = `
    <h1>Review backlog</h1>
    <p class="sub">Wiktionary records what an editor wrote, and it is not always
      consistent: an entry may name an etymon that does not exist in the PIE lexicon, or
      one its own cognate set contradicts, or assert a chain its prose hedges. Those
      words are parked here and are not counted as explained until a reader checks the
      source. Persian <b dir="auto">باران</b> is the worked example — ancestry
      <span class="mono">*weh₁r-</span> against the cognate set
      <span class="mono">ine-pro:wódr̥</span>. Generated by
      <span class="mono">tools/backlog.py</span>${b.generated ? ` on ${esc(b.generated)}` : ""};
      the full finding is in <span class="mono">pie.dubious.suspects()</span>, this file is
      a reading list capped per kind.</p>
    <div class="grid g4">
      ${Object.keys(BACKLOG_KINDS).map((k) => `<div class="card">
        <div class="stat">${count(k)}</div>
        <div class="stat-label">${esc(k.replace(/_/g, " "))}${truncated[k] ? ` · ${truncated[k].toLocaleString()} not listed` : ""}</div>
        <p class="sub" style="margin:6px 0 0">${esc(BACKLOG_KINDS[k])}</p></div>`).join("")}
    </div>
    <div class="backlogbar">
      <label>kind
        <select id="bl-kind">
          <option value="">all</option>
          ${Object.keys(BACKLOG_KINDS).map((k) => `<option value="${k}"${k === kind ? " selected" : ""}>${esc(k.replace(/_/g, " "))}</option>`).join("")}
        </select></label>
      <label>language
        <select id="bl-lang"><option value="">all</option>
          ${langs.map((l) => `<option value="${esc(l)}"${l === lang ? " selected" : ""}>${esc(l)}</option>`).join("")}
        </select></label>
      <span class="sub" id="bl-count"></span>
      <button id="bl-more" class="ghost" type="button">show more</button>
    </div>
    <div class="card" id="bl-table"></div>`;
  const table = $("#bl-table");
  const paint = () => {
    const pick = rows.filter((r) => (!kind || r.kind === kind) && (!lang || r.lang === lang));
    $("#bl-count").textContent = `${pick.length.toLocaleString()} listed`;
    $("#bl-more").style.display = pick.length > shown ? "" : "none";
    if (!pick.length) { table.innerHTML = `<p class="sub">No row for this filter.</p>`; return; }
    table.innerHTML = `<table class="covtable"><thead><tr><th>language</th><th>word</th>
      <th>etymon</th><th>kind</th><th>why</th></tr></thead><tbody>
      ${pick.slice(0, shown).map((r) => `<tr>
        <td class="sub mono">${esc(r.lang)}</td>
        <td dir="auto"><a href="#/word/${encodeURIComponent(r.lang)}/${encodeURIComponent(r.word)}">${esc(r.word)}</a></td>
        <td class="mono" dir="auto">${esc(r.etymon || "")}</td>
        <td><span class="badge">${esc(r.kind.replace(/_/g, " "))}</span></td>
        <td class="sub">${esc(r.detail)} <span class="mono">${esc(r.evidence || "")}</span></td>
      </tr>`).join("")}
    </tbody></table>`;
    $("#bl-more").style.display = pick.length > shown ? "" : "none";
  };
  $("#bl-kind").onchange = (e) => { kind = e.target.value; shown = 150; paint(); };
  $("#bl-lang").onchange = (e) => { lang = e.target.value; shown = 150; paint(); };
  $("#bl-more").onclick = () => { shown += 300; paint(); };
  paint();
}

async function viewCoverage() {
  const o = await api("/api/overview");
  const cov = o.coverage || {};
  const t = cov.totals || {};
  const defs = cov.definitions || {};
  const rules = cov.rules_used || [];
  app.innerHTML = `
    <h1>Coverage</h1>
    <p class="sub">A word is <b>explained</b> when cited rules carry an ancestor the record gives it
      to the attested form: the strict column counts a character-for-character match, the notation column
      one that differs only in how the form is written, and the script column a form the word's own signs
      allow and its reading agrees with. A word with no recorded ancestor cannot be explained, and no law is
      invented for it. Every stored word is counted once, and a loan or a formation is
      counted beside the bands, never in green.
      Source: <span class="mono">tools/coverage.py</span>${cov.generated ? `, measured ${esc(cov.generated)}` : ""}${cov.sample ? ` · ${esc(cov.sample)}` : ""}.</p>
    ${cov.stale ? `<p class="sub">measured before the last data change — rerun <span class="mono">tools/coverage.py</span></p>` : ""}
    ${categoryOverview(cov.categories, defs)}
    <h2>By language</h2>
    <p class="sub">The same bands, per language. <b>Not held yet</b> is an estimate of words not
      stored, never in a bar; the last column is the <a href="#/backlog">review backlog</a>.</p>
    <div class="card">${categoryTable(cov.languages || {}, defs, 60)}</div>
    ${estimateTable(cov.languages || {})}
    <details class="layerfold">
      <summary><span class="foldtitle">How the layers add up</span>
        <span class="sub">laws, spelling, script, citation, unchanged forms, stored pathways</span></summary>
      ${coverageOverall(t)}
      ${coverageStats(t, cov.languages)}
      <div class="card">${coverageTable(cov.languages || {}, 100)}</div>
      ${rules.length ? `<h2>Rules used in exact derivations</h2>
        <p class="sub">Successful derivations only. Frequent without an exact match: candidate for review.</p>
        <div class="card"><table><thead><tr><th>rule</th><th>transition</th><th>tier</th><th>applications</th></tr></thead><tbody>
        ${rules.slice(0, 30).map((r) => `<tr><td>${lawCell(r)}</td>
          <td class="sub mono">${esc(r.from)} → ${esc(r.to)}</td><td>${badge(r.tier)}</td>
          <td class="sub">${(r.count || 0).toLocaleString()}</td></tr>`).join("")}
        </tbody></table></div>` : ""}
    </details>
    <p class="sub">Records that contradict themselves sit in the
      <a href="#/backlog">review backlog</a>, never counted against the model.</p>`;
}

const flowMarkup = (forms, chain) => `<div class="flow deriv-flow">
  ${forms.map((f, i) => `
    ${i ? `<span class="flow-arrow" aria-hidden="true">→</span>` : ""}
    <span class="flow-step reveal" style="--i:${i}">
      <span class="flow-form${i === forms.length - 1 ? " end" : ""}">${esc(pf(f))}</span>
      <span class="flow-stage">${esc((chain[i] || {}).name || "")}</span>
    </span>`).join("")}
</div>`;

function renderCognateTable(cog, current, currentWord) {
  const groups = {};
  const branchKey = (b) => b.split(" (")[0];
  (cog.forms || []).forEach((f) => { (groups[branchKey(f.branch || "Other")] ||= []).push(f); });
  const order = Object.keys(groups).sort((a, b) => branchKey(a).localeCompare(branchKey(b)));
  return `<div class="cogtable">
    ${order.map((branch) => {
      const forms = groups[branch];
      return `<div class="coggroup">
        <div class="coghead">
          <span class="branch" style="background:${colorFor(branchKey(branch))}"></span>
          <span>${esc(branchKey(branch))}</span>
          <span class="cogcount">${forms.length}</span>
        </div>
        <table><tbody>
        ${forms.map((f) => {
          const here = current && f.l === current && (!currentWord || f.w === currentWord);
          /* The language name is the link, not the word: a form may be a
             literature reconstruction with no page of its own, and a word is
             something to read and copy, not something to click. */
          const href = f.known
            ? `#/word/${f.l}/${encodeURIComponent(f.w)}`
            : `#/search?q=${encodeURIComponent(f.w)}&lang=${encodeURIComponent(f.l)}`;
          const linkTitle = f.known ? `Open ${f.w} in the word view` : `Search the glossary for ${f.w}`;
          return `<tr class="cogrow${here ? " here" : ""}">
            <td class="coglang"><a href="${href}" title="${esc(linkTitle)}">${esc(f.lang_name || f.l)}</a></td>
            <td class="cogform" dir="auto">${form(f.w, f.l, formOpts(f))}</td>
            <td class="sub coggloss">${esc(f.s || "")}</td>
          </tr>`;
        }).join("")}
        </tbody></table>
      </div>`;
    }).join("")}
  </div>`;
}

/* ------------------------------------------------------------------ */
/* tree                                                                */
/* ------------------------------------------------------------------ */
async function viewTree() {
  const o = await api("/api/overview");
  const byParent = {};
  o.languages.forEach((l) => { (byParent[l.ancestor || "root"] ||= []).push(l); });
  Object.values(byParent).forEach((arr) => arr.sort((a, b) => (a.era?.[0] ?? 0) - (b.era?.[0] ?? 0)));
  const render = (id, depth) => {
    const kids = byParent[id] || [];
    return kids.map((l) => `
      <div style="padding-left:${depth * 22}px">
        <span class="node" onclick="location.hash='#/word/${l.id}/${encodeURIComponent((l.sample||''))}'"
              title="${esc(l.notes)}">
          <span class="branch" style="background:${colorFor(l.branch)}"></span>${esc(l.name)}
          <span class="n-words">${l.words ? l.words.toLocaleString() : ""}</span>
        </span>
      </div>` + render(l.id, depth + 1)).join("");
  };
  app.innerHTML = `
    <h1>Family tree</h1>
    <p class="sub">Nodes marked with a dot colour are attested languages; italic names are reconstructions.
      Counts are glossary entries. Grey without a count means no glossary has been built yet.</p>
    <div class="card tree">${render("root", 0)}</div>
    <h2>Branches</h2>
    <div class="grid g3">
      ${Object.keys(BRANCH_COLORS).map((b) => {
        const ls = o.languages.filter((l) => l.branch.startsWith(b));
        return `<div class="card"><h3><span class="branch" style="background:${colorFor(b)}"></span>${b}</h3>
          <p class="sub" style="margin:0">${ls.length} stages · ${ls.reduce((n, l) => n + l.words, 0).toLocaleString()} entries</p></div>`;
      }).join("")}
    </div>
    <h2>Chain status</h2>
    <table><thead><tr><th>language</th><th>derivation chain</th><th>status</th></tr></thead><tbody>
      ${o.languages.filter((l) => l.chain.length).map((l) => `<tr>
        <td>${esc(l.name)}</td>
        <td class="sub mono">${l.chain.map((c) => esc(langName(o, c))).join(" → ")}</td>
        <td>${l.missing.length ? `<span class="badge warn">${l.missing.length} transition(s) missing</span>` : `<span class="badge established">complete</span>`}</td>
      </tr>`).join("")}
    </tbody></table>`;
}

/* ------------------------------------------------------------------ */
/* rules                                                               */
/* ------------------------------------------------------------------ */
async function viewRules(params) {
  const tier = params.get("tier") || "";
  const from = params.get("from") || "";
  const to = params.get("to") || "";
  const sets = await api("/api/rules", { tier, from, to });
  const keep = [from ? `from=${encodeURIComponent(from)}` : "", to ? `to=${encodeURIComponent(to)}` : ""].filter(Boolean).join("&");
  app.innerHTML = `
    <h1>Rules</h1>
    <p class="sub">Ordered rules per stage transition. Established rules are cited in the literature;
      proposed and custom rules are untested hypotheses and are not used for cited reconstructions.</p>
    <div class="chips">
      ${["", "established", "proposed", "custom"].map((t) => `<button onclick="location.hash='#/rules?tier=${t}${keep ? `&${keep}` : ""}'"
        class="${t === tier ? "primary" : ""}">${t || "all tiers"}</button>`).join("")}
      ${from && to ? `<a class="chip" href="#/rules">every transition</a>` : ""}
    </div>
    ${sets.map((s) => `
      <h2>${esc(s.src_name)} → ${esc(s.dst_name)} <span class="badge">${s.rules.length} rules</span></h2>
      ${s.description ? `<p class="sub">${esc(s.description)}</p>` : ""}
      ${s.rules.map((r) => `
        <details class="rule"><summary>
          <span class="mono" style="color:var(--dim);width:38px">${r.order}</span>
          <a style="flex:1" href="${lawHref(null, r.id, s.src, s.dst)}"
             onclick="event.stopPropagation()" data-tip="Open this law's page">${esc(r.name)}</a>
          ${badge(r.tier)}
        </summary>
        <div class="body">
          <div><span class="pattern">${esc(r.transform ? "transform: " + r.transform : `${r.match} → ${r.replace || "∅"}`)}</span>
            ${r.left || r.right ? `<span class="sub"> / ${esc(r.left || "")}_${esc(r.right || "")}</span>` : ""}</div>
          ${r.description ? `<p>${esc(r.description)}</p>` : ""}
          ${r.notes ? `<p class="sub">${esc(r.notes)}</p>` : ""}
          ${(r.examples || []).length ? `<div class="ex">${r.examples.map((e) => `${esc(e.in)} → ${esc(e.out)}${e.gloss ? "  · " + esc(e.gloss) : ""}`).join("<br>")}</div>` : ""}
          ${(r.references || []).length ? `<p class="sub" style="margin-bottom:0">refs: ${r.references.map(esc).join(", ")}</p>` : ""}
          <p style="margin:12px 0 0"><a class="more" href="${lawHref(null, r.id, s.src, s.dst)}">Open this law’s page →</a></p>
        </div></details>`).join("")}
    `).join("")}`;
}

/* ------------------------------------------------------------------ */
/* one law                                                             */
/* ------------------------------------------------------------------ */
/* Every law named anywhere in the interface opens here (2026-11-08). The page is the law's whole claim in one place: what it changes and
   in which environment, the words the rule file cites for it, the work it
   stands on, and its neighbours in the same transition. */
const TIER_SAYS = {
  established: "Cited in the literature and used for every reconstruction. A word counts as explained only when laws of this tier (and proposed ones where the record requires them) carry it exactly.",
  proposed: "A hypothesis this repo registers with a citation: the change is real but sporadic or not in every grammar. It is never used for a cited reconstruction, and any word page can switch it off.",
  custom: "This project's own working rule, not from the literature. It is reported as such and never counted as established.",
  orthographic: "A writing convention, not a sound change. It belongs to the orthographic layer and is measured apart from the sound laws.",
};
const TIER_LABEL = {
  established: "established", proposed: "proposed", custom: "custom",
  orthographic: "orthographic",
};

async function viewRule(key) {
  const r = await api("/api/rule", { key });
  if (!r || r.error) {
    app.innerHTML = `<p class="empty">No law with that name is registered.</p>`;
    return;
  }
  const t = r.transition;
  const dates = [t.date_start, t.date_end].every((d) => d != null)
    ? `${t.date_start}–${t.date_end}` : (t.date_start != null ? `from ${t.date_start}` : "");
  const env = r.pattern.left || r.pattern.right
    ? `${esc(r.pattern.left == null ? "" : r.pattern.left)}_${esc(r.pattern.right == null ? "" : r.pattern.right)}`
    : "";
  const examples = (r.examples || []).length
    ? `<table><thead><tr><th>in</th><th>out</th><th>word</th></tr></thead><tbody>
        ${r.examples.map((e) => `<tr><td class="mono" dir="auto">${esc(pf(e.in))}</td>
          <td class="mono" dir="auto">${esc(pf(e.out))}</td>
          <td class="sub">${esc(e.gloss || "")}</td></tr>`).join("")}
      </tbody></table>`
    : `<p class="sub">The rule file cites no example for this law yet.</p>`;
  const sources = (r.references || []).length
    ? `<ul class="lawrefs">${r.references.map((ref) => `<li>
        ${ref.url ? `<a href="${esc(ref.url)}" target="_blank" rel="noopener">${esc(ref.title)}</a>`
                  : `<span>${esc(ref.title)}</span>`}
        <span class="sub"> · ${esc(ref.kind || "source")} · <span class="mono">${esc(ref.id)}</span></span></li>`).join("")}
      </ul>`
    : `<p class="sub">No citation is attached to this law — that is a defect, not a style.</p>`;
  const tally = r.applications === 0
    ? `<p class="sub">It applies in <b>no</b> exact derivation measured so far — an earlier step has
         no rule file, or these words miss the record for another reason.
         <a href="#/coverage">Coverage</a> lists them.</p>`
    : r.applications
      ? `<p class="sub">It applies in <b>${r.applications.toLocaleString()}</b> of the derivations that
           reproduce a recorded word exactly (<a href="#/coverage">coverage</a>).</p>`
      : `<p class="sub">How often this law appears in exact derivations is measured by
           <span class="mono">tools/coverage.py</span>; run it to fill this in.</p>`;
  const neighbour = (label, row) => row
    ? `<a class="chip" href="${lawHref(row.key)}">${label} · ${esc(row.name)}</a>` : "";
  const tryForm = ((r.examples || [])[0] || {}).in || "";
  app.innerHTML = `
    <nav class="crumbs reveal"><a href="#/tree">family tree</a><span>/</span>
      <a href="#/rules">sound laws</a><span>/</span><a href="#/rules?from=${encodeURIComponent(t.src)}&to=${encodeURIComponent(t.dst)}">${esc(t.dst_name)}</a></nav>
    <header class="wordhead reveal">
      <div class="wordmain">
        <h1 class="headword">${esc(r.name)}</h1>
        <div class="wordmeta">
          ${badge(r.tier)}
          <span class="badge lang">${esc(t.src_name)} → ${esc(t.dst_name)}</span>
          <span class="badge">${esc(dates || "date unknown")}</span>
          <span class="mono sub">${esc(r.id)}</span>
        </div>
      </div>
    </header>
    <p class="gloss reveal" style="--i:1">${esc(r.description || r.name)}</p>
    <section class="reveal" style="--i:2">
      <h2>The change</h2>
      <div class="card rulepage">
        <p class="pattern big mono" dir="auto">${esc(r.pattern.display)}</p>
        ${env ? `<p class="sub">Environment: <span class="mono">${env}</span>
          — the law applies only between those neighbours (word edge is <span class="mono">#</span>).</p>` : ""}
        ${r.notes ? `<p class="sub">${esc(r.notes)}</p>` : ""}
        <p class="sub">${esc(TIER_SAYS[r.tier] || "")}</p>
      </div>
    </section>
    <section class="reveal" style="--i:3">
      <h2>Words the rule file cites</h2>
      <div class="card">${examples}</div>
    </section>
    <section class="reveal" style="--i:4">
      <h2>Evidence</h2>
      <div class="card">${sources}${tally}</div>
    </section>
    <section class="reveal" style="--i:5">
      <h2>In its transition</h2>
      <p class="sub">${esc(t.name)}${t.description ? ` — ${esc(t.description.trim())}` : ""}
        ${t.rules ? `· ${t.rules} laws in this file.` : ""}</p>
      <div class="chips">
        ${neighbour("previous", r.previous)}${neighbour("next", r.next)}
        <a class="chip" href="#/rules?from=${encodeURIComponent(t.src)}&to=${encodeURIComponent(t.dst)}">all ${esc(t.dst_name)} laws →</a>
        ${tryForm ? `<a class="chip" href="#/lab?form=${encodeURIComponent(tryForm)}&lang=${encodeURIComponent(t.dst)}">try ${esc(tryForm)} in the lab →</a>` : ""}
      </div>
    </section>`;
  wrapTables(app);
  void app.offsetWidth;
  app.classList.add("enter");
}

/* ------------------------------------------------------------------ */
/* derivation lab                                                      */
/* ------------------------------------------------------------------ */
async function viewLab(params) {
  const o = await api("/api/overview");
  const targets = o.languages.filter((l) => l.chain.length);
  app.innerHTML = `
    <h1>Lab</h1>
    <p class="sub">Apply the rule chain to any form. Rules marked proposed or custom can be switched off.</p>
    <div class="searchbox">
      <input id="lform" value="${esc(params.get("form") || "*pṓds")}" placeholder="*pṓds">
      <select id="ltarget">${targets.map((l) => `<option value="${l.id}" ${l.id === (params.get("lang") || "en") ? "selected" : ""}>${esc(l.name)}</option>`).join("")}</select>
      <button class="primary" id="lgo">Derive</button>
    </div>
    <div id="lout"></div>`;
  const run = async () => {
    const form = $("#lform").value;
    const lang = $("#ltarget").value;
    history.replaceState(null, "", `#/lab?form=${encodeURIComponent(form)}&lang=${lang}`);
    const d = await api("/api/derive", { form, lang });
    $("#lout").innerHTML = `
      <div class="card deriv">
        ${flowMarkup(d.forms, d.chain)}
        ${d.skipped.length ? `<p class="notice" style="margin-top:12px">No rules yet for: ${d.skipped.map(esc).join(", ")}</p>` : ""}
      </div>
      <h2>Rule applications</h2>
      ${d.steps.length ? `<table><thead><tr><th>form</th><th>rule</th><th></th></tr></thead><tbody>
        ${d.steps.map((s, i) => `<tr class="reveal step-row" style="--i:${Math.min(i, 16)}"><td class="mono">${esc(pf(s.before))} → ${esc(pf(s.after))}</td>
          <td class="mono">${lawLink(s.rule_id, s.key)}</td><td>${badge(s.tier)}</td></tr>`).join("")}
      </tbody></table>` : `<p class="sub">No rule applied.</p>`}`;
    wrapTables($("#lout"));
    void $("#lout").offsetWidth;
    $("#lout").classList.add("enter");
  };
  $("#lgo").onclick = run;
  $("#lform").addEventListener("keydown", (e) => { if (e.key === "Enter") run(); });
  run();
}

/* ------------------------------------------------------------------ */
/* cognates                                                            */
/* ------------------------------------------------------------------ */
async function viewCognates(params) {
  const q = params.get("q") || "";
  const rows = await api("/api/cognates", { q, limit: 200 });
  app.innerHTML = `
    <h1>Cognate sets</h1>
    <p class="sub">Proto-Indo-European etyma with the reflexes recorded across the family.</p>
    <div class="searchbox"><input id="cq" value="${esc(q)}" placeholder="meaning or etymon, e.g. water"><button class="primary" id="cgo">Filter</button></div>
    <table><thead><tr><th>etymon</th><th>meaning</th><th>pos</th><th>reflexes</th><th>branches</th></tr></thead><tbody>
      ${rows.map((r, i) => `<tr class="click reveal" style="--i:${Math.min(i, 16)}" onclick="location.hash='#/cognate/${encodeURIComponent(r.id)}'">
        <td>${form(r.pie, "ine-pro", { ev: "literary" })}</td><td>${esc(r.gloss)}</td><td class="sub">${esc(r.pos)}</td>
        <td>${r.n}</td><td>${r.branches}</td></tr>`).join("")}
    </tbody></table>`;
  $("#cgo").onclick = () => { location.hash = `#/cognates?q=${encodeURIComponent($("#cq").value)}`; };
  $("#cq").addEventListener("keydown", (e) => { if (e.key === "Enter") $("#cgo").click(); });
}

async function viewCognate(id) {
  const c = await api("/api/cognate", { id });
  if (c.error) { app.innerHTML = `<p class="empty">Unknown cognate set.</p>`; return; }
  app.innerHTML = `
    <p class="sub" style="margin:0"><a href="#/cognates">cognates</a> / ${esc(c.gloss)}</p>
    <div class="wordhead">${form(c.pie, "ine-pro", { ev: "literary" })}<span class="badge">${esc(c.pos)}</span>
      <span style="font-size:18px;color:var(--muted)">${esc(c.gloss)}</span></div>
      ${renderCognateTable(c, null, null)}`;
}

/* ------------------------------------------------------------------ */
/* compare                                                             */
/* ------------------------------------------------------------------ */
async function viewCompare(params) {
  const a = params.get("a") || "";
  const b = params.get("b") || "";
  app.innerHTML = `
    <h1>Compare two words</h1>
    <p class="sub">Do these two words share an etymon? Use <span class="mono">language:word</span> for an exact match,
      or a bare word to search.</p>
    <div class="searchbox">
      <input id="ca" dir="auto" value="${esc(a)}" placeholder="en:foot">
      <input id="cb" dir="auto" value="${esc(b)}" placeholder="fa:پا">
      <button class="primary" id="cgo">Compare</button>
    </div>
    <div id="cout"></div>`;
  const run = async () => {
    const A = $("#ca").value, B = $("#cb").value;
    if (!A || !B) return;
    history.replaceState(null, "", `#/compare?a=${encodeURIComponent(A)}&b=${encodeURIComponent(B)}`);
    const d = await api("/api/compare", { a: A, b: B });
    $("#cout").innerHTML = d.error ? `<p class="empty">${esc(d.error)}</p>` : `
      <div class="card">
        <div class="split">
          ${[d.a, d.b].map((w) => `<div><div class="sub">${esc(w.lang_name)}</div>
            <div style="font-size:26px">${form(w.word, w.lang)}</div>
            <div class="sub">${esc((w.gloss || []).join("; "))}</div></div>`).join("")}
        </div>
        <hr style="border:0;border-top:1px solid var(--line);margin:16px 0">
        ${d.same_etymon
          ? `<p><span class="badge established">connected</span> Both descend from ${form(d.etymon.split(":")[1], "ine-pro")} “${esc(d.etymon_gloss || "")}”.</p>
             <p class="sub"><a href="#/cognate/${encodeURIComponent(d.etymon)}">Open the cognate set →</a></p>`
          : `<p><span class="badge warn">no shared etymon recorded</span> These words are not connected by a recorded Proto-Indo-European source in this dataset (one may be a borrowing, a derivation, or simply outside the current coverage).</p>`}
      </div>`;
    wrapTables($("#cout"));
    void $("#cout").offsetWidth;
    $("#cout").classList.add("enter");
  };
  $("#cgo").onclick = run;
  [$("#ca"), $("#cb")].forEach((el) => el.addEventListener("keydown", (e) => { if (e.key === "Enter") run(); }));
  if (a && b) run();
}

/* ------------------------------------------------------------------ */
/* about                                                               */
/* ------------------------------------------------------------------ */
async function viewAbout() {
  const o = await api("/api/overview");
  app.innerHTML = `
    <h1>About</h1>
    <p class="sub">What this dataset is, what it is not, and how sure we are.</p>
    <div class="grid g2">
      <div class="card"><h3>Model</h3>
        <p>Each stage of each branch is a language node. Sound laws are ordered rewrite rules over
        phonological segments with contexts, not over spelling. A word is explained by two independent
        records: Wiktionary's ancestry chain, and rule application.</p></div>
      <div class="card"><h3>Evidence tiers</h3>
        <p>${badge("established")} from the standard literature and cited.
        ${badge("proposed")} a hypothesis not yet tested against held-out data.
        ${badge("custom")} this project's own working rule, not from the literature.</p></div>
      <div class="card"><h3>Coverage</h3>
        <p>${o.stats.words.toLocaleString()} glossary entries in ${o.languages.filter((l) => l.words).length} languages,
        ${o.stats.rules} rules, ${o.stats.cognate_sets.toLocaleString()} cognate sets. Exact derivation
        rate per language below.</p></div>
      <div class="card"><h3>Known limits</h3>
        <p>Rules output phonological forms, not modern English or German spelling. Coverage is uneven,
        and borrowed vocabulary is recorded as ancestry but not derived by the sound laws.</p></div>
      <div class="card"><h3>Evidence colours</h3>
        <p>Hover any coloured form for what it is: <b>green</b> attested, <b>gold</b> reconstructed in
        the literature (written with *), <b>orange</b> rebuilt here from established laws only,
        <b>red</b> rebuilt on a proposed or custom law, or against a recorded form. Green and gold are
        recorded somewhere; orange and red are ours. Colour is never the only signal.</p></div>
    </div>
    <h2>Exact-derivation coverage</h2>
    <p class="sub">A word counts only when registered rules reproduce it exactly. Full corpus;
      see <span class="mono">docs/COVERAGE.md</span>.</p>
    ${o.coverage && o.coverage.languages ? `<div class="card">${coverageTable(o.coverage.languages, 40)}</div>` : ""}
    <h2>Chain completeness</h2>
    <table><thead><tr><th>language</th><th>chain</th><th>status</th></tr></thead><tbody>
      ${o.languages.filter((l) => l.chain.length).map((l) => `<tr><td>${esc(l.name)}</td>
        <td class="sub mono">${l.chain.map((c) => esc(langName(o, c))).join(" → ")}</td>
        <td>${l.missing.length ? `<span class="badge warn">incomplete</span>` : `<span class="badge established">complete</span>`}</td></tr>`).join("")}
    </tbody></table>`;
}
