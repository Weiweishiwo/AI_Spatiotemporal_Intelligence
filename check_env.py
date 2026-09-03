"""环境检查：判断依赖、样例数据、后端是否就绪，供新成员验证环境。

用法（项目根目录）：
    .venv/Scripts/python.exe check_env.py
"""

import sys
import warnings
from pathlib import Path

# 强制 UTF-8 输出，避免 Windows 控制台中文乱码（和 run.bat 的 chcp 65001 一致）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent
passed = 0
failed = 0


def check(label, fn):
    global passed, failed
    try:
        fn()
    except Exception as e:  # 任何异常都算这一项失败
        failed += 1
        print(f"  [FAIL] {label}")
        print(f"         {e}")
    else:
        passed += 1
        print(f"  [PASS] {label}")


def main():
    print("=" * 58)
    print("环境检查：厂区/园区地面巡检 · 时空智能平台")
    print("=" * 58)

    # 1. Python 版本
    def _python():
        assert sys.version_info >= (3, 10), f"需要 Python 3.10+，当前 {sys.version.split()[0]}"
    check("Python 版本 >= 3.10", _python)

    # 2. 核心依赖（全员都需要）
    for name in ["fastapi", "uvicorn", "pydantic", "pydantic_settings", "sqlmodel",
                 "pymysql", "pandas", "numpy", "pyproj", "networkx", "openai",
                 "httpx", "pytest"]:
        check(f"核心依赖可导入：{name}", lambda n=name: __import__(n))

    # 3. 感知依赖（成员 1 需要；CPU 版 torch，无需 NVIDIA）
    for name in ["ultralytics", "cv2", "torch"]:
        check(f"感知依赖可导入：{name}", lambda n=name: __import__(n))

    # 4. 样例数据文件
    for rel in ["data/map/campus.geojson", "data/tracks/task-001.json", "data/events/events.json"]:
        def _file(rel=rel):
            if not (ROOT / rel).exists():
                raise AssertionError(f"{rel} 不存在")
        check(f"样例数据存在：{rel}", _file)

    # 5. 后端可启动
    def _backend():
        from fastapi.testclient import TestClient
        from backend.main import app
        r = TestClient(app).get("/api/health")
        assert r.status_code == 200 and r.json()["code"] == 0, f"/api/health 异常：{r.text}"
    check("后端可启动：GET /api/health", _backend)

    print("-" * 58)
    total = passed + failed
    print(f"结果：{passed}/{total} 通过")
    if failed == 0:
        print("环境就绪，可以开始开发。")
    else:
        print(f"有 {failed} 项未通过，请按上面 [FAIL] 的提示处理。")
    print("=" * 58)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()