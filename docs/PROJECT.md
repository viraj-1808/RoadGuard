## Purpose - Why the project exists

To provide an automated, scalable system for detecting potholes in road imagery and converting those detections into timely maintenance reports, thereby improving road safety and maintenance efficiency.

## Core problem - Pothole object detection

Accurately identifying potholes in varying lighting, weather, and road surface conditions from monocular camera inputs, with sufficient precision to trigger maintenance workflows.

## Core technical contribution - Training and validating a pothole detection model

Developing a dataset-specific object detection model (e.g., YOLO, Faster R-CNN) that achieves high recall and precision for potholes, accompanied by rigorous evaluation protocols and error analysis. The project's core contribution is the training and evaluation pipeline itself.

## Target operation - image, recorded video, live camera

The system must process static images, offline video files, and real-time video streams from vehicle-mounted or fixed cameras.

## Application - Pothole event generation and reporting

Individual detections are aggregated over time and space to form pothole events, which are stored, queried, and visualized via a reporting dashboard for municipal maintenance crews.

## Scope

- Pothole detection model training and evaluation
- Inference pipeline for image, video, and live camera
- Temporal detection tracking and pothole event generation
- Backend API for event persistence and reporting
- Frontend dashboard for visualization and interaction
- Integration contracts between components
- Experiment tracking and benchmarking

## Current non-goals

Do NOT currently claim:

- Precise 3D pothole measurement (volume or depth)
- Scientifically validated pothole depth estimation from monocular imagery
- Exact pothole GPS localization (beyond coarse geotagging)
- Severity prediction (e.g., immediate vs. scheduled repair)
- Distributed multi-region deployment (single-instance design for now)

These are open/deferred unless later research explicitly adds them.

## Current status

Clearly separate:

- **RESEARCH COMPLETE**: Literature review, dataset surveys, and architecture discovery finished. Empirical experiments not started.
- **ARCHITECTURE PROVISIONALLY DEFINED**: Component boundaries and contracts drafted. Status labels and boundary principles are defined.
- **IMPLEMENTATION NOT STARTED**: No production code written; only skeleton directories and placeholder files exist.
- **EMPIRICAL EXPERIMENTS NOT STARTED**: No training, evaluation, or benchmarking experiments have been run. Candidate models and dataset audit are at the planning stage.