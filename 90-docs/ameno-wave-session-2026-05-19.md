---
id: ameno-wave-session-2026-05-19
title: Ameno wave — session chronicle 2026-05-19
status: active
doc_type: explanation
topic: ameno-deployment
authoritative: false
last_verified: 2026-05-19
related:
  - ameno-end-to-end-runbook
V05190824-ameno-mediapipe-llm-browser-runtime
V05191000-ameno-browser-pregel-reflection
V05191648-substrate-boundary-lefthook
---

# Ameno wave — session chronicle 2026-05-19

One-session record of the ameno feature wave. This is **non-decisional
documentation** — every architectural choice is in its own ADR; this
file just chronicles what was built, in what order, and what carryover
remains. Useful for posterity / onboarding / honest retro.

## What landed

**19 ADRs added** in this session(JST 09:00 – 22:00, 約 13 時間):

| ADR | title | status |
|---|---|---|
| 2605190824 | Ameno MediaPipe LLM Inference Web — third browser kernel | proposed |
| 2605191000 | Ameno browser-side Pregel (LangGraph) with reflection loop | proposed |
| 2605191113 | Active inference Tier A — lexical surprise + predict-next | proposed |
| 2605191120 | Active inference Tier C — MiniLM embedding surprise | proposed |
| 2605191129 | Browser-local tool use — ReAct over JSON-tagged calls | proposed |
| 2605191135 | Ameno as Tier-2 daemon residency (tab-resident) | proposed |
| 2605191206 | Long-term encrypted memory vault — IndexedDB + AES-GCM + MiniLM index | proposed |
| 2605191229 | Ameno headless daemon Path A — Bun + Hono + LangGraph + Ollama | proposed |
| 2605191257 | Ameno headless daemon Path B — kotodama Python port | proposed |
| 2605191346 | etzhayyim is Vultr-free — Murakumo Mac-mini control plane | proposed |
| 2605191407 | Ameno browser viewer mode — svelte appview as thin client over daemon SSE | proposed |
| 2605191524 | Ameno multi-tab swarm via BroadcastChannel | proposed |
| 2605191559 | Ameno → MstCheckpointSaver Stage 2 activation | proposed |
| 2605191603 | Swarm deterministic leader election + auto-respond gating | proposed |
| 2605191608 | Ameno Stage 3 IPFS pin activation | proposed |
| 2605191625 | Ameno Stage 4 Base L2 anchor CronJob | proposed |
| 2605191638 | Substrate-level swarm lease lex (`com.etzhayyim.swarm.lease`) | proposed |
| 2605191641 | DID auth allowlist (`AMENO_ALLOWED_DIDS`) | proposed |
| 2605191645 | Browser ↔ daemon checkpoint sync v0.1 (pull-from-daemon) | proposed |
| 2605191648 | Substrate-boundary enforcement via lefthook + CI | proposed |
| 2605191657 | did:key Ed25519 daemon auth | proposed |

(2605190824 / 191000 landed via PRs #58 just before the session;
included here for narrative completeness.)

## PRs merged

| PR | branch | what |
|---|---|---|
| #58 | ameno-mediapipe-runtime | MediaPipe + browser Pregel (pre-session) |
| #62 | ameno-daemon-wave | core wave: 17 ADRs + Path A/B daemons + K3s manifests + runbook |
| #64 | ameno-did-allowlist | `AMENO_ALLOWED_DIDS` whitelist |
| #66 | lefthook-substrate-boundary | lefthook pre-commit hook |
| #68 | ci-substrate-boundary-backstop | CI backstop for the boundary hook |

5 PRs, all `lint-and-test` SUCCESS, all merged to `main` clean.

## What's in `main` after this session

```
60-apps/etzhayyim-project-ameno/
├── appview/.../svelte/src/
│   ├── App.svelte
│   └── lib/
│       ├── daemon.ts            ← DID + uptime
│       ├── did-auth.ts          ← did:key Ed25519 sign
│       ├── embedding.ts         ← MiniLM (lazy)
│       ├── graph.ts             ← StateGraph (7 nodes)
│       ├── inference.ts         ← @etzhayyim/ameno re-export
│       ├── local-checkpointer.ts← localStorage persistence
│       ├── memory-vault.ts      ← IndexedDB + AES-GCM
│       ├── mediapipe-runtime.ts ← Gemma 4 web.task
│       ├── swarm.ts             ← BroadcastChannel + leader
│       ├── tools.ts             ← ReAct registry
│       └── viewer-mode.ts       ← SSE client + auth
└── daemon/                       ← Path A (Bun, port 12480)
    ├── src/
    │   ├── server.ts
    │   ├── graph.ts
    │   ├── did-auth.ts
    │   ├── file-checkpointer.ts
    │   └── ...
    └── com.etzhayyim.ameno-daemon.plist

40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/projects/ameno/  ← Path B (Python, port 12481)
├── pregel.py                     ← StateGraph + MstCheckpointSaver auto-attach
├── server.py                     ← FastAPI + SSE + auth middleware
├── did_auth.py
├── file_checkpointer.py
├── ollama_stream.py
├── tools.py
└── ameno-daemon.service          ← systemd

50-infra/k8s/
├── ameno-ingress/                ← Cloudflare Tunnel + bearer/DID auth
├── lg-ameno/                     ← K3s 2-container Pod + PVC + Service
├── lima-k3s/                     ← 3-node HA dry-run scaffolding
└── ollama-fleet/                 ← DaemonSet per murakumo-host
50-infra/anchor-cron/k8s/
└── cronjob-ameno.yaml            ← Stage 4 anchor

00-contracts/lexicons/com/etzhayyim/apps/ameno/
└── swarmLease.json               ← cross-device coordination shape

70-tools/scripts/lint/
└── substrate-boundary.mjs        ← ADR-2605172000/172100 enforcement

90-docs/
├── ameno-end-to-end-runbook.md   ← 8-layer deployment walkthrough
└── adr/2605191*-*.md             ← 19 new ADRs
```

