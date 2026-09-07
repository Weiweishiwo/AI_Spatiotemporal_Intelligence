"""后端骨架：把冻结契约落地成可运行的 FastAPI 服务。

当前直接从 data/ 下的 JSON 样例数据读取，不依赖 MySQL，
保证「双击 run.bat 就能跑」。落库 MySQL（成员 3）在第二阶段接。

启动：uvicorn backend.main:app --reload
查看契约：http://127.0.0.1:8000/docs
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from . import schemas
from .response import error, ok

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MAP_PATH = DATA_DIR / "map" / "campus.geojson"
EVENTS_PATH = DATA_DIR / "events" / "events.json"

app = FastAPI(title="厂区/园区地面巡检 · 时空智能平台 API", version="0.1.0")


@app.exception_handler(RequestValidationError)
async def on_validation_error(request: Request, exc: RequestValidationError):
    """把 FastAPI 默认的 422 校验错误也包装进统一信封。"""
    return JSONResponse(
        status_code=422,
        content={"code": 42200, "message": "参数校验失败", "data": exc.errors()},
    )


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_events() -> list[dict]:
    return _load_json(EVENTS_PATH)


@app.get("/api/health")
def health():
    return ok({"status": "ok"})


@app.get("/api/map")
def get_map():
    if not MAP_PATH.exists():
        return error(40401, "园区地图数据不存在", 404)
    return ok(_load_json(MAP_PATH))


@app.get("/api/trajectory")
def get_trajectory(task_id: str = Query(..., description="任务 ID，如 task-001")):
    path = DATA_DIR / "tracks" / f"{task_id}.json"
    if not path.exists():
        return error(40401, f"轨迹 {task_id} 不存在", 404)
    return ok(_load_json(path))


@app.post("/api/plan")
def plan(req: schemas.PlanRequest):
    # 骨架占位：按输入顺序返回。真实路径规划由成员 2（C 时空智能）实现后替换。
    route = [p.id for p in req.points]
    if req.start and req.start.id not in route:
        route.insert(0, req.start.id)
    return ok(schemas.PlanResponse(route=route, total_distance_m=0.0).model_dump())


@app.post("/api/detect")
def detect(req: schemas.DetectRequest):
    # 骨架占位：返回空检测。真实异常检测由成员 1（B 感知）实现后替换。
    return ok(schemas.DetectionResult(image_path=req.image_path, detections=[]).model_dump())


@app.get("/api/events")
def list_events(
    type: str | None = Query(None, description="按类型过滤，如 smoke"),
    status: str | None = Query(None, description="按状态过滤，如 pending"),
):
    events = _load_events()
    if type:
        events = [e for e in events if e.get("type") == type]
    if status:
        events = [e for e in events if e.get("status") == status]
    return ok(events)


@app.get("/api/report")
def get_report(task_id: str = Query(..., description="任务 ID，如 task-001")):
    track_path = DATA_DIR / "tracks" / f"{task_id}.json"
    if not track_path.exists():
        return error(40401, f"轨迹 {task_id} 不存在", 404)
    traj = _load_json(track_path)
    track = traj.get("track", [])
    task_events = [e for e in _load_events() if e.get("task_id") == task_id]
    summary = {
        "task_id": task_id,
        "agent_id": traj.get("agent_id"),
        "started_at": track[0]["timestamp"] if track else None,
        "finished_at": track[-1]["timestamp"] if track else None,
        "track_points": len(track),
        "events_count": len(task_events),
    }
    report = {
        "task_id": task_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "events": task_events,
        "conclusion": "骨架占位：巡检决策与结论由智能体模块（F）接入后生成。",
    }
    return ok(report)
