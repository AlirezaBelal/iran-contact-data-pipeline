"""Utility functions for contact-cleaning operations."""

import os
import re
from typing import Optional

import pandas as pd

from constants import IRAN_MOBILE_REGEX, OPERATOR_PATTERNS
from exceptions import ContactNormalizationError

DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)
ALLOWED_PHONE_CHARS_REGEX = re.compile(r"^[0-9+\s().-]+$")


def normalize_phone_number(phone_number: str) -> str:
    """Normalize an Iranian mobile number to local ``09xxxxxxxxx`` format.

    Supported inputs include local numbers, ``+98``/``0098`` international
    forms, ten-digit numbers beginning with ``9``, and Persian/Arabic digits.
    Common visual separators are tolerated, while embedded text or unsupported
    characters are rejected instead of being silently stripped away.
    """
    raw_value = "" if phone_number is None else str(phone_number).strip()
    raw_value = raw_value.translate(DIGIT_TRANSLATION)

    if (
        not raw_value
        or not ALLOWED_PHONE_CHARS_REGEX.fullmatch(raw_value)
        or raw_value.count("+") > 1
        or ("+" in raw_value and not raw_value.startswith("+"))
    ):
        raise ContactNormalizationError("Invalid Iranian mobile number")

    digits = re.sub(r"\D", "", raw_value)

    if digits.startswith("0098"):
        digits = "0" + digits[4:]
    elif digits.startswith("98"):
        digits = "0" + digits[2:]
    elif len(digits) == 10 and digits.startswith("9"):
        digits = "0" + digits

    if not IRAN_MOBILE_REGEX.fullmatch(digits):
        # Contact data is potentially sensitive. Keep exception text generic so
        # callers can safely log or surface it without leaking the raw value.
        raise ContactNormalizationError("Invalid Iranian mobile number")

    return digits


def detect_mobile_operator(phone_number: str) -> str:
    """Classify a normalized mobile number using configured prefix rules."""
    for operator_name, pattern in OPERATOR_PATTERNS:
        if pattern.fullmatch(phone_number):
            return operator_name
    return "Other/Unknown"


def ensure_directory_exists(file_path: str) -> None:
    """Ensure the output directory for ``file_path`` exists."""
    folder_path = os.path.dirname(file_path)
    if folder_path:
        os.makedirs(folder_path, exist_ok=True)


def safe_str_conversion(value: Optional[object], default: str = "") -> str:
    """Convert a value to stripped text while handling null/NaN values."""
    if value is None or pd.isna(value):
        return default
    return str(value).strip()
