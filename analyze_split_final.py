import json

# Load correlation graph
with open('C:/Users/viraj/Code_files/Github/RoadGuard AI/experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json') as f:
    cg = json.load(f)

# Load split manifest fixed
with open('C:/Users/viraj/Code_files/Github/RoadGuard AI/experiments/dataset/normalized_rdd2022_india/split_manifest_fixed.json') as f:
    sm = json.load(f)

assignments = sm['assignments']
components = cg['component_manifest']['components']

print(f"Total components: {len(components)}")
print(f"Total assignments: {len(assignments)}")

# Check if any component IDs have assignments in split_manifest_fixed
comp_id_assignments = {}
for k, v in assignments.items():
    if k.startswith('CC_'):
        comp_id_assignments[k] = v

print(f"\nComponent-level assignments found: {len(comp_id_assignments)}")

# Check which component members have individual assignments
all_component_members = set()
for comp in components:
    for m in comp['members']:
        all_component_members.add(m)

individual_member_assignments = {}
unassigned_members = set()
for m in all_component_members:
    if m in assignments:
        individual_member_assignments[m] = assignments[m]
    else:
        unassigned_members.add(m)

print(f"\nComponent members with individual split assignment: {len(individual_member_assignments)}")
print(f"Component members WITHOUT individual split assignment: {len(unassigned_members)}")

# Now do the full analysis
component_analysis = {}
single_split_count = 0
multi_split_count = 0
cross_split_details = []
edges_by_split = {'train': 0, 'val': 0, 'test': 0}
cross_split_edges = 0

for comp in components:
    comp_id = comp['component_id']
    members = comp['members']
    internal_edge_count = comp['internal_edge_count']
    
    # Check component-level assignment
    comp_split = assignments.get(comp_id)
    
    # Check individual member assignments
    member_splits = {}
    for mid in members:
        member_splits[mid] = assignments.get(mid)  # None if not assigned
    
    # Determine the effective split for each member
    # If member has individual assignment, use it
    # If not, use component-level assignment (inherit)
    effective_splits = {}
    for mid in members:
        ms = member_splits[mid]
        if ms is not None:
            effective_splits[mid] = ms
        elif comp_split is not None:
            effective_splits[mid] = comp_split
        else:
            effective_splits[mid] = None
    
    unique_effective_splits = set(effective_splits.values())
    has_none = None in unique_effective_splits
    
    if has_none:
        status = 'unassigned_members'
    elif len(unique_effective_splits) == 1:
        status = 'single_split'
        single_split_count += 1
        edges_by_split[list(unique_effective_splits)[0]] += internal_edge_count
    else:
        status = 'multi_split'
        multi_split_count += 1
        cross_split_edges += internal_edge_count
        cross_split_details.append({
            'component_id': comp_id,
            'members': members,
            'effective_splits': effective_splits,
            'unique_effective_splits': unique_effective_splits,
            'internal_edge_count': internal_edge_count,
            'comp_split': comp_split,
            'individual_assignments': member_splits
        })
    
    component_analysis[comp_id] = {
        'status': status,
        'comp_split': comp_split,
        'effective_splits': effective_splits,
        'unique_effective_splits': unique_effective_splits,
        'internal_edge_count': internal_edge_count
    }

print(f"\n=== ANALYSIS RESULTS ===")
print(f"Components analyzed: {len(components)}")
print(f"Components with single split: {single_split_count}")
print(f"Components with multiple splits (leakage): {multi_split_count}")
print(f"Components with unassigned members: {sum(1 for v in component_analysis.values() if v['status'] == 'unassigned_members')}")
print(f"Total edges: {sum(c['internal_edge_count'] for c in components)}")
print(f"\nEdges by split (intra-component same split):")
for split, count in edges_by_split.items():
    print(f"  {split}: {count}")
print(f"Cross-split edges: {cross_split_edges}")

if cross_split_details:
    print(f"\nCross-split components ({len(cross_split_details)}):")
    for d in cross_split_details:
        print(f"  {d['component_id']}: comp_split={d['comp_split']}, effective_splits={d['unique_effective_splits']}, edges={d['internal_edge_count']}")

print(f"\n=== SUMMARY ===")
print(f"Number of components analyzed: {len(components)}")
print(f"Number of components with single split: {single_split_count}")
print(f"Number of components with multiple splits (leakage): {multi_split_count}")

if multi_split_count > 0:
    print(f"\nPROBLEMATIC COMPONENTS with mixed splits:")
    for d in cross_split_details:
        print(f"  {d['component_id']}: {d['unique_effective_splits']}")
else:
    print(f"\nNo problematic components with mixed split assignments.")

print(f"\nOverall edges_cross_split count: {cross_split_edges}")
print(f"Whether the split respects correlation graph (edges_cross_split == 0): {cross_split_edges == 0}")

if cross_split_edges > 0:
    print(f"\nISSUE: Split does NOT respect correlation graph!")
    print(f"Need to fix the split assignments to ensure all component members have the same split.")
else:
    print(f"\nSUCCESS: Split respects correlation graph - all edges are intra-component within the same split.")