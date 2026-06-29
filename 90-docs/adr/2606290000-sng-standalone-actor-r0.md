---
id: adr-2606290000-sng-standalone-actor-r0
title: "com-etzhayyim-sng — promote e-methane (Sabatier SNG) from a hikari path-reserved cell to a standalone Tier-B actor (R0)"
status: accepted
doc_type: adr
topic: sng-standalone-actor
authoritative: true
last_verified: 2026-06-29
priority: 6.2
axis: constitutional
weight: 0.62
priority_note: "Promotes the Sabatier SNG pathway evaluated in ADR-2605265900 (CONDITIONALLY PERMITTED, green H₂ + DAC CO₂, combined biomethane+SNG ≤200 Nm³/day R3) from a path-reserved cell under the hikari energy actor to its own standalone Tier-B actor repo com-etzhayyim-sng, following the kamado precedent (D-gate sub-ADR → standalone actor). Implementation shape: langgraph-clj StateGraph + independent CarbonGovernor + append-only batch-genealogy ledger (kyoninka pattern, 5th instance of the workspace actor pattern). Lexicons re-namespaced com.etzhayyim.hikari.* → com.etzhayyim.sng.*."
authoritative_for:
  - "com-etzhayyim-sng actor identity and repo-premise registration"
  - "Sabatier SNG CarbonGovernor hard invariants (closed-loop carbon / open catalyst / cap / leak / storage / mass-balance / high-temp-council / no-actuation)"
  - "SNG lexicon namespace com.etzhayyim.sng.*"
depends_on:
  - adr-2605265900-sng-methanation-sabatier-d-gate-evaluation-r0
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605263600-hydrogen-economy-d-gate-evaluation-r0
  - adr-2605264600-direct-air-capture-d-gate-evaluation-r0
  - adr-2605263800-biomethane-d-gate-evaluation-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605265900-sng-methanation-sabatier-d-gate-evaluation-r0
  - adr-2605264700-methanol-dme-synfuel-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2606290000: com-etzhayyim-sng — standalone e-methane actor (R0)

**Status**: accepted (R0 scaffold; ADR-2605265900 Council ratification still pending)
**Date**: 2026-06-29
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

## Context

ADR-2605265900 evaluates Sabatier methanation (CO₂ + 4 H₂ → CH₄ + 2 H₂O over
Ni/γ-Al₂O₃, 250–400 °C) as a closed-loop synfuel pathway and conditions it
**CONDITIONALLY PERMITTED** pending Council ratification, with a combined
biomethane+SNG ≤ 200 Nm³/day cap (R3), an open Ni/γ-Al₂O₃ catalyst mandate
(proprietary catalysts PROHIBITED), a green-H₂ + DAC-CO₂-only feedstock chain
(commercial-CO₂ ABSOLUTELY PROHIBITED), a ≤ 1 % leak rate, and a Council
Lv6+≥3 quarterly pathway-selection review. That ADR path-reserved the
implementation as a cell under the `hikari` energy actor
(`20-actors/hikari/cells/sng_sabatier/`, lexicons `com.etzhayyim.hikari.*`).
The cell was never scaffolded and SNG does not appear anywhere in hikari's
tree.

A methanation operation is a liability-bearing carbon-discipline decision
across many batches, facilities and Council seats — wider than a single
energy cell. The `kamado` actor already established the precedent of
promoting a D-gate sub-ADR pathway to its own Tier-B actor (kamado's G1 gate
cites the parent ADR-2605263500 D3 directly). We follow that precedent for
SNG.

## Decision

Promote SNG to a **standalone Tier-B actor `com-etzhayyim-sng`** — the fifth
instance of the workspace actor pattern (after robotaxi-actor /
gftd-talent-actor / ai-gftd-itonami / com-etzhayyim-kyoninka), not a hikari
cell. The repo is registered in the west manifest at
`orgs/etzhayyim/com-etzhayyim-sng` (remote `etzhayyim`, pin == repo HEAD).

### Implementation shape (kyoninka pattern)

- **langgraph-clj StateGraph**, 1 run = 1 operation; `interrupt-before
  #{:request-approval}` for the Council Lv6+≥3 pathway-selection signoff.
