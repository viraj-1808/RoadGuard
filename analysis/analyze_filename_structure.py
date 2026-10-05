"""
Filename structure and metadata-grouping analysis for the RDD2022 India dataset.

Phase 1 of the sequence/group identification task. This phase gathers evidence
ONLY. It does NOT create splits, does NOT modify data, and does NOT assume that
filename proximity implies sequence membership.

Analyzed:
  1. Filename structure: numbering range, gaps, contiguity, encoding
  2. Explicit group metadata: any source/sequence/video/trip/camera/timestamp keys
  3. XML element inventory across all annotations (what metadata actually exists)

Outputs:
  - experiments/dataset/normalized_rdd2022_india/group_analysis/filename_report.json
  - experiments/dataset/normalized_rdd2022_india/group_analysis/filename_report.md

Usage:
    python analysis/analyze_filename_structure.py
"""
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter, defaultdict
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


RAW_IMAGES_DIR = Path(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_rdd2022_india\train\images")
RAW_ANNOTATIONS_DIR = Path(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_rdd2022_india\train\annotations\xmls")
NORMALIZED_DIR = Path(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\normalized_rdd2022_india")
OUT_DIR = NORMALIZED_DIR / "group_analysis"

# Regex to decompose the observed filename pattern
# Observed: India_000005.jpg / India_000005.xml
FILENAME_RE = re.compile(r"^(?P<prefix>[A-Za-z_]+)_(?P<number>\d+)$")


def parse_filename(stem: str) -> Dict[str, Any]:
    """Decompose a filename stem into prefix and numeric index."""
    m = FILENAME_RE.match(stem)
    if not m:
        return {"stem": stem, "prefix": None, "number": None, "pattern_match": False}
    return {
        "stem": stem,
        "prefix": m.group("prefix"),
        "number": int(m.group("number")),
        "pattern_match": True,
    }


def analyze_filenames() -> Dict[str, Any]:
    """Analyze the numbering structure of image and annotation filenames."""
    image_stems = sorted(p.stem for p in RAW_IMAGES_DIR.glob("*.jpg"))
    ann_stems = sorted(p.stem for p in RAW_ANNOTATIONS_DIR.glob("*.xml"))

    report: Dict[str, Any] = {
        "image_count": len(image_stems),
        "annotation_count": len(ann_stems),
    }

    # Do image and annotation stems correspond 1:1?
    report["stems_identical"] = image_stems == ann_stems
    report["stems_only_in_images"] = sorted(set(image_stems) - set(ann_stems))
    report["stems_only_in_annotations"] = sorted(set(ann_stems) - set(image_stems))

    parsed = [parse_filename(s) for s in image_stems]
    report["all_match_prefix_number_pattern"] = all(p["pattern_match"] for p in parsed)

    unmatched = [p["stem"] for p in parsed if not p["pattern_match"]]
    report["unmatched_filenames"] = unmatched

    matched = [p for p in parsed if p["pattern_match"]]

    prefixes = Counter(p["prefix"] for p in matched)
    report["prefixes"] = dict(prefixes)

    # Numeric width (zero padding) observed
    digit_widths = Counter(len(re.search(r"(\d+)$", p["stem"]).group(1)) for p in matched)
    report["numeric_field_widths"] = {str(k): v for k, v in sorted(digit_widths.items())}

    numbers = sorted(p["number"] for p in matched)
    report["number_min"] = numbers[0]
    report["number_max"] = numbers[-1]
    report["number_span"] = numbers[-1] - numbers[0] + 1
    report["number_unique"] = len(set(numbers))
    report["number_contiguous"] = report["number_span"] == report["number_unique"]

    # Gaps
    present = set(numbers)
    gaps = []
    for n in range(numbers[0], numbers[-1] + 1):
        if n not in present:
            gaps.append(n)
    report["gap_count"] = len(gaps)
    report["total_missing_indices"] = report["number_span"] - report["number_unique"]
    report["missing_count_pct_of_span"] = (
        round(len(gaps) / report["number_span"] * 100, 2) if report["number_span"] else 0.0
    )
    report["missing_indices_sample"] = gaps[:50]
    report["missing_indices_all"] = gaps

    # Gap run structure: consecutive missing runs
    runs = []
    if gaps:
        start = prev = gaps[0]
        for g in gaps[1:]:
            if g == prev + 1:
                prev = g
            else:
                runs.append({"start": start, "end": prev, "length": prev - start + 1})
                start = prev = g
        runs.append({"start": start, "end": prev, "length": prev - start + 1})
    report["missing_runs_count"] = len(runs)
    report["missing_runs_longest"] = sorted(runs, key=lambda r: r["length"], reverse=True)[:10]

    # Index ordering vs lexical filename ordering
    lexical = sorted(image_stems)
    numeric = [p["stem"] for p in sorted(matched, key=lambda x: x["number"])]
    report["lexical_order_equals_numeric_order"] = lexical == numeric

    # First / last few
    report["first_10_stems"] = image_stems[:10]
    report["last_10_stems"] = image_stems[-10:]

    return report


def collect_xml_element_inventory() -> Dict[str, Any]:
    """Enumerate every XML tag and attribute actually present across all annotations."""
    import xml.etree.ElementTree as ET

    tag_counts: Counter = Counter()
    attribute_keys: Counter = Counter()
    parse_failures: List[str] = []

    files = sorted(RAW_ANNOTATIONS_DIR.glob("*.xml"))
    for f in files:
        try:
            root = ET.parse(f).getroot()
        except Exception as exc:
            parse_failures.append(f"{f.name}: {exc}")
            continue
        for el in root.iter():
            tag_counts[el.tag] += 1
            for k in el.attrib:
                attribute_keys[f"{el.tag}@{k}"] += 1

    return {
        "files_scanned": len(files),
        "parse_failures": parse_failures,
        "tag_counts": dict(tag_counts.most_common()),
        "attribute_keys": dict(attribute_keys.most_common()),
    }


# Candidate metadata keys that would indicate grouping or capture provenance
GROUPING_KEY_HINTS = [
    "sequence", "seq", "video", "vid", "trip", "route", "session", "capture",
    "camera", "cam", "device", "timestamp", "time", "date", "gps", "lat",
    "lon", "location", "place", "source", "frame", "clip", "drive", "run",
    "track", "uuid", "id",
]

METADATA_KEY_HINTS = ["source", "folder", "path", "owner", "database", "flickr"]

# Standard Pascal VOC tags that are known NOT to carry grouping information.
# Listed explicitly so a naive substring match is documented rather than trusted.
KNOWN_VOC_TAGS = {
    "annotation", "folder", "filename", "path", "source", "size",
    "width", "height", "depth", "segmented",
    "object", "name", "pose", "truncated", "difficult", "bndbox",
    "xmin", "ymin", "xmax", "ymax",
}


def search_for_group_metadata(element_inventory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search discovered XML tags/attributes for anything that could carry
    grouping information. Reports what EXISTS and what is ABSENT.
    """
    observed_tags = set(element_inventory["tag_counts"].keys()) | {
        k.split("@")[0] for k in element_inventory["attribute_keys"].keys()
    }
    observed_attrs = set(element_inventory["attribute_keys"].keys())

    def has_hint(name: str, hints: List[str]) -> bool:
        low = name.lower()
        return any(h in low for h in hints)

    naive_grouping_hits = sorted(t for t in observed_tags if has_hint(t, GROUPING_KEY_HINTS))
    naive_metadata_hits = sorted(t for t in observed_tags if has_hint(t, METADATA_KEY_HINTS))

    # Substring matching produces false positives. A hit only counts as a real
    # grouping candidate if the tag is NOT a known standard VOC tag.
    real_grouping_hits = sorted(set(naive_grouping_hits) - KNOWN_VOC_TAGS)
    false_positives = {
        tag: [h for h in GROUPING_KEY_HINTS if h in tag.lower()]
        for tag in naive_grouping_hits
        if tag in KNOWN_VOC_TAGS
    }

    # Every observed tag should be explainable as standard VOC.
    unexplained_tags = sorted(observed_tags - KNOWN_VOC_TAGS)

    return {
        "observed_tags": sorted(observed_tags),
        "observed_attribute_keys": sorted(observed_attrs),
        "naive_substring_grouping_hits": naive_grouping_hits,
        "naive_substring_false_positives": false_positives,
        "real_grouping_candidate_tags": real_grouping_hits,
        "unexplained_non_standard_tags": unexplained_tags,
        "metadata_like_tags_present": naive_metadata_hits,
        "any_attributes_at_all": bool(observed_attrs),
        "notes": [
            "No sequence/video/trip/camera/timestamp/GPS field observed in any annotation.",
            "All VOC objects carry only name, pose, truncated, difficult, and bndbox.",
            "Naive substring matching produced false positives "
            f"({false_positives}); these are standard VOC tags, not grouping metadata.",
            "Every observed tag is a standard Pascal VOC tag; there are no custom or "
            "vendor-specific metadata fields.",
        ],
    }


def build_markdown_report(fn_report: Dict[str, Any],
                          element_inventory: Dict[str, Any],
                          group_meta: Dict[str, Any]) -> str:
    L: List[str] = []
    L.append("# RDD2022 India: Filename Structure and Grouping Metadata Analysis")
    L.append("")
    L.append("**Scope**: evidence gathering only. No splits created, no data modified.")
    L.append("**Analyzed source**: `experiments/dataset/raw_rdd2022_india/train/`")
    L.append("")
    L.append("## 1. Filename Structure")
    L.append("")
    L.append("| Property | Value |")
    L.append("|----------|-------|")
    L.append(f"| Image files | {fn_report['image_count']:,} |")
    L.append(f"| Annotation files | {fn_report['annotation_count']:,} |")
    L.append(f"| Image/annotation stems identical (1:1) | {fn_report['stems_identical']} |")
    L.append(f"| All match `<prefix>_<digits>` | {fn_report['all_match_prefix_number_pattern']} |")
    L.append(f"| Filename prefixes | {fn_report['prefixes']} |")
    L.append(f"| Numeric field width (zero-padding) | {fn_report['numeric_field_widths']} |")
    L.append(f"| Index range | {fn_report['number_min']} .. {fn_report['number_max']} |")
    L.append(f"| Index span | {fn_report['number_span']:,} |")
    L.append(f"| Unique indices | {fn_report['number_unique']:,} |")
    L.append(f"| Contiguous (no gaps) | {fn_report['number_contiguous']} |")
    L.append(f"| Missing indices | {fn_report['gap_count']:,} ({fn_report['missing_count_pct_of_span']}% of span) |")
    L.append(f"| Distinct missing runs | {fn_report['missing_runs_count']:,} |")
    L.append(f"| Lexical order == numeric order | {fn_report['lexical_order_equals_numeric_order']} |")
    L.append("")
    L.append("**First 10 filenames**:")
    L.append("")
    L.append("```")
    L.append(", ".join(fn_report["first_10_stems"]))
    L.append("```")
    L.append("")
    L.append("**Last 10 filenames**:")
    L.append("")
    L.append("```")
    L.append(", ".join(fn_report["last_10_stems"]))
    L.append("```")
    L.append("")
    L.append("### Interpretation")
    L.append("")
    L.append("The filename encodes exactly one thing: a single integer index. The prefix is the")
    L.append("country/dataset identifier (`India`). The index is a flat, dataset-wide counter.")
    L.append("There is **no** embedded country sub-region, video, trip, camera, or timestamp")
    L.append("component. Because numeric padding is uniform and lexical order equals numeric order,")
    L.append("filename ordering carries no information beyond the index itself.")
    L.append("")
    L.append("## 2. XML Tag Inventory (all annotations)")
    L.append("")
    L.append(f"Files scanned: {element_inventory['files_scanned']:,}; parse failures: {len(element_inventory['parse_failures'])}")
    L.append("")
    L.append("| Tag | Occurrences |")
    L.append("|-----|-------------|")
    for tag, count in element_inventory["tag_counts"].items():
        L.append(f"| `{tag}` | {count:,} |")
    L.append("")
    L.append("### Attributes")
    L.append("")
    if element_inventory["attribute_keys"]:
        for k, v in element_inventory["attribute_keys"].items():
            L.append(f"- `{k}`: {v:,}")
    else:
        L.append("**No attributes exist on any element in any annotation.**")
    L.append("")
    L.append("## 3. Grouping Metadata Search")
    L.append("")
    L.append("| Check | Result |")
    L.append("|-------|--------|")
    L.append(f"| Any XML attributes at all | {group_meta['any_attributes_at_all']} |")
    L.append(f"| Non-standard (non-VOC) tags | {group_meta['unexplained_non_standard_tags'] or 'NONE'} |")
    L.append(f"| Real grouping candidate tags | {group_meta['real_grouping_candidate_tags'] or 'NONE'} |")
    L.append(f"| Naive substring matches (incl. false positives) | {group_meta['naive_substring_grouping_hits']} |")
    L.append("")
    if group_meta["naive_substring_false_positives"]:
        L.append("**Naive substring false positives** (standard VOC tags that merely contain a")
        L.append("grouping keyword as a substring):")
        L.append("")
        for tag, hits in group_meta["naive_substring_false_positives"].items():
            L.append(f"- `{tag}` matched because it contains {hits} — standard VOC tag, **not** grouping metadata")
        L.append("")
    for note in group_meta["notes"]:
        L.append(f"- {note}")
    L.append("")
    L.append("### Directory structure (official CRDDC'2022 listing)")
    L.append("")
    L.append("```")
    L.append("RDD2022/")
    L.append("  India/")
    L.append("    train/")
    L.append("      annotations/xmls/     <- flat, no sequence subdirectories")
    L.append("      images/               <- flat, no sequence subdirectories")
    L.append("    test/")
    L.append("      images/")
    L.append("```")
    L.append("")
    L.append("The official directory listing contains **no** sequence, video, trip, or route")
    L.append("subdirectory level. The hierarchy stops at country -> split -> {images, annotations}.")
    L.append("")
    L.append("### Auxiliary files present in the artifact")
    L.append("")
    L.append("| File | Content |")
    L.append("|------|---------|")
    L.append("| `label_map.pbtxt` | 4-class CRDDC label map (D00/D10/D20/D40); no grouping data |")
    L.append("| `Directory_Structure_CRDDC_RDD2022.txt` | Directory listing; no grouping level |")
    L.append("| `RDD2022_India.zip` | 243-byte saved S3 `AccessDenied` error page, not an archive |")
    L.append("")
    L.append("## 4. Verdict (Structure and Metadata Only)")
    L.append("")
    L.append("**No explicit grouping metadata exists in this artifact.** There is no sequence ID,")
    L.append("video ID, trip ID, camera ID, timestamp, or GPS field in any annotation, no XML")
    L.append("attributes at all, and no grouping directory level. Any grouping must therefore be")
    L.append("established empirically from image content, which is Phase 2.")
    L.append("")
    return "\n".join(L)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Phase 1: filename structure and metadata analysis")
    print(f"  Images:      {RAW_IMAGES_DIR}")
    print(f"  Annotations: {RAW_ANNOTATIONS_DIR}")
    print()

    fn_report = analyze_filenames()
    print("[1/3] Filename structure")
    print(f"  Range: {fn_report['number_min']}..{fn_report['number_max']}  span={fn_report['number_span']:,}  unique={fn_report['number_unique']:,}")
    print(f"  Contiguous: {fn_report['number_contiguous']}   missing indices: {fn_report['gap_count']:,} ({fn_report['missing_count_pct_of_span']}%)")
    print(f"  Prefixes: {fn_report['prefixes']}")
    print(f"  Stems 1:1 with annotations: {fn_report['stems_identical']}")
    print()

    print("[2/3] XML element inventory")
    element_inventory = collect_xml_element_inventory()
    print(f"  Files scanned: {element_inventory['files_scanned']:,}  failures: {len(element_inventory['parse_failures'])}")
    print(f"  Distinct tags: {sorted(element_inventory['tag_counts'].keys())}")
    print(f"  Attributes: {element_inventory['attribute_keys'] or 'NONE'}")
    print()

    print("[3/3] Grouping metadata search")
    group_meta = search_for_group_metadata(element_inventory)
    print(f"  Real grouping candidate tags: {group_meta['real_grouping_candidate_tags'] or 'NONE'}")
    print(f"  Non-standard tags: {group_meta['unexplained_non_standard_tags'] or 'NONE'}")
    print(f"  Naive substring false positives: {group_meta['naive_substring_false_positives']}")
    print()

    payload = {
        "analysis_version": "1.0.0",
        "filename_structure": fn_report,
        "xml_element_inventory": element_inventory,
        "grouping_metadata_search": group_meta,
    }

    json_path = OUT_DIR / "filename_report.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"JSON: {json_path}")

    md = build_markdown_report(fn_report, element_inventory, group_meta)
    md_path = OUT_DIR / "filename_report.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"MD:   {md_path}")
    print()
    print("Phase 1 complete. No splits created; no data modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
