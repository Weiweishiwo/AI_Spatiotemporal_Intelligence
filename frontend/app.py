"""AI 智能体时空智能平台 — 纯前端页面（Flask 仅作模板渲染 + /api 同源反代，无后端业务逻辑）

路由：
  /       官网首页
  /login  登录/注册页（纯前端交互）
  /map    园区巡检地图可视化页（直接输出 pure_html_map/index.html）
  /api/*  同源反代 → 后端 D 模块 127.0.0.1:8000（原样转发冻结契约的 GET/POST，零后端改动；
          目的：页面统一走本站同源请求，规避浏览器跨端口/代理拦截与 CORS 依赖）
  /api/report/stream  例外：这一条不走上面的通用反代，单独开一条**流式**透传（见 api_stream）
  /media/images[/<name>]  前端内部路由：把 data/images/ 的 demo 图片供出去给浏览器显示
          （视觉检测演示要叠检测框；后端冻结契约里没有也不需要这类接口）
"""
import os
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, render_template, request, send_from_directory
load_dotenv()

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

BACKEND_ORIGIN = "http://127.0.0.1:8000"  # 后端 D 模块地址（冻结契约宿主）

# demo 图片目录（项目根/data/images）。注意 BASE_DIR 是 frontend/，不是项目根 ——
# 后端 /api/detect 收的是「相对项目根」的路径（backend/services.py::image_abs_path
# 按项目根解析），两边的根必须对齐，写成 BASE_DIR/"data"/"images" 会得到空目录。
DATA_IMAGES = BASE_DIR.parent / "data" / "images"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# 代理超时：/api/detect 首次调用要在后端进程里 import torch 并加载 YOLOv8 权重
# （perception/detect.py 在模块导入期就建模型），冷启动实测 4~8s，慢盘/杀软扫描下更久，
# 15s 不够用；其余接口都只是读 JSON，15s 绰绰有余。
PROXY_TIMEOUT_S = 15
PROXY_TIMEOUT_SLOW = 60
SLOW_PATHS = ("detect",)

# SSE 透传的读超时：流式连接本就该久开，不能复用上面那 15s（那是给「一问一答」定的）。
STREAM_TIMEOUT_S = 300


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
    timeout = PROXY_TIMEOUT_SLOW if rest.startswith(SLOW_PATHS) else PROXY_TIMEOUT_S
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return (resp.read(), resp.status,
                    {"Content-Type": resp.headers.get_content_type() or "application/json"})
    except urllib.error.HTTPError as err:
        return (err.read(), err.code,
                {"Content-Type": err.headers.get_content_type() or "application/json"})
    except urllib.error.URLError:
        # 连接阶段就失败（后端没起 / 端口不通）：秒失败，不是超时
        body = '{"code":50000,"message":"后端服务不可用（请确认 127.0.0.1:8000 已启动）","data":null}'.encode("utf-8")
        return body, 502, {"Content-Type": "application/json"}
    except OSError as err:
        # 读阶段超时：urllib 只把**连接阶段**包成 URLError，等响应等到超时抛的是裸
        # TimeoutError（OSError 子类，且 isinstance(e, URLError) 为 False），上面那个
        # except 接不住。不接就会冒到 Flask → 500 + HTML traceback，前端只能报
        # 「响应解析失败」，既看不出是超时也没法重试。这里补成统一信封（504 + 50001）。
        print(f"[proxy] 读响应失败 {request.method} {request.full_path}: {err!r}", flush=True)
        body = ('{"code":50001,"message":"后端响应超时，请重试'
                '（首次 /api/detect 需加载模型，可能较慢）","data":null}').encode("utf-8")
        return body, 504, {"Content-Type": "application/json"}


