// ═══════════════════════════════════════════════════════════════════
// KuroWatch — FAZ-3: İndirme Kuyruğu + Video Player + Manga Reader
// ═══════════════════════════════════════════════════════════════════
(function () {
  'use strict';

  const API = 'http://localhost:8099';

  // ── İndirme WS Bağlantısı ────────────────────────────────────────
  let _ws = null;
  let _jobs = {}; // id → job

  // ── Floating Download İndikatörü ────────────────────────────────
  let _floatHideTimer = null;

  function _updateFloatIndicator() {
    const el = document.getElementById('download-float');
    if (!el) return;
    const active = Object.values(_jobs).filter(function(j) { return j.status === 'queued' || j.status === 'downloading'; });
    if (active.length > 0) {
      const job = active[0];
      clearTimeout(_floatHideTimer);
      el.style.display = 'block';
      const icon = document.getElementById('download-float-icon');
      const lbl  = document.getElementById('download-float-label');
      const pctEl = document.getElementById('download-float-pct');
      const bar  = document.getElementById('download-float-bar');
      if (icon) { icon.textContent = 'downloading'; icon.style.color = '#00d4ff'; }
      if (lbl)  lbl.textContent = (job.content_title || '') + ' Bölüm ' + job.episode_number;
      const pct = job.progress_pct || 0;
      if (pctEl) pctEl.textContent = pct + '%';
      if (bar)  { bar.style.width = pct + '%'; bar.style.background = '#00d4ff'; }
    }
  }

  function _onDownloadDone(job) {
    const el = document.getElementById('download-float');
    if (!el) return;
    clearTimeout(_floatHideTimer);
    el.style.display = 'block';
    const icon = document.getElementById('download-float-icon');
    const lbl  = document.getElementById('download-float-label');
    const pctEl = document.getElementById('download-float-pct');
    const bar  = document.getElementById('download-float-bar');
    if (job.status === 'done') {
      if (icon) { icon.textContent = 'check_circle'; icon.style.color = '#4caf50'; }
      if (lbl)  lbl.textContent = 'İndirildi: ' + (job.content_title || '') + ' Bölüm ' + job.episode_number;
      if (pctEl) pctEl.textContent = '';
      if (bar)  { bar.style.width = '100%'; bar.style.background = '#4caf50'; }
    } else if (job.status === 'failed') {
      if (icon) { icon.textContent = 'error'; icon.style.color = '#ef4444'; }
      if (lbl)  lbl.textContent = job.error_msg ? job.error_msg.slice(0, 80) : 'İndirme hatası';
      if (pctEl) pctEl.textContent = '';
      if (bar)  { bar.style.width = '100%'; bar.style.background = '#ef4444'; }
    }
    _floatHideTimer = setTimeout(function() {
      const active = Object.values(_jobs).filter(function(j) { return j.status === 'queued' || j.status === 'downloading'; });
      if (!active.length && el) el.style.display = 'none';
    }, job.status === 'failed' ? 8000 : 4000);
  }

  function connectDownloadWS() {
    if (_ws && _ws.readyState < 2) return;
    _ws = new WebSocket('ws://localhost:8099/api/download/ws');

    _ws.onmessage = function (e) {
      const msg = JSON.parse(e.data);
      if (msg.event === 'state') {
        _jobs = {};
        (msg.jobs || []).forEach(j => { _jobs[j.id] = j; });
        _updateFloatIndicator();
      } else if (msg.event === 'queued' || msg.event === 'started') {
        if (msg.job) _jobs[msg.job.id] = msg.job;
        _updateFloatIndicator();
      } else if (msg.event === 'done') {
        if (msg.job) { _jobs[msg.job.id] = msg.job; _onDownloadDone(msg.job); }
      } else if (msg.event === 'progress') {
        if (_jobs[msg.job_id]) _jobs[msg.job_id].progress_pct = msg.pct;
        _updateFloatIndicator();
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
      _updateFloatIndicator();
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
    const ep   = 'Bölüm ' + job.episode_number;
    const size = job.file_size_bytes ? _fmtSize(job.file_size_bytes) : '';
    const TYPE_TC = { anime: '#00d4ff', manga: '#ffd9a1', manhwa: '#bbc5eb', game: '#ffb4ab' };
    const tc   = TYPE_TC[job.media_type] || '#00d4ff';
    const initials = (job.content_title || '').split(' ').slice(0, 2).map(function (w) { return w[0] || ''; }).join('').toUpperCase() || '?';
    const typeLbl  = (job.media_type || 'anime').toUpperCase();

    const coverBox =
      '<div class="w-[56px] h-[80px] rounded-lg flex-shrink-0 flex items-center justify-center relative overflow-hidden"' +
      ' style="background:#16213e;border:1px solid rgba(255,255,255,0.05)">' +
      '<span class="font-bold text-xl" style="color:' + tc + '">' + escHtml(initials) + '</span>' +
      '<div class="absolute top-1 left-1 text-[7px] font-bold px-1 rounded" style="background:' + tc + ';color:#003642">' + typeLbl + '</div></div>';

    const pct = job.progress_pct || 0;
    let progressHtml = '';
    if (job.status === 'downloading' || job.status === 'queued') {
      const barBg = job.status === 'downloading' ? '#00d4ff' : '#3b4665';
      progressHtml =
        '<div class="w-full rounded-full overflow-hidden" style="height:3px;background:rgba(255,255,255,0.1)">' +
        '<div class="h-full rounded-full transition-all duration-500" style="width:' + pct + '%;background:' + barBg + '"></div></div>' +
        '<div class="flex justify-between">' +
        '<span class="text-[10px] font-bold" style="color:' + tc + '">' + pct + '%</span>' +
        '<span class="text-[10px]" style="color:#9090b0">' + (job.status === 'downloading' ? 'İndiriliyor…' : 'Kuyrukta') + '</span></div>';
    }

    let actions = '';
    if (job.status === 'done') {
      if (job.media_type === 'anime') {
        actions = '<button class="dl-play-btn px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase active:scale-95 transition-all min-h-[36px]"' +
          ' data-job-id="' + job.id + '" data-title="' + escHtml(job.content_title + ' — ' + ep) + '"' +
          ' style="background:#00d4ff;color:#003642;box-shadow:0 0 10px rgba(0,212,255,0.3)">▶ OYNAT</button>';
      } else {
        actions = '<button class="dl-read-btn px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase active:scale-95 transition-all min-h-[36px]"' +
          ' data-job-id="' + job.id + '" data-title="' + escHtml(job.content_title + ' — ' + ep) + '"' +
          ' data-content-id="' + job.content_id + '" data-ep-num="' + job.episode_number + '"' +
          ' style="background:#ffd9a1;color:#1a0a00;box-shadow:0 0 10px rgba(255,217,161,0.2)">📖 OKU</button>';
      }
      actions += '<button onclick="window.kuroDownload.cancel(' + job.id + ')"' +
        ' class="w-9 h-9 flex items-center justify-center rounded-full hover:bg-white/10 transition-all ml-1" style="color:#9090b0" title="Sil">' +
        '<span class="material-symbols-outlined" style="font-size:18px">delete</span></button>';
    } else if (job.status === 'queued') {
      actions = '<button onclick="window.kuroDownload.cancel(' + job.id + ')"' +
        ' class="px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase active:scale-95 transition-all min-h-[36px]"' +
        ' style="background:rgba(255,255,255,0.05);color:#9090b0">✕ İPTAL</button>';
    } else if (job.status === 'downloading') {
      actions = '<button onclick="window.kuroDownload.cancel(' + job.id + ')"' +
        ' class="w-9 h-9 flex items-center justify-center rounded-full hover:bg-white/10 transition-all" style="color:#9090b0" title="İptal">' +
        '<span class="material-symbols-outlined" style="font-size:18px">close</span></button>';
    } else if (job.status === 'failed') {
      actions = '<span class="text-[11px] truncate flex-1" style="color:#ffb4ab" title="' + escHtml(job.error_msg || '') + '">' +
        escHtml((job.error_msg || 'Bilinmeyen hata').substring(0, 50)) + '</span>' +
        '<button onclick="window.kuroDownload.retry(' + job.id + ')"' +
        ' class="px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase active:scale-95 transition-all min-h-[36px] flex-shrink-0"' +
        ' style="background:#ffb4ab;color:#1a0000">TEKRAR DENE</button>' +
        '<button onclick="window.kuroDownload.cancel(' + job.id + ')"' +
        ' class="w-9 h-9 flex items-center justify-center rounded-full hover:bg-white/10 transition-all flex-shrink-0" style="color:#9090b0" title="Sil">' +
        '<span class="material-symbols-outlined" style="font-size:18px">delete</span></button>';
    }

    return '<div class="glass-card rounded-xl p-4 flex flex-col gap-3">' +
      '<div class="flex gap-3">' + coverBox +
      '<div class="flex-1 flex flex-col justify-between min-w-0 py-0.5">' +
      '<div>' +
      '<h3 class="text-[14px] font-semibold truncate" style="color:#e1e0ff">' + escHtml(job.content_title) + '</h3>' +
      '<p class="text-[11px] mt-0.5" style="color:#9090b0">' + ep + (size ? ' · ' + size : '') + '</p>' +
      '</div>' +
      (actions ? '<div class="flex items-center gap-2 flex-wrap">' + actions + '</div>' : '') +
      '</div></div>' +
      (progressHtml ? '<div class="space-y-1">' + progressHtml + '</div>' : '') +
      '</div>';
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

    // Duruma göre grupla
    const active    = jobs.filter(function (j) { return j.status === 'downloading' || j.status === 'queued'; });
    const done      = jobs.filter(function (j) { return j.status === 'done'; });
    const failed    = jobs.filter(function (j) { return j.status === 'failed' || j.status === 'cancelled' || j.status === 'deleted'; });

    function _section(icon, color, label, items) {
      const extraBtn = (label === 'Tamamlandı')
        ? '<button onclick="window.kuroDownload.clearDone()" class="text-[10px] font-bold uppercase tracking-wider active:scale-95 transition-transform" style="color:#00d4ff">TÜMÜNÜ TEMİZLE</button>'
        : '';
      return '<div class="space-y-3">' +
        '<div class="flex items-center justify-between">' +
        '<h2 class="text-[13px] font-semibold flex items-center gap-2" style="color:#dde3e7">' +
        '<span class="material-symbols-outlined text-[18px]" style="color:' + color + '">' + icon + '</span>' + label + '</h2>' +
        extraBtn + '</div>' +
        items.map(_jobCard).join('') + '</div>';
    }

    const sections = [];
    if (active.length) sections.push(_section('downloading', '#00d4ff', 'İndiriliyor', active));
    if (done.length)   sections.push(_section('check_circle', '#4caf50', 'Tamamlandı', done));
    if (failed.length) sections.push(_section('error', '#ffb4ab', 'Hata / İptal', failed));
    el.innerHTML = sections.join('');

    // Depolama güncelle
    const storage = await _fetchStorage();
    const storageEl = document.getElementById('downloads-storage');
    const storageBar = document.getElementById('downloads-storage-bar');
    if (storageEl && storage) {
      storageEl.textContent = _fmtSize(storage.bytes) + ' BOŞ';
      const pctUsed = storage.total_bytes ? Math.min(100, Math.round(storage.bytes / storage.total_bytes * 100)) : 0;
      if (storageBar) storageBar.style.width = pctUsed + '%';
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

  // ── Controls Overlay v7 ──────────────────────────────────────────
  const _controls = {
    _uiTimer: null,
    _isPlaying: false,

    show() {
      const overlay = document.getElementById('controls-overlay');
      if (overlay) { overlay.style.opacity = '1'; overlay.style.pointerEvents = 'auto'; }
      const vm = document.getElementById('video-master');
      if (vm) vm.style.cursor = 'default';
      clearTimeout(this._uiTimer);
    },

    resetTimer() {
      this.show();
      if (this._isPlaying) {
        this._uiTimer = setTimeout(function () {
          const overlay = document.getElementById('controls-overlay');
          if (overlay) { overlay.style.opacity = '0'; overlay.style.pointerEvents = 'none'; }
          const vm = document.getElementById('video-master');
          if (vm) vm.style.cursor = 'none';
        }, 3500);
      }
    },

    setPlaying(playing) {
      this._isPlaying = playing;
      const icon = document.getElementById('play-icon');
      if (icon) icon.textContent = playing ? 'pause' : 'play_arrow';
      if (playing) this.resetTimer(); else this.show();
    },

    updateTime(currentTime, duration) {
      const progress = document.getElementById('timeline-progress');
      if (progress) progress.style.width = (duration > 0 ? (currentTime / duration) * 100 : 0) + '%';
      const timeEl = document.getElementById('player-time');
      if (timeEl) timeEl.innerHTML = _fmtTime(currentTime) + ' <span style="color:rgba(255,255,255,0.4);padding:0 4px">/</span> ' + _fmtTime(duration || 0);
    },

    reset() {
      clearTimeout(this._uiTimer);
      this._isPlaying = false;
      const overlay = document.getElementById('controls-overlay');
      if (overlay) { overlay.style.opacity = '0'; overlay.style.pointerEvents = 'none'; }
    },
  };

  function _fmtTime(s) {
    if (!s || isNaN(s) || !isFinite(s)) return '0:00';
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return m + ':' + String(sec).padStart(2, '0');
  }

  // ── Screen Lock v7 ───────────────────────────────────────────────
  const _lock = {
    _active: false,

    toggle() {
      this._active = !this._active;
      const lockOverlay = document.getElementById('player-lock-overlay');
      const lockBtn = document.getElementById('player-lock-btn');
      if (this._active) {
        clearTimeout(_controls._uiTimer);
        const overlay = document.getElementById('controls-overlay');
        if (overlay) { overlay.style.opacity = '0'; overlay.style.pointerEvents = 'none'; }
        if (lockOverlay) { lockOverlay.classList.remove('hidden'); lockOverlay.style.display = 'flex'; }
        if (lockBtn) lockBtn.querySelector('span').textContent = 'lock';
      } else {
        if (lockOverlay) { lockOverlay.classList.add('hidden'); lockOverlay.style.display = ''; }
        if (lockBtn) lockBtn.querySelector('span').textContent = 'lock_open';
        _controls.resetTimer();
      }
    },

    isActive() { return this._active; },

    reset() {
      this._active = false;
      const lockOverlay = document.getElementById('player-lock-overlay');
      if (lockOverlay) { lockOverlay.classList.add('hidden'); lockOverlay.style.display = ''; }
      const lockBtn = document.getElementById('player-lock-btn');
      if (lockBtn) lockBtn.querySelector('span').textContent = 'lock_open';
    },
  };

  // ── Capture (Screenshot) v7 ──────────────────────────────────────
  function _captureFrame() {
    const video = document.getElementById('player-video');
    if (!video) return;
    const canvas = document.createElement('canvas');
    canvas.width  = video.videoWidth  || 1280;
    canvas.height = video.videoHeight || 720;
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(function (blob) {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'kurowatch-frame.png'; a.click();
      setTimeout(function () { URL.revokeObjectURL(url); }, 5000);
    }, 'image/png');
    if (window.showToast) window.showToast('Ekran görüntüsü kaydedildi', 'success', 3000);
  }

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
    if (_panelSubtitle) _panelSubtitle.syncCC();
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

  // ── Episodes Panel v7 ────────────────────────────────────────────
  const _panelEpisodes = {
    _contentId: null,
    _episodes: [],
    _currentEp: null,

    async open(contentId, contentTitle, currentEpNumber) {
      const panel = document.getElementById('panel-episodes');
      if (!panel) return;
      this._currentEp = currentEpNumber;
      const titleEl = document.getElementById('panel-episodes-title');
      if (titleEl) titleEl.textContent = contentTitle || '';
      panel.classList.remove('hidden');

      if (this._contentId !== contentId || !this._episodes.length) {
        this._contentId = contentId;
        this._episodes = [];
        const listEl = document.getElementById('panel-episodes-list');
        if (listEl) listEl.innerHTML = '<div class="text-center text-[#9090b0] py-8 text-sm">Yükleniyor…</div>';
        try {
          const r = await fetch(API + '/api/content/' + contentId + '/episodes');
          if (!r.ok) throw new Error(r.status);
          this._episodes = await r.json();
        } catch (_e) {
          const listEl2 = document.getElementById('panel-episodes-list');
          if (listEl2) listEl2.innerHTML = '<div class="text-center text-[#9090b0] py-8 text-sm">Bölümler yüklenemedi</div>';
          return;
        }
      }
      this._render();
    },

    _render() {
      const listEl = document.getElementById('panel-episodes-list');
      if (!listEl || !this._episodes.length) return;
      const cid = this._contentId;
      listEl.innerHTML = this._episodes.map(function (ep) {
        const isCurrent = ep.number === _panelEpisodes._currentEp;
        const job = Object.values(_jobs).find(function (j) {
          return j.content_id === cid && j.episode_number === ep.number && j.status === 'done';
        });
        return '<div class="episode-panel-card flex gap-3 p-3 rounded-xl transition-all cursor-pointer active:scale-[0.97]' +
          (isCurrent ? '' : ' hover:bg-white/5') + '"' +
          ' style="' + (isCurrent ? 'background:rgba(0,212,255,0.08);border:1px solid rgba(0,212,255,0.25)' : 'border:1px solid transparent') + '"' +
          ' data-ep-num="' + ep.number + '" data-ep-job="' + (job ? job.id : '') + '">' +
          '<div class="w-10 h-10 flex items-center justify-center rounded-lg text-sm font-bold flex-shrink-0"' +
          ' style="' + (isCurrent ? 'background:#00d4ff;color:#003642' : 'background:#1c1d37;color:#9090b0') + '">' + ep.number + '</div>' +
          '<div class="flex flex-col gap-0.5 min-w-0 flex-1 justify-center">' +
          '<p class="text-[13px] truncate" style="' + (isCurrent ? 'color:#00d4ff;font-weight:600' : 'color:#dde3e7') + '">Bölüm ' + ep.number + '</p>' +
          (ep.duration ? '<p class="text-[11px] text-[#9090b0]">' + ep.duration + 'dk</p>' : '') +
          '</div>' +
          (job ? '<span class="material-symbols-outlined text-lg flex-shrink-0 self-center" style="color:#4caf50;font-variation-settings:\'FILL\' 1">download_done</span>' : '') +
          '</div>';
      }).join('');

      listEl.querySelectorAll('.episode-panel-card').forEach(function (card) {
        card.addEventListener('click', function () {
          const jobId = parseInt(card.dataset.epJob, 10);
          if (!jobId || !_jobs[jobId]) return;
          const job = _jobs[jobId];
          const epNum = parseInt(card.dataset.epNum, 10);
          _panelEpisodes.close();
          setTimeout(function () {
            _player.close();
            setTimeout(function () { _player.open(jobId, job.content_title + ' — Bölüm ' + epNum, job.content_id, epNum); }, 200);
          }, 300);
        });
      });

      setTimeout(function () {
        const active = listEl.querySelector('[style*="rgba(0,212,255,0.08)"]');
        if (active) active.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 100);
    },

    close() {
      const panel = document.getElementById('panel-episodes');
      if (panel) panel.classList.add('hidden');
    },
  };

  // ── Quality Panel v7 ─────────────────────────────────────────────
  const _panelQuality = {
    _qualities: ['1080p', '720p', '480p', '360p'],
    _current: '720p',

    open(currentQuality) {
      const panel = document.getElementById('panel-quality');
      if (!panel) return;
      this._current  = currentQuality || '720p';
      this._selected = this._current;
      this._render();
      panel.classList.remove('hidden');
    },

    _render() {
      const listEl = document.getElementById('panel-quality-list');
      if (!listEl) return;
      const selected = this._selected || this._current;
      listEl.innerHTML = this._qualities.map(function (q) {
        const isCurrent  = q === _panelQuality._current;
        const isSelected = q === selected;
        return '<button class="quality-opt w-full flex items-center justify-between p-4 rounded-xl transition-all active:scale-[0.97]"' +
          ' data-quality="' + q + '"' +
          ' style="' + (isSelected ? 'background:rgba(0,212,255,0.1);border:1px solid rgba(0,212,255,0.4)' : 'background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1)') + '">' +
          '<span class="text-[15px] font-semibold text-[#dde3e7]">' + q + (isCurrent ? ' — Mevcut' : '') + '</span>' +
          (isSelected ? '<span class="material-symbols-outlined" style="color:#00d4ff;font-variation-settings:\'FILL\' 1">check_circle</span>' : '') +
          '</button>';
      }).join('');
      listEl.querySelectorAll('.quality-opt').forEach(function(btn) {
        btn.addEventListener('click', function() {
          _panelQuality._selected = btn.dataset.quality;
          _panelQuality._render();
        });
      });
    },

    close() {
      const panel = document.getElementById('panel-quality');
      if (panel) panel.classList.add('hidden');
    },
  };

  // ── Subtitle / Speed Panel v7 ────────────────────────────────────
  const _panelSubtitle = {
    _speeds: [0.5, 0.75, 1, 1.25, 1.5, 2],

    open() {
      const panel = document.getElementById('panel-subtitle');
      if (!panel) return;
      this._renderSpeeds();
      this.syncCC();
      panel.classList.remove('hidden');
    },

    syncCC() {
      const thumb  = document.getElementById('panel-cc-thumb');
      const toggle = document.getElementById('panel-cc-toggle');
      if (!thumb || !toggle) return;
      toggle.style.background = _ccActive ? '#00d4ff' : 'rgba(255,255,255,0.1)';
      thumb.style.transform   = _ccActive ? 'translateX(24px)' : '';
    },

    _renderSpeeds() {
      const listEl = document.getElementById('panel-speed-list');
      const video  = document.getElementById('player-video');
      if (!listEl) return;
      const cur = video ? video.playbackRate : 1;
      listEl.innerHTML = this._speeds.map(function (s) {
        const active = Math.abs(s - cur) < 0.01;
        return '<button class="speed-opt h-10 rounded-lg text-sm font-medium transition-all"' +
          ' style="' + (active ? 'background:#00d4ff;color:#003642;font-weight:700' : 'background:rgba(255,255,255,0.05);color:#9090b0') + '"' +
          ' data-speed="' + s + '">' + (s === 1 ? '1× Normal' : s + '×') + '</button>';
      }).join('');

      listEl.querySelectorAll('.speed-opt').forEach(function (btn) {
        btn.addEventListener('click', function () {
          const video = document.getElementById('player-video');
          if (video) video.playbackRate = parseFloat(btn.dataset.speed);
          _panelSubtitle._renderSpeeds();
          const speedEl = document.getElementById('player-speed-display');
          if (speedEl && video) {
            const r = video.playbackRate;
            speedEl.textContent = (r === Math.floor(r) ? r.toFixed(0) : r.toFixed(2)) + '×';
          }
        });
      });
    },

    close() {
      const panel = document.getElementById('panel-subtitle');
      if (panel) panel.classList.add('hidden');
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

      // Bölüm etiketi (örn: "Bölüm 3")
      const epLabel = document.getElementById('player-ep-label');
      if (epLabel) epLabel.textContent = episodeNumber ? 'Bölüm ' + episodeNumber : '';

      // Mini/theater sıfırla
      modal.classList.remove('player-mini', 'player-theater');
      _miniActive    = false;
      _theaterActive = false;
      modal.classList.remove('hidden');
      modal.classList.add('open');
      document.body.style.overflow = 'hidden';

      video.dataset.jobId         = jobId;
      video.dataset.contentId     = contentId || '';
      video.dataset.episodeNumber = episodeNumber || '';
      video.dataset.quality       = (_jobs[jobId] && _jobs[jobId].quality) || '720p';
      video._daisyTriggered       = false;

      // Controls v7 başlat
      _controls.reset();
      _controls.show();
      _lock.reset();
      _panelEpisodes.close();
      _panelQuality.close();
      _panelSubtitle.close();

      // Hız göstergesini sıfırla
      video.playbackRate = 1;
      const speedEl = document.getElementById('player-speed-display');
      if (speedEl) speedEl.textContent = '1×';

      // Timeline sıfırla
      const progress = document.getElementById('timeline-progress');
      if (progress) progress.style.width = '0%';
      const buffer = document.getElementById('timeline-buffer');
      if (buffer) buffer.style.width = '0%';
      const timeEl = document.getElementById('player-time');
      if (timeEl) timeEl.innerHTML = '0:00 <span style="color:rgba(255,255,255,0.4);padding:0 4px">/</span> 0:00';

      video.play().catch(function () {});
      _controls.setPlaying(true);

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
      _controls.reset();
      _lock.reset();
      _panelEpisodes.close();
      _panelQuality.close();
      _panelSubtitle.close();
      _miniActive    = false;
      _theaterActive = false;
      if (document.fullscreenElement) document.exitFullscreen().catch(function () {});
    },

    openVideo: async function (jobId, title) {
      let job = _jobs[jobId];
      if (!job) {
        try {
          const r = await fetch(API + '/api/download/queue');
          if (r.ok) {
            const data = await r.json();
            (data.jobs || []).forEach(function(j) { _jobs[j.id] = j; });
            job = _jobs[jobId];
          }
        } catch (e) {}
      }
      const contentId = job ? job.content_id : null;
      const epNum     = job ? job.episode_number : null;
      this.open(jobId, title, contentId, epNum);
    },
  };

  // timeupdate: v7 timeline + Skip Intro + Auto-Next + Daisy-chain
  document.addEventListener('timeupdate', function (e) {
    const video = e.target;
    if (!video || video.tagName !== 'VIDEO') return;

    _controls.updateTime(video.currentTime, video.duration);
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
                fetch(API + '/api/download/start', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    content_id: job.content_id,
                    content_title: job.content_title,
                    media_type: job.media_type,
                    episode_number: nextEp,
                    url: next.url,
                    quality: autoQ,
                  }),
                }).then(function(r) {
                  if (r.ok) return r.json();
                }).then(function(j) {
                  if (j) {
                    _jobs[j.id] = j;
                    _updateBadge();
                    if (window.showToast) window.showToast('Sıradaki bölüm arka planda indiriliyor...', 'info', 4000);
                  }
                }).catch(function() {});
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
    _observer: null,

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
      const chLabel = document.getElementById('reader-chapter-label');
      if (chLabel) chLabel.textContent = episodeNumber ? 'BÖLÜM ' + episodeNumber : '';
      modal.classList.remove('hidden');
      modal.classList.add('open');
      document.body.style.overflow = 'hidden';
      _readerUI.reset();

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
      if (this._observer) { this._observer.disconnect(); this._observer = null; }
      if (this._autoNextTimer) { clearInterval(this._autoNextTimer); this._autoNextTimer = null; }
      const overlay = document.getElementById('reader-autonext');
      if (overlay) overlay.remove();
      _panelTranslate.close();
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    },

    toggleMode: function (forceWebtoon) {
      this._webtoon = (forceWebtoon !== undefined) ? forceWebtoon : !this._webtoon;
      this._current = 0;
      this._render();
      const webBtn  = document.getElementById('reader-webtoon-btn');
      const pageBtn = document.getElementById('reader-page-btn');
      if (webBtn) {
        webBtn.style.background = this._webtoon ? '#00d4ff' : 'transparent';
        webBtn.style.color      = this._webtoon ? '#003642' : '#9090b0';
      }
      if (pageBtn) {
        pageBtn.style.background = !this._webtoon ? '#00d4ff' : 'transparent';
        pageBtn.style.color      = !this._webtoon ? '#003642' : '#9090b0';
      }
    },

    _render: function () {
      const pagesEl = document.getElementById('reader-pages');
      const pages = (this._showTr && this._trPages && this._trPages.length)
        ? this._trPages : this._pages;
      if (!pagesEl || pages.length === 0) return;

      if (this._webtoon) {
        pagesEl.innerHTML = pages.map(function (url, i) {
          return '<img src="' + API + url + '" alt="Sayfa ' + (i + 1) + '" loading="lazy" data-page-idx="' + i + '" style="width:100%;max-width:800px;margin:0 auto;display:block;height:auto;">';
        }).join('');
        this._initScrollObserver(pages.length);
        this._updateProgress(0, pages.length);
      } else {
        pagesEl.innerHTML =
          '<img src="' + API + pages[this._current] + '" alt="Sayfa ' + (this._current + 1) + '"' +
          ' style="width:auto;height:auto;max-width:100%;max-height:calc(100dvh - 130px);margin:0 auto;display:block;object-fit:contain;">';
        this._updateProgress(this._current, pages.length);
      }
    },

    _updateProgress: function (pageIndex, total) {
      const pct  = total > 0 ? Math.round(((pageIndex + 1) / total) * 100) : 0;
      const bar  = document.getElementById('reader-progress-bar');
      const pnum = document.getElementById('reader-page-num');
      const plbl = document.getElementById('reader-pct-label');
      const curP = document.getElementById('reader-cur-page');
      const ofP  = document.getElementById('reader-of-pages');
      if (bar)  bar.style.width  = pct + '%';
      if (pnum) pnum.textContent = (pageIndex + 1) + ' / ' + total;
      if (plbl) plbl.textContent = '%' + pct + ' OKUNDU';
      if (curP) curP.textContent = pageIndex + 1;
      if (ofP)  ofP.textContent  = '/ ' + total;
    },

    _initScrollObserver: function (total) {
      if (this._observer) this._observer.disconnect();
      const pagesEl = document.getElementById('reader-pages');
      if (!pagesEl) return;
      let maxIdx = 0;
      this._observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            const idx = parseInt(entry.target.dataset.pageIdx, 10);
            if (!isNaN(idx) && idx > maxIdx) maxIdx = idx;
          }
        });
        _reader._updateProgress(maxIdx, total);
      }, { threshold: 0.3 });
      pagesEl.querySelectorAll('img[data-page-idx]').forEach(function (img) {
        _reader._observer.observe(img);
      });
    },

    prev: function () {
      if (this._webtoon) { this.prevChapter(); return; }
      if (this._current > 0) { this._current--; this._render(); }
      document.getElementById('modal-reader').scrollTop = 0;
    },

    next: function () {
      if (this._webtoon) {
        // Webtoon modunda tüm sayfalar görünür — page-next butonu chapter geçişi yapar
        this.nextChapter();
        return;
      }
      if (this._current < this._pages.length - 1) {
        this._current++;
        this._render();
        document.getElementById('modal-reader').scrollTop = 0;
      } else {
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
          // Sonraki bölüm: jobs listesinden bul, yoksa kapat
          const cid = _reader._contentId;
          const nep = (_reader._episodeNumber || 0) + 1;
          const nj  = Object.values(_jobs).find(function(j) {
            return j.content_id == cid && j.episode_number === nep && j.status === 'done';
          });
          if (nj) {
            _reader.close();
            setTimeout(function() { _reader.open(nj.id, nj.content_title + ' — Bölüm ' + nep, cid, nep); }, 200);
          } else {
            _reader.close();
          }
        }
      }, 1000);
    },

    nextChapter: function() {
      const cid = this._contentId;
      const ep  = this._episodeNumber;
      if (!cid || !ep) return;
      const nep = ep + 1;
      const nj  = Object.values(_jobs).find(function(j) {
        return j.content_id == cid && j.episode_number === nep && j.status === 'done';
      });
      if (nj) {
        this.close();
        setTimeout(function() { _reader.open(nj.id, nj.content_title + ' — Bölüm ' + nep, cid, nep); }, 200);
      } else {
        this._triggerAutoNextChapter();
      }
    },

    prevChapter: function() {
      const cid = this._contentId;
      const ep  = this._episodeNumber;
      if (!cid || !ep || ep <= 1) return;
      const pep = ep - 1;
      const pj  = Object.values(_jobs).find(function(j) {
        return j.content_id == cid && j.episode_number === pep && j.status === 'done';
      });
      if (pj) {
        this.close();
        setTimeout(function() { _reader.open(pj.id, pj.content_title + ' — Bölüm ' + pep, cid, pep); }, 200);
      }
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

  // ── Reader UI Visibility Toggle v7 ──────────────────────────────
  const _readerUI = {
    _visible: true,
    _lastScroll: 0,

    toggle() {
      this._visible = !this._visible;
      const header = document.getElementById('reader-header');
      const nav    = document.getElementById('reader-nav');
      const fab    = document.getElementById('reader-ui-toggle');
      const icon   = document.getElementById('reader-ui-icon');
      if (header) header.style.transform = this._visible ? '' : 'translateY(-100%)';
      if (nav)    nav.style.transform    = this._visible ? '' : 'translateY(100%)';
      if (fab)    fab.style.opacity      = this._visible ? '1' : '0.5';
      if (icon)   icon.textContent       = this._visible ? 'visibility' : 'visibility_off';
    },

    show() {
      if (this._visible) return;
      this.toggle();
    },

    reset() {
      this._visible = false;
      this.toggle();
      this._lastScroll = 0;
    },
  };

  // ── Kuro Translate Panel v7 ───────────────────────────────────────
  const _panelTranslate = {
    _open: false,

    open() {
      this._open = true;
      const overlay = document.getElementById('panel-translate');
      const sheet   = document.getElementById('panel-translate-sheet');
      if (overlay) { overlay.style.opacity = '1'; overlay.style.pointerEvents = 'auto'; }
      if (sheet)   sheet.style.transform = 'translateY(0)';
    },

    close() {
      this._open = false;
      const sheet   = document.getElementById('panel-translate-sheet');
      const overlay = document.getElementById('panel-translate');
      if (sheet)   sheet.style.transform = 'translateY(100%)';
      setTimeout(function () {
        if (overlay) { overlay.style.opacity = '0'; overlay.style.pointerEvents = 'none'; }
      }, 300);
    },

    isOpen() { return this._open; },
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
    _fetchJobs: async function() {
      try {
        var r = await fetch(API + '/api/download/queue');
        if (r.ok) { var data = await r.json(); (data.jobs || []).forEach(function(j) { _jobs[j.id] = j; }); }
      } catch (e) {}
    },
    clearDone: async function() {
      const done = Object.values(_jobs).filter(function(j) { return j.status === 'done'; });
      await Promise.all(done.map(function(j) { return cancelJob(j.id); }));
    },
    retry: async function(jobId) {
      const job = _jobs[jobId];
      if (!job) return;
      await cancelJob(jobId);
      await startDownload(job.content_id, job.content_title, job.media_type, job.episode_number, job.url, job.quality);
    },
    analyzeIntro: async function (contentId) {
      try {
        const r = await fetch(`${API}/api/analyze/intro/${contentId}`, { method: 'POST' });
        const d = await r.json();
        alert(`İntro analizi başladı: ${d.episode_count} bölüm. Birkaç dakika içinde tamamlanır.`);
      } catch (err) {
        alert('Analiz başlatılamadı: ' + err.message);
      }
    },
    getDownloadedJob: function(contentId, epNum) {
      return Object.values(_jobs).find(function(j) {
        return j.content_id === contentId && j.episode_number === epNum && j.status === 'done';
      }) || null;
    },
  };

  // ── Başlat ───────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    connectDownloadWS();

    // ── Downloads listesi — OYNAT / OKU buton delegation ─────────
    const _dlList = document.getElementById('downloads-list');
    if (_dlList) {
      _dlList.addEventListener('click', function(evt) {
        const playBtn = evt.target.closest('.dl-play-btn');
        if (playBtn) {
          _player.openVideo(parseInt(playBtn.dataset.jobId, 10), playBtn.dataset.title);
          return;
        }
        const readBtn = evt.target.closest('.dl-read-btn');
        if (readBtn) {
          _reader.open(
            parseInt(readBtn.dataset.jobId, 10),
            readBtn.dataset.title,
            parseInt(readBtn.dataset.contentId, 10),
            parseInt(readBtn.dataset.epNum, 10)
          );
        }
      });
    }

    // ── Player Butonları (v7) ─────────────────────────────────────
    const _pb = function (id, fn) { const el = document.getElementById(id); if (el) el.addEventListener('click', fn); };
    _pb('player-close',        function () { _player.close(); });
    _pb('skip-intro-btn',      function () { _intro.skip(); });
    _pb('skip-outro-btn',      function () { _outro.skip(); });
    _pb('player-ambient-btn',  function () { _ambient.toggle(); });
    _pb('player-theater-btn',  function () { _toggleTheater(); });
    _pb('player-pip-btn',      function () { _togglePiP(); });
    _pb('player-mini-btn',     function () { _toggleMini(); });
    _pb('player-fullscreen-btn', function () { _toggleFullscreen(); });
    _pb('player-cc-btn',       function () { _panelSubtitle.open(); });
    _pb('player-volume-btn',   function () {
      const video = document.getElementById('player-video');
      if (!video) return;
      video.muted = !video.muted;
      const btn = document.getElementById('player-volume-btn');
      const icon = btn ? btn.querySelector('.material-symbols-outlined') : null;
      if (icon) icon.textContent = video.muted ? 'volume_off' : 'volume_up';
    });
    _pb('autonext-cancel',     function () { _autoNext.reset(); });

    // v7 yeni butonlar
    _pb('master-play-pause',   function () {
      const video = document.getElementById('player-video');
      if (!video) return;
      if (video.paused) { video.play().catch(function () {}); _controls.setPlaying(true); }
      else { video.pause(); _controls.setPlaying(false); }
    });
    _pb('player-rewind-btn', function () {
      const video = document.getElementById('player-video');
      if (video) { video.currentTime = Math.max(0, video.currentTime - 10); _controls.resetTimer(); }
    });
    _pb('player-forward-btn', function () {
      const video = document.getElementById('player-video');
      if (video) { video.currentTime = Math.min(video.duration || 0, video.currentTime + 10); _controls.resetTimer(); }
    });
    _pb('player-lock-btn',     function () { _lock.toggle(); });
    _pb('player-unlock-btn',   function () { _lock.toggle(); });
    _pb('player-capture-btn',  function () { _captureFrame(); _controls.resetTimer(); });
    _pb('player-quality-btn',  function () {
      const video = document.getElementById('player-video');
      const q = (video && video.dataset.quality) || '720p';
      _panelQuality.open(q);
    });
    _pb('player-episodes-btn', function () {
      const video = document.getElementById('player-video');
      const cid   = video && video.dataset.contentId;
      const epNum = video && parseInt(video.dataset.episodeNumber, 10);
      const jobId = video && parseInt(video.dataset.jobId, 10);
      const job   = _jobs[jobId];
      if (cid) _panelEpisodes.open(parseInt(cid, 10), job ? job.content_title : '', epNum || null);
    });
    _pb('player-speed-btn',    function () { _panelSubtitle.open(); });
    _pb('player-ep-next-btn',  function () {
      const video = document.getElementById('player-video');
      if (!video) return;
      const jobId = parseInt(video.dataset.jobId, 10);
      const job   = _jobs[jobId];
      if (!job) return;
      const nextEp  = job.episode_number + 1;
      const nextJob = Object.values(_jobs).find(function (j) {
        return j.content_id === job.content_id && j.episode_number === nextEp && j.status === 'done';
      });
      if (nextJob) {
        _player.close();
        setTimeout(function () { _player.open(nextJob.id, nextJob.content_title + ' — Bölüm ' + nextEp, nextJob.content_id, nextEp); }, 200);
      }
    });
    _pb('panel-cc-toggle',       function () { _toggleCC(); });
    _pb('panel-episodes-close',  function () { _panelEpisodes.close(); });
    _pb('panel-episodes-backdrop', function () { _panelEpisodes.close(); });
    _pb('panel-quality-close',   function () { _panelQuality.close(); });
    _pb('panel-quality-backdrop', function () { _panelQuality.close(); });
    _pb('panel-quality-apply',   function () {
      const video = document.getElementById('player-video');
      if (video && _panelQuality._selected) {
        video.dataset.quality = _panelQuality._selected;
        _panelQuality._current = _panelQuality._selected;
      }
      _panelQuality.close();
    });
    _pb('panel-subtitle-close',  function () { _panelSubtitle.close(); });
    _pb('panel-subtitle-backdrop', function () { _panelSubtitle.close(); });

    // v7 Video element events
    const _playerVideo = document.getElementById('player-video');
    if (_playerVideo) {
      _playerVideo.addEventListener('play',  function () { _controls.setPlaying(true); });
      _playerVideo.addEventListener('pause', function () { _controls.setPlaying(false); });
      _playerVideo.addEventListener('ended', function () { _controls.setPlaying(false); });
      _playerVideo.addEventListener('progress', function () {
        const video = document.getElementById('player-video');
        if (!video || !video.duration) return;
        const buf = document.getElementById('timeline-buffer');
        if (buf && video.buffered.length) {
          buf.style.width = ((video.buffered.end(video.buffered.length - 1) / video.duration) * 100) + '%';
        }
      });
    }

    // v7 Controls overlay interaction (touch/mouse)
    const vm = document.getElementById('video-master');
    if (vm) {
      vm.addEventListener('mousemove',  function () { if (!_lock.isActive()) _controls.resetTimer(); });
      vm.addEventListener('touchstart', function () { if (!_lock.isActive()) _controls.resetTimer(); }, { passive: true });
      vm.addEventListener('click', function (e) {
        if (_lock.isActive()) return;
        const overlay = document.getElementById('controls-overlay');
        const isVisible = overlay && overlay.style.opacity !== '0';
        if (!isVisible) { _controls.show(); return; }
        const inControls = e.target.closest('#controls-overlay');
        if (!inControls) {
          const video = document.getElementById('player-video');
          if (video) {
            if (video.paused) { video.play().catch(function () {}); _controls.setPlaying(true); }
            else { video.pause(); _controls.setPlaying(false); }
          }
        }
      });
    }

    // v7 Timeline seeking
    const timelineSlider = document.getElementById('timeline-slider');
    if (timelineSlider) {
      let _seeking = false;
      function _doSeek(e) {
        const video = document.getElementById('player-video');
        if (!video || !video.duration) return;
        const rect = timelineSlider.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const pct = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        video.currentTime = pct * video.duration;
        _controls.resetTimer();
      }
      timelineSlider.addEventListener('mousedown',  function (e) { _seeking = true; _doSeek(e); });
      timelineSlider.addEventListener('touchstart', function (e) { _seeking = true; _doSeek(e); }, { passive: true });
      document.addEventListener('mousemove',  function (e) { if (_seeking) _doSeek(e); });
      document.addEventListener('touchmove',  function (e) { if (_seeking) _doSeek(e); }, { passive: true });
      document.addEventListener('mouseup',  function () { _seeking = false; });
      document.addEventListener('touchend', function () { _seeking = false; });
      timelineSlider.addEventListener('click', _doSeek);
    }

    // ── Reader Butonları (v7) ─────────────────────────────────────
    _pb('reader-close',              function () { _reader.close(); });
    _pb('reader-webtoon-btn',        function () { _reader.toggleMode(true); });
    _pb('reader-page-btn',           function () { _reader.toggleMode(false); });
    _pb('reader-kuro-translate-btn', function () { _panelTranslate.open(); });
    _pb('reader-prev',               function () { _reader.prevChapter(); });
    _pb('reader-next',               function () { _reader.nextChapter(); });
    _pb('reader-prev-page',          function () { _reader.prev(); });
    _pb('reader-next-page',          function () { _reader.next(); });
    _pb('reader-ui-toggle',          function () { _readerUI.toggle(); });
    _pb('reader-fullscreen-btn',     function () { _reader.toggleFullscreen(); });
    _pb('reader-translate-btn',      function () { _translate.startTranslate(); });
    _pb('reader-lang-original',      function () { _translate.showOriginal(); });
    _pb('reader-lang-tr',            function () { _translate.showTranslated(); });
    _pb('reader-fix-btn',            function () { _translate.showFixModal(); });
    _pb('panel-translate-close',     function () { _panelTranslate.close(); });
    _pb('panel-translate-start',     function () { _translate.startTranslate(); });

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

    // ── Reader Sliders + merkez-tap + scroll (v7) ─────────────────
    const _rFont = document.getElementById('range-font');
    if (_rFont) _rFont.addEventListener('input', function () {
      document.documentElement.style.setProperty('--reader-font-size', _rFont.value + 'px');
      const lbl = document.getElementById('val-font');
      if (lbl) lbl.textContent = _rFont.value + 'px';
    });
    const _rOp = document.getElementById('range-opacity');
    if (_rOp) _rOp.addEventListener('input', function () {
      document.documentElement.style.setProperty('--reader-overlay-opacity', _rOp.value / 100);
      const lbl = document.getElementById('val-opacity');
      if (lbl) lbl.textContent = _rOp.value + '%';
    });
    const _rPagesArea = document.getElementById('reader-pages');
    if (_rPagesArea) _rPagesArea.addEventListener('click', function (e) {
      const modal = document.getElementById('modal-reader');
      if (!modal || !modal.classList.contains('open')) return;
      if (e.target.tagName !== 'IMG') _readerUI.toggle();
    });
    const _rModal = document.getElementById('modal-reader');
    if (_rModal) _rModal.addEventListener('scroll', function () {
      if (!_reader._webtoon) return;
      const st  = _rModal.scrollTop;
      const dir = st - _readerUI._lastScroll;
      _readerUI._lastScroll = st;
      if (dir > 10  && _readerUI._visible)  _readerUI.toggle();
      if (dir < -10 && !_readerUI._visible) _readerUI.toggle();
    }, { passive: true });

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
