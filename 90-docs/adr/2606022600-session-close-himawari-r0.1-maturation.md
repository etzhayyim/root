---
id: adr-2606022600-session-close-himawari-r0.1-maturation
title: "ADR-2606022600: Session close — himawari (向日葵) solar-PV actor R0 → R0.1 maturation + clean main-based PR"
status: active
doc_type: adr
topic: session-close-himawari-r0.1-maturation
authoritative: false
last_verified: 2026-06-02
related:
  - adr-2606021200-himawari-solar-pv-manufacturing-r0
  - adr-2606021400-tsuukan-customs-clearance-orchestration-r0
supersedes: []
superseded_by: []
---

# ADR-2606022600: Session close — himawari (向日葵) solar-PV actor R0 → R0.1 maturation + clean main-based PR

**Status**: active
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

Documentation-only closure for the session answering
*「今の actor で alibaba に出展している企業の情報をすべて収集して tsukuru と robotics に接続して、商品の購入仕入れなどはすべて繋がっている？また関税や輸送などの手続き関係のアクターはすべて定義されている? kotoba wasm に atproto actor として deploy されている?」*
followed by *「coverage, 成熟度を高めて」*.
Authoritative design = **ADR-2606021200**.

# Context

A coverage audit of the himawari actor (launched R0-scaffold in the prior session,
ADR-2606021300) found every cell was an import-time `RuntimeError` stub and the four
asked-about integration seams were ADR-prose / manifest-declaration only, not code:

- **Alibaba supplier ingestion** — not in himawari (a provisioning concern; himawari
  sources feedstock with on-chain provenance, not supplier catalogs).
- **tsukuru** — intentionally **separate** (logic-fab 9N+ EG-Si vs himawari solar-grade
  6N, N1 non-goal); robotics composition was declared but not wired.
- **Procurement (購入仕入れ)** — okaimono was live, but himawari's `supply_procurement`
  cell did not call it.
- **Customs / freight (関税・輸送)** — `open-customs-clearance` BPMN existed, but no
  standalone tariff/通関 actor and no wiring; outbound cell was a data-shaped stub on a
  non-existent namespace.
- **kotoba-WASM atproto deploy** — infrastructure proven (ADR-2605301625) but himawari
  had no deploy artifact.

# Decision

Matured himawari from R0 scaffold to **R0.1** via two multi-agent workflows
(understand → implement → integrate → verify; then an adversarial-critic-driven fix pass),
then delivered it as a **clean, main-based PR** isolated from the contended shared working
tree via a dedicated git worktree.

Shipped this session:

- **7 Pregel cells implemented** (no `RuntimeError` stubs) — polysilicon_refine (G2/N6
  XUAR/forced-labor exclusion + #custodyHop chain, fail-closed) · ingot_wafer (mass-balance
  + kerf recovery G5) · cell_process (G3 high-GWP abatement DRE ≥0.99) · module_assembly
  (G11 chain + G12 hikari-internal-only) · panel_loading (composes sarutahiko F10) ·
  outbound_logistics (real kami-autodrive VehicleClass + `com.etzhayyim.etzhayyim.apps.customsClearance`
  + funadaiku) · supply_procurement (okaimono SBT settlement + TitheRouter gross=tithe+payout
  + giemon CycloneDX→kotoba bridge). **109 tests green** via `pytest cells/ --import-mode=importlib`.
- **7 lexicons** reconciled to cell emits (recordedAt / #custodyHop / #robotSignature objects /
  loadingId) + per-cell lexicon-conformance tests.
- **kotoba-WASM atproto deploy scaffold** (`20-actors/himawari/deploy/`) — componentize-py
  component build-verified, PDS XRPC write path (ADR-2606015000), Murakumo-only inference;
  `agent.wasm` gitignored. In-WASM invoke not exercised (live node feature-gated).
- **ADR-2606021400 (tsuukan 通関係)** proposed — customs/tariff/通関 orchestrator wrapping
  the existing BPMN, consumed by himawari `outbound_logistics`; **Proposed only**, no actor
  code until Council Lv6+ ratify.

An adversarial completeness critic was run; all findings it raised (lexicon↔emit mismatches,
a prose-only outbound stub, a wrong customs namespace, a pytest import-collision) were fixed
and re-verified before merge.

# Delivery / git hygiene

- himawari R0.1 committed on the feature line as `9756f4565` (also reachable from
  `feat/himawari-r0.1`).
- A **dedicated worktree** (`feat/himawari-r0.1`) was created to decouple from the shared
  main working tree, which concurrent /loop sessions were actively mutating (one mislabeled
  commit was created and reverted during the contention; no work lost).
- A **clean, main-based** branch `feat/himawari-r0.1-pr` (commit `26b19f85e`, 46-file
  himawari-only delta vs `main`) was opened as **PR #748**. `pytest cells/` 109/109 green on
  the clean base; `e7m verify` 9/9 constitutional invariants; all lefthook gates green.

# Honest R0.1 scope

Solvers are logic-complete and tested, but **NOT operationally activated**: no
Pregel/Murakumo runtime wiring, no sim, deterministic-digest CIDs (real IPFS CIDv1 /
Base-L2 anchoring is operator-gated), HMAC module-signature stand-in for the off-cell
Ed25519 device key. Activation remains gated on the unchanged ADR-2606021200 R1 triggers
(Council Lv6+ ratify, ≥1 PV-process engineer, ≥1 LANDS brownfield parcel, G2/G3 frameworks).
A parallel session's himawari R1 benchtop design (ADR-2606022300) is tracked separately and
is out of scope for this closure.

# Consequences

- PR #748 is the preferred clean route of himawari to `main`; the feature-line himawari
  commits should be reconciled to it at merge time (avoid double-registration).
- tsuukan (ADR-2606021400) is a Proposed capability-gap ADR, not an actor; no scaffold yet.
- Future himawari work should use the dedicated worktree to avoid shared-index contention.
