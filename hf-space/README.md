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
about hosting/access logs. The first owner-approved deployment on 2026-10-24
replaced the current Gradio source with this Static Space. The current remote
tree no longer includes `app.py` or `requirements.txt`; historical revisions,
hosting caches and logs are not verified as erased by publication or GitHub CI.

[Local CLI quick start](https://github.com/AlirezaBelal/iran-contact-data-pipeline#safe-quick-start)

## Approved publication cleanup and verification

The pinned Hugging Face CLI 2.3.0 upload uses explicit `--delete app.py` and
`--delete requirements.txt` in the same commit as the static upload. These are
the obsolete runtime files observed in the remote tree; `.gitattributes` and
unrelated files are preserved. There is no repository-wide deletion wildcard.
This procedure runs only after separate owner authorization, never during CI.

After each separately approved publication:

- Confirm remote README metadata has `sdk: static` and serves `index.html`.
- Confirm the previous Gradio interface, CSV upload and contact-entry UI are absent.
- Confirm `app.py` and `requirements.txt` are absent from the current remote tree.
- Confirm only the reviewed synthetic fixture and core-generated results appear.
- Review residual hosting caches and retention separately. Removing current files
  does not erase Git history or prove that historical contact data was deleted.
