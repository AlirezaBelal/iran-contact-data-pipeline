# Iranian Contact Data Normalization Pipeline

[![CI](https://github.com/AlirezaBelal/iran-contact-data-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/AlirezaBelal/iran-contact-data-pipeline/actions/workflows/ci.yml)

A lightweight local Python CLI for normalizing Iranian contact exports, inspecting
up to four phone fields and selecting one mobile-number-shaped value per contact.
It preserves Persian names and reports aggregate data-quality metrics.

**Number format is not ownership, reachability or consent. This tool sends no SMS.**

## Safe quick start

Python 3.9–3.14 is checked in CI. Use only the bundled synthetic fixture to try it:

```bash
git clone https://github.com/AlirezaBelal/iran-contact-data-pipeline.git
cd iran-contact-data-pipeline
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -e .
contact-cleaner examples/contacts.example.csv outputs/cleaned.csv
```

Expected core summary:

```text
Cleaned contacts saved.
Input rows: 6
Output rows with a valid mobile number: 5
Rows without a valid mobile number: 1
```

Additional lines report invalid nonempty phone values, duplicates within records,
rows with multiple candidates, repeated selected numbers across records, rows with
no name and selected operator groups. These are aggregate counts, not contact data.

An existing output is refused. Review it before explicitly using `--overwrite`.
Input/output aliases (including hard links) are always refused; output symlinks are
unsupported. Success exits 0, processing/file errors exit 1, CLI usage errors exit 2,
and interruption exits 130. Diagnostics omit private contact values and file paths.

## Input and output

Input is UTF-8 CSV (BOM accepted). Required headers:
`First Name`, `Last Name`, `Phone 1 - Value`. Names may be empty.
Optional fields: `Phone 2 - Value` through `Phone 4 - Value`.
Duplicate headers, malformed rows, inconsistent field counts, empty files and
header-only files are rejected. CLI limits are 50 MiB and 100,000 input rows; the
in-memory core has no claim of constant-memory or unbounded-scale processing.

| Output column | Meaning |
|---|---|
| `first_name` | Stripped first name, or empty |
| `last_name` | Stripped last name, or empty |
| `selected_phone` | Selected local `09xxxxxxxxx` representation |
| `mobile_operator` | Heuristic prefix group, or `Other/Unknown` |

Output is UTF-8-SIG, including its four headers when every input row is rejected.
Rows without any valid mobile-number format are omitted and counted. Source records
are not modified. Output contains personal data and must remain private.

### Normalization and selection

Supported shapes include `09…`, ten-digit `9…`, `989…`, `+989…`, `00989…`, Persian
and Arabic digits, and common visual separators. Invalid lengths, landlines,
embedded arbitrary text, unsupported characters and malformed plus signs are
rejected; an ambiguous number is not repaired into a plausible recipient.

Within each contact, equivalent normalized numbers are suppressed. Preference is
**MCI → Irancell → Rightel → Other/Unknown**, then original phone-field order for
ties. This is a transparent product rule, not a universal recommendation.

Prefix classification is a conservative heuristic, not a current carrier registry.
Ambiguous `0931`, `0932` and `0934` groups are intentionally left `Other/Unknown`.
Unknown groups remain usable if their number shape is valid. Rules are in
`src/constants.py`; they neither resolve mobile-number portability nor prove
allocation, current service or ownership.

Different contact rows sharing a selected number are **preserved**, even with
identical names. `Repeated selected numbers across records` counts output rows
after the first occurrence of each selected number. It does not merge people or
claim globally unique recipients. Candidate/invalid/within-row metrics inspect only
the first four configured phone fields; empty optional values are not errors.

## Local file and privacy safeguards

A complete output is written to a private temporary file in the destination
folder, flushed, then atomically published. Without `--overwrite`, atomic
create-if-absent prevents a competing writer from being overwritten. Filesystems
that cannot support this operation fail safely. With explicit overwrite, the
complete replacement is atomic. A failed/interrupted write removes its temporary
file and does not truncate an existing output. Power-loss durability still depends
on the filesystem; atomic publication is not a backup policy.

New output files use restrictive creation permissions where supported. Keep input,
output and their parent directories private; protect backups and host access too.
Do not commit datasets or attach them to Issues, PRs or public services. The tool
intentionally writes the requested normalized file: **there is no zero-retention
claim or automatic deletion**. Apply an authorized retention policy and delete
inputs, outputs and backups when appropriate. Spreadsheet software can interpret
untrusted names as formulas; import CSV columns as text rather than trusting a
file extension. Names are preserved, not rewritten as a spreadsheet-safety policy.

## Static synthetic demonstration

The CLI is the product. `hf-space/index.html` is a self-contained HTML/CSS preview
of fixed synthetic input and its actual Python core output. It has no scripts,
upload controls, contact textboxes, backend processing or user-generated downloads.
Gradio and its Pillow dependency were removed because this presentation needs no
Python/GPU runtime on the hosting platform. No vulnerable dependency is suppressed.

From an installed checkout, regenerate with `python scripts/build_demo.py` or check
for drift with `python scripts/build_demo.py --check`. The generator calls the
same core as the CLI; it does not reimplement normalization in another language.
Its fixture is explicitly synthetic, deterministic and network-free. Tests compare
the HTML tables/counters with the core and CLI CSV contract. The committed page
is reviewable and works without a network connection after opening it locally.

The Space metadata uses [Static HTML SDK](https://huggingface.co/docs/hub/spaces-sdks-static).
Only `hf-space/README.md` and `hf-space/index.html` are staged for publication.
No source package, contact datasets or environment files belong in that payload.
The sync workflow remains manual-only and requires explicit approval on master.
The first owner-approved Static Space publication succeeded on 2026-10-24;
subsequent runs still require separate owner approval.

The approved publication on 2026-10-24 deployed Static HTML to the Space and
removed `app.py` and `requirements.txt` from the current remote file tree.
[Publication workflow](https://github.com/AlirezaBelal/iran-contact-data-pipeline/actions/runs/40119605303)
and [Hugging Face commit](https://huggingface.co/spaces/AlirezaBelal/iran-contact-data-pipeline/commit/067d1453b9d042c0a6873eb052524740956694cf)
record that release. Current-tree removal does **not** establish deletion of earlier
Git revisions, hosting caches, runtime files or access logs. The owner must assess
historical retention independently; never upload real contact data to the public
Space. See [Space source notes](hf-space/README.md).

## Independent downstream SMS use

[Batch SMS Campaign Automation](https://github.com/AlirezaBelal/batch-sms-campaign-automation)
is an independent downstream tool. Its phone normalizer accepts this local format.
Its name column can be configured as `first_name`; `selected_phone` already matches.

This output **does not contain or create consent**. An authorized enrichment step
must supply independently supported consent status, scope, source and timestamp;
an exclusion list and explicit sending authorization are also required downstream.
Do not infer permission from a contact export. There is no automatic forwarding,
SMS dependency, shared database or campaign execution in this repository.

## Development and verification

```bash
python -m unittest discover -s tests -v
python -m pip install coverage ruff build twine pip-audit
coverage run --source=src -m unittest discover -s tests
coverage report --show-missing --fail-under=80
python benchmarks/benchmark_pipeline.py --rows 10000
python -m build
python -m twine check dist/*
```

All tests run on Python 3.9–3.14 without Gradio. Full coverage includes the core
and generator using `--source=src,scripts`. CI checks committed HTML against fresh
core output, Ruff correctness, dataset hygiene, runtime/build dependency advisories,
wheel/sdist validity and an independently installed wheel. No CI job publishes or
processes real contacts. Install build tools with `pip install -r requirements-build.txt`.

[Benchmarks](BENCHMARKS.md) use synthetic data without unstable timing gates.
The core retains `itertuples()` and does not add distributed processing or another
DataFrame framework. [Security guidance](SECURITY.md) covers private reporting.
MIT licensed; no CRM, telecom lookup, consent verification or messaging service is included.
