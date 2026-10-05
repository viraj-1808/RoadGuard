#!/usr/bin/env python3
"""
Independent split validator for RoadGuard AI project.
Validates split_manifest_fixed.json against raw data sources without trusting the manifest's own validation.
"""

import json
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
import hashlib

# Paths
BASE_DIR = r"C:\Users\viraj\Code_files\Github\RoadGuard AI"
XML_DIR = os.path.join(BASE_DIR, r"experiments\dataset\raw_rdd2022_india\train\annotations\xmls")
CORRELATION_GRAPH_PATH = os.path.join(BASE_DIR, r"experiments\dataset\normalized_rdd2022_india\group_analysis\correlation_graph.json")
SPLIT_MANIFEST_PATH = os.path.join(BASE_DIR, r"experiments\dataset\normalized_rdd2022_india\split_manifest_fixed.json")
MANIFEST_PATH = os.path.join(BASE_DIR, r"experiments\dataset\normalized_rdd2022_india\manifest.json")
NORMALIZED_ANNOTATIONS_DIR = os.path.join(BASE_DIR, r"experiments\dataset\normalized_rdd2022_india\train\annotations")
NORMALIZED_IMAGES_DIR = os.path.join(BASE_DIR, r"experiments\dataset\normalized_rdd2022_india\train\images")

# Expected class counts from XML annotations (final mapped classes)
EXPECTED_CLASS_COUNTS = {
    'longitudinal_crack': 498,
    'transverse_crack': 30,
    'alligator_crack': 645,
    'pothole': 3187
}
EXPECTED_TOTAL_OBJECTS = 4360
EXPECTED_TOTAL_IMAGES = 1530
EXPECTED_SPLIT_COUNTS = {
    'train': 1071,
    'val': 229,
    'test': 229
}
EXPECTED_TRANSVERSE_CRACK_TOTAL = 30

def read_xml_files():
    """Read all XML annotation files and extract object information."""
    print("Reading XML annotation files...")
    xml_files = [f for f in os.listdir(XML_DIR) if f.endswith('.xml')]
    
    # Data structures
    image_objects = defaultdict(list)  # image_id -> list of objects
    class_counts = defaultdict(int)    # class_name -> count
    image_dimensions = {}              # image_id -> (width, height)
    bboxes_valid = True
    
    for xml_file in xml_files:
        image_id = xml_file.replace('.xml', '')
        xml_path = os.path.join(XML_DIR, xml_file)
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Get image dimensions
            size_elem = root.find('size')
            if size_elem is not None:
                width = int(size_elem.find('width').text)
                height = int(size_elem.find('height').text)
                image_dimensions[image_id] = (width, height)
            
            # Process objects
            for obj in root.findall('object'):
                name_elem = obj.find('name')
                if name_elem is not None:
                    class_name = name_elem.text
                    
                    # Map raw D-classes to final classes
                    if class_name in ['D00', 'D01']:
                        final_class = 'longitudinal_crack'
                    elif class_name in ['D10', 'D11']:
                        final_class = 'transverse_crack'
                    elif class_name == 'D20':
                        final_class = 'alligator_crack'
                    elif class_name == 'D40':
                        final_class = 'pothole'
                    elif class_name in ['D43', 'D44', 'D50']:
                        # Excluded classes - skip
                        continue
                    else:
                        print(f"WARNING: Unknown class '{class_name}' in {xml_file}")
                        continue
                    
                    # Get bounding box
                    bndbox = obj.find('bndbox')
                    if bndbox is not None:
                        xmin = int(bndbox.find('xmin').text)
                        ymin = int(bndbox.find('ymin').text)
                        xmax = int(bndbox.find('xmax').text)
                        ymax = int(bndbox.find('ymax').text)
                        
                        # Validate bounding box
                        if xmin >= xmax or ymin >= ymax:
                            print(f"ERROR: Invalid bounding box in {xml_file}: ({xmin},{ymin},{xmax},{ymax})")
                            bboxes_valid = False
                        elif image_id in image_dimensions:
                            width, height = image_dimensions[image_id]
                            if xmin < 0 or ymin < 0 or xmax > width or ymax > height:
                                print(f"ERROR: Bounding box out of image bounds in {xml_file}: ({xmin},{ymin},{xmax},{ymax}) for image {width}x{height}")
                                bboxes_valid = False
                    
                    # Add object
                    obj_data = {
                        'class': final_class,
                        'bbox': (xmin, ymin, xmax, ymax) if bndbox is not None else None
                    }
                    image_objects[image_id].append(obj_data)
                    class_counts[final_class] += 1
                    
        except Exception as e:
            print(f"ERROR processing {xml_file}: {e}")
            return None, None, None, None
    
    return image_objects, class_counts, image_dimensions, bboxes_valid

