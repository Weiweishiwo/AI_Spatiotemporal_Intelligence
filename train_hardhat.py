# -*- coding: utf-8 -*-
"""训练 YOLOv8 识别安全帽 —— 基于 hardhat 安全帽数据集

【怎么跑】必须用项目自带的 .venv,它里面是 CUDA 版 torch,能吃到显卡:
    cd D:\\AAA_XUNJIAN\\AI_Spatiotemporal_Intelligence
    .venv\\Scripts\\python.exe train_hardhat.py

    (别用 D:\\AAA_python_XF\\XF_python —— 那个 torch 是 +cpu 版,用不上显卡,会慢几十倍)

【跑完在哪看结果】
    runs/detect/hardhat_yolov8n/
        weights/best.pt   <- 验证集上表现最好的权重,以后线上就用它
        weights/last.pt   <- 最后一轮的权重
        results.csv       <- 每一轮的 loss / mAP 数字,可以用来画曲线
        *.png             <- 混淆矩阵、PR 曲线等图

【为什么这样配参数】见下面每一处的注释。
"""
from pathlib import Path

from ultralytics import YOLO

# ---- 路径:统一以本文件所在目录(项目根)为基准,这样在哪个目录下跑都不出错 ----
ROOT = Path(__file__).resolve().parent
DATA_YAML = ROOT / "datasets" / "hardhat" / "data.yaml"
PRETRAINED = ROOT / "yolov8n.pt"          # COCO 预训练权重,本地已有,不用联网下载

if __name__ == "__main__":
    # ---- 1. 加载模型 ----
    # yolov8n.pt 是在 COCO 80 类上预训练过的。我们不是从零学,而是"借"它已经学会的
    # 边缘/纹理/形状特征,只把最后的分类头改成我们的 2 类(hardhat / no-hardhat)。
    # 这叫迁移学习 —— 是让小数据集也能训出好效果的关键,能省掉十几倍的数据量。
    model = YOLO(str(PRETRAINED))

    # ---- 2. 开训 ----
    model.train(
        # ===== 数据 =====
        data=str(DATA_YAML),   # 数据集说明书:去哪找图、去哪找标签、有几个类
        imgsz=640,             # 训练时把图缩放到 640×640。安全帽在远景里比较小,
                               # 但 640 已是精度/速度的常规平衡点,先用它。
        batch=16,              # 一次喂 16 张图给显卡。8GB 显存跑 yolov8n 很宽裕,
                               # 若之后换 yolov8m 需要降到 8~12。
        workers=4,             # 每个 dataloader 开几个进程来读图+解码(CPU 侧的活)。
                               # 注意:ultralytics 会给 train/val 各建一个 dataloader,
                               # 所以**实际进程数 ≈ workers × 3**,不是 workers 本身。
                               #
                               # 【实测结论,含两次翻车的教训】
                               # 1) 这值**不影响速度**:设 8 和设 12,跑出来都是 3.1 it/s,分毫不差。
                               #    说明瓶颈不在读数据 —— yolov8n 只有 3M 参数、每轮 862 次迭代,
                               #    卡的是"每次迭代的启动开销摊不薄",不是喂不饱数据。
                               # 2) 但这值**按倍数吃掉提交内存**:设 8 时进程数 ~24、提交内存冲到
                               #    58GB/59GB;设 12 时直接把内存撑爆,OpenCV 抛
                               #    Insufficient memory 当场崩掉。(本机只有 15.7GB 物理内存)
                               #    原因不是工作集大,而是每个进程都预留一大块虚拟内存。
                               # 3) 一个反直觉的坑:workers 越大 → 进程越多 → 内存越爆,
                               #    但速度一点不涨。所以这个参数**只该往小给**,4 够用且安全。
                               #    实测 4 与 8 速度一致。

        # ===== 训练时长 =====
        epochs=12,             # 把 13782 张训练图过 12 遍。这是按"1 小时内出结果"倒推的:
                               # 约 5 分钟/轮 × 12 ≈ 60 分钟。轮数越多效果越好,以后可加训。
        patience=12,           # 连续 12 轮没提升就停。设成等于总轮数 = 本轮不会提前中断,
                               # 保证一定能跑满 12 轮拿到完整的 close_mosaic 收益。

        # ===== 硬件 =====
        device=0,              # 用第 0 号显卡(RTX 5060)。写 'cpu' 则用 CPU,会慢几十倍
        amp=True,              # 自动混合精度:用 FP16 算,显存更省、速度更快,精度几乎不掉

        # ===== 数据增强 =====
        # 马赛克增强:把 4 张图拼成 1 张喂进去,逼模型学"半个安全帽""被挡住的工人"这类
        # 困难情况。它是 YOLOv8 最有效的增强,但最后几轮要关掉,让模型适应真实的整图排布。
        # 默认值是 close_mosaic=10(最后 10 轮关)。我们只跑 12 轮,照默认就只剩 2 轮带增强,
        # 等于白设,所以改成 2 —— 让前 10 轮都吃满马赛克。
        close_mosaic=2,

        # ===== 输出 =====
        project=str(ROOT / "runs" / "detect"),   # 结果存放的父目录
        name="hardhat_yolov8n",                  # 本次实验名,结果落在 .../<name>/ 下
        plots=True,            # 每轮画混淆矩阵、PR 曲线等图,方便肉眼判断好坏
        val=True,              # 每轮都在 valid 集上算 mAP,才能挑出 best.pt

        # 其余留默认值即可,这几个默认值值得知道:
        #   optimizer='auto' -> 自动挑优化器(会自动配学习率)
        #   seed=0           -> 固定随机种子,同样的参数跑两次结果基本一致
        #   warmup_epochs=3  -> 前 3 轮把学习率从很小线性升上来,防止一上来就练崩
    )

    # ---- 3. 训练完,直接看它在测试集(test,训练中完全没见过的 2001 张)上的真实水平 ----
    best = ROOT / "runs" / "detect" / "hardhat_yolov8n" / "weights" / "best.pt"
    print(f"\n训练结束。最好权重: {best}")
    print("正在用 test 集评估...")
    YOLO(str(best)).val(data=str(DATA_YAML), split="test", imgsz=640, device=0)
