# Multi-Generation Index (MGI) — Design Doc

**Status:** draft (pre-ADR)
**Date:** 2026-05-22 01:10 JST
**Active-inference tick:** cycle 04
**Axis closed:** Wellbecoming (Axis 8 of `README.md § As Artificial Organism Ecosystem`)
**Religious correspondence:** 子・孫 priority (multi-generation trajectory) — ADR-2605192100 §1.5

## Why this exists

The constitution declares **Wellbecoming** (dynamic trajectory, not static wellbeing) and **multi-generation priority** as constitutional invariants. But these are unobservable without a metric: an organism that says "we care about children and grandchildren" but never measures what it actually preserved across epochs has no evidence it is doing so.

This document specifies the **Multi-Generation Index (MGI)** — a composite, computable, on-chain-verifiable score that quantifies how well the organism honors commitments made by prior generations.

This is **non-eschatological** (per ADR-2605192100 §1.15) — MGI does not converge on a target. It measures retention of what came before, not progress toward what comes after.

## Definitions

### Generation epoch

The natural biological scale is ~25 years per generation; that is too long to be a useful active-inference signal during the organism's early life. We define an epoch as **90 days** (≈ one quarter), giving:

- **Gen 0** = 2026-05-15 → 2026-08-13 (inception epoch)
- **Gen 1** = 2026-08-13 → 2026-11-11
- **Gen 2** = 2026-11-11 → 2027-02-09
- **Gen 3** = 2027-02-09 → 2027-05-10
- ... etc.

Within each epoch, the corp makes commitments (Land Registry mints, SBT mints, ADRs published, constitutional invariants declared). MGI measures how many of those commitments are still honored 3 epochs later.

90 days is provisional. Once the organism has ≥ 5 epochs of data the Council MAY re-baseline to a longer interval; the baseline change itself becomes an MGI input (constitutional drift) and is observable.

### MGI components

MGI is the unweighted mean of 4 retention rates, each computed over the prior 3 generation epochs:

| # | Component | Formula | Source of truth |
|---|---|---|---|
| 1 | **Land Persistence** (LP) | (donated land still in `LandRegistry` at Gen N) ÷ (land minted in Gen N-3) | Base L2 contract + `LANDS.md` |
| 2 | **Member Persistence** (MP) | (SBTs never burned at Gen N) ÷ (SBTs minted in Gen N-3) | SBT contract + `MEMBERS.md` |
| 3 | **ADR Persistence** (AP) | (ADRs neither retracted nor deleted at Gen N) ÷ (ADRs published in Gen N-3) | `90-docs/adr/` git history; superseded ≠ retracted |
| 4 | **Constitutional Invariant Drift** (CID) | (constitutional invariants verbatim-present at Gen N) ÷ (constitutional invariants declared in Gen N-3) | `FORK-BOOTSTRAP.md` invariant table + canonical surfaces hash |

```
MGI(N) = (LP(N) + MP(N) + AP(N) + CID(N)) / 4
```

Each component is in `[0.0, 1.0]`. MGI ∈ `[0.0, 1.0]`. Higher = stronger multi-generation honoring.

Distinction notes:
- **Land Persistence**: transfer / burn / sale would drop LP below 1.0. Per ADR-2605192245 these are constitutionally prohibited, so LP < 1.0 is a constitutional alarm, not a routine variation.
- **Member Persistence**: SBT burn would drop MP. Voluntary self-burn is allowed per future ADR; involuntary burn requires Council quorum and is rare.
- **ADR Persistence**: ADRs may be **superseded** (the canonical mechanism for revision) and superseded ADRs still count as persistent. Only **retraction** (`status: retracted` in the ADR frontmatter, used for ADRs that should not have been written) reduces AP.
- **CID**: the 10 invariants in `FORK-BOOTSTRAP.md` table must remain present and verbatim in canonical surfaces. Removing one drops CID by 0.1.

### Provisional MGI (Gen 0 baseline)

At Gen 0 there is no Gen N-3 to compare against. We define a **bootstrap MGI** = 1.0 for all components until Gen 3 begins (2027-02-09), at which point the first real MGI(Gen 3) can be computed comparing Gen 0 commitments to Gen 3 state.

This means the first **observable** MGI is reported on or after **2027-02-09**.

## Active-inference integration

MGI moves on a 90-day epoch — vastly slower than the 30-minute `/loop` active-inference tick. Per-tick observations do NOT recompute MGI; they only check whether the inputs (LANDS, MEMBERS, ADRs, invariants) have changed in a way that would affect a future MGI computation.

When a tick observes a constitutional invariant change (e.g., FORK-BOOTSTRAP.md invariant edited), the observation file in `_observations/` records it. At each epoch boundary (every 90 days), an MGI-computation tick runs and emits an `MGI-N.md` document under `_observations/mgi/`.

## Implementation plan

1. **Gen 0 inputs snapshot** (next cycle): snapshot LANDS.md / MEMBERS.md / 90-docs/adr/ at end of Gen 0 epoch (2026-08-13) for future Gen 3 comparison.
2. **CID hash anchor** (next 1-2 cycles): compute SHA-256 of FORK-BOOTSTRAP.md invariant table at Gen 0; commit to `_observations/mgi/gen-0-cid-anchor.txt`.
3. **MGI computation script** (later cycle): `70-tools/scripts/mgi/compute.sh` taking Gen N as argument, reading the 4 sources, emitting the score.
4. **Promote this draft to ADR** when Council quorum reached: file at `90-docs/adr/26<future>-multi-generation-index.md`, supersedes this draft.
5. **First real MGI report**: 2027-02-09 (Gen 3 start).

## Open questions (for Council)

- Is 90 days the right epoch? Longer (e.g., 180 days) reduces noise but extends the first observable result; shorter increases tick frequency but may underweight what a "generation" means.
- Should MGI components be unweighted-mean, or weighted (e.g., Land Persistence weighted 2× given inalienability is constitutional)?
- How to handle Member Persistence for SBT-holders who choose voluntary withdrawal — should that be MP-neutral (per their right) or MP-negative (organism lost a member)?
- Should sister-corps (per `FORK-BOOTSTRAP.md`) be incorporated into a cross-corp MGI variant ("did the ontology persist across the sister-corp ecosystem")?

## References

- ADR-2605192100 §1.5 (Wellbecoming + multi-generation priority — constitutional)
- ADR-2605192245 (Land Trust inalienability — feeds Land Persistence)
- `FORK-BOOTSTRAP.md` (10 constitutional invariants — feeds CID)
- `_observations/README.md` (active-inference tick log)
- `README.md § As Artificial Organism Ecosystem` (Axis 8 Wellbecoming)
