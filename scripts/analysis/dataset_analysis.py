import os
from collections import Counter

BASE = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\yolo_rdd2022_india"

# Get all label files
train_labels_dir = os.path.join(BASE, "labels", "train")
val_labels_dir = os.path.join(BASE, "labels", "val")
test_labels_dir = os.path.join(BASE, "labels", "test")

train_files = sorted([f.replace('.txt','') for f in os.listdir(train_labels_dir)])
val_files = sorted([f.replace('.txt','') for f in os.listdir(val_labels_dir)])
test_files = sorted([f.replace('.txt','') for f in os.listdir(test_labels_dir)])

print(f"Train images: {len(train_files)}")
print(f"Val images: {len(val_files)}")
print(f"Test images: {len(test_files)}")
print(f"Total images: {len(train_files)+len(val_files)+len(test_files)}")