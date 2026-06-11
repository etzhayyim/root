---
id: adr-2606039000-kotoba-net-nat-traversal-autonat-relay-dcutr
title: "ADR-2606039000: kotoba-net NAT Traversal — AutoNAT + Circuit Relay v2 + DCUtR (clean-room WG/TS-equivalent)"
status: proposed
doc_type: adr
topic: kotoba-net-nat-traversal-autonat-relay-dcutr
authoritative: true
last_verified: 2026-06-03
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Closes the public-internet reach gap for donated/edge nodes: kotoba-net was QUIC+Noise+GossipSub+Kademlia with no NAT traversal, so a kotoba pod / e7m node behind home NAT could not join the mesh. Adds the WireGuard/Tailscale-equivalent function (reachability detection + relay fallback + hole punching) entirely over libp2p — no vendored VPN code, no central coordination server."
authoritative_for:
  - kotoba-net-nat-traversal
  - kotoba-donated-node-public-reachability
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-no-server-key-religious-corp-architecture
related:
  - adr-2606036400-kotoba-browser-p2p-webrtc-direct-and-mcp-over-libp2p
  - adr-2606012100-donation-funded-operation-and-compute-node-donation
  - adr-2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules
supersedes: []
superseded_by: []
---

# ADR-2606039000: kotoba-net NAT Traversal — AutoNAT + Circuit Relay v2 + DCUtR (clean-room WG/TS-equivalent)

**Status**: proposed
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

The question raised: *「kotoba 本体に WireGuard / Tailscale のような network は設計統合されているか? クリーンルーム設計で。」*

Audit of the kotoba submodule (`40-engine/kotoba`) found:

- `kotoba-net` is a **libp2p** stack — QUIC-v1 transport + Noise handshake + GossipSub + Kademlia DHT + Bitswap (`KotobaBehaviour`). Description string: *"Kotoba libp2p network: QUIC, Noise, GossipSub, Kademlia"*.
- **No WireGuard / Tailscale code is vendored** (no `wireguard-go` / `boringtun` / `tailscale`). The "relay" already present (`NodeRole::Relay`, `net_actor.rs`) is an *application-level* KSE-Journal firehose relay, **not** an L3 VPN relay.
- WireGuard `wg0` exists only at the **fleet underlay** (`50-infra/murakumo/fleet.toml`: `overlay_network = "WireGuard wg0 (VM-to-VM cross-host pod traffic)"`) — k3s pod networking, a layer **below** kotoba, not part of the engine.

