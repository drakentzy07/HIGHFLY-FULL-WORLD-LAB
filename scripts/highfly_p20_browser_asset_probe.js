/* HIGHFLY P20 private browser-only asset failure probe.
 * Observes failures without changing app assets, scene or error policy.
 * The exported JSON contains same-origin resource paths, not hostnames/tokens.
 */
(() => {
  'use strict';
  const namespace = '__HIGHFLY_P20_PROBE__';
  if (window[namespace]) return;
  const begunAt = Date.now();
  const entries = new Map();
  let attempts = 0;
  let badResponses = 0;
  let captureErrors = 0;
  const MAX_ENTRIES = 5000;
  const assetPath = (input) => {
    try {
      const target = typeof input === 'string' ? input
        : (input && typeof input.url === 'string' ? input.url : String(input));
      const url = new URL(target, window.location.href);
      if (url.origin !== window.location.origin) return null;
      const path = url.pathname;
      return /^\/(?:models|textures|vfx)\//i.test(path) ? path : null;
    } catch {
      return null;
    }
  };
  const record = (path, reason, status = null) => {
    if (!path) return;
    const key = path + '|' + reason + '|' + (status ?? '');
    const now = Date.now() - begunAt;
    let item = entries.get(key);
    if (!item) {
      if (entries.size >= MAX_ENTRIES) return;
      item = { path, reason, status, attempts: 0, firstMs: now, lastMs: now };
      entries.set(key, item);
    }
    item.attempts++;
    item.lastMs = now;
    refresh();
  };
  const originalFetch = window.fetch;
  if (typeof originalFetch === 'function') {
    window.fetch = function (input, init) {
      const path = assetPath(input);
      if (path) attempts++;
      let result;
      try {
        result = originalFetch.apply(this, arguments);
      } catch (error) {
        if (path) record(path, 'FETCH_THROW');
        throw error;
      }
      if (!path) return result;
      return Promise.resolve(result).then(
        (response) => {
          const contentType = response.headers?.get('content-type') ?? '';
          const wrongMime = /text\/html|application\/xhtml/i.test(contentType);
          if (!response.ok || wrongMime) {
            badResponses++;
            record(path, wrongMime ? 'HTML_FALLBACK_OR_WRONG_MIME' : 'HTTP_ERROR',
              response.status);
          }
          return response;
        },
        (error) => {
          badResponses++;
          record(path, 'FETCH_REJECTED');
          throw error;
        }
      );
    };
  }
  window.addEventListener('error', (ev) => {
    const element = ev.target;
    const source = element && element !== window &&
      (element.currentSrc || element.src || element.href);
    const path = source ? assetPath(source) : null;
    if (path) {
      captureErrors++;
      record(path, 'ELEMENT_LOAD_ERROR');
    }
    const message = typeof ev.message === 'string' ? ev.message : '';
    // Only extract local resource paths from JS errors; never retain raw error text.
    const matches = message.match(/\/(?:models|textures|vfx)\/[A-Za-z0-9_./-]+/gi) || [];
    for (const match of matches.slice(0, 200)) {
      const safePath = assetPath(match);
      if (safePath) record(safePath, 'JAVASCRIPT_ERROR_MENTION');
    }
  }, true);
  window.addEventListener('unhandledrejection', (ev) => {
    const message = String(ev.reason instanceof Error ? ev.reason.message : ev.reason ?? '');
    const matches = message.match(/\/(?:models|textures|vfx)\/[A-Za-z0-9_./-]+/gi) || [];
    for (const match of matches.slice(0, 250)) {
      const safePath = assetPath(match);
      if (safePath) record(safePath, 'PROMISE_REJECTION_MENTION');
    }
  });
  const report = () => {
    const failures = [...entries.values()].sort((a, b) => a.firstMs - b.firstMs);
    const byCategory = {};
    for (const x of failures) {
      const category = x.path.split('/').slice(1, 3).join('/');
      byCategory[category] = (byCategory[category] || 0) + 1;
    }
    return {
      product: 'HIGHFLY ORIGIN',
      diagnostic: 'P20 PRIVATE BROWSER ASSET PROBE',
      capturedAt: new Date().toISOString(),
      elapsedMs: Date.now() - begunAt,
      pagePath: window.location.pathname,
      fetchAssetAttempts: attempts,
      badFetchResponses: badResponses,
      elementErrors: captureErrors,
      distinctFailures: failures.length,
      missingByCategory: byCategory,
      failures,
      notes: [
        'No source code, media, game mechanics or error policy were changed by the probe.',
        'Repeated retries appear as counts; entries are unique path/reason/status.',
        'A 200 text/html response for a GLB may mean a Vite SPA fallback, not a valid model.',
        'Fetch hook captures errors and wrong MIME, not GLB parse errors returning valid binary.',
        'Only events after this script loaded are covered. Dynamic assets may still be absent.'
      ]
    };
  };
  let button = null;
  const refresh = () => {
    if (button) button.textContent = 'HIGHFLY LOG · ' + entries.size + ' fallos · DESCARGAR';
  };
  const download = () => {
    const json = JSON.stringify(report(), null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'HIGHFLY_P20_BROWSER_ASSET_LOG.json';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 5000);
  };
  const attachButton = () => {
    if (!document.body) return;
    if (button && button.isConnected) return;
    button = document.createElement('button');
    button.type = 'button';
    button.setAttribute('aria-label', 'Descargar diagnóstico HIGHFLY P20');
    Object.assign(button.style, {
      position: 'fixed', left: '12px', bottom: '12px', zIndex: '2147483647',
      background: '#111c2d', color: '#aee9ff', border: '1px solid #50b8e8',
      borderRadius: '8px', padding: '10px 12px', font: 'bold 12px sans-serif',
      cursor: 'pointer', maxWidth: '90vw', boxShadow: '0 0 9px #143e56'
    });
    button.addEventListener('click', download);
    document.body.appendChild(button);
    refresh();
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attachButton, { once: true });
  } else {
    attachButton();
  }
  // Recover the diagnostic control if the game completely replaces its body.
  document.addEventListener('DOMContentLoaded', () => {
    const obs = new MutationObserver(() => {
      if (button && !button.isConnected) attachButton();
    });
    obs.observe(document.documentElement, { childList: true, subtree: false });
    if (document.body) obs.observe(document.body, { childList: true });
  }, { once: true });
  window[namespace] = Object.freeze({ report, download });
  console.info('[HIGHFLY P20] Private asset diagnostics active (download button bottom-left).');
})();
