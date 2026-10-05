import json

with open('experiments/dataset/normalized_rdd2022_india/group_analysis/large_component_audit.json') as f:
    data = json.load(f)

print(f'Type: {type(data)}')
if isinstance(data, dict):
    keys = list(data.keys())
    print(f'Number of entries: {len(data)}')
    print(f'First 5 keys: {keys[:5]}')
    first_key = keys[0]
    print(f'First key: {first_key}')
    print(f'First key value: {data[first_key]}')
elif isinstance(data, list):
    print(f'Number of entries: {len(data)}')
    if data:
        print(f'First item: {json.dumps(data[0], indent=2)[:500]}')