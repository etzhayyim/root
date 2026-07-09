---
id: adr-2607090900-kotoba-lang-bpmn-canonical-engine-omg-202
title: "ADR-2607090900: kotoba-lang/bpmn (BPMN-as-edn) is the canonical BPMN engine for actor flows; SpiffWorkflow host decoupled; OMG BPMN 2.0.2 conformance scope"
status: proposed
doc_type: adr
topic: kotoba-lang-bpmn-canonical-engine
authoritative: true
last_verified: 2026-07-09
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Adopts kotoba-lang/bpmn (BPMN-as-edn .cljc, seeded by com-junkawasaki/bpmn-clj) as the canonical BPMN engine for actor procedure flows (toritsugi/ooyake first), and decouples those actors from the Python SpiffWorkflow host (50-infra/k8s/bpmn-engine-host). OMG BPMN 2.0.2 is the conformance target. No charter amendment; this is a substrate/engineering placement decision."
authoritative_for:
  - kotoba-lang/bpmn as the canonical BPMN-as-edn engine for first-party actor procedure flows
  - decoupling of toritsugi/ooyake BPMN models from the SpiffWorkflow (Python) host
  - OMG BPMN 2.0.2 as the conformance vocabulary for BPMN-as-edn node/flow types
depends_on:
  - adr-2605312030-toritsugi-government-procedure-concierge-tier-b-actor-r0
  - adr-2606021600-ooyake-world-government-atlas-tier-b-actor-r0
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605192100-etzhayyim-mission-charter
related:
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605302130-himotoki-disclosure-request-tier-b-actor-r0
supersedes: []
superseded_by: []
---

# ADR-2607090900: kotoba-lang/bpmn (BPMN-as-edn) is the canonical BPMN engine for actor flows; SpiffWorkflow host decoupled; OMG BPMN 2.0.2 conformance scope

**Status**: proposed
**Date**: 2026-07-09
**Deciders**: Jun Kawasaki

# Context

Several Tier-B actors model an end-to-end procedure as a **BPMN process** — toritsugi
(the citizen-concierge 伴走 flow) and ooyake (the government-atlas citizen-procedure
process models) are the first two. The question this ADR settles: **which BPMN engine
is the canonical home for those models, and what is the conformance vocabulary?**

Prior state (the pressure that forced this decision):

1. **ooyake** shipped three BPMN models at R0 (`resolveUnit.bpmn`, `findService.bpmn`,
   `reconcileUnit.bpmn`) under `00-contracts/bpmn/com/etzhayyim/ooyake/`, noted as
   `:model-only` with **no Zeebe engine deployed** (ADR-2606021600 §7). The
   `:gov.procedure/bpmn` field on the procedure records carried a STUB
   `bpmn.ooyake.find-service` placeholder.
2. A **Python SpiffWorkflow host** lives at `50-infra/k8s/bpmn-engine-host`
   (`engine.py`, `main.py`, `deployment.yaml`) as a cluster-side BPMN runtime candidate.
   SpiffWorkflow is a capable OSS BPMN engine, but it is a **Python process boundary**:
   it forces the actor's procedure flow out of the substrate-native Clojure/kotoba
   process group and into a separate Python pod with its own state, its own charter
   compliance surface, and a serialization seam (XML/BPMN file ↔ Python objects).
3. **`com-junkawasaki/bpmn-clj`** was authored as an early Clojure seed exploring
   BPMN-as-data. It demonstrated the shape (process = plain EDN map, nodes/flows
   id-keyed, topology from sequence-flow source/target) but was a single-org prototype,
   not a canonical, conformance-targeted kernel.

