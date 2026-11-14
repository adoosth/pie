"""Dependency-free HTTP server for the pie interface."""

from __future__ import annotations

import gzip
import json
import mimetypes
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .. import __version__, data, service

WEB = Path(__file__).resolve().parent / "web"
DATA = data.DATA


def _path(qs: dict, lang: str = "") -> list[str]:
    """``path=pal,fa``: the stages the reader carried the timeline into.

    A link written before 2026-11-12 says ``into=fa`` — the language the old
    *reconstruct into* selector chose.  The selector is gone (a PIE page is a
    ladder now, and its daughter stages are the steps down), so the old address
    is read as the same request: the stages between the page's own language and
    the one it named.
    """
    stages = [stage for stage in qs.get("path", "").split(",") if stage]
    if stages:
        return stages
    into = (qs.get("into") or "").strip()
    if not into:
        return []
    chain = data.derivation_chain(into)
    if lang and lang in chain:
        return chain[chain.index(lang) + 1:]
    return list(chain[1:])


class Handler(BaseHTTPRequestHandler):
    server_version = f"pie/{__version__}"
    # Keep-alive: a page makes a dozen requests (assets, then a word, its
    # cognates, its ladder).  Over HTTP/1.0 each one paid for a new connection.
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # quieter than the default
        pass

    # -- helpers ---------------------------------------------------------
    def _send(self, body: bytes, ctype: str, status: int = 200,
              cache: str = "no-store", etag: str | None = None) -> None:
        """One response path: gzip when the client asks, ETag when it can cache."""
        if etag and self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", cache)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        encoded = body
        if len(body) > 900 and "gzip" in (self.headers.get("Accept-Encoding") or ""):
            encoded = gzip.compress(body, 6)
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        if encoded is not body:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", cache)
        if etag:
            self.send_header("ETag", etag)
        self.end_headers()
        self.wfile.write(encoded)

    def _json(self, payload, status: int = 200) -> None:
        # A measured coverage or overview payload is large and changes only when
        # a run rewrites it, so the browser may keep it for a minute.
        cache = "public, max-age=60" if status == 200 else "no-store"
        self._send(json.dumps(payload, ensure_ascii=False).encode(),
                   "application/json; charset=utf-8", status, cache)

    def _index(self) -> None:
        """The page, with its script and style tagged by the build they belong to.

        A browser that keeps the page for a moment cannot then run yesterday's
        script against today's server: the address of `app.js` names the build,
        so a new build is a new file to fetch.
        """
        html = (WEB / "index.html").read_text(encoding="utf-8")
        # The stamp covers the *sheet* too: a change to style.css alone once
        # kept its old address, so an open tab kept yesterday's fonts while the
        # script said it was current (a ǰ drawn with a floating caron, 2026-11-13).
        newest = max((WEB / name).stat().st_mtime_ns
                     for name in ("app.js", "style.css", "index.html"))
        stamp = f"{newest:x}"
        html = html.replace('/static/app.js"', f'/static/app.js?v={stamp}"')
        html = html.replace('/static/style.css"', f'/static/style.css?v={stamp}"')
        self._send(html.encode("utf-8"), "text/html; charset=utf-8", 200,
                   "no-cache")

    def _file(self, path: Path) -> None:
        # ``/static/`` is a door to one directory and nothing else.  The path
        # arrives from the URL, so ``/static/../../../etc/passwd`` would have
        # been resolved by the operating system and served: the candidate is
        # resolved first and refused unless it is still inside the web root
        # (2026-11-12).  A symlink out of the directory is refused the same way.
        root = WEB.resolve()
        try:
            path = path.resolve()
        except (OSError, RuntimeError):
            self._json({"error": "not found"}, 404)
            return
        if not path.is_relative_to(root) or not path.is_file():
            self._json({"error": "not found"}, 404)
            return
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix in {".js", ".css", ".html"}:
            ctype += "; charset=utf-8"
        st = path.stat()
        etag = f'"{st.st_mtime_ns:x}-{st.st_size:x}"'
        # The page, its script and its style are what a fix lands in: a copy
        # kept for five minutes shows a reader code that no longer exists and
        # a click that does nothing. Revalidate every time — an unchanged file
        # costs one 304.
        cache = ("no-cache" if path.suffix in {".js", ".css", ".html"}
                 else "public, max-age=300, must-revalidate")
        self._send(path.read_bytes(), ctype, 200, cache, etag)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        qs = {k: v[0] for k, v in parse_qs(parsed.query, keep_blank_values=True).items()}
        try:
            if path.startswith("/api/"):
                return self._api(path[5:], qs)
            if path in {"/", "/index.html"}:
                return self._index()
            if path.startswith("/static/"):
                return self._file(WEB / path[len("/static/"):])
            return self._file(WEB / "index.html")
        except Exception:
            traceback.print_exc()
            self._json({"error": "internal error"}, 500)

    def _api(self, endpoint: str, qs: dict) -> None:
        if endpoint == "version":
            # A tab loaded before a fix keeps the old script in memory until it
            # is reloaded; the page asks this once a minute and says so.
            app_js = WEB / "app.js"
            st = app_js.stat()
            # The stamp covers the script *and* the published measurement: a
            # tab that was open over a rerun of tools/coverage.py has to drop
            # the payloads it cached, or the colours it shows are yesterday's
            # (2026-11-12, critic P1-6).
            sheet = (WEB / "style.css").stat()
            parts = [f"{st.st_mtime_ns:x}-{st.st_size:x}",
                     f"{sheet.st_mtime_ns:x}-{sheet.st_size:x}"]
            for name in ("coverage.json", "category_index.json.gz"):
                artifact = DATA / name
                try:
                    parts.append(f"{artifact.stat().st_mtime_ns:x}")
                except OSError:
                    parts.append("-")
            return self._json({"app": "-".join(parts)})
        if endpoint == "overview":
            return self._json(service.overview())
        if endpoint == "search":
            return self._json(service.search(qs.get("q", ""), qs.get("lang") or None,
                                             int(qs.get("limit", 40)),
                                             qs.get("gloss") != "0"))
        if endpoint == "suggest":
            return self._json(service.suggest(qs.get("q", ""), int(qs.get("limit", 8)),
                                              qs.get("lang") or None))
        if endpoint == "glossary":
            # ``q`` narrows the list to words whose spelling contains it; the
            # service has accepted it since 2026-11-10, but the endpoint
            # dropped it, so the interface could not ask (2026-11-12).
            # ``page`` steps through the list: Middle Persian holds 17,000
            # words and the first 400 used to be all a reader could reach
            # (2026-11-13).
            return self._json(service.glossary(qs.get("lang", "ine-pro"),
                                               int(qs.get("limit", 400)),
                                               band=qs.get("band") or None,
                                               q=qs.get("q") or None,
                                               page=int(qs.get("page", 1) or 1)))
        if endpoint == "compose":
            return self._json(service.compose(qs.get("form", ""),
                                              qs.get("suffix") or None,
                                              qs.get("lang") or service.ROOT_LANG))
        if endpoint == "build":
            # The construction row asks for one step at a time (2026-11-12):
            # the composed form and its pieces, with no ladder to fetch.
            row = service.build_at(qs.get("spec") or "", qs.get("base") or "")
            return self._json(row or {"error": "cannot build that"}, 200 if row else 404)
        if endpoint == "words":
            # The stage's own words, for the construction menu.  Cached in the
            # tab per stage; a bound morpheme is a suffix and is not here.
            return self._json({"lang": qs.get("lang") or service.ROOT_LANG,
                               "words": service.headwords(
                                   qs.get("lang") or service.ROOT_LANG,
                                   int(qs.get("limit", 4000)))})
        if endpoint == "word":
            off = [d for d in qs.get("off", "").split(",") if d]
            row = service.word(qs.get("lang", ""), qs.get("w", ""), off,
                               from_stage=qs.get("from") or None,
                               from_form=qs.get("form") or None,
                               from_recorded=qs.get("recorded") == "1",
                               ghost=qs.get("ghost") == "1",
                               via=qs.get("via") or None,
                               pathway=qs.get("pathway") != "0",
                               suffix=qs.get("suffix") or None,
                               path=_path(qs, qs.get("lang", "")),
                               sense=qs.get("sense") or None,
                               build=qs.get("build") or None)
            return self._json(row or {"error": "not found"}, 200 if row else 404)
        if endpoint == "rule":
            row = service.rule_page(qs.get("key") or qs.get("id") or "")
            return self._json(row or {"error": "no such law"}, 200 if row else 404)
        if endpoint == "meanings":
            # One tab per source (2026-11-10): Wiktionary's glosses and,
            # for Persian, Dehkhoda's entry as vajehyab.com prints it.  Fetched
            # on demand and cached; never part of a band or a derivation.
            from .. import meanings
            lang = qs.get("lang", "")
            word = qs.get("w", "")
            row = service.word(lang, word, sense=qs.get("sense") or None)
            if not row:
                return self._json({"error": "not found"}, 404)
            # A spelling with several words opens a landing page; its glosses
            # are per sense, and the Wiktionary tab keeps the numbers the page
            # already uses (1, 2, …) instead of silently showing one meaning.
            if row.get("pick"):
                glosses = [f"({s['sense']}) {'; '.join(s.get('gloss') or [])}"
                           for s in row.get("senses") or [] if s.get("gloss")]
            else:
                glosses = list(row.get("gloss") or [])
            return self._json(meanings.sources(lang, word, glosses,
                                              refresh=qs.get("refresh") == "1"))
        if endpoint == "rules":
            return self._json(service.rules(qs.get("from") or None, qs.get("to") or None,
                                            qs.get("tier") or None))
        if endpoint == "derive":
            disabled = [d for d in qs.get("disable", "").split(",") if d]
            tiers = [t for t in qs.get("tier", "").split(",") if t] or None
            return self._json(service.derive_form(qs.get("form", ""), qs.get("lang", "en"),
                                                  disabled, tiers))
        if endpoint == "cognates":
            return self._json(service.cognates(qs.get("q", ""), int(qs.get("limit", 60))))
        if endpoint == "cognate":
            row = service.cognate(qs.get("id", ""))
            return self._json(row or {"error": "not found"}, 200 if row else 404)
        if endpoint == "rebuild":
            row = service.rebuilds_for_etymon(qs.get("form", ""))
            return self._json(row or {"error": "no form"}, 200 if row else 400)
        if endpoint == "reconstruct":
            row = service.reconstruct(qs.get("form", ""), qs.get("lang", "en"),
                                      qs.get("suffix") or None,
                                      [k for k in (qs.get("off") or "").split(",") if k],
                                      from_stage=qs.get("from") or None,
                                      from_form=qs.get("edit") or None)
            return self._json(row or {"error": "this etymon cannot be reconstructed there"},
                              200 if row else 404)
        if endpoint == "hierarchy":
            off = [d for d in qs.get("off", "").split(",") if d]
            row = service.hierarchy(qs.get("lang", ""), qs.get("w", ""), off,
                                    from_stage=qs.get("from") or None,
                                    from_form=qs.get("form") or None,
                                    pathway=qs.get("pathway") != "0",
                                    suffix=qs.get("suffix") or None,
                                    path=_path(qs, qs.get("lang", "")),
                                    sense=qs.get("sense") or None,
                                    build=qs.get("build") or None)
            return self._json(
                row or {"error": "no ladder for this word and starting stage"},
                200 if row else 404)
        if endpoint == "pathways":
            from .. import pathways

            return self._json({"pathways": pathways.for_word(qs.get("lang", ""),
                                                            qs.get("w", ""))})
        if endpoint == "coverage":
            return self._json(service.coverage())
        if endpoint == "backlog":
            return self._json(service.backlog())
        if endpoint == "compare":
            return self._json(service.compare(qs.get("a", ""), qs.get("b", "")))
        return self._json({"error": "unknown endpoint"}, 404)

    # -- writes ----------------------------------------------------------
    def do_POST(self) -> None:  # noqa: N802
        """Store a pathway the reader validated on the word page.

        The body is re-derived here, so the file only ever receives paths the
        registered rules really produce; nothing is taken on trust.
        """
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 64 * 1024:
                return self._json({"error": "payload too large"}, 413)
            raw = self.rfile.read(length) if length else b"{}"
            payload = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return self._json({"error": "invalid json"}, 400)
        if not isinstance(payload, dict):
            return self._json({"error": "invalid json"}, 400)
        try:
            if path == "/api/pathway":
                off = payload.get("off") or payload.get("disabled") or []
                if isinstance(off, str):
                    off = [d for d in off.split(",") if d]
                result = service.store_pathway(
                    payload.get("lang", ""), payload.get("word", ""),
                    payload.get("from", "") or payload.get("from_stage", ""),
                    payload.get("form", "") or payload.get("from_form", ""),
                    [str(d) for d in off if d],
                    payload.get("note", ""),
                    default=bool(payload.get("default")),
                )
                return self._json(result, 201 if result["created"] else 200)
        except ValueError as exc:
            return self._json({"error": str(exc)}, 400)
        except Exception:
            traceback.print_exc()
            return self._json({"error": "internal error"}, 500)
        return self._json({"error": "unknown endpoint"}, 404)


def _prewarm() -> None:
    """Read the corpus once, in the background, before anyone asks for a page.

    A word page needs its own glossary, the laws, and — for the cognate table —
    a dozen other glossaries.  Paying for those inside the first request made
    that page take seconds after every restart.  Nothing here is a cache the
    reader can see: it is the same work the first request would have done, run
    a moment earlier while the window is still loading.  A failure is silent —
    the request path will do the work itself and report it properly
    (2026-11-12).
    """
    try:
        service.prewarm()
    except Exception:  # noqa: BLE001 - a warm-up must never take the server down
        import traceback
        traceback.print_exc()


def run(host: str = "127.0.0.1", port: int = 8100) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"pie · http://{host}:{port}")
    threading.Thread(target=_prewarm, name="prewarm", daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    run()
