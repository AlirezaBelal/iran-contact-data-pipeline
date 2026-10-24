"""Bounded CSV input and atomic, explicit output for private local processing."""

import argparse
import csv
import os
from pathlib import Path
import sys
import tempfile

import pandas as pd

from contact_processor import ContactProcessor
from exceptions import ContactCleanerError, FileProcessingError

MAX_INPUT_BYTES = 50 * 1024 * 1024
MAX_INPUT_ROWS = 100_000
REQUIRED_COLUMNS = {"First Name", "Last Name", "Phone 1 - Value"}


def _read_input_file(file_path: str) -> pd.DataFrame:
    """Read strict UTF-8 CSV without pandas' implicit index/header repair."""
    try:
        path = Path(file_path)
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise FileProcessingError("Input CSV exceeds the 50 MiB size limit.")
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            fields = reader.fieldnames
            if not fields:
                raise FileProcessingError("The input CSV file is empty.")
            if len(fields) != len(set(fields)):
                raise FileProcessingError("Duplicate CSV headers are not supported.")
            missing = REQUIRED_COLUMNS.difference(fields)
            if missing:
                raise FileProcessingError(
                    "Missing required columns: " + ", ".join(sorted(missing))
                )
            records = []
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise FileProcessingError("CSV contains an inconsistent row shape.")
                records.append(row)
                if len(records) > MAX_INPUT_ROWS:
                    raise FileProcessingError("Input CSV exceeds the 100000-row limit.")
            if not records:
                raise FileProcessingError("The input CSV has no contact records.")
            return pd.DataFrame(records, columns=fields)
    except (FileNotFoundError, PermissionError, ContactCleanerError):
        raise
    except (OSError, UnicodeError, csv.Error):
        raise FileProcessingError("Unable to read a valid UTF-8 CSV file.") from None


def _validate_output_path(input_path, output_path, overwrite=False):
    source, destination = Path(input_path), Path(output_path)
    if source.resolve() == destination.resolve() or (
        destination.exists()
        and source.exists()
        and os.path.samefile(source, destination)
    ):
        raise FileProcessingError("Input and output must identify different files.")
    if destination.is_symlink():
        raise FileProcessingError("Output symlinks are not supported.")
    if destination.exists() and not overwrite:
        raise FileProcessingError(
            "Output already exists; use --overwrite only after review."
        )


def _write_output_file(frame, output_path, overwrite=False):
    """Publish a complete private file; a failed write never truncates an old output."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(
        prefix=".contact-output-", suffix=".tmp", dir=destination.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as stream:
            frame.to_csv(stream, index=False)
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            if destination.is_symlink():
                raise FileProcessingError("Output symlinks are not supported.")
            os.replace(temporary, destination)
        else:
            # Atomic create-if-absent prevents a competing writer from being overwritten.
            # Unsupported filesystems fail safely rather than falling back to truncation.
            os.link(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="contact-cleaner",
        description="Normalize Iranian mobile-number formats locally; no ownership or consent verification.",
    )
    parser.add_argument("input", help="Private input UTF-8 CSV")
    parser.add_argument("output", help="Private output CSV; must differ from input")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Explicitly replace an existing output after a complete successful write",
    )
    args = parser.parse_args()
    try:
        _validate_output_path(args.input, args.output, args.overwrite)
        contacts = _read_input_file(args.input)
        cleaned, stats = ContactProcessor.clean_contacts_with_stats(contacts)
        _write_output_file(cleaned, args.output, args.overwrite)
        print("Cleaned contacts saved.")
        print(f"Input rows: {stats.input_rows}")
        print(f"Output rows with a valid mobile number: {stats.output_rows}")
        print(
            f"Rows without a valid mobile number: {stats.input_rows - stats.output_rows}"
        )
        print(f"Invalid nonempty phone values: {stats.invalid_phone_values}")
        print(
            f"Duplicate numbers within records: {stats.duplicate_numbers_within_rows}"
        )
        print(
            f"Rows with multiple distinct valid candidates: {stats.rows_with_multiple_candidates}"
        )
        print(
            f"Repeated selected numbers across records: {stats.repeated_selected_numbers}"
        )
        print(f"Output rows without a name: {stats.rows_without_names}")
        for operator, count in sorted(stats.selected_operators.items()):
            print(f"Selected operator group {operator}: {count}")
    except FileNotFoundError:
        print(
            "Error: input file not found or destination unavailable.", file=sys.stderr
        )
        sys.exit(1)
    except PermissionError:
        print("Error: permission denied while accessing local files.", file=sys.stderr)
        sys.exit(1)
    except ContactCleanerError as exc:
        print(f"Contact cleaning error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print(
            "Processing interrupted; no partial output is published.", file=sys.stderr
        )
        sys.exit(130)
    except Exception:
        print(
            "Unable to complete contact processing; private exception details omitted.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
