---
id: adr-2606021400
title: "ADR-2606021400: 通関係 (つうかんがかり / tsuukan) — Customs/Tariff/通関 Clearance Orchestration Tier-B Actor R0 (Capability-Gap Resolution)"
status: proposed
doc_type: adr
topic: tsuukan-customs-clearance-orchestration
authoritative: true
last_verified: 2026-06-02
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - customs/tariff/通関 clearance orchestration capability-gap resolution (R0 decision)
  - tsuukan actor charter sketch (proposed; NOT yet scaffolded — Council-gated)
  - com.etzhayyim.customsClearing lexicon namespace reservation
related:
  - adr-2606021200-himawari-solar-pv-manufacturing-r0
  - adr-2606013400-funadaiku-zero-emission-cargo-ship-building
  - adr-2606010600-kami-autodrive-gnc-autonomy-layer
  - adr-2606012100-okaimono-provisioning-commons-actor
  - adr-2605262700-chigiri-legal-procedure-substrate
  - adr-2605312030-toritsugi-citizen-government-procedure-concierge
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606021200 (himawari — first internal consumer of clearance for cross-border PV feedstock/module logistics)
  - ADR-2606013400 (funadaiku — builds the vessel; tsuukan clears the cargo that vessel carries)
  - ADR-2605262700 (chigiri — legal-procedure substrate; UPL/customs-law boundary shared)
  - ADR-2605192100 (Mission Charter)
  - ADR-2605192200 (Charter Compliance Rider v2.0 — license invariants)
---

# ADR-2606021400: 通関係 (つうかんがかり / tsuukan) — Customs/Tariff/通関 Clearance Orchestration Tier-B Actor R0 (Capability-Gap Resolution)

**Date**: 2026-06-02
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify before any scaffold lands)

# Context

The cargo / cross-border logistics supply chain has a structural hole. Four existing
substrate elements each touch one slice of border trade, but **no actor holds
operational responsibility for the end-to-end 通関 (customs clearance) workflow**
(lodge → inspect → assess duty → release → audit).

**What exists today:**

| Element | Path | Scope | What it does NOT do |
|---|---|---|---|
| `hs` actor | `20-actors/hs/actor-manifest.jsonld` (`did:web:hs.etzhayyim.com`) | HS hierarchy (section/chapter/heading/subheading), GTIN/CPC/ISIC concordance, policy overlays (tariff_rate, restriction_summary, license_required), border-controls | Does NOT execute 通関 clearance, lodge declarations, route inspection, or compute landed-cost. It is a **taxonomy + reference** actor. |
| `port` actor | `20-actors/port/actor-manifest.jsonld` (`did:web:port.etzhayyim.com`) | 35+ ports, berths, terminals, vessel-call tracking | Does NOT handle customs declaration, duty calculation, inspection routing, or release. |
| `cargo` actor | (`did:web:cargo.etzhayyim.com`) | B/L lifecycle, manifest, container tracking, IMDG DG code | Does NOT assess tariff or lodge declarations — it is the *source* of the manifest clearance reads. |
| `okaimono` actor | `20-actors/okaimono/kotoba/schema.edn` (`:product/tariff-bps`) | Ring-2 external-catalog landed-cost roll-up | Consumes a tariff-bps *input*; does not derive it from a clearance workflow. |
| `open-customs-clearance` BPMN/lexicon | `00-contracts/bpmn/com/etzhayyim/open-customs-clearance/{lodgeDeclaration,releaseShipment}.bpmn` + `00-contracts/lexicons/com/etzhayyim/etzhayyim/apps/customsClearance/{lodgeDeclaration,releaseShipment}.json` | 2 bare procedures: lodge (hsCode, declaredValueUsd, importerLei, sanctionsScreeningVid → riskTier, requireInspection); release (inspection, dutiesPaidUsd → efficiencyTier) | Bare BPMN/lexicon **without an actor wrapper** — no manifest, no DID, no agent autonomy, no lexicon depth beyond 2 ops. |

Note: `00-contracts/lexicons/com/etzhayyim/kotoba/economy/tariff.json` is the **mKOTO
economy pricing** schema and is unrelated to import/export border tariff — it must NOT
be conflated with this work.

