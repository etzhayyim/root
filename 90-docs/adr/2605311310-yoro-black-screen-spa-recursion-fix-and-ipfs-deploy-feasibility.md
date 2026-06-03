---
id: adr-2605311310-yoro-black-screen-spa-recursion-fix-and-ipfs-deploy-feasibility
title: "ADR-2605311310: yoro AppView black-screen fix (SPA-router infinite recursion) + IPFS-deploy feasibility (kotoba/Kubo) session closure"
status: active
doc_type: adr
topic: yoro-black-screen-and-ipfs-deploy
authoritative: true
last_verified: 2026-05-31
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Production root-page outage fix (etzhayyim.com black screen) + empirical IPFS-deploy capability map."
authoritative_for:
  - yoro-appview-root-route-render
  - ipfs-static-frontend-deploy-feasibility
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2604261936-ipfs-self-hosted-vultr-b2
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - "60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/IPFS-DEPLOY.md"
supersedes: []
superseded_by: []
---

# ADR-2605311310: yoro AppView black-screen fix (SPA-router infinite recursion) + IPFS-deploy feasibility (kotoba/Kubo) — session closure

**Status**: active
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

`https://etzhayyim.com/` rendered a fully black page. The zone is a Cloudflare
Worker (`etzhayyim-did-web`) that proxies `yoro.etzhayyim.com` — the yoro
AppView, a Svelte 5 SPA (`+layout.ts` `ssr=false`, `csr=true`). Served via the
`magatama-yoro` Worker's Assets binding (`assets.directory: ./static`,
`not_found_handling: single-page-application`).

Empirical diagnosis (live browser + curl):

- HTTP 200 on `/` and on every `_app/immutable/*` chunk (no 404 / stale-deploy).
- Browser console: a single fatal `RangeError: Maximum call stack size exceeded`
  inside the Svelte client runtime, thrown from route node `3.*.js`.
- Client route dictionary maps `"/": [3]` → `routes/+page.svelte`.

Root cause: `routes/+page.svelte` rendered `<App/>` (`src/App.svelte`), a custom
client SPA shell that uses `src/spa/router.ts`. That router does
`import.meta.glob("../routes/**/+page.svelte", { eager: true })` and compiles
**every** page, including the root `+page.svelte` itself, to route `"/"`. So on
`/`, `App` resolved the active match to `+page.svelte`, which renders `<App/>`,
which re-resolves `/` → `+page.svelte` → `<App/>` … unbounded recursion → stack
overflow **before first paint**. With `ssr:false` and no `<noscript>` / SSR
fallback, the dark layout background was all that remained = black screen.

This contradicted the project's own documented contract
(`60-apps/etzhayyim-project-yoro/CLAUDE.md` → "Route-First Architecture": `/` =
**Vibes feed**; "禁止: `+page.svelte` に複数タブの UI を同居"). The `<App/>` +
`src/spa/*` island was an experimental shell that violated that contract and
introduced the cycle. `VibesPanel` (the actual home-feed component) was exported
from `$lib/superapp` but wired nowhere.

Secondary question raised in-session: can the frontend deploy via IPFS / kotoba
**without** Cloudflare, and be reachable over IPFS? This ADR records the
empirical capability map alongside the fix.

# Decision

**1. Fix the black screen (shipped).** `routes/+page.svelte` now renders
`<VibesPanel/>` directly, matching the documented Route-First Architecture and
the sibling pages (`apps/+page.svelte` → `<ServicesPanel/>`,
`profile/+page.svelte` → `<ProfilePanel/>`). The recursive island is deleted:
`src/App.svelte`, `src/spa/router.ts`, `src/spa/app-environment.ts`,
`src/spa/app-navigation.ts`, `src/spa/app-stores.ts` (no remaining importers).
Verified: `pnpm build` exits 0; the rebuilt route nodes contain no `spa/router`
/ `activeMatch` signature; `VibesPanel` reads the public `getDiscoverFeed` so it
renders for signed-out visitors too.

**2. IPFS deploy is mechanically possible for the static frontend, but "no
Cloudflare" is not achievable today** — record as an explicit hybrid target. The
SPA was packaged to IPFS (local Kubo 0.41 + kotoba 0.1.0 both running):
- Root CID `bafybeidl5t4ztktqmfcqrfqpio6qf64n6t65a7inkz2pa6jq4tyqwfjfhy`
  (CIDv1; contains `_app/`, `index.html`, a `_redirects` SPA-fallback, assets),
  recursively pinned locally; CAR exported.
- kotoba reuses the same Kubo IPFS layer (`KOTOBA_IPFS_ENDPOINT`) as the pin
  substrate, but is a Datalog DB, not a web host; static publish is plain
  `ipfs add` + pin (kept by kotoba / ipfs-pinner).

