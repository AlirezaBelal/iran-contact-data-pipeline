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

## Measured safety/quality instrumentation cost (2026-10-24)

Three fresh-process runs per size, same local Python 3.12 / pandas environment,
using only the benchmark's synthetic generator. Times are medians for core
processing, excluding input generation and CSV I/O. Baseline is `4d935443`.

| Rows | Baseline seconds | Instrumented seconds | Baseline / instrumented peak process MiB |
|---|---:|---:|---:|
| 1,000 | 0.005055 | 0.006370 | 65.92 / 66.64 |
| 10,000 | 0.060239 | 0.069751 | 70.24 / 71.50 |
| 100,000 | 0.541971 | 0.627548 | 111.99 / 117.06 |

Quality counters and the set used to report repeated selected numbers add overhead
(about 16% time at 100,000 rows in this measurement). This is not a performance
optimization claim. Peak process memory is Linux `ru_maxrss`, including interpreter,
pandas, generated input and output; it is not incremental algorithm-only memory.
No timing threshold or change of DataFrame framework is justified by these results.

The static preview is generated once at build time from five synthetic rows. It
does not change the core algorithm or introduce a browser/backend processing
benchmark; the measurements above still describe the instrumented Python core.
