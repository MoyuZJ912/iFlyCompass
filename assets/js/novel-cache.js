/**
 * NovelCache - IndexedDB wrapper for whole-book caching.
 *
 * Stores raw novel file bytes, decoded text, local reading progress,
 * and user settings. Supports resume download via HTTP Range.
 *
 * DB: NovelCacheDB v2
 *   novelFiles    — key: novelName, full book data + metadata
 *   readingProgress — key: novelName, local reading position
 *   userSettings  — key: novelName, per-novel user preferences
 */
(function () {
  'use strict';

  var DB_NAME = 'NovelCacheDB';
  var DB_VERSION = 2;
  var FILE_STORE = 'novelFiles';
  var PROGRESS_STORE = 'readingProgress';
  var SETTINGS_STORE = 'userSettings';

  var _db = null;
  var _pending = null;

  function openDB() {
    if (_db) return Promise.resolve(_db);
    if (_pending) return _pending;

    _pending = new Promise(function (resolve, reject) {
      var request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = function (e) {
        var db = e.target.result;
        var oldVersion = e.oldVersion;

        // Clean up old v1 stores if migrating
        if (oldVersion < 2) {
          if (db.objectStoreNames.contains('chapterLists')) {
            db.deleteObjectStore('chapterLists');
          }
          if (db.objectStoreNames.contains('chapterContents')) {
            db.deleteObjectStore('chapterContents');
          }
        }

        if (!db.objectStoreNames.contains(FILE_STORE)) {
          db.createObjectStore(FILE_STORE, { keyPath: 'novelName' });
        }
        if (!db.objectStoreNames.contains(PROGRESS_STORE)) {
          db.createObjectStore(PROGRESS_STORE, { keyPath: 'novelName' });
        }
        if (!db.objectStoreNames.contains(SETTINGS_STORE)) {
          db.createObjectStore(SETTINGS_STORE, { keyPath: 'novelName' });
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
    var args = Array.prototype.slice.call(arguments, 2);
    return new Promise(function (resolve, reject) {
      var request = store[method].apply(store, args);
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { reject(request.error); };
    });
  }

  // ── File storage ────────────────────────────────────────────────

  function getFileStore(mode) {
    return openDB().then(function (db) {
      return db.transaction(FILE_STORE, mode).objectStore(FILE_STORE);
    });
  }

  window.NovelCache = {

    // ── Novel file operations ─────────────────────────────────────

    /**
     * Get stored novel file record.
     * Returns { novelName, totalSize, encoding, serverModified,
     *           receivedBytes, content, complete, cachedAt } or null.
     */
    getNovelFile: function (novelName) {
      return openDB().then(function (db) {
        return promiseRequest(
          db.transaction(FILE_STORE, 'readonly').objectStore(FILE_STORE),
          'get', novelName
        );
      }).catch(function (err) {
        console.warn('[NovelCache] getNovelFile failed:', err.message);
        return null;
      });
    },

    /**
     * Store/update a novel file record.
     */
    putNovelFile: function (record) {
      return openDB().then(function (db) {
        return new Promise(function (resolve, reject) {
          var tx = db.transaction(FILE_STORE, 'readwrite');
          var store = tx.objectStore(FILE_STORE);
          store.put(record);
          tx.oncomplete = function () { resolve(); };
          tx.onerror = function () { reject(tx.error); };
        });
      }).catch(function (err) {
        console.warn('[NovelCache] putNovelFile failed:', err.message);
      });
    },

    /**
     * Save partial download progress for resume support.
     */
    savePartialBytes: function (novelName, rawBytes, receivedBytes, totalSize, encoding, serverModified) {
      return this.putNovelFile({
        novelName: novelName,
        rawBytes: rawBytes,
        totalSize: totalSize,
        encoding: encoding,
        serverModified: serverModified,
        receivedBytes: receivedBytes,
        content: null,
        complete: false,
        cachedAt: Date.now()
      });
    },

    /**
     * Mark download complete with decoded content.
     */
    markDownloadComplete: function (novelName, content, totalSize, encoding, serverModified) {
      return this.putNovelFile({
        novelName: novelName,
        totalSize: totalSize,
        encoding: encoding,
        serverModified: serverModified,
        receivedBytes: totalSize,
        content: content,
        rawBytes: null,
        complete: true,
        cachedAt: Date.now()
      });
    },

    /**
     * Check if a novel is fully cached and up-to-date with server.
     */
    isNovelCached: function (novelName, serverModified) {
      return this.getNovelFile(novelName).then(function (record) {
        if (!record || !record.complete) return false;
        if (serverModified !== undefined && record.serverModified !== serverModified) return false;
        return true;
      });
    },

    /**
     * Get all locally cached novels (for the local list).
     */
    getAllLocalNovels: function () {
      return openDB().then(function (db) {
        return promiseRequest(
          db.transaction(FILE_STORE, 'readonly').objectStore(FILE_STORE),
          'getAll'
        ).then(function (records) {
          return records.filter(function (r) { return r.complete; });
        });
      }).catch(function (err) {
        console.warn('[NovelCache] getAllLocalNovels failed:', err.message);
        return [];
      });
    },

    /**
     * Delete a novel from local cache.
     */
    deleteNovel: function (novelName) {
      return openDB().then(function (db) {
        return new Promise(function (resolve, reject) {
          var tx = db.transaction([FILE_STORE, PROGRESS_STORE, SETTINGS_STORE], 'readwrite');
          tx.objectStore(FILE_STORE).delete(novelName);
          tx.objectStore(PROGRESS_STORE).delete(novelName);
          tx.objectStore(SETTINGS_STORE).delete(novelName);
          tx.oncomplete = function () { resolve(); };
          tx.onerror = function () { reject(tx.error); };
        });
      }).catch(function (err) {
        console.warn('[NovelCache] deleteNovel failed:', err.message);
      });
    },

    // ── Reading progress (local only) ─────────────────────────────

    getProgress: function (novelName) {
      return openDB().then(function (db) {
        return promiseRequest(
          db.transaction(PROGRESS_STORE, 'readonly').objectStore(PROGRESS_STORE),
          'get', novelName
        );
      }).catch(function () { return null; });
    },

    saveProgress: function (novelName, chapterIndex, scrollPosition) {
      return openDB().then(function (db) {
        return promiseRequest(
          db.transaction(PROGRESS_STORE, 'readwrite').objectStore(PROGRESS_STORE),
          'put',
          { novelName: novelName, chapterIndex: chapterIndex,
            scrollPosition: scrollPosition || 0, updatedAt: Date.now() }
        );
      }).catch(function (err) {
        console.warn('[NovelCache] saveProgress failed:', err.message);
      });
    },

    // ── User settings ─────────────────────────────────────────────

    getSettings: function (novelName) {
      return openDB().then(function (db) {
        return promiseRequest(
          db.transaction(SETTINGS_STORE, 'readonly').objectStore(SETTINGS_STORE),
          'get', novelName
        );
      }).then(function (record) {
        return record || { novelName: novelName, skipUpdatePrompt: false };
      }).catch(function () {
        return { novelName: novelName, skipUpdatePrompt: false };
      });
    },

    setSettings: function (novelName, settings) {
      return openDB().then(function (db) {
        var store = db.transaction(SETTINGS_STORE, 'readwrite').objectStore(SETTINGS_STORE);
        return promiseRequest(store, 'get', novelName).then(function (existing) {
          var merged = existing || { novelName: novelName };
          Object.keys(settings).forEach(function (k) {
            merged[k] = settings[k];
          });
          return promiseRequest(store, 'put', merged);
        });
      }).catch(function (err) {
        console.warn('[NovelCache] setSettings failed:', err.message);
      });
    },

    // ── Utility ───────────────────────────────────────────────────

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
