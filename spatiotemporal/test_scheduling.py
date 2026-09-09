"""spatiotemporal/Scheduling.py 的单元测试（pytest）。

运行方式（在项目根目录）：
    pytest spatiotemporal/test_scheduling.py -v

覆盖两部分：
    schedule() —— 每条测试对应一条「调度规则」：
        1. 空输入 → 空路线、零里程
        2. route 不含 start（契约要求）
        3. priority 小的点一定排在大的前面
        4. 所有点都恰好被访问一次（不丢、不重）
        5. 同一优先级内，先访问更近的点（最近邻贪心）
        6. 里程为正、量级正确
        7. 组内 2-opt 只调序、不跨优先级
        8. 单优先级组时与 plan_tour 结果一致
    summarize_mileage() —— 每条测试对应一条「里程规则」：
        9. 空输入 / 空 track / 单点 → 零里程
        10. 总里程量级正确（同一经度差 0.01° 纬度 ≈ 1110 米）
        11. 今日/非今日分段：只统计「段起点落在今天」的段
        12. UTC+8 跨天边界（16:00Z 是东八区午夜）
        13. 多条轨迹累加
"""

from datetime import date

from Scheduling import schedule, summarize_mileage


# ---------------------------------------------------------------------------
# schedule()
# ---------------------------------------------------------------------------


def test_empty_points():
    """没有巡检点时，返回空路线和零里程。"""
    result = schedule([])
    assert result == {"route": [], "total_distance_m": 0.0}


def test_route_excludes_start():
    """契约规定 route 只含巡检点 id，不含 start。"""
    start = {"id": "IP-000", "lng": 116.12, "lat": 39.13}
    points = [{"id": "IP-001", "lng": 116.15, "lat": 39.18, "priority": 1}]
    result = schedule(points, start=start)
    assert result["route"] == ["IP-001"]
    assert "IP-000" not in result["route"]


def test_priority_order():
    """priority 数字小的点，在 route 里必须排在数字大的前面。"""
    start = {"id": "IP-000", "lng": 116.0, "lat": 39.0}
    points = [
        {"id": "LOW", "lng": 116.2, "lat": 39.0, "priority": 3},
        {"id": "HIGH", "lng": 116.1, "lat": 39.0, "priority": 1},
        {"id": "MID", "lng": 116.3, "lat": 39.0, "priority": 2},
    ]
    route = schedule(points, start=start)["route"]
    assert route.index("HIGH") < route.index("MID") < route.index("LOW")


def test_covers_all_points_exactly_once():
    """9 个点（3 个优先级 × 各 3 个），结果应恰好覆盖全部、无重复。"""
    points = [
        {"id": f"IP-{i:03d}", "lng": 116.0 + i * 0.01, "lat": 39.0, "priority": i % 3}
        for i in range(9)
    ]
    result = schedule(points)
    assert len(result["route"]) == len(points)
    assert sorted(result["route"]) == sorted(p["id"] for p in points)


def test_same_priority_nearest_first():
    """同一优先级内，从 start 出发应先访问更近的点。"""
    start = {"id": "IP-000", "lng": 116.0, "lat": 39.0}
    points = [
        {"id": "NEAR", "lng": 116.0, "lat": 39.01, "priority": 1},
        {"id": "FAR", "lng": 116.0, "lat": 39.10, "priority": 1},
    ]
    route = schedule(points, start=start)["route"]
    assert route[0] == "NEAR"


def test_total_distance_magnitude():
    """同一经度、各差 0.01° 纬度 ≈ 1110 米，两段合计约 2220 米左右。"""
    start = {"id": "IP-000", "lng": 116.0, "lat": 39.0}
    points = [
        {"id": "IP-001", "lng": 116.0, "lat": 39.01, "priority": 1},
        {"id": "IP-002", "lng": 116.0, "lat": 39.02, "priority": 1},
    ]
    total = schedule(points, start=start)["total_distance_m"]
    assert 2000 < total < 2500


def test_schedule_two_opt_preserves_priority_order():
    """组内 2-opt 只在同一 priority 内调序，跨优先级顺序不被破坏。"""
    start = {"id": "IP-000", "lng": 0.0, "lat": 0.0}
    points = [
        # priority 1：故意摆成交叉（4 个点），2-opt 会在组内消交叉
        {"id": "A1", "lng": -1.0, "lat": 3.0, "priority": 1},
        {"id": "A2", "lng": -1.0, "lat": -1.0, "priority": 1},
        {"id": "A3", "lng": 6.0, "lat": 1.0, "priority": 1},
        {"id": "A4", "lng": -8.0, "lat": 5.0, "priority": 1},
        # priority 2：两个点
        {"id": "B1", "lng": 10.0, "lat": 0.0, "priority": 2},
        {"id": "B2", "lng": 12.0, "lat": 0.0, "priority": 2},
    ]
    route = schedule(points, start=start)["route"]
    p1 = [p["id"] for p in points if p["priority"] == 1]
    p2 = [p["id"] for p in points if p["priority"] == 2]
    # 所有 priority 1 的点都排在 priority 2 之前
    assert max(route.index(x) for x in p1) < min(route.index(x) for x in p2)
    # 仍覆盖全部点、不丢不重
    assert sorted(route) == sorted(p["id"] for p in points)


