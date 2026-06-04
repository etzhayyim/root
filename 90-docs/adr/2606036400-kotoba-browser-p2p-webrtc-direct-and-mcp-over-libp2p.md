---
id: adr-2606036400-kotoba-browser-p2p-webrtc-direct-and-mcp-over-libp2p
title: "ADR-2606036400: kotoba Browser-Reachable P2P (WebRTC-direct) + MCP-over-libp2p"
status: proposed
doc_type: adr
topic: kotoba-browser-p2p-webrtc-direct-and-mcp-over-libp2p
authoritative: true
last_verified: 2026-06-03
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Closes the browser↔kotoba gap: kotoba speaks only libp2p-QUIC (UDP), unreachable from browsers, so every browser path today depends on a CF Worker HTTP edge. Adds a browser-dialable transport + an MCP request-response protocol so browsers reach a kotoba node P2P with no Worker."
authoritative_for:
  - kotoba-browser-transport
  - kotoba-mcp-over-libp2p
  - kotoba-worker-independent-reachability
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-no-server-key-religious-corp-architecture
related:
  - adr-2606015400-mesh-runner-serving-and-ipfs-did-retrieval
  - adr-2606015600-self-certifying-did-attestation
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
supersedes: []
superseded_by: []
---

# ADR-2606036400: kotoba Browser-Reachable P2P (WebRTC-direct) + MCP-over-libp2p

**Status**: proposed
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

A live-debug session (2026-06-03) established two facts on the deployed stack:

1. **`mcp.etzhayyim.com` is down (502)** with body
   `Service binding fetch failed (MCP → mcp.gftd.ai): this worker has been deleted via a force-delete`.
   The CF Worker `etzhayyim-xrpc-proxy` (`50-infra/etzhayyim-xrpc-proxy/wrangler.toml`)
   binds `MCP` → service `ai-gftd-agentgateway` (route `mcp.gftd.ai`), which has been
   force-deleted. The same dead router breaks passkey login
   (`authn.etzhayyim.com` → `ai.gftd.auth.passkeyBeginAuth` → 502/522).

2. The MCP *logic* is **not** in the Worker. kotoba-server serves a full MCP JSON-RPC 2.0
   facade in native Rust (`40-engine/kotoba/crates/kotoba-server/src/mcp.rs`, ADR-2605091400):
   `POST /mcp`, `protocolVersion 2024-11-05`, `initialize`/`ping`/`tools/list`/`tools/call`,
   18 tools, `tools/call` gated by `Authorization: Bearer <AT-session-JWT>`. It is served by
   axum over TCP (`lib.rs:1506` `TcpListener::bind` + `axum::serve`), and in parallel the node
   runs a libp2p swarm (`lib.rs:1348` `KOTOBA_P2P_PORT` → `KotobaSwarm`).

The deeper question this ADR answers: **can browser↔kotoba be made Worker-independent
using kotoba's own protocol / DHT, and is kotoba wired to QUIC / WebTransport?**

Verified state of `crates/kotoba-net/` (libp2p `0.53`, features
`quic, noise, yamux, gossipsub, kad, identify, ping, macros, request-response`):

- **Transport = QUIC (`quic-v1`, UDP) only.** `transport.rs:4` default
  `/ip4/0.0.0.0/udp/0/quic-v1`; `swarm.rs:97` `.with_quic()`. No TCP, **no WebSocket,
  no WebTransport, no WebRTC** (grep-confirmed empty).
- **behaviour** (`behaviour.rs`): `gossipsub + kademlia(DHT) + identify + ping +
  bitswap(request_response)`. No relay / dcutr / autonat.
- The P2P wire carries **blocks (bitswap, incl. `WantSince` delta sync), gossip
  (KSE topics / Pregel / firehose), DHT** — it does **not** carry MCP JSON-RPC.
- Browser side: `kotoba-store-web` is an **IndexedDB cache only** ("does not run Pregel");
  there is **no `kotoba-runtime-web` crate**; `wasmtime` is native-only. The deployed
  `/projects` page therefore uses an in-browser kotoba-wasm *read* SW that is **network-first
  to a same-origin HTTP endpoint** — i.e. it still depends on an HTTP edge (the Worker).

Consequence: **a browser cannot open a raw libp2p-QUIC (UDP) connection.** Every browser
path to kotoba today must traverse an HTTP edge, which is why a force-deleted Worker can
take down both MCP and login. node↔node is already Worker-independent (QUIC + Kademlia +
bitswap); **browser↔node is not.**

