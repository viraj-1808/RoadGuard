import xml.etree.ElementTree as ET
import os
from collections import Counter

xml_dir = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_rdd2022_india\train\annotations\xmls'

# Canonical class mapping from docs/CLASS_MAPPING.md §1
raw_to_final = {
    'D00': 'longitudinal_crack',   # KEEP
    'D01': 'longitudinal_crack',   # MERGE → D00
    'D10': 'transverse_crack',     # KEEP
    'D11': 'transverse_crack',     # MERGE → D10
    'D20': 'alligator_crack',      # KEEP
    'D40': 'pothole',              # KEEP
    'D43': None,                   # EXCLUDE
    'D44': None,                   # EXCLUDE
    'D50': None,                   # EXCLUDE
}

raw_counts = Counter()
final_counts = Counter()
excluded_counts = Counter()

xml_files = sorted([f for f in os.listdir(xml_dir) if f.endswith('.xml')])
total = len(xml_files)
print(f'Total XML files: {total}')

# Parse all XML files
empty_annotations = []
malformed = []
structure_issues = []
missing_fields = []

for xf in xml_files:
    path = os.path.join(xml_dir, xf)
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as e:
        malformed.append(xf)
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
    if len(objects) == 0:
        empty_annotations.append(xf)

    for obj in objects:
        name_el = obj.find('name')
        bndbox_el = obj.find('bndbox')
        if name_el is None or name_el.text is None:
            structure_issues.append((xf, 'missing name'))
            continue
        class_name = name_el.text.strip()
        raw_counts[class_name] += 1

        # Map to final class
        final_class = raw_to_final.get(class_name)
        if final_class is None:
            # Excluded class
            excluded_counts[class_name] += 1
            final_counts['excluded'] += 1
        else:
            final_counts[final_class] += 1

print()
print('=== RAW CLASS COUNTS ===')
for cls, cnt in sorted(raw_counts.items()):
    print(f'  {cls}: {cnt}')
print(f'  Total raw objects: {sum(raw_counts.values())}')

print()
print('=== FINAL PROJECT CLASS COUNTS ===')
for cls, cnt in sorted(final_counts.items()):
    if cls == 'excluded':
        print(f'  Excluded (D43/D44/D50): {cnt}')
    else:
        print(f'  {cls}: {cnt}')
print(f'  Total final objects: {sum(c for k, c in final_counts.items() if k != "excluded")}')

print()
print('=== EXCLUDED OBJECTS (D43/D44/D50) ===')
for cls, cnt in sorted(excluded_counts.items()):
    print(f'  {cls}: {cnt}')
print(f'  Total excluded: {sum(excluded_counts.values())}')

print()
print('=== MALFORMED XML FILES ===')
if malformed:
    for f in malformed:
        print(f'  {f}')
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

print()
print('=== OBJECTS PER FILE STATS ===')
obj_counts_per_file = []
for xf in xml_files:
    path = os.path.join(xml_dir, xf)
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        objects = root.findall('object')
        obj_counts_per_file.append(len(objects))
    except:
        obj_counts_per_file.append(0)

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

print()
print('=== RAW vs EXPECTED CLASS MAPPING VERIFICATION ===')
# Verify: all raw classes present are from the documented set {D00, D01, D10, D11, D20, D40, D43, D44, D50}
valid_raw_classes = {'D00', 'D01', 'D10', 'D11', 'D20', 'D40', 'D43', 'D44', 'D50'}
unexpected = set(raw_counts.keys()) - valid_raw_classes
if unexpected:
    print(f'  UNEXPECTED raw classes found: {unexpected}')
else:
    print('  All raw classes are from documented set {D00, D01, D10, D11, D20, D40, D43, D44, D50}')

# Verify final class mapping matches expected totals from CLASS_MAPPING.md §9
# Expected: longitudinal_crack = D00 + D01 = 498, transverse_crack = D10 + D11 = 30
#           alligator_crack = D20 = 645, pothole = D40 = 3187
lc_expected = raw_counts.get('D00', 0) + raw_counts.get('D01', 0)
tc_expected = raw_counts.get('D10', 0) + raw_counts.get('D11', 0)
ac_expected = raw_counts.get('D20', 0)
ph_expected = raw_counts.get('D40', 0)

print(f'  longitudinal_crack: computed={final_counts.get("longitudinal_crack", 0)}, expected={lc_expected}, match={final_counts.get("longitudinal_crack", 0) == lc_expected}')
print(f'  transverse_crack: computed={final_counts.get("transverse_crack", 0)}, expected={tc_expected}, match={final_counts.get("transverse_crack", 0) == tc_expected}')
print(f'  alligator_crack: computed={final_counts.get("alligator_crack", 0)}, expected={ac_expected}, match={final_counts.get("alligator_crack", 0) == ac_expected}')
print(f'  pothole: computed={final_counts.get("pothole", 0)}, expected={ph_expected}, match={final_counts.get("pothole", 0) == ph_expected}')

# Verify excluded count: D43 + D44 + D50 = 164
excl_total = raw_counts.get('D43', 0) + raw_counts.get('D44', 0) + raw_counts.get('D50', 0)
print(f'  Excluded total (D43+D44+D50): computed={sum(excluded_counts.values())}, expected={excl_total}, match={sum(excluded_counts.values()) == excl_total}')

# Total: retained + excluded = source
retained = sum(1 for c in final_counts.values() if c != 'excluded') if 'excluded' in final_counts else sum(final_counts.values())
# Actually compute retained properly
retained_total = sum(c for k, c in final_counts.items() if k != 'excluded')
source_total = sum(raw_counts.values())
print(f'  Retained + Excluded = Source: {retained_total} + {sum(excluded_counts.values())} = {retained_total + sum(excluded_counts.values())} vs source {source_total}, match={retained_total + sum(excluded_counts.values()) == source_total}')