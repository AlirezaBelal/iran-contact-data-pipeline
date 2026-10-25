"""Regression tests use synthetic contact records and private temporary directories."""

import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cli import _read_input_file, _write_output_file, main
from contact_processor import ContactProcessor
from exceptions import ContactNormalizationError, FileProcessingError
from utils import normalize_phone_number, detect_mobile_operator

HEADER = "First Name,Last Name,Phone 1 - Value\n"
ROW = "Synthetic,Example,09120000001\n"


class FileSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / "input.csv"
        self.output = self.directory / "output.csv"
        self.source.write_text(HEADER + ROW, encoding="utf-8")

    def invoke(self, *extra, output=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(
            sys,
            "argv",
            ["contact-cleaner", str(self.source), str(output or self.output), *extra],
        ):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    main()
                    code = 0
                except SystemExit as error:
                    code = error.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_input_output_collision_never_changes_source_even_with_overwrite(self):
        original = self.source.read_bytes()
        for flag in [(), ("--overwrite",)]:
            self.assertEqual(self.invoke(*flag, output=self.source)[0], 1)
            self.assertEqual(self.source.read_bytes(), original)

    def test_existing_output_requires_explicit_overwrite(self):
        self.output.write_text("previous private output")
        self.assertEqual(self.invoke()[0], 1)
        self.assertEqual(self.output.read_text(), "previous private output")
        self.assertEqual(self.invoke("--overwrite")[0], 0)
        self.assertEqual(
            list(pd.read_csv(self.output).columns),
            ["first_name", "last_name", "selected_phone", "mobile_operator"],
        )
        self.assertTrue(self.source.read_text().endswith(ROW))
        if os.name == "posix":
            self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)

    @unittest.skipUnless(hasattr(os, "link"), "Hard links unavailable")
    def test_hard_link_source_collision_is_rejected(self):
        os.link(self.source, self.output)
        self.assertEqual(self.invoke("--overwrite")[0], 1)
        self.assertEqual(self.source.read_text(), HEADER + ROW)

    @unittest.skipUnless(os.name == "posix", "POSIX symlink behavior")
    def test_symlink_output_is_rejected(self):
        self.output.symlink_to(self.source)
        self.assertEqual(self.invoke("--overwrite")[0], 1)
        self.assertEqual(self.source.read_text(), HEADER + ROW)

    def test_partial_write_disk_failure_and_interruption_preserve_existing_output(self):
        self.output.write_text("unchanged")

        def partial(frame, stream, **kwargs):
            stream.write("private partial row")
            raise OSError("disk-full private-details")

        with patch.object(pd.DataFrame, "to_csv", partial):
            code, out, error = self.invoke("--overwrite")
        self.assertEqual(code, 1)
        self.assertNotIn("private-details", out + error)
        self.assertEqual(self.output.read_text(), "unchanged")
        self.assertEqual(list(self.directory.glob(".contact-output-*.tmp")), [])
        with patch.object(pd.DataFrame, "to_csv", side_effect=KeyboardInterrupt):
            self.assertEqual(self.invoke("--overwrite")[0], 130)
        self.assertEqual(self.output.read_text(), "unchanged")
        self.assertEqual(list(self.directory.glob(".contact-output-*.tmp")), [])

    def test_sync_and_publish_errors_never_truncate_existing_output(self):
        self.output.write_text("unchanged")
        for operation in ["cli.os.fsync", "cli.os.replace"]:
            with patch(operation, side_effect=OSError("sensitive path")):
                self.assertEqual(self.invoke("--overwrite")[0], 1)
            self.assertEqual(self.output.read_text(), "unchanged")
            self.assertEqual(list(self.directory.glob(".contact-output-*.tmp")), [])

    def test_concurrent_destination_creation_cannot_be_overwritten(self):
        frame = ContactProcessor.clean_contacts(_read_input_file(str(self.source)))
        original_link = os.link

        def competing_writer(src, dst):
            Path(dst).write_text("competing complete output")
            return original_link(src, dst)

        with (
            patch("cli.os.link", side_effect=competing_writer),
            self.assertRaises(FileExistsError),
        ):
            _write_output_file(frame, self.output)
        self.assertEqual(self.output.read_text(), "competing complete output")
        self.assertEqual(list(self.directory.glob(".contact-output-*.tmp")), [])

    def test_unwritable_destination_returns_safe_error(self):
        with patch(
            "cli.tempfile.mkstemp", side_effect=PermissionError("private destination")
        ):
            code, out, error = self.invoke()
        self.assertEqual(code, 1)
        self.assertNotIn("private destination", out + error)
        self.assertFalse(self.output.exists())

    def test_empty_malformed_duplicate_headers_and_encoding_errors(self):
        for text in [
            "",
            HEADER,
            "Wrong,Headers\na,b\n",
            HEADER + "one,two\n",
            HEADER + ROW.rstrip() + ",extra\n",
            HEADER + '"unclosed',
            "First Name,Last Name,Phone 1 - Value,First Name\na,b,c,d\n",
        ]:
            with self.subTest(text=text):
                self.source.write_text(text)
                with self.assertRaises(FileProcessingError):
                    _read_input_file(str(self.source))
                self.assertEqual(self.invoke()[0], 1)
                self.assertFalse(self.output.exists())
        self.source.write_bytes(b"\xff\xfe")
        self.assertEqual(self.invoke()[0], 1)

    def test_quoted_phone_with_newline_is_not_repaired_before_validation(self):
        self.source.write_text(
            "First Name,Last Name,Phone 1 - Value,Phone 2 - Value\n"
            'Synthetic,Example,"09120000001\\n",09300000001\n'.replace(
                "\\n", "\n"
            ),
            encoding="utf-8",
        )
        code, out, error = self.invoke()
        self.assertEqual(code, 0, error)
        cleaned = pd.read_csv(self.output, dtype=str)
        self.assertEqual(cleaned.iloc[0]["selected_phone"], "09300000001")
        self.assertIn("Invalid nonempty phone values: 1", out)
        self.assertNotIn("09120000001", out + error)

    def test_input_limits_fail_before_output_creation(self):
        with patch("cli.MAX_INPUT_BYTES", 2):
            self.assertEqual(self.invoke()[0], 1)
        with patch("cli.MAX_INPUT_ROWS", 1):
            self.source.write_text(HEADER + ROW * 2)
            self.assertEqual(self.invoke()[0], 1)
        self.assertFalse(self.output.exists())

    def test_bom_persian_names_and_blank_names_survive(self):
        self.source.write_text(
            HEADER + ROW.replace("Synthetic,Example", "علی,نمونه") + ",,09120000002\n",
            encoding="utf-8-sig",
        )
        self.assertEqual(self.invoke()[0], 0)
        output = pd.read_csv(self.output, dtype=str, keep_default_na=False)
        self.assertEqual(output.iloc[0]["first_name"], "علی")
        self.assertEqual(output.iloc[1]["first_name"], "")
        self.assertTrue(self.output.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_real_cli_process_exit_codes_and_no_private_path_diagnostics(self):
        completed = subprocess.run(
            [sys.executable, "-m", "cli", str(self.source), str(self.output)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("09120000001", completed.stdout)
        self.assertNotIn("Synthetic", completed.stdout)
        self.assertNotIn(str(self.directory), completed.stdout)
        completed = subprocess.run(
            [sys.executable, "-m", "cli", str(self.source), str(self.output)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 1)


class NormalizationContractTests(unittest.TestCase):
    def test_rejects_ambiguous_plus_forms_without_echoing_values(self):
        for number in [
            "+09120000001",
            "+9120000001",
            "+98+9120000001",
            "++989120000001",
            "0912/private/value",
        ]:
            with (
                self.subTest(number=number),
                self.assertRaises(ContactNormalizationError) as error,
            ):
                normalize_phone_number(number)
            self.assertNotIn(number, str(error.exception))

    def test_control_only_phone_value_is_ignored_not_normalized(self):
        data = pd.DataFrame([{
            "First Name": "Synthetic",
            "Last Name": "Test",
            "Phone 1 - Value": "\n\t",
            "Phone 2 - Value": "09120000002",
        }])
        cleaned, stats = ContactProcessor.clean_contacts_with_stats(data)
        self.assertEqual(cleaned.iloc[0]["selected_phone"], "09120000002")
        self.assertEqual(stats.invalid_phone_values, 0)

    def test_equivalent_forms_are_idempotent_for_synthetic_range(self):
        translation = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
        for suffix in range(100):
            local = f"0912{suffix:07d}"
            for value in [
                local,
                local[1:],
                "98" + local[1:],
                "+98" + local[1:],
                "0098" + local[1:],
                local.translate(translation),
            ]:
                self.assertEqual(normalize_phone_number(value), local)
                self.assertEqual(
                    normalize_phone_number(normalize_phone_number(value)), local
                )

    def test_ambiguous_prefixes_remain_unknown_valid_shapes(self):
        for prefix in ["0931", "0932", "0934", "0988"]:
            value = prefix + "0000001"
            self.assertEqual(normalize_phone_number(value), value)
            self.assertEqual(detect_mobile_operator(value), "Other/Unknown")

    def test_quality_statistics_preserve_shared_contacts_and_tie_order(self):
        data = pd.DataFrame(
            [
                {
                    "First Name": "First",
                    "Phone 1 - Value": "09120000001",
                    "Phone 2 - Value": "+989120000001",
                    "Phone 3 - Value": "09120000002",
                    "Phone 4 - Value": "invalid",
                },
                {"First Name": "Other person", "Phone 1 - Value": "09120000001"},
                {"First Name": None, "Phone 1 - Value": "09880000001"},
                {"First Name": "Rejected", "Phone 1 - Value": "02100000000"},
            ]
        )
        cleaned, stats = ContactProcessor.clean_contacts_with_stats(data)
        self.assertEqual(
            (stats.input_rows, stats.output_rows, stats.invalid_phone_values), (4, 3, 2)
        )
        self.assertEqual(
            (
                stats.duplicate_numbers_within_rows,
                stats.rows_with_multiple_candidates,
                stats.repeated_selected_numbers,
            ),
            (1, 1, 1),
        )
        self.assertEqual(stats.rows_without_names, 1)
        self.assertEqual(stats.selected_operators, {"MCI": 2, "Other/Unknown": 1})
        self.assertEqual(list(cleaned["first_name"]), ["First", "Other person", ""])
        self.assertEqual(cleaned.iloc[0]["selected_phone"], "09120000001")
        self.assertEqual(
            list(cleaned.columns),
            ["first_name", "last_name", "selected_phone", "mobile_operator"],
        )
        self.assertFalse(any(name.startswith("consent") for name in cleaned.columns))

    def test_duplicate_dataframe_columns_are_rejected(self):
        with self.assertRaises(ContactNormalizationError):
            ContactProcessor.clean_contacts(
                pd.DataFrame([["a", "b"]], columns=["First Name", "First Name"])
            )
