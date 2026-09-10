/* spatiotemporal.js —— 首页「时空智能 · 全域数据总览」综合仪表盘
 *
 * 只读消费后端 7 个冻结接口中的 3 个，不改后端、不新增接口：
 *   /api/trajectory?task_id=  → 轨迹采样点 → 里程 / 时长 / 速度 / 平均高度
 *   /api/map                  → 园区 GeoJSON → 楼栋 / 道路 / 巡检点
 *   /api/events               → 异常事件   → 类型分布 / 状态构成 / 点位邻近
 * 聚合一律复用 api.js 的 trackStats / coverage / aggEvents / nearCounts，
 * 口径与首页三卡、/map 页、各 Hub 页完全一致（不另起一套算法）。
 *
 * 后端不可用时：整块降级为明确的离线提示，**绝不编造数字**（沿用首页三卡的做法）。
 *
 * 绘制约定（对齐 dataviz 规范）：
 *   - 条形 ≤24px 厚、数据端 4px 圆角、基线端方角、统一从一条基线生长；
 *   - 基线 1px 实线、贴近底色，不画网格——因为每根条都已直标数值；
 *   - 文字一律用文本色令牌，绝不穿数据色；身份由每行的标签承担；
 *   - 命中区铺满整行（≥24px），不必瞄准细条；<title>/tooltip 只做增强，
 *     每个值都在轴上直标且整块可切「表格视图」，不被 tooltip 独占。
 *
 * 色板说明：TYPE_DOT / STATUS_DOT / PRIORITY_DOT 三套色均与 /map、各 Hub 页同源，
 * 未在本文件重新配色（跨页一致是硬要求）。三套均过 validate_palette.js 的 --pairs all：
 * TYPE_DOT 正常 ΔE 15.4 / 红绿色盲 11.1、PRIORITY_DOT 24.1 / 20.2，全 PASS。
 * STATUS_DOT 的琥珀↔绿在红绿色盲下 ΔE 7.0，落在 6–8 底线带——按规范该带内必须有
 * 次级编码；这里的次级编码就是**数据端直标数值**，不依赖颜色即可读出全部信息。
 * 同理它的琥珀/灰对比度低于 3:1，也由直标兜底。
 *
 * 为什么不用堆叠柱：demo 数据里 8 条事件状态全是 pending，堆叠柱会退化成一整根
 * 实心色块，不承载任何信息（anti-pattern：one-bar bar chart，数字本身就是图）。
 * 改用同形的横向条形 + 一句文字结论——单一状态和混合状态两种分布下都读得通。
 */
