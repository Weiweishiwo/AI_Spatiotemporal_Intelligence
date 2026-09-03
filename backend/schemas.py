"""数据契约（代码形态）。

这里定义的 Pydantic 模型就是全组的「冻结契约」：
docs/data-schema.md 和 docs/api.md 是给人看的文档，本文件是给机器看/给 FastAPI 自动生成
Swagger（/docs）用的同一份契约。改这里 = 改契约，需要全组同步。
"""

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 地图
# ---------------------------------------------------------------------------


class InspectionPoint(BaseModel):
    """巡检点（对应 GeoJSON 里 kind=inspection_point 的 properties）。"""

    id: str
    name: str
    priority: int = 1


# ---------------------------------------------------------------------------
# 轨迹
# ---------------------------------------------------------------------------


class TrackPoint(BaseModel):
    """轨迹上的一个采样点。"""

    timestamp: str  # ISO 8601 UTC，如 2026-09-01T08:00:00Z
    lng: float
    lat: float
    alt: float = 0.0
    speed: float = 0.0
    heading: float = 0.0


class Trajectory(BaseModel):
    task_id: str
    agent_id: str
    status: Literal["running", "finished"] = "finished"
    track: list[TrackPoint]


# ---------------------------------------------------------------------------
# 事件 / 检测
# ---------------------------------------------------------------------------

EventType = Literal["smoke", "fire", "no_helmet", "intrusion", "equipment_abnormal"]
EventStatus = Literal["pending", "confirmed", "resolved", "false_alarm"]


class Event(BaseModel):
    event_id: str
    task_id: str
    timestamp: str
    lng: float
    lat: float
    type: EventType
    confidence: float = Field(ge=0.0, le=1.0)
    image_path: str
    status: EventStatus = "pending"


class Detection(BaseModel):
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[float]  # [x1, y1, x2, y2]


class DetectRequest(BaseModel):
    """检测入参。第一版用图片路径；后续可扩展 base64 或 multipart 上传。"""

    image_path: str


class DetectionResult(BaseModel):
    image_path: str
    detections: list[Detection] = []


# ---------------------------------------------------------------------------
# 路径规划
# ---------------------------------------------------------------------------


class PlanPoint(BaseModel):
    id: str
    lng: float
    lat: float


class PlanRequest(BaseModel):
    points: list[PlanPoint]
    start: PlanPoint | None = None


class PlanResponse(BaseModel):
    route: list[str]  # 访问顺序（巡检点 id 列表）
    total_distance_m: float


# ---------------------------------------------------------------------------
# 报告
# ---------------------------------------------------------------------------


class ReportSummary(BaseModel):
    task_id: str
    agent_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    track_points: int = 0
    events_count: int = 0


class Report(BaseModel):
    task_id: str
    generated_at: str
    summary: ReportSummary
    events: list[Event] = []
    conclusion: str = ""
