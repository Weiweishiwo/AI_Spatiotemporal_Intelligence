"""感知模块（B）hello-world 演示 —— 成员 1。

职责：异常检测（安全帽 / 烟火 / 设备状态等）。
技术栈：ultralytics (YOLOv8) + OpenCV。

这份 hello-world 只做两件事，用来证明你第一周的成果：
1. 你的环境装好了（双击 run.bat 装依赖后，能 import cv2 / numpy）。
2. 你理解了感知模块的「输出契约」——检测结果长什么样（见 docs/data-schema.md §4）。

运行方式（在项目根目录，也就是 README.md 那一层）：
    python Xperception/hello_perception.py

它会：用 OpenCV 画一张合成图模拟「拍到异常」，再对它做一次占位检测，
打印出符合契约格式的检测结果 JSON
"""

import json
import cv2
from ultralytics import  YOLO
from pathlib import Path
import numpy as np
import sys

# 项目根目录：本文件在 Xperception/ 下，往上一级就是根目录
BASE_DIR = Path(__file__).resolve().parent.parent
# 合成图放这里，和契约里 image_path 的约定（data/images/...）保持一致
IMAGE_DIR = BASE_DIR / "data" / "images"
MODEL_PATH = Path(__file__).resolve().parent.parent / "yolov8n.pt"
model=YOLO(str(MODEL_PATH))

def make_image_path(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img=np.zeros((240,320,3),dtype=np.uint8)
    cv2.imwrite(str(path), img)
    return path
def detect_folder(folder):
    """ 目的:
            把目录里所有的图片逐张检测,并打印每张的契约JSON
        参数:
            folder:图片所在的目录(Path 对象)
        效果:
            每张图片打印一行==文件名==和检测结果JSON,无返回值
    """
    count = 0
    for i in sorted(folder.iterdir()):
        if i.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue
        count += 1
        result = detect(str(i))
        print(f"=={i.name}==")
        print(json.dumps(result, ensure_ascii=False, indent=2))

def detect(image_path: str) -> dict:
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
    results = model(image_path)[0]
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


if __name__ == "__main__":

