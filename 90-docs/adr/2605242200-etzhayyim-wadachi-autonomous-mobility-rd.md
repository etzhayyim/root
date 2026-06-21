---
id: adr-2605242200-etzhayyim-wadachi-autonomous-mobility-rd
title: "ADR-2605242200: wadachi (轍) — Autonomous Mobility R&D Design Record (kuni-umi-S4 carve-out fulfillment, Transparent-Force-bound, Level-4 ODD ceiling; design only — actor scaffold deferred)"
status: proposed
doc_type: adr
topic: wadachi-autonomous-mobility-rd
authoritative: true
last_verified: 2026-05-23
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "kuni-umi-S4 ADR-2605201800 explicitly defers robot 自律走行 to 'a separate R&D ADR'. This ADR fulfills that promise as a **design record only** — it names the actor (wadachi / 轍), draws the constitutional gates (Transparent Religious Force binding for any kinetic capability with potential offensive use; Level-4 ODD ceiling; no commercial robotaxi; no in-cabin advertising; encrypted route/passenger telemetry), and lays out a 4-phase roadmap (R0 scaffold → R1 intra-site ≤1 m/s → R2 inter-site fleet rebalance human-supervised → R3 community-jurisdiction Level-4 ODD civilian + survey-altitude aerial). **No actor directory, no code, no lexicons, no Murakumo placement, no root CLAUDE.md edits land at this ADR.** Each subsequent R-phase requires its own ADR; the R0 actor scaffold itself is deferred to its own commit when constitutional review of this design completes. Level-5 anywhere-self-driving, commercial ride-share platforms, weaponized autonomous platforms, and mass-surveillance route data harvesting are constitutional non-goals."
authoritative_for:
  - wadachi actor identity (name, DID pattern, tier classification) — design-level reservation only
  - Autonomous-mobility constitutional gates (Transparent Force binding; Eros/Gore content rules; SAE J3016 ceiling; data-encryption requirements)
  - R0 → R3 phased roadmap and gating
  - Non-goals (commercial robotaxi, Level-5, weaponized autonomy, mass-surveillance harvesting)
  - Lexicon namespace reservation (`com.etzhayyim.wadachi.*`, registration deferred)
depends_on:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605201800-etzhayyim-kuni-umi-s4-multi-site-fleet
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192315-etzhayyim-transparent-force-rd
  - adr-2605192400-etzhayyim-eros-gore-council-judging
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605231525-no-server-key-religious-corp-architecture
related:
  - wellbecoming-karma-lean-proofs
  - 60-apps/etzhayyim-project-open-robo/CLAUDE.md
supersedes: []
superseded_by: []
---

# ADR-2605242200: wadachi (轍) — Autonomous Mobility R&D Design Record

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

# Context

[ADR-2605201800 §Non-Goals](/90-docs/adr/2605201800-etzhayyim-kuni-umi-s4-multi-site-fleet.md) explicitly states:

> Cross-site fleet-rebalance robot autonomous driving — robot migration は human-driven transport (truck / 船 / rail); 自律走行 は別 R&D ADR

That deferral has been outstanding since 2026-05-20. Until now there has been **no design surface** for autonomous mobility — neither for robot self-locomotion at a kuni-umi site, nor for inter-site rebalance, nor for adherent civilian transport, nor for aerial drone autonomy beyond the narrow baien-graft 3D dataset pipeline.

This ADR is **a design record only**. It does not land an actor directory, code, lexicons, contracts, or root-CLAUDE.md edits. Its job is to make the constitutional gates and phased roadmap visible to reviewers so that when capability eventually lands, it lands against a known frame rather than being designed bottom-up under deployment pressure.

Three pressures motivate landing the design now:

