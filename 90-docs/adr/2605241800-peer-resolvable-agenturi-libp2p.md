---
id: adr-2605241800-peer-resolvable-agenturi-libp2p
title: "ADR-2605241800: Peer-resolvable agentURI — collapse per-actor DNS subdomains; libp2p Multiaddr as the canonical XRPC transport (ERC-8004 identity preserved)"
status: proposed
doc_type: adr
topic: peer-resolvable-agenturi-libp2p
authoritative: true
last_verified: 2026-05-24
priority: 8.0
axis: architecture
weight: 0.70
priority_note: "Identifies the discovery+transport layer that the ERC-8004 identity stack (ADRs 2604262100 / 2604262145 / 2605231500) was designed to compose with but never named. Resolves the DNS-subdomain proliferation pressure (8+ Workers as of 2026-05-24: pinner / esign / audit / dataset-pinner / pds / anchorer / projector / karute) without disturbing the on-chain identity primitives."
authoritative_for:
  - peer-resolvable agentURI service[] format (libp2p Multiaddr)
  - DNS subdomain collapse policy (per-actor → root + IPFS-anchored agentURI)
  - libp2p protocol id namespacing (/x/etzhayyim/xrpc/<version>)
  - 4-phase migration (deploy ERC-8004 → dual-publish HTTPS+libp2p → retire HTTPS → kotoba-datomic witness)
  - Transport layer choice (libp2p as primary; iroh as experimental sibling)
depends_on:
  - adr-2604262100-erc725-erc8004-k8s-ipfs-agent-runtime
  - adr-2604262145-erc8004-protocol-root-atproto-profile
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605241500-etzhayyim-dataset-cid-substrate
related:
  - adr-2605231500-etzhayyim-agent-driven-unspsc-supply-flows
  - adr-2605092600-holochain-agent-actor-runtime-experiment
supersedes: []
superseded_by: []
---

# ADR-2605241800: Peer-resolvable agentURI via libp2p

**Status**: proposed
**Date**: 2026-05-24
**Deciders**: Jun Kawasaki

# Context

The religious-corp substrate currently ships one Cloudflare DID Worker
per actor: `pinner.etzhayyim.com`, `esign.etzhayyim.com`,
`audit.etzhayyim.com`, `dataset-pinner.etzhayyim.com` (just added in
ADR-2605241500), `pds.etzhayyim.com`, `anchorer.etzhayyim.com`,
`projector.etzhayyim.com`, `karute.etzhayyim.com`. Each demands:

1. An AAAA DNS record on the `etzhayyim.com` zone (manual CF dashboard step).
2. A CF Worker route binding.
3. NOTICE + CHARTER-RIDER.md symlink + npm/wrangler scaffold.
4. Council-visible review for new public hostnames.

This pattern scales O(actors). Three deeper concerns:

- **ADR-2605231525 (No-Server-Key)** posture wants etzhayyim infrastructure to
  hold zero signing capability; each per-actor Worker is one more piece of
  infra to vet.
- **ADR-2605172000 (RW-free substrate)** is fine with DNS for *bootstrap* but
  prefers peer-routed bytes after that.
- **ADR-2605231400 (kotoba-datomic Holochain-iso)** already names the intended
  end-state: agent-centric DHT with witness quorum. The Worker-per-actor
  pattern is its operational opposite.

**Crucially**, the identity layer is **already designed and partly
implemented**: ADRs 2604262100 / 2604262145 specify ERC-725 root +
ERC-8004 agent registry + `agentURI = ipfs://<cid>/agent.json` +
`did:pkh:eip155:8453:<addr>`. The on-chain contracts
`AdherentRegistry.sol` (ERC-5192 soulbound) and `AgentAuthorityToken.sol`
(ERC-721+5192 soulbound, 11/11 forge tests) already exist under
`50-infra/etzhayyim-chain-contracts/src/`. ERC-1271 multi-controller
binds the on-chain Council Safe to `did:web:etzhayyim.com`.

What was never specified was: **what goes in `agent.json`'s
`service[]` field** beyond the per-actor HTTPS URL. This ADR fills that
gap by declaring a peer-resolvable transport — libp2p Multiaddr — and
phasing out the per-actor HTTPS subdomains.

# Decision

Adopt a **5-layer architecture** that pins each layer to a settled or
to-be-settled mechanism, with the peer transport being the only
genuinely new decision:

