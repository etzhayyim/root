---
id: adr-2605231900-karute-deployment-topology
title: "ADR-2605231900: karute deployment topology — DID Worker + LangServer Pod + CF Pages"
status: proposed
doc_type: adr
topic: karute-deployment-topology
authoritative: true
last_verified: 2026-05-23
priority: 6.5
axis: infrastructure
weight: 0.65
priority_note: "Operationalizes ADR-2605231100 (karute EMR Phase 1) + ADR-2605231400/1603/1700 by specifying the concrete pod / Worker / DNS / tunnel layout. Includes the audit.etzhayyim.com DID Worker that every actor (not just karute) targets per ADR-2605231700."
authoritative_for:
  - "karute deployment topology (DID Worker + LangServer Pod + Pages)"
  - "audit.etzhayyim.com DID Worker"
  - "lg-karute k3s Pod manifest contract"
  - "karute static bundle hosting (CF Pages)"
  - "DNS + CF Tunnel wiring for karute.etzhayyim.com + karu7t3e.etzhayyim.com"
depends_on:
  - adr-2605231100-karute-emr-phase1
  - adr-2605231400-karute-consent-capability-iryo-bridge
  - adr-2605231603-per-record-rekey-tombstone-protocol
  - adr-2605231700-audit-webhook-subsystem
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605180900-unispsc-isic-langserver-actor-lexicon-xrpc-mcp
related:
  - adr-2605172000-etzhayyim-kotoba-substrate
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
  - adr-2605232100-etzhayyim-organism-vertical-implementation
supersedes: []
superseded_by: []
---

# ADR-2605231900: karute deployment topology

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

# Context

ADR-2605231100 specified the karute actor (lexicons + UI + actor manifest + ADRs) but left "how do we actually run this" implicit. The repo has multiple precedents (lg-uhl-right-neural Pod, etzhayyim-did-web Worker, atproto-pds Pod) but no canonical write-up for a karute-shaped actor: a PHI-handling clinical app with a SuperApp UI, an XRPC pipeline graph, an audit emission requirement, and a vendor-bridge dependency.

Two specific gaps:

1. **karute.etzhayyim.com routing**: the DID resolution path (`/.well-known/did.json`), the XRPC path (`/xrpc/*`), and the SuperApp static path (`/`) all share one origin but have three different upstreams (DID literal, LangServer Pod, CF Pages). The etzhayyim-did-web pattern handles the apex domain; karute needs its own Worker for the subdomain.
2. **audit.etzhayyim.com**: ADR-2605231700 introduced `did:web:audit.etzhayyim.com` as the canonical audit target for every actor's emission step but did not provision the DID Worker. Without this Worker the actor manifests' `agent.invoke targetDid: did:web:audit.etzhayyim.com` steps fail closed (denied audit emission = constitutional violation).

Plus a third operational concern: keeping the LangServer Pod's substrate seam alive (sidecar + IPFS pin + L2 anchor) follows ADR-2605171800 — but karute's PHI requirement raises the bar (every payload MUST be sealed before MST projection, per ADR-2605181100).

# Decision

## Topology overview

```
                                ┌────────────────────────────────────────┐
                                │ Cloudflare Pages: karute-pages.pages.dev│
                                │ (Svelte static bundle, dist/)           │
                                └────────────────────────────────────────┘
                                          ▲
                                          │ /, /assets/*
                                          │
                                          │
  did:web:karute.etzhayyim.com            │
                                 ┌────────┴─────────────────────────────┐
                                 │ CF Worker: karute-did-web            │
                                 │ Routes: karute.etzhayyim.com/*       │
                                 │                                      │
                                 │   /.well-known/did.json → did.json   │
                                 │   /xrpc/*               → XRPC up    │
                                 │   /*                    → Pages up   │
                                 │   /healthz              → local      │
                                 └────────┬─────────────────────────────┘
                                          │ XRPC_KARUTE_UPSTREAM
                                          │
                                          ▼
                              karu7t3e.etzhayyim.com (CF Tunnel)
                                          │
                                          ▼
                          ┌───────────────────────────────────┐
                          │ k3s Service: lg-karute :8080      │
                          │ (mitama-udf namespace)            │
                          │                                   │
                          │  ┌─────────────┐ ┌─────────────┐  │
                          │  │ server (Py) │↔│ checkpointer│  │
                          │  │ langgraph   │ │ TS sidecar  │  │
                          │  │ karute-graph│ │ @etzhayyim/ │  │
                          │  │             │ │  sdk        │  │
                          │  └─────────────┘ └─────────────┘  │
                          │             │                     │
                          │             ▼                     │
                          │       /var/etzhayyim/             │
                          │       checkpointer-state          │
                          │       (PVC 16Gi Retain)           │
                          └───────────────┬───────────────────┘
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            │                             │                             │
            ▼                             ▼                             ▼
   AT MST (atproto-pds)         IPFS (simeon kubo)            Base L2 anchor
   public meta + envelopes      CAR pins (ciphertext)         monotonic root
```

