# Security Policy

## Supported version

Security fixes are applied to the current `master` branch.

## Reporting a vulnerability

Please report security issues privately through GitHub's security reporting features when available. Do not open a public issue containing credentials, personal contact data, or other sensitive information.

Include enough detail to reproduce the issue without attaching real contact exports or production datasets.

## Data handling

This repository is a sanitized portfolio snapshot. Contact exports can contain personally identifiable information, including names and phone numbers.

- Do not commit real contact exports or generated cleaned datasets.
- Keep operational datasets outside the repository.
- Use synthetic data for tests, examples, and bug reports.
- Avoid logging or surfacing raw phone values in error messages.
- If sensitive data is accidentally committed, remove it from the active branch and assess whether Git history must also be rewritten.

Any credential or sensitive dataset that has been publicly exposed should be treated as compromised even after deletion from the current branch.

## Dependency and CI security

GitHub Actions uses read-only repository contents permission. Runtime dependencies are checked in CI with `pip-audit`, and automated dependency update checks are configured with Dependabot.

## Local processing and public demo

Local CLI output intentionally contains normalized personal data. Protect inputs,
outputs, their directories and backups; define retention and deletion procedures.
Atomic output publication prevents partial/truncated files, not all power-loss or
host-compromise scenarios. Import untrusted CSV names as text in spreadsheets.

The historical Hugging Face preview is static HTML/CSS generated offline from a fixed synthetic
fixture. It accepts no contact inputs and has no processing backend or Python runtime.
It does not need Gradio, Pillow or GPU support. This does not establish anything
about old hosted code/caches or the platform's access logs. Review the existing
service separately; never upload real data for testing. Publication remains manual
and requires separate owner approval.

Phone normalization rejects quoted CSV phone fields with embedded or trailing
control whitespace and values over 64 characters before any trimming. This
avoids silently repairing malformed contact data into a plausible recipient.
Tests use fictional values only and never transmit messages.

Normalization does not establish ownership, active service or consent. Shared phone
numbers across contact rows are retained; downstream senders must independently
verify permission, honor exclusions and prevent duplicate submissions.

## Removed demo runtime dependency

The former Gradio dependency set constrained Pillow below the version fixing the
reported advisories, including
[GHSA-78g4-xqwv-q3g8](https://github.com/python-pillow/Pillow/security/advisories/GHSA-78g4-xqwv-q3g8).
The resolution is removal of the unnecessary Python demo runtime, not an audit
exception or unsupported dependency override. CI still audits the actual CLI
runtime and distribution build/validation dependencies. Static files need no
Python packages on the hosting platform. The owner-approved publication on 2026-10-24 replaced the current Space with
Static HTML and removed its Gradio runtime files; the public static SDK and
current tree were rechecked on 2026-10-26. Historical revisions, caches, logs
and prior runtime storage remain outside that verification.

## GitHub Pages browser-local tool

`docs/` is the real CSV tool, independent of the historical Static Space. It reads
selected files in tab memory with a 1 MiB / 1,000-row limit and fatal UTF-8 decoding.
No dataset upload, accounts, remote processing, contact logging, analytics, or
persistent contact storage is implemented. A restrictive CSP blocks connections.
All untrusted values are rendered with textContent. Errors omit contact values.
Reset clears the workspace and invalidates pending reads; memory handling cannot
guarantee erasure of all browser/OS artifacts. Downloaded CSV files remain local
copies requiring appropriate retention and access controls.

Browser exports prefix formula-like names with an apostrophe (including formulas
behind leading whitespace). Python intentionally preserves names. Treat either
CSV as untrusted and import columns as text; spreadsheet behavior varies.

Browser and Python core normalization/selection rules use synthetic parity tests.
Their input limits and parser implementation details differ as documented in the
README. Neither implementation verifies consent or current carrier. No SMS is sent.
