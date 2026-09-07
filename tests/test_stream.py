"""流式接口测试：/ws/track（WebSocket 回放）+ /api/report/stream（SSE）。

帧协议见 docs/api.md「第二阶段」。跑在 JSON 数据源 + 样例数据上。
"""

import json

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# WebSocket 轨迹回放
# ---------------------------------------------------------------------------


def test_ws_replay_sends_all_points():
    with client.websocket_connect("/ws/track?task_id=task-001&interval_ms=1") as ws:
        meta = ws.receive_json()
        assert meta["type"] == "meta"
        assert meta["task_id"] == "task-001"
        assert meta["agent_id"] == "drone-01"
        assert meta["total"] == 10

        seen = 0
        while True:
            msg = ws.receive_json()
            if msg["type"] == "finished":
                break
            assert msg["type"] == "point"
            assert msg["index"] == seen  # 按顺序推，index 连续
            assert {"timestamp", "lng", "lat"} <= set(msg["point"])
            seen += 1

        assert seen == meta["total"] == msg["total"]


def test_ws_track_missing_task_gets_error_frame():
    with client.websocket_connect("/ws/track?task_id=task-999&interval_ms=1") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert "task-999" in msg["message"]


# ---------------------------------------------------------------------------
# SSE 报告流
# ---------------------------------------------------------------------------


def _sse_events(resp):
    """把 SSE 响应体拆成 [(event, data_dict), ...]。"""
    text = b"".join(resp.iter_bytes()).decode("utf-8")
    events = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        event = lines[0].removeprefix("event: ")
        data = json.loads(lines[1].removeprefix("data: "))
        events.append((event, data))
    return events


def test_report_stream_events():
    with client.stream("GET", "/api/report/stream?task_id=task-001") as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        events = _sse_events(resp)

    kinds = [e for e, _ in events]
    assert kinds == ["progress", "progress", "progress", "report", "done"]
    assert events[0][1]["pct"] == 30  # 依次 30 → 60 → 80

    _, report = events[3]
    assert report["task_id"] == "task-001"
    assert report["summary"]["events_count"] == 3
    assert isinstance(report["conclusion"], str)


def test_report_stream_missing_task_404():
    resp = client.get("/api/report/stream", params={"task_id": "task-999"})
    assert resp.status_code == 404
    assert resp.json()["code"] == 40401