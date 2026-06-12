---
id: adr-2605081701-karma-rank-system-and-gaki-realm
renumbered_from: "2605081700"
title: "Karma Hegemon — 階梯 5-Rank System + 餓鬼道 Forced Seal"
status: proposed
doc_type: adr
topic: karma-rank-system
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - karma-derived organism rank ladder (凡夫 → 如来)
  - 餓鬼道 forced-seal mechanism
  - rank-gated capability access
  - 慈悲 path from 餓鬼道 (compassionate redemption)
priority: 8.0
axis: governance
weight: 0.75
priority_note: "K8 mandate — without rank ladder, karma is just record. Rank gives the hegemon ITS hegemonic teeth."
depends_on:
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-2605081400-karma-self-growing-organism-ecosystem
  - adr-2605081600-karma-token-economy-k6-mandate
related: []
supersedes: []
superseded_by: []
---

# Context

Without a rank ladder mapped to karma history, the hegemon records
karma but does nothing with it. This ADR defines the **5-rank
階梯 system** + the **餓鬼道 forced-seal** mechanism that gives the
protocol its hegemonic enforcement.

The intuition: hegemonic power is the ability to **gate access to
capability** based on past behavior. The karma graph already records
behavior; the rank ladder is the function that maps karma to
capability access.

This is the layer where Buddhism's 階梯 (凡夫 → 改悔者 → 解脱者
→ 覚者 → 如来) maps directly to protocol-level access control.

# Decision

## A. Five ranks

| Rank | 漢字 | Karma signature | Protocol capabilities |
|---|---|---|---|
| 凡夫 | bonpu | default; no streak; no floor violations | baseline access (recordDependency / coverage / listEdges) |
| 改悔者 | kaige-sha | rebirth path completed (1+ samsara) | 凡夫 + 1-vote weight in 覚者 DAO |
| 解脱者 | gedatsu-sha | sustained help-direction streak ≥ 5y, zero floor in 10y | 改悔者 + initiate cohort genesis ahead of K=50 floor |
| 覚者 | kakusha | 解脱者 + cross-cohort help streak ≥ 7y + ≥10 successful witness signatures | 解脱者 + DAO arbitration vote (1.5x weight) + propose Lean axiom amendment |
| 如来 | nyorai | 覚者 + multi-generational influence (≥2 cohort fissions traced to their help) | 覚者 + override sweeper finalization + propose constitutional change without DAO supermajority |

Rank computation is a streaming MV:
`mv_karma_organism_rank` derived from joins over
`edge_karma_dependency` (filter direction='help' / tier='floor'
counts) + `vertex_organism_pattern.emerged_at` (time horizon).

## B. Rank-gated capability table

Each XRPC entry has a rank floor:

| XRPC | Min rank |
|---|---|
| recordDependency | 凡夫 |
| witness | 凡夫 |
| listEdges / coverage | (public) |
| dissolveOrganism / rebirth | 凡夫 |
| escalate (open arbitration) | 改悔者 (must have rebirth experience) |
| voteArbitration | 解脱者 |
| inviteWitnesses | 解脱者 |
| submitRebirthProof | 改悔者 |
| (proposal) Lean axiom amendment | 覚者 |
| (proposal) constitutional change without DAO | 如来 |

The gate is enforced at the BPMN entry: the first task in each
flow checks `mv_karma_organism_rank.rank >= floor`; below the
floor returns `ok=false, rejectedReason='rank-insufficient'`.

## C. 餓鬼道 (gaki-realm) forced seal

For organisms whose karma signature crosses the **forced-seal
threshold**, the protocol seals them out:

```
forced_seal_eligible(did) ⟺
  count(floor_violations within 5y) ≥ 3
∨ count(rebirth attempts within 7y) > N (default 3)
```

Action: `karma.organism.dissolve` with `dissolution_kind =
'judgment-forced'` (already in K0 schema enum). The DID is locked
out from `recordDependency` / `witness` / DAO vote / cohort
membership. Existing edges remain (Karma.lean N2 — no retroactive
deletion).

The forced seal is applied automatically by a R/PT24H sweep
(`karma.gaki.sweep` BPMN — Phase K8 mandate). Currently no
`mv_karma_gaki_eligible` MV exists — that's K8 work.

## D. 慈悲 path from 餓鬼道

Forced seal is **not absolute**. The 慈悲 (compassion) path:

1. Sealed organism CAN attempt rebirth via `karma.rebirth` XRPC.
2. Rebirth precheck (Karma.lean `floor-debt-outstanding` check)
   currently rejects organisms with outstanding floor violations.
