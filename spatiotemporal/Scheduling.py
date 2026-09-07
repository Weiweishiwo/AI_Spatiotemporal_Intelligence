"""时空智能模块（C）—— 任务调度（成员 2）。

职责：在「路径规划」的基础上加优先级约束，做单条巡检路线的排序调度。

和 hello_planning.py 里的 plan() 的区别：
    - plan()      ：不看优先级，纯按距离贪心（最近邻 TSP 近似）。
    - schedule()  ：priority 数字越小的巡检点越先访问，同一优先级内再按距离贪心。

一句话概括 schedule 的思路：
    先按 priority 分组 → 组内各自做最近邻贪心 → 各组按优先级从小到大串成一条线。

入参/出参契约见 docs/data-schema.md §5：
    入参：{ start?: {id, lng, lat}, points: [{id, lng, lat, priority}, ...] }
    返回：{ route: [id, ...], total_distance_m: float }
    （route 不含 start，但总里程会算上从 start 出发的第一段距离）

运行方式（在项目根目录）：
    python spatiotemporal/Scheduling.py
"""

import json
from pathlib import Path

from hello_planning import haversine_m


def schedule(points: list[dict], start: dict | None = None) -> dict:
    """优先级调度（单路线）。

    points : 巡检点列表，每个点是 {id, lng, lat, priority}。
    start  : 可选起点 {id, lng, lat}。若给，则从它出发并计入第一段里程，
             但它本身不出现在 route 里（契约如此）。

    返回   : {"route": [id, ...], "total_distance_m": 米（保留两位小数）}
    """
    if not points:
        return {"route": [], "total_distance_m": 0.0}

    # 1. 按 priority 升序分组（契约约定：priority 数字越小越优先）
    groups: dict[int, list[dict]] = {}
    for p in points:
        groups.setdefault(p["priority"], []).append(p)

    route: list[str] = []      # 最终访问顺序（巡检点 id）
    total = 0.0                # 累计里程（米）
    # cur 是「当前位置」的 (lng, lat)。还没定起点时是 None。
    cur: tuple[float, float] | None = (start["lng"], start["lat"]) if start else None

    # 2. 逐个优先级组处理（sorted(groups) 即按 priority 从小到大）
    for priority in sorted(groups):
        group = groups[priority]
        pos = {p["id"]: (p["lng"], p["lat"]) for p in group}
        unvisited = set(pos)

        # 组内第一个点：如果整条路线还没有起点，就取本组第一个点不产生里程
        if cur is None:
            first_id = group[0]["id"]
            route.append(first_id)
            unvisited.remove(first_id)
            cur = pos[first_id]

        # 组内最近邻贪心：每次从当前点去最近的未访问点
        while unvisited:
            nxt = min(unvisited, key=lambda x: haversine_m(cur[0], cur[1], *pos[x]))
            total += haversine_m(cur[0], cur[1], *pos[nxt])
            route.append(nxt)
            unvisited.remove(nxt)
            cur = pos[nxt]

    return {"route": route, "total_distance_m": round(total, 2)}


def load_inspection_points(geojson_path) -> list[dict]:
    """从园区地图 GeoJSON 里读出所有巡检点（kind=inspection_point）。

    把每个巡检点转成 schedule() 需要的格式：{id, lng, lat, priority}。
    """
    data = json.loads(Path(geojson_path).read_text(encoding="utf-8"))
    points = []
    for feat in data["features"]:
        props = feat["properties"]
        if props.get("kind") != "inspection_point":
            continue  # 跳过建筑、道路等非巡检点的要素
        lng, lat = feat["geometry"]["coordinates"]
        points.append({
            "id": props["id"],
            "lng": lng,
            "lat": lat,
            "priority": props.get("priority", 1),
        })
    return points


if __name__ == "__main__":
    # 从真实园区地图里读出所有巡检点（不用再手写样例数据
    map_path = Path(__file__).resolve().parent.parent / "data" / "map" / "campus.geojson"
    points = load_inspection_points(map_path)
    # 起点：假设是园区门口的机库（地图里没有这个点，先临时指定一个）
    start = {"id": "IP-000", "lng": 116.11, "lat": 39.12}

    result = schedule(points, start=start)

    # 把 start 放在最前面，和访问顺序拼成一条完整路径
    path = [start["id"]] + result["route"]

    print("任务调度运行成功！")
    print(f"共 {len(points)} 个巡检点")
    print("巡检路径：")
    print("  " + " → ".join(path))
    print(f"总里程：{result['total_distance_m']} 米")
