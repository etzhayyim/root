---
id: adr-2606071100-yoro-browser-only-kotoba-reads-and-profile-fix-e2e
title: "ADR-2606071100: yoro browser-only kotoba reads (no RisingWave), profile-500 fix, and the langgraph+browser-use+Murakumo e2e harness"
status: accepted
doc_type: adr
topic: yoro-browser-only-kotoba-reads
authoritative: true
last_verified: 2026-06-07
priority: 4.0
axis: architecture
weight: 0.60
priority_note: "Fixes the user-reported 'vibes 表示が遅い' + an all-profiles 500; establishes the browser-only read path + its e2e verifier."
authoritative_for:
  - yoro-home-feed-read-path
  - kotoba-browser-only-reads
  - browser-only-e2e-verification
depends_on:
  - "2605262130"
  - "2605312345"
  - "2605215000"
related:
  - "2606013800"
  - "2606014600"
superseded_by: []
supersedes: []
---

# ADR-2606071100: yoro browser-only kotoba reads, profile-500 fix, and the e2e harness

**Status**: accepted
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

## Context

The user reported the home "vibes" feed at https://etzhayyim.com was slow to
display. Measurement showed the apex HTML is fast (~87ms) but the feed/profile
XRPC reads proxied to the RisingWave-backed AppView (`atproto.etzhayyim.com`) cost
**2.8–5.2 s each, warm or cold** — the SvelteKit SPA waits on them before painting
posts. Per ADR-2605262130 / 2605312345 the canonical state is the kotoba Datom log
(IPFS blocks; RisingWave prohibited as canonical), and reads are meant to resolve
**in the browser** (kotoba-sw.js + kotoba-wasm), not via a server.

While fixing this, two further problems surfaced: (a) two early stop-gaps were
off-design — a CF edge-cache over the slow AppView and a `KotobaRoot` Durable
Object for publish CAS; (b) a **pre-existing, all-profiles-500** bug in real
browsers (SSR was clean).

## Decision

1. **Home feed is browser-only.** Generated the `yoro-social-v1` content-addressed
   blocks + root (`gen-kotoba-blocks.mjs`) served as static apex assets; the
   Service Worker hydrates from CID-verified IPFS blocks (or the seed snapshot) and
   serves `app.bsky.feed.*` / `actor.getProfile` from the in-browser Datom log. On a
   read MISS the SW no longer falls through to the RisingWave AppView — it returns a
   browser-only empty/`notFound` (bounded data: coverage = the published blocks).
2. **Remove the off-design stop-gaps.** Deleted the AppView edge-cache and the
   `KotobaRoot` Durable Object (`wrangler.toml` v2 `deleted_classes` migration);
   the publish path advances the root under KV check-and-set (no DO, no server key,
   ADR-2605231525). `XRPC_KOTOBA_UPSTREAM` set EMPTY — kotoba is not a server;
   `com.etzhayyim.apps.kotoba.*` block.put/has/root stay apex-local (KV), every
   other such NSID returns 503 instead of proxying to a kotoba node.
3. **First-paint.** Register the SW from `app.html` `<head>` (earliest), prefetch
   the kotoba WASM, and paint a self-removing boot skeleton (hard 8 s fallback).
4. **Fix the profile-500 (P1).** Root cause: `AgentProfile.svelte` STATICALLY
   imported `BpmnDiagram.svelte`, whose top-level `import 'bpmn-js/dist/assets/*.css'`
   are BARE specifiers; `bpmn-js` is externalized in the prod build (a dev-only stub
   masked it), so those bare specifiers became unresolvable runtime imports →
   TypeError at the profile route chunk's module-eval → SvelteKit 500 in every
   browser (crawlers/SSR got a clean 200). Fix: lazy-load `BpmnDiagram` via
   `{#await import()} … {:catch}`, removing the bare-CSS module from the profile
   route's critical graph.
5. **e2e verifier.** New `70-tools/kotoba-e2e` — a langgraph + browser-use + LLM
   harness whose inference is **Murakumo-only** (`assert_murakumo_only` refuses any
   non-fleet base URL, ADR-2605215000). A deterministic Playwright layer
   (`browser.py` + pure `signals.py`) gates the verdict; an agentic layer
   (browser-use, Murakumo LLM) adds semantic judgement when the gateway is up. It
   classifies each page's data path (`csr-sw` / `csr-net` / `ssr` / `empty`).

## Honest scope / not-yet

- **profile + post-thread are still SSR** from the RisingWave AppView
  (`+page.server.ts ssr=true` → `getProfile`/`getPostThread` via PDS_SERVICE).
  They render `data_path=ssr`, not browser-only. De-SSR is designed
  (`90-docs/260606-profile-thread-browser-only-de-ssr.md`) but deferred — a blind
  `ssr=false` breaks the multi-branch client loader (attempt #1 reverted), so it
  needs an interactive `loadProfile()` rework. SEO is de-prioritised for kotoba-base
  (operator directive 2026-06-07), which unblocks it.
- Browser-only ⇒ **bounded data**: the etzhayyim social feed is small (~9 authors /
  ~100 posts), so the seed already covers ~the whole feed; the unbounded ~200M-actor
  profile universe inherently cannot live in the browser (misses → notFound).
- Stage-E internal-HMAC dissolution (`access_jwt_verify.py`, 12/12 tests) is
  implemented but operator-gated (kubectl + Cloudflare Access).

## Verification (empirical, live)

`70-tools/kotoba-e2e --no-agent` against live **https://etzhayyim.com**:
`sw_active ✓`, `blocks_hydrated ✓ (x-kotoba-src=blocks)`, `no_risingwave_reads ✓`,
`feed_served_by_sw ✓`, `skeleton seen→removed ✓`, `posts_rendered ✓`,
`data_path=csr-sw`. Profile-500 fix verified in headed **and** headless Chromium
across 3 profiles (was 500 in both → OK). Offline unit tests: 7 signals + 6
murakumo guard + 12 access-jwt = 25 green. Deploys: apex did-web + kotodama-yoro
(several iterations; final live seed 102 posts / 0 malformed).

## Consequences

- The home feed renders browser-side from content-addressed blocks with **zero
  RisingWave reads**; the AppView route remains only for non-kotoba functions
  (writes, auth, search) and non-SW clients.
- A real, pre-existing, user-facing P1 (all profile pages 500) is fixed.
- A reusable, charter-clean (Murakumo-only) browser e2e verifier exists,
  independent of the Claude Chrome extension.

## References

- ADR-2605262130 (kotoba storage substrate), ADR-2605312345 (Datom first-class
  canonical state), ADR-2605215000 (Murakumo-only inference),
  ADR-2605231525 (no-server-key), ADR-2606013800 / 2606014600 (dynamic did.json /
  trustless IPFS gateway).
- `70-tools/kotoba-e2e/` · `90-docs/260606-profile-thread-browser-only-de-ssr.md`
- `50-infra/k8s/bpmn-dispatcher/STAGE-E-HMAC-DISSOLUTION.md`
