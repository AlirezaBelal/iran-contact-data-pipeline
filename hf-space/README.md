---
title: Iranian Contact Data Pipeline
emoji: 🧹
colorFrom: teal
colorTo: blue
sdk: gradio
app_file: app.py
python_version: "3.12"
pinned: false
license: mit
---

# Iranian Contact Data Pipeline — Demo

A privacy-safe interactive demo of the public Python pipeline for structured Iranian contact-data processing.

The Space demonstrates:
- Iranian mobile normalization
- malformed/landline rejection
- multi-phone-field extraction
- duplicate suppression
- operator classification
- explicit operator-priority selection

Output contract:

`one contact → one selected normalized mobile number → one operator label`

Operator priority:
1. MCI
2. Irancell
3. Rightel
4. Other / Unknown

Operator-prefix rules are transparent heuristics, not an authoritative telecom allocation or number-portability registry.

Use synthetic or intentionally shared data only.

Original project:
https://github.com/AlirezaBelal/iran-contact-data-pipeline
