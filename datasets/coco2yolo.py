# -*- coding: utf-8 -*-
"""COCO -> YOLO 格式转换(安全帽数据集)

把 hardhat/<split>/_annotations.coco.json 里的框,转成 YOLO 需要的
hardhat/<split>/labels/<图片名>.txt,并把散放的图片归拢进 <split>/images/。

YOLO 标签格式(每行一个框):  类别编号 中心x 中心y 宽 高
后四个数都是「除以图片宽高」之后的 0~1 小数,所以叫归一化坐标。
"""
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\AAA_XUNJIAN\AI_Spatiotemporal_Intelligence\datasets\hardhat")
SPLITS = ["train", "valid", "test"]
CLASSES = ["hardhat", "no-hardhat"]      # 0 = 戴安全帽, 1 = 没戴安全帽
NAME2IDX = {name: i for i, name in enumerate(CLASSES)}


def convert_split(split: str) -> None:
    split_dir = ROOT / split
    images_dir = split_dir / "images"
    labels_dir = split_dir / "labels"

    # 1. 把散放在 <split>/ 下的 jpg 归拢进 <split>/images/
    images_dir.mkdir(exist_ok=True)
    moved = 0
    for jpg in split_dir.glob("*.jpg"):
        shutil.move(str(jpg), str(images_dir / jpg.name))
        moved += 1

    # 2. 读 COCO json
    data = json.loads((split_dir / "_annotations.coco.json").read_text(encoding="utf-8"))
    id2name = {c["id"]: c["name"] for c in data["categories"]}
    id2img = {im["id"]: im for im in data["images"]}

    # 3. 每个标注 -> 一行 YOLO 文本,按图片分组
    labels_dir.mkdir(exist_ok=True)
    per_image: dict[str, list[str]] = {}
    skipped = 0
    stat = Counter()
    for ann in data["annotations"]:
        name = id2name.get(ann["category_id"])
        if name not in NAME2IDX:
            skipped += 1
            continue
        img = id2img[ann["image_id"]]
        w_img, h_img = img["width"], img["height"]
        x, y, bw, bh = ann["bbox"]          # COCO 的 bbox 是 [左上角x, 左上角y, 宽, 高],单位是像素
        if bw <= 1 or bh <= 1:
            skipped += 1
            continue
        # 像素 -> 归一化的 中心点 + 宽高
        cx, cy = (x + bw / 2) / w_img, (y + bh / 2) / h_img
        nw, nh = bw / w_img, bh / h_img
        # 夹到 0~1,防止个别越界的框让训练直接报错
        cx, cy = min(max(cx, 0.0), 1.0), min(max(cy, 0.0), 1.0)
        nw, nh = min(nw, 1.0), min(nh, 1.0)
        stem = Path(img["file_name"]).stem
        per_image.setdefault(stem, []).append(
            f"{NAME2IDX[name]} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}"
        )
        stat[name] += 1

    # 4. 写 txt
    for stem, lines in per_image.items():
        (labels_dir / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    n_imgs = len(list(images_dir.glob("*.jpg")))
    print(f"[{split}] 图片 {n_imgs} 张 / 标注 {len(data['annotations'])} 个 / "
          f"写出标签 {len(per_image)} 个文件 / 无标注图片 {n_imgs - len(per_image)} 张 / 跳过 {skipped} 个")
    print(f"         类别分布: {dict(stat)}")
    if moved:
        print(f"         已把 {moved} 张图移进 images/")


if __name__ == "__main__":
    for s in SPLITS:
        convert_split(s)

    # 5. 生成 data.yaml(YOLOv8 训练的入口文件)
    yaml_text = (
        f"path: {ROOT.as_posix()}\n"
        "train: train/images\n"
        "val: valid/images\n"
        "test: test/images\n"
        f"nc: {len(CLASSES)}\n"
        "names:\n"
        "  0: hardhat\n"
        "  1: no-hardhat\n"
    )
    (ROOT / "data.yaml").write_text(yaml_text, encoding="utf-8")
    print(f"\n已生成 {ROOT / 'data.yaml'}:\n{yaml_text}")
