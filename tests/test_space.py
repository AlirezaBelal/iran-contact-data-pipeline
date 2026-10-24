"""Source-only Gradio smoke/contract tests. No server or Space is launched."""

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cli import _read_input_file
from contact_processor import ContactProcessor

HAS_GRADIO = importlib.util.find_spec("gradio") is not None
if not HAS_GRADIO and os.environ.get("REQUIRE_SPACE_TESTS") == "true":
    raise RuntimeError("Space dependencies are required for this CI gate")


@unittest.skipUnless(
    HAS_GRADIO, "Install hf-space requirements for the separate Space gate"
)
class SyntheticSpaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "contact_space_demo",
            Path(__file__).resolve().parents[1] / "hf-space" / "app.py",
        )
        cls.app = importlib.util.module_from_spec(spec)
        # Offline import must not use inherited proxy settings or open sockets.
        proxies = {
            name: ""
            for name in (
                "ALL_PROXY",
                "all_proxy",
                "HTTP_PROXY",
                "http_proxy",
                "HTTPS_PROXY",
                "https_proxy",
            )
        }
        with (
            patch.dict(os.environ, proxies),
            patch(
                "socket.socket.connect", side_effect=AssertionError("Network forbidden")
            ),
        ):
            spec.loader.exec_module(cls.app)

    def test_cli_and_demo_share_exact_output_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "synthetic.csv"
            self.app.SAMPLE.to_csv(input_path, index=False, encoding="utf-8-sig")
            expected = ContactProcessor.clean_contacts(
                _read_input_file(str(input_path))
            )
        actual, summary = self.app.run_demo()
        pd.testing.assert_frame_equal(actual, expected)
        self.assertEqual((len(self.app.SAMPLE), len(actual)), (5, 4))
        self.assertIn("repeated selected numbers: 1", summary)
        self.assertEqual(actual.iloc[0]["first_name"], "کاربر")
        self.assertEqual(actual.iloc[2]["mobile_operator"], "Other/Unknown")

    def test_no_contact_upload_editable_inputs_or_file_outputs(self):
        config = self.app.demo.config
        self.assertTrue(all(not dep["inputs"] for dep in config["dependencies"]))
        forbidden = {"file", "uploadbutton", "textbox", "downloadbutton"}
        self.assertFalse(
            any(component["type"] in forbidden for component in config["components"])
        )
        for component in config["components"]:
            if component["type"] == "dataframe":
                self.assertFalse(component["props"]["interactive"])

    def test_repeated_calls_do_not_mutate_fixture_or_write_output_files(self):
        original = self.app.SAMPLE.copy(deep=True)
        first, _ = self.app.run_demo()
        first.iloc[0, 0] = "changed synthetic result"
        second, _ = self.app.run_demo()
        pd.testing.assert_frame_equal(self.app.SAMPLE, original)
        self.assertNotEqual(second.iloc[0, 0], "changed synthetic result")
        self.assertIsInstance(second, pd.DataFrame)
