import json
with open('experiments/analysis/overnight/experiment2_dataset_b/experiment2_leakage_report.json') as f:
    report = json.load(f)
check_e = report['checks']['E']
corr = check_e['near_duplicates']['correlation_criterion']
print('Check E correlation_criterion confirmed pairs:', corr['confirmed_near_duplicate_pairs'])
crossing = [p for p in corr.get('pairs', []) if p.get('crosses_splits')]
print('Total crossing pairs in correlation criterion:', len(crossing))
for p in crossing[:20]:
    ia = p['image_a'].split('/')[-1]
    ib = p['image_b'].split('/')[-1]
    print('    {} <-> {}  corr={}  mad={}'.format(ia, ib, p['pixel_corr'], p['pixel_mad']))
print()
dhash = check_e['near_duplicates']['dhash_screen']
print('Check E dhash_screen confirmed pairs:', dhash.get('confirmed_near_duplicate_pairs'))
dhash_crossing = [p for p in dhash.get('pairs', []) if p.get('crosses_splits')]
print('Crossing pairs:', len(dhash_crossing))
# Check split pair distribution
split_pairs = {}
for p in corr.get('pairs', []):
    if p.get('crosses_splits'):
        sp = tuple(p.get('split_pair', []))
        split_pairs[sp] = split_pairs.get(sp, 0) + 1
print('Crossing split pair distribution:', split_pairs)