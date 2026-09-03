# API 契约（冻结）

> 状态：**第 1 周冻结**。冻结后任何改动需全组同步。
> 在线版：启动服务后打开 http://127.0.0.1:8000/docs（FastAPI 自动生成的 Swagger）。

## 全局约定

### 统一响应信封

所有接口（含错误）都返回同一种结构：

```json
{ "code": 0, "message": "ok", "data": { } }
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | int | `0` 成功，非 0 失败，见错误码表 |
| `message` | string | 提示信息 |
| `data` | any | 业务数据，失败时为 `null` |

### 错误码

| code | HTTP | 含义 |
|---|---|---|
| `0` | 200 | 成功 |
| `40001` | 400 | 业务参数错误 |
| `40401` | 404 | 资源不存在（如 `task_id` 找不到） |
| `42200` | 422 | 请求体校验失败（字段缺失/类型错，FastAPI 自动返回） |
| `50000` | 500 | 服务器内部错误 |

### 基础地址

`http://127.0.0.1:8000`（本机开发）。前缀统一为 `/api`。

---

## 接口一览

| 方法 | 路径 | 入参 | 说明 | 负责模块 |
|---|---|---|---|---|
| GET | `/api/health` | - | 健康检查 | D 后端 |
| GET | `/api/map` | - | 园区 GeoJSON | A 数据 |
| GET | `/api/trajectory` | `task_id` | 巡检轨迹 | A 数据 |
| POST | `/api/plan` | body | 返回巡检点访问顺序 | C 时空智能 |
| POST | `/api/detect` | body | 图片异常检测 | B 感知 |
| GET | `/api/events` | `type`? `status`? | 异常事件列表 | B/A 数据 |
| GET | `/api/report` | `task_id` | 巡检报告 | F 智能体 |

---

## 接口详情

### 1. `GET /api/health`

返回：

```json
{ "code": 0, "message": "ok", "data": { "status": "ok" } }
```

### 2. `GET /api/map`

返回园区地图 GeoJSON（结构见 `data-schema.md` §1），直接放 `data` 里。

```json
{ "code": 0, "message": "ok", "data": { "type": "FeatureCollection", "features": [] } }
```

### 3. `GET /api/trajectory?task_id=task-001`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `task_id` | string | 是 | 任务 ID |

成功返回 `data-schema.md` §2 的轨迹对象；找不到返回 `40401`。

```json
{ "code": 0, "message": "ok", "data": { "task_id": "task-001", "agent_id": "drone-01", "status": "finished", "track": [] } }
```

### 4. `POST /api/plan`

Body（`application/json`）：

```json
{
  "start": { "id": "IP-000", "lng": 116.12, "lat": 39.13 },
  "points": [
    { "id": "IP-001", "lng": 116.15, "lat": 39.18 },
    { "id": "IP-002", "lng": 116.17, "lat": 39.16 }
  ]
}
```

返回：

```json
{ "code": 0, "message": "ok", "data": { "route": ["IP-001", "IP-002"], "total_distance_m": 328.5 } }
```

### 5. `POST /api/detect`

Body（`application/json`）：

```json
{ "image_path": "data/images/evt001.jpg" }
```

返回：

```json
{
  "code": 0, "message": "ok",
  "data": { "image_path": "data/images/evt001.jpg", "detections": [ { "class_name": "smoke", "confidence": 0.92, "bbox": [120, 80, 300, 220] } ] }
}
```

> 第一版用图片路径；后续可扩展为 `multipart/form-data` 上传或 base64（需加 `python-multipart` 依赖）。

### 6. `GET /api/events?type=smoke&status=pending`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `type` | string | 否 | 按类型过滤 |
| `status` | string | 否 | 按状态过滤 |

返回事件数组（结构见 `data-schema.md` §3）：

```json
{ "code": 0, "message": "ok", "data": [ { "event_id": "EVT-001", "type": "smoke", "status": "pending" } ] }
```

### 7. `GET /api/report?task_id=task-001`

返回 `data-schema.md` §6 的报告对象；找不到任务返回 `40401`。

---

## 示例：错误返回

```json
{ "code": 40401, "message": "轨迹 task-999 不存在", "data": null }
```

```json
{ "code": 42200, "message": "参数校验失败", "data": [ { "loc": ["body", "points"], "msg": "field required" } ] }
```

---

## 第二阶段（未冻结，先占位）

- **WebSocket** `/ws/track?task_id=`：轨迹实时回放，前端（E）第 3 周接入。
- **落库 MySQL**：当前接口读 `data/` 下 JSON；接 MySQL（POINT 空间类型）后替换数据源，接口签名不变。
- **SSE 流式输出**：智能体（F）生成报告时的流式输出通道。
