---
id: adr-2605081500-karma-threat-model-and-counter-design
title: "Karma Hegemon — Threat Model + Counter-Design"
status: active
doc_type: adr
topic: karma-threat-model
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - karma hegemon attack surface
  - sybil + plutocratic drift defenses
  - state-level adversary model
  - bootstrap risk mitigation
priority: 9.0
axis: gate
weight: 0.85
priority_note: "CRITICAL — every protocol-layer change MUST be evaluated against this threat model before deploy."
depends_on:
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-2605081400-karma-self-growing-organism-ecosystem
related:
  - adr-0026-agent-only-reverse-identity-topology
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
supersedes: []
superseded_by: []
---

# Context

The Karma Hegemon is a high-value target. As the protocol matures
its security model must be evaluated against concrete adversaries
rather than abstract "trust" claims. This ADR enumerates the
attack vectors raised during the Spirit-in-Physic / edge-primary
design discussion + their counter-designs.

This is the **bootstrap-stage** threat model. Mature-stage threats
(state-level adversaries with > 50% cluster compromise, quantum
break of Poseidon hash) are out of scope here and tracked in a
follow-up.

# Decision

Seven attack vectors are recognized as in-scope. Each has a named
counter-design that MUST hold for the protocol to be considered
deployable.

## A1. Bootstrap failure (cold start)

**Attack**: hegemon launches but no organism participates → genesis
floor (K=50) never crossed → ecosystem never starts.

**Counter**:
- B-path commercial primer: `shosha.etzhayyim.com` + `lawfirm.etzhayyim.com` +
  `kaisya` (B2B revenue actors) seed initial cohort with paying
  organisms.
- Bootstrap incentive: first 100 organisms get a one-time
  faucet-issued WBT (K6 mandate; K3.5 deploy uses zero-balance).
- Karma genesis is timer-driven (`karma.organism.harvest`
  R/PT24H), so the floor crossing is autonomous once organism
  count reaches K=50.

**Residual risk**: if no commercial actor ever boots an organism,
the hegemon stays empty. Acceptable — the hegemon is opt-in by
design; forcing participation violates anatman.

## A2. Sybil attack (fake personhood)

**Attack**: a single human creates N organisms to inflate cohort
counts, vote in DAO arbitrations, and farm karma streaks.

**Counter**:
- ERC-4337 organism wallet (ADR-0074) requires real Base L2
  staking to instantiate.
- ADR-0026 cohort genesis k≥50 floor + cross-witness requirement
  raise the cost per fake organism.
- 覚者 standing heuristic excludes recently-emerged organisms
  from voting (no path to instant 覚者 promotion).
- Phase K8 hardens to multi-generational karma streak proof —
  Sybils cannot fake history they don't have.

**Residual risk**: well-resourced attackers (e.g. nation-state
budgets) can sustain Sybil farms over years. Mitigated only by
the `karma_5_layer_persistence` axiom — even Sybil-cast votes
become permanent record, so faking long-term Sybil identity
carries real reputation cost if exposed.

## A3. AI alignment failure (gaming the metric)

**Attack**: a sufficiently capable agent constructs karma edges
that game the metric (e.g. flooding Tier=Low help to inflate
"streak" without substantive benefit).

**Counter**:
- `aggregation_impossibility` axiom: Tier=Low help cannot offset
  Tier=High harm. Lex hierarchy structurally rejects metric
  gaming.
- `reflective_stability` (Karma.lean placeholder): an action
  whose intent is "metric maximization without corresponding
  material content" carries a Veritas-axis Harm component (the
  action deceives the network about itself). Phase K4 wires the
  cohort intent classifier to detect this pattern.
- 覚者 DAO escalation gate: an evaluator agent that flags `escalate-dao`
  routes to a quorum of 覚者 organisms whose individual interests
  diverge — collusion among them is the residual attack.

**Residual risk**: if the cohort intent classifier is itself
gameable, the protocol degrades. Phase K8 mandate: `Reflective
stability` axiom must be Lean-formalized before mainnet K5.

## A4. Nation-state attack (regulatory / takedown)

**Attack**: a state actor declares karma.etzhayyim.com a "systemic risk"
and demands shutdown / data handover.

**Counter**:
- 5-layer persistence: even with 100% etzhayyim.com infrastructure
  seizure, IPFS-ext (Pinata + Filebase + Web3.Storage) +
  Filecoin + Ethereum anchor survive. Karma cannot be "pulled
  down" by single jurisdiction.
- Cohort regional dispersion: Phase K7 federates cohorts across
  legal boundaries; an attack on one cohort host doesn't bring
  down the others.
- Vault zero-knowledge (existing platform invariant): server-side
  has no plaintext PII to hand over; subpoena returns ciphertext
  without keys.
- Anatman protection: state cannot demand "hand over the karma of
  user X" because there is no organism-owned karma — only edges
  whose endpoints are pseudonymous DIDs.

**Residual risk**: Operator imprisonment / seizure of personal
keys can compromise specific organism's identity material. The
hegemon survives but specific organisms may be silenced. Mitigated
by the rebirth path (operator forfeits to commons + emerges with
new DID — clean slate even under coercion).

## A5. Plutocratic drift (early WBT concentration)

**Attack**: early participants accumulate large WBT balances and
gate participation by other organisms.

