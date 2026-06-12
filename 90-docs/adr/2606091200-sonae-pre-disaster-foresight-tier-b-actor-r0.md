---
id: adr-2606091200-sonae-pre-disaster-foresight-tier-b-actor-r0
title: "ADR-2606091200: sonae (備え) — non-profit religious-corp civilian pre-disaster foresight + preparedness + early-warning substrate Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: sonae-pre-disaster-foresight-r0
authoritative: true
last_verified: 2026-06-09
priority: 6.4
axis: emergency-response
weight: 0.55
priority_note: "Closes the BEFORE half of the disaster cycle left open by kazaori (ADR-2605263200), whose lifecycle is reactive (declaration on/after event -> assessment -> supply -> review). sonae adds prevention / mitigation / preparedness / early-warning: open-feed hazard watch (USGS / PHIVOLCS / JMA / GDACS / Copernicus EMS / WMO GTS), per-community-site risk assessment, official-warning RELAY (relay-only, authoritativeSource cited), preparedness planning + stockpile pre-positioning (mizuho / mitsuho), drills, and an imminence-signal handoff to kazaori. Motivating case: 2026-06-08 Mw 7.8 offshore Sarangani (Mindanao) earthquake + tsunami. NOT response (N3, clean boundary to kazaori). NO false authority (G8 — MUST NOT originate official warnings). NO unilateral declaration (G10 — only kazaori Council Lv6+ >=4/7). NO commercial disaster-prediction software (G4). NO surveillance (G6). Murakumo-only (G7). Community-scale only (G3). 任意団体 internal substrate at did:web:sonae.etzhayyim.com (20-actors/sonae/). Etymology: 備え = preparedness (備えあれば憂いなし); what stands ready before 風折 kazaori (the wind-broken branch)."
authoritative_for:
  - sonae actor R0 charter
  - religious-corp civilian pre-disaster foresight + preparedness + early-warning substrate single SoT
  - "`com.etzhayyim.sonae.*` Lexicon namespace boundary"
  - civilian-only invariant (NOT military; force authorization separate per ADR-2605192315)
  - no-false-authority invariant (G8 — relay-only; MUST NOT originate official seismic/tsunami warnings)
  - no-unilateral-declaration invariant (G10 — emergency state owned by kazaori Council path)
  - phase-boundary invariant (N3 — sonae does NOT do response; kazaori does)
  - prohibition on commercial disaster-prediction software (One Concern / FloodFlash / Jupiter Intelligence / RMS / Tomorrow.io enterprise / Everbridge / OnSolve / AlertMedia)
  - prohibition on surveillance-based monitoring (open feeds + opt-in self-report only)
  - Sendai Framework + Sphere Standards reference (NOT membership)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605192315-etzhayyim-transparent-force-rd
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605261015-mitsuho-food-agriculture-tier-b-actor-r0
  - adr-2605261030-hagukumi-care-tier-b-actor-r0
  - adr-2605261100-hikari-energy-tier-b-actor-r0
  - adr-2605263100-mizuho-water-sanitation-tier-b-actor-r0
  - adr-2605263200-kazaori-disaster-response-tier-b-actor-r0
related:
  - adr-2605263200-kazaori-disaster-response-tier-b-actor-r0
supersedes: []
superseded_by: []
---

# ADR-2606091200: sonae (備え) — non-profit religious-corp civilian pre-disaster foresight + preparedness + early-warning substrate Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-06-09
**Deciders**: Jun Kawasaki

# Context

kazaori (ADR-2605263200) is the civilian disaster **response** substrate.
Its lifecycle is, by design, **reactive**: a Council Lv6+ ≥4/7
declaration is made on or after an event, damage assessment runs
*during* the active emergency, supply/evacuation/medical-surge cells
run *during* the emergency, and a post-emergency review closes the
cycle. kazaori has a `needs prediction` element, but it is *during-event*
needs/supply-demand routing — **not** hazard forecasting, early warning,
or preparedness.

