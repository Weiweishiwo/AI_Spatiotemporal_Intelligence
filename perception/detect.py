import json
from ultralytics import  YOLO
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = BASE_DIR / "data" / "images"
MODEL_PATH = Path(__file__).resolve().parent.parent / "yolov8n.pt"
model=YOLO(str(MODEL_PATH))

def run_detect(image_path: str) -> dict:
    """
        目的:真是的YOLOv8推理,输出符合docs/data-schema.md §4的检测结果
        参数:image_path:str
        results（报告单）
        results.boxes       ← 检测框区（目标检测用这个）
        results.masks       ← 分割区（画轮廓时才有）
        results.keypoints   ← 关键点区（测姿态时才有）
        results.orig_img    ← 原图
        box.cls   类别编号
        box.conf   置信度
        box.xyxy   左上/右下坐标
    """
    # 后端传的是相对项目根的路径（如 data/images/xxx.jpg），先转绝对路径再喂给 YOLO
    img_path = Path(image_path)
    if not img_path.is_absolute():
        img_path = BASE_DIR / img_path
    results = model(str(img_path))[0]
    detections =[]
    for box in results.boxes:# 遍历每个检测框
        cls_id=int(box.cls[0]) # 类别编号，如 0=person
        conf=float(box.conf[0])# 置信度，0~1
        x1,y1,x2,y2=[int(v) for v in box.xyxy[0].tolist()] # 框的像素坐标
        detections.append({
            "class_name":model.names[cls_id], # 编号 → 名字
            "confidence":round(conf,2),
            "bbox":[x1,y1,x2,y2],
        })

    return {"image_path":image_path, "detections":detections}