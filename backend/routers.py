"""REST 接口层：冻结契约里的 7 个接口（docs/api.md）。

只做三件事：收参数（schemas）→ 调数据源/业务层 → 包统一信封（response.ok/error）。
数据源是 JSON 还是 MySQL 由 storage.get_storage() 决定，路由不感知。
"""

from fastapi import APIRouter, Query

from . import schemas, services
from .response import error, ok
from .storage import get_storage

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return ok({"status": "ok"})


@router.get("/map")
def get_map():
    try:
        return ok(get_storage().map_geojson())
    except LookupError as e:
        return error(40401, str(e), 404)


@router.get("/trajectory")
def get_trajectory(task_id: str = Query(..., description="任务 ID，如 task-001")):
    try:
        return ok(get_storage().trajectory(task_id))
    except LookupError as e:
        return error(40401, str(e), 404)


@router.post("/plan")
def plan(req: schemas.PlanRequest):
    result = services.plan_route(
        req.start.model_dump() if req.start else None,
        [p.model_dump() for p in req.points],
    )
    return ok(schemas.PlanResponse(**result).model_dump())


@router.post("/detect")
def detect(req: schemas.DetectRequest):
    try:
        services.image_abs_path(req.image_path)  # 先确认图片在，不在给 40401
    except LookupError as e:
        return error(40401, str(e), 404)
    return ok(services.run_detect(req.image_path))


@router.get("/events")
def list_events(
    type: str | None = Query(None, description="按类型过滤，如 smoke"),
    status: str | None = Query(None, description="按状态过滤，如 pending"),
):
    return ok(get_storage().events(type=type, status=status))


@router.get("/report")
def get_report(task_id: str = Query(..., description="任务 ID，如 task-001")):
    try:
        traj = get_storage().trajectory(task_id)
        events = get_storage().events(task_id=task_id)
    except LookupError as e:
        return error(40401, str(e), 404)
    return ok(services.build_report(traj, events))