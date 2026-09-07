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
    """用 OpenCV 画一张合成图，模拟「拍到异常」的现场画面。

    为什么这么做：现在没有真机、没有真实图片，先用 OpenCV 画一张带色块的图，
    既能证明 OpenCV 装好了，又给下面的 detect() 提供一张能读的输入图。
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    img=np.zeros((240,320,3),dtype=np.uint8)
    cv2.imwrite(str(path), img)
    return path


def detect(image_path: str) -> dict:
    """占位检测：先返回一个写死的检测结果，证明输出格式是对的。

    【真实实现要替换这里】第二周把这段换成真正的 YOLOv8 推理，例如：
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")          # 首次运行会自动下载权重（需联网）
        results = model(image_path)[0]      # 推理
        # 把 results 里每个框转成 detections 列表（class_name / confidence / bbox）

    输出结构必须保持和 docs/data-schema.md §4 一致，后端 /api/detect 就靠这个格式。
    """
    # 契约：detections 是列表，每个元素 {class_name, confidence, bbox:[x1,y1,x2,y2]}
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
    if len(sys.argv) >1:
        #用法:Python hello_perception.py 图片路径
        img_path = Path(sys.argv[1])
        if not img_path.exists():
            print(f"找不到图片:{img_path}")
            sys.exit(1) #退出程序,1 表示"出错退出"
        print(f"检测图片:{img_path}")
    else:
        #没传图片就用合成图兜底,保持原来的行为
        img_path = make_image_path(IMAGE_DIR / "hello_perception.jpg")
    result = detect(str(img_path))
    print("感知模块 hello-world 运行成功！输出：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
