---
id: adr-2606041822-session-close-apex-etzhayyim-com-kotoba-query-proxy
title: "ADR-2606041822: Session close — apex etzhayyim.com kotoba query proxy + public-read posture finding"
status: active
doc_type: adr
topic: session-close-apex-etzhayyim-com-kotoba-query-proxy
authoritative: false
last_verified: 2026-06-04
priority: 4.5
axis: architecture
weight: 0.36
priority_note: "Documentation-only closure; follows the 2606041657 session close"
authoritative_for: []
depends_on:
  - "2606041657"
related:
  - "2605231525"
  - "2606036400"
  - "2606013800"
supersedes: []
superseded_by: []
---

# ADR-2606041822: Session close — apex etzhayyim.com kotoba query proxy + public-read posture

**Status**: active
**Date**: 2026-06-04
**Deciders**: Jun Kawasaki

# Context

Closure for the follow-on segment answering *「https://etzhayyim.com/ からの query
にも対応できている?」*. Continues the 2026-06-04 session (cf. ADR-2606041657).

# Decision

(Documentation only — records the finding + the shipped proxy + the rejected
global-public flip.)

## 1. Finding — public query reachability

- **apex `etzhayyim.com/xrpc/com.etzhayyim.apps.kotoba.*` → 404.** The apex
  Worker (`50-infra/etzhayyim-did-web`) already proxies `/xrpc/*` by NSID prefix,
  but the kotoba NSIDs fell through the `com.etzhayyim.` catch-all to
  `XRPC_etzhayyim_UPSTREAM` (the atproto PDS), which has no kotoba endpoints.
- **`kotoba.etzhayyim.com` (cloudflared tunnel → :8077) is reachable** (health
  200), but the query surface is **auth-gated per graph**: `graph.sparql`
  (datomic) → CACAO/Private (403 anon); `kg.query` (kotobase kg graph) →
  **Authenticated / any non-empty Bearer** (401 anon, evaluates with any bearer).
- `etzhayyim.com/projects` browser chat is a separate path (ameno
  onnxruntime-web WASM, ADR-2606036400), not a kotoba-server query.

## 2. Shipped — apex query proxy

`feat(did-web): apex xrpc proxy for the kotoba graph query surface` (committed,
on `main`): two NSID routes added **before** the `com.etzhayyim.` catch-all —
`com.etzhayyim.apps.kotoba.` / `com.etzhayyim.apps.kotobase.` →
`XRPC_KOTOBA_UPSTREAM = https://kotoba.etzhayyim.com`. Read-only proxy; the
client's CACAO / Authorization **passes through unchanged** (no server key
injected, ADR-2605231525). `tsc` clean. After `wrangler deploy`,
`etzhayyim.com/xrpc/{graph.sparql,kg.query,kg.mv.*}` reach the kotoba node.

## 3. Rejected — global public-default flip

Setting `KOTOBA_DEFAULT_VISIBILITY=public` was investigated and **reverted**:
(a) `launchctl kickstart -k` does **not** reload the plist `EnvironmentVariables`
(the env never reached the running process — `bootout`+`bootstrap` is required);
(b) more fundamentally, the kg/datomic graphs carry **registered per-graph
visibility** in `graph_registry`, which the node default would not override; and
(c) a global `public` default would expose **every unregistered graph**
anonymously — too broad. The plist change was removed; the server stays at its
private/per-graph-registered posture.

# Consequences

- **Once deployed**, querying the kotoba graph via `etzhayyim.com` works, with
  auth unchanged: `kg.query` needs any `Authorization: Bearer <token>`
  (effectively public-with-a-token); `graph.sparql` needs CACAO; anonymous
  (no header) is blocked.
- **Truly-anonymous public read** (no header) is NOT enabled and should be done,
  if wanted, by marking the specific **public actor graphs** `Public` per-graph
  (transparency mission — public KGs open, sensitive/member data stays CACAO /
  E2E-encrypted), never by a global flag.
- Deploy is operator-run (`wrangler deploy` in `50-infra/etzhayyim-did-web`);
  this session has no Cloudflare credentials.
- ZERO Charter invariant amendments (read-only proxy, no server key, consent
  boundary preserved).

# Alternatives Considered

- **Global `KOTOBA_DEFAULT_VISIBILITY=public`** — rejected (broad anonymous
  exposure of all unregistered graphs; also wouldn't override registered graphs).
- **Inject a bearer in the apex proxy** — rejected (violates the no-server-key
  invariant, ADR-2605231525; the client must carry its own credential).
- **Browser-P2P (WebRTC-direct) instead of the apex HTTP proxy** — complementary,
  tracked separately (ADR-2606036400); the apex proxy is the immediate HTTP path.

# References

- 90-docs/adr/2606041657-session-close-kotoba-durability-and-canonical-tier.md
- 50-infra/etzhayyim-did-web/src/worker.ts (XRPC_ROUTES + XRPC_KOTOBA_UPSTREAM)
- 50-infra/etzhayyim-did-web/wrangler.toml (XRPC_KOTOBA_UPSTREAM var)
- ADR-2605231525 (no-server-key), ADR-2606036400 (browser-P2P), ADR-2606013800 (actor DID/profile)
