import cv2
import numpy as np
from ultralytics import YOLO

model = YOLO(r'runs\detect\experiments\training\yol11s_experiment2\weights\epoch72.pt')

images = [
    ('road002.jpg', 700, 525, 3, [260.76, 150.74, 413.56, 237.59]),
    ('road003.jpg', 978, 1390, 2, [0, 208.01, 978, 965.89]),
    ('road007.jpg', 739, 415, 3, [205.11, 190.42, 739, 415]),
    ('road018.jpg', 4096, 3072, 3, [9.01, 0, 1785.26, 1042.56]),
    ('road021.jpg', 3072, 4096, 2, [222.92, 0, 2268.62, 2095.62]),
]

for name, w, h, cls_id, gt_bbox in images:
    img_path = f'validation/manual/input/{name}'
    img = cv2.imread(img_path)
    results = model.predict(img, imgsz=720, conf=0.001, iou=0.7, device='0', verbose=False)
    
    detections = []
    if results and results[0].boxes is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        confs = results[0].boxes.conf.cpu().numpy()
        cls_ids = results[0].boxes.cls.cpu().numpy().astype(int)
        for box, conf, cid in zip(boxes, confs, cls_ids):
            detections.append({'bbox': box, 'conf': conf, 'class': cid})
    
    print(f'\n=== {name} ({w}x{h}) ===')
    print(f'GT: class={cls_id}, bbox={gt_bbox}')
    gt_area = (gt_bbox[2]-gt_bbox[0])*(gt_bbox[3]-gt_bbox[1])
    print(f'GT area: {gt_area:.0f} px^2 ({gt_area/(w*h)*100:.1f}% of image)')
    
    gt_cx = (gt_bbox[0] + gt_bbox[2]) / 2
    gt_cy = (gt_bbox[1] + gt_bbox[3]) / 2
    
    nearby = []
    for det in detections:
        det_cx = (det['bbox'][0] + det['bbox'][2]) / 2
        det_cy = (det['bbox'][1] + det['bbox'][3]) / 2
        dist = np.sqrt((det_cx - gt_cx)**2 + (det_cy - gt_cy)**2)
        if dist < 100:
            nearby.append((det, dist))
    
    if nearby:
        print('Nearby detections:')
        for det, dist in sorted(nearby, key=lambda x: x[1]):
            print(f'  class={det["class"]} conf={det["conf"]:.4f} bbox={det["bbox"]} dist={dist:.1f}')
    else:
        print('No detections within 100px of GT center')
    
    if detections:
        print('All detections:')
        for det in detections:
            print(f'  class={det["class"]} conf={det["conf"]:.4f} bbox={det["bbox"]}')
    else:
        print('No detections at all')