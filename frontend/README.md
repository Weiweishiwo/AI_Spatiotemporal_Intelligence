# 前端模块(E)—— Flask 官网 + 园区巡检地图可视化

已移除秒哒(React)官网模板,前端由 Flask 提供,页面均为纯 HTML/CSS/JS。

## 页面

| 路由 | 页面 | 模板/文件 |
| --- | --- | --- |
| `/` | 官网首页（导航显示登录状态：用户名/退出 + 后端在线状态点） | `templates/index.html` + `static/` |
| `/login` | 登录/注册页（真实接后端 `/api/auth/*`，账号存 `data/users.json`） | `templates/login.html` + `static/` |
| `/map` | 园区巡检地图可视化（底图/轨迹/回放/异常事件，数据接后端 `/api/*`） | 直接输出 `pure_html_map/index.html` |

## 运行

```bash
# 需 flask(见 requirements.txt);用项目根 .venv 或任意含 flask 的环境
python app.py          # 默认 http://127.0.0.1:5000
```

或双击直接打开 `pure_html_map/index.html`(需联网加载 Leaflet CDN)。

## 说明

- 前后端联调：浏览器统一打开 `http://127.0.0.1:5000`（Flask），API 走
  `http://127.0.0.1:8000`（FastAPI，先跑项目根 `run.bat`）。前端页面
  （`index.html` / `login.html`）必须经 Flask 访问，否则 base.html 的
  `url_for` 与 `static/` 都取不到。
- 登录会话：`auth.js`（经 base.html 全站引入）管理 —— 登录成功跳 `/map`；
  导航的登录/退出组 + 「后端在线」状态点（15s 探一次 `/api/health`）都在 `auth.js` 里。
  「记住密码」勾选存 localStorage，否则 sessionStorage（关标签即失效）。
- 地图数据直接请求后端 `http://127.0.0.1:8000/api/{map,trajectory,events}`；
  后端连不上时有降级提示（不改动 7 个冻结接口）。
- 地图页只有 `pure_html_map/index.html` 一份,Flask `/map` 直接引用它,修改后刷新即生效。
