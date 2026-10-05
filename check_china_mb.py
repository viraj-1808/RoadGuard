import json
with open('experiments/analysis/overnight/experiment2_dataset_b/experiment2_leakage_report.json') as f:
    report = json.load(f)
corr = report['checks']['E']['near_duplicates']['correlation_criterion']
china_mb = [p for p in corr.get('pairs', []) if 'China_MotorBike' in p.get('image_a', '') or 'China_MotorBike' in p.get('image_b', '')]
print('China_MotorBike pairs in correlation criterion:', len(china_mb))
for p in china_mb[:30]:
    ia = p['image_a'].split('/')[-1]
    ib = p['image_b'].split('/')[-1]
    print('  {} <-> {}  corr={}  mad={}  crosses={}'.format(ia, ib, p.get('pixel_corr'), p.get('pixel_mad'), p.get('crosses_splits')))
print()
# Also check which of these are in val vs train
val_dir = 'val'
train_dir = 'train'
china_in_val = []
china_in_train = []
for p in china_mb:
    for key in ['image_a', 'image_b']:
        path = p[key]
        if val_dir in path:
            china_in_val.append(path.split('/')[-1])
        elif train_dir in path:
            china_in_train.append(path.split('/')[-1])
print('China_MotorBike in VAL:', sorted(set(china_in_val)))
print('China_MotorBike in TRAIN:', sorted(set(china_in_train)))