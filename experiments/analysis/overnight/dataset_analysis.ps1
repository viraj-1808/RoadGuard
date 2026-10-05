# Dataset Analysis Script for YOLO format
$yoloBase = "experiments/dataset/yolo_rdd2022_india"

# Class mapping from validation report:
# 0 = longitudinal_crack (D00 + D01)
# 1 = transverse_crack (D10 + D11)  
# 2 = alligator_crack (D20)
# 3 = pothole (D40)

$trainLabelsDir = Join-Path $yoloBase "labels/train"
$valLabelsDir = Join-Path $yoloBase "labels/val"
$testLabelsDir = Join-Path $yoloBase "labels/test"

function Analyze-Labels {
    param([string]$dir, [string]$setName)
    
    $files = Get-ChildItem -Path $dir -Filter *.txt -File
    if (-not $files) {
        Write-Host "No label files found in $dir"
        return
    }
    
    $totalImages = $files.Count
    $imagesWithPothole = 0
    $imagesWithoutPothole = 0
    $imagesOnlyPothole = 0
    $imagesPotholePlusOther = 0
    $totalObjects = 0
    $potholeObjects = 0
    $smallObjects = 0  # width * height < 0.1
    
    foreach ($file in $files) {
        $content = Get-Content $file.FullName
        $hasPothole = $false
        $hasOther = $false
        $objectCount = 0
        
        foreach ($line in $content) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            
            $parts = $line -split ' '
            if ($parts.Length -lt 5) { continue }
            
            $classId = [int]$parts[0]
            $xCenter = [double]$parts[1]
            $yCenter = [double]$parts[2]
            $width = [double]$parts[3]
            $height = [double]$parts[4]
            
            $objectCount++
            $totalObjects++
            
            if ($classId -eq 3) {  # pothole
                $hasPothole = $true
                $potholeObjects++
                
                # Check if small object (<10% of image area)
                $area = $width * $height
                if ($area -lt 0.1) {
                    $smallObjects++
                }
            } else {
                $hasOther = $true
            }
        }
        
        if ($hasPothole) {
            $imagesWithPothole++
            if ($hasOther) {
                $imagesPotholePlusOther++
            } else {
                $imagesOnlyPothole++
            }
        } else {
            $imagesWithoutPothole++
        }
    }
    
    Write-Host "`n=== $setName Set Analysis ===`n"
    Write-Host "Total images: $totalImages"
    Write-Host "Images with pothole: $imagesWithPothole"
    Write-Host "Images without pothole: $imagesWithoutPothole"
    Write-Host "Images with only pothole: $imagesOnlyPothole"
    Write-Host "Images with pothole + other damage: $imagesPotholePlusOther"
    Write-Host "Total objects: $totalObjects"
    Write-Host "Pothole objects: $potholeObjects"
    if ($totalObjects -gt 0) {
        Write-Host "Pothole object percentage: {0:P1}" -f ($potholeObjects / $totalObjects)
        Write-Host "Small objects (<10% image): $smallObjects ({0:P1})" -f ($smallObjects / $totalObjects)
    }
}

# Analyze each set
Analyze-Labels $trainLabelsDir "TRAIN"
Analyze-Labels $valLabelsDir "VALIDATION"
Analyze-Labels $testLabelsDir "TEST"

# Also check for empty annotations (natural background/negative images)
function Check-EmptyAnnotations {
    param([string]$dir, [string]$setName)
    
    $files = Get-ChildItem -Path $dir -Filter *.txt -File
    $emptyCount = 0
    
    foreach ($file in $files) {
        $content = Get-Content $file.FullName
        $nonEmpty = $false
        foreach ($line in $content) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                $nonEmpty = $true
                break
            }
        }
        if (-not $nonEmpty) {
            $emptyCount++
        }
    }
    
    Write-Host "`nEmpty annotation check for $setName: $emptyCount/$($files.Count) images"
}

Check-EmptyAnnotations $trainLabelsDir "TRAIN"
Check-EmptyAnnotations $valLabelsDir "VALIDATION" 
Check-EmptyAnnotations $testLabelsDir "TEST"