This leaves the entire **before** half of the disaster cycle
unmodelled. In Sendai Framework terms, kazaori covers Response and
contributes to Recovery, but nothing in the substrate covers:

- **Priority 1** Understanding disaster risk (hazard watch + exposure)
- **Priority 2** Strengthening governance to manage risk (drills, plans)
- **Priority 3** Investing in resilience (stockpile pre-positioning)
- **Priority 4** Enhancing preparedness for effective response + early
  warning

## Motivating case — 2026-06-08 Mindanao (Sarangani) Mw 7.8 earthquake

On 2026-06-08 ~07:40 local, a **Mw 7.8** earthquake struck offshore
Sarangani, southern Mindanao (depth ≈55 km), the strongest in the
Philippines since 1990. It generated a tsunami (≈1.5 m max, Talengan,
North Sulawesi), prompted PHIVOLCS tsunami warnings, was followed by
>1,000 aftershocks (max Mw 6.5), killed ≥37 with >200 injured and 12
missing (incl. a Glan landslide killing 14), cut power to ≈800,000
households, disrupted water/internet, and forced ≈10,000 families in
Sarangani + Sultan Kudarat to evacuate under tsunami warning. Tsunami
advisories reached as far as Okinawa.
(Sources: USGS; PHIVOLCS 08 June 2026 primer; Al Jazeera; NPR; RNZ; CBS.)

Walking this event through the existing substrate exposes the gap
precisely:

- **The ~minutes between the quake and the tsunami** — the window where
  an early-warning relay + pre-mapped evacuation routes save lives — has
  **no actor**. kazaori cannot act until a Council declaration exists.
- **The ≈10,000 evacuating families** needed *pre-designated* safe sites
  and *pre-positioned* water/food. kazaori designates safe sites and
  dispatches supply *reactively*; nothing pre-positions them.
- **The ≈800,000 households' power loss + water/comms disruption** is a
  *known* lifeline exposure that should have been profiled in advance.
- **>1,000 aftershocks** require a continuous hazard watch feeding
  community decisions — again, no actor.

sonae fills exactly this window, while respecting two hard boundaries
the case also makes vivid: (1) only PHIVOLCS/PTWC may *issue* the
tsunami warning — a community actor that fabricated one would be lethal
(hence **G8 no-false-authority, relay-only**); and (2) kazaori, not
sonae, owns the emergency declaration and the response (**G10 + N3**).

# Decision

Create **sonae** (備え), a Tier-B 任意団体 internal civilian
**pre-disaster** substrate at `did:web:sonae.etzhayyim.com`
(`20-actors/sonae/`), as the **before** complement to kazaori. sonae is
parallel to — not a replacement for — state early-warning systems
(PHIVOLCS / JMA / etc.), which remain authoritative.

## §1. Phase boundary (the core architectural commitment)

```
sonae (備え, BEFORE)              kazaori (風折, DURING)         after
prevention / mitigation          emergency declaration         silenKazaoriReview
preparedness / stockpiling       damage assessment             shidemori / kokoro
hazard watch                     supply / evacuation / medical
official-warning RELAY      ───▶ (response)
imminence signal ───────────────▶ (recommends; Council declares)
```

sonae MUST NOT perform response (N3). The only coupling is
`disasterImminenceSignal` → `kazaori.emergency_declaration`, which is
**recommend-only**: kazaori's Council Lv6+ ≥4/7 remains the sole
emergency-state authority (G10).

## §2. Scope (6 cells)

| # | Cell | Node | Phase | I/O |
|---|---|---|---|---|
| 1 | `hazard_watch` | naphtali | continuous | OPEN gov feeds → `hazardSignalRecord` (open-data-only; G6) |
| 2 | `risk_assessment` | naphtali | standing | exposure + vulnerability fusion → `siteRiskProfile` (community-scale; aggregate-only) |
| 3 | `early_warning_relay` | naphtali | event | official warning → opt-in relay → `earlyWarningRelay` (relay-only + source cited; G8) |
| 4 | `preparedness_plan` | naphtali | periodic | stockpile + safe-site + route + opt-in registry → `preparednessPlan` |
| 5 | `drill_attestation` | naphtali | event | opt-in drill record → `drillAttestation` (also satisfies kazaori R1 drill gate) |
| 6 | `handoff_trigger` | naphtali | event | threshold crossed → `disasterImminenceSignal` → kazaori (recommend only) |

