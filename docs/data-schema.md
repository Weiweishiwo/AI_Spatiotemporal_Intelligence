# 数据格式契约（冻结）

> 状态：**第 1 周冻结**。冻结后任何字段增删改都需全组同步。
> 代码形态见 `backend/schemas.py`（同一份契约，供 FastAPI 自动生成 /docs 用）。

## 通用约定

| 项 | 约定 |
|---|---|
| 坐标系 | WGS84 经纬度，`lng` 经度、`lat` 纬度，浮点数 |
| 时间 | ISO 8601 UTC，带 `Z` 后缀，如 `2026-09-01T08:00:00Z` |
| 主键命名 | 巡检点 `IP-xxx`、任务 `task-xxx`、事件 `EVT-xxx`、智能体 `drone-xx` |
| 置信度 `confidence` | 0.0 ~ 1.0 浮点 |
| 文件编码 | 全部 UTF-8 |

---

## 1. 园区地图（GeoJSON FeatureCollection）

文件：`data/map/campus.geojson`

Feature 分三类，靠 `properties.kind` 区分：

| kind | geometry 类型 | 说明 | properties |
|---|---|---|---|
| `building` | Polygon | 建筑物 | `name` |
| `road` | LineString | 道路 | `name` |
| `inspection_point` | Point | 巡检点 | `id`、`name`、`priority`（数字越小越优先） |

```jsonc
{
  "type": "FeatureCollection",
  "features": [
    { "type": "Feature", "properties": { "kind": "building", "name": "1号厂房" },
      "geometry": { "type": "Polygon", "coordinates": [[[116.14, 39.16], [116.16, 39.16], [116.16, 39.18], [116.14, 39.18], [116.14, 39.16]]] } },
    { "type": "Feature", "properties": { "kind": "road", "name": "主干道" },
      "geometry": { "type": "LineString", "coordinates": [[116.12, 39.17], [116.20, 39.17]] } },
    { "type": "Feature", "properties": { "kind": "inspection_point", "id": "IP-001", "name": "配电房", "priority": 1 },
      "geometry": { "type": "Point", "coordinates": [116.15, 39.18] } }
  ]
}
```

---

## 2. 巡检轨迹

文件：`data/tracks/{task_id}.json`

| 字段 | 类型 | 说明 |
|---|---|---|
| `task_id` | string | 任务 ID |
| `agent_id` | string | 智能体 ID（如 `drone-01`） |
| `status` | string | `running` / `finished` |
| `track` | array | 采样点，按时间**升序** |

`track[]` 元素字段：`timestamp`、`lng`、`lat`、`alt`(米)、`speed`(m/s)、`heading`(度，0-360)。

```json
{
  "task_id": "task-001",
  "agent_id": "drone-01",
  "status": "finished",
  "track": [
    { "timestamp": "2026-09-01T08:00:00Z", "lng": 116.12, "lat": 39.13, "alt": 15.0, "speed": 0.0, "heading": 45.0 }
  ]
}
```

---

## 3. 异常事件

文件：`data//events.json`（数组）

| 字段 | 类型 | 说明 |
|---|---|---|
| `event_id` | string | 事件 ID |
| `task_id` | string | 关联任务 |
| `timestamp` | string | 发生时间 |
| `lng` / `lat` | float | 位置 |
| `type` | string | 见下方枚举 |
| `confidence` | float | 0~1 |
| `image_path` | string | 现场图路径 |
| `status` | string | 见下方枚举 |

`type` 枚举：`smoke`（烟雾）、`fire`（明火）、`no_helmet`（未戴安全帽）、`intrusion`（闯入）、`equipment_abnormal`（设备异常）。

`status` 枚举：`pending`（待处理）、`confirmed`（已确认）、`resolved`（已处置）、`false_alarm`（误报）。

```json
{
  "event_id": "EVT-001",
  "task_id": "task-001",
  "timestamp": "2026-09-01T08:02:30Z",
  "lng": 116.16,
  "lat": 39.18,
  "type": "smoke",
  "confidence": 0.92,
  "image_path": "data/images/evt001.jpg",
  "status": "pending"
}
```

---

## 4. 感知检测结果

| 字段 | 类型 | 说明 |
|---|---|---|
| `image_path` | string | 被检测图片路径 |
| `detections` | array | 检测框列表 |

`detections[]` 元素：

| 字段 | 类型 | 说明 |
|---|---|---|
| `class_name` | string | 类别名（与事件 `type` 同枚举） |
| `confidence` | float | 0~1 |
| `bbox` | array[4] | `[x1, y1, x2, y2]`，左上/右下像素坐标 |

```json
{
  "image_path": "data/images/evt001.jpg",
  "detections": [
    { "class_name": "smoke", "confidence": 0.92, "bbox": [120, 80, 300, 220] }
  ]
}
```

> 说明：早期草案里类别字段叫 `class`，因 `class` 是 Python 保留字，冻结时改为 `class_name`。

---

## 5. 路径规划

请求（`POST /api/plan` 的 body）：

```json
{
  "start": { "id": "IP-000", "lng": 116.12, "lat": 39.13 },
  "points": [
    { "id": "IP-001", "lng": 116.15, "lat": 39.18 },
    { "id": "IP-002", "lng": 116.17, "lat": 39.16 }
  ]
}
```

响应：

```json
{
  "route": ["IP-001", "IP-002"],
  "total_distance_m": 328.5
}
```

`start` 可选；`route` 是访问顺序（巡检点 id 列表），`total_distance_m` 是估算总里程（米）。

---

## 6. 巡检报告

`GET /api/report` 返回，由智能体模块（F）最终生成，骨架阶段先给占位：

```json
{
  "task_id": "task-001",
  "generated_at": "2026-09-01T08:10:00Z",
  "summary": {
    "task_id": "task-001",
    "agent_id": "drone-01",
    "started_at": "2026-09-01T08:00:00Z",
    "finished_at": "2026-09-01T08:07:00Z",
    "track_points": 10,
    "events_count": 3
  },
  "events": [],
  "conclusion": "本次巡检共发现 3 起异常，建议立即处置 EVT-001 烟雾。"
}
```
