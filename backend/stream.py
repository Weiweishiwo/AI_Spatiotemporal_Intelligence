"""实时/流式接口（docs/api.md「第二阶段」）。

- WebSocket  /ws/track          轨迹实时回放（前端 E 第 3 周接入）
- SSE        /api/report/stream 报告生成过程流式输出（智能体 F 通道的骨架版）
"""

import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from . import services
from .response import error
from .storage import get_storage

router = APIRouter()


@router.websocket("/ws/track")
async def ws_track(
    websocket: WebSocket,
    task_id: str = Query(..., description="任务 ID，如 task-001"),
    interval_ms: int = Query(200, ge=1, description="每两个采样点的间隔（毫秒），越小回放越快"),
):
    """按采样点逐帧推轨迹。帧格式：
    {type:"meta", task_id, agent_id, total} → N 个 {type:"point", index, point:{…}}
    → {type:"finished"}；任务不存在先发 {type:"error", message} 再关闭。
    """
    await websocket.accept()
    try:
        traj = get_storage().trajectory(task_id)
    except LookupError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
        return

    track = traj.get("track", [])
    await websocket.send_json({
        "type": "meta", "task_id": task_id,
        "agent_id": traj.get("agent_id"), "total": len(track),
    })
    try:
        for index, point in enumerate(track):
            await websocket.send_json({"type": "point", "index": index, "point": point})
            await asyncio.sleep(interval_ms / 1000)
        await websocket.send_json({"type": "finished", "total": len(track)})
    except WebSocketDisconnect:
        pass  # 前端中途关页面是正常情况，静默收尾


def _sse(event: str, data: dict) -> str:
    """拼一个 SSE 帧：event: xxx\\ndata: {json}\\n\\n"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/api/report/stream")
async def report_stream(task_id: str = Query(..., description="任务 ID，如 task-001")):
    """SSE 报告流：先发 progress 步骤，最后发 report（data-schema.md §6 结构）。

    智能体（F）接入后把结论生成换成 LLM，同一事件通道不变。
    """
    try:
        traj = get_storage().trajectory(task_id)
        events = get_storage().events(task_id=task_id)
    except LookupError as e:
        return error(40401, str(e), 404)

    async def gen():
        yield _sse("progress", {"step": "加载轨迹", "pct": 30})
        yield _sse("progress", {"step": "收集异常事件", "pct": 60})
        yield _sse("progress", {"step": "生成巡检结论", "pct": 80})
        yield _sse("report", services.build_report(traj, events))
        yield _sse("done", {"message": "报告生成完毕"})

    return StreamingResponse(gen(), media_type="text/event-stream")