```
L5  Authority         : ERC-725 root + ERC-8004 etzhayyimAgentRegistry +
                        AdherentRegistry + AgentAuthorityToken
                        (Base L2; ERC-1271 multi-controller; AT Protocol mirrors)
        ↑ binds
L4  Identity          : did:pkh:eip155:8453:<addr>  ←→  did:web:etzhayyim.com
                        ←→  did:key:<ed25519>
                        agentURI = ipfs://<cid>/agent.json  (CID anchored on-chain)
        ↑ resolved via
L3  Discovery doc     : agent.json @ IPFS — contains
                          - verificationMethod (Ed25519 pubkey)
                          - service[] with libp2p Multiaddr (NEW)
                          - capabilities[] (ERC-8004 / AAT scope hash)
        ↑ used to dial
L2  Transport         : libp2p (primary) — Kademlia DHT + relay + mDNS,
                        QUIC/TCP, Noise/TLS handshake
                        iroh (experimental sibling) — same wire-compatible
                        Ed25519 NodeId; uses pkarr for discovery
        ↑ carries
L1  App protocol      : AT Protocol XRPC + Lexicons (00-contracts/lexicons/)
                        UNCHANGED — XRPC is tunneled over the libp2p Stream
```

## D1. agent.json `service[]` shape (NEW)

```json
{
  "@context": "https://w3id.org/did/v1",
  "id": "did:pkh:eip155:8453:0xABCD...",
  "controller": "did:web:etzhayyim.com",
  "verificationMethod": [
    { "id": "#key-1",
      "type": "Ed25519VerificationKey2020",
      "publicKeyMultibase": "z6Mk..." }
  ],
  "service": [
    {
      "id": "#xrpc-libp2p-primary",
      "type": "AtprotoXrpc",
      "serviceEndpoint": "/p2p/12D3KooW...AiEc",
      "x-libp2p-protocol": "/x/etzhayyim/xrpc/1.0"
    },
    {
      "id": "#xrpc-libp2p-bootstrap",
      "type": "AtprotoXrpc",
      "serviceEndpoint": "/dnsaddr/etzhayyim.com/p2p/12D3KooW...AiEc",
      "x-libp2p-protocol": "/x/etzhayyim/xrpc/1.0",
      "x-rationale": "DNS-anchored fallback so cold clients can bootstrap before joining the DHT"
    },
    {
      "id": "#xrpc-https-legacy",
      "type": "AtprotoXrpc",
      "serviceEndpoint": "https://etzhayyim.com/actor/<slug>",
      "x-deprecated-at": "Phase C",
      "x-rationale": "warm migration; retired after Phase C lands"
    }
  ],
  "capabilities": [
    { "id": "com.etzhayyim.apps.substrate.datasetPin", "scope": "0x<aat-scope-hash>" }
  ]
}
```

The PeerId in `serviceEndpoint` MUST be the libp2p host's Ed25519
identity, which is bit-identical to the `did:key` form of the same key.
Consumers SHOULD prefer entries in declaration order (libp2p first,
HTTPS fallback). The `/dnsaddr/etzhayyim.com/...` form is **the only
DNS dependency** in the steady state; resolvers walk it via libp2p's
standard dnsaddr resolution + Mainline DHT.

## D2. libp2p protocol namespace

Use a single shared XRPC tunnel protocol id, versioned:

```
/x/etzhayyim/xrpc/<MAJOR>.<MINOR>
```

`MAJOR=1` ships with this ADR. Backwards-incompatible changes (e.g.,
required multiplexed framing, mandatory authn) bump MAJOR.

Inside the libp2p Stream, the wire format is HTTP/1.1 framing carrying
AT Protocol XRPC bodies — i.e., the libp2p stream is a drop-in
transport replacement for the TCP socket that an HTTPS request would
otherwise terminate on. The consumer-side `ipfs p2p forward` (or any
libp2p Multistream-Select dialer) exposes this as a local TCP socket;
the receiver's `ipfs p2p listen` hands it off to a localhost XRPC
handler.

## D3. Implementation — Kubo's libp2p subsystem (Phase B starting point)

Every Murakumo Mac mini already runs Kubo (per ADR-2605241500 for
datasets; ADR-2605171800 Stage 4 for MST CARs). Kubo embeds
go-libp2p and exposes `ipfs p2p listen` / `forward` once
`Experimental.Libp2pStreamMounting = true` is set. Phase B does **not**
require adding a new daemon; it only adds:

1. Per-machine config: `ipfs config --json Experimental.Libp2pStreamMounting true`
2. Per-actor `ipfs p2p listen /x/etzhayyim/xrpc/1.0 /ip4/127.0.0.1/tcp/<actor-port>`
3. Update agent.json service[] with the local PeerId

Smoke verified (2026-05-24 17:57 UTC, log at
`10-protocol/etzhayyim-libp2p/_poc-evidence/2026-05-24-2-peer-loopback.md`):

