"""AI 智能体时空智能平台 — 纯前端页面（Flask 仅作模板渲染，无后端业务逻辑）

路由：
  /      官网首页
  /login 登录/注册页（纯前端交互）
  /map   园区巡检地图可视化页（直接输出 pure_html_map/index.html）
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template, send_from_directory

load_dotenv()

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent


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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))