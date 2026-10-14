# Human Review Instructions - RoadGuard AI

## Overview
This package contains 15 images flagged as **NEEDS_HUMAN_REVIEW** from the model verification pipeline. These images require human annotation to establish ground truth for model evaluation and improvement.

## Images Requiring Review
| Image | Dimensions | Split | Key Issue |
|-------|------------|-------|-----------|
| road013.jpg | 1200x900 | train | No detections; may be clean or defects below threshold |
| road016.jpg | 4096x3072 | holdout | Very high resolution; small defects may be missed at 720 imgsz |
| road017.jpg | 3072x4096 | val | Portrait + high res; possible missed defects |
| road019.jpg | 3072x4096 | holdout | High res portrait; no detections |
| road020.jpg | 960x1280 | val | Portrait orientation; no detections |
| road023.jpg | 3072x4096 | holdout | Epoch72 shows 5 low-conf detections; original had none |
| road024.jpg | 960x1280 | train | Portrait; no detections |
| road030.jpg | 3072x4096 | train | Epoch72 shows 2 low-conf alligator_crack; original had none |
| road032.jpg | 4096x3072 | val | No detections on 4K image |
| road034.jpg | 960x1280 | train | Epoch72 shows 3 low-conf detections (2 alligator, 1 pothole); original had none |
| road035.jpg | 4096x3072 | train | No detections on 4K image |
| road036.jpg | 960x1280 | train | Portrait; no detections |
| road037.jpg | 4096x3072 | holdout | No detections on 4K image |
| road038.jpg | 1280x960 | holdout | No detections |
| road039.jpg | 3072x4096 | holdout | No detections on 4K portrait |

## Review Process

### 1. Open the Review Interface
Open `review_template.html` in a modern web browser (Chrome, Firefox, Edge).

### 2. Navigation
- Use **Previous/Next** buttons or **Left/Right arrow keys** to navigate between images
- Current position shown in header (e.g., "Image 1 of 15")

### 3. Understanding the Display
Each image shows:
- **Original image** (centered, scaled to fit)
- **Epoch 72 Predictions** (red boxes) - Model predictions after 72 epochs of training
- **Original Model Predictions** (blue boxes) - Baseline model predictions
- **Metadata panel** with dimensions, split, error analysis notes, and review reason

### 4. Drawing Ground Truth Boxes
1. Press **`D` key** to toggle drawing mode (indicator appears bottom-right)
2. **Click and drag** on the image to draw a bounding box
3. Release mouse → **Enter defect class** when prompted:
   - `alligator_crack`
   - `longitudinal_crack`
   - `transverse_crack`
   - `pothole`
4. Box appears in green with label
5. Repeat for all visible defects

### 5. Saving Annotations
- **Save Annotations** - Downloads JSON for current image only
- **Clear Boxes** - Removes all drawn boxes for current image
- **Export All Annotations** - Downloads combined JSON for all annotated images

### 6. Annotation Guidelines
- **Be conservative**: Only mark defects you can clearly see
- **Tight boxes**: Fit boxes closely around defect regions
- **Class accuracy**: Use correct defect class
- **Multiple defects**: Draw separate box for each distinct defect
- **No defects**: If image is truly clean, leave empty and note in export

### 7. Special Considerations
- **High-res images** (4096x3072, 3072x4096): Zoom in (browser zoom) to inspect details
- **Portrait images**: May need rotation consideration; annotate as displayed
- **Low-confidence model predictions**: Treat as hints only; verify visually
- **Epoch72 vs Original discrepancies**: Pay attention where models disagree

## Output Format
Exported JSON structure:
```json
{
  "review_images/road013.jpg": [
    {"x1": 100, "y1": 200, "x2": 400, "y2": 500, "class": "alligator_crack"},
    {"x1": 600, "y1": 100, "x2": 800, "y2": 300, "class": "pothole"}
  ],
  "review_images/road016.jpg": [...]
}
```
Coordinates are in **original image pixel space** (not scaled display coordinates).

## After Review
1. Collect all exported JSON files
2. Merge into single `ground_truth_annotations.json`
3. Place in `experiments/results/real_world_model_improvement/human_review_package/`
4. Run evaluation script to compute metrics against model predictions

## Contact
For questions about annotation criteria or ambiguous cases, refer to the RoadGuard AI annotation guidelines document or contact the ML team.