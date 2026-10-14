import os
import hashlib
import torch
import pandas as pd
from datetime import datetime
from pathlib import Path

def get_file_info(filepath):
    """Get file size, SHA-256, and modification time."""
    stat = os.stat(filepath)
    size = stat.st_size
    mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
    
    # SHA-256
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    sha256 = sha256_hash.hexdigest()
    
    return size, sha256, mtime

def extract_epoch_from_filename(filename):
    """Extract epoch number from filename."""
    import re
    # Match epoch<number>.pt or epoch<number>_suffix.pt
    match = re.search(r'epoch(\d+)', filename)
    if match:
        return int(match.group(1))
    # best.pt and last.pt don't have epoch in name
    return None

def analyze_checkpoint(filepath):
    """Load checkpoint and check for optimizer state, epoch, best_fitness."""
    try:
        checkpoint = torch.load(filepath, map_location="cpu", weights_only=False)
        has_optimizer = any(key in checkpoint for key in ['optimizer', 'optimizer_state_dict'])
        epoch = checkpoint.get('epoch', None)
        best_fitness = checkpoint.get('best_fitness', None)
        keys = list(checkpoint.keys())
        return {
            'has_optimizer': has_optimizer,
            'epoch': epoch,
            'best_fitness': best_fitness,
            'keys': keys
        }
    except Exception as e:
        return {
            'has_optimizer': False,
            'epoch': None,
            'best_fitness': None,
            'keys': [],
            'error': str(e)
        }

def parse_results_csv(csv_path):
    """Parse results.csv and find best epoch by mAP50."""
    try:
        # Try reading with header first
        df = pd.read_csv(csv_path)
        # Check if first row looks like a header (non-numeric column names)
        has_header = not all(str(c).replace('.', '').replace('_', '').replace('/', '').isdigit() for c in df.columns)
        
        if not has_header:
            # No header - use standard YOLO column names
            df = pd.read_csv(csv_path, header=None)
            df.columns = ['epoch', 'time', 'train/box_loss', 'train/cls_loss', 'train/dfl_loss',
                         'metrics/precision(B)', 'metrics/recall(B)', 'metrics/mAP50(B)', 'metrics/mAP50-95(B)',
                         'val/box_loss', 'val/cls_loss', 'val/dfl_loss', 'lr/pg0', 'lr/pg1', 'lr/pg2']
        
        # Find column for mAP50
        map50_cols = [c for c in df.columns if 'mAP50' in c and 'val' not in c.lower() and '50-95' not in c]
        if not map50_cols:
            map50_cols = [c for c in df.columns if 'mAP50' in c and '50-95' not in c]
        if not map50_cols:
            return None, None, None
        map50_col = map50_cols[0]
        best_idx = df[map50_col].idxmax()
        best_epoch = int(df.loc[best_idx, 'epoch']) if 'epoch' in df.columns else best_idx + 1
        best_map50 = df.loc[best_idx, map50_col]
        return best_epoch, best_map50, map50_col
    except Exception as e:
        return None, None, str(e)

# Checkpoint directories
checkpoint_dirs = [
    "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights",
    "runs/detect/experiments/training/yol11s_experiment2/weights",
    "runs/detect/experiments/training/yol11s_microtrial_w2_pf2/weights",
    "runs/detect/experiments/training/yol11s_smoke_test/weights",
    "weights"
]

results_csv_paths = {
    "yol11s_dataset_v2_split_v2": "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/results.csv",
    "yol11s_experiment2": "runs/detect/experiments/training/yol11s_experiment2/results.csv",
    "yol11s_microtrial_w2_pf2": None,
    "yol11s_smoke_test": "runs/detect/experiments/training/yol11s_smoke_test/results.csv",
}

all_checkpoints = []

