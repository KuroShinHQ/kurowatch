// ═══════════════════════════════════════════════════════════════════
// KuroWatch Service Worker
// Cache-first: app shell · Network-first: /api/* · Offline shell
// ═══════════════════════════════════════════════════════════════════

const CACHE_NAME = 'kurowatch-v1';
const SHELL_FILES = [
  './',
  'index.html',
  'style.css',
  'app.js',
  'debug-logger.js',
  'i18n.js',
  'locales/tr.json',
  'locales/en.json',
  'manifest.json',
  'icons/icon.svg'
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

// Fetch: API → network-first, diğer her şey → cache-first
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

  // Statik kaynaklar: cache-first
  event.respondWith(
    caches.match(req).then(cached => {
      if (cached) return cached;
      return fetch(req).then(resp => {
        if (resp && resp.status === 200 && url.origin === location.origin) {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(req, clone));
        }
        return resp;
      }).catch(() => {
        // Offline fallback: HTML istekleri için index.html göster
        if (req.headers.get('accept') && req.headers.get('accept').includes('text/html')) {
          return caches.match('index.html');
        }
        return new Response('Offline', { status: 503 });
      });
    })
  );
});
