"""Command-line interface for the contact-cleaning pipeline."""

import argparse
import sys

import pandas as pd

from contact_processor import ContactProcessor
from exceptions import ContactCleanerError, FileProcessingError
from utils import ensure_directory_exists


def main():
    """Run the contact-cleaning pipeline from the command line."""
    parser = argparse.ArgumentParser(
        description="Normalize Iranian contact data and select a preferred valid mobile number."
    )
    parser.add_argument("input", help="Input CSV file path")
    parser.add_argument("output", help="Output CSV file path")
    args = parser.parse_args()

    try:
        contacts_df = _read_input_file(args.input)
        input_count = len(contacts_df)

        print("Processing contacts...")
        cleaned_df = ContactProcessor.clean_contacts(contacts_df)

        ensure_directory_exists(args.output)
        cleaned_df.to_csv(args.output, index=False, encoding="utf-8-sig")

        output_count = len(cleaned_df)
        rejected_count = input_count - output_count

        print(f"Cleaned contacts saved to {args.output}")
        print(f"Input rows: {input_count}")
        print(f"Output rows with a valid mobile number: {output_count}")
        print(f"Rows without a valid mobile number: {rejected_count}")

    except FileNotFoundError:
        print(f"Error: input file not found - {args.input}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(
            f"Error: permission denied when accessing {args.input} or {args.output}",
            file=sys.stderr,
        )
        sys.exit(1)
    except ContactCleanerError as exc:
        print(f"Contact cleaning error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


def _read_input_file(file_path: str) -> pd.DataFrame:
    """Read and validate the input CSV file."""
    try:
        df = pd.read_csv(
            file_path,
            encoding="utf-8",
            low_memory=False,
            dtype=str,
            keep_default_na=False,
        )

        required_columns = ["First Name", "Last Name", "Phone 1 - Value"]
        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            raise FileProcessingError(
                f"Missing required columns: {', '.join(missing_columns)}"
            )

        return df

    except (FileNotFoundError, PermissionError):
        raise
    except pd.errors.EmptyDataError as exc:
        raise FileProcessingError("The input CSV file is empty.") from exc
    except pd.errors.ParserError as exc:
        raise FileProcessingError(f"Error parsing CSV file: {exc}") from exc
    except ContactCleanerError:
        raise
    except Exception as exc:
        raise FileProcessingError(f"Unexpected error reading CSV file: {exc}") from exc


if __name__ == "__main__":
    main()
