const CACHE_NAME = 'ezanplus-v21-runtime';

// The demo is served from /app/ while a root deployment serves /. Deriving the
// scope from the worker's own URL keeps both correct; hardcoded root paths made
// every STATIC_ASSETS entry miss under /app/.
const BASE = new URL('./', self.location).pathname;
const STATIC_ASSETS = ['', 'index.html', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png']
  .map((name) => BASE + name);

const CACHE_FIRST_DOMAINS = [
  'fonts.googleapis.com',
  'fonts.gstatic.com',
  'cdn-icons-png.flaticon.com',
  'images.unsplash.com',
  'unpkg.com',
  'cdn.jsdelivr.net'
];

const NETWORK_FIRST_DOMAINS = [
  'api.aladhan.com',
  'api.quran.com',
  'nominatim.openstreetmap.org',
  'overpass-api.de',
  'interpreter.overpass-api.de',
  'overpass.kumi.systems'
];

const matchesDomain = (hostname, domain) => hostname === domain || hostname.endsWith(`.${domain}`);

const cacheFirst = async (request) => {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response && response.status === 200) {
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, response.clone());
  }
  return response;
};

const networkFirst = async (request, fallbackPath) => {
  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (e) {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (fallbackPath) return caches.match(fallbackPath);
    throw e;
  }
};

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  const path = url.pathname;

  if (event.request.mode === 'navigate') {
    event.respondWith(networkFirst(event.request, `${BASE}index.html`));
    return;
  }

  if (STATIC_ASSETS.includes(path)) {
    event.respondWith(cacheFirst(event.request));
    return;
  }

  if (NETWORK_FIRST_DOMAINS.some((domain) => matchesDomain(url.hostname, domain))) {
    event.respondWith(networkFirst(event.request));
    return;
  }

  if (CACHE_FIRST_DOMAINS.some((domain) => matchesDomain(url.hostname, domain))) {
    event.respondWith(cacheFirst(event.request));
    return;
  }

  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
