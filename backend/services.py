"""业务层：C/B 模块接入点 + 报告生成。

【给队友的接入约定】后端按下面的「模块名 + 函数名」自动探测你的实现，
存在就直接用，不存在/报错时回退到本文件内置的兜底实现，接口始终可用：

- C 路径规划（成员 2）：在 spatiotemporal/planning.py 里实现
      def plan_tour(start: dict | None, points: list[dict]) -> dict:
          # start/points 元素: {"id": str, "lng": float, "lat": float}
          # 返回 {"route": [巡检点id, ...], "total_distance_m": float}
- B 感知检测（成员 1）：在 perception/detect.py 里实现
      def run_detect(image_path: str) -> dict:
          # 返回契约 §4 结构 {"image_path": str, "detections": [{class_name, confidence, bbox}]}
"""

import importlib.util
import logging
import math
from datetime import datetime, timezone
from pathlib import Path

from .config import BASE_DIR

logger = logging.getLogger(__name__)

#: 事件 type 枚举 → 中文名（见 data-schema.md §3）
EVENT_TYPE_CN = {
    "smoke": "烟雾",
    "fire": "明火",
    "no_helmet": "未戴安全帽",
    "intrusion": "闯入",
    "equipment_abnormal": "设备异常",
}
#: 建议优先处置的类型：火情类且还没人处理
URGENT_TYPES = ("smoke", "fire")

R_EARTH_M = 6_371_000.0


def _haversine_m(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """两经纬度点的球面距离（米）。规划只需要估算，够用且无额外依赖。"""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_EARTH_M * math.asin(math.sqrt(a))


def _load_external_func(module_name: str, func_name: str):
    """队友模块已交付且能正常导入时返回其函数，否则返回 None（不抛错、不阻塞）。"""
    if importlib.util.find_spec(module_name) is None:
        return None
    try:
        return getattr(importlib.import_module(module_name), func_name, None)
    except Exception as e:
        logger.warning("%s 导入失败，用后端内置实现兜底：%s", module_name, e)
        return None


# ===========================================================================
# 路径规划（接入 C）
# ===========================================================================


def _greedy_nearest_neighbor(start: dict | None, points: list[dict]) -> dict:
    """内置兜底：最近邻贪心（TSP 近似，README 协作约定允许）。

    route 语义与骨架一致：按访问顺序排巡检点 id；给了 start 且它不在
    points 里时插到队首。distance 把「起点 → 第一个点」的里程也算进去。
    """
    todo = [{"id": p["id"], "lng": p["lng"], "lat": p["lat"]} for p in points]
    cur = None if start is None else (start["lng"], start["lat"])
    route: list[str] = []
    total = 0.0

    def _pick_next():
        nonlocal cur, total
        if cur is None:  # 没给起点：从列表第一个开始，保证结果可复现
            nxt = todo.pop(0)
            cur = (nxt["lng"], nxt["lat"])
            return nxt
        idx = min(range(len(todo)), key=lambda i: _haversine_m(
            cur[0], cur[1], todo[i]["lng"], todo[i]["lat"]))
        nxt = todo.pop(idx)
        total += _haversine_m(cur[0], cur[1], nxt["lng"], nxt["lat"])
        cur = (nxt["lng"], nxt["lat"])
        return nxt

    while todo:
        route.append(_pick_next()["id"])

    if start is not None and start["id"] not in route:
        route.insert(0, start["id"])
    return {"route": route, "total_distance_m": round(total, 1)}


def plan_route(start: dict | None, points: list[dict]) -> dict:
    """POST /api/plan 的业务：优先调成员 2 的 spatiotemporal.planning.plan_tour。"""
    fn = _load_external_func("spatiotemporal.planning", "plan_tour")
    if fn is not None:
        try:
            result = fn(start, points)
            route = [str(i) for i in result["route"]]
            return {"route": route, "total_distance_m": float(result["total_distance_m"])}
        except Exception as e:
            logger.warning("spatiotemporal.planning.plan_tour 调用失败，用内置贪心兜底：%s", e)
    return _greedy_nearest_neighbor(start, points)


# ===========================================================================
# 图片检测（接入 B）
# ===========================================================================


def image_abs_path(image_path: str) -> Path:
    """契约里 image_path 相对项目根目录（如 data/images/evt001.jpg）。"""
    path = BASE_DIR / image_path
    if not path.is_file():
        raise LookupError(f"图片 {image_path} 不存在")
    return path


def run_detect(image_path: str) -> dict:
    """POST /api/detect 的业务：优先调成员 1 的 perception.detect.run_detect。"""
    fn = _load_external_func("perception.detect", "run_detect")
    if fn is None:
        logger.info("perception.detect 未交付，/api/detect 返回空检测结果")
        return {"image_path": image_path, "detections": []}
    try:
        return fn(image_path)
    except Exception as e:
        logger.warning("perception.detect.run_detect 调用失败，返回空检测：%s", e)
        return {"image_path": image_path, "detections": []}


# ===========================================================================
# 巡检报告（骨架阶段规则生成；智能体 F 交付后替换 conclusion 生成器）
# ===========================================================================


def _rule_conclusion(events: list[dict]) -> str:
    if not events:
        return "本次巡检未发现异常事件，巡检点状态正常。"
    urgent = [e for e in events if e["type"] in URGENT_TYPES and e["status"] == "pending"]
    others = [e for e in events if e not in urgent]
    summary = [f"本次巡检共发现 {len(events)} 起异常："]
    if urgent:
        summary.append("建议优先处置 " + "、".join(
            f"{e['event_id']}（{EVENT_TYPE_CN.get(e['type'], e['type'])}）"
            for e in urgent))
    if others:
        summary.append("其余待跟进 " + "、".join(
            f"{e['event_id']}（{EVENT_TYPE_CN.get(e['type'], e['type'])}）"
            for e in others))
    return "；".join(summary) + "。"
    # TODO(F 智能体)：接 DeepSeek 后改为 LLM 生成的自然语言结论，
    # 报告结构（data-schema.md §6）不变，只换 conclusion 的来源。


def build_report(traj: dict, events: list[dict]) -> dict:
    """GET /api/report 的业务：轨迹 + 事件 → data-schema.md §6 报告对象。"""
    task_id = traj["task_id"]
    track = traj.get("track", [])
    summary = {
        "task_id": task_id,
        "agent_id": traj.get("agent_id"),
        "started_at": track[0]["timestamp"] if track else None,
        "finished_at": track[-1]["timestamp"] if track else None,
        "track_points": len(track),
        "events_count": len(events),
    }
    return {
        "task_id": task_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "events": events,
        "conclusion": _rule_conclusion(events),
    }