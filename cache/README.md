# Project-local training cache

This directory is reserved for generated optimization artifacts that must stay out of Git.

- `decoded_images/` contains the Experiment 2 mirror used for Ultralytics `cache='disk'`.
- `benchmarks/` contains temporary benchmark/runtime outputs.
- `runtime/` contains temporary guard files and local run state.

The mirror keeps the source dataset unchanged. Images and labels are linked back to the canonical dataset where possible, and Ultralytics writes decoded `.npy` files beside those mirror image links under `cache/decoded_images/`.
