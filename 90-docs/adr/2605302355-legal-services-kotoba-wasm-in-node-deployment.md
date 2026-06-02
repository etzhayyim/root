---
id: adr-2605302355-legal-services-kotoba-wasm-in-node-deployment
title: "ADR-2605302355: legal-services constitutional gates run as in-node kotoba WASM Component guests (not Cloudflare Workers)"
status: accepted
doc_type: adr
topic: legal-services-kotoba-wasm-deployment
authoritative: true
last_verified: 2026-05-30
priority: 6.5
axis: architecture
weight: 0.62
priority_note: "Records the decision + live verification that the legal-services constitutional gates execute as WASM Component guests INSIDE the kotoba node (wasm32-wasip2 WasmExecutor), not as external Cloudflare Workers. Two guests: chigiri-legal-aid-guest (G14/G15/G16 intake gate) + chigiri-legal-comms-guest (G18 counsel-actuation gate). Both compiled with cargo-component, content-addressed in kotoba via block.put, and invoked via com.etzhayyim.apps.kotoba.invoke.run (program_type=wasm-node) under an operator JWT. Gate violations are blocked server-side (assert_count=0); valid invocations journal the matter/legal-act quad (gas-metered execution + content-addressed JournalEntry). Documents the request surfaces (HTTP XRPC / MCP kotoba_wasm_run / QUIC libp2p mesh propagation), the Python-guest blocker (wasmtime 22 extended-const) that forced the Rust path, and the relationship to the now-superseded CF Worker gate logic (CF retained only as optional HTTP front-door + downstream egress transport). Stored program CIDs recorded for reproducibility."
authoritative_for:
  - legal-services in-node kotoba WASM deployment decision
  - chigiri-legal-aid-guest + chigiri-legal-comms-guest program manifests + CIDs
  - invoke.run / MCP kotoba_wasm_run / QUIC mesh request-surface for legal-services
  - CF Worker → kotoba WASM gate-logic migration record
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605302200-chigiri-unpaid-legal-aid-lane-multijurisdiction
  - adr-2605302330-chigiri-japan-certified-adr-mediation-lane
  - adr-2605302345-etzhayyim-legal-services-delivery-and-global-judiciary-corpus
related:
  - adr-2605301030-kotoba-kg-storage-session-52-entity-actor-graph
supersedes: []
superseded_by: []
---

# ADR-2605302355: legal-services constitutional gates as in-node kotoba WASM guests

**Status**: accepted
**Date**: 2026-05-30
**Deciders**: Jun Kawasaki

# Context

ADR-2605302345 stood up the legal-services delivery surface as Cloudflare Workers
(`50-infra/etzhayyim-legal-clinic`, `50-infra/etzhayyim-legal-comms`). The directive
that followed was to run these **on kotoba as WASM, not Cloudflare**. kotoba already
ships a WASM Component Model host (`wasm_executor` / `udf_executor` / `invoke_router`,
WIT world `kotoba:kais@0.1.0` / `kotoba-node`), so the constitutional gates can execute
*inside the storage substrate* and write their results directly into the EAVT graph.

This ADR records the decision and its live verification.

# Decision

The legal-services **constitutional gates run as WASM Component guests inside the kotoba
node**, compiled with `cargo-component` to `wasm32-wasip2`. Two guests:

| guest | crate | gates | on pass |
|---|---|---|---|
| chigiri-legal-aid-guest | `40-engine/legal-aid-wasm-guest/` | G14 (no advice) · G15 (zero compensation) · G16 (in-jurisdiction Public-Fund counsel; AT/US-state `verify-required` rejected) | `kqe.assert-quad com.etzhayyim.chigiri/legalAidMatter` + `kse.publish …/legalAid/counsel-assigned` |
| chigiri-legal-comms-guest | `40-engine/legal-comms-wasm-guest/` | G18 (counselActuation: counsel DID + own signature + license == destination jurisdiction) | `kqe.assert-quad com.etzhayyim.legal/outboundLegalAct` + `kse.publish …/legalAct/authorized` |

## D1. Content-addressed program storage

Each guest's `.wasm` is stored in kotoba via `block.put` and addressed by CID
(content-hash → integrity by construction; live-verified retrievable via `block.get`):

- chigiri-legal-aid-guest (151 702 B) → `bafyreictmsolu2dto5wyr7pm2yosh67vx3z47o7vf7wqmqsmdlly7k2vmq`
- chigiri-legal-comms-guest (152 949 B) → `bafyreiadu2mwil2xz4bwcyjpxosttujve6lofteoab3paf43jre55xns4y`

## D2. Request surfaces

