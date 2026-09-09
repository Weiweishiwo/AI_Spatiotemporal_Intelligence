"""Auth 数据与凭证层：JSON 用户表 + 内存会话令牌（新增，未冻结；见 docs/api.md Auth 节）。

设计约束（与项目风格一致）：
- 账号存 DATA_DIR/users.json（不走 MySQL，开箱即用），结构 {"version": 1, "users": [...]}；
  密码绝不明文：PBKDF2-SHA256（随机盐 + 20 万次迭代），库内只存 salt/hash。
- 会话令牌是服务端内存 dict，secrets 随机 256bit，TTL 24h。
  因此：⚠️ 仅支持单进程 uvicorn（run.bat 现状就是单进程）；后端重启后所有令牌失效，
  前端收到 40101 会自动清本地会话、回到未登录态（无需人工干预）。
- 读写 users.json 全程持模块级锁（含"查重→改写"原子性）；哈希计算在锁外做，
  把持锁时间压到毫秒级。写盘用 .tmp + os.replace 原子替换；文件损坏时改名备份再重建。

异常统一抛 AuthStoreError(code, http_status, message)，路由层原样映射。
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from datetime import datetime, timezone

from .config import DATA_DIR

logger = logging.getLogger(__name__)

USERS_PATH = DATA_DIR / "users.json"
TOKEN_TTL = 24 * 3600  # 24h
PBKDF2_ITER = 200_000
PBKDF2_ALGO = "pbkdf2_sha256"

_users_lock = threading.Lock()
_tokens_lock = threading.Lock()
_tokens: dict[str, dict] = {}  # token -> {"username", "user", "exp"}


class AuthStoreError(Exception):
    """带信封错误码与 HTTP 状态的 auth 异常。"""

    def __init__(self, code: int, http_status: int, message: str):
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.message = message  # Exception 只存 args，不设 .message；路由层要用


# ===========================================================================
# users.json 读写（持锁）
# ===========================================================================


def _load_users() -> dict:
    """读用户表；文件缺失 → 空表；文件损坏 → 备份改名后重建（不静默丢数据）。"""
    if not USERS_PATH.exists():
        return {"version": 1, "users": []}
    try:
        return json.loads(USERS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        backup = USERS_PATH.with_name(f"users.json.corrupt-{int(time.time())}")
        try:
            os.replace(USERS_PATH, backup)
        except OSError:
            pass
        logger.warning("users.json 损坏，已备份为 %s 并重建空表：%s", backup.name, e)
        return {"version": 1, "users": []}


def _save_users(data: dict) -> None:
    """原子写：先写 .tmp 再 os.replace（Windows 下目标存在时 replace 可行）。"""
    tmp = USERS_PATH.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(tmp, USERS_PATH)


# ===========================================================================
# 密码 / 用户对象
# ===========================================================================


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """返回 (salt_hex, digest_hex)；不传 salt 时随机生成（注册用）。"""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITER
    ).hex()
    return salt, digest


def _public_user(rec: dict) -> dict:
    """脱敏副本：只给路由/前端看的字段，永不带 salt/pwd_hash。"""
    return {
        "username": rec["username"],
        "email": rec.get("email"),
        "created_at": rec.get("created_at", ""),
    }


def _issue_token(user: dict) -> str:
    """生成内存令牌并登记（dict 单键操作在 GIL 下原子，仍加小锁保持整洁）。"""
    token = secrets.token_hex(32)
    with _tokens_lock:
        _tokens[token] = {
            "username": user["username"],
            "user": user,
            "exp": time.time() + TOKEN_TTL,
        }
    return token


# ===========================================================================
# 对外接口（路由层调用）
# ===========================================================================


def register_user(username: str, password: str, email: str | None = None) -> dict:
    """注册：重名/邮箱重复抛 AuthStoreError(40901)；成功返回 {token, user}。

    email 归一化：None / 空串 / 纯空白 → None（不占唯一索引）。
    """
    username = (username or "").strip()
    email = ((email or "").strip().lower()) or None

    # 哈希计算（贵，~100ms 级）在锁外做
    salt, digest = _hash_password(password)

    with _users_lock:
        data = _load_users()
        users = data["users"]
        for u in users:
            if u["username"] == username:
                raise AuthStoreError(40901, 409, "该用户名或邮箱已被注册，可直接登录")
            if email and u.get("email") and u["email"].lower() == email:
                raise AuthStoreError(40901, 409, "该用户名或邮箱已被注册，可直接登录")

        rec = {
            "username": username,
            "email": email,
            "salt": salt,
            "pwd_hash": digest,
            "algo": PBKDF2_ALGO,
            "iter": PBKDF2_ITER,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        users.append(rec)
        _save_users(data)

    user = _public_user(rec)
    return {"token": _issue_token(user), "user": user}


def login_user(account: str, password: str) -> dict:
    """登录：account 匹配 username（精确）或 email（不区分大小写）。

    找不到用户与密码不符统一抛 40101，文案不区分"账号不存在/密码错"，
    避免暴露用户是否存在；成功返回 {token, user}。
    """
    account = (account or "").strip()
    with _users_lock:
        data = _load_users()
        rec = None
        for u in data["users"]:
            if u["username"] == account:
                rec = u
                break
            if u.get("email") and u["email"].lower() == account.lower():
                rec = u
                break
        if rec is None:
            raise AuthStoreError(40101, 401, "用户名或邮箱 / 密码错误")

    # 比对在锁外做（PBKDF2 贵；rec 的 salt/hash 是不可变快照，安全）
    salt, digest = _hash_password(password, rec["salt"])
    if not hmac.compare_digest(digest, rec["pwd_hash"]):
        raise AuthStoreError(40101, 401, "用户名或邮箱 / 密码错误")

    user = _public_user(rec)
    return {"token": _issue_token(user), "user": user}


def get_user_by_token(token: str) -> dict | None:
    """按令牌取脱敏用户；无效/过期 → None（过期条目顺手清掉）。"""
    if not token:
        return None
    entry = _tokens.get(token)
    if entry is None:
        return None
    if entry["exp"] < time.time():
        logout_token(token)
        return None
    return entry["user"]


def logout_token(token: str) -> None:
    """注销令牌；不存在也无妨（幂等）。"""
    if not token:
        return
    with _tokens_lock:
        _tokens.pop(token, None)
