import csv, os, pathlib
from datetime import datetime

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

csv_path = PROJECT_ROOT / "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/results.csv"
weights_dir = PROJECT_ROOT / "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights"

with open(csv_path) as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Find best epoch based on mAP50-95
best_epoch = max(rows, key=lambda r: float(r['metrics/mAP50-95(B)']))
best_epoch_num = int(best_epoch['epoch']) + 1  # +1 for 1-indexed
best_map50 = float(best_epoch['metrics/mAP50(B)'])
best_map5095 = float(best_epoch['metrics/mAP50-95(B)'])
best_prec = float(best_epoch['metrics/precision(B)'])
best_rec = float(best_epoch['metrics/recall(B)'])

print("=== RESULTS.CSV ANALYSIS ===")
print(f"Total epochs logged: {len(rows)}")
print()
print("=== BEST EPOCH (by mAP50-95) ===")
print(f"Best epoch: {best_epoch_num}")
print(f"Best mAP50: {best_map50:.6f}")
print(f"Best mAP50-95: {best_map5095:.6f}")
print(f"Best precision: {best_prec:.6f}")
print(f"Best recall: {best_rec:.6f}")
print(f"Best train box loss: {float(best_epoch['train/box_loss']):.6f}")
print(f"Best train cls loss: {float(best_epoch['train/cls_loss']):.6f}")
print(f"Best train dfl loss: {float(best_epoch['train/dfl_loss']):.6f}")
print(f"Best val box loss: {float(best_epoch['val/box_loss']):.6f}")
print(f"Best val cls loss: {float(best_epoch['val/cls_loss']):.6f}")
print(f"Best val dfl loss: {float(best_epoch['val/dfl_loss']):.6f}")
print(f"Best lr: {float(best_epoch['lr/pg0']):.6f}")
print()

# Final epoch values
final = rows[-1]
print("=== FINAL EPOCH ===")
final_epoch = int(final['epoch']) + 1
print(f"Final epoch: {final_epoch}")
print(f"Final mAP50: {float(final['metrics/mAP50(B)']):.6f}")
print(f"Final mAP50-95: {float(final['metrics/mAP50-95(B)']):.6f}")
print(f"Final precision: {float(final['metrics/precision(B)']):.6f}")
print(f"Final recall: {float(final['metrics/recall(B)']):.6f}")
print(f"Final train box loss: {float(final['train/box_loss']):.6f}")
print(f"Final val box loss: {float(final['val/box_loss']):.6f}")
print(f"Final time: {float(final['time']):.1f}s")
print()

# Trend analysis
print("=== TRAINING TREND ===")
first_10_map5095 = sum(float(r['metrics/mAP50-95(B)']) for r in rows[:10]) / 10
last_10_map5095 = sum(float(r['metrics/mAP50-95(B)']) for r in rows[-10:]) / 10
print(f"Avg mAP50-95 (epochs 1-10): {first_10_map5095:.6f}")
print(f"Avg mAP50-95 (epochs 91-100): {last_10_map5095:.6f}")
if last_10_map5095 > first_10_map5095 * 1.5:
    print("Trend: Improved significantly")
elif last_10_map5095 > first_10_map5095:
    print("Trend: Moderately improved")
else:
    print("Trend: Plateaued or decreased")

# Plateau detection
max_plateau = 0
best_idx = 0
for i, r in enumerate(rows):
    if float(r['metrics/mAP50-95(B)']) > float(rows[best_idx]['metrics/mAP50-95(B)']):
        best_idx = i

# Count epochs from best to end (plateau after best)
epochs_after_best = len(rows) - best_idx - 1
print(f"Epochs after best: {epochs_after_best}")

# Loss trend
print()
print("=== LOSS TRENDS ===")
train_box_first = float(rows[0]['train/box_loss'])
train_box_last = float(rows[-1]['train/box_loss'])
val_box_first = float(rows[0]['val/box_loss'])
val_box_last = float(rows[-1]['val/box_loss'])
print(f"Train box loss: {train_box_first:.4f} -> {train_box_last:.4f} (trend: {'decreasing' if train_box_last < train_box_first else 'increasing'})")
print(f"Val box loss: {val_box_first:.4f} -> {val_box_last:.4f} (trend: {'decreasing' if val_box_last < val_box_first else 'increasing'})")

# Best precision/recall
best_prec_epoch = max(rows, key=lambda r: float(r['metrics/precision(B)']))
best_rec_epoch = max(rows, key=lambda r: float(r['metrics/recall(B)']))
print()
print("=== BEST PRECISION/RECALL ===")
print(f"Best precision: {float(best_prec_epoch['metrics/precision(B)']):.6f} at epoch {int(best_prec_epoch['epoch'])+1}")
print(f"Best recall: {float(best_rec_epoch['metrics/recall(B)']):.6f} at epoch {int(best_rec_epoch['epoch'])+1}")

# File sizes
print()
print("=== CHECKPOINT FILE SIZES ===")
for fname in ['best.pt', 'last.pt', 'epoch0.pt', 'epoch99.pt']:
    fpath = weights_dir / fname
    if fpath.exists():
        size_mb = fpath.stat().st_size / 1024**2
        mtime = datetime.fromtimestamp(fpath.stat().st_mtime)
        print(f"{fname}: {size_mb:.2f} MB, modified: {mtime}")