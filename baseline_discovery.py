"""Baseline discovery script for RoadGuard AI repository.
Collects repository facts needed across all six phases.
"""
import hashlib
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
PROTECTED_EPOCH72 = os.path.join(
    PROJECT_ROOT,
    "runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt",
)

def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_dir(dirpath, max_depth=4, indent=""):
    """Return a compact listing of a directory tree."""
    lines = []
    try:
        entries = sorted(os.listdir(dirpath))
    except PermissionError:
        return lines
    total = 0
    total_size = 0
    for name in entries:
        p = os.path.join(dirpath, name)
        if os.path.isdir(p):
            lines.append(f"{indent}{name}/")
            total += 1
            total_size += 0
        else:
            try:
                total_size += os.path.getsize(p)
                total += 1
            except OSError:
                pass
    if total > 0:
        lines.append(f"{indent}  [{total} files, {total_size:,} bytes]")
    return lines


def print_tree(root, max_depth=3, indent=""):
    print(f"\n{indent}{os.path.relpath(root, PROJECT_ROOT)}/")
    try:
        entries = sorted(os.listdir(root))
    except PermissionError:
        return 0
    dirs = [e for e in entries if os.path.isdir(os.path.join(root, e))]
    files = [e for e in entries if os.path.isfile(os.path.join(root, e))]
    for name in dirs[:40]:
        print(f"{indent}  {name}/")
    if len(dirs) > 40:
        print(f"{indent}    ... and {len(dirs) - 40} more directories")
    for name in sorted(files):
        print(f"{indent}  {name}")
    return 0


print("=" * 80)
print("ROADGUARD AI BASELINE DISCOVERY")
print("Root:", PROJECT_ROOT)
print("=" * 80)

# --- 1. Protect checkpoint verification ---
print("\n--- PROTECTED CHECKPOINT ---")
if os.path.exists(PROTECTED_EPOCH72):
    h = sha256_of_file(PROTECTED_EPOCH72)
    print(f"path: {PROTECTED_EPOCH72}")
    print(f"sha256: {h}")
    print(f"expected: e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5")
    print(f"size: {os.path.getsize(PROTECTED_EPOCH72):,} bytes")
    print(f"match: {h == 'e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5'}")
else:
    print("CHECKPOINT NOT FOUND - need to locate it")

# --- 2. Top-level tree ---
print("\n" + "=" * 80)
print("TOP-LEVEL TREE")
print("=" * 80)
print_tree(PROJECT_ROOT)

# --- 3. Directory sizes ---
print("\n" + "=" * 80)
print("TOP-LEVEL DIRECTORY SIZES (KB)")
print("=" * 80)
for name in sorted(os.listdir(PROJECT_ROOT)):
    p = os.path.join(PROJECT_ROOT, name)
    if os.path.isdir(p) and not name.startswith("."):
        total = 0
        for dirpath, dirnames, filenames in os.walk(p):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
        print(f"{name:30s} {total // 1024:>12,} KB")

# --- 4. Git status (basic) ---
print("\n" + "=" * 80)
print("GIT STATUS")
print("=" * 80)
git_dir = os.path.join(PROJECT_ROOT, ".git")
if os.path.isdir(git_dir):
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        lines = out.stdout.strip().splitlines()
        if lines:
            for line in lines[:50]:
                print(line)
            if len(lines) > 50:
                print(f"  ... and {len(lines) - 50} more changed files")
        else:
            print("(no uncommitted changes)")
    except Exception as e:
        print(f"git status failed: {e}")
else:
    print("not a git repo")

# --- 5. Manual input/output paths ---
print("\n" + "=" * 80)
print("MANUAL INFERENCE INPUT / OUTPUT")
print("=" * 80)
for label, path in [
    ("INPUT", os.path.join(PROJECT_ROOT, "validation/manual/input")),
    ("OUTPUT", os.path.join(PROJECT_ROOT, "validation/manual/output")),
]:
    print(f"\n[{label}] {path}")
    if os.path.exists(path):
        for entry in sorted(os.listdir(path)):
            p = os.path.join(path, entry)
            if os.path.isdir(p):
                files = os.listdir(p)
                print(f"  {entry}/  ({len(files)} items)")
            else:
                print(f"  {entry}")
    else:
        print("  DIRECTORY DOES NOT EXIST")

# --- 6. Key directories listing ---
print("\n" + "=" * 80)
print("experiments/ contents")
print("=" * 80)
exp_dir = os.path.join(PROJECT_ROOT, "experiments")
if os.path.isdir(exp_dir):
    print_tree(exp_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("configs/ contents")
print("=" * 80)
cfg_dir = os.path.join(PROJECT_ROOT, "configs")
if os.path.isdir(cfg_dir):
    print_tree(cfg_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("docs/ contents")
print("=" * 80)
docs_dir = os.path.join(PROJECT_ROOT, "docs")
if os.path.isdir(docs_dir):
    print_tree(docs_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("validation/ contents")
print("=" * 80)
val_dir = os.path.join(PROJECT_ROOT, "validation")
if os.path.isdir(val_dir):
    print_tree(val_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("ml/ contents")
print("=" * 80)
ml_dir = os.path.join(PROJECT_ROOT, "ml")
if os.path.isdir(ml_dir):
    print_tree(ml_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("inference/ contents")
print("=" * 80)
inf_dir = os.path.join(PROJECT_ROOT, "inference")
if os.path.isdir(inf_dir):
    print_tree(inf_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("backend/ contents")
print("=" * 80)
be_dir = os.path.join(PROJECT_ROOT, "backend")
if os.path.isdir(be_dir):
    print_tree(be_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("frontend/ contents")
print("=" * 80)
fe_dir = os.path.join(PROJECT_ROOT, "frontend")
if os.path.isdir(fe_dir):
    print_tree(fe_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("scripts/ contents")
print("=" * 80)
sc_dir = os.path.join(PROJECT_ROOT, "scripts")
if os.path.isdir(sc_dir):
    print_tree(sc_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("tests/ contents")
print("=" * 80)
ts_dir = os.path.join(PROJECT_ROOT, "tests")
if os.path.isdir(ts_dir):
    print_tree(ts_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("cache/ contents")
print("=" * 80)
ca_dir = os.path.join(PROJECT_ROOT, "cache")
if os.path.isdir(ca_dir):
    print_tree(ca_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("analysis/ contents")
print("=" * 80)
an_dir = os.path.join(PROJECT_ROOT, "analysis")
if os.path.isdir(an_dir):
    print_tree(an_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("contracts/ contents")
print("=" * 80)
co_dir = os.path.join(PROJECT_ROOT, "contracts")
if os.path.isdir(co_dir):
    print_tree(co_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("orchestration/ contents")
print("=" * 80)
or_dir = os.path.join(PROJECT_ROOT, "orchestration")
if os.path.isdir(or_dir):
    print_tree(or_dir, max_depth=2)
else:
    print("missing")

print("\n" + "=" * 80)
print("Analysis report and research files")
print("=" * 80)
for f in sorted(os.listdir(PROJECT_ROOT)):
    if f.endswith(".md") and f not in ("README.md",):
        print(f)

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
