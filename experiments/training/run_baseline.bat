@echo off
REM =============================================================================
REM RoadGuard AI - Baseline Training Script for YOLO11s
REM =============================================================================
REM Model: YOLO11s pretrained
REM Dataset: experiments/dataset/yolo_rdd2022_india/data.yaml
REM Configuration: baseline_config.yaml
REM =============================================================================

echo.
echo ================================================================================
echo RoadGuard AI - Baseline Training: YOLO11s on RDD2022 India Dataset
echo ================================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH. Please install Python 3.8+
    exit /b 1
)

REM Check if baseline config exists
if not exist "experiments\training\baseline_config.yaml" (
    echo [ERROR] Baseline config not found: experiments\training\baseline_config.yaml
    exit /b 1
)

echo [INFO] Using baseline configuration: experiments\training\baseline_config.yaml
echo.

REM Run training using the baseline config file
python -m ultralytics train --cfg experiments\training\baseline_config.yaml

echo.
echo ================================================================================
echo Training completed!
echo Results saved to: experiments\training\yol11s_dataset_v2_split_v2
echo ================================================================================