---
id: adr-2606161800-ugachi-extraction-risk-gate-actor-r0
title: "ADR-2606161800: ugachi (穿ち) — the §2(l) multi-generational extraction RISK-GATE actor (clj-native R0)"
status: accepted
doc_type: adr
topic: ugachi-extraction-risk-gate
authoritative: true
last_verified: 2026-06-16
priority: 7.0
axis: architecture
weight: 0.70
authoritative_for:
  - ugachi actor identity (name, DID, namespace, scope) — clj-native R0
  - the §2(l) extraction-authorization gate as executable code (verdict algebra)
  - extraction gates G1..G9 + non-goals N1..N5 (assessment + R0 design only; never digs)
depends_on:
  - adr-2606161700-multigenerational-extraction-risk-gate
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192245-etzhayyim-global-land-sovereignty
related:
  - adr-2606161730-busshi-commodity-materials-observatory
  - adr-2605252400-kanayama-circular-metallurgy-r0
  - adr-2606051500-kamado-closed-loop-carbon-refining
  - adr-2606073100-abaki-anti-monopoly-intelligence-membrane-r0
supersedes: []
superseded_by: []
---

# ADR-2606161800: ugachi (穿ち) — the §2(l) extraction RISK-GATE actor

**Status**: accepted (R0 landed, clj-native, tests green)
**Date**: 2026-06-16
**Deciders**: Jun Kawasaki

# Context

ADR-2606161700 reframed the Charter's stance on extraction: 採掘・採油は一律禁止ではない
— extraction is gated by a multi-generational (子・孫) × wellbecoming **risk assessment**,
not banned by industry name. busshi 物資 (ADR-2606161730) is the OBSERVATION side of that
axis. **What was still missing is the axis made executable**: the actor that takes a
*specific proposed extraction project* and renders the gate verdict — refuse, route to a
lower-risk recovery path, or permit design.

ugachi 穿ち is that actor. It proves the constitutional change is not a slogan: it can both
**refuse** (a deep-sea-nodule / new-coal / monopoly-entrenching / no-consent project) and
**permit-design** (a reversible, remediated, supply-diversifying, consented project) — by
the *same* measured rule, not by the word "mining". It is the structural counterpart of
kanayama (which does recovery) and the consumer of busshi / rare-earth-coverage
concentration data (the monopoly factor).

