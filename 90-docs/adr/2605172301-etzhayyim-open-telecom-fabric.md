---
id: adr-2605172301-etzhayyim-open-telecom-fabric
renumbered_from: "2605172300"
title: "ADR-2605172301: etzhayyim Open Telecom Fabric"
status: proposed
doc_type: adr
topic: etzhayyim-open-telecom-fabric
authoritative: true
last_verified: 2026-05-17
priority: 7.0
axis: protocol
weight: 0.70
priority_note: "Defines the open-source PSTN-like voice fabric boundary: protocol-native addressing and switching live in etzhayyim/root; regulated PSTN numbering and interconnect remain vendor/carrier bridge responsibilities."
authoritative_for:
  - etzhayyim open telecom protocol boundary
  - protocol-native telephone-like addressing without public E.164 number issuance
  - open voice switching fabric architecture
  - vendor bridge boundary for PSTN, SIP trunk, IMS, and carrier compliance
depends_on:
  - adr-2605152100-etzhayyim-github-org-boundary
related:
  - adr-2604262145-erc8004-protocol-root-atproto-profile
  - adr-2604251830-shannon-optimal-layered-architecture
supersedes: []
superseded_by: []
---

# ADR-2605172301: etzhayyim Open Telecom Fabric

**Status**: proposed
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

The goal is to build a PSTN-like public voice network as open source under
etzhayyim, rather than only consuming carrier-provided telephone numbers.

This is technically possible if "PSTN" is decomposed into two layers:

1. **Open voice fabric**: addressing, discovery, call setup, media relay,
   routing, portability, settlement metadata, and audit records.
2. **Regulated PSTN bridge**: E.164 public telephone numbers, emergency calls,
   carrier interconnect, lawful obligations, subscriber identity checks, and
   country-specific telecom filings.

The open layer can be implemented as protocol and software. The regulated
bridge cannot mint public telephone numbers by protocol alone; it must connect
through licensed or otherwise authorized telecom operators in each jurisdiction.

Existing vendor-side telecom actors already include IMS/SIP concepts such as
`establishVoiceCall` and `bridgeVoiceToInterconnect`. Those remain useful, but
the open fabric needs a principal-owned protocol root in `etzhayyim/root` so it
does not become a etzhayyim Japan proprietary carrier product by default.

# Decision

Create **etzhayyim Open Telecom Fabric** as an open-source, protocol-native
voice network with PSTN-compatible semantics but not PSTN number sovereignty.

## Protocol Boundary

The open fabric owns:

- **Addressing**: `telx:` URIs and DID-bound aliases, for example
  `telx:alice@etzhayyim.com` or `did:web:example.org#voice`.
- **Routing**: signed route advertisements from domains, communities, and
  gateways.
- **Call setup**: SIP-compatible offer/answer metadata with WebRTC/SRTP media.
- **Portability**: alias transfer records signed by the old and new route
  authority.
- **Settlement metadata**: open CDR envelopes that can be settled on-chain or
  off-chain without exposing media content.
- **Governance**: registry rules, abuse handling, and gateway conformance tests.

The open fabric does **not** own:

- Japanese `0AB-J`, `050`, `070/080/090/060`, or any other public E.164 number
  allocation.
- Emergency calling availability claims unless a regulated bridge explicitly
  provides them.
- Carrier interconnect rights.
- SIM/eSIM issuance, IMSI/SUPI assignment, or radio spectrum use.

## Architecture

```
caller app
  -> telx resolver
  -> route authority
  -> signaling node
  -> media relay / direct WebRTC
  -> callee app

optional:
  signaling node
    -> regulated bridge adapter
    -> SIP trunk / IMS / PSTN gateway
    -> public telephone network
```

## Minimal Components

1. **telx resolver**
   Resolves `telx:` and DID voice service entries to route candidates.

2. **route authority**
   Publishes signed routing records and revocation records.

3. **signaling node**
   Handles invite, provisional response, answer, hangup, transfer, and failure
   events. It should speak a small JSON/XRPC surface first and map to SIP later.

4. **media plane**
   Uses WebRTC DTLS/SRTP for endpoint calls. TURN is allowed. RTP/SIP gatewaying
   belongs to bridge adapters.

5. **gateway adapter**
   Bridges the open fabric to SIP trunk, IMS, PSTN, or carrier APIs. This is the
   compliance boundary and must be deployable separately from open routing.

6. **CDR/audit stream**
   Emits call metadata records with hashed regulated identifiers and plain
   protocol-native aliases.

## Repository Placement

Open protocol material belongs in `etzhayyim/root`:

- `10-protocol/open-telecom/`
- `00-contracts/lexicons/com/etzhayyim/apps/openTelecom/` after cutover or rename
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/open-telecom/` for public governance workflows

Vendor bridge material remains in this repo:

- `00-contracts/lexicons/com/etzhayyim/apps/telecom/*`
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/telecom/*`
- `50-infra/multicluster/*/telecom-actors/*`

The current repository may carry a staging copy until the etzhayyim cutover is
complete, but the authoritative open-source destination is `etzhayyim/root`.

# Consequences

Positive:

- Creates a real open telecom target without claiming illegal number issuance.
- Lets apps use telephone-like addressing even before carrier interconnect.
- Keeps PSTN gateways replaceable and jurisdiction-specific.
- Reuses existing telecom actors for bridge-side service activation, billing,
  interconnect CDRs, and compliance workflows.

Costs:

- The system will not be reachable from ordinary phone numbers until a bridge is
  provisioned.
- Federation and abuse handling become first-class protocol work, not an
  afterthought.
- Product copy must be precise: this is open voice fabric first, PSTN bridge
  second.

# Implementation Plan

1. Add `10-protocol/open-telecom/README.md` with the minimal protocol contract.
2. Add lexicons for resolver, route advertisement, invite, answer, hangup, and
   CDR envelopes.
3. Implement a local signaling node using JSON/XRPC and WebRTC offer/answer.
4. Add a loopback gateway adapter that proves call setup without PSTN.
5. Add a SIP trunk adapter behind `bridgeVoiceToInterconnect`.
6. Move open protocol files to `etzhayyim/root` when the open-scope cutover is
   executed.

# Alternatives Considered

## A. Directly become a public telephone-number issuer

Rejected for protocol scope. Public telephone-number allocation is a regulated
national resource and cannot be created by open-source software alone.

## B. Build only a SIP PBX

Rejected because it would reproduce a private PBX, not an open federated voice
fabric with portable identities and public route governance.

## C. Use only Matrix/WebRTC calling

Rejected as insufficient for PSTN-like semantics. Matrix/WebRTC can be a media
and signaling substrate, but the fabric still needs telecom-grade routing,
portability, gateway, CDR, and abuse-control semantics.

# References

- `10-protocol/open-telecom/README.md`
- `00-contracts/lexicons/com/etzhayyim/apps/telecom/establishVoiceCall.json`
- `00-contracts/lexicons/com/etzhayyim/apps/telecom/bridgeVoiceToInterconnect.json`
- `50-infra/multicluster/murakumo-vke/telecom-actors/README.md`
- ADR-2605152100 etzhayyim GitHub Org Boundary + Monorepo Seed Strategy
