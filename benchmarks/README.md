# Reproducible Performance Benchmark

This directory provides a deterministic, synthetic benchmark for the contact-normalization core.

The benchmark exists to support **evidence-driven performance changes**. It does not claim that a particular laptop, CI runner, or deployment will process a fixed number of contacts per second, and it is not a production-scale SLA.

## Run locally

From an installed development checkout:

```bash
python benchmarks/benchmark_pipeline.py --rows 10000
python benchmarks/benchmark_pipeline.py --rows 100000
```

The command emits machine-readable JSON containing:

- `input_rows`
- `output_rows`
- `elapsed_seconds`
- `rows_per_second`

All generated contacts are synthetic. No real names, phone numbers, or operational datasets are required.

## How to use the result

Use the same environment and row count when comparing two implementations. Compare repeated runs rather than treating a single wall-clock measurement as authoritative.

The benchmark is useful for questions such as:

- Did a normalization refactor materially reduce per-row overhead?
- Did a correctness or validation change cause an obvious performance regression?
- Is a proposed optimization worth its added complexity?

It should **not** be used to infer production throughput without separately measuring I/O, file sizes, deployment hardware, concurrency, and downstream systems.

## Current implementation note

`ContactProcessor.clean_contacts()` iterates records with `DataFrame.itertuples()` and a precomputed column-position map rather than `DataFrame.iterrows()`. The public behavior remains covered by the normal test suite, while CI also executes a benchmark smoke run to ensure the benchmark stays runnable.
