"""Static demo contract: no Gradio, server, uploads or live data are needed."""

import contextlib
from html.parser import HTMLParser
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cli import _read_input_file
from contact_processor import ContactProcessor

spec = importlib.util.spec_from_file_location(
    "build_demo", ROOT / "scripts" / "build_demo.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.stack = []
        self.tables = {}
        self.cells = None
        self.buffer = None
        self.identifier = None
        self.metrics = {}
        self.metric_id = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.tags.append((tag, attributes))
        if tag not in {"meta", "link", "br", "hr", "img", "input", "source", "wbr"}:
            self.stack.append(tag)
        if tag == "table":
            self.identifier = attributes["id"]
            self.tables[self.identifier] = []
        if tag == "tr":
            self.cells = []
        if tag in {"th", "td", "dd"}:
            self.buffer = ""
        if tag == "dd":
            self.metric_id = attributes["id"]

    def handle_data(self, data):
        if self.buffer is not None:
            self.buffer += data

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise AssertionError("Unbalanced HTML markup")
        if tag in {"th", "td"}:
            self.cells.append(self.buffer)
            self.buffer = None
        if tag == "tr":
            self.tables[self.identifier].append(self.cells)
        if tag == "dd":
            self.metrics[self.metric_id] = int(self.buffer)
            self.buffer = None


class StaticSpaceTests(unittest.TestCase):
    def setUp(self):
        self.page = (ROOT / "hf-space" / "index.html").read_text(encoding="utf-8")
        self.parsed = PageParser()
        self.parsed.feed(self.page)
        self.assertFalse(self.parsed.stack)

    def test_committed_page_is_deterministic_and_offline(self):
        with patch(
            "socket.socket.connect", side_effect=AssertionError("Network forbidden")
        ):
            self.assertEqual(builder.build_page(), self.page)
            self.assertEqual(builder.build_page(), self.page)
        self.assertTrue(self.page.startswith("<!doctype html>"))
        self.assertIn('<html lang="en">', self.page)
        self.assertIn("width=device-width", self.page)
        self.assertIn("overflow-x:auto", self.page)

    def test_rendered_tables_match_cli_core_output_and_preserve_persian(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic.csv"
            builder.SAMPLE.to_csv(path, index=False, encoding="utf-8-sig")
            expected = ContactProcessor.clean_contacts(_read_input_file(str(path)))
        self.assertEqual(self.parsed.tables["core-output"][0], list(expected.columns))
        self.assertEqual(
            self.parsed.tables["core-output"][1:], expected.values.tolist()
        )
        self.assertEqual(
            self.parsed.tables["synthetic-input"][1:], builder.SAMPLE.values.tolist()
        )
        self.assertIn("کاربر", self.page)
        self.assertIn("۰۹۱۲۰۰۰۰۰۰۱", self.page)
        self.assertIn("synthetic", self.page.lower())

    def test_rendered_metrics_come_from_authoritative_core(self):
        output, stats = ContactProcessor.clean_contacts_with_stats(builder.SAMPLE)
        self.assertEqual(
            self.parsed.metrics,
            {
                "input-rows": stats.input_rows,
                "output-rows": stats.output_rows,
                "invalid-rows": stats.input_rows - stats.output_rows,
                "within-duplicates": stats.duplicate_numbers_within_rows,
                "shared-numbers": stats.repeated_selected_numbers,
            },
        )
        self.assertEqual((len(builder.SAMPLE), len(output)), (5, 4))
        for name, count in stats.selected_operators.items():
            self.assertIn(f"{name}: {count}", self.page)

    def test_no_user_input_processing_or_external_assets(self):
        forbidden = {
            "form",
            "input",
            "textarea",
            "select",
            "button",
            "script",
            "iframe",
            "object",
            "embed",
            "img",
            "link",
        }
        self.assertFalse(any(tag in forbidden for tag, _ in self.parsed.tags))
        for tag, attrs in self.parsed.tags:
            self.assertFalse(any(key.lower().startswith("on") for key in attrs))
            self.assertNotIn("src", attrs)
            self.assertNotIn("action", attrs)
        self.assertIn("default-src 'none'", self.page)
        self.assertIn("form-action 'none'", self.page)
        for filename in ["app.py", "requirements.txt", "package.json"]:
            self.assertFalse((ROOT / "hf-space" / filename).exists())
        self.assertEqual(
            {p.name for p in (ROOT / "hf-space").iterdir() if p.is_file()},
            {"README.md", "index.html"},
        )

    def test_space_metadata_has_static_sdk_at_published_root(self):
        text = (ROOT / "hf-space" / "README.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        metadata = dict(
            line.split(": ", 1) for line in text.split("---", 2)[1].strip().splitlines()
        )
        self.assertEqual(metadata["sdk"], "static")
        self.assertEqual(metadata["app_file"], "index.html")
        self.assertEqual(metadata["license"], "mit")
        self.assertNotIn("app_build_command", metadata)
        self.assertNotIn("python_version", metadata)

    def test_generator_cli_checks_drift_and_html_escapes_values(self):
        with patch.object(sys, "argv", ["build_demo.py", "--check"]):
            self.assertEqual(builder.main(), 0)
        with patch.object(builder, "build_page", return_value="stale"):
            with (
                patch.object(sys, "argv", ["build_demo.py", "--check"]),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                with self.assertRaises(SystemExit) as error:
                    builder.main()
                self.assertEqual(error.exception.code, 1)
        html = builder.table(
            pd.DataFrame([{"Name": "<script>bad</script>&"}]), "test", "Synthetic"
        )
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        original = builder.SAMPLE.copy(deep=True)
        builder.build_page()
        pd.testing.assert_frame_equal(builder.SAMPLE, original)
