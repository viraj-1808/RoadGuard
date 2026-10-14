#!/usr/bin/env python3
"""
Create combined dataset for real-world fine-tuning:
- Original Experiment 2 training data (19,719 images)
- 15 CLEAR manual images with model-derived annotations
"""

import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Source paths
EXP2_DATA_YAML = PROJECT_ROOT / "experiments/dataset/experiment2/data.yaml"
EXP2_IMAGES_TRAIN = PROJECT_ROOT / "experiments/dataset/experiment2/images/train"
EXP2_LABELS_TRAIN = PROJECT_ROOT / "experiments/dataset/experiment2/labels/train"
EXP2_IMAGES_VAL = PROJECT_ROOT / "experiments/dataset/experiment2/images/val"
EXP2_LABELS_VAL = PROJECT_ROOT / "experiments/dataset/experiment2/labels/val"

MANUAL_IMAGES_DIR = PROJECT_ROOT / "validation/manual/input"
MANUAL_ANNOTATIONS_DIR = PROJECT_ROOT / "experiments/results/real_world_model_improvement/annotations"
ANNOTATION_MANIFEST = PROJECT_ROOT / "experiments/results/real_world_model_improvement/annotation_manifest.json"
DATA_SPLIT = PROJECT_ROOT / "experiments/results/real_world_model_improvement/data_split.json"

# Destination paths
COMBINED_DIR = PROJECT_ROOT / "experiments/dataset/yol11s_realworld_finetune"
COMBINED_IMAGES_TRAIN = COMBINED_DIR / "images/train"
COMBINED_LABELS_TRAIN = COMBINED_DIR / "labels/train"
COMBINED_IMAGES_VAL = COMBINED_DIR / "images/val"
COMBINED_LABELS_VAL = COMBINED_DIR / "labels/val"

# 15 CLEAR images (from all splits: train, val, holdout)
CLEAR_IMAGES = {
    # From train split (8)
    "road018.jpg", "road021.jpg", "road025.jpg", "road015.jpg",
    "road009.jpg", "road011.jpg", "road014.webp", "road010.jpg",
    # From val split (3)
    "road027.jpg", "road006.jpg", "road008.jpg",
    # From holdout split (4)
    "road001.webp", "road002.jpg", "road003.jpg", "road007.jpg",
}

# 8 val-split manual images for monitoring (all from val split)
VAL_SPLIT_IMAGES = {
    "road032.jpg", "road017.jpg", "road027.jpg", "road022.jpg",
    "road033.jpg", "road020.jpg", "road006.jpg", "road008.jpg",
}

