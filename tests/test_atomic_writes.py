"""A failed rewrite leaves the published file untouched (2026-11-12)."""
from __future__ import annotations

import gzip
import importlib.util
import json
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def _load_tool(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


build_lexicons_tool = _load_tool("atomic_build_lexicons", "build_lexicons.py")
worklist_tool = _load_tool("atomic_worklist", "worklist.py")
backlog_tool = _load_tool("atomic_backlog", "backlog.py")


def _partial_text_writer(fail_on: int, calls: list[int]):
    real_write_text = Path.write_text

    def flaky(path: Path, data: str, *args, **kwargs):
        calls[0] += 1
        if calls[0] == fail_on:
            encoding = kwargs.get("encoding") or "utf-8"
            with path.open("w", encoding=encoding) as fh:
                fh.write(data[:max(1, len(data) // 2)])
            raise OSError("interrupted")
        return real_write_text(path, data, *args, **kwargs)

    return flaky


class BuildLexiconsAtomicWriteTest(unittest.TestCase):
    def test_a_midstream_failure_keeps_the_previous_lexicon(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            src = root / "src"
            for path in (data / "lexicon", data / "cognate_sets", data / "graph", src):
                path.mkdir(parents=True, exist_ok=True)

            rows = [
                {"word": "one", "pos": "num", "senses": [{"glosses": ["first"]}]},
                {"word": "two", "pos": "num", "senses": [{"glosses": ["second"]}]},
            ]
            (src / "English.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            destination = data / "lexicon" / "en.jsonl.gz"
            original = gzip.compress(b'{"word":"old"}\n', mtime=0)
            destination.write_bytes(original)

            writes = [0]
            real_write = gzip.GzipFile.write

            def flaky_write(stream, payload):
                if payload:
                    writes[0] += 1
                    if writes[0] == 2:
                        raise OSError("interrupted")
                return real_write(stream, payload)

            argv = ["build_lexicons.py", "--src", str(src), "--only", "en",
                    "--min-ancestry", "0"]
            with mock.patch.object(build_lexicons_tool, "DATA", data), \
                    mock.patch.object(build_lexicons_tool, "DUMP_TO_ID", {"English": "en"}), \
                    mock.patch.object(build_lexicons_tool, "merge_supplements", lambda: None), \
                    mock.patch.object(gzip.GzipFile, "write", flaky_write), \
                    mock.patch.object(sys, "argv", argv):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ResourceWarning)
                    with self.assertRaises(OSError):
                        build_lexicons_tool.main()

            self.assertEqual(destination.read_bytes(), original)
            with gzip.open(destination, "rt", encoding="utf-8") as fh:
                self.assertEqual(fh.read(), '{"word":"old"}\n')


class WorklistAtomicWriteTest(unittest.TestCase):
    def test_each_output_survives_a_failed_rewrite(self):
        for fail_on, name in ((1, "WORKLIST.md"), (2, "worklist.json")):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                md_path = root / "WORKLIST.md"
                json_path = root / "worklist.json"
                md_original = b"old worklist\n"
                json_original = b'{"old": true}\n'
                md_path.write_bytes(md_original)
                json_path.write_bytes(json_original)

                calls = [0]
                argv = ["worklist.py", "--write"]
                with mock.patch.object(worklist_tool.wl, "OUT_MD", md_path), \
                        mock.patch.object(worklist_tool.wl, "OUT_JSON", json_path), \
                        mock.patch.object(worklist_tool.wl, "run", lambda limit, langs=None: {}), \
                        mock.patch.object(worklist_tool.wl, "render", lambda report: "new worklist\n"), \
                        mock.patch.object(Path, "write_text", _partial_text_writer(fail_on, calls)), \
                        mock.patch.object(sys, "argv", argv):
                    with self.assertRaises(OSError):
                        worklist_tool.main()

                if fail_on == 1:
                    self.assertEqual(md_path.read_bytes(), md_original)
                else:
                    self.assertEqual(json_path.read_bytes(), json_original)
                    self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")),
                                     {"old": True})


class BacklogAtomicWriteTest(unittest.TestCase):
    def test_each_output_survives_a_failed_rewrite(self):
        report = {"generated": "now", "words": [], "counts": {}, "truncated": {}}
        for fail_on, name in ((1, "review_backlog.yaml"), (2, "REVIEW_BACKLOG.md")):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                yaml_path = root / "review_backlog.yaml"
                doc_path = root / "REVIEW_BACKLOG.md"
                yaml_original = b"old backlog\n"
                doc_original = b"old review\n"
                yaml_path.write_bytes(yaml_original)
                doc_path.write_bytes(doc_original)

                calls = [0]
                with mock.patch.object(backlog_tool, "YAML_PATH", yaml_path), \
                        mock.patch.object(backlog_tool, "DOC_PATH", doc_path), \
                        mock.patch.object(backlog_tool.dubious, "render", lambda report: "new review\n"), \
                        mock.patch.object(Path, "write_text", _partial_text_writer(fail_on, calls)):
                    with self.assertRaises(OSError):
                        backlog_tool.write(report)

                if fail_on == 1:
                    self.assertEqual(yaml_path.read_bytes(), yaml_original)
                else:
                    self.assertEqual(doc_path.read_bytes(), doc_original)


if __name__ == "__main__":
    unittest.main()
