/**
 * Service Worker - منصة نبيه للقدرات العامة
 * يوفر إمكانية التثبيت كـ PWA والعمل دون اتصال وتخزين الملفات الأساسية
 */

const CACHE_NAME = 'nabih-qiyas-v4-pdf-engine';
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
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-192.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon.png'
];

// تثبيت Service Worker وتخزين الملفات الأساسية
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      // نستخدم التخزين الفردي لضمان نجاح التثبيت حتى لو تعذر جلب ملف واحد
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

// تفعيل وتطهير الإصدارات القديمة من الكاش
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((name) => {
          if (name.startsWith('nabih-qiyas-') && name !== CACHE_NAME) {
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

  // لطلبات الـ API المحلية: Network First مع كاش كبديل عند انقطاع النت
  if (url.pathname.startsWith('/api/')) {
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

  // لباقي ملفات الواجهة والخطوط والمكتبات الخارجية (Stale While Revalidate)
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
        .catch((err) => {
          // في حال كان الجهاز دون اتصال
          return cachedResponse;
        });

      return cachedResponse || fetchPromise;
    })
  );
});