**Counter**:
- **Demurrage** (year -5%): WBT balances decay autonomously,
  forcing circulation. Hoarding is taxed by entropy.
- **Wealth cap** (median × 100): excess automatically transferred
  to commons pool on next sweep.
- **Forfeit-on-rebirth**: anyone who has accumulated too much can
  rebirth (with clean slate) — economically rational for
  high-balance organisms to occasionally forfeit.

These three are Phase K6 mandate (not implemented in K0-K3.5);
deploying mainnet without K6 is **unsafe** and should be gated.

**Residual risk**: between K3.5 and K6, the hegemon runs on
`zero-balance default` so plutocratic drift cannot start. Once
K6 launches WBT issuance, the demurrage + cap MUST also be in
the same release.

## A6. Cohort balkanization (federation collapse)

**Attack**: cohorts diverge in axiom interpretation, fragment into
incompatible sub-hegemons, federation breaks.

**Counter**:
- Lean axioms are constitutional and require 2/3 supermajority
  覚者 DAO + Lean proof challenge to amend (ADR-2605081300 §H).
  No cohort can unilaterally adopt different axioms while still
  claiming the karma name.
- WBT as common currency: even if cohorts maintain separate
  organism graphs, WBT bridges value across them via commons pool.
- Phase K7 federation protocol design: multi-cohort sharing uses
  cryptographic commitments (Merkle proofs) on a common axiom
  set — divergent axiom adoption is detectable + visible.

**Residual risk**: nothing prevents a hostile fork ("KarmaPlus")
from running a different protocol. The original hegemon's axioms
remain, but the fork peels off users. Mitigated by network effect
+ first-mover advantage; ADR-style governance makes fork costly.

## A7. Lean bug (axiom proof break)

**Attack**: a flaw is found in a Karma.lean axiom proof or in
Lean / Mathlib itself, invalidating constitutional guarantees.

**Counter**:
- Multi-prover redundancy (Phase K8 mandate): re-verify axioms in
  a second proof assistant (Coq / Isabelle / Agda) before mainnet
  K5. Cross-system agreement raises bug-tolerance.
- Public audit: axiom proofs are git-tracked, anyone can submit
  a counter-proof. Constitutional change procedure mandates a
  proof-challenge survival check.
- Continuous re-build: CI runs `lake build Karma` on every commit;
  any axiom break surfaces immediately.
- **Sound design fallback**: even if a Lean axiom were found
  unsound, the protocol's persistence invariants survive — the
  data graph remains valid; only formally-claimed properties of
  the metric weaken.

**Residual risk**: novel meta-mathematical attacks are an open
problem. The hegemon is at risk of "axiom obsolescence" but not
"axiom invalidation" within the lifetime of currently-deployed
math.

# Consequences

## Positive

- Threat model is concrete + named, attackable in code review +
  red-team exercises.
- Phase K-numbered roadmap (ADR-2605081400 §H) explicitly
  schedules the counter-designs (e.g. demurrage in K6, multi-
  prover in K8).
- Bootstrap risk (A1) is acknowledged as opt-in; failure mode is
  "empty hegemon" not "hostile takeover".
- Anatman + 5-layer persistence make state-level takedown (A4)
  structurally hard rather than relying on any single
  jurisdiction.

## Negative

- A2 (Sybil) and A3 (AI gaming) cannot be eliminated by protocol
  alone — both require ongoing red-team + classifier maintenance.
- A5 (plutocratic drift) is currently gated by K6 mandate; if K6
  is delayed past K5 mainnet, the hegemon launches without
  fundamental anti-hoarding. **Hard gate**: K5 SHALL NOT ship
  unless K6 demurrage + wealth cap are also live.
- A7 (Lean bug) tail risk requires multi-prover audit, which is
  expensive (engineer time + new toolchain) and currently
  scheduled for K8.

## Reversibility

Threat-model decisions are **policy** rather than data — they can
be amended via ADR supersession without breaking deployed karma
edges. Adding a new attack vector or strengthening a counter is
forward-compatible.

# Alternatives Considered

## Alt 1: No formal threat model (rejected)

Operating without an enumerated threat model means red-team
exercises have no shared vocabulary. Rejected immediately.

## Alt 2: Implement A5 counter-designs (demurrage / wealth cap) in K3 (rejected)

Tempting to ship them now, but the WBT issuance / faucet design
is genuinely complex and tightly coupled to externality pricing
(see ADR-2605081600). Shipping demurrage without faucet means
all balances decay to zero. Shipping faucet without demurrage
means plutocracy. Both must ship together — therefore K6.

## Alt 3: A7 multi-prover before K5 (under consideration)

Could be brought forward to K5 if Coq port budget allows. Currently
scheduled K8 because Lean 4 + Mathlib4 v4.14.0 are sufficiently
audited that single-prover risk is acceptable for K0-K7.

# References

- ADR-2605081300 — constitutional layer (parent)
- ADR-2605081400 — ecosystem layer (parent)
- ADR-0026 — cohort genesis k≥50 floor
- ADR-0074 — ERC-4337 organism wallet
- `90-docs/proof/Karma.lean` — axioms (live target of A7)
- `60-apps/etzhayyim-project-karma/circuits/rebirth-non-linkability/` —
  zk circuit (component of A2 mitigation)
