"""时空智能模块（C）—— 路径规划（成员 2）。

职责：把「可选起点 + 一批巡检点」规划成一条覆盖所有巡检点的巡检路线。
算法：最近邻贪心（TSP 近似）构造初始路线，再用 2-opt 局部搜索消交叉。

这是后端真正接入的入口（backend/services.py 会探测
spatiotemporal.planning.plan_tour），和 hello_planning.py 的 plan() 区别在于：
    - plan()      ：把 start 当普通节点，会把它塞进 route（不符合契约）。
    - plan_tour() ：route 只含巡检点 id，不含 start，但总里程计入
                    「start → 第一个巡检点」这一段（对齐 docs/data-schema.md §5）。

入参/出参契约见 docs/data-schema.md §5：
    入参：plan_tour(start, points)
        start  : 可选起点 {id, lng, lat}；不给则从第一个巡检点出发。
        points : 巡检点列表，每个点是 {id, lng, lat}。
    返回：{ route: [id, ...], total_distance_m: float }

运行方式（在项目根目录）：
    python spatiotemporal/planning.py

注意：本文件是后端 importlib.import_module("spatiotemporal.planning") 的接入点，
必须零跨模块依赖（不能 from hello_planning import ...，包导入时那个名字不在
sys.path 上），所以 haversine_m 在这里内联了一份。
"""

import math

R_EARTH_M = 6_371_000.0


def haversine_m(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """两个经纬度点之间的地表距离（米），Haversine 公式，纯 Python 实现。"""
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


def plan_tour(start: dict | None, points: list[dict], optimize: bool = True) -> dict:
    """最近邻贪心 + 2-opt 路径规划（单路线）。

    start    : 可选起点 {id, lng, lat}。若给，则从它出发并计入第一段里程，
               但它本身不出现在 route 里（契约如此）。
    points   : 巡检点列表，每个点是 {id, lng, lat}。
    optimize : 是否对贪心结果再做 2-opt 局部搜索（默认 True，结果不差于纯贪心）。

    返回     : {"route": [id, ...], "total_distance_m": 米（保留两位小数）}
    """
    if not points:
        return {"route": [], "total_distance_m": 0.0}

    # 坐标索引：巡检点 + 可选起点（起点在完整路径里固定在最前）
    pos = {p["id"]: (p["lng"], p["lat"]) for p in points}
    if start:
        pos[start["id"]] = (start["lng"], start["lat"])

    # 1. 最近邻贪心构造初始顺序（route 不含 start）
    route: list[str] = []
    unvisited = {p["id"] for p in points}
    # cur 是「当前位置」的 (lng, lat)。还没定起点时是 None。
    cur: tuple[float, float] | None = (start["lng"], start["lat"]) if start else None

    # 没给 start 时：取第一个巡检点作为起点，不产生里程
    if cur is None:
        first = points[0]["id"]
        route.append(first)
        unvisited.remove(first)
        cur = pos[first]

    # 每次从当前点去最近的未访问点
    while unvisited:
        nxt = min(unvisited, key=lambda x: (haversine_m(cur[0], cur[1], *pos[x]), x))
        route.append(nxt)
        unvisited.remove(nxt)
        cur = pos[nxt]

    # 2. 完整路径（含 start）上做 2-opt 消交叉
    order = ([start["id"]] + route) if start else route
    if optimize:
        order = _two_opt(order, pos)

    # 3. 输出：route 不含 start，total 按完整路径累加
    route_out = order[1:] if start else order
    total = sum(haversine_m(*pos[order[i]], *pos[order[i + 1]]) for i in range(len(order) - 1))
    return {"route": route_out, "total_distance_m": round(total, 2)}


if __name__ == "__main__":
    # 直接用契约里的样例数据（docs/data-schema.md §5）
    start = {"id": "IP-000", "lng": 116.12, "lat": 39.13}
    points = [
        {"id": "IP-001", "lng": 116.15, "lat": 39.18},
        {"id": "IP-002", "lng": 116.17, "lat": 39.16},
    ]
    result = plan_tour(start, points)
    print("路径规划运行成功！输出：")
    print(result)
