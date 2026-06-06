# Browser-only profile/thread (de-SSR) — design

> Status: design (no prod change). Unblocked by the directive **"kotoba-base では
> SEO は重要視しない"** (2026-06-06) + the browser-only-kotoba migration shipped
> this session. Anchors: ADR-2605262130 / 2605312345 (kotoba Datom log canonical,
> browser-side reads), ADR-2605215000 (Murakumo-only).

## Where we are (empirical)

Verified with `70-tools/kotoba-e2e` against live etzhayyim.com:

| Surface | data_path | Browser-only? |
|---|---|---|
| Home feed (`/`) | `csr-sw` | ✅ yes — SW serves from content-addressed IPFS blocks, **0 RisingWave reads** |
| Profile (`/profile/<id>`) | `ssr` | ❌ no — **0 client XRPC**; rendered server-side via `+page.server.ts` (`ssr=true`, `getProfile(handle, platform)` → PDS_SERVICE → RisingWave) |
| Post thread (`/profile/<id>/post/<rkey>`) | `ssr` | ❌ no — same (`+page.server.ts`, `ssr=true`) |

`+page.svelte loadProfile()` *does* contain a client `fetch('/xrpc/app.bsky.actor.getProfile')`
— but only inside the `did:web:` (app-agent) branch. For `did:gftd:` / human DIDs it
relies on the SSR-provided `data.og.did` and fetches nothing client-side. Hence the
observed 0 client XRPC.

## What "SEO not important" changes

The ONLY reason `+page.server.ts` SSR'd profile/thread was OG/SEO + crawler
snapshots (yoro CLAUDE.md §SEO). With SEO de-prioritised for kotoba-base, the
SSR-from-RisingWave path can be removed and these pages can render browser-side
(CSR + the kotoba Service Worker), making the data path `csr-sw` like the feed.

## Required change (NOT a one-line `ssr=false`)

Flipping `export const ssr = false` alone would BREAK `did:gftd:`/human profiles —
they currently get their data from SSR `data.og`, and the client path fetches
nothing for them. The change is:

1. **`profile/[handle]/+page.server.ts`** and **`post/[rkey]/+page.server.ts`:**
   `export const ssr = false` (drop the server `getProfile`/`getPostThread`). Keep
   only pure-routing logic (e.g. the legacy-nanoid 301), no PDS fetch.
2. **`profile/[handle]/+page.svelte` `loadProfile()`:** fetch
   `GET /xrpc/app.bsky.actor.getProfile?actor=<did|handle>` **for every DID type**
   (not just `did:web:`), so the kotoba SW intercepts it and serves browser-side.
   Remove the `data.og.did` short-circuit (no SSR data anymore; resolve the DID
   client-side via `isDid()` / `didFromRouteActor()` / `resolveHandle()`).
3. **`post/[rkey]/+page.svelte`:** same — client `getPostThread` via the SW.
4. **Accept the bounded-data tradeoff (already the feed's posture):** the SW
   answers from the published blocks (feed authors resolve via `profileFromPostAuthor`;
   thread posts resolve if in the blocks); everything else → the SW's browser-only
   `notFound` (no RisingWave). This is the inherent browser-only ⇒ bounded-data
   tradeoff — fine for kotoba-base, which is the bounded kotoba dataset, not the
   ~200M-actor universe.
5. **Delete/disable the crawler SSR snapshot** for these routes if it still hits
   RisingWave (SEO de-prioritised) — or leave it (it is a separate UA-gated path),
   but it is no longer required.

## Verification (objective gate)

After the change, `70-tools/kotoba-e2e` must show:

```
python -m kotoba_e2e.run --url https://etzhayyim.com/profile/<seeded-did>  --no-agent
  → data_path = csr-sw   (was: ssr)
  → no_risingwave_reads  clean
```

A seeded feed-author profile → `csr-sw` + rendered; a random actor → SW `notFound`
(browser-only), never a RisingWave read.

## Risk + rollout

- Touches the main frontend's profile/thread rendering for ALL browsers. Most
  profiles (non-seeded actors) will show browser-only `notFound` — the accepted
  bounded-data tradeoff, but a visible behaviour change.
- The `+page.svelte` data loading has several DID branches (did:web agent vs
  did:gftd/human vs gov fields); each must be re-pointed at the client `getProfile`
  so none silently render blank. This is the real work — verify each branch.
- Roll out behind a verify-and-revert loop: deploy → `kotoba-e2e` against a seeded
  profile + a random actor → revert (one-line `ssr=true`) if data_path ≠ csr-sw or
  the page renders blank.

## Not doing (yet)

- Reworking `+page.svelte`'s multi-branch loader is deferred to an implementation
  pass — it is not a safe blind one-line flip, and the main frontend should not be
  broken speculatively. This doc is the plan; implementation + the verify-and-revert
  deploy is the next step once the loader rework is reviewed.
