#!/usr/bin/env python3
"""Verify protected epoch-72 checkpoint hash"""
import hashlib
from pathlib import Path

checkpoint_path = Path("runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt")
expected_hash = "e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5"

if checkpoint_path.exists():
    sha256_hash = hashlib.sha256()
    with open(checkpoint_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    actual_hash = sha256_hash.hexdigest()
    
    print(f"Checkpoint path: {checkpoint_path}")
    print(f"Expected SHA-256: {expected_hash}")
    print(f"Actual SHA-256:   {actual_hash}")
    print(f"Match: {actual_hash == expected_hash}")
    
    if actual_hash == expected_hash:
        print("✓ PROTECTED CHECKPOINT HASH VERIFIED")
    else:
        print("✗ PROTECTED CHECKPOINT HASH MISMATCH")
else:
    print(f"✗ CHECKPOINT NOT FOUND: {checkpoint_path}")