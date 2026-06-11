# kotoba-webrtc-poc — ADR-2606036400 Phase 0+2 PoC

Proves a **browser can reach a kotoba (rust libp2p) node directly over WebRTC-direct**
— no CF Worker, no signaling server, self-signed cert — on the libp2p line kotoba pins
(`libp2p 0.53.2` / `libp2p-webrtc 0.7.1-alpha` / `libp2p-core 0.41.3`).

Standalone crate (empty `[workspace]`) — **does not touch the `40-engine/kotoba` submodule
or its pinned deps.**

## Phase 0 — rust ↔ rust (self-contained)

```sh
cargo run -p kotoba-webrtc-poc            # default bin = self-test
# ⇒ ✅ PHASE 0 PASS — ConnectionEstablished over /webrtc-direct/certhash/...
```

Finding: the libp2p-webrtc transport can only *dial* from a node that itself has an
**active webrtc-direct listener** (else `"no active listeners, can not dial"`).

## Phase 2 — real browser → rust node (verified 2026-06-03, headless Chrome 148)

1. Start the long-lived listener (prints `DIAL_ADDR_LOOPBACK=...`):
   ```sh
   KOTOBA_POC_PORT=49999 cargo run -p kotoba-webrtc-poc --bin listener
   ```
2. Serve the browser dialer:
   ```sh
   ( cd browser && python3 -m http.server 8088 )
   ```
3. Open `http://localhost:8088/?addr=<DIAL_ADDR_LOOPBACK>` in a WebRTC-capable browser.
   ⇒ page logs `✅ CONNECTED to <listener PeerId>`; the listener logs `CONNECTED_FROM=<browser PeerId>`.

js-libp2p (esm.sh): `libp2p@2` + `@libp2p/webrtc@5` (`webRTCDirect()`) +
`@chainsafe/libp2p-noise@16` + `@multiformats/multiaddr@12`. `webRTCDirect()` needs
`connectionEncrypters: [noise()]` and **no** `streamMuxers`. The rust `webrtc-dtls`
`Unsupported Extension Type 51/43/45` warnings (Chrome TLS-1.3 ClientHello extensions) are
benign — the handshake completes.

## Not yet (per ADR phases 1/3)

- Wiring WebRTC-direct into `kotoba-net` proper (multi-listen + certhash advertise) — Phase 1.
- js-libp2p ↔ kotoba **protocol** parity (bitswap/gossip wire) — Phase 2 remainder.
- `/kotoba/mcp/1.0.0` request-response + CACAO-in-frame auth — Phase 3.
