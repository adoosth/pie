"""UTF-8 guarantees for text I/O and console output.

Windows still defaults to the legacy cp1252 code page ("charmap") whenever an
encoding is not named explicitly. Every file in this project carries IPA, and
the UTF-8 continuation bytes used by the diacritics (0x8d in "ō", 0x81 in "ā")
are undefined in cp1252, so a single unnamed ``open()`` aborts a whole run.

File I/O therefore always names UTF-8. This module covers the other half: the
process's own ``stdout``/``stderr``, which Python opens with the console code
page when output is redirected to a file or a pipe.
"""

from __future__ import annotations

import sys
from typing import IO


def _upgrade(stream: IO[str] | None) -> None:
    if stream is None:
        return
    encoding = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
    if encoding in {"utf8", "utf8sig"}:
        return
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError, OSError):
        pass


def enable_utf8_stdio() -> None:
    """Switch stdio to UTF-8 when the platform picked a legacy code page."""
    _upgrade(sys.stdout)
    _upgrade(sys.stderr)
