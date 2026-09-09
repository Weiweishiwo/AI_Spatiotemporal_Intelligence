"""时空智能模块（C）—— 任务调度 + 里程统计（成员 2）。

两部分职责：
    1. schedule()          —— 路径规划 + 优先级调度：priority 数字越小的巡检点越先访问，
                               同一优先级内再按距离贪心（最近邻 TSP 近似）。
    2. summarize_mileage() —— 里程统计：把无人机轨迹累加成「总里程 + 今日里程」。

和 hello_planning.py 里的 plan() 的区别：
    - plan()      ：不看优先级，纯按距离贪心（最近邻 TSP 近似）。
    - schedule()  ：priority 数字越小的巡检点越先访问，同一优先级内再按距离贪心。

一句话概括 schedule 的思路：
    先按 priority 分组 → 组内各自做最近邻贪心 → 各组按优先级从小到大串成一条线。

入参/出参契约：
    schedule()：见 docs/data-schema.md §5
        入参：{ start?: {id, lng, lat}, points: [{id, lng, lat, priority}, ...] }
        返回：{ route: [id, ...], total_distance_m: float }
        （route 不含 start，但总里程会算上从 start 出发的第一段距离）
    summarize_mileage()：见 docs/data-schema.md §2
        入参：tracks —— 轨迹对象列表，每个元素含 track 点列表
        返回：{ total_distance_m: float, today_distance_m: float }

运行方式（在项目根目录）：
    python spatiotemporal/Scheduling.py
"""

import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

R_EARTH_M = 6_371_000.0
CN_TZ = timezone(timedelta(hours=8))  # 中国时区 UTC+8（里程「今日」判定用）


def haversine_m(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """两个经纬度点之间的地表距离（米），Haversine 公式，纯 Python 实现。

    说明：本文件可能被按包导入（spatiotemporal.Scheduling），包导入时
    hello_planning 不在 sys.path 上，所以这里内联一份、不跨模块 import
    （与 backend/services.py 的 _haversine_m、planning.py 的 haversine_m
    保持一致，各自自包含）。
    """
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d_lng / 2) ** 2
    a = min(1.0, a)  # 浮点误差可能让 a 略超 1，asin 会报 domain error
    return 2 * R_EARTH_M * math.asin(math.sqrt(a))


def _two_opt(order: list[str], pos: dict, group_of: dict | None = None) -> list[str]:
    """对一条访问顺序做 2-opt 局部搜索（开路径，不回到起点）。

    order   : 节点 id 的访问顺序（order[0] 是固定起点，不会被移动）。
    pos     : {id: (lng, lat)}。
    group_of: 可选 {id: 组键}。给了就只允许反转「同一组内」的子段
              （用于 schedule 的优先级约束：不跨优先级反转）。

    反复尝试反转子段 order[i:j+1]：若反转后总长变短则接受，直到无改进。
    """
    def _d(a: str, b: str) -> float:
        return haversine_m(*pos[a], *pos[b])

    n = len(order)
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                if group_of is not None and group_of[order[i]] != group_of[order[j]]:
                    continue  # 跨组反转会破坏优先级顺序，跳过
                # 反转 [i..j]：去掉边 (i-1,i)（和 (j,j+1) 若存在），换成 (i-1,j)（和 (i,j+1)）
                gain = _d(order[i - 1], order[i]) - _d(order[i - 1], order[j])
                if j + 1 < n:
                    gain += _d(order[j], order[j + 1]) - _d(order[i], order[j + 1])
                if gain > 1e-9:  # 变短才接受
                    order[i:j + 1] = reversed(order[i:j + 1])
                    improved = True
    return order


