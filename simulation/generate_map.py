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
      make_building("1号厂房", 116.1505, 39.1605, 0.0006, 0.0006),
      make_building("2号厂房", 116.1515, 39.1605, 0.0006, 0.0006),
      make_building("办公楼", 116.1505, 39.1615, 0.0006, 0.0006),
      make_building("仓库", 116.1515, 39.1615, 0.0006, 0.0006),
  ]

roads = [
    make_road("主干道",116.149, 39.161,116.153, 39.161),
    make_road("次干道",116.151, 39.159,116.151, 39.163),
  ]
points = [
    make_inspection_point("IP-001","配电房",1,116.150, 39.160),
    make_inspection_point("IP-002","消防栓",1,116.1505, 39.160),
    make_inspection_point("IP-003","充电桩",2,116.150, 39.161),
    make_inspection_point("IP-004","门岗",2,116.150, 39.160),
    make_inspection_point("IP-005","水泵房",3,116.151, 39.161),
  ]

features = buildings + roads + points
campus = {"type":"FeatureCollection","features":features}

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(campus, f, ensure_ascii=False, indent=2)