**The gap (concrete trigger).** himawari (ADR-2606021200) imports cross-border PV
feedstock/consumables (G2 requires first-party on-chain provenance to avoid XUAR
forced-labor polysilicon) and may export finished modules across jurisdictions to
hikari install sites. Its `supply_procurement` and `outbound_logistics` cells emit an
`com.etzhayyim.himawari.outboundManifest` (carrier DID, route, destinationSiteDid,
kami-autodrive class) but have **no clearance counterparty** — no actor to lodge the
declaration, compute landed-cost (duty + VAT + fees), route inspection, or authorize
release. The same hole blocks funadaiku-built Nagi-class voyages (the vessel exists; the
cargo aboard it cannot be cleared), and okaimono Ring-2 cross-border provisioning prices
a `:product/tariff-bps` it cannot derive from an authoritative clearance run.

This is a **genuine capability gap**, not a duplicate: none of `hs` / `port` / `cargo` /
`okaimono` carries operational responsibility for customs-authority workflows.

# Decision

**Adopt Option A: a new Tier-B actor — 通関係 (つうかんがかり / `tsuukan`)** — as the
customs-clearance **orchestrator** for maritime and cross-border cargo. This ADR is a
**Proposed charter sketch only**. No actor directory, manifest, cells, lexicon files, or
DID are created by this ADR. Scaffolding requires Council Lv6+ ratification (per the
Tier-B actor convention: ADR + manifest + cells + lex land only after vote).

**Proposed identity (subject to ratification):**

