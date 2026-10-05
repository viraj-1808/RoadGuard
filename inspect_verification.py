import json
import sys

with open(r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\normalized_rdd2022_india\group_analysis\near_duplicate_verification.json') as f:
    data = json.load(f)

print("Top-level keys:", list(data.keys()))
print()

# Look at the structure of pairs
if 'pairs' in data:
    pairs = data['pairs']
    print(f"Number of pairs: {len(pairs)}")
    if pairs:
        print("First pair keys:", list(pairs[0].keys()))
        print("First pair sample:", json.dumps(pairs[0], indent=2))
if 'pixel_verified_groups' in data:
    groups = data['pixel_verified_groups']
    print(f"\nNumber of pixel_verified_groups: {len(groups)}")
    if groups:
        print("First group sample:", json.dumps(groups[0], indent=2)[:1000])