// ═══════════════════════════════════════════════════════════════════
// KuroLog — Debug Overlay
// Aktif: ?kurodev=1 veya KuroWatch logosuna 3x hızlı tıklayınca
// Click (mavi), Fetch (cyan), Error (kırmızı), Nav (mor) logları
// ═══════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  const STORAGE_KEY = 'kuro_dev_logs';
  const MAX_EVENTS = 100;
  const COLOR = {
    click: '#3b82f6',
    fetch: '#00d4ff',
    error: '#ff4444',
    nav:   '#a855f7',
    info:  '#9090b0'
  };

  let active = false;
  let panel = null;
  let logoClicks = [];

  // Etkinlik koşulu
  const url = new URL(location.href);
  if (url.searchParams.get('kurodev') === '1') active = true;

  function loadStored() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
    catch { return []; }
  }

  function saveEvent(ev) {
    const arr = loadStored();
    arr.push(ev);
    if (arr.length > MAX_EVENTS) arr.splice(0, arr.length - MAX_EVENTS);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(arr)); } catch {}
  }

  function createPanel() {
    if (panel) return panel;
    panel = document.createElement('div');
    panel.id = 'kurolog-panel';
    panel.style.cssText = `
      position:fixed; bottom:16px; right:16px; z-index:99999;
      width:300px; height:400px;
      background:rgba(10,11,37,0.92); backdrop-filter:blur(12px);
      border:1px solid rgba(0,212,255,0.4); border-radius:12px;
      box-shadow:0 0 20px rgba(0,212,255,0.2);
      font-family:ui-monospace,monospace; font-size:11px;
      color:#e1e0ff; display:flex; flex-direction:column;
      overflow:hidden;
    `;
    panel.innerHTML = `
      <div style="padding:8px 12px; background:rgba(0,212,255,0.1); border-bottom:1px solid rgba(0,212,255,0.3); display:flex; align-items:center; justify-content:space-between; cursor:move;">
        <span style="color:#00d4ff; font-weight:700;">KURO LOG</span>
        <div>
          <button id="kurolog-clear" style="background:none; border:1px solid #3c494e; color:#9090b0; padding:2px 6px; border-radius:4px; cursor:pointer; margin-right:4px; font-size:10px;">Temizle</button>
          <button id="kurolog-close" style="background:none; border:none; color:#ff4444; cursor:pointer; font-size:14px; padding:0 4px;">×</button>
        </div>
      </div>
      <div id="kurolog-list" style="flex:1; overflow-y:auto; padding:6px 8px; line-height:1.4;"></div>
    `;
    document.body.appendChild(panel);

    panel.querySelector('#kurolog-close').addEventListener('click', () => {
      panel.remove(); panel = null; active = false;
    });
    panel.querySelector('#kurolog-clear').addEventListener('click', () => {
      try { localStorage.removeItem(STORAGE_KEY); } catch {}
      const list = panel.querySelector('#kurolog-list');
      if (list) list.innerHTML = '';
    });

    // Mevcut log'ları göster
    const stored = loadStored();
    stored.forEach(renderEvent);
    return panel;
  }

  function renderEvent(ev) {
    if (!panel) return;
    const list = panel.querySelector('#kurolog-list');
    if (!list) return;
    const row = document.createElement('div');
    const color = COLOR[ev.type] || COLOR.info;
    const time = new Date(ev.ts).toLocaleTimeString('tr-TR');
    row.style.cssText = 'margin-bottom:4px; padding:3px 6px; border-left:2px solid ' + color + '; background:rgba(255,255,255,0.02); border-radius:0 4px 4px 0; word-break:break-all;';
    row.innerHTML = `
      <div style="color:#9090b0; font-size:9px;">${time} · <span style="color:${color}; font-weight:700;">${ev.type.toUpperCase()}</span></div>
      <div style="color:#e1e0ff;">${escapeHtml(ev.msg)}</div>
    `;
    list.appendChild(row);
    list.scrollTop = list.scrollHeight;
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function log(type, msg) {
    const ev = { type, msg: String(msg), ts: Date.now() };
    saveEvent(ev);
    if (active) {
      if (!panel) createPanel();
      renderEvent(ev);
    }
  }

  // ── Logo 3x tıklama: aktifleştirme ──
  document.addEventListener('click', function(e) {
    const txt = e.target.textContent || '';
    if (txt.trim() === 'KuroWatch') {
      const now = Date.now();
      logoClicks = logoClicks.filter(t => now - t < 1500);
      logoClicks.push(now);
      if (logoClicks.length >= 3) {
        active = true; createPanel(); logoClicks = [];
      }
    }
  }, true);

  // ── Click tracker ──
  document.addEventListener('click', function(e) {
    const t = e.target;
    let desc = t.tagName.toLowerCase();
    if (t.id) desc += '#' + t.id;
    if (t.dataset.nav) desc += ' [nav=' + t.dataset.nav + ']';
    if (t.dataset.modalOpen) desc += ' [modal=' + t.dataset.modalOpen + ']';
    const txt = (t.textContent || '').trim().slice(0, 30);
    if (txt) desc += ' "' + txt + '"';
    log('click', desc);
  });

  // ── Fetch tracker ──
  const origFetch = window.fetch;
  window.fetch = function(input, init) {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    const method = (init && init.method) || 'GET';
    log('fetch', method + ' ' + url);
    return origFetch.apply(this, arguments)
      .then(r => {
        log('fetch', '← ' + r.status + ' ' + url);
        return r;
      })
      .catch(err => {
        log('error', 'fetch fail: ' + err.message);
        throw err;
      });
  };

  // ── Error tracker ──
  window.addEventListener('error', function(e) {
    log('error', (e.message || 'unknown') + ' @ ' + (e.filename || '') + ':' + (e.lineno || 0));
  });
  window.addEventListener('unhandledrejection', function(e) {
    log('error', 'unhandled: ' + (e.reason && e.reason.message ? e.reason.message : e.reason));
  });

  // ── Expose API ──
  window.kuroLog = {
    log: (msg) => log('info', msg),
    nav: (msg) => log('nav', msg),
    error: (msg) => log('error', msg),
    show: () => { active = true; createPanel(); },
    hide: () => { if (panel) { panel.remove(); panel = null; } active = false; },
    clear: () => { try { localStorage.removeItem(STORAGE_KEY); } catch {} },
    dump: () => loadStored()
  };

  if (active) {
    document.addEventListener('DOMContentLoaded', createPanel);
  }
})();
