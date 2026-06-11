---
id: adr-2606036000-wasm-actor-sbom-attestation-on-kotoba-deploy
title: "ADR-2606036000: WASM-actor SBOM attestation on kotoba deploy"
status: proposed
doc_type: adr
topic: wasm-actor-sbom-attestation-on-kotoba-deploy
authoritative: true
last_verified: 2026-06-03
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - wasm-actor-sbom
  - deployed-wasm-supply-chain
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605312330-giemon-part-graph-sbom-kotoba-fleet-cve-svelte
related:
  - adr-2606015600-self-certifying-did-attestation
  - adr-2606033600-sumitsubo-cleanroom-cad-interop-and-kotoba-langgraph-generative-modeling
  - adr-2605231525-no-server-key-religious-corp-architecture
supersedes: []
superseded_by: []
---

# ADR-2606036000: WASM-actor SBOM attestation on kotoba deploy

**Status**: proposed
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

> **NOTE**: ADR id `2606036000` is shared with a concurrent-session session-close ADR (`2606036000-session-close-kotoba-os-r0-r2-reference.md`) per the repo's documented parallel-agent id-race convention; filename + topic disambiguate. Tracked for the future ADR-id reconciliation.

# Context

A WASM actor deployed to a kotoba node (via `com.etzhayyim.apps.kotoba.invoke.run`
/ `block.put`) is content-addressed by its **program CID** =
`KotobaCid::from_bytes(wasm)` → `to_multibase()` — CIDv1 dag-cbor sha2-256
(`40-engine/kotoba/crates/kotoba-core/src/cid.rs`). The deploy path records:

- **what** the binary is — the program CID (`InvokeRunReq.program_cid`),
- **who** deployed it — `agent_did` (operator-auth gated), and
- — with a self-certifying did.json attestation (ADR-2606015600) — that the
  handle→CID binding is **authentic**.

It records **nothing about what the binary is made of**. A componentize-py actor
embeds a CPython interpreter + the actor's pip dependency closure
(`langgraph`, `typing_extensions`, …); a Rust actor embeds its crate closure.
None of that supply chain is captured, queryable, or CVE-matchable.

This is asymmetric with the rest of the substrate: the giemon *hardware* fleet
already has a full CycloneDX SBOM → kotoba EAVT → purl↔CVE VulnMatch pipeline
(ADR-2605312330), and there is a legacy software-stack SBOM for robot firmware.
The thing we actually *ship to a server and execute* — the wasm actor — was the
one artifact with no bill of materials. The triggering question (this session,
on the sumitsubo branch): *"今の kotoba server に deploy される wasm は SBOM は
ついている?"* — answer at the time: **no**.

# Decision

Introduce a **substrate-wide** wasm-actor SBOM mechanism, bound to the kotoba
program CID, reusing the existing CycloneDX → kotoba → VulnMatch chain with zero
changes to the matcher. Demonstrated and wired on **sumitsubo** (current
branch); applicable to every wasm actor (componentize-py *and* Rust).

1. **Generator** — `70-tools/scripts/wasm-sbom/wasm_sbom_gen.py` (stdlib-only, so
   it runs on the edge). It recomputes the **exact** kotoba program CID from the
   built wasm (CIDv1 dag-cbor sha2-256, base32lower `b…`; verified in tests
   against an independent RFC4648 base32 encoder — output `bafyrei…` matches the
   canonical IPFS CIDv1 dag-cbor prefix), and emits, **keyed by that CID**:
   - `<stem>.wasm.cdx.json` — portable CycloneDX 1.5 (ships next to the binary /
     pinnable to IPFS). `metadata.component` = the wasm itself (program CID as
     `bom-ref`, sha-256 hash, `kotoba:programCid` property); `components[]` = the
     dependency closure.
   - `<stem>.wasm.sbom.ingest.json` — a `kg.ingest_batch` body: one
     `WasmActorImage` entity (id = program CID) plus one `SbomComponent` per dep,
     each joined to the image by a `wasm/componentOf` **relation edge**.
   Two component sources: `--requirements` (Python/componentize-py, with optional
   `--freeze` for lock-resolved versions) and `--from-cdx` (re-key a
   `cargo cyclonedx` SBOM for Rust actors).

2. **Vocabulary SSoT** — `00-contracts/schemas/wasm-sbom.kotoba.edn`. Image
   claims are the `wasm/*` namespace (`programCid`, `actor`, `programType`,
   `world`, `sha256`, `byteSize`, `builtBy`, `sbomSerial`, `sbomFormat`,
   `sourcing`, `adr`). Component claims **reuse the `cdx/*` namespace** — in
   particular `cdx/purl` — which is exactly the join key
   `70-tools/scripts/sbom/purl_vuln_match.py` already scans. The binding edge is
   `wasm/componentOf` (SbomComponent → WasmActorImage).

