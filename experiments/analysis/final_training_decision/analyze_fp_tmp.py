import json
from collections import Counter

with open('experiments/evaluation/exp2_frozen_dataset_a_test/eval/predictions.json') as f:
    preds = json.load(f)

print('Total predictions:', len(preds))
classes = Counter(p['category_id'] for p in preds)
print('Class distribution:', dict(classes))
scores = [p['score'] for p in preds]
print('Score min:', min(scores), 'max:', max(scores))

# By confidence band
bands = {'<0.1':0,'0.1-0.3':0,'0.3-0.5':0,'0.5-0.7':0,'>=0.7':0}
for p in preds:
    s = p['score']
    if s < 0.1: bands['<0.1'] += 1
    elif s < 0.3: bands['0.1-0.3'] += 1
    elif s < 0.5: bands['0.3-0.5'] += 1
    elif s < 0.7: bands['0.5-0.7'] += 1
    else: bands['>=0.7'] += 1
print('Confidence bands:', bands)

print()
print('Top 30 highest confidence predictions:')
sorted_preds = sorted(preds, key=lambda x: x['score'], reverse=True)
for p in sorted_preds[:30]:
    print(f"  {p['image_id']} class={p['category_id']} score={p['score']:.4f} bbox={[round(v,1) for v in p['bbox']]}")

# bbox area stats for high-conf
print()
print('High conf (>=0.5) bbox areas:')
hc = [p for p in preds if p['score'] >= 0.5]
for p in hc:
    area = p['bbox'][2]*p['bbox'][3]
    print(f"  {p['image_id']} class={p['category_id']} score={p['score']:.4f} area={area:.0f}")