# Decision

Add a **browser-dialable libp2p transport** to kotoba-net and an **MCP request-response
protocol over libp2p**, so a browser reaches a publicly-reachable kotoba node directly with
**no CF Worker in the path**. Four workstreams:

## 1. Transport — adopt **WebRTC-direct** (`/webrtc-direct`)

Browser→server transport candidates and verdict:

| candidate | browser→node direct | CA / domain TLS | signaling server | rust 0.53 server maturity | verdict |
|---|---|---|---|---|---|
| **WebRTC-direct** | yes | none (self-signed DTLS + `certhash` in multiaddr) | **none** (direct) | `libp2p-webrtc` tokio server | **chosen** |
| WebTransport | yes | self-signed ok but cert ≤14d rotation + HTTP/3 listener | none | rust **server weak** (`websys` is browser-side) | Phase 2 |
| WebSocket (wss) | yes | **CA cert + domain required** → reintroduces an HTTPS edge | none | server feature not enabled | rejected (defeats the goal) |

WebRTC-direct is the only path that is browser-dialable **and** CA-free **and**
signaling-free for the publicly-reachable-server case. Self-signed DTLS cert; `certhash`
embedded in the multiaddr; PeerId (Ed25519) authenticates the node — which already aligns
with kotoba's Ed25519 node identity and the actor `did:key` cross-link
(ADR-2606015600). WebTransport stays Phase 2 pending a libp2p bump with a production
WebTransport server.

kotoba-net changes: add `libp2p-webrtc` (tokio) dep; generate/persist a self-signed cert
and expose its `certhash`; in `swarm.rs` build the WebRTC-direct transport via
`SwarmBuilder::…with_other_transport(...)` and **listen on both QUIC and WebRTC-direct**
(generalise the single `listen_addr` to `listen_addrs: Vec<Multiaddr>`); `transport.rs`
gains `webrtc_direct_addr(port)`. `KotobaBehaviour` is unchanged (transport-layer only).

## 2. Discovery — Worker-free, dynamic (cert/multiaddr churn)

The browser must learn `…/webrtc-direct/certhash/<mb>/p2p/<PeerId>`, which changes on cert
rotation. Two Worker-free channels (use both):

- **`dnsaddr`** (primary): Cloudflare **DNS** TXT
  `_dnsaddr.<node>.etzhayyim.com = dnsaddr=/ip4/…/udp/…/webrtc-direct/certhash/…/p2p/…`.
  DNS is not a Worker; js-libp2p resolves `dnsaddr`. Short TTL absorbs rotation.
- **content-addressed actor record** (reuse existing): actor `did.json` is already published
  content-addressed to IPFS (ADR-2606015400/15600). Add a `p2p` multiaddr array; the browser
  fetches it from **any public IPFS gateway** (not the etzhayyim Worker), converging with the
  in-browser `kotoba-sw` gateway-fetch path.

## 3. Browser client — **js-libp2p** (not kotoba-wasm)

Because `kotoba-store-web` is cache-only, there is no `kotoba-runtime-web`, and `wasmtime`
is native-only, the browser P2P client is **js-libp2p** configured with
`webrtc-direct + noise + yamux`. It must match kotoba's wire **exactly**: protocol IDs
(`KOTOBA_SYNC_PROTOCOL` for identify, `BITSWAP_PROTOCOL` for bitswap), the
`BitswapRequest/Response/WantSince` serde shapes, and the gossipsub topic naming
(`gossipsub_topic()`). Compiling a rust kotoba node to wasm (a new `kotoba-net-web` crate
over `webtransport-websys`/`websys`) is deferred to Phase 4.

## 4. **MCP-over-libp2p** — `/kotoba/mcp/1.0.0`

To carry MCP without an HTTP edge, add a libp2p `request_response::Behaviour` protocol
`/kotoba/mcp/1.0.0` whose frames are MCP JSON-RPC (`initialize`/`tools/list`/`tools/call`).
Refactor `mcp.rs::mcp_handler` into a **transport-independent core** (today it depends on
axum `State` + `HeaderMap`) callable from both the HTTP and the libp2p entry points.

