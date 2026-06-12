---
id: adr-2606073001-robotics-remote-work-actor-roster-and-isco-coverage
renumbered_from: "2606073000"
title: "ADR-2606073001: Robotics remote-work actor roster + ISCO coverage/GAP survey (tazuna as the on-site→remote substrate)"
status: proposed
doc_type: adr
topic: robotics-remote-work-actor-survey
authoritative: true
last_verified: 2026-06-07
priority: 4.0
axis: architecture
weight: 0.50
priority_note: "Survey/analysis ADR. Defers the canonical LPS ISIC/ISCO/UNSPSC ranking to ADR-2606032100; authoritative only for the remote-work lens (tazuna substrate + on-site→remote coverage map + GAP roadmap)."
authoritative_for:
  - robotics remote-work (teleoperation) actor roster across the etzhayyim corpus
  - on-site→remote-work coverage/GAP map for physical-labour occupations
  - remote-work-value reframing of the labour-liberation roadmap
depends_on:
  - ADR-2606042100 (tazuna — remote-robotics fleet operation + teleoperation + LfD)
  - ADR-2606032100 (Labor-Liberation Robotics-Actor Wave — canonical ISIC/ISCO/UNSPSC LPS ranking)
  - ADR-2606032130 (Displacement Dividend — G2 coupling gate)
  - ADR-2605261000 (Labor Liberation Ladder — L0..L6)
  - ADR-2605192100 (Mission Charter — 構造的労働解放, N1 mining/weapons exclusion)
related:
  - ADR-2605301020 (Basic High Income — in-kind, cash≡0)
  - ADR-2605215000 (Murakumo-only inference)
  - ADR-2606042300 (todoke last-mile delivery)
  - ADR-2606013400 (funadaiku zero-emission cargo-ship)
  - ADR-2605252200 (watatsumi civilian submersible)
  - ADR-2606012600 (watatsuna submarine-cable laying)
  - ADR-2605250715 (tatekata construction)
  - ADR-2605261215 (hodoki ELV disassembly)
  - ADR-2606051500 (kamado carbon refining / refinery decommission)
  - ADR-2605263100 (mizuho water + sanitation)
supersedes: []
superseded_by: []
---

# ADR-2606073001: Robotics remote-work actor roster + ISCO coverage/GAP survey

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

A recurring planning question: *how much of the actor corpus is already designed around
**robotics-enabled remote work** — converting on-site physical jobs (high-rise window
cleaning, mining, construction, shipping, freight, loading/unloading, logging, sewer
cleaning, …) into teleoperated / autonomous work — and, on an ISCO basis, which of these
most effectively advance the Charter's 構造的労働解放 (structural liberation of humanity
from labour)?*

The information needed to answer exists, but it is **scattered across ~20 actor ADRs plus
the root Status table**, and no single doc takes the *remote-work lens*: the unit that
matters for "remote work" is not the manufacturing actor but the **teleoperation /
learning-from-demonstration substrate that pulls a human out of a dangerous on-site role
and lets them operate the body from elsewhere**. That substrate (tazuna, ADR-2606042100)
landed only on 2026-06-04 and re-frames the whole roster.

The canonical occupational ranking already exists — **ADR-2606032100** ranks the
un-automated toil by `LPS = headcount × misery × automatability × charter_fit ×
coverage_gap` over ISIC / **ISCO** / UNSPSC and stands up the first three labour-liberation
robotics actors (sanae / hataori / kiyome). This ADR does **not** restate or re-derive that
ranking; it **points to it** and adds the orthogonal *remote-work* view: a consolidated
roster, a coverage/GAP map against the named occupations, and the observation that
teleoperation value is highest exactly where the current corpus has GAPs.

# Decision

Record the following as the authoritative remote-work view (the LPS ranking remains owned by
ADR-2606032100).

## 1. The remote-work substrate: tazuna 手綱 (ADR-2606042100, R0)

`tazuna` is the **single layer that converts "on-site labour" into "remote labour"**:
clean-room remote-robotics **fleet operation + teleoperation + learning-from-demonstration**
(Boston-Dynamics-Orbit equivalent), Transparent-Force + no-server-key, *weaponizable
unrepresentable*, dividend-coupled. Every robotics-bodied actor below is a *body*; tazuna is
how a human drives/teaches that body from home. The remote-work mission is therefore
**tazuna × {domain robotics actor} × Displacement-Dividend (G2)**, not any actor alone.

## 2. Roster of robotics-bodied actors (the "bodies")

