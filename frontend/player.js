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
        actions = `<button onclick="window.kuroReader.open(${job.id},'${escHtml(job.content_title)} — ${ep}',${job.content_id},${job.episode_number})"
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

  // ── Ambient Mode ─────────────────────────────────────────────────
  const _ambient = {
    _raf: null,
    active: false,

    toggle() {
      this.active = !this.active;
      const canvas = document.getElementById('ambient-canvas');
      const btn    = document.getElementById('player-ambient-btn');
      if (!canvas) return;
      if (this.active) {
        canvas.classList.remove('hidden');
        if (btn) btn.classList.add('text-[#00d4ff]');
        this._loop();
      } else {
        canvas.classList.add('hidden');
        if (btn) btn.classList.remove('text-[#00d4ff]');
        if (this._raf) { cancelAnimationFrame(this._raf); this._raf = null; }
      }
    },

    _loop() {
      const video  = document.getElementById('player-video');
      const canvas = document.getElementById('ambient-canvas');
      if (!canvas || !video || !this.active) return;
      const ctx = canvas.getContext('2d');
      if (canvas.width !== 64) { canvas.width = 64; canvas.height = 36; }
      if (video.readyState >= 2) ctx.drawImage(video, 0, 0, 64, 36);
      this._raf = requestAnimationFrame(() => { setTimeout(() => this._loop(), 80); });
    },

    stop() {
      this.active = false;
      const canvas = document.getElementById('ambient-canvas');
      if (canvas) canvas.classList.add('hidden');
      const btn = document.getElementById('player-ambient-btn');
      if (btn) btn.classList.remove('text-[#00d4ff]');
      if (this._raf) { cancelAnimationFrame(this._raf); this._raf = null; }
    },
  };

  // ── Theater Mode ─────────────────────────────────────────────────
  let _theaterActive = false;
  function _toggleTheater() {
    const modal = document.getElementById('modal-player');
    const btn   = document.getElementById('player-theater-btn');
    if (!modal) return;
    _theaterActive = !_theaterActive;
    modal.classList.toggle('player-theater', _theaterActive);
    if (btn) btn.classList.toggle('text-[#00d4ff]', _theaterActive);
  }

  // ── Picture-in-Picture ───────────────────────────────────────────
  async function _togglePiP() {
    const video = document.getElementById('player-video');
    if (!video) return;
    try {
      if (document.pictureInPictureElement) {
        await document.exitPictureInPicture();
      } else {
        await video.requestPictureInPicture();
      }
    } catch {}
  }

  // ── Mini Player ──────────────────────────────────────────────────
  let _miniActive = false;
  function _toggleMini() {
    const modal = document.getElementById('modal-player');
    const btn   = document.getElementById('player-mini-btn');
    if (!modal) return;
    _miniActive = !_miniActive;
    modal.classList.toggle('player-mini', _miniActive);
    if (btn) btn.classList.toggle('text-[#00d4ff]', _miniActive);
  }

  // ── Fullscreen ───────────────────────────────────────────────────
  function _toggleFullscreen() {
    const modal = document.getElementById('modal-player');
    const btn   = document.getElementById('player-fullscreen-btn');
    if (!modal) return;
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
      if (btn) btn.querySelector('span').textContent = 'fullscreen';
    } else {
      (modal.requestFullscreen || modal.webkitRequestFullscreen).call(modal).catch(() => {});
      if (btn) btn.querySelector('span').textContent = 'fullscreen_exit';
    }
  }

  // ── Subtitle (CC) ────────────────────────────────────────────────
  let _ccActive = false;
  async function _loadSubtitles(jobId) {
    const track = document.getElementById('subtitle-track');
    if (!track) return;
    track.src = '';
    try {
      const r = await fetch(API + '/api/download/subtitles/' + jobId);
      if (!r.ok) return;
      const blob = await r.blob();
      track.src = URL.createObjectURL(blob);
      track.mode = 'hidden';
    } catch {}
  }

  function _toggleCC() {
    const video = document.getElementById('player-video');
    const btn   = document.getElementById('player-cc-btn');
    if (!video || !video.textTracks.length) return;
    _ccActive = !_ccActive;
    video.textTracks[0].mode = _ccActive ? 'showing' : 'hidden';
    if (btn) btn.classList.toggle('text-[#00d4ff]', _ccActive);
  }

  // ── Auto-Next Episode ────────────────────────────────────────────
  const _autoNext = {
    _timer: null,
    _shown: false,
    _nextJobId: null,

    reset() {
      clearInterval(this._timer);
      this._timer = null;
      this._shown = false;
      this._nextJobId = null;
      const overlay = document.getElementById('autonext-overlay');
      if (overlay) overlay.classList.add('hidden');
      const bar = document.getElementById('autonext-bar');
      if (bar) bar.style.width = '0%';
      const count = document.getElementById('autonext-count');
      if (count) count.textContent = '10';
    },

    check(currentTime, duration) {
      if (!duration || this._shown || duration - currentTime > 30) return;
      const video = document.getElementById('player-video');
      if (!video) return;
      const jobId = parseInt(video.dataset.jobId, 10);
      const job   = _jobs[jobId];
      if (!job) return;
      const nextEp  = job.episode_number + 1;
      const nextJob = Object.values(_jobs).find(
        j => j.content_id === job.content_id && j.episode_number === nextEp && j.status === 'done'
      );
      if (!nextJob) return;

      this._shown    = true;
      this._nextJobId = nextJob.id;
      let count = 10;

      const overlay  = document.getElementById('autonext-overlay');
      const titleEl  = document.getElementById('autonext-title');
      const countEl  = document.getElementById('autonext-count');
      const bar      = document.getElementById('autonext-bar');

      if (titleEl)  titleEl.textContent  = job.content_title + ' — Bölüm ' + nextEp;
      if (overlay)  overlay.classList.remove('hidden');

      this._timer = setInterval(() => {
        count--;
        if (countEl) countEl.textContent = count;
        if (bar)     bar.style.width = ((10 - count) * 10) + '%';
        if (count <= 0) {
          clearInterval(this._timer);
          const nId  = this._nextJobId;
          const nJob = nId !== null ? _jobs[nId] : null;
          this.reset();
          if (nJob) {
            _player.close();
            setTimeout(() => _player.openVideo(nJob.id, nJob.content_title + ' — Bölüm ' + nJob.episode_number), 200);
          }
        }
      }, 1000);
    },
  };

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

  // ── Skip Outro ───────────────────────────────────────────────────
  const _outro = {
    start: null,
    end:   null,

    async load(contentId, episodeNumber) {
      this.start = null;
      this.end   = null;
      const btn = document.getElementById('skip-outro-btn');
      if (btn) btn.classList.add('hidden');
      if (!contentId || !episodeNumber) return;
      try {
        const r = await fetch(`${API}/api/analyze/outro/${contentId}/${episodeNumber}`);
        if (!r.ok) return;
        const d = await r.json();
        if (d.found) {
          this.start = d.start;
          this.end   = d.end;
        }
      } catch {}
    },

    tick(currentTime) {
      const introBtn = document.getElementById('skip-intro-btn');
      const outroBtn = document.getElementById('skip-outro-btn');
      if (!outroBtn) return;
      // Outro butonu: intro bölümü değilken ve outro bölümündeyken göster
      const inIntro = introBtn && !introBtn.classList.contains('hidden');
      if (!inIntro && this.start !== null && currentTime >= this.start && currentTime < this.end) {
        outroBtn.classList.remove('hidden');
      } else {
        outroBtn.classList.add('hidden');
      }
    },

    skip() {
      const video = document.getElementById('player-video');
      if (video && this.end !== null) {
        video.currentTime = this.end - 1;  // bitiş - 1sn (son frame donmasın)
      }
      const btn = document.getElementById('skip-outro-btn');
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

      // Mini modunu çıkar, tam ekrana aç
      modal.classList.remove('player-mini', 'player-theater');
      _miniActive    = false;
      _theaterActive = false;
      modal.classList.remove('hidden');
      modal.classList.add('open');
      document.body.style.overflow = 'hidden';
      video.play().catch(() => {});

      video.dataset.jobId        = jobId;
      video.dataset.contentId    = contentId || '';
      video.dataset.episodeNumber = episodeNumber || '';
      video._daisyTriggered      = false;

      _intro.load(contentId, episodeNumber);
      _outro.load(contentId, episodeNumber);
      _autoNext.reset();
      _loadSubtitles(jobId);
      _ccActive = false;
      const ccBtn = document.getElementById('player-cc-btn');
      if (ccBtn) ccBtn.classList.remove('text-[#00d4ff]');
    },

    close: function () {
      const modal = document.getElementById('modal-player');
      const video = document.getElementById('player-video');
      if (video) { video.pause(); video.src = ''; }
      if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('open', 'player-mini', 'player-theater');
      }
      document.body.style.overflow = '';
      const skipBtn = document.getElementById('skip-intro-btn');
      if (skipBtn) skipBtn.classList.add('hidden');
      const outroBtn = document.getElementById('skip-outro-btn');
      if (outroBtn) outroBtn.classList.add('hidden');
      _ambient.stop();
      _autoNext.reset();
      _miniActive    = false;
      _theaterActive = false;
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    },

    openVideo: function (jobId, title) {
      const job = _jobs[jobId];
      const contentId = job ? job.content_id : null;
      const epNum     = job ? job.episode_number : null;
      this.open(jobId, title, contentId, epNum);
    },
  };

  // timeupdate: Skip Intro + Auto-Next + Daisy-chain
  document.addEventListener('timeupdate', function (e) {
    const video = e.target;
    if (!video || video.tagName !== 'VIDEO') return;

    _intro.tick(video.currentTime);
    _outro.tick(video.currentTime);
    _autoNext.check(video.currentTime, video.duration);

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
            Promise.all([
              fetch(API + '/api/content/' + job.content_id + '/episodes').then(r => r.json()),
              fetch(API + '/api/settings').then(r => r.json()).catch(() => ({})),
            ]).then(function(results) {
              const eps = results[0];
              const settings = results[1];
              const autoQ = settings.download_quality_auto || '480p';
              const next = eps.find(ep => ep.number === nextEp);
              if (next && next.url) {
                startDownload(job.content_id, job.content_title, job.media_type,
                              nextEp, next.url, autoQ);
              }
            }).catch(() => {});
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
    _trPages: null,
    _showTr: false,
    _contentId: null,
    _episodeNumber: null,

    open: async function (jobId, title, contentId, episodeNumber) {
      const modal = document.getElementById('modal-reader');
      const ttl   = document.getElementById('reader-title');
      if (!modal) return;

      this._contentId    = contentId    || null;
      this._episodeNumber = episodeNumber || null;
      this._trPages = null;
      this._showTr  = false;

      const toggle = document.getElementById('reader-lang-toggle');
      if (toggle) toggle.style.display = 'none';
      const trBtn = document.getElementById('reader-translate-btn');
      if (trBtn) { trBtn.style.display = 'none'; trBtn.disabled = false; }
      const trLabel = document.getElementById('reader-translate-label');
      if (trLabel) trLabel.textContent = 'Çevir';

      if (ttl) ttl.textContent = title || '';
      modal.classList.remove('hidden');
      modal.classList.add('open');
      document.body.style.overflow = 'hidden';

      if (contentId && episodeNumber) {
        _translate.init(contentId, episodeNumber);
      }

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
      this._trPages = null;
      this._showTr  = false;
      if (this._autoNextTimer) { clearInterval(this._autoNextTimer); this._autoNextTimer = null; }
      const overlay = document.getElementById('reader-autonext');
      if (overlay) overlay.remove();
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
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
      const pages = (this._showTr && this._trPages && this._trPages.length)
        ? this._trPages : this._pages;
      if (!pagesEl || pages.length === 0) return;

      if (this._webtoon) {
        // Dikey scroll — tüm sayfalar
        pagesEl.innerHTML = pages.map((url, i) =>
          `<img src="${API + url}" alt="Sayfa ${i + 1}"
                loading="lazy"
                style="width:100%;max-width:800px;margin:0 auto;display:block;height:auto;">`
        ).join('');
        document.getElementById('reader-nav') && (document.getElementById('reader-nav').style.display = 'none');
      } else {
        // Sayfa modu — tek sayfa, viewport yüksekliğine sığdır
        const nav = document.getElementById('reader-nav');
        if (nav) nav.style.display = 'flex';
        pagesEl.innerHTML = `
          <img src="${API + pages[this._current]}"
               alt="Sayfa ${this._current + 1}"
               style="width:auto;height:auto;max-width:100%;max-height:calc(100dvh - 130px);margin:0 auto;display:block;object-fit:contain;">
          <div class="text-center text-[#9090b0] text-sm py-2">${this._current + 1} / ${pages.length}</div>`;
      }
    },

    prev: function () {
      if (this._current > 0) { this._current--; this._render(); }
      document.getElementById('modal-reader').scrollTop = 0;
    },

    next: function () {
      if (this._current < this._pages.length - 1) {
        this._current++;
        this._render();
        document.getElementById('modal-reader').scrollTop = 0;
      } else if (!this._webtoon) {
        // Son sayfa → auto-next chapter
        this._triggerAutoNextChapter();
      }
    },

    toggleFullscreen() {
      const modal = document.getElementById('modal-reader');
      const btn   = document.getElementById('reader-fullscreen-btn');
      if (!modal) return;
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {});
        if (btn) btn.querySelector('span').textContent = 'fullscreen';
      } else {
        (modal.requestFullscreen || modal.webkitRequestFullscreen).call(modal).catch(() => {});
        if (btn) btn.querySelector('span').textContent = 'fullscreen_exit';
      }
    },

    _autoNextTimer: null,
    _triggerAutoNextChapter() {
      if (this._autoNextTimer) return;
      let count = 5;
      const overlay = document.createElement('div');
      overlay.id = 'reader-autonext';
      overlay.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:rgba(13,13,26,0.92);border:1px solid rgba(255,255,255,0.15);border-radius:12px;padding:12px 20px;z-index:20;display:flex;align-items:center;gap:12px;backdrop-filter:blur(8px);font-size:13px;';
      overlay.innerHTML = '<span style="color:#9090b0">Sonraki bölüm: <strong id="rc-count" style="color:#00d4ff">' + count + '</strong>s</span>'
        + '<button id="rc-cancel" style="color:#9090b0;background:none;border:none;cursor:pointer;font-size:12px;padding:4px 8px;border-radius:6px;">İptal</button>';
      document.body.appendChild(overlay);

      document.getElementById('rc-cancel').onclick = () => {
        clearInterval(this._autoNextTimer);
        this._autoNextTimer = null;
        overlay.remove();
      };

      this._autoNextTimer = setInterval(() => {
        count--;
        const el = document.getElementById('rc-count');
        if (el) el.textContent = count;
        if (count <= 0) {
          clearInterval(this._autoNextTimer);
          this._autoNextTimer = null;
          overlay.remove();
          // Sonraki bölüm yükle (jobId context reader close ile kaybolur — şimdilik kapat)
          this.close();
        }
      }, 1000);
    },
  };

  // ── FAZ-5 Manga Çevirisi ─────────────────────────────────────────
  const _translate = {
    _gpu: null,     // null=kontrol edilmedi, false=yok, object=var
    _ws:  null,
    _contentId: null,
    _episode:   null,

    async checkGpu() {
      if (this._gpu !== null) return this._gpu;
      try {
        const r = await fetch(API + '/api/system/gpu');
        if (!r.ok) { this._gpu = false; return false; }
        const d = await r.json();
        this._gpu = d.available ? d : false;
      } catch { this._gpu = false; }
      return this._gpu;
    },

    async init(contentId, episodeNumber) {
      this._contentId = contentId;
      this._episode   = episodeNumber;

      // Önce mevcut çeviri durumunu kontrol et
      try {
        const r = await fetch(`${API}/api/translate/${contentId}/${episodeNumber}`);
        if (r.ok) {
          const s = await r.json();
          this._applyStatus(s);
        }
      } catch {}

      // GPU var mı?
      const gpu = await this.checkGpu();
      const btn = document.getElementById('reader-translate-btn');
      if (btn && gpu) btn.style.display = 'flex';
    },

    _applyStatus(status) {
      const toggle = document.getElementById('reader-lang-toggle');
      const btn    = document.getElementById('reader-translate-btn');
      const label  = document.getElementById('reader-translate-label');

      if (!status || status.status === 'not_started') {
        if (toggle) toggle.style.display = 'none';
        if (label) label.textContent = 'Çevir';
        if (btn) btn.disabled = false;
      } else if (status.status === 'translating') {
        if (toggle) toggle.style.display = 'none';
        const pct = status.pages_total > 0 ? `${status.pages_done}/${status.pages_total}` : '…';
        if (label) label.textContent = pct;
        if (btn) btn.disabled = true;
        this._connectWS();
      } else if (status.status === 'done') {
        if (toggle) toggle.style.display = 'flex';
        if (label) label.textContent = '✓ Çevrildi';
        if (btn) btn.disabled = true;
      } else if (status.status === 'failed') {
        if (label) label.textContent = 'Tekrar Dene';
        if (btn) btn.disabled = false;
      }
    },

    async startTranslate() {
      const { _contentId: cid, _episode: ep } = this;
      if (!cid || !ep) return;
      const label = document.getElementById('reader-translate-label');
      const btn   = document.getElementById('reader-translate-btn');
      if (label) label.textContent = 'Başlatılıyor…';
      if (btn) btn.disabled = true;
      try {
        const r = await fetch(`${API}/api/translate/${cid}/${ep}`, { method: 'POST' });
        if (!r.ok) throw new Error(r.status);
        this._connectWS();
      } catch {
        if (label) label.textContent = 'Hata';
        if (btn) btn.disabled = false;
      }
    },

    _connectWS() {
      if (this._ws && this._ws.readyState < 2) return;
      this._ws = new WebSocket('ws://localhost:8099/api/translate/ws');
      this._ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.event === 'progress') {
          const label = document.getElementById('reader-translate-label');
          if (label) label.textContent = `${msg.pages_done}/${msg.pages_total}`;
        } else if (msg.event === 'done') {
          this._applyStatus({ status: 'done' });
        } else if (msg.event === 'failed') {
          this._applyStatus({ status: 'failed' });
        }
      };
    },

    async showTranslated() {
      const { _contentId: cid, _episode: ep } = this;
      if (!cid || !ep) return;
      try {
        const r = await fetch(`${API}/api/translate/pages/${cid}/${ep}`);
        if (!r.ok) return;
        const d = await r.json();
        if (d.pages && d.pages.length) {
          _reader._trPages = d.pages;
          _reader._showTr  = true;
          _reader._render();
          this._setLang('tr');
        }
      } catch {}
    },

    showOriginal() {
      _reader._showTr  = false;
      _reader._trPages = null;
      _reader._render();
      this._setLang('original');
    },

    _setLang(lang) {
      const orgBtn = document.getElementById('reader-lang-original');
      const trBtn  = document.getElementById('reader-lang-tr');
      const fixBtn = document.getElementById('reader-fix-btn');
      if (!orgBtn || !trBtn) return;
      const active   = 'px-3 py-1.5 bg-[#00d4ff]/20 text-[#00d4ff] font-medium transition-colors';
      const inactive = 'px-3 py-1.5 bg-[#1c1d37] text-[#9090b0] hover:text-white transition-colors';
      orgBtn.className = lang === 'tr' ? inactive : active;
      trBtn.className  = lang === 'tr' ? active   : inactive;
      if (fixBtn) fixBtn.style.display = lang === 'tr' ? 'flex' : 'none';
    },

    showFixModal() {
      const page = _reader._current;
      const cid  = this._contentId;
      const ep   = this._episode;

      const old = document.getElementById('kw-fix-modal');
      if (old) old.remove();

      const modal = document.createElement('div');
      modal.id = 'kw-fix-modal';
      modal.style.cssText = 'position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.75);backdrop-filter:blur(4px);padding:16px';
      modal.innerHTML =
        '<div style="background:#1a2123;border:1px solid rgba(255,217,161,0.3);border-radius:16px;padding:24px;width:100%;max-width:480px;display:flex;flex-direction:column;gap:16px">' +
          '<div style="display:flex;justify-content:space-between;align-items:center">' +
            '<span style="font-size:14px;font-weight:700;color:#ffd9a1">✏️ Sayfa ' + (page + 1) + ' — Çeviri Düzeltme</span>' +
            '<button id="kw-fix-close" style="background:none;border:none;color:#9090b0;cursor:pointer;font-size:20px;line-height:1;padding:4px">✕</button>' +
          '</div>' +
          '<textarea id="kw-fix-input" style="width:100%;min-height:120px;background:#0d0d1a;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:12px;color:#e1e0ff;font-size:14px;resize:vertical;font-family:inherit;box-sizing:border-box" placeholder="Düzeltilmiş çeviriyi gir..."></textarea>' +
          '<button id="kw-fix-save" style="height:44px;background:#ffd9a1;color:#1a0a00;font-weight:700;border:none;border-radius:8px;cursor:pointer;font-size:14px">Kaydet</button>' +
        '</div>';
      document.body.appendChild(modal);

      const closeModal = function() { modal.remove(); };
      document.getElementById('kw-fix-close').onclick = closeModal;
      modal.addEventListener('click', function(e) { if (e.target === modal) closeModal(); });

      document.getElementById('kw-fix-save').onclick = async function() {
        const text = (document.getElementById('kw-fix-input').value || '').trim();
        const btn  = document.getElementById('kw-fix-save');
        btn.disabled = true;
        btn.textContent = 'Kaydediliyor...';
        try {
          const r = await fetch(API + '/api/translate/' + cid + '/' + ep + '/' + page, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text }),
          });
          if (!r.ok) throw new Error(r.status);
          closeModal();
        } catch(err) {
          btn.disabled = false;
          btn.textContent = 'Hata — Tekrar Dene';
        }
      };

      const inp = document.getElementById('kw-fix-input');
      if (inp) inp.focus();
    },
  };

  // ── Yardımcı ─────────────────────────────────────────────────────
  function escHtml(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // ── Dışa Aç ──────────────────────────────────────────────────────
  window.kuroPlayer    = _player;
  window.kuroReader    = _reader;
  window.kuroIntro     = _intro;
  window.kuroOutro     = _outro;
  window.kuroTranslate = _translate;
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

    // ── Player Butonları ──────────────────────────────────────────
    const _pb = (id, fn) => { const el = document.getElementById(id); if (el) el.addEventListener('click', fn); };
    _pb('player-close',        () => _player.close());
    _pb('skip-intro-btn',      () => _intro.skip());
    _pb('skip-outro-btn',      () => _outro.skip());
    _pb('player-ambient-btn',  () => _ambient.toggle());
    _pb('player-theater-btn',  () => _toggleTheater());
    _pb('player-pip-btn',      () => _togglePiP());
    _pb('player-mini-btn',     () => _toggleMini());
    _pb('player-fullscreen-btn', () => _toggleFullscreen());
    _pb('player-cc-btn',       () => _toggleCC());
    _pb('autonext-cancel',     () => _autoNext.reset());

    // ── Reader Butonları ──────────────────────────────────────────
    _pb('reader-close',          () => _reader.close());
    _pb('reader-mode-btn',       () => _reader.toggleMode());
    _pb('reader-prev',           () => _reader.prev());
    _pb('reader-next',           () => _reader.next());
    _pb('reader-fullscreen-btn', () => _reader.toggleFullscreen());
    _pb('reader-translate-btn',  () => _translate.startTranslate());
    _pb('reader-lang-original',  () => _translate.showOriginal());
    _pb('reader-lang-tr',        () => _translate.showTranslated());
    _pb('reader-fix-btn',        () => _translate.showFixModal());

    // ── Reader Swipe ──────────────────────────────────────────────
    let _swipeStartX = 0, _swipeStartY = 0;
    const readerEl = document.getElementById('modal-reader');
    if (readerEl) {
      readerEl.addEventListener('touchstart', function (e) {
        _swipeStartX = e.touches[0].clientX;
        _swipeStartY = e.touches[0].clientY;
      }, { passive: true });

      readerEl.addEventListener('touchend', function (e) {
        if (!_reader._pages.length || _reader._webtoon) return;
        const dx = e.changedTouches[0].clientX - _swipeStartX;
        const dy = e.changedTouches[0].clientY - _swipeStartY;
        if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 50) {
          if (dx < 0) _reader.next(); else _reader.prev();
        }
      }, { passive: true });
    }

    // ── Keyboard Shortcuts ────────────────────────────────────────
    document.addEventListener('keydown', function (e) {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      const playerModal = document.getElementById('modal-player');
      const readerModal = document.getElementById('modal-reader');
      const playerOpen  = playerModal && playerModal.classList.contains('open');
      const readerOpen  = readerModal && readerModal.classList.contains('open');

      if (e.key === 'Escape') {
        if (playerOpen) { _player.close(); return; }
        if (readerOpen) { _reader.close(); return; }
      }

      if (playerOpen) {
        const video = document.getElementById('player-video');
        if (!video) return;
        switch (e.key) {
          case ' ': case 'k': case 'K':
            e.preventDefault();
            video.paused ? video.play().catch(() => {}) : video.pause();
            break;
          case 'f': case 'F': e.preventDefault(); _toggleFullscreen(); break;
          case 't': case 'T': e.preventDefault(); _toggleTheater(); break;
          case 'i': case 'I': e.preventDefault(); _togglePiP(); break;
          case 'm': case 'M': e.preventDefault(); _toggleMini(); break;
          case 'a': case 'A': e.preventDefault(); _ambient.toggle(); break;
          case 'c': case 'C': e.preventDefault(); _toggleCC(); break;
          case 'ArrowLeft':  case 'j': case 'J':
            e.preventDefault();
            video.currentTime = Math.max(0, video.currentTime - 10);
            break;
          case 'ArrowRight': case 'l': case 'L':
            e.preventDefault();
            video.currentTime = Math.min(video.duration || 0, video.currentTime + 10);
            break;
          case '[':
            e.preventDefault();
            video.playbackRate = Math.max(0.25, +(video.playbackRate - 0.25).toFixed(2));
            break;
          case ']':
            e.preventDefault();
            video.playbackRate = Math.min(3, +(video.playbackRate + 0.25).toFixed(2));
            break;
        }
        if (e.key >= '0' && e.key <= '9') {
          e.preventDefault();
          video.currentTime = (video.duration || 0) * parseInt(e.key, 10) / 10;
        }
        return;
      }

      if (readerOpen) {
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); _reader.next(); }
        if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   { e.preventDefault(); _reader.prev(); }
        if (e.key === 'f' || e.key === 'F') { e.preventDefault(); _reader.toggleFullscreen(); }
      }
    });
  });

})();
