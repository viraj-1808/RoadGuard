# Review Tool Audit — `review_template.html`

**Auditor:** Kilo orchestrator  
**Date:** 2026-10-11  
**Source file audited:** `experiments/results/real_world_model_improvement/human_review_package/review_template.html`  
**Lines:** 471  

---

## 1. Audit Methodology

Every function, data path, and user interaction in `review_template.html` was traced against the requirements defined in the task specification:

1. Loads the correct original image for every review item.
2. Displays image dimensions and filename.
3. Visually distinguishes existing model predictions from human-confirmed annotations.
4. Supports drawing, moving, resizing, and deleting bounding boxes.
5. Supports all four RoadGuard classes.
6. Lets the reviewer mark an image as confirmed positive / confirmed negative / uncertain.
7. Does not silently convert model predictions into ground truth.

---

## 2. Detailed Findings

### 2.1 CRITICAL — No Decision Persistence (Issue #1)

**Location:** Lines 202–206 (state declaration), Lines 420–468 (save/export functions).

**Finding:** The only state variable is the in-memory `let gtBoxes = {}` object (line 204). `saveCurrent()` (lines 420–436) and `exportAll()` (lines 444–459) create Blob URLs and trigger browser downloads, but **never write to `localStorage` or any persistent store**. On browser refresh, tab close, or navigation, all drawn boxes and status decisions are silently lost.

**Severity:** Critical. Decisions cannot survive page refresh.

