# Iranian Contact Data Normalization Pipeline

A small Python CLI pipeline for cleaning Iranian contact exports, validating mobile numbers, selecting a preferred number from multiple phone fields, and producing a normalized CSV suitable for downstream workflows.

The broader operational workflow was tested on datasets of approximately **1 million contact records**. This public repository is a **sanitized portfolio snapshot** and intentionally does not reproduce every operational component or dataset used in that environment.

## What it demonstrates

- CSV-based batch data processing with pandas
- Strict Iranian mobile-number normalization
- Rejection of malformed and landline values
- Multi-phone-field extraction per contact
- Configurable operator-priority selection
- Mobile operator classification
- Duplicate-number suppression within each contact
- UTF-8/Persian-friendly CSV output
- CLI packaging and repeatable execution
- Unit tests for normalization and selection rules

## Processing flow

```text
Raw contact CSV
      ↓
Schema validation
      ↓
Inspect up to 4 phone fields
      ↓
Strict mobile normalization
      ↓
Reject invalid / landline values
      ↓
Detect operator prefix group
      ↓
Select preferred valid number
      ↓
Normalized output CSV
```

## Input schema

Required columns:

- `First Name`
- `Last Name`
- `Phone 1 - Value`

Optional additional phone fields:

- `Phone 2 - Value`
- `Phone 3 - Value`
- `Phone 4 - Value`

A small **synthetic** dataset is included in `sample_contacts.csv` for demonstration only.

## Output schema

The pipeline writes:

| Column | Description |
|---|---|
| `first_name` | Cleaned first name |
| `last_name` | Cleaned last name |
| `selected_phone` | Preferred normalized mobile number in `09xxxxxxxxx` format |
| `mobile_operator` | Prefix-based operator group or `Other/Unknown` |

Rows without any valid Iranian mobile number are excluded from the output.

## Operator selection

If a contact contains multiple valid mobile numbers, the current preference order is:

1. MCI
2. Irancell
3. Rightel
4. Other/Unknown valid mobile prefixes

The operator rules in this repository are **explicit prefix heuristics**, not an authoritative or permanent telecom allocation registry. They can be extended in `src/constants.py` as numbering allocations change.

## Project structure

```text
.
├── README.md
├── requirements.txt
├── setup.py
├── sample_contacts.csv          # Synthetic demonstration data
├── src/
│   ├── cli.py                   # CLI entry point and file validation
│   ├── constants.py             # Phone/operator rules and priority
│   ├── contact_processor.py     # Extraction, filtering and selection logic
│   ├── exceptions.py            # Domain-specific exceptions
│   └── utils.py                 # Normalization and utility functions
└── tests/
    └── test_pipeline.py         # Normalization/operator/selection tests
```

## Installation

Requires **Python 3.9+**.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
```

The editable install exposes the `contact-cleaner` command.

## Usage

```bash
contact-cleaner sample_contacts.csv cleaned_contacts.csv
```

Example CLI summary:

```text
Processing contacts...
Cleaned contacts saved to cleaned_contacts.csv
Input rows: 6
Output rows with a valid mobile number: 5
Rows without a valid mobile number: 1
```

The output is written with `utf-8-sig` encoding for practical compatibility with Persian text and common spreadsheet tools.

## Tests

After installing dependencies:

```bash
python -m unittest discover -s tests -v
```

Current tests cover:

- local and international Iranian mobile formats
- malformed/landline rejection
- operator classification
- multi-field selection priority
- dropping rows without a valid mobile number

## Data safety

Real contact datasets may contain personal information. The repository therefore ignores general CSV/Excel datasets through `.gitignore` and tracks only the deliberately synthetic sample file.

For real workflows:

- do not commit source contact exports
- do not publish normalized output files
- review retention and access requirements before processing personal data
- treat phone numbers and names as sensitive operational data

## Current public-snapshot scope

This repository reflects the normalization core and CLI workflow. It should not be read as a full reproduction of the larger operational pipeline.

Not included here:

- production-scale orchestration
- external storage/integration layers
- every operational transformation used on larger datasets
- telecom-grade authoritative number portability/operator lookup

That distinction is intentional: the repository documents what the public code actually implements without overstating missing behavior.

## Portfolio context

For broader project context and other product/data work, see the **[portfolio](https://alirezabelal.github.io/)**.
