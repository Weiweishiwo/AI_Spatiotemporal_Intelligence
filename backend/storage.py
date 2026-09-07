"""数据源层：契约接口的数据从哪来（见 docs/api.md 第二阶段「落库 MySQL」）。

两种实现方法签名一致，接口层只面向 get_storage()，切换数据源不碰路由代码：

- JsonStorage  —— 默认。直接读 data/ 下的 JSON 样例，保证「双击 run.bat 就能跑」。
- MysqlStorage —— 第二阶段。MySQL 8：巡检点 / 事件 / 轨迹点落库，
    巡检点和事件带 POINT(4326) 空间列 + 空间索引，nearby_events() 演示
    ST_DistanceSphere 附近查询；首次连上且表为空时自动从 data/ 灌样例，
    接口返回的 JSON 结构和 JsonStorage 完全一致。

⚠️ 本机没装 MySQL 就别开：.env 设 MYSQL_ENABLED=true 后连不上库，
会打印警告并自动回退 JsonStorage，服务照常启动（不阻塞 demo）。
"""

import json
import logging
from pathlib import Path

from sqlalchemy import Column, text
from sqlalchemy.types import UserDefinedType
from sqlmodel import Field, SQLModel, create_engine

from .config import BASE_DIR, DATA_DIR, get_settings

logger = logging.getLogger(__name__)


class MySQLPOINT(UserDefinedType):
    """渲染成 MySQL 空间列「POINT SRID 4326」。

    只借用它的 DDL 效果（create_all 能建出带 SRID 的 POINT 列）；
    空间数据的写入/查询全部走原始 SQL（ST_GeomFromText / ST_DistanceSphere），
    绕开 ORM 对二进制几何类型的绑定问题。
    """

    cache_ok = True

    def get_col_spec(self, **kw) -> str:
        return "POINT SRID 4326"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ===========================================================================
# 默认数据源：读 data/ 下的 JSON
# ===========================================================================


class JsonStorage:
    """样例数据源。data/ 目录结构见 README「建议目录结构」。

    找不到资源时抛 LookupError（消息可直接展示给用户），由路由层转成 40401。
    """

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir

    def map_geojson(self) -> dict:
        path = self.data_dir / "map" / "campus.geojson"
        if not path.exists():
            raise LookupError("园区地图数据不存在")
        return _load_json(path)

    def trajectory(self, task_id: str) -> dict:
        path = self.data_dir / "tracks" / f"{task_id}.json"
        if not path.exists():
            raise LookupError(f"轨迹 {task_id} 不存在")
        return _load_json(path)

    def events(self, type: str | None = None, status: str | None = None,
               task_id: str | None = None) -> list[dict]:
        path = self.data_dir / "events" / "events.json"
        events = _load_json(path) if path.exists() else []
        if type:
            events = [e for e in events if e.get("type") == type]
        if status:
            events = [e for e in events if e.get("status") == status]
        if task_id:
            events = [e for e in events if e.get("task_id") == task_id]
        return events


# ===========================================================================
# MySQL 数据源（默认关闭）：POINT 空间列 + 空间索引 + 附近查询
# ===========================================================================
# 空间列（POINT）不能被 SQLModel/pymysql 正常绑定，所以带 geom 的写入、
# 空间查询统一走 ST_GeomFromText 原始 SQL；普通字段查询走 SQLModel 引擎。


class InspectionPointRow(SQLModel, table=True):
    """巡检点（来自 campus.geojson 里 kind=inspection_point 的 Feature）。"""

    __tablename__ = "inspection_points"

    id: str = Field(primary_key=True)  # IP-001
    name: str
    priority: int = 1
    lng: float
    lat: float
    geom: bytes = Field(sa_column=Column("geom", MySQLPOINT(), nullable=False))


class EventRow(SQLModel, table=True):
    """异常事件，结构与 data/events/events.json 的元素一致。"""

    __tablename__ = "events"

    event_id: str = Field(primary_key=True)  # EVT-001
    task_id: str
    timestamp: str
    lng: float
    lat: float
    type: str
    confidence: float
    image_path: str
    status: str
    geom: bytes = Field(sa_column=Column("geom", MySQLPOINT(), nullable=False))


class TrackPointRow(SQLModel, table=True):
    """轨迹采样点；task_id + seq 联合主键，seq 从 1 递增。"""

    __tablename__ = "track_points"

    task_id: str = Field(primary_key=True)
    seq: int = Field(primary_key=True)
    timestamp: str
    lng: float
    lat: float
    alt: float = 0.0
    speed: float = 0.0
    heading: float = 0.0


