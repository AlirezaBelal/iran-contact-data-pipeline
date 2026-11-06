"""Cross-language boundary matrix using synthetic values only."""
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from contact_processor import ContactProcessor
from exceptions import ContactNormalizationError
from utils import normalize_phone_number


def browser(script, data):
    return json.loads(subprocess.check_output(
        ['node', '-e', "const d=require('./docs/app.js');let s='';process.stdin.setEncoding('utf8');process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>{const data=JSON.parse(s);process.stdout.write(JSON.stringify(" + script + "));});"],
        cwd=ROOT, input=json.dumps(data), text=True, encoding='utf-8'))


class ExtendedParityTests(unittest.TestCase):
    def test_normalization_boundary_matrix(self):
        values = ['09120000001', '9120000001', '989120000001', '+989120000001', '00989120000001', '۰۹۱۲۰۰۰۰۰۰۱', '٠٩١٢٠٠٠٠٠٠١', ' 09 (120) 000-001 ', '', ' ', None, '02100000000', '0912text0000001', '++989120000001', '09+120000001', '+00989120000001', '0912000000', '091200000011', '9'*65]
        values += ['09120000001'+suffix for suffix in ['\r', '\n', '\t', '\x00', '\u2028', '\u00a0', '\u200f']]
        actual = browser('data.map(v=>d.normalizePhone(v))', values)
        expected = []
        for value in values:
            try:
                expected.append(normalize_phone_number(value))
            except ContactNormalizationError:
                expected.append(None)
        self.assertEqual(actual, expected)

    def test_selection_metrics_and_export_schema(self):
        records = [
            {'first': 'نمونه', 'last': '', 'phones': ['09300000002', '09200000003', '09120000001', '+989120000001']},
            {'first': 'Shared', 'last': 'Fictional', 'phones': ['09120000001\n', '09120000001']},
            {'first': '', 'last': '', 'phones': ['09320000004']},
            {'first': 'No', 'last': 'Mobile', 'phones': ['bad', '02100000000']},
            {'first': '=1+1', 'last': 'Quoted, "Name"', 'phones': ['09200000003', '09200000004']},
            {'first': 'Order', 'last': 'Unknown', 'phones': ['09880000001', '09880000002']},
        ]
        actual = browser('d.processContacts(data)', records)
        frame, stats = ContactProcessor.clean_contacts_with_stats(pd.DataFrame([
            {'First Name': r['first'], 'Last Name': r['last'], **{f'Phone {i+1} - Value': v for i,v in enumerate(r['phones'])}}
            for r in records]))
        selected = [{ 'first': r.first_name, 'last': r.last_name, 'phone': r.selected_phone, 'operator': r.mobile_operator } for r in frame.itertuples(index=False)]
        self.assertEqual([{k:r[k] for k in ('first','last','phone','operator')} for r in actual['selected']], selected)
        for js, py in [('inputRows','input_rows'),('outputRows','output_rows'),('invalidPhoneValues','invalid_phone_values'),('duplicateNumbersWithinRows','duplicate_numbers_within_rows'),('rowsWithMultipleCandidates','rows_with_multiple_candidates'),('repeatedSelectedNumbers','repeated_selected_numbers'),('rowsWithoutNames','rows_without_names'),('selectedOperators','selected_operators')]:
            self.assertEqual(actual['stats'][js], getattr(stats,py))
        exported = browser('d.buildOutputCsv(d.processContacts(data).selected)', records)
        rows = list(csv.DictReader(io.StringIO(exported.lstrip('\ufeff'))))
        self.assertEqual(list(rows[0]), list(frame.columns))
        # Deliberate output policy difference: browser protects formula-like names;
        # Python preserves them. Core names and all normalized phone values match.
        self.assertEqual(rows[3]['first_name'], "'=1+1")
        self.assertEqual(frame.iloc[3]['first_name'], '=1+1')
        self.assertEqual([r['selected_phone'] for r in rows], list(frame.selected_phone))
