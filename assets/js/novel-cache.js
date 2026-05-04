/**
 * NovelCache - IndexedDB wrapper for novel chapter caching.
 * All novel chapter content is stored browser-side so repeated
 * chapter navigation skips the server API entirely.
 */
(function () {
  'use strict';

  var DB_NAME = 'NovelCacheDB';
  var DB_VERSION = 1;
  var LIST_STORE = 'chapterLists';
  var CONTENT_STORE = 'chapterContents';

  var _db = null;
  var _pending = null;

  function openDB() {
    if (_db) return Promise.resolve(_db);
    if (_pending) return _pending;

    _pending = new Promise(function (resolve, reject) {
      var request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = function (e) {
        var db = e.target.result;
        if (!db.objectStoreNames.contains(LIST_STORE)) {
          db.createObjectStore(LIST_STORE, { keyPath: 'novelName' });
        }
        if (!db.objectStoreNames.contains(CONTENT_STORE)) {
          db.createObjectStore(CONTENT_STORE, { keyPath: 'key' });
        }
      };

      request.onsuccess = function (e) {
        _db = e.target.result;
        _pending = null;
        resolve(_db);
      };

      request.onerror = function (e) {
        _pending = null;
        console.error('[NovelCache] Failed to open database:', e.target.error);
        reject(e.target.error);
      };
    });

    return _pending;
  }

  function promiseRequest(store, method) {
    return new Promise(function (resolve, reject) {
      var request = store[method].apply(store, Array.prototype.slice.call(arguments, 2));
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { reject(request.error); };
    });
  }

  window.NovelCache = {
    getChapterList: function (novelName) {
      return openDB().then(function (db) {
        return promiseRequest(
          db.transaction(LIST_STORE, 'readonly').objectStore(LIST_STORE),
          'get',
          novelName
        ).then(function (record) {
          return record ? record.chapters : null;
        });
      }).catch(function (err) {
        console.warn('[NovelCache] getChapterList failed, will fetch from server:', err.message);
        return null;
      });
    },

    setChapterList: function (novelName, chapters) {
      return openDB().then(function (db) {
        return promiseRequest(
          db.transaction(LIST_STORE, 'readwrite').objectStore(LIST_STORE),
          'put',
          { novelName: novelName, chapters: chapters, cachedAt: Date.now() }
        );
      }).catch(function (err) {
        console.warn('[NovelCache] setChapterList failed:', err.message);
      });
    },

    getChapterContent: function (novelName, chapterIndex) {
      var key = novelName + '_' + chapterIndex;
      return openDB().then(function (db) {
        return promiseRequest(
          db.transaction(CONTENT_STORE, 'readonly').objectStore(CONTENT_STORE),
          'get',
          key
        ).then(function (record) {
          if (!record) return null;
          return { content: record.content, chapterName: record.chapterName };
        });
      }).catch(function (err) {
        console.warn('[NovelCache] getChapterContent failed, will fetch from server:', err.message);
        return null;
      });
    },

    setChapterContent: function (novelName, chapterIndex, content, chapterName) {
      var key = novelName + '_' + chapterIndex;
      return openDB().then(function (db) {
        return promiseRequest(
          db.transaction(CONTENT_STORE, 'readwrite').objectStore(CONTENT_STORE),
          'put',
          { key: key, content: content, chapterName: chapterName, cachedAt: Date.now() }
        );
      }).catch(function (err) {
        console.warn('[NovelCache] setChapterContent failed:', err.message);
      });
    },

    isNovelFullyCached: function (novelName, totalChapters) {
      return openDB().then(function (db) {
        var store = db.transaction(CONTENT_STORE, 'readonly').objectStore(CONTENT_STORE);
        var range = IDBKeyRange.bound(novelName + '_0', novelName + '_' + (totalChapters - 1));
        return promiseRequest(store, 'count', range).then(function (count) {
          return count >= totalChapters;
        });
      }).catch(function (err) {
        console.warn('[NovelCache] isNovelFullyCached failed:', err.message);
        return false;
      });
    },

    cacheAllChapters: function (novelName, chapters) {
      return openDB().then(function (db) {
        var tx = db.transaction(CONTENT_STORE, 'readwrite');
        var store = tx.objectStore(CONTENT_STORE);
        return Promise.all(chapters.map(function (ch) {
          return promiseRequest(store, 'put', {
            key: novelName + '_' + ch.index,
            content: ch.content,
            chapterName: ch.name,
            cachedAt: Date.now()
          });
        }));
      }).catch(function (err) {
        console.warn('[NovelCache] cacheAllChapters failed:', err.message);
      });
    },

    getCachedChapterCount: function (novelName) {
      return openDB().then(function (db) {
        var range = IDBKeyRange.bound(novelName + '_', novelName + '_￿');
        return promiseRequest(
          db.transaction(CONTENT_STORE, 'readonly').objectStore(CONTENT_STORE),
          'count',
          range
        );
      }).catch(function (err) {
        console.warn('[NovelCache] getCachedChapterCount failed:', err.message);
        return 0;
      });
    },

    deleteNovel: function (novelName) {
      return openDB().then(function (db) {
        var tx = db.transaction([LIST_STORE, CONTENT_STORE], 'readwrite');
        promiseRequest(tx.objectStore(LIST_STORE), 'delete', novelName);

        // Delete all chapter contents for this novel
        var contentStore = tx.objectStore(CONTENT_STORE);
        var range = IDBKeyRange.bound(novelName + '_', novelName + '_￿');
        promiseRequest(contentStore, 'openCursor', range).then(function (cursor) {
          return new Promise(function (resolve) {
            function deleteNext(c) {
              if (!c) { resolve(); return; }
              c.delete();
              c.continue();
            }
            contentStore.openCursor(range).onsuccess = function (e) {
              var c = e.target.result;
              if (c) { c.delete(); c.continue(); } else { resolve(); }
            };
          });
        });
      }).catch(function (err) {
        console.warn('[NovelCache] deleteNovel failed:', err.message);
      });
    },

    clearAll: function () {
      return openDB().then(function (db) {
        db.close();
        _db = null;
        return new Promise(function (resolve, reject) {
          var request = indexedDB.deleteDatabase(DB_NAME);
          request.onsuccess = function () { resolve(); };
          request.onerror = function () { reject(request.error); };
        });
      }).catch(function (err) {
        console.warn('[NovelCache] clearAll failed:', err.message);
      });
    }
  };
})();
