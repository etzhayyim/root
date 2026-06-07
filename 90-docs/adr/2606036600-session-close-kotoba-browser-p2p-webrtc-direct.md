---
id: adr-2606036600-session-close-kotoba-browser-p2p-webrtc-direct
title: "ADR-2606036600: Session close — kotoba browser-P2P WebRTC-direct feasibility (ADR-2606036400 Phase 0+2)"
status: active
doc_type: adr
topic: session-close-kotoba-browser-p2p-webrtc-direct
authoritative: true
last_verified: 2026-06-03
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Documentation-only session-close. Authoritative design = ADR-2606036400. Records the live-debug findings behind the browser↔kotoba P2P question and the empirical Phase 0+2 PoC results."
authoritative_for:
  - session-close-2606036600
depends_on:
  - adr-2606036400-kotoba-browser-p2p-webrtc-direct-and-mcp-over-libp2p
related:
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605231525-no-server-key-religious-corp-architecture
supersedes: []
superseded_by: []
---

# ADR-2606036600: Session close — kotoba browser-P2P WebRTC-direct feasibility

**Status**: active
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

Session driven by a chain of questions about `etzhayyim.com/projects` and kotoba's
reachability, answered with live debugging (headless Chrome via CDP — the Claude browser
extension was unavailable the whole session, so all browser work used a locally-launched
Chrome 148 driven over the DevTools Protocol).

Authoritative design for the forward work: **ADR-2606036400**. This is the documentation-only
session-close recording what was found and shipped.

# Decision

Record findings; ship a design ADR + a feasibility PoC; defer implementation.

## Findings (empirical, 2026-06-03)

1. **`/projects` browser-local LLM**: served by the yoro SPA (apex reverse-proxies all
   non-local paths to `yoro.etzhayyim.com`). Chat inference is **ameno = onnxruntime-web
   (WASM) + WebGPU**, plus WebLLM — *not* "kotoba server compiled to WASM". The in-browser
   `kotoba-sw.js` is a **Datom read engine** (network-first to a same-origin HTTP endpoint,
   IndexedDB cache), not the chat LLM. Runtime check: WebGPU adapter available, model
   `onnx-community/embeddinggemma-300m-ONNX` fetched **from huggingface.co** (so cold-start is
   not network-free). A server fallback (`com.etzhayyim.projector.sendProjectMessage`) ships
   in the bundle, gated on `localLLM.isReady`. Could not exercise an authenticated chat turn
   (login required).

2. **Login**: `authn.etzhayyim.com/sign-in` is **passkey-only** (no username/password field;
   usernameless/discoverable; platform authenticator + conditional-mediation available) — but
   currently **502** at `ai.etzhayyim.auth.passkeyBeginAuth`.

3. **MCP**: `mcp.etzhayyim.com` is **502** — `Service binding fetch failed (MCP →
   mcp.etzhayyim.com): this worker has been deleted via a force-delete`. The `etzhayyim-xrpc-proxy`
   Worker binds `MCP` → service `etzhayyim-agentgateway` (force-deleted). kotoba-server itself
   **does** implement MCP (`crates/kotoba-server/src/mcp.rs`: `POST /mcp`, JSON-RPC 2.0,
   `protocolVersion 2024-11-05`, 18 tools, `tools/call` Bearer-gated) — the logic is not in
   the Worker. Same dead router breaks both MCP and passkey login.

4. **Transport / Worker-independence**: kotoba-net is **libp2p QUIC-only** (no WebTransport /
   WebRTC / WebSocket). node↔node is already Worker-free (QUIC + Kademlia DHT + bitswap), but
   **browsers cannot dial QUIC**, so every browser path needs an HTTP edge → the structural
   reason a force-deleted Worker takes the system down.

## Shipped this session

- **ADR-2606036400** — design: WebRTC-direct transport + dnsaddr/IPFS discovery + js-libp2p
  client + `/kotoba/mcp/1.0.0` (MCP-over-libp2p) with CACAO-in-frame auth; 5-phase plan.
- **`70-tools/kotoba-webrtc-poc/`** — standalone crate (empty `[workspace]`, **kotoba
  submodule untouched**):
  - **Phase 0 PASS** — rust↔rust WebRTC-direct `ConnectionEstablished` on libp2p 0.53.2 /
    libp2p-webrtc 0.7.1-alpha (dep graph co-resolves; **no libp2p bump needed**).
  - **Phase 2 transport leg PASS** — a **real headless Chrome 148 + js-libp2p `webRTCDirect()`**
    dialed the rust node; bidirectional `CONNECTED`, zero CF Worker, zero signaling server,
    self-signed cert.
  - `cargo test` 4 green (1 rust↔rust regression + 3 `loopback_variant` unit) · clippy clean ·
    `.gitignore`.
- Loop iterations (`/loop`, since stopped) added the regression test, the unit tests + clippy
  pass, and fixed two dangling ADR cross-reference slugs.

# Consequences

- The browser↔kotoba **transport** is proven feasible on kotoba's pinned libp2p line — the
  Worker dependency is removable for the transport tier of publicly-reachable nodes.
- **Not done** (honest): Phase 1 (WebRTC-direct in `kotoba-net` proper — submodule edit, needs
  go-ahead); Phase 2 protocol parity (bitswap/gossip wire in js-libp2p); Phase 3 MCP-over-libp2p;
  the operational hotfix (repoint `xrpc-proxy` `MCP` binding `etzhayyim-agentgateway` → live kotoba
  `/mcp`, which also fixes passkey 502); and committing the artifacts (all currently untracked).
- NAT-bound nodes still need a `circuit-relay-v2` (itself a server) — "fully Worker-free"
  holds only for publicly UDP-reachable nodes.

# Alternatives Considered

- **Operational hotfix only** (repoint the dead binding): fastest restore, but leaves the
  structural single-point-of-failure. Recommended to ship *alongside*, not instead of, 2606036400.
- **WebTransport / wss** instead of WebRTC-direct: rejected for now (rust WebTransport server
  immaturity in 0.53; wss needs a CA cert + domain = an HTTP edge). See ADR-2606036400.

# References

- ADR-2606036400 (kotoba browser-P2P WebRTC-direct + MCP-over-libp2p — authoritative design)
- ADR-2605091400 (MCP-as-cell-membrane / lexicon-XRPC demotion — kotoba `POST /mcp` facade)
- ADR-2605262130 (kotoba storage substrate unification)
- ADR-2605231525 (no-server-key religious-corp architecture — CACAO auth alignment)
- `70-tools/kotoba-webrtc-poc/` (Phase 0+2 PoC, README with reproduction steps)
- `50-infra/etzhayyim-xrpc-proxy/wrangler.toml` (dead `MCP` → `etzhayyim-agentgateway` binding)
