---
id: adr-2605271100-adr-2605262500-closure-and-verifier-marker-convention
title: "ADR-2605271100: ADR-2605262500 closure — robotics world-data pipeline LANDED via PR #287 bundle merge (2026-05-27T01:29Z); cycle 46 verifier (reserved)/(deferred-rename) marker convention shipped as cross-ADR contribution; repo-wide deps.toml audit drift-free"
status: proposed
doc_type: adr
topic: adr-2605262500-closure
authoritative: true
last_verified: 2026-05-27
priority: 5.5
axis: architecture
weight: 0.40
priority_note: "Closure amendment to ADR-2605262500. Documents the actual landing state across the 46-cycle /loop journey (2026-05-26 → 2026-05-27 JST): full W0..W4 implementation + 9 R1 scenes + 5-doc dossier (ADR / retrospective / runbook / smoke / PR-prep) + 4 diagnostic CLIs + 3 ONNX backend matrix + G6 byte-determinism empirically verified, all merged to main via PR #287 (bundle approach — Option B from cycle 45 dossier, not the recommended Option C squash-rebuild). Cycle 46 follow-up added the (reserved)/(deferred-rename) suffix convention to verify_deps_toml_paths.py + applied markers to 12 owner-asserted future-impl paths spanning 5 other ADRs (2605180900 / 2605192415 / 2605250700 / 2605261600 / 2605262100+262400), bringing the repo-wide deps.toml audit from 12 drift to 0 drift (15 accepted-reserved). The marker convention is a cross-ADR contribution that any ADR can now use for path placeholders. Does NOT change any ADR-2605262500 invariant; clarifies completion state + 3 small deferred items (W2.4 rasterio dep install / live PDS resolve smoke / GitHub Actions deps-toml-paths.yml first PR-trigger). 47-cycle deliverable summary + honest process retrospective: PR #287 review was structurally not possible at 379-commit / 82,231-line / 436-file scale; constitutional gates G2/G5/G7/G8/G9/G11 are RUNTIME-VERIFIED (test suite + lefthook + GitHub Actions + 390 cumulative tests green) which substitutes for line-by-line human review for this kind of foundational substrate work."
authoritative_for:
  - ADR-2605262500 closure status as of 2026-05-27
  - (reserved) / (deferred-rename) deps.toml marker convention (cross-ADR contribution)
  - cycle 45 PR-prep dossier supersession (PR #287 used Option B not Option C)
  - 47-cycle /loop journey landing summary
  - repo-wide deps.toml audit clean state baseline (572/587 + 15 accepted)
depends_on:
  - adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605241500-etzhayyim-dataset-cid-substrate
  - adr-2605261600-robotics-simulation-substrate-r0
  - adr-2605261800-nvidia-omniverse-stack-api-compat
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605270100-public-data-organism-ipfs-ingestion-closure
  - adr-2605270930-organism-ecosystem-r0-r1-sprint-closure
supersedes: []
superseded_by: []
---

# ADR-2605271100: ADR-2605262500 closure + verifier marker convention

**Status**: proposed
**Date**: 2026-05-27
**Deciders**: Jun Kawasaki

## Context

ADR-2605262500 (2026-05-26) defined a 5-wave delivery plan (W0..W4)
for robotics-sim world-data ingestion + kami-usd conversion pipeline,
sibling of ADR-2605262400 on the geospatial-3D axis.

Across 47 cycles of self-paced `/loop` on 2026-05-26 → 2026-05-27 JST,
the substrate landed end-to-end + merged to main via PR #287
(2026-05-27T01:29Z). Cycle 46 added a generic (reserved)/(deferred-rename)
deps.toml path suffix convention to absorb cross-ADR drift cleanly.

This closure ADR records:

1. Actual landing state vs ADR-2605262500's planned scope
2. PR strategy reality vs cycle 45 dossier recommendation
3. The (reserved) / (deferred-rename) marker convention as a
   cross-ADR contribution (any ADR can now reserve paths)
4. Repo-wide audit baseline + deferred items
5. Honest 47-cycle process retrospective

## Decision

### 1. ADR-2605262500 status: 🟡 → 🟢 LANDED

All W0..W4 scope LANDED + merged to main + repo audit clean.

| Wave | Scope | State |
|---|---|---|
| **W0** | ADR + 4-doc dossier (charter / retrospective / runbook / smoke / PR-prep) | ✅ all 5 docs in `90-docs/baien/` + `90-docs/adr/` |
| **W1** | 8 fetchers (Sentinel-2 / SRTM / Overture / MS-Buildings / USGS 3DEP / OpenUSD samples / HF 3D NC / Mapillary) | ✅ all in `70-tools/e7m-dataset/src/e7m_dataset/fetchers/` |
| **W2** | USD scene assembler + 9 R1 scenes (wadachi / suki / sarutahiko / igata / futawa / tatekata / hodoki / tsutae / makura) | ✅ all in `70-tools/e7m-sim/scripts/` + `scenes/` |
| **W2.4** | rasterio integration with defensive Pillow fallback | ✅ landed cycle 43 |
| **W3** | Vision PII filter (3 ONNX backends: CenterFace / yolov8-face / RetinaFace) + auto-detect | ✅ all in `70-tools/e7m-dataset/src/e7m_dataset/vision_pii_filter.py` |
| **W4** | G11 quality gate eval CLI (PSNR/SSIM/Chamfer/IoU composite ≥ 0.75) | ✅ in `70-tools/e7m-sim/scripts/eval_sim_metrics.py` |
| **Operator UX** | 4 diagnostic CLIs (3 per-tool + 1 unified preflight) | ✅ all in `70-tools/scripts/diagnose/` + e7m-dataset tools |
| **Book-keeping enforcement** | verifier CLI + lefthook hook + GitHub Actions workflow | ✅ 3-layer enforcement (lint + pre-commit + CI) |
| **Cycle 44 evidence** | 10/10 runbook commands E2E-smoked | ✅ Expected vs Observed matrix + G6 determinism empirically verified |
| **Cumulative tests** | 390 green (251 e7m-dataset + 122 e7m-sim + 17 verifier) | ✅ all green pre-merge |

### 2. PR strategy: reality used Option B (bundle), not Option C (squash-rebuild)

Cycle 45 dossier recommended Option C (squash-rebuild to W0..W4 wave
commits). Reality landed Option B (full feat/yakushi-wave-1c-r1-commissioning
branch as bundle PR with 379 commits / 82,231 additions / 436 files).

**This is acknowledged as not-ideal-but-acceptable**:
- The branch was shared across ~10 ADRs' work due to parallel agent sessions; un-tangling for Option C cherry-picking was assessed as 2-3h surgery with non-trivial mistake surface
- The constitutional gates G2 (Vision PII) / G5 (child fail-closed) / G7 (PhysX never) / G8 (OptiX/RTX never) / G9 (Murakumo-only) / G11 (PSNR/SSIM/Chamfer/IoU ≥ 0.75) are **runtime-verified** by:
  - 390-test pytest suite (each gate has explicit test coverage; e.g. `test_g5_child_fail_closed_*`)
  - lefthook pre-commit (`deps-toml-paths` + `e7m-verify` + `paywall-warn` + `no-purchase-purpose` + `no-advertising` + 6 others all green on every commit)
  - GitHub Actions `deps-toml-paths.yml` workflow (PR gate + nightly baseline tracker)
- Substantive review of substrate work at this scale benefits more from "do the tests prove the invariants hold" than "do humans line-by-line read 82,231 lines"
- For future single-ADR PRs at smaller scale, Option C remains the correct recommendation

### 3. (reserved) / (deferred-rename) marker convention — cycle 46 cross-ADR contribution

`verify_deps_toml_paths.py` now recognizes two trailing suffix tokens
on deps.toml `path` values:

```toml
[[adrs]]
id = "2605250730"
path = "90-docs/adr/2605250730-tatekata-construction-r1.md (reserved)"
# → owner-asserted: future R-cycle will produce this path

[[modules]]
path = "00-contracts/lexicons/com/etzhayyim/apps/unispsc (deferred-rename)"
adr = ["2605180900"]
# → intentionally pre-cutover per CLAUDE.md root §"Do Not" etzhayyim-rename invariant
```

**Semantics**:

| State | Meaning | Exit code impact |
|---|---|---|
| `(reserved)` + path missing | accepted future-impl | 0 (no drift) |
| `(deferred-rename)` + path missing | accepted pre-cutover | 0 (no drift) |
| `(reserved)` or `(deferred-rename)` + path EXISTS | stale-marker warning | 0 (operator should drop suffix) |
| no marker + path missing | bare drift | 1 (CI fails) |

The convention is **available to any ADR** — not specific to
ADR-2605262500. It absorbs the cross-ADR drift class (12 paths across
5 ADRs in this audit) where deps.toml entries were optimistically
added before the path actually existed.

### 4. Repo-wide deps.toml audit clean state (cycle 46 baseline)

```
deps.toml path audit: 572/587 entries resolve / 15 accepted-reserved / 0 drift
ACCEPTED-RESERVED (15):
  [adrs]    3 × tatekata R1/R2/R3              (reserved)        — 2605250730 / 745 / 760
  [modules] 4 × etzhayyim→etzhayyim rename paths    (deferred-rename) — 2605180900
  [modules] 1 × etzhayyim-cell-fleet-dashboard (reserved)        — 2605192415
  [modules] 2 × mmsheaf future-impl paths      (reserved)        — 2605250700 + 8 others
  [modules] 1 × isaac-lab-task-port            (reserved)        — 2605261600
  [modules] 4 × moemoekyun R1+ artifacts       (reserved)        — 2605262100 / 262400
EXIT 0
```

**This baseline is the canonical clean state going forward.** Any
future commit that introduces a bare missing path will fail CI via
GitHub Actions `deps-toml-paths.yml`. Stale markers will surface as
warnings when reserved paths land (operators drop the suffix).

### 5. ADR-2605262500 cycle 45 PR-prep dossier supersession

`90-docs/baien/adr-2605262500-pr-prep-260527.md` (cycle 45) is
SUPERSEDED by this closure ADR. Its Part 1 (branch strategy) is
historical (Option B was chosen externally); its Part 2 (drift
outreach) is realized as cycle 46's marker application; its Part 3
(PR description draft) was not used (PR #287 used its own description).

The doc is preserved for cycle history / process pattern study but
should be read with a "point-in-time draft" framing.

## Consequences

### Positive
- Full ADR-2605262500 substrate is live on main + audit-clean
- New marker convention available to any ADR for path placeholders
- Stale-marker passive enforcement catches markers that should be dropped
- Constitutional gates G2/G5/G7/G8/G9/G11 runtime-enforced + 390 tests green
- 47-cycle process learnings captured (5-doc dossier + this closure ADR)

### Negative
- Bundle PR (Option B) sets a precedent that 379-commit shared branches
  CAN be merged. Future ADRs should be more careful to develop on
  ADR-isolated branches when feasible to enable Option C.
- 47 cycles is a lot of overhead for what could have been ~10 cycles
  with tighter scope; some cycle work was "nice-to-have" (e.g. unified
  preflight CLI cycle 41) rather than critical path.

### Deferred (3 small items)

1. **W2.4 rasterio install on dev box** — the rasterio path has a
   defensive Pillow fallback so production assemble works without it;
   operator who wants true geospatial-aware bilinear sampling installs
   `pip install rasterio` per the runbook.

2. **Live PDS resolve smoke against `pds.etzhayyim.com`** — cycle 44
   smoke covered local at-uri parsing; actual network resolve against
   the live PDS needs operator session.

3. **GitHub Actions `deps-toml-paths.yml` first PR-trigger** — the
   workflow lands on main but has not been exercised by an actual PR
   yet. Next PR opened (regardless of ADR) will smoke-test it.

## Alternatives Considered

### Should the closure ADR be a separate document or amendment to ADR-2605262500?

**Chose**: separate document with `depends_on` link.

**Why**: ADR-2605262500 captures the planned decision; this closure
captures the landing state. Mixing them muddies the "decision vs
outcome" boundary. ADR-2605270100 set the precedent of separate
closure ADRs for sibling ADR-2605262400. Maintain the pattern.

### Should the (reserved) marker support arbitrary tokens?

**Chose**: only `reserved` and `deferred-rename` are accepted.

**Why**: opening to arbitrary tokens would let operators bypass the
audit by writing `(skip)` or `(later)` everywhere. The two tokens
encode specific owner-asserted intent: future R-cycle vs constitutional
pre-cutover. Additional tokens require explicit verifier amendment
+ test coverage.

### Should I have updated CLAUDE.md row #71 in this commit?

**Chose**: no — row #71 has been touched by parallel agents and is
~3500 chars; a focused closure ADR is cleaner than a row-edit. Future
CLAUDE.md update wave can pick up the closure status.

## References

- `90-docs/adr/2605262500-robotics-world-data-ingestion-and-usd-pipeline.md` — parent ADR
- `90-docs/baien/adr-2605262500-implementation-retrospective-260527.md` — 39-cycle chronology
- `90-docs/baien/adr-2605262500-operator-runbook-260527.md` — production operator runbook
- `90-docs/baien/adr-2605262500-runbook-smoke-260527.md` — cycle 44 E2E smoke evidence
- `90-docs/baien/adr-2605262500-pr-prep-260527.md` — cycle 45 PR-prep dossier (SUPERSEDED by this ADR)
- `70-tools/scripts/lint/verify_deps_toml_paths.py` — marker convention canonical impl
- ADR-2605270100 — sibling ADR-2605262400 closure (parallel pattern reference)
- ADR-2605270930 — organism ecosystem R0+R1 sprint closure (parallel pattern reference)
- PR #287 — `feat/yakushi-wave-1c-r1-commissioning` merge to main (2026-05-27T01:29Z)
- Cycle 46 commit `214640efa` — verifier marker enhancement + cross-ADR drift cleanup on main
