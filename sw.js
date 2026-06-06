// ============================================================
// FinRight AI — Service Worker (sw.js)
// Enables offline support and faster loading
// ============================================================

const CACHE_NAME = 'finright-ai-v1';

// Files to cache for offline use
const STATIC_ASSETS = [
  '/finright-ai/',
  '/finright-ai/index.html',
  '/finright-ai/manifest.json',
  '/finright-ai/icon-192.png',
  '/finright-ai/icon-512.png',
  'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js',
  'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2',
];

// ── Install: cache all static files ──────────────────────────
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      // Cache what we can, ignore failures (fonts etc may be blocked)
      return Promise.allSettled(
        STATIC_ASSETS.map(function(url) {
          return cache.add(url).catch(function() {
            console.log('Could not cache:', url);
          });
        })
      );
    }).then(function() {
      self.skipWaiting();
    })
  );
});

// ── Activate: clean old caches ────────────────────────────────
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(key) {
          return key !== CACHE_NAME;
        }).map(function(key) {
          return caches.delete(key);
        })
      );
    }).then(function() {
      self.clients.claim();
    })
  );
});

// ── Fetch: serve from cache, fallback to network ─────────────
self.addEventListener('fetch', function(event) {
  // Skip Supabase API calls — always go to network
  if (event.request.url.includes('supabase.co')) {
    return;
  }

  // Network-first for HTML (always fresh)
  if (event.request.destination === 'document') {
    event.respondWith(
      fetch(event.request)
        .then(function(response) {
          // Cache the fresh page
          var clone = response.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(event.request, clone);
          });
          return response;
        })
        .catch(function() {
          // Offline — serve from cache
          return caches.match('/finright-ai/index.html');
        })
    );
    return;
  }

  // Cache-first for static assets (JS, CSS, fonts, images)
  event.respondWith(
    caches.match(event.request).then(function(cached) {
      if (cached) return cached;
      return fetch(event.request).then(function(response) {
        if (response && response.status === 200) {
          var clone = response.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(event.request, clone);
          });
        }
        return response;
      }).catch(function() {
        // Return empty response if both cache and network fail
        return new Response('', { status: 503 });
      });
    })
  );
});