- Canonical name: `tsuukan` (通関係 / つうかんがかり, "customs-handling specialist")
- Form factor: Tier-B religious-corp actor (Pregel cells + manifest + lexicon)
- Proposed DID: `did:web:tsuukan.etzhayyim.com` (or `did:web:etzhayyim.com:tsuukan`,
  matching himawari's path-style DID — Council to choose the convention at scaffold time)
- Lexicon namespace (reserved by this ADR): **`com.etzhayyim.customsClearing`**

**One-line scope.** Customs-clearance orchestrator for maritime & cross-border cargo:
intake manifest + HS codes from `cargo.etzhayyim.com`, query tariff rates & restrictions
from `hs.etzhayyim.com`, lodge declaration, route inspection (risk-tier + sanctions),
calculate landed-cost, authorize release, feed release SLA to `port.etzhayyim.com` and
landed-cost to `okaimono.etzhayyim.com`.

**Proposed Pregel cell shape (R0 sketch — illustrative, finalized at scaffold):**

1. `manifest_intake` — subscribe `cargo`/`port` events → normalize lot + HS codes.
2. `tariff_classify` — query `hs` policy overlay (tariff_rate, restriction_summary,
   license_required) per HS code per destination jurisdiction.
3. `landed_cost` — compute duty + VAT/consumption-tax + fees per SKU/lot; emit basis-
   points roll-up consumable by okaimono `:product/tariff-bps`.
4. `declaration_lodge` — assemble declaration (port, importerLei, manifestVid, HS codes,
   declaredValueUsd, sanctionsScreeningVid) via the existing `lodgeDeclaration` BPMN.
5. `inspection_route` — risk-tier (red/yellow/green) + sanctions screening; record result.
6. `release_authorize` — record duty payment + inspection result; authorize release via
   `releaseShipment` BPMN; emit efficiencyTier (express/normal/slow/stuck) → port SLA.
7. `clearance_audit` (cross-cutting) — append-only post-clearance audit trail on the
   kotoba Datom log; tariff-schedule + jurisdiction-policy versioning provenance.

**Interfaces.**

- Inbound (subscribe): `cargo.etzhayyim.com/manifest`, `port.etzhayyim.com/vessel-call`,
  `himawari` `outboundManifest`.
- Query (XRPC): `hs.etzhayyim.com` tariff/restriction/license overlay (read-only).
- Emit (publish): `com.etzhayyim.customsClearing.declarationLodged`,
  `….releaseAuthorized`, `….landedCost` → okaimono landed-cost + port SLA.

**Substrate binding (constitutional).** Canonical state = **kotoba Datom log (EAVT
Datalog)** only. Declaration / duty / release / dispute / tariff-schedule-version records
are Datoms; reads via `kotoba-kqe` arrangements. **No RisingWave / Postgres / Kysely /
SQLite / DuckDB / Lance** as canonical or cache. Any agentic reasoning (e.g.,
classification-dispute triage) uses **Murakumo fleet only** (LiteLLM 127.0.0.1:4000 /
EVO-X2 LAN / per-node Ollama) — never RunPod / OpenAI-direct / Vertex / Bedrock / any
commercial GPU. License: **Apache 2.0 + Charter Compliance Rider v2.0** on all
first-party source/docs. Payment (duty settlement where on-chain): **USDC on Base L2 +
TitheRouter**; no Stripe/PayPal/fiat processor; no external advertising.

**Constitutional & domain gates (R0 sketch — finalized at scaffold):**

- **G1 License** — all firmware/source Apache 2.0 + Charter Rider v2.0.
- **G2 No-fee tariff lookup** — clearance reasoning consumes **public tariff data only**
  via `hs` overlay; no paywalled customs database, no per-lookup fee monetization.
- **G3 Anti-corruption** — no bribery/facilitation-payment path; every duty figure and
  release decision is an append-only Datom audit trail (kotoba), publicly reconstructible.
- **G4 Jurisdictional compliance** — declarations align with the competent customs
  authority of the destination (e.g., JP 税関 / Singapore Customs / Dutch Douane);
  tsuukan never asserts a duty/classification it cannot cite to a published schedule.
- **G5 Murakumo-only inference** — no commercial GPU; LLM inference via Murakumo fleet.
- **G6 Sanctions integrity** — sanctions screening uses verifiable on-chain VID
  (`sanctionsScreeningVid`); never silently passes an unscreened lot.

# Prohibitions (UPL / customs-law boundary)

tsuukan is an **orchestration + computation substrate**, NOT a licensed customs broker or
legal adviser. Mirroring the chigiri (ADR-2605262700) UPL boundary and the toritsugi
(ADR-2605312030) concierge boundary:

- **NOT a licensed customs broker (通関業者).** In jurisdictions where lodging a
  declaration with the authority requires a registered/licensed broker (e.g., JP 通関士
  / 通関業者 under 通関業法), tsuukan **assists and computes**; the licensed broker or the
  importer-of-record self-lodges. tsuukan does not represent itself to a customs authority
  as the responsible declarant unless a properly licensed member/operator is bound.
- **No unauthorized practice of law (UPL).** tsuukan does not give legal advice on
  classification disputes, valuation rulings, or penalty defense. It surfaces published
  rules + computed figures + citations; adjudication/representation routes to chigiri or a
  licensed professional.
- **No duty evasion / misclassification assistance.** tsuukan must not select an HS code
  or valuation to minimize duty contrary to the goods' true character; G3/G4 forbid it.
  Classification follows `hs` taxonomy honestly; ambiguity is flagged, not exploited.
- **No sanctions/export-control circumvention.** No routing designed to evade sanctions,
  embargoes, or dual-use export controls. Force-separation invariant (ADR-2605192100
  §1.12) applies: no covert/weapons-adjacent logistics.
- **No customs-authority impersonation.** tsuukan never represents itself *as* a customs
  authority; it interfaces *with* authorities as an importer-side orchestrator.

# How himawari.outbound_logistics consumes it

himawari (ADR-2606021200) is the **first internal consumer**, exercising the full chain:

1. himawari `supply_procurement` (inbound cross-border PV feedstock/consumables) and
   `outbound_logistics` (finished-module export to a foreign hikari install site) emit an
   `com.etzhayyim.himawari.outboundManifest` (carrier DID, route, **destinationSiteDid**,
   kami-autodrive/funadaiku class).
2. tsuukan `manifest_intake` subscribes that manifest (plus the `cargo` B/L + HS codes),
   `tariff_classify` queries `hs` for the destination jurisdiction's tariff/restriction/
   license overlay, and `landed_cost` computes duty + VAT + fees.
3. tsuukan `declaration_lodge` → `inspection_route` → `release_authorize` runs the
   existing `open-customs-clearance` BPMN, emitting `releaseAuthorized` + efficiencyTier.
4. himawari receives `releaseAuthorized` as the **gate** for its `outbound_logistics`
   completion (transport to the foreign hikari site proceeds only post-clearance), closing
   the loop so the energy supply chain 製造 → 積込 → 通関 → 輸送 → 設置 has no border hole.
5. okaimono Ring-2 cross-border provisioning consumes tsuukan's `landedCost` to populate
   `:product/tariff-bps` from an authoritative clearance run rather than a guessed input.

Compatibility note: tsuukan **wraps** the existing `lodgeDeclaration` / `releaseShipment`
BPMN + lexicon unchanged (no duplication); it adds the actor wrapper, manifest_intake,
tariff_classify, landed_cost, clearance_audit, and the `com.etzhayyim.customsClearing`
lexicon depth those bare procedures lack.

# Consequences

**Positive.**
- Closes the only structural border-trade hole; himawari/funadaiku/okaimono cross-border
  flows become end-to-end without ad-hoc per-actor clearance logic.
- Clean separation preserved: `hs` governs taxonomy (stable, Council-gated); tsuukan
  *executes* procedures (volatile, jurisdiction-specific) using that taxonomy.
- Reuses (does not fork) existing customs BPMN + lexicon; adds an actor + audit + landed-
  cost it lacked.

**Negative / risk.**
- Customs law is jurisdiction-specific and changes frequently; R1 must scope a
  jurisdiction-rule engine carefully (JP first, then SG / NL) and keep G4 honest.
- UPL/broker-licensing boundary is sharp and varies by country; scaffold must encode the
  licensed-declarant binding before any live lodging.
- Adds a new DID + lexicon namespace to govern (tariff-schedule + jurisdiction-policy
  versioning).

**R1 roadmap (gated, post-Council):** live duty-calculation engine; JP/SG/NL
jurisdiction rule engine; bonded-warehouse / FTZ / duty-deferral routing; post-clearance
audit + classification-dispute triage (chigiri-routed); landed-cost feedback loop to
okaimono pricing.

# Alternatives Considered

**Option B — Wire-to-existing (extend `hs`).** Rejected. `hs` is a taxonomy + policy
reference actor; embedding operational clearance would conflate stable Council-gated
taxonomy governance with volatile jurisdiction-specific operations. Same rejection
reasoning applies to extending `port` (berth/vessel ops, not duty assessment), `cargo`
(manifest custodian; would gain a contradictory "agent of customs authority" role), and
`okaimono` (member-facing provisioning; would blur member-journey from port operations).

**Option C — Leave bare BPMN as-is.** Rejected. The `open-customs-clearance` BPMN/lexicon
has no actor wrapper, DID, agent autonomy, audit trail, landed-cost, or lexicon depth;
himawari/funadaiku/okaimono cannot consume a bare procedure as a clearance counterparty.

**Naming alternatives.** `通関荷` (つうかんか) and `通関係` (つうかんがかり) were both
considered; `tsuukan` (通関係) is recommended as the canonical slug for readability and to
emphasize the *handling-specialist* (orchestrator) role over the *cargo* (に) reading.

# References

- ADR-2606021200 (himawari — solar PV mfg + outbound logistics; first consumer)
- ADR-2606013400 (funadaiku — zero-emission cargo-ship building; vessel ≠ cargo clearance)
- ADR-2606010600 (kami-autodrive GNC — outbound transport)
- ADR-2606012100 (okaimono — provisioning commons; `:product/tariff-bps` consumer)
- ADR-2605262700 (chigiri — legal-procedure substrate; shared UPL boundary)
- ADR-2605312030 (toritsugi — citizen procedure concierge; shared UPL/self-submit pattern)
- ADR-2605192100 (Mission Charter — §1.12 force-separation invariant)
- ADR-2605192200 (Charter Compliance Rider v2.0 — license invariants)
- `00-contracts/bpmn/com/etzhayyim/open-customs-clearance/{lodgeDeclaration,releaseShipment}.bpmn`
- `00-contracts/lexicons/com/etzhayyim/etzhayyim/apps/customsClearance/{lodgeDeclaration,releaseShipment}.json`
- `20-actors/hs/actor-manifest.jsonld` · `20-actors/port/actor-manifest.jsonld` · `20-actors/okaimono/kotoba/schema.edn`