for ckpt_dir in checkpoint_dirs:
    if not os.path.exists(ckpt_dir):
        continue
    for fname in os.listdir(ckpt_dir):
        if fname.endswith('.pt'):
            filepath = os.path.join(ckpt_dir, fname)
            size, sha256, mtime = get_file_info(filepath)
            epoch_from_name = extract_epoch_from_filename(fname)
            ckpt_info = analyze_checkpoint(filepath)
            
            all_checkpoints.append({
                'path': filepath,
                'filename': fname,
                'dir': ckpt_dir,
                'size': size,
                'sha256': sha256,
                'mtime': mtime,
                'epoch_from_name': epoch_from_name,
                'has_optimizer': ckpt_info['has_optimizer'],
                'epoch_from_ckpt': ckpt_info['epoch'],
                'best_fitness': ckpt_info['best_fitness'],
                'keys': ckpt_info['keys'],
                'error': ckpt_info.get('error', None)
            })

# Parse results.csv for each experiment
results_summary = {}
for exp_name, csv_path in results_csv_paths.items():
    if csv_path and os.path.exists(csv_path):
        best_epoch, best_map50, map50_col = parse_results_csv(csv_path)
        results_summary[exp_name] = {
            'best_epoch': best_epoch,
            'best_map50': best_map50,
            'map50_column': map50_col
        }
    else:
        results_summary[exp_name] = {
            'best_epoch': None,
            'best_map50': None,
            'map50_column': None
        }

# Write report
output_dir = "experiments/results/20261010_phase1_checkpoint_audit"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "checkpoint_inventory.md")

