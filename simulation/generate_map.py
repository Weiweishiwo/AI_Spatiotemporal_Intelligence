import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
out_path = ROOT / "data" / "map" / "campus.geojson"

def make_building(name, lng, lat, w, h):
    ring = [
        [lng, lat],  # 左下
        [lng+w, lat],  # 右下
        [lng+w, lat+h],  # 右上
        [lng, lat+h],  # 左上
        [lng, lat],  # 回到左下（闭合）
    ]
    return {
        "type": "Feature",
        "properties": {"kind": "building", "name": name},
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }

def make_road(name, lng1, lat1, lng2, lat2):
    return {
          "type": "Feature",
          "properties": {"kind": "road", "name": name},
          "geometry": {"type": "LineString", "coordinates": [[lng1, lat1], [lng2, lat2]]},
    }


def make_inspection_point(pid, name, priority, lng, lat):
    return {
        "type": "Feature",
        "properties": {"kind": "inspection_point", "id": pid, "name": name, "priority": priority},
        "geometry": {"type": "Point", "coordinates": [lng, lat]},
    }

buildings = [
      make_building("1号厂房", 116.14, 39.16, 0.02, 0.02),   # 我给你示范第一个
      make_building("2号厂房", 116.17, 39.15, 0.02, 0.02),              # 2号厂房，你来填
      make_building("办公楼", 116.13, 39.12, 0.02, 0.02),              # 办公楼
      make_building("仓库", 116.17, 39.18, 0.02, 0.02),              # 仓库
  ]

roads = [
    make_road("主干道",116.12, 39.17,116.20, 39.17),
    make_road("次干道",116.15, 39.12,116.15, 39.20),
  ]
points = [
    make_inspection_point("IP-001","配电房",1,116.15, 39.18),
    make_inspection_point("IP-002","消防栓",1,116.17, 39.16),
    make_inspection_point("IP-003","充电桩",2,116.13, 39.17),
    make_inspection_point("IP-004","门岗",2,116.12, 39.13),
    make_inspection_point("IP-005","水泵房",3,116.18, 39.19),
  ]

features = buildings + roads + points
campus = {"type":"FeatureCollection","features":features}

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(campus, f, ensure_ascii=False, indent=2)
