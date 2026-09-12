/* report.js —— /report 巡检报告页（window.Report）
 *
 * 接口（后端冻结契约，前端只读不改）：
 *   SSE GET /api/report/stream?task_id=  → progress(30/60/80) → report → done 共 5 帧
 *   GET     /api/report?task_id=         → 同 report 帧同构的 JSON（兜底路径用）
 * 经 Flask 同源反代；SSE 那条走 app.py 里单独的流式透传路由（通用反代是全量缓冲的）。
 *
 * 形态与 spatiotemporal.js 一致：独立文件 + 自守卫（只在存在 #rp-run 的页面生效）+ 不挂别人的 Promise 链。
 * 与 /robots /nodes 那种「载入即拉一次」的详情页不同：报告生成是**用户触发**的动作，
 * 页面载入时不自动跑，也不做「失败就整页重载」的自愈（那会把用户刚点的这一次结果冲掉）。
 *
 * 页面上如实标注、代码里也如实处理的三件事：
 *   1. 后端这版生成器没有 sleep/await，5 帧实测 26ms 内全部到达 —— 进度条就是「瞬间点亮」，
 *      本文件不做人为延时去演出逐步推进。
 *   2. 结论是 services.py::_rule_conclusion 规则拼接的，不是大模型生成。
 *   3. EventSource 的 onerror 拿不到任何 message（4xx/5xx 回的是 JSON 信封，不是 SSE 帧），
 *      所以错误文案一律来自兜底那次 GET 的 message，不在 onerror 里现编。
 */
