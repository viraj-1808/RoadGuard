#!/usr/bin/env python3
"""Detached launcher that survives tool timeouts."""
import subprocess
import sys
import os

if __name__ == "__main__":
    project_root = r"C:\Users\viraj\Code_files\Github\RoadGuard AI"
    log_path = os.path.join(project_root, "microtrial_output.log")
    
    with open(log_path, "w") as logf:
        proc = subprocess.Popen(
            [sys.executable, "scripts/optimization/microtrial_workers2_prefetch2.py"],
            cwd=project_root,
            stdout=logf,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    
    print(f"Started micro-trial with PID {proc.pid}")
    sys.exit(0)