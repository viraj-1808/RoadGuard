#!/usr/bin/env python3
import os, json, numpy as np
from collections import defaultdict
from PIL import Image, ImageDraw

BASE = r"C:\Users\viraj\Code_files\Github\RoadGuard AI"
PRED_FILE = os.path.join(BASE, "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/test_eval/predictions.json")
LABEL_DIR = os.path.join(BASE, "experiments/dataset/yolo_rdd2022_india/labels/test")
IMAGE_DIR = os.path.join(BASE, "experiments/dataset/yolo_rdd2022_india/images/test")
OUTPUT_DIR = os.path.join(BASE, "experiments/analysis/overnight/visual_cases")

CLASS_NAMES = {0: 'longitudinal', 1: 'transverse', 2: 'alligator', 3: 'pothole'}
PRED_CLASS_MAP = {1: 0, 2: 1, 3: 2, 4: 3}
IMAGE_SIZE = 720
os.makedirs(OUTPUT_DIR, exist_ok=True)

COLORS = {0: (0,255,0), 1: (0,0,255), 2: (255,165,0), 3: (255,0,255)}

def load_data():
    gt_data = {}
    for fn in os.listdir(LABEL_DIR):
        if not fn.endswith('.txt'): continue
        iid = fn.replace('.txt','')
        objs = []
        with open(os.path.join(LABEL_DIR, fn)) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5: continue
                try:
                    cid = int(parts[0]); xc,yc,w,h = map(float, parts[1:5])
                    x = (xc-w/2)*IMAGE_SIZE; y = (yc-h/2)*IMAGE_SIZE
                    objs.append({'class_id':cid,'bbox':[x,y,w*IMAGE_SIZE,h*IMAGE_SIZE]})
                except: continue
        gt_data[iid] = objs
    with open(PRED_FILE) as f: raw = json.load(f)
    pred_data = defaultdict(list)
    for p in raw:
        pred_data[p['image_id']].append({'class_id':PRED_CLASS_MAP.get(p['category_id'],p['category_id']-1),'bbox':p['bbox'],'score':p['score']})
    return gt_data, pred_data

def bbox_iou(b1,b2):
    x1_1,y1_1,x2_1,y2_1 = b1[0],b1[1],b1[0]+b1[2],b1[1]+b1[3]
    x1_2,y1_2,x2_2,y2_2 = b2[0],b2[1],b2[0]+b2[2],b2[1]+b2[3]
    xi1,yi1,xi2,yi2 = max(x1_1,x1_2),max(y1_1,y1_2),min(x2_1,x2_2),min(y2_1,y2_2)
    if xi2<=xi1 or yi2<=yi1: return 0.0
    inter = (xi2-xi1)*(yi2-yi1)
    a1=(x2_1-x1_1)*(y2_1-y1_1); a2=(x2_2-x1_2)*(y2_2-y1_2)
    return inter/(a1+a2-inter) if (a1+a2-inter)>0 else 0.0

def nms(boxes,scores,thresh):
    if not boxes: return []
    x1=np.array([b[0] for b in boxes]); y1=np.array([b[1] for b in boxes])
    x2=np.array([b[0]+b[2] for b in boxes]); y2=np.array([b[1]+b[3] for b in boxes])
    areas=(x2-x1)*(y2-y1); order=np.argsort(scores)[::-1]; keep=[]
    while len(order)>0:
        i=order[0]; keep.append(i)
        xx1=np.maximum(x1[i],x1[order[1:]]); yy1=np.maximum(y1[i],y1[order[1:]])
        xx2=np.minimum(x2[i],x2[order[1:]]); yy2=np.minimum(y2[i],y2[order[1:]])
        inter=np.maximum(0,xx2-xx1)*np.maximum(0,yy2-yy1)
        iou=inter/(areas[i]+areas[order[1:]]-inter+1e-6)
        order=order[np.where(iou<=thresh)[0]+1]
    return keep

