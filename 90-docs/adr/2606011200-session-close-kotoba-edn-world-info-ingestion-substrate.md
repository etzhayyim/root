---
id: adr-2606011200-session-close-kotoba-edn-world-info-ingestion-substrate
title: "ADR-2606011200: Session close — kotodama organism kotoba-EDN world-info ingestion substrate (10-iteration maturity loop)"
status: active
doc_type: adr
topic: kotoba-edn-ingestion
authoritative: true
last_verified: 2026-06-01
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Documentation-only session-close ADR. Records the implementation + test build-out of the world-info → kotoba datomic-EDN ingestion path in the kotodama organism Python layer: legal-corpus sensor family completion (5/5) + the junkan EDN wire-format read/write + the EavtSink ingest pipeline with constitutional gates (tier-C carve-out G4/R9 + Charter Rider §2 content scan G1)."
authoritative_for:
  - session-close record for the 2026-06-01 kotoba-EDN ingestion maturity loop
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
  - adr-2605290927-junkan-societal-feedback-loop-observer
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605302300-kanae-global-fiscal-flow-visualization-tier-b-actor-r0
supersedes: []
superseded_by: []
---

# ADR-2606011200: Session close — kotodama organism kotoba-EDN world-info ingestion substrate (10-iteration maturity loop)

**Status**: active (documentation-only session-close record)
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

The originating question for this session was: *"worldmonitor.app と同様に全世界の情報を kotoba server に
datomic EDN で ingest するのはどれぐらい設計・実装されているか"* — how much of a "ingest world-wide
information into kotoba as datomic EDN" capability exists.

The pre-session audit verdict was **design ≈ 95% / implementation ≈ 27%**: the passive
sensors (geo/netreg/routing/dns/web + government + a corp scaffold), the kotoba EAVT store
(`kotoba-graph` / `kotoba-kqe`), and the `junkan` reference `DatomStore` all existed — but
there was **no EDN wire-format serializer**, **no bridge from sensor observations to datoms**,
and the **legal corpus had only 2 of 5 sensor families** implemented. The literal "datomic EDN"
spine of the user's question was missing.

A self-paced `/loop 1h 成熟度とcoverage を高めて` then ran for ten iterations, each closing the
next-highest-leverage gap in this path. This ADR records the deliverables and verification at
session close (the loop was stopped; no remaining gap is buildable without crossing into
Council-gated fleet activation — see Consequences).

# Decision

Build the world-info → kotoba-EDN ingestion path end-to-end in the kotodama organism Python
layer (`40-engine/kotoba/crates/kotoba-kotodama/py`), against the reference `junkan.DatomStore` EAVT model whose
canonical production binding is `kotoba-kqe` (ADR-2605262130 + ADR-2605312345). Scope held to
**pure / offline / test-only** code (no network, no inference, no fleet) consistent with the
junkan analysis-only discipline; the live `kotoba-kqe` transact binding and the organism-tick
wiring remain Council-gated.

Deliverables, by loop iteration:

1. **Two bug fixes.** `kaizen.StaleSensorPinRule` (R7) skipped sensors whose
   `latest_pin_created_at_ms == 0`, masking never-pinned sensors that are in fact maximally
   stale — fixed to gate only on unknown cadence. The `tick → poll_sensors` integration test
   built an `INACTIVE` organism (lifecycle R1, commit `c0d1099f5`, gates `tick()` behind
   ACTIVE/CLONED), so it asserted polling that never happened — fixed to birth the organism.
2–5. **Legal corpus completed to 5/5 sensor families** (ADR-2605262800): added test coverage
   for the previously-untested `UsUscSensor` (Statute), and implemented + tested
   `TreatyCorpusSensor` (Treaty), `ProcedureCorpusSensor` (Procedure), and
   `TemplateCorpusSensor` (Template) — each a passive `law/<bucket>/<corpus>` NDJSON sensor
   mirroring the established `JudiciaryCorpusSensor` structure (corpus→subdataset path mapping,
   deterministic G9 reservoir `hot_sample`, Tier-A, Protocol conformance). Template retains the
   FULL body (chigiri instantiates whole templates) and supports per-row jurisdiction override.
6. **`junkan/edn.py` — EDN wire format (writer) + observation→datom bridge.** `to_edn`
   (nil/bool/keyword/string+escape/int/float/vector/map/set/`#inst`, with bool-before-int and
   Keyword-before-str), `datoms_to_tx_edn` (`[[:db/add e a v] …]`, the kotoba-kqe ingest form),
   `datom_to_eavt_edn`, `entity_to_edn`, `store_to_tx_edn`, and the generic
   `datoms_from_dataclass` that maps any frozen Observation dataclass to `(e,a,v)` facts with a
   class-name-derived namespace (`LegalTreatyObservation` → `:legal.treaty/…`).
7. **`junkan/sink.py` — `EavtSink` ingest pipeline.** Assembles the primitives: stable entity
   identity from a per-family natural key (so re-pins UPDATE, not duplicate), `IngestReceipt`,
   `ingest` / `ingest_all` / `to_tx_edn`, with verified EAVT `as_of` / `history` time travel.
