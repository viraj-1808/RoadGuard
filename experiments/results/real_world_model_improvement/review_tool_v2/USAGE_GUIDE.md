# USAGE_GUIDE.md

# RoadGuard AI - Review Tool v2

## Overview

This guide documents the improved offline human-review workflow for RoadGuard AI annotations. The Review Tool v2 provides a comprehensive, reliable interface for reviewing road-damage detections, drawing ground truth annotations, and exporting verified annotations.

## System Requirements

### Minimum Requirements
- Web browser with JavaScript support (Chrome, Firefox, Edge, Safari)
- 4 GB RAM minimum (8 GB recommended for 4K images)
- 50 MB free disk space for the HTML file
- Local file access (not a web server)

### Recommended Setup
- Desktop browser (not mobile)
- 1920×1080 resolution or higher
- Disable browser extensions that block local files (some ad-blockers)
- Allow local file access if prompted

## Launching the Tool

### Method 1: Double-Click HTML File
1. Navigate to: `experiments/results/real_world_model_improvement/review_tool_v2/`
2. Double-click `review_template_v2.html`
3. If prompted, allow local file access

### Method 2: Open in Browser
1. Open your web browser
2. Go to: `file:///C:/Users/viraj/Code_files/Github/RoadGuard AI/experiments/results/real_world_model_improvement/review_tool_v2/review_template_v2.html`
3. Accept local file permissions if requested

### Method 3: Run from Terminal (Optional)
```bash
# Navigate to the project root
cd "C:\Users\viraj\Code_files\Github\RoadGuard AI"

# Start a simple HTTP server for testing (not required for offline use)
# This is only for development/testing
python -m http.server 8000 --bind 127.0.0.1

# Then open: http://127.0.0.1:8000/experiments/results/real_world_model_improvement/review_tool_v2/review_template_v2.html
```

## Interface Overview

### Main Components

1. **Header** - Image counter and status selection
2. **Image Info Panel** - Filename, dimensions, and split information
3. **Canvas Area** - Main image with overlays for predictions and ground truth
4. **Prediction Panels** - Display epoch 72 and original model predictions
5. **Drawing Controls** - Toggle drawing mode and clear boxes
6. **Export/Import Tools** - Save current, export all, import annotations
7. **Class Selector** - Choose defect class for drawing boxes
8. **Toast Notifications** - Success/error messages

### Key Features

#### Drawing Boxes
1. Click **"Draw Mode (D)"** or press **D** to activate drawing mode
2. Click and drag on the image to create a bounding box
3. Select class from the **Class** dropdown
4. Box appears in green on the canvas
5. Release mouse to finalize box

#### Box Editing
- **Delete**: Hover over a box → × button appears → click to delete
- **Move**: Click inside a box → drag to reposition
- **Resize**: Hover over edges/corners → drag to resize

#### Navigation
- **Arrow Keys**: Navigate between images
- **Progress Indicator**: Shows current image number and status
- **Status Buttons**: Set image status (see below)

#### Status Management
- **Confirmed Positive**: Image contains verified defects
- **Confirmed Negative**: Image is clean (no defects)
- **Uncertain**: Human inspection needed but inconclusive

## Workflow Guide

### Initial Setup
1. Launch the tool using one of the methods above
2. Wait for metadata to load (all 18 images)
3. Review the image count in the progress indicator

### Reviewing Images

#### For Each Image:

1. **Review Information**
   - Filename and dimensions shown in info panel
   - Status buttons at top (default: NEEDS_HUMAN_REVIEW)
   - Prediction panels show model outputs (red = epoch72, blue = original)

2. **Understand Predictions**
   - Red boxes (epoch72): Model's 72nd epoch predictions
   - Blue boxes (original): Baseline model predictions
   - Hover predictions in panels for details (confidence, bbox)

3. **Drawing Ground Truth**
   - Click **"Draw Mode (D)"** or press **D**
   - Click and drag on the image to create box
   - Select class from dropdown (4 classes available):
     - **0 - longitudinal_crack** (vertical cracks)
     - **1 - transverse_crack** (horizontal cracks)
     - **2 - alligator_crack** (crocodile-like cracks)
     - **3 - pothole** (depressions in road)
   - Box appears in green with label

4. **Verify and Refine**
   - Use mouse wheel to **zoom** in/out
   - Hover over existing boxes to **edit** (move, resize, delete)
   - Use **Clear Boxes** to remove all boxes for current image

5. **Set Status**
   - Click one of three status buttons:
     - **Confirmed Positive**: Contains verified defects
     - **Confirmed Negative**: Image is clean (no defects)
     - **Uncertain**: Indeterminate after inspection

6. **Save Decisions**
   - Click **"Save Current"** - saves to browser localStorage
   - **Data persists** across page refreshes and browser closure

