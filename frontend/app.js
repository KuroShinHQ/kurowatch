// ═══════════════════════════════════════════════════════════════════
// KuroWatch SPA — Ana JavaScript
// Navigasyon + Mock Data + API Layer + Render Fonksiyonları
// ═══════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  // ── Konfigürasyon ─────────────────────────────────────────────────
  const API_BASE = window.location.origin;
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

  // Tür çevirileri (AniList İngilizce → Türkçe)
  const GENRE_TR = {
    'Action':'Aksiyon','Adult Cast':'Yetişkin','Adventure':'Macera',
    'Award Winning':'Ödüllü','Boys Love':'Boys Love','Comedy':'Komedi',
    'Detective':'Dedektif','Drama':'Dram','Ecchi':'Ecchi',
    'Fantasy':'Fantezi','Girls Love':'Girls Love','Gore':'Gore/Şiddet',
    'Gourmet':'Gurme','Harem':'Harem','Historical':'Tarihi',
    'Horror':'Korku','Isekai':'Isekai','Iyashikei':'İyileştirici',
    'Josei':'Josei','Kids':'Çocuk','Love Polygon':'Aşk Üçgeni',
    'Mahou Shoujo':'Sihirli Kız','Martial Arts':'Dövüş Sanatları',
    'Mecha':'Meka','Medical':'Tıbbi','Military':'Askeri','Music':'Müzik',
    'Mystery':'Gizem','Mythology':'Mitoloji','Organized Crime':'Organize Suç',
    'Parody':'Parodi','Psychological':'Psikolojik','Racing':'Yarış',
    'Reincarnation':'Reenkarnasyon','Reverse Harem':'Ters Harem',
    'Romance':'Romantik','Samurai':'Samuray','School':'Okul',
    'Sci-Fi':'Bilim Kurgu','Seinen':'Seinen','Shoujo':'Shoujo',
    'Shounen':'Shounen','Slice of Life':'Günlük Yaşam','Space':'Uzay',
    'Sports':'Spor','Super Power':'Süper Güç','Supernatural':'Doğaüstü',
    'Survival':'Hayatta Kalma','Suspense':'Gerilim','Team Sports':'Takım Sporu',
    'Thriller':'Gerilim','Time Travel':'Zaman Yolculuğu',
    'Urban Fantasy':'Kentsel Fantezi','Vampire':'Vampir',
    'Video Game':'Video Oyunu','Villainess':'Kötü Kız','Workplace':'İş Yeri',
    'Eligible Titles For You Should Read This':'Önerilen',
  };
  function genreTR(g) { return GENRE_TR[g] || g; }

  // Tip rozetleri için renkler
  const TYPE_COLOR = {
    'anime':  { color:'#00d4ff', label:'Anime' },
    'manga':  { color:'#ffd9a1', label:'Manga' },
    'manhwa': { color:'#bbc5eb', label:'Manhwa' },
    'game':   { color:'#ffb4ab', label:'Oyun' }
  };
  function tcStyle(tc) {
    const c = tc.color;
    return { badge: `color:${c};background:${c}1a;border:1px solid ${c}33`, bar: `background:${c}` };
  }

  const STATUS_LABEL = {
    'watching': 'İzliyor',
    'completed': 'Tamamlandı',
    'on_hold': 'Beklemede',
    'plan_to_watch': 'Planlı',
    'planning': 'Planlı',
    'dropped': 'Bırakıldı',
    'rewatching': 'Tekrar İzliyor'
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
  const _NAV_ORDER = ['screen-home','screen-search','screen-updates','screen-downloads','screen-settings','screen-stats','screen-archive'];
  let _currentScreen = 'screen-home';

  function showScreen(id) {
    const prev = _currentScreen;
    const prevIdx = _NAV_ORDER.indexOf(prev);
    const nextIdx = _NAV_ORDER.indexOf(id);
    const isDetail = id === 'screen-detail';

    let animClass = '';
    if (isDetail) {
      animClass = 'slide-up';
    } else if (prevIdx >= 0 && nextIdx >= 0 && nextIdx !== prevIdx) {
      animClass = nextIdx > prevIdx ? 'slide-in-right' : 'slide-in-left';
    }

    document.querySelectorAll('.screen').forEach(s => {
      const isTarget = s.id === id;
      s.classList.toggle('active', isTarget);
      s.classList.toggle('hidden', !isTarget);
      if (isTarget) {
        s.classList.remove('slide-in-right','slide-in-left','slide-up');
        if (animClass) {
          void s.offsetWidth;
          s.classList.add(animClass);
        }
      }
    });
    _currentScreen = id;
    history.replaceState({ screen: id }, '', '#' + id);
    updateNavActive(id);

    // Ekran başına render
    if (id === 'screen-home')      renderHome();
    if (id === 'screen-updates')   renderUpdates();
    if (id === 'screen-stats')     renderStats();
    if (id === 'screen-archive')   renderArchive();
    if (id === 'screen-settings')  renderSettings();
    if (id === 'screen-downloads' && window.kuroDownload) window.kuroDownload.render();
    if (id === 'screen-search') {
      setTimeout(() => {
        _initSearchTabs();
        const inp = document.getElementById('search-discover-input');
        if (inp) { inp.focus(); }
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

  function _initModalSwipe(el, id) {
    const sheet = el.querySelector('[data-swipe-sheet]') || el.querySelector('.modal-sheet') || el.lastElementChild;
    if (!sheet) return;
    let startY = 0, currentY = 0, dragging = false;
    sheet.addEventListener('touchstart', function(e) {
      startY = e.touches[0].clientY;
      currentY = 0;
      dragging = true;
      sheet.style.transition = 'none';
    }, { passive: true });
    sheet.addEventListener('touchmove', function(e) {
      if (!dragging) return;
      currentY = e.touches[0].clientY - startY;
      if (currentY > 0) sheet.style.transform = 'translateY(' + currentY + 'px)';
    }, { passive: true });
    sheet.addEventListener('touchend', function() {
      dragging = false;
      sheet.style.transition = 'transform 0.25s cubic-bezier(0.32,0.72,0,1)';
      if (currentY > 120) {
        sheet.style.transform = 'translateY(100%)';
        setTimeout(function() {
          sheet.style.transform = '';
          sheet.style.transition = '';
          closeModal(id);
        }, 250);
      } else {
        sheet.style.transform = '';
      }
    });
  }

  function openModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('hidden');
    // Add modal: her açılışta step-1'den başla, step-2 gizle
    if (id === 'modal-add') {
      const s1 = document.getElementById('add-step-1');
      const s2 = document.getElementById('add-step-2');
      if (s1) s1.classList.remove('hidden');
      if (s2) s2.classList.add('hidden');
      _initAddSearch();
      _initModalSwipe(el, id);
    }
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
  window.kuroNav   = { show: showScreen, openModal: openModal, closeModal: closeModal };
  window.openDetail = function(id) { renderDetail(id); showScreen('screen-detail'); };
  window.kuroToast = showToast;

  // ── Render: Home (Kütüphane Grid) ────────────────────────────────
  let homeFilter = { type: 'all', status: 'all', genre: 'all', query: '' };

  // ── v7 Hero + Satır render ────────────────────────────────────────
  async function renderHomeV7(items) {
    if (!items || items.length === 0) return;
    const tc = TYPE_COLOR;

    // Hero: en yüksek skorlu veya en son eklenen
    const hero = items.slice().sort((a,b) => (b.my_score||0) - (a.my_score||0))[0];
    const heroBg  = document.getElementById('home-hero-bg');
    const heroTit = document.getElementById('home-hero-title');
    const heroMet = document.getElementById('home-hero-meta');
    const heroSyn = document.getElementById('home-hero-synopsis');
    const heroBadge = document.getElementById('home-hero-status-badge');
    const heroCont  = document.getElementById('home-hero-continue-btn');
    const heroDetail= document.getElementById('home-hero-detail-btn');

    if (hero) {
      if (heroBg && hero.cover_url) heroBg.style.backgroundImage = 'url(' + escapeHtml(hero.cover_url) + ')';
      if (heroTit) heroTit.textContent = hero.title_tr || hero.title;
      const col = (tc[hero.type]||tc.anime).color;
      if (heroMet) heroMet.textContent = (hero.type||'').toUpperCase() + (hero.my_score ? ' · ★' + hero.my_score.toFixed(1) : '');
      if (heroSyn) { heroSyn.textContent = hero.note_text || ''; heroSyn.classList.toggle('hidden', !hero.note_text); }
      const statusMap = {watching:'● İZLİYORUM',completed:'● TAMAMLANDI',on_hold:'● ASKIDA',dropped:'● BIRAKTIM',plan_to_watch:'● PLANLANDI'};
      if (heroBadge) heroBadge.textContent = statusMap[hero.status] || '● —';
      if (heroCont) heroCont.onclick = () => window.openDetail(hero.id);
      if (heroDetail) heroDetail.onclick = () => window.openDetail(hero.id);
    }

    // Devam Et: progress 1-99%
    const continueItems = items.filter(it => {
      const total = it.type==='game' ? 100 : (it.type==='anime' ? (it.total_episodes||1) : (it.total_chapters||1));
      const pct = it.type==='game' ? (it.my_progress_pct||0) : Math.min(100,Math.round((it.my_progress||0)/total*100));
      return pct > 0 && pct < 100;
    });
    const contRow = document.getElementById('home-continue-row');
    const contSec = document.getElementById('home-continue-section');
    if (contRow && continueItems.length > 0) {
      contSec && contSec.classList.remove('hidden');
      contRow.innerHTML = continueItems.slice(0,10).map(it => {
        const col = (tc[it.type]||tc.anime);
        const total = it.type==='game' ? 100 : (it.type==='anime' ? (it.total_episodes||1) : (it.total_chapters||1));
        const pct = it.type==='game' ? (it.my_progress_pct||0) : Math.min(100,Math.round((it.my_progress||0)/total*100));
        const bg = it.cover_url ? `style="background-image:url(${escapeHtml(it.cover_url)})"` : '';
        return `<div class="flex-none w-[280px] md:w-[320px] aspect-video relative rounded-xl overflow-hidden bg-[#1a1a2e] border border-white/5 active:scale-[0.95] transition-transform cursor-pointer snap-start group" data-content-id="${it.id}">
          <div class="absolute inset-0 bg-cover bg-center" ${bg}></div>
          <div class="absolute top-2 right-2 z-20"><span class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase backdrop-blur-sm" style="${tcStyle(col).badge}">${escapeHtml(col.label)}</span></div>
          <div class="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/95 via-black/40 to-transparent">
            <h4 class="text-[13px] font-bold text-[#e1e0ff] mb-1 line-clamp-1">${escapeHtml(it.title_tr||it.title)}</h4>
            <div class="w-full h-1 bg-white/10 rounded-full overflow-hidden shimmer-bar">
              <div class="h-full rounded-full" style="background:${col.color};width:${pct}%;box-shadow:0 0 8px ${col.color}99"></div>
            </div>
          </div>
          <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <span class="material-symbols-outlined fill-1 text-[#00d4ff]" style="font-size:40px">play_circle</span>
          </div>
        </div>`;
      }).join('');
      contRow.querySelectorAll('[data-content-id]').forEach(c => _attachCardEvents(c));
    }

    // Tip satırları
    const rows = [
      {key:'anime', secId:'home-anime-section', rowId:'home-anime-row', label:'Animeler'},
      {key:'manga', secId:'home-manga-section', rowId:'home-manga-row', label:'Manga & Manhwa'},
      {key:'manhwa',secId:'home-manga-section', rowId:'home-manga-row', label:'Manga & Manhwa'},
      {key:'game',  secId:'home-games-section', rowId:'home-games-row', label:'Oyunlar'},
    ];
    const rowMap = {};
    rows.forEach(r => {
      if (!rowMap[r.rowId]) rowMap[r.rowId] = {secId:r.secId, items:[]};
      rowMap[r.rowId].items.push(...items.filter(it => it.type===r.key));
    });
    Object.entries(rowMap).forEach(([rowId, {secId, items:rowItems}]) => {
      const row = document.getElementById(rowId);
      const sec = document.getElementById(secId);
      if (!row || rowItems.length === 0) return;
      sec && sec.classList.remove('hidden');
      row.innerHTML = rowItems.slice(0,20).map(it => {
        const col = (tc[it.type]||tc.anime);
        const bg = it.cover_url ? `style="background-image:url(${escapeHtml(it.cover_url)})"` : '';
        return `<div class="flex-none w-[140px] md:w-[180px] aspect-[2/3] relative rounded-xl overflow-hidden bg-[#1a1a2e] border border-white/5 active:scale-[0.95] transition-all snap-start cursor-pointer hover:-translate-y-1" data-content-id="${it.id}">
          <div class="absolute inset-0 bg-cover bg-center" ${bg}>${!it.cover_url ? '<div class="absolute inset-0 flex items-center justify-center text-[#31324d] text-3xl font-bold">'+escapeHtml(it.title.slice(0,2).toUpperCase())+'</div>' : ''}</div>
          <div class="absolute top-2 right-2 z-20"><span class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase backdrop-blur-sm" style="${tcStyle(col).badge}">${escapeHtml(col.label)}</span></div>
          <div class="absolute inset-x-0 bottom-0 p-2 bg-gradient-to-t from-[#0d0d1a]/95 via-[#0d0d1a]/60 to-transparent">
            <h4 class="text-[11px] font-bold text-[#e1e0ff] line-clamp-2">${escapeHtml(it.title_tr||it.title)}</h4>
          </div>
        </div>`;
      }).join('');
      row.querySelectorAll('[data-content-id]').forEach(c => _attachCardEvents(c));
    });
  }

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

    // v7 Hero + satırları doldur (paralel, bağımsız)
    renderHomeV7(items).catch(() => {});

    // Background: genres boş ama external_id varsa otomatik patch
    const needsPatch = items.some(function(it) { return it.external_id && (!it.genres || it.genres.length === 0); });
    if (needsPatch) {
      apiPost('/api/genres/patch-all', {}).then(function(res) {
        if (res.patched > 0) renderHome();
      }).catch(function() {});
    }

    // Filtrele
    const filtered = items.filter(it => {
      if (homeFilter.type !== 'all' && it.type !== homeFilter.type) return false;
      if (homeFilter.status !== 'all' && it.status !== homeFilter.status) return false;
      if (homeFilter.genre !== 'all' && !(it.genres || []).includes(homeFilter.genre)) return false;
      if (homeFilter.query && !it.title.toLowerCase().includes(homeFilter.query.toLowerCase())) return false;
      return true;
    });

    if (filtered.length === 0) {
      const isEmpty = items.length === 0;
      grid.innerHTML = isEmpty
        ? '<div class="col-span-full flex flex-col items-center gap-5 py-16">' +
            '<span class="material-symbols-outlined text-[64px] text-[#31324d]">video_library</span>' +
            '<div class="text-center"><p class="text-[18px] font-bold text-[#e1e0ff] mb-1">Kütüphanen boş</p>' +
            '<p class="text-[13px] text-[#9090b0]">İlk içeriğini eklemek için aşağıdaki + butonuna bas</p></div>' +
            '<button class="flex items-center gap-2 px-6 py-3 rounded-2xl bg-[#00d4ff] text-[#003642] font-bold text-[14px] active:scale-[0.97] transition-transform" data-modal-open="modal-add">' +
            '<span class="material-symbols-outlined">add</span> İçerik Ekle</button>' +
          '</div>'
        : '<div class="col-span-full text-center text-[#9090b0] py-12 flex flex-col items-center gap-2">' +
            '<span class="material-symbols-outlined text-4xl">filter_list_off</span>' +
            '<p>Bu filtreyle eşleşen içerik yok</p></div>';
      return;
    }

    grid.innerHTML = filtered.map(it => {
      const tc = TYPE_COLOR[it.type] || TYPE_COLOR.anime;
      const isGameCard = it.type === 'game';
      const isAnimeCard = it.type === 'anime';
      const total = isGameCard ? 100 : (isAnimeCard ? (it.total_episodes || 1) : (it.total_chapters || 1));
      const pct = isGameCard
        ? (it.my_progress_pct || 0)
        : Math.min(100, Math.round((it.my_progress || 0) / total * 100));
      // Sağ üst: senin puanın (my_score) — yoksa badge gösterme
      const myScoreBadge = it.my_score != null && it.my_score > 0
        ? `<div style="position:absolute;top:8px;right:8px;background:#00d4ff;color:#003642;font-size:11px;font-weight:700;padding:2px 7px;border-radius:999px;box-shadow:0 2px 8px #0006;z-index:10">${it.my_score.toFixed(1)}</div>`
        : '';
      // Sol üst: dış kaynak puanı (external_score) → yıldız — yoksa gösterme
      const extStarCount = it.external_score != null && it.external_score > 0 ? Math.round(it.external_score / 2) : 0;
      const starsHtml = extStarCount > 0
        ? `<div style="position:absolute;top:8px;left:8px;z-index:10;pointer-events:none;color:#fbbf24;font-size:12px;text-shadow:0 1px 4px rgba(0,0,0,0.9);letter-spacing:1px;display:flex;gap:1px">${'★'.repeat(extStarCount)}<span style="opacity:0.22;color:#fff">${'★'.repeat(5 - extStarCount)}</span></div>`
        : '';
      const initials = it.title.split(' ').slice(0,2).map(w => w[0]).join('').toUpperCase();
      const initialsHtml = `<div class="absolute inset-0 flex items-center justify-center text-[#31324d] text-5xl font-bold">${initials}</div>`;
      const coverBg = it.cover_url
        ? `${initialsHtml}<img src="${escapeHtml(it.cover_url)}" class="absolute inset-0 w-full h-full object-cover" loading="lazy" onerror="this.style.display='none'"/>`
        : initialsHtml;

      return `
        <div class="interactive-card relative group aspect-[2/3] rounded-card overflow-hidden bg-[#1c1d37] border border-white/5 hover:border-[#00d4ff]/50 hover:scale-[1.02] transition-all duration-300 cursor-pointer inner-glow" data-content-id="${it.id}">
          ${coverBg}
          <div class="absolute inset-0 bg-gradient-to-t from-[#0d0d1a]/95 via-[#0d0d1a]/60 to-transparent"></div>
          ${myScoreBadge}
          ${starsHtml}
          <div class="absolute bottom-0 w-full p-3 flex flex-col gap-1.5">
            <span class="text-[10px] font-bold w-fit px-1.5 py-0.5 rounded uppercase leading-none" style="${tcStyle(tc).badge}">${tc.label}</span>
            <h3 class="text-[13px] font-bold text-[#e1e0ff] line-clamp-2 leading-tight">${escapeHtml(it.title_tr || it.title)}</h3>
            <div class="w-full bg-white/10 h-1 rounded-full mt-1 overflow-hidden">
              <div class="h-full" style="${tcStyle(tc).bar};width:${pct}%;box-shadow:0 0 8px ${tc.color}99"></div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Kart tıklama + uzun bas menüsü
    grid.querySelectorAll('[data-content-id]').forEach(card => {
      _attachCardEvents(card);
    });
  }

  // ── Context menü (Home kartları) ─────────────────────────────────
  let _ctxMenu = null;
  function _getCtxMenu() {
    if (_ctxMenu) return _ctxMenu;
    _ctxMenu = document.createElement('div');
    _ctxMenu.id = 'home-ctx-menu';
    _ctxMenu.className = 'fixed z-[9999] hidden flex-col rounded-2xl overflow-hidden shadow-2xl border border-white/10 bg-[#12132a]/95 backdrop-blur-xl min-w-[160px]';
    _ctxMenu.innerHTML = `
      <button id="ctx-detail" class="flex items-center gap-3 px-4 py-3 text-[14px] text-[#e1e0ff] hover:bg-white/10 transition-colors text-left">
        <span class="material-symbols-outlined text-[18px] text-[#00d4ff]">open_in_new</span> Detay
      </button>
      <div class="h-px bg-white/10 mx-3"></div>
      <button id="ctx-delete" class="flex items-center gap-3 px-4 py-3 text-[14px] text-red-400 hover:bg-red-500/10 transition-colors text-left">
        <span class="material-symbols-outlined text-[18px]">delete</span> Sil
      </button>`;
    document.body.appendChild(_ctxMenu);
    document.addEventListener('click', function(e) {
      if (!_ctxMenu.contains(e.target)) _hideCtxMenu();
    }, true);
    return _ctxMenu;
  }

  function _showCtxMenu(x, y, contentId) {
    const menu = _getCtxMenu();
    menu.classList.remove('hidden');
    menu.classList.add('flex');
    // Ekran sınırı kontrolü
    const mw = 180, mh = 110;
    const px = Math.min(x, window.innerWidth - mw - 8);
    const py = Math.min(y, window.innerHeight - mh - 8);
    menu.style.left = px + 'px';
    menu.style.top = py + 'px';
    menu.querySelector('#ctx-detail').onclick = function() {
      _hideCtxMenu();
      renderDetail(contentId);
      showScreen('screen-detail');
    };
    menu.querySelector('#ctx-delete').onclick = async function() {
      _hideCtxMenu();
      if (!confirm('Bu içeriği silmek istiyor musun?')) return;
      try {
        await apiDelete('/api/content/' + contentId);
        renderHome();
      } catch(e) { alert('Silinemedi: ' + e.message); }
    };
  }

  function _hideCtxMenu() {
    if (!_ctxMenu) return;
    _ctxMenu.classList.add('hidden');
    _ctxMenu.classList.remove('flex');
  }

  function _attachCardEvents(card) {
    let pressTimer = null;
    let longPressed = false;
    const LONG_MS = 550;

    function startPress(x, y) {
      longPressed = false;
      pressTimer = setTimeout(function() {
        longPressed = true;
        const id = parseInt(card.dataset.contentId, 10);
        _showCtxMenu(x, y, id);
        if (navigator.vibrate) navigator.vibrate(30);
      }, LONG_MS);
    }
    function cancelPress() { clearTimeout(pressTimer); }

    card.addEventListener('mousedown', function(e) {
      if (e.button !== 0) return;
      startPress(e.clientX, e.clientY);
    });
    card.addEventListener('mousemove', cancelPress);
    card.addEventListener('mouseup', cancelPress);
    card.addEventListener('mouseleave', cancelPress);
    card.addEventListener('touchstart', function(e) {
      const t = e.touches[0];
      startPress(t.clientX, t.clientY);
    }, { passive: true });
    card.addEventListener('touchmove', cancelPress, { passive: true });
    card.addEventListener('touchend', cancelPress);
    card.addEventListener('click', function(e) {
      if (longPressed) { e.preventDefault(); e.stopPropagation(); return; }
      const id = parseInt(card.dataset.contentId, 10);
      renderDetail(id);
      showScreen('screen-detail');
    });
  }

  // ── Render: Detail ───────────────────────────────────────────────
  async function renderDetail(id) {
    const qePanel = document.getElementById('progress-quick-edit');
    if (qePanel) qePanel.style.display = 'none';
    let item;
    try { item = await apiGet('/api/content/' + id); }
    catch (err) { console.error('renderDetail', err); return; }
    if (!item) return;

    const tc = TYPE_COLOR[item.type] || TYPE_COLOR.anime;
    const isGame = item.type === 'game';
    const isAnime = item.type === 'anime';
    const total = isGame ? 100 : (isAnime ? (item.total_episodes || 0) : (item.total_chapters || 0)) || 0;
    const cur = isGame ? (item.my_progress_pct || 0) : (item.my_progress || 0);
    const pct = isGame ? cur : (total > 0 ? Math.round(cur / total * 100) : 0);

    document.getElementById('detail-title').textContent = item.title_tr || item.title;
    const typeLabelMap = { 'anime':'ANİME', 'manga':'MANGA', 'manhwa':'MANHWA', 'game':'OYUN' };
    const typeBadgeEl = document.getElementById('detail-type-badge');
    typeBadgeEl.textContent = typeLabelMap[item.type] || (item.type || '').toUpperCase();
    typeBadgeEl.style.cssText = tcStyle(tc).badge;
    document.getElementById('detail-progress-bar').style.background = tc.color;
    const statusIcon = isGame ? 'sports_esports' : (isAnime ? 'play_circle' : 'menu_book');
    document.getElementById('detail-status-badge').innerHTML = `<span class="material-symbols-outlined text-[14px]">${statusIcon}</span> ${STATUS_LABEL[item.status] || item.status}`;
    document.getElementById('detail-progress-current').textContent = isGame ? cur + '%' : cur;
    document.getElementById('detail-progress-total').textContent = isGame ? 'tamamlandı' : ('/ ' + (total || '?'));
    document.getElementById('detail-progress-pct').textContent = pct + '%';
    document.getElementById('detail-progress-bar').style.width = pct + '%';
    const slider = document.getElementById('detail-progress-slider');
    slider.max = isGame ? 100 : (total || 999);
    slider.value = cur;
    document.getElementById('detail-slider-max').textContent = isGame ? '100%' : (total || '?');

    // Progress bölüm etiketi (oyun / manga / anime)
    const progressLabel = document.querySelector('#screen-detail .font-label-caps.uppercase');
    if (progressLabel) progressLabel.textContent = isGame ? 'TAMAMLANMA' : (isAnime ? 'BÖLÜM' : 'CHAPTER');

    // Mark butonu etiketi
    const markBtn = document.getElementById('detail-mark-btn');
    if (markBtn) {
      if (isGame) {
        markBtn.style.display = 'none';
      } else {
        markBtn.style.display = '';
        markBtn.querySelector('span.font-bold').textContent = isAnime ? 'Sonraki Bölümü İşaretle' : 'Sonraki Chapter\'ı İşaretle';
      }
    }

    // DEVAM ET butonu (hero'da): progress 1-99% ise göster
    const contBtn = document.getElementById('detail-continue-btn');
    const contLabel = document.getElementById('detail-continue-label');
    if (contBtn) {
      const showCont = !isGame && pct > 0 && pct < 100;
      contBtn.classList.toggle('hidden', !showCont);
      if (showCont && contLabel) {
        const nextEp = cur + 1;
        const unitWord = isAnime ? 'Bölüm' : 'Chapter';
        contLabel.textContent = 'DEVAM ET — ' + unitWord + ' ' + nextEp;
      }
      if (showCont && markBtn) {
        contBtn.onclick = function() { markBtn.click(); };
      }
    }

    // Rating yıldızları (interaktif — tıklanınca PATCH ile kaydet)
    let currentScore = item.my_score || 0;
    const ratingEl = document.getElementById('detail-rating-container');
    const scoreTxt = document.getElementById('detail-score-text');
    function highlightStars(n) {
      Array.from(ratingEl.querySelectorAll('[data-star]')).forEach(function(s) {
        s.style.color = parseInt(s.dataset.star, 10) <= n ? '#00d4ff' : '#4a4b72';
      });
      if (scoreTxt) scoreTxt.textContent = n > 0 ? n + ' / 10' : '— / 10';
    }
    ratingEl.innerHTML = '';
    for (let i = 1; i <= 10; i++) {
      const span = document.createElement('span');
      span.className = 'material-symbols-outlined cursor-pointer text-[28px] transition-colors';
      span.style.color = i <= currentScore ? '#00d4ff' : '#4a4b72';
      span.style.fontVariationSettings = "'FILL' 1";
      span.textContent = 'star';
      span.dataset.star = String(i);
      ratingEl.appendChild(span);
    }
    ratingEl.addEventListener('pointerover', function(e) {
      const s = e.target.closest('[data-star]');
      if (s) highlightStars(parseInt(s.dataset.star, 10));
    });
    ratingEl.addEventListener('pointerleave', function() { highlightStars(currentScore); });
    ratingEl.addEventListener('click', async function(e) {
      const s = e.target.closest('[data-star]');
      if (!s) return;
      const v = parseInt(s.dataset.star, 10);
      currentScore = v;
      highlightStars(v);
      try { await apiPatch('/api/content/' + id, { my_score: v }); }
      catch (err) { console.error('score save', err); }
    });
    if (scoreTxt) scoreTxt.textContent = currentScore > 0 ? currentScore + ' / 10' : '— / 10';

    // Cover bg
    const coverEl = document.getElementById('detail-cover-bg');
    if (item.cover_url) {
      coverEl.style.backgroundImage = 'url(' + item.cover_url + ')';
      coverEl.style.backgroundSize = 'auto 100%';
      coverEl.style.backgroundPosition = 'center center';
      coverEl.style.backgroundColor = '#0d0d1a';
      coverEl.style.filter = '';
      coverEl.style.transform = '';
      coverEl.innerHTML = '';
    } else {
      coverEl.style.backgroundImage = '';
      coverEl.style.backgroundSize = '';
      coverEl.style.backgroundPosition = '';
      coverEl.style.backgroundColor = '#16213e';
      const initials = item.title.split(' ').slice(0, 2).map(function(w) { return w[0] || ''; }).join('').toUpperCase();
      coverEl.innerHTML = '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:64px;font-weight:900;color:#31324d;letter-spacing:-2px">' + initials + '</div>';
    }

    // Cover upload
    const coverInput = document.getElementById('cover-file-input');
    if (coverInput) {
      coverInput.value = '';
      coverInput.onchange = async function(e) {
        const file = e.target.files[0];
        if (!file) return;
        const fd = new FormData();
        fd.append('file', file);
        try {
          const r = await fetch('/api/content/' + id + '/cover', { method: 'POST', body: fd });
          const d = await r.json();
          coverEl.style.backgroundImage = 'url(' + d.cover_url + '?' + Date.now() + ')';
          coverEl.style.backgroundSize = 'auto 100%';
          coverEl.style.backgroundPosition = 'center center';
          coverEl.style.backgroundColor = '#0d0d1a';
          renderHome();
        } catch (err) { showToast('Cover yüklenemedi: ' + err.message, 'error'); }
      };
    }

    // Mark butonu
    if (markBtn && !isGame) {
      markBtn.onclick = async function() {
        const btn = this;
        if (btn.disabled) return;
        const next = (item.my_progress || 0) + 1;
        if (total > 0 && next > total) return;
        btn.disabled = true;
        const origHTML = btn.innerHTML;
        btn.innerHTML = '<span class="material-symbols-outlined" style="animation:spin .8s linear infinite">progress_activity</span>';
        try {
          item.my_progress = next;
          await apiPost('/api/content/' + id + '/progress', { progress: next });
          if (total > 0 && next >= total) {
            const updated = await apiGet('/api/content/' + id);
            _showCompleteModal(id, item.title || '', updated.my_score);
          } else {
            renderDetail(id);
          }
        } catch(e) {
          btn.disabled = false;
          btn.innerHTML = origHTML;
          showToast('İşaretlenemedi: ' + e.message, 'error');
        }
      };
    }

    // Slider değişimi
    slider.oninput = function() {
      const v = parseInt(this.value, 10);
      if (isGame) {
        document.getElementById('detail-progress-current').textContent = v + '%';
        document.getElementById('detail-progress-pct').textContent = v + '%';
        document.getElementById('detail-progress-bar').style.width = v + '%';
      } else {
        document.getElementById('detail-progress-current').textContent = v;
        const newPct = total > 0 ? Math.round(v / total * 100) : 0;
        document.getElementById('detail-progress-pct').textContent = newPct + '%';
        document.getElementById('detail-progress-bar').style.width = newPct + '%';
      }
    };
    slider.onchange = function() {
      const v = parseInt(this.value, 10);
      if (isGame) {
        item.my_progress_pct = v;
        apiPatch('/api/content/' + id, { my_progress_pct: v });
      } else {
        item.my_progress = v;
        apiPost('/api/content/' + id + '/progress', { progress: v });
      }
    };

    // Quick-edit pop-up (mobil ilerleme düzenleme)
    const tapBtn  = document.getElementById('detail-progress-tap');
    const qeInput = document.getElementById('pqe-input');
    if (tapBtn && qePanel && qeInput) {
      tapBtn.onclick = function(e) {
        e.stopPropagation();
        const open = qePanel.style.display !== 'none';
        qePanel.style.display = open ? 'none' : '';
        if (!open) { qeInput.value = isGame ? (item.my_progress_pct || 0) : (item.my_progress || 0); qeInput.focus(); }
      };
      document.getElementById('pqe-minus').onclick = function() { qeInput.value = Math.max(0, parseInt(qeInput.value || 0, 10) - 1); };
      document.getElementById('pqe-plus').onclick  = function() { qeInput.value = parseInt(qeInput.value || 0, 10) + 1; };
      document.getElementById('pqe-save').onclick  = async function() {
        const v = parseInt(qeInput.value, 10);
        if (isNaN(v) || v < 0) return;
        qePanel.style.display = 'none';
        if (isGame) {
          item.my_progress_pct = v;
          await apiPatch('/api/content/' + id, { my_progress_pct: v });
        } else {
          item.my_progress = v;
          await apiPost('/api/content/' + id + '/progress', { progress: v });
        }
        renderDetail(id);
      };
      document.addEventListener('click', function closeQe(e) {
        if (!qePanel.contains(e.target) && e.target !== tapBtn && !tapBtn.contains(e.target)) {
          qePanel.style.display = 'none';
          document.removeEventListener('click', closeQe);
        }
      });
    }

    // Bölümler tab
    const epsTabEl = document.getElementById('detail-tab-episodes');
    if (epsTabEl) renderDetailEpisodes(epsTabEl, item.episodes || [], id, item.type, item.title, item.sites || [], item.my_progress || 0);

    // Siteler tab
    const sitesTabEl = document.getElementById('detail-tab-sites');
    if (sitesTabEl) renderDetailSites(sitesTabEl, item.sites || [], id);

    // Notlar tab
    const notesArea = document.getElementById('detail-notes-area');
    if (notesArea) {
      notesArea.value = item.note_text || '';
      const isSpoiler = !!item.note_is_spoiler;
      notesArea.classList.toggle('blur-sm', isSpoiler);
      const overlay = document.getElementById('detail-spoiler-overlay');
      if (overlay) overlay.style.display = isSpoiler ? 'flex' : 'none';
      const spoilerToggle = document.getElementById('detail-spoiler-toggle');
      if (spoilerToggle) {
        spoilerToggle.checked = isSpoiler;
        spoilerToggle.onchange = function() {
          apiPatch('/api/content/' + id, { note_is_spoiler: this.checked }).catch(function() {});
        };
      }
      clearTimeout(notesArea._saveTimer);
      notesArea.oninput = function() {
        clearTimeout(this._saveTimer);
        this._saveTimer = setTimeout(function() {
          apiPatch('/api/content/' + id, { note_text: notesArea.value }).catch(function() {});
        }, 1000);
      };
    }

    // Genres badge'leri
    const genresRow = document.getElementById('detail-genres-row');
    if (genresRow) {
      const genres = item.genres || [];
      if (genres.length) {
        genresRow.classList.remove('hidden');
        genresRow.classList.add('flex');
        genresRow.innerHTML = genres.map(function(g) {
          return '<span class="px-3 py-1 rounded-full text-[11px] font-bold bg-[#00d4ff]/10 text-[#00d4ff] border border-[#00d4ff]/30">' + escapeHtml(genreTR(g)) + '</span>';
        }).join('');
      } else {
        genresRow.classList.add('hidden');
        genresRow.classList.remove('flex');
      }
    }

    renderDetailTags(id, item.tags || []);

    // ── AniList: Synopsis + nextAiringEpisode ─────────────────────
    const synSec    = document.getElementById('detail-synopsis-section');
    const naeEl     = document.getElementById('detail-next-airing');
    const naeTxt    = document.getElementById('detail-next-airing-text');
    const synWrap   = document.getElementById('detail-synopsis-wrap');
    const synEl     = document.getElementById('detail-synopsis-text');
    const synToggle = document.getElementById('detail-synopsis-toggle');

    // Reset
    if (synSec)    synSec.style.display    = 'none';
    if (naeEl)     naeEl.style.display     = 'none';
    if (synWrap)   synWrap.style.display   = 'none';
    if (synToggle) synToggle.style.display = 'none';
    if (synEl)     synEl.style.webkitLineClamp = '3';

    // DB'den synopsis varsa hemen göster (TR önce, yoksa EN)
    function _showSynopsis(text) {
      if (!text || !synEl || !synWrap) return false;
      synEl.textContent = text;
      synWrap.style.display = 'flex';
      if (synSec) synSec.style.display = '';
      if (text.length > 200 && synToggle) {
        synEl.style.webkitLineClamp = '3';
        synEl.style.overflow = 'hidden';
        synToggle.style.display = '';
        var expanded = false;
        synToggle.textContent = 'Devamını Gör';
        synToggle.onclick = function() {
          expanded = !expanded;
          synEl.style.webkitLineClamp = expanded ? 'unset' : '3';
          synEl.style.overflow = expanded ? 'visible' : 'hidden';
          synEl.style.display = expanded ? 'block' : '-webkit-box';
          synToggle.textContent = expanded ? 'Daha Az Göster' : 'Devamını Gör';
        };
      } else if (synToggle) { synToggle.style.display = 'none'; }
      return true;
    }

    var _synShown = _showSynopsis(item.synopsis_tr || item.synopsis);

    if (item.external_id) {
      apiGet('/api/content/' + id + '/anilist').then(function(al) {
        var showSection = false;

        // nextAiringEpisode
        if (al.next_airing_episode && naeEl && naeTxt) {
          var ms = al.next_airing_episode.airing_at * 1000 - Date.now();
          if (ms > 0) {
            var days  = Math.floor(ms / 86400000);
            var hours = Math.floor((ms % 86400000) / 3600000);
            var mins  = Math.floor((ms % 3600000) / 60000);
            var timeStr;
            if (days > 0)       timeStr = days + ' gün' + (hours > 0 ? ' ' + hours + ' saat' : '') + ' sonra';
            else if (hours > 0) timeStr = hours + ' saat ' + mins + ' dk sonra';
            else                timeStr = mins + ' dk sonra';
            naeTxt.textContent = 'Bölüm ' + al.next_airing_episode.episode + ' — ' + timeStr + ' yayınlanıyor';
            naeEl.style.display = 'flex';
            showSection = true;
          }
        }

        // Synopsis — DB'de yoksa AniList'ten göster
        if (!_synShown && al.synopsis && synEl && synWrap) {
          var tmp = document.createElement('div');
          tmp.innerHTML = al.synopsis;
          var text = (tmp.textContent || tmp.innerText || '').trim();
          if (text) {
            synEl.textContent = text;
            synWrap.style.display = 'flex';
            showSection = true;
            if (text.length > 200 && synToggle) {
              synEl.style.webkitLineClamp = '3';
              synEl.style.overflow = 'hidden';
              synToggle.style.display = '';
              var expanded = false;
              synToggle.textContent = 'Devamını Gör';
              synToggle.onclick = function() {
                expanded = !expanded;
                if (expanded) {
                  synEl.style.webkitLineClamp = 'unset';
                  synEl.style.overflow = 'visible';
                  synEl.style.display = 'block';
                  synToggle.textContent = 'Daha Az Göster';
                } else {
                  synEl.style.webkitLineClamp = '3';
                  synEl.style.overflow = 'hidden';
                  synEl.style.display = '-webkit-box';
                  synToggle.textContent = 'Devamını Gör';
                }
              };
            } else {
              synEl.style.webkitLineClamp = 'unset';
              synEl.style.overflow = 'visible';
              synEl.style.display = 'block';
            }
          }
        }

        if (showSection && synSec) synSec.style.display = 'flex';

        // Karakterler tab: al.characters varsa render et
        var charTab = document.getElementById('detail-tab-characters');
        if (charTab && al.characters && al.characters.length > 0) {
          charTab.innerHTML = '<div class="flex overflow-x-auto gap-4 pb-2 hide-scrollbar">' +
            al.characters.map(function(ch) {
              var imgHtml = ch.image
                ? '<img src="' + escapeHtml(ch.image) + '" class="w-full h-full object-cover rounded-full" loading="lazy"/>'
                : '<span class="text-[#00d4ff] font-bold text-lg">' + escapeHtml((ch.name||'?').slice(0,2)) + '</span>';
              var roleLabel = ch.role === 'MAIN' ? '★ Baş Rol' : ch.role === 'SUPPORTING' ? 'Yan Rol' : (ch.role || '');
              var vaHtml = ch.voice_actor ? '<p class="text-[#9090b0] text-[9px] truncate">' + escapeHtml(ch.voice_actor) + '</p>' : '';
              return '<div class="flex flex-col items-center gap-2 flex-shrink-0" style="width:76px">' +
                '<div class="w-16 h-16 rounded-full border-2 flex items-center justify-center overflow-hidden" style="border-color:' + (ch.role==='MAIN'?'#00d4ff':'#3c494e') + ';background:#16213e">' +
                imgHtml + '</div>' +
                '<div class="text-center w-full">' +
                '<p class="text-[11px] font-bold text-[#e1e0ff] truncate leading-tight">' + escapeHtml(ch.name||'') + '</p>' +
                '<p class="text-[9px] text-[#00d4ff] font-bold uppercase tracking-wider">' + escapeHtml(roleLabel) + '</p>' +
                vaHtml + '</div></div>';
            }).join('') + '</div>';
        } else if (charTab) {
          charTab.innerHTML = '<p class="text-center text-[#9090b0] py-8 text-[13px]">Karakter bilgisi bulunamadı.</p>';
        }
      }).catch(function() {});
    } else if (_synShown && synSec) {
      synSec.style.display = 'flex';
    }

    // ── Sezon Tabları ─────────────────────────────────────────────
    (function() {
      var seasonBar  = document.getElementById('detail-season-bar');
      var seasonTabs = document.getElementById('detail-season-tabs');
      if (!seasonBar || !seasonTabs) return;
      seasonBar.style.display = 'none';
      seasonTabs.innerHTML = '';
      apiGet('/api/content/' + id + '/seasons').then(function(seasons) {
        if (!seasons || seasons.length <= 1) return;
        seasonBar.style.display = '';
        seasonTabs.innerHTML = '';
        seasons.forEach(function(s) {
          var btn = document.createElement('button');
          var isCurrent = s.id === id;
          btn.style.cssText = [
            'flex-shrink:0',
            'padding:4px 14px',
            'border-radius:20px',
            'font-size:12px',
            'font-weight:700',
            'border:1px solid',
            isCurrent
              ? 'background:#00d4ff1a;border-color:#00d4ff;color:#00d4ff'
              : 'background:transparent;border-color:#ffffff22;color:#9090b0',
          ].join(';');
          btn.textContent = 'S' + (s.season_number || 1);
          btn.title = s.title || '';
          if (!isCurrent) {
            btn.addEventListener('click', function() { renderDetail(s.id); });
          }
          seasonTabs.appendChild(btn);
        });
      }).catch(function() {});
    })();

    // ── Edit butonu bağla ─────────────────────────────────────────
    const editBtn = document.getElementById('detail-edit-btn');
    if (editBtn) {
      editBtn.onclick = function() { openEditModal(item); };
    }

    // HATA-14: Her renderDetail'de tab'ı episodes'a sıfırla
    detailSwitchTab('episodes');
  }

  // ── Detail Tab Geçişi (global scope — inline onclick'ten de çağrılıyor) ──
  function detailSwitchTab(tabId) {
    const tabs = ['episodes','characters','sites','notes'];
    const matchMap = { episodes:'böl', characters:'karak', sites:'site', notes:'not' };
    const buttons = document.querySelectorAll('#screen-detail .sticky.top-0 button');
    buttons.forEach(function(btn) {
      const isActive = btn.textContent.toLowerCase().includes(matchMap[tabId] || tabId);
      btn.classList.toggle('text-[#00d4ff]', isActive);
      btn.classList.toggle('border-[#00d4ff]', isActive);
      btn.classList.toggle('text-[#9090b0]', !isActive);
      btn.classList.toggle('border-transparent', !isActive);
    });
    tabs.forEach(function(t) {
      const el = document.getElementById('detail-tab-' + t);
      if (!el) return;
      if (t === tabId) { el.classList.remove('hidden'); el.classList.add('flex'); }
      else { el.classList.add('hidden'); el.classList.remove('flex'); }
    });
  }
  window.detailSwitchTab = detailSwitchTab;

  // ── Edit Modal ───────────────────────────────────────────────────
  function openEditModal(item) {
    const modal = document.getElementById('modal-edit');
    if (!modal) return;

    // Form doldur
    const titleInput = document.getElementById('edit-form-title');
    if (titleInput) titleInput.value = item.title || '';

    const titleTrInput = document.getElementById('edit-form-title-tr');
    if (titleTrInput) titleTrInput.value = item.title_tr || '';

    const statusSel = document.getElementById('edit-form-status');
    if (statusSel) statusSel.value = item.status || 'watching';

    const scoreSlider = document.getElementById('edit-form-score');
    const scoreDisp   = document.getElementById('edit-score-display');
    const sc = item.my_score || 0;
    if (scoreSlider) scoreSlider.value = sc;
    if (scoreDisp) scoreDisp.innerHTML = (sc > 0 ? sc : '—') + ' <span class="text-[#9090b0] text-[11px]">/ 10</span>';

    const noteArea = document.getElementById('edit-form-note');
    if (noteArea) noteArea.value = item.note_text || '';

    // Tip butonları
    document.querySelectorAll('.edit-type-btn').forEach(function(btn) {
      const isActive = btn.dataset.editType === item.type;
      btn.className = btn.className.replace(/bg-\[#1a2123\]|text-\[#00d4ff\]|border\s+border-\[#3c494e\]\/50|text-\[#9090b0\]/g, '').trim();
      if (isActive) {
        btn.style.background = '#1a2123';
        btn.style.color = '#00d4ff';
        btn.style.border = '1px solid rgba(60,73,78,0.5)';
      } else {
        btn.style.background = '';
        btn.style.color = '#9090b0';
        btn.style.border = '';
      }
    });

    // Kaydet
    const saveBtn = document.getElementById('edit-save-btn');
    if (saveBtn) {
      saveBtn.onclick = async function() {
        const btn = this;
        btn.disabled = true;
        const origHtml = btn.innerHTML;
        btn.innerHTML = '<span class="material-symbols-outlined" style="animation:spin .8s linear infinite">progress_activity</span>';
        try {
          const scoreVal = parseInt(document.getElementById('edit-form-score').value, 10);
          const titleTrEl = document.getElementById('edit-form-title-tr');
          const patchBody = {
            title:     (document.getElementById('edit-form-title').value || '').trim(),
            title_tr:  titleTrEl ? (titleTrEl.value || '').trim() : undefined,
            status:    document.getElementById('edit-form-status').value,
            note_text: document.getElementById('edit-form-note').value,
          };
          if (scoreVal > 0) patchBody.my_score = scoreVal;
          await apiPatch('/api/content/' + item.id, patchBody);
          closeModal('modal-edit');
          await renderDetail(item.id);
          renderHome();
          showToast('Kaydedildi', 'success');
        } catch (e) {
          showToast('Kaydedilemedi: ' + e.message, 'error');
        } finally {
          btn.disabled = false;
          btn.innerHTML = origHtml;
        }
      };
    }

    // Sil
    const delBtn = document.getElementById('edit-delete-btn');
    if (delBtn) {
      delBtn.onclick = async function() {
        if (!confirm('"' + item.title + '"\n\nBu içeriği kütüphaneden silmek istiyor musun?')) return;
        try {
          await apiDelete('/api/content/' + item.id);
          closeModal('modal-edit');
          showScreen('screen-home');
          renderHome();
          showToast('"' + item.title + '" silindi', 'success');
        } catch (e) {
          showToast('Silinemedi: ' + e.message, 'error');
        }
      };
    }

    // Tip butonu onclick
    document.querySelectorAll('.edit-type-btn').forEach(function(btn) {
      btn.onclick = function() {
        document.querySelectorAll('.edit-type-btn').forEach(function(b) {
          b.style.background = ''; b.style.color = '#9090b0'; b.style.border = '';
        });
        this.style.background = '#1a2123';
        this.style.color = '#00d4ff';
        this.style.border = '1px solid rgba(60,73,78,0.5)';
      };
    });

    openModal('modal-edit');
  }

  // ── Render: Updates v7 ───────────────────────────────────────────
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
      list.innerHTML = '<div class="text-center text-[#9090b0] py-12 flex flex-col items-center gap-3">' +
        '<span class="material-symbols-outlined" style="font-size:48px;opacity:0.4">notifications_off</span>' +
        '<p class="text-[14px] font-medium">Yeni güncelleme yok</p>' +
        '<p class="text-[12px] opacity-60">Kontrol Et butonuna basarak yeni bölümleri tara</p>' +
        '</div>';
      return;
    }

    // Zaman grupları
    const groups = { 'Bugün': [], 'Dün': [], 'Bu Hafta': [], 'Daha Önce': [] };
    const now = new Date();
    items.forEach(function(u) {
      const diff = Math.floor((now - new Date(u.detected_at)) / 86400000);
      if      (diff === 0) groups['Bugün'].push(u);
      else if (diff === 1) groups['Dün'].push(u);
      else if (diff < 7)   groups['Bu Hafta'].push(u);
      else                 groups['Daha Önce'].push(u);
    });

    const TYPE_BADGE = {
      anime:  { bg: 'rgba(0,212,255,0.1)',     color: '#00d4ff', label: 'Anime'  },
      manga:  { bg: 'rgba(255,217,161,0.1)',    color: '#ffd9a1', label: 'Manga'  },
      manhwa: { bg: 'rgba(187,197,235,0.12)',   color: '#bbc5eb', label: 'Manhwa' },
      game:   { bg: 'rgba(255,180,171,0.12)',   color: '#ffb4ab', label: 'Oyun'   },
    };

    function _card(u) {
      const badge   = TYPE_BADGE[u.content_type] || TYPE_BADGE.anime;
      const time    = formatRelativeTime(u.detected_at);
      const initials = u.content_title.split(' ').slice(0,2).map(function(w){return w[0];}).join('').toUpperCase();
      const cover   = u.content_cover_url
        ? '<img src="' + escapeHtml(u.content_cover_url) + '" class="w-full h-full object-cover" loading="lazy"/>'
        : '<span class="font-bold text-sm" style="color:' + badge.color + '">' + escapeHtml(initials) + '</span>';
      const epText  = 'Bölüm ' + u.episode_number + ' yayınlandı';

      const coverBox = '<div class="w-[56px] h-[80px] shrink-0 rounded-lg overflow-hidden border border-white/5 relative flex items-center justify-center" style="background:#16213e">' +
        cover + '<div class="absolute bottom-0 left-0 w-full h-1/2 pointer-events-none" style="background:linear-gradient(to top,rgba(0,0,0,0.8),transparent)"></div></div>';

      if (u.is_read) {
        return '<div class="flex items-center gap-3 p-3 rounded-xl transition-all cursor-pointer active:scale-[0.98] opacity-60"' +
          ' style="background:rgba(26,26,46,0.3);border-left:3px solid transparent" data-content-id="' + u.content_id + '">' +
          coverBox +
          '<div class="flex-1 space-y-1 min-w-0">' +
          '<div class="flex justify-between items-center">' +
          '<span class="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded" style="background:rgba(255,255,255,0.05);color:#9090b0">' + badge.label + '</span>' +
          '<span class="text-[10px] text-[#9090b0] font-medium">' + time + '</span></div>' +
          '<h3 class="text-[15px] font-semibold truncate" style="color:rgba(255,255,255,0.7)">' + escapeHtml(u.content_title) + '</h3>' +
          '<p class="text-[12px]" style="color:#9090b0">' + epText + '</p>' +
          '<div class="flex gap-2 pt-1">' +
          '<button class="details-btn px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase active:scale-95 transition-all min-h-[36px]"' +
          ' style="background:rgba(255,255,255,0.1);color:#dde3e7" data-content-id="' + u.content_id + '">' +
          'DETAYLAR</button></div></div></div>';
      }

      const actionLabel = (u.content_type === 'anime') ? 'İZLE' : 'OKU';
      return '<div class="flex items-center gap-3 p-3 rounded-xl transition-all cursor-pointer active:scale-[0.98] shadow-[0_4px_12px_rgba(0,0,0,0.4)]"' +
        ' style="background:rgba(26,26,46,0.6);border-left:4px solid #00d4ff" data-content-id="' + u.content_id + '">' +
        coverBox +
        '<div class="flex-1 space-y-1 min-w-0">' +
        '<div class="flex justify-between items-center">' +
        '<span class="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded" style="background:' + badge.bg + ';color:' + badge.color + '">' + badge.label + '</span>' +
        '<span class="text-[10px] font-medium" style="color:' + badge.color + '">' + time + '</span></div>' +
        '<h3 class="text-[15px] font-semibold text-white truncate">' + escapeHtml(u.content_title) + '</h3>' +
        '<p class="text-[12px]" style="color:#9090b0">' + epText + '</p>' +
        '<div class="flex gap-2 pt-1">' +
        '<button class="action-btn px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase active:scale-95 transition-all min-h-[36px]"' +
        ' style="background:#00d4ff;color:#003642;box-shadow:0 0 12px rgba(0,212,255,0.3)" data-content-id="' + u.content_id + '">' +
        actionLabel + '</button>' +
        '<button class="read-btn px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase active:scale-95 transition-all min-h-[36px]"' +
        ' style="background:rgba(255,255,255,0.05);color:#9090b0" data-update-id="' + u.id + '">' +
        'GÖRDÜM</button></div></div></div>';
    }

    const ORDER = ['Bugün', 'Dün', 'Bu Hafta', 'Daha Önce'];
    list.innerHTML = ORDER.filter(function(g) { return groups[g].length > 0; }).map(function(g) {
      return '<section class="space-y-3">' +
        '<h2 class="text-[10px] font-bold uppercase tracking-widest px-1" style="color:#9090b0">' + g + '</h2>' +
        groups[g].map(_card).join('') +
        '</section>';
    }).join('');

    if (!list._v7ListenerAttached) {
      list._v7ListenerAttached = true;
      list.addEventListener('click', function(e) {
        const readBtn = e.target.closest('.read-btn');
        if (readBtn) {
          e.stopPropagation();
          const uid = readBtn.dataset.updateId;
          if (uid) apiPatch('/api/updates/' + uid + '/read', {}).then(function() { renderUpdates(); }).catch(function(){});
          return;
        }
        const card = e.target.closest('[data-content-id]');
        if (card) {
          const id = parseInt(card.dataset.contentId, 10);
          if (id) { renderDetail(id); showScreen('screen-detail'); }
        }
      });
    }
  }

  // ── Updates: Kontrol Et ──────────────────────────────────────────
  async function runCheckUpdates() {
    const btn = document.getElementById('updates-check-btn');
    if (!btn || btn.disabled) return;
    btn.disabled = true;
    btn.innerHTML = '<span class="material-symbols-outlined animate-spin text-sm">progress_activity</span> Kontrol ediliyor...';
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 90000);
      const r = await fetch(API_BASE + '/api/check-updates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
        signal: ctrl.signal,
      });
      clearTimeout(timer);
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const res = await r.json();
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
  function showToast(msg, type, durationMs) {
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
    }, durationMs || 3000);
  }
  window.showToast = showToast;

  // ── Render: Stats v7 ─────────────────────────────────────────────
  async function renderStats() {
    let items;
    try { items = await apiGet('/api/content'); }
    catch (err) { console.error('renderStats', err); return; }

    const total = items.length || 1;

    // ── Bento sayılar ─────────────────────────────────────────────
    const countEl = document.getElementById('stats-library-count');
    if (countEl) countEl.textContent = items.length;

    const completed = items.filter(function(i) { return i.status === 'completed'; }).length;
    const completedEl = document.getElementById('stats-completed');
    if (completedEl) completedEl.textContent = completed;

    const scored = items.filter(function(i) { return i.my_score != null; });
    const avg = scored.length
      ? (scored.reduce(function(s, i) { return s + i.my_score; }, 0) / scored.length).toFixed(1)
      : '—';
    const avgEl = document.getElementById('stats-avg-score');
    if (avgEl) avgEl.textContent = avg;

    const hoursEl = document.getElementById('stats-hours');
    if (hoursEl) {
      let totalMins = 0;
      items.forEach(function(it) {
        if (it.type === 'anime')       totalMins += (it.my_progress || 0) * 24;
        else if (it.type === 'manga')  totalMins += (it.my_progress || 0) * 5;
        else if (it.type === 'manhwa') totalMins += (it.my_progress || 0) * 3;
      });
      hoursEl.textContent = Math.round(totalMins / 60).toLocaleString('tr-TR') + 's';
    }

    // ── Donut chart ───────────────────────────────────────────────
    const CIRC = 251.33;
    const TYPE_LABELS = { anime: 'Anime', manga: 'Manga', manhwa: 'Manhwa', game: 'Oyun' };
    const typeCounts = { anime: 0, manga: 0, manhwa: 0, game: 0 };
    items.forEach(function(it) { if (it.type in typeCounts) typeCounts[it.type]++; });
    const typeKeys  = ['anime', 'manga', 'manhwa', 'game'];
    const donutIds  = ['stat-donut-anime', 'stat-donut-manga', 'stat-donut-manhwa', 'stat-donut-game'];
    let donutOffset = 0;
    donutIds.forEach(function(id, i) {
      const el = document.getElementById(id);
      if (!el) return;
      const count = typeCounts[typeKeys[i]];
      const dash = count > 0 ? Math.max(2, (count / total) * CIRC) : 0;
      el.setAttribute('stroke-dasharray', dash.toFixed(1) + ' ' + CIRC);
      el.setAttribute('stroke-dashoffset', (-donutOffset).toFixed(1));
      donutOffset += dash;
    });
    const topType = typeKeys.reduce(function(a, b) { return typeCounts[a] >= typeCounts[b] ? a : b; });
    const topPct  = Math.round((typeCounts[topType] / total) * 100);
    const centerPct  = document.getElementById('stat-donut-center-pct');
    const centerType = document.getElementById('stat-donut-center-type');
    if (centerPct)  centerPct.textContent  = topPct + '%';
    if (centerType) centerType.textContent = TYPE_LABELS[topType] || topType;

    // ── CSS bar'lar (Platform Kullanımı = tip dağılımı) ───────────
    const barTypes = [
      { key: 'anime',  barId: 'stats-bar-anime',  pctId: 'stats-pct-anime'  },
      { key: 'manga',  barId: 'stats-bar-manga',  pctId: 'stats-pct-manga'  },
      { key: 'manhwa', barId: 'stats-bar-manhwa', pctId: 'stats-pct-manhwa' },
    ];
    barTypes.forEach(function(t) {
      const pct = Math.round((typeCounts[t.key] / total) * 100);
      const barEl = document.getElementById(t.barId);
      const pctEl = document.getElementById(t.pctId);
      if (barEl) barEl.style.width = pct + '%';
      if (pctEl) pctEl.textContent = pct + '%';
    });

    // ── Favori Türler ─────────────────────────────────────────────
    const genreMap = {};
    items.forEach(function(it) {
      (it.genres || []).forEach(function(g) { genreMap[g] = (genreMap[g] || 0) + 1; });
    });
    const genresEl = document.getElementById('stats-genres');
    if (genresEl) {
      const sorted = Object.entries(genreMap).sort(function(a, b) { return b[1] - a[1]; }).slice(0, 8);
      if (sorted.length === 0) {
        genresEl.innerHTML = '<span class="text-[11px] text-[#9090b0]">Henüz tür verisi yok</span>';
      } else {
        const colors = ['#00d4ff', '#ffd9a1', '#bbc5eb', '#ffb4ab', '#90e090', '#ff9a3c', '#a0a0d0', '#9090b0'];
        genresEl.innerHTML = sorted.map(function(entry, i) {
          const c = colors[i] || '#9090b0';
          return '<span class="px-3 py-1.5 rounded-lg text-[10px] font-bold cursor-pointer"' +
            ' style="background:' + c + '18;color:' + c + ';border:1px solid ' + c + '30">' +
            escapeHtml(genreTR(entry[0])) + ' <span style="opacity:0.6">(' + entry[1] + ')</span></span>';
        }).join('');
      }
    }
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
              <span class="font-bold text-[14px] text-[#e1e0ff] truncate">${escapeHtml(it.title_tr || it.title)}</span>
              <span class="text-[10px] font-bold px-1 py-[2px] rounded uppercase tracking-wider" style="${tcStyle(tc).badge}">${tc.label}</span>
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

    // MAL input
    const malClientId = document.getElementById('settings-mal-client-id');
    if (malClientId) malClientId.value = cfg.mal_client_id || '';

    // Kayıtlı olmayan kimlik bilgilerini otomatik kaydet
    (async function _seedCredentials() {
      const patch = {};
      if (!cfg.igdb_client_id) patch.igdb_client_id = 'c9p2endd78aknjq52x9qx7o4voupqn';
      if (!cfg.mal_client_id)  patch.mal_client_id  = '7bf9dbc0538aefb6eb465ca9ef04c8bb';
      if (Object.keys(patch).length) {
        try { await apiPost('/api/settings', patch); } catch(e) {}
        if (igdbId && patch.igdb_client_id) igdbId.value = patch.igdb_client_id;
        if (malClientId && patch.mal_client_id) malClientId.value = patch.mal_client_id;
      }
    })();

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

    // Kalite butonları (manual + auto iki ayrı grup)
    function _makeQualityGroup(selector, settingKey, initialVal) {
      const btns = document.querySelectorAll(selector);
      function setActive(q) {
        btns.forEach(b => {
          const active = b.dataset.quality === q;
          b.classList.toggle('bg-[#0d0d1a]', active);
          b.classList.toggle('border', active);
          b.classList.toggle('border-white\\/5', active);
          b.classList.toggle('shadow-sm', active);
          b.style.color = active ? '#00d4ff' : '';
          if (!active) b.style.color = '';
        });
        btns.forEach(b => { b.style.color = b.dataset.quality === q ? '#00d4ff' : '#9090b0'; });
      }
      setActive(initialVal || '720p');
      btns.forEach(btn => {
        btn.addEventListener('click', async function() {
          cfg[settingKey] = this.dataset.quality;
          setActive(cfg[settingKey]);
          await apiPost('/api/settings', { [settingKey]: cfg[settingKey] });
        });
      });
    }
    _makeQualityGroup('.settings-quality-manual-btn', 'download_quality_manual', cfg.download_quality_manual || cfg.default_quality || '720p');
    _makeQualityGroup('.settings-quality-auto-btn',   'download_quality_auto',   cfg.download_quality_auto   || '480p');

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

    // MAL kaydet butonu
    const malSecret = document.getElementById('settings-mal-client-secret');
    const malSecretBadge = document.getElementById('settings-mal-secret-badge');
    if (cfg.mal_client_secret) {
      if (malSecret) malSecret.placeholder = '••••••••••••••••••••••••••••••••';
      if (malSecretBadge) malSecretBadge.classList.remove('hidden');
    } else {
      if (malSecretBadge) malSecretBadge.classList.add('hidden');
    }
    const malSaveBtn = document.getElementById('settings-mal-save');
    if (malSaveBtn) {
      malSaveBtn.onclick = async function() {
        try {
          const patch = { mal_client_id: malClientId ? malClientId.value.trim() : '' };
          if (malSecret && malSecret.value.trim()) patch.mal_client_secret = malSecret.value.trim();
          await apiPost('/api/settings', patch);
          this.textContent = 'Kaydedildi ✓';
          setTimeout(() => { this.textContent = 'Kaydet'; }, 2000);
        } catch(e) { alert('Kayıt hatası: ' + e.message); }
      };
    }

    // Versiyon
    const verEl = document.getElementById('settings-version');
    if (verEl) verEl.textContent = 'v0.3.0 — Medya Takip Uygulaması';

    // Uygulamayı Güncelle butonu
    const updateBtn = document.getElementById('settings-update-btn');
    if (updateBtn) {
      updateBtn.onclick = async function() {
        this.disabled = true;
        this.innerHTML = '<span class="material-symbols-outlined text-[16px] animate-spin">progress_activity</span> Kontrol...';
        try {
          if ('serviceWorker' in navigator) {
            const reg = await navigator.serviceWorker.getRegistration();
            if (reg) await reg.update();
          }
          location.reload();
        } catch(e) {
          location.reload();
        }
      };
    }

    // Türleri AniList'ten Güncelle butonu
    const genresPatchBtn = document.getElementById('settings-genres-patch-btn');
    if (genresPatchBtn) {
      genresPatchBtn.onclick = async function() {
        if (this.disabled) return;
        this.disabled = true;
        const origHTML = this.innerHTML;
        this.innerHTML = '<span class="material-symbols-outlined text-[18px] animate-spin" style="margin-right:8px">progress_activity</span><span>Güncelleniyor...</span><span class="material-symbols-outlined text-[18px]">chevron_right</span>';
        try {
          const res = await apiPost('/api/genres/patch-all', {});
          showToast((res.patched || 0) + ' içeriğe tür eklendi', (res.patched || 0) > 0 ? 'success' : 'info');
        } catch (e) {
          showToast('Hata: ' + e.message, 'error');
        } finally {
          this.disabled = false;
          this.innerHTML = origHTML;
        }
      };
    }

    // Cover Zenginleştir butonu
    const enrichCoversBtn = document.getElementById('settings-enrich-covers-btn');
    if (enrichCoversBtn) {
      enrichCoversBtn.onclick = async function() {
        if (this.disabled) return;
        this.disabled = true;
        const origHTML = this.innerHTML;
        this.innerHTML = '<span class="material-symbols-outlined text-[18px] animate-spin" style="margin-right:8px">progress_activity</span><span>AniList taranıyor...</span><span class="material-symbols-outlined text-[18px]">chevron_right</span>';
        try {
          const res = await apiPost('/api/content/enrich-covers', {});
          const msg = (res.enriched || 0) > 0
            ? (res.enriched) + ' içeriğe cover eklendi'
            : 'Yeni cover bulunamadı (' + (res.failed_count || 0) + ' başarısız)';
          showToast(msg, (res.enriched || 0) > 0 ? 'success' : 'info');
          if ((res.enriched || 0) > 0) renderHome();
        } catch (e) {
          showToast('Hata: ' + e.message, 'error');
        } finally {
          this.disabled = false;
          this.innerHTML = origHTML;
        }
      };
    }

    // Cover Debugger butonu
    const coverDebugBtn = document.getElementById('settings-cover-debug-btn');
    if (coverDebugBtn) {
      coverDebugBtn.onclick = async function() {
        openModal('modal-cover-debug');
        const listEl   = document.getElementById('cover-debug-list');
        const okCount  = document.getElementById('cover-debug-ok-count');
        const misCount = document.getElementById('cover-debug-missing-count');
        if (listEl) listEl.innerHTML = '<div class="text-center text-[#9090b0] py-8">Yükleniyor...</div>';
        try {
          const all = await apiGet('/api/content');
          const missing = all.filter(function(c) { return !c.cover_url; });
          const ok      = all.length - missing.length;
          if (okCount)  okCount.textContent  = ok;
          if (misCount) misCount.textContent = missing.length;
          if (!listEl) return;
          if (missing.length === 0) {
            listEl.innerHTML = '<div class="text-center text-green-400 py-8">Tüm içeriklerin cover\'ı var ✓</div>';
            return;
          }
          const typeIcon = { anime: '▶', manga: '📖', manhwa: '📖', game: '🎮' };
          listEl.innerHTML = missing.map(function(c) {
            return '<div class="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/5">' +
              '<div class="flex items-center gap-2 min-w-0">' +
                '<span class="text-[11px] text-[#9090b0] shrink-0">' + (typeIcon[c.type] || '?') + '</span>' +
                '<span class="text-[13px] text-[#e1e0ff] truncate">' + escapeHtml(c.title) + '</span>' +
              '</div>' +
              '<span class="text-[10px] text-[#9090b0] shrink-0 ml-2">#' + c.id + '</span>' +
            '</div>';
          }).join('');
        } catch(e) {
          if (listEl) listEl.innerHTML = '<div class="text-center text-red-400 py-8">Hata: ' + escapeHtml(e.message) + '</div>';
        }
      };
    }

    // Cookies yönetimi
    async function refreshCookiesList() {
      const listEl = document.getElementById('settings-cookies-list');
      if (!listEl) return;
      try {
        const data = await apiGet('/api/settings/cookies');
        if (!data.files.length) {
          listEl.innerHTML = '<span style="color:#9090b0">Henüz cookies yüklenmedi</span>';
        } else {
          listEl.innerHTML = data.files.map(function(f) {
            return '<div style="display:flex;align-items:center;justify-content:space-between;padding:4px 0">' +
              '<span style="color:#e1e0ff">' + escapeHtml(f.name) + '</span>' +
              '<span style="color:#9090b0;font-size:11px">' + (f.bytes/1024).toFixed(1) + ' KB</span>' +
              '</div>';
          }).join('');
        }
      } catch(e) { listEl.textContent = 'Cookies yüklenirken hata'; }
    }
    refreshCookiesList();
    const cookiesInput = document.getElementById('settings-cookies-input');
    if (cookiesInput) {
      cookiesInput.addEventListener('change', async function() {
        const file = this.files[0];
        if (!file) return;
        const site = (document.getElementById('settings-cookies-site') || {}).value || 'tranimeizle';
        const fd = new FormData();
        fd.append('file', file);
        try {
          const r = await fetch('/api/settings/cookies/' + encodeURIComponent(site), { method: 'POST', body: fd });
          const d = await r.json();
          showToast(d.file + ' yüklendi (' + (d.bytes/1024).toFixed(1) + ' KB)', 'success');
          refreshCookiesList();
        } catch(e) { showToast('Cookie yükleme hatası: ' + e.message, 'error'); }
        this.value = '';
      });
    }

    // CAPTCHA Human-in-the-Loop
    const captchaBtn = document.getElementById('captcha-browser-btn');
    const captchaBox = document.getElementById('captcha-status-box');
    if (captchaBtn && captchaBox) {
      captchaBtn.addEventListener('click', function() {
        const site = (document.getElementById('settings-cookies-site') || {}).value || 'tranimeizle';
        captchaBtn.disabled = true;
        captchaBtn.style.opacity = '0.5';
        captchaBox.className = captchaBox.className.replace('hidden', '');
        captchaBox.style.color = '#9090b0';
        captchaBox.textContent = 'Tarayıcı başlatılıyor...';

        const evtSrc = new EventSource('/api/settings/cookies/captcha/' + encodeURIComponent(site));

        evtSrc.onmessage = function(e) {
          try {
            const d = JSON.parse(e.data);
            const statusColors = {
              starting: '#9090b0',
              open:     '#ffb300',
              waiting:  '#9090b0',
              saving:   '#00d4ff',
              done:     '#4caf50',
              timeout:  '#ff5252',
              error:    '#ff5252',
            };
            captchaBox.style.color = statusColors[d.status] || '#9090b0';
            captchaBox.textContent = d.msg;

            if (d.status === 'done' || d.status === 'timeout' || d.status === 'error') {
              evtSrc.close();
              captchaBtn.disabled = false;
              captchaBtn.style.opacity = '1';
              if (d.status === 'done') {
                showToast('Cookie\'ler kaydedildi!', 'success');
                refreshCookiesList();
              }
            }
          } catch(_) {}
        };

        evtSrc.onerror = function() {
          evtSrc.close();
          captchaBtn.disabled = false;
          captchaBtn.style.opacity = '1';
          captchaBox.style.color = '#ff5252';
          captchaBox.textContent = 'Bağlantı hatası. Backend çalışıyor mu?';
        };
      });
    }

    renderTagSettings();
    renderTagColorPicker();
    if (window.kuroPWA) window.kuroPWA.initPushUI();
    _initMalSync();

    // ── validate-key wiring ───────────────────────────────────────
    const validateResult = document.getElementById('settings-validate-result');
    async function _validateKey(service, key, labelEl) {
      if (!key) { showToast('Key boş', 'error'); return; }
      const origText = labelEl ? labelEl.textContent : '';
      if (labelEl) { labelEl.textContent = '...'; labelEl.disabled = true; }
      try {
        const r = await apiPost('/api/proxy/validate-key', { service, key });
        const color = r.valid ? '#22c55e' : '#ff5252';
        if (validateResult) {
          validateResult.classList.remove('hidden');
          validateResult.style.color = color;
          validateResult.textContent = (r.valid ? '✓ ' : '✗ ') + r.message;
        }
        showToast(r.message, r.valid ? 'success' : 'error');
      } catch(e) {
        showToast('Test hatası: ' + e.message, 'error');
      } finally {
        if (labelEl) { labelEl.textContent = origText; labelEl.disabled = false; }
      }
    }

    const igdbTestBtn = document.getElementById('settings-igdb-test');
    if (igdbTestBtn) {
      igdbTestBtn.onclick = function() {
        const id  = document.getElementById('settings-igdb-id');
        const sec = document.getElementById('settings-igdb-secret');
        const key = (sec && sec.value.trim()) || (id && id.value.trim()) || '';
        _validateKey('igdb', key, igdbTestBtn);
      };
    }

    // ── DeepL key ──────────────────────────────────────────────────
    const deeplKey  = document.getElementById('settings-deepl-key');
    const deeplSave = document.getElementById('settings-deepl-save');
    if (deeplKey) deeplKey.value = cfg.deepl_api_key || '';
    if (deeplSave) {
      deeplSave.onclick = async function() {
        try {
          await apiPost('/api/settings', { deepl_api_key: deeplKey ? deeplKey.value.trim() : '' });
          this.textContent = 'Kaydedildi ✓';
          setTimeout(() => { this.textContent = 'Kaydet'; }, 2000);
        } catch(e) { alert('Kayıt hatası: ' + e.message); }
      };
    }

    // ── Kuro Translate sliders ──────────────────────────────────────
    const fontSlider    = document.getElementById('settings-translate-font');
    const fontVal       = document.getElementById('settings-translate-font-val');
    const opacSlider    = document.getElementById('settings-translate-opacity');
    const opacVal       = document.getElementById('settings-translate-opacity-val');
    if (fontSlider) {
      fontSlider.value = cfg.translate_font_size || 16;
      if (fontVal) fontVal.textContent = fontSlider.value + 'px';
      fontSlider.addEventListener('input', async function() {
        if (fontVal) fontVal.textContent = this.value + 'px';
        await apiPost('/api/settings', { translate_font_size: parseInt(this.value) });
      });
    }
    if (opacSlider) {
      opacSlider.value = cfg.translate_opacity != null ? cfg.translate_opacity : 85;
      if (opacVal) opacVal.textContent = opacSlider.value + '%';
      opacSlider.addEventListener('input', async function() {
        if (opacVal) opacVal.textContent = this.value + '%';
        await apiPost('/api/settings', { translate_opacity: parseInt(this.value) });
      });
    }

    // ── Kuro Translate smart toggle ─────────────────────────────────
    const translateSmartEl = document.getElementById('settings-translate-smart');
    if (translateSmartEl) {
      translateSmartEl.checked = cfg.translate_smart !== false;
      translateSmartEl.addEventListener('change', async function() {
        await apiPost('/api/settings', { translate_smart: this.checked });
      });
    }

    // ── Akıllı Ön-İndirme ──────────────────────────────────────────
    const predownEl = document.getElementById('settings-predownload-toggle');
    if (predownEl) {
      predownEl.checked = cfg.smart_predownload !== false;
      predownEl.addEventListener('change', async function() {
        await apiPost('/api/settings', { smart_predownload: this.checked });
      });
    }

    // ── Threshold counters ──────────────────────────────────────────
    function _makeCounter(minusId, plusId, valId, cfgKey, defaultVal, min, max) {
      let val = cfg[cfgKey] != null ? cfg[cfgKey] : defaultVal;
      const valEl = document.getElementById(valId);
      if (valEl) valEl.textContent = val;
      const minusBtn = document.getElementById(minusId);
      const plusBtn  = document.getElementById(plusId);
      if (minusBtn) minusBtn.addEventListener('click', async function() {
        if (val <= min) return;
        val--;
        if (valEl) valEl.textContent = val;
        cfg[cfgKey] = val;
        await apiPost('/api/settings', { [cfgKey]: val });
      });
      if (plusBtn) plusBtn.addEventListener('click', async function() {
        if (val >= max) return;
        val++;
        if (valEl) valEl.textContent = val;
        cfg[cfgKey] = val;
        await apiPost('/api/settings', { [cfgKey]: val });
      });
    }
    _makeCounter('settings-anime-thresh-minus', 'settings-anime-thresh-plus', 'settings-anime-thresh-val', 'predownload_anime_threshold', 10, 1, 60);
    _makeCounter('settings-manga-thresh-minus', 'settings-manga-thresh-plus', 'settings-manga-thresh-val', 'predownload_manga_threshold', 5, 1, 30);
    _makeCounter('settings-parallel-minus', 'settings-parallel-plus', 'settings-parallel-val', 'parallel_downloads', 3, 1, 10);
    _makeCounter('settings-opening-show-minus', 'settings-opening-show-plus', 'settings-opening-show-val', 'opening_show_time', 85, 0, 300);
    _makeCounter('settings-opening-skip-minus', 'settings-opening-skip-plus', 'settings-opening-skip-val', 'opening_skip_duration', 85, 0, 180);
    _makeCounter('settings-ending-show-minus', 'settings-ending-show-plus', 'settings-ending-show-val', 'ending_show_time', 90, 0, 300);
    _makeCounter('settings-ending-skip-minus', 'settings-ending-skip-plus', 'settings-ending-skip-val', 'ending_skip_duration', 90, 0, 180);

    // ── İndirme Kalitesi dropdown ───────────────────────────────────
    const qualSelect = document.getElementById('settings-quality-select');
    if (qualSelect) {
      qualSelect.value = cfg.download_quality_manual || cfg.default_quality || '720p';
      qualSelect.addEventListener('change', async function() {
        await apiPost('/api/settings', { download_quality_manual: this.value, download_quality_auto: this.value });
      });
    }

    // ── Wi-Fi only ──────────────────────────────────────────────────
    const wifiEl = document.getElementById('settings-wifi-only');
    if (wifiEl) {
      wifiEl.checked = cfg.wifi_only_download === true;
      wifiEl.addEventListener('change', async function() {
        await apiPost('/api/settings', { wifi_only_download: this.checked });
      });
    }

    // ── Opening / Ending toggles ────────────────────────────────────
    const openingToggleEl = document.getElementById('settings-opening-toggle');
    if (openingToggleEl) {
      openingToggleEl.checked = cfg.opening_skip_enabled !== false;
      openingToggleEl.addEventListener('change', async function() {
        await apiPost('/api/settings', { opening_skip_enabled: this.checked });
      });
    }
    const endingToggleEl = document.getElementById('settings-ending-toggle');
    if (endingToggleEl) {
      endingToggleEl.checked = cfg.ending_skip_enabled !== false;
      endingToggleEl.addEventListener('change', async function() {
        await apiPost('/api/settings', { ending_skip_enabled: this.checked });
      });
    }

    // ── Tema seçimi ─────────────────────────────────────────────────
    const themeButtons = document.querySelectorAll('.settings-theme-btn');
    const savedTheme = localStorage.getItem('kurowatch-theme') || 'kuro';
    themeButtons.forEach(btn => {
      const isActive = btn.dataset.theme === savedTheme;
      btn.style.background = isActive ? 'rgba(0,212,255,0.1)' : '';
      btn.style.borderColor = isActive ? 'rgba(0,212,255,0.4)' : 'rgba(255,255,255,0.08)';
      const icon = btn.querySelector('.material-symbols-outlined');
      const circle = btn.querySelector('div.w-6.h-6');
      if (icon) icon.style.display = isActive ? '' : 'none';
      if (circle) circle.style.display = isActive ? 'none' : '';
      btn.addEventListener('click', function() {
        const theme = this.dataset.theme;
        localStorage.setItem('kurowatch-theme', theme);
        themeButtons.forEach(b => {
          const isCur = b.dataset.theme === theme;
          b.style.background = isCur ? 'rgba(0,212,255,0.1)' : '';
          b.style.borderColor = isCur ? 'rgba(0,212,255,0.4)' : 'rgba(255,255,255,0.08)';
          const bi = b.querySelector('.material-symbols-outlined');
          const bc = b.querySelector('div.w-6.h-6');
          if (bi) bi.style.display = isCur ? '' : 'none';
          if (bc) bc.style.display = isCur ? 'none' : '';
        });
      });
    });

    // ── Önbelleği Temizle ───────────────────────────────────────────
    const cacheClearBtn  = document.getElementById('settings-cache-clear-btn');
    const cacheSizeEl    = document.getElementById('settings-cache-size');
    if (navigator.storage && navigator.storage.estimate) {
      navigator.storage.estimate().then(est => {
        if (cacheSizeEl) {
          const mb = ((est.usage || 0) / 1048576).toFixed(1);
          cacheSizeEl.textContent = mb + ' MB kullanılıyor';
        }
      });
    } else if (cacheSizeEl) { cacheSizeEl.textContent = ''; }
    if (cacheClearBtn) {
      cacheClearBtn.addEventListener('click', async function() {
        if ('caches' in window) {
          const keys = await caches.keys();
          await Promise.all(keys.map(k => caches.delete(k)));
        }
        if (cacheSizeEl) cacheSizeEl.textContent = '0 MB kullanılıyor';
      });
    }

    // ── Sezon indirme ───────────────────────────────────────────────
    const seasonDlBtn = document.getElementById('settings-season-download-btn');
    if (seasonDlBtn) {
      seasonDlBtn.addEventListener('click', function() {
        const modal = document.getElementById('modal-add');
        if (modal) modal.classList.remove('hidden');
      });
    }
  }

  // ── MAL OAuth2 Sync ──────────────────────────────────────────────
  async function _initMalSync() {
    const statusLabel    = document.getElementById('mal-status-label');
    const connectBtn     = document.getElementById('mal-connect-btn');
    const importBtn      = document.getElementById('mal-import-btn');
    const disconnectBtn  = document.getElementById('mal-disconnect-btn');
    const importResult   = document.getElementById('mal-import-result');
    if (!connectBtn) return;

    async function _refreshMalStatus() {
      try {
        const s = await apiGet('/api/sync/mal/status');
        if (s.connected) {
          if (statusLabel) statusLabel.textContent = `MAL: @${s.username} ✓`;
          connectBtn.classList.add('hidden');
          importBtn.classList.remove('hidden');
          disconnectBtn.classList.remove('hidden');
        } else {
          if (statusLabel) statusLabel.textContent = 'MAL: Bağlı değil';
          connectBtn.classList.remove('hidden');
          importBtn.classList.add('hidden');
          disconnectBtn.classList.add('hidden');
        }
      } catch {}
    }
    await _refreshMalStatus();

    connectBtn.onclick = async function () {
      try {
        const { auth_url } = await apiGet('/api/sync/mal/auth');
        const popup = window.open(auth_url, 'mal_auth', 'width=600,height=700');
        window.addEventListener('message', async function handler(e) {
          if (e.data === 'mal_connected') {
            window.removeEventListener('message', handler);
            await _refreshMalStatus();
          }
        });
      } catch (e) { alert('Hata: ' + e.message); }
    };

    importBtn.onclick = async function () {
      importBtn.disabled = true;
      importBtn.textContent = 'İçe aktarılıyor...';
      try {
        const r = await apiPost('/api/sync/mal/import', {});
        if (importResult) {
          importResult.classList.remove('hidden');
          importResult.textContent = `✅ ${r.created} yeni eklendi, ${r.updated} güncellendi`;
        }
      } catch (e) {
        if (importResult) { importResult.classList.remove('hidden'); importResult.style.color='#ef4444'; importResult.textContent='❌ Hata: ' + e.message; }
      } finally {
        importBtn.disabled = false;
        importBtn.textContent = '↓ Listemi İçe Aktar';
      }
    };

    disconnectBtn.onclick = async function () {
      await apiDelete('/api/sync/mal/disconnect');
      await _refreshMalStatus();
      if (importResult) importResult.classList.add('hidden');
    };
  }

  // ── Detail Tab Yardımcıları ──────────────────────────────────────

  function renderDetailEpisodes(el, episodes, contentId, contentType, contentTitle, sites, myProgress) {
    const isAnime = contentType === 'anime';
    const readLabel = isAnime ? 'İzle' : 'Oku';
    const readIcon  = isAnime ? 'play_circle' : 'menu_book';
    const syncLabel = 'Bölümleri Güncelle';

    // ── Sezon yönetimi ──
    const allSeasons = episodes.length
      ? [...new Set(episodes.map(function(e) { return e.season || 1; }))].sort(function(a,b){return a-b;})
      : [1];
    let activeSeason = allSeasons[allSeasons.length - 1]; // son sezon varsayılan

    function _buildEpisodeView() {
      const seasonEps = episodes.filter(function(e) { return (e.season || 1) === activeSeason; });

      // En iyi site: ölü değil + en yüksek bölüm sayısı (backend zaten sıralı gönderir)
      const primarySite = (sites || []).find(function(s) { return !s.is_dead; }) || (sites || [])[0];
      // myProgress = izlenen bölüm sayısı. Sıradaki = myProgress+1 (0 ise Bölüm 1'den başla)
      const nextEpNum = myProgress + 1;
      const nextEp = seasonEps.find(function(e) { return e.number === nextEpNum; }) || null;
      const targetUrl = (nextEp && nextEp.url) ? nextEp.url : (primarySite && primarySite.site_url ? primarySite.site_url : null);
      const targetLabel = (nextEp && nextEp.url)
        ? readLabel + ' — Bölüm ' + nextEpNum
        : readLabel + (primarySite ? ' — ' + (function(url) { try { return new URL(url).hostname.replace(/^www\./, ''); } catch(e2) { return escapeHtml(primarySite.site_name); } })(primarySite.site_url) : '');
      const siteShortcut = targetUrl
        ? '<a href="' + escapeHtml(targetUrl) + '" target="_blank" rel="noopener" ' +
          'class="flex items-center justify-center gap-2 w-full rounded-xl font-bold mb-2" ' +
          'style="height:44px;background:#00d4ff1a;border:1px solid #00d4ff4d;color:#00d4ff;font-size:13px;text-decoration:none">' +
          '<span class="material-symbols-outlined" style="font-size:18px">' + readIcon + '</span>' +
          targetLabel + '</a>'
        : '<button class="ep-go-sites-btn flex items-center justify-center gap-2 w-full rounded-xl font-bold mb-2" ' +
          'style="height:44px;background:#31324d;border:1px solid rgba(255,255,255,0.1);color:#9090b0;font-size:13px;cursor:pointer">' +
          '<span class="material-symbols-outlined" style="font-size:18px">add_link</span> ' +
          readLabel + ' için site ekle → Siteler sekmesi</button>';

      // ── Sezon seçici ──
      const seasonPickerHtml = allSeasons.length > 1
        ? '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">' +
          allSeasons.map(function(s) {
            const active = s === activeSeason;
            return '<button class="ep-season-btn" data-season="' + s + '" style="' +
              'padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;cursor:pointer;' +
              'background:' + (active ? '#00d4ff' : '#31324d') + ';' +
              'color:' + (active ? '#0d0d1a' : '#9090b0') + ';' +
              'border:1px solid ' + (active ? '#00d4ff' : 'rgba(255,255,255,0.1)') + '">Sezon ' + s + '</button>';
          }).join('') +
          '<button class="ep-add-season-btn" style="padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;cursor:pointer;background:#31324d;color:#00d4ff;border:1px solid #00d4ff4d">+ Sezon Ekle</button>' +
          '</div>'
        : '<div style="display:flex;justify-content:flex-end;margin-bottom:6px">' +
          '<button class="ep-add-season-btn" style="font-size:11px;color:#9090b0;background:none;border:none;cursor:pointer">+ Sezon Ekle</button></div>';

      const epCountBadge = seasonEps.length > 0
        ? '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">' +
          '<span style="font-size:12px;font-weight:700;color:#9090b0;text-transform:uppercase;letter-spacing:.06em">Sezon ' + activeSeason + '</span>' +
          '<span style="font-size:12px;font-weight:700;color:#00d4ff;background:#00d4ff1a;border:1px solid #00d4ff33;border-radius:20px;padding:2px 10px">' + seasonEps.length + ' Bölüm</span>' +
          '</div>'
        : '';
      const syncBtnHtml = '<button class="ep-anilist-sync-btn" style="display:flex;align-items:center;gap:6px;width:100%;padding:8px 12px;margin-bottom:8px;border-radius:8px;background:#16213e;border:1px solid #ffffff0d;color:#9090b0;font-size:12px;font-weight:600;cursor:pointer" data-content-id="' + contentId + '" data-season="' + activeSeason + '">' +
        '<span class="material-symbols-outlined" style="font-size:16px;color:#00d4ff">cloud_sync</span> S' + activeSeason + ' ' + syncLabel + '</button>';

      // ── Sezon ekleme formu ──
      const addSeasonFormHtml = '<div id="ep-add-season-form" style="display:none;flex-direction:column;gap:6px;padding:10px;background:#16213e;border-radius:10px;border:1px solid #00d4ff2a;margin-bottom:8px">' +
        '<div style="font-size:11px;color:#9090b0;margin-bottom:2px">Yeni sezon yükle (AniList ID ile)</div>' +
        '<div style="display:flex;gap:6px">' +
        '<input id="ep-new-season-num" type="number" min="1" value="' + (activeSeason + 1) + '" placeholder="Sezon No" ' +
        'style="width:80px;height:36px;background:#0d0d1a;border:1px solid #00d4ff4d;border-radius:8px;color:#00d4ff;font-size:13px;text-align:center;padding:0 8px">' +
        '<input id="ep-new-anilist-id" type="text" placeholder="AniList ID (opsiyonel)" ' +
        'style="flex:1;height:36px;background:#0d0d1a;border:1px solid #ffffff1a;border-radius:8px;color:#e1e0ff;font-size:12px;padding:0 8px">' +
        '<button id="ep-new-season-load" data-content-id="' + contentId + '" ' +
        'style="height:36px;padding:0 14px;background:#00d4ff1a;border:1px solid #00d4ff4d;border-radius:8px;color:#00d4ff;font-size:12px;font-weight:700;cursor:pointer">Yükle</button>' +
        '</div></div>';

      if (!seasonEps.length) {
        el.innerHTML = seasonPickerHtml + siteShortcut + addSeasonFormHtml + syncBtnHtml +
          '<div style="text-align:center;color:#9090b0;padding:32px 0;display:flex;flex-direction:column;align-items:center;gap:10px">' +
          '<span class="material-symbols-outlined" style="font-size:48px;color:#31324d">video_library</span>' +
          '<p style="font-size:13px">Sezon ' + activeSeason + ' bölüm listesi yok</p>' +
          '<p style="font-size:12px;color:#6060a0">Yukarıdan "' + syncLabel + '" butonuna bas</p></div>';
      } else {
        el.innerHTML = seasonPickerHtml + siteShortcut + addSeasonFormHtml + epCountBadge + syncBtnHtml +
          '<div id="ep-virtual-list" style="display:flex;flex-direction:column;gap:4px"></div>';
        const list = el.querySelector('#ep-virtual-list');
        let loaded = 0;
        let observer = null;
        function _loadBatch() {
          const slice = seasonEps.slice(loaded, loaded + 20);
          if (!slice.length) { if (observer) { observer.disconnect(); observer = null; } return; }
          const frag = document.createDocumentFragment();
          slice.forEach(function(e) {
            const wrap = document.createElement('div');
            wrap.innerHTML = _epHtml(e);
            frag.appendChild(wrap.firstElementChild);
          });
          list.appendChild(frag);
          loaded += slice.length;
          if (loaded < seasonEps.length) {
            if (observer) observer.disconnect();
            const sentinel = list.lastElementChild;
            observer = new IntersectionObserver(function(entries) {
              if (entries[0].isIntersecting) { observer.disconnect(); observer = null; _loadBatch(); }
            }, { rootMargin: '200px' });
            observer.observe(sentinel);
          }
        }
        _loadBatch();
      }

      // Event listeners
      el.querySelectorAll('.ep-season-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
          activeSeason = parseInt(this.dataset.season, 10);
          _buildEpisodeView();
        });
      });
      const addSeasonBtn = el.querySelector('.ep-add-season-btn');
      if (addSeasonBtn) addSeasonBtn.addEventListener('click', function() {
        const form = document.getElementById('ep-add-season-form');
        if (form) form.style.display = form.style.display === 'none' ? 'flex' : 'none';
      });
      const loadNewSeasonBtn = el.querySelector('#ep-new-season-load');
      if (loadNewSeasonBtn) loadNewSeasonBtn.addEventListener('click', async function() {
        const seasonNum = parseInt(document.getElementById('ep-new-season-num').value, 10) || (activeSeason + 1);
        const anilistId = (document.getElementById('ep-new-anilist-id').value || '').trim() || null;
        const fakeEvt = { currentTarget: this, target: this };
        this.dataset.season = String(seasonNum);
        await syncEpisodesFromAniList(fakeEvt, seasonNum, anilistId);
      });
      const syncBtn2 = el.querySelector('.ep-anilist-sync-btn');
      if (syncBtn2) syncBtn2.addEventListener('click', syncEpisodesFromAniList);
      const goSitesBtn = el.querySelector('.ep-go-sites-btn');
      if (goSitesBtn) goSitesBtn.addEventListener('click', function() { detailSwitchTab('sites'); });
    }

    // ── Episode row HTML (Stitch v7 — thumbnail + progress) ──────────
    function _epHtml(e) {
      const epUrl = e.url || null;
      const fbSite = (typeof primarySite !== 'undefined') ? primarySite : null;
      const fallbackUrl = !epUrl && fbSite ? fbSite.site_url : null;
      const openUrl = epUrl || fallbackUrl;
      const numTxt = 'Bölüm ' + e.number;

      // Thumbnail block (96×54px, 16:9)
      function _thumb(watched) {
        const numColor = watched ? '#4a4b72' : (e.is_new ? '#00d4ff' : '#9090b0');
        return '<div style="position:relative;width:96px;height:54px;flex-shrink:0;border-radius:8px;overflow:hidden;background:#0d1526">' +
          '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">' +
          '<span style="font-size:20px;font-weight:800;color:' + numColor + '">' + e.number + '</span></div>' +
          (watched
            ? '<div style="position:absolute;top:4px;right:4px;width:18px;height:18px;border-radius:50%;background:#22c55e;display:flex;align-items:center;justify-content:center">' +
              '<span class="material-symbols-outlined" style="font-size:11px;color:#fff;font-variation-settings:\'FILL\' 1">check</span></div>'
            : '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">' +
              '<span class="material-symbols-outlined" style="font-size:26px;color:' + numColor + '55;font-variation-settings:\'FILL\' 1">play_circle</span></div>') +
          '</div>';
      }

      if (e.is_watched) {
        return '<div class="ep-row" style="display:flex;align-items:center;gap:10px;padding:8px;border-radius:12px;background:#16213e4d;border:1px solid rgba(255,255,255,0.04);box-shadow:0 2px 8px rgba(0,0,0,0.25);opacity:0.55">' +
          _thumb(true) +
          '<div style="flex:1;min-width:0">' +
          '<div style="color:#e1e0ff;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + numTxt + '</div>' +
          (e.title ? '<div style="color:#9090b0;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:2px">' + escapeHtml(e.title) + '</div>' : '') +
          '</div>' +
          '<button class="ep-watch-btn" data-ep-id="' + e.id + '" data-content-id="' + contentId + '" style="min-width:40px;min-height:40px;display:flex;align-items:center;justify-content:center;background:none;border:none;cursor:pointer">' +
          '<div style="width:22px;height:22px;border-radius:4px;background:#00d4ff22;border:1px solid #00d4ff55;display:flex;align-items:center;justify-content:center">' +
          '<span class="material-symbols-outlined" style="font-size:14px;color:#00d4ff;font-variation-settings:\'FILL\' 1">check</span></div></button>' +
          '</div>';
      }

      const isNew = e.is_new;
      const numColor2 = isNew ? '#00d4ff' : '#e1e0ff';
      const rowBg = isNew ? 'rgba(0,212,255,0.06)' : '#16213e';
      const rowBorder = isNew ? '1px solid rgba(0,212,255,0.25)' : '1px solid rgba(255,255,255,0.05)';

      return '<div class="ep-row" style="display:flex;align-items:center;gap:10px;padding:8px;border-radius:12px;background:' + rowBg + ';border:' + rowBorder + ';box-shadow:0 2px 8px rgba(0,0,0,0.25)">' +
        _thumb(false) +
        '<div style="flex:1;min-width:0">' +
        '<div style="display:flex;align-items:center;gap:6px">' +
        '<span style="color:' + numColor2 + ';font-size:13px;font-weight:700">' + numTxt + '</span>' +
        (isNew ? '<span style="padding:1px 6px;background:#00d4ff1a;color:#00d4ff;border-radius:4px;font-size:9px;font-weight:700;text-transform:uppercase">YENİ</span>' : '') +
        '</div>' +
        (e.title ? '<div style="color:#9090b0;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:2px">' + escapeHtml(e.title) + '</div>' : '') +
        '</div>' +
        '<div style="display:flex;align-items:center;gap:2px">' +
        (openUrl
          ? '<button class="ep-overlay-btn" data-url="' + escapeHtml(openUrl) + '" data-label="' + numTxt + '"' +
            (epUrl ? ' data-ep-id="' + e.id + '" data-content-id="' + contentId + '"' : '') +
            ' style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;cursor:pointer;' +
            (epUrl ? 'background:#00d4ff1a;border:1px solid #00d4ff4d;color:#00d4ff">' : 'background:#31324d;border:1px solid rgba(255,255,255,0.08);color:#9090b0">' ) +
            '<span class="material-symbols-outlined" style="font-size:18px">' + readIcon + '</span></button>'
          : '') +
        (openUrl ? '<button class="ep-dl-btn" title="İndir" style="color:#9090b0;background:none;border:none;cursor:pointer;width:36px;height:36px;display:flex;align-items:center;justify-content:center" ' +
          'data-ep-num="' + e.number + '" data-ep-url="' + escapeHtml(openUrl) + '" ' +
          'data-content-id="' + contentId + '" data-content-type="' + escapeHtml(contentType || '') + '" data-content-title="' + escapeHtml(contentTitle || '') + '">' +
          '<span class="material-symbols-outlined" style="font-size:18px">download</span></button>' : '') +
        '<button class="ep-watch-btn" data-ep-id="' + e.id + '" data-content-id="' + contentId + '" style="min-width:40px;min-height:40px;display:flex;align-items:center;justify-content:center;background:none;border:none;cursor:pointer">' +
        '<div style="width:22px;height:22px;border-radius:4px;background:#31324d;border:1px solid rgba(255,255,255,0.1)"></div></button>' +
        '</div></div>';
    }

    _buildEpisodeView();

    // ── Event delegation — overlayBtn / watchBtn / dlBtn (tek listener) ─
    el.addEventListener('click', async function(evt) {
      const overlayBtn = evt.target.closest('.ep-overlay-btn');
      const watchBtn = evt.target.closest('.ep-watch-btn');
      const dlBtn    = evt.target.closest('.ep-dl-btn');

      if (overlayBtn) {
        const url   = overlayBtn.dataset.url;
        const label = overlayBtn.dataset.label || '';
        const epId  = overlayBtn.dataset.epId ? parseInt(overlayBtn.dataset.epId, 10) : null;
        const cid   = overlayBtn.dataset.contentId ? parseInt(overlayBtn.dataset.contentId, 10) : null;
        openReadOverlay(url, label);
        if (epId && cid) {
          try { await apiPatch('/api/episodes/' + epId + '/watch', {}); } catch(e2) {}
          const scr = document.getElementById('screen-detail');
          const savedY = scr ? scr.scrollTop : 0;
          await renderDetail(cid);
          if (scr) requestAnimationFrame(function() { scr.scrollTop = savedY; });
        }
        return;
      }

      if (watchBtn) {
        const epId = parseInt(watchBtn.dataset.epId, 10);
        const cid  = parseInt(watchBtn.dataset.contentId, 10);
        const row = watchBtn.closest('.ep-row');
        if (row) {
          row.style.opacity = '0.55';
          row.style.background = '#16213e4d';
          const checkDiv = watchBtn.querySelector('div');
          if (checkDiv) {
            checkDiv.style.background = '#00d4ff22';
            checkDiv.style.border = '1px solid #00d4ff55';
            checkDiv.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;color:#00d4ff;font-variation-settings:\'FILL\' 1">check</span>';
          }
        }
        try {
          await apiPatch('/api/episodes/' + epId + '/watch', {});
          const updated = await apiGet('/api/content/' + cid);
          const allWatched = updated.episodes && updated.episodes.length > 0 &&
            updated.episodes.every(function(e) { return e.is_watched; });
          if (allWatched) { _showCompleteModal(cid, updated.title || '', updated.my_score); }
        } catch(e) { console.error('ep watch', e); }
        return;
      }

      if (dlBtn) {
        if (!window.kuroDownload) { showToast('İndirme modülü yüklenmedi', 'error'); return; }
        window.kuroDownload.start(
          parseInt(dlBtn.dataset.contentId, 10), dlBtn.dataset.contentTitle,
          dlBtn.dataset.contentType, parseInt(dlBtn.dataset.epNum, 10),
          dlBtn.dataset.epUrl, '720p'
        );
      }
    });
  }

  // ── Tamamlama Modalı ─────────────────────────────────────────────
  function _showCompleteModal(contentId, title, currentScore) {
    let modal = document.getElementById('complete-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'complete-modal';
      modal.className = 'fixed inset-0 z-[9998] flex items-end justify-center pb-8 px-4';
      modal.innerHTML = `
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" id="complete-modal-backdrop"></div>
        <div id="complete-modal-card" class="relative z-10 w-full max-w-sm rounded-3xl bg-[#12132a] border border-[#00d4ff]/30 p-6 flex flex-col gap-5 shadow-2xl" style="animation:completeIn .35s cubic-bezier(.34,1.56,.64,1) both">
          <div class="flex flex-col items-center gap-2 text-center">
            <div id="complete-emoji" class="text-5xl" style="animation:emojiBounce .6s ease .2s both">🎉</div>
            <h2 class="text-[18px] font-bold text-[#e1e0ff]">Tamamlandı!</h2>
            <p id="complete-modal-title" class="text-[13px] text-[#9090b0]"></p>
            <p class="text-[12px] text-[#00d4ff]/70 font-medium">Puan vermek ister misin?</p>
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-[12px] font-bold text-[#9090b0] uppercase tracking-wider">Puanın</label>
            <div class="flex items-center gap-3">
              <input id="complete-score-slider" type="range" min="1" max="10" step="0.5"
                class="flex-1 accent-[#00d4ff] h-1"
                value="7">
              <span id="complete-score-val" class="text-[20px] font-bold text-[#00d4ff] w-10 text-right">7.0</span>
            </div>
          </div>
          <label class="flex items-center gap-3 cursor-pointer">
            <input id="complete-status-check" type="checkbox" checked
              class="w-5 h-5 accent-[#00d4ff] rounded">
            <span class="text-[13px] text-[#e1e0ff]">Durumu "Tamamlandı" olarak işaretle</span>
          </label>
          <div class="flex gap-3">
            <button id="complete-modal-skip" class="flex-1 py-3 rounded-2xl border border-white/10 text-[#9090b0] text-[13px] font-bold hover:bg-white/5 transition-colors">Atla</button>
            <button id="complete-modal-save" class="flex-1 py-3 rounded-2xl bg-[#00d4ff] text-[#003642] text-[13px] font-bold hover:bg-[#00bfef] transition-colors">Kaydet</button>
          </div>
        </div>`;
      document.body.appendChild(modal);
    }

    const scoreInput = modal.querySelector('#complete-score-slider');
    const scoreVal = modal.querySelector('#complete-score-val');
    modal.querySelector('#complete-modal-title').textContent = title;
    scoreInput.value = currentScore != null ? currentScore : 7;
    scoreVal.textContent = parseFloat(scoreInput.value).toFixed(1);
    scoreInput.oninput = function() {
      scoreVal.textContent = parseFloat(this.value).toFixed(1);
    };

    modal.classList.remove('hidden');
    // Animasyonu her açılışta sıfırla
    const card = modal.querySelector('#complete-modal-card');
    const emoji = modal.querySelector('#complete-emoji');
    if (card) { card.style.animation = 'none'; void card.offsetHeight; card.style.animation = 'completeIn .35s cubic-bezier(.34,1.56,.64,1) both'; }
    if (emoji) { emoji.style.animation = 'none'; void emoji.offsetHeight; emoji.style.animation = 'emojiBounce .6s ease .2s both'; }

    function close() { modal.classList.add('hidden'); renderDetail(contentId); }

    modal.querySelector('#complete-modal-backdrop').onclick = close;
    modal.querySelector('#complete-modal-skip').onclick = close;
    modal.querySelector('#complete-modal-save').onclick = async function() {
      const score = parseFloat(scoreInput.value);
      const markDone = modal.querySelector('#complete-status-check').checked;
      const patch = { my_score: score };
      if (markDone) patch.status = 'completed';
      try {
        await apiPatch('/api/content/' + contentId, patch);
        showToast('Kaydedildi! ' + (markDone ? '✓ Tamamlandı' : ''), 'success');
      } catch(e) { showToast('Kaydedilemedi', 'error'); }
      modal.classList.add('hidden');
      renderDetail(contentId);
    };
  }

  async function syncEpisodesFromAniList(e, seasonOverride, anilistIdOverride) {
    const btn = e.currentTarget || e.target;
    const cid = parseInt(btn.dataset.contentId, 10);
    const season = seasonOverride || parseInt(btn.dataset.season || '1', 10);
    btn.disabled = true;
    btn.innerHTML = '<span class="material-symbols-outlined animate-spin text-[16px]">progress_activity</span> Yükleniyor...';
    const scr = document.getElementById('screen-detail');
    const savedY = scr ? scr.scrollTop : 0;
    try {
      const body = { season: season };
      if (anilistIdOverride) body.anilist_override_id = String(anilistIdOverride);
      const res = await apiPost('/api/content/' + cid + '/episodes/sync', body);
      const total = res.episodes ? res.episodes.length : 0;
      const msg = res.synced > 0
        ? 'S' + season + ': ' + res.synced + ' bölüm yüklendi (' + total + ' toplam)'
        : total > 0 ? 'S' + season + ': ' + total + ' bölüm zaten güncel' : 'Bölüm bulunamadı';
      showToast(msg, res.synced > 0 ? 'success' : (total > 0 ? 'info' : 'error'));
      await renderDetail(cid);
      if (scr) requestAnimationFrame(function() { scr.scrollTop = savedY; });
    } catch (err) {
      showToast('Yükleme hatası: ' + err.message, 'error');
      btn.disabled = false;
      btn.innerHTML = '<span class="material-symbols-outlined text-[16px]">cloud_sync</span> AniList\'ten Yükle';
    }
  }

  function renderDetailSites(el, sites, contentId) {
    // Çalışan siteler önce, kendi içinde en yüksek bölüm sayısına göre
    const sorted = sites.slice().sort(function(a, b) {
      const deadA = a.is_dead ? 1 : 0;
      const deadB = b.is_dead ? 1 : 0;
      if (deadA !== deadB) return deadA - deadB;
      const av = a.latest_known_ep != null ? a.latest_known_ep : -1;
      const bv = b.latest_known_ep != null ? b.latest_known_ep : -1;
      return bv - av;
    });
    const sitesHtml = sorted.length
      ? sorted.map(function(s) {
          const abbr = (s.site_name || '?').slice(0, 2).toUpperCase();
          return '<div class="p-4 rounded-xl bg-[#16213e] border border-[#00d4ff]/20 inner-glow flex justify-between items-center gap-2">' +
            '<div class="flex items-center gap-3 min-w-0">' +
            '<div class="w-10 h-10 rounded bg-[#00d4ff]/20 flex items-center justify-center text-[#00d4ff] font-bold flex-shrink-0">' + abbr + '</div>' +
            '<div class="flex flex-col min-w-0">' +
            '<span class="font-bold text-[14px] text-[#e1e0ff] truncate">' + escapeHtml(s.site_name) + (s.latest_known_ep != null ? ' <span style="color:#9090b0;font-weight:normal;font-size:12px;">[' + s.latest_known_ep + '. bölüm]</span>' : '') + (s.is_dead ? ' <span style="color:#ffb4ab;font-size:11px;font-weight:700;">⚠️ Ölü</span>' : '') + '</span>' +
            '<div class="flex gap-1 flex-wrap mt-0.5">' +
            (sorted.indexOf(s) === 0 && !s.is_dead ? '<span style="background:#00d4ff22;color:#00d4ff;font-size:10px;font-weight:700;padding:1px 6px;border-radius:4px;">✓ Aktif</span>' : '') +
            (s.is_primary ? '<span style="background:#ffffff11;color:#9090b0;font-size:10px;padding:1px 6px;border-radius:4px;">Birincil</span>' : '') +
            (s.is_dead ? '<span style="background:#ffb4ab22;color:#ffb4ab;font-size:10px;padding:1px 6px;border-radius:4px;">Ölü — Yedek yok</span>' : '') +
            '</div>' +
            '</div></div>' +
            '<div class="flex items-center gap-2 flex-shrink-0">' +
            '<a href="' + escapeHtml(s.site_url) + '" target="_blank" rel="noopener" class="px-3 py-2 bg-[#31324d] border border-white/10 rounded-lg text-[#e1e0ff] text-[13px] hover:text-[#00d4ff] transition-colors flex items-center gap-1 active:scale-[0.97]">' +
            'Aç <span class="material-symbols-outlined text-[16px]">open_in_new</span></a>' +
            '<button class="site-delete-btn w-8 h-8 flex items-center justify-center text-[#9090b0] hover:text-[#ffb4ab] transition-colors rounded-lg hover:bg-white/5" data-site-id="' + s.id + '" data-content-id="' + contentId + '">' +
            '<span class="material-symbols-outlined text-[18px]">delete</span></button>' +
            '</div></div>';
        }).join('')
      : '<div class="text-center text-[#9090b0] py-6 flex flex-col items-center gap-2"><span class="material-symbols-outlined text-4xl">link_off</span><p>Henüz site eklenmemiş</p></div>';

    el.innerHTML = sitesHtml +
      '<button id="detail-site-add-toggle" class="flex items-center gap-2 text-[13px] text-[#9090b0] hover:text-[#00d4ff] transition-colors pt-2 pb-1">' +
      '<span class="material-symbols-outlined text-[16px]">add_circle</span> Site Ekle</button>' +
      '<div id="detail-site-add-form" class="hidden flex-col gap-2 pt-1">' +
      '<input id="detail-site-name" class="w-full h-[44px] px-3 bg-[#16213e] border border-white/5 rounded-lg text-[14px] text-[#e1e0ff] focus:outline-none focus:border-[#00d4ff]/50 placeholder:text-[#9090b0]" placeholder="Site adı (ör. Crunchyroll)" type="text"/>' +
      '<input id="detail-site-url" class="w-full h-[44px] px-3 bg-[#16213e] border border-white/5 rounded-lg text-[12px] text-[#e1e0ff] focus:outline-none focus:border-[#00d4ff]/50 placeholder:text-[#9090b0] font-mono" placeholder="https://..." type="text"/>' +
      '<div class="flex gap-2 items-center">' +
      '<label class="flex items-center gap-2 text-[13px] text-[#9090b0] cursor-pointer">' +
      '<input id="detail-site-primary" type="checkbox" class="accent-[#00d4ff]"/> Ana Site</label>' +
      '<button id="detail-site-save-btn" class="ml-auto h-[44px] px-4 bg-[#00d4ff]/10 border border-[#00d4ff]/30 text-[#00d4ff] rounded-lg text-[13px] font-medium hover:bg-[#00d4ff]/20 active:scale-[0.97] transition-colors" data-content-id="' + contentId + '">Kaydet</button>' +
      '</div></div>';

    el.querySelector('#detail-site-add-toggle').addEventListener('click', function() {
      const form = el.querySelector('#detail-site-add-form');
      const hidden = form.classList.contains('hidden');
      form.classList.toggle('hidden', !hidden);
      form.classList.toggle('flex', hidden);
    });
    if (!sites.length) {
      const form = el.querySelector('#detail-site-add-form');
      form.classList.remove('hidden');
      form.classList.add('flex');
    }

    el.querySelector('#detail-site-save-btn').addEventListener('click', async function() {
      const cid = parseInt(this.dataset.contentId, 10);
      const nameEl = el.querySelector('#detail-site-name');
      const urlEl = el.querySelector('#detail-site-url');
      const primaryEl = el.querySelector('#detail-site-primary');
      const name = nameEl ? nameEl.value.trim() : '';
      const url = urlEl ? urlEl.value.trim() : '';
      if (!name || !url) { showToast('Ad ve URL gerekli', 'error'); return; }
      try {
        await apiPost('/api/content/' + cid + '/sites', { site_name: name, site_url: url, is_primary: primaryEl ? primaryEl.checked : false });
        const updated = await apiGet('/api/content/' + cid);
        renderDetailSites(el, updated.sites || [], cid);
        const epsTabEl = document.getElementById('detail-tab-episodes');
        if (epsTabEl) renderDetailEpisodes(epsTabEl, updated.episodes || [], cid, updated.type, updated.title, updated.sites || [], updated.my_progress || 0);
        showToast('Site eklendi', 'success');
      } catch(e) { showToast('Eklenemedi: ' + e.message, 'error'); }
    });

    el.querySelectorAll('.site-delete-btn').forEach(function(btn) {
      btn.addEventListener('click', async function() {
        const sid = parseInt(this.dataset.siteId, 10);
        const cid = parseInt(this.dataset.contentId, 10);
        try {
          await apiDelete('/api/sites/' + sid);
          const updated = await apiGet('/api/content/' + cid);
          renderDetailSites(el, updated.sites || [], cid);
          const epsTabEl = document.getElementById('detail-tab-episodes');
          if (epsTabEl) renderDetailEpisodes(epsTabEl, updated.episodes || [], cid, updated.type, updated.title, updated.sites || [], updated.my_progress || 0);
        } catch(e) { showToast('Site silinemedi', 'error'); }
      });
    });
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
    picker.className = 'fixed z-[150] bg-[#1c1d37] border border-white/10 rounded-xl shadow-2xl overflow-hidden';
    picker.style.cssText = 'min-width:210px;max-width:260px';

    function _buildTagList(query) {
      const q = (query || '').toLowerCase().trim();
      const filtered = q ? allTags.filter(function(t) { return t.name.toLowerCase().includes(q); }) : allTags;
      if (filtered.length === 0 && q) {
        return '<div class="px-4 py-2 text-[12px] text-[#9090b0]">Eşleşme yok</div>';
      }
      if (allTags.length === 0) {
        return '<div class="px-4 py-2 text-[12px] text-[#9090b0]">Etiket yok — Ayarlar\'dan oluştur</div>';
      }
      return filtered.map(function(t) {
        const color = t.color || '#9090b0';
        const assigned = assignedIds.has(t.id);
        return '<button class="tag-picker-item w-full flex items-center gap-3 px-4 py-2 hover:bg-white/5 transition-colors text-left" data-tag-id="' + t.id + '" data-content-id="' + contentId + '" data-assigned="' + assigned + '">' +
          '<span class="w-3 h-3 rounded-full flex-shrink-0" style="background:' + color + '"></span>' +
          '<span class="text-[13px] text-[#e1e0ff] flex-1">' + escapeHtml(t.name) + '</span>' +
          (assigned ? '<span class="material-symbols-outlined text-[16px] text-[#00d4ff]">check</span>' : '') +
          '</button>';
      }).join('');
    }

    picker.innerHTML =
      '<div class="px-3 pt-3 pb-2 border-b border-white/5">' +
        '<input id="tag-search-input" type="text" placeholder="Etiket ara..." autocomplete="off" ' +
          'style="width:100%;height:34px;background:#0d0d1a;border:1px solid #00d4ff4d;border-radius:8px;color:#e1e0ff;font-size:13px;padding:0 10px;outline:none">' +
      '</div>' +
      '<div id="tag-picker-list" style="max-height:200px;overflow-y:auto;padding:4px 0">' + _buildTagList('') + '</div>';

    document.body.appendChild(picker);
    const rect = anchorEl.getBoundingClientRect();
    picker.style.top = (rect.bottom + 8) + 'px';
    picker.style.left = Math.min(rect.left, window.innerWidth - 220) + 'px';
    _tagPickerEl = picker;

    const searchInput = picker.querySelector('#tag-search-input');
    const listEl = picker.querySelector('#tag-picker-list');
    searchInput.focus();
    searchInput.addEventListener('input', function() {
      listEl.innerHTML = _buildTagList(this.value);
    });

    setTimeout(function() {
      document.addEventListener('click', function closePickerOnce(e) {
        if (!picker.contains(e.target) && !anchorEl.contains(e.target)) {
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
  let _discoverGenre = null;
  let _discoverType = 'anime';
  let _activeSearchTab = 'library';

  function _initSearchTabs() {
    const tabLib = document.getElementById('search-tab-library');
    const tabDis = document.getElementById('search-tab-discover');
    const panelLib = document.getElementById('search-panel-library');
    const panelDis = document.getElementById('search-panel-discover');
    const inp = document.getElementById('search-discover-input');
    const filterBtn = document.getElementById('search-filter-toggle');
    const filterPanel = document.getElementById('search-filter-panel');
    const filterTypeSection = document.getElementById('filter-type-section');
    const filterGenreSection = document.getElementById('discover-genre-section');
    if (!tabLib || !tabDis) return;

    // FİLTRELE butonu toggle (bir kez bağla)
    if (filterBtn && filterPanel && !filterBtn._filterListenerAdded) {
      filterBtn._filterListenerAdded = true;
      filterBtn.addEventListener('click', function() {
        filterPanel.classList.toggle('hidden');
        if (!filterPanel.classList.contains('hidden') && _activeSearchTab === 'discover') {
          _buildDiscoverGenreChips();
        }
      });
    }

    function switchTab(tab) {
      _activeSearchTab = tab;
      const isLib = tab === 'library';
      tabLib.className = 'search-tab flex-1 py-2 min-h-[40px] rounded-lg text-[12px] font-semibold tracking-wider uppercase transition-all ' + (isLib ? 'bg-[#00d4ff]/15 text-[#00d4ff]' : 'text-[#859398]');
      tabDis.className = 'search-tab flex-1 py-2 min-h-[40px] rounded-lg text-[12px] font-semibold tracking-wider uppercase transition-all ' + (!isLib ? 'bg-[#00d4ff]/15 text-[#00d4ff]' : 'text-[#859398]');
      if (panelLib) { panelLib.classList.toggle('hidden', !isLib); }
      if (panelDis) {
        panelDis.classList.toggle('hidden', isLib);
        panelDis.classList.toggle('flex', !isLib);
      }
      // Filtre panelini kapat ve tip/tür bölümlerini tab'a göre gizle/göster
      if (filterPanel) filterPanel.classList.add('hidden');
      if (filterTypeSection) filterTypeSection.classList.toggle('hidden', isLib);
      if (filterGenreSection) filterGenreSection.classList.toggle('hidden', isLib);
      const typeLabels = { anime: 'AniList\'te ara...', manga: 'Manga ara...', manhwa: 'Manhwa ara...', game: 'Oyun ara (IGDB)...' };
      if (inp) inp.placeholder = isLib ? 'Kütüphanende ara...' : (typeLabels[_discoverType] || 'Ara...');
      if (inp && inp.value) {
        isLib ? renderLibrarySearch(inp.value) : renderSearch(inp.value);
      } else if (!isLib) {
        _buildDiscoverGenreChips();
        if (_discoverGenre) renderSearch('');
      }
    }

    // Keşfet tip seçici (birikmeli listener önlemek için her düğmeye bir kez bağla)
    document.querySelectorAll('.discover-type-btn').forEach(function(btn) {
      if (btn._discoverListenerAdded) return;
      btn._discoverListenerAdded = true;
      btn.addEventListener('click', function() {
        _discoverType = this.dataset.discoverType;
        _discoverGenre = null;
        document.querySelectorAll('.discover-type-btn').forEach(function(b) {
          const active = b.dataset.discoverType === _discoverType;
          b.className = 'discover-type-btn flex-shrink-0 px-4 py-2 rounded-full text-[11px] font-bold tracking-wider active:scale-[0.95] transition-all ' +
            (active ? 'bg-[#00d4ff]/10 text-[#00d4ff] border border-[#00d4ff]/50' : 'bg-[#2f3639] text-[#859398]');
        });
        // Oyun tipinde tür bölümünü gizle
        const genreSection = document.getElementById('discover-genre-section');
        if (genreSection) genreSection.classList.toggle('hidden', _discoverType === 'game');
        const typeLabels2 = { anime: 'AniList\'te ara...', manga: 'Manga ara...', manhwa: 'Manhwa ara...', game: 'Oyun ara (IGDB)...' };
        if (inp) inp.placeholder = typeLabels2[_discoverType] || 'Ara...';
        const q = inp ? inp.value.trim() : '';
        if (q.length >= 2) renderSearch(q);
        else {
          _buildDiscoverGenreChips();
          const results = document.getElementById('search-results');
          if (results) results.innerHTML = '<div class="col-span-3 text-center py-8 text-[14px] text-[#859398]">' + (typeLabels2[_discoverType] || 'Ara...') + '</div>';
        }
      });
    });

    tabLib.onclick = function() { switchTab('library'); };
    tabDis.onclick = function() { switchTab('discover'); };

    if (inp) {
      inp.oninput = function() {
        clearTimeout(_searchTimer);
        _searchTimer = setTimeout(function() {
          if (_activeSearchTab === 'library') renderLibrarySearch(inp.value);
          else renderSearch(inp.value);
        }, 300);
      };
    }

    switchTab(_activeSearchTab);
  }

  async function renderLibrarySearch(q) {
    const box = document.getElementById('library-search-results');
    if (!box) return;
    if (!q || q.trim().length < 1) {
      box.innerHTML = '<div class="col-span-3 text-center py-8 text-[14px] text-[#859398]">Kütüphanende aramak için yaz...</div>';
      return;
    }
    box.innerHTML = '<div class="col-span-3 text-center py-8 flex items-center justify-center gap-2 text-[14px] text-[#859398]"><span class="material-symbols-outlined animate-spin" style="font-size:20px">progress_activity</span>Aranıyor...</div>';
    try {
      const items = await apiGet('/api/content?q=' + encodeURIComponent(q.trim()));
      if (!items || !items.length) {
        box.innerHTML = '<div class="col-span-3 text-center py-12 flex flex-col items-center gap-3"><span class="material-symbols-outlined text-[#9090b0]" style="font-size:48px;opacity:0.4">search_off</span><p class="text-[14px] font-medium text-[#9090b0]">Sonuç bulunamadı</p></div>';
        return;
      }
      const _TYPE_STRIPE = {anime:'#00d4ff',manga:'#ffd9a1',manhwa:'#bbc5eb',game:'#ffb4ab'};
      const _TYPE_LABEL  = {anime:'Anime',manga:'Manga',manhwa:'Manhwa',game:'Oyun'};
      box.innerHTML = items.map(function(it) {
        const stripe = _TYPE_STRIPE[it.type] || '#00d4ff';
        const label  = _TYPE_LABEL[it.type]  || 'Anime';
        const cover = it.cover_url
          ? '<img src="' + escapeHtml(it.cover_url) + '" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" loading="lazy"/>'
          : '<div class="absolute inset-0 flex items-center justify-center text-[#31324d] text-2xl font-bold">' + escapeHtml((it.title||'?').slice(0,2).toUpperCase()) + '</div>';
        const score = it.my_score != null
          ? '<div class="flex items-center gap-1"><span class="material-symbols-outlined fill-1 text-[#feb528]" style="font-size:10px">star</span><span class="text-[9px] text-[#9090b0]">' + it.my_score.toFixed(1) + '</span></div>'
          : '';
        return '<div class="group relative aspect-[2/3] rounded-lg overflow-hidden bg-[#1a1a2e] cursor-pointer active:scale-[0.95] transition-all duration-300 inner-glow shadow-[0_4px_12px_rgba(0,0,0,0.4)] hover:shadow-[0_16px_32px_rgba(0,0,0,0.7)] hover:scale-[1.02]" data-content-id="' + it.id + '">' +
          '<div class="absolute top-0 left-0 w-1 h-full z-10" style="background:' + stripe + '"></div>' +
          '<div class="absolute inset-0 bg-gradient-to-t from-[#0a0a12] via-[#0a0a12]/40 to-transparent z-10"></div>' +
          cover +
          '<div class="absolute inset-0 z-20 flex flex-col justify-end p-3">' +
          '<span class="inline-block px-2 py-0.5 rounded mb-1 w-max text-[9px] font-bold uppercase" style="background:rgba(26,27,45,0.85);backdrop-filter:blur(4px);color:' + stripe + ';border:1px solid ' + stripe + '33">' + label + '</span>' +
          '<p class="text-[12px] font-bold text-white line-clamp-2 leading-tight mb-1">' + escapeHtml(it.title_tr||it.title||'') + '</p>' +
          score +
          '</div>' +
          '</div>';
      }).join('');
      box.querySelectorAll('[data-content-id]').forEach(function(card) {
        card.addEventListener('click', function() {
          renderDetail(parseInt(this.dataset.contentId, 10));
          showScreen('screen-detail');
        });
      });
    } catch(e) {
      box.innerHTML = '<div class="col-span-3 text-center py-8 text-[14px] text-[#859398]">Hata: ' + escapeHtml(e.message) + '</div>';
    }
  }

  const DISCOVER_GENRES = ['Action','Adventure','Comedy','Drama','Fantasy','Horror','Mecha','Mystery','Romance','Sci-Fi','Slice of Life','Sports','Supernatural','Thriller'];

  function _buildDiscoverGenreChips() {
    const row = document.getElementById('discover-genre-row');
    if (!row) return;
    row.innerHTML = DISCOVER_GENRES.map(function(g) {
      const active = _discoverGenre === g;
      return '<button class="discover-genre-chip flex-shrink-0 px-4 py-2 rounded-full text-[11px] font-bold tracking-wider active:scale-[0.95] transition-all border ' +
        (active ? 'bg-[#00d4ff]/15 border-[#00d4ff] text-[#00d4ff]' : 'bg-[#2f3639] border-transparent text-[#859398] hover:text-[#e1e0ff]') +
        '" data-genre="' + g + '">' + g + '</button>';
    }).join('');
    row.querySelectorAll('.discover-genre-chip').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const g = this.dataset.genre;
        _discoverGenre = (_discoverGenre === g) ? null : g;
        _buildDiscoverGenreChips();
        const inp = document.getElementById('search-discover-input');
        renderSearch(inp ? inp.value : '');
      });
    });
  }

  async function renderSearch(q) {
    const results = document.getElementById('search-results');
    if (!results) return;
    _buildDiscoverGenreChips();
    const hasQ = q && q.trim().length >= 2;
    if (!hasQ && !_discoverGenre) {
      results.innerHTML = '<div class="col-span-3 text-center py-8 text-[14px] text-[#859398]">En az 2 karakter yaz veya bir tür seç...</div>';
      return;
    }
    const sourceLabel = _discoverType === 'game' ? 'IGDB' : 'AniList';
    results.innerHTML = '<div class="col-span-3 text-center py-8 flex items-center justify-center gap-2 text-[14px] text-[#859398]"><span class="material-symbols-outlined animate-spin" style="font-size:20px">progress_activity</span>' + sourceLabel + '\'te aranıyor...</div>';
    let url = '/api/discover?type=' + _discoverType;
    if (hasQ) url += '&q=' + encodeURIComponent(q.trim());
    if (_discoverGenre && _discoverType !== 'game') url += '&genre=' + encodeURIComponent(_discoverGenre);
    try {
      const items = await apiGet(url);
      if (!items || items.length === 0) {
        results.innerHTML = '<div class="col-span-3 text-center py-12 flex flex-col items-center gap-3">' +
          '<span class="material-symbols-outlined text-[#9090b0]" style="font-size:48px;opacity:0.4">search_off</span>' +
          '<p class="text-[14px] font-medium text-[#9090b0]">' + (hasQ ? '"' + escapeHtml(q.trim()) + '" için sonuç bulunamadı' : 'Bu türde sonuç yok') + '</p>' +
          '<p class="text-[12px] text-[#9090b0] opacity-60">Farklı bir arama dene</p>' +
          '</div>';
        return;
      }
      const _DS_STRIPE = {anime:'#00d4ff',manga:'#ffd9a1',manhwa:'#bbc5eb',game:'#ffb4ab'};
      const _DS_LABEL  = {anime:'Anime',manga:'Manga',manhwa:'Manhwa',game:'Oyun'};
      results.innerHTML = items.map(function(it) {
        const stripe = _DS_STRIPE[it.type] || '#00d4ff';
        const typeLabel = _DS_LABEL[it.type] || it.type || 'Anime';
        const cover = it.cover_url
          ? '<img src="' + escapeHtml(it.cover_url) + '" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" loading="lazy"/>'
          : '<div class="absolute inset-0 flex items-center justify-center text-[#31324d] text-2xl font-bold">' + escapeHtml((it.title||'??').slice(0,2).toUpperCase()) + '</div>';
        const discoverData = JSON.stringify({
          title: it.title,
          type: it.type || 'anime',
          cover_url: it.cover_url || '',
          external_id: String(it.external_id || ''),
          genres: it.genres || []
        });
        return '<div class="group relative aspect-[2/3] rounded-lg overflow-hidden bg-[#1a1a2e] cursor-pointer active:scale-[0.95] transition-all duration-300 inner-glow shadow-[0_4px_12px_rgba(0,0,0,0.4)] hover:shadow-[0_16px_32px_rgba(0,0,0,0.7)] hover:scale-[1.02]">' +
          '<div class="absolute top-0 left-0 w-1 h-full z-10" style="background:' + stripe + '"></div>' +
          '<div class="absolute inset-0 bg-gradient-to-t from-[#0a0a12] via-[#0a0a12]/40 to-transparent z-10"></div>' +
          cover +
          '<div class="absolute inset-0 z-20 flex flex-col justify-end p-3">' +
          '<span class="inline-block px-2 py-0.5 rounded mb-1 w-max text-[9px] font-bold uppercase" style="background:rgba(26,27,45,0.85);backdrop-filter:blur(4px);color:' + stripe + ';border:1px solid ' + stripe + '33">' + typeLabel + '</span>' +
          '<p class="text-[12px] font-bold text-white line-clamp-2 leading-tight mb-2">' + escapeHtml(it.title) + '</p>' +
          '<button class="w-full h-8 rounded-lg text-[11px] font-bold flex items-center justify-center gap-1 active:scale-[0.97] transition-all" style="background:rgba(0,212,255,0.9);color:#003642" data-discover-add=\'' + discoverData.replace(/'/g,'&#39;') + '\'>' +
          '<span class="material-symbols-outlined" style="font-size:14px">add</span>Ekle</button>' +
          '</div></div>';
      }).join('');

      results.querySelectorAll('[data-discover-add]').forEach(function(btn) {
        btn.addEventListener('click', function() {
          const data = JSON.parse(this.dataset.discoverAdd);
          prefillAddForm(data);
          openModal('modal-add');
        });
      });
    } catch (err) {
      results.innerHTML = '<div class="col-span-3 text-center py-8 text-[14px] text-[#859398]">Hata: ' + escapeHtml(err.message) + '</div>';
    }
  }

  // ── Add Modal Step-1: AniList Arama ──────────────────────────────
  let _addSearchTimer = null;
  let _addStep1Type = 'anime';

  function _initAddSearch() {
    const inp = document.getElementById('add-step1-search-input');
    const resultsBox = document.querySelector('#add-step-1 .flex-1.overflow-y-auto');
    if (!inp || !resultsBox) return;

    // Tip seçici butonları
    document.querySelectorAll('.add-step1-type-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        _addStep1Type = this.dataset.step1Type;
        document.querySelectorAll('.add-step1-type-btn').forEach(function(b) {
          const a = b.dataset.step1Type === _addStep1Type;
          b.className = 'add-step1-type-btn shrink-0 px-3 py-1.5 min-h-[36px] rounded-full text-[12px] font-bold transition-all ' +
            (a ? 'bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/40' : 'text-[#9090b0] border border-[#3c494e]/40 hover:text-[#e1e0ff]');
        });
        const q = inp.value.trim();
        if (q.length >= 2) inp.dispatchEvent(new Event('input'));
        else resultsBox.innerHTML = '<div class="text-center text-[#9090b0] py-8 text-[13px]">Başlık yaz, ' + (_addStep1Type === 'game' ? 'IGDB' : 'AniList') + '\'te ara...</div>';
      });
    });

    inp.value = '';
    _addStep1Type = 'anime';
    resultsBox.innerHTML = '<div class="text-center text-[#9090b0] py-8 text-[13px]">Başlık yaz, AniList\'te ara...</div>';
    inp.oninput = function() {
      clearTimeout(_addSearchTimer);
      const q = this.value.trim();
      if (q.length < 2) {
        resultsBox.innerHTML = '<div class="text-center text-[#9090b0] py-8 text-[13px]">En az 2 karakter yaz...</div>';
        return;
      }
      resultsBox.innerHTML = '<div class="text-center text-[#9090b0] py-6 text-[13px] flex items-center justify-center gap-2"><span class="material-symbols-outlined animate-spin text-sm">progress_activity</span> Aranıyor...</div>';
      _addSearchTimer = setTimeout(async function() {
        try {
          const items = await apiGet('/api/discover?q=' + encodeURIComponent(q) + '&type=' + _addStep1Type);
          if (!items || !items.length) {
            resultsBox.innerHTML = '<div class="text-center text-[#9090b0] py-8 text-[13px]">Sonuç bulunamadı</div>';
            return;
          }
          resultsBox.innerHTML = items.map(function(it) {
            const cover = it.cover_url
              ? '<img src="' + escapeHtml(it.cover_url) + '" class="w-full h-full object-cover" loading="lazy"/>'
              : '<span class="font-bold text-xs text-[#9090b0]">' + escapeHtml((it.title || '?').slice(0,2).toUpperCase()) + '</span>';
            const yr = it.year || '';
            const tpMap2 = { anime: 'Anime', manga: 'Manga', manhwa: 'Manhwa', game: 'Oyun' };
            const tp = tpMap2[it.type] || (it.type || 'anime');
            return '<div class="flex items-center gap-3 p-2 rounded-lg hover:bg-[#2f3639] transition-transform active:scale-[0.97] etched-border bg-[#0e1417]" data-add-pick=\'' + JSON.stringify(it).replace(/'/g, '&#39;') + '\'>' +
              '<div class="w-[40px] h-[56px] bg-[#2f3639] rounded-md overflow-hidden flex-shrink-0 flex items-center justify-center">' + cover + '</div>' +
              '<div class="flex-1 min-w-0 flex flex-col justify-center">' +
              '<h3 class="text-[13px] font-bold text-[#dde3e7] truncate">' + escapeHtml(it.title || '') + '</h3>' +
              '<div class="flex items-center gap-2 mt-0.5"><span class="text-[12px] text-[#9090b0]">' + yr + '</span><span class="px-1.5 py-0.5 rounded-full bg-[#00d4ff]/20 text-[#00d4ff] text-[10px] font-bold">' + tp + '</span></div>' +
              '</div>' +
              '<button class="h-11 min-h-[44px] px-3 border border-[#00d4ff] text-[#00d4ff] rounded-full text-[14px] font-semibold flex items-center gap-1 hover:bg-[#00d4ff]/10 transition-colors flex-shrink-0 active:scale-[0.97]">' +
              '<span class="material-symbols-outlined text-[16px]">add</span></button>' +
              '</div>';
          }).join('');
          resultsBox.querySelectorAll('[data-add-pick]').forEach(function(row) {
            row.querySelector('button').addEventListener('click', function() {
              const data = JSON.parse(row.dataset.addPick);
              prefillAddForm(data);
            });
          });
        } catch(e) {
          resultsBox.innerHTML = '<div class="text-center text-[#9090b0] py-8 text-[13px]">Hata: ' + escapeHtml(e.message) + '</div>';
        }
      }, 350);
    };
  }

  function prefillAddForm(data) {
    const titleEl = document.getElementById('add-form-title');
    if (titleEl) titleEl.value = data.title || '';
    const coverEl = document.getElementById('add-form-cover');
    if (coverEl) coverEl.value = data.cover_url || '';
    const extInput = document.getElementById('add-form-external-id');
    if (extInput) extInput.value = data.external_id || '';
    const genresInput = document.getElementById('add-form-genres');
    if (genresInput) genresInput.value = JSON.stringify(data.genres || []);
    const epEl = document.getElementById('add-form-total-episodes');
    if (epEl) epEl.value = data.total_episodes != null ? data.total_episodes : '';
    const chEl = document.getElementById('add-form-total-chapters');
    if (chEl) chEl.value = data.total_chapters != null ? data.total_chapters : '';

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
      showToast('Başlık gerekli', 'error');
      return;
    }
    const type = _addActiveType || 'anime';
    const status = (document.getElementById('add-form-status') || {}).value || 'planning';
    const cover_url = (document.getElementById('add-form-cover') || {}).value.trim() || null;
    const note_text = (document.getElementById('add-form-note') || {}).value.trim() || null;
    const external_id = (document.getElementById('add-form-external-id') || {}).value.trim() || null;
    const _epRaw = (document.getElementById('add-form-total-episodes') || {}).value;
    const _chRaw = (document.getElementById('add-form-total-chapters') || {}).value;
    const total_episodes = _epRaw ? parseInt(_epRaw) || null : null;
    const total_chapters = _chRaw ? parseInt(_chRaw) || null : null;
    const starEl = document.querySelector('input[name="add-rating"]:checked');
    const my_score = starEl ? parseFloat(starEl.value) : null;
    const genresRaw = (document.getElementById('add-form-genres') || {}).value || '[]';
    let genres = [];
    try { genres = JSON.parse(genresRaw); } catch (e) { genres = []; }

    const btn = document.getElementById('add-save-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Kaydediliyor...'; }

    try {
      await apiPost('/api/content', { title: title.trim(), type, status, cover_url, note_text, external_id, my_score, genres: genres.length ? genres : undefined, total_episodes: total_episodes || undefined, total_chapters: total_chapters || undefined });
      closeModal('modal-add');
      // Formu temizle
      ['add-form-title','add-form-cover','add-form-note'].forEach(id => {
        const el = document.getElementById(id); if (el) el.value = '';
      });
      if (window.location.hash === '#screen-home' || !window.location.hash) renderHome();
    } catch (err) {
      showToast('Kayıt hatası: ' + err.message, 'error');
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

  // Add-form aktif tip takibi
  let _addActiveType = 'anime';

  // Add-form type butonları
  document.addEventListener('click', function(e) {
    const typeBtn = e.target.closest('.add-type-btn');
    if (typeBtn) {
      _addActiveType = typeBtn.dataset.addType || 'anime';
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
    // search-discover-input: _initSearchTabs tarafından yönetiliyor
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

  // ── PWA Install ───────────────────────────────────────────────────
  let _pwaInstallPrompt = null;

  window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    _pwaInstallPrompt = e;
    const sec = document.getElementById('pwa-install-section');
    if (sec) sec.classList.remove('hidden');
  });

  window.addEventListener('appinstalled', function() {
    _pwaInstallPrompt = null;
    const sec = document.getElementById('pwa-install-section');
    if (sec) sec.classList.add('hidden');
  });

  document.addEventListener('click', function(e) {
    if (!e.target.closest('#pwa-install-btn')) return;
    if (!_pwaInstallPrompt) return;
    _pwaInstallPrompt.prompt();
    _pwaInstallPrompt.userChoice.then(function(result) {
      if (result.outcome === 'accepted') {
        const sec = document.getElementById('pwa-install-section');
        if (sec) sec.classList.add('hidden');
      }
      _pwaInstallPrompt = null;
    });
  });

  // ── Service Worker Kaydı ─────────────────────────────────────────
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('sw.js').catch(err => {
        console.warn('SW kayıt hatası:', err);
      });
    });
  }

  // ── Read Overlay: aç/kapat (IIFE scope — renderDetailEpisodes'dan erişilebilir) ──
  function openReadOverlay(url, label) {
    const el = document.getElementById('read-overlay');
    if (!el) return;
    const titleEl = document.getElementById('read-overlay-title');
    const extEl   = document.getElementById('read-overlay-external');
    const frameEl = document.getElementById('read-overlay-frame');
    if (titleEl) titleEl.textContent = label || '';
    if (extEl)   extEl.href = url;
    if (frameEl) frameEl.src = url;
    el.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }

  function closeReadOverlay() {
    const el = document.getElementById('read-overlay');
    if (!el) return;
    el.style.display = 'none';
    document.body.style.overflow = '';
    const frameEl = document.getElementById('read-overlay-frame');
    if (frameEl) frameEl.src = '';
  }

  // ── Init ─────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function() {
    // Arama kutularını autocomplete önlemek için temizle
    ['home-search-input','search-discover-input'].forEach(function(id) {
      const el = document.getElementById(id);
      if (el) {
        el.value = '';
        el.addEventListener('focus', function() { if (this.value && !homeFilter.query) this.value = ''; });
      }
    });

    // İlk hash'e göre ekran aç
    const initial = (location.hash || '').replace('#','') || 'screen-home';
    const valid = ['screen-home','screen-detail','screen-search','screen-updates','screen-downloads','screen-stats','screen-settings','screen-archive'];
    showScreen(valid.includes(initial) ? initial : 'screen-home');

    // ── Pull-to-refresh (Home + Updates) ──────────────────────────
    (function() {
      var _ptrScreens = ['screen-home', 'screen-updates'];
      var _ptrStartY  = 0;
      var _ptrActive  = false;
      var _ptrMinDist = 72;
      var _ptrIndicator = null;

      function _getIndicator() {
        if (!_ptrIndicator) {
          _ptrIndicator = document.createElement('div');
          _ptrIndicator.id = 'ptr-indicator';
          _ptrIndicator.style.cssText = [
            'position:fixed;top:56px;left:50%;transform:translateX(-50%) translateY(-100%)',
            'width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center',
            'background:rgba(0,212,255,0.15);border:1px solid rgba(0,212,255,0.4)',
            'transition:transform 0.2s ease,opacity 0.2s ease;opacity:0;z-index:200'
          ].join(';');
          _ptrIndicator.innerHTML = '<span class="material-symbols-outlined" style="font-size:18px;color:#00d4ff">arrow_downward</span>';
          document.body.appendChild(_ptrIndicator);
        }
        return _ptrIndicator;
      }

      document.addEventListener('touchstart', function(e) {
        if (!_ptrScreens.includes(_currentScreen)) return;
        if (window.scrollY > 4) return;
        _ptrStartY = e.touches[0].clientY;
        _ptrActive = true;
      }, { passive: true });

      document.addEventListener('touchmove', function(e) {
        if (!_ptrActive) return;
        var dy = e.touches[0].clientY - _ptrStartY;
        if (dy < 0) { _ptrActive = false; return; }
        var ratio = Math.min(dy / (_ptrMinDist * 1.5), 1);
        var ind = _getIndicator();
        ind.style.opacity = String(ratio);
        ind.style.transform = 'translateX(-50%) translateY(' + (ratio * 20 - 100 + 100 * ratio) + '%)';
      }, { passive: true });

      document.addEventListener('touchend', function(e) {
        if (!_ptrActive) return;
        _ptrActive = false;
        var dy = e.changedTouches[0].clientY - _ptrStartY;
        var ind = _getIndicator();
        if (dy >= _ptrMinDist) {
          ind.querySelector('.material-symbols-outlined').style.animation = 'spin 0.6s linear infinite';
          if (_currentScreen === 'screen-home') renderHome();
          else if (_currentScreen === 'screen-updates') renderUpdates();
          setTimeout(function() {
            ind.style.opacity = '0';
            ind.style.transform = 'translateX(-50%) translateY(-100%)';
            if (ind.querySelector('.material-symbols-outlined'))
              ind.querySelector('.material-symbols-outlined').style.animation = '';
          }, 600);
        } else {
          ind.style.opacity = '0';
          ind.style.transform = 'translateX(-50%) translateY(-100%)';
        }
      }, { passive: true });
    })();

    // i18n uygula (varsa)
    if (window.kuroI18n && typeof window.kuroI18n.apply === 'function') {
      window.kuroI18n.apply();
    }

    // ── Read Overlay: event wiring ──────────────────────────────────
    var _readOverlayClose = document.getElementById('read-overlay-close');
    if (_readOverlayClose) _readOverlayClose.addEventListener('click', closeReadOverlay);

    document.addEventListener('keydown', function(e) {
      const ro = document.getElementById('read-overlay');
      if (e.key === 'Escape' && ro && ro.style.display === 'flex') {
        closeReadOverlay();
      }
    });
  });

})();