- Host peer `12D3KooW...AiEc` on `/Volumes/260317/etzhayyim/ipfs-data` listens.
- Consumer peer `12D3KooW...1bdX` on `/tmp/kubo-consumer` (separate Kubo) forwards.
- Backend HTTP `:18080` served identical bytes via tunneled `:29080`.
- libp2p protocol id `/x/etzhayyim/xrpc/1.0` confirmed end-to-end.
- backend `http.server` log shows the tunneled GET reached it.

## D4. Helper package — `10-protocol/etzhayyim-libp2p/`

Phase B ships a tiny package that wraps the Kubo p2p commands:

- `scripts/expose-xrpc.sh <actor-port> [protocol-version]` — actor-side
- `scripts/dial-xrpc.sh <peer-id> <local-port> [protocol-version]` — consumer-side
- `scripts/agent-json-libp2p-service.sh` — emits the service[] entry
  for the current Kubo node, ready to splice into `agent.json`
- `scripts/print-multiaddr.sh` — emits the bootstrap-ready `/dnsaddr/.../p2p/<id>` form

These are shell wrappers; the Go-libp2p binding is the underlying Kubo
HTTP API (`POST /api/v0/p2p/listen`, etc.). A future Phase B+ may
introduce a Go binary in `70-tools/e7m-libp2p/` for richer control
(circuit-relay reservation, identity-key rotation, etc.).

## D5. Capabilities and authentication

XRPC over libp2p inherits AT Protocol's existing capability scheme:

- Caller signs the XRPC request with their atproto JWT (DPoP-style) or
  consent capability JWS (per ADR-2605231400).
- Receiver verifies the JWT/JWS using the caller's DID, resolved
  through (a) on-chain ERC-8004 record by `did:pkh`, or (b) IPFS
  agentURI for `did:key`.
- The libp2p layer adds a **second** authn channel: every libp2p
  connection is mutually authenticated at the Ed25519 PeerId level
  (Noise handshake). The PeerId equals the actor's `did:key` form,
  so the transport peer == the XRPC caller — no Sybil exposure beyond
  what the chain already prevents.

## D6. Bootstrap and discovery topology

- **mDNS**: Murakumo intra-cluster peers discover each other via
  multicast DNS on LAN. Zero config; works out of the box.
- **Kademlia DHT**: WAN peer discovery via Mainline-style DHT. Already
  active on every Kubo (default routing mode includes DHT in
  `dhtclient` profile).
- **DNS bootstrap fallback**: `/dnsaddr/etzhayyim.com/p2p/<id>` for
  cold clients. The single AAAA record `etzhayyim.com 100::` proxied
  is already provisioned. **No new DNS record is added in Phase B**.
- **Circuit relay v2**: peers behind NAT can advertise reachability
  through any 1 well-known relay. We host one relay on
  `simeon.etzhayyim.com` (= the existing PDS host); a Murakumo-quorum
  relay arrangement (3 relays, 2-of-3 reachable) is a Phase D
  upgrade.

# Consequences

## Positive

- ✅ DNS subdomain count: 8+ → 1 (etzhayyim.com root only). DNS
  provisioning bottleneck for new actors disappears.
- ✅ No new infra: Kubo's libp2p subsystem is already running on every
  Murakumo node.
- ✅ ERC-8004 identity stack is preserved unchanged — this ADR only
  fills the `agent.json service[]` slot that the existing ADRs left
  open.
- ✅ NAT traversal handled by libp2p Circuit Relay v2 + AutoNAT (no
  separate WireGuard mesh required).
- ✅ Doctrinal fit with ADR-2605231400 kotoba-datomic-iso witness quorum:
  libp2p is the IPFS-substrate of the Holochain-iso target.
- ✅ Path is open to a fully peerful future (Phase D kotoba-datomic DHT)
  without further architectural churn.

## Negative / costs

- ⚠️ Operational training: operators must understand libp2p Multiaddr,
  PeerId, mDNS, and the dual-mount listen/forward pattern.
- ⚠️ Self-dial is unsupported (libp2p deduplicates connections to one's
  own PeerId). PoC required two peers; production needs the same.
- ⚠️ Kubo `ipfs p2p` is marked `EXPERIMENTAL` in the Kubo CLI help.
  We accept this — the underlying go-libp2p p2p subsystem is
  production-grade; only the Kubo CLI wrapper carries the label.
- ⚠️ Backwards compatibility window (Phase B → C) is 60-90 days where
  agents publish BOTH libp2p and HTTPS endpoints.

## Invariants introduced

1. New agentURI documents MUST declare at least one libp2p
   `service[]` entry. HTTPS-only is allowed for Phase B legacy actors
   but deprecated.
2. The libp2p protocol id `/x/etzhayyim/xrpc/1.0` is reserved
   substrate-wide. Per-actor protocols MAY be introduced under
   `/x/etzhayyim/<actor>/<lexicon-domain>/<version>` but XRPC routing
   stays canonical at `/xrpc/1.0`.
