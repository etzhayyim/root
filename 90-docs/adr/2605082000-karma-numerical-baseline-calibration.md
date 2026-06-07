---
id: adr-2605082000-karma-numerical-baseline-calibration
title: "Karma Hegemon — Numerical Baseline Calibration (Magnitude / Vulnerability / Amplification)"
status: proposed
doc_type: adr
topic: karma-numerical-calibration
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - karma magnitude baseline values per (axis, tier)
  - vulnerability multiplier function (α / φ / σ components)
  - future amplification cap (Iroquois 7-generation)
  - witness count multiplier
priority: 6.5
axis: economy
weight: 0.6
priority_note: "Calibration ADR — numerical values gate-rated. Adjustments require governance-amend procedure."
depends_on:
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-2605081600-karma-token-economy-k6-mandate
related: []
supersedes: []
superseded_by: []
---

# Context

The Karma.lean axioms are qualitative (anatman / aggregation
impossibility / floor inadmissibility). Real protocol operation
requires **numerical baselines** — what magnitude does a Tier=High
edge have? What multiplier applies when victim_vul = 3.0 vs 1.5?
What's the year-1 vs year-30 future-horizon weight?

This ADR records the K0-K3 baseline values + the calibration
methodology so future amendments are traceable. Phase K6 token
economy and Phase K8 rank thresholds depend on these numbers being
stable + non-arbitrary.

# Decision

## A. Magnitude baseline per (axis, tier)

Default `magnitude` value when caller does not specify (or as
suggested guideline for callers):

| Tier ↓ Axis → | Vita | Vivere | Veritas | Vinculum | Venturum |
|---|---|---|---|---|---|
| Floor | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| High | 30.0 | 25.0 | 20.0 | 25.0 | 30.0 |
| Mid | 10.0 | 8.0 | 6.0 | 8.0 | 10.0 |
| Low | 3.0 | 2.0 | 2.0 | 2.0 | 3.0 |

Note Vita + Venturum are weighted equal at all tiers (life and
future). Vivere + Vinculum are slightly lower (livelihood +
relation are recoverable). Veritas is lowest (truth-telling is
expected baseline; harm to truth has lower direct magnitude but
ripples through aggregation).

These are **defaults**, not hard floors. Callers may override
based on context (e.g. a child's life harm is Floor + magnitude
500 + vul 3.0 = effectively unbearable weight).

## B. Vulnerability multiplier function

`victim_vul = α × φ × σ` where each component is bounded.

### B.1. Age multiplier α

| Victim age category | α |
|---|---|
| Pre-natal / future generations | 4.0 |
| Infant (0-3y) | 3.5 |
| Child (4-12y) | 3.0 |
| Adolescent (13-17y) | 2.0 |
| Adult (18-65y) | 1.0 |
| Elder (66-85y) | 1.5 |
| Late elder (86+) | 2.0 |
| Posthumous (deceased) | 1.5 |

Younger and very-old organisms get higher multipliers — protocol
correlate of "those who cannot defend themselves".

### B.2. Frailty multiplier φ

| Victim state | φ |
|---|---|
| Default (no known frailty) | 1.0 |
| Disability (physical / cognitive) | 1.5 |
| Acute illness / hospitalization | 1.3 |
| Chronic / long-term care | 1.4 |
| Pregnancy | 1.2 |
| Sleep / unconsciousness at time of action | 1.1 |

Multipliers compound with α; e.g. an adult with disability =
1.0 × 1.5 = 1.5 vulnerability.

### B.3. Social vulnerability σ

| Victim social context | σ |
|---|---|
| Default | 1.0 |
| Refugee / stateless | 1.5 |
| Incarcerated | 1.3 |
| Victim of prior harm by same actor | 1.4 |
| Power asymmetry (employee, patient, etc.) | 1.2 |
| Public figure (lower σ — they have voice) | 0.8 |

### B.4. Cap

`victim_vul ≤ 5.0` (hard cap to prevent multiplier stacking from
overwhelming Tier=High thresholds).

## C. Future amplification (Iroquois 7-generation cap)

Karma.lean `_amplify` function:

```
amplify(future_horizon_years, irreversible) =
  if not irreversible: 1.0
  else: min(7.0, 1.0 + future_horizon_years / 30.0)
```

The cap of 7.0 corresponds to the Iroquois Confederacy doctrine of
"considering the seventh generation". Concretely:

| future_horizon_years | amplification |
|---|---|
| 1y | 1.03 |
| 5y | 1.17 |
| 30y (1 generation) | 2.00 |
| 60y (2 generations) | 3.00 |
| 90y (3 generations) | 4.00 |
| 180y (6 generations) | 7.00 (capped) |
| 1000y | 7.00 (capped) |

