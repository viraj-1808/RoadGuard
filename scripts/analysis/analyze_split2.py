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

# Check if any component IDs have assignments in split_manifest_fixed
comp_id_assignments = {}
for k, v in assignments.items():
    if k.startswith('CC_'):
        comp_id_assignments[k] = v

print(f"\nComponent-level assignments found: {len(comp_id_assignments)}")
print(f"Component-level assignments: {comp_id_assignments}")

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
# For each component:
# 1. If the component ID has a split assignment in split_manifest_fixed, use that
# 2. Check if all members also have the same individual split assignment
# 3. If component ID has assignment but members don't, check if members are unassigned

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
        # Some members have no assignment at all
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

# Also check if individual members have assignments that differ from component assignment
print(f"\n=== DETAILED CHECK ===")
mismatched = []
for comp in components:
    comp_id = comp['component_id']
    comp_split = assignments.get(comp_id)
    for mid in comp['members']:
        ind_split = assignments.get(mid)
        if ind_split is not None and comp_split is not None and ind_split != comp_split:
            mismatched.append((comp_id, mid, ind_split, comp_split))

if mismatched:
    print(f"Mismatched individual vs component assignments: {len(mismatched)}")
    for m in mismatched[:20]:
        print(f"  {m[0]}: {m[1]} individual={m[2]} component={m[3]}")
else:
    print("No mismatched individual vs component assignments")

# Check: which component members have individual assignments at all?
print(f"\n=== MEMBER ASSIGNMENT BREAKDOWN ===")
comp_with_individual = []
comp_without_individual = []
for comp in components:
    comp_id = comp['component_id']
    members_with_individual = [m for m in comp['members'] if assignments.get(m) is not None]
    if members_with_individual:
        comp_with_individual.append((comp_id, len(members_with_individual), [m for m in comp['members'] if assignments.get(m) is not None]))
    else:
        comp_without_individual.append(comp_id)

print(f"Components with at least one individually-assigned member: {len(comp_with_individual)}")
print(f"Components with NO individually-assigned members: {len(comp_without_individual)}")
if comp_with_individual:
    print(f"\nFirst few components with individual assignments:")
    for cid, cnt, mlist in comp_with_individual[:5]:
        print(f"  {cid}: {cnt} members assigned: {mlist}")

PYEOF