### After Completing All Images

1. **Export Annotations**
   - Click **"Export All"** button
   - Choose save location for `ground_truth_review_v2.json`
   - Tool validates all boxes before export (reports errors if invalid)

2. **Export YOLO Labels**
   - Click **"Export YOLO Labels"** button
   - Downloads individual `.txt` files for each **CONFIRMED_POSITIVE** image
   - Files match `annotations_v1/confirmed/` format

3. **Import Previous Work** (optional)
   - Click **"Import Annotations"** button
   - Select previously exported `ground_truth_review_v2.json`
   - All boxes and statuses are restored

### Validation and Quality Control

#### Automatic Validation
- **Coordinate Validation**: Boxes within image bounds, positive dimensions
- **Class Validation**: Valid class IDs (0-3), correct name mapping
- **Negative Handling**: CONFIRMED_NEGATIVE images must have empty boxes

#### Error Messages
- **Red toast** for validation errors (must fix before export)
- **Yellow warning** for non-critical issues (can proceed with export)

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **D** | Toggle draw mode |
| **Delete** | Delete selected box |
| **← / →** | Navigate to previous/next image |
| **Esc** | Cancel current operation |

### Troubleshooting

#### Common Issues

1. **No image displayed**
   - Check browser compatibility (Chrome, Firefox, Edge recommended)
   - Ensure file:// protocol is allowed
   - Try opening with a different browser

2. **Boxes not saving**
   - Refresh the page - data should auto-load from localStorage
   - Check browser storage limits (clear cache if needed)
   - Try a different browser profile

3. **Export fails**
   - Check for validation errors (red toast messages)
   - Ensure all required fields are filled
   - Try exporting one image at a time

4. **Import fails**
   - Ensure JSON file is from v2.0 format
   - Check file is not corrupted
   - Try importing to a fresh browser session

#### File Access Issues

If the browser blocks local file access:
- **Chrome/Edge**: Go to `chrome://settings/cookies` and allow local storage
- **Firefox**: Go to `about:preferences#privacy` and allow local storage
- **Safari**: Go to Safari > Preferences > Security and allow local files

## Best Practices

### For Human Reviewers
1. **Be Conservative**: Only mark defects you can clearly see
2. **Tight Boxes**: Fit boxes closely around defect regions
3. **Class Accuracy**: Use correct class based on defect type
4. **Multiple Defects**: Draw separate box for each distinct defect
5. **No Defects**: For clean images, set **CONFIRMED_NEGATIVE** status

### For Quality Assurance
1. **Always validate** before exporting
2. **Check negative handling** - CONFIRMED_NEGATIVE images must be empty
3. **Verify YOLO exports** match expected format
4. **Maintain backup** of exported JSON files
5. **Document ambiguous cases** for future reference

### Performance Tips
1. **For high-resolution images** (4K):
   - Use browser zoom (Ctrl+Scroll) to inspect details
   - Consider focusing on most likely defect areas first

2. **For portrait orientation images**:
   - Review as displayed (may require mental rotation)
   - Pay attention to vertical defects

3. **For low-confidence predictions**:
   - Treat as hints only
   - Verify visually with caution

## Maintenance and Updates

### Updating the Tool
1. Replace `review_template_v2.html` with new version
2. Existing data in localStorage will automatically load
3. New images added to metadata will be available

### Backing Up Reviews
1. Export frequently using **"Export All"**
2. Store JSON files in version-controlled directory
3. Use validator.py for automated validation

## Files Included

- `review_template_v2.html` - Main review interface
- `validator.py` - Annotation validation script
- `test_validator.py` - Unit tests for validation
- `README.md` - This guide
- `CONTRIBUTING.md` - Development guidelines

## Technical Specifications

### File Format
- **Single HTML file**: All CSS/JS inline for offline use
- **No external dependencies**: Works completely offline
- **Responsive design**: Adapts to different screen sizes

### Data Storage
- **LocalStorage**: Persistent storage of annotations and status
- **File exports**: JSON format for human readability and tooling
- **YOLO format**: Standardized format for model training

### Security
- **Local execution**: No network calls during normal operation
- **Read-only access**: Only writes to localStorage
- **No authentication**: Open access for human reviewers

## Contact and Support

For questions or issues:
1. Check the validator output for specific error messages
2. Review `validator.py` source code for debugging
3. Run unit tests: `python -m pytest test_validator.py -v`
4. Consult the RoadGuard AI annotation guidelines
5. Contact the ML team for ambiguous cases

---

**Version**: 2.0.0
**Last Updated**: 2026-10-11
**License**: Internal use only

This tool is part of the RoadGuard AI model improvement pipeline and is intended for human annotation of real-world road damage images.
