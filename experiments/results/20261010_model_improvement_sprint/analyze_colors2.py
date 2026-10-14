"""Analyze annotated images - first few only."""
import os
import numpy as np
from PIL import Image

ANNOTATED_DIR = "validation/manual/output/test2"

files = sorted([f for f in os.listdir(ANNOTATED_DIR) if 'annotated' in f])[:10]
for f in files:
    path = os.path.join(ANNOTATED_DIR, f)
    img = Image.open(path).convert("RGB")
    w, h = img.size
    if w > 1000 or h > 1000:
        # Downsample for analysis
        img = img.resize((min(w, 500), min(h, 500)))
    arr = np.array(img)
    colors, counts = np.unique(arr.reshape(-1, 3), axis=0, return_counts=True)
    saturated = []
    for i, (r, g, b) in enumerate(colors):
        if max(r, g, b) - min(r, g, b) > 50:
            saturated.append((int(r), int(g), int(b), int(counts[i])))
    saturated.sort(key=lambda x: -x[3])
    if saturated:
        print(f"{f} ({w}x{h}): top saturated: {saturated[:5]}")
    else:
        print(f"{f} ({w}x{h}): no saturated colors")