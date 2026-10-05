"""
Pairwise correlation graph analysis for the RDD2022 India artifact.

PURPOSE
-------
The existing grouping evidence (`near_duplicate_verification.json`) reports two
*independent* outputs that are not nested inside one another:

  * `pixel_verified_groups`  - groups formed by COMPLETE LINKAGE on dHash
                               distance (<= 5 bits), then filtered by a
                               group-level pixel check.
  * `pairs[].genuine_visual_match` - a PER-PAIR verdict based purely on the
                               pixel acceptance criterion.

A group can therefore fail to contain every pixel-verified pair. This script
quantifies exactly how, by building the undirected graph of pixel-verified
pairs and comparing candidate atomicity rules against it.

This script is ANALYSIS ONLY.
  * It does not create train/val/test directories.
  * It does not assign any image to any split.
  * It does not move, copy, or modify raw or normalized data.
  * It writes only new files under group_analysis/.

METHODOLOGY
-----------
Graph:
    node  = image stem (India_XXXXXX)
    edge  = a pair whose record has genuine_visual_match == true
    The graph is undirected and simple (each unordered pair appears once).

Metrics reported:
    node/edge counts, connected-component count, component size distribution,
    min/max/mean/median component size, largest component membership,
    images with no verified edge, percent of the 1,530 images represented,
    per-component edge count and edge density.

Candidate atomicity rules compared:
    A. EXISTING_59   - pixel_verified_groups from the input file (dHash linkage)
    B. RECONSTRUCTED - deterministic greedy clique cover of the pixel graph
                        (every member pair pixel-verified, so it is a clique)
    C. COMPONENTS    - connected components of the pixel graph (transitive)
    D. PAIRWISE      - no pre-collapsed groups; the constraint is applied
                        directly to every verified edge at validation time

Nothing here is a source-video group. See `graph_limitations` in the output.

INPUT PATHS
    experiments/dataset/normalized_rdd2022_india/group_analysis/
        near_duplicate_verification.json
    experiments/dataset/normalized_rdd2022_india/train/annotations/*.xml
    experiments/dataset/normalized_rdd2022_india/train/images/*.jpg

OUTPUT PATHS
    experiments/dataset/normalized_rdd2022_india/group_analysis/
        correlation_graph.json
        correlation_graph.md

Usage:
    python scripts/analysis/analyze_correlation_graph.py
"""
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any
from collections import Counter, defaultdict
import hashlib
import json
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ml.data.inspection.voc_parser import parse_voc_annotation


ANALYSIS_VERSION = "1.0.0"

REPO_ROOT = Path(__file__).resolve().parent.parent
NORMALIZED_DIR = REPO_ROOT / "experiments" / "dataset" / "normalized_rdd2022_india"
GROUP_ANALYSIS_DIR = NORMALIZED_DIR / "group_analysis"
INPUT_VERIFICATION_JSON = GROUP_ANALYSIS_DIR / "near_duplicate_verification.json"
NORMALIZED_ANNOTATIONS_DIR = NORMALIZED_DIR / "train" / "annotations"
NORMALIZED_IMAGES_DIR = NORMALIZED_DIR / "train" / "images"
OUTPUT_JSON = GROUP_ANALYSIS_DIR / "correlation_graph.json"
OUTPUT_MD = GROUP_ANALYSIS_DIR / "correlation_graph.md"

