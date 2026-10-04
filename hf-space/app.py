import re
from pathlib import Path
import tempfile

import gradio as gr
import pandas as pd
import spaces


# ZeroGPU requires at least one registered @spaces.GPU function during startup.
# This demo is CPU-only, so this no-op is intentionally never called.
@spaces.GPU(duration=10)
def _zerogpu_requirement():
    return None


IRAN_MOBILE_REGEX = re.compile(r"^09\d{9}$")
MCI_REGEX = re.compile(r"^(?:091\d{8}|099[012]\d{7})$")
IRANCELL_REGEX = re.compile(r"^(?:093\d{8}|090[0-5]\d{7})$")
RIGHTEL_REGEX = re.compile(r"^092[0-3]\d{7}$")

OPERATOR_PATTERNS = [
    ("MCI", MCI_REGEX),
    ("Irancell", IRANCELL_REGEX),
    ("Rightel", RIGHTEL_REGEX),
]
OPERATOR_PRIORITY = ["MCI", "Irancell", "Rightel"]
MAX_PHONE_NUMBERS = 4

DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)
ALLOWED_PHONE_CHARS_REGEX = re.compile(r"^[0-9+\s().-]+$")

SAMPLE = pd.DataFrame([
    {
        "First Name": "Ava",
        "Last Name": "Example",
        "Phone 1 - Value": "0912 123 4567",
        "Phone 2 - Value": "",
        "Phone 3 - Value": "",
        "Phone 4 - Value": "",
    },
    {
        "First Name": "Nima",
        "Last Name": "Example",
        "Phone 1 - Value": "+98 935 123 4567",
        "Phone 2 - Value": "02112345678",
        "Phone 3 - Value": "",
        "Phone 4 - Value": "",
    },
    {
        "First Name": "Sara",
        "Last Name": "Example",
        "Phone 1 - Value": "09211234567",
        "Phone 2 - Value": "09101112222",
        "Phone 3 - Value": "",
        "Phone 4 - Value": "",
    },
    {
        "First Name": "Omid",
        "Last Name": "Example",
        "Phone 1 - Value": "invalid",
        "Phone 2 - Value": "",
        "Phone 3 - Value": "",
        "Phone 4 - Value": "",
    },
])


def normalize_phone_number(phone_number):
    raw_value = "" if phone_number is None else str(phone_number).strip()
    raw_value = raw_value.translate(DIGIT_TRANSLATION)

    if (
        not raw_value
        or not ALLOWED_PHONE_CHARS_REGEX.fullmatch(raw_value)
        or raw_value.count("+") > 1
        or ("+" in raw_value and not raw_value.startswith("+"))
    ):
        raise ValueError("Invalid Iranian mobile number")

    digits = re.sub(r"\D", "", raw_value)

    if digits.startswith("0098"):
        digits = "0" + digits[4:]
    elif digits.startswith("98"):
        digits = "0" + digits[2:]
    elif len(digits) == 10 and digits.startswith("9"):
        digits = "0" + digits

    if not IRAN_MOBILE_REGEX.fullmatch(digits):
        raise ValueError("Invalid Iranian mobile number")

    return digits


def detect_mobile_operator(phone_number):
    for operator_name, pattern in OPERATOR_PATTERNS:
        if pattern.fullmatch(phone_number):
            return operator_name
    return "Other/Unknown"


