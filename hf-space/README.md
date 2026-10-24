---
title: Iranian Contact Data Pipeline
emoji: 🧹
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
python_version: "3.12"
pinned: false
license: mit
---

# Iranian Contact Data Pipeline — Synthetic Demonstration

This CPU-only demo processes a fixed synthetic fixture through the same installed
core as the local CLI. It accepts no user contact arguments, CSV uploads or editable
contact tables and returns no application-generated file paths. Displayed records
are synthetic. Do not send personal data to this public service or its API.

The generic hosting/Gradio stack may still retain requests and caches; no
zero-retention or session-private file-serving guarantee is made. Cache cleanup
is bounded where Gradio supports it, but is not a personal-data protection boundary.

Number shape is not ownership, reachability or consent. Operator labels are prefix
heuristics and do not resolve portability. Duplicate numbers within a row are
suppressed; different rows sharing a number remain separate contacts.

## Source and deployment

Install the repository package and this directory's requirements from the repository
root to import/smoke-test locally. Importing `app.py` does not launch a service.
The manually gated sync workflow assembles this directory plus `src/`, `setup.py`
and `pyproject.toml`; `.` in requirements installs that staged core. Uploading only
`hf-space/` is insufficient. No duplicate normalization implementation is maintained.

Publication requires separate maintainer approval, manual workflow confirmation and
a CPU-compatible Space. No GPU/ZeroGPU workaround is included. Source tests do not
prove that a currently hosted Space is updated or safe; its hardware, old caches
and operational state must be reviewed separately before approved publication.

[Source repository](https://github.com/AlirezaBelal/iran-contact-data-pipeline)
