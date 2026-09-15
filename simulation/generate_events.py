import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)  # 固定随机种子：每次生成的事件类型/置信度/位置一致，demo 可复现

ROOT = Path(__file__).resolve().parent.parent
TRACK_PATH = ROOT / "data" / "tracks" / "task-001.json"
OUT_PATH = ROOT / "data" / "events" / "events.json"

EVENT_TYPES = ["smoke", "fire", "no_helmet", "intrusion", "equipment_abnormal"]


def parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


# 事件要和轨迹「时空对齐」：时间落在巡检时间范围内、位置落在轨迹采样点上，
# 这样 demo 才能讲「无人机 X 时飞到 Y 处发现 Z」，而不是随机的时间和位置。
track = json.loads(TRACK_PATH.read_text(encoding="utf-8"))["track"]
t_start = parse_ts(track[0]["timestamp"])
t_end = parse_ts(track[-1]["timestamp"])
duration_s = (t_end - t_start).total_seconds()
track_points = [(p["lng"], p["lat"]) for p in track]

events = []
for i in range(1, 9):
    ts = t_start + timedelta(seconds=random.uniform(0, duration_s))
    lng, lat = random.choice(track_points)
    events.append({
        "event_id": f"EVT-{i:03d}",
        "task_id": "task-001",
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lng": round(lng, 5),
        "lat": round(lat, 5),
        "type": random.choice(EVENT_TYPES),
        "confidence": round(random.uniform(0.5, 1.0), 2),
        "image_path": "data/images/placeholder.jpg",
        "status": "pending",
    })

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)
print(f"已生成 {len(events)} 个事件 -> {OUT_PATH}")