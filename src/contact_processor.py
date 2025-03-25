"""Main module for processing and cleaning contact information."""

from typing import List, Dict, Optional

import pandas as pd

from constants import (
    OPERATOR_PRIORITY,
    MAX_PHONE_NUMBERS
)
from utils import normalize_phone_number, safe_str_conversion


class ContactProcessor:
    """
    A class to process and clean contact information.
    """

    @classmethod
    def clean_contacts(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and process contact information from a DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame with contact information.

        Returns:
            pd.DataFrame: Cleaned contacts DataFrame.
        """
        cleaned_contacts: List[Dict[str, str]] = []

        for _, row in df.iterrows():
            # Extract and normalize phone numbers
            numbers = cls._extract_phone_numbers(row)

            # Select the best phone number
            selected_number = cls._select_best_phone_number(numbers)

            # If no number found, try to use an unfiltered number
            if not selected_number and numbers:
                selected_number = numbers[0]['number']

            # If still no number, skip to next contact
            if not selected_number:
                continue

            # Prepare contact information
            first_name = safe_str_conversion(row.get("First Name"))
            last_name = safe_str_conversion(row.get("Last Name"))

            cleaned_contacts.append({
                "first_name": first_name,
                "last_name": last_name,
                "selected_phone": selected_number
            })

        # Convert to DataFrame
        return pd.DataFrame(cleaned_contacts)

    @classmethod
    def _extract_phone_numbers(cls, row: pd.Series) -> List[Dict[str, str]]:
        """
        Extract and normalize phone numbers from a contact row.

        Args:
            row (pd.Series): A single row of contact data.

        Returns:
            List[Dict[str, str]]: List of normalized phone numbers.
        """
        numbers: List[Dict[str, str]] = []

        for i in range(1, MAX_PHONE_NUMBERS + 1):
            phone_key = f"Phone {i} - Value"
            if phone_key in row and pd.notna(row[phone_key]):
                phone_number = str(row[phone_key])

                # Normalize phone number
                normalized_number = normalize_phone_number(phone_number)

                # Explicitly avoid removing numbers, just normalize them
                numbers.append({"number": normalized_number})

        return numbers

    @classmethod
    def _select_best_phone_number(cls, numbers: List[Dict[str, str]]) -> Optional[str]:
        """
        Select the best phone number based on operator priority.

        Args:
            numbers (List[Dict[str, str]]): List of phone numbers.

        Returns:
            Optional[str]: Selected phone number or None.
        """
        # First, check for operator-specific numbers
        for regex in OPERATOR_PRIORITY:
            for num in numbers:
                if regex.match(num["number"]):
                    return num["number"]

        # If no operator-specific number, return None to allow fallback
        return None
