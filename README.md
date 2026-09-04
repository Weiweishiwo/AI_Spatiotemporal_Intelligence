# 厂区/园区地面巡检 · AI 智能体时空智能平台

> 团队锻炼项目。目标：面向厂区/园区的**地面巡检**系统，核心是「AI 智能体 + 时空智能」，最终形态上无人机。**当前无硬件**，先用仿真数据 + 地图可视化跑通全链路，等有硬件再把数据源换成真机。

---

## 快速开始（新成员先看这里）

> 目标：**装一次 Python，之后双击就能跑**，其余全自动，不需要手动配环境。

### 第一步：装 Python（只做一次）

1. 打开 <https://www.python.org/downloads/> 下载 Python 3.12。
2. 运行安装包，**务必勾选 `Add Python to PATH`**（关键一步），然后一路「下一步」。

### 第二步：下载项目

两种方式任选：

- **最简单**：GitHub 仓库页面点 `Code → Download ZIP`，下载后解压。
- 或用 HTTPS 克隆（需先装 Git）：

```bash
git clone https://github.com/Weiweishiwo/AI_Spatiotemporal_Intelligence.git
```

### 第三步：双击运行

双击项目根目录下的 **`run.bat`**：

- 首次会**自动**创建虚拟环境 `.venv` 并安装依赖（走清华镜像，国内快，可能要几分钟）。
- 之后每次双击都会秒开，不用再配置。

### 常见问题

- **提示 `Python not found`**：装 Python 时没勾 `Add Python to PATH`，重新安装并勾选即可。
- **依赖装到一半报错**：删掉项目里的 `.venv` 文件夹，重新双击 `run.bat`。
- **想更新依赖**：同上，删 `.venv` 后重跑。

> 当前 `run.bat` 启动后端 uvicorn 服务（`backend.main:app`），浏览器打开 http://127.0.0.1:8000/docs 查看 API 契约。

---

## 一、项目定位

- **主题**：地面巡检面向厂区/园区的 AI 智能体时空智能
- **周期**：2-4 周（先做最小可跑通闭环 demo）
- **团队**：5 人（1 组长 + 4 成员），基础偏弱，重在锻炼
- **无硬件方案**：程序化生成仿真时空轨迹 + 异常事件，用地图可视化演示「巡检 → 感知 → 时空规划 → 智能决策 → 报告」全流程

### 为什么不用 AirSim/Gazebo

学习曲线陡（Unreal/C++/环境配置），2-4 周对弱基础组跑不通。用**纯数据/地图仿真**：GeoJSON 定义园区 + 脚本生成轨迹/事件，正好把「时空智能」核心演示出来。

---

## 二、系统架构

```
┌─────────────┐   ┌────────────────┐   ┌─────────────────┐
│ A 时空数据层 │   │ C 时空智能      │   │ F 智能体/决策    │
│ 地图+轨迹+事件│──▶│ 路径规划/调度   │──▶│ 巡检决策/报告    │
└─────────────┘   └────────────────┘   └─────────────────┘
                                              │
┌─────────────┐   ┌────────────────┐          │
│ B 感知(视觉) │──▶│ D 后端服务      │◀─────────┘
│ 异常检测     │   │ FastAPI + DB   │──▶ 前端 E 可视化
└─────────────┘   └────────────────┘    地图/轨迹回放/报告
```

**数据流向**：A 产出园区地图 + 仿真轨迹 + 异常事件 → B 对图像做异常检测 → C 做巡检路径规划/调度 → F 汇总感知+时空上下文做决策/生成报告 → D 统一 REST 接口落库 → E 可视化展示。

---

## 三、技术栈

| 模块 | 技术选型 |
|---|---|
| 通用/环境 | Python 3.10+、`requirements.txt`、`.env`（pydantic-settings） |
| 数据/仿真 | GeoJSON、pandas、numpy、pyproj（经纬度 ↔ 投影坐标） |
| 感知 | ultralytics (YOLOv8)、OpenCV、LabelImg（数据标注） |
| 时空智能 | networkx（TSP 贪心 / 最短路径） |
| 后端 | FastAPI、MySQL 8（POINT 空间类型 + 空间索引）、SQLModel + pymysql、uvicorn |
| 前端 | 纯 HTML + JS + Leaflet + 天地图/OSM 底图、WebSocket（轨迹实时回放） |
| 智能体 | DeepSeek API（openai 兼容 SDK）、function calling 工具调用、SSE 流式输出 |
| 部署/测试 | Docker + docker-compose（起 MySQL）、pytest |

> 两个扣主题的关键点：**MySQL 空间类型**用来做「附近巡检点 / 轨迹相交」这类时空查询；**function calling** 让 DeepSeek 能直接调用后端的巡检、规划接口，而不只是回文字。

---

## 四、任务分工（5 人）

> 核心原则：**第一周冻结数据格式 + API 契约**，各模块并行开发、互不阻塞。每人第一周必须有一个能独立运行的 hello-world demo。