The actor is **assessment + R0 design only — it never digs.** There is no actuation method;
live extraction remains Council Lv7+ gated and is never performed by ugachi (consistent with
kanayama's R0 `.solve()` refusal pattern and the no-server-key invariant).

# Decision

## 1. Identity

| Field | Value |
|---|---|
| Name | `ugachi` |
| Japanese | 穿ち (うがち — 穿つ = to bore through / to see through to the truth; the bore + the discernment) |
| DID | `did:web:etzhayyim.com:ugachi` |
| Namespace | `com.etzhayyim.ugachi.*` |
| Repo | `20-actors/ugachi/` |
| License | Apache 2.0 + Charter Compliance Rider v3.2 |
| Kind | extraction risk-GATE (assessment + R0 design; never digs) — clj-native |

## 2. The gate (executable §2(l) verdict algebra)

For a proposed project with factors {irreversibility, remediation, carbon ∈
{net-negative,neutral,positive}, monopoly-effect ∈ {entrench,neutral,diversify},
recovery-alternative ∈ {none,partial,viable}, consent, transparent, descendant-benefit},
`verdict` returns one of `{:refuse :route-to-recovery :propose-r0 :insufficient-evidence}`,
checked in order:

1. **G5** no consent → `:refuse :no-consent` (Tree of Life land sovereignty + community, ADR-2605192245)
2. **G6** carbon `:net-positive` → `:refuse :carbon-positive` (§2(d) fossil→combusted; kamado pattern)
3. **G3** monopoly-effect `:entrench` → `:refuse :monopoly-entrenchment` (§1.12; a project that *diversifies* a chokepoint is favorable, not refused)
4. **G3** `net-irreversibility = irreversibility·(1−remediation) ≥ 0.5` → `:refuse :irreversible-multigen-harm` (§2(d), persons ≥25yr hence)
5. recovery-alternative `:viable` → `:route-to-recovery` (kanayama — recovery-first preference)
6. transparent (on-chain + open-source + 1 SBT = 1 vote) AND descendant-benefit ≥ 0.5 → `:propose-r0` (design-only)
7. else → `:insufficient-evidence`

**Hard refusals precede recovery routing** (a refused project is never "fixed" by routing) —
proven by a meta-invariant test: NO no-consent / carbon-positive / entrenching / irreversible
project anywhere in the seed returns a permit.

## 3. Constitutional gates (G1–G9)

| Gate | Requirement |
|---|---|
| **G1** | **Assessment + R0 design ONLY — never digs.** No actuation/extraction method; `:ugachi/actuate` + `:ugachi/extract` unrepresentable (test-enforced). |
| **G2** | The §2(l) multi-gen (子・孫) × wellbecoming assessment is the SOLE authorization basis; `:ugachi.gate/by-industry-name` unrepresentable (the rule is harm-to-子孫, not the word "mining"). |
| **G3** | Refuse on monopoly entrenchment (§1.12) OR irreversible multi-gen harm (§2(d)); a *diversifying* project is favorable. |
| **G4** | Any permitted project requires Transparent-Force conditions (on-chain monitor + open-source + 1 SBT = 1 vote, §1.12.B). |
| **G5** | Tree of Life land sovereignty + community consent (ADR-2605192245) required; no consent → refuse. |
| **G6** | Carbon-balance per §2(d) (fossil→combusted net-positive → refuse; kamado measured-instance). |
| **G7** | No-server-key; live actuation is Council Lv7+ gated, NEVER by ugachi. |
| **G8** | kotoba Datom-native (EAVT); verdict datoms flagged `:ugachi/derived` + `:ugachi/sourcing`. |
| **G9** | Synthetic seed (`:synthetic`); real-project assessment is an operator/Council step. |

## 4. Non-goals (N1–N5)

- **N1** — never actually extracts/digs/drills (R0 assessment + design; live actuation unrepresentable).
- **N2** — NOT a by-name mining ban AND NOT a rubber stamp: it is a risk gate that genuinely refuses AND genuinely permits-design.
- **N3** — conflict/weapons-mineral sourcing without attestation is out of scope (kanayama N3/N8 echo).
- **N4** — irreversible-biosphere / deep-sea-habitat projects auto-refuse (kanayama N7 echo).
- **N5** — no person-level data; aggregate/project-level only.

## 5. Clj-native files (R0)

```
20-actors/ugachi/
├── CLAUDE.md · README.md · MATURITY.md · manifest.edn · run_tests.sh
├── kotoba/{ontology.ugachi.edn, seed.edn}   # seed = synthetic proposed projects
└── methods/
    ├── ugachi_edn.cljc       # loader + classify
    ├── gate.cljc             # verdict → assess → render-datoms → render-report (+ bb CLI)
    ├── test_ugachi_edn.cljc  # loader tests
    └── test_gate.cljc        # gate verdicts + refusal/structural invariants
```

Run: `./20-actors/ugachi/run_tests.sh` (14 tests / 37 assertions green). On the R0 synthetic
seed: 3 `:propose-r0`, 1 `:route-to-recovery`, 5 `:refuse`, 2 `:insufficient-evidence`.

# Consequences

**Positive** — the §2(l) axis is now executable, not just doctrinal: the same measured rule
refuses catastrophic/monopolistic projects and permits-design the stewarded, diversifying,
consented ones. Closes the loop the founder opened ("採掘を禁止しているわけではない"). Pairs
with kanayama (recovery), busshi/rare-earth-coverage (monopoly input), kamado (carbon),
abaki (de-monopolization), inochi (restoration).

**Negative / deferred** — seed is `:synthetic`; real-project assessment + live actuation are
operator/Council steps (G7/G9). The factor scores are an input model, not a measurement
pipeline (Wave 2 wires busshi/rare-earth-coverage concentration + kamado carbon-balance as
real inputs). The gate is a judgment standard (gameable via optimistic foreseeability) — the
prudent multi-generational steward standard + plaintext-public + Council attestation mitigate.

# Alternatives Considered

1. **Fold the gate into busshi.** Rejected: busshi observes commodities (no project concept); the gate is a distinct project-level decision actor.
2. **Make ugachi an actual mining actor (R1 digging).** Rejected for R0: live actuation is Council Lv7+ + no-server-key; the gate must precede capability (kanayama precedent).
3. **A by-name allowlist of "OK minerals".** Rejected: that is the blanket-ban anti-pattern ADR-2606161700 removed — the rule is the harm-to-子孫 assessment, not the resource's name.

# References

- ADR-2606161700 — multi-gen extraction risk-gate (the axis this actor executes)
- ADR-2606161730 — busshi commodity/materials observatory (concentration input)
- ADR-2605252400 — kanayama recovery (the route-to-recovery target)
- ADR-2606051500 — kamado carbon-balance (the §2(d) measured instance)
- ADR-2605192245 — Tree of Life land sovereignty (G5 consent)
- ADR-2606073100 — abaki anti-monopoly (de-monopolization route)