## §3. Lexicons (6, under `com.etzhayyim.sonae.*`)

`hazardSignalRecord` · `siteRiskProfile` · `earlyWarningRelay` ·
`preparednessPlan` · `drillAttestation` · `sonaeReadinessReview`.
See `/00-contracts/lexicons/com/etzhayyim/sonae/README.md`.

## §4. Cross-actor

kazaori (downstream handoff + drill-gate satisfaction) · mizuho +
mitsuho (stockpile pre-positioning) · tatekata (exposure + safe-site
pre-designation) · hagukumi (vulnerable opt-in pre-registry) · hikari +
watatsuna (lifeline + comms resilience) · kawaraban (relay channel) ·
toritate (preparedness fund) · chigiri (handoff procedural attestation).

## §5. Constitutional Gates (G1–G12, immutable)

| Gate | Statement |
|---|---|
| G1 | Charter Rider §2(a)–(h) scan on every preparedness document |
| G2 | kotoba-datomic attestation lineage on every record |
| G3 | **Community-scale only** — NOT a national early-warning replacement |
| G4 | **NO commercial disaster-prediction software** (One Concern / FloodFlash / Jupiter Intelligence / RMS / Tomorrow.io enterprise / Everbridge / OnSolve / AlertMedia PROHIBITED per Charter Rider §2(e)+§2(c)); OPEN gov feeds only |
| G5 | NO armed enforcement (civilian only; force separate per ADR-2605192315) |
| G6 | **NO surveillance** — open geophysical/met feeds + opt-in self-report only; no individual tracking / no person-profiling / no household risk-scoring |
| G7 | Murakumo-only inference (commercial disaster-AI PROHIBITED) |
| G8 | **NO false authority** — MUST NOT originate official seismic/tsunami/typhoon warnings; `relayOnly` const true + `authoritativeSource` required |
| G9 | Sendai Framework + Sphere Standards reference (open-publication; sonaeReadinessReview audit) |
| G10 | **NO unilateral disaster declaration** — only kazaori Council Lv6+ ≥4/7 may declare; sonae signals/recommends |
| G11 | NOT a state-licensed early-warning entity |
| G12 | NO payroll for stewards (vocation-flow L5) |

## §6. Non-Goals (N1–N12)

| | |
|---|---|
| N1 | NOT military / armed enforcement |
| N2 | NOT war-zone humanitarian aid |
| N3 | **NOT disaster response** (clean phase boundary to kazaori) |
| N4 | NOT commercial catastrophe / insurance risk modeling |
| N5 | NOT state early-warning-system replacement (PHIVOLCS/JMA authoritative) |
| N6 | NOT surveillance / NOT individual risk-scoring |
| N7 | NOT commercial disaster-prediction software integrator |
| N8 | NOT armed enforcement |
| N9 | NOT closed-source |
| N10 | NOT state-licensed entity |
| N11 | NOT single-jurisdiction-dependent |
| N12 | NOT issuing authoritative public alerts (relay-only) |

## §7. Roadmap

| Phase | Date / gate | Scope | Murakumo |
|---|---|---|---|
| R0 | 2026-06-09 (this ADR, PROPOSED) | scaffold; 6 cells path-reserved; 6 Lexicon skeletons | none |
| R1 | Council Lv6+ ≥3 + open-feed baseline + Sendai self-assessment + ≥1 drill | hazard_watch + risk_assessment | naphtali |
| R2 | Council Lv6+ ≥4 + 30-day public + 3 site attestations | +early_warning_relay + preparedness_plan + drill_attestation | naphtali + dan |
| R3 | Council Lv7+ unanimity + ≥1 live hazard-to-handoff cycle | +handoff_trigger + sonaeReadinessReview cycle | naphtali + dan + levi |

