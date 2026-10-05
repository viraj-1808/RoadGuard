import xml.etree.ElementTree as ET
import os
from collections import Counter

xml_dir = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_rdd2022_india\train\annotations\xmls'

# Expected mapping
expected = {
    'D00': 'longitudinal_crack',
    'D10': 'longitudinal_crack',
    'D20': 'longitudinal_crack',
    'D40': 'longitudinal_crack',
    'A00': 'alligator_crack',
    'A10': 'alligator_crack',
    'A20': 'alligator_crack',
    'A40': 'alligator_crack',
    'A50': 'alligator_crack',
    'B00': 'longitudinal_crack',
    'B10': 'longitudinal_crack',
    'B20': 'longitudinal_crack',
    'B30': 'longitudinal_crack',
    'B40': 'longitudinal_crack',
    'C00': 'pothole',
    'C10': 'pothole',
    'C20': 'pothole',
}

xml_files = sorted([f for f in os.listdir(xml_dir) if f.endswith('.xml')])
total = len(xml_files)
print(f'Total XML files: {total}')

# Check if all 1530 files exist (India_000001 to India_001530)
expected_files = set(f'India_{i:06d}.xml' for i in range(1, 1531))
actual_files = set(xml_files)
missing = expected_files - actual_files
extra = actual_files - expected_files
print(f'Missing files (expected but not found): {len(missing)}')
if missing:
    print(f'  Missing: {sorted(missing)[:20]}')
print(f'Extra files (found but not expected): {len(extra)}')
if extra:
    print(f'  Extra: {sorted(extra)[:20]}')

# Parse all XML files
class_counts = Counter()
obj_counts_per_file = []
malformed = []
structure_issues = []
empty_annotations = []
wrong_class_names = []
missing_fields = []

for xf in xml_files:
    path = os.path.join(xml_dir, xf)
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as e:
        malformed.append((xf, str(e)))
        continue

    # Check required fields
    filename_el = root.find('filename')
    size_el = root.find('size')
    width_el = size_el.find('width') if size_el is not None else None
    height_el = size_el.find('height') if size_el is not None else None
    depth_el = size_el.find('depth') if size_el is not None else None

    if filename_el is None or filename_el.text is None:
        missing_fields.append((xf, 'filename'))
    if size_el is None or width_el is None or height_el is None or depth_el is None:
        missing_fields.append((xf, 'size/width/height/depth'))

    objects = root.findall('object')
    obj_counts_per_file.append(len(objects))

    if len(objects) == 0:
        empty_annotations.append(xf)

    for obj in objects:
        name_el = obj.find('name')
        bndbox_el = obj.find('bndbox')
        if name_el is None or name_el.text is None:
            wrong_class_names.append((xf, 'missing name'))
            continue
        class_name = name_el.text.strip()
        class_counts[class_name] += 1

        if bndbox_el is None:
            structure_issues.append((xf, f'object missing bndbox: {class_name}'))
            continue
        xmin = bndbox_el.find('xmin')
        ymin = bndbox_el.find('ymin')
        xmax = bndbox_el.find('xmax')
        ymax = bndbox_el.find('ymax')
        if any(e is None or e.text is None for e in [xmin, ymin, xmax, ymax]):
            structure_issues.append((xf, f'incomplete bndbox: {class_name}'))

        # Check if class name is in expected mapping
        if class_name not in expected:
            wrong_class_names.append((xf, class_name))

print()
print('=== CLASS COUNTS (from XML, not manifest) ===')
for cls, cnt in sorted(class_counts.items()):
    mapped = expected.get(cls, 'UNKNOWN')
    print(f'  {cls}: {cnt} (maps to: {mapped})')
print(f'  Total objects: {sum(class_counts.values())}')

print()
print('=== MALFORMED XML FILES ===')
if malformed:
    for f, e in malformed:
        print(f'  {f}: {e}')
else:
    print('  None found')

print()
print('=== EMPTY ANNOTATIONS (images with no objects) ===')
if empty_annotations:
    print(f'  Count: {len(empty_annotations)}')
    for f in empty_annotations[:20]:
        print(f'  {f}')
    if len(empty_annotations) > 20:
        print(f'  ... and {len(empty_annotations) - 20} more')
else:
    print('  None found')

print()
print('=== STRUCTURE VERIFICATION ===')
print(f'  Missing filename: {len([x for x in missing_fields if x[1]=="filename"])}')
print(f'  Missing size fields: {len([x for x in missing_fields if x[1]=="size/width/height/depth"])}')
print(f'  Missing bndbox: {len([x for x in structure_issues if "bndbox" in x[1]])}')
print(f'  Incomplete bndbox: {len([x for x in structure_issues if "incomplete" in x[1]])}')

print()
print('=== UNEXPECTED CLASS NAMES ===')
if wrong_class_names:
    unique_wrong = set(c for _, c in wrong_class_names)
    print(f'  Unique unexpected classes: {unique_wrong}')
    print(f'  Total occurrences: {len(wrong_class_names)}')
else:
    print('  All class names are in expected mapping')

print()
print('=== OBJECTS PER FILE STATS ===')
if obj_counts_per_file:
    print(f'  Min: {min(obj_counts_per_file)}')
    print(f'  Max: {max(obj_counts_per_file)}')
    print(f'  Mean: {sum(obj_counts_per_file)/len(obj_counts_per_file):.1f}')
    print(f'  Median: {sorted(obj_counts_per_file)[len(obj_counts_per_file)//2]}')
    zero_files = sum(1 for c in obj_counts_per_file if c == 0)
    one_file = sum(1 for c in obj_counts_per_file if c == 1)
    print(f'  Files with 0 objects: {zero_files}')
    print(f'  Files with 1 object: {one_file}')
    print(f'  Files with 2+ objects: {sum(1 for c in obj_counts_per_file if c >= 2)}')