The actors are being built **substrate-native** (Clojure `.cljc` over the kotoba Datom
log, portable to JVM / ClojureScript / WASM; root CLAUDE.md §"Operational code =
clj/bb"). A Python BPMN host is the wrong process boundary for an actor whose entire
charter surface (Governor, cells, audit ledger, G-gates) is already Clojure.

# Decision

**kotoba-lang/bpmn is the canonical BPMN engine for first-party actor procedure
flows.** It is adopted as the "正位置" (canonical placement) for BPMN in this org.

Concretely:

1. **`kotoba-lang/bpmn`** — the OMG BPMN 2.0.2-conformant **BPMN-as-edn** kernel
   (`github.com/kotoba-lang/bpmn`). Every namespace is portable `.cljc` with **zero
   third-party runtime deps**, so it runs on JVM / ClojureScript / WASM (SCI). A BPMN
   process is plain EDN data you can `assoc`, `diff`, store in Datomic, or generate;
   the library adds graph queries, structural validation, XML I/O, and a pure token
   interpreter. This is the canonical home; it carries no domain process and no engine
   bindings — those remain host-injected ports (per the kotoba-lang reusable-kernel
   discipline). Referenced in this wave's planning as **`org-omg-bpmn`** (the OMG BPMN
   2.0.2 conformance scope).

2. **Seed lineage** — `kotoba-lang/bpmn` was seeded by **`com-junkawasaki/bpmn-clj`**
   (the early Clojure prototype) and re-designed canonically at kotoba-lang as a
   reusable, zero-dep, conformance-targeted contract kernel. bpmn-clj remains the
   historical seed; kotoba-lang/bpmn is the SSoT going forward. (Mirrors the
   langgraph-clj / langchain-clj pattern: a sibling kotoba-lang reusable kernel that
   actors depend on via `:local/root` for now and via published coords once stable.)

3. **SpiffWorkflow host decoupled** — toritsugi and ooyake BPMN models are **NOT**
   wired to the `50-infra/k8s/bpmn-engine-host` (Python SpiffWorkflow) pod. The
   canonical path is: BPMN-as-edn model → kotoba-lang/bpmn graph queries /
   validation / token interpreter → the actor's own langgraph-clj StateGraph drives
   execution within the substrate-native process group. The SpiffWorkflow host is left
   in place for any future Python-side need but is **not on the critical path** for
   these actors; it is not a dependency of toritsugi or ooyake.

