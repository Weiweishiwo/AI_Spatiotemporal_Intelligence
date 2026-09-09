/* ===========================================================================
 * 登录态 / 后端健康状态（auth 集成，与后端 /api/auth/* 配套）
 *
 * 页面标记约定（元素缺失即 no-op，天然兼容任何继承 base.html 的页面）：
 *   .js-auth-guest      未登录时显示的一组（原样保留布局类，JS 只切 display）
 *   .js-auth-user       已登录时显示的一组（HTML 里初态 style="display:none"）
 *   .js-auth-name       用户名文字槽
 *   [data-auth-logout]  退出按钮（document 级事件委托，动态元素也生效）
 *   .js-online          状态点容器（含 .auth-dot + .js-online-text），
 *                       存在该标记才启动 15s 健康轮询
 *   #login-submit       登录页表单 → 已有有效会话时自动弹回 /map
 *
 * 显隐一律切 style.display（不用 Tailwind hidden 类：CDN 运行时类顺序不可靠）。
 *
 * 会话规则：
 *   读：sessionStorage 优先，其次 localStorage（勾了「记住」）
 *   写：勾「记住」→ localStorage，否则 sessionStorage（关标签即失效）
 *   清：两处一起清（登出 / 后端 401）
 *   网络错误（TypeError）≠ 401 —— 后端连不上绝不清本地会话；
 *   只有 HTTP 401 + code 40101（登录已过期）才清，并立即重绘为未登录。
 *   storage 事件跨标签页同步登出/登录。
 * ========================================================================= */