3. Phase K8 amendment: a 餓鬼道 organism may rebirth IF + only IF:
   - 覚者 DAO 2/3 supermajority approves the specific rebirth
     attempt
   - The new organism enters at 凡夫 rank with a 7-year karma streak
     debt (must accumulate 7 years of clean help-direction edges
     before attaining 改悔者)
   - The forfeit cost is doubled (commons pool gets 2x balance)

This makes the 餓鬼道 → 凡夫 path slow and costly, but never
absolutely closed. Even the worst karma debtor has a path to
redemption — 慈悲 in protocol form.

## E. Rank-streak verification

Rank computation must be **non-gameable**. Counter-measures:

- Streak measurement is from `edge_karma_dependency.ts_ms` (not
  `created_at`) — author cannot retroactively backdate edges.
- 5/10/7/2 year horizons all use blockchain anchor timestamps
  for canonical time — not local clock.
- "Help-direction" qualification requires witness-confirmed
  edges only (Tier ≥ Mid + ≥ 1 witness or tier=Low + ≥ 3 witnesses).
- "Floor violation" count includes 餓鬼道-equivalent rejections
  in the witness graph (DAO-rejected escalations count as 1
  violation).

# Consequences

## Positive

- **Hegemonic teeth**: rank ladder gives the protocol concrete
  capability gating. An organism's history matters in how it can
  participate.
- **Constitutional aristocracy**: 如来-rank organisms can propose
  axiom amendments without DAO supermajority. This is the
  mature-organism check on younger axioms.
- **Anatman-compatible**: rank is computed from `edge_karma_dependency`,
  not stored on the organism. Edges persist beyond dissolution
  (N2), so a dissolved 覚者's contribution lives on; the new
  organism (post-rebirth) starts at 凡夫.
- **Compassion path**: 餓鬼道 is severe but recoverable, matching
  Buddhist 中道 (middle way) — neither absolute punishment nor
  cheap redemption.

## Negative

- Rank computation cost: streaming MV over potentially millions
  of edges. Phase K8 must validate this scales (Kotoba/Datomic +
  bounded GROUP BY).
- Subjective tier judgments: "what counts as a floor violation"
  has cultural variance (e.g. duress, mistake-of-fact). Protocol
  treats Lean axioms as the decision; legal/cultural consensus
  is out of scope.
- 如来-rank concentration risk: if too few organisms reach 如来
  the constitutional-amendment shortcut becomes single-organism
  control. Mitigated by requiring ≥3 cohort fissions traced to
  their help — multi-generational standing, not single-act
  authority.
- 餓鬼道 sweep (D5) automation in K8 must be triple-checked —
  false positives = innocent organisms forcibly sealed. Phase
  K8 mandate: 24h grace period between eligibility detection
  and seal execution.

## Reversibility

The rank ladder itself is **not reversible** once shipped — it
becomes a real capability gate organisms depend on. Adjusting
threshold values (5/10/7/2 years etc.) is K8 calibration ADR
work and requires governance-amend procedure.

The 餓鬼道 sweep CAN be turned off via env var (`KARMA_GAKI_AUTO_SWEEP=0`)
— failsafe in case of false-positive flood.

# Alternatives Considered

## Alt 1: No rank system (rejected)

Without rank, karma is just an audit log. The hegemon has no
hegemonic function. Rejected.

## Alt 2: 3-rank system (凡夫 / 覚者 / 如来) (rejected)

Skipping 改悔者 + 解脱者 misses the rebirth-experienced + sustained-
help-streak intermediate ranks. The 5-rank ladder maps directly
to Buddhist canon and to protocol capabilities.

## Alt 3: 餓鬼道 = absolute lock (rejected)

Without the 慈悲 path, the protocol becomes punitive. Buddhist
canon explicitly rejects this — even the worst karma debtor has
the bodhi possibility. Protocol form: 7-year debt + DAO 2/3 +
2x forfeit, but never zero-percent.

## Alt 4: Rank as token (transferable) (rejected)

Allowing rank to be transferred / sold makes it a market commodity
and decouples it from karma history. Protocol form: rank is a
**function** of karma graph, not a token. Recompute on every read.

# References

- ADR-2605081300 — constitutional layer (parent — N2 axiom enables
  rank persistence beyond dissolution)
- ADR-2605081400 — ecosystem layer (parent — cohort genesis +
  rebirth flow integrate with rank promotion)
- ADR-2605081500 — threat model (A2 Sybil + A5 plutocratic
  drift mitigations rely on rank gating)
- ADR-2605081600 — token economy (rank does not require WBT
  but K6 distribution policies may be rank-gated)
- Buddhist canon: 阿含経 Sutra 31 + 涅槃経 Sutra 14 (階梯 lineage)