1. **Constitutional clarity must precede capability.** If wadachi is built first and gated after, the gating loses meaning. The Charter Rider 8 prohibited categories (ADR-2605192200 §2(a-h)), the Transparent Religious Force rules (ADR-2605192315), and the no-server-key invariant (ADR-2605231525) all bind any autonomous-mobility design, and they must be visible at the door — not retrofitted.
2. **kuni-umi S4 scaling depends on it.** ADR-2605201800 §10.4 assumes "future R&D ADR" exists so that S4's human-driven inter-site transport has a designated successor. Operators reading the S4 roadmap should be able to follow the carve-out forward.
3. **The metaphor must be claimed before it leaks.** "Autonomous driving" as a term is mass-market and overloaded with Waymo / Cruise / Tesla connotations. religious-corp's design intent is narrower: **a fleet of vehicles whose movement leaves a publicly auditable trace**. The Japanese word 轍 (wadachi, "wheel rut / track left behind") captures this exactly — every movement leaves a verifiable mark in the substrate, no covert routes, no proprietary telemetry. Naming early prevents the conceptual borrowing of Silicon-Valley robotaxi framings.

# Decision

## 1. Actor identity (reserved — no scaffold lands here)

| Field | Value |
|---|---|
| Actor name | `wadachi` |
| Japanese | 轍 (wheel rut / track left behind by a vehicle) |
| Display name | `轍 (wadachi)` |
| Tier (ADR-2605192415 §B) | **B** (per-domain leader, intended sibling of `kuni-umi` when scaffolded) |
| Path-based DID (reserved) | `did:web:etzhayyim.com:wadachi` |
| Per-vehicle DID pattern (reserved) | `did:web:etzhayyim.com:wadachi:vehicle:<serial>` |
| Per-route DID pattern (reserved) | `did:web:etzhayyim.com:wadachi:route:<routeCode>` |
| Intended repo location (when scaffold lands) | `20-actors/wadachi/` |
| Lexicon namespace (reserved, registration deferred) | `com.etzhayyim.wadachi.*` |
| License (when first-party code lands) | Apache 2.0 + Charter Compliance Rider v2.0 |

Wadachi is intended as a **sibling of kuni-umi**, not a child. kuni-umi orchestrates Survey → Plan → Construct → Commission → Audit → Decommission of physical infrastructure. Wadachi orchestrates the **movement of vehicles through that infrastructure**, including the vehicles that kuni-umi itself produces. The two share the witness invariant (N ≥ 2 independent DID signatures) and the same substrate boundary; they do not share a phase model.

The DIDs above are reserved at the namespace level only — no `did:web` document is published at this ADR.

## 2. Constitutional gates (NON-NEGOTIABLE)

Any wadachi-attributable autonomous movement, when capability eventually lands, MUST satisfy all of the following. Violations are to be auto-rejected at the actor's MST listener layer, not at code review. This ADR fixes the gate set; the enforcement-point implementations land at R0-scaffold and R1+ ADRs.