## Implementation depth per ADR

| ADR | code merged | tested | infra-gated |
|---|---|---|---|
| 2605191113 lexical surprise | ✅ | local | — |
| 2605191120 MiniLM Tier C | ✅ | local | — |
| 2605191129 ReAct tools | ✅ | local | — |
| 2605191135 daemon residency | ✅ | local | — |
| 2605191206 memory vault | ✅ | local | — |
| 2605191229 Path A daemon | ✅ | local + smoke | — |
| 2605191257 Path B daemon | ✅ | local + import smoke | — |
| 2605191346 Vultr-free | design | — | M1-M7 schedule(2026-06-15 → 09-15) |
| 2605191407 viewer mode | ✅ | local | — |
| 2605191524 swarm presence | ✅ | local 2-tab | — |
| 2605191559 MST Stage 2 | ✅ | env-gated | sidecar reachable |
| 2605191603 swarm leader | ✅ | local 2-tab | — |
| 2605191608 Stage 3 IPFS | manifest | — | kubo node access |
| 2605191625 Stage 4 L2 anchor | manifest | — | EtzhayyimAnchor deploy |
| 2605191638 substrate lease lex | schema only | — | sdk write impl |
| 2605191641 DID allowlist | ✅ | local 4-case | — |
| 2605191645 pull sync v0.1 | ✅ | local | — |
| 2605191648 substrate-boundary hook | ✅ | self-check + violation case | — |
| 2605191657 did:key auth | ✅ | local 2-language | — |

8 ADRs are infra/deployment-gated, not code-gated. They sit waiting for:
- Lima K3s bring-up (M1 deadline 2026-06-15)
- kubo node reachability from `etzhayyim-langserver` namespace
- `EtzhayyimAnchor` testnet contract deploy

## Carryover follow-ups (documented but not implemented)

1. **substrate swarm lease implementation** — lex is committed; MST
   write + takeover algorithm is a separate PR
2. **bi-directional checkpoint sync** — v0.1 is pull-only; push +
   conflict resolution + LWW is a follow-up ADR
3. **HTTP Message Signatures (RFC 9421)** — current DIDSig signs just
   the nonce; full RFC 9421 body-and-headers signing is v0.2
4. **Signal Protocol DID binding** — `com.etzhayyim.identity.signalIdentity`
   integration with did:key
5. **anchor-cron monitoring** — alerting / metrics for Stage 4
6. **native macOS Ollama ansible** — alternative to ollama-fleet
   DaemonSet for non-K8s ops
7. **browser CryptoKey HSM** — replace localStorage JWK with
   `extractable: false` CryptoKey
8. **memory vault inspector UI** — list / delete stored memories from
   the appview
9. **CF exit ADR** — long-term self-host of all edge functions
10. **end-to-end automated smoke test** — single `pnpm smoke` that
    walks the runbook

## Substrate boundary status

After 5 PRs, the ADR-2605172000 / 172100 invariants are enforced at
two layers:

- **lefthook pre-commit**: fast local feedback
- **CI lint-and-test step**: backstop for PRs (caught even when
  contributors bypass lefthook)

Branch protection on `main` can promote CI to a required check,
making the boundary structurally unbreakable. (Not in this session;
GitHub repo settings change.)

## Stats

- ADRs added: 19 (this session) + 3 inherited at session start = 22
- PRs merged: 5 (this session; 3 more by parallel actors during the
  session: #61, #63, #65, #67)
- Lines added (estimated): ~12,000 (10,498 from PR #62 alone +
  ~200/PR for the four follow-ups)
- Languages touched: TypeScript, Python, YAML, JSON, JSON-LD,
  Solidity (referenced), Bash
- New npm deps: `@noble/curves`, `@noble/hashes`, `@scure/base`
- New Python deps: `cryptography` (lazy)
- Branches consumed: `ameno-daemon-wave`, `ameno-did-allowlist`,
  `lefthook-substrate-boundary`, `ci-substrate-boundary-backstop`
  (all auto-deleted on merge)

## Honest limits

- **Nothing was deployed to actual hardware** in this session. K3s
  dry-run is scaffolded but un-executed; Mac-mini fleet is referenced
  but untouched.
- **No formal `proposed → accepted` status promotions** — all 19 ADRs
  remain `proposed`. Production rollout (M1+) will promote them
  individually.
- **Path A and Path B daemons share no DID rotation strategy**; each
  reads its own `~/.ameno/worker-did` independently. Cross-daemon
  identity unification is not designed.
- **Browser `did-auth` keypair lives in localStorage** (extractable).
  HSM-backed CryptoKey is a follow-up.

## License

Apache-2.0.