So kotoba already provides — at L4/L7, over libp2p — the functions a WG/TS overlay provides at L3:区間暗号 (Noise vs WG's Noise_IK), node identity (libp2p `PeerId` + DID, vs TS control-plane), serverless discovery (Kademlia, vs TS DERP/coordination server). Choosing Kademlia over a Tailscale-style coordination server is also required by the **no-central-master** invariant (kotoba 禁止: 中央マスターノード) and the **no-server-key** posture (ADR-2605231525).

**The gap**: kotoba-net had **no NAT traversal**. On a LAN (Murakumo fleet under `wg0`) this is fine, but ADR-2606012100 recognises **donated/edge node classes** (`e7m` CLI node, `kotoba` pod) that live behind **home NAT** on the public internet. They could not be reached to join the mesh. A WG/TS overlay is *one* way to solve this; the clean-room, invariant-preserving way is to use libp2p's own NAT-traversal protocols (the same ones the browser-P2P work in ADR-2606036400 builds toward).

# Decision

Add the libp2p NAT-traversal triad to `kotoba-net`, **clean-room over libp2p 0.53** (no VPN code, no coordination server). A relay is just another peer; discovery stays on Kademlia.

## `kotoba-net`

`KotobaBehaviour` (`behaviour.rs`) gains four fields:

| field | protocol | role | WG/TS analogue |
|---|---|---|---|
| `autonat` | AutoNAT | reachability detection (am I publicly dialable?) | — |
| `relay_client` | Circuit Relay v2 client | relayed fallback path | Tailscale DERP relay |
| `dcutr` | DCUtR | Direct Connection Upgrade through Relay (hole punch) | WG/TS hole-punch |
| `relay_server` | `Toggle<relay::Behaviour>` | Circuit Relay v2 *server*, **off by default** | DERP server (serverless / decentralised) |

- Builder: `.with_quic().with_dns()?.with_relay_client(noise, yamux)?` — relayed connections reuse the base transport's Noise+Yamux upgrades; `dns` lets public relays be addressed by `/dns4/host/...`.
- New API: `NatConfig { relay_server: bool }` (default = client-only); `with_config` / `new_with_config`; `reserve_relay` / `reserve_relay_with_peer`; `dial_via_relay`; `add_external_address`; `ed25519_keypair_from_hex` (stable identity from a 32-byte hex seed).
- New events: `NatStatusChanged { public }`, `DirectConnectionUpgraded { peer }`, `RelayReservationAccepted { relay }`. The existing `_ => {}` catch-all in `KotobaNetEvent` consumers keeps downstream unchanged.

## `kotoba-server`

- `KOTOBA_NODE_ROLES=relay` now also runs the libp2p **Circuit Relay v2 server** (a designated public helper node). Reuses the existing role that already drives the firehose bridge.
- `KOTOBA_P2P_ED25519_HEX` pins a **persistent PeerId** (and therefore relay reservations / addresses) across restarts. **Kept separate from the CACAO/DID agent key by design** — networking identity ≠ signing identity. Absent/invalid → ephemeral per-boot identity (previous behaviour).
- `KOTOBA_RELAY_PEERS` (`peerid@multiaddr`, comma-separated) → an edge node takes a Circuit Relay v2 reservation on each at startup; DCUtR then upgrades to a direct link. **Edge/donated nodes need only this env to join over NAT.**

Edge/donated nodes need no behaviour config: AutoNAT + DCUtR + relay-client are always on; only a public node sets `relay` role, and a NAT'd node sets `KOTOBA_RELAY_PEERS`.

# Consequences

**Positive**
- Donated-node classes from ADR-2606012100 (`e7m`, `kotoba` pod) behind NAT can now join the mesh over the public internet: AutoNAT detects NAT → reserve on a public `relay`-role node → peers reach via the relay → DCUtR upgrades to a direct hole-punched connection.
- No new trust surface: encryption/auth stays Noise + libp2p `PeerId`; no central coordination server (Kademlia), preserving no-central-master and no-server-key.
- No vendored WG/TS code; libp2p (Apache/MIT) only — compatible with Apache-2.0 + Charter Rider.
- Networking identity decoupled from the signing identity.

**Negative / cost**
- New deps compiled in: `libp2p-{relay,autonat,dcutr,dns}` (+ `hickory-resolver` for DNS). Larger binary.
- Relay server, when enabled, consumes bandwidth relaying for others (bounded by libp2p relay limits; only public nodes opt in).

**Honest R0 / follow-ups**
- Node identity is ephemeral unless `KOTOBA_P2P_ED25519_HEX` is set (no auto-persisted key file yet).
- Relays are **configured** (`KOTOBA_RELAY_PEERS`), not yet **discovered** from the DHT.
- A public relay node does not yet auto-advertise its externally reachable address to the mesh.
- Verified by build + unit/integration tests; **not** yet validated against two real NAT'd hosts on the public internet (R1).

**Tests**: `kotoba-net` 69 unit + 2 integration green, clippy clean; `kotoba-server` builds clean.

# Alternatives Considered

1. **Integrate WireGuard / Tailscale into kotoba (a real L3 tun overlay).** Rejected: would vendor non-libp2p networking code, and Tailscale's model needs a central coordination server (DERP + control plane) which violates no-central-master and no-server-key. WireGuard alone has no NAT-traversal/discovery (still needs a coordinator). libp2p already provides equivalent function at L4/L7.
2. **Keep using WireGuard `wg0` only (fleet underlay).** Works for LAN fleet nodes but cannot reach arbitrary donated nodes behind home NAT without enrolling each into the WG mesh (manual key distribution, a coordinator) — exactly the toil libp2p relay/DCUtR removes.
3. **Browser WebRTC-direct path (ADR-2606036400).** Complementary, not a substitute: that closes browser↔kotoba reachability; this closes server↔server NAT traversal for non-browser donated nodes.
4. **Always-on relay server on every node.** Rejected: wasteful on edge nodes and undesirable (edge nodes are not public). Gated behind the `relay` role via `Toggle`.

# References

- kotoba PR: `etzhayyim/kotoba#23` (`feat/kotoba-net-nat-traversal`)
- `40-engine/kotoba/crates/kotoba-net/src/{behaviour,swarm,lib}.rs`
- `40-engine/kotoba/crates/kotoba-server/src/lib.rs` (swarm wiring)
- ADR-2606036400 — kotoba Browser-Reachable P2P (WebRTC-direct) + MCP-over-libp2p
- ADR-2606012100 — Donation-funded operation + compute-node donation (ameno / e7m / kotoba pod node classes)
- ADR-2605214000 — Murakumo mesh (no-VKE) + lexicon port rules
- ADR-2605231525 — no-server-key religious-corp architecture
- ADR-2605262130 — kotoba storage substrate unification
- `50-infra/murakumo/fleet.toml` — WireGuard `wg0` fleet underlay (layer below kotoba)