**Auth migration**: libp2p frames have no HTTP headers, so the `tools/call`
`Authorization: Bearer` gate is replaced over libp2p by a **CACAO delegation chain carried
in the request frame** (already implemented in `kotoba-auth`; DID-bound, no-server-key —
strictly *more* aligned with ADR-2605231525). The passkey→`did:key`→CACAO `tools:call`
flow becomes the native auth path. HTTP keeps Bearer for backward compatibility.

End state: **browser → WebRTC-direct → `/kotoba/mcp/1` → kotoba-server**, HTTP edge = 0.

## Immediate, separate, non-blocking fix

Independent of this ADR, the dead MCP/login can be restored **at the etzhayyim-root config
level** by re-pointing the `xrpc-proxy` `MCP` service binding from the force-deleted
`ai-gftd-agentgateway` to a live kotoba-server `/mcp` origin and redeploying. That is a
config change, not a code dependency, and also fixes the passkey 502. This ADR is the
*structural* answer (remove the edge); the binding repoint is the *operational* hotfix.

# Consequences

**Positive**
- Browsers reach a publicly-reachable kotoba node with **no CF Worker** for block read,
  gossip, and MCP — a force-deleted Worker can no longer take down MCP.
- node↔node already needs no Worker; this extends Worker-independence to the browser tier.
- Auth moves to CACAO-in-frame (DID-bound, no-server-key) — tightens, not loosens, invariants.
- PeerId(Ed25519)↔actor `did:key` binding is natural; reuses content-addressed discovery.

**Negative / honest limits**
- **NAT**: browser→server WebRTC-direct needs the node **publicly UDP-reachable**. NAT-bound
  home nodes are not directly dialable and would need `circuit-relay-v2` — which is itself a
  server. "Fully Worker-free" holds only for publicly-reachable nodes.
- **Cert/multiaddr churn**: self-signed cert rotation changes `certhash`; discovery (§2) must
  refresh on a short TTL or browsers cache a stale, undialable multiaddr.
- **js-libp2p re-implementation cost**: bitswap codec, gossipsub schema, and `WantSince` must
  be reproduced **byte-for-byte** against the rust wire; drift = silent failure.
- **libp2p 0.53 WebRTC server maturity**: may force a libp2p bump, which violates the pinned
  `= "0.53"` policy workspace-wide → must be ratified here if Phase 0 requires it.
- **Browser is DHT-client-only** (no inbound) — kademlia client mode; sufficient for read.
- New attack surface: a public WebRTC-direct + `/kotoba/mcp/1` listener is internet-facing;
  rate-limit + the existing fingerprint middleware + CACAO gate on `tools/call` are mandatory.

**Phasing**

| Phase | scope | exit criterion |
|---|---|---|
| 0 | ADR (this) + rust↔rust WebRTC-direct dial PoC | **✅ DONE 2026-06-03 — feasibility confirmed (see below)** |
| 1 | kotoba-net WebRTC-direct listener + certhash + multi-listen | node advertises a webrtc-direct addr |
| 2 | js-libp2p browser client (bitswap read + gossip) + dnsaddr discovery | **✅ transport leg DONE 2026-06-03** (real browser dials a rust node, see below); bitswap/gossip protocol parity still TODO |
| 3 | `/kotoba/mcp/1` protocol + `mcp.rs` core split + CACAO-in-frame auth | browser runs MCP `tools/call` Worker-free |
| 4 | (optional) wasm kotoba node (`kotoba-net-web`) | in-browser kotoba is itself a peer |

## Phase 0 — empirical result (2026-06-03)

PoC at `70-tools/kotoba-webrtc-poc/` (standalone crate, empty `[workspace]`, **does not
touch the kotoba submodule or its pinned deps**). Two libp2p nodes, WebRTC-direct only.

- **Dependency resolution**: `libp2p 0.53.2` + `libp2p-webrtc 0.7.1-alpha` + `libp2p-core
  0.41.3` co-resolve cleanly (415 crates) — **no libp2p bump required** for Phase 0/1.
  WebRTC-direct is built via `SwarmBuilder::…with_other_transport(|key|
  webrtc::tokio::Transport::new(key.clone(), Certificate::generate(&mut rng)?))`.
- **Result**: ✅ `ConnectionEstablished` between the two nodes over
  `/ip4/127.0.0.1/udp/<p>/webrtc-direct/certhash/<mb>/p2p/<PeerId>` — the exact multiaddr
  shape a js-libp2p browser dials. Build+run 29.5 s, self-signed cert + certhash, no CA,
  no signaling server.