All are **R0 (design + simulation only); no hardware exists**. Live actuation is Council
Lv6+/operator-gated (G7) and dividend-coupled (G2). kami-engine/kami-genesis provides the
physics sim; inference is Murakumo-only (ADR-2605215000).

| Tier | Actors | On-site job converted | ADR |
|---|---|---|---|
| **0 — remote-op substrate** | tazuna 手綱 | teleop + LfD for *all* bodies | 2606042100 |
| **1 — explicit labour-liberation (dividend-coupled by design)** | sanae 早苗 (field agri) · hataori 機織 (garment) · kiyome 清め (domestic/janitorial) | sow/weed/harvest · cut-make-trim · cleaning | 2606032100 |
| **2 — dangerous/dirty on-site (highest teleop value)** | tatekata 建方 (construction) · watatsumi 綿津見 (submersible) · watatsuna 綿津綱 (cable-laying) · hodoki 解き (ELV disassembly) · giemon kabitori (黴取り mold-removal) · kamado 竈 (refinery decommission) · haraedo 祓戸 (bulky-waste logistics) · mizuho 水穂 (water/sanitation) | building · deep-water · seabed · teardown · mold · hazmat plant · waste · sewage *treatment* | 2605250715 / 2605252200 / 2606012600 / 2605261215 / 2605312300 / 2606051500 / 2606010200 / 2605263100 |
| **3 — mobility / logistics** | wadachi 轍 · todoke 届け · ainori 相乗 · sarutahiko 猿田彦 (+積込ロボット) · funadaiku 船大工 | driving · last-mile · pooled transit · Class-8 haul + loading · cargo-ship build+voyage | 2605242000 / 2606042300 / 2606071500 / 2605252500 / 2606013400 |
| **4 — factory / plant automation** | igata 鋳型 · kanayama 金山 · suki 鋤 · tsutae 伝え · yakushi 薬師 · makura 枕 · futawa 二輪 · hikari 光 · noroshi 烽 (packaging robotics) | casting · Al recycling · tractor mfg · device assembly · pharma · foam · motorcycle · energy · chip packaging | 2605261200 / 2605252400 / 2605261500 / 2605261300 / 2605250500 / 2605261115 / 2605261330 / 2605261100 / 2606051600 |

**Count**: 1 remote-op substrate + ~18–25 robotics-bodied actors (depending on whether
plant-automation is counted). Purpose-built labour-liberation actors: **3** (sanae / hataori
/ kiyome). Everything is **R0** — designs and sims, zero deployed hardware.

## 3. Coverage map vs the named occupations

