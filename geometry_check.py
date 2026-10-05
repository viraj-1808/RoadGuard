import random
import os
from datasets import load_from_disk
from PIL import Image

# Load dataset
ds = load_from_disk(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022")

# Test a small sample for geometry comparison
splits = ['train', 'validation', 'test']
random.seed(42)

for split_name in splits:
    split_ds = ds[split_name]
    # Build map
    arrow_map = {}
    for ex in split_ds:
        arrow_map[ex['file_name']] = ex['objects']
    
    # Sample 50 images
    all_files = list(arrow_map.keys())
    sampled = random.sample(all_files, min(50, len(all_files)))
    
    labels_root = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022\data\labels"
    split_dir = {'train': 'train', 'validation': 'valid', 'test': 'test'}[split_name]
    
    max_dev_cx = max_dev_cy = max_dev_w = max_dev_h = 0.0
    devs_cx = []
    devs_cy = []
    devs_w = []
    devs_h = []
    matched = 0
    total_boxes = 0
    
    for img_name in sampled:
        # Find label file
        label_path = None
        for shard in os.listdir(os.path.join(labels_root, split_dir)):
            test_path = os.path.join(labels_root, split_dir, shard, img_name + '.txt')
            if os.path.exists(test_path):
                label_path = test_path
                break
            test_path = os.path.join(labels_root, split_dir, shard, img_name.replace('.jpg', '') + '.txt')
            if os.path.exists(test_path):
                label_path = test_path
                break
        
        if label_path is None:
            continue
        
        # Get image dimensions
        img_path = None
        images_root = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022\data\images"
        for shard in os.listdir(os.path.join(images_root, split_dir)):
            test_path = os.path.join(images_root, split_dir, shard, img_name)
            if os.path.exists(test_path):
                img_path = test_path
                break
        
        if img_path is None:
            continue
        
        with Image.open(img_path) as im:
            w, h = im.size
        
        # Read repo labels
        repo_boxes = []
        with open(label_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) == 5:
                    class_id = int(float(parts[0]))
                    cx, cy, bw, bh = map(float, parts[1:5])
                    repo_boxes.append((class_id, cx, cy, bw, bh))
        
        # Get Arrow boxes
        arrow_obj = arrow_map.get(img_name)
        if arrow_obj is None:
            continue
        
        arrow_boxes = []
        for cat, x, y, bw, bh in zip(arrow_obj['categories'], 
                                      [b[0] for b in arrow_obj['bbox']],
                                      [b[1] for b in arrow_obj['bbox']],
                                      [b[2] for b in arrow_obj['bbox']],
                                      [b[3] for b in arrow_obj['bbox']]):
            cx = (x + bw / 2.0) / w
            cy = (y + bh / 2.0) / h
            nw = bw / w
            nh = bh / h
            arrow_boxes.append((cat, cx, cy, nw, nh))
        
        # Match by index (assuming same order)
        for i, (r_box, a_box) in enumerate(zip(repo_boxes, arrow_boxes)):
            if r_box[0] != a_box[0]:
                continue  # class mismatch, skip geometry
            devs_cx.append(abs(r_box[1] - a_box[1]))
            devs_cy.append(abs(r_box[2] - a_box[2]))
            devs_w.append(abs(r_box[3] - a_box[3]))
            devs_h.append(abs(r_box[4] - a_box[4]))
            total_boxes += 1
            if abs(r_box[1] - a_box[1]) < 1e-3 and abs(r_box[2] - a_box[2]) < 1e-3 and abs(r_box[3] - a_box[3]) < 1e-3 and abs(r_box[4] - a_box[4]) < 1e-3:
                matched += 1
    
    if devs_cx:
        print(f"\n=== Geometry Check: {split_name} (sample {len(sampled)} images, {total_boxes} boxes) ===")
        print(f"Max |dev| cx: {max(devs_cx):.6f}, median: {sorted(devs_cx)[len(devs_cx)//2]:.6f}")
        print(f"Max |dev| cy: {max(devs_cy):.6f}, median: {sorted(devs_cy)[len(devs_cy)//2]:.6f}")
        print(f"Max |dev| w:  {max(devs_w):.6f}, median: {sorted(devs_w)[len(devs_w)//2]:.6f}")
        print(f"Max |dev| h:  {max(devs_h):.6f}, median: {sorted(devs_h)[len(devs_h)//2]:.6f}")
        print(f"Fraction within 1e-3: {matched}/{total_boxes} = {matched/total_boxes*100:.2f}%")