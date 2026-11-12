#!/usr/bin/env python3
"""Convert a PDF/DOCX to Markdown with the SAIA Docling service.

    export SAIA_API_KEY=...
    python tools/docling_convert.py book.pdf -o book.md

Endpoint: https://chat-ai.academiccloud.de/v1/documents/convert/file
(docling-serve; see https://docs.hpc.gwdg.de/services/ai-services/saia/)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ENDPOINT = "https://chat-ai.academiccloud.de/v1/documents/convert/file"


def convert(path: Path, api_key: str, timeout: int = 3600, backend: str | None = None,
            images: str = "placeholder", ocr: bool = True) -> dict:
    boundary = "----pie" + uuid.uuid4().hex
    fields = {"image_export_mode": images, "do_ocr": str(ocr).lower()}
    if backend:
        fields["pdf_backend"] = backend
    body = b""
    for k, v in fields.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; "
             f"filename=\"{path.name}\"\r\nContent-Type: application/pdf\r\n\r\n").encode()
    body += path.read_bytes() + b"\r\n" + f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("-o", "--out")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--backend")
    ap.add_argument("--json", action="store_true", help="keep the full JSON response")
    args = ap.parse_args()
    key = os.environ.get("SAIA_API_KEY", "").strip()
    if not key:
        print("SAIA_API_KEY is not set", file=sys.stderr)
        return 2
    src = Path(args.source)
    started = time.time()
    try:
        data = convert(src, key, args.timeout, args.backend)
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}: {exc.read()[:400].decode(errors='replace')}", file=sys.stderr)
        return 1
    md = (data.get("document") or {}).get("md_content") or ""
    out = Path(args.out or (src.with_suffix(".md")))
    out.write_text(md, encoding="utf-8")
    if args.json:
        out.with_suffix(".json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    conf = data.get("confidence") or {}
    print(f"{src.name} → {out}  {len(md):,} chars in {time.time()-started:.0f}s  "
          f"(status {data.get('status')}, mean_score {conf.get('mean_score')})")
    return 0 if md else 1


if __name__ == "__main__":
    raise SystemExit(main())