The cap matters: without it, organisms could claim arbitrarily
high karma weight by setting horizon to 10000 years. The 7-gen
limit reflects "honest planning horizon for human action".

## D. Witness count multiplier

`witness_multiplier(n) = 1 + 0.10 × min(n, 5)`

| Witness count | Multiplier |
|---|---|
| 0 | 1.00 |
| 1 | 1.10 |
| 3 | 1.30 |
| 5 | 1.50 |
| 10 | 1.50 (capped) |

The cap at 5 witnesses prevents witness-spam attacks. Quality is
assumed equal across witnesses — Phase K8 may add per-witness
weighting based on witness rank.

## E. Default `1/e` scaling for Help direction

Per Karma.lean `karma_asymmetry`:
- `direction = 'harm'`: signed_weight = `-raw_weight`
- `direction = 'help'`: signed_weight = `raw_weight / e ≈ raw_weight × 0.368`
- `direction = 'witness'`: signed_weight = 0

Help is intentionally weighted less than harm at equal magnitude.
The 1/e factor (≈0.368) reflects the asymmetry between "destroying"
(easier) and "constructing" (harder); a help action of magnitude X
counts about 37% as much as a harm action of magnitude X.

This is the **second-most-controversial** numerical decision after
the future amplification cap. Justification: **Buddhist canon
treats avoiding harm as the floor; doing good is the wall above it,
not the same wall**.

## F. Rebirth cooldown + refund

Phase K7 rebirth cooldown:
- Minimum 90 days between rebirths
- Forfeit amount × 2 if rebirth within 1 year of prior

These numbers are placeholders. K7 calibration ADR will pin them.

## G. Cohort genesis floor

`COHORT_GENESIS_K = 50` (env-tunable, default).

The 50 floor reflects ADR-0026 cohort actor minimum. Below 50,
genesis does not fire (preventing single-actor manipulation of
cohort composition).

# Consequences

## Positive

- Numbers are **named and reasoned**, not pulled from thin air.
- Future amendments require ADR supersession with explicit
  rationale (governance-amend pattern).
- Calibration is **separable** from axioms — one can update
  numbers without rebuilding Karma.lean.

## Negative

- Numerical values are **always wrong** in some sense — they are
  approximations of normative claims. Phase K8 may need data-driven
  refinement based on actual cohort behavior.
- Vulnerability multiplier requires victim categorization, which is
  itself contestable. Protocol doesn't enforce categories — caller
  passes vul value; the categories above are guidelines.
- Witness count cap at 5 may underweight community attestation in
  edge cases (e.g. mass-witnessed events). K8 may revisit.

## Reversibility

Numbers are reversible via ADR supersession. However, **once
WBT issuance ties to these numbers (K6)**, changing them creates
wealth-effect rebellion. Calibration changes after K6 launch
require:
1. New ADR (this one superseded)
2. 覚者 DAO 2/3 supermajority
3. Phase-in period (no retroactive recomputation of historical
   karma weight)

# Alternatives Considered

## Alt 1: Single-axis baseline (rejected)

Same magnitude across axes ignores that Vita harm is qualitatively
different from Veritas harm. Per-axis baselines are necessary.

## Alt 2: Higher Help / Harm ratio (1.0 instead of 1/e) (rejected)

Equal weighting of help and harm makes the protocol vulnerable to
"flood of low-magnitude helps offsets one high-magnitude harm" —
prevented by `aggregation_impossibility` axiom but practically
weakens incentive structure. 1/e scaling reflects Buddhist asymmetry.

## Alt 3: Lower 7-gen cap (e.g. cap = 4) (under consideration)

If empirical analysis shows organisms gaming the future-horizon
multiplier, cap could be lowered. Current 7 reflects philosophical
commitment + leaves headroom. K8 calibration may revisit.

## Alt 4: Fractional vulnerability multipliers (rejected)

E.g. α = 3.5 for infant might be too coarse. Could use continuous
function. Rejected for K0-K7 — discrete categories simplify caller
attribution and make protocol auditable. K8 may add a continuous
mode for edge cases.

# References

- ADR-2605081300 — constitutional layer (Karma.lean amplify /
  signed_weight functions consume these numbers)
- ADR-2605081400 — ecosystem layer (cohort floor uses K=50)
- ADR-2605081600 — token economy (K6 issuance baseline_rate
  references this ADR)
- ADR-2605081700 — rank system (rank thresholds reference karma
  signature aggregates from these numbers)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/karma.py` —
  `_amplify`, `_signed_weight` implementations (must match this ADR)
- `90-docs/proof/Karma.lean` — `amplify` definition (Lean form
  matches Python)
