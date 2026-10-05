import ast
import random
import sys
import os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, repo_root)

from scripts.experiment2.build_splits import stratified_val_selection

def test_syntax():
    with open(os.path.join(repo_root, "scripts", "experiment2", "build_splits.py"), "r") as f:
        ast.parse(f.read())

def test_determinism():
    pool = [
        {"stem": f"img_{i}", "country": random.choice(["A", "B", "C"]), "is_negative": random.choice([True, False])}
        for i in range(100)
    ]
    
    val1, _ = stratified_val_selection(pool, 0.2, 42)
    
    # Scramble inputs
    pool2 = list(pool)
    random.shuffle(pool2)
    val2, _ = stratified_val_selection(pool2, 0.2, 42)
    
    assert [x["stem"] for x in val1] == [x["stem"] for x in val2], "Outputs are not identical for scrambled inputs"

if __name__ == "__main__":
    test_syntax()
    test_determinism()
    print("All tests passed.")
