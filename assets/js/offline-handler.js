/**
 * 离线请求处理器。包装 fetch，在服务端不可达时返回结构化错误对象，
 * 避免浏览器抛出 TypeError 或显示 ERR_CONNECTION_REFUSED。
 */
(function () {
  'use strict';

  var serverCheckPromise = null;
  var lastCheckTime = 0;
  var CHECK_TTL = 5000; // 5 秒内复用检测结果

  /**
   * 检测服务端是否可达。带 TTL 缓存避免频繁探测。
   */
  window.isServerReachable = function () {
    var now = Date.now();
    if (serverCheckPromise && now - lastCheckTime < CHECK_TTL) {
      return serverCheckPromise;
    }
    lastCheckTime = now;

    serverCheckPromise = new Promise(function (resolve) {
      fetch('/api/novels', { method: 'GET', cache: 'no-store' })
        .then(function (r) {
          resolve(r.ok);
        })
        .catch(function () {
          resolve(false);
        });
    });

    return serverCheckPromise;
  };

  /**
   * 安全 fetch 包装。
   * 网络可达时行为与原生 fetch 完全一致。
   * 网络不可达时返回 { error: '服务端离线', offline: true, _offline: true }。
   */
  window.safeFetch = function (url, options) {
    return fetch(url, options).catch(function (err) {
      console.warn('[离线处理] 网络请求失败:', url, err.message);
      return {
        ok: false,
        status: 0,
        offline: true,
        _offline: true,
        json: function () {
          return Promise.resolve({ error: '服务端离线，该功能暂不可用', offline: true });
        },
        text: function () {
          return Promise.resolve('');
        }
      };
    });
  };

  /**
   * 显示离线功能不可用的提示。
   * 优先使用 Element UI Message，否则降级到 alert。
   */
  window.showOfflineError = function (featureName) {
    if (window.ELEMENT && window.ELEMENT.Message) {
      window.ELEMENT.Message.warning({
        message: (featureName || '该功能') + '需要服务端支持，当前无法使用',
        duration: 3000,
        showClose: true
      });
    } else {
      console.warn('[离线提示] ' + (featureName || '该功能') + '需要服务端支持');
    }
  };

  /**
   * 检查响应是否为离线降级响应。
   */
  window.isOfflineResponse = function (response) {
    return !!(response && response._offline);
  };
})();