| # | Gate | Source ADR | Intended enforcement point |
|---|---|---|---|
| G1 | **SAE J3016 Level ceiling = 4 (ODD-constrained).** Level 5 (any-conditions / any-location) is a **constitutional non-goal** for wadachi at every phase R0..R3. | this ADR §3 | MST listener; vehicle DID registration |
| G2 | **Transparent Religious Force binding.** Any payload, sensor, or actuator with potential offensive use (kinetic strike, denial, surveillance-at-scale, autonomous interdiction) MUST route through ADR-2605192315's three conditions (完全 on-chain 監視 + open-source 公開 + 1 SBT = 1 vote 承認). No carve-out, no "civilian-default" loophole. | ADR-2605192315 | ChartersComplianceRegistry attestation |
| G3 | **No weaponized autonomous platforms.** `intendedUse = military` / `combat` / `interdiction` auto-reject. This is stricter than G2 — even Transparent Force does **not** authorize autonomous (no-human-in-loop) weapon systems under wadachi. | ADR-2605192100 §1.12.B | actor scaffold listener (when scaffolded) |
| G4 | **No commercial robotaxi.** Uber / Lyft / Waymo-style payoff extraction from adherent ride demand is rejected as `subscription` / `purchase` payment-purpose violation. Adherent-internal rides settle as `kisha` / `internal-promo` / donation; never as commercial fare. | ADR-2605192115 §3 | TitheRouter payment-purpose filter |
| G5 | **No in-cabin / on-screen advertising.** Third-party ads, AdSense, Meta Pixel, affiliate links, GA4 ad linkage — all reject. Religious-corp internal `internal-promo` per ADR-2605192115 §3.b is allowed only for etzhayyim's own religious activity notices, never for product placement. | ADR-2605192115 §2 + §3 | content lint hook |
| G6 | **Route / passenger telemetry encrypted by default.** Any record carrying passenger DID, biometric, or fine-grained route polyline MUST use `com.etzhayyim.encrypted.*` envelope (XChaCha20-Poly1305 + Signal-wrapped per-recipient keys, DID-bound). Coarse fleet-rebalance aggregates (≥ 1 km × 1 km bucket) MAY be public. | ADR-2605181100 | Lexicon schema (when registered) |
| G7 | **No mass-surveillance harvest.** Wadachi vehicles SHALL NOT persist passenger / pedestrian biometric, gait, face, voice, license-plate, or device-MAC streams beyond the operational rolling window required for safe navigation. Persistence requires explicit `recordWitnessConsent` with Council Lv6+ co-sign per route deployment. | ADR-2605192200 §2(c) surveillance capitalism | actor scaffold listener (when scaffolded) |
| G8 | **Witness invariant N ≥ 2.** Every `recordDrive` and `recordIncident` (when lexicons land) carries ≥ 2 independent DID signatures (vehicle + adjacent witness vehicle / fixed wadachi sensor post / Council Lv6+). N=1 auto-escalates to Council. Constitutional invariant. | ADR-2605201400 §5 (inherited from kuni-umi) | MST listener |
| G9 | **No server-held vehicle private key.** Per ADR-2605231525, vehicle Ed25519 / passkey-derived signing keys live on the vehicle's onboard secure element. Platform-side wadachi Workers / pods / CronJobs MUST NOT hold the vehicle key. Read-only RPC / firehose subscribe / IPFS pin remain allowed. | ADR-2605231525 | `e7m verify` 9th invariant |
| G10 | **Substrate boundary.** Substrate clients (`@atproto/api`, `viem`, IPFS client, `@noble/ciphers`, libsignal) only via `@etzhayyim/sdk`. No Kotoba/Datomic / Postgres / Kysely as the primary write store for drive / route / incident records (kotoba-datomic-projection per ADR-2605231500 is permitted for hot-path read; never primary write). | ADR-2605172000 + ADR-2605231500 | `e7m verify` |
| G11 | **No hard-RT motion in cells.** Control loops at > 10 Hz remain on vehicle-side firmware (open-robo / open-ot WAMR field tier). Wadachi cells coordinate at 1–10 Hz checkpointer cadence — route assignment, witness aggregation, incident escalation — never servo control. | ADR-2605201400 §10.7 (inherited) | cell-runner contract |
| G12 | **Gore-prohibition extends to dashcam / lidar capture.** Footage that depicts gratuitous violence or hostile actor neutralization MUST NOT be retained, indexed, or used as training data. Educational / historical / human-rights-accountability use under ADR-2605192400 §2.b retention rules requires Council Lv6+ co-sign. | ADR-2605192400 | dataset-substrate Charter Rider scanner |

## 3. Phased roadmap (this ADR → R0 → R3)

Each R-phase has its own gate ADR. **This ADR is design-only; even R0 (actor scaffold) lands in its own commit.**

