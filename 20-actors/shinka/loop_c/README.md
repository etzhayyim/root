# Shinka Loop C R0 — architecture-evolution harness (ranking only)

Implements **R0** of ADR-2606172200 (Loop C): rank the *existing* weight family on the
**real measured fitness** from this session — invents no architecture, promotes nothing.

- `genotypes.edn` — the 4 family genotypes (AR `maxwell-1` / `maxwell-diffusion-1` /
  `oka-mmsheaf` / `baien-1.58`) + fitness fields holding **only measured values or nil**
  (nil = not measured → ranked `insufficient-evidence`; no fabrication, D5/D6).
- `rank.clj` — pure-data ranker: tiered cost-gated fitness (weights Σ=1.0, renormalised
  over present terms), requires the t2 task signal (`microbench`) to be scoreable, Elo/score
  over the comparable cohort, route ∈ `{:propose-candidate :insufficient-evidence :excluded}`.
  Emits `scorecard.edn` + `scorecard.md` (the PR-draft artifact). `bb rank.clj`.
- `rank_test.clj` — invariants: Σweights=1.0, **no-fabrication** (unmeasured→insufficient),
  scoreable→propose, ranking order, oka(R0) never scored. `bb rank_test.clj` (ALL PASS).

## Current R0 result (`scorecard.md`)

Only `maxwell-diffusion-1` has a measured task signal (e7m micro 0.80) → `propose-candidate`
(score 0.640). `maxwell-1` (loss-landscape + train-loss measured, but no microbench),
`oka-mmsheaf` (R0 scaffold, no weights), `baien-1.58` (not benched) → `insufficient-evidence`.

This is the honest R0: the harness runs and ranks on real evidence; most of the family
needs more measurement before Loop C could propose an architecture. **Promotion of any
candidate to a trainable/deployable target is member-CACAO-gated** (ADR-2606172200 D5) —
this harness only scores and drafts.

### Next (R1, leash-gated)
Fill the missing t2 signals (bench `maxwell-1`/`baien` on e7m micro; measure tok/s) so the
cohort is comparable; then the Co-scientist `propose`/`recombine` cells over **novel**
genotypes (config genes + merge recipes) — only behind a member-signed capability.
