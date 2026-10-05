import json
from collections import Counter

with open(r'C:\Users\viraj\Code_files\Github\RoadGuard AI\runs\detect\experiments\training\yol11s_dataset_v2_split_v2\test_eval\predictions.json', 'r') as f:
    preds = json.load(f)

# Check image IDs and see if there's a file_name we can use to get dimensions
images = set(p['image_id'] for p in preds)
print(f'Unique image IDs: {len(images)}')
print(f'Sample image IDs: {sorted(images)[:5]}')

# Check file_name field - it has .jpg extension
sample = preds[0]
fn = sample['file_name']
ii = sample['image_id']
print(f'First pred file_name: {fn}')
print(f'First pred image_id: {ii}')

# Check score distribution more carefully
scores = sorted([p['score'] for p in preds], reverse=True)
print(f'Top 5 scores: {scores[:5]}')

# Count predictions per image
preds_per_img = Counter(p['image_id'] for p in preds)
print(f'Predictions per image: min={min(preds_per_img.values())}, max={max(preds_per_img.values())}, mean={sum(preds_per_img.values())/len(preds_per_img):.1f}')
print(f'Images with > 50 preds: {sum(1 for c in preds_per_img.values() if c > 50)}')
print(f'Images with > 20 preds: {sum(1 for c in preds_per_img.values() if c > 20)}')

# Category distribution
cats = Counter(p['category_id'] for p in preds)
print(f'Category distribution: {dict(cats)}')

# Check per-image predictions
for img_id in sorted(images)[:3]:
    img_preds = [p for p in preds if p['image_id'] == img_id]
    scores_img = [p['score'] for p in img_preds]
    print(f'{img_id}: {len(img_preds)} predictions, scores range [{min(scores_img):.3f}, {max(scores_img):.3f}]')