- **HTTP XRPC** (primary): `POST /xrpc/com.etzhayyim.apps.kotoba.invoke.run`
  `{program_type:"wasm-node", wasm_b64, ctx_b64, agent_did}` under an **operator JWT**
  (`require_operator_auth`: `sub == operator_did`, exp checked, signature not verified).
  `ctx_b64` is the CBOR `InvokeContext{graph, session_cid, args_cbor}`; the host passes it
  to the guest's `run(ctx_cbor)` verbatim. Response: `{status, gas_used, assert_count,
  retract_count, journal_cids[]}`.
- **MCP** (`POST /mcp`, JSON-RPC 2.0): tool **`kotoba_wasm_run`** (one of 18 tools).
  `initialize`/`tools/list`/`ping` are public; the run tool requires auth. This is the
  path for LLM / agent / MCP-host invocation.
- **QUIC / libp2p mesh** (gossipsub + Kademlia + request_response): NOT a direct invoke
  channel — it propagates *effects*. Asserted quads publish to gossipsub topic
  `kotoba/quad/assert`; the source-chain ChainEntry propagates via Kademlia DHT; blocks
  sync via request_response. Multi-node: invoke on any node via HTTP/MCP → journaled
  result replicates over QUIC. Currently single-node (`peers=0`), mesh idle.

## D3. Server-side enforcement (live-verified)

invoke.run executes the guest in the metered WasmExecutor and journals assertions:

| input | result |
|---|---|
| legal-aid valid (jpn + jpn counsel + zero-comp) | `status=ok gas_used=30 assert_count=1 journal_cids=[bafyrei…]` |
| legal-aid G15 (zero_compensation=false) | `rejected assert_count=0 gas=0` |
| legal-aid G16 (Austria verify-required / no counsel) | `rejected assert_count=0` |
| legal-comms valid (court-filing + jpn counsel + own signature) | `authorized assert_count=1` |
| legal-comms G18 (no actuation / wrong-jx / no signature) | `refused assert_count=0` |

`gas_used > 0` proves metered execution; `journal_cids` proves the assertion was
content-addressed and persisted. The gates are enforced **inside the substrate**, not at
an external edge.

## D4. Relationship to the Cloudflare Workers

The CF Workers' **gate logic is superseded** by the guests. CF is retained only as an
optional HTTP front-door (`etzhayyim-legal-clinic`) and as the home for **downstream
egress transport** (the legal-comms guest authorizes + records; actual fax/email/e-filing
send happens OUTSIDE the sandboxed guest, keyed off the `…/legalAct/authorized` event).
The guest never performs network egress and holds no legal-act signing key (no-server-key
ADR-2605231525).

# Consequences

**Positive**
- Constitutional gates execute in the same trust domain as storage; a violation cannot
  reach the EAVT graph (assert_count=0), enforced by the host, not by edge convention.
- Content-addressed, gas-metered, journaled — auditable + reproducible by CID.
- One substrate: no external edge runtime in the gate path; aligns with the
  blockchain-self-contained substrate boundary.

**Negative / costs**
- `invoke.run` currently requires `wasm_b64` on every call (no program_cid-only resolution
  in the host yet); the stored block CID is provenance, not yet a call-by-reference. A host
  feature (resolve wasm from program_cid when wasm_b64 absent) would remove the re-upload.
- Python guests are **blocked** on the current kotoba (wasmtime 22 disables EXTENDED_CONST;
  componentize-py 0.23 emits `i32.add` in global initializers). The Rust guest path is the
  only working one until the wasmtime-24 + `wasm_extended_const(true)` upgrade (deps.toml).
- Egress transport is now a separate downstream concern (intentional, but it is unbuilt).

**Risks**
- Operator-JWT auth checks `sub` only (no signature verification on this tier); operator-DID
  scoping is the control. Acceptable for a single-operator node; revisit for multi-operator.

# Alternatives Considered

1. **Keep the gates as Cloudflare Workers** — rejected per directive + substrate-boundary:
   an external edge runtime in the gate path is outside the self-contained substrate.
2. **Python (componentize-py) guests** — rejected: blocked on wasmtime 22 (extended-const);
   Rust (cargo-component) is live-verified. Revisit after the wasmtime-24 upgrade.
3. **Call-by-program_cid now** — deferred: the host requires `wasm_b64`; block.put gives
   content-addressed provenance, and call-by-CID is a host feature to add later.

# References

- ADR-2605302345 (legal-services delivery — the CF Workers this supersedes for gate logic)
- ADR-2605302200 / 2605302330 (the gates G14/G15/G16 + lanes) · ADR-2605231525 (no-server-key)
- ADR-2605262130 (kotoba substrate) · ADR-2605301030 (kotoba KG storage session — invoke/commit discipline)
- `40-engine/legal-aid-wasm-guest/` · `40-engine/legal-comms-wasm-guest/` (guest crates + deploy scripts)
- kotoba WIT world `kotoba:kais@0.1.0` (`40-engine/kotoba/crates/kotoba-guest/wit/world.wit`)
