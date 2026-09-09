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

## 第二阶段（部分已落地，未冻结；改动仍需全组同步）

### WebSocket `/ws/track`（已实现，D 后端）

轨迹实时回放，前端（E）第 3 周接入。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `task_id` | string | 是 | 任务 ID |
| `interval_ms` | int | 否 | 采样点推送间隔（默认 200），越小回放越快 |

服务端帧格式（每帧一个 JSON）：

1. `{ "type": "meta", "task_id", "agent_id", "total" }` — 总点数
2. N 个 `{ "type": "point", "index": i, "point": { 采样点（§2 track[] 元素）} }`
3. `{ "type": "finished", "total" }`

任务不存在：先发 `{ "type": "error", "message" }` 再关闭连接。

### SSE `GET /api/report/stream?task_id=`（已实现，D 后端）

`Content-Type: text/event-stream`，事件序列：`progress`（`step`/`pct` 加载轨迹 30 → 收集事件 60 → 生成结论 80）→ `report`（data 为 data-schema §6 报告对象）→ `done`。任务不存在返回 HTTP 404 + 统一信封（`40401`）。

> 智能体（F）接入后：conclusion 由 LLM 生成，同一事件通道不变。

### 落库 MySQL（代码就绪、默认关闭；D 后端）

实现见 `backend/storage.py`：`.env` 设 `MYSQL_ENABLED=true` 后启用 MySQL 8
（巡检点 / 事件 / 轨迹点落库，事件与巡检点带 `POINT(4326)` 空间列 + 空间索引；
首次启动自动从 `data/` 灌样例，接口返回结构与 JSON 数据源一致）。
连不上库自动回退 JSON，接口签名不变。空间查询演示：`nearby_events(lng, lat, radius_m)`
（`ST_DistanceSphere` 附近事件），供后续「附近巡检点 / 轨迹相交」类接口复用。
### Auth（新增，未冻结；改动仍需全组同步）— E 模块接入，账号存 JSON

统一信封与错误码同上。会话用 `Authorization: Bearer <token>` 请求头。
token 由后端内存生成（`secrets`，256bit，TTL 24h）——**仅支持单进程
uvicorn（run.bat 现状），后端重启后全部失效，前端会收到 40101 自动回到未登录态。**

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/register` | 注册。body `{username, password, email?}`；成功即发会话（自动登录），返回 `{token, user}`；用户名/邮箱重复 → `40901`/409 |
| POST | `/api/auth/login` | 登录。body `{account, password}`，account 兼容 username（精确）或 email（不区分大小写）；失败统一 `40101`/401「用户名或邮箱 / 密码错误」 |
| GET | `/api/auth/me` | 当前用户（脱敏：username/email/created_at，无任何密码字段）；未登录/过期 → `40101`/401 |
| POST | `/api/auth/logout` | 注销，幂等（token 无效也返回 ok） |

注册约束：username `^[A-Za-z0-9_]{3,20}$`；password 6–64 位；
email 选填（前端为空时不传该键）。密码库内存 `PBKDF2-SHA256`（随机盐 + 20 万次迭代），
`data/users.json`（已 gitignore）只存 salt/hash，绝不存明文。

新错误码：`40101`（未登录/凭证错，HTTP 401）、`40901`（用户名或邮箱已注册，HTTP 409）。