@app.route("/api/report/stream")
def api_stream():
    """SSE 专用透传。与 api_proxy 的区别只有两点：逐块转发 + 不设 Content-Length。

    单独开一条的理由：api_proxy 的 resp.read() 读到 EOF 才返回，会把流式压成一次性，
    且 Flask 3-tuple 响应会补上 Content-Length，不可能 chunked。
    /api/report（无 /stream）**仍然走 api_proxy** —— 那条是普通 JSON，缓冲反代正合适。

    路由优先级：Werkzeug 里静态规则排在 <path:...> 之前，所以本函数能抢在 api_proxy 前命中。
    """
    upstream = BACKEND_ORIGIN + "/api/report/stream"
    if request.query_string:
        upstream += "?" + request.query_string.decode("utf-8")
    headers = {}
    for key in ("Accept", "Authorization"):
        if key in request.headers:
            headers[key] = request.headers[key]

    # ★ 必须在返回 Response 之前就把连接建起来：响应头一旦发出去，失败就只能表现为
    #   「200 + 空流」，而 EventSource 的 onerror 拿不到任何原因（它读不到 JSON 信封）。
    #   先连再决定返回什么，才能把 404/502 原样交给前端。
    try:
        resp = urllib.request.urlopen(
            urllib.request.Request(upstream, method="GET", headers=headers),
            timeout=STREAM_TIMEOUT_S,
        )
    except urllib.error.HTTPError as err:
        return (err.read(), err.code,
                {"Content-Type": err.headers.get_content_type() or "application/json"})
    except urllib.error.URLError:
        body = '{"code":50000,"message":"后端服务不可用（请确认 127.0.0.1:8000 已启动）","data":null}'.encode("utf-8")
        return body, 502, {"Content-Type": "application/json"}

    def gen():
        try:
            while True:
                # ★ read1 而不是 read：read(n) 会阻塞到读满 n 字节或 EOF 才返回。现在后端
                #   把 5 帧一口气吐完就关流，两者看不出差别；但这个路由存在的意义正是等 F
                #   模块把生成器改成真·分步产出 —— 那时每帧才几十字节，read(4096) 会攒够
                #   4096 字节才转发，等于把流式又压回批量，而且藏得更深（帧最终会到，只是
                #   全挤在最后）。read1 是「有多少给多少、不为此阻塞」。
                chunk = resp.read1(4096)     # bytes，原样往下吐，不经 str 编解码
                if not chunk:
                    break
                yield chunk
        finally:
            resp.close()                     # 客户端中途断开 → GeneratorExit → 这里收尾

    # 不设 Content-Length → 生成器响应在 HTTP/1.1 下自动走 chunked。
    # 不用 stream_with_context：上游 URL 与请求头都在生成器外算好，生成器内不碰 request，
    # 从根上避开「working outside of request context」。
    return Response(gen(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",           # 将来挂 nginx 时才有用；本机直连无害
    })


# 下方两条是**前端内部**路由（供浏览器显示 demo 图片），与后端冻结契约无关：
# 浏览器看不到 data/ 目录，而视觉检测演示必须能把原图和检测框叠在一起展示。
@app.route("/media/images")
def media_images():
    """列出 data/images 里可送去 /api/detect 的图片。统一信封，页面用 apiGet 取。"""
    try:
        names = sorted(
            p.name for p in DATA_IMAGES.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS
        )
    except OSError:
        names = []      # 目录不存在/无权限：给空列表，页面显示「暂无可用图片」，不抛 500
    return {
        "code": 0, "message": "ok",
        # path = 喂 POST /api/detect 的（后端按项目根解析）；src = 给 <img> 用的本站 URL。
        # 两者不能混用：/media/images/ + "data/images/x.jpg" 会被 safe_join 判成穿越 → 404。
        "data": [
            {"name": n, "path": f"data/images/{n}", "src": f"/media/images/{n}"}
            for n in names
        ],
    }


@app.route("/media/images/<path:name>")
def media_image(name):
    """按文件名送图；send_from_directory 自带路径穿越防护，不存在时是干净的 404。"""
    return send_from_directory(DATA_IMAGES, name)


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


@app.route("/report")
def report():
    """巡检报告详情：任务总结 + 异常事件清单 + 结论，支持 SSE 流式生成进度。"""
    return render_template("report.html")


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