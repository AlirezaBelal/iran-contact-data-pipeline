# Benchmarks

The repository includes a deterministic synthetic benchmark so performance changes can be measured instead of inferred from dataset-size claims.

The benchmark uses generated names and Iranian mobile-number-shaped test values. It does **not** use real contact data.

## Run

```bash
python benchmarks/benchmark_pipeline.py --rows 10000
python benchmarks/benchmark_pipeline.py --rows 100000
python benchmarks/benchmark_pipeline.py --rows 1000000
```

Output is JSON with input rows, output rows, elapsed seconds, and observed rows per second.

## Interpretation

The current implementation uses row-wise pandas processing. Benchmark results describe the machine and dependency versions on which they were produced; they are not a throughput SLA.

Use the same synthetic row counts before and after a vectorization, chunking, Polars, or PyArrow experiment. Keep an optimization only when it preserves normalization/selection behavior and demonstrates a meaningful measured improvement.

CI runs a 1,000-row benchmark smoke test to keep the benchmark executable, but deliberately does not enforce a wall-clock threshold because shared GitHub runners are not stable benchmark infrastructure.