- **Containment + independent governor + immutable ledger**: the synthesis
  advisor (synth-LLM) is sealed into one node and returns proposals only;
  an independent **CarbonGovernor** censors every proposal against the ADR's
  hard carbon invariants; every commit/hold/record appends to an append-only
  batch-genealogy ledger (H₂ CID → CO₂ CID → catalyst lot → CH₄ batch →
  attestation).
- **Three injection seams**: Store (`MemStore` ‖ `DatomicStore` via
  langchain.db `:db-api`), Advisor (mock ‖ real `langchain.model`), Phase
  (R0→R3). `MemStore ≡ DatomicStore` contract-enforced.
- **deps.edn** with `langgraph-clj :local/root` + `:dev` langchain-clj
  override, `:run`/`:test`/`:lint` aliases (identical to kyoninka).
- **No** manifest.edn / cells / kotoba / py tree (kyoninka is a plain CLJ
  project; the carbon rulebook is data in `sng.store/demo-data`, the gates
  are code in `sng.governor`).

### CarbonGovernor hard invariants (ADR-2605265900 D1–D5 + §1/§2)

1. facility recognized · 2. closed-loop carbon only (commercial-CO₂
   ABSOLUTELY PROHIBITED) · 3. open Ni/γ-Al₂O₃ catalyst (proprietary
   PROHIBITED) · 4. aggregate cap ≤ 200 Nm³/day (combined biomethane+SNG) ·
   5. leak ≤ 1 % with quarterly OGI · 6. storage ≤ 500 Nm³/parcel and
   ≤ 2,000 aggregate · 7. mass-balance ≥ 95 % · 8. op-temp > 350 °C needs
   council-level ≥ 6 · 9. no-actuation (`:effect :assessment`). Soft:
   confidence floor → escalate; `:pathway/select` is always high-stakes →
   Council Lv6+≥3 signoff.

### Lexicon re-namespace

The four SNG lexicons ADR-2605265900 §6 pre-declared under
`com.etzhayyim.hikari.*` move to `com.etzhayyim.sng.*`:
`sngBatchAttestation`, `sngStorageInventory`, `sngPathwaySelectionRecord`,
`silenSngReview` — matching the kamado pattern (`com.etzhayyim.kamado`).
ADR-2605265900 §6 is amended accordingly (the `hikari` namespace was never
materialized, so there are no existing references to migrate).

## Consequences

- The hikari cell reservation (`20-actors/hikari/cells/sng_sabatier/`) is
  **withdrawn**; SNG lives in its own repo. hikari's 5 energy cells are
  unchanged.
- A clean batch auto-attests in phase 3 (the CarbonGovernor is the
  guarantee); a deficient batch is held with the exact violated rules in the
  ledger, unoverridable by a human (you cannot approve past commercial-CO₂ or
  a proprietary catalyst or an exceeded cap).
- A pathway selection never auto-approves — it interrupts for a named
  Council Lv6+≥3 signoff (founder seat until the Council is seated).
- The synth-LLM can be upgraded without touching the carbon guarantees; the
  guarantees live in the CarbonGovernor and the data.

## Follow-ups

- **RAD identity journal** (`80-data/kotoba-rad/sng.identity.journal.edn`):
  requires the kotoba/IPFS signing tooling to produce a real `:rad/head`
  bafkrei signature CID (the same artifact every existing RAD journal
  carries). Deferred on the same basis kyoninka defers its RAD journal — a
  langgraph-clj actor does not block on RAD; the actor's did:web
  (`did:web:etzhayyim.github.io:com-etzhayyim-sng` → migrated
  `did:web:etzhayyim.com:actor:sng`) is asserted once the signing seat is
  available.
- Curate the per-facility chain-of-custody (green-H₂ CID / DAC-CO₂ CID / Ni
  catalyst lot provenance) with the catalysis-chemist Council seat once
  ADR-2605265900 is ratified and R1 (≥1 catalysis-chemist on Council) is met.
- Optional sovereign ledger on kotoba-server (kotobase.net): give the actor
  its own Ed25519 identity (`.sng/identity.edn`, gitignored) and bind the
  store to `langchain.kotoba-db`, per `ai-gftd-itonami/src/itonami/cacao.clj`.