class TrajectoryRow(SQLModel, table=True):
    """轨迹头：一个任务一条。"""

    __tablename__ = "trajectories"

    task_id: str = Field(primary_key=True)
    agent_id: str
    status: str = "finished"


class MapFeatureRow(SQLModel, table=True):
    """园区地图：campus.geojson 原样存一份（几何归一化留给以后），一行一条。"""

    __tablename__ = "map_features"

    doc_id: str = Field(primary_key=True, default="campus")
    payload: str  # GeoJSON FeatureCollection 文本


class MysqlStorage:
    """MySQL 数据源。构造时：建表 + 建空间索引 + 空表时从 data/ 灌样例。

    MySQLPOINT() 存经纬度；nearby_events() 用 ST_DistanceSphere 算球面距离，
    这就是 README 里「MySQL 空间类型做附近查询」的落点。
    """

    def __init__(self, data_dir: Path = DATA_DIR, settings=None):
        s = settings or get_settings()
        self.data_dir = data_dir
        url = (
            f"mysql+pymysql://{s.mysql_user}:{s.mysql_password}"
            f"@{s.mysql_host}:{s.mysql_port}/{s.mysql_db}?charset=utf8mb4"
        )
        self.engine = create_engine(url, pool_pre_ping=True)
        self._fallback = JsonStorage(data_dir)  # 连不上/出错时兜底，保证服务可用
        try:
            with self.engine.connect():
                pass  # 探活失败会抛异常，直接回退
        except Exception as e:  # OperationalError 等连接类错误
            logger.warning("MySQL 连接失败，自动回退 JSON 数据源：%s", e)
            self._json_mode = True
            return
        self._json_mode = False
        self._init_schema()

    # ---- 初始化：建表 + 空间索引 + 灌样例 ----

    def _init_schema(self):
        SQLModel.metadata.create_all(self.engine)
        with self.engine.begin() as conn:
            # 空间索引不能由 create_all 生成，需手动 DDL（幂等：先删后建）
            for table in ("inspection_points", "events"):
                conn.execute(text(f"ALTER TABLE {table} DROP INDEX idx_geom"))
                conn.execute(text(
                    f"CREATE SPATIAL INDEX idx_geom ON {table}(geom)"
                ))
        if self._tables_empty():
            self._seed_from_json()

    def _tables_empty(self) -> bool:
        with self.engine.connect() as conn:
            total = sum(
                conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar_one()
                for t in ("trajectories", "track_points", "events",
                          "inspection_points", "map_features")
            )
        return total == 0

    def _seed_from_json(self):
        """把 data/ 样例灌进 MySQL，使两套数据源返回一致（幂等：空表才灌）。"""

        def _point_wkt(lng: float, lat: float) -> str:
            return f"POINT({lng} {lat})"

        with self.engine.begin() as conn:
            # 巡检点 + 地图原稿
            geojson = JsonStorage(data_dir=self.data_dir).map_geojson()
            for f in geojson["features"]:
                props, geom = f["properties"], f["geometry"]
                if props.get("kind") == "inspection_point":
                    lng, lat = geom["coordinates"]
                    conn.execute(text(
                        "INSERT INTO inspection_points (id, name, priority, lng, lat, geom) "
                        "VALUES (:id, :name, :priority, :lng, :lat, ST_GeomFromText(:wkt, 4326))"
                    ), {"id": props["id"], "name": props["name"],
                        "priority": props.get("priority", 1),
                        "lng": lng, "lat": lat, "wkt": _point_wkt(lng, lat)})
            conn.execute(text(
                "INSERT INTO map_features (doc_id, payload) VALUES ('campus', :payload)"
            ), {"payload": json.dumps(geojson, ensure_ascii=False)})

            # 事件
            for e in self._fallback.events():
                conn.execute(text(
                    "INSERT INTO events (event_id, task_id, timestamp, lng, lat, type, "
                    "confidence, image_path, status, geom) VALUES "
                    "(:event_id, :task_id, :timestamp, :lng, :lat, :type, :confidence, "
                    ":image_path, :status, ST_GeomFromText(:wkt, 4326))"
                ), {**e, "wkt": _point_wkt(e["lng"], e["lat"])})

            # 轨迹
            for path in (self.data_dir / "tracks").glob("*.json"):
                traj = _load_json(path)
                conn.execute(text(
                    "INSERT INTO trajectories (task_id, agent_id, status) "
                    "VALUES (:task_id, :agent_id, :status)"
                ), {"task_id": traj["task_id"], "agent_id": traj["agent_id"],
                    "status": traj.get("status", "finished")})
                for seq, p in enumerate(traj["track"], start=1):
                    conn.execute(text(
                        "INSERT INTO track_points (task_id, seq, timestamp, lng, lat, "
                        "alt, speed, heading) VALUES "
                        "(:task_id, :seq, :timestamp, :lng, :lat, :alt, :speed, :heading)"
                    ), {"task_id": traj["task_id"], "seq": seq,
                        "timestamp": p["timestamp"], "lng": p["lng"], "lat": p["lat"],
                        "alt": p.get("alt", 0.0), "speed": p.get("speed", 0.0),
                        "heading": p.get("heading", 0.0)})

    # ---- 与 JsonStorage 一致的接口 ----

    def map_geojson(self) -> dict:
        if self._json_mode:
            return self._fallback.map_geojson()
        with self.engine.connect() as conn:
            row = conn.execute(text(
                "SELECT payload FROM map_features WHERE doc_id = 'campus'"
            )).first()
        if row is None:
            raise LookupError("园区地图数据不存在")
        return json.loads(row[0])

    def trajectory(self, task_id: str) -> dict:
        if self._json_mode:
            return self._fallback.trajectory(task_id)
        with self.engine.connect() as conn:
            head = conn.execute(text(
                "SELECT task_id, agent_id, status FROM trajectories WHERE task_id = :tid"
            ), {"tid": task_id}).first()
            if head is None:
                raise LookupError(f"轨迹 {task_id} 不存在")
            rows = conn.execute(text(
                "SELECT timestamp, lng, lat, alt, speed, heading FROM track_points "
                "WHERE task_id = :tid ORDER BY seq"
            ), {"tid": task_id}).all()
        return {
            "task_id": head[0],
            "agent_id": head[1],
            "status": head[2],
            "track": [dict(r._mapping) for r in rows],
        }

    def events(self, type: str | None = None, status: str | None = None,
               task_id: str | None = None) -> list[dict]:
        if self._json_mode:
            return self._fallback.events(type, status, task_id)
        sql = ("SELECT event_id, task_id, timestamp, lng, lat, type, confidence, "
               "image_path, status FROM events")
        conds, params = [], {}
        if type:
            conds.append("type = :type")
            params["type"] = type
        if status:
            conds.append("status = :status")
            params["status"] = status
        if task_id:
            conds.append("task_id = :task_id")
            params["task_id"] = task_id
        if conds:
            sql += " WHERE " + " AND ".join(conds)
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql + " ORDER BY timestamp"), params).all()
        return [dict(r._mapping) for r in rows]

    # ---- MySQL 专属：附近查询（README 强调的时空查询落点）----

    def nearby_events(self, lng: float, lat: float, radius_m: float) -> list[dict]:
        """返回距 (lng, lat) 球面距离 <= radius_m 的事件，按距离升序。

        ST_DistanceSphere 是 MySQL 自带的球面距离（米），配合 geom 上的
        空间索引做「附近 N 米有什么」这类查询。
        """
        if self._json_mode:
            raise LookupError("附近查询需要 MySQL 数据源（JsonStorage 不支持）")
        sql = text(
            "SELECT * FROM ("
            "  SELECT event_id, task_id, timestamp, lng, lat, type, confidence, "
            "         image_path, status, "
            "         ST_DistanceSphere(geom, ST_GeomFromText(:pt, 4326)) AS dist_m "
            "  FROM events) t "
            "WHERE dist_m <= :radius ORDER BY dist_m"
        )
        with self.engine.connect() as conn:
            rows = conn.execute(sql, {
                "pt": f"POINT({lng} {lat})", "radius": radius_m,
            }).all()
        return [dict(r._mapping) for r in rows]


# ===========================================================================
# 数据源入口
# ===========================================================================

_storage = None


def get_storage():
    """全局唯一数据源：.env 没开 MySQL（或连不上）就是 JsonStorage。"""
    global _storage
    if _storage is None:
        s = get_settings()
        _storage = MysqlStorage(settings=s) if s.mysql_enabled else JsonStorage()
        logger.info("数据源：%s", type(_storage).__name__)
    return _storage