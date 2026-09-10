from openai import OpenAI
from backend.config import get_settings
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent   # agent/ 的上一级再上一级 = 项目根目录
events = json.loads((BASE_DIR / "data" / "events" / "events.json").read_text(encoding="utf-8"))

settings = get_settings()
api_key = settings.agent_deepseek_api_key      # ← 就是 .env 里的 DEEPSEEK_API_KEY
base_url = settings.deepseek_base_url    # ← DEEPSEEK_BASE_URL
model = settings.deepseek_model          # ← DEEPSEEK_MODEL

def query_events(events,event_type=None, min_confidence=None):
    result = []
    for e in events:
        if event_type is not None and e["type"] != event_type:
            continue
        if min_confidence is not None and e["confidence"] < min_confidence:
            continue
        result.append(e)
    return result

tools = [
    {
        "type": "function",
        "function":{
            "name":"query_events",
            "description":"按事件类型和最低置信度，查询厂区的异常事件列表",
            "parameters": {
                "type":"object",
                "properties":{
                    "event_type":{
                        "type":"string",
                        "description":"事件类型：smoke/fire/no_helmet/intrusion/equipment_abnormal"
                    },
                    "min_confidence":{
                        "type":"number",
                        "description":"只返回置信度不低于该值的事件，默认 0",
                    }
                },
                "required":[]
            }
        }
    }
]

messages = [
    {"role": "system", "content": (
        "你是厂区地面巡检的报告助手。根据用户给出的异常事件列表，用中文写一段巡检结论。"
        "要求：1) 一句话概括本次巡检发现了几起异常；"
        "2) 按紧急程度列出需要优先处置的事件；"
        "3) 事件类型含义——smoke=烟雾、fire=明火、no_helmet=未戴安全帽、intrusion=闯入、equipment_abnormal=设备异常；"
        "4) 火情类（smoke/fire）必须排在最前面优先处置。"
    )},     # ← 你写人设和规则
    {"role": "user", "content": "帮我查一下今天厂区发生了哪些 fire（明火）事件，按置信度从高到低列出来。"},
]

client = OpenAI(api_key=api_key, base_url=base_url)

resp = client.chat.completions.create(
    model=model,          # 你 settings 里读到的 "deepseek-chat"，直接用这个变量
    messages=messages,
    tools=tools,
)

tool_call = resp.choices[0].message.tool_calls[0]

args = json.loads(tool_call.function.arguments)

result = query_events(events,event_type=args["event_type"])

messages.append(resp.choices[0].message)

messages.append({
    "role":"tool",
    "tool_call_id":tool_call.id,
    "content":json.dumps(result,ensure_ascii=False),
})

resp2 = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=tools,
)
print(resp2.choices[0].message.content)