3. DNS records under `*.etzhayyim.com` MUST NOT be added for new
   first-party actors after Phase C lands. Existing per-actor records
   stay through Phase C, then are retired.

# Alternatives Considered

The full 10-candidate transport+discovery comparison is in the design
notes (chat log; reproduced inline below). Top non-libp2p candidates:

- **iroh** (NodeId-based, single Rust binary, pkarr discovery). Tied
  with libp2p on doctrinal + atproto fit; behind on maturity for our
  scale (4.36 vs 4.53 weighted). Adopted as **experimental sibling**:
  a future Phase B+ may expose the same `/x/etzhayyim/xrpc/1.0` over
  iroh streams when iroh's relay quorum semantics stabilize.
- **Holochain DPKI** (5.0 doctrinal). Excellent fit but 1.0 on AT
  Protocol compatibility (it would require porting PDS/XRPC to
  Holochain primitives). Slated for ADR-2605231400 kotoba-datomic Phase D
  (witness quorum), not the present transport decision.
- **WireGuard mesh / Tailscale**: 5.0 on Mac fleet, 1.0 on discovery
  (coordinator dependency). Rejected as a primary substrate; may serve
  as a complementary node-level VPN for sensitive operator tooling.
- **Single did:web path collapse alone**: 5.0 on AT Protocol fit, 1.0
  on doctrinal. Would solve DNS pressure but not the substrate-boundary
  posture. **Adopted as Phase A** of this ADR (necessary precursor).
- **NATS supercluster**: rejected on discovery (2/5) and doctrinal
  fit (2/5).
- **Bitcoin OP_RETURN anchor**: rejected on Mac fleet fit (2/5) and
  doctrinal tension with §2(b) speculative finance.
- **k3s Pod / Service**: orchestration only, not a discovery substrate;
  retained for `ADR-2605232100` cell deployment, not as transport.
- **BitTorrent Mainline DHT**: subsumed by libp2p Kademlia (libp2p uses
  the same algorithm with stronger identity semantics).
- **Hypercore / Holepunch hyperswarm**: technically capable; smaller
  community than libp2p; rejected on maturity.

# Migration phasing (4 stages)

| Phase | Trigger | Scope | Exit gate |
|---|---|---|---|
| **A. did:web path collapse** | Now | 8 per-actor DID Workers → 1 root Worker at `etzhayyim.com/actor/<slug>/did.json`. AAAA for new actors stops. | All new actors register under path; existing actors keep their AAAA until Phase C. |
| **B. libp2p dual-publish** | After this ADR lands | Each actor's `agent.json` adds a libp2p `service[]` entry alongside the existing HTTPS entry. Helper scripts in `10-protocol/etzhayyim-libp2p/`. Smoke-verified by the PoC log. | At least one consumer (e.g. `e7m-dataset publish-ipfs`'s PDS emit) is exercised over the libp2p path in prod. |
| **C. HTTPS retirement** | 60-90 days after Phase B | Per-actor `*.etzhayyim.com` AAAA records removed. Per-actor Workers archived (`_archive/`). `etzhayyim.com` root + IPFS gateway are the only DNS endpoints. | `e7m verify` adds an invariant: no first-party actor publishes an HTTPS-only `service[]`. |
| **D. kotoba-datomic witness quorum** | Post-Council ratify (per ADR-2605231400) | 3-of-5 Murakumo witness quorum for capability records; libp2p relay quorum replaces single-relay; bootstrap DNS dependency optional. | DPKI test suite + kotoba-datomic spec compliance. |

This ADR authorizes Phase A and Phase B execution. Phase C is gated on
Phase B observability proving stability. Phase D is a separate
follow-on ADR.

# References

- ADR-2604262100 (ERC725 + ERC-8004 + k8s + IPFS agent runtime — identity origin)
- ADR-2604262145 (ERC-8004 protocol root + atproto profile — agentURI shape)
- ADR-2605231400 (kotoba-datomic Holochain-iso substrate — Phase D destination)
- ADR-2605231525 (No-Server-Key religious-corp architecture — doctrinal constraint)
- ADR-2605241500 (Dataset CID substrate — first consumer of peer transport)
- libp2p specs: https://github.com/libp2p/specs
- Multiaddr: https://github.com/multiformats/multiaddr
- Kubo `ipfs p2p` subsystem: https://github.com/ipfs/kubo/blob/master/docs/experimental-features.md#p2p
- PoC evidence: `10-protocol/etzhayyim-libp2p/_poc-evidence/2026-05-24-2-peer-loopback.md`
- AAT contract: `50-infra/etzhayyim-chain-contracts/src/AgentAuthorityToken.sol`
- AdherentRegistry: `50-infra/etzhayyim-chain-contracts/src/AdherentRegistry.sol`
