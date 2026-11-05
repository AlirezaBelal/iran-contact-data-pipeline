import json
import csv
import io
import subprocess
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from contact_processor import ContactProcessor


class BrowserParityTests(unittest.TestCase):
    def test_browser_sample_matches_authoritative_python_pipeline(self):
        script = "const d=require('./docs/app.js');process.stdout.write(JSON.stringify(d.processContacts(d.sample)))"
        browser = json.loads(subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True))
        records = [
            {"First Name": "کاربر", "Last Name": "نمونه", "Phone 1 - Value": "۰۹۱۲۰۰۰۰۰۰۱", "Phone 2 - Value": "+989120000001"},
            {"First Name": "Synthetic", "Last Name": "International", "Phone 1 - Value": "+989300000002", "Phone 2 - Value": "09120000003"},
            {"First Name": "", "Last Name": "", "Phone 1 - Value": "09880000004", "Phone 2 - Value": ""},
            {"First Name": "Synthetic", "Last Name": "Rejected", "Phone 1 - Value": "invalid", "Phone 2 - Value": "02100000000"},
            {"First Name": "Synthetic", "Last Name": "Shared number", "Phone 1 - Value": "09120000001", "Phone 2 - Value": ""},
        ]
        frame, stats = ContactProcessor.clean_contacts_with_stats(pd.DataFrame(records))
        expected = [
            {"first": row.first_name, "last": row.last_name, "phone": row.selected_phone, "operator": row.mobile_operator}
            for row in frame.itertuples(index=False)
        ]
        browser_output = [
            {key: row[key] for key in ("first", "last", "phone", "operator")}
            for row in browser["selected"]
        ]
        self.assertEqual(browser_output, expected)
        self.assertEqual(browser["stats"]["inputRows"], stats.input_rows)
        self.assertEqual(browser["stats"]["outputRows"], stats.output_rows)
        self.assertEqual(browser["stats"]["invalidPhoneValues"], stats.invalid_phone_values)
        self.assertEqual(browser["stats"]["duplicateNumbersWithinRows"], stats.duplicate_numbers_within_rows)
        self.assertEqual(browser["stats"]["rowsWithMultipleCandidates"], stats.rows_with_multiple_candidates)
        self.assertEqual(browser["stats"]["repeatedSelectedNumbers"], stats.repeated_selected_numbers)
        self.assertEqual(browser["stats"]["rowsWithoutNames"], stats.rows_without_names)

    def test_browser_csv_import_matches_authoritative_python_pipeline(self):
        source = (
            "First Name,Last Name,Phone 1 - Value,Phone 2 - Value,Phone 3 - Value\r\n"
            '"Ali, Jr",Example,02144556677,+98 912 123 4567,09301234567\r\n'
            "Nima,Sample,invalid,09201234567,\r\n"
            "No,Mobile,02188990011,,\r\n"
            "Shared,Number,09121234567,,\r\n"
        )
        script = "const d=require('./docs/app.js');const rows=d.parseCsvContacts(process.argv[1]);process.stdout.write(JSON.stringify(d.processContacts(rows)))"
        browser = json.loads(subprocess.check_output(["node", "-e", script, source], cwd=ROOT, text=True))
        records = list(csv.DictReader(io.StringIO(source)))
        frame, stats = ContactProcessor.clean_contacts_with_stats(pd.DataFrame(records))
        expected = [
            {"first": row.first_name, "last": row.last_name, "phone": row.selected_phone, "operator": row.mobile_operator}
            for row in frame.itertuples(index=False)
        ]
        actual = [
            {key: row[key] for key in ("first", "last", "phone", "operator")}
            for row in browser["selected"]
        ]
        self.assertEqual(actual, expected)
        for browser_key, python_key in (
            ("inputRows", "input_rows"),
            ("outputRows", "output_rows"),
            ("invalidPhoneValues", "invalid_phone_values"),
            ("duplicateNumbersWithinRows", "duplicate_numbers_within_rows"),
            ("rowsWithMultipleCandidates", "rows_with_multiple_candidates"),
            ("repeatedSelectedNumbers", "repeated_selected_numbers"),
            ("rowsWithoutNames", "rows_without_names"),
        ):
            self.assertEqual(browser["stats"][browser_key], getattr(stats, python_key))


if __name__ == "__main__":
    unittest.main()
