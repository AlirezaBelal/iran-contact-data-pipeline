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

The proposed public demo source accepts only its built-in synthetic fixture and
returns no application-generated file paths. It must not invite personal-data uploads.
Gradio's generic endpoints, request logs and hosting caches are not a verified
zero-retention boundary. Existing hosted code/caches are separate from source tests
and need review before any explicitly approved publication. Do not upload real data
for testing. Publication must remain a manual, separately approved operation.

Normalization does not establish ownership, active service or consent. Shared phone
numbers across contact rows are retained; downstream senders must independently
verify permission, honor exclusions and prevent duplicate submissions.

## Current Space dependency blocker

The audited Gradio 6.30.0 dependency set requires Pillow `<13`. The dependency audit
reports advisories in Pillow 12.3.0 with fixes in 13.0.0, including
[GHSA-78g4-xqwv-q3g8](https://github.com/python-pillow/Pillow/security/advisories/GHSA-78g4-xqwv-q3g8).
Do not publish this Space dependency set. Do not override dependency metadata,
downgrade blindly or suppress the audit. A compatible supported upstream dependency
set and successful import/contract/audit checks are required before publication.
The local CLI does not depend on Gradio or Pillow. Existing hosted dependencies
have not been inspected or changed by this source audit.