def safe_str(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def extract_numbers(row):
    numbers = []
    seen = set()

    for index in range(1, MAX_PHONE_NUMBERS + 1):
        key = f"Phone {index} - Value"
        if key not in row:
            continue

        raw_value = row.get(key)
        if raw_value is None or pd.isna(raw_value):
            continue

        raw_phone = safe_str(raw_value)
        if not raw_phone:
            continue

        try:
            normalized = normalize_phone_number(raw_phone)
        except ValueError:
            continue

        if normalized in seen:
            continue

        seen.add(normalized)
        numbers.append({
            "number": normalized,
            "operator": detect_mobile_operator(normalized),
        })

    return numbers


def select_best(numbers):
    for operator_name in OPERATOR_PRIORITY:
        for number in numbers:
            if number["operator"] == operator_name:
                return number
    return numbers[0] if numbers else None


def clean_contacts(df):
    if df is None:
        raise gr.Error("Upload a CSV or use the synthetic example.")

    if isinstance(df, str):
        df = pd.read_csv(df, encoding="utf-8-sig")

    required = ["First Name", "Last Name", "Phone 1 - Value"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise gr.Error("Missing required columns: " + ", ".join(missing))

    cleaned = []
    for _, row in df.iterrows():
        selected = select_best(extract_numbers(row))
        if not selected:
            continue

        cleaned.append({
            "first_name": safe_str(row.get("First Name")),
            "last_name": safe_str(row.get("Last Name")),
            "selected_phone": selected["number"],
            "mobile_operator": selected["operator"],
        })

    out = pd.DataFrame(
        cleaned,
        columns=["first_name", "last_name", "selected_phone", "mobile_operator"],
    )

    summary = (
        f"### Processing summary\n"
        f"- Input rows: **{len(df)}**\n"
        f"- Output rows with a valid mobile number: **{len(out)}**\n"
        f"- Rows without a usable mobile number: **{len(df) - len(out)}**\n\n"
        "> Prefix classification is a transparent heuristic, not an authoritative operator registry."
    )

    path = Path(tempfile.gettempdir()) / "cleaned_contacts.csv"
    out.to_csv(path, index=False, encoding="utf-8-sig")
    return out, summary, str(path)


def test_single(number):
    try:
        normalized = normalize_phone_number(number)
        operator = detect_mobile_operator(normalized)
        return normalized, operator, "Valid mobile shape"
    except Exception:
        return "", "", "Invalid or unsupported Iranian mobile shape"


with gr.Blocks(title="Iranian Contact Data Pipeline") as demo:
    gr.Markdown(
        "# 🧹 Iranian Contact Data Pipeline\n"
        "Normalize, validate, classify and select Iranian mobile numbers using transparent rules."
    )

    with gr.Tab("CSV pipeline"):
        with gr.Row():
            upload = gr.File(label="Upload CSV", file_types=[".csv"], type="filepath")
            sample_btn = gr.Button("Load synthetic example", variant="secondary")

        preview = gr.Dataframe(
            value=SAMPLE,
            interactive=True,
            label="Input preview",
            wrap=True,
        )

        run_btn = gr.Button("Clean contacts", variant="primary")
        output_columns = [
            "first_name",
            "last_name",
            "selected_phone",
            "mobile_operator",
        ]
        output = gr.Dataframe(
            headers=output_columns,
            value=pd.DataFrame(columns=output_columns),
            label="Normalized output",
            interactive=False,
            wrap=True,
        )
        summary = gr.Markdown(
            "### Ready to process\n"
            "Upload a CSV or use the synthetic example, then select **Clean contacts**."
        )
        download = gr.DownloadButton(
            "Download cleaned CSV",
            value=None,
            variant="secondary",
        )

        sample_btn.click(lambda: SAMPLE, outputs=preview)

        def load_uploaded(path):
            if not path:
                return SAMPLE
            return pd.read_csv(path, encoding="utf-8-sig")

        upload.change(load_uploaded, inputs=upload, outputs=preview)
        run_btn.click(
            clean_contacts,
            inputs=preview,
            outputs=[output, summary, download],
        )

    with gr.Tab("Single-number demo"):
        number = gr.Textbox(
            label="Iranian mobile number",
            placeholder="+98 912 123 4567",
        )
        normalize_btn = gr.Button("Normalize", variant="primary")
        normalized = gr.Textbox(label="Normalized", interactive=False)
        operator = gr.Textbox(label="Operator heuristic", interactive=False)
        status = gr.Textbox(label="Status", interactive=False)
        normalize_btn.click(
            test_single,
            inputs=number,
            outputs=[normalized, operator, status],
        )

    gr.Markdown(
        "> Privacy note: this public demo does not persist uploaded contact data. "
        "Use synthetic or intentionally shared data only."
    )


if __name__ == "__main__":
    demo.launch(ssr_mode=False)