# Consequences

**Positive.** Closes the Sendai before-phase gap; gives the substrate a
lawful, life-saving early-warning relay that the Mindanao case shows is
otherwise missing; pre-positions mizuho/mitsuho stock so kazaori's
response cells start from a stocked baseline; and sonae drills double as
kazaori's R1 activation evidence (the two actors bootstrap each other).

**Risks / mitigations.** (1) *False-authority drift* — mitigated
structurally by G8 (`relayOnly` const true, `authoritativeSource`
required) + a `falseAuthorityIncidents` audit counter in
`sonaeReadinessReview` (target 0). (2) *Scope creep into response* —
mitigated by N3 + the recommend-only handoff (G10 keeps declaration with
kazaori). (3) *Surveillance creep* — mitigated by G6 (open feeds +
opt-in only; aggregate counts, no individual records).

# Alternatives considered

1. **Extend kazaori with pre-disaster cells** — rejected: pollutes
   kazaori's clean reactive declaration→response lifecycle and risks
   the actor self-declaring on its own forecasts (G10 violation). A
   separate before-actor with a recommend-only handoff is cleaner.
2. **Integrate a commercial early-warning vendor** (One Concern /
   Everbridge) — rejected per G4 + Charter Rider §2(e)/§2(c).
3. **Originate community tsunami/quake alerts** — rejected per G8; only
   authoritative agencies may issue, sonae relays.

# R0 scaffold status (as-built, 2026-06-09)

Honest framing (G8): R0 is scaffold only. Cells are path-reserved and
raise import-time `RuntimeError` until R1 Council ratification. What is
on disk and verified:

- **Actor scaffold** — `20-actors/sonae/{manifest.jsonld, README.md,
  CLAUDE.md, MATURITY.md}`.
- **6 Lexicon skeletons** — `00-contracts/lexicons/com/etzhayyim/sonae/`
  (+ README). `manifest-lexicon-drift` audit: **sonae drift 0**.
- **R0 data asset** — `registry/warning-sources.seed.json`: 20
  authoritative official warning issuers across 16 jurisdictions, all
  `isAuthoritativeIssuer=true` + `verificationStatus="unverified-seed"`
  (G14). This is the relay-only allowlist for `earlyWarningRelay` (G8).
- **Coverage** — 20 fail-closed invariant tests green:
  `70-tools/scripts/audit/test_sonae_lexicon_invariants.py` (10, pins
  the constitutional gates) + `test_sonae_warning_sources_seed.py` (10,
  pins the registry incl. a G8 cross-lexicon check that
  `earlyWarningRelay.authoritativeSource` is realized by the registry).
- **SSoT registration** — `deps.toml` (this ADR + 2 sonae modules);
  root `CLAUDE.md` §Status row.

**NOT yet (R1 gates, honest):** cell solvers · live feed ingest ·
Sendai 4-priority self-assessment · ≥1 community drill · Council Lv6+
ratification · registry human-verification (all 20 sources are
`unverified-seed`; 0 human-verified) · registry `VERIFICATION.md`.

# References

- ADR-2605263200 — kazaori (downstream response actor; handoff target)
- ADR-2605192315 — Transparent Force authorization (G5 + N1 separation)
- ADR-2605215000 — Murakumo-only inference (G7)
- ADR-2605263100 / 2605261015 / 2605261030 / 2605261100 — mizuho /
  mitsuho / hagukumi / hikari cross-actors
- Sendai Framework for DRR 2015–2030; Sphere Standards; WMO/IOC Tsunami
  Warning System (all open-publication; reference NOT membership)
- USGS; PHIVOLCS "Primer on the 08 June 2026 Mw 7.8 Offshore Sarangani
  Earthquake" — motivating case