def read_correlation_graph():
    """Read correlation graph and extract connected components."""
    print("Reading correlation graph...")
    try:
        with open(CORRELATION_GRAPH_PATH, 'r') as f:
            graph_data = json.load(f)
        
        # Extract components from component_manifest
        components = graph_data['component_manifest']['components']
        
        # Build component mapping: image_id -> component_id
        image_to_component = {}
        component_sizes = defaultdict(int)
        
        for component in components:
            component_id = component['component_id']
            members = component['members']
            component_sizes[component_id] = len(members)
            
            for member in members:
                image_to_component[member] = component_id
        
        return image_to_component, component_sizes, components
    except Exception as e:
        print(f"ERROR reading correlation graph: {e}")
        return None, None, None

def read_split_manifest():
    """Read split manifest and extract assignments."""
    print("Reading split manifest...")
    try:
        with open(SPLIT_MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
        
        assignments = manifest['assignments']
        
        # Build split mapping: image_id -> split
        image_to_split = {}
        split_counts = defaultdict(int)
        
        for image_id, split in assignments.items():
            image_to_split[image_id] = split
            split_counts[split] += 1
        
        return image_to_split, split_counts, manifest
    except Exception as e:
        print(f"ERROR reading split manifest: {e}")
        return None, None, None

def compute_checksum(filepath):
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Main validation function."""
    print("=" * 60)
    print("RoadGuard AI Split Validator - Independent Verification")
    print("=" * 60)
    
    # Track overall pass/fail
    all_checks_passed = True
    
    # Read data
    image_objects, class_counts, image_dimensions, bboxes_valid = read_xml_files()
    if image_objects is None:
        print("FAIL: Could not read XML files")
        return 1
    
    image_to_component, component_sizes, components = read_correlation_graph()
    if image_to_component is None:
        print("FAIL: Could not read correlation graph")
        return 1
    
    image_to_split, split_counts, manifest = read_split_manifest()
    if image_to_split is None:
        print("FAIL: Could not read split manifest")
        return 1
    
    # Check 1: All 1530 images assigned to exactly one split (no duplicates, no missing)
    print("\n1. Checking image assignment completeness and uniqueness...")
    xml_image_ids = set([f.replace('.xml', '') for f in os.listdir(XML_DIR) if f.endswith('.xml')])
    manifest_image_ids = set(image_to_split.keys())
    
    missing_in_manifest = xml_image_ids - manifest_image_ids
    extra_in_manifest = manifest_image_ids - xml_image_ids
    duplicate_check = len(image_to_split) == len(set(image_to_split.keys()))  # Should always be true for dict
    
    check1_pass = (len(missing_in_manifest) == 0 and 
                   len(extra_in_manifest) == 0 and 
                   duplicate_check and
                   len(xml_image_ids) == EXPECTED_TOTAL_IMAGES)
    
    print(f"   Total XML images: {len(xml_image_ids)}")
    print(f"   Images in manifest: {len(manifest_image_ids)}")
    print(f"   Missing from manifest: {len(missing_in_manifest)}")
    print(f"   Extra in manifest: {len(extra_in_manifest)}")
    if missing_in_manifest:
        print(f"   First few missing: {sorted(list(missing_in_manifest))[:5]}")
    if extra_in_manifest:
        print(f"   First few extra: {sorted(list(extra_in_manifest))[:5]}")
    print(f"   Result: {'PASS' if check1_pass else 'FAIL'}")
    if not check1_pass:
        all_checks_passed = False
    
    # Check 2: Class totals from XML
    print("\n2. Checking class totals from XML annotations...")
    check2_pass = True
    for class_name, expected_count in EXPECTED_CLASS_COUNTS.items():
        actual_count = class_counts.get(class_name, 0)
        if actual_count != expected_count:
            print(f"   {class_name}: expected {expected_count}, got {actual_count}")
            check2_pass = False
        else:
            print(f"   {class_name}: {actual_count} (PASS)")
    
    total_objects = sum(class_counts.values())
    if total_objects != EXPECTED_TOTAL_OBJECTS:
        print(f"   Total objects: expected {EXPECTED_TOTAL_OBJECTS}, got {total_objects}")
        check2_pass = False
    else:
        print(f"   Total objects: {total_objects} (PASS)")
    
    print(f"   Result: {'PASS' if check2_pass else 'FAIL'}")
    if not check2_pass:
        all_checks_passed = False
    
    # Check 3: Split ratios
    print("\n3. Checking split ratios...")
    check3_pass = True
    for split_name, expected_count in EXPECTED_SPLIT_COUNTS.items():
        actual_count = split_counts.get(split_name, 0)
        if actual_count != expected_count:
            print(f"   {split_name}: expected {expected_count}, got {actual_count}")
            check3_pass = False
        else:
            print(f"   {split_name}: {actual_count} (PASS)")
    
    total_assigned = sum(split_counts.values())
    if total_assigned != EXPECTED_TOTAL_IMAGES:
        print(f"   Total assigned: expected {EXPECTED_TOTAL_IMAGES}, got {total_assigned}")
        check3_pass = False
    else:
        print(f"   Total assigned: {total_assigned} (PASS)")
    
    print(f"   Result: {'PASS' if check3_pass else 'FAIL'}")
    if not check3_pass:
        all_checks_passed = False
    
    # Check 4: Atomicity - every connected component's members are in the same split
    print("\n4. Checking atomicity (connected components in same split)...")
    check4_pass = True
    component_violations = []
    
    for component in components:
        component_id = component['component_id']
        members = component['members']
        
        if len(members) > 1:  # Only check multi-member components
            splits_in_component = set()
            for member in members:
                if member in image_to_split:
                    splits_in_component.add(image_to_split[member])
                else:
                    print(f"   WARNING: Member {member} not found in manifest")
            
            if len(splits_in_component) > 1:
                component_violations.append((component_id, list(splits_in_component), len(members)))
                check4_pass = False
    
    if component_violations:
        print(f"   Found {len(component_violations)} components split across multiple splits:")
        for comp_id, splits, size in component_violations[:5]:  # Show first 5
            print(f"     Component {comp_id} (size {size}): splits {splits}")
        if len(component_violations) > 5:
            print(f"     ... and {len(component_violations) - 5} more")
    else:
        print("   All connected components are assigned to single splits")
    
    print(f"   Result: {'PASS' if check4_pass else 'FAIL'}")
    if not check4_pass:
        all_checks_passed = False
    
    # Check 5: Transverse crack objects total = 30
    print("\n5. Checking transverse crack objects total...")
    transverse_count = class_counts.get('transverse_crack', 0)
    check5_pass = (transverse_count == EXPECTED_TRANSVERSE_CRACK_TOTAL)
    print(f"   Transverse crack objects: expected {EXPECTED_TRANSVERSE_CRACK_TOTAL}, got {transverse_count}")
    print(f"   Result: {'PASS' if check5_pass else 'FAIL'}")
    if not check5_pass:
        all_checks_passed = False
    
    # Check 6: No image appears in multiple splits (already covered by dict uniqueness, but double-check)
    print("\n6. Checking for duplicate image assignments...")
    # This is inherently true for a dictionary, but let's verify no image appears in multiple split lists
    split_to_images = defaultdict(list)
    for image_id, split in image_to_split.items():
        split_to_images[split].append(image_id)
    
    duplicates_found = False
    for split_name, images in split_to_images.items():
        if len(images) != len(set(images)):
            print(f"   Duplicate images found in {split_name} split")
            duplicates_found = True
    
    check6_pass = not duplicates_found
    print(f"   Result: {'PASS' if check6_pass else 'FAIL'}")
    if not check6_pass:
        all_checks_passed = False
    
    # Check 7: Every assigned image actually exists on disk (in normalized dataset)
    print("\n7. Checking assigned images exist on disk...")
    missing_images = []
    for image_id in image_to_split.keys():
        # Check normalized image
        img_path = os.path.join(NORMALIZED_IMAGES_DIR, f"{image_id}.jpg")
        if not os.path.exists(img_path):
            missing_images.append((image_id, "image"))
            continue
        
        # Check normalized annotation
        ann_path = os.path.join(NORMALIZED_ANNOTATIONS_DIR, f"{image_id}.xml")
        if not os.path.exists(ann_path):
            missing_images.append((image_id, "annotation"))
            continue
    
    check7_pass = len(missing_images) == 0
    if missing_images:
        print(f"   Missing files for {len(missing_images)} images:")
        for image_id, file_type in missing_images[:5]:
            print(f"     {image_id}: missing {file_type}")
        if len(missing_images) > 5:
            print(f"     ... and {len(missing_images) - 5} more")
    else:
        print(f"   All {len(image_to_split)} assigned images have corresponding files on disk")
    print(f"   Result: {'PASS' if check7_pass else 'FAIL'}")
    if not check7_pass:
        all_checks_passed = False
    
    # Check 8: Every assigned annotation actually exists on disk (same as check 7 really)
    print("\n8. Checking assigned annotations exist on disk...")
    # This is essentially the same as check 7, but let's be explicit
    missing_annotations = []
    for image_id in image_to_split.keys():
        ann_path = os.path.join(NORMALIZED_ANNOTATIONS_DIR, f"{image_id}.xml")
        if not os.path.exists(ann_path):
            missing_annotations.append(image_id)
    
    check8_pass = len(missing_annotations) == 0
    if missing_annotations:
        print(f"   Missing annotations for {len(missing_annotations)} images:")
        print(f"     First few: {missing_annotations[:5]}")
    else:
        print(f"   All {len(image_to_split)} assigned annotations exist on disk")
    print(f"   Result: {'PASS' if check8_pass else 'FAIL'}")
    if not check8_pass:
        all_checks_passed = False
    
    # Check 9: Bounding boxes are valid (x1<x2, y1<y2, within image dimensions)
    print("\n9. Checking bounding box validity...")
    check9_pass = bboxes_valid
    print(f"   Result: {'PASS' if check9_pass else 'FAIL'}")
    if not check9_pass:
        all_checks_passed = False
    
    # Check 10: Class IDs are only 0-3 (we're using string class names, but let's verify mapping)
    print("\n10. Checking class ID mapping validity...")
    valid_classes = set(['longitudinal_crack', 'transverse_crack', 'alligator_crack', 'pothole'])
    actual_classes = set(class_counts.keys())
    invalid_classes = actual_classes - valid_classes
    
    check10_pass = len(invalid_classes) == 0
    if invalid_classes:
        print(f"   Invalid class names found: {invalid_classes}")
    else:
        print(f"   All class names are valid: {actual_classes}")
    print(f"   Result: {'PASS' if check10_pass else 'FAIL'}")
    if not check10_pass:
        all_checks_passed = False
    
    # Check 11: Deterministic checksum matches (verify manifest checksum)
    print("\n11. Checking deterministic checksum...")
    # Compute checksum of split_manifest_fixed.json
    manifest_checksum = compute_checksum(SPLIT_MANIFEST_PATH)
    expected_checksum = manifest['validation']['V8_checksum']['sha256']
    
    check11_pass = (manifest_checksum == expected_checksum)
    print(f"   Manifest checksum:")
    print(f"     Computed:  {manifest_checksum}")
    print(f"     Expected:  {expected_checksum}")
    print(f"   Result: {'PASS' if check11_pass else 'FAIL'}")
    if not check11_pass:
        all_checks_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    checks = [
        ("Image assignment completeness", check1_pass),
        ("Class totals from XML", check2_pass),
        ("Split ratios", check3_pass),
        ("Atomicity (connected components)", check4_pass),
        ("Transverse crack objects total", check5_pass),
        ("No duplicate assignments", check6_pass),
        ("Assigned images exist on disk", check7_pass),
        ("Assigned annotations exist on disk", check8_pass),
        ("Bounding box validity", check9_pass),
        ("Class ID mapping validity", check10_pass),
        ("Deterministic checksum", check11_pass)
    ]
    
    passed_count = sum(1 for _, passed in checks if passed)
    total_count = len(checks)
    
    for check_name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"{check_name:<35} [{status}]")
    
    print("-" * 60)
    print(f"Overall: {passed_count}/{total_count} checks passed")
    print(f"Result: {'PASS - All checks passed' if all_checks_passed else 'FAIL - Some checks failed'}")
    print("=" * 60)
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    exit(main())