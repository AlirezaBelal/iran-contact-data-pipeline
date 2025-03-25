"""Utility functions for contact cleaning operations."""

import os
import re
from typing import Optional

import pandas as pd

from exceptions import ContactNormalizationError


def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone numbers to a standard format.

    Args:
        phone_number (str): Input phone number to normalize.

    Returns:
        str: Normalized phone number.

    Raises:
        ContactNormalizationError: If phone number cannot be normalized.
    """
    try:
        # Remove spaces and dashes
        phone_number = str(phone_number).replace(" ", "").replace("-", "")

        # Remove any non-digit characters except +
        phone_number = re.sub(r'[^\d+]', '', phone_number)

        # Handle +98 prefix
        if phone_number.startswith("+98"):
            phone_number = "09" + phone_number[3:]

        # Ensure number starts with 0
        if not phone_number.startswith("0"):
            # If the number looks like a valid phone number length, add leading zero
            if len(phone_number) == 10 or len(phone_number) == 9:
                phone_number = "0" + phone_number
            elif len(phone_number) > 10:
                # For very long numbers, take the last 10 digits and add leading zero
                phone_number = "0" + phone_number[-10:]

        # Truncate to maximum length if needed
        phone_number = phone_number[:11]

        return phone_number
    except Exception as e:
        raise ContactNormalizationError(f"Failed to normalize phone number: {phone_number}") from e


def ensure_directory_exists(file_path: str) -> None:
    """
    Ensure the directory for the given file path exists.

    Args:
        file_path (str): Path to the file.
    """
    folder_path = os.path.dirname(file_path)
    if folder_path and not os.path.exists(folder_path):
        os.makedirs(folder_path)


def safe_str_conversion(value: Optional[object], default: str = "") -> str:
    """
    Safely convert a value to string, handling None and NaN.

    Args:
        value (Optional[object]): Value to convert to string.
        default (str, optional): Default value if conversion fails. Defaults to "".

    Returns:
        str: Converted string value.
    """
    if pd.isna(value):
        return default
    return str(value).strip()
