# Iranian Contact Data Normalization Pipeline

[![CI](https://github.com/AlirezaBelal/iran-contact-data-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/AlirezaBelal/iran-contact-data-pipeline/actions/workflows/ci.yml)

> A Python CLI pipeline for turning inconsistent Iranian contact exports into a normalized, downstream-ready contact dataset.

This project addresses a practical data-operations problem:

**How can large contact exports with inconsistent phone formats, multiple phone fields, malformed values, and mixed operator prefixes be transformed into a predictable dataset for downstream workflows?**

The broader operational workflow was tested on datasets of approximately **1 million contact records**. This public repository is a **sanitized portfolio snapshot** of the normalization core; it intentionally does not reproduce every operational component, integration, or dataset used in that environment.

## Product / data context

Raw contact exports are rarely analysis- or automation-ready. Common issues include local and international phone-number representations, multiple phone fields, duplicate representations, landlines mixed with mobile numbers, malformed values, inconsistent operator prefixes, Persian text, and spreadsheet-generated UTF-8 BOM files.

The pipeline turns those inputs into a small, explicit output contract:

**one contact → one selected normalized mobile number → one operator label**

## Processing flow

```text
Raw contact CSV
      ↓
Schema validation
      ↓
Inspect up to 4 phone fields
      ↓
Normalize supported phone representations
      ↓
Reject malformed / non-mobile-shaped values
      ↓
Suppress duplicate numbers within the contact
      ↓
Classify configured operator-prefix groups
      ↓
Apply operator preference
      ↓
Normalized output CSV
```

## Core capabilities

- **CSV batch processing** with pandas
- **Iranian mobile normalization** to `09xxxxxxxxx`
- **Local / +98 / 0098 input handling**
- **Malformed and landline rejection**
- **Multi-phone-field extraction** from up to four fields
- **Duplicate suppression within each contact**
- **Explicit operator-priority selection**
- **Prefix-based MCI / Irancell / Rightel classification**
- **Persian text preservation**
- **UTF-8 and UTF-8-BOM input compatibility**
- **UTF-8-SIG output** for spreadsheet compatibility
- **Installable CLI command**
- **Privacy-safe validation errors** that do not echo raw phone values
- **Automated tests, dependency auditing, package validation, and GitHub Actions CI**

## Complementary downstream workflow

A natural downstream use case for the normalized output is **[batch-sms-campaign-automation](https://github.com/AlirezaBelal/batch-sms-campaign-automation)**.

```text
Raw contact exports
      ↓
Iran Contact Data Pipeline
normalize · validate · select preferred mobile
      ↓
Downstream-ready contact dataset
      ↓
Batch SMS Campaign Automation
personalize · simulate · submit · observe
```

The repositories are intentionally independent. This relationship documents a natural upstream/downstream workflow rather than a runtime dependency.

## Input schema

Required columns:

- `First Name`
- `Last Name`
- `Phone 1 - Value`

Optional phone fields:

- `Phone 2 - Value`
- `Phone 3 - Value`
- `Phone 4 - Value`

A deliberately synthetic example is included at:

```text
examples/contacts.example.csv
```

Real contact exports should not be committed to the repository.

## Output contract

| Column | Description |
|---|---|
| `first_name` | Cleaned first name |
| `last_name` | Cleaned last name |
| `selected_phone` | Selected normalized number in `09xxxxxxxxx` format |
| `mobile_operator` | Configured prefix group or `Other/Unknown` |

Rows without a usable normalized mobile number are excluded from the output.

## Number and operator semantics

Normalization is intentionally conservative about **shape**: supported inputs are converted into the local `09xxxxxxxxx` representation, while malformed values and landline-shaped values are rejected.

Operator classification is a separate heuristic layer. Current preference order when multiple valid numbers exist:

1. MCI
2. Irancell
3. Rightel
4. Other/Unknown

> Prefix rules are not an authoritative telecom allocation or number-portability registry. They are transparent heuristics used by this public snapshot and can be updated in `src/constants.py` as requirements change.

## Repository structure

```text
.
├── README.md
├── SECURITY.md
├── LICENSE
├── requirements.txt
├── pyproject.toml               # Standard Python build backend
├── setup.py                     # Package and console-script metadata
├── examples/
│   └── contacts.example.csv     # Synthetic demonstration dataset
├── src/
│   ├── cli.py                   # CLI, CSV loading and schema validation
│   ├── constants.py             # Format/operator rules and priority
│   ├── contact_processor.py     # Extraction, filtering and selection logic
│   ├── exceptions.py            # Domain-specific exceptions
│   └── utils.py                 # Normalization and utility functions
├── tests/
│   └── test_pipeline.py
└── .github/
    ├── dependabot.yml
    └── workflows/
        └── ci.yml
```

## Quick start

Requires **Python 3.9+**.

```bash
git clone https://github.com/AlirezaBelal/iran-contact-data-pipeline.git
cd iran-contact-data-pipeline
python -m venv .venv
```

Linux / macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\activate
```

Install the CLI:

```bash
python -m pip install -e .
```

Run the synthetic example:

```bash
contact-cleaner examples/contacts.example.csv cleaned_contacts.csv
```

Expected summary shape:

```text
Processing contacts...
Cleaned contacts saved to cleaned_contacts.csv
Input rows: 6
Output rows with a valid mobile number: 5
Rows without a valid mobile number: 1
```

The generated file is ignored by Git.

## Example transformation

Supported representations such as:

```text
0912 123 4567
+98 912 123 4567
0098-912-123-4567
9121234567
```

normalize to:

```text
09121234567
```

Malformed values and landlines such as `021...` are rejected rather than converted into plausible-looking mobile numbers.

## Tests

Run locally:

```bash
python -m unittest discover -s tests -v
```

The suite covers normalization formats, malformed/landline rejection, privacy-safe validation errors, operator classification, operator-priority selection, duplicate suppression, Persian name preservation, UTF-8-BOM compatibility, schema validation, and dropping contacts without a usable mobile number.

## Continuous Integration

GitHub Actions runs on pushes and pull requests to `master`.

CI verifies the application on **Python 3.9 through 3.14** by checking:

- editable package installation
- dependency consistency with `pip check`
- source compilation / syntax
- unit tests
- the installed `contact-cleaner` command against the synthetic example
- output schema, row count, and normalized-number shape
- runtime dependency vulnerabilities with `pip-audit`
- Python distribution buildability and metadata with `build` + `twine check`

Repository workflow permissions are read-only for contents, and checkout credentials are not persisted after checkout.

## Data safety

Contact exports can contain personally identifiable information. The repository ignores general CSV/Excel datasets and generated outputs while explicitly tracking only the synthetic example under `examples/`.

For real workflows:

- do not commit source contact exports
- do not publish normalized output files
- keep operational datasets outside the repository
- review retention and access requirements before processing personal data
- treat names and phone numbers as sensitive operational data
- do not include raw contact values in logs, exceptions, issues, or bug reports

See [SECURITY.md](SECURITY.md) for reporting and data-handling guidance.

## Public-snapshot boundaries

This repository demonstrates the normalization and selection core. It is **not** a claim that the public code reproduces the complete operational pipeline used on larger datasets.

Not included here:

- production-scale orchestration
- external storage or downstream integration layers
- every transformation used in the broader operational workflow
- authoritative telecom allocation lookup
- number-portability resolution
- distributed processing or job scheduling

The approximately **1 million-record** figure refers to the broader operational workflow tested at that scale, not to a benchmark claimed for this exact public repository snapshot.

## Why this project matters

The useful engineering problem is not simply cleaning strings. It is creating a predictable data contract from messy operational input while making validation, selection rules, data boundaries, and failure behavior explicit:

**raw exports → schema validation → normalization → selection → clean downstream dataset**

## License

Released under the [MIT License](LICENSE).

## Portfolio

For broader project context and other product/data work, see **[alirezabelal.github.io](https://alirezabelal.github.io/)**.
