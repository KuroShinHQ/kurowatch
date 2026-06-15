// ═══════════════════════════════════════════════════════════════════
// KuroWatch PWA — Service Worker kaydı + Push Notification yönetimi
// ═══════════════════════════════════════════════════════════════════
(function () {
  'use strict';

  const API = 'http://localhost:8099';

  // ── Service Worker Kaydı ─────────────────────────────────────────
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('./sw.js').catch(err => {
        console.warn('[PWA] SW kayıt hatası:', err);
      });
    });
  }

  // ── Base64 → Uint8Array (VAPID applicationServerKey için) ────────
  function _urlB64ToUint8Array(b64) {
    const pad = '='.repeat((4 - (b64.length % 4)) % 4);
    const raw = atob(b64.replace(/-/g, '+').replace(/_/g, '/') + pad);
    return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
  }

  // ── Push Durumu ──────────────────────────────────────────────────
  async function _getSubscription() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return null;
    const reg = await navigator.serviceWorker.ready;
    return reg.pushManager.getSubscription();
  }

  async function _isPushEnabled() {
    const sub = await _getSubscription();
    return !!sub;
  }

  async function _subscribePush() {
    const reg = await navigator.serviceWorker.ready;

    // VAPID public key al
    const r = await fetch(API + '/api/push/vapid-public-key');
    if (!r.ok) throw new Error('VAPID key alınamadı');
    const { publicKey } = await r.json();

    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: _urlB64ToUint8Array(publicKey),
    });

    // Backend'e gönder
    const subJson = sub.toJSON();
    const res = await fetch(API + '/api/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(subJson),
    });
    if (!res.ok) throw new Error('Abonelik kaydedilemedi');
    return sub;
  }

  async function _unsubscribePush() {
    const sub = await _getSubscription();
    if (!sub) return;
    const endpoint = sub.endpoint;
    await sub.unsubscribe();
    await fetch(API + '/api/push/subscribe', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ endpoint }),
    });
  }

  // ── UI ───────────────────────────────────────────────────────────
  function _setToggleUI(enabled) {
    const btn = document.getElementById('push-toggle-btn');
    const dot = document.getElementById('push-toggle-dot');
    const testBtn = document.getElementById('push-test-btn');
    if (!btn || !dot) return;

    if (enabled) {
      btn.classList.replace('bg-[#1c1d37]', 'bg-[#00d4ff]');
      btn.classList.replace('border-white/10', 'border-[#00d4ff]');
      dot.classList.replace('bg-[#9090b0]', 'bg-white');
      dot.style.transform = 'translateX(24px)';
      if (testBtn) testBtn.classList.remove('hidden');
    } else {
      btn.classList.replace('bg-[#00d4ff]', 'bg-[#1c1d37]');
      btn.classList.replace('border-[#00d4ff]', 'border-white/10');
      dot.classList.replace('bg-white', 'bg-[#9090b0]');
      dot.style.transform = 'translateX(0)';
      if (testBtn) testBtn.classList.add('hidden');
    }
  }

  function _setStatus(msg, type) {
    const el = document.getElementById('push-status');
    if (!el) return;
    el.classList.remove('hidden');
    el.textContent = msg;
    el.style.color = type === 'ok' ? '#90e090'
                   : type === 'err' ? '#ffb4ab'
                   : '#9090b0';
  }

  async function _initPushUI() {
    const toggleBtn = document.getElementById('push-toggle-btn');
    const testBtn   = document.getElementById('push-test-btn');
    if (!toggleBtn) return;

    // API desteği kontrolü
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      _setStatus('Tarayıcınız push bildirimlerini desteklemiyor.', 'err');
      toggleBtn.disabled = true;
      return;
    }

    const perm = Notification.permission;
    if (perm === 'denied') {
      _setStatus('Bildirimler engellendi. Tarayıcı ayarlarından izin verin.', 'err');
      toggleBtn.disabled = true;
      return;
    }

    const enabled = await _isPushEnabled();
    _setToggleUI(enabled);
    _setStatus(enabled ? 'Bildirimler aktif ✓' : 'Kapalı', enabled ? 'ok' : 'neutral');

    toggleBtn.addEventListener('click', async () => {
      toggleBtn.disabled = true;
      try {
        const isOn = await _isPushEnabled();
        if (isOn) {
          await _unsubscribePush();
          _setToggleUI(false);
          _setStatus('Bildirimler kapatıldı.', 'neutral');
        } else {
          const perm = await Notification.requestPermission();
          if (perm !== 'granted') {
            _setStatus('İzin verilmedi.', 'err');
            return;
          }
          await _subscribePush();
          _setToggleUI(true);
          _setStatus('Bildirimler aktif ✓', 'ok');
        }
      } catch (err) {
        _setStatus('Hata: ' + err.message, 'err');
        console.error('[PWA] push toggle hata:', err);
      } finally {
        toggleBtn.disabled = false;
      }
    });

    if (testBtn) {
      testBtn.addEventListener('click', async () => {
        testBtn.disabled = true;
        testBtn.textContent = 'Gönderiliyor…';
        try {
          const r = await fetch(API + '/api/push/test', { method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'KuroWatch Test', body: 'Push bildirimleri çalışıyor! 🎉' })
          });
          const d = await r.json();
          _setStatus(`Test gönderildi: ${d.sent} başarı, ${d.failed} hata.`, d.sent > 0 ? 'ok' : 'err');
        } catch (err) {
          _setStatus('Test hatası: ' + err.message, 'err');
        } finally {
          testBtn.disabled = false;
          testBtn.textContent = '🔔 Test Bildirimi Gönder';
        }
      });
    }
  }

  // Settings ekranı açıldığında push UI'ı init et
  const _origShowScreen = window.kuroNav?.show;
  document.addEventListener('DOMContentLoaded', () => {
    // kuroNav henüz tanımlı olmayabilir — MutationObserver ile izle
    const observer = new MutationObserver(() => {
      const el = document.getElementById('screen-settings');
      if (el && el.classList.contains('active')) {
        _initPushUI();
        observer.disconnect();
      }
    });
    observer.observe(document.body, { attributes: true, subtree: true, attributeFilter: ['class'] });
  });

  window.kuroPWA = { initPushUI: _initPushUI, subscribe: _subscribePush, unsubscribe: _unsubscribePush };
})();
