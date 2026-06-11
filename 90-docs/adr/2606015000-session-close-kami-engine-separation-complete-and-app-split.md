---
id: adr-2606015000-session-close-kami-engine-separation-complete-and-app-split
title: "ADR-2606015000: Session close — kami-engine separation complete (stages 1–4) + native-build/CI fixes + product-app split"
status: active
doc_type: adr
topic: session-close-kami-engine-separation
authoritative: true
last_verified: 2026-06-01
priority: 5.0
axis: architecture
weight: 0.5
priority_note: "Operational close for the 2026-06-01 kami-engine reusable-vs-repo-specific separation. All 4 staged migrations of ADR-2606011500 landed on main (L1 kami-engine-sdk submodule · L2 generic fixtures in-workspace · L3 robotics apps extracted to kami-apps · kami-engine itself → public git-submodule etzhayyim/kami-engine with kami-engine-sdk nested inside). Three follow-ups also landed: the 3 native-build-broken engine crates fixed, the 2 pre-existing CI baseline reds (deps-toml-paths set -e abort, monorepo-health rollup baseline) turned green, and the app-crate-home question resolved as a split (robotics/sim apps maintained in the engine submodule; *.etzhayyim.com product apps in monorepo kami-apps). Honest process note: a concurrent parallel-work collision on the engine repo produced one erroneous revert that was force-undone before reconciliation."
authoritative_for:
  - kami-engine separation completion (stages 1–4) operational close
  - post-separation fixes (native build, CI baseline reds, product-app/robotics split)
depends_on:
  - adr-2606011500-kami-engine-reusable-vs-repo-specific-separation-plan
related:
  - adr-2605211845-etzhayyim-org-cleanup-completion-and-kami-engine-sdk-standalone
  - adr-2605312355-session-close-kotoba-datom-first-class-and-charter-rider-d1
supersedes: []
superseded_by: []
---

# ADR-2606015000: Session close — kami-engine separation complete + app split

**Status**: active
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

Operational close for the kami-engine reusable-vs-repo-specific separation
(planned in **ADR-2606011500**). The full plan + per-stage detail lives there;
this ADR records the landing on `main` and the follow-on work.

# Decision / what landed

## Separation stages 1–4 (all merged)

| Stage | Result | PR |
|---|---|---|
| **1** | `kami-engine-sdk` subrepo → git-submodule (SoT inverted) | #655 |
| **2** | generic fixtures `git mv`'d into `kami-engine/fixtures/` (L2 self-contained) | #662 |
| **3** | robotics-actor apps extracted to a new `40-engine/kami-apps/` workspace | #663 |
| **4** | `kami-engine` → public submodule `etzhayyim/kami-engine` (105-commit subtree split); `kami-engine-sdk` now **nested** inside it; LICENSE/Rider/README added; 3 CI workflows switched to `--init --recursive` | #666 |

Clones now require `git submodule update --init --recursive 40-engine/kami-engine`.

## Follow-on fixes (all merged)

- **Engine native build** (PR #672, gitlink → `etzhayyim/kami-engine@0419c43`):
  kami-character (`glam` 0.29 vs workspace 0.33), kami-map / kami-web (ungated
  wasm-only wgpu code → `#![cfg(target_family = "wasm")]`); added a `.gitignore`
  the subtree split hadn't carried.
- **CI baseline reds** (PR #680): `deps-toml-paths` non-strict tracker no longer
  aborts under `bash -e` on pre-existing kotoba metadata drift; `monorepo-health`
  rollup re-baselined 25 → 7 (legitimate resolution; the 7 are the etzhayyim→etzhayyim
  404 `.gitrepo` stale-subrepo URLs).
- **Status doc sync** (PR #686).
- **App-crate-home split** (PR #692, gitlink → `8e60f9a`): resolved as a **split**
  — robotics/sim apps (giemon / giemon-factory / shibuya / tatekata / sarutahiko
  / funadaiku) are maintained IN the engine submodule; `*.etzhayyim.com` product
  apps (bim / cad / live / maps3d / animeka-timeline) live in monorepo
  `kami-apps/`. The stale stage-3 robotics duplicates were dropped from
  `kami-apps` (their `Collider` match never tracked the engine's `Collider::Box`
  variant — abandoned for the engine copies). Each app crate now has one home.

# Consequences

- L1 (kami-engine-sdk) and L2 (kami-engine) are independently versioned git
  submodules of the monorepo; L3 (`kami-apps` product apps + repo-specific
  scenes) stay in-repo. `etzhayyim/kami-engine` is a live public reusable repo.
- The engine workspace builds green on native; the two CI baseline reds are
  green; no app-crate duplication remains.
- **External dependents verified** (PR #699): `kotodama-kami-host` +
  `watashi-host` build green against the submodule — their
  `../../../../40-engine/kami-engine/kami-X` path-deps resolve through it (all
  6 needed crates present at `8e60f9a`). One *unrelated* blocker was fixed in
  passing: `png` 0.18 changed `output_buffer_size()` to `Option<usize>`, which
  broke `decode_png()` in kotodama-kami-host (pure dependency drift, not the
  separation). The separation's "external dependents unaffected" claim is now
  proven, not just asserted.

# Honest process note

This session ran **concurrently with parallel work on the `etzhayyim/kami-engine`
repo** (PRs #1–#4: physics sync · carry robotics apps in · sarutahiko · funadaiku).
That collision caused one mistake: an inference that the engine should be an
app-superset led to an erroneous `git revert` of the engine's product-app
removal (`de15ac4`). It was caught immediately (PR #4 had been built on top of
the removal, i.e. the removal was accepted) and **force-undone** before any
reconciliation; engine `main` stayed at the owner's `8e60f9a`. Lesson recorded:
when collaborating on a fast-moving shared repo, align to what the commits show
rather than inferring direction.

# References

- ADR-2606011500 (separation plan + per-stage detail)
- `etzhayyim/kami-engine` (public reusable engine submodule), `40-engine/kami-apps/`
- PRs #655 / #662 / #663 / #666 / #672 / #680 / #686 / #692
