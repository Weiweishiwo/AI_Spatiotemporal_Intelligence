"""AI 智能体时空智能平台 — 纯前端页面（Flask 仅作模板渲染，无后端业务逻辑）

路由：
  /      官网首页
  /login 登录/注册页（纯前端交互）
"""
import os

from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))