def test_schedule_single_group_matches_plan_tour():
    """单优先级组时，schedule 退化成 plan_tour（组内 2-opt 结果一致）。"""
    from planning import plan_tour
    start = {"id": "IP-000", "lng": 0.0, "lat": 0.0}
    coords = [(-1.0, 3.0), (-1.0, -1.0), (6.0, 1.0), (-8.0, 5.0)]
    sched_pts = [{"id": f"P{i}", "lng": lng, "lat": lat, "priority": 1}
                 for i, (lng, lat) in enumerate(coords)]
    plan_pts = [{"id": f"P{i}", "lng": lng, "lat": lat}
                for i, (lng, lat) in enumerate(coords)]
    assert schedule(sched_pts, start=start) == plan_tour(start, plan_pts)


# ---------------------------------------------------------------------------
# summarize_mileage()
# ---------------------------------------------------------------------------


def _traj(*points):
    """把点列表包成契约 §2 的轨迹对象形状。"""
    return {"task_id": "task-x", "agent_id": "drone-01",
            "status": "finished", "track": list(points)}


def test_mileage_empty_tracks():
    assert summarize_mileage([]) == {"total_distance_m": 0.0, "today_distance_m": 0.0}


def test_mileage_empty_track_list():
    assert summarize_mileage([{"task_id": "t", "track": []}]) == \
        {"total_distance_m": 0.0, "today_distance_m": 0.0}


def test_mileage_single_point_no_segment():
    """单点轨迹没有相邻对，贡献 0 里程。"""
    traj = _traj({"timestamp": "2026-09-09T08:00:00Z", "lng": 116.0, "lat": 39.0})
    assert summarize_mileage([traj], today=date(2026, 9, 9)) == \
        {"total_distance_m": 0.0, "today_distance_m": 0.0}


def test_mileage_total_distance_magnitude():
    """同一经度、差 0.01° 纬度 ≈ 1110 米。"""
    traj = _traj(
        {"timestamp": "2026-09-09T08:00:00Z", "lng": 116.0, "lat": 39.0},
        {"timestamp": "2026-09-09T08:01:00Z", "lng": 116.0, "lat": 39.01},
    )
    result = summarize_mileage([traj], today=date(2026, 9, 9))
    assert 1000 < result["total_distance_m"] < 1300
    assert result["today_distance_m"] == result["total_distance_m"]  # 同一段既是总也是今日


def test_mileage_today_split():
    """三段：段1起点昨天、段2起点今天，今日里程只算段2。"""
    traj = _traj(
        {"timestamp": "2026-09-01T08:00:00Z", "lng": 116.0, "lat": 39.00},  # 段1起点，非今天
        {"timestamp": "2026-09-09T08:00:00Z", "lng": 116.0, "lat": 39.01},  # 段2起点，今天
        {"timestamp": "2026-09-09T08:01:00Z", "lng": 116.0, "lat": 39.02},
    )
    result = summarize_mileage([traj], today=date(2026, 9, 9))
    assert 2000 < result["total_distance_m"] < 2500    # 两段 ≈ 2220
    assert 1000 < result["today_distance_m"] < 1300    # 只有段2 ≈ 1110
    assert result["today_distance_m"] < result["total_distance_m"]


def test_mileage_utc8_boundary():
    """16:00Z 是 UTC+8 的午夜分界：15:59Z 仍昨天、16:00Z 已是今天。"""
    traj = _traj(
        {"timestamp": "2026-09-08T15:59:00Z", "lng": 116.0, "lat": 39.00},  # UTC+8 还是 09-08
        {"timestamp": "2026-09-08T16:00:00Z", "lng": 116.0, "lat": 39.01},  # UTC+8 已是 09-09
        {"timestamp": "2026-09-08T16:01:00Z", "lng": 116.0, "lat": 39.02},
    )
    result = summarize_mileage([traj], today=date(2026, 9, 9))
    # 段1起点 15:59Z → 非今天；段2起点 16:00Z → 今天
    assert 2000 < result["total_distance_m"] < 2500
    assert 1000 < result["today_distance_m"] < 1300


def test_mileage_sums_multiple_tracks():
    """多条轨迹的里程累加。"""
    t1 = _traj(
        {"timestamp": "2026-09-09T08:00:00Z", "lng": 116.0, "lat": 39.00},
        {"timestamp": "2026-09-09T08:01:00Z", "lng": 116.0, "lat": 39.01},
    )
    t2 = _traj(
        {"timestamp": "2026-09-09T08:02:00Z", "lng": 116.0, "lat": 39.02},
        {"timestamp": "2026-09-09T08:03:00Z", "lng": 116.0, "lat": 39.03},
    )
    result = summarize_mileage([t1, t2], today=date(2026, 9, 9))
    assert 2000 < result["total_distance_m"] < 2500    # 两段各 ~1110
    assert result["today_distance_m"] == result["total_distance_m"]
