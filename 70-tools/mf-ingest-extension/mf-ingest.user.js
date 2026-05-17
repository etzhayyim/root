// ==UserScript==
// @name         MF CSV Ingest Helper (Tampermonkey)
// @namespace    https://etzhayyim.com/adr-0031
// @version      1.0
// @description  Ingest MoneyForward CSV exports via localhost writer. Bypasses Chrome Private Network Access + programmatic multi-download restrictions.
// @match        https://accounting.moneyforward.com/*
// @match        https://invoice.moneyforward.com/*
// @match        https://contract.moneyforward.com/*
// @match        https://pc.moneyforward.com/*
// @grant        GM_xmlhttpRequest
// @grant        unsafeWindow
// @connect      127.0.0.1
// @connect      localhost
// @run-at       document-start
// ==/UserScript==

(function () {
  'use strict';

  const ENDPOINT = 'http://127.0.0.1:8765';

  // Exposed on the page as window.__mfSave(name, textOrBlob) → Promise
  // GM_xmlhttpRequest runs in a privileged context, so it bypasses
  // Mixed Content + Private Network Access blocks that prevent the
  // page itself from POSTing to 127.0.0.1.
  function save(name, body) {
    return new Promise((resolve, reject) => {
      if (!/^[-A-Za-z0-9._]+$/.test(name)) {
        return reject(new Error('bad name: ' + name));
      }
      GM_xmlhttpRequest({
        method: 'POST',
        url: ENDPOINT + '/' + encodeURIComponent(name),
        data: body,
        headers: { 'Content-Type': 'text/csv; charset=utf-8' },
        timeout: 30000,
        onload: (res) => {
          if (res.status === 200) resolve({ ok: true, name, msg: (res.responseText || '').trim() });
          else reject(new Error('status ' + res.status + ' ' + (res.responseText || '')));
        },
        onerror: (err) => reject(new Error('xhr error ' + (err.error || 'unknown'))),
        ontimeout: () => reject(new Error('timeout')),
      });
    });
  }

  // Install on the page window (unsafeWindow = real page context in Tampermonkey)
  try {
    unsafeWindow.__mfSave = function (name, body) {
      return save(name, body);
    };
    unsafeWindow.__mfIngest = { version: '1.0', endpoint: ENDPOINT };
    // Also a quick ping for probing from page JS
    unsafeWindow.__mfPing = function () {
      return new Promise((resolve) => {
        GM_xmlhttpRequest({
          method: 'POST',
          url: ENDPOINT + '/ping.txt',
          data: 'pong',
          timeout: 5000,
          onload: (r) => resolve({ ok: r.status === 200, status: r.status }),
          onerror: () => resolve({ ok: false, err: 'error' }),
          ontimeout: () => resolve({ ok: false, err: 'timeout' }),
        });
      });
    };
    // eslint-disable-next-line no-console
    console.log('[mf-ingest] userscript loaded. window.__mfSave(name, body) and window.__mfPing() available.');
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error('[mf-ingest] userscript install failed:', e);
  }
})();
