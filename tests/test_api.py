"""冻结契约（docs/api.md）的接口冒烟测试。

跑在默认 JSON 数据源上，用的是 data/ 下真实样例（不依赖 MySQL）。
运行方式（项目根目录）：
    .venv\\Scripts\\python -m pytest tests/ -v
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

# 样例数据事实（见 data/tracks/task-001.json、data/events/events.json）
TRACK_POINTS = 10
EVENT_IDS = {"EVT-001", "EVT-002", "EVT-003"}
EXISTING_IMAGE = "data/images/hello_perception.jpg"


def _ok(resp):
    """断言统一信封成功，返回 data。"""
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["message"] == "ok"
    return body["data"]


# ---------------------------------------------------------------------------
# 通用
# ---------------------------------------------------------------------------


def test_health():
    data = _ok(client.get("/api/health"))
    assert data == {"status": "ok"}


def test_unknown_route_not_wrapped():
    assert client.get("/api/nope").status_code == 404


# ---------------------------------------------------------------------------
# 园区地图
# ---------------------------------------------------------------------------


def test_map_is_featurecollection():
    data = _ok(client.get("/api/map"))
    assert data["type"] == "FeatureCollection"
    kinds = {f["properties"]["kind"] for f in data["features"]}
    assert {"building", "road", "inspection_point"} <= kinds


# ---------------------------------------------------------------------------
# 轨迹
# ---------------------------------------------------------------------------


def test_trajectory_found():
    data = _ok(client.get("/api/trajectory", params={"task_id": "task-001"}))
    assert data["task_id"] == "task-001"
    assert data["agent_id"] == "drone-01"
    assert len(data["track"]) == TRACK_POINTS
    first = data["track"][0]
    assert {"timestamp", "lng", "lat", "alt", "speed", "heading"} <= set(first)


def test_trajectory_missing_returns_40401():
    resp = client.get("/api/trajectory", params={"task_id": "task-999"})
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == 40401
    assert body["data"] is None


# ---------------------------------------------------------------------------
# 路径规划（C 模块未交付时走内置最近邻贪心）
# ---------------------------------------------------------------------------

PLAN_POINTS = [
    {"id": "IP-001", "lng": 116.15, "lat": 39.18},
    {"id": "IP-002", "lng": 116.17, "lat": 39.16},
    {"id": "IP-003", "lng": 116.14, "lat": 39.17},
]
START = {"id": "IP-000", "lng": 116.12, "lat": 39.13}


def test_plan_returns_route_and_real_distance():
    data = _ok(client.post("/api/plan", json={"start": START, "points": PLAN_POINTS}))
    assert len(data["route"]) == len(PLAN_POINTS) + 1  # start 不在 points 里时插到队首
    assert data["route"][0] == "IP-000"
    assert set(data["route"]) == {"IP-000", "IP-001", "IP-002", "IP-003"}
    assert data["total_distance_m"] > 0  # 不再返回占位的 0.0


def test_plan_without_start():
    data = _ok(client.post("/api/plan", json={"points": PLAN_POINTS}))
    assert set(data["route"]) == {"IP-001", "IP-002", "IP-003"}
    assert data["total_distance_m"] > 0


def test_plan_route_visits_every_point_once():
    """不管输入顺序如何，每个巡检点都恰好访问一次（规划的核心性质）。"""
    for pts in (PLAN_POINTS, list(reversed(PLAN_POINTS))):
        data = _ok(client.post("/api/plan", json={"points": pts}))
        route = data["route"]
        assert len(route) == len(pts) == len(set(route))  # 无遗漏、无重复
        assert set(route) == {p["id"] for p in pts}


def test_plan_reproducible():
    """同一输入两次规划结果一致（贪心实现是确定性的）。"""
    d1 = _ok(client.post("/api/plan", json={"start": START, "points": PLAN_POINTS}))
    d2 = _ok(client.post("/api/plan", json={"start": START, "points": PLAN_POINTS}))
    assert d1 == d2


def test_plan_validation_error_wrapped():
    resp = client.post("/api/plan", json={"points": [{"id": "IP-001"}]})  # 缺 lng/lat
    assert resp.status_code == 422
    assert resp.json()["code"] == 42200


# ---------------------------------------------------------------------------
# 检测（B 模块未交付时返回空 detections）
# ---------------------------------------------------------------------------


def test_detect_image_missing_returns_40401():
    resp = client.post("/api/detect", json={"image_path": "data/images/nope.jpg"})
    assert resp.status_code == 404
    assert resp.json()["code"] == 40401


def test_detect_existing_image():
    data = _ok(client.post("/api/detect", json={"image_path": EXISTING_IMAGE}))
    assert data["image_path"] == EXISTING_IMAGE
    assert isinstance(data["detections"], list)


# ---------------------------------------------------------------------------
# 异常事件
# ---------------------------------------------------------------------------


def test_events_all_and_filters():
    data = _ok(client.get("/api/events"))
    assert {e["event_id"] for e in data} == EVENT_IDS

    smoke = _ok(client.get("/api/events", params={"type": "smoke"}))
    assert [e["event_id"] for e in smoke] == ["EVT-001"]

    pending = _ok(client.get("/api/events", params={"status": "pending"}))
    assert {e["event_id"] for e in pending} == {"EVT-001", "EVT-002"}

    assert _ok(client.get("/api/events", params={"type": "fire"})) == []
    assert _ok(client.get(
        "/api/events", params={"type": "smoke", "status": "confirmed"})) == []


# ---------------------------------------------------------------------------
# 报告
# ---------------------------------------------------------------------------


def test_report_shape():
    data = _ok(client.get("/api/report", params={"task_id": "task-001"}))
    assert data["task_id"] == "task-001"
    summary = data["summary"]
    assert summary["agent_id"] == "drone-01"
    assert summary["track_points"] == TRACK_POINTS
    assert summary["events_count"] == len(EVENT_IDS)
    assert len(data["events"]) == len(EVENT_IDS)
    assert isinstance(data["conclusion"], str) and "3" in data["conclusion"]


def test_report_missing_returns_40401():
    resp = client.get("/api/report", params={"task_id": "task-999"})
    assert resp.status_code == 404
    assert resp.json()["code"] == 40401