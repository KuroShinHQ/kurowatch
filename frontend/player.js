// ═══════════════════════════════════════════════════════════════════
// KuroWatch — FAZ-3: İndirme Kuyruğu + Video Player + Manga Reader
// ═══════════════════════════════════════════════════════════════════
(function () {
  'use strict';

  const API = 'http://localhost:8099';

  // ── İndirme WS Bağlantısı ────────────────────────────────────────
  let _ws = null;
  let _jobs = {}; // id → job

  function connectDownloadWS() {
    if (_ws && _ws.readyState < 2) return;
    _ws = new WebSocket('ws://localhost:8099/api/download/ws');

    _ws.onmessage = function (e) {
      const msg = JSON.parse(e.data);
      if (msg.event === 'state') {
        _jobs = {};
        (msg.jobs || []).forEach(j => { _jobs[j.id] = j; });
      } else if (msg.event === 'queued' || msg.event === 'started' || msg.event === 'done') {
        if (msg.job) _jobs[msg.job.id] = msg.job;
      } else if (msg.event === 'progress') {
        if (_jobs[msg.job_id]) _jobs[msg.job_id].progress_pct = msg.pct;
      }
      _renderDownloadScreen();
      _updateBadge();
    };

    _ws.onclose = function () {
      setTimeout(connectDownloadWS, 3000);
    };

    _ws.onerror = function () {
      _ws.close();
    };
  }

  function _updateBadge() {
    const active = Object.values(_jobs).filter(j => j.status === 'queued' || j.status === 'downloading');
    const badge = document.getElementById('download-badge');
    if (badge) {
      badge.textContent = active.length || '';
      badge.style.display = active.length ? 'flex' : 'none';
    }
  }

  // ── İndirme Kuyruğu Başlatma ─────────────────────────────────────
  async function startDownload(contentId, contentTitle, mediaType, episodeNumber, url, quality) {
    try {
      const r = await fetch(API + '/api/download/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content_id: contentId,
          content_title: contentTitle,
          media_type: mediaType,
          episode_number: episodeNumber,
          url: url,
          quality: quality || '720p',
        }),
      });
      if (!r.ok) throw new Error(r.status);
      const job = await r.json();
      _jobs[job.id] = job;
      _renderDownloadScreen();
      _updateBadge();
      window.kuroNav && window.kuroNav.show('screen-downloads');
      return job;
    } catch (err) {
      alert('İndirme başlatılamadı: ' + err.message);
    }
  }

  async function cancelJob(jobId) {
    await fetch(API + '/api/download/' + jobId, { method: 'DELETE' });
    delete _jobs[jobId];
    _renderDownloadScreen();
    _updateBadge();
  }

  // ── Depolama Bilgisi ─────────────────────────────────────────────
  async function _fetchStorage() {
    try {
      const r = await fetch(API + '/api/download/storage');
      if (!r.ok) return null;
      return r.json();
    } catch { return null; }
  }

  // ── İndirmeler Ekranı Render ──────────────────────────────────────
  function _fmtSize(bytes) {
    if (!bytes) return '0 B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
    return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB';
  }

  function _statusBadge(job) {
    const map = {
      queued:      ['bg-[#3b4665] text-[#9090b0]', 'Kuyrukta'],
      downloading: ['bg-[#00d4ff]/20 text-[#00d4ff]', 'İndiriliyor'],
      done:        ['bg-[#90e090]/20 text-[#90e090]', 'Hazır'],
      failed:      ['bg-[#ffb4ab]/20 text-[#ffb4ab]', 'Hata'],
      cancelled:   ['bg-[#3b4665] text-[#9090b0]', 'İptal'],
      deleted:     ['bg-[#3b4665] text-[#9090b0]', 'Silindi'],
    };
    const [cls, label] = map[job.status] || ['bg-[#3b4665]', job.status];
    return `<span class="text-xs px-2 py-0.5 rounded-full font-medium ${cls}">${label}</span>`;
  }

  function _jobCard(job) {
    const ep = job.media_type === 'anime' ? `Bölüm ${job.episode_number}` : `Bölüm ${job.episode_number}`;
    const size = job.file_size_bytes ? _fmtSize(job.file_size_bytes) : '';

    let progressBar = '';
    if (job.status === 'downloading' || job.status === 'queued') {
      progressBar = `
        <div class="w-full bg-white/10 rounded-full h-1.5 mt-2 overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500 ${job.status === 'downloading' ? 'bg-[#00d4ff]' : 'bg-[#3b4665]'}"
               style="width:${job.progress_pct || 0}%"></div>
        </div>
        <div class="text-xs text-[#9090b0] mt-1">${job.progress_pct || 0}%</div>`;
    }

    let actions = '';
    if (job.status === 'done') {
      if (job.media_type === 'anime') {
        actions = `<button onclick="window.kuroPlayer.openVideo(${job.id},'${escHtml(job.content_title)} — ${ep}')"
                     class="text-xs px-3 py-1.5 rounded-lg bg-[#00d4ff]/20 text-[#00d4ff] hover:bg-[#00d4ff]/30 transition-colors min-h-[36px]">
                     ▶ Oynat</button>`;
      } else {
        actions = `<button onclick="window.kuroReader.open(${job.id},'${escHtml(job.content_title)} — ${ep}')"
                     class="text-xs px-3 py-1.5 rounded-lg bg-[#ffd9a1]/20 text-[#ffd9a1] hover:bg-[#ffd9a1]/30 transition-colors min-h-[36px]">
                     📖 Oku</button>`;
      }
      actions += `<button onclick="window.kuroDownload.cancel(${job.id})"
                   class="text-xs px-3 py-1.5 rounded-lg bg-[#ffb4ab]/10 text-[#ffb4ab] hover:bg-[#ffb4ab]/20 transition-colors min-h-[36px] ml-2">
                   🗑 Sil</button>`;
    } else if (job.status === 'queued') {
      actions = `<button onclick="window.kuroDownload.cancel(${job.id})"
                   class="text-xs px-3 py-1.5 rounded-lg bg-[#3b4665] text-[#9090b0] hover:bg-white/10 transition-colors min-h-[36px]">
                   ✕ İptal</button>`;
    } else if (job.status === 'failed') {
      actions = `<span class="text-xs text-[#ffb4ab] truncate max-w-[200px]" title="${escHtml(job.error_msg || '')}">${escHtml((job.error_msg || 'Bilinmeyen hata').substring(0, 60))}</span>`;
    }

    return `
      <div class="glass-card rounded-xl p-4 flex flex-col gap-2">
        <div class="flex items-start justify-between gap-3">
          <div class="flex flex-col gap-1 min-w-0">
            <div class="font-medium text-sm truncate text-[#e1e0ff]">${escHtml(job.content_title)}</div>
            <div class="text-xs text-[#9090b0]">${ep} · ${escHtml(job.media_type)} ${size ? '· ' + size : ''}</div>
          </div>
          ${_statusBadge(job)}
        </div>
        ${progressBar}
        ${actions ? `<div class="flex items-center mt-1">${actions}</div>` : ''}
      </div>`;
  }

  async function _renderDownloadScreen() {
    const el = document.getElementById('downloads-list');
    if (!el) return;

    const jobs = Object.values(_jobs).sort((a, b) => b.id - a.id);
    if (jobs.length === 0) {
      el.innerHTML = `<div class="text-center text-[#9090b0] py-12">
        <div class="text-4xl mb-3">📥</div>
        <div>Henüz indirme yok</div>
        <div class="text-xs mt-1">İçerik detayından bölüm indir</div>
      </div>`;
      return;
    }

    el.innerHTML = jobs.map(_jobCard).join('');

    // Depolama güncelle
    const storage = await _fetchStorage();
    const storageEl = document.getElementById('downloads-storage');
    if (storageEl && storage) {
      storageEl.textContent = _fmtSize(storage.bytes) + ' kullanılıyor';
    }
  }

  // ── Skip Intro ───────────────────────────────────────────────────
  const _intro = {
    start: null,
    end:   null,

    async load(contentId, episodeNumber) {
      this.start = null;
      this.end   = null;
      const skipBtn = document.getElementById('skip-intro-btn');
      if (skipBtn) skipBtn.classList.add('hidden');
      if (!contentId || !episodeNumber) return;
      try {
        const r = await fetch(`${API}/api/analyze/intro/${contentId}/${episodeNumber}`);
        if (!r.ok) return;
        const d = await r.json();
        if (d.found) {
          this.start = d.start;
          this.end   = d.end;
        }
      } catch {}
    },

    tick(currentTime) {
      const btn = document.getElementById('skip-intro-btn');
      if (!btn) return;
      if (this.start !== null && currentTime >= this.start && currentTime < this.end) {
        btn.classList.remove('hidden');
      } else {
        btn.classList.add('hidden');
      }
    },

    skip() {
      const video = document.getElementById('player-video');
      if (video && this.end !== null) {
        video.currentTime = this.end;
      }
      const btn = document.getElementById('skip-intro-btn');
      if (btn) btn.classList.add('hidden');
    },
  };

  // ── Video Player ─────────────────────────────────────────────────
  const _player = {
    open: function (jobId, title, contentId, episodeNumber) {
      const modal = document.getElementById('modal-player');
      const video = document.getElementById('player-video');
      const src   = document.getElementById('player-source');
      const ttl   = document.getElementById('player-title');
      if (!modal || !video || !src) return;

      src.src = API + '/api/download/serve/' + jobId;
      video.load();
      if (ttl) ttl.textContent = title || '';
      modal.classList.remove('hidden');
      modal.classList.add('open');
      document.body.style.overflow = 'hidden';
      video.play().catch(() => {});

      // Daisy-chain tetikleyici: %50 oynandığında sonraki bölüm kuyruğa alınır
      video.dataset.jobId = jobId;
      video.dataset.contentId = contentId || '';
      video.dataset.episodeNumber = episodeNumber || '';
      video._daisyTriggered = false;

      // Skip Intro — intro zamanlarını yükle
      _intro.load(contentId, episodeNumber);
    },

    close: function () {
      const modal = document.getElementById('modal-player');
      const video = document.getElementById('player-video');
      if (video) { video.pause(); video.src = ''; }
      if (modal) { modal.classList.add('hidden'); modal.classList.remove('open'); }
      document.body.style.overflow = '';
      const skipBtn = document.getElementById('skip-intro-btn');
      if (skipBtn) skipBtn.classList.add('hidden');
    },

    openVideo: function (jobId, title) {
      const job = _jobs[jobId];
      const contentId = job ? job.content_id : null;
      const epNum     = job ? job.episode_number : null;
      this.open(jobId, title, contentId, epNum);
    },
  };

  // timeupdate: Skip Intro göster/gizle + Daisy-chain
  document.addEventListener('timeupdate', function (e) {
    const video = e.target;
    if (!video || video.tagName !== 'VIDEO') return;

    // Skip Intro tick
    _intro.tick(video.currentTime);

    // Daisy-chain: %50 oynandığında sonraki bölüm kuyruğa al
    if (!video._daisyTriggered && video.duration > 0) {
      const pct = (video.currentTime / video.duration) * 100;
      if (pct >= 50) {
        video._daisyTriggered = true;
        const jobId = parseInt(video.dataset.jobId, 10);
        const job = _jobs[jobId];
        if (job) {
          const nextEp = job.episode_number + 1;
          const exists = Object.values(_jobs).some(
            j => j.content_id === job.content_id && j.episode_number === nextEp
          );
          if (!exists) {
            fetch(API + '/api/content/' + job.content_id + '/episodes')
              .then(r => r.json())
              .then(eps => {
                const next = eps.find(e => e.number === nextEp);
                if (next && next.url) {
                  startDownload(job.content_id, job.content_title, job.media_type,
                                nextEp, next.url, job.quality || '720p');
                }
              })
              .catch(() => {});
          }
        }
      }
    }
  }, true);

  // ── Manga Reader ─────────────────────────────────────────────────
  const _reader = {
    _pages: [],
    _current: 0,
    _webtoon: true,

    open: async function (jobId, title) {
      const modal = document.getElementById('modal-reader');
      const ttl   = document.getElementById('reader-title');
      if (!modal) return;

      if (ttl) ttl.textContent = title || '';
      modal.classList.remove('hidden');
      modal.classList.add('open');
      document.body.style.overflow = 'hidden';

      try {
        const r = await fetch(API + '/api/download/pages/' + jobId);
        if (!r.ok) throw new Error(r.status);
        const data = await r.json();
        this._pages = data.pages || [];
        this._current = 0;
        this._render();
      } catch (err) {
        const pagesEl = document.getElementById('reader-pages');
        if (pagesEl) pagesEl.innerHTML = `<div class="text-[#ffb4ab] p-4">Sayfalar yüklenemedi: ${err.message}</div>`;
      }
    },

    close: function () {
      const modal = document.getElementById('modal-reader');
      if (modal) { modal.classList.add('hidden'); modal.classList.remove('open'); }
      document.body.style.overflow = '';
      this._pages = [];
    },

    toggleMode: function () {
      this._webtoon = !this._webtoon;
      this._current = 0;
      this._render();
      const btn = document.getElementById('reader-mode-btn');
      if (btn) btn.textContent = this._webtoon ? '↕ Webtoon' : '📄 Sayfa';
    },

    _render: function () {
      const pagesEl = document.getElementById('reader-pages');
      if (!pagesEl || this._pages.length === 0) return;

      if (this._webtoon) {
        // Dikey scroll — tüm sayfalar
        pagesEl.innerHTML = this._pages.map((url, i) =>
          `<img src="${API + url}" alt="Sayfa ${i + 1}"
                class="w-full block" loading="lazy"
                style="max-width:800px;margin:0 auto;display:block;">`
        ).join('');
        document.getElementById('reader-nav') && (document.getElementById('reader-nav').style.display = 'none');
      } else {
        // Sayfa modu — tek sayfa
        const nav = document.getElementById('reader-nav');
        if (nav) nav.style.display = 'flex';
        pagesEl.innerHTML = `
          <img src="${API + this._pages[this._current]}"
               alt="Sayfa ${this._current + 1}"
               class="w-full block" style="max-width:800px;margin:0 auto;display:block;">
          <div class="text-center text-[#9090b0] text-sm py-2">${this._current + 1} / ${this._pages.length}</div>`;
      }
    },

    prev: function () {
      if (this._current > 0) { this._current--; this._render(); }
      document.getElementById('modal-reader').scrollTop = 0;
    },

    next: function () {
      if (this._current < this._pages.length - 1) { this._current++; this._render(); }
      document.getElementById('modal-reader').scrollTop = 0;
    },
  };

  // ── Yardımcı ─────────────────────────────────────────────────────
  function escHtml(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // ── Dışa Aç ──────────────────────────────────────────────────────
  window.kuroPlayer   = _player;
  window.kuroReader   = _reader;
  window.kuroIntro    = _intro;
  window.kuroDownload = {
    start:  startDownload,
    cancel: cancelJob,
    render: _renderDownloadScreen,
    analyzeIntro: async function (contentId) {
      try {
        const r = await fetch(`${API}/api/analyze/intro/${contentId}`, { method: 'POST' });
        const d = await r.json();
        alert(`İntro analizi başladı: ${d.episode_count} bölüm. Birkaç dakika içinde tamamlanır.`);
      } catch (err) {
        alert('Analiz başlatılamadı: ' + err.message);
      }
    },
  };

  // ── Başlat ───────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    connectDownloadWS();

    // Player kapat
    const playerClose = document.getElementById('player-close');
    if (playerClose) playerClose.addEventListener('click', () => _player.close());

    // Skip Intro butonu
    const skipIntroBtn = document.getElementById('skip-intro-btn');
    if (skipIntroBtn) skipIntroBtn.addEventListener('click', () => _intro.skip());

    // Reader kapat
    const readerClose = document.getElementById('reader-close');
    if (readerClose) readerClose.addEventListener('click', () => _reader.close());

    // Reader mod değiştir
    const readerMode = document.getElementById('reader-mode-btn');
    if (readerMode) readerMode.addEventListener('click', () => _reader.toggleMode());

    // Reader sayfa nav
    const readerPrev = document.getElementById('reader-prev');
    const readerNext = document.getElementById('reader-next');
    if (readerPrev) readerPrev.addEventListener('click', () => _reader.prev());
    if (readerNext) readerNext.addEventListener('click', () => _reader.next());

    // Keyboard shortcuts
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        const playerModal = document.getElementById('modal-player');
        const readerModal = document.getElementById('modal-reader');
        if (playerModal && playerModal.classList.contains('open')) { _player.close(); return; }
        if (readerModal && readerModal.classList.contains('open')) { _reader.close(); return; }
      }
      const readerModal = document.getElementById('modal-reader');
      if (!readerModal || !readerModal.classList.contains('open')) return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') _reader.next();
      if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   _reader.prev();
    });

    // downloads ekranı açılınca render et
    const origShow = window.kuroNav && window.kuroNav.show;
    // patch showScreen: downloads ekranı açılınca _renderDownloadScreen çağrılsın
    // (app.js zaten showScreen içinde id'ye göre render çağırıyor, orayı güncelleyeceğiz)
  });

})();
