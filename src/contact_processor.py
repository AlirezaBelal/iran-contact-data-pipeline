"""Contact normalization and selection logic."""

from typing import Dict, List, Mapping, Optional

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

        Row iteration uses ``itertuples`` rather than ``iterrows`` so pandas
        does not allocate a Series for every record. This keeps the existing
        validation semantics while reducing per-row overhead for larger files.
        """
        cleaned_contacts: List[Dict[str, str]] = []
        column_positions = {
            column: position for position, column in enumerate(df.columns)
        }

        for row in df.itertuples(index=False, name=None):
            numbers = cls._extract_phone_numbers(row, column_positions)
            selected = cls._select_best_phone_number(numbers)

            if not selected:
                continue

            cleaned_contacts.append(
                {
                    "first_name": safe_str_conversion(
                        cls._value_for_column(row, column_positions, "First Name")
                    ),
                    "last_name": safe_str_conversion(
                        cls._value_for_column(row, column_positions, "Last Name")
                    ),
                    "selected_phone": selected["number"],
                    "mobile_operator": selected["operator"],
                }
            )

        return pd.DataFrame(
            cleaned_contacts,
            columns=["first_name", "last_name", "selected_phone", "mobile_operator"],
        )

    @staticmethod
    def _value_for_column(
        row: tuple[object, ...], column_positions: Mapping[str, int], column: str
    ) -> object | None:
        position = column_positions.get(column)
        return row[position] if position is not None else None

    @classmethod
    def _extract_phone_numbers(
        cls,
        row: pd.Series | tuple[object, ...],
        column_positions: Mapping[str, int] | None = None,
    ) -> List[Dict[str, str]]:
        """Extract valid normalized mobile numbers from one contact record.

        ``clean_contacts`` passes tuples plus a precomputed column-position map
        for lower iteration overhead. Accepting a Series without that map keeps
        the focused extractor contract available to unit tests and callers.
        """
        numbers: List[Dict[str, str]] = []
        seen = set()

        for index in range(1, MAX_PHONE_NUMBERS + 1):
            phone_key = f"Phone {index} - Value"
            if column_positions is None:
                if not isinstance(row, pd.Series) or phone_key not in row:
                    continue
                raw_value = row[phone_key]
            else:
                if not isinstance(row, tuple):
                    raise TypeError("tuple row required when column positions are provided")
                raw_value = cls._value_for_column(row, column_positions, phone_key)

            if raw_value is None or pd.isna(raw_value):
                continue

            raw_phone = safe_str_conversion(raw_value)
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
