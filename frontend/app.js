// ═══════════════════════════════════════════════════════════════════
// KuroWatch SPA — Ana JavaScript
// Navigasyon + Mock Data + API Layer + Render Fonksiyonları
// ═══════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  // ── Konfigürasyon ─────────────────────────────────────────────────
  const API_BASE = 'http://localhost:8099';
  let USE_MOCK = false; // backend :8099 bağlı

  // ── Mock Data ─────────────────────────────────────────────────────
  const MOCK_LIBRARY = [
    {
      id: 1, title: 'Magic Emperor', type: 'manhwa', status: 'watching',
      my_progress: 457, total_chapters: 600, my_score: 9.0, cover_url: null,
      country: 'KR', year: 2018, genres: ['Fantasy','Action']
    },
    {
      id: 2, title: 'Jujutsu Kaisen', type: 'manga', status: 'watching',
      my_progress: 270, total_chapters: 300, my_score: 8.5, cover_url: null,
      country: 'JP', year: 2018, genres: ['Action','Supernatural']
    },
    {
      id: 3, title: 'Spy×Family', type: 'anime', status: 'watching',
      my_progress: 2, total_chapters: 24, my_score: 8.0, cover_url: null,
      country: 'JP', year: 2022, genres: ['Comedy','Action']
    },
    {
      id: 4, title: 'Solo Leveling', type: 'manhwa', status: 'completed',
      my_progress: 200, total_chapters: 200, my_score: 9.5, cover_url: null,
      country: 'KR', year: 2018, genres: ['Action','Fantasy']
    },
    {
      id: 5, title: 'Elden Ring', type: 'game', status: 'on_hold',
      my_progress_pct: 60, my_score: null, cover_url: null,
      year: 2022, genres: ['RPG','Action']
    }
  ];

  const MOCK_UPDATES = [
    { id:1, content_id:1, content_title:'Magic Emperor',  episode_number:458, site_name:'MangaOkuTR',  detected_at:'2026-06-14T10:00:00', is_read:false },
    { id:2, content_id:2, content_title:'Jujutsu Kaisen', episode_number:271, site_name:'MangaTR',     detected_at:'2026-06-13T18:00:00', is_read:true  },
    { id:3, content_id:3, content_title:'Spy×Family',     episode_number:3,   site_name:'Crunchyroll', detected_at:'2026-06-12T22:00:00', is_read:false }
  ];

  // Tip rozetleri için renkler
  const TYPE_COLOR = {
    'anime':  { bg:'bg-[#00d4ff]/10', text:'text-[#00d4ff]', border:'border-[#00d4ff]/20', bar:'bg-[#00d4ff]', label:'Anime' },
    'manga':  { bg:'bg-[#ffd9a1]/10', text:'text-[#ffd9a1]', border:'border-[#ffd9a1]/20', bar:'bg-[#ffd9a1]', label:'Manga' },
    'manhwa': { bg:'bg-[#bbc5eb]/10', text:'text-[#bbc5eb]', border:'border-[#bbc5eb]/20', bar:'bg-[#bbc5eb]', label:'Manhwa' },
    'game':   { bg:'bg-[#ffb4ab]/10', text:'text-[#ffb4ab]', border:'border-[#ffb4ab]/20', bar:'bg-[#ffb4ab]', label:'Oyun' }
  };

  const STATUS_LABEL = {
    'watching': 'İzliyor',
    'completed': 'Tamamlandı',
    'on_hold': 'Beklemede',
    'plan_to_watch': 'Planlı',
    'dropped': 'Bırakıldı'
  };

  const TAG_COLORS = ['#00d4ff', '#bbc5eb', '#ffd9a1', '#ffb4ab', '#90e090', '#ff9a3c'];
  let _selectedTagColor = TAG_COLORS[0];
  let _tagPickerEl = null;

  // ── API Layer ─────────────────────────────────────────────────────
  function getMockData(path) {
    if (path === '/api/content')          return Promise.resolve(MOCK_LIBRARY);
    if (path === '/api/updates')          return Promise.resolve(MOCK_UPDATES);
    if (path.startsWith('/api/content/')) {
      const id = parseInt(path.split('/').pop(), 10);
      return Promise.resolve(MOCK_LIBRARY.find(c => c.id === id) || null);
    }
    return Promise.resolve(null);
  }

  async function apiGet(path) {
    if (USE_MOCK) return getMockData(path);
    const r = await fetch(API_BASE + path);
    if (!r.ok) throw new Error('GET ' + path + ' → ' + r.status);
    return r.json();
  }

  async function apiPost(path, body) {
    if (USE_MOCK) return { ok: true };
    const r = await fetch(API_BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!r.ok) throw new Error('POST ' + path + ' → ' + r.status);
    return r.json();
  }

  async function apiPatch(path, body) {
    if (USE_MOCK) return { ok: true };
    const r = await fetch(API_BASE + path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!r.ok) throw new Error('PATCH ' + path + ' → ' + r.status);
    return r.json();
  }

  async function apiDelete(path) {
    if (USE_MOCK) return { ok: true };
    const r = await fetch(API_BASE + path, { method: 'DELETE' });
    if (!r.ok && r.status !== 204) throw new Error('DELETE ' + path + ' → ' + r.status);
    return true;
  }

  // Expose
  window.kuroAPI = { get: apiGet, post: apiPost, patch: apiPatch, del: apiDelete, setMockMode: m => USE_MOCK = m };

  // ── Navigasyon Sistemi ────────────────────────────────────────────
  function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => {
      const isTarget = s.id === id;
      s.classList.toggle('active', isTarget);
      s.classList.toggle('hidden', !isTarget);
    });
    history.replaceState({ screen: id }, '', '#' + id);
    updateNavActive(id);

    // Ekran başına render
    if (id === 'screen-home')     renderHome();
    if (id === 'screen-updates')  renderUpdates();
    if (id === 'screen-stats')    renderStats();
    if (id === 'screen-archive')  renderArchive();
    if (id === 'screen-settings') renderSettings();
    if (id === 'screen-search') {
      setTimeout(() => {
        const inp = document.getElementById('search-discover-input');
        if (inp) { inp.focus(); if (inp.value) renderSearch(inp.value); }
      }, 100);
    }

    // Scroll to top
    window.scrollTo(0, 0);

    if (window.kuroLog) window.kuroLog.nav(id);
  }

  function updateNavActive(id) {
    // Sidebar nav
    document.querySelectorAll('#sidebar-nav .nav-item').forEach(item => {
      const isActive = item.dataset.nav === id;
      item.classList.toggle('active-nav', isActive);
    });
    // Bottom nav
    document.querySelectorAll('#bottom-nav .bottom-nav-item').forEach(item => {
      const isActive = item.dataset.nav === id;
      item.classList.toggle('active-nav', isActive);
    });
  }

  function openModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('hidden');
    el.classList.add('open');
    document.body.style.overflow = 'hidden';
    if (window.kuroLog) window.kuroLog.nav('modal-open:' + id);
  }

  function closeModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.add('hidden');
    el.classList.remove('open');
    document.body.style.overflow = '';
    if (window.kuroLog) window.kuroLog.nav('modal-close:' + id);
  }

  // Geri/ileri
  window.addEventListener('popstate', function(e) {
    const screen = (e.state && e.state.screen) || 'screen-home';
    showScreen(screen);
  });

  // Expose
  window.kuroNav = { show: showScreen, openModal: openModal, closeModal: closeModal };

  // ── Render: Home (Kütüphane Grid) ────────────────────────────────
  let homeFilter = { type: 'all', status: 'all', query: '' };

  async function renderHome() {
    const grid = document.getElementById('home-library-grid');
    if (!grid) return;

    let items;
    try {
      items = await apiGet('/api/content');
    } catch (err) {
      grid.innerHTML = '<div class="col-span-full text-center text-[#9090b0] py-12">Yüklenemedi: ' + err.message + '</div>';
      return;
    }

    // Filtrele
    const filtered = items.filter(it => {
      if (homeFilter.type !== 'all' && it.type !== homeFilter.type) return false;
      if (homeFilter.status !== 'all' && it.status !== homeFilter.status) return false;
      if (homeFilter.query && !it.title.toLowerCase().includes(homeFilter.query.toLowerCase())) return false;
      return true;
    });

    if (filtered.length === 0) {
      grid.innerHTML = '<div class="col-span-full text-center text-[#9090b0] py-12 flex flex-col items-center gap-2"><span class="material-symbols-outlined text-4xl">inbox</span><p>Eşleşen içerik yok</p></div>';
      return;
    }

    grid.innerHTML = filtered.map(it => {
      const tc = TYPE_COLOR[it.type] || TYPE_COLOR.anime;
      const total = it.total_chapters || 1;
      const pct = it.my_progress_pct != null
        ? it.my_progress_pct
        : Math.round((it.my_progress || 0) / total * 100);
      const score = it.my_score != null ? it.my_score.toFixed(1) : '—';
      const initials = it.title.split(' ').slice(0,2).map(w => w[0]).join('').toUpperCase();

      return `
        <div class="interactive-card relative group aspect-[2/3] rounded-card overflow-hidden bg-[#1c1d37] border border-white/5 hover:border-[#00d4ff]/50 hover:scale-[1.02] transition-all duration-300 cursor-pointer inner-glow" data-content-id="${it.id}">
          <div class="absolute inset-0 flex items-center justify-center text-[#31324d] text-5xl font-bold">${initials}</div>
          <div class="absolute inset-0 bg-gradient-to-t from-[#0d0d1a]/95 via-[#0d0d1a]/60 to-transparent"></div>
          <div class="absolute top-2 right-2 bg-[#00d4ff] text-[#003642] text-xs font-bold px-2 py-1 rounded-full shadow-lg">${score}</div>
          <div class="absolute bottom-0 w-full p-3 flex flex-col gap-1.5">
            <span class="text-[10px] font-bold ${tc.text} ${tc.bg} w-fit px-1.5 py-0.5 rounded uppercase border ${tc.border} leading-none">${tc.label}</span>
            <h3 class="text-[13px] font-bold text-[#e1e0ff] line-clamp-2 leading-tight">${escapeHtml(it.title)}</h3>
            <div class="w-full bg-white/10 h-1 rounded-full mt-1 overflow-hidden">
              <div class="${tc.bar} h-full shadow-[0_0_8px_rgba(0,212,255,0.6)]" style="width:${pct}%"></div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Kart tıklama → detay
    grid.querySelectorAll('[data-content-id]').forEach(card => {
      card.addEventListener('click', function() {
        const id = parseInt(this.dataset.contentId, 10);
        renderDetail(id);
        showScreen('screen-detail');
      });
    });
  }

  // ── Render: Detail ───────────────────────────────────────────────
  async function renderDetail(id) {
    let item;
    try { item = await apiGet('/api/content/' + id); }
    catch (err) { console.error('renderDetail', err); return; }
    if (!item) return;

    const tc = TYPE_COLOR[item.type] || TYPE_COLOR.anime;
    const total = item.total_chapters || 100;
    const cur = item.my_progress || 0;
    const pct = item.my_progress_pct != null ? item.my_progress_pct : Math.round(cur / total * 100);

    document.getElementById('detail-title').textContent = item.title;
    document.getElementById('detail-type-badge').textContent = (item.type || '').toUpperCase();
    document.getElementById('detail-status-badge').innerHTML = `<span class="material-symbols-outlined text-[14px]">play_circle</span> ${STATUS_LABEL[item.status] || item.status}`;
    document.getElementById('detail-progress-current').textContent = cur;
    document.getElementById('detail-progress-total').textContent = '/ ' + total;
    document.getElementById('detail-progress-pct').textContent = pct + '%';
    document.getElementById('detail-progress-bar').style.width = pct + '%';
    const slider = document.getElementById('detail-progress-slider');
    slider.max = total;
    slider.value = cur;
    document.getElementById('detail-slider-max').textContent = total;

    // Rating yıldızları (interaktif — tıklanınca PATCH ile kaydet)
    let currentScore = item.my_score || 0;
    const ratingEl = document.getElementById('detail-rating-container');
    function buildStars(highlighted) {
      ratingEl.innerHTML = '';
      for (let i = 1; i <= 10; i++) {
        const span = document.createElement('span');
        span.className = 'material-symbols-outlined cursor-pointer text-[28px] transition-colors ' + (i <= highlighted ? 'text-[#00d4ff]' : 'text-[#31324d]');
        span.style.fontVariationSettings = "'FILL' 1";
        span.textContent = 'star';
        span.dataset.star = i;
        span.addEventListener('mouseover', () => buildStars(i));
        span.addEventListener('mouseleave', () => buildStars(currentScore));
        span.addEventListener('click', async () => {
          currentScore = i;
          buildStars(i);
          try { await apiPatch('/api/content/' + id, { my_score: i }); }
          catch (e) { console.error('score save', e); }
        });
        ratingEl.appendChild(span);
      }
    }
    buildStars(currentScore);

    // Cover bg
    const coverEl = document.getElementById('detail-cover-bg');
    if (item.cover_url) {
      coverEl.style.backgroundImage = 'url(' + item.cover_url + ')';
      coverEl.style.backgroundColor = '';
    } else {
      coverEl.style.backgroundImage = '';
      coverEl.style.backgroundColor = '#16213e';
    }

    // Mark butonu
    document.getElementById('detail-mark-btn').onclick = function() {
      const next = (item.my_progress || 0) + 1;
      if (next > total) return;
      item.my_progress = next;
      apiPost('/api/content/' + id + '/progress', { progress: next });
      renderDetail(id);
    };

    // Slider değişimi
    slider.oninput = function() {
      const v = parseInt(this.value, 10);
      document.getElementById('detail-progress-current').textContent = v;
      const newPct = Math.round(v / total * 100);
      document.getElementById('detail-progress-pct').textContent = newPct + '%';
      document.getElementById('detail-progress-bar').style.width = newPct + '%';
    };
    slider.onchange = function() {
      const v = parseInt(this.value, 10);
      item.my_progress = v;
      apiPost('/api/content/' + id + '/progress', { progress: v });
    };

    renderDetailTags(id, item.tags || []);
  }

  // ── Render: Updates ──────────────────────────────────────────────
  async function renderUpdates() {
    const list = document.getElementById('updates-list');
    if (!list) return;

    let items;
    try { items = await apiGet('/api/updates'); }
    catch (err) {
      list.innerHTML = '<div class="text-center text-[#9090b0] py-12">Yüklenemedi: ' + err.message + '</div>';
      return;
    }

    if (items.length === 0) {
      list.innerHTML = '<div class="text-center text-[#9090b0] py-12 flex flex-col items-center gap-2"><span class="material-symbols-outlined text-4xl">notifications_off</span><p>Henüz güncelleme yok</p></div>';
      return;
    }

    list.innerHTML = items.map(u => {
      const initials = u.content_title.split(' ').slice(0,2).map(w => w[0]).join('').toUpperCase();
      const time = formatRelativeTime(u.detected_at);
      if (u.is_read) {
        return `
          <div class="group flex items-center gap-4 px-4 h-[56px] rounded-xl bg-[#1a1a2e]/60 border-l-[4px] border-transparent inner-glow cursor-pointer hover:bg-[#1a1a2e] transition-transform duration-200 opacity-70 hover:opacity-100 active:scale-[0.97]" data-content-id="${u.content_id}">
            <div class="w-10 h-10 rounded-md bg-[#16213e] flex-shrink-0 flex items-center justify-center text-white/40 font-bold text-sm grayscale-[50%]">${initials}</div>
            <div class="flex flex-col justify-center w-full min-w-0">
              <div class="flex justify-between items-center mb-0.5">
                <h3 class="text-[16px] font-bold text-white/70 group-hover:text-white transition-colors leading-tight truncate">${escapeHtml(u.content_title)}</h3>
                <span class="text-[10px] text-white/40 font-medium whitespace-nowrap ml-2">${time}</span>
              </div>
              <div class="flex items-center gap-2 text-white/50 text-[12px]">
                <span class="px-1.5 py-0.5 rounded bg-[#16213e]/50 text-white/60 text-[9px] uppercase font-bold tracking-wider">BÖL ${u.episode_number}</span>
                <span class="truncate">${escapeHtml(u.site_name)} üzerinde</span>
              </div>
            </div>
          </div>`;
      }
      return `
        <div class="group flex items-center gap-4 px-4 h-[56px] rounded-xl bg-[#1a1a2e] border-l-[4px] border-[#00d4ff] inner-glow cursor-pointer hover:bg-[#1a1a2e]/80 transition-transform duration-200 relative overflow-hidden active:scale-[0.97]" data-content-id="${u.content_id}">
          <div class="absolute inset-0 bg-gradient-to-r from-[#00d4ff]/5 to-transparent pointer-events-none"></div>
          <div class="w-10 h-10 rounded-md bg-[#16213e] flex-shrink-0 flex items-center justify-center text-[#00d4ff] font-bold text-sm">${initials}</div>
          <div class="flex flex-col justify-center w-full min-w-0">
            <div class="flex justify-between items-center mb-0.5">
              <h3 class="text-[16px] font-bold text-white group-hover:text-[#00d4ff] transition-colors leading-tight truncate">${escapeHtml(u.content_title)}</h3>
              <span class="text-[10px] text-[#00d4ff] font-medium whitespace-nowrap ml-2">${time}</span>
            </div>
            <div class="flex items-center gap-2 text-white/60 text-[12px]">
              <span class="px-1.5 py-0.5 rounded bg-[#16213e] text-[#00d4ff] text-[9px] uppercase font-bold tracking-wider">BÖL ${u.episode_number}</span>
              <span class="truncate">${escapeHtml(u.site_name)} üzerinde</span>
            </div>
          </div>
        </div>`;
    }).join('');

    list.querySelectorAll('[data-content-id]').forEach(card => {
      card.addEventListener('click', function() {
        const id = parseInt(this.dataset.contentId, 10);
        renderDetail(id);
        showScreen('screen-detail');
      });
    });
  }

  // ── Updates: Kontrol Et ──────────────────────────────────────────
  async function runCheckUpdates() {
    const btn = document.getElementById('updates-check-btn');
    if (!btn || btn.disabled) return;
    btn.disabled = true;
    btn.innerHTML = '<span class="material-symbols-outlined animate-spin text-sm">progress_activity</span> Kontrol ediliyor...';
    try {
      const res = await apiPost('/api/check-updates', {});
      const msg = res.new_updates > 0
        ? res.new_updates + ' yeni güncelleme bulundu!'
        : 'Yeni güncelleme yok';
      showToast(msg, res.new_updates > 0 ? 'success' : 'info');
      renderUpdates();
    } catch (err) {
      showToast('Hata: ' + err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<span class="material-symbols-outlined text-sm">refresh</span> Kontrol Et';
    }
  }

  // ── Toast ────────────────────────────────────────────────────────
  function showToast(msg, type) {
    const toast = document.getElementById('kw-toast');
    if (!toast) return;
    const colors = { success: '#90e090', error: '#ffb4ab', info: '#9090b0' };
    toast.style.borderColor = colors[type] || colors.info;
    toast.querySelector('.toast-msg').textContent = msg;
    toast.classList.remove('hidden', 'opacity-0');
    toast.classList.add('opacity-100');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function() {
      toast.classList.remove('opacity-100');
      toast.classList.add('opacity-0');
      setTimeout(function() { toast.classList.add('hidden'); }, 300);
    }, 3000);
  }

  // ── Render: Stats ────────────────────────────────────────────────
  async function renderStats() {
    let items;
    try { items = await apiGet('/api/content'); }
    catch (err) { console.error('renderStats', err); return; }

    document.getElementById('stats-library-count').textContent = items.length;

    const scored = items.filter(i => i.my_score != null);
    const avg = scored.length
      ? (scored.reduce((s, i) => s + i.my_score, 0) / scored.length).toFixed(1)
      : '—';
    document.getElementById('stats-avg-score').textContent = avg;
  }

  // ── Render: Archive ─────────────────────────────────────────────────
  async function renderArchive() {
    const list = document.getElementById('archive-list');
    const countEl = document.getElementById('archive-count');
    if (!list) return;

    let items;
    try { items = await apiGet('/api/content'); }
    catch (err) {
      list.innerHTML = '<div class="text-center text-[#9090b0] py-12">Yüklenemedi</div>';
      return;
    }

    const archived = items.filter(i => i.status === 'completed');
    if (countEl) countEl.textContent = archived.length + ' öğe';

    if (archived.length === 0) {
      list.innerHTML = '<div class="text-center text-[#9090b0] py-16 flex flex-col items-center gap-2"><span class="material-symbols-outlined text-4xl">archive</span><p>Arşiv boş</p><p class="text-sm">Tamamlanan içerikler burada görünür</p></div>';
      return;
    }

    list.innerHTML = archived.map(it => {
      const tc = TYPE_COLOR[it.type] || TYPE_COLOR.anime;
      const initials = it.title.split(' ').slice(0,2).map(w=>w[0]).join('').toUpperCase();
      const cover = it.cover_url
        ? `<img src="${it.cover_url}" class="w-full h-full object-cover" loading="lazy"/>`
        : `<span class="text-[#9090b0] font-bold text-sm">${escapeHtml(initials)}</span>`;
      const date = it.updated_at ? formatRelativeTime(it.updated_at) + ' tamamlandı' : 'Tamamlandı';
      return `
        <div class="flex items-center w-full h-[56px] bg-[#1a1a2e] rounded-lg px-2 gap-2 border border-[#31324d]/50 cursor-pointer hover:bg-[#1a1a2e]/80 transition-colors" data-content-id="${it.id}">
          <div class="w-[40px] h-[40px] rounded overflow-hidden flex-shrink-0 bg-[#31324d] flex items-center justify-center">${cover}</div>
          <div class="flex-1 min-w-0 flex flex-col justify-center gap-[2px]">
            <div class="flex items-center gap-1">
              <span class="font-bold text-[14px] text-[#e1e0ff] truncate">${escapeHtml(it.title)}</span>
              <span class="${tc.bg} ${tc.text} text-[10px] font-bold px-1 py-[2px] rounded uppercase tracking-wider">${tc.label}</span>
            </div>
            <span class="text-[12px] text-[#9090b0] truncate">${date}</span>
          </div>
          <button class="archive-restore-btn h-[32px] px-3 rounded border border-[#00d4ff] text-[#00d4ff] text-[12px] font-semibold hover:bg-[#00d4ff]/10 active:scale-[0.97] whitespace-nowrap flex-shrink-0" data-id="${it.id}">Geri Al</button>
        </div>`;
    }).join('');

    list.querySelectorAll('[data-content-id]').forEach(card => {
      card.addEventListener('click', function(e) {
        if (e.target.closest('.archive-restore-btn')) return;
        const cid = parseInt(this.dataset.contentId, 10);
        renderDetail(cid);
        showScreen('screen-detail');
      });
    });
    list.querySelectorAll('.archive-restore-btn').forEach(btn => {
      btn.addEventListener('click', async function(e) {
        e.stopPropagation();
        try {
          await apiPatch('/api/content/' + this.dataset.id, { status: 'watching' });
          renderArchive();
        } catch(err) { alert('Hata: ' + err.message); }
      });
    });
  }

  // ── Render: Settings ────────────────────────────────────────────────
  async function renderSettings() {
    let cfg;
    try { cfg = await apiGet('/api/settings'); }
    catch (e) { console.error('settings load', e); return; }

    // IGDB inputs
    const igdbId = document.getElementById('settings-igdb-id');
    const igdbSecret = document.getElementById('settings-igdb-secret');
    if (igdbId) igdbId.value = cfg.igdb_client_id || '';
    if (igdbSecret) igdbSecret.value = cfg.igdb_client_secret || '';

    // Auto-delete toggle
    const toggleDot = document.getElementById('settings-auto-delete-dot');
    const toggleBg = document.getElementById('settings-auto-delete-bg');
    function setToggle(val) {
      if (toggleDot) toggleDot.classList.toggle('translate-x-4', val);
      if (toggleBg) toggleBg.style.backgroundColor = val ? '#00d4ff' : '';
    }
    setToggle(cfg.auto_delete_after_watch);
    const toggleWrap = document.getElementById('settings-auto-delete-wrap');
    if (toggleWrap) {
      toggleWrap.onclick = async function() {
        cfg.auto_delete_after_watch = !cfg.auto_delete_after_watch;
        setToggle(cfg.auto_delete_after_watch);
        await apiPost('/api/settings', { auto_delete_after_watch: cfg.auto_delete_after_watch });
      };
    }

    // Kalite butonları
    const qualBtns = document.querySelectorAll('.settings-quality-btn');
    function setQuality(q) {
      qualBtns.forEach(b => {
        const active = b.dataset.quality === q;
        b.classList.toggle('bg-[#0d0d1a]', active);
        b.classList.toggle('text-[#00d4ff]', active);
        b.classList.toggle('text-[#9090b0]', !active);
      });
    }
    setQuality(cfg.default_quality || '720p');
    qualBtns.forEach(btn => {
      btn.addEventListener('click', async function() {
        cfg.default_quality = this.dataset.quality;
        setQuality(cfg.default_quality);
        await apiPost('/api/settings', { default_quality: cfg.default_quality });
      });
    });

    // IGDB kaydet butonu
    const igdbSaveBtn = document.getElementById('settings-igdb-save');
    if (igdbSaveBtn) {
      igdbSaveBtn.onclick = async function() {
        try {
          await apiPost('/api/settings', {
            igdb_client_id: igdbId ? igdbId.value.trim() : '',
            igdb_client_secret: igdbSecret ? igdbSecret.value.trim() : ''
          });
          this.textContent = 'Kaydedildi ✓';
          setTimeout(() => { this.textContent = 'Token Yenile'; }, 2000);
        } catch(e) { alert('Kayıt hatası: ' + e.message); }
      };
    }

    // Versiyon
    const verEl = document.getElementById('settings-version');
    if (verEl) verEl.textContent = 'v0.3.0 — Medya Takip Uygulaması';

    renderTagSettings();
    renderTagColorPicker();
  }

  // ── Tag Yönetimi ─────────────────────────────────────────────────

  function renderDetailTags(contentId, tags) {
    const row = document.getElementById('detail-tags-row');
    if (!row) return;
    const chips = tags.map(function(t) {
      const color = t.color || '#9090b0';
      return '<span class="flex items-center gap-1 px-2 py-1 rounded-full text-[11px] font-bold border" style="color:' + color + ';border-color:' + color + '40;background:' + color + '15">' +
        escapeHtml(t.name) +
        '<button class="detail-tag-remove flex items-center opacity-60 hover:opacity-100 ml-0.5" data-tag-id="' + t.id + '" data-content-id="' + contentId + '">' +
        '<span class="material-symbols-outlined text-[12px]">close</span></button></span>';
    }).join('');
    row.innerHTML = chips +
      '<button id="detail-tag-add-btn" class="flex items-center gap-1 px-2 py-1 rounded-full text-[11px] font-bold border border-white/10 text-[#9090b0] hover:border-[#00d4ff]/50 hover:text-[#00d4ff] transition-colors" data-content-id="' + contentId + '">' +
      '<span class="material-symbols-outlined text-[14px]">add</span> Etiket</button>';
  }

  async function openTagPicker(contentId, anchorEl) {
    if (_tagPickerEl) { _tagPickerEl.remove(); _tagPickerEl = null; }

    let allTags, contentData;
    try { allTags = await apiGet('/api/tags'); } catch (e) { return; }
    try { contentData = await apiGet('/api/content/' + contentId); } catch (e) { return; }
    const assignedIds = new Set((contentData.tags || []).map(function(t) { return t.id; }));

    const picker = document.createElement('div');
    picker.id = 'tag-picker-popover';
    picker.className = 'fixed z-[150] bg-[#1c1d37] border border-white/10 rounded-xl shadow-2xl min-w-[180px] max-h-[240px] overflow-y-auto py-2';

    if (allTags.length === 0) {
      picker.innerHTML = '<div class="px-4 py-3 text-[12px] text-[#9090b0]">Etiket yok — Ayarlar\'dan oluştur</div>';
    } else {
      picker.innerHTML = allTags.map(function(t) {
        const color = t.color || '#9090b0';
        const assigned = assignedIds.has(t.id);
        return '<button class="tag-picker-item w-full flex items-center gap-3 px-4 py-2 hover:bg-white/5 transition-colors text-left" data-tag-id="' + t.id + '" data-content-id="' + contentId + '" data-assigned="' + assigned + '">' +
          '<span class="w-3 h-3 rounded-full flex-shrink-0" style="background:' + color + '"></span>' +
          '<span class="text-[13px] text-[#e1e0ff] flex-1">' + escapeHtml(t.name) + '</span>' +
          (assigned ? '<span class="material-symbols-outlined text-[16px] text-[#00d4ff]">check</span>' : '') +
          '</button>';
      }).join('');
    }

    document.body.appendChild(picker);
    const rect = anchorEl.getBoundingClientRect();
    picker.style.top = (rect.bottom + 8) + 'px';
    picker.style.left = Math.min(rect.left, window.innerWidth - 200) + 'px';
    _tagPickerEl = picker;

    setTimeout(function() {
      document.addEventListener('click', function closePickerOnce(e) {
        if (!picker.contains(e.target) && e.target.id !== 'detail-tag-add-btn') {
          picker.remove();
          _tagPickerEl = null;
          document.removeEventListener('click', closePickerOnce);
        }
      });
    }, 0);
  }

  async function toggleTagOnContent(contentId, tagId, currentlyAssigned) {
    try {
      if (currentlyAssigned) {
        await apiDelete('/api/content/' + contentId + '/tags/' + tagId);
      } else {
        await apiPost('/api/content/' + contentId + '/tags/' + tagId, {});
      }
      const updated = await apiGet('/api/content/' + contentId);
      renderDetailTags(contentId, updated.tags || []);
      if (_tagPickerEl) { _tagPickerEl.remove(); _tagPickerEl = null; }
    } catch (e) {
      showToast('Etiket hatası: ' + e.message, 'error');
    }
  }

  async function renderTagSettings() {
    const list = document.getElementById('tag-list-settings');
    if (!list) return;
    let tags;
    try { tags = await apiGet('/api/tags'); } catch (e) { return; }
    if (tags.length === 0) {
      list.innerHTML = '<div class="px-4 py-4 text-[13px] text-[#9090b0]">Henüz etiket yok — Yeni butonu ile oluştur</div>';
      return;
    }
    list.innerHTML = tags.map(function(t) {
      const color = t.color || '#9090b0';
      return '<div class="flex items-center gap-3 px-4 py-3">' +
        '<span class="w-3 h-3 rounded-full flex-shrink-0" style="background:' + color + '"></span>' +
        '<span class="flex-1 text-[14px] text-[#e1e0ff]">' + escapeHtml(t.name) + '</span>' +
        '<span class="text-[10px] text-[#9090b0] uppercase font-bold mr-2">' + (t.tag_type === 'user' ? 'Kullanıcı' : 'API') + '</span>' +
        '<button class="tag-delete-btn w-8 h-8 flex items-center justify-center text-[#9090b0] hover:text-[#ffb4ab] transition-colors rounded-lg hover:bg-white/5" data-tag-id="' + t.id + '">' +
        '<span class="material-symbols-outlined text-[18px]">delete</span></button></div>';
    }).join('');
  }

  function renderTagColorPicker() {
    const picker = document.getElementById('tag-color-picker');
    if (!picker) return;
    picker.innerHTML = TAG_COLORS.map(function(c) {
      const active = c === _selectedTagColor;
      return '<button class="tag-color-dot w-6 h-6 rounded-full border-2 transition-all ' +
        (active ? 'border-white scale-125' : 'border-transparent hover:scale-110') +
        '" style="background:' + c + '" data-color="' + c + '"></button>';
    }).join('');
  }

  async function submitCreateTag() {
    const nameEl = document.getElementById('tag-name-input');
    const name = nameEl ? nameEl.value.trim() : '';
    if (!name) { showToast('Etiket adı gerekli', 'error'); return; }
    const btn = document.getElementById('tag-save-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Oluşturuluyor...'; }
    try {
      await apiPost('/api/tags', { name: name, color: _selectedTagColor, tag_type: 'user' });
      if (nameEl) nameEl.value = '';
      _selectedTagColor = TAG_COLORS[0];
      renderTagColorPicker();
      renderTagSettings();
      showToast('"' + name + '" etiketi oluşturuldu', 'success');
      const form = document.getElementById('tag-create-form');
      if (form) { form.classList.add('hidden'); form.classList.remove('flex'); }
    } catch (err) {
      showToast(err.message.includes('409') ? 'Bu etiket zaten var' : 'Hata: ' + err.message, 'error');
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = 'Oluştur'; }
    }
  }

  async function deleteTag(tagId) {
    try {
      await apiDelete('/api/tags/' + tagId);
      renderTagSettings();
      showToast('Etiket silindi', 'info');
    } catch (e) {
      showToast('Silme hatası', 'error');
    }
  }

  // ── Render: Search / Discover ─────────────────────────────────────
  let _searchTimer = null;

  async function renderSearch(q) {
    const results = document.getElementById('search-results');
    if (!results) return;
    if (!q || q.trim().length < 2) {
      results.innerHTML = '<div class="text-center text-[#9090b0] py-8">En az 2 karakter yaz...</div>';
      return;
    }
    results.innerHTML = '<div class="text-center text-[#9090b0] py-8 flex items-center justify-center gap-2"><span class="material-symbols-outlined animate-spin">progress_activity</span> AniList\'te aranıyor...</div>';
    try {
      const items = await apiGet('/api/discover?q=' + encodeURIComponent(q.trim()) + '&type=anime');
      if (!items || items.length === 0) {
        results.innerHTML = '<div class="text-center text-[#9090b0] py-8">Sonuç bulunamadı</div>';
        return;
      }
      results.innerHTML = items.map(it => {
        const typeLabel = it.type === 'manhwa' ? 'Manhwa' : it.type === 'manga' ? 'Manga' : 'Anime';
        const cover = it.cover_url
          ? `<img src="${it.cover_url}" class="w-full h-full object-cover" loading="lazy"/>`
          : `<span class="text-[#9090b0] font-bold text-xs">${escapeHtml(it.title.slice(0,2).toUpperCase())}</span>`;
        return `
          <div class="interactive-card flex items-center gap-4 p-3 rounded-xl bg-[#1c1d37] border border-white/5 inner-glow group hover:border-[#00d4ff]/30 transition-colors">
            <div class="w-[40px] h-[56px] shrink-0 rounded bg-[#31324d] overflow-hidden flex items-center justify-center">${cover}</div>
            <div class="flex flex-col gap-0.5 flex-grow min-w-0">
              <h4 class="font-bold text-[14px] text-[#e1e0ff] leading-tight truncate">${escapeHtml(it.title)}</h4>
              <div class="flex items-center gap-2 text-[#9090b0] text-[12px]">
                ${it.year ? '<span>' + it.year + '</span>' : ''}
                <span class="px-1.5 py-0.5 rounded-full bg-[#00d4ff]/15 text-[#00d4ff] text-[10px] font-bold">${typeLabel}</span>
              </div>
            </div>
            <button class="h-9 px-3 border border-[#00d4ff] text-[#00d4ff] rounded-full text-[13px] font-semibold flex items-center gap-1 hover:bg-[#00d4ff]/10 transition-colors flex-shrink-0 active:scale-[0.97]"
              data-discover-add='${JSON.stringify({title: it.title, type: (it.type||"anime"), cover_url: it.cover_url||"", external_id: String(it.id||"")})}'
            ><span class="material-symbols-outlined text-[16px]">add</span> Ekle</button>
          </div>`;
      }).join('');

      results.querySelectorAll('[data-discover-add]').forEach(btn => {
        btn.addEventListener('click', function() {
          const data = JSON.parse(this.dataset.discoverAdd);
          prefillAddForm(data);
          openModal('modal-add');
        });
      });
    } catch (err) {
      results.innerHTML = '<div class="text-center text-[#9090b0] py-8">Hata: ' + escapeHtml(err.message) + '</div>';
    }
  }

  function prefillAddForm(data) {
    const titleEl = document.getElementById('add-form-title');
    if (titleEl) titleEl.value = data.title || '';
    const coverEl = document.getElementById('add-form-cover');
    if (coverEl) coverEl.value = data.cover_url || '';
    const extInput = document.getElementById('add-form-external-id');
    if (extInput) extInput.value = data.external_id || '';

    // Tip seçimi
    document.querySelectorAll('.add-type-btn').forEach(btn => {
      const active = btn.dataset.addType === data.type;
      btn.classList.toggle('bg-[#1a2123]', active);
      btn.classList.toggle('text-[#00d4ff]', active);
      btn.classList.toggle('border', active);
      btn.classList.toggle('border-[#3c494e]/50', active);
      btn.classList.toggle('text-[#9090b0]', !active);
    });

    // step-1 gizle, step-2 göster
    const s1 = document.getElementById('add-step-1');
    const s2 = document.getElementById('add-step-2');
    if (s1) s1.classList.add('hidden');
    if (s2) s2.classList.remove('hidden');
  }

  async function submitAddContent() {
    const title = (document.getElementById('add-form-title') || {}).value || '';
    if (!title.trim()) {
      alert('Başlık gerekli');
      return;
    }
    const activeType = document.querySelector('.add-type-btn.text-\\[\\#00d4ff\\]');
    const type = activeType ? activeType.dataset.addType : 'anime';
    const status = (document.getElementById('add-form-status') || {}).value || 'planning';
    const cover_url = (document.getElementById('add-form-cover') || {}).value.trim() || null;
    const note_text = (document.getElementById('add-form-note') || {}).value.trim() || null;
    const external_id = (document.getElementById('add-form-external-id') || {}).value.trim() || null;
    const starEl = document.querySelector('input[name="add-rating"]:checked');
    const my_score = starEl ? parseFloat(starEl.value) : null;

    const btn = document.getElementById('add-save-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Kaydediliyor...'; }

    try {
      await apiPost('/api/content', { title: title.trim(), type, status, cover_url, note_text, external_id, my_score });
      closeModal('modal-add');
      // Formu temizle
      ['add-form-title','add-form-cover','add-form-note'].forEach(id => {
        const el = document.getElementById(id); if (el) el.value = '';
      });
      if (window.location.hash === '#screen-home' || !window.location.hash) renderHome();
    } catch (err) {
      alert('Kayıt hatası: ' + err.message);
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '<span class="material-symbols-outlined">library_add</span> Kütüphaneye Ekle'; }
    }
  }

  // ── Yardımcı Fonksiyonlar ────────────────────────────────────────
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatRelativeTime(iso) {
    const d = new Date(iso);
    const now = new Date();
    const diff = (now - d) / 1000;
    if (diff < 60) return 'şimdi';
    if (diff < 3600) return Math.floor(diff/60) + ' dk önce';
    if (diff < 86400) return Math.floor(diff/3600) + ' saat önce';
    if (diff < 86400*2) return 'Dün';
    if (diff < 86400*7) return Math.floor(diff/86400) + ' gün önce';
    return d.toLocaleDateString('tr-TR');
  }

  // ── Event Binders ────────────────────────────────────────────────
  document.addEventListener('click', function(e) {
    const navEl = e.target.closest('[data-nav]');
    if (navEl) {
      e.preventDefault();
      showScreen(navEl.dataset.nav);
      return;
    }
    const openEl = e.target.closest('[data-modal-open]');
    if (openEl) {
      e.preventDefault();
      openModal(openEl.dataset.modalOpen);
      return;
    }
    const closeEl = e.target.closest('[data-modal-close]');
    if (closeEl) {
      e.preventDefault();
      closeModal(closeEl.dataset.modalClose);
      return;
    }
  });

  // Dışa Aktar
  document.addEventListener('click', function(e) {
    if (e.target.closest('#settings-export-btn')) {
      apiGet('/api/export').then(data => {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'kurowatch_export_' + new Date().toISOString().slice(0,10) + '.json';
        a.click();
        URL.revokeObjectURL(url);
      }).catch(e => alert('Export hatası: ' + e.message));
    }
  });

  // Add-form type butonları
  document.addEventListener('click', function(e) {
    const typeBtn = e.target.closest('.add-type-btn');
    if (typeBtn) {
      document.querySelectorAll('.add-type-btn').forEach(b => {
        const active = b === typeBtn;
        b.classList.toggle('bg-[#1a2123]', active);
        b.classList.toggle('text-[#00d4ff]', active);
        b.classList.toggle('border', active);
        b.classList.toggle('border-[#3c494e]/50', active);
        b.classList.toggle('text-[#9090b0]', !active);
      });
    }
    // Save butonu
    if (e.target.closest('#add-save-btn')) {
      e.preventDefault();
      submitAddContent();
    }
  });

  // ESC ile modal kapat
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.open').forEach(m => closeModal(m.id));
    }
  });

  // Home arama + Discover arama
  document.addEventListener('input', function(e) {
    if (e.target.id === 'home-search-input') {
      homeFilter.query = e.target.value;
      renderHome();
    }
    if (e.target.id === 'search-discover-input') {
      clearTimeout(_searchTimer);
      const q = e.target.value;
      _searchTimer = setTimeout(() => renderSearch(q), 400);
    }
  });

  // Home filtre chips
  document.addEventListener('click', function(e) {
    const t = e.target.closest('.filter-type');
    if (t) {
      homeFilter.type = t.dataset.filterType;
      document.querySelectorAll('.filter-type').forEach(b => {
        const active = b === t;
        b.classList.toggle('bg-[#00d4ff]/15', active);
        b.classList.toggle('border-[#00d4ff]', active);
        b.classList.toggle('text-[#00d4ff]', active);
        b.classList.toggle('bg-[#1c1d37]', !active);
        b.classList.toggle('border-white/5', !active);
        b.classList.toggle('text-[#9090b0]', !active);
      });
      renderHome();
    }
    const s = e.target.closest('.filter-status');
    if (s) {
      homeFilter.status = s.dataset.filterStatus;
      document.querySelectorAll('.filter-status').forEach(b => {
        const active = b === s;
        b.classList.toggle('bg-[#3b4665]', active);
        b.classList.toggle('border-[#3b4665]', active);
        b.classList.toggle('text-[#e1e0ff]', active);
        b.classList.toggle('bg-[#1c1d37]', !active);
        b.classList.toggle('border-white/5', !active);
        b.classList.toggle('text-[#9090b0]', !active);
      });
      renderHome();
    }
  });

  // Updates + Tag click handlers
  document.addEventListener('click', function(e) {
    // Kontrol Et butonu
    if (e.target.closest('#updates-check-btn')) {
      runCheckUpdates();
      return;
    }
    // Detail tag ekle butonu → picker aç
    const addTagBtn = e.target.closest('#detail-tag-add-btn');
    if (addTagBtn) {
      const cid = parseInt(addTagBtn.dataset.contentId, 10);
      openTagPicker(cid, addTagBtn);
      return;
    }
    // Detail tag kaldır butonu
    const removeTagBtn = e.target.closest('.detail-tag-remove');
    if (removeTagBtn) {
      e.stopPropagation();
      const cid = parseInt(removeTagBtn.dataset.contentId, 10);
      const tid = parseInt(removeTagBtn.dataset.tagId, 10);
      toggleTagOnContent(cid, tid, true);
      return;
    }
    // Tag picker öğesi → toggle
    const pickerItem = e.target.closest('.tag-picker-item');
    if (pickerItem) {
      const cid = parseInt(pickerItem.dataset.contentId, 10);
      const tid = parseInt(pickerItem.dataset.tagId, 10);
      const assigned = pickerItem.dataset.assigned === 'true';
      toggleTagOnContent(cid, tid, assigned);
      return;
    }
    // Yeni etiket formu aç/kapat
    if (e.target.closest('#tag-create-toggle')) {
      const form = document.getElementById('tag-create-form');
      if (!form) return;
      const hidden = form.classList.contains('hidden');
      form.classList.toggle('hidden', !hidden);
      form.classList.toggle('flex', hidden);
      return;
    }
    // Etiket oluştur
    if (e.target.closest('#tag-save-btn')) {
      submitCreateTag();
      return;
    }
    // Etiket renk seç
    const colorDot = e.target.closest('.tag-color-dot');
    if (colorDot) {
      _selectedTagColor = colorDot.dataset.color;
      renderTagColorPicker();
      return;
    }
    // Etiket sil
    const deleteBtn = e.target.closest('.tag-delete-btn');
    if (deleteBtn) {
      deleteTag(parseInt(deleteBtn.dataset.tagId, 10));
      return;
    }
  });

  // ── Service Worker Kaydı ─────────────────────────────────────────
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('sw.js').catch(err => {
        console.warn('SW kayıt hatası:', err);
      });
    });
  }

  // ── Init ─────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function() {
    // İlk hash'e göre ekran aç
    const initial = (location.hash || '').replace('#','') || 'screen-home';
    const valid = ['screen-home','screen-detail','screen-search','screen-updates','screen-stats','screen-settings','screen-archive'];
    showScreen(valid.includes(initial) ? initial : 'screen-home');

    // i18n uygula (varsa)
    if (window.kuroI18n && typeof window.kuroI18n.apply === 'function') {
      window.kuroI18n.apply();
    }
  });

})();