(function () {
  'use strict';

  var A = window.API;
  var ROOT = 'stDash';
  if (!A) return;

  /* ---------- 文本/线条令牌色（取自 style.css 的 HSL 变量转 hex，页面无深色模式） ---------- */
  var INK = '#1d2935';          // foreground        hsl(210 30% 16%)
  var INK_MUTED = '#637383';    // muted-foreground  hsl(210 14% 45%)
  var HAIRLINE = '#dae0e7';     // border            hsl(214 20% 88%)
  var PRIMARY = '#1e5e8f';      // primary           hsl(206 65% 34%)
  var TRACK = 'hsl(206 65% 34% / 0.12)';  // 同色相更浅一档，做进度槽

  /* ---------- 小工具 ---------- */

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function pctOf(n, total) {
    return total > 0 ? A.fmtNum(n / total * 100, 1) : '0';
  }
  // 里程：>=1km 用 km（2 位小数），否则用 m
  function fmtDist(m) {
    return m >= 1000 ? A.fmtNum(m / 1000, 2) + ' km' : m + ' m';
  }

  /* ---------- SVG 图元 ---------- */

  // 基线端方角、数据端 4px 圆角的横条
  function roundEndBar(x, y, w, h, r) {
    r = Math.min(r, h / 2, w);
    return 'M' + x + ' ' + y +
      'H' + (x + w - r) +
      'a' + r + ' ' + r + ' 0 0 1 ' + r + ' ' + r +
      'V' + (y + h - r) +
      'a' + r + ' ' + r + ' 0 0 1 ' + (-r) + ' ' + r +
      'H' + x + 'Z';
  }

  // 横向条形图。每根条直标数值 → 不画网格、不画坐标轴，只留一条零基线。
  // rows: [{label, value, color, tip}]
  function barChart(rows) {
    var W = 560, ROW = 40, BAR = 20, PAD_L = 104, PAD_R = 68, PAD_T = 4, PAD_B = 4;
    var H = PAD_T + PAD_B + rows.length * ROW;
    var plotW = W - PAD_L - PAD_R;
    var max = 1;
    rows.forEach(function (r) { if (r.value > max) max = r.value; });

    var o = ['<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;height:auto" role="img" ' +
      'aria-label="' + esc(rows.map(function (r) { return r.label + ' ' + r.value; }).join('，')) + '">'];
    // 零基线（1px 实线，贴近底色）
    o.push('<line x1="' + PAD_L + '" y1="' + PAD_T + '" x2="' + PAD_L + '" y2="' + (H - PAD_B) +
      '" stroke="' + HAIRLINE + '" stroke-width="1"/>');

    rows.forEach(function (r, i) {
      var top = PAD_T + i * ROW;
      var y = top + (ROW - BAR) / 2;
      var w = r.value > 0 ? Math.max(2, r.value / max * plotW) : 0;
      var cy = y + BAR / 2 + 5;

      o.push('<text x="' + (PAD_L - 12) + '" y="' + cy + '" text-anchor="end" font-size="13" ' +
        'fill="' + INK_MUTED + '">' + esc(r.label) + '</text>');
      if (w > 0) o.push('<path d="' + roundEndBar(PAD_L, y, w, BAR, 4) + '" fill="' + r.color + '"/>');
      o.push('<text x="' + (PAD_L + w + 10) + '" y="' + cy + '" font-size="13" font-weight="600" ' +
        'fill="' + INK + '">' + r.value + '</text>');
      // 命中区铺满整行（≥24px），不必瞄准细条
      o.push('<rect class="st-hit" x="0" y="' + top + '" width="' + W + '" height="' + ROW +
        '" fill="transparent" data-tip="' + esc(r.tip) + '"/>');
    });
    o.push('</svg>');
    return o.join('');
  }

  // 进度计（覆盖率）。槽是同一色相的浅一档，状态在整条上都能读出来。
  function meter(frac) {
    var W = 560, H = 12, R = 6;
    var w = Math.max(0, Math.min(1, frac / 100)) * W;
    return '<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;height:auto" role="img" ' +
      'aria-label="覆盖率 ' + frac + '%">' +
      '<rect x="0" y="0" width="' + W + '" height="' + H + '" rx="' + R + '" fill="' + TRACK + '"/>' +
      (w > 0 ? '<rect x="0" y="0" width="' + w.toFixed(1) + '" height="' + H + '" rx="' + R +
        '" fill="' + PRIMARY + '"/>' : '') +
      '</svg>';
  }

  // 面板外壳
  function panel(title, sub, body) {
    return '<div class="tech-card rounded-2xl p-5 md:p-6">' +
      '<h3 class="text-base font-semibold">' + esc(title) + '</h3>' +
      (sub ? '<p class="mt-1 text-xs text-muted-foreground">' + esc(sub) + '</p>' : '') +
      '<div class="mt-5">' + body + '</div></div>';
  }

  // 数字芯片
  function tile(label, value, unit) {
    return '<div class="tech-card rounded-xl p-3 md:p-4">' +
      '<p class="text-xs text-muted-foreground">' + esc(label) + '</p>' +
      '<p class="mt-1 text-xl font-semibold tabular-nums md:text-2xl" style="color:' + PRIMARY + '">' +
      esc(value) + '<span class="ml-0.5 text-xs font-normal text-muted-foreground">' + esc(unit) + '</span></p>' +
      '</div>';
  }

  function skeleton(msg) {
    return '<div class="tech-card rounded-2xl p-10 text-center text-sm text-muted-foreground">' + esc(msg) + '</div>';
  }

  /* ---------- 渲染 ---------- */

  var lastOk = false;

  function render(force) {
    var root = document.getElementById(ROOT);
    if (!root) return Promise.resolve(false);
    var charts = document.getElementById('stDashCharts');
    var tv = document.getElementById('stDashTable');
    var bar = document.getElementById('stDashBar');

    // 重取时保留上一次画面并降透明度，不闪骨架屏、不跳布局
    if (lastOk) root.classList.add('st-loading');

    return Promise.all([
      A.apiGet('/api/trajectory?task_id=' + encodeURIComponent(A.TASK)),
      A.apiGet('/api/map'),
      A.apiGet('/api/events')
    ]).then(function (r) {
      root.classList.remove('st-loading');
      var tr = r[0], mp = r[1], ev = r[2];

      if (!(tr.ok && mp.ok && ev.ok && tr.data && tr.data.track && mp.data)) {
        lastOk = false;
        if (bar) bar.innerHTML = offlineBar(r);
        if (charts) charts.innerHTML = skeleton('后端服务不可用，全域数据总览暂缺 —— 这里不显示占位数字');
        if (tv) tv.innerHTML = '';
        return false;
      }

      var track = tr.data.track;
      var features = A.inspectionFeatures(mp.data);
      var events = ev.data || [];
      draw(charts, tv, bar, track, features, events);
      lastOk = true;
      return true;
    }).catch(function () {
      root.classList.remove('st-loading');
      lastOk = false;
      if (charts) charts.innerHTML = skeleton('数据拉取异常，全域数据总览暂缺');
      return false;
    });
  }

  function offlineBar(r) {
    var msg = r.map(function (x, i) {
      return ['/api/trajectory', '/api/map', '/api/events'][i] + ' ' + (x.ok ? '✓' : '✗');
    }).join(' · ');
    return '<div class="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-xl border border-border bg-card px-4 py-3 text-xs text-muted-foreground">' +
      '<span class="font-medium text-foreground">数据源不可用</span><span>' + esc(msg) + '</span></div>';
  }

  function draw(charts, tv, bar, track, features, events) {
    var st = A.trackStats(track);
    var cov = A.coverage(features.points, track);
    var agg = A.aggEvents(events);
    var near = A.nearCounts(features.points, events);

    /* ---- 数据源条 ---- */
    if (bar) {
      bar.innerHTML = '<div class="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-border ' +
        'bg-card px-4 py-3 text-xs text-muted-foreground">' +
        '<span class="inline-flex items-center gap-1.5 font-medium text-foreground">' +
        '<span class="h-1.5 w-1.5 rounded-full" style="background:#10b981"></span>后端实时数据</span>' +
        '<span>数据源 /api/trajectory · /api/map · /api/events</span>' +
        '<span>任务 ' + esc(A.TASK) + '</span>' +
        '<span class="ml-auto">更新于 ' + esc(new Date().toLocaleTimeString('zh-CN', { hour12: false })) + '</span>' +
        '</div>';
    }

    /* ---- 轨迹概览 ---- */
    var tiles = [
      tile('轨迹采样点', st.count, '个'),
      tile('巡检里程', fmtDist(st.distM).split(' ')[0], fmtDist(st.distM).split(' ')[1]),
      tile('巡检时长', Math.round(st.durationS / 60), '分'),
      tile('平均速度', st.avgMs, 'm/s'),
      tile('峰值速度', A.fmtNum(st.maxMs, 1), 'm/s'),
      tile('平均高度', st.altM, 'm')
    ].join('');

    /* ---- 事件类型分布 ---- */
    var typeRows = agg.types.map(function (t) {
      return {
        label: t.cn, value: t.count, color: t.dot,
        tip: t.cn + '：' + t.count + ' 条 · 占 ' + pctOf(t.count, agg.total) + '%'
      };
    });

    /* ---- 事件状态分布 ---- */
    var statusRows = agg.statuses.map(function (s) {
      return {
        label: s.cn, value: s.count, color: s.dot,
        tip: s.cn + '：' + s.count + ' 条 · 占 ' + pctOf(s.count, agg.total) + '%'
      };
    });
    // 构成结论直接写成一句话。数据全落在单一状态时，堆叠柱会退化成"一根满条"
    // （不承载信息，属 anti-pattern），所以这里用同形的条形图 + 文字结论。
    var topSt = agg.statuses.reduce(function (a, b) { return b.count > a.count ? b : a; }, agg.statuses[0]);
    var statusNote = agg.total <= 0 ? '当前没有事件记录'
      : (topSt.count === agg.total
        ? '全部 ' + agg.total + ' 条都停在「' + topSt.cn + '」，尚无其他状态记录'
        : '占比最高的是「' + topSt.cn + '」' + topSt.count + ' 条（' + pctOf(topSt.count, agg.total) + '%）');

    /* ---- 巡检点优先级分布 ---- */
    var prioCount = { 1: 0, 2: 0, 3: 0 };
    features.points.forEach(function (p) { if (prioCount[p.priority] != null) prioCount[p.priority]++; });
    var prioRows = [1, 2, 3].map(function (p) {
      return {
        label: A.prioCN(p), value: prioCount[p], color: A.prioDot(p),
        tip: A.prioCN(p) + '：' + prioCount[p] + ' 个 · 占 ' + pctOf(prioCount[p], features.points.length) + '%'
      };
    });

    /* ---- 图表区 ---- */
    charts.innerHTML =
      '<div class="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">' + tiles + '</div>' +
      '<div class="mt-5 grid gap-5 lg:grid-cols-2">' +
      panel('异常事件类型分布', '共 ' + agg.total + ' 条事件，按 ' + A.TYPE_ORDER.length + ' 类枚举归集',
        barChart(typeRows)) +
      panel('事件状态分布', statusNote, barChart(statusRows)) +
      '</div>' +
      '<div class="mt-5 grid gap-5 lg:grid-cols-2">' +
      panel('巡检点优先级分布', features.points.length + ' 个感知节点，按优先级归集', barChart(prioRows)) +
      panel('巡检覆盖率', cov.covered + ' / ' + cov.total + ' 个巡检点被轨迹覆盖（阈值 ' + A.COVER_RADIUS_M + ' m）',
        '<div class="flex items-baseline gap-2">' +
        '<span class="text-3xl font-semibold" style="color:' + PRIMARY + '">' + cov.pct + '</span>' +
        '<span class="text-sm text-muted-foreground">%</span></div>' +
        '<div class="mt-3">' + meter(Number(cov.pct)) + '</div>' +
        '<div class="mt-5 grid grid-cols-3 gap-3 text-center">' +
        '<div><p class="text-xs text-muted-foreground">园区建筑</p><p class="mt-0.5 text-lg font-semibold" style="color:' + INK + '">' + features.buildings.length + '</p></div>' +
        '<div><p class="text-xs text-muted-foreground">园区道路</p><p class="mt-0.5 text-lg font-semibold" style="color:' + INK + '">' + features.roads.length + '</p></div>' +
        '<div><p class="text-xs text-muted-foreground">感知节点</p><p class="mt-0.5 text-lg font-semibold" style="color:' + INK + '">' + features.points.length + '</p></div>' +
        '</div>'
      ) +
      '</div>';

    /* ---- 表格视图（每张图的无障碍等价物，值不被 tooltip 独占） ---- */
    var rows = cov.rows.map(function (p) {
      var n = near[p.id] || { total: 0 };
      return '<tr class="border-t border-border">' +
        '<td class="py-2 pr-3 tabular-nums text-muted-foreground">' + esc(p.id) + '</td>' +
        '<td class="py-2 pr-3">' + esc(p.name) + '</td>' +
        '<td class="py-2 pr-3">' + esc(A.prioCN(p.priority)) + '</td>' +
        '<td class="py-2 pr-3 tabular-nums">' + p.minM + ' m</td>' +
        '<td class="py-2 pr-3">' + (p.covered ? '已覆盖' : '未覆盖') + '</td>' +
        '<td class="py-2 tabular-nums">' + n.total + '</td></tr>';
    }).join('');

    tv.innerHTML =
      '<div class="tech-card rounded-2xl p-5 md:p-6">' +
      '<h3 class="text-base font-semibold">全域指标明细表</h3>' +
      '<p class="mt-1 text-xs text-muted-foreground">与上方各图同源同口径；轨迹与事件的逐条明细见 ' +
      '<a href="/map" class="text-primary hover:underline">地图可视化</a> 页</p>' +

      '<h4 class="mt-5 text-sm font-semibold">轨迹</h4>' +
      '<table class="mt-2 w-full text-sm"><tbody>' +
      [['采样点数', st.count + ' 个'], ['巡检里程', fmtDist(st.distM)], ['巡检时长', A.fmtDur(st.durationS)],
       ['平均速度', A.fmtNum(st.avgMs, 1) + ' m/s'], ['峰值速度', A.fmtNum(st.maxMs, 1) + ' m/s'],
       ['平均高度', st.altM + ' m']].map(function (r) {
        return '<tr class="border-t border-border"><td class="py-2 pr-3 text-muted-foreground">' + esc(r[0]) +
          '</td><td class="py-2 tabular-nums">' + esc(r[1]) + '</td></tr>';
      }).join('') + '</tbody></table>' +

      '<h4 class="mt-5 text-sm font-semibold">事件 · 按类型</h4>' +
      '<table class="mt-2 w-full text-sm"><tbody>' + agg.types.map(function (t) {
        return '<tr class="border-t border-border"><td class="py-2 pr-3 text-muted-foreground">' + esc(t.cn) +
          '</td><td class="py-2 tabular-nums">' + t.count + ' 条</td><td class="py-2 text-muted-foreground">' +
          pctOf(t.count, agg.total) + '%</td></tr>';
      }).join('') + '</tbody></table>' +

      '<h4 class="mt-5 text-sm font-semibold">事件 · 按状态</h4>' +
      '<table class="mt-2 w-full text-sm"><tbody>' + agg.statuses.map(function (s) {
        return '<tr class="border-t border-border"><td class="py-2 pr-3 text-muted-foreground">' + esc(s.cn) +
          '</td><td class="py-2 tabular-nums">' + s.count + ' 条</td><td class="py-2 text-muted-foreground">' +
          pctOf(s.count, agg.total) + '%</td></tr>';
      }).join('') + '</tbody></table>' +

      '<h4 class="mt-5 text-sm font-semibold">巡检点</h4>' +
      '<table class="mt-2 w-full text-sm"><thead><tr class="text-xs text-muted-foreground">' +
      '<th class="py-1 pr-3 text-left font-medium">编号</th><th class="py-1 pr-3 text-left font-medium">名称</th>' +
      '<th class="py-1 pr-3 text-left font-medium">优先级</th><th class="py-1 pr-3 text-left font-medium">最近轨迹距离</th>' +
      '<th class="py-1 pr-3 text-left font-medium">覆盖</th><th class="py-1 text-left font-medium">邻近事件</th>' +
      '</tr></thead><tbody>' + rows + '</tbody></table>' +
      '</div>';
  }

  /* ---------- 交互：共享 tooltip + 表格视图切换 ---------- */

  function initTip() {
    var root = document.getElementById(ROOT);
    if (!root || root.dataset.tipBound) return;
    root.dataset.tipBound = '1';
    var tip = document.createElement('div');
    tip.className = 'st-tip';
    tip.style.display = 'none';
    root.appendChild(tip);

    root.addEventListener('mouseover', function (e) {
      var t = e.target.closest ? e.target.closest('.st-hit,.st-bar-hit') : null;
      if (!t || !t.dataset.tip) return;
      tip.textContent = t.dataset.tip;
      tip.style.display = 'block';
    });
    root.addEventListener('mousemove', function (e) {
      if (tip.style.display !== 'block') return;
      var b = root.getBoundingClientRect();
      tip.style.left = (e.clientX - b.left + 14) + 'px';
      tip.style.top = (e.clientY - b.top + 14) + 'px';
    });
    root.addEventListener('mouseout', function (e) {
      var t = e.target.closest ? e.target.closest('.st-hit,.st-bar-hit') : null;
      if (t) tip.style.display = 'none';
    });
  }

  function initToggle() {
    var btn = document.getElementById('stDashViewBtn');
    var charts = document.getElementById('stDashCharts');
    var tv = document.getElementById('stDashTable');
    if (!btn || !charts || !tv || btn.dataset.bound) return;
    btn.dataset.bound = '1';
    btn.addEventListener('click', function () {
      var toTable = charts.style.display !== 'none';
      charts.style.display = toTable ? 'none' : '';
      tv.style.display = toTable ? '' : 'none';
      btn.textContent = toTable ? '图表视图' : '表格视图';
      btn.setAttribute('aria-pressed', toTable ? 'true' : 'false');
    });
  }

  function boot() {
    var root = document.getElementById(ROOT);
    if (!root) return;
    initTip();
    initToggle();
    render();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  // 暴露刷新入口，供首页定时器复用
  window.Spatiotemporal = { refresh: render };

  /* 图表的 tooltip 走 data-tip 属性（见 initTip），柱子本身另带 <title> 兜底 */
})();
