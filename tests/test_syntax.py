"""The tree must parse on the oldest Python the project declares.

``pyproject.toml`` says ``>=3.10``, but a f-string with a replacement field that
runs on to the next line is Python 3.12 only (PEP 701): CPython 3.14 here read
it happily and the Windows reader's 3.11 answered "unterminated string
literal" on `server.py` (2026-11-13).  One rule, checked here: a
single-quoted f-string stays on one line.
"""
import io
import pathlib
import tokenize
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
START = getattr(tokenize, "FSTRING_START", None)
END = getattr(tokenize, "FSTRING_END", None)


def _long_fields(path: pathlib.Path) -> list[tuple[int, str]]:
    """Lines where a plain-quoted f-string starts and does not finish."""
    stack, found = [], []
    try:
        with path.open(encoding="utf-8") as fh:
            tokens = tokenize.generate_tokens(fh.readline)
            for tok in tokens:
                if tok.type == START:
                    stack.append((tok.start[0], tok.string.lstrip("fFrRbB")))
                elif tok.type == END and stack:
                    line, quote = stack.pop()
                    if len(quote) < 3 and tok.start[0] != line:
                        found.append((line, tok.string))
    except (tokenize.TokenError, IndentationError):
        pass
    return found


class TestPortableSyntax(unittest.TestCase):
    def test_no_f_string_field_spans_a_line(self):
        bad = []
        for folder in ("src", "tools", "tests"):
            for path in sorted((ROOT / folder).rglob("*.py")):
                if "__pycache__" in path.parts:
                    continue
                for line, _ in _long_fields(path):
                    bad.append(f"{path.relative_to(ROOT)}:{line}")
        self.assertEqual(bad, [], "f-string fields that need Python 3.12: "
                                  + ", ".join(bad))


if __name__ == "__main__":
    unittest.main()
