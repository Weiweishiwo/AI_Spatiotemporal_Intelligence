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

messages = [
    {"role": "system", "content": (
        "你是厂区地面巡检的报告助手。根据用户给出的异常事件列表，用中文写一段巡检结论。"
        "要求：1) 一句话概括本次巡检发现了几起异常；"
        "2) 按紧急程度列出需要优先处置的事件；"
        "3) 事件类型含义——smoke=烟雾、fire=明火、no_helmet=未戴安全帽、intrusion=闯入、equipment_abnormal=设备异常；"
        "4) 火情类（smoke/fire）必须排在最前面优先处置。"
    )},     # ← 你写人设和规则
    {"role": "user", "content": json.dumps(events, ensure_ascii=False)},   # ← 把事件喂给它
]

client = OpenAI(api_key=api_key, base_url=base_url)

resp = client.chat.completions.create(
    model=model,          # 你 settings 里读到的 "deepseek-chat"，直接用这个变量
    messages=messages,
)
print(resp.choices[0].message.content)