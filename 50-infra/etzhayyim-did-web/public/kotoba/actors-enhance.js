// actors-enhance.js — progressive enhancement for the apex /actors page.
//
// First-party, same-origin, zero-egress (CSP `connect-src 'self'`), cookie-free.
// Uses the ActorResolver lib to resolve every named actor AND self-verify each
// actor's canonical DID document (CID(:actor/didDocJson) === :actor/didDocCid)
// entirely in the visitor's own browser, from the content-addressed /kotoba
// blocks — no server resolution, no CF KV, no third-party call. The /actors page
// is fully functional without this script; it only adds an in-browser
// verification badge. This is not surveillance (Charter Rider §2(c) is about the
// surveillance-capitalism business model; first-party local resolution is not it
// — ADR-2606064500 Layer-C).

import { ActorResolver } from './actor-resolver.js';

const mount = document.getElementById('kotoba-verify');
if (mount) {
  (async () => {
    const t0 = (globalThis.performance?.now?.() ?? 0);
    try {
      const r = new ActorResolver({ base: '/kotoba' });
      await r.init();
      const handles = r.listHandles();
      let verified = 0;
      const failures = [];
      for (const h of handles) {
        try {
          const res = await r.resolveDid(h);
          if (res && res.verified) verified += 1;
          else failures.push(h);
        } catch {
          failures.push(h);
        }
      }
      const ms = Math.round((globalThis.performance?.now?.() ?? 0) - t0);
      const ok = failures.length === 0;
      mount.textContent =
        `✓ ${verified}/${handles.length} DID documents self-verified in your browser ` +
        `from content-addressed /kotoba blocks (no server, no KV, no third-party)` +
        (ms ? ` · ${ms} ms` : '') +
        (ok ? '' : ` · unverified: ${failures.join(', ')}`);
      mount.style.color = ok
        ? 'color-mix(in srgb, green 70%, currentColor)'
        : 'color-mix(in srgb, orange 70%, currentColor)';
      mount.hidden = false;
    } catch (e) {
      // Stay silent on failure — the server-rendered page is the baseline.
      mount.hidden = true;
      if (globalThis.console) console.warn('[actors-enhance] skipped:', e?.message || e);
    }
  })();
}
