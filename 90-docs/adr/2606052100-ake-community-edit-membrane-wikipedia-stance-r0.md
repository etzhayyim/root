---
id: adr-2606052100-ake-community-edit-membrane-wikipedia-stance-r0
title: "ADR-2606052100: 朱 (ake) — community-edit membrane (Wikipedia-stance KG/profile correction) R0"
status: proposed
doc_type: adr
topic: ake-community-edit-membrane
authoritative: true
last_verified: 2026-06-05
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - ake-community-edit-membrane
  - wikipedia-stance-collaborative-correction
depends_on:
  - adr-2606042330-entity-as-actor-society-wide-social-mirror-graph
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605291500-tsukuroi-authorized-vuln-remediation-patch-proposer
  - adr-2605301600-danjo-public-accountability-oversight
supersedes: []
superseded_by: []
---

# ADR-2606052100: 朱 (ake) — community-edit membrane (Wikipedia-stance KG/profile correction) R0

**Status**: proposed
**Date**: 2026-06-05
**Deciders**: Jun Kawasaki

# Context

The question: *「etzhayyim の actor や情報の更新を Wikipedia のようなスタンスで更新させたい。
そういった設計になっているか?」*

The honest answer before this ADR: **no, by design.** The current write path for actor records and
KG entity data is **actor-owned, git-committed, ADR-author-gated**:

- Actor records live in `00-contracts/schemas/actor-profile-seed.kotoba.edn` and per-actor
  `registry/*.seed.json` / `data/seed-*.kotoba.edn`; entity-actor mirrors are *deterministically
  regenerated* from KG seeds (`70-tools/scripts/entity-actors/gen-entity-handles.mjs`).
- The only way to correct a wrong fact (a government unit's address, a company's status) is a git
  issue/PR that the KG actor's designer reviews and merges. There is **no community-edit pathway,
  no proposal/vote workflow for data, and no `:representative→:authoritative` promotion a member
  can initiate.**

Yet the substrate already holds every primitive a Wikipedia-style model needs:

| Wikipedia element | already present in etzhayyim |
|---|---|
| revision history | **kotoba Datom log** — append-only, `as-of` (上位互換: immutable, non-終末) |
| sourcing discipline | `:representative` ↔ `:authoritative` + `provenance` + `last-verified` |
| community consensus | **1 SBT = 1 vote** + Council + the objection lexicon |
| accountable contribution | **no-server-key** (member-signed) — stronger than anonymous edits |
| neutral observation (NPOV) | the `isMirror` invariant (ADR-2606042330) + danjo non-adjudication |
| edit-quality scoring (ORES) | Murakumo-only LLM (ADR-2605215000) |

What is missing is exactly **one membrane**: a member-signed write path that triages, routes,
votes, and promotes — appending to the Datom log, amending no invariant.

Two charter constraints shape the design and are stated up-front:

1. **It cannot be Wikipedia's anonymous open-edit.** Charter §1.16 conversion-gating + the
   no-server-key invariant (ADR-2605231525) require **信者-gated, member-signed** contribution. ake
   is therefore a **permissioned wiki**.
2. **A mirror entity-actor cannot be "edited to speak as the entity."** ADR-2606042330 fixes
   entity-actors as keyless observational mirrors; ake corrects **the observation**, never
   impersonates the subject.

# Decision

Introduce **朱 (ake)** — a Tier-B *community-edit membrane*. 朱 = vermillion editorial ink
(**朱を入れる** = to correct a manuscript). One public/power **fact** or one **actor profile** is
corrected by a **信者**, through a five-cell pipeline, with **zero invariant amendments**.

## The pipeline

```
propose ─▶ edit_triage ─▶ route ─▶ review_vote ─▶ promote ─▶ revision_log
(信者署名)  (LLM score)   (pure fn)  (consensus)    (no-srv-key)  (append-only)
```

- **propose** (`com.etzhayyim.ake.editProposal`) — member-signed intake; screens **G1** (member +
  no-server-key), **G3** (target ∈ {kg-fact, actor-profile}), **G4** (provenance present).
- **edit_triage** (`com.etzhayyim.ake.editTriage`) — a Murakumo-only LLM scores **risk** ∈
  {low, medium, high, invariant} + **quality** ∈ [0,1] (the Wikipedia **ORES** analogue). The
  route is computed by **`route_for(risk, quality, rider)` — a PURE FUNCTION** (G2): the model
  scores, it never accepts/rejects. There is **no `:triage/decision`** attribute.
- **route** — `auto-accept` (low risk + quality ≥ 0.7, the optimistic fast-path) ·
  `vote` · `council-lv7` (invariant-adjacent, G7) · `refused` (Charter-Rider §2(a)-(h) hit — unpromotable).
- **review_vote** (`com.etzhayyim.ake.editReview`) — optimistic fast-path / **1 SBT = 1 vote** with
  a 48h timelock / Council-pending. A server-signed tally is refused.
- **promote** (`com.etzhayyim.ake.editPromotion`) — member/operator-signed append; optional
  `:representative→:authoritative` with **verifiable** provenance; `published = false` at R0 (G8).
- **revision_log** (`com.etzhayyim.ake.revisionEntry`) — the append-only **"view history"** tab;
  the log only ever grows (G5, 非終末論).