with open(output_path, 'w') as f:
    f.write("# Checkpoint Inventory Report\n\n")
    f.write(f"Generated: {datetime.now().isoformat()}\n\n")
    
    # Section (a): All checkpoints with details
    f.write("## (a) All Checkpoints with Details\n\n")
    
    # Group by directory
    for ckpt_dir in checkpoint_dirs:
        dir_checkpoints = [c for c in all_checkpoints if c['dir'] == ckpt_dir]
        if not dir_checkpoints:
            continue
        f.write(f"### {ckpt_dir}\n\n")
        f.write("| Filename | Size (bytes) | SHA-256 | Modified | Epoch (from name) | Epoch (from ckpt) | Best Fitness | Has Optimizer | Keys |\n")
        f.write("|----------|--------------|---------|----------|-------------------|-------------------|--------------|---------------|------|\n")
        for c in sorted(dir_checkpoints, key=lambda x: (x['epoch_from_name'] if x['epoch_from_name'] is not None else 999, x['filename'])):
            epoch_name = c['epoch_from_name'] if c['epoch_from_name'] is not None else "N/A (best/last)"
            epoch_ckpt = c['epoch_from_ckpt'] if c['epoch_from_ckpt'] is not None else "N/A"
            best_fit = c['best_fitness'] if c['best_fitness'] is not None else "N/A"
            keys_str = ", ".join(c['keys'][:5]) + ("..." if len(c['keys']) > 5 else "")
            if c['error']:
                keys_str += f" [ERROR: {c['error']}]"
            f.write(f"| {c['filename']} | {c['size']} | {c['sha256'][:16]}... | {c['mtime']} | {epoch_name} | {epoch_ckpt} | {best_fit} | {c['has_optimizer']} | {keys_str} |\n")
        f.write("\n")
    
    # Section (b): results.csv best epochs
    f.write("## (b) results.csv Best Epochs by mAP50\n\n")
    f.write("| Experiment | Best Epoch | Best mAP50 | mAP50 Column |\n")
    f.write("|------------|------------|------------|--------------|\n")
    for exp_name, info in results_summary.items():
        epoch = info['best_epoch'] if info['best_epoch'] is not None else "N/A"
        map50 = info['best_map50'] if info['best_map50'] is not None else "N/A"
        col = info['map50_column'] if info['map50_column'] is not None else "N/A"
        f.write(f"| {exp_name} | {epoch} | {map50} | {col} |\n")
    f.write("\n")
    
    # Section (c): Conclusion - strongest checkpoint by validation metrics
    f.write("## (c) Conclusion: Strongest Checkpoint by Validation Metrics\n\n")
    
    # Find best checkpoint based on best_fitness from checkpoint or results.csv
    best_overall = None
    best_map50 = -1
    best_checkpoint_file = None
    best_checkpoint_path = None
    
    for exp_name, info in results_summary.items():
        if info['best_map50'] is not None and info['best_map50'] > best_map50:
            best_map50 = info['best_map50']
            best_overall = {
                'experiment': exp_name,
                'best_epoch': info['best_epoch'],
                'best_map50': info['best_map50']
            }
            # Find the corresponding epoch checkpoint file
            for c in all_checkpoints:
                if exp_name in c['dir'] and c['epoch_from_name'] == info['best_epoch']:
                    best_checkpoint_file = c['filename']
                    best_checkpoint_path = c['path']
                    break
    
    # Also check checkpoint best_fitness
    for c in all_checkpoints:
        if c['best_fitness'] is not None and c['best_fitness'] > best_map50:
            best_map50 = c['best_fitness']
            best_overall = {
                'experiment': c['dir'],
                'best_epoch': c['epoch_from_ckpt'] or c['epoch_from_name'],
                'best_map50': c['best_fitness'],
            }
            best_checkpoint_file = c['filename']
            best_checkpoint_path = c['path']
    
    # Add info about best.pt in the winning experiment
    if best_overall:
        exp_name = best_overall['experiment']
        for c in all_checkpoints:
            if exp_name in c['dir'] and c['filename'] == 'best.pt':
                best_overall['best_epoch_from_best_pt'] = c['epoch_from_ckpt']
                best_overall['best_fitness_from_best_pt'] = c['best_fitness']
                break
    
    if best_overall:
        checkpoint_name = best_checkpoint_file if best_checkpoint_file else 'best.pt'
        f.write(f"**Strongest checkpoint by validation metrics:** `{checkpoint_name}` from **{best_overall['experiment']}**\n\n")
        f.write(f"- **Best Epoch:** {best_overall['best_epoch']}\n")
        f.write(f"- **Best mAP50:** {best_overall['best_map50']:.4f}\n\n")
        
        if best_checkpoint_path:
            f.write(f"- **Checkpoint file:** {checkpoint_name} (path: {best_checkpoint_path})\n")
        else:
            # Try to find best.pt in that experiment
            for c in all_checkpoints:
                if best_overall['experiment'] in c['dir'] and c['filename'] == 'best.pt':
                    f.write(f"- **Checkpoint file:** {c['filename']} (path: {c['path']})\n")
                    break
        
        # Check if best.pt corresponds to the best epoch
        best_epoch = best_overall['best_epoch']
        matching_epoch_ckpt = None
        for c in all_checkpoints:
            if best_overall['experiment'] in c['dir'] and c['epoch_from_name'] == best_epoch:
                matching_epoch_ckpt = c
                break
        if matching_epoch_ckpt and matching_epoch_ckpt['filename'] != 'best.pt' and matching_epoch_ckpt['filename'] != checkpoint_name:
            best_pt_epoch = best_overall.get('best_epoch_from_best_pt', 'unknown')
            best_pt_fitness = best_overall.get('best_fitness_from_best_pt', 'unknown')
            if best_pt_fitness is not None and best_pt_fitness != 'unknown':
                best_pt_fitness = f"{best_pt_fitness:.4f}"
            else:
                best_pt_fitness = "N/A"
            f.write(f"- **Note:** The `best.pt` in this experiment was saved at epoch {best_pt_epoch} "
                    f"(mAP50: {best_pt_fitness}), but training continued to epoch {best_epoch} "
                    f"with higher mAP50 ({best_overall['best_map50']:.4f}). The checkpoint for the best epoch is `{matching_epoch_ckpt['filename']}`.\n")
    else:
        f.write("No validation metrics found to determine strongest checkpoint.\n")
    
    f.write("\n---\n\n")
    f.write("### Summary Statistics\n\n")
    f.write(f"- **Total checkpoints analyzed:** {len(all_checkpoints)}\n")
    f.write(f"- **Checkpoints with optimizer state:** {sum(1 for c in all_checkpoints if c['has_optimizer'])}\n")
    f.write(f"- **Experiments with results.csv:** {sum(1 for v in results_summary.values() if v['best_epoch'] is not None)}\n")

print(f"Report written to {output_path}")