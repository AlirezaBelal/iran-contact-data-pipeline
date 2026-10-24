"""Generate the static demonstration offline from fixed synthetic data and the core."""

import argparse
from html import escape
from pathlib import Path

import pandas as pd

from contact_processor import ContactProcessor

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = pd.DataFrame(
    [
        {
            "First Name": "کاربر",
            "Last Name": "نمونه",
            "Phone 1 - Value": "۰۹۱۲۰۰۰۰۰۰۱",
            "Phone 2 - Value": "+989120000001",
        },
        {
            "First Name": "Synthetic",
            "Last Name": "International",
            "Phone 1 - Value": "+989300000002",
            "Phone 2 - Value": "09120000003",
        },
        {
            "First Name": "",
            "Last Name": "",
            "Phone 1 - Value": "09880000004",
            "Phone 2 - Value": "",
        },
        {
            "First Name": "Synthetic",
            "Last Name": "Rejected",
            "Phone 1 - Value": "invalid",
            "Phone 2 - Value": "02100000000",
        },
        {
            "First Name": "Synthetic",
            "Last Name": "Shared number",
            "Phone 1 - Value": "09120000001",
            "Phone 2 - Value": "",
        },
    ]
)


def table(frame, identifier, caption):
    headers = "".join(f'<th scope="col">{escape(str(x))}</th>' for x in frame.columns)
    rows = "".join(
        "<tr>" + "".join(f'<td dir="auto">{escape(str(x))}</td>' for x in row) + "</tr>"
        for row in frame.itertuples(index=False, name=None)
    )
    return f'<div class="table-wrap"><table id="{identifier}"><caption>{caption}</caption><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>'


def build_page():
    output, stats = ContactProcessor.clean_contacts_with_stats(SAMPLE.copy(deep=True))
    metrics = [
        ("input-rows", "Input rows", stats.input_rows),
        ("output-rows", "Output rows", stats.output_rows),
        (
            "invalid-rows",
            "Rows without a valid mobile format",
            stats.input_rows - stats.output_rows,
        ),
        (
            "within-duplicates",
            "Duplicates within records",
            stats.duplicate_numbers_within_rows,
        ),
        (
            "shared-numbers",
            "Repeated selected numbers across records",
            stats.repeated_selected_numbers,
        ),
    ]
    counters = "".join(
        f'<div><dt>{label}</dt><dd id="{key}">{value}</dd></div>'
        for key, label, value in metrics
    )
    operators = ", ".join(
        f"{escape(name)}: {count}"
        for name, count in sorted(stats.selected_operators.items())
    )
    return (
        """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Iranian Contact Data Pipeline</title>
<style>
:root{font-family:system-ui,sans-serif;color:#172d2a;background:#f2f6f4;line-height:1.65}
*{box-sizing:border-box}body{margin:0}main{max-width:1120px;margin:auto;padding:48px 24px}
header{max-width:760px;margin-bottom:28px}.eyebrow{color:#266756;font-weight:700;letter-spacing:.1em;font-size:.8rem}
h1{font-size:clamp(2rem,5vw,3.5rem);line-height:1.12;margin:12px 0 20px}h2{font-size:1.35rem;margin-top:0}
section{background:#fff;border:1px solid #d6e2dc;border-radius:16px;padding:24px;margin:20px 0}
.notice{border-left:5px solid #277357;background:#e5f1eb}.notice p{margin:6px 0}
a{color:#175c48;text-underline-offset:3px}a:focus-visible{outline:3px solid #aa6a00;outline-offset:4px}
.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:.9rem;white-space:nowrap}
caption{text-align:left;margin-bottom:12px;color:#50655e}th,td{text-align:left;padding:12px;border-bottom:1px solid #dce5df}
th{background:#eef4f0}dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:16px;margin:0}
dt{font-size:.85rem;color:#50655e}dd{margin:8px 0 0;font-size:1.8rem;font-weight:700}code{overflow-wrap:anywhere}
footer{font-size:.9rem;color:#50655e;margin-top:28px}@media(max-width:600px){main{padding:28px 14px}section{padding:18px}}
</style>
</head>
<body><main>
<header><p class="eyebrow">LOCAL PYTHON TOOL · SYNTHETIC PREVIEW</p>
<h1>Iranian Contact Data Pipeline</h1>
<p>A privacy-conscious Python tool for normalizing Iranian contact exports.</p></header>
<section class="notice" aria-labelledby="privacy"><h2 id="privacy">A demonstration, not a contact service</h2>
<p>This is a synthetic demonstration. No contact files can be uploaded through this page.</p>
<p>No personal contact information is processed by this page. The actual pipeline runs locally through the Python CLI.</p>
<p>All displayed names and phone-shaped values are fabricated fixtures, not recipients. Do not use them for messaging.</p>
<p>This page makes no claim about the hosting platform's access logs or retention policies.</p></section>
<section><h2>Synthetic input</h2>
"""
        + table(
            SAMPLE,
            "synthetic-input",
            "Fixed fixture: Persian digits, international formats, invalid values and shared numbers.",
        )
        + """
</section><section><h2>Actual Python core output</h2>
<p>Generated at build time by <code>ContactProcessor.clean_contacts_with_stats</code>. No JavaScript normalization or backend processing is used.</p>
"""
        + table(
            output,
            "core-output",
            "The four output columns are unchanged from the CLI contract.",
        )
        + f"""
</section><section><h2>Processing summary</h2><dl>{counters}</dl>
<p id="operator-summary">Approximate operator labels — {operators}</p></section>
"""
        + """<section><h2>What this result does not prove</h2><ul>
<li>Operator classification is heuristic; mobile number portability is not resolved.</li>
<li>Normalization does not verify ownership, reachability or active service.</li>
<li>This tool does not establish consent for SMS campaigns and sends no messages.</li>
<li>Duplicate numbers within a row are suppressed. Different contacts sharing a number remain separate rows.</li>
</ul></section><section><h2>Process authorized data locally</h2>
<p>The CLI is the product. Keep private inputs, outputs and backups on a secured local system.</p>
<p><a href="https://github.com/AlirezaBelal/iran-contact-data-pipeline#safe-quick-start">Read the local CLI quick start</a>
 · <a href="https://github.com/AlirezaBelal/iran-contact-data-pipeline/blob/master/SECURITY.md">Security guidance</a></p>
</section><footer>Static HTML and CSS only. Regenerate with <code>python scripts/build_demo.py</code>; CI checks this file against the authoritative core.</footer>
</main></body></html>
"""
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the committed page differs from freshly generated output",
    )
    args = parser.parse_args()
    destination = ROOT / "hf-space" / "index.html"
    rendered = build_page()
    if args.check:
        if (
            not destination.exists()
            or destination.read_text(encoding="utf-8") != rendered
        ):
            parser.exit(1, "Static demo is stale; run python scripts/build_demo.py\n")
    else:
        destination.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