4. **OMG BPMN 2.0.2 conformance vocabulary** — the BPMN-as-edn node-type keywords are
   restricted to the OMG BPMN 2.0.2 valid set: `:start-event` / `:end-event` /
   `:service-task` / `:user-task` / `:send-task` / `:script-task` /
   `:exclusive-gateway` / `:parallel-gateway` / `:inclusive-gateway` (the working
   subset this org's flows use). `:bpmn/id`, `:bpmn/type`, `:bpmn/name`,
   `:bpmn/source`, `:bpmn/target`, `:bpmn/condition`, `:bpmn/default`,
   `:bpmn/legal-basis`, `:bpmn/provenance` are the edn keys. This keeps the models
   round-trippable to/from OMG-standard BPMN 2.0.2 XML (the library's XML I/O) where a
   government/external counterparty ever needs the wire format.

5. **First consumers** —
   - **ooyake** `registry/gov-procedures.bpmn.edn` (6 R0 citizen-procedure process
     models; ADR-2606021600 R2) — the 公 side, consumed by toritsugi.
   - **toritsugi** `registry/toritsugi.procedure-flow.bpmn.edn` (14 nodes / 14 flows;
     ADR-2605312030 R1) — the citizen-伴走 spine, whose `mode_gw` exclusive-gateway
     encodes G15 (member-self-submit default | 代行 gated).

# Consequences

- **Positive**: the actor's BPMN model and its Governor/cell/ledger code live in ONE
  process group (Clojure over the kotoba Datom log). No Python seam, no separate pod
  state, no second charter-compliance surface. The model is plain EDN → diffable,
  testable, storable in Datomic, generatable. Portable to JVM/cljs/WASM with the rest
  of the actor. OMG BPMN 2.0.2 conformance keeps the door open to interop with
  external/standard BPMN tooling.
- **Negative / honest limits**: kotoba-lang/bpmn's token interpreter is a pure
  reference executor — it is not (and does not need to be) a distributed workflow
  engine with retries/persistence/HA. Actors that need durable long-running workflow
  state get it from their **langgraph-clj StateGraph + checkpoint + the kotoba Datom
  log** (the append-only audit ledger is the concierge genealogy), NOT from the BPMN
  interpreter. The BPMN model is the *declared process shape*; the StateGraph is the
  *executable spine*; the two are deliberately separate concerns.
- **Constitutional**: no invariant is amended. The BPMN models inherit the actor's
  charter gates structurally (toritsugi's `mode_gw` reflects G15; ooyake's
  non-fabrication G5 via verbatim legal-basis/provenance). PII handling, Murakumo-only
  inference, encrypted-envelope confidentiality all hold — they are unaffected by the
  engine choice (a substrate/engineering decision, changeable at the implementation
  layer per ADR-2606182359 lineage).

# Alternatives Considered

- **Wire the actors to the SpiffWorkflow (Python) host** — rejected: it forces a
  Python process boundary, a serialization seam, and a second charter-compliance
  surface for a flow whose Governor/cells/ledger are already Clojure. The
  substrate-native rule (clj/bb over the kotoba Datom log) is the deciding factor.
  SpiffWorkflow remains available for any future Python-side need but is not the
  canonical path.
- **Zeebe / Camunda (external BPMN engine)** — rejected for the same process-boundary
  reason, plus lock-in (ADR-2606021600 §7 already noted "no Zeebe engine deployed").
  The OMG-conformance vocabulary still lets us emit standard BPMN 2.0.2 XML if a Zeebe
  interop is ever genuinely needed.
- **Keep BPMN models as informal diagrams only (no engine)** — rejected: toritsugi's
  flow is the executable spine of the StateGraph, and ooyake's models are consumed by
  toritsugi's `resolve` step. A declared, validated, queryable model (vs. a drawing)
  is what makes the charter gates machine-verifiable (the `mode_gw` G15 test, the
  node-type valid-set restriction).
- **Stay on `com-junkawasaki/bpmn-clj`** — rejected as canonical: it was a valuable
  seed but is single-org and not conformance-targeted. Promoting the canonical design
  to `kotoba-lang/bpmn` (sibling reusable kernel) gives every actor the same
  zero-dep portable kernel without each re-deriving it.

# References

- **Runtime priority (CLAUDE.md 2026-07-10 改訂)**: kotoba-lang/bpmn と actor 側の
  `.cljc` は、app の第一 runtime を **cljs / kotoba wasm** に据える方針（JVM と bb
  は app runtime として最下位に降格）。toritsugi の現状ビルドは JVM (`deps.edn` +
  cognitect test-runner、kyoninka と同じ local/root 構造) で test するが、cljs/kotoba
  wasm 第一 runtime への移行は **follow-up ADR** として切り出す（本 ADR の範囲外）。
  bpmn-clj / langgraph-clj / langchain-clj はいずれもポータブル `.cljc` であり、
  第一 runtime の切り替えは reader-conditional と test harness の変更で到達可能。

- This ADR: `/90-docs/adr/2607090900-kotoba-lang-bpmn-canonical-engine-omg-202.md`
- Canonical engine: `orgs/kotoba-lang/bpmn` (`github.com/kotoba-lang/bpmn`)
- Seed: `orgs/com-junkawasaki/bpmn-clj` (historical prototype, superseded as canonical)
- Decoupled host: `50-infra/k8s/bpmn-engine-host` (Python SpiffWorkflow; not on the toritsugi/ooyake critical path)
- ADR-2605312030 (toritsugi — first consumer; R1 technical build)
- ADR-2606021600 (ooyake — 公 side BPMN models; R2 technical build)
- ADR-2605262130 (kotoba storage substrate unification)
- OMG BPMN 2.0.2 (formal/2013-12-09; ISO/IEC 19510:2013) — the conformance vocabulary source
