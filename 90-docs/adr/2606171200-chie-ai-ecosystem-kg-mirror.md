---
id: adr-2606171200-chie-ai-ecosystem-kg-mirror
title: "ADR-2606171200: chie 智慧 — AI-ecosystem KG mirror (有力者・組織・投資・政策)"
status: accepted
doc_type: adr
topic: chie-ai-ecosystem-kg-mirror
authoritative: true
last_verified: 2026-06-17
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/chie
depends_on:
  - adr-2606011800-tsumugi-engi-knowledge-graph
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2606066001-keizu-government-power-relations-kg
  - adr-2606022000-kabuto-supply-chain-kg
  - adr-2606032000-kanjo-financial-disclosure-kg
  - adr-2606073000-inochi-living-world-kg-mirror
supersedes: []
superseded_by: []
---

# ADR-2606171200: chie 智慧 — AI-ecosystem KG mirror

**Status**: accepted (R1+ landed 2026-06-17 — PR #1913)
**Date**: 2026-06-17
**Deciders**: Jun Kawasaki

# Context

The actor roster covers power, supply chains, financials, government, and the biosphere —
but the **AI ecosystem as a unified, EDN/Clojure-native knowledge graph** (有力者・企業・
組織・投資・政策) has **no single actor**. The pieces are scattered and none unifies the AI
axis:

- **tsumugi** 紡ぎ — generic power-entity KG (取-concentration + 産官学報 + 旗); an AI lab can
  enter as a "company" node but there is no AI-axis schema (compute / capital / talent /
  policy concentration).
- **kabuto** 兜 — public-company supply chain (HHI); upstream of chips, not the AI field.
- **kanjō** 勘定 — disclosed financials (EDGAR/EDINET); only listed cos, no VC rounds.
- **keizu** 系図 — government power; the substrate for policy, not AI-policy-specific.
- **kosatsu** 高札 — designations; AI export-control is latent but generic.
- **handotai / kasa / silicon** — the physical compute base only.
- **kenkyusha** — an AI *research-frontier* generator, not an ecosystem KG.
- `*-compat` (anthropic / openai / huggingface / …) — interop API facades, not a KG ingest.

So there is a clear coverage gap: no actor that integrates **AI labs / companies / research
/ standards / funders / states / public-role persons / investment rounds / policy
instruments / models** into one append-only kotoba Datom graph with an AI-specific
取-concentration lens.

# Decision

Add an observation-only mirror actor **chie 智慧** (`20-actors/chie/`), the **AI sibling** of
the power-mirror lineage, built **clj-native** (`.cljc`, no Python twin) on the kotoba Datom
log.

- **State** — kotoba Datom log (EAVT, content-addressed; ADR-2605312345). `:organism/*` nodes
  (engi-organism ontology, 11 `:ai.*` kinds) + `:en/*` 縁 carrying `:en/grasping-load` ∈ [0,1]
  (where 取 lives; N1).
- **Lens** — edge-primary **取-concentration over four axes** (compute / capital / talent /
  policy), **routed to OPENING**: `:bond/opening-priority` = Σ inbound accumulation ×
  **(1 − openness)**. An **open** accumulator (open-weights / open-compute / public standard)
  scores **0** — the map points at *opening the concentration*, never at a winner.
- **Gates** (all test-enforced where structural):
  - **G1** — OPENING map, NEVER a target-list or winner-ranking. No capability grade, no
    winner forecast, no investment advice (N3).
  - **G2** — edge-primary. 取 only on edges; computed on read; no stored per-entity score.
    Persons appear only as public-power **role nodes**, never private profiles.
  - **G3** — non-adjudicating. Rounds / designations / `:ai/open?` are DISCLOSED facts.
  - **G4** — chie **never trades / never forecasts**: `:trade` / `:forecast-point` /
    `:capability-grade` / `:winner-rank` are unrepresentable (no such edge/attr; the emitter
    refuses them).
  - **G5** — sourcing honesty. Seed is all `:representative`; coverage ~0 by design;
    `coverage_report` names the gaps.
  - **G6** — Murakumo-only narration. **G7** — live ingest Council+operator-gated.
- **No duplication** — chie *references* sibling actors (financials → kanjō, supply → kabuto,
  silicon → handotai, compute capacity → kasa, research → kenkyusha, gov power → keizu,
  designations → kosatsu, antitrust → abaki); it does not re-ingest their data.
- **R0 deliverable (this ADR)** — ontology (`kotoba/schema.edn`), representative seed (39
  nodes / 39 縁), `analyze` / `datom_emit` / `coverage_report` (`.cljc`), 3 test suites (69
  assertions green, auto-discovered by `etzhayyim.tools.discovery` per ADR-2606131500).
- **R1** — 常駐化 (resident): an `autorun` heartbeat cell appending content-addressed Datom
  tx to the append-only kotoba commit-DAG (`verify-chain` tamper-evident, resume-safe;
  ibuki/mimamori pattern), registered in the cell-runner `cells.edn` + a fleet node.

# Implementation record (R1+ landed 2026-06-17 — PR #1913)

Delivered on branch `chie-ai-ecosystem` (PR #1913), clj-native (`.cljc`, no Python twin),
across a 30-min self-paced loop. The three mandate legs — **clj · datomic · kotoba 常駐化** —
are all empirically proven:

- **Ontology + seed** — `kotoba/schema.edn` (rich) + `00-contracts/schemas/ai-ecosystem-ontology.kotoba.edn`
  (db/ident vocab). Seed grew to **66 nodes / 58 縁**; all 11 node kinds, 8 edge kinds, 4 axes covered.
- **analyze / datom_emit / coverage_report** — edge-primary 取-concentration → OPENING; EAVT
  GROUND `:add` + DERIVED transient (N1/G2); sourcing-honest gap worklist (G5).
- **常駐化 (kotoba)** — `autorun.cljc` + `cell.cljc` heartbeat → content-addressed tx on the
  append-only commit-DAG (`verify-chain` tamper-evident, resume-safe); `ChieHeartbeatCell`
  registered in cell-runner `cells.edn` (node gad, cron `37 * * * *`, healthz 13082).
- **Murakumo digest** — deterministic `template-digest` + Murakumo-only `narrate` (fail-open;
  non-fleet endpoint refused).
- **DISCLOSED ingest + G7 gate** — `ingest.cljc` upgrades rounds + policy instruments →
  `:authoritative` with official-source `:en/disclosed-src` (idempotent, concentration-preserving);
  `ingest-live` refuses without `CHIE_INGEST_LIVE` + operator DID.
- **root kotoba roster** — `bb kotoba:ingest --validate` = 124 entities / 700 datoms /
  0 undeclared / 0 value-violations; `roster-report` lists chie.
- **datomic read path** — `kqe.cljc` queries the REAL `etzhayyim.kotoba.engine` via Datalog
  `q` + Datomic `pull` (VAET reverse-ref), result == in-memory `query.cljc` (one source of truth).
- **query + verify + manifest.edn + README** — KG query API, one-shot charter self-audit gate,
  edn-native manifest, orientation doc.
- **Tests** — 11 suites · **56 tests / 184 assertions** green (auto-discovered by `bb test:actors`).

Open follow-ups (next R-cycle, all G7/Council-gated): the LIVE network ingest behind the G7
gate (regulator texts / disclosed rounds / Wikidata), structured per-round capital attribution,
and a kotoba-clj WASM build.

# Consequences

- (+) First unified AI-ecosystem layer in EDN/Clojure; feeds mitooshi (distribution-only),
  tanemaki (grant DD), and abaki (anti-monopoly routing).
- (+) Reuses the proven mirror-lineage analyze/coverage/datom-emit triad → low cost, and the
  charter gates are inherited and test-locked.
- (−) Until the G7 live leg, coverage is a bounded representative seed (made explicit by
  `coverage_report`).
- (−) ADR id time component (`1200`) is provisional; reconcile at registration.

# Alternatives Considered

1. **Extend tsumugi with an AI lens** (no new actor) — rejected: investment rounds and policy
   texts do not fit tsumugi's power-縁 schema; mixing degrades coverage honesty.
2. **Extend kabuto / kanjō** — rejected: both assume listed companies; they cannot hold
   non-listed labs, policy instruments, talent flows, or VC rounds.
3. **Rely on `*-compat` facades** — rejected: those are API adapters, not a knowledge graph.

# References

- ADR-2606011800 (tsumugi) · ADR-2606073000 (inochi mirror pattern) · ADR-2605262130 (kotoba)
- ADR-2605312345 (Datom = canonical state) · ADR-2605081300 (edge-primary karma)
- ADR-2606131500 (bb test auto-discovery) · ADR-2605215000 (Murakumo-only)
- `20-actors/chie/` — actor home (CLAUDE.md / MATURITY.md / kotoba/schema.edn)
