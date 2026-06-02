# shared-ip/libp2p-nic — die-level libp2p protocol engine

Per **ADR-2605242530** §"Murakumo mesh interconnect" and
**ADR-2605214000** (Murakumo no-VKE mesh).

This IP block makes fuigo dies first-class Murakumo mesh peers without
requiring a separate NIC or k8s control plane.

## Protocols supported

- libp2p kademlia DHT (peer discovery)
- libp2p GossipSub (training control-plane messages)
- libp2p bitswap subset (gradient AllReduce payload)
- noise handshake (ed25519 peer identity)

## Peer identity

- 256-bit ed25519 peer ID is burned into eFuse at tape-out
- Peer ID derivation: `keccak256(lot_id || die_xy_coord || nonce_council_attest)`
- Recorded in `com.etzhayyim.silicon.chipManufacturingAttestation` Lexicon at shipment

## Why on-die

- Avoid commercial NIC dependency (Mellanox, Broadcom, Intel)
- Avoid k8s control-plane (per ADR-2605214000 no-VKE invariant)
- Murakumo fleet adds nodes by peer discovery — no orchestrator change

## Phase 1 scope

Stub `rtl/libp2p_nic.sv` (Phase 2 wave) — peer-id register + GossipSub
framer skeleton.
