# Benchmark Experiments

This directory contains runtime/performance measurements.

## Purpose

- Record inference latency (per-frame, per-batch)
- Record throughput (frames per second)
- Record memory usage (CPU, GPU)
- Document hardware configurations used for benchmarking
- Compare runtime characteristics of different models

## Benchmark Scenarios

- Static image inference
- Recorded video inference
- Live-camera inference (with bounded buffering)

## Status

- Benchmarks: **NOT STARTED**
- First benchmark: **NOT STARTED**

## Important

Do not commit large benchmark result files (video recordings, charts as binaries). Store metadata and references here. See `docs/MODEL_EVALUATION.md` for evaluation dimensions.