| 角色 | 模块 | 职责 | 交付物 | 难度 |
|---|---|---|---|---|
| **组长** | **技术负责人**（接口契约 + A 数据/仿真 + F 智能体/集成） | ① 牵头定数据格式和 API 契约，写成 `docs/data-schema.md`、`docs/api.md` 并冻结；② 生成园区 GeoJSON、仿真轨迹、异常事件（正好作为契约的落地样例）；③ 写巡检决策 + 报告生成（DeepSeek API + function calling 调用后端接口）；④ 最终全链路集成 + demo 串讲 | 契约文档 + 样例数据 + 决策/报告模块 | ⭐⭐ |
| **成员 1** | **B 感知（视觉）** | 异常检测：安全帽 / 烟火 / 设备状态等，用 YOLOv8 预训练权重 + 合成图/公开数据集跑通，输出检测 API | 推理脚本 + 一个可调用的检测接口 | ⭐⭐⭐ |
| **成员 2** | **C 时空智能** | 巡检路径规划（覆盖所有巡检点的可行/最优路径）+ 简单任务调度 | 路径规划模块 + 单元测试 | ⭐⭐⭐ |
| **成员 3** | **D 后端** | FastAPI 统一 REST 接口，整合 A/C/B 数据，落库 MySQL | REST API + 数据模型 | ⭐⭐ |
| **成员 4** | **E 前端** | 地图可视化：园区地图 + 轨迹回放 + 异常点标注 + 巡检报告页 | Web 前端 demo | ⭐⭐ |

**分工逻辑**：组长兼数据/仿真，因为「冻结数据格式」是组长的职责，最自然的做法就是自己先把样例数据生成出来，避免成为所有人的上游阻塞。感知（成员 1）、时空（成员 2）是项目两大技术亮点，分别给偏算法方向的组员。

---

## 五、数据格式 & API 契约（草案，组长第一周冻结）

### 1. 园区地图（GeoJSON FeatureCollection）

```jsonc
{
  "type": "FeatureCollection",
  "features": [
    { "type": "Feature", "properties": { "kind": "building", "name": "1号厂房" },
      "geometry": { "type": "Polygon", "coordinates": [[[116.1, 39.1], [116.2, 39.1], [116.2, 39.2], [116.1, 39.2], [116.1, 39.1]]] } },
    { "type": "Feature", "properties": { "kind": "road", "name": "主干道" },
      "geometry": { "type": "LineString", "coordinates": [[116.1, 39.15], [116.2, 39.15]] } },
    { "type": "Feature", "properties": { "kind": "inspection_point", "id": "IP-001", "name": "配电房", "priority": 1 },
      "geometry": { "type": "Point", "coordinates": [116.15, 39.18] } }
  ]
}
```

### 2. 巡检轨迹（JSON 数组，按时间升序）

```json
{
  "task_id": "TASK-001",
  "agent_id": "drone-01",
  "track": [
    { "timestamp": "2026-09-01T08:00:00Z", "lng": 116.15, "lat": 39.18, "alt": 15.0, "speed": 2.5, "heading": 90.0 }
  ]
}
```

### 3. 异常事件

```json
{
  "event_id": "EVT-001",
  "timestamp": "2026-09-01T08:12:00Z",
  "lng": 116.16, "lat": 39.19,
  "type": "smoke",
  "confidence": 0.92,
  "image_path": "data/images/evt001.jpg",
  "status": "pending"
}
```

### 4. 感知检测结果

```json
{
  "image_path": "data/images/evt001.jpg",
  "detections": [
    { "class": "smoke", "confidence": 0.92, "bbox": [120, 80, 300, 220] }
  ]
}
```

### 5. REST API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/map` | 返回园区 GeoJSON |
| GET | `/api/trajectory?task_id=` | 返回巡检轨迹 |
| POST | `/api/plan` | 入参巡检点列表，返回访问顺序 |
| POST | `/api/detect` | 入参图片，返回检测结果 |
| GET | `/api/events` | 返回异常事件列表 |
| GET | `/api/report?task_id=` | 返回巡检报告 |

> 以上是草案，组长第一周落实到 `docs/data-schema.md` 和 `docs/api.md` 并冻结。冻结后任何改动需全组同步。

---

## 六、里程碑（2-4 周）

| 周 | 目标 | 关键动作 |
|---|---|---|
| **第 1 周** | 定框架、冻结契约 | 组长定数据格式 + API 契约并产出样例数据；每人搭好各自环境，**出可独立运行的 hello-world demo**；成员 2 出路径规划初版 |
| **第 2 周** | 各模块核心功能 | A 完善轨迹/事件生成；B 检测跑通；C 路径规划 + 调度完成；D 骨架接口；E 地图 + 轨迹静态展示 |
| **第 3 周** | 集成 | D 串起 A/C/B 数据；E 接轨迹回放 + 异常点；F 出决策/报告初版 |
| **第 4 周** | 联调 + demo | 全链路联调、修 bug、写文档、准备演示 |

---

## 七、协作约定

- **Git**：`master` 为主分支，每人 `feature/<模块>` 分支，通过 PR 合并；提交信息写清「why」。
- **契约冻结**：第一周末冻结 `docs/data-schema.md` 和 `docs/api.md`，之后改动必须全组同意。
- **每周 demo**：每周五每人演示自己模块的可运行状态，早发现阻塞。
- **不追求精度**：感知先用现成权重 + 合成图跑通，路径规划先用贪心/TSP 近似，先把闭环做出来。

---

## 八、建议目录结构

```
.
├── README.md
├── requirements.txt        # Python 依赖
├── .env.example            # 配置模板（DeepSeek key、MySQL 连接）
├── docker-compose.yml      # 起 MySQL 容器
├── docs/
│   ├── data-schema.md      # 数据格式（组长冻结）
│   └── api.md              # API 契约（组长冻结）
├── data/
│   ├── map/                # 园区 GeoJSON
│   ├── tracks/             # 仿真轨迹
│   └── events/             # 仿真/合成图片
├── simulation/             # A 数据/仿真生成脚本
├── perception/             # B 感知
├── spatiotemporal/         # C 路径规划/调度
├── agent/                  # F 智能体/决策
├── backend/                # D 后端 FastAPI
└── frontend/               # E 前端可视化
```