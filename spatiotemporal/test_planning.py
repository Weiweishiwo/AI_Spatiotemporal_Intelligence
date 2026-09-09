"""spatiotemporal/planning.py 的单元测试（pytest）。

运行方式（在项目根目录）：
    pytest spatiotemporal/test_planning.py -v

每个测试函数对应一条「路径规划」的契约要求，把 plan_tour() 的正确行为钉死：
    1. 空输入 → 空路线、零里程
    2. 参数顺序 (start, points)；start 不作为巡检点出现在 route 里（契约 §5）
    3. 最近邻贪心：从 start 出发先访问更近的点
    4. 所有点都恰好被访问一次（不丢、不重）
    5. 没给 start 时，第一个巡检点「白送」、不产生里程
    6. 里程为正、量级正确
    7. 2-opt 结果永不差于纯贪心
    8. 2-opt 能解开贪心的交叉回头路
"""

from planning import plan_tour


def test_empty_points():
    """没有巡检点时，返回空路线和零里程。"""
    result = plan_tour(None, [])
    assert result == {"route": [], "total_distance_m": 0.0}


def test_route_excludes_start():
    """契约规定 route 只含巡检点 id，不含 start（docs/data-schema.md §5）。"""
    start = {"id": "IP-000", "lng": 116.12, "lat": 39.13}
    points = [{"id": "IP-001", "lng": 116.15, "lat": 39.18}]
    result = plan_tour(start, points)
    assert result["route"] == ["IP-001"]
    assert "IP-000" not in result["route"]


def test_nearest_first_from_start():
    """从 start 出发，应先访问更近的巡检点（最近邻贪心）。"""
    start = {"id": "IP-000", "lng": 116.0, "lat": 39.0}
    points = [
        {"id": "NEAR", "lng": 116.0, "lat": 39.01},
        {"id": "FAR", "lng": 116.0, "lat": 39.10},
    ]
    route = plan_tour(start, points)["route"]
    assert route[0] == "NEAR"


def test_covers_all_points_exactly_once():
    """9 个点，结果应恰好覆盖全部、无重复。"""
    points = [
        {"id": f"IP-{i:03d}", "lng": 116.0 + i * 0.01, "lat": 39.0}
        for i in range(9)
    ]
    result = plan_tour(None, points)
    assert len(result["route"]) == len(points)
    assert sorted(result["route"]) == sorted(p["id"] for p in points)


def test_no_start_first_point_free():
    """没给 start 时，从第一个巡检点出发，第一段不产生里程。"""
    points = [
        {"id": "A", "lng": 116.0, "lat": 39.0},
        {"id": "B", "lng": 116.0, "lat": 39.01},
    ]
    result = plan_tour(None, points)
    assert result["route"][0] == "A"
    # 只有 A→B 一段，约 0.01° 纬度 ≈ 1110 米
    assert 1000 < result["total_distance_m"] < 1300


def test_total_distance_magnitude():
    """同一经度、各差 0.01° 纬度 ≈ 1110 米，两段合计约 2220 米左右。"""
    start = {"id": "IP-000", "lng": 116.0, "lat": 39.0}
    points = [
        {"id": "IP-001", "lng": 116.0, "lat": 39.01},
        {"id": "IP-002", "lng": 116.0, "lat": 39.02},
    ]
    total = plan_tour(start, points)["total_distance_m"]
    assert 2000 < total < 2500


def test_two_opt_never_worse():
    """2-opt 只接受变短的交换，结果永不差于纯贪心。"""
    start = {"id": "IP-000", "lng": 0.0, "lat": 0.0}
    point_sets = [
        # 一条直线上的点：贪心已是最优，2-opt 不应让它变差
        [{"id": "P0", "lng": 1.0, "lat": 0.0},
         {"id": "P1", "lng": 2.0, "lat": 0.0},
         {"id": "P2", "lng": 3.0, "lat": 0.0}],
        # 会交叉的一组点：2-opt 应消交叉、不会更差
        [{"id": "P0", "lng": -1.0, "lat": 3.0},
         {"id": "P1", "lng": -1.0, "lat": -1.0},
         {"id": "P2", "lng": 6.0, "lat": 1.0},
         {"id": "P3", "lng": -8.0, "lat": 5.0}],
    ]
    for points in point_sets:
        greedy = plan_tour(start, points, optimize=False)["total_distance_m"]
        two_opt = plan_tour(start, points, optimize=True)["total_distance_m"]
        assert two_opt <= greedy + 1e-6


def test_two_opt_uncrosses_greedy():
    """已知交叉例子：贪心会绕回头路，2-opt 能解开、里程严格变短。"""
    start = {"id": "IP-000", "lng": 0.0, "lat": 0.0}
    points = [
        {"id": "P0", "lng": -1.0, "lat": 3.0},
        {"id": "P1", "lng": -1.0, "lat": -1.0},
        {"id": "P2", "lng": 6.0, "lat": 1.0},
        {"id": "P3", "lng": -8.0, "lat": 5.0},
    ]
    greedy = plan_tour(start, points, optimize=False)
    two_opt = plan_tour(start, points, optimize=True)
    assert two_opt["total_distance_m"] < greedy["total_distance_m"]
    # 优化前后都仍覆盖全部巡检点、不丢不重
    ids = {p["id"] for p in points}
    assert sorted(greedy["route"]) == sorted(ids)
    assert sorted(two_opt["route"]) == sorted(ids)