from datasets import load_from_disk

ds = load_from_disk(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022")
print("Splits:", list(ds.keys()))
for split in ds:
    print(f"{split}: {len(ds[split])} examples")
    print(f"  Features: {ds[split].features}")
    for i in range(min(3, len(ds[split]))):
        ex = ds[split][i]
        fn = ex['file_name']
        print(f"  {fn}: objects={ex['objects']}")