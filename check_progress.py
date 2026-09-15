# -*- coding: utf-8 -*-
"""查看训练进度 —— 训练跑到一半也能随时运行,不会干扰训练

【怎么用】在项目目录下敲:
    .venv\\Scripts\\python.exe check_progress.py

它做两件事:
  1. 读 train_hardhat.log 的尾巴,告诉你"现在正在跑第几轮、这一轮跑到百分之几"
  2. 读 runs/.../results.csv,告诉你"已经跑完的轮次,各自的 mAP 是多少"

results.csv 是 ultralytics 每跑完一轮就追加一行的账本 ——
它是判断训练好坏的**主要依据**,比看进度条有用得多。
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_DIR = ROOT / "runs" / "detect" / "hardhat_yolov8n"
CSV_PATH = RUN_DIR / "results.csv"
LOG_PATH = ROOT / "train_hardhat.log"

TOTAL_EPOCHS = 12          # 和 train_hardhat.py 里的 epochs 保持一致


def show_current_epoch() -> None:
    """从日志尾部解析出"当前跑到第几轮、进度、预计还要多久" """
    if not LOG_PATH.is_file():
        print("  (还没生成 train_hardhat.log)")
        return

    # 进度条用 \r 不断刷新,把 \r 也当换行切开,才能取到最后那一条
    tail = LOG_PATH.read_bytes()[-8000:].decode("utf-8", errors="ignore")
    # 日志里混着终端的颜色/清行控制符(如 \x1b[K、\x1b[34m)。必须先剥掉 ——
    # 它们会顶在行首,让下面的 ^\s* 匹配失败,结果就是"明明在训练却报没找到进度"。
    tail = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", tail)
    lines = tail.replace("\r", "\n").split("\n")

    # 匹配形如:  1/12  1.96G  1.642 ... 640: 21% ━━ 186/862 3.0it/s 1:04<3:42
    pat = re.compile(r"^\s*(\d+)/(\d+)\s+[\d.]+G\s+.*?:\s*(\d+)%.*?(\S+?)<(\S+)\s*$")
    for line in reversed(lines):
        m = pat.match(line)
        if m:
            ep, total, pct, _rate, remain = m.groups()
            print(f"  正在跑:  第 {ep}/{total} 轮,本轮 {pct}%,本轮预计还需 {remain}")
            return
    print("  (没解析到进度条 —— 可能正在做开训前的数据扫描,或刚好在两轮之间的验证阶段)")


def show_history() -> None:
    """读 results.csv,列出每轮的 mAP"""
    if not CSV_PATH.is_file():
        print("  results.csv 还没生成 —— 说明第一轮还没跑完。")
        print("  (ultralytics 是每跑完一轮才写一行,所以开头几分钟这里会是空的,正常)")
        return

    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("  results.csv 还是空的,等第一轮跑完。")
        return

    # 按名字找列,避免 ultralytics 版本间列顺序变化导致读错
    def col(row, key):
        for k in row:
            if key in k:
                return row[k]
        return "?"

    print(f"  已完成:  {len(rows)}/{TOTAL_EPOCHS} 轮")
    print()
    # 注意:results.csv 的 time 列是"从开训到此刻的累计秒数",不是本轮耗时。
    # 所以要减去上一行的值,才是这一轮真正花了多久。
    print(f"  {'轮':>3} {'mAP50':>8} {'mAP50-95':>9} {'精确率':>8} {'召回率':>8}   本轮用时")
    prev_t = 0.0
    for r in rows:
        t = float(r["time"])
        print(f"  {r['epoch']:>3} {col(r,'mAP50(B)'):>8} {col(r,'mAP50-95(B)'):>9} "
              f"{col(r,'precision(B)'):>8} {col(r,'recall(B)'):>8}   {(t-prev_t)/60:.1f}分")
        prev_t = t

    # 用"每轮平均耗时"外推剩余时间
    last = rows[-1]
    done = len(rows)
    sec_per_epoch = float(last["time"]) / done
    remain_min = (TOTAL_EPOCHS - done) * sec_per_epoch / 60
    print()
    print(f"  平均 {sec_per_epoch/60:.1f} 分钟/轮,预计还需约 {remain_min:.0f} 分钟")

    # 顺手指出最好的一轮,以及"最好"是按什么选的
    best = max(rows, key=lambda r: float(col(r, "mAP50-95(B)")))
    print(f"  目前最好: 第 {best['epoch']} 轮,mAP50-95 = {col(best,'mAP50-95(B)')}")


if __name__ == "__main__":
    print("=" * 62)
    print("安全帽训练进度")
    print("=" * 62)
    show_current_epoch()
    print()
    show_history()
    print()
    print(f"详细文件都在: {RUN_DIR}")
    print("=" * 62)