def draw(img_id, gt_objs, pred_objs, out_name, mark_fn=None, mark_fp_high=None):
    img = Image.open(os.path.join(IMAGE_DIR, f"{img_id}.jpg")).convert('RGB')
    d = ImageDraw.Draw(img)
    for obj in gt_objs:
        x,y,w,h = obj['bbox']; c = COLORS[obj['class_id']]
        d.rectangle([x,y,x+w,y+h], outline=c, width=2)
        d.text((x,y-13), f"GT:{CLASS_NAMES[obj['class_id']][:4]}", fill=c)
    for obj in pred_objs:
        x,y,w,h = obj['bbox']; c = COLORS[obj['class_id']]
        if mark_fp_high and obj.get('score',0)>=0.7:
            d.rectangle([x-2,y-2,x+w+2,y+h+2], outline=(255,255,0), width=3)
        d.rectangle([x,y,x+w,y+h], outline=c, width=1)
        d.text((x,y+h+2), f"{obj['score']:.2f}", fill=c)
    if mark_fn:
        for bx,by,bw,bh in mark_fn:
            d.rectangle([bx,by,bx+bw,by+bh], outline=(0,0,0), width=4)
            d.text((bx,by-13), "FN", fill=(0,0,0))
    d.text((10,10), out_name, fill=(255,255,255))
    out = os.path.join(OUTPUT_DIR, f"{out_name}.jpg")
    img.save(out); return out

