import os, hashlib, json

SAVE_DIR = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022'

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

major_files = [
    'train/data-00000-of-00001.arrow',
    'validation/data-00000-of-00001.arrow',
    'test/data-00000-of-00001.arrow',
    'train/dataset_info.json',
    'validation/dataset_info.json',
    'test/dataset_info.json',
    'dataset_dict.json',
    '.cache/huggingface/trees/d597e2962458f7242a72aaa1b7909118d40f5d29.json',
]

print('SHA256 checksums of major files:')
for mf in major_files:
    fpath = os.path.join(SAVE_DIR, mf)
    if os.path.exists(fpath):
        sz = os.path.getsize(fpath)
        sha = sha256_file(fpath)
        print('  {}:'.format(mf))
        print('    size: {} bytes'.format(sz))
        print('    sha256: {}'.format(sha))
    else:
        print('  {}: NOT FOUND'.format(mf))

total = 0
for root, dirs, files in os.walk(SAVE_DIR):
    for f in files:
        fpath = os.path.join(root, f)
        total += os.path.getsize(fpath)
print('\nTotal local size: {} bytes ({:.2f} MB)'.format(total, total/1024/1024))

manifest = {}
for root, dirs, files in os.walk(SAVE_DIR):
    for f in files:
        fpath = os.path.join(root, f)
        rel = os.path.relpath(fpath, SAVE_DIR)
        sz = os.path.getsize(fpath)
        ext = os.path.splitext(f)[1] or '(no ext)'
        if ext not in manifest:
            manifest[ext] = {'count': 0, 'total_size': 0}
        manifest[ext]['count'] += 1
        manifest[ext]['total_size'] += sz

print('\nFile manifest by extension:')
for ext, info in sorted(manifest.items()):
    print('  {}: {} files, {} bytes ({:.2f} MB)'.format(ext, info['count'], info['total_size'], info['total_size']/1024/1024))
