---
id: adr-2606071800-kotoba-monorepo-projection-r2-adr-corpus-persistence
title: "ADR-2606071800: kotoba monorepo projection Phase R2 — ADR corpus persistence via kotoba-wasm and kotodama on Murakumo"
status: proposed
doc_type: adr
topic: adr-persistence-r2
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Advances the ADR corpus monorepo projection (ADR-2605281700) to Phase R2. Moves from static NDJSON emission (R1) to live, verifiable datom ingestion into the kotoba EAVT database using kotoba-wasm and kotodama cells running on the Murakumo fleet."
authoritative_for:
  - Phase R2 ADR corpus persistence mechanism
depends_on:
  - "2605281700"
  - "2605281800"
  - "2606013600"
related: []
supersedes: []
superseded_by: []
---

# ADR-2606071800: kotoba monorepo projection Phase R2 — ADR corpus persistence via kotoba-wasm and kotodama on Murakumo

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

Per ADR-2605281700, the `kotoba` content-addressed monorepo projection was established as a 7-phase rollout. Phase R0 defined the schema, and Phase R1 (ADR-2605281800) delivered the offline Python tool (`ingest_adr.py`) that parses the `90-docs/adr/*.md` corpus, computes IPFS CIDs via local Kubo, and emits a static NDJSON quad stream (`kotoba-quads.ndjson`).

Server-side persistence (`quad.create` via XRPC + CACAO signing) was initially deferred. With the verification of the browser `kotoba-wasm` node as the sovereign tier-2 (ADR-2606013600), the underlying `kotoba-kqe` read engine and `commitSigned` logic have proven to be both mature and perfectly suited to a WebAssembly host environment.

We must now elevate the monorepo projection to Phase R2: live, on-chain/in-EAVT persistence of the R0/R1 ADR corpus using Kotodama cells executing on the Murakumo fleet, securely backed by `kotoba-wasm`.

# Decision

1. **Kotodama Cell for Ingestion:** We define a new Kotodama cell, `sys_adr_corpus_persist`, responsible for reading the static `kotoba-quads.ndjson` (the R1 output) and transacting those quads into the canonical kotoba EAVT state.
2. **Execution Substrate:** The cell executes on the Murakumo fleet, preserving the Murakumo-only invariant (ADR-2605215000).
3. **Storage Engine:** The cell utilizes the `kotoba-wasm` bindings (`kotoba-kqe` EAVT/AEVT/AVET/VAET and `commitSigned` no-server-key writes) to perform deterministic content-addressed writes. This ensures that the generated state root is functionally identical to what would be produced client-side by a browser node.
4. **Gates:** The operation is guarded by a Phase R2 activation check, requiring explicit execution parameters rather than firing silently.

# Consequences

- **Live Database Integration:** The ADR corpus is no longer just a static NDJSON file; it is fully integrated into the live kotoba datom log, available for cross-referencing by other actors (e.g., `danjo`).
- **Sovereign WASM Write Path:** Writing is governed by the `kotoba-wasm` engine, confirming its viability not just as a client-side reader but as the core embedded state transition module for Kotodama cells.
- **Completion of Phase R2:** Completes the next logical step in the monorepo projection roadmap.

# References
- ADR-2605281700 (R0 Schema)
- ADR-2605281800 (R1 Ingest Tool)
- ADR-2606013600 (browser kotoba node — kqe-in-wasm)
- ADR-2605215000 (Murakumo-only compute boundary)