## Component 1 — karute DID Worker (`50-infra/karute-did-web/`)

CF Worker bound to `karute.etzhayyim.com/*` zone-route. Three responsibilities:

1. **`/.well-known/did.json`** → serves `did.json` with `Content-Type: application/did+json` + 5-minute cache. The document declares two verification key formats (JWK + multibase), `AtprotoPersonalDataServer` service pointing at the XRPC origin, `LinkedDomains` to the actor-manifest, and `EtzhayyimCharterCompliance` ADR pointers.
2. **`/xrpc/*`** → reverse-proxy to `$XRPC_KARUTE_UPSTREAM` (CF Tunnel hostname for the LangServer Pod). Worker is transport-only — it never validates payloads.
3. **`/*`** → reverse-proxy to `$KARUTE_STATIC_UPSTREAM` (CF Pages project). Worker stays in front of Pages so the apex DID and XRPC paths share one routable origin without subdomain proliferation.

Additionally `/healthz` is a Worker-local liveness probe that does NOT depend on the Pod, so Cloudflare's edge can independently confirm the Worker is reachable even if the Pod is down.

Private key: macOS Keychain `service=etzhayyim, account=DID_PRIVATE_KEY_ED25519_KARUTE` + 1Password mirror `karute/did-web/key-0`. Rotation by appending a new `#key-N` then removing `#key-0` after window.

## Component 2 — audit DID Worker (`50-infra/audit-did-web/`)

Same pattern, different subject. Serves `did:web:audit.etzhayyim.com/.well-known/did.json` and exposes `/xrpc/com.etzhayyim.audit.emitAuditEvent` (forwards to `$AUDIT_AGGREGATOR_UPSTREAM`).

Critically: this Worker is **substrate-wide** (not karute-specific). Every actor manifest that emits an audit event references `did:web:audit.etzhayyim.com` as the canonical target. Provisioning it as part of the karute rollout closes the constitutional gap from ADR-2605231700 ("audit subsystem deferred until first consumer lands").

