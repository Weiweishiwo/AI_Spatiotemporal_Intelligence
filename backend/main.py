"""后端入口：组装 FastAPI 应用（路由 / CORS / 422 信封）。

数据逻辑不在本文件：
- 业务与数据源     backend/routers.py、backend/storage.py、backend/services.py
- 实时/流式接口    backend/stream.py

启动：uvicorn backend.main:app --reload（或直接双击 run.bat）
查看契约：http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import router as rest_router
from .routers_auth import router as auth_router
from .stream import router as stream_router

app = FastAPI(title="厂区/园区地面巡检 · 时空智能平台 API", version="0.2.0")

# 本地前端（E 模块）调试用，demo 阶段全放开；上线前收紧
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rest_router)
app.include_router(auth_router)
app.include_router(stream_router)


@app.exception_handler(RequestValidationError)
async def on_validation_error(request: Request, exc: RequestValidationError):
    """把 FastAPI 默认的 422 校验错误也包装进统一信封。"""
    return JSONResponse(
        status_code=422,
        content={"code": 42200, "message": "参数校验失败", "data": exc.errors()},
    )