- **councilEditReview** (`com.etzhayyim.ake.councilEditReview`) — Council Lv7+ attestation for
  invariant-adjacent edits.

## The 9 gates (immutable R0→R5)

**G1 信者-gated + no-server-key** · **G2 LLM non-adjudicating** · **G3 mirror-preserving** ·
**G4 sourcing-mandatory** · **G5 append-only / non-destructive** · **G6 Murakumo-only** ·
**G7 invariant-lock escalation (Council Lv7+ + Charter-Rider hard-gate)** · **G8 outward-gated** ·
**G9 anti-vandalism / contributor-trajectory** (Wellbecoming, not a score-of-soul).

Each structural gate is encoded in **three places**: the ontology `:db/allowed`/enum
(`00-contracts/schemas/community-edit-ontology.kotoba.edn`), the lexicon `:const`/`:enum`
(`20-actors/ake/lex/*.edn`), and a Python `ValueError`/refusal (`methods/triage.py` +
`methods/revision.py` + the cell state machines). `methods/test_charter_invariants.py` asserts all
three structurally (not by prose-grep).

## Non-goals

N1 not anonymous open-edit (G1) · N2 the LLM never decides (G2) · N3 no impersonation (G3) ·
N4 no overwrite/deletion of history (G5) · N5 no unsourced edits (G4) · N6 no server-signed edits
(G1) · N7 not an arbiter of legal/criminal truth (danjo/chigiri boundary).

## R0 deliverables (all landed, 71 tests green)

- ontology `community-edit-ontology.kotoba.edn` (closed structural vocab + EAVT schema)
- 6 lexicons `com.etzhayyim.ake.*`
- 5 cells (coded state machines; `.solve()` raises at R0)
- `methods/triage.py` — risk+quality scorer + pure-function router (the G2 anchor)
- `methods/revision.py` — append-only history (append/as-of/current/history_of) +
  non-destructive `:representative→:authoritative` promotion
- `methods/analyze.py` — end-to-end membrane over the `:representative` seed
- `data/seed-edit-graph.kotoba.edn` — 5 edits, one per route
- registered in `INFRA_ACTORS` → `did:web:etzhayyim.com:actor:ake`; actor-profile seed added
- 71 tests (17 triage + 7 revision + 16 charter-invariants + 6 analyze + 5 lexicons + 20 cells)

# Consequences

**Positive.** A member can, for the first time, **propose a correction** to a KG fact or an actor
profile and have it land through transparent, on-chain, signed consensus. The substrate gains the
Wikipedia properties it was missing (open-ish contribution + review workflow) without sacrificing
its stronger ones (immutable history, signed contribution, no impersonation). ake becomes the write
membrane that drives `:representative→:authoritative` coverage honesty for ooyake/kabuto/kanjo/etc.

**Negative / honest.** It is a **permissioned wiki**, not Wikipedia — 信者-gating raises the
contribution bar (deliberately). R0 is design + offline routing/revision only: no live ingest, no
binding vote, no promotion, no publish (all G8). Triage scoring is deterministic at R0; the
Murakumo-only LLM refinement is R1 (the routing stays a pure function regardless). The seed is
`:representative`.

**Invariant posture.** **ZERO amendments.** ake *strengthens* no-server-key (every edit
member-signed), kotoba-canonical-state (append-only, no parallel mutable store), 1 SBT = 1 vote
(now wired to data edits), and the mirror invariant (corrections are observations).

# Alternatives Considered

1. **True anonymous open-edit (full Wikipedia).** Rejected: violates §1.16 conversion-gating + the
   no-server-key invariant; an anonymous edit cannot be member-signed.
2. **Optimistic-append + post-hoc revert (edit-first).** Rejected as the default: a wrong/abusive
   fact would be transiently live. The optimistic fast-path is preserved but *bounded* to low-risk,
   well-sourced, non-invariant edits; everything else routes to a vote before it lands.
3. **Lightweight method on an existing actor (danjo/tsukuroi).** Considered (the user's option 2);
   rejected for R0 because the membrane crosses actor boundaries (any KG actor + profiles) and needs
   its own ontology + gates. tsukuroi/Kaizen remain the propose-only prior art ake generalizes.
4. **LLM auto-merge (the model decides).** Rejected hard (G2): an LLM verdict on what is "true" is
   adjudication; the model may only *score and route*. Acceptance authority is the optimistic rule,
   a 1 SBT = 1 vote, or Council.

# References

- This actor: `/20-actors/ake/` (manifest, CLAUDE.md, README.md, MATURITY.md, cells, methods, lex)
- Ontology: `/00-contracts/schemas/community-edit-ontology.kotoba.edn`
- Mirror invariant: `/90-docs/adr/2606042330-entity-as-actor-society-wide-social-mirror-graph.md`
- No-server-key: `/90-docs/adr/2605231525-server-side-signing-capability-boundary.md`
- Canonical Datom state: `/90-docs/adr/2605312345-kotoba-datom-first-class-canonical-state.md`
- Charter Rider: `/90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md`
- Murakumo-only inference: `/90-docs/adr/2605215000-etzhayyim-inference-murakumo-only-no-runpod.md`
