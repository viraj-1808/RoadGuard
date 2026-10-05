import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Load correlation graph
with open(PROJECT_ROOT / 'experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json') as f:
    cg = json.load(f)

# Load split manifest fixed
with open(PROJECT_ROOT / 'experiments/dataset/normalized_rdd2022_india/split_manifest_fixed.json') as f:
    sm = json.load(f)

assignments = sm['assignments']
components = cg['component_manifest']['components']

print(f"Total components: {len(components)}")
print(f"Total assignments: {len(assignments)}")

# Step 1: Check each component's split assignments
component_splits = {}
problematic_components = []

for comp in components:
    comp_id = comp['component_id']
    members = comp['members']

    # Get split for each member
    member_splits = []
    for mid in members:
        split = assignments.get(mid)
        if split is None:
            member_splits.append(None)  # unassigned
        else:
            member_splits.append(split)

    # Check if all members have the same non-None split
    unique_splits = set(member_splits)
    has_none = None in unique_splits

    if has_none or len(unique_splits) > 1:
        # Mixed or unassigned splits
        component_splits[comp_id] = {
            'members': members,
            'splits': member_splits,
            'unique_splits': unique_splits,
            'has_none': has_none
        }
        problematic_components.append(comp_id)
    else:
        # All same split
        component_splits[comp_id] = {
            'members': members,
            'split': member_splits[0],
            'unique_splits': unique_splits
        }

single_split_components = [cid for cid, data in component_splits.items() if 'split' in data and len(data.get('unique_splits', set())) == 1 and not data.get('has_none', False)]
multi_split_components = [cid for cid in component_splits if cid not in single_split_components]

print(f"\nComponents analyzed: {len(component_splits)}")
print(f"Components with single split: {len(single_split_components)}")
print(f"Components with multiple splits (leakage): {len(multi_split_components)}")
if multi_split_components:
    print(f"Problematic components: {multi_split_components}")

# Now count edges
# Sum internal_edge_count across all components
total_internal_edges = sum(comp['internal_edge_count'] for comp in components)
print(f"\nSum of internal_edge_count across all components: {total_internal_edges}")

# Count edges by split for intra-component edges
edges_by_split = {'train': 0, 'val': 0, 'test': 0}
cross_split_edges = 0
cross_split_details = []

# For each component, count internal edges and check if members are in same split
for comp in components:
    comp_id = comp['component_id']
    members = comp['members']
    internal_edge_count = comp['internal_edge_count']
    
    # Get splits for all members
    member_split_map = {}
    for mid in members:
        member_split_map[mid] = assignments.get(mid)
    
    unique_member_splits = set(member_split_map.values())
    
    if len(unique_member_splits) == 1 and None not in unique_member_splits:
        # All members in same split
        split = list(unique_member_splits)[0]
        edges_by_split[split] += internal_edge_count
    else:
        # Cross-split component
        cross_split_edges += internal_edge_count
        cross_split_details.append({
            'component_id': comp_id,
            'members': members,
            'splits': member_split_map,
            'unique_splits': unique_member_splits,
            'internal_edge_count': internal_edge_count
        })

print(f"\nEdges by split (intra-component, same split):")
for split, count in edges_by_split.items():
    print(f"  {split}: {count}")
print(f"Cross-split edges: {cross_split_edges}")

if cross_split_details:
    print(f"\nCross-split component details:")
    for detail in cross_split_details:
        print(f"  Component {detail['component_id']}: {detail['unique_splits']}")
        print(f"    Internal edges: {detail['internal_edge_count']}")

# Also check: does the split_manifest_fixed have assignments for all component members?
all_component_members = set()
for comp in components:
    for m in comp['members']:
        all_component_members.add(m)

assigned_members = set(assignments.keys())
missing_assignments = all_component_members - assigned_members
extra_assignments = assigned_members - all_component_members

print(f"\nComponent members: {len(all_component_members)}")
print(f"Assigned members: {len(assigned_members)}")
print(f"Missing assignments: {len(missing_assignments)}")
if missing_assignments:
    print(f"  Missing: {list(missing_assignments)[:20]}")

# Check split statistics
print(f"\nSplit statistics from split_manifest_fixed:")
for split, stats in sm['split_statistics'].items():
    print(f"  {split}: {stats['image_count']} images, {stats['component_count']} components, {stats['singleton_count']} singletons")

# Verify V1_atomicity
print(f"\nValidation V1_atomicity: {sm['validation']['V1_atomicity']['pass']}")