def schedule(points: list[dict], start: dict | None = None) -> dict:
    """优先级调度（单路线）。

    points : 巡检点列表，每个点是 {id, lng, lat, priority}。
    start  : 可选起点 {id, lng, lat}。若给，则从它出发并计入第一段里程，
             但它本身不出现在 route 里（契约如此）。

    返回   : {"route": [id, ...], "total_distance_m": 米（保留两位小数）}

    实现   : 先按 priority 分组做最近邻贪心串成一条线，再在每个优先级组
             内部做 2-opt 消交叉（不跨组反转，保持优先级顺序）。
    """
    if not points:
        return {"route": [], "total_distance_m": 0.0}

    # 坐标索引：巡检点 + 可选起点（起点在完整路径里固定在最前）
    pos = {p["id"]: (p["lng"], p["lat"]) for p in points}
    if start:
        pos[start["id"]] = (start["lng"], start["lat"])

    # 1. 按 priority 升序分组（契约约定：priority 数字越小越优先）
    groups: dict[int, list[dict]] = {}
    for p in points:
        groups.setdefault(p["priority"], []).append(p)

    route: list[str] = []      # 最终访问顺序（巡检点 id）
    # cur 是「当前位置」的 (lng, lat)。还没定起点时是 None。
    cur: tuple[float, float] | None = (start["lng"], start["lat"]) if start else None

    # 2. 逐个优先级组做最近邻贪心（sorted(groups) 即按 priority 从小到大）
    for priority in sorted(groups):
        unvisited = {p["id"] for p in groups[priority]}
        # 组内第一个点：如果整条路线还没有起点，就取本组第一个点不产生里程
        if cur is None:
            first_id = groups[priority][0]["id"]
            route.append(first_id)
            unvisited.remove(first_id)
            cur = pos[first_id]
        # 组内最近邻贪心：每次从当前点去最近的未访问点
        while unvisited:
            nxt = min(unvisited, key=lambda x: (haversine_m(cur[0], cur[1], *pos[x]), x))
            route.append(nxt)
            unvisited.remove(nxt)
            cur = pos[nxt]

    # 3. 完整路径（含 start）上做「组内 2-opt」：只反转同一 priority 的子段
    order = ([start["id"]] + route) if start else route
    priority_of = {p["id"]: p["priority"] for p in points}
    order = _two_opt(order, pos, group_of=priority_of)

    # 4. 输出：route 不含 start，total 按完整路径累加
    route_out = order[1:] if start else order
    total = sum(haversine_m(*pos[order[i]], *pos[order[i + 1]]) for i in range(len(order) - 1))
    return {"route": route_out, "total_distance_m": round(total, 2)}


def load_inspection_points(geojson_path) -> list[dict]:
    """从园区地图 GeoJSON 里读出所有巡检点（kind=inspection_point）

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


def _utc8_date(timestamp: str) -> date | None:
    """把 ISO 8601 时间戳转成 UTC+8 的日期；解析失败返回 None。

    轨迹 timestamp 形如 "2026-09-01T08:00:00Z"。先把 Z 换成 +00:00 再解析，
    兼容旧版 Python（fromisoformat 直到 3.11 才支持 Z 后缀），再转到东八区取日期。
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if dt.tzinfo is None:  # 没带时区的当 UTC 处理
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(CN_TZ).date()
    except (ValueError, TypeError):
        return None


def summarize_mileage(tracks: list[dict], today: date | None = None) -> dict:
    """累加所有轨迹的里程，返回总里程 + 今日里程。

    tracks : 轨迹对象列表，每个元素含 "track"（点列表，点含 timestamp/lng/lat）。
    today  : 判断「今日」的日期；缺省取 UTC+8 的今天。

    总里程   = 所有相邻轨迹点 haversine 距离之和。
    今日里程 = 同上，但只统计「段起点 UTC+8 日期 == 今天」的段。
    """
    if today is None:
        today = datetime.now(CN_TZ).date()

    total = 0.0
    today_dist = 0.0
    for traj in tracks:
        track = traj.get("track", [])
        for a, b in zip(track, track[1:]):
            d = haversine_m(a["lng"], a["lat"], b["lng"], b["lat"])
            total += d
            # 段归「今天」当且仅当段起点（a）的 UTC+8 日期 == today
            if _utc8_date(a.get("timestamp", "")) == today:
                today_dist += d
    return {
        "total_distance_m": round(total, 2),
        "today_distance_m": round(today_dist, 2),
    }


if __name__ == "__main__":
    # ---- 任务调度演示 ----
    # 从真实园区地图里读出所有巡检点（不用再手写样例数据）
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
    print()

    # ---- 里程统计演示 ----
    # 用契约 §2 的样例形状，构造一条「昨天 + 今天」的轨迹演示。
    # 时间戳 16:00Z 是 UTC+8 的午夜分界：15:59Z 仍是昨天，16:01Z 已是今天。
    tracks = [{
        "task_id": "task-demo",
        "agent_id": "drone-01",
        "status": "finished",
        "track": [
            {"timestamp": "2026-09-08T15:59:00Z", "lng": 116.0, "lat": 39.00},
            {"timestamp": "2026-09-08T16:01:00Z", "lng": 116.0, "lat": 39.01},
            {"timestamp": "2026-09-09T08:00:00Z", "lng": 116.0, "lat": 39.02},
        ],
    }]
    mileage = summarize_mileage(tracks, today=date(2026, 9, 9))
    print("里程统计运行成功！")
    print(f"总里程：{mileage['total_distance_m']} 米")
    print(f"今日里程：{mileage['today_distance_m']} 米")