| Occupation (JP / EN) | Status | Actor / note |
|---|---|---|
| 工事・施工 (construction) | ✅ covered | tatekata 建方 (civil+MEP ≤2-story) |
| 船舶 (ships / marine) | ✅ covered | funadaiku (build+voyage) + watatsumi (submersible) + watatsuna (cable) |
| 運送 (freight / transport) | ✅ covered | sarutahiko + todoke + wadachi + ainori |
| 積み下ろし (loading / unloading) | △ partial | sarutahiko **積込ロボット** integrated; standalone warehouse = roadmap `kuramori 倉守` |
| 下水道清掃 (sewer cleaning) | △ partial | mizuho 水穂 does wastewater **treatment**, *not* in-pipe cleaning robotics — **robotics GAP** |
| 伐採 (logging / forestry) | ❌ GAP (roadmapped) | `soma 杣` reserved in ADR-2606032100 roadmap (#9, "one of the deadliest jobs"); not authored |
| 窓際・高所清掃 (high-rise / façade window cleaning) | ❌ GAP | kiyome is indoor/ground-level only; façade/fall-risk work is on no roadmap |
| 採掘 (mining) | ⛔ excluded by construction | Mission Charter N1 (ISIC B extraction + weapons), ADR-2605192100 / 2606032100 |

## 4. ISCO-based liberation analysis (remote-work lens)

The corpus already reads as a **two-layer ISCO structure** (ADR-2606032100 §Meta-finding):
**ISCO 1–4 = software/knowledge actors** (already shipped: danjo, kanae, toritsugi,
chigiri, toritate, kanjō, ooyake, …) and **ISCO 6–9 = robotics actors** (this wave). The
robotics GAP maps almost entirely onto ISCO 6–9. For the canonical 12-row LPS table see
**ADR-2606032100 §Decision — the ranking**; it is not duplicated here.

**Where liberation is largest (headcount × misery), per the canonical ranking:**
agricultural field labour (sanae, ISCO 6/92, ≈0.6–0.86 B) ≫ construction (tatekata, ISCO
71/931, ≈0.26 B) > food service (roadmap kamado/ISCO 51/94, ≈0.1 B+) > domestic/cleaning
(kiyome, ISCO 91, ≈75 M+) > warehouse handling (roadmap kuramori, ISCO 93/82).

**Where the *remote-work* value is largest (teleoperation lens — added by this ADR):**
the marginal value of tazuna teleoperation is highest where **autonomy is hard but on-site
presence is itself the hazard** — i.e. removing the human from the location matters even
before full autonomy is solved. Ranked by that criterion:

1. 高所・façade window cleaning — fall fatality; **current GAP** (highest unmet remote value).
2. 下水道 sewer / confined-space cleaning — toxic-gas/confined-space death; **robotics GAP**.
3. 伐採 logging (soma) — struck-by/crush fatality; roadmapped, **unauthored**.
4. Deep-water / seabed (watatsumi, watatsuna) — **covered**; teleop already the design intent.
5. Hazmat plant decommission (kamado) / mold/biohazard (giemon kabitori) — **covered**.

**Finding**: the three occupations the question highlights as most "obviously remote-able"
(high-rise window cleaning, sewer cleaning, logging) are precisely the ones that are **GAP or
unauthored**, while the corpus has invested first in the *highest-headcount* toil (agri /
garment / cleaning) per the LPS's deliberate "most-exploited over most-automatable" choice.
The two lenses are complementary, not contradictory: LPS optimises total labour-hours
freed; the remote-work lens optimises lives-removed-from-danger per unit of (hard) autonomy.

## 5. Constitutional coupling (unchanged, referenced not restated)

No robotics actor may **displace live** (G7) without the displaced cohort registered for the
tenure-weighted, **in-kind, cash≡0** Displacement Dividend (G2, ADR-2606032130), delivered
along the Liberation Ladder L0→L6 (ADR-2605261000) toward Basic High Income (ADR-2605301020).
Mining/weapons remain N1-excluded.

# Consequences

**Positive** — gives operators a single remote-work map (substrate + bodies + coverage +
GAPs) without re-deriving the LPS; names tazuna as the on-site→remote unit; surfaces three
concrete high-remote-value GAPs (façade cleaning, sewer/confined-space, soma logging) and a
loading GAP (kuramori) as candidate next R0 charters, all tazuna-operated + dividend-coupled.

**Negative / risks** — (a) this is a *survey* over R0 designs; nothing here is deployed, and
headcounts are the order-of-magnitude figures inherited from ADR-2606032100. (b) Authority
overlap risk with ADR-2606032100 is mitigated by deferring the LPS ranking to it and scoping
this doc to the remote-work lens only. (c) Roster counts drift as actors land; treat the
table as a snapshot `last_verified: 2026-06-07`.

# Alternatives Considered

1. **Fold this into ADR-2606032100** — rejected; that ADR is the *occupation-ranking +
   first-three-actors* decision. The remote-work lens (tazuna as on-site→remote unit + GAP
   map) is a distinct, cross-cutting view that would bloat the ranking ADR and blur its scope.
2. **Author the GAP actors (façade / sewer / soma / kuramori) now** — deferred; each needs
   its own R0 charter (manifest + cells + lex + method) per the shared contract in
   ADR-2606032100 §Design, and the Displacement Dividend pool must be sized first (G2). This
   ADR records the priority; the charters are follow-ups.
3. **Rank purely by remote-work value (lives-removed-from-danger)** — rejected as the *sole*
   axis; it would deprioritise the largest headcount toil (agriculture). Kept as a
   complementary lens alongside the canonical LPS.

# References

- ADR-2606042100 (tazuna — remote-robotics fleet op + teleoperation + LfD)
- ADR-2606032100 (Labor-Liberation Robotics-Actor Wave — canonical ISIC/ISCO/UNSPSC LPS ranking + sanae/hataori/kiyome)
- ADR-2606032130 (Displacement Dividend — G2 coupling gate)
- ADR-2605261000 (Labor Liberation Ladder — L0..L6)
- ADR-2605301020 (Basic High Income — in-kind, cash≡0)
- ADR-2605192100 (Mission Charter — 構造的労働解放; N1 mining/weapons exclusion)
- ADR-2605215000 (Murakumo-only inference)
- Per-actor ADRs: 2605250715 (tatekata) · 2605252200 (watatsumi) · 2606012600 (watatsuna) · 2605261215 (hodoki) · 2606051500 (kamado) · 2606010200 (haraedo) · 2605263100 (mizuho) · 2606042300 (todoke) · 2606071500 (ainori) · 2605252500 (sarutahiko) · 2606013400 (funadaiku)
