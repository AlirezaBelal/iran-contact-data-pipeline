# Iranian Contact Data Normalization Pipeline

[![CI](https://github.com/AlirezaBelal/iran-contact-data-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/AlirezaBelal/iran-contact-data-pipeline/actions/workflows/ci.yml)

Prepare Iranian contact CSV files through a real **browser-local tool** or a local
Python CLI. Normalize supported phone formats, select one preferred mobile value
per accepted contact, and review aggregate data quality. No SMS is sent.

## Option A — Browser-local CSV tool

[Open CSV Tool](https://alirezabelal.github.io/iran-contact-data-pipeline/#workspace)
· [Product website](https://alirezabelal.github.io/iran-contact-data-pipeline/)
· [Portfolio overview](https://alirezabelal.github.io/work/lab/iran-contact-data-pipeline/)

Choose an authorized UTF-8 CSV (BOM supported), then select the local processing
button. Review accepted, rejected, and warning-bearing rows. Download all accepted
records as normalized UTF-8-SIG CSV, or headers only when none are accepted.
The Persian RTL workbench includes before/after comparison and 25-row pagination.
The optional sample is fictional; this is a working tool, not a simulation.

- Browser limits: **1 MiB and 1,000 records**. Required columns are listed below.
- Files are read in this tab. No uploads, accounts, analytics, contact logging, or
  persistent browser storage. CSP blocks outbound application connections.
- Reset clears references and invalidates pending reads; closing the tab ends the
  workspace. This is not a guarantee of browser/OS artifact erasure.
- Downloading creates a local copy. Protect it, your inputs, backups, and screen.
- Browser exports prefix formula-like name cells with an apostrophe, including
  leading-whitespace formulas. Python preserves names. Import CSV as text.
- Review flags include rejected rows, invalid values, multiple candidates, repeated
  selected numbers, unnamed accepted records, and unknown prefix groups.
- Shared numbers across rows are reported, **not merged**. Prefix groups do not
  prove current carrier, reachability, ownership, or consent.

## Option B — Local Python CLI

## Safe quick start

Python 3.9â€“3.14 is checked in CI. Use only the bundled synthetic fixture to try it:

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

Supported shapes include `09â€¦`, ten-digit `9â€¦`, `989â€¦`, `+989â€¦`, `00989â€¦`, Persian
and Arabic digits, and common visual separators. Invalid lengths, landlines,
embedded arbitrary text, unsupported characters, control whitespace (including
quoted CSV tabs/newlines), oversized values and malformed plus signs are
rejected; an ambiguous number is not repaired into a plausible recipient.
Ordinary ASCII spaces and visual separators are still accepted. Phone cells
are validated **before** trimming so hidden controls cannot be discarded.

Within each contact, equivalent normalized numbers are suppressed. Preference is
**MCI â†’ Irancell â†’ Rightel â†’ Other/Unknown**, then original phone-field order for
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

## Historical Hugging Face Static Space

Separately from the working GitHub Pages browser tool, `hf-space/index.html` is a self-contained HTML/CSS preview
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
coverage run --source=src,scripts -m unittest discover -s tests
coverage report --show-missing --fail-under=80
python benchmarks/benchmark_pipeline.py --rows 10000
python -m build
python -m twine check dist/*
```

Build dependencies also use Python-version markers: Python 3.9 resolves the
compatible `setuptools>=68,<83` range, while Python 3.10+ uses
`setuptools>=84.2.1`. Do not replace both branches with a single new
minimum without first confirming the entire Python support matrix.

All tests run on Python 3.9â€“3.14 without Gradio. Full coverage includes the core
and generator using `--source=src,scripts`. CI checks committed HTML against fresh
core output, Ruff correctness, dataset hygiene, runtime/build dependency advisories,
wheel/sdist validity and an independently installed wheel. No CI job publishes or
processes real contacts. Install build tools with `pip install -r requirements-build.txt`.

[Benchmarks](BENCHMARKS.md) use synthetic data without unstable timing gates.
The core retains `itertuples()` and does not add distributed processing or another
DataFrame framework. [Security guidance](SECURITY.md) covers private reporting.
MIT licensed; no CRM, telecom lookup, consent verification or messaging service is included.

## Browser implementation and verification

The standalone website and workbench live in `docs/`; Pages publishes only that
folder. JavaScript has no runtime dependencies. The Python CLI remains separately
supported with its existing atomic output and strict validation contract.

```bash
node --test tests/browser_demo.test.cjs
python -m unittest discover -s tests -v
```

Parity tests cover supported formats, Persian/Arabic digits, controls, malformed
values, operator priority, duplicates, empty names, metrics, schema, and export.
Core rules match on tested fixtures. Deliberate boundaries: Python's CLI allows
50 MiB / 100,000 rows; browser allows 1 MiB / 1,000. CSV parsers are independent:
the browser rejects quotes outside quoted fields more strictly than Python's CSV
reader. Both require consistent row widths. Browser review labels/pagination are
presentation features. Browser formula escaping differs from name-preserving CLI
exports; neither should be opened blindly in spreadsheet software.

The browser QA workflow tests Chromium at 320, 375, 390, 768, 1024, 1440, and
1920px, real synthetic file import/export, failures, reset/read races, keyboard
focus, RTL/table scrolling, axe WCAG checks, and a zero-external-request boundary.
Synthetic-only screenshots and JSON results are retained as Actions artifacts for
14 days. Production QA verifies the actual published release after merge.
