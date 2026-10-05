import json

m = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))
for i, img in enumerate(m['image_manifest'][:5]):
    print(i, img['normalized_image_path'], img['final_class_counts'])

print('...')
prev = {'pothole': 0, 'alligator_crack': 0, 'longitudinal_crack': 0, 'transverse_crack': 0}
for i, img in enumerate(m['image_manifest'][:10]):
    curr = img['final_class_counts']
    delta = {k: curr.get(k, 0) - prev.get(k, 0) for k in prev}
    print(i, delta)
    prev = curr