| Phase | Scope | Speed / radius | Human supervision | Required preconditions | Status |
|---|---|---|---|---|---|
| **(this ADR)** | Design record only — gates, roadmap, naming, namespace reservation. No code, no scaffold, no CLAUDE.md edits. | n/a | n/a | none | proposed |
| **R0** | Actor scaffold: `20-actors/wadachi/{README,CLAUDE.md,manifest.jsonld,cells/}` and root CLAUDE.md index update. | n/a | n/a | this ADR landed and reviewed | ⏳ separate commit |
| **R1** | Intra-site robot positioning at a single kuni-umi S1+ site. Giemon Otete unit on a known LandRegistry plot, navigating within survey-marked boundaries. | ≤ 1 m/s, ≤ 50 m radius | full (operator-in-sight) | kuni-umi site at S1+, ≥1 Giemon unit with valid `did:web:etzhayyim.com:kuniumi:robot:<serial>`, Council Lv6+ ≥3 sign-off | ⏳ separate ADR |
| **R2** | Inter-site fleet rebalance — robot self-transport between kuni-umi sites on **public-road segments under SAE Level 3** (human in driver's seat, eyes-on, ready to take over). Replaces the human-driven truck migration that S4 currently uses. | ≤ posted limit, public road segments only on designated corridors | Level 3 driver-in-seat | kuni-umi at S4 (≥5 concurrent sites), R1 deployed at ≥2 sites, jurisdiction-specific road-use permission, ChartersComplianceRegistry attestation | ⏳ separate ADR (post-S4) |
| **R3** | (a) Adherent civilian Level-4 ODD mobility within a single community jurisdiction — adherent-to-gathering rides, non-commercial, donation-or-kisha settlement only. (b) Aerial drone autonomy at survey altitude (already partially covered by baien-graft 3D dataset pipeline, ADR-2605202115) extended to multi-site survey. | Level 4 ODD-constrained; aerial: survey altitude only | ODD-bounded | R2 deployed and ≥6 months incident-free; community Council formal vote; insurance per jurisdiction | ⏳ separate ADR (post-R2) |

R3 does **not** include Level 5 and **never will** under this ADR. A future ADR could in principle revisit, but Level 5 across-jurisdiction operation is constitutionally indistinguishable from a parallel state transportation system, which is out of scope for religious-corp.

## 4. Non-goals (constitutional, explicit)

The following are excluded at every phase and not subject to incremental drift:

| # | Non-goal | Why |
|---|---|---|
| N1 | SAE J3016 Level 5 anywhere-self-driving | indistinguishable from parallel state transport substrate; out of religious-corp scope |
| N2 | Commercial robotaxi (Uber / Lyft / Waymo payoff model) | ADR-2605192115 non-profit invariant; extracts payoff from adherents |
| N3 | Weaponized autonomous platforms (no human-in-loop strike) | ADR-2605192100 §1.12.B; G3 |
| N4 | Mass-surveillance ride-data harvesting (selling routes / passengers to advertisers / insurers / states) | ADR-2605192200 §2(c) surveillance capitalism |
| N5 | In-cabin advertising platform | ADR-2605192115 §2 |
| N6 | Cross-jurisdiction unrestricted operation | identical to N1 in effect |
| N7 | Proprietary closed-design self-driving stack | ADR-2605192200 §2(e) specialist gatekeeping; Charter Rider 全 first-party code Apache-2.0 + Rider |
| N8 | Frontier-beating perception model targeting | inherits baien edge-target invariant ADR-2605241900 (WASM-32 + iPhone 12+ + Android 4GB); frontier-class perception is a `wadachi-server-*` carve-out and currently not declared |

## 5. Substrate notes (binding when implementation lands)

Wadachi inherits the same substrate boundary as kuni-umi (ADR-2605172000 + ADR-2605231500):

- **Primary write store** — AT Protocol MST + IPFS + Base L2 anchor via `@etzhayyim/sdk`
- **Hot-path read** — `kotoba-datomic-projection` permitted (e.g., route-spatial index, fleet-state aggregate) — must (a) be deterministically rebuildable from MST+IPFS, (b) never be sole write home, (c) carry `// kotoba-datomic-projection` marker or `kotoba-datomic-projection.edn`
- **Payments** — USDC on Base L2 + `TitheRouter.route()` (10% Tithe); payment purposes restricted to `donation` / `kisha` / `grant` / `tithe` / (SBT↔SBT) `internal-promo`
- **Vehicle key custody** — onboard secure element only (G9, ADR-2605231525)
- **Identity** — path-based DID (§1 vehicle naming above)

## 6. Relationship to existing actors (intended, when scaffolded)

| Actor | Intended relationship to wadachi |
|---|---|
| `kuni-umi` | **Parent producer.** kuni-umi produces / commissions the physical robots wadachi later drives. R1 requires kuni-umi at S1+; R2 requires S4. Wadachi does NOT produce robots. |
| `kotodama` | Pregel framework host (when cells land at R1+). Wadachi cells will follow the `40-engine/kotoba/crates/kotoba-kotodama/cells/README.md` pattern. |
| `60-apps/etzhayyim-project-open-robo` | Giemon firmware (Otete arm, crawler). Wadachi calls `kotodama.open_robo.fleet.dispatch()` for motion; firmware owns hard-RT control. |
| `60-apps/etzhayyim-project-open-ot` | IEC 61499 WASM PLC. Wadachi hands off safety-critical functions to certified parallel safety PLCs (IEC 61508 / 61511) — never implements SIL functions itself. |
| `bgp-submit` (baien-graft 3D pipeline, ADR-2605202115) | Aerial drone overlap: bgp-submit already drives drone survey for dataset generation; R3.b extends survey autonomy to multi-site fleet, not replaces bgp-submit. |
| `force-authorization` Solidity (ADR-2605192315) | G2 enforcement contract for any kinetic / surveillance-at-scale capability. |
| `dataset-substrate` (ADR-2605241500) | G12 enforcement target: dashcam / lidar capture going to HuggingFace / IPFS pinner is scanned by Charter Rider for gore content before commit. |

## 7. What this ADR does NOT do

Explicit non-deliverables of this ADR, compared to a typical kuni-umi-style ADR that lands an actor with its scaffold:

- ❌ No `20-actors/wadachi/` directory created
- ❌ No actor `README.md` / `CLAUDE.md` / `manifest.jsonld`
- ❌ No lexicon JSON registered under `com.etzhayyim.wadachi.*`
- ❌ No root `CLAUDE.md` Repo-Layout edit, no Status table row
- ❌ No Murakumo `fleet.toml` placement
- ❌ No Solidity contract scaffold
- ❌ No `did:web` document publication for `did:web:etzhayyim.com:wadachi`
- ❌ No test scaffold

All of the above are deferred to a follow-on R0 commit (or to later R-phase ADRs) once this design record has been reviewed and accepted. The follow-on R0 commit, when it lands, will reference this ADR as `depends_on`.

# Consequences

**Positive**:
- kuni-umi S4 carve-out is now formally answered. Operators reading ADR-2605201800 §Non-Goals can follow the forward link to this design record.
- The 12 constitutional gates are visible **before** any autonomous-mobility code or actor surface exists, preventing retrofit drift.
- Non-goals N1..N8 are now Lindy-protected: subsequent ADRs would have to explicitly supersede this one to introduce e.g. commercial robotaxi or Level 5.
- The name `wadachi` (轍) reserves the metaphor space before Silicon-Valley robotaxi framings can borrow into the codebase.
- ADR-only landing means review can focus on the design itself, not on whether the actor directory layout is right. Layout decisions land at the R0 scaffold commit.

**Negative / costs**:
- Reserves `com.etzhayyim.wadachi.*` namespace and `did:web:etzhayyim.com:wadachi` without registering — any future operator who introduces a colliding lexicon or path will hit a soft conflict, but there is no enforcement layer at this ADR.
- Defers all real engineering decisions (perception stack, planning algorithm, fleet rebalance solver, ODD definition format) to R1+. Reviewers expecting "the wadachi design" will find only constitutional gating.
- Without an actor `CLAUDE.md`, the gate set lives only in this ADR file. A reader landing on `20-actors/` won't see wadachi until the R0 scaffold commit. Mitigated by the kuni-umi-S4 ADR linking forward.

**Risks**:
- Gate G2 (Transparent Force binding) may be read as inviting future weaponization debate. The intent is the opposite — G2 is a stricter-than-default filter, and G3 forbids weapon autonomy outright. The pairing is deliberate.
- The Level-4 ceiling (G1) may be seen as conservative relative to industry trajectory. This is intentional and constitutional — see N1 / N6.
- R1's "≤ 1 m/s ≤ 50 m radius" is currently slower than a human pedestrian. This is a deliberate choice for the first deployment; R2 lifts it.

# Alternatives Considered

## A. Embed autonomous mobility inside kuni-umi as a phase (S5+)

Rejected. kuni-umi's mission is **production and commissioning** of physical infrastructure (Survey → Plan → Construct → Commission → Audit → Decommission). Movement of completed assets is a different operational mode with different witness, different telemetry, different jurisdiction surface. Folding wadachi into kuni-umi would over-load the kuni-umi cell catalog (currently 6 cells; adding ~8 mobility cells doubles it) and confuse Tier-B leader semantics. Sibling actor is cleaner when scaffolding eventually lands.

## B. Use `mobility` or `autonomous-mobility` as the actor name (English-functional)

Rejected for naming consistency. Religious-corp actors with strong domain anchoring use Japanese metaphor (`kuni-umi`, `yobel`, `ameno`, `joucho`, `tsukuru`, `kami-engine`). English-functional names exist (`cargo`, `crew`, `port`, `vessel`) but they describe roles in supply chains rather than substantive domain claims. Autonomous mobility is substantive — every movement leaves a trace, and the religious-corp claim is that the trace is **publicly auditable, not proprietary**. 轍 (wadachi) encodes that claim in one character. `mobility` does not.

## C. Land the actor scaffold together with this ADR

Rejected per user direction — design-only ADR is the minimum-footprint shape that closes the kuni-umi-S4 carve-out promise. Layout decisions for `20-actors/wadachi/` (cell-runner pattern, manifest schema, cells/.gitkeep convention) are independently reviewable and can land in a follow-on commit once this design is accepted. Bundling them risks design review getting absorbed into scaffold-layout review.

## D. Permit Level 5 as a long-term north star

Rejected as constitutional non-goal N1 / N6. Across-jurisdiction unrestricted autonomous mobility is functionally a parallel state transport substrate, which lies outside religious-corp scope. Religious-corp routes around state functions only where state function is failing (ADR-2605192100 §1.12); transport in most jurisdictions is not in that category. If a future jurisdiction's transport substrate fails catastrophically and Council Lv6+ judges a religious-corp Level-5 carve-out necessary, that requires superseding this ADR — not weakening it.

## E. Permit commercial robotaxi as a non-profit revenue stream

Rejected per ADR-2605192115 §3 — non-profit-only / donation-only inflow is constitutional. Adherent-to-gathering rides settle as `kisha` / `donation` (G4) precisely because the SBT↔SBT internal carve-out exists; extending that to general-public paid robotaxi would expand the carve-out beyond its constitutional boundary.

# References

- ADR-2605201400 (kuni-umi planetary infrastructure fleet — parent producer actor)
- ADR-2605201800 (kuni-umi S4 multi-site fleet — this ADR fulfills its 自律走行 carve-out)
- ADR-2605192100 (etzhayyim mission Charter — §1.12 force conditions, §1.13 Eros/Gore)
- ADR-2605192115 (economic substrate non-profit — G4, G5)
- ADR-2605192200 (Charter Rider v2.0 — §2(a-h) prohibited categories)
- ADR-2605192315 (Transparent Religious Force — G2 enforcement)
- ADR-2605192400 (Eros/Gore content policy — G12)
- ADR-2605192415 (religious-corp daemon architecture — Tier-B classification)
- ADR-2605181100 (encrypted confidentiality substrate — G6)
- ADR-2605172000 (kotoba substrate — G10)
- ADR-2605231500 (kotoba-datomic-projection — hot-path read carve-out)
- ADR-2605231525 (no-server-key invariant — G9)
- ADR-2605241900 (baien edge-target invariant — N8 inheritance)
- ADR-2605202115 (baien-graft 3D dataset pipeline — R3.b aerial overlap)