- **Finding feeding Phase 1**: the libp2p-webrtc transport can only *dial* from a node that
  itself holds an **active webrtc-direct listener** (else
  `"no active listeners, can not dial without a previous listen"`). For kotoba this is moot
  on server nodes (they listen anyway) but means a **dial-only** browser/edge peer must also
  open a webrtc-direct listen socket before dialing — to be reflected in the js-libp2p client
  config and in `kotoba-net`'s multi-listen wiring.

## Phase 2 — empirical result: real browser → rust node (2026-06-03)

The decisive interop unknown (rust `libp2p-webrtc 0.7.1-alpha` ↔ js-libp2p latest) is **confirmed
working**. A long-lived rust listener (`70-tools/kotoba-webrtc-poc/src/bin/listener.rs`,
`/ip4/0.0.0.0/udp/49999/webrtc-direct`) was dialed from a **real headless Chrome 148** running a
js-libp2p page (`webRTCDirect()` + `noise()`, no Worker, no signaling server, served over a plain
static `http.server`):

- js-libp2p versions (esm.sh): `libp2p@2`, `@libp2p/webrtc@5`, `@chainsafe/libp2p-noise@16`,
  `@multiformats/multiaddr@12`.
- **Bidirectional confirmation**: browser logged `✅ CONNECTED to <listener PeerId>`; the rust
  node logged `CONNECTED_FROM=<browser PeerId>` for the same connection.
- Config note: `webRTCDirect()` needs `connectionEncrypters: [noise()]`; **no `streamMuxers`**
  (WebRTC data channels mux natively).
- Interop observation: the rust `webrtc-dtls` stack logs `Unsupported Extension Type 51/43/45`
  (TLS 1.3 `key_share`/`supported_versions`/`psk_key_exchange_modes` from Chrome's ClientHello) —
  **benign**; the DTLS handshake completes and the connection establishes regardless.

Conclusion: the **browser↔kotoba transport leg is proven on kotoba's pinned libp2p line with zero
CF Worker.** Remaining Phase 2 work is protocol parity (bitswap/gossip wire); Phase 3 is
MCP-over-libp2p — neither is a transport-feasibility risk anymore.

- **Re-point the Worker binding only** (operational hotfix): restores service fastest but
  leaves the structural single-point-of-failure (a browser still needs an HTTP edge). Adopted
  as the immediate fix, **not** as the answer to the structural question. Both ship.
- **WebTransport instead of WebRTC-direct**: reuses QUIC and is conceptually cleaner, but the
  rust WebTransport *server* is not production-ready in libp2p 0.53 and self-signed certs must
  rotate ≤14 days. Deferred to Phase 2.
- **WebSocket (wss)**: works in all browsers but requires a CA-signed cert on a domain →
  reintroduces an HTTPS edge (TLS termination), defeating the Worker-free goal.
- **Keep MCP HTTP-only, serve it directly from the kotoba node**: removes the *Worker* but not
  the *HTTP edge*; does not make the browser path P2P. Insufficient for the structural goal,
  though it is exactly the §"immediate fix" when paired with the binding repoint.
- **Compile kotoba to wasm and run a full browser peer now**: maximal, but needs a new
  `kotoba-net-web` crate over browser transports and a metered interpreter (wasmtime is
  native-only). Deferred to Phase 4.

# References

- ADR-2605091400 (MCP-as-cell-membrane / lexicon-XRPC demotion — the kotoba `POST /mcp` facade, 18 tools)
- ADR-2605262130 (kotoba storage substrate unification)
- ADR-2605215000 (Murakumo-only inference)
- ADR-2605231525 (no-server-key religious-corp architecture — CACAO auth alignment)
- ADR-2606015400 (mesh-runner serving + IPFS DID retrieval — content-addressed discovery)
- ADR-2606015600 (self-certifying DID attestation — `did:key`↔PeerId binding)
- `40-engine/kotoba/crates/kotoba-net/{transport,swarm,behaviour}.rs` (current QUIC-only swarm)
- `40-engine/kotoba/crates/kotoba-server/src/mcp.rs` (MCP handler to be split transport-independent)
- `50-infra/etzhayyim-xrpc-proxy/wrangler.toml` (dead `MCP` → `ai-gftd-agentgateway` binding)
