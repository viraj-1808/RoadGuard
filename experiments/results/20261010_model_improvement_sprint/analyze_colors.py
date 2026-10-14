"""Analyze annotated images to find bounding box colors."""
import os
import numpy as np
from PIL import Image

ANNOTATED_DIR = "validation/manual/output/test2"

for f in sorted(os.listdir(ANNOTATED_DIR)):
    if not 'annotated' in f:
        continue
    path = os.path.join(ANNOTATED_DIR, f)
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    
    # Find unique colors and their counts
    colors, counts = np.unique(arr.reshape(-1, 3), axis=0, return_counts=True)
    
    # Filter for saturated colors (not gray/white/black)
    saturated = []
    for i, (r, g, b) in enumerate(colors):
        if r > 100 or g > 100 or b > 100:
            if max(r, g, b) - min(r, g, b) > 50:  # saturated color
                saturated.append((int(r), int(g), int(b), int(counts[i])))
    
    if saturated:
        print(f"{f}: {len(saturated)} saturated colors, top: {saturated[:5]}")
    else:
        print(f"{f}: no saturated colors found")