"""时空智能模块（C）hello-world 演示 —— 成员 2。

职责：巡检路径规划（覆盖所有巡检点的可行/最优路线）+ 简单任务调度。
技术栈：networkx（图 / 最短路径 / 贪心 TSP）。

这份 hello-world 的目标：
1. 证明环境装好了（能 import networkx）。
2. 演示路径规划的核心骨架：把巡检点连成图 → 贪心找一条路线 → 输出契约格式。

运行方式（在项目根目录）：
    python spatiotemporal/hello_planning.py

输入/输出契约见 docs/data-schema.md §5 和 docs/api.md 的 POST /api/plan：
    入参：{ start?, points: [{id, lng, lat}, ...] }
    返回：{ route: [id, ...], total_distance_m: float }
"""

import math

import networkx as nx


def haversine_m(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """两个经纬度点之间的地表距离（米）。

    巡检点坐标是 WGS84 经纬度，直接算平面欧氏距离不对，要用球面距离。
    这里用 Haversine 公式，纯 Python 实现，不依赖额外包。
    """
    R = 6371000.0  # 地球半径（米）
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d_lng / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def plan(points: list[dict], start: dict | None = None) -> dict:
    """贪心路径规划：从起点（或第一个点）出发，每次去最近的未访问点。

    这是「最近邻贪心」的 TSP 近似解，不是全局最优，但第一周够用。
    第二周可以在这里换成更优算法，或加约束（优先级、障碍物、任务调度）。
    """
    # 1. 收集所有节点：巡检点 + 可选起点（start 可能不在 points 里，单独加入并去重）
    nodes = list(points)
    current = None
    if start:
        ids = {p["id"] for p in nodes}
        if start["id"] not in ids:
            nodes = [start] + nodes
        current = start["id"]
    else:
        current = nodes[0]["id"]

    all_ids = [p["id"] for p in nodes]
    pos = {p["id"]: (p["lng"], p["lat"]) for p in nodes}

    # 2. 用 networkx 建一个完全图（任意两点之间都有边），边权 = 球面距离
    G = nx.Graph()
    for i, a in enumerate(all_ids):
        for b in all_ids[i + 1:]:
            G.add_edge(a, b, weight=haversine_m(*pos[a], *pos[b]))

    # 3. 最近邻贪心：每次从当前点出发，选最近的未访问点
    route = [current]
    unvisited = set(all_ids) - {current}
    while unvisited:
        nxt = min(unvisited, key=lambda x: G[current][x]["weight"])
        route.append(nxt)
        unvisited.remove(nxt)
        current = nxt

    # 4. 累加总里程，输出契约格式
    total = sum(G[route[i]][route[i + 1]]["weight"] for i in range(len(route) - 1))
    return {"route": route, "total_distance_m": round(total, 2)}


if __name__ == "__main__":
    # 直接用契约里的样例数据（docs/data-schema.md §5）
    start = {"id": "IP-000", "lng": 116.12, "lat": 39.13}
    points = [
        {"id": "IP-001", "lng": 116.15, "lat": 39.18},
        {"id": "IP-002", "lng": 116.17, "lat": 39.16},
    ]
    result = plan(points, start=start)
    print("时空智能模块 hello-world 运行成功！输出：")
    print(result)