3. **Ingest path** — `POST com.etzhayyim.apps.kotobase.kg.ingest_batch` into the
   `kotobase-kg-v1` named graph (schemaless `kg/claim/*` + `kg/relation/*`
   quads), the same KG model the giemon SBOMs use. This is **not** the
   `kotoba transact` schema path; the EDN file is a predicate reference, not a
   `:db/ident` schema.

4. **Deploy wiring** — `20-actors/sumitsubo/kotoba/deploy.sh` runs the generator
   immediately after the `componentize-py` build and, **only when `KOTOBA_TOKEN`
   is present**, ingests the body. Without a token the SBOM is written to disk
   only (dry-run-consistent with the rest of the script).

5. **Manifest** — `sumitsubo/manifest.edn` gains gate **G11
   (wasm-sbom-attestation)** and an `:actor/sbom` block recording the format,
   vocab, generator, artifacts, and CID key.

**Honesty invariants** (G7-consistent):
- A `>=` requirement yields a purl at the **lower bound** with
  `wasm:versionSource = constraint` — explicitly *not* a resolved lock. `--freeze`
  promotes deps to `lock`; only then is `--sourcing authoritative` warranted.
- The SBOM is **content-addressed and reproducible**: the CycloneDX
  `serialNumber` is derived deterministically from the program CID and **no
  wall-clock timestamp** is emitted.

**Constitutional posture**:
- **No-server-key** (ADR-2605231525): the ingest body is written by the operator
  session, never a platform-held key; the SBOM is content-addressed and
  member/operator-signed, never platform-signed.
- **Canonical state** (ADR-2605262130 / 2605312345): the SBOM lives in the Datom
  log; no RW/SQL/Lance. **Murakumo-only** is unaffected (the generator does no
  inference). **Zero invariant amendments.**

# Consequences

- A deployed wasm now answers "what is it made of?" — its dependency closure is
  first-class in the EAVT log and joins the **same** purl↔CVE VulnMatch surface
  as the giemon hardware SBOMs, with no change to `purl_vuln_match.py`.
- `?c <kg/relation/wasm/componentOf> ?img . ?img <kg/claim/wasm/programCid> "<CID>"`
  enumerates exactly the components of a specific deployed binary; a CVE on a
  pulled CID's dependency is now a query, not an audit.
- The CycloneDX artifact is portable: it can later be pinned to IPFS and
  referenced from the actor's did.json attestation (ADR-2606015600) so the
  SBOM travels with the content-addressed binary across any gateway.
- **Honest R0 scope**: the SBOM is only as complete as its inputs. Today
  componentize-py's embedded CPython interpreter and any native shared libs are
  **not** auto-enumerated — only the declared pip/cargo closure is. `>=`
  requirements are recorded as constraints, not locks, unless `--freeze` is
  supplied. There is no automatic CVE feed refresh (CVEs are seeded/ingested
  separately per ADR-2605312330). Signing the SBOM with the actor's `did:key`
  (so the manifest itself is attested, not just content-addressed) is deferred.

# Alternatives Considered

- **A new SBOM lexicon + dedicated XRPC method.** Rejected: the giemon
  CycloneDX → `kg.ingest_batch` → VulnMatch chain already exists and works;
  reusing `cdx/purl` gives vuln-matching for free. A parallel surface would
  fragment the supply-chain query model.
- **`kotoba transact` with a `:db/ident` `:wasm.sbom/*` schema.** Rejected: the
  KG/VulnMatch surface is the schemaless `kg/claim/*` model; declaring a separate
  EAVT schema would isolate the wasm SBOM from the matcher and the giemon SBOMs.
- **Server-side SBOM generation inside the kotoba node at `block.put`.**
  Rejected: the node would need the build context (requirements/lock, toolchain
  versions) it does not have, and it conflates the trustless content-address
  layer with build provenance. Generation belongs at deploy/build time; the node
  stores the result like any other datom.
- **Embed the SBOM as a custom section inside the `.wasm`.** Rejected for R0:
  changes the bytes (hence the CID) and needs a component-model custom-section
  convention; the external content-addressed artifact + EAVT binding is simpler
  and keeps the CID = the executable bytes.

# References

- `70-tools/scripts/wasm-sbom/wasm_sbom_gen.py` + `test_wasm_sbom_gen.py` + `README.md`
- `00-contracts/schemas/wasm-sbom.kotoba.edn` (vocabulary SSoT)
- `20-actors/sumitsubo/kotoba/deploy.sh` (deploy wiring) + `manifest.edn` (G11, `:actor/sbom`)
- `70-tools/scripts/sbom/{cyclonedx_to_kotoba.py,purl_vuln_match.py}` (reused chain, ADR-2605312330)
- `40-engine/kotoba/crates/kotoba-core/src/cid.rs` (`KotobaCid::from_bytes` / `to_multibase`)
- `40-engine/kotoba/crates/kotoba-server/src/{xrpc.rs (InvokeRunReq/block_put), kg.rs (kg.ingest_batch)}`
- ADR-2605312330 (giemon SBOM↔kotoba↔CVE), ADR-2606015600 (self-certifying DID attestation), ADR-2605231525 (no-server-key)
