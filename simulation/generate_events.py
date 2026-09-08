import json
import random
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = ROOT / "data" / "map" / "campus.geojson"
OUT_PATH = ROOT / "data" / "events" / "events.json"

features = json.loads(MAP_PATH.read_text(encoding="utf-8"))

EVENT_TYPES = ["smoke","fire","no_helmet","intrusion","equipment_abnormal"]

point = []

t = datetime(2026,9,1,8,0,0)

for f in features["features"]:
    if(f["properties"]["kind"] == "inspection_point"):
        point.append(f["geometry"]["coordinates"])

events = []

for i in range(1,9):
    t += timedelta(seconds=random.randint(30,80))
    timestamp = t.strftime("%Y-%m-%dT%H:%M:%SZ")
    lng, lat = random.choice(point)
    event = {
        "event_id":f"EVT-{i:03d}",
        "task_id": "task-001",
        "timestamp": timestamp,   # 先写死，下一步再让它递增
        "lng": round(lng,3),          # 提示：round(lng, 3)
        "lat": round(lat,3),
        "type": random.choice(EVENT_TYPES),         # 提示：random.choice(EVENT_TYPES)
        "confidence": round(random.uniform(0.5,1.0),2),   # 提示：random.uniform(0.5, 1.0)，再 round 到 2 位
        "image_path": "data/images/placeholder.jpg",
        "status": "pending",
    }
    events.append(event)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)
print(f"已生成 {len(events)} 个事件 -> {OUT_PATH}")
