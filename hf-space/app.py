"""Synthetic-only Gradio demonstration using the installed authoritative core."""

import os

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio as gr
import pandas as pd

from contact_processor import ContactProcessor

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
            "Last Name": "Example",
            "Phone 1 - Value": "09300000002",
            "Phone 2 - Value": "09120000003",
        },
        {
            "First Name": "",
            "Last Name": "",
            "Phone 1 - Value": "09880000004",
            "Phone 2 - Value": None,
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


def run_demo():
    """No file paths, uploads, editable contact records or personal-data arguments."""
    output, stats = ContactProcessor.clean_contacts_with_stats(SAMPLE.copy(deep=True))
    summary = (
        f"Input rows: {stats.input_rows}; output rows: {stats.output_rows}; "
        f"rejected rows: {stats.input_rows - stats.output_rows}; "
        f"repeated selected numbers: {stats.repeated_selected_numbers}. "
        "Prefix labels are heuristic; normalization does not verify consent or ownership."
    )
    return output, summary


with gr.Blocks(title="Iranian Contact Data Pipeline", delete_cache=(600, 600)) as demo:
    gr.Markdown(
        "# Iranian Contact Data Pipeline\n"
        "**Synthetic-only demonstration. Do not upload or enter personal contact data.**\n"
        "This interface processes only the built-in fixture. Use the local CLI for authorized private data. "
        "The hosting platform may retain requests or caches; this is not a zero-retention service."
    )
    gr.Dataframe(value=SAMPLE, interactive=False, label="Built-in synthetic input")
    run_button = gr.Button("Process synthetic example", variant="primary")
    output = gr.Dataframe(
        headers=["first_name", "last_name", "selected_phone", "mobile_operator"],
        interactive=False,
        label="Synthetic normalized output",
    )
    summary = gr.Markdown(
        "Select the button to run the shared core on the built-in fixture."
    )
    run_button.click(run_demo, inputs=[], outputs=[output, summary])


if __name__ == "__main__":
    # CPU-only source. No server is launched by import or tests.
    demo.launch(ssr_mode=False, share=False, show_error=False, max_file_size="1kb")
