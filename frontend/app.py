"""AI 智能体时空智能平台 — 纯前端页面（Flask 仅作模板渲染 + /api 同源反代，无后端业务逻辑）

路由：
  /       官网首页
  /login  登录/注册页（纯前端交互）
  /map    园区巡检地图可视化页（直接输出 pure_html_map/index.html）
  /api/*  同源反代 → 后端 D 模块 127.0.0.1:8000（只读转发冻结契约，零后端改动；
          目的：页面统一走本站同源请求，规避浏览器跨端口/代理拦截与 CORS 依赖）
"""
import os
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template, request, send_from_directory
load_dotenv()

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

BACKEND_ORIGIN = "http://127.0.0.1:8000"  # 后端 D 模块地址（冻结契约宿主）


@app.after_request
def no_html_cache(resp):
    """页面响应禁用缓存：调试期保证浏览器每次拿到最新模板/内联脚本，
    避免旧页面（直连 8000 时代）残留在缓存里造成「修好了还红条」。"""
    if resp.mimetype == "text/html":
        resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.route("/api/<path:rest>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def api_proxy(rest):
    """把本站 /api/* 请求转发到后端 127.0.0.1:8000，原样回传状态码与 JSON 信封。"""
    ua = (request.headers.get("User-Agent") or "")[:90]
    print(f"[proxy] {request.method} {request.full_path} UA={ua}", flush=True)
    payload = request.get_data() if request.method not in ("GET", "HEAD") else None
    headers = {}
    for key in ("Content-Type", "Authorization", "Accept"):
        if key in request.headers:
            headers[key] = request.headers[key]
    req = urllib.request.Request(
        BACKEND_ORIGIN + "/api/" + rest
        + (("?" + request.query_string.decode("utf-8")) if request.query_string else ""),
        data=payload, method=request.method, headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return (resp.read(), resp.status,
                    {"Content-Type": resp.headers.get_content_type() or "application/json"})
    except urllib.error.HTTPError as err:
        return (err.read(), err.code,
                {"Content-Type": err.headers.get_content_type() or "application/json"})
    except urllib.error.URLError:
        body = '{"code":50000,"message":"后端服务不可用（请确认 127.0.0.1:8000 已启动）","data":null}'.encode("utf-8")
        return body, 502, {"Content-Type": "application/json"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/map")
def map_page():
    """地图可视化页（纯 HTML + Leaflet，自包含，直接按原文件输出）。"""
    return send_from_directory(BASE_DIR / "pure_html_map", "index.html")


# 首页三数据卡详情页：数据一律实时拉后端 127.0.0.1:8000（7 个冻结接口只读），统计前端现算
@app.route("/robots")
def robots():
    """巡检机器人运行详情：最近巡检任务 task-001 与执行智能体 drone-01 的轨迹/指标。"""
    return render_template("robots.html")


@app.route("/nodes")
def nodes():
    """实时感知节点（巡检点位）详情：点位清单、事件分布与地图。"""
    return render_template("nodes.html")


@app.route("/coverage")
def coverage():
    """巡检覆盖率详情：轨迹对 5 个巡检点位的覆盖明细。"""
    return render_template("coverage.html")


# 首页四大板块 Hub 页：能挂真数据的面板实时拉后端（127.0.0.1:8000，只读冻结接口），
# 无对应数据的方案/案例/客户以静态占位呈现，不伪造数字
@app.route("/capabilities")
def capabilities():
    """产品能力 Hub：六项能力 + 各自联动演示数据面板。"""
    return render_template("capabilities.html")


@app.route("/solutions")
def solutions():
    """解决方案 Hub：三个场景方案，厂区场景挂 task-001 演示数据。"""
    return render_template("solutions.html")


@app.route("/cases")
def cases():
    """落地案例 Hub：华北案例挂 task-001 演示数据，华南案例静态占位。"""
    return render_template("cases.html")


@app.route("/clients")
def clients():
    """合作客户名录（演示环境无后端对应数据，纯图文）。"""
    return render_template("clients.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))