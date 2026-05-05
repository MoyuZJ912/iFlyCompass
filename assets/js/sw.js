/* eslint-env serviceworker */
/**
 * iFlyCompass Service Worker
 * App Shell 全量预缓存 + 离线回退策略
 */
(function () {
  'use strict';

  var CACHE_NAME = 'iflycompass-v1';

  // ── 静态资源清单（App Shell） ──
  var STATIC_ASSETS = [
    // CSS
    '/assets/css/loading.css',
    '/assets/css/material-icons.css',
    '/assets/css/element-ui.css',
    '/assets/css/console.css',
    '/assets/css/drop.css',
    '/assets/css/style.css',
    '/assets/css/auth.css',
    '/assets/css/plyr.css',
    '/assets/css/aplayer.min.css',
    '/assets/css/video-js.min.css',
    // JS
    '/assets/js/vue.min.js',
    '/assets/js/element-ui.js',
    '/assets/js/loading.js',
    '/assets/js/drop.js',
    '/assets/js/novel-cache.js',
    '/assets/js/chapter-parser.js',
    '/assets/js/offline-handler.js',
    '/assets/js/socket.io.js',
    '/assets/js/aplayer.min.js',
    '/assets/js/plyr.min.js',
    '/assets/js/video.min.js',
    // 字体
    '/assets/css/fonts/element-icons.ttf',
    '/assets/css/fonts/element-icons.woff',
    '/assets/fonts/MaterialIcons-Regular.ttf',
    '/assets/fonts/MaterialIcons-Regular.woff2',
    // 图片和图标
    '/assets/images/logo-trans-white.png',
    '/assets/icons/icon-192x192.png',
    '/assets/icons/icon-512x512.png',
    // 清单
    '/assets/manifest.json'
  ];

  // ── HTML 页面路由（用于导航请求的离线回退） ──
  var HTML_ROUTES = [
    '/',
    '/board',
    '/board/tools',
    '/board/chat',
    '/board/users',
    '/board/passkeys',
    '/board/settings',
    '/board/swipe-test',
    '/board/announcements',
    '/tools/novelreader',
    '/tools/immersive-reader',
    '/tools/biliplayer',
    '/tools/videoplayer',
    '/tools/webproxy',
    '/ncmplayer',
    '/login',
    '/register',
    '/forgot-password',
    '/announcements',
    '/drop/settings'
  ];

  // ── Install：全量预缓存 ──
  self.addEventListener('install', function (event) {
    console.log('[SW] 安装中，预缓存 ' + (STATIC_ASSETS.length + HTML_ROUTES.length) + ' 个资源...');
    self.skipWaiting();

    event.waitUntil(
      caches.open(CACHE_NAME).then(function (cache) {
        // 分批缓存，避免一次全量加载失败
        function addAllSafely(urls) {
          return Promise.allSettled(
            urls.map(function (url) {
              return cache.add(url).catch(function (err) {
                console.warn('[SW] 预缓存失败: ' + url, err.message);
              });
            })
          );
        }

        return addAllSafely(STATIC_ASSETS).then(function () {
          return addAllSafely(HTML_ROUTES);
        }).then(function () {
          console.log('[SW] 预缓存完成');
        });
      })
    );
  });

  // ── Activate：接管客户端 + 清理旧缓存 ──
  self.addEventListener('activate', function (event) {
    console.log('[SW] 激活');
    self.clients.claim();

    event.waitUntil(
      caches.keys().then(function (keys) {
        return Promise.all(
          keys.filter(function (k) { return k !== CACHE_NAME; })
            .map(function (k) {
              console.log('[SW] 清理旧缓存:', k);
              return caches.delete(k);
            })
        );
      })
    );
  });

  // ── Fetch：分级策略 ──
  self.addEventListener('fetch', function (event) {
    var request = event.request;
    var url = new URL(request.url);

    // 只处理同源请求
    if (url.origin !== self.location.origin) return;

    // SocketIO 请求不缓存
    if (url.pathname.indexOf('/socket.io/') === 0) return;

    // ── 策略 1：静态资源 → Cache First ──
    if (isStaticAsset(url.pathname)) {
      event.respondWith(
        caches.match(request).then(function (cached) {
          return cached || fetch(request).then(function (response) {
            if (response.ok) {
              var clone = response.clone();
              caches.open(CACHE_NAME).then(function (cache) { cache.put(request, clone); });
            }
            return response;
          });
        })
      );
      return;
    }

    // ── 策略 2：API 请求 → Network Only（透传，由前端处理离线） ──
    if (isApiRequest(url.pathname)) {
      // 不拦截，让浏览器原生处理
      // 由 offline-handler.js 在各模块中实现降级
      return;
    }

    // ── 策略 3：HTML 导航请求 → Network First + Cache Fallback ──
    if (request.mode === 'navigate') {
      event.respondWith(
        fetch(request).then(function (response) {
          if (response.ok) {
            var clone = response.clone();
            caches.open(CACHE_NAME).then(function (cache) { cache.put(request, clone); });
          }
          return response;
        }).catch(function () {
          return caches.match(request).then(function (cached) {
            return cached || caches.match('/board');
          });
        })
      );
      return;
    }

    // ── 策略 4：其他请求（图片、字体等） → Cache First ──
    event.respondWith(
      caches.match(request).then(function (cached) {
        return cached || fetch(request);
      })
    );
  });

  // ── 辅助函数 ──

  function isStaticAsset(pathname) {
    return pathname.indexOf('/assets/') === 0
        || pathname.indexOf('/favicon.ico') === 0;
  }

  function isApiRequest(pathname) {
    return pathname.indexOf('/api/') === 0
        || pathname === '/login'
        || pathname === '/register'
        || pathname === '/logout';
  }
})();