8. **`junkan/edn.py` — EDN reader (round-trip).** `read_edn` / `read_all_edn` / `parse_tx_edn`
   (the inverse of the writer; rejects `:db/retract` per G9 append-only) + `EdnError`, proving
   serialize→parse fidelity against the receiving (kotoba-kqe) side.
9. **Tier-C ingest gating (G4 / R9).** `EavtSink(classification=…)`; an `internal_only=True`
   observation is dropped fail-closed at an `EXTERNAL_FACING` sink and recorded as a
   `DroppedObservation` (maps 1:1 to `kaizen.LeakAttempt`), reusing the `sensors.tier_gate`
   semantics while keeping junkan fleet-independent.
10. **Charter Rider §2 content gate (G1).** Added a pure `charter_rider.scan_text` / `is_clean`
    (no file I/O / tempfile / normalizer dependency) and an INJECTED `content_scanner` hook on
    `EavtSink` that drops violating observations fail-closed and records them. Composes with the
    tier gate.

# Consequences

- The world-info → kotoba datomic-EDN path now exists and is verifiable in both directions
  against the reference EAVT store, with both constitutional gates an external-facing ingest
  needs (tier-C carve-out G4/R9 + Charter Rider §2 content scan G1), both fail-closed and
  recorded for the kaizen backstop. The session moved the answer to the originating question
  from *"design 95% / impl 27%, no EDN path"* to *"the spine is implemented and tested
  end-to-end (pure/offline) against `junkan.DatomStore`."*
- **R0 ceiling held throughout**: all new code is pure/offline/test-only. The live `kotoba-kqe`
  transact binding, the organism-tick → sink wiring, and any external publication remain
  Council-gated (junkan fleet-cell activation is gated on Bootstrap Council Seats 2-5 RFP close
  2026-06-19; ADR-2605290927). `EXTERNAL_FACING` is a code-path classification only — no datoms
  are published by this code.
- **Honest deferrals**: (a) live `kotoba-kqe` ingest of the emitted EDN is not wired (reference
  `DatomStore` only); (b) the consumer actors `danjo` (ADR-2605301600) / `kanae`
  (ADR-2605302300) remain design-only — their cross-reference / visualization methods are the
  natural next maturity target; (c) only the legal corpus is fully built — the public-data /
  gov / corp families predate this session at their prior wave levels.

## Verification

Branch `feat/social-security-for-humanity`. **253 tests pass / 0 fail** across the session's
areas (junkan EDN read/write + sink + tier-gate + content-gate, the 5 legal sensor families,
the corp/gov W1 sensor suite, organism sensors W1–W4, sensor integration, kaizen). The repo's
broader kotodama suite has 22 pre-existing collection errors in unrelated `zeebe_worker` /
NSID-validation test modules — untouched by and orthogonal to this session.

Session deliverable footprint (this ADR's commit): 2 new engine modules (`junkan/edn.py`,
`junkan/sink.py`), 3 new legal sensors (`treaty_/procedure_/template_corpus_sensor.py`), 12 new
test files (~139 new tests), and edits to `junkan/__init__.py`, `kaizen/__init__.py`,
`sensors/charter_rider.py`, `sensors/legal/__init__.py`, and the sensor-integration test.

Out of scope of this commit (surfaced, not claimed): a separate `GleifL2OwnershipSensor` corp
change (ADR-2605263800 CorpOwnership family) surfaced in the working tree during the session and
was authored elsewhere; it is left for its own commit.

# Alternatives Considered

- **Wire `EavtSink` into the live organism tick + `kotoba-kqe` this session** — rejected: crosses
  the R0/Council-gated boundary (ADR-2605290927); the pure offline pipeline is the correct R0
  deliverable.
- **Build `danjo`/`kanae` consumer methods instead of completing the sensor + EDN substrate** —
  deferred: the producer substrate (sensors + EDN bridge + gated sink) is the prerequisite the
  consumers read from; completing it first is the correct dependency order.
- **Couple `junkan` to `sensors`/`kaizen` for the gates** — rejected: junkan is constitutionally
  self-contained (analysis-only, fleet-independent); the tier + content gates are therefore
  injected (content scanner) or locally mirrored (`SinkClass` / `DroppedObservation`).

# References

- ADR-2605262130 — kotoba storage substrate unification (canonical engine; kotoba-kqe)
- ADR-2605312345 — kotoba Datom log = first-class canonical state
- ADR-2605262400 — public-data organism IPFS ingestion (sensor framework + tier ladder + G-gates)
- ADR-2605262800 — global legal-corpus ingestion (5 sensor families)
- ADR-2605290927 — junkan societal feedback-loop observer (DatomStore reference model)
- ADR-2605192200 — Charter Compliance Rider v2.0 (§2(a)..(h) scanner)
- ADR-2605301600 — danjo (downstream consumer, design-only)
- ADR-2605302300 — kanae (downstream consumer, design-only)
