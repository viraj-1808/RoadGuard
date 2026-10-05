import json

f = open('C:/Users/viraj/Code_files/Github/RoadGuard AI/experiments/dataset/normalized_rdd2022_india/manifest.json')
m = json.load(f)

# Check original_class_counts for TC images
tc = [img for img in m['image_manifest'] if img.get('final_class_counts', {}).get('transverse_crack', 0) > 0]
print(f'TC images: {len(tc)}')

# Check retained_object_count
total_retained = sum(img.get('retained_object_count', 0) for img in tc)
print(f'Total retained objects in TC images: {total_retained}')

# Check original_class_counts for TC objects
tc_retained = 0
for img in tc:
    orig = img.get('original_class_counts', {})
    tc_retained += orig.get('D10', 0) + orig.get('D11', 0)
print(f'TC objects from original_class_counts (D10+D11): {tc_retained}')

# Check final_class_counts for TC
tc_final = sum(img['final_class_counts']['transverse_crack'] for img in tc)
print(f'TC objects from final_class_counts: {tc_final}')

# Check what's in original_class_counts
print(f'\nOriginal class counts keys in first TC image: {list(tc[0].get("original_class_counts", {}).keys())}')
print(f'  original_class_counts: {tc[0].get("original_class_counts")}')
print(f'  final_class_counts: {tc[0].get("final_class_counts")}')
print(f'  retained_object_count: {tc[0].get("retained_object_count")}')