---
id: adr-2606074000-kotoba-murakumo-reintegrated-into-kotoba-submodule
title: "ADR-2606074000: kotoba_murakumo re-integrated into the kotoba submodule (py/kotoba_murakumo/) — submodule era supersedes the subrepo-relocation"
status: proposed
doc_type: adr
topic: kotoba-murakumo-submodule-reintegration
authoritative: true
last_verified: 2026-06-07
priority: 5.5
axis: architecture
weight: 0.40
priority_note: "Reverses the ADR-2605282300 relocation now that the root-cause has dissolved. The relocation was forced by a git-subrepo failure mode — the upstream kotoba repo had force-pushed away the merge-base commit recorded in .gitrepo, making subrepo sync impossible. kotoba is now a true git submodule (a pinned commit + an independent push/pull lifecycle), so that sync hazard no longer exists. The Modal-compat facade rejoins the engine repo at py/kotoba_murakumo/ as a sibling of py/kotoba_langgraph/, keeping the religious-corp Modal-API surface co-located with the substrate it consumes."
authoritative_for:
  - kotoba_murakumo canonical filesystem location (now inside the kotoba submodule)
  - the submodule-era placement rule for religious-corp Python siblings of the kotoba engine
depends_on:
  - "2605282000"  # kotoba_murakumo facade (the subject)
  - "2605282100"  # kotoba mKOTO economy (lives alongside)
  - "2605282300"  # the relocation this ADR supersedes
  - "2605262130"  # kotoba canonical storage substrate
  - "2605215000"  # Murakumo-only inference invariant
related: []
supersedes:
  - "2605282300"
superseded_by: []
---

# ADR-2606074000: kotoba_murakumo re-integrated into the kotoba submodule (py/kotoba_murakumo/)

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

## Context

ADR-2605282300 relocated the `kotoba_murakumo` Modal-compatible facade **out** of
the kotoba repo (`40-engine/kotoba/py/kotoba_murakumo/`) to a monorepo sibling
(`40-engine/kotoba_murakumo/`). The stated root cause was a **git-subrepo**
failure: the first subrepo push revealed that upstream
`github.com/etzhayyim/kotoba` had force-pushed away the merge-base commit
recorded in `.gitrepo` (`17e30d9db…`), making all three subrepo sync paths
(pull / branch / pull --force) fail or turn destructive. The honest fix at the
time was structural — move the consumer outside the upstream mirror.

That root cause was **specific to git-subrepo**, which inlines upstream history
into the parent repo and depends on a stable recorded merge-base. kotoba is now
vendored as a **git submodule**: the parent records only a pinned commit SHA and
the submodule has its own independent push/pull lifecycle. A force-push upstream
can no longer corrupt a parent-side merge-base, because there is no inlined
history to sync — there is only a pointer. The hazard that justified the
relocation no longer exists.

Meanwhile the canonical kotoba WASM Component source already lives inside the
submodule at `py/kotoba_langgraph/`. Keeping the Modal-compat facade outside,
in a parallel monorepo directory, splits the Python surface of one engine across
two repos for no remaining reason.

## Decision

Re-integrate `kotoba_murakumo` into the kotoba submodule at
**`40-engine/kotoba/py/kotoba_murakumo/`**, as a sibling of `py/kotoba_langgraph/`.
The monorepo:

- removes the standalone copy at `40-engine/kotoba_murakumo/`;
- advances the `40-engine/kotoba` submodule pointer to the commit that adds the
  package (no upstream feature bump is pulled in — the bump is the local kotoba
  line plus the one integration commit);
- updates the path constants in `70-tools/scripts/test-kotoba-murakumo.sh` and
  `70-tools/scripts/lint/verify_no_modal_labs_calls.py` to the new location.

### Path / standalone-checkout handling

`kotoba_murakumo` remains a **monorepo-context** package: its canonical inputs
(`50-infra/murakumo/fleet.toml`, the `70-tools` lint gate) live in the etzhayyim
monorepo, not in a bare `kotoba` clone. Test path-depth is rebased
(`resolve().parents[3] → parents[5]`) for the new location, and `conftest.py`
skips the whole suite when `fleet.toml` is absent — so upstream CI on a
standalone kotoba checkout stays green rather than hard-failing on missing
monorepo inputs. 62 tests pass / 2 `live_fleet` skipped in the monorepo context.

The Murakumo-only invariant (ADR-2605215000), the Charter Rider §2 dispatch scan
(ADR-2605192200), and the no-Modal-Labs-calls N1 gate (ADR-2605282000) are all
unchanged by the move; only the package's filesystem home changes.

## Consequences

- **Positive**: one engine, one Python surface — facade co-located with the
  substrate it consumes; the subrepo-era split is gone; the submodule push/pull
  lifecycle removes the original sync hazard.
- **Negative / watch**: the submodule's `main` had diverged from upstream
  `origin/main` (a local-only commit line vs. upstream feature commits). The
  integration is stacked on the local line to keep the monorepo delta minimal;
  reconciling that divergence with upstream `main` (and thereby giving the
  upstream PR a clean diff) is tracked separately and is **not** part of this ADR.
- **Pattern update**: ADR-2605282300's "downstream-consumer must live outside the
  upstream mirror" rule was a **subrepo-era** rule. Under git submodules, a
  religious-corp Python sibling MAY live inside the submodule, provided (a) it
  does not contaminate the engine's Apache-2.0 canonical surface with
  operating-entity-exclusive logic, and (b) its monorepo-context inputs degrade
  to skips (not failures) in a standalone checkout. This ADR supersedes
  ADR-2605282300.
