// ═══════════════════════════════════════════════════════════════════
// KuroWatch Service Worker
// Cache-first: app shell · Network-first: /api/* · Offline shell
// ═══════════════════════════════════════════════════════════════════

const CACHE_NAME = 'kurowatch-v12';
const SHELL_FILES = [
  'style.css',
  'player.js',
  'debug-logger.js',
  'i18n.js',
  'locales/tr.json',
  'locales/en.json',
  'manifest.json',
  'icons/icon.svg',
  'icons/icon-192.png',
];

// Install: shell cache
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(SHELL_FILES).catch(err => {
        console.warn('[SW] shell cache partial fail:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate: eski cache temizliği
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      );
    }).then(() => self.clients.claim())
  );
});

// ── Push Bildirimleri ────────────────────────────────────────────────
self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch {}
  event.waitUntil(
    self.registration.showNotification(data.title || 'KuroWatch', {
      body:  data.body  || '',
      icon:  data.icon  || '/icons/icon-192.png',
      badge: '/icons/icon-192.png',
      tag:   'kurowatch-update',
      renotify: true,
      data:  { url: data.url || '/' },
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      for (const c of list) {
        if ('focus' in c) return c.focus();
      }
      return clients.openWindow(target);
    })
  );
});

// Fetch: API → network-first, HTML/navigation → network-first, statik → cache-first
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // API istekleri: network-first
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(req).catch(() => new Response(
        JSON.stringify({ error: 'offline', cached: false }),
        { status: 503, headers: { 'Content-Type': 'application/json' } }
      ))
    );
    return;
  }

  // Navigation/HTML istekleri: network-first (cache-busting çalışsın)
  if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
    event.respondWith(
      fetch(req).then(resp => {
        if (resp && resp.status === 200) {
          caches.open(CACHE_NAME).then(cache => cache.put(req, resp.clone()));
        }
        return resp;
      }).catch(() => caches.match(req).then(c => c || caches.match('index.html')))
    );
    return;
  }

  // Diğer statik kaynaklar (JS, CSS, resimler): cache-first
  event.respondWith(
    caches.match(req).then(cached => {
      if (cached) return cached;
      return fetch(req).then(resp => {
        if (resp && resp.status === 200 && url.origin === location.origin) {
          caches.open(CACHE_NAME).then(cache => cache.put(req, resp.clone()));
        }
        return resp;
      }).catch(() => new Response('Offline', { status: 503 }));
    })
  );
});
