"""Reproducible synthetic benchmark for the contact-cleaning pipeline.

This benchmark measures the current implementation; it does not assert a scale
claim or a performance SLA. Use it before and after optimization work so changes
are evidence-driven.
"""

from __future__ import annotations

import argparse
import json
from time import perf_counter

import pandas as pd

from contact_processor import ContactProcessor


def build_synthetic_contacts(rows: int) -> pd.DataFrame:
    """Build deterministic synthetic contacts without real personal data."""
    if rows < 1:
        raise ValueError("rows must be positive")

    return pd.DataFrame(
        {
            "First Name": [f"Synthetic{i}" for i in range(rows)],
            "Last Name": ["Contact"] * rows,
            "Phone 1 - Value": [f"0912{i % 10_000_000:07d}" for i in range(rows)],
        }
    )


def run_benchmark(rows: int) -> dict[str, float | int]:
    frame = build_synthetic_contacts(rows)
    started = perf_counter()
    output = ContactProcessor.clean_contacts(frame)
    elapsed_seconds = perf_counter() - started

    return {
        "input_rows": rows,
        "output_rows": len(output),
        "elapsed_seconds": round(elapsed_seconds, 6),
        "rows_per_second": round(rows / elapsed_seconds, 2) if elapsed_seconds else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark synthetic contact normalization")
    parser.add_argument("--rows", type=int, default=10_000)
    args = parser.parse_args()

    result = run_benchmark(args.rows)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
