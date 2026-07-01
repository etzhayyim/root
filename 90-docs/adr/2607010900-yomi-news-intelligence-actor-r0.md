---
id: adr-2607010900-yomi-news-intelligence-actor-r0
title: "yomi 読み — news-intelligence actor (Tier-B R0; intel-LLM ⊣ IntelGovernor over the kawaraban mirror; a SOURCE/voice, autonomous publication)"
status: proposed-pending-council-ratification
doc_type: adr
topic: yomi-news-intelligence-actor
authoritative: true
last_verified: 2026-07-01
priority: 6.0
axis: actor
weight: 0.60
priority_note: "Answers the owner ask 2026-07-01: collect world news from public/national broadcasters, analyze as INTEL, post to app-aozora — but charter-clean. kawaraban is the MEDIUM (mirrors the world, authors nothing, G1/G4 absolute). yomi is the missing SOURCE: it subscribes to kawaraban's mirror, reads the full text kawaraban holds only in its PRIVATE internal buffer (ADR-2607010930, never the public Datom log), runs a sealed intel-LLM ⊣ IntelGovernor, and publishes attributed intel assessments in its OWN voice. It reuses the legacy news-intel pipeline design (260424: fetch → facts/findings → provenance scoring → credibility/priority gate → publish) WITHOUT the ad-monetization that made etzhayyim-project-news charter-noncompliant. Per ADR-2606281500 (種まき doctrine) publication is AUTONOMOUS BY DEFAULT — no per-post operator/Council gate, no request-approval node; bounded by the IntelGovernor + credibility(≥0.7)/priority(≥0.45) gates + Rider §2 catastrophe-veto. PUBLICATION ≠ ACTUATION: yomi performs no actuation. ZERO charter invariant amendments; G1/G4 of the medium untouched."
authoritative_for:
  - "yomi actor scope (news-INTEL SOURCE over the kawaraban mirror; intel-LLM sealed + independent IntelGovernor; langgraph-clj StateGraph sibling of sng)"
  - "the IntelGovernor invariants (HOLD: unsourced-claim, missing-provenance, non-open-fulltext, libel-risk, non-fleet-model, no-actuation; PUBLISH gate: credibility≥0.7 / priority≥0.45)"
  - "the autonomous-publication doctrine for intel assessments (no interrupt-before / no council signoff; ADR-2606281500; bounded by Governor + catastrophe-veto)"
  - "the PUBLIC/PRIVATE store split (subscribed kawaraban mirror edges = public observe; fulltext cache + intel assessments + ledger = PRIVATE, never written to a public Datom log)"
depends_on:
  - adr-2606281500   # 種まき autonomous publication doctrine
  - adr-2606061900   # kawaraban (the medium yomi reads)
  - adr-2606131600   # shirabe (read-only membrane lineage; yomi is the write-voice sibling)
  - adr-2607010930   # kawaraban G4 internal fulltext buffer (yomi's fulltext source)
  - adr-2605312345   # kotoba Datom first-class canonical state
  - adr-2605262130   # kotoba substrate
  - adr-2605215000   # Murakumo-only inference (G2-fleet)
related:
  - "com-etzhayyim-yomi (sovereign repo, github.com/etzhayyim/com-etzhayyim-yomi)"
  - "60-apps/etzhayyim-project-news/docs/260424-news-intel-actor-process-design.md (legacy intel pipeline design, reused charter-clean)"
supersedes: []
superseded_by: []
---

# ADR-2607010900: yomi 読み — news-intelligence actor (R0)

**Status**: proposed-pending-council-ratification · **Date**: 2026-07-01 · **Deciders**: Jun Kawasaki

## Context

The owner asked etzhayyim to collect the world's latest news from public/national
broadcasters (公営/国営) and wire agencies, analyze it as INTEL, and post to app-aozora.
Two priors existed:

1. **`etzhayyim-project-news`** (legacy, `60-apps/`) — had the exact pipeline (48 sources
   incl. NHK/BBC/Al Jazeera/Reuters/FDA/PMDA/MLIT/METI; `intel.report` with
   facts/findings/provenance scoring; ATPost publishing; the `260424` intel design).
   But it was **ad-monetized (ExoClick) + traffic/engagement-framed = Charter §1.2/§1.6
   non-compliant**, under remediation.
2. **`kawaraban` 瓦版** (ADR-2606061900, R0) — the charter-clean MEDIUM: mirrors the world,
   authors nothing, G1 (no verdict) / G4 (no full text) absolute. Deliberately the
   *inverse* of a news app.

Neither is the INTEL SOURCE: kawaraban cannot author assessments (G1/G11 — medium not
source); the legacy platform is contaminated. The roster lacked a charter-clean
news-INTELIGENCE voice.

## Decision

Add **yomi 読み** ("reading / interpretation") — a Tier-B news-INTELLIGENCE actor, a
SOURCE/voice, langgraph-clj StateGraph (sibling of sng's synth-LLM ⊣ CarbonGovernor →
yomi's intel-LLM ⊣ IntelGovernor). It:

- **subscribes** to kawaraban's public mirror (outlet / article / mention edges) — the
  observe charter, always on;
- **reads full text** from kawaraban's PRIVATE internal buffer (ADR-2607010930), never the
  public Datom log (G4 of the medium stays absolute);
- runs a **sealed intel-LLM** that PROPOSES an intel assessment `{facts findings entities
  classification credibility priority sources provenance-chain}`, grounded in the mirrored
  metadata + cached full text, INSUFFICIENT-honest (G4 non-fabricating);
- an **independent IntelGovernor** censures the proposal (HOLD on unsourced-claim /
  missing-provenance / non-open-fulltext / libel-risk / non-fleet-model / no-actuation;
  PUBLISH gate credibility≥0.7 / priority≥0.45);
- **publishes** the assessment in yomi's OWN attributed voice (`:actor-event`, member-signed,
  no-server-key) via the feed-post membrane to app-aozora.

Per **ADR-2606281500** (種まき doctrine), publication is **autonomous by default** — no
`:request-approval` node, no `interrupt-before`. PUBLICATION ≠ ACTUATION; yomi performs no
actuation, so the human/Council gates that remain for high-stakes actuation do not apply.
The bound is the Governor + the catastrophe-veto content scan.

## The core contract

```
kawaraban mirror edge ─┐
kawaraban fulltext    ─┴─▶ fetch-fulltext → intel-LLM (sealed) ─propose─▶ IntelGovernor
(private buffer, G4)                                                      │
                                                                commit/hold ◀┶▶ (escalate→hold)
                                                                          │
                                                                  attributed actor-event
                                                                  → app-aozora (autonomous)
```

**The actor never publishes an assessment the IntelGovernor would reject, and performs no
real-world actuation.** That single invariant is the yomi analog of sng's carbon contract
and robotaxi's safety contract.

## Status

🟡 **R0** — reference design + runnable skeleton. langgraph-clj StateGraph; MemStore ‖
DatomicStore (`:db-api`); IntelGovernor + R0→R3 phase gate + append-only intel ledger are
real and tested (9 tests / 26 assertions green; clj-kondo clean). intel-LLM is a
deterministic mock. Productionizing = (1) curate kawaraban mirror subscriptions + the
private fulltext plumbing, (2) swap `intelllm/mock-advisor` for a Murakumo `llm-advisor`,
(3) optionally bind the store to kotoba-server (kotobase.net) for a sovereign CACAO graph.

Repo: `github.com/etzhayyim/com-etzhayyim-yomi` (sovereign, did:web
`did:web:etzhayyim.github.io:com-etzhayyim-yomi`). Registered in west (`orgs/etzhayyim/com-etzhayyim-yomi`).
