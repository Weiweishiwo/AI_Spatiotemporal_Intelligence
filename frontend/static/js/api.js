/* api.js —— 官网首页与数据详情页共享的后端数据工具（window.API）
 *
 * 配套后端 FastAPI http://127.0.0.1:8000（7 个冻结契约接口，只读使用，不改后端）：
 *   /api/map  /api/trajectory?task_id=  /api/events  /api/report?task_id=  /api/plan  /api/detect  /api/health
 * 信封约定：{code:0, message, data}，code===0 才算成功（失败 data 为 null）。
 * 映射表/配色与 pure_html_map/index.html（/map 页）同源，保证跨页视觉一致。
 *
 * 页面内联脚本在 content 块内，本文件由 base.html 在 <head> 同步加载 → 内联脚本
 * 执行时 window.API 已就绪。本文件不做任何 DOM 副作用（initHomeStats 例外，且自守卫）。
 */
(function () {
  'use strict';

  var API_BASE = '';   // 同源：经 Flask /api/* 反代到 127.0.0.1:8000（避免浏览器跨端口拦截/CORS）
  var TASK = 'task-001';             // demo 唯一任务（后端 tracks/ 目录仅有此任务）
  var COVER_RADIUS_M = 100;          // 判定"轨迹覆盖巡检点"的最近距离阈值

  /* ---------- 基础请求 ---------- */

  // 归一化信封：{ok, code, message, data, netError?, httpStatus?}
  function apiGet(path) {
    return fetch(API_BASE + path, { cache: 'no-store' })
      .then(function (resp) {
        return resp.text().then(function (txt) {
          var r = { ok: false, httpStatus: resp.status, message: 'HTTP ' + resp.status };
          try {
            var j = JSON.parse(txt);
            r.code = j.code;
            r.message = j.message;
            r.data = j.data;
            r.ok = resp.ok && j.code === 0;
          } catch (e) {
            r.netError = true;
            r.message = '响应解析失败';
          }
          return r;
        });
      })
      .catch(function () {
        return { ok: false, netError: true, message: '无法连接后端服务（127.0.0.1:8000）' };
      });
  }

  /* ---------- 映射表（与 /map 页同源） ---------- */

  // 事件类型：固定展示顺序（demo 数据 fire=0，仍保留在枚举里）
  var TYPE_ORDER = ['equipment_abnormal', 'intrusion', 'smoke', 'no_helmet', 'fire'];
  var TYPE_CN = {
    smoke: '烟雾', fire: '明火', no_helmet: '未戴安全帽',
    intrusion: '闯入', equipment_abnormal: '设备异常'
  };
  var TYPE_DOT = {
    smoke: '#ea580c', fire: '#dc2626', no_helmet: '#7c3aed',
    intrusion: '#db2777', equipment_abnormal: '#2563eb'
  };

  var STATUS_ORDER = ['pending', 'confirmed', 'resolved', 'false_alarm'];
  var STATUS_CN = { pending: '待处理', confirmed: '已确认', resolved: '已处置', false_alarm: '误报' };
  var STATUS_DOT = { pending: '#f59e0b', confirmed: '#2563eb', resolved: '#16a34a', false_alarm: '#94a3b8' };
  var TASK_STATUS_CN = { running: '执行中', finished: '已完成' };

  var PRIORITY_CN = { 1: '一级重点', 2: '二级', 3: '三级' };
  var PRIORITY_DOT = { 1: '#d0342c', 2: '#f0a020', 3: '#2f7bd0' };

  function typeCN(t) { return TYPE_CN[t] || '未知'; }
  function typeDot(t) { return TYPE_DOT[t] || '#64748b'; }
  function statusCN(s) { return STATUS_CN[s] || s || '未知'; }
  function statusDot(s) { return STATUS_DOT[s] || '#64748b'; }
  function prioCN(p) { return PRIORITY_CN[p] || '未知'; }
  function prioDot(p) { return PRIORITY_DOT[p] || '#64748b'; }

  /* ---------- 通用工具 ---------- */

  function pad2(n) { return n < 10 ? '0' + n : '' + n; }

  // ISO8601(UTC Z) → 本地 'YYYY-MM-DD HH:mm:ss'
  function fmtDateTime(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return iso || '';
    return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()) + ' ' +
      pad2(d.getHours()) + ':' + pad2(d.getMinutes()) + ':' + pad2(d.getSeconds());
  }

  // 秒数 → 'X 分 YY 秒'
  function fmtDur(sec) {
    sec = Math.max(0, Math.round(sec));
    return Math.floor(sec / 60) + ' 分 ' + pad2(sec % 60) + ' 秒';
  }

  // WGS84 球面距离（米）
  function haversineM(lng1, lat1, lng2, lat2) {
    var R = 6371000;
    var toRad = Math.PI / 180;
    var dLat = (lat2 - lat1) * toRad;
    var dLng = (lng2 - lng1) * toRad;
    var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * toRad) * Math.cos(lat2 * toRad) *
      Math.sin(dLng / 2) * Math.sin(dLng / 2);
    return 2 * R * Math.asin(Math.sqrt(a));
  }

  // 就地写 textContent（元素不存在时 no-op，多页复用安全）
  function setText(id, txt) {
    var el = document.getElementById(id);
    if (el) el.textContent = txt;
  }

  // 数字保留 n 位小数的字符串（去多余 0），如 100→'100'、99.84→'99.8'
  function fmtNum(x, digits) {
    var v = Number(x);
    if (isNaN(v)) return '--';
    var s = v.toFixed(digits == null ? 1 : digits);
    return s.replace(/\.0+$/, '').replace(/(\.\d*?)0+$/, '$1');
  }

  /* ---------- 聚合统计（前端基于冻结接口原始数据现算） ---------- */

  // 轨迹统计。里程 = Σ 段首速度 × 该段时长（坐标点是合成粗采样，
  // 相邻点空间跳变是假距离，不能用 haversine 连点）。
  function trackStats(track) {
    var n = track ? track.length : 0;
    var st = { count: n, durationS: 0, distM: 0, avgMs: 0, maxMs: 0, altM: 0 };
    if (n < 1) return st;
    var altSum = 0;
    for (var i = 0; i < n; i++) {
      var p = track[i];
      altSum += (p.alt || 0);
      st.maxMs = Math.max(st.maxMs, p.speed || 0);
    }
    st.altM = fmtNum(altSum / n, 1);
    var t0 = Date.parse(track[0].timestamp), tn = Date.parse(track[n - 1].timestamp);
    if (!isNaN(t0) && !isNaN(tn) && n > 1) {
      st.durationS = Math.round((tn - t0) / 1000);
      for (var j = 0; j < n - 1; j++) {
        var dt = (Date.parse(track[j + 1].timestamp) - Date.parse(track[j].timestamp)) / 1000;
        if (!isNaN(dt) && dt > 0) st.distM += (track[j].speed || 0) * dt;
      }
    }
    st.distM = Math.round(st.distM);
    st.avgMs = st.durationS > 0 ? fmtNum(st.distM / st.durationS, 1) : 0;
    return st;
  }

  // 覆盖率：某巡检点被覆盖 ⟺ 它到轨迹任一点的最小球面距离 ≤ r。
  // 返回 {total, covered, pct, rows:[{id,name,priority,lng,lat,minM,visitAt,covered}]}
  function coverage(points, track, r) {
    r = r == null ? COVER_RADIUS_M : r;
    var rows = [];
    var coveredCount = 0;
    for (var i = 0; i < points.length; i++) {
      var pt = points[i];
      var minM = Infinity, visitAt = '';
      for (var j = 0; j < (track || []).length; j++) {
        var q = track[j];
        var d = haversineM(pt.lng, pt.lat, q.lng, q.lat);
        if (d < minM) { minM = d; visitAt = q.timestamp; }
      }
      var covered = minM <= r;
      if (covered) coveredCount++;
      rows.push({
        id: pt.id, name: pt.name, priority: pt.priority,
        lng: pt.lng, lat: pt.lat,
        minM: Math.round(minM), visitAt: visitAt, covered: covered
      });
    }
    var total = points.length;
    return {
      total: total,
      covered: coveredCount,
      pct: total > 0 ? fmtNum(coveredCount / total * 100, 1) : 0,
      rows: rows
    };
  }

  // 事件分组：types/statuses 都按固定枚举序返回 {type,cn,dot,count}（含 0 项）
  function aggEvents(events) {
    events = events || [];
    var types = TYPE_ORDER.map(function (t) {
      return { type: t, cn: typeCN(t), dot: typeDot(t), count: 0 };
    });
    var statuses = STATUS_ORDER.map(function (s) {
      return { status: s, cn: statusCN(s), dot: statusDot(s), count: 0 };
    });
    for (var i = 0; i < events.length; i++) {
      var e = events[i];
      for (var a = 0; a < types.length; a++) if (types[a].type === e.type) types[a].count++;
      for (var b = 0; b < statuses.length; b++) if (statuses[b].status === e.status) statuses[b].count++;
    }
    return { total: events.length, types: types, statuses: statuses };
  }

  // 每个巡检点 r 米内的邻近事件：{点id: {total, items:[]}}
  function nearCounts(points, events, r) {
    r = r == null ? COVER_RADIUS_M : r;
    var out = {};
    for (var i = 0; i < points.length; i++) {
      var pt = points[i];
      var items = [];
      for (var j = 0; j < (events || []).length; j++) {
        var e = events[j];
        if (haversineM(pt.lng, pt.lat, e.lng, e.lat) <= r) items.push(e);
      }
      out[pt.id] = { total: items.length, items: items };
    }
    return out;
  }

  /* ---------- GeoJSON 与 Leaflet 地图 ---------- */

  // 拆解园区 GeoJSON（坐标 [lng,lat] → Leaflet [lat,lng]）
  function inspectionFeatures(geojson) {
    var out = { buildings: [], roads: [], points: [] };
    var feats = (geojson && geojson.features) || [];
    for (var i = 0; i < feats.length; i++) {
      var f = feats[i];
      var kind = f.properties && f.properties.kind;
      var g = f.geometry;
      if (kind === 'building' && g.type === 'Polygon') {
        var rings = [];
        for (var rI = 0; rI < g.coordinates.length; rI++) {
          var ring = [];
          for (var pI = 0; pI < g.coordinates[rI].length; pI++) {
            ring.push([g.coordinates[rI][pI][1], g.coordinates[rI][pI][0]]);
          }
          rings.push(ring);
        }
        out.buildings.push({ name: f.properties.name, latlngs: rings });
      } else if (kind === 'road' && g.type === 'LineString') {
        var line = [];
        for (var lI = 0; lI < g.coordinates.length; lI++) line.push([g.coordinates[lI][1], g.coordinates[lI][0]]);
        out.roads.push({ name: f.properties.name, latlngs: line });
      } else if (kind === 'inspection_point' && g.type === 'Point') {
        out.points.push({
          id: f.properties.id, name: f.properties.name,
          priority: f.properties.priority,
          lng: g.coordinates[0], lat: g.coordinates[1]
        });
      }
    }
    return out;
  }

  // 统一小地图：底图 + 巡检点 + 轨迹（线+起终点）+ 事件纯色圆点。
  // Leaflet 未加载（离线/CDN 挂）→ 容器内写降级文案并返回 null，不抛错。
  // opts: {features, track, events, fit}
  function buildMap(elId, opts) {
    var el = document.getElementById(elId);
    if (!el) return null;
    if (typeof L === 'undefined') {
      el.textContent = '地图组件加载失败（离线环境），下方表格数据不受影响';
      return null;
    }
    opts = opts || {};
    var map = L.map(el, { scrollWheelZoom: false });
    L.tileLayer('https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
      maxZoom: 19, attribution: '高德地图'
    }).addTo(map);

    var all = [];
    var f = opts.features;

    if (f) {
      for (var b = 0; b < f.buildings.length; b++) {
        L.polygon(f.buildings[b].latlngs, {
          color: '#64748b', weight: 2, fillColor: '#cbd5e1', fillOpacity: 0.7
        }).bindPopup(f.buildings[b].name || '建筑').addTo(map);
        f.buildings[b].latlngs.forEach(function (ring) { all = all.concat(ring); });
      }
      for (var r2 = 0; r2 < f.roads.length; r2++) {
        L.polyline(f.roads[r2].latlngs, { color: '#f59e0b', weight: 4 }).addTo(map);
        all = all.concat(f.roads[r2].latlngs);
      }
      for (var p = 0; p < f.points.length; p++) {
        var ip = f.points[p];
        var mk = L.circleMarker([ip.lat, ip.lng], {
          radius: 8, color: '#ffffff', weight: 2, fillColor: prioDot(ip.priority), fillOpacity: 0.95
        }).bindPopup((ip.id || '') + ' · ' + (ip.name || '') + ' · ' + prioCN(ip.priority))
          .addTo(map);
        mk._ipId = ip.id;
        all.push([ip.lat, ip.lng]);
      }
    }

    var tr = opts.track;
    if (tr && tr.length) {
      var line = tr.map(function (q) { return [q.lat, q.lng]; });
      L.polyline(line, { color: '#2563eb', weight: 4, opacity: 0.85 }).addTo(map);
      L.circleMarker(line[0], { radius: 7, color: '#ffffff', weight: 2, fillColor: '#16a34a', fillOpacity: 1 })
        .bindPopup('起点 · ' + (tr[0].timestamp || '')).addTo(map);
      L.circleMarker(line[line.length - 1], { radius: 7, color: '#ffffff', weight: 2, fillColor: '#dc2626', fillOpacity: 1 })
        .bindPopup('终点 · ' + (tr[tr.length - 1].timestamp || '')).addTo(map);
      all = all.concat(line);
    }

    var evs = opts.events;
    if (evs) {
      for (var e = 0; e < evs.length; e++) {
        var ev = evs[e];
        L.circleMarker([ev.lat, ev.lng], {
          radius: 10, color: '#ffffff', weight: 2, fillColor: typeDot(ev.type), fillOpacity: 0.9
        }).bindPopup(
          (ev.event_id || '') + ' · ' + typeCN(ev.type) + ' · 置信度 ' +
          fmtNum((ev.confidence || 0) * 100, 0) + '% · ' + statusCN(ev.status) + ' · ' +
          fmtDateTime(ev.timestamp)
        ).addTo(map);
        all.push([ev.lat, ev.lng]);
      }
    }

    if (opts.fit !== false && all.length) {
      try { map.fitBounds(L.latLngBounds(all), { padding: [40, 40] }); }
      catch (err) { /* 单点时 fitBounds 可抛错，忽略 */ }
    }
    return map;
  }

  /* ---------- 首页三卡实时统计（自守卫，仅首页生效） ---------- */

  var homeFilled = false;

  // 后端 ok → 就地写真实值 1 / 5 / 100；失败 → 保持 '--' 并给卡片挂离线 title
  function initHomeStats() {
    if (!document.getElementById('stat-robots-val')) return Promise.resolve(false);
    return Promise.all([
      apiGet('/api/trajectory?task_id=' + encodeURIComponent(TASK)),
      apiGet('/api/map')
    ]).then(function (results) {
      var tr = results[0], mp = results[1];
      if (!(tr.ok && tr.data && tr.data.track && mp.ok && mp.data)) {
        if (!homeFilled) {
          var links = document.querySelectorAll('a[href="/robots"], a[href="/nodes"], a[href="/coverage"]');
          for (var i = 0; i < links.length; i++) {
            links[i].setAttribute('title', '后端服务不可用，实时统计暂缺');
          }
        }
        return false;
      }
      var points = inspectionFeatures(mp.data).points;
      var cov = coverage(points, tr.data.track);
      setText('stat-robots-val', '1');                      // 最近任务唯一在册智能体（口径见 /robots）
      setText('stat-nodes-val', String(points.length));      // 巡检点（感知节点）数
      setText('stat-coverage-val', String(cov.pct));        // 覆盖百分比
      homeFilled = true;
      return true;
    }).catch(function () { return false; });
  }

  window.API = {
    API_BASE: API_BASE, TASK: TASK, COVER_RADIUS_M: COVER_RADIUS_M,
    // 常量映射表一并导出（页面里可能直接用 A.xxx 查中文/色点，漏导出会 TypeError）
    TYPE_ORDER: TYPE_ORDER, STATUS_ORDER: STATUS_ORDER,
    TYPE_CN: TYPE_CN, TYPE_DOT: TYPE_DOT,
    STATUS_CN: STATUS_CN, STATUS_DOT: STATUS_DOT,
    TASK_STATUS_CN: TASK_STATUS_CN,
    PRIORITY_CN: PRIORITY_CN, PRIORITY_DOT: PRIORITY_DOT,
    apiGet: apiGet,
    typeCN: typeCN, typeDot: typeDot, statusCN: statusCN, statusDot: statusDot,
    prioCN: prioCN, prioDot: prioDot,
    fmtDateTime: fmtDateTime, fmtDur: fmtDur, fmtNum: fmtNum,
    haversineM: haversineM, setText: setText,
    trackStats: trackStats, coverage: coverage, aggEvents: aggEvents,
    nearCounts: nearCounts, inspectionFeatures: inspectionFeatures,
    buildMap: buildMap, initHomeStats: initHomeStats
  };
})();
