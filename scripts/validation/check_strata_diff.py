import json
from collections import Counter

m = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))

# Compute per-image class counts from cumulative manifest
prev = {'pothole': 0, 'alligator_crack': 0, 'longitudinal_crack': 0, 'transverse_crack': 0}
per_image_strata = []
per_image_counts = []

for i, img in enumerate(m['image_manifest']):
    curr = img['final_class_counts']
    delta = {k: curr.get(k, 0) - prev.get(k, 0) for k in prev}
    per_image_counts.append(delta)
    
    # Determine stratum from classes present
    classes = [cls for cls, count in delta.items() if count > 0]
    classes.sort()
    
    # Map to stratum label
    stratum_map = {
        (): "empty",
        ("pothole",): "pothole",
        ("longitudinal_crack",): "longitudinal_crack",
        ("alligator_crack",): "alligator_crack",
        ("transverse_crack",): "transverse_crack",
        ("pothole", "longitudinal_crack"): "longitudinal_crack+pothole",
        ("pothole", "alligator_crack"): "alligator_crack+pothole",
        ("pothole", "transverse_crack"): "transverse_crack+pothole",
        ("longitudinal_crack", "alligator_crack"): "longitudinal_crack+alligator_crack",
        ("pothole", "longitudinal_crack", "alligator_crack"): "longitudinal_crack+alligator_crack+pothole",
        ("pothole", "longitudinal_crack", "transverse_crack"): "longitudinal_crack+transverse_crack+pothole",
        ("pothole", "alligator_crack", "transverse_crack"): "transverse_crack+alligator_crack+pothole",
        ("longitudinal_crack", "alligator_crack", "transverse_crack"): "longitudinal_crack+alligator_crack+transverse_crack",
        ("pothole", "longitudinal_crack", "alligator_crack", "transverse_crack"): "longitudinal_crack+transverse_crack+alligator_crack+pothole",
    }
    stratum = stratum_map.get(tuple(classes), "other")
    per_image_strata.append(stratum)
    
    prev = curr

# Summarize
stratum_counts = Counter(per_image_strata)
print("Stratum distribution from manifest deltas:")
for s, c in sorted(stratum_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")
print(f"Total: {sum(stratum_counts.values())}")

# Ground truth from correlation_graph.json
gt = {
    "pothole": 760,
    "alligator_crack+pothole": 380,
    "longitudinal_crack+pothole": 198,
    "longitudinal_crack+alligator_crack+pothole": 163,
    "longitudinal_crack+transverse_crack+pothole": 14,
    "transverse_crack+pothole": 9,
    "longitudinal_crack+transverse_crack+alligator_crack+pothole": 5,
    "transverse_crack+alligator_crack+pothole": 1,
}
print("\nGround truth from correlation_graph.json:")
for s, c in sorted(gt.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")
print(f"Total: {sum(gt.values())}")

# Difference
print("\nDifferences:")
all_strata = set(stratum_counts.keys()) | set(gt.keys())
for s in sorted(all_strata):
    diff = stratum_counts.get(s, 0) - gt.get(s, 0)
    if diff != 0:
        print(f"  {s}: manifest={stratum_counts.get(s,0)}, gt={gt.get(s,0)}, diff={diff}")