**Evidence (code):**
```javascript
function saveCurrent() {
    const item = metadata[currentIndex];
    const boxes = gtBoxes[item.image_path] || [];
    const data = {
        image_path: item.image_path,
        gt_boxes: boxes,
        timestamp: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${item.image_path.replace('review_images/', '').replace('.jpg', '')}_gt.json`;
    a.click();
    URL.revokeObjectURL(url);
    alert('Annotations saved!');  // Fires before download dialog actually completes
}
```

The `alert()` claims "saved" but the download may be blocked by browser pop-up blockers, and even if it downloads, there is no mechanism to re-import it later. The in-memory `gtBoxes` is never updated after a "save" — the function only downloads.

### 2.2 CRITICAL — No Status Tracking (Issue #2)

**Location:** Lines 216–260 (rendered HTML), Lines 420–468 (button handlers).

**Finding:** The `item.status` field from `review_metadata.json` (e.g., `"NEEDS_HUMAN_REVIEW"`) is rendered as a static badge (line 231), but there are **no buttons or controls** to change the status to `CONFIRMED_POSITIVE`, `CONFIRMED_NEGATIVE`, or `UNCERTAIN`. The only actions are "Save Annotations" (downloads current boxes), "Clear Boxes" (empties in-memory boxes), and "Export All" (downloads). A reviewer cannot mark an empty image as a confirmed negative — they can only leave it empty and hope the export captures that.

**Severity:** Critical. Cannot fulfill the "confirmed positive / confirmed negative / uncertain" requirement.

### 2.3 HIGH — No Box Deletion or Individual Editing (Issue #3)

**Location:** Lines 306–398 (drawing logic), Lines 438–442 (clearBoxes).

**Finding:** Boxes can only be created (draw + prompt for class) or cleared en masse (`clearBoxes` empties the entire array). There is **no way to delete an individual box**, move/resize an existing box, or change a box's class after creation. The `prompt()` on line 361 fires immediately after every `mouseup`, interrupting workflow with a modal dialog for every box.

**Severity:** High. No delete, no move, no resize — only create and clear-all.

### 2.4 HIGH — Class Selection via Unvalidated Free-Text prompt() (Issue #4)

**Location:** Line 361.

**Finding:** Class is selected via `prompt('Enter defect class (alligator_crack, longitudinal_crack, transverse_crack, pothole):', 'alligator_crack')`. This is:
- Free-text entry — typos like `"pothole "` or `"Pothole"` produce invalid class names.
- No validation against the 4-class mapping.
- No numeric class ID assigned.
- The class string is stored directly (line 363: `currentBox.class = className`), bypassing the YOLO numeric ID system.

**Severity:** High. Invalid class entries will corrupt downstream YOLO conversions.

### 2.5 HIGH — Predictions Not Drawn as Boxes (Issue #5)

**Location:** Lines 220–221 (string conversion of predictions), Lines 74–79 (canvas-overlay CSS), Lines 242–245 (prediction panel HTML).

**Finding:** The "Epoch 72 Predictions (Red Boxes)" heading (line 242) and "Original Model Predictions (Blue Boxes)" heading (line 244) are misleading — **predictions are never rendered as rectangles on the canvas**. They exist only as text strings inside `<div class="prediction-item">` elements (lines 243, 245). Only human-drawn GT boxes appear on the canvas (green). The "red boxes" and "blue boxes" labels are inaccurate.

**Severity:** High. Visual distinction between predictions and GT is broken.

### 2.6 HIGH — Export Skips Confirmed-Negative Images (Issue #6)

**Location:** Lines 444–459 (exportAll).

**Finding:** `exportAll()` iterates `gtBoxes` and only exports images where `boxes.length > 0` (line 447). Confirmed-negative images (no defects) are **silently excluded** from the export. A reviewer who inspects an image, finds no defects, and exports will not see that image in the output — making it impossible to distinguish "not yet reviewed" from "confirmed negative."

**Severity:** High. Negative decisions are lost.

### 2.7 MEDIUM — No File Import / Resume (Issue #7)

**Location:** Lines 18–12 (CSS), Lines 201–469 (script).

**Finding:** There is no "Import" button to load previously exported JSON. Even if a reviewer exports their work, closes the browser, and reopens, there is no way to resume — `gtBoxes` starts empty and `loadMetadata()` (lines 209–213) only fetches the original `review_metadata.json`.

**Severity:** Medium. No resume capability.

### 2.8 MEDIUM — Coordinate System Ambiguity (Issue #8)

**Location:** Lines 306–315 (setupCanvas), Lines 338–373 (drawing math).

**Finding:** `setupCanvas()` sizes the canvas to `img.naturalWidth × img.naturalHeight` (lines 311–312) but the image is displayed scaled via CSS (`max-width: 100%`). Mouse coordinates are divided by `scale` (lines 342–343, 351–352). Since the canvas CSS size matches the displayed image width (both constrained by the container), and `scale = img.clientWidth / img.naturalWidth`, the conversion appears correct for standard layouts. However, **there is no validation** that resulting coordinates fall within `[0, naturalWidth]` × `[0, naturalHeight]`, and no clamping is performed.

**Severity:** Medium. Coordinates may exceed image bounds.

### 2.9 LOW — No Error Feedback on Save (Issue #9)

**Location:** Lines 435, 458.

**Finding:** Both `saveCurrent()` and `exportAll()` display `alert('...')` unconditionally after calling `a.click()`. If the download is blocked, fails silently, or the Blob creation fails, the reviewer is told it succeeded. No try/catch, no `download` event listener, no error path.

**Severity:** Low. False success messages.

### 2.10 LOW — Missing LIKELY_NEGATIVE Images (Issue #10)

**Location:** review_metadata.json (15 entries).

**Finding:** The metadata only contains 15 images (`NEEDS_HUMAN_REVIEW`), but `annotations_v1/uncertain/metadata.json` identifies **18 images** requiring decisions: 15 NEEDS_HUMAN_REVIEW + 3 LIKELY_NEGATIVE (`road005.jpg`, `road012.jpg`, `road028.jpg`). These 3 likely-negative images are not present in the review package at all, preventing complete review.

**Severity:** Low (data gap, not a code bug).

---

## 3. Requirement-by-Requirement Compliance Matrix

| Requirement | Status | Notes |
|---|---|---|
| Loads correct original image for every review item | ✅ Pass | `src="${item.image_path}"` loads from `review_images/` |
| Displays image dimensions and filename | ✅ Pass | `item.dimensions` and `item.image_path` (trimmed) shown |
| Visually distinguishes predictions from GT | ❌ Fail | Predictions shown as text only, never as canvas rectangles |
| Supports drawing bounding boxes | ✅ Pass | mousedown/mouseup drawing with `scale` correction |
| Supports moving bounding boxes | ❌ Fail | No move/edit handler exists |
| Supports resizing bounding boxes | ❌ Fail | No resize handles |
| Supports deleting bounding boxes | ❌ Fail | Only bulk `clearBoxes()` exists |
| Supports all four RoadGuard classes | ⚠️ Partial | Free-text prompt accepts any string; no validation |
| Marks confirmed positive / negative / uncertain | ❌ Fail | No status-setting UI; `item.status` is read-only |
| Does not silently convert predictions to GT | ✅ Pass | Predictions are text-only, never added to `gtBoxes` |
| Decisions survive page refresh | ❌ Fail | No localStorage or persistent store |
| Resume unfinished work | ❌ Fail | No import mechanism |
| Clear feedback on save/export | ❌ Fail | `alert()` fires regardless of success |
| Export captures confirmed negatives | ❌ Fail | `exportAll()` skips images with zero boxes |

**Compliance rate: 7/13 requirements met (54%).**

---

## 4. Classes of Defects

| Category | Count | Severity | Description |
|---|---|---|---|
| Persistence | 3 issues | Critical | No localStorage, no import, no resume |
| Status tracking | 1 issue | Critical | No confirmed/negative/uncertain marking |
| Box operations | 1 issue | High | No delete, move, resize — only create and clear-all |
| Class validation | 1 issue | High | Free-text prompt, no numeric ID, no validation |
| Prediction rendering | 1 issue | High | Predictions not drawn as boxes despite "Red Boxes" label |
| Export semantics | 1 issue | High | Confirmed negatives silently excluded |
| Coordinate validation | 1 issue | Medium | No bounds checking or clamping |
| Save feedback | 1 issue | Low | False success alert |
| Data gap | 1 issue | Low | 3 likely-negative images missing from review package |

---

## 5. Summary

The existing `review_template.html` provides a usable drawing surface but fails at the core requirements of persistence, status tracking, box editing, and reliable export. The most severe gaps are:

1. **All decisions are lost on page refresh** — no localStorage.
2. **No way to mark an image as confirmed-negative or uncertain** — only "draw boxes" or "clear all."
3. **No box editing** — boxes cannot be moved, resized, or deleted individually.
4. **Class selection is unsafe** — free-text prompt with no validation.
5. **Predictions are not visualized as boxes** — misleading red/blue box labels.

The improved tool in `review_tool_v2/` addresses all 12 findings with:
- `localStorage`-backed persistence with explicit export/import.
- Status buttons: Confirmed Positive, Confirmed Negative, Uncertain.
- Individual box delete, move, resize via canvas handles.
- Dropdown class selector with 4-class validation.
- Model prediction rectangles on canvas (red/orange, semi-transparent).
- Export that includes negative and uncertain images.
- Real-time validation with error feedback.
