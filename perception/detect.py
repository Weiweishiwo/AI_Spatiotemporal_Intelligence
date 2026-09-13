import json
from ultralytics import  YOLO
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = BASE_DIR / "data" / "images"
# 两个模型各管一段:
#   yolov8n.pt —— COCO 80 类通用模型(person/bus/car...),它没学过安全帽,问它也白问
#   best.pt    —— 自己训的安全帽模型,只有 hardhat / no-hardhat 两类
GENERAL_MODEL_PATH = BASE_DIR / "yolov8n.pt"
HARDHAT_MODEL_PATH = BASE_DIR / "runs" / "detect" / "hardhat_yolov8n" / "weights" / "best.pt"
general_model = YOLO(str(GENERAL_MODEL_PATH))
hardhat_model = YOLO(str(HARDHAT_MODEL_PATH))

# 契约(docs/data-schema.md §4)的事件枚举写的是 no_helmet(下划线),
# 模型输出的是 no-hardhat(连字符),名字对不上前端就找不到,这里对齐
CLASS_NAME_MAP = {"no-hardhat": "no_helmet"}


def _detect_one(model, img_path: Path) -> list:
    """跑一个模型,把检测框转成契约 §4 的格式,返回列表。"""
    results = model(str(img_path))[0]
    out = []
    for box in results.boxes:# 遍历每个检测框
        cls_id=int(box.cls[0]) # 类别编号，如 0=person
        conf=float(box.conf[0])# 置信度，0~1
        x1,y1,x2,y2=[int(v) for v in box.xyxy[0].tolist()] # 框的像素坐标
        name = model.names[cls_id] # 编号 → 名字
        out.append({
            "class_name": CLASS_NAME_MAP.get(name, name),
            "confidence": round(conf,2),
            "bbox":[x1,y1,x2,y2],
        })
    return out


#2026/9/9
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
    # 一张图跑两次:通用模型找 person/bus 等,安全帽模型找 hardhat/no-hardhat,结果合并
    detections = _detect_one(general_model, img_path) + _detect_one(hardhat_model, img_path)

    return {"image_path":image_path, "detections":detections}