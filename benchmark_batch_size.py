import torch
import gc
from ultralytics import YOLO

DATA_YAML = r"experiments\dataset\yolo_rdd2022_india\data.yaml"
MODEL_NAME = "yolo11s.pt"
DEVICE = 0
IMGSZ = 720
EPOCHS = 1
SEED = 42

BATCH_SIZES = [8, 16, 32]
RESULTS = {}

def get_gpu_stats():
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        allocated = torch.cuda.memory_allocated() / (1024 ** 2)
        reserved = torch.cuda.memory_reserved() / (1024 ** 2)
        peak = torch.cuda.max_memory_reserved() / (1024 ** 2)
        return round(allocated, 2), round(reserved, 2), round(peak, 2)
    return 0.0, 0.0, 0.0

def reset_gpu():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

for bs in BATCH_SIZES:
    print(f"\n{'='*50}")
    print(f"Testing batch size: {bs}")
    print(f"{'='*50}")

    reset_gpu()
    oom = False
    oom_msg = None

    try:
        model = YOLO(MODEL_NAME)

        train_result = model.train(
            data=DATA_YAML,
            imgsz=IMGSZ,
            epochs=EPOCHS,
            batch=bs,
            seed=SEED,
            device=DEVICE,
            workers=0,
            optimizer="auto",
            patience=1,
            exist_ok=True,
            name=f"yol11s_batch_{bs}",
            project="experiments/training"
        )

        allocated, reserved, peak = get_gpu_stats()
        RESULTS[bs] = {
            "status": "completed",
            "allocated_mb": allocated,
            "reserved_mb": reserved,
            "peak_mb": peak,
            "oom": False,
            "oom_msg": None
        }
        print(f"Status: completed")
        print(f"Allocated: {allocated} MB")
        print(f"Reserved: {reserved} MB")
        print(f"Peak: {peak} MB")

    except torch.cuda.OutOfMemoryError as e:
        oom = True
        oom_msg = str(e)
        allocated, reserved, peak = get_gpu_stats()
        RESULTS[bs] = {
            "status": "OOM",
            "allocated_mb": allocated,
            "reserved_mb": reserved,
            "peak_mb": peak,
            "oom": True,
            "oom_msg": oom_msg
        }
        print(f"CUDA OOM: {oom_msg}")
        print(f"Peak at OOM: {peak} MB")

    except Exception as e:
        oom = True
        oom_msg = str(e)
        allocated, reserved, peak = get_gpu_stats()
        RESULTS[bs] = {
            "status": f"ERROR: {type(e).__name__}",
            "allocated_mb": allocated,
            "reserved_mb": reserved,
            "peak_mb": peak,
            "oom": True,
            "oom_msg": oom_msg
        }
        print(f"Error ({type(e).__name__}): {e}")

    finally:
        reset_gpu()
        gc.collect()

print("\n" + "="*60)
print("BENCHMARK RESULTS SUMMARY")
print("="*60)

max_safe = None
for bs in sorted(BATCH_SIZES, reverse=True):
    r = RESULTS[bs]
    print(f"Batch {bs}: status={r['status']}, peak={r['peak_mb']}MB, allocated={r['allocated_mb']}MB, OOM={r['oom']}")
    if not r['oom']:
        max_safe = bs

print(f"\nRecommended maximum safe batch size: {max_safe}")
print("\nDone.")