The aggregator implementation (sign + write into the subject's PDS + hash-chain the events) is intentionally left open — Phase 1 can be a CF Worker fan-out, Phase 2 a dedicated k3s pod, Phase 3 a queue-backed batcher. The Worker's role is to keep the DID + the XRPC entrypoint stable across implementations.

## Component 3 — lg-karute Pod (`50-infra/k8s/lg-karute/`)

Two-container k3s Pod following ADR-2605171800:

| Container | Image | Role |
|---|---|---|
| `server` | `ghcr.io/etzhayyim/lg-karute:main` | Python 3.11 + langgraph-cli + kotodama. Serves the `karute` graph (31-pipeline StateGraph defined at `kotodama.projects.karute.pregel:app`). Phase 1 stub: every node returns `{"status": "stub"}` — the graph topology is real, but the substrate calls (encrypt.write / graph.write / agent.chat / agent.invoke) are not yet wired. |
| `checkpointer` | `ghcr.io/etzhayyim/etzhayyim-sdk-checkpointer:main` | TS sidecar. Reads from the Unix socket at `/run/etzhayyim/checkpointer.sock`. AEAD-seals every payload with a per-cell XChaCha20-Poly1305 key (lazy-generated, persisted to PVC). MUST be enabled for karute (`ETZ_CHECKPOINTER_ENCRYPT_CELLS=did:web:karute.etzhayyim.com`). |

Resource profile (initial):
- `server`: 200m CPU / 512Mi mem requested, 2 CPU / 2Gi mem limit
- `checkpointer`: 100m CPU / 256Mi mem requested, 1 CPU / 1Gi mem limit
- PVC: 16Gi `ReadWriteOnce` with Retain reclaim policy (PHI envelope queue tends to be busier than uhl-right-neural's 8Gi; sized for ~1y at conservative cadence)

Namespace: `mitama-udf` (shared with other lg-* pods).

Image pull secret `ghcr-pull` (configured per-cluster).

## Component 4 — CF Tunnel (`karu7t3e.etzhayyim.com`)

`cloudflared tunnel run lg-karute` exposes the in-cluster `lg-karute.mitama-udf.svc.cluster.local:8080` Service as the public hostname `karu7t3e.etzhayyim.com`. The DID Worker's `XRPC_KARUTE_UPSTREAM` var points here.

Why a tunnel rather than ingress-nginx:
- The Mac mini fleet is behind a residential NAT (192.168.1.x); no static public IP.
- CF Tunnel terminates TLS at Cloudflare's edge and provides DDoS protection + WAF for free.
- The same tunnel architecture is used for other Mac mini-hosted services (per ADR-2605191346).

## Component 5 — Cloudflare Pages (`karute-pages.pages.dev`)

`wrangler pages deploy dist` from `60-apps/.../svelte/`. Pages hosts the static bundle (~6MB unzipped, ~2.4MB gzipped — dominated by `@signalapp/libsignal-client`). The DID Worker proxies `karute.etzhayyim.com/` to this Pages project so the user-facing URL is the same as the DID.

## DNS records (one-time)

```
karute    AAAA  100::         Proxied  (CF Worker route)
audit     AAAA  100::         Proxied  (CF Worker route)
karu7t3e  CNAME  <tunnel-id>.cfargotunnel.com  Proxied  (CF Tunnel)
```

## End-to-end deploy script

`50-infra/karute-deploy.sh` orchestrates all six stages (DID Worker × 2 / Pod / Tunnel / Pages / smoke) with `--only <stage>` and `--dry-run` flags. Each stage is idempotent.

# Consequences

## 正の効果

- **Single resolvable origin** (`karute.etzhayyim.com`) for DID + UI + XRPC. Patients and clinicians only need to know one hostname.
- **Worker-local healthz** decouples DNS / DID liveness from the Pod's status — debuggable in isolation.
- **PHI sealing is enforced at the sidecar boundary**, not at app code. Even a misbehaving Pregel cell cannot write plaintext to MST because the sidecar refuses payloads from non-allowlisted DIDs.
- **Audit Worker provisioning** closes the constitutional gap from ADR-2605231700 — every actor's emission step now has a real target.
- **Stub-mode Pregel** lets the graph topology be validated by `langgraph dev` before any substrate seam is live, enabling fast iteration.

## 負の効果 / コスト

- **Phase 1 ships in stub mode**: encrypted.write / graph.write / agent.chat / agent.invoke nodes return `{"status": "stub"}`. Real substrate calls require the `@etzhayyim/sdk` checkpointer sidecar to be live AND the Pregel module to import the SDK seam. Both are present; the wiring step is Phase 2.
- **CF Tunnel single point of failure**: if the tunnel process dies, XRPC is unreachable until restart. Mitigation: systemd unit on the fleet leader + auto-restart; for HA, deploy two tunnel processes on different nodes.
- **Mac mini PVC vs cloud-managed PVC**: the Retain reclaim policy depends on a cluster default StorageClass that honors it. On local-path provisioner (k3s default), Retain works — but on some cloud SCs the default is Delete; cluster operator must verify.
- **Image pull secret per cluster**: `ghcr-pull` is namespace-scoped to `mitama-udf` — moving the Pod to a new namespace requires re-creating the secret.
- **DID rotation downtime**: removing `#key-0` after adding `#key-N` involves a redeploy; sign-in flows that cache the old key see a brief lookup miss.
- **CF Pages bundle does not auto-rebuild**: every Svelte change requires `wrangler pages deploy`. Future ADR: GitHub Actions CI hook on `60-apps/etzhayyim-project-karute/**`.

## Rollout

1. **This commit** — DID Workers (karute + audit) + lg-karute manifest + Pregel stub + deploy script + ADR. No real deployment performed.
2. **Phase 2** — Generate Ed25519 keypairs (Keychain + 1Password). `wrangler deploy` both Workers. Image build + push. `kubectl apply`. CF Tunnel. `wrangler pages deploy`. End-to-end smoke.
3. **Phase 3** — Wire the Pregel stub to real SDK calls (encrypt.write → `@etzhayyim/sdk.encryptedWrite`, agent.invoke → cross-actor XRPC fetch). Convert the stub graph nodes one pipeline at a time.
4. **Phase 4** — Audit aggregator implementation (the body behind `did:web:audit.etzhayyim.com/xrpc/emitAuditEvent`).
5. **Phase 5** — Fleet placement: add karute cells to `50-infra/murakumo/fleet.toml` for redundancy across Mac mini nodes (per ADR-2605232100 DaemonSet pattern).

# Alternatives Considered

## A. Subdomain-per-purpose (karute-did / karute-app / karute-xrpc)

Use three different subdomains. Rejected because (i) `did:web` resolution requires the DID to live at the same origin as the document, (ii) every additional subdomain is a DNS record + CF Worker route to maintain, (iii) the patient/clinician UX of "one hostname" is preferable.

## B. ingress-nginx instead of CF Tunnel

Use `ingress-nginx-dispatcher` (existing) for `karu7t3e.etzhayyim.com`. Rejected for Phase 1 because the Mac mini fleet has no static public IP. CF Tunnel is the right tool for residential-NAT clusters. Phase 2 cloud cluster (if/when) can switch to ingress.

## C. Single combined DID + audit Worker

Have one Worker handle both `karute.etzhayyim.com` and `audit.etzhayyim.com`. Rejected because (i) routing complexity multiplies, (ii) constitutional separation — audit is substrate-wide; karute is one consumer; conflating them couples lifecycles in confusing ways, (iii) blast radius — a karute Worker bug shouldn't take audit offline.

## D. Pages-only (no DID Worker)

Host everything as CF Pages with Functions for `/.well-known/did.json`. Rejected because Pages Functions have route-binding constraints that make zone-level routing awkward; Workers route on `zone_name = "etzhayyim.com"` cleanly.

## E. Direct k3s ingress (skip CF entirely)

Expose the Pod via LoadBalancer + DNS. Rejected because (i) no static public IP on the fleet, (ii) loses CF's DDoS + WAF for free, (iii) PHI traffic should be CF-terminated (Apex Trust Services SOC 2 controls).

# References

- ADR-2605231100 [karute EMR Phase 1](./2605231100-karute-emr-phase1.md)
- ADR-2605231400 [karute consent capability + iryo billing bridge](./2605231400-karute-consent-capability-iryo-bridge.md)
- ADR-2605231603 [per-record rekey + tombstone protocol](./2605231603-per-record-rekey-tombstone-protocol.md)
- ADR-2605231700 [audit webhook subsystem](./2605231700-audit-webhook-subsystem.md)
- ADR-2605171800 [LangGraph → MstCheckpointSaver → MST → IPFS → L2 anchor](/90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md)
- ADR-2605181100 [encrypted records + Signal keywrap](./2605181100-mst-encrypted-records-signal-keywrap.md)
- ADR-2605191346 [religious-corp cells HA stateful](/90-docs/adr/2605191346-etzhayyim-vultr-free-murakumo-control-plane.md)
- ADR-2605232100 [religious-corp cells k3s DaemonSet](/90-docs/adr/2605232100-etzhayyim-organism-vertical-implementation.md)
- Cloudflare Workers — https://developers.cloudflare.com/workers/
- Cloudflare Tunnel — https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- Cloudflare Pages — https://developers.cloudflare.com/pages/
- W3C did:web — https://w3c-ccg.github.io/did-method-web/
