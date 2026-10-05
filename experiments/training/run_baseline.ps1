#!/usr/bin/env pwsh
<#
.SYNOPSIS
    RoadGuard AI - Baseline Training Script for YOLO11s (PowerShell)

.DESCRIPTION
    Runs YOLO11s baseline training on the RDD2022 India dataset with:
    - Model: YOLO11s pretrained
    - Dataset: experiments/dataset/yolo_rdd2022_india/data.yaml
    - Image size: 720
    - Batch size: 16 (safe for RTX 4050, ~5.5GB peak)
    - Epochs: 100 (with early stopping based on validation mAP)
    - Seed: 42
    - Device: 0 (GPU)
    - Optimizer: auto
    - Workers: 0 (minimal)
    - Pretrained: True
    - Resume: False
    - Patience: 50 (early stopping)
    - Save: True
    - Save_period: 1
    - Project: experiments/training
    - Name: yol11s_dataset_v2_split_v2

.PARAMETER ConfigPath
    Path to the baseline configuration YAML file
    Default: experiments/training/baseline_config.yaml

.EXAMPLE
    .\run_baseline.ps1

.EXAMPLE
    .\run_baseline.ps1 -ConfigPath "experiments/training/baseline_config.yaml"
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = "experiments/training/baseline_config.yaml"
)

Write-Host ""
Write-Host "================================================================================"
Write-Host "RoadGuard AI - Baseline Training: YOLO11s on RDD2022 India Dataset"
Write-Host "================================================================================"
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Python detected: $pythonVersion"
} catch {
    Write-Error "[ERROR] Python not found in PATH. Please install Python 3.8+"
    exit 1
}

# Check if baseline config exists
if (-not (Test-Path $ConfigPath)) {
    Write-Error "[ERROR] Baseline config not found: $ConfigPath"
    exit 1
}

Write-Host "[INFO] Using baseline configuration: $ConfigPath"
Write-Host ""

# Run training using the baseline config file
python -m ultralytics train --cfg $ConfigPath

$exitCode = $LASTEXITCODE
if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "================================================================================"
    Write-Host "Training completed successfully!"
    Write-Host "Results saved to: experiments/training/yol11s_dataset_v2_split_v2"
    Write-Host "================================================================================"
} else {
    Write-Error "[ERROR] Training failed with exit code $exitCode"
}

exit $exitCode