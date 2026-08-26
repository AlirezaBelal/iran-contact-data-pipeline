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
