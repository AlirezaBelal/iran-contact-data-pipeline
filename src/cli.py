"""Command line interface for the contact cleaner application."""

import argparse
import sys

import pandas as pd

from contact_processor import ContactProcessor
from exceptions import ContactCleanerError, FileProcessingError
from utils import ensure_directory_exists


def main():
    """
    Main entry point for the contact cleaner CLI.

    Handles command-line arguments and runs the contact cleaning process.
    """
    parser = argparse.ArgumentParser(description="Clean and normalize contact information.")
    parser.add_argument("input", help="Input CSV file path")
    parser.add_argument("output", help="Output CSV file path")

    args = parser.parse_args()

    try:
        # Read input CSV
        contacts_df = _read_input_file(args.input)

        # Process contacts
        print("Processing contacts...")
        cleaned_df = ContactProcessor.clean_contacts(contacts_df)

        # Ensure output directory exists
        ensure_directory_exists(args.output)

        # Save cleaned contacts
        cleaned_df.to_csv(args.output, index=False)

        print(f"Cleaned contacts saved to {args.output}")
        print(f"Total contacts processed: {len(cleaned_df)}")

    except FileNotFoundError:
        print(f"Error: Input file not found - {args.input}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied when accessing {args.input} or {args.output}", file=sys.stderr)
        sys.exit(1)
    except ContactCleanerError as e:
        print(f"Contact cleaning error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def _read_input_file(file_path: str) -> pd.DataFrame:
    """
    Read and validate the input CSV file.

    Args:
        file_path (str): Path to the input CSV file.

    Returns:
        pd.DataFrame: Loaded DataFrame with contact information.

    Raises:
        FileProcessingError: If there are issues reading the file.
    """
    try:
        # Read CSV with tolerant parsing
        df = pd.read_csv(file_path,
                         encoding='utf-8',
                         low_memory=False,
                         dtype=str,  # Read all columns as strings to prevent type issues
                         keep_default_na=False)  # Prevent converting empty strings to NaN

        # Validate required columns
        required_columns = ["First Name", "Last Name", "Phone 1 - Value"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise FileProcessingError(f"Missing required columns: {', '.join(missing_columns)}")

        return df

    except pd.errors.EmptyDataError:
        raise FileProcessingError("The input CSV file is empty.")
    except pd.errors.ParserError as e:
        raise FileProcessingError(f"Error parsing CSV file: {e}")
    except Exception as e:
        raise FileProcessingError(f"Unexpected error reading CSV file: {e}")


if __name__ == "__main__":
    main()
