import json
import math
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = ROOT / "data" / "map" / "campus.geojson"
OUT_PATH = ROOT / "data" / "tracks" / "task-001.json"

features = json.loads(MAP_PATH.read_text(encoding="utf-8"))

points = []

for f in features["features"]:
    if f["properties"]["kind"] == "inspection_point":
        lng, lat = f["geometry"]["coordinates"]
        points.append({
            "id": f["properties"]["id"],
            "priority": f["properties"]["priority"],
            "lng": lng,
            "lat": lat,
        })

points = sorted(points, key=lambda p: p["priority"])

def heading_between(a,b):
    dlng = b["lng"] - a["lng"]
    dlat = b["lat"] - a["lat"]
    return math.degrees(math.atan2(dlng, dlat)) % 360

# 4. 生成轨迹：从门岗起飞，依次经过巡检点
start = {"id": "IP-000", "lng": 116.12, "lat": 39.13}
waypoints = [start] + points   # 起点 + 巡检点，拼成一条路线

track = []
t = datetime(2026, 9, 1, 8, 0, 0)

for i, wp in enumerate(waypoints):
      # 朝向：指向下一个点；最后一个点沿用 0
      heading = heading_between(wp, waypoints[i + 1]) if i < len(waypoints) - 1 else 0.0

      track.append({
          "timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
          "lng": round(wp["lng"], 3),
          "lat": round(wp["lat"], 3),
          "alt": 15.0,
          "speed": 0.0 if i == 0 else 2.5,   # 起点速度为 0
          "heading": round(heading, 1),
      })

      t += timedelta(seconds=40)   # 每点间隔 40 秒

# 5. 拼结果并写文件
result = {
      "task_id": "task-001",
      "agent_id": "drone-01",
      "status": "finished",
      "track": track,
  }

with open(OUT_PATH, "w", encoding="utf-8") as f:
      json.dump(result, f, ensure_ascii=False, indent=2)

print(f"已生成 {len(track)} 个轨迹点 -> {OUT_PATH}")