def sheet(paths, name, cols=4):
    thumbs = []
    for p in paths:
        if os.path.exists(p):
            t = Image.open(p).convert('RGB'); t.thumbnail((180,180)); thumbs.append(t)
    if not thumbs: return None
    rows=(len(thumbs)+cols-1)//cols
    sheet = Image.new('RGB',(cols*180,rows*180),(32,32,32))
    for i,t in enumerate(thumbs): sheet.paste(t,((i%cols)*180,(i//cols)*180))
    sheet.save(os.path.join(OUTPUT_DIR, name))
    return os.path.join(OUTPUT_DIR, name)

print("Loading...")
gt_data, pred_data = load_data()

# Apply conf+NMS
filt = {}
for iid, preds in pred_data.items():
    fl = [p for p in preds if p['score']>=0.25]
    if not fl: continue
    kept = []
    for cid in range(4):
        cp = [p for p in fl if p['class_id']==cid]
        if not cp: continue
        ks = nms([p['bbox'] for p in cp],[p['score'] for p in cp],0.5)
        kept.extend([cp[k] for k in ks])
    filt[iid] = kept

# Match and categorize
fn_list = []; fp_list = []; matched = []
for iid in sorted(set(gt_data.keys())&set(filt.keys())):
    gt = gt_data[iid]; pred = filt[iid]
    iou_m = np.zeros((len(gt),len(pred)))
    for i,g in enumerate(gt):
        for j,p in enumerate(pred):
            if g['class_id']==p['class_id']: iou_m[i,j]=bbox_iou(g['bbox'],p['bbox'])
    idx = np.where(iou_m>=0.5)
    mg=set(); mp=set(); mlist=[]
    if len(idx[0])>0:
        si = np.argsort(iou_m[idx])[::-1]
        for s in si:
            gi=idx[0][s]; pi=idx[1][s]
            if gi not in mg and pi not in mp:
                mlist.append((gi,pi,iou_m[gi,pi])); mg.add(gi); mp.add(pi)
    for i,g in enumerate(gt):
        if i not in mg:
            o=dict(g); o['image_id']=iid; o['class_name']=CLASS_NAMES[g['class_id']]; fn_list.append(o)
    for i,p in enumerate(pred):
        if i not in mp:
            o=dict(p); o['image_id']=iid; o['class_name']=CLASS_NAMES[p['class_id']]; o['area']=p['bbox'][2]*p['bbox'][3]; fp_list.append(o)
    for gi,pi,iou in mlist:
        matched.append({'image_id':iid,'iou':iou,'gt_bbox':gt[gi]['bbox'],'pred_bbox':pred[pi]['bbox']})

fn_by_class = defaultdict(list)
for o in fn_list: fn_by_class[o['class_id']].append(o)
fp_by_class = defaultdict(list)
for o in fp_list: fp_by_class[o['class_id']].append(o)
for cid in fp_by_class: fp_by_class[cid].sort(key=lambda x:x['score'],reverse=True)
for cid in fn_by_class: fn_by_class[cid].sort(key=lambda x:x['bbox'][2]*x['bbox'][3],reverse=True)

print(f"FNs: {len(fn_list)}, FPs: {len(fp_list)}, Matched: {len(matched)}")

# Contact sheet 1: High-confidence FPs
print("Contact 1: High-conf FPs")
fp_high = []
for cid in range(4):
    for obj in fp_by_class[cid]:
        if obj['score']>=0.7:
            fp_high.append((obj['image_id'],obj['class_name'],obj['score']))
            if len(fp_high)>=16: break
    if len(fp_high)>=16: break
paths=[]
for iid,cn,sc in fp_high[:16]:
    p=draw(iid,gt_data.get(iid,[]),filt.get(iid,[]),f"fp_high_{iid}_{cn}_{sc:.2f}",mark_fp_high=True)
    if p: paths.append(p)
sheet(paths,"contact_fp_high_confidence.jpg")

# Contact sheet 2: Low-confidence FPs (noise)
print("Contact 2: Low-conf FPs")
fp_low = []
for cid in range(4):
    for obj in fp_by_class[cid]:
        if obj['score']<0.3:
            fp_low.append((obj['image_id'],obj['class_name'],obj['score']))
            if len(fp_low)>=16: break
    if len(fp_low)>=16: break
paths=[]
for iid,cn,sc in fp_low[:16]:
    p=draw(iid,gt_data.get(iid,[]),filt.get(iid,[]),f"fp_low_{iid}_{cn}_{sc:.2f}")
    if p: paths.append(p)
sheet(paths,"contact_fp_low_confidence.jpg")

# Contact sheet 3: Large missed objects (FNs)
print("Contact 3: Large FNs")
fn_large = []
for cid in range(4):
    for obj in fn_by_class[cid][:4]:
        fn_large.append((obj['image_id'],obj['class_name'],obj['bbox'][2]*obj['bbox'][3]))
paths=[]
for iid,cn,area in fn_large[:16]:
    p=draw(iid,gt_data.get(iid,[]),filt.get(iid,[]),f"fn_large_{iid}_{cn}",mark_fn=[o['bbox'] for o in gt_data.get(iid,[]) if CLASS_NAMES[o['class_id']]==cn])
    if p: paths.append(p)
sheet(paths,"contact_fn_large.jpg")

# Contact sheet 4: Small missed objects
print("Contact 4: Small FNs")
fn_small = []
for cid in range(4):
    for obj in fn_by_class[cid]:
        na=(obj['bbox'][2]*obj['bbox'][3])/(IMAGE_SIZE**2)
        if na<0.005:
            fn_small.append((obj['image_id'],obj['class_name'],na))
            if len(fn_small)>=16: break
    if len(fn_small)>=16: break
paths=[]
for iid,cn,na in fn_small[:16]:
    p=draw(iid,gt_data.get(iid,[]),filt.get(iid,[]),f"fn_small_{iid}_{cn}")
    if p: paths.append(p)
sheet(paths,"contact_fn_small.jpg")

# Contact sheet 5: Transverse cracks (all missed)
print("Contact 5: Transverse cracks")
transverse = fn_by_class.get(1,[])
paths=[]
for obj in transverse[:8]:
    iid=obj['image_id']
    p=draw(iid,gt_data.get(iid,[]),filt.get(iid,[]),f"transverse_{iid}")
    if p: paths.append(p)
sheet(paths,"contact_transverse_all_missed.jpg")

# Contact sheet 6: Localization errors (IoU 0.5-0.7)
print("Contact 6: Localization errors")
loc_cases=[]
for iid in gt_data:
    if iid not in filt: continue
    for gt in gt_data[iid]:
        for pr in filt[iid]:
            if gt['class_id']==pr['class_id']:
                iou=bbox_iou(gt['bbox'],pr['bbox'])
                if 0.5<=iou<0.7:
                    loc_cases.append((iid,iou,gt['class_id']))
                    break
        if len(loc_cases)>=16: break
    if len(loc_cases)>=16: break
paths=[]
for iid,iou,cid in loc_cases[:16]:
    p=draw(iid,gt_data.get(iid,[]),filt.get(iid,[]),f"loc_{iid}_{CLASS_NAMES[cid]}_{iou:.2f}")
    if p: paths.append(p)
sheet(paths,"contact_localization_errors.jpg")

print(f"\nGenerated {len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.jpg')])} annotated images in {OUTPUT_DIR}")