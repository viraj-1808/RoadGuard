# Training resource monitor
# Logs RAM and GPU usage every 60 seconds, reports peaks and threshold breaches

$outputPath = "experiments/optimization/microtrial_monitoring.csv"
$intervalSec = 60
$maxDurationMin = 30
$maxLoops = [math]::Floor($maxDurationMin * 60 / $intervalSec)

# Ensure output directory exists
New-Item -ItemType Directory -Path (Split-Path $outputPath -Parent) -Force | Out-Null

# CSV header
"timestamp,ram_used_gb,ram_pct,gpu_util_pct,gpu_mem_used,gpu_mem_total" | Out-File -FilePath $outputPath -Encoding UTF8

$ramTotalBytes = (Get-ComputerInfo).CsTotalPhysicalMemory
$ramTotalGB = [math]::Round($ramTotalBytes / 1GB, 2)

$peakRamUsedGB = 0
$peakRamPct = 0
$peakGpuUtil = 0
$breaches = @()

Write-Host "=== MONITORING START ==="
Write-Host "RAM total: $ramTotalGB GB"
Write-Host "Interval: $intervalSec sec, max duration: $maxDurationMin min"
Write-Host "Output: $outputPath"
Write-Host ""

for ($i = 1; $i -le $maxLoops; $i++) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    # RAM
    $freeMem = [math]::Round((Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue, 2)
    $ramUsedGB = [math]::Round(($ramTotalGB - ($freeMem / 1024)), 2)
    $ramPct = [math]::Round(($ramUsedGB / $ramTotalGB) * 100, 2)

    # GPU
    $gpuInfo = nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>$null
    if ($gpuInfo) {
        $parts = $gpuInfo.Split(',').Trim()
        $gpuUtil = [int]$parts[0]
        $gpuMemUsed = [int]$parts[1]
        $gpuMemTotal = [int]$parts[2]
    } else {
        $gpuUtil = 0
        $gpuMemUsed = 0
        $gpuMemTotal = 0
    }

    # Log to CSV
    "$ts,$ramUsedGB,$ramPct,$gpuUtil,$gpuMemUsed,$gpuMemTotal" | Out-File -FilePath $outputPath -Encoding UTF8 -Append

    # Track peaks
    if ($ramUsedGB -gt $peakRamUsedGB) { $peakRamUsedGB = $ramUsedGB }
    if ($ramPct -gt $peakRamPct) { $peakRamPct = $ramPct }
    if ($gpuUtil -gt $peakGpuUtil) { $peakGpuUtil = $gpuUtil }

    # Threshold checks
    if ($ramPct -gt 95) {
        $breaches += "CRITICAL: RAM at $ramPct% (>$ts)"
        Write-Host "!!! RAM CRITICAL: $ramPct% !!!" -ForegroundColor Red
    }
    if ($gpuUtil -eq 0 -and $i -gt 1) {
        $breaches += "WARNING: GPU utilization 0% ($ts)"
        Write-Host "!!! GPU IDLE: 0% utilization !!!" -ForegroundColor Yellow
    }

    Write-Host "[$ts] RAM: $ramUsedGB/$ramTotalGB GB ($ramPct%) | GPU: $gpuUtil% util, $gpuMemUsed/$gpuMemTotal MiB"

    # Check for training process (heuristic: any python training script running)
    $trainProcs = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "train|microtrial|optimize" }
    if ($trainProcs.Count -eq 0 -and $i -gt 1) {
        Write-Host ">>> No training process detected, stopping monitor." -ForegroundColor Cyan
        break
    }

    if ($i -lt $maxLoops) {
        Start-Sleep -Seconds $intervalSec
    }
}

Write-Host ""
Write-Host "=== MONITORING COMPLETE ==="
Write-Host "Peak RAM: $peakRamUsedGB GB ($peakRamPct%)"
Write-Host "Peak GPU utilization: $peakGpuUtil%"
if ($breaches.Count -gt 0) {
    Write-Host "THRESHOLD BREACHES:" -ForegroundColor Red
    $breaches | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
} else {
    Write-Host "No threshold breaches detected."
}