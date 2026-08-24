import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cli import _read_input_file
from contact_processor import ContactProcessor
from exceptions import ContactNormalizationError, FileProcessingError
from utils import detect_mobile_operator, normalize_phone_number


class PhoneNormalizationTests(unittest.TestCase):
    def test_normalizes_supported_formats(self):
        self.assertEqual(normalize_phone_number("09121234567"), "09121234567")
        self.assertEqual(normalize_phone_number("9121234567"), "09121234567")
        self.assertEqual(normalize_phone_number("+98 912 123 4567"), "09121234567")
        self.assertEqual(normalize_phone_number("0098-912-123-4567"), "09121234567")

    def test_rejects_landline_and_malformed_values(self):
        for value in ("02188990011", "12345", "", "not-a-number", "0912123456789"):
            with self.subTest(value=value):
                with self.assertRaises(ContactNormalizationError):
                    normalize_phone_number(value)

    def test_operator_classification(self):
        self.assertEqual(detect_mobile_operator("09121234567"), "MCI")
        self.assertEqual(detect_mobile_operator("09901234567"), "MCI")
        self.assertEqual(detect_mobile_operator("09301234567"), "Irancell")
        self.assertEqual(detect_mobile_operator("09011234567"), "Irancell")
        self.assertEqual(detect_mobile_operator("09211234567"), "Rightel")

    def test_unclassified_valid_mobile_is_preserved_as_unknown(self):
        self.assertEqual(detect_mobile_operator("09881234567"), "Other/Unknown")


class ContactProcessorTests(unittest.TestCase):
    def test_filters_invalid_numbers_and_selects_by_priority(self):
        data = pd.DataFrame(
            [
                {
                    "First Name": "Test",
                    "Last Name": "User",
                    "Phone 1 - Value": "02188990011",
                    "Phone 2 - Value": "09301234567",
                    "Phone 3 - Value": "09121234567",
                },
                {
                    "First Name": "No",
                    "Last Name": "Mobile",
                    "Phone 1 - Value": "02144556677",
                },
            ]
        )

        cleaned = ContactProcessor.clean_contacts(data)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["selected_phone"], "09121234567")
        self.assertEqual(cleaned.iloc[0]["mobile_operator"], "MCI")

    def test_suppresses_duplicate_numbers_within_one_contact(self):
        row = pd.Series(
            {
                "Phone 1 - Value": "09121234567",
                "Phone 2 - Value": "+98 912 123 4567",
                "Phone 3 - Value": "09301234567",
            }
        )

        numbers = ContactProcessor._extract_phone_numbers(row)

        self.assertEqual(len(numbers), 2)
        self.assertEqual(numbers[0]["number"], "09121234567")
        self.assertEqual(numbers[1]["number"], "09301234567")

    def test_preserves_persian_names_in_output(self):
        data = pd.DataFrame(
            [
                {
                    "First Name": "علی",
                    "Last Name": "نمونه",
                    "Phone 1 - Value": "09121234567",
                }
            ]
        )

        cleaned = ContactProcessor.clean_contacts(data)

        self.assertEqual(cleaned.iloc[0]["first_name"], "علی")
        self.assertEqual(cleaned.iloc[0]["last_name"], "نمونه")


class CsvInputTests(unittest.TestCase):
    def test_reads_utf8_bom_export(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "contacts.csv"
            input_path.write_text(
                "First Name,Last Name,Phone 1 - Value\nعلی,نمونه,09121234567\n",
                encoding="utf-8-sig",
            )

            loaded = _read_input_file(str(input_path))

            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded.iloc[0]["First Name"], "علی")

    def test_rejects_missing_required_columns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "contacts.csv"
            input_path.write_text(
                "First Name,Phone 1 - Value\nTest,09121234567\n",
                encoding="utf-8",
            )

            with self.assertRaises(FileProcessingError):
                _read_input_file(str(input_path))


if __name__ == "__main__":
    unittest.main()