def main():
    print("=" * 60)
    print("Creating Combined Dataset for Real-World Fine-Tuning")
    print("=" * 60)
    
    # Load annotation manifest
    with open(ANNOTATION_MANIFEST) as f:
        manifest = json.load(f)
    
    # Create destination directories
    COMBINED_IMAGES_TRAIN.mkdir(parents=True, exist_ok=True)
    COMBINED_LABELS_TRAIN.mkdir(parents=True, exist_ok=True)
    COMBINED_IMAGES_VAL.mkdir(parents=True, exist_ok=True)
    COMBINED_LABELS_VAL.mkdir(parents=True, exist_ok=True)
    
    # Copy original Experiment 2 training data
    print("\n[1/4] Copying Experiment 2 training images...")
    train_img_count = 0
    for src_img in EXP2_IMAGES_TRAIN.iterdir():
        if src_img.is_file():
            dst_img = COMBINED_IMAGES_TRAIN / src_img.name
            if not dst_img.exists():
                shutil.copy2(src_img, dst_img)
                train_img_count += 1
    print(f"    Copied {train_img_count} training images")
    
    print("[2/4] Copying Experiment 2 training labels...")
    train_lbl_count = 0
    for src_lbl in EXP2_LABELS_TRAIN.iterdir():
        if src_lbl.is_file():
            dst_lbl = COMBINED_LABELS_TRAIN / src_lbl.name
            if not dst_lbl.exists():
                shutil.copy2(src_lbl, dst_lbl)
                train_lbl_count += 1
    print(f"    Copied {train_lbl_count} training labels")
    
    # Copy original Experiment 2 validation data (for reference, not for training)
    print("[3/4] Copying Experiment 2 validation data...")
    val_img_count = 0
    for src_img in EXP2_IMAGES_VAL.iterdir():
        if src_img.is_file():
            dst_img = COMBINED_IMAGES_VAL / src_img.name
            if not dst_img.exists():
                shutil.copy2(src_img, dst_img)
                val_img_count += 1
    print(f"    Copied {val_img_count} validation images")
    
    val_lbl_count = 0
    for src_lbl in EXP2_LABELS_VAL.iterdir():
        if src_lbl.is_file():
            dst_lbl = COMBINED_LABELS_VAL / src_lbl.name
            if not dst_lbl.exists():
                shutil.copy2(src_lbl, dst_lbl)
                val_lbl_count += 1
    print(f"    Copied {val_lbl_count} validation labels")
    
    # Add 15 CLEAR manual images to training set
    print("[4/4] Adding 15 CLEAR manual images to training set...")
    clear_added = 0
    for entry in manifest:
        img_name = entry["image_name"]
        if img_name in CLEAR_IMAGES:
            # Copy image
            src_img = MANUAL_IMAGES_DIR / img_name
            dst_img = COMBINED_IMAGES_TRAIN / img_name
            if src_img.exists():
                shutil.copy2(src_img, dst_img)
            else:
                print(f"    WARNING: Image not found: {src_img}")
                continue
            
            # Write label file from annotations
            annotations = entry.get("annotations", [])
            label_name = Path(img_name).stem + ".txt"
            dst_lbl = COMBINED_LABELS_TRAIN / label_name
            
            with open(dst_lbl, "w") as f:
                for ann in annotations:
                    class_id = ann["class_id"]
                    x_center = ann["x_center"]
                    y_center = ann["y_center"]
                    width = ann["width"]
                    height = ann["height"]
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
            
            clear_added += 1
            print(f"    Added: {img_name} ({len(annotations)} annotations)")
    
    print(f"\n    Added {clear_added} CLEAR manual images to training set")
    
    # Verify counts
    final_train_imgs = len(list(COMBINED_IMAGES_TRAIN.iterdir()))
    final_train_lbls = len(list(COMBINED_LABELS_TRAIN.iterdir()))
    final_val_imgs = len(list(COMBINED_IMAGES_VAL.iterdir()))
    final_val_lbls = len(list(COMBINED_LABELS_VAL.iterdir()))
    
    print(f"\nFinal dataset counts:")
    print(f"  Training images: {final_train_imgs} (expected ~19,734)")
    print(f"  Training labels: {final_train_lbls}")
    print(f"  Validation images: {final_val_imgs}")
    print(f"  Validation labels: {final_val_lbls}")
    
    # Create data.yaml for combined dataset
    data_yaml_content = f"""# Combined dataset for YOLO11s real-world fine-tuning
# Original Experiment 2 training data (19,719 images) + 15 CLEAR manual images
path: {COMBINED_DIR.as_posix()}
train: images/train
val: images/val
nc: 4
names:
  - longitudinal_crack
  - transverse_crack
  - alligator_crack
  - pothole
"""
    data_yaml_path = COMBINED_DIR / "data.yaml"
    with open(data_yaml_path, "w") as f:
        f.write(data_yaml_content)
    print(f"\nCreated data.yaml: {data_yaml_path}")
    
    # Also create a validation data.yaml pointing to Dataset A validation split (229 images)
    val_data_yaml_content = """# Dataset A validation split (229 images) for validation during fine-tuning
path: experiments/dataset/yolo_rdd2022_india
val: images/val
nc: 4
names:
  - longitudinal_crack
  - transverse_crack
  - alligator_crack
  - pothole
"""
    val_data_yaml_path = PROJECT_ROOT / "experiments/dataset/yol11s_realworld_finetune_val.yaml"
    with open(val_data_yaml_path, "w") as f:
        f.write(val_data_yaml_content)
    print(f"Created validation data.yaml: {val_data_yaml_path}")
    
    print("\n" + "=" * 60)
    print("Combined dataset creation complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()