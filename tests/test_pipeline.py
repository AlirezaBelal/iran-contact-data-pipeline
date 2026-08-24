import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from contact_processor import ContactProcessor
from exceptions import ContactNormalizationError
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
        self.assertEqual(detect_mobile_operator("09301234567"), "Irancell")
        self.assertEqual(detect_mobile_operator("09211234567"), "Rightel")


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


if __name__ == "__main__":
    unittest.main()
