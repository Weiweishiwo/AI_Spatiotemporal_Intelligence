"""后端配置。

从项目根目录的 .env 读取（模板见 .env.example），没配就用默认值，
保证「双击 run.bat 就能跑」：默认数据源是 data/ 下的 JSON，MySQL 默认关闭。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（本文件在 backend/ 下，往上一级）
BASE_DIR = Path(__file__).resolve().parent.parent
# 样例数据目录：地图 / 轨迹 / 事件
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """所有配置项。.env 里同名字段会覆盖默认值（大小写不敏感）。"""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---- MySQL（第二阶段数据源，默认关闭）----
    # 打开后若连不上库，会打印警告并自动回退 JSON，服务照常启动。
    mysql_enabled: bool = False
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_db: str = "inspection"

    # ---- DeepSeek（智能体 F 的配置，D 骨架阶段只占位、不调用）----
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"


@lru_cache
def get_settings() -> Settings:
    return Settings()