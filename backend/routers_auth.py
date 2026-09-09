"""Auth REST 接口（新增，未冻结；改动需全组同步，见 docs/api.md Auth 节）。

与 routers.py 里 7 个冻结接口保持同一套信封 {code, message, data}：
成功 code=0；业务失败用 response.error(code, message, http_status)。

手动解析 Authorization: Bearer <token>（不用 FastAPI HTTPBearer 依赖，
避免 401 响应体不是本项目信封格式）。
"""

from fastapi import APIRouter, Request

from .auth_store import (
    AuthStoreError,
    get_user_by_token,
    login_user,
    logout_token,
    register_user,
)
from .response import error, ok
from .schemas import LoginRequest, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _bearer_token(request: Request) -> str | None:
    """从请求头取 Bearer token；头缺失/格式不对 → None。"""
    auth = request.headers.get("Authorization", "")
    scheme, _, value = auth.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


def _unauthorized(message: str = "未登录或登录已过期"):
    return error(40101, message, http_status=401)


def _require_user(request: Request):
    """校验 token → 脱敏 user；无效/过期 → None。"""
    token = _bearer_token(request)
    if token is None:
        return None
    return get_user_by_token(token)


@router.post("/register")
def register(body: RegisterRequest):
    """注册：成功即发会话（自动登录）；重名/邮箱重复 → 40901。"""
    try:
        return ok(register_user(body.username, body.password, body.email))
    except AuthStoreError as e:
        return error(e.code, e.message, e.http_status)


@router.post("/login")
def login(body: LoginRequest):
    """登录：account 支持 username 或 email（大小写不敏感）；失败统一 40101。"""
    try:
        return ok(login_user(body.account, body.password))
    except AuthStoreError as e:
        return error(e.code, e.message, e.http_status)


@router.get("/me")
def me(request: Request):
    """取当前登录用户（脱敏：username/email/created_at，无任何密码字段）。"""
    user = _require_user(request)
    if user is None:
        return _unauthorized()
    return ok(user)


@router.post("/logout")
def logout(request: Request):
    """注销：幂等——token 不在/已过期也返回 ok。"""
    token = _bearer_token(request)
    if token is not None:
        logout_token(token)
    return ok()
