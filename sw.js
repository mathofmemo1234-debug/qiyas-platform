/**
 * Service Worker - منصة نبيه للقدرات العامة
 * يوفر إمكانية التثبيت كـ PWA والعمل دون اتصال وتخزين الملفات الأساسية
 */

const CACHE_NAME = 'nabih-qiyas-v8-4options-cbt';
const CORE_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './pwa-install.js',
  './pdf-import.js',
  './firebase-config.js',
  './firebase-service.js',
  './questions.json',
  './foundation_data.json',
  './downloadable_pdfs.json',
  './scanned_data.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-192.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon.png'
];

// تثبيت Service Worker وتخزين الملفات الأساسية فوراً
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      for (const asset of CORE_ASSETS) {
        try {
          await cache.add(asset);
        } catch (err) {
          console.warn('[SW] تحذير عند تخزين الأصل مسبقاً:', asset, err);
        }
      }
    }).then(() => self.skipWaiting())
  );
});

// تفعيل وتطهير كافة الإصدارات القديمة من الكاش فوراً
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((name) => {
          if (name !== CACHE_NAME) {
            console.log('[SW] حذف الكاش القديم:', name);
            return caches.delete(name);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// التعامل مع الطلبات (Fetch Requests)
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // لا نعالج الطلبات غير التابعة لـ GET
  if (request.method !== 'GET') {
    return;
  }

  // Network First لجميع صفحات HTML والبيانات والـ APIs
  // لضمان استلام أحدث بنك أسئلة (150 سؤالاً) والتحديثات دائماً عند توفر النت
  const isNetworkFirst = url.pathname.endsWith('.json') ||
                         url.pathname.endsWith('.html') ||
                         url.pathname === '/' ||
                         url.pathname.endsWith('/index.html') ||
                         url.pathname.startsWith('/api/');

  if (isNetworkFirst) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // لباقي الأصول الثابتة (أيقونات، خطوط، مكتبات): Stale While Revalidate
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      const fetchPromise = fetch(request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return networkResponse;
        })
        .catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});
