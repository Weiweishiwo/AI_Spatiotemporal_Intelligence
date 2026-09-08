# 前端模块(E)—— Flask 官网 + 园区巡检地图可视化

已移除秒哒(React)官网模板,前端由 Flask 提供,页面均为纯 HTML/CSS/JS。

## 页面

| 路由 | 页面 | 模板/文件 |
| --- | --- | --- |
| `/` | 官网首页 | `templates/index.html` + `static/` |
| `/login` | 登录/注册页(纯前端交互) | `templates/login.html` + `static/` |
| `/map` | 园区巡检地图可视化(底图/轨迹/回放/异常事件) | 直接输出 `pure_html_map/index.html` |

## 运行

```bash
# 需 flask(见 requirements.txt);用项目根 .venv 或任意含 flask 的环境
python app.py          # 默认 http://127.0.0.1:5000
```

或双击直接打开 `pure_html_map/index.html`(需联网加载 Leaflet CDN)。

## 说明

- 地图数据目前写死在页面内;第二阶段改为请求后端
  `http://127.0.0.1:8000/api/*`(代码预留取数位置,见页面顶部注释)。
- 地图页只有 `pure_html_map/index.html` 一份,Flask `/map` 直接引用它,修改后刷新即生效。