(function () {
  'use strict';

  var API_BASE = '';   // 同源：经 Flask /api/* 反代到 127.0.0.1:8000（避免浏览器跨端口拦截/CORS）
  var TOKEN_KEY = 'inspection_token';
  var USER_KEY = 'inspection_user';

  var SESSION_401 = 40101;
  var HEALTH_MS = 15000;

  /* ---------- 本地会话读写 ---------- */

  function getToken() {
    return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY) || null;
  }

  function getCachedUser() {
    var raw = sessionStorage.getItem(USER_KEY) || localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try { return JSON.parse(raw); } catch (e) { return null; }
  }

  function saveSession(token, user, remember) {
    clearSession(); // 先清，避免两个 storage 各留一半
    var store = remember ? localStorage : sessionStorage;
    store.setItem(TOKEN_KEY, token);
    if (user) store.setItem(USER_KEY, JSON.stringify(user));
    renderAuthState();
  }

  function clearSession() {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  /* ---------- 后端调用（统一信封解析） ---------- */

  function parseResponse(payload) {
    // 尝试按 {code,message,data} 信封解析；失败当后端异常处理
    try {
      var obj = typeof payload === 'string' ? JSON.parse(payload) : payload;
      return { ok: obj.code === 0, code: obj.code, message: obj.message, data: obj.data };
    } catch (e) {
      return { ok: false, netError: true, message: '后端返回了无法解析的内容' };
    }
  }

  function request(path, method, body, token) {
    var headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = 'Bearer ' + token;
    var init = { method: method || 'GET', headers: headers, cache: 'no-store' };
    // 只给真 body（GET/HEAD 带 body 会抛 "cannot have body"）；null 表示无 body
    if (body !== undefined && body !== null) init.body = JSON.stringify(body);
    return fetch(API_BASE + path, init).then(function (resp) {
      // 信封错误码全挂在响应体里，HTTP 状态只作参考（401 时 body 里是 40101）
      var payload = resp.text().then(function (t) { return t ? JSON.parse(t) : {}; }).catch(function () { return {}; });
      return payload.then(function (obj) {
        var r = parseResponse(obj);
        if (resp.status === 401 && r.code === SESSION_401) r.unauthorized = true;
        if (!r.ok && !r.netError) r.httpStatus = resp.status;
        return r;
      });
    });
  }

  function apiLogin(account, password) {
    return request('/api/auth/login', 'POST', { account: account, password: password });
  }

  function apiRegister(payload) {
    return request('/api/auth/register', 'POST', payload);
  }

  function apiLogout(token) {
    return request('/api/auth/logout', 'POST', null, token);
  }

  function apiMe(token) {
    return request('/api/auth/me', 'GET', null, token);
  }

  /* ---------- 页面渲染 ---------- */

  function setVisible(selector, visible) {
    document.querySelectorAll(selector).forEach(function (el) {
      el.style.display = visible ? '' : 'none';
    });
  }

  function renderName(user) {
    document.querySelectorAll('.js-auth-name').forEach(function (el) {
      el.textContent = user ? (user.username || '') : '';
    });
  }

  function renderAuthState() {
    // 有缓存 user（或仅 token）就算已登录；后端复核失败（401）才会再降到未登录
    var user = getCachedUser();
    var loggedIn = !!getToken();
    if (loggedIn && !user) user = { username: '' };
    setVisible('.js-auth-guest', !loggedIn);
    setVisible('.js-auth-user', loggedIn);
    renderName(user);
    return loggedIn;
  }

  /* ---------- 后端复核：401 才清会话 ---------- */

  function refreshAuth() {
    var token = getToken();
    if (!token) { renderAuthState(); return Promise.resolve(false); }

    renderAuthState(); // 先用缓存渲染，避免闪烁
    return apiMe(token).then(function (r) {
      if (r.ok) {
        // 刷新脱敏用户缓存（username 可能展示用）
        var store = sessionStorage.getItem(TOKEN_KEY) ? sessionStorage : localStorage;
        store.setItem(USER_KEY, JSON.stringify(r.data || {}));
        renderAuthState();
        return true;
      }
      if (r.unauthorized) {
        clearSession();
        renderAuthState(); // 401 = 登录过期 → 回到未登录
        return false;
      }
      // 网络错误 / 后端 5xx：保持当前显示，不清会话
      return true;
    }).catch(function () { return true; });
  }

  /* ---------- 登出（best-effort） ---------- */

  function doLogout() {
    var token = getToken();
    setVisible('.js-auth-user', false); // 先关 UI，请求结果不再回显
    apiLogout(token).finally(function () {
      clearSession();
      renderAuthState();
    });
  }

  /* ---------- 健康状态轮询（15s，防堆积） ---------- */

  function startHealth() {
    if (!document.querySelector('.js-online')) return; // 无状态点标记就不轮询
    var inFlight = false;
    var timer = null;

    // 桌面/移动端可能有多个状态点（.js-online 容器内含 .auth-dot + .js-online-text），全部更新
    function render(online) {
      document.querySelectorAll('.auth-dot').forEach(function (dot) {
        dot.classList.toggle('is-on', online);
        dot.classList.toggle('is-off', !online);
      });
      document.querySelectorAll('.js-online-text').forEach(function (text) {
        text.textContent = online ? '后端在线' : '后端离线';
      });
    }

    function poll() {
      if (inFlight) return;
      inFlight = true;
      fetch(API_BASE + '/api/health', { cache: 'no-store' })
        .then(function (resp) { render(resp.ok); })
        .catch(function () { render(false); }) // 后端没起来 → 离线
        .finally(function () { inFlight = false; });
    }

    poll(); // 立即探一次
    timer = setInterval(poll, HEALTH_MS);
    // 页面生命周期结束即停（旧浏览器不认 stop 就随页面销毁）
    if (document.visibilitychange !== undefined) {
      document.addEventListener('visibilitychange', function () {
        if (document.hidden && timer) { clearInterval(timer); timer = null; }
        else if (!document.hidden && !timer) { timer = setInterval(poll, HEALTH_MS); poll(); }
      });
    }
  }

  /* ---------- 对外 API（登录/注册页表单直接调用） ---------- */

  window.Auth = {
    apiLogin: apiLogin,
    apiRegister: apiRegister,
    apiLogout: apiLogout,
    apiMe: apiMe,
    saveSession: saveSession,
    clearSession: clearSession,
    getToken: getToken,
  };

  /* ---------- 事件：登出按钮（委托）+ 跨标签页同步 ---------- */

  document.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('[data-auth-logout]') : null;
    if (btn) { e.preventDefault(); doLogout(); }
  });

  window.addEventListener('storage', function (e) {
    if (e.key !== TOKEN_KEY && e.key !== USER_KEY) return;
    // 别的标签页登出/登录了 → 本页跟着切
    renderAuthState();
    if (!getToken()) { setVisible('.js-auth-user', false); setVisible('.js-auth-guest', true); }
  });

  /* ---------- 启动 ---------- */

  // 登录页特判：已有有效会话直接弹回地图页（不显示登录框）
  var isLoginPage = !!document.getElementById('login-submit');

  if (isLoginPage) {
    var token0 = getToken();
    if (token0) {
      apiMe(token0).then(function (r) {
        if (r.ok) { location.replace('/map'); }        // 会话还有效
        else if (r.unauthorized) { clearSession(); }    // 过期 → 留下正常登录
        // 网络错误：后端没起，登录页照常可用，不清 token
      }).catch(function () {});
    }
  } else {
    // 官网等普通页面：渲染登录态 + 复核
    refreshAuth();
    startHealth();
  }
})();