Full runbook + capability matrix:
`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/IPFS-DEPLOY.md`.

# Consequences

- The fix is committed at source level (`+page.svelte` → `<VibesPanel/>`, island
  deleted). **Production still shows black until rebuilt + redeployed** — the
  served artifacts under `static/_app` are the old recursive build. Deploy is
  **blocked on credentials**, not code:
  - Cloudflare path: `wrangler` present but the token is the blocker; deploy not
    run by the assistant (CF token via 1Password `op` read hit `authorization
    timeout` under non-interactive Touch-ID; the documented deploy is
    `wrangler deploy` from `appview/yoro-ui-g00h5zto/` + `purge-cache.mjs`).
  - IPFS path: **no live write endpoint**. `ipfs.etzhayyim.com` /
    `ipfs-origin.etzhayyim.com` do not resolve (DNS absent → write front
    unbuilt). `the legacy IPFS gateway zone (pre-ADR-2605212340 cutover; canonical is ipfs.etzhayyim.com)` is a working **read-only** gateway (`/api/v0/*` →
    405). The Vultr VKE Kubo backend is unreachable: the kubeconfig's admin
    client cert is rejected (401) and the API-server cert SAN omits the VKE
    FQDN. The HMAC write key exists in Keychain (`etzhayyim.cloudflare/IPFS_HMAC`)
    but has no live front to authenticate against.
- "Fully Cloudflare-free" requires, beyond the frontend: (a) PDS / AppView /
  XRPC migration off `atproto.etzhayyim.com` (CF Worker + Hyperdrive +
  RisingWave) onto kotoba (ADR-2605262130, in progress); (b) PDS **CORS** to
  allow the IPFS origin; (c) DNS move or `ipfs://`/IPNS; (d) bots-only
  SEO/OGP/sitemap renderer or prerender-in-CID. Until then the realistic state
  is **IPFS frontend + CF/kotoba backend** (a hybrid).
- New invariant captured in IPFS-DEPLOY.md: ship `static/_redirects`
  (`/* /index.html 200`) so subdomain/DNSLink gateways do SPA fallback; CAR
  should drop `bpmn-files/` (3287 files) — the full export is ~76.7 MB.
- Process note: this session ran in a repo with concurrent agents actively
  switching branches/commits; the yoro fix landed in-tree (HEAD) but rode along
  with unrelated commits, and the working branch moved (kami-genesis →
  social-security-for-humanity). Build artifacts under `static/_app` and the
  76 MB `yoro-site.car` are intentionally NOT committed (regenerable; deploy is
  pending); the CAR was removed.

# Alternatives Considered

- **Keep `<App/>` and break the self-match in `spa/router.ts`** (exclude the
  root `+page.svelte` from the glob). Rejected: it preserves a parallel
  client-router that duplicates SvelteKit routing and contradicts the
  documented Route-First Architecture; the island has no other consumer.
- **Add an SSR/`<noscript>` fallback so a hydration crash isn't a black
  screen.** Worth doing as defense-in-depth but does not fix the actual bug;
  the root render must not recurse regardless. Deferred as a follow-up
  (`ssr:false` CSR shells have no crash guard).
- **Pin via `50-infra/ipfs-pinner`.** Rejected for now: it is a substrate
  MST-CAR pinner (ADR-2605171800 Stage 4) whose Pinata/web3.storage/Filecoin
  providers are throw-on-call stubs (only the Kubo provider works); it is not a
  general static-site publisher as-is.
- **Third-party pin (Pinata / web3.storage) for immediate public reach.**
  Viable and would make `the legacy IPFS gateway zone (pre-ADR-2605212340 cutover; canonical is ipfs.etzhayyim.com)/ipfs/<CID>/` resolve via DHT, but needs a
  token and adds a mild centralization dependency; left as an option.

# References

- ADR-2605262130 (kotoba storage substrate unification — IPFS cold tier, no RW)
- ADR-2604261936 (ipfs.etzhayyim.com self-hosted Kubo on Vultr + B2)
- ADR-2605171800 (LangGraph → MST → IPFS → L2-anchor pipeline; Stage 4 pinner)
- ADR-2605215000 (Murakumo-only inference SSoT)
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/IPFS-DEPLOY.md` (runbook + capability matrix)
- `60-apps/etzhayyim-project-yoro/CLAUDE.md` (Route-First Architecture: `/` = Vibes feed)
- Root CID `bafybeidl5t4ztktqmfcqrfqpio6qf64n6t65a7inkz2pa6jq4tyqwfjfhy`