(function () {
  'use strict';

  var root = document.getElementById('rp-run');
  if (!root) return;                 // 非 /report 页：直接退出
  var A = window.API;
  if (!A) return;

  var btn = root;
  var msg = document.getElementById('rp-msg');
  var stepsBox = document.getElementById('rp-steps');
  var tableBody = document.getElementById('rp-table');
  var barsBox = document.getElementById('rp-type-bars');
  var degrade = document.getElementById('degrade-box');
  var degradeMsg = document.getElementById('degrade-msg');

  var es = null;                     // 当前 EventSource；同一时刻只允许一条
  var done = false;                  // 本次生成是否已收到 done 帧
  var degraded = false;              // 本次是否走了「SSE 失败 → GET 兜底」路径

  /* ---------- 降级条 ---------- */

  function fail(text) {
    if (degrade) {
      degradeMsg.textContent = text || '数据加载失败';
      degrade.style.display = 'flex';
    }
    heal();
  }
  function ok() { if (degrade) degrade.style.display = 'none'; }

  // 自愈：失败后每 4s 探一次 /api/health，恢复即恢复按钮。
  // ★ 这里**不** location.reload()：本页数据由按钮触发，重载会把用户刚点的这次结果冲掉。
  var healing = false;
  function heal() {
    if (healing) return;
    healing = true;
    setTimeout(function probe() {
      fetch((window.API && window.API.API_BASE) + '/api/health', { cache: 'no-store' })
        .then(function (r) {
          if (!r.ok) { setTimeout(probe, 4000); return; }
          healing = false;
          ok();
          setBusy(false);
          setMsg('后端已恢复，可重新生成');
        })
        .catch(function () { setTimeout(probe, 4000); });
    }, 4000);
  }

  /* ---------- 小工具（同 nodes.html 的 el/dot 写法） ---------- */

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function dot(color, px) {
    var d = document.createElement('span');
    d.style.cssText = 'display:inline-block;width:' + (px || 8) + 'px;height:' + (px || 8) +
      'px;border-radius:50%;background:' + color + ';flex:none';
    return d;
  }
  function chip(cls, color, text) {
    var c = el('span', cls);
    if (color) c.appendChild(dot(color, 8));
    c.appendChild(document.createTextNode(text));
    return c;
  }
  function wipe(node) { if (node) while (node.firstChild) node.removeChild(node.firstChild); }
  function setMsg(t) { if (msg) msg.textContent = t; }
  function setBusy(b) { btn.disabled = !!b; }

  // 'YYYY-MM-DD HH:mm:ss' → 'MM-DD HH:mm:ss'（表格用，去掉年份）
  function dtShort(iso) {
    var s = A.fmtDateTime(iso);
    return s.length > 5 ? s.slice(5) : s;
  }

  /* ---------- 进度条 ---------- */

  // 只画后端真正发过来的 progress 帧：不做「预置三步、到点变灰/变亮」那种演出，
  // 也不会出现后端没说的步骤。pct 就是帧里带的 pct（当前 30/60/80）。
  function resetSteps(placeholderText) {
    wipe(stepsBox);
    if (!stepsBox) return;
    var li = el('li',
      'inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground',
      placeholderText);
    li.setAttribute('data-rp-placeholder', '1');   // lightStep 靠它认出「这是占位，该撤了」
    stepsBox.appendChild(li);
  }

  function lightStep(pct, text) {
    if (!stepsBox) return;
    // 占位（或空态）先撤掉
    var placeholder = stepsBox.querySelector('[data-rp-placeholder]');
    if (placeholder) stepsBox.removeChild(placeholder);
    else if (!stepsBox.querySelector('[data-rp-step]')) wipe(stepsBox);

    var li = el('li',
      'inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary');
    li.setAttribute('data-rp-step', String(pct));
    // 色点跟随文字色（currentColor），不另写死十六进制 —— 换主题时不会和文字色脱节
    var d = document.createElement('span');
    d.style.cssText = 'display:inline-block;width:8px;height:8px;border-radius:50%;background:currentColor;flex:none';
    li.appendChild(d);
    li.appendChild(document.createTextNode(pct + '% ' + text));
    stepsBox.appendChild(li);
  }

  /* ---------- 渲染（SSE 的 report 帧与 GET /api/report 的 data 同构，共用这一份） ---------- */

  function render(data) {
    var s = (data && data.summary) || {};
    var events = (data && data.events) || [];

    A.setText('rp-task', s.task_id || '--');
    A.setText('rp-agent', s.agent_id || '--');
    A.setText('rp-start', s.started_at ? A.fmtDateTime(s.started_at) : '--');
    A.setText('rp-end', s.finished_at ? A.fmtDateTime(s.finished_at) : '--');
    A.setText('rp-pts', s.track_points == null ? '--' : String(s.track_points));
    A.setText('rp-count', s.events_count == null ? '--' : String(s.events_count));
    A.setText('rp-at', data && data.generated_at ? A.fmtDateTime(data.generated_at) : '--');
    A.setText('rp-conclusion', (data && data.conclusion) || '（后端未返回结论文本）');
    A.setText('rp-ev-count', '共 ' + events.length + ' 起');

    // 类型分布：顺序用 TYPE_ORDER（颜色跟随实体、不随排名/数量变化），零值类型也画出来
    var agg = A.aggEvents(events);
    wipe(barsBox);
    var zero = [];
    agg.types.forEach(function (ty) {
      if (!ty.count) { zero.push(ty.cn); return; }
      var item = el('div', '');
      var head = el('div', 'flex items-center justify-between gap-3 text-sm');
      var left = el('div', 'flex items-center gap-2 text-muted-foreground');
      left.appendChild(dot(ty.dot, 8));
      left.appendChild(el('span', '', ty.cn));
      head.appendChild(left);
      head.appendChild(el('span', 'tabular-nums font-medium', String(ty.count)));
      item.appendChild(head);

      var wrap = el('div', 'mt-1.5 h-2 overflow-hidden rounded-full bg-secondary');
      var bar = el('div', 'h-full rounded-full');
      bar.style.background = ty.dot;
      bar.style.width = agg.total > 0 ? Math.max(2, ty.count / agg.total * 100) + '%' : '0%';
      wrap.appendChild(bar);
      item.appendChild(wrap);
      barsBox.appendChild(item);
    });
    if (!agg.total) barsBox.appendChild(el('p', 'text-sm text-muted-foreground', '本次任务无异常事件'));
    // 零值类型不画空条（0 长度的条读不出是 0 还是没画），改成一句文字说明
    if (zero.length) {
      barsBox.appendChild(el('p', 'text-xs text-muted-foreground',
        zero.join('、') + ' 本次未检出（不代表无风险）'));
    }

    // 事件表
    wipe(tableBody);
    if (!events.length) {
      var trEmpty = el('tr');
      var tdEmpty = el('td', 'py-6 text-muted-foreground', '本次任务无异常事件');
      tdEmpty.colSpan = 6;
      trEmpty.appendChild(tdEmpty);
      tableBody.appendChild(trEmpty);
    } else {
      events.slice().sort(function (a, b) {
        return Date.parse(a.timestamp) - Date.parse(b.timestamp);
      }).forEach(function (e) {
        var tr = el('tr', 'border-b border-border');
        tr.appendChild(el('td', 'py-2.5 pr-4 font-mono text-xs', e.event_id));
        tr.appendChild(el('td', 'py-2.5 pr-4 tabular-nums font-mono text-xs', dtShort(e.timestamp)));
        var tdType = el('td', 'py-2.5 pr-4');
        tdType.appendChild(chip('inline-flex items-center gap-1.5 rounded-full bg-secondary px-2.5 py-0.5 text-xs text-muted-foreground',
          A.typeDot(e.type), A.typeCN(e.type)));
        tr.appendChild(tdType);
        tr.appendChild(el('td', 'py-2.5 pr-4 tabular-nums', Math.round((e.confidence || 0) * 100) + '%'));
        tr.appendChild(el('td', 'py-2.5 pr-4 tabular-nums font-mono text-xs',
          A.fmtNum(e.lng, 3) + ', ' + A.fmtNum(e.lat, 3)));
        var tdSt = el('td', 'py-2.5');
        tdSt.appendChild(chip('inline-flex items-center gap-1.5 rounded-full bg-secondary px-2.5 py-0.5 text-xs text-muted-foreground',
          A.statusDot(e.status), A.statusCN(e.status)));
        tr.appendChild(tdSt);
        tableBody.appendChild(tr);
      });
    }
  }

  /* ---------- 兜底路径：SSE 拿不到就用一次性 GET ---------- */

  function fallback(reason) {
    setMsg('流式进度不可用，改用一次性获取…');
    A.apiGet('/api/report?task_id=' + encodeURIComponent(A.TASK)).then(function (r) {
      setBusy(false);
      if (!r.ok) {
        // 连 GET 也失败：这时才有可读的 message 可映射成人话
        resetSteps('未取到进度');
        fail(A.errText(r, '报告获取失败'));
        setMsg('生成失败');
        return;
      }
      ok();
      degraded = true;
      render(r.data || {});
      resetSteps('已降级为一次性获取，无进度');
      setMsg(reason + '，已用 /api/report 一次性取回');
    });
  }

  /* ---------- 主路径：SSE ---------- */

  function generate() {
    // ★ 连点会开出多条 EventSource：先把上一条关掉。同 Leaflet「already initialized」那类问题。
    if (es) { es.close(); es = null; }
    done = false;
    degraded = false;

    setBusy(true);
    setMsg('正在生成…');
    ok();
    resetSteps('等待后端进度…');
    wipe(tableBody);
    var trWait = el('tr');
    var tdWait = el('td', 'py-6 text-muted-foreground', '正在生成…');
    tdWait.colSpan = 6;
    trWait.appendChild(tdWait);
    tableBody.appendChild(trWait);

    var url = '/api/report/stream?task_id=' + encodeURIComponent(A.TASK);
    try {
      es = new EventSource(url);
    } catch (e) {
      es = null;
      fallback('浏览器不支持 EventSource');
      return;
    }

    // 具名事件必须 addEventListener —— onmessage 只收不带 event: 的帧
    es.addEventListener('progress', function (ev) {
      var d = {};
      try { d = JSON.parse(ev.data); } catch (e) { return; }
      var pct = (d.pct == null) ? '--' : d.pct;
      // 帧里没带的步骤就不编：直接显示后端给的文字
      lightStep(pct, d.step || '');
      setMsg('生成中…');
    });

    es.addEventListener('report', function (ev) {
      var d = null;
      try { d = JSON.parse(ev.data); } catch (e) { d = null; }
      if (!d) { return; }              // 交给 onerror/兜底去报错，不在这里编文案
      render(d);
      setBusy(false);
      setMsg('报告已生成');
    });

    es.addEventListener('done', function () {
      // ★ 必须 close：后端发完就断连且没给 retry:，不关的话浏览器会自动重连、
      //   把整份报告重跑一遍（表现为莫名其妙的二次请求 + 数字跳动）。
      done = true;
      if (es) { es.close(); es = null; }
      setBusy(false);
      setMsg(degraded ? '报告已生成（一次性获取）' : '报告生成完毕');
    });

    // onerror 里**拿不到 message**（404/502 回的是 JSON 信封，不是 SSE 帧），
    // 所以这里只负责「判断要不要兜底」，文案交给 fallback 那次 GET。
    es.onerror = function () {
      if (done) return;                // 已正常收尾，忽略（有些浏览器在 close 后仍会补一次）
      var closed = (es && es.readyState === EventSource.CLOSED);
      if (es) { es.close(); es = null; }
      // CONNECTING = 浏览器自己在重连，CLOSED = 上游 4xx/断流不会重连；两种都走兜底
      fallback(closed ? '流式连接被后端拒绝' : '流式连接中断');
    };
  }

  /* ---------- 载入时探一次后端 ---------- */

  // 本页载入不拉数据，所以「后端离线」不会自己暴露出来 —— 不探的话，用户要点一下按钮
  // 才知道后端没起，而表格还一直写着「尚未生成」。这里探一次 /api/health：
  // 离线就地把降级条亮出来 + 按钮置灰 + 表格给明确空态，别让页面装作一切正常。
  function probeOnLoad() {
    fetch((window.API && window.API.API_BASE) + '/api/health', { cache: 'no-store' })
      .then(function (r) {
        if (r.ok) { ok(); setBusy(false); return; }
        markOffline();
      })
      .catch(function () { markOffline(); });
  }
  function markOffline() {
    // 按钮**不置灰**：与 /capabilities 的 dt-run 同一策略 —— 保持可点，点了才能拿到
    // 后端给的确切失败原因（报告不存在「算出个假结果」的风险，故无需像 pl-run 那样禁用）。
    setMsg('后端离线，可稍后重试');
    resetSteps('后端离线');
    wipe(tableBody);
    var tr = el('tr');
    var td = el('td', 'py-6 text-muted-foreground', '后端离线，尚未取到报告');
    td.colSpan = 6;
    tr.appendChild(td);
    tableBody.appendChild(tr);
    fail('后端服务不可用（请确认 127.0.0.1:8000 已启动）');
  }

  /* ---------- 绑定 ---------- */

  btn.addEventListener('click', generate);

  // 页面离开时主动断开，别把上游生成器挂着（app.py 生成器的 finally 是第二道保险）
  window.addEventListener('beforeunload', function () { if (es) { es.close(); es = null; } });

  resetSteps('尚未生成');
  probeOnLoad();

  window.Report = { refresh: generate };
})();
