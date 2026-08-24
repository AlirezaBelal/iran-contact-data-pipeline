"""Contact normalization and selection logic."""

from typing import Dict, List, Optional

import pandas as pd

from constants import MAX_PHONE_NUMBERS, OPERATOR_PRIORITY
from exceptions import ContactNormalizationError
from utils import detect_mobile_operator, normalize_phone_number, safe_str_conversion


class ContactProcessor:
    """Normalize contact records and select one preferred valid mobile number."""

    @classmethod
    def clean_contacts(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Return a normalized contact DataFrame.

        Rows without any valid Iranian mobile number are omitted. When a row
        contains multiple valid numbers, configured operator priority is used;
        otherwise the first valid number is selected.
        """
        cleaned_contacts: List[Dict[str, str]] = []

        for _, row in df.iterrows():
            numbers = cls._extract_phone_numbers(row)
            selected = cls._select_best_phone_number(numbers)

            if not selected:
                continue

            cleaned_contacts.append(
                {
                    "first_name": safe_str_conversion(row.get("First Name")),
                    "last_name": safe_str_conversion(row.get("Last Name")),
                    "selected_phone": selected["number"],
                    "mobile_operator": selected["operator"],
                }
            )

        return pd.DataFrame(
            cleaned_contacts,
            columns=["first_name", "last_name", "selected_phone", "mobile_operator"],
        )

    @classmethod
    def _extract_phone_numbers(cls, row: pd.Series) -> List[Dict[str, str]]:
        """Extract valid normalized mobile numbers from configured phone fields."""
        numbers: List[Dict[str, str]] = []
        seen = set()

        for index in range(1, MAX_PHONE_NUMBERS + 1):
            phone_key = f"Phone {index} - Value"
            if phone_key not in row or pd.isna(row[phone_key]):
                continue

            raw_phone = safe_str_conversion(row[phone_key])
            if not raw_phone:
                continue

            try:
                normalized = normalize_phone_number(raw_phone)
            except ContactNormalizationError:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)
            numbers.append(
                {
                    "number": normalized,
                    "operator": detect_mobile_operator(normalized),
                }
            )

        return numbers

    @classmethod
    def _select_best_phone_number(
        cls, numbers: List[Dict[str, str]]
    ) -> Optional[Dict[str, str]]:
        """Select one valid number using operator priority, then input order."""
        for operator_name in OPERATOR_PRIORITY:
            for number in numbers:
                if number["operator"] == operator_name:
                    return number

        return numbers[0] if numbers else None
