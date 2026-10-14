import json

with open(r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\results\real_world_model_improvement\ground_truth_annotations.json') as f:
    data = json.load(f)

holdout = ['road037.jpg', 'road016.jpg', 'road019.jpg', 'road039.jpg', 'road023.jpg', 'road038.jpg', 'road001.webp', 'road029.jpg', 'road003.jpg', 'road026.jpg', 'road005.jpg', 'road002.jpg', 'road007.jpg', 'road012.jpg']

for img in data['images']:
    if img['image'] in holdout:
        print(f"{img['image']}: {img['status']} - {len(img['annotations'])} annotations")
        for ann in img['annotations']:
            print(f"  Class {ann['class_id']} ({ann['class_name']}): {ann['bbox_xyxy']}")