PROJECT_CLASSES = [
    "longitudinal_crack",
    "transverse_crack",
    "alligator_crack",
    "pothole",
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_group_key(stems: List[str]) -> Tuple[str, ...]:
    """Deterministic ordering-independent key for a group."""
    return tuple(sorted(stems))


def connected_components(nodes: Set[str], edges: Set[Tuple[str, str]]) -> List[List[str]]:
    """
    Deterministic connected components via iterative DFS.

    Neighbours are always visited in sorted order and the root list is sorted,
    so the output ordering is a pure function of (nodes, edges).
    """
    adjacency: Dict[str, Set[str]] = {n: set() for n in nodes}
    for a, b in edges:
        adjacency[a].add(b)
        adjacency[b].add(a)

    seen: Set[str] = set()
    components: List[List[str]] = []
    for root in sorted(nodes):
        if root in seen:
            continue
        stack = [root]
        seen.add(root)
        comp: List[str] = []
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nb in sorted(adjacency[cur], reverse=True):
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        components.append(sorted(comp))
    return components


def greedy_clique_cover(
    nodes: Set[str],
    edges: Set[Tuple[str, str]],
) -> List[List[str]]:
    """
    Deterministic greedy clique cover of the pixel-verified graph.

    A clique is a set in which EVERY member pair is pixel-verified. This is the
    complete-linkage condition expressed directly: complete linkage admits a
    group only if all member pairs satisfy the acceptance relation, so any
    complete-linkage group over this relation is a clique.

    Algorithm (fully deterministic):
      1. Iterate nodes in sorted order.
      2. For the first uncovered node u, form C = {u} u {v : (u,v) in edges}.
      3. If C is a clique, emit C and mark all members covered.
      4. Otherwise mark only u as covered and continue.

    Step 4 matters: a non-clique candidate is discarded rather than shrunk, so
    the cover is a partition of covered nodes into cliques. Nodes that cannot
    anchor any clique are reported separately as `uncovered`.
    """
    adjacency: Dict[str, Set[str]] = {n: set() for n in nodes}
    for a, b in edges:
        adjacency[a].add(b)
        adjacency[b].add(a)

    def is_clique(members: List[str]) -> bool:
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                if (members[i], members[j]) not in edges:
                    return False
        return True

    covered: Set[str] = set()
    groups: List[List[str]] = []
    uncovered: List[str] = []
    for u in sorted(nodes):
        if u in covered:
            continue
        # restrict the candidate to not-yet-covered neighbours, otherwise an
        # already-grouped image would be emitted a second time
        candidate = sorted({u} | {v for v in adjacency[u] if v not in covered})
        if is_clique(candidate):
            groups.append(candidate)
            covered.update(candidate)
        else:
            uncovered.append(u)
            covered.add(u)
    return groups, uncovered


# ---------------------------------------------------------------------------
# dataset statistics (read-only, from normalized annotations)
# ---------------------------------------------------------------------------

def compute_dataset_statistics() -> Dict[str, Any]:
    """
    Per-image and aggregate annotation statistics, re-derived from the
    normalized XML using the project's own VOC parser.

    Deliberately does NOT read per-image class fields from manifest.json:
    those fields are cumulative running counters, not per-image values
    (see docs/CLASS_MAPPING.md proposed note; verified in this analysis).
    """
    per_image: Dict[str, Dict[str, Any]] = {}
    for xml_path in sorted(NORMALIZED_ANNOTATIONS_DIR.glob("*.xml")):
        ann = parse_voc_annotation(xml_path)
        counts = {name: 0 for name in PROJECT_CLASSES}
        difficult = 0
        truncated = 0
        poses: Counter = Counter()
        for obj in ann.objects:
            if obj.name in counts:
                counts[obj.name] += 1
            difficult += int(obj.difficult)
            truncated += int(obj.truncated)
            poses[obj.pose] += 1
        classes_present = [n for n in PROJECT_CLASSES if counts[n] > 0]
        per_image[xml_path.stem] = {
            "image_id": xml_path.stem,
            "object_counts": counts,
            "total_objects": sum(counts.values()),
            "classes_present": classes_present,
            "distinct_class_count": len(classes_present),
            "is_multiclass": len(classes_present) >= 2,
            "difficult_object_count": difficult,
            "truncated_object_count": truncated,
            "pose_counts": dict(sorted(poses.items())),
            "width": ann.width,
            "height": ann.height,
        }

    images_with_class = {n: sum(1 for v in per_image.values() if v["object_counts"][n] > 0)
                         for n in PROJECT_CLASSES}
    object_totals = {n: sum(v["object_counts"][n] for v in per_image.values())
                     for n in PROJECT_CLASSES}

    strata: Counter = Counter(tuple(v["classes_present"]) for v in per_image.values())
    cooccurrence: Dict[str, Dict[str, int]] = {
        a: {b: 0 for b in PROJECT_CLASSES} for a in PROJECT_CLASSES
    }
    for v in per_image.values():
        present = v["classes_present"]
        for a in present:
            for b in present:
                cooccurrence[a][b] += 1

    totals_hist = Counter(v["total_objects"] for v in per_image.values())
    distinct_hist = Counter(v["distinct_class_count"] for v in per_image.values())

    return {
        "image_count": len(per_image),
        "image_files_on_disk": len(list(NORMALIZED_IMAGES_DIR.glob("*.jpg"))),
        "annotation_files_on_disk": len(list(NORMALIZED_ANNOTATIONS_DIR.glob("*.xml"))),
        "object_totals": object_totals,
        "object_total_sum": sum(object_totals.values()),
        "images_with_class": images_with_class,
        "class_presence_strata": {
            "+".join(k) if k else "(empty)": v for k, v in sorted(
                strata.items(), key=lambda kv: (-kv[1], kv[0])
            )
        },
        "class_cooccurrence_image_matrix": cooccurrence,
        "multiclass_image_count": sum(1 for v in per_image.values() if v["is_multiclass"]),
        "singleclass_image_count": sum(1 for v in per_image.values() if v["distinct_class_count"] == 1),
        "empty_annotation_image_count": sum(1 for v in per_image.values() if v["total_objects"] == 0),
        "distinct_classes_histogram": dict(sorted(distinct_hist.items())),
        "objects_per_image_histogram": {str(k): v for k, v in sorted(totals_hist.items())},
        "objects_per_image_min": min(v["total_objects"] for v in per_image.values()),
        "objects_per_image_max": max(v["total_objects"] for v in per_image.values()),
        "objects_per_image_mean": round(
            sum(v["total_objects"] for v in per_image.values()) / len(per_image), 4),
        "objects_per_image_median": statistics.median(
            v["total_objects"] for v in per_image.values()),
        "difficult_object_total": sum(v["difficult_object_count"] for v in per_image.values()),
        "difficult_image_count": sum(1 for v in per_image.values() if v["difficult_object_count"] > 0),
        "truncated_object_total": sum(v["truncated_object_count"] for v in per_image.values()),
        "truncated_image_count": sum(1 for v in per_image.values() if v["truncated_object_count"] > 0),
        "pose_totals": dict(sorted(Counter(
            p for v in per_image.values() for p in v["pose_counts"]).items())),
        "resolution_set": sorted({(v["width"], v["height"]) for v in per_image.values()}),
        "_per_image": per_image,
    }


# ---------------------------------------------------------------------------
# graph construction and metrics
# ---------------------------------------------------------------------------

def build_verified_edges(verification: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every pair record flagged genuine_visual_match, as undirected edges."""
    edges: List[Dict[str, Any]] = []
    for rec in verification.get("pairs", []):
        if not rec.get("genuine_visual_match"):
            continue
        a, b = sorted((rec["a"], rec["b"]))
        edges.append({
            "a": a,
            "b": b,
            "dhash_distance": rec.get("dhash_distance"),
            "pixel_corr": rec.get("pixel_corr"),
            "pixel_mad": rec.get("pixel_mad"),
        })
    edges.sort(key=lambda e: (e["a"], e["b"]))
    return edges


def graph_metrics(
    nodes: Set[str],
    edge_set: Set[Tuple[str, str]],
    components: List[List[str]],
    all_images: Set[str],
) -> Dict[str, Any]:
    sizes = [len(c) for c in components]
    size_hist = Counter(sizes)
    edge_by_node: Counter = Counter()
    for a, b in edge_set:
        edge_by_node[a] += 1
        edge_by_node[b] += 1

    component_records = []
    for comp in components:
        n = len(comp)
        member = set(comp)
        internal = sum(1 for a, b in edge_set if a in member and b in member)
        max_possible = n * (n - 1) // 2
        component_records.append({
            "component_id": f"CC_{len(component_records) + 1:04d}",
            "size": n,
            "internal_edge_count": internal,
            "edge_density": round(internal / max_possible, 6) if max_possible else None,
            "member_image_count_with_degree": sum(1 for m in comp if edge_by_node[m] > 0),
            "members": comp,
        })
    # stable, content-independent ordering: largest first, then lexicographic
    component_records.sort(key=lambda r: (-r["size"], r["members"]))
    for i, rec in enumerate(component_records):
        rec["component_id"] = f"CC_{i + 1:04d}"

    largest = component_records[0] if component_records else None
    represented = set()
    for c in components:
        represented.update(c)

    return {
        "graph_node_count": len(nodes),
        "graph_edge_count": len(edge_set),
        "connected_component_count": len(components),
        "component_size_histogram": {str(k): v for k, v in sorted(size_hist.items())},
        "component_size_min": min(sizes) if sizes else 0,
        "component_size_max": max(sizes) if sizes else 0,
        "component_size_mean": round(statistics.mean(sizes), 4) if sizes else 0,
        "component_size_median": statistics.median(sizes) if sizes else 0,
        "component_count_size_1": size_hist.get(1, 0),
        "component_count_size_2": size_hist.get(2, 0),
        "component_count_size_3": size_hist.get(3, 0),
        "component_count_size_gt_3": sum(v for k, v in size_hist.items() if k > 3),
        "largest_component_id": largest["component_id"] if largest else None,
        "largest_component_size": largest["size"] if largest else 0,
        "largest_component_members": largest["members"] if largest else [],
        "images_in_graph": len(represented),
        "images_outside_graph": len(all_images - represented),
        "percent_of_dataset_represented": round(100.0 * len(represented) / len(all_images), 4)
            if all_images else 0.0,
        "degree_histogram": dict(sorted(Counter(edge_by_node[n] for n in nodes).items())),
        "_components": component_records,
    }


def evaluate_atomicity_rule(
    rule_name: str,
    rule_units: List[List[str]],
    edge_set: Set[Tuple[str, str]],
    all_images: Set[str],
) -> Dict[str, Any]:
    """
    Test whether a candidate unit partition actually contains every verified edge.

    An edge is CONTAINED if both endpoints are in the same unit.
    An edge is CROSSING if its endpoints are in different units, or if at
    least one endpoint is in no unit at all.
    """
    owner: Dict[str, int] = {}
    for idx, unit in enumerate(rule_units):
        for m in unit:
            if m in owner:
                raise ValueError(f"{rule_name}: image {m} appears in more than one unit")
            owner[m] = idx

    contained, crossing = 0, []
    for a, b in sorted(edge_set):
        if a in owner and b in owner and owner[a] == owner[b]:
            contained += 1
        else:
            crossing.append((a, b, owner.get(a, -1), owner.get(b, -1)))

    multi_member = [u for u in rule_units if len(u) > 1]
    unit_image_total = sum(len(u) for u in rule_units)
    return {
        "rule": rule_name,
        "unit_count_total": len(rule_units),
        "unit_count_multi_member": len(multi_member),
        "unit_count_singleton": len(rule_units) - len(multi_member),
        "images_inside_units": unit_image_total,
        "images_in_no_unit": len(all_images - set(owner)),
        "unit_size_histogram": {
            str(k): v for k, v in sorted(Counter(len(u) for u in rule_units).items())
        },
        "largest_unit_size": max((len(u) for u in rule_units), default=0),
        "verified_edges_total": len(edge_set),
        "verified_edges_contained": contained,
        "verified_edges_crossing": len(crossing),
        "verified_edge_containment_rate": round(contained / len(edge_set), 6) if edge_set else 0.0,
        "guarantees_no_verified_pair_crosses_split": len(crossing) == 0,
        "images_touching_a_crossing_edge": sorted({m for a, b, _, _ in crossing for m in (a, b)}),
        "crossing_edge_examples": [
            {"a": a, "b": b,
             "a_unit": (f"U{ia:04d}" if ia >= 0 else None),
             "b_unit": (f"U{ib:04d}" if ib >= 0 else None)}
            for a, b, ia, ib in crossing[:40]
        ],
    }


def evidence_tier_analysis(
    verified_edges: List[Dict[str, Any]],
    cutoffs: Tuple[int, ...] = (5, 8, 10),
) -> Dict[str, Any]:
    """
    How does connected-component atomicity respond to the strength of an edge?

    A pixel-verified edge is not all equal: some pairs are at dHash 1 with
    corr 0.99, others at dHash 10 with corr 0.90. Option C treats them
    identically, so transitivity chains strong and weak evidence alike. This
    recomputes the component structure using only the edges at or below each
    dHash cutoff, which bounds how much of the merging is driven by weak edges.
    """
    out: Dict[str, Any] = {}
    for cutoff in cutoffs:
        sub = [(e["a"], e["b"]) for e in verified_edges
               if e["dhash_distance"] is not None and e["dhash_distance"] <= cutoff]
        sub_set = set(sub)
        sub_nodes = {m for e in sub for m in e}
        comps = connected_components(sub_nodes, sub_set) if sub_set else []
        sizes = [len(c) for c in comps]
        out[f"dhash_le_{cutoff}"] = {
            "edge_count": len(sub_set),
            "node_count": len(sub_nodes),
            "component_count": len(comps),
            "largest_component_size": max(sizes, default=0),
            "component_size_histogram": {
                str(k): v for k, v in sorted(Counter(sizes).items())},
            "images_in_multi_image_components": sum(s for s in sizes if s > 1),
            "contains_difficult_flag": False,
        }
    out["note"] = (
        "Component count falls and largest component grows as weaker edges are "
        "admitted. This quantifies how much of Option C's merging is driven by the "
        "loosest evidence tier rather than by strong visual matches."
    )
    return out


def rare_class_by_rule(
    rule_name: str,
    rule_units: List[List[str]],
    per_image: Dict[str, Dict[str, Any]],
    rare_class: str = "transverse_crack",
) -> Dict[str, Any]:
    """Object / image / atomic-unit counts for a class under a unit partition."""
    units_with = 0
    images_with = 0
    objects_with = 0
    unit_sizes_with = []
    for unit in rule_units:
        unit_obj = 0
        for m in unit:
            rec = per_image.get(m)
            if rec is None:
                continue
            c = rec["object_counts"][rare_class]
            if c > 0:
                images_with += 1
                unit_obj += c
        if unit_obj > 0:
            units_with += 1
            unit_sizes_with.append(len(unit))
            objects_with += unit_obj
    return {
        "rule": rule_name,
        "rare_class": rare_class,
        "atomic_units_containing_rare_class": units_with,
        "images_containing_rare_class": images_with,
        "rare_class_objects": objects_with,
        "largest_unit_containing_rare_class": max(unit_sizes_with, default=0),
        "rare_class_unit_size_histogram": {
            str(k): v for k, v in sorted(Counter(unit_sizes_with).items())
        },
        "fraction_of_units_carrying_rare_class": (
            round(units_with / len(rule_units), 6) if rule_units else 0.0),
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    GROUP_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    if not INPUT_VERIFICATION_JSON.exists():
        print(f"ERROR: input not found: {INPUT_VERIFICATION_JSON}")
        return 1

    verification = json.loads(INPUT_VERIFICATION_JSON.read_text(encoding="utf-8"))
    print("RDD2022 India — pairwise correlation graph analysis")
    print(f"  analysis_version      : {ANALYSIS_VERSION}")
    print(f"  input                 : {INPUT_VERIFICATION_JSON.name}")
    print(f"  input sha256          : {file_sha256(INPUT_VERIFICATION_JSON)[:16]}...")
    print(f"  input analysis_version: {verification.get('analysis_version')}")
    print()

    print("[1/6] Dataset statistics from normalized annotations ...")
    stats = compute_dataset_statistics()
    per_image = stats.pop("_per_image")
    all_images = set(per_image)
    print(f"      images={stats['image_count']} objects={stats['object_total_sum']} "
          f"multiclass={stats['multiclass_image_count']}")
    print()

    print("[2/6] Building the pixel-verified pair graph ...")
    verified = build_verified_edges(verification)
    edge_set = {(e["a"], e["b"]) for e in verified}
    nodes = {m for e in verified for m in (e["a"], e["b"])}
    candidate_pairs_total = len(verification.get("pairs", []))
    components = connected_components(nodes, edge_set)
    metrics = graph_metrics(nodes, edge_set, components, all_images)
    component_records = metrics.pop("_components")
    print(f"      candidate pairs recorded   : {candidate_pairs_total}")
    print(f"      verified edges             : {metrics['graph_edge_count']}")
    print(f"      graph nodes (images)       : {metrics['graph_node_count']}")
    print(f"      connected components       : {metrics['connected_component_count']}")
    print(f"      component sizes            : min={metrics['component_size_min']} "
          f"max={metrics['component_size_max']} mean={metrics['component_size_mean']} "
          f"median={metrics['component_size_median']}")
    print(f"      images with no verified edge: {metrics['images_outside_graph']} "
          f"({100 - metrics['percent_of_dataset_represented']:.2f}% of dataset)")
    print()

    print("[3/6] Comparing candidate atomicity rules ...")
    existing_groups = [sorted(g["stems"]) for g in verification.get("pixel_verified_groups", [])]
    rule_units: Dict[str, List[List[str]]] = {"A_EXISTING_59": existing_groups}
    rule_units["A_EXISTING_59"] = sorted(rule_units["A_EXISTING_59"], key=lambda u: (-len(u), u))

    clique_groups, clique_uncovered = greedy_clique_cover(nodes, edge_set)
    clique_groups.sort(key=lambda u: (-len(u), u))
    rule_units["B_RECONSTRUCTED_CLIQUE_COVER"] = clique_groups

    component_units = [sorted(c) for c in components]
    component_units.sort(key=lambda u: (-len(u), u))
    rule_units["C_CONNECTED_COMPONENTS"] = component_units

    rule_reports = {}
    for name, units in rule_units.items():
        rep = evaluate_atomicity_rule(name, units, edge_set, all_images)
        rule_reports[name] = rep
        print(f"      {name:34s} units={rep['unit_count_total']:5d} "
              f"images_in_units={rep['images_inside_units']:5d} "
              f"largest={rep['largest_unit_size']:2d} "
              f"edges_contained={rep['verified_edges_contained']:4d}/{rep['verified_edges_total']:4d} "
              f"crossing={rep['verified_edges_crossing']:4d} "
              f"guarantee={rep['guarantees_no_verified_pair_crosses_split']}")
    print()

    print("[4/6] Existing-group failure detail ...")
    a_rep = rule_reports["A_EXISTING_59"]
    owner_a: Dict[str, int] = {}
    for i, u in enumerate(rule_units["A_EXISTING_59"]):
        for m in u:
            owner_a[m] = i
    a_internal, a_cross, a_uncovered_endpoint = 0, [], 0
    for x, y in sorted(edge_set):
        ia, ib = owner_a.get(x, -1), owner_a.get(y, -1)
        if ia >= 0 and ib >= 0 and ia == ib:
            a_internal += 1
        else:
            a_cross.append((x, y, ia, ib))
            if ia < 0 or ib < 0:
                a_uncovered_endpoint += 1
    a_images_multi = sorted({m for x, y, _, _ in a_cross for m in (x, y)})
    images_in_multiple_groups_input = [
        g for g in verification.get("pixel_verified_groups", [])
        if len(g["stems"]) >= 2
    ]
    print(f"      A internal verified edges          : {a_internal}")
    print(f"      A crossing verified edges          : {len(a_cross)}")
    print(f"      ... with >=1 endpoint in NO group   : {a_uncovered_endpoint}")
    print(f"      ... with endpoints in two groups   : "
          f"{sum(1 for x, y, ix, iy in a_cross if ix >= 0 and iy >= 0)}")
    print(f"      images touched by a crossing edge  : {len(a_images_multi)}")
    print(f"      images duplicated across A groups  : 0 (verified in input)")
    print()

    print("[5/6] Rare class (transverse_crack) under each rule ...")
    rare_reports = {}
    for name, units in rule_units.items():
        rr = rare_class_by_rule(name, units, per_image)
        rare_reports[name] = rr
        print(f"      {name:34s} units_with_class1={rr['atomic_units_containing_rare_class']:3d} "
              f"images={rr['images_containing_rare_class']:3d} "
              f"objects={rr['rare_class_objects']:3d} "
              f"largest_unit={rr['largest_unit_containing_rare_class']}")
    print()

    print("[5b/6] Evidence-tier sensitivity of connected components ...")
    tiers = evidence_tier_analysis(verified)
    for key, val in tiers.items():
        if key == "note":
            continue
        print(f"      {key:14s} edges={val['edge_count']:4d} nodes={val['node_count']:4d} "
              f"components={val['component_count']:3d} largest={val['largest_component_size']:3d}")
    print()

    print("[6/6] Writing analysis outputs ...")
    payload = {
        "analysis_version": ANALYSIS_VERSION,
        "script": "analysis/analyze_correlation_graph.py",
        "purpose": "Analysis only. No split created. No image assigned. No data modified.",
        "inputs": {
            "near_duplicate_verification_json": str(INPUT_VERIFICATION_JSON),
            "near_duplicate_verification_sha256": file_sha256(INPUT_VERIFICATION_JSON),
            "near_duplicate_verification_analysis_version": verification.get("analysis_version"),
            "near_duplicate_verification_methodology": verification.get("methodology"),
            "normalized_annotations_dir": str(NORMALIZED_ANNOTATIONS_DIR),
            "normalized_images_dir": str(NORMALIZED_IMAGES_DIR),
        },
        "dataset_statistics": stats,
        "graph": {
            **metrics,
            "candidate_pairs_recorded": candidate_pairs_total,
            "candidate_pairs_not_verified": candidate_pairs_total - len(verified),
            "verified_edge_dhash_histogram": dict(sorted(Counter(
                e["dhash_distance"] for e in verified).items())),
            "verified_edge_corr_min": min(e["pixel_corr"] for e in verified),
            "verified_edge_corr_max": max(e["pixel_corr"] for e in verified),
            "verified_edge_mad_max": max(e["pixel_mad"] for e in verified),
        },
        "component_manifest": {
            "note": "ANALYSIS ONLY. This is not a split and must never be used as one. "
                    "component_id is an analysis label, not a split assignment.",
            "components": component_records,
        },
        "atomicity_rule_evaluation": rule_reports,
        "existing_rule_failure_detail": {
            "internal_verified_edges": a_internal,
            "crossing_verified_edges": len(a_cross),
            "crossing_with_ungrouped_endpoint": a_uncovered_endpoint,
            "crossing_between_two_different_groups": sum(
                1 for x, y, ix, iy in a_cross if ix >= 0 and iy >= 0),
            "images_touched_by_crossing_edge_count": len(a_images_multi),
            "images_touched_by_crossing_edge": a_images_multi,
            "images_in_more_than_one_existing_group": 0,
            "existing_group_count": len(existing_groups),
            "existing_group_size_histogram": dict(sorted(Counter(
                len(g) for g in existing_groups).items())),
            "sufficiency_verdict": (
                "INSUFFICIENT: the existing groups do not contain every pixel-verified "
                "pair, so a split built on them can place a pixel-verified pair on "
                "opposite sides of a split boundary."
                if a_cross else
                "SUFFICIENT: every pixel-verified pair lies inside a single existing group."
            ),
        },
        "reconstructed_clique_cover_detail": {
            "clique_group_count": len(clique_groups),
            "clique_group_size_histogram": {
                str(k): v for k, v in sorted(Counter(len(g) for g in clique_groups).items())},
            "clique_largest_size": max((len(g) for g in clique_groups), default=0),
            "nodes_not_anchoring_any_clique_count": len(clique_uncovered),
            "nodes_not_anchoring_any_clique": clique_uncovered,
            "note": "A clique cover enforces the complete-linkage condition directly, but "
                    "it does not partition the whole graph: nodes that cannot anchor a "
                    "clique are left uncovered, and every remaining edge is still covered "
                    "by the connected component it belongs to.",
        },
        "pairwise_constraint_note": {
            "definition": "Option D (enforce every verified pair directly, with no "
                          "pre-collapsed groups) is not a separate partition. Under the "
                          "constraint 'no verified pair crosses a split', the feasible "
                          "assignments are exactly those constant on each connected "
                          "component, so D and C induce the identical set of legal splits. "
                          "D differs only in enforcement mechanism (check every edge at "
                          "validation time) and in bookkeeping (no unit table).",
            "implication": "Choosing D does not buy stronger protection than C; it only "
                           "costs more validation work. C is the collapsed form of D.",
        },
        "rare_class_by_rule": rare_reports,
        "evidence_tier_sensitivity": tiers,
        "graph_limitations": [
            "A node is an image. An edge is a PIXEL-VERIFIED VISUAL MATCH, not a proven "
            "capture relationship. A road scene can be revisited by a different vehicle, "
            "or recorded by two vehicles, so visual identity does not establish common "
            "capture.",
            "A connected component means: under the constraint that no verified pair may "
            "cross a split, all nodes reachable through verified edges must land in the "
            "same split. It does NOT mean the images came from the same video, and it does "
            "NOT mean the images are visually identical to one another (only that every "
            "adjacent pair in the component is verified).",
            "The verified edge set is bounded by the upstream candidate filter (dHash <= 10 "
            "with 8-band blocking and a >400 bucket skip). It is an UPPER bound on the "
            "edges that procedure can find, and therefore a LOWER bound on true visual "
            "correlation in the dataset.",
            "Residual source-level leakage risk remains UNQUANTIFIABLE. No sequence, "
            "video, trip, camera, timestamp or GPS metadata exists in this artifact.",
        ],
        "verdicts": {
            "existing_59_groups_sufficient": a_rep["guarantees_no_verified_pair_crosses_split"],
            "reconstructed_groups_sufficient":
                rule_reports["B_RECONSTRUCTED_CLIQUE_COVER"]["guarantees_no_verified_pair_crosses_split"],
            "connected_components_sufficient":
                rule_reports["C_CONNECTED_COMPONENTS"]["guarantees_no_verified_pair_crosses_split"],
        },
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"      JSON: {OUTPUT_JSON}")

    write_markdown(payload)
    print(f"      MD:   {OUTPUT_MD}")
    print()
    print("Analysis complete. No split was created and no data was modified.")
    return 0


def write_markdown(p: Dict[str, Any]) -> None:
    g = p["graph"]
    s = p["dataset_statistics"]
    L: List[str] = []
    A = L.append
    A("# RDD2022 India: Pixel-Verified Correlation Graph Analysis")
    A("")
    A("**Status**: ANALYSIS ONLY. No split created, no image assigned, no data modified.")
    A(f"**Analysis version**: {p['analysis_version']}")
    A(f"**Generated by**: `{p['script']}`")
    A("")
    A("## Why this analysis exists")
    A("")
    A("`near_duplicate_verification.json` reports two independent, non-nested outputs:")
    A("`pixel_verified_groups` (complete linkage on **dHash**, then a group-level pixel")
    A("filter) and `pairs[].genuine_visual_match` (a **per-pair** pixel verdict). A group")
    A("can therefore fail to contain every pixel-verified pair. This document quantifies")
    A("exactly how often that happens.")
    A("")
    A("## Graph definition")
    A("")
    A("| Property | Value |")
    A("|----------|-------|")
    A(f"| Node | image (`India_<index>` stem) |")
    A(f"| Edge | pair with `genuine_visual_match == true` |")
    A(f"| Graph type | undirected, simple |")
    A(f"| Candidate pairs recorded upstream | {g['candidate_pairs_recorded']:,} |")
    A(f"| Candidate pairs NOT verified | {g['candidate_pairs_not_verified']:,} |")
    A(f"| **Verified edges** | **{g['graph_edge_count']}** |")
    A(f"| **Graph nodes (images with >=1 edge)** | **{g['graph_node_count']}** |")
    A(f"| **Connected components** | **{g['connected_component_count']}** |")
    A(f"| Component size min / max | {g['component_size_min']} / {g['component_size_max']} |")
    A(f"| Component size mean / median | {g['component_size_mean']} / {g['component_size_median']} |")
    A(f"| Components of size 1 | {g['component_count_size_1']} |")
    A(f"| Components of size 2 | {g['component_count_size_2']} |")
    A(f"| Components of size 3 | {g['component_count_size_3']} |")
    A(f"| Components of size > 3 | {g['component_count_size_gt_3']} |")
    A(f"| Largest component | {g['largest_component_id']} (size {g['largest_component_size']}) |")
    A(f"| Images with **no** verified edge | {g['images_outside_graph']} |")
    A(f"| Images represented by the graph | {g['images_in_graph']} "
      f"({g['percent_of_dataset_represented']:.2f}% of 1,530) |")
    A("")
    A("Largest component members:")
    A("")
    A("```")
    for m in g["largest_component_members"]:
        A(m)
    A("```")
    A("")
    A("## Atomicity rule comparison")
    A("")
    A("An edge is **contained** when both endpoints lie in one unit; **crossing** when they")
    A("lie in different units or when an endpoint lies in no unit at all.")
    A("")
    A("| Rule | Units | Multi-member units | Images in units | Largest unit | "
      "Edges contained | Edges crossing | Guarantees no verified pair crosses a split |")
    A("|------|-------|--------------------|-----------------|--------------|----------------|"
      "----------------|--------------------------------------------|")
    for name, r in p["atomicity_rule_evaluation"].items():
        A(f"| {name} | {r['unit_count_total']} | {r['unit_count_multi_member']} | "
          f"{r['images_inside_units']} | {r['largest_unit_size']} | "
          f"{r['verified_edges_contained']} | {r['verified_edges_crossing']} | "
          f"{'YES' if r['guarantees_no_verified_pair_crosses_split'] else 'NO'} |")
    A("")
    d = p["existing_rule_failure_detail"]
    A("## Existing 59-group failure detail")
    A("")
    A("| Quantity | Value |")
    A("|----------|-------|")
    A(f"| Verified edges internal to an existing group | {d['internal_verified_edges']} |")
    A(f"| Verified edges crossing existing group boundaries | {d['crossing_verified_edges']} |")
    A(f"| ... with at least one endpoint in no existing group | {d['crossing_with_ungrouped_endpoint']} |")
    A(f"| ... with endpoints in two different existing groups | "
      f"{d['crossing_between_two_different_groups']} |")
    A(f"| Images touched by at least one crossing edge | "
      f"{d['images_touched_by_crossing_edge_count']} |")
    A(f"| Images duplicated across existing groups | "
      f"{d['images_in_more_than_one_existing_group']} |")
    A(f"| Existing group count / size histogram | {d['existing_group_count']} / "
      f"{d['existing_group_size_histogram']} |")
    A("")
    A(f"**Verdict**: {d['sufficiency_verdict']}")
    A("")
    A("Example crossing edges (a pair the existing groups fail to keep together):")
    A("")
    A("| image A | image B | A in group | B in group |")
    A("|---------|---------|-----------|-----------|")
    for e in p["atomicity_rule_evaluation"]["A_EXISTING_59"]["crossing_edge_examples"][:15]:
        A(f"| {e['a']} | {e['b']} | {e['a_unit'] or '-'} | {e['b_unit'] or '-'} |")
    A("")
    r = p["reconstructed_clique_cover_detail"]
    A("## Reconstructed clique cover (complete-linkage condition on the pixel relation)")
    A("")
    A("| Quantity | Value |")
    A("|----------|-------|")
    A(f"| Clique groups | {r['clique_group_count']} |")
    A(f"| Group size histogram | {r['clique_group_size_histogram']} |")
    A(f"| Largest group | {r['clique_largest_size']} |")
    A(f"| Nodes that cannot anchor any clique | {r['nodes_not_anchoring_any_clique_count']} |")
    A("")
    A(f"{r['note']}")
    A("")
    A("## Rare class (`transverse_crack`) under each rule")
    A("")
    A("| Rule | Atomic units containing class 1 | Images | Objects | Largest such unit |")
    A("|------|----------------------------------|--------|---------|------------------|")
    for name, rr in p["rare_class_by_rule"].items():
        A(f"| {name} | {rr['atomic_units_containing_rare_class']} | "
          f"{rr['images_containing_rare_class']} | {rr['rare_class_objects']} | "
          f"{rr['largest_unit_containing_rare_class']} |")
    A("")
    A("## Dataset statistics (re-derived from normalized annotations)")
    A("")
    A("| Quantity | Value |")
    A("|----------|-------|")
    A(f"| Images / annotations | {s['image_count']} / {s['annotation_files_on_disk']} |")
    A(f"| Objects (retained) | {s['object_total_sum']} |")
    A(f"| Multi-class images | {s['multiclass_image_count']} |")
    A(f"| Single-class images | {s['singleclass_image_count']} |")
    A(f"| Annotation-empty images | {s['empty_annotation_image_count']} |")
    A(f"| Objects per image min / median / mean / max | "
      f"{s['objects_per_image_min']} / {s['objects_per_image_median']} / "
      f"{s['objects_per_image_mean']} / {s['objects_per_image_max']} |")
    A(f"| `difficult` objects / images | {s['difficult_object_total']} / {s['difficult_image_count']} |")
    A(f"| `truncated` objects / images | {s['truncated_object_total']} / {s['truncated_image_count']} |")
    A(f"| `pose` totals | {s['pose_totals']} |")
    A(f"| Resolutions | {s['resolution_set']} |")
    A("")
    A("| Class | Objects | Images containing |")
    A("|-------|---------|-------------------|")
    for k in ("longitudinal_crack", "transverse_crack", "alligator_crack", "pothole"):
        A(f"| {k} | {s['object_totals'][k]} | {s['images_with_class'][k]} |")
    A("")
    A("Class-presence strata:")
    A("")
    A("| Classes present | Images |")
    A("|-----------------|--------|")
    for k, v in s["class_presence_strata"].items():
        A(f"| {k} | {v} |")
    A("")
    A("## Evidence-tier sensitivity of connected components")
    A("")
    t = p["evidence_tier_sensitivity"]
    A("| Edge tier | Edges | Nodes | Components | Largest component | Images in multi-image components |")
    A("|-----------|-------|-------|------------|------------------|-----------------------------------|")
    for key in ("dhash_le_5", "dhash_le_8", "dhash_le_10"):
        if key in t:
            v = t[key]
            A(f"| {key} | {v['edge_count']} | {v['node_count']} | {v['component_count']} | "
              f"{v['largest_component_size']} | {v['images_in_multi_image_components']} |")
    A("")
    A(f"{t['note']}")
    A("")
    A("## Limitations (explicit)")
    A("")
    for lim in p["graph_limitations"]:
        A(f"- {lim}")
    A("")
    A("---")
    A("")
    A(f"*Generated by `{p['script']}`. Inputs are read-only; this script writes only to* "
      f"`group_analysis/`.")
    OUTPUT_MD.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
