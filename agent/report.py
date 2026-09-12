from openai import OpenAI
from backend.config import get_settings
import json

settings = get_settings()
api_key = settings.agent_deepseek_api_key
base_url = settings.deepseek_base_url
model = settings.deepseek_model


def query_events(events, event_type=None, min_confidence=None):
    result = []
    for e in events:
        if event_type is not None and e["type"] != event_type:
            continue
        if min_confidence is not None and e["confidence"] < min_confidence:
            continue
        result.append(e)
    return result


def query_trajectory(tracks, task_id=None):
    tr = tracks["track"]
    return {
        "task_id": tracks["task_id"],
        "point_count": len(tr),
        "start_time": tr[0]["timestamp"],
        "end_time": tr[-1]["timestamp"],
    }


def generate_conclusion(events, traj):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "query_events",
                "description": "按事件类型和最低置信度，查询厂区的异常事件列表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_type": {"type": "string", "description": "事件类型：smoke/fire/no_helmet/intrusion/equipment_abnormal"},
                        "min_confidence": {"type": "number", "description": "只返回置信度不低于该值的事件，默认 0"},
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_trajectory",
                "description": "查询巡检任务的轨迹概况：点数、起止时间",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "任务ID，如 task-001"}
                    },
                    "required": []
                }
            }
        }
    ]

    messages = [
        {"role": "system", "content": (
            "你是厂区地面巡检的报告助手。你可以调用工具查数据，用中文写一段巡检结论。"
            "要求：1) 一句话概括本次巡检发现了几起异常；"
            "2) 按紧急程度列出需要优先处置的事件；"
            "3) 事件类型含义——smoke=烟雾、fire=明火、no_helmet=未戴安全帽、intrusion=闯入、equipment_abnormal=设备异常；"
            "4) 火情类（smoke/fire）必须排在最前面优先处置。"
        )},
        {"role": "user", "content": "请根据这些巡检数据生成一份完整的巡检结论，覆盖所有异常事件。"},
    ]

    client = OpenAI(api_key=api_key, base_url=base_url)

    while True:
        resp = client.chat.completions.create(model=model, messages=messages, tools=tools)
        msg = resp.choices[0].message

        if not msg.tool_calls:
            break

        messages.append(msg)
        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if name == "query_events":
                result = query_events(events, event_type=args.get("event_type"))
            elif name == "query_trajectory":
                result = query_trajectory(traj, task_id=args.get("task_id"))
            else:
                result = {"error": "未知工具: " + name}

            messages.append({"role": "tool", "tool_call_id": tool_call.id,
                            "content": json.dumps(result, ensure_ascii=False)})

    return msg.content
