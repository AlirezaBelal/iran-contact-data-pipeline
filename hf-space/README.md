---
title: Iranian Contact Data Pipeline
emoji: 🧹
colorFrom: green
colorTo: blue
sdk: static
app_file: index.html
license: mit
---

# Iranian Contact Data Pipeline — Static Synthetic Demonstration

The CLI is the product. This HTML/CSS page shows a fixed synthetic input and the
actual output of the authoritative Python core. It has no scripts, contact inputs,
upload form, processing API, user-generated downloads or Python/GPU runtime.
Gradio and its Pillow dependency are no longer needed for this demonstration.

From an installed repository checkout, run `python scripts/build_demo.py` to
regenerate the committed page or add `--check` to detect drift. Fixture data is
embedded in that generator; no external contacts, randomness, timestamp or network
are used. Tests compare the rendered tables and counters with core/CLI results.

Only this README and `index.html` belong in the published Space root. CI does not
publish them. The sync workflow remains manual-only, requires explicit confirmation
on master and must not run without separate owner approval. No Space build command,
Python requirements, source package or backend is required on the hosting platform.

Number format is not ownership, reachability or consent. Operator labels are
heuristic and do not resolve portability. This page makes no zero-retention claim
about hosting/access logs. Existing hosted Gradio code, dependencies and caches are
separate from these proposed static files and are not changed by GitHub tests.

[Local CLI quick start](https://github.com/AlirezaBelal/iran-contact-data-pipeline#safe-quick-start)
