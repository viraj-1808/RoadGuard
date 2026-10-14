# Dataloader Benchmark Report

## 1. Environment

- **Python**: 3.12.10
- **PyTorch**: 2.14.0+cu126
- **CUDA**: 12.6
- **Ultralytics**: 8.4.138
- **GPU**: NVIDIA GeForce RTX 4050 Laptop GPU
- **CPU cores**: 12
- **RAM**: 15.65 GB
- **Dataset**: data.yaml
- **Checkpoint**: epoch53.pt
- **Device index**: 0

## 2. Benchmark Methodology

- Each configuration: 10 warmup batches, 100 measurement batches
- Batch: 16, Image size: 720 (internally adjusted to 736 by Ultralytics)
- Measure: CPU loading time, host-to-GPU transfer, RAM usage, GPU memory
- All configurations preserve dataset, batch size, imgsz, seed, deterministic

## 3. Configuration Matrix

| workers | prefetch_factor | Description |
|--------|-----------------|-------------|
| 0 | None | ✓ valid |
| 2 | 1 | ✓ valid |
| 2 | 2 | ✓ valid |
| 2 | 4 | ✓ valid |
| 4 | 1 | ✓ valid |
| 4 | 2 | ✓ valid |
| 4 | 4 | ✓ valid |
| 6 | 1 | ✓ valid |
| 6 | 2 | ✓ valid |
| 6 | 4 | ✓ valid |
| 8 | 1 | ✓ valid |
| 8 | 2 | ✓ valid |
| 8 | 4 | ✓ valid |

## 4. Raw Measurements

| workers | prefetch | mean_ms | median_ms | p95_ms | batches/s | samples/s |
|--------|----------|---------|-----------|--------|-----------|-----------|
| 0 | None | 562.98 | 551.29 | 705.36 | 1.78 | 28.42 |
| 2 | 1 | 282.83 | 295.41 | 635.63 | 3.54 | 56.57 |
| 2 | 2 | 244.45 | 250.83 | 589.23 | 4.09 | 65.45 |
| 2 | 4 | 256.45 | 172.68 | 634.19 | 3.90 | 62.39 |
| 4 | 1 | 153.41 | 132.82 | 466.86 | 6.52 | 104.30 |
| 4 | 2 | 136.55 | 0.88 | 582.69 | 7.32 | 117.18 |
| 4 | 4 | 140.64 | 0.66 | 655.00 | 7.11 | 113.77 |
| 6 | 1 | 123.53 | 33.49 | 490.74 | 8.10 | 129.53 |
| 6 | 2 | 111.38 | 1.17 | 553.62 | 8.98 | 143.65 |
| 6 | 4 | 121.87 | 0.81 | 789.44 | 8.21 | 131.29 |
| 8 | 1 | 118.99 | 16.07 | 430.49 | 8.40 | 134.46 |
| 8 | 2 | 115.89 | 1.00 | 556.82 | 8.63 | 138.06 |
| 8 | 4 | 104.19 | 0.92 | 722.28 | 9.60 | 153.56 |

## 5. RAM Comparison

| workers | prefetch | peak_RAM% | peak_RAM_GB | peak_process_GB | peak_child_GB |
|--------|----------|-----------|-------------|-----------------|----------------|
| 0 | None | 83.6% | 13.08 | 1.01 | 0.02 |
| 2 | 1 | 88.0% | 13.78 | 0.98 | 2.30 |
| 2 | 2 | 87.6% | 13.71 | 0.89 | 2.24 |
| 2 | 4 | 87.5% | 13.69 | 0.90 | 2.25 |
| 4 | 1 | 96.5% | 15.11 | 0.90 | 4.25 |
| 4 | 2 | 96.1% | 15.04 | 0.93 | 4.29 |
| 4 | 4 | 94.6% | 14.80 | 0.97 | 4.27 |
| 6 | 1 | 99.6% | 15.58 | 0.99 | 5.74 |
| 6 | 2 | 99.7% | 15.60 | 0.97 | 6.46 |
| 6 | 4 | 98.5% | 15.42 | 0.99 | 6.40 |
| 8 | 1 | 99.9% | 15.63 | 0.97 | 7.62 |
| 8 | 2 | 100.0% | 15.64 | 0.75 | 8.29 |
| 8 | 4 | 94.6% | 14.80 | 0.61 | 8.40 |

## 6. Throughput Comparison

| workers | prefetch | batches/sec | samples/sec |
|--------|----------|-------------|-------------|
| 8 | 4 | 9.60 | 153.56 |
| 6 | 2 | 8.98 | 143.65 |
| 8 | 2 | 8.63 | 138.06 |
| 8 | 1 | 8.40 | 134.46 |
| 6 | 4 | 8.21 | 131.29 |
| 6 | 1 | 8.10 | 129.53 |
| 4 | 2 | 7.32 | 117.18 |
| 4 | 4 | 7.11 | 113.77 |
| 4 | 1 | 6.52 | 104.30 |
| 2 | 2 | 4.09 | 65.45 |

## 7. Pareto Analysis

- **Fastest configuration**: workers=8, prefetch_factor=4
  - Throughput: 9.60 batches/sec
  - Mean latency: 104.19 ms/batch
  - RAM: 14.80 GB (94.6%)
  - GPU allocated: 190 MB

- **Lowest RAM usage**: workers=0, prefetch_factor=None
  - RAM: 13.08 GB (83.6%)

- **Best speed/RAM tradeoff**: workers=8, prefetch_factor=4
  - Throughput: 9.60 batches/sec
  - RAM: 14.80 GB (94.6%)
  - Ratio (RAM%/throughput): 9.8565

## 8. Recommended Production Configuration

**workers=8, prefetch_factor=4**
- Recommended despite higher RAM usage (94.6%) due to no viable alternatives below 50%

## 9. Rejected Configurations and Why

No configurations failed.

## 10. Limitations

- Benchmark measures only CPU loading + GPU transfer, not actual training
- Prefetching behavior differs slightly from production (no num_workers heuristic limiting)
- Single GPU only tested
- Results may vary with system load
