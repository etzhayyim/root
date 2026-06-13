# Runbook — remove the `kotoba` submodule from root (Phase 4 cutover)

**ADR**: 2606131645 (kotodama extraction + functional UNSPSC clj migration + kotoba submodule removal)
**Status**: PREPARED — gated, operator-executed as ONE atomic PR
**Why a runbook, not a single agent commit**: `40-engine/kotoba` is referenced by
**934 tracked files** (most are docs/ADR history; the load-bearing ones are CI,
k8s, scripts, pnpm-workspace, deps). Ripping the gitlink without the rewrite
breaks CI (the kotodama container image builds from
`40-engine/kotoba/crates/kotoba-kotodama/py/Dockerfile`) and the in-production
Python fleet. The removal must be one atomic, reviewed, gated PR.

## Gates (ALL must hold before executing)

1. **Fleet live** — the clj UNSPSC fleet (`etzhayyim/kotodama`, ADR-2606131645)
   is deployed on the Murakumo cluster against a live kotoba-db backend and
   healthy (joseph/issachar/dan), so removing the Python path breaks nothing.
2. **ADR ratified** — ADR-2606131645 approved (founder = Council Lv7+ 1/1, PR review).
3. **kotodama published** — `etzhayyim/kotodama` pushed + tagged; root can depend on it.

## Change classes (what the atomic PR touches)

| # | Class | Files | Action |
|---|-------|------:|--------|
| A | **Submodule** | `.gitmodules` (block lines 37–40) + gitlink `40-engine/kotoba` | remove block; `git rm --cached 40-engine/kotoba`; drop `.git/modules/40-engine/kotoba` |
| B | **CI workflows** | 7 (`.github/workflows/`: kotodama-image.yml, kami-engine-sdk.yml, kawase-yui-r0-audit.yml, test.yml, README.md, …) | kotodama image → build from `etzhayyim/kotodama`; drop `git submodule update … 40-engine/kotoba`; repoint cell-audit paths |
| C | **pnpm workspace** | `pnpm-workspace.yaml` (2 globs into the submodule) | remove the `40-engine/kotoba/**` globs (mcp pkgs move with kotoba repo) |
| D | **k8s** | 12 (`50-infra/k8s/**`) | repoint image refs / mounted paths to the kotodama image |
| E | **scripts** | 72 (`70-tools/scripts/**`) | repoint path consumers to the external kotoba / kotodama repo |
| F | **deps** | `deps.edn` (+ `deps.toml` if reintroduced) | kotoba → external git/cargo dep; add `etzhayyim/kotodama` dep |
| G | **CLAUDE.md** | substrate-engine decl + cell-catalog pointer + do-not clause (the kotoba-kotodama/py rename lock) + status row | point at external kotoba + kotodama repo; add ADR-2606131645 status row; the §Do-Not rename-lock item is superseded by this ADR |
| H | **CHARTER-RIDER.md** | `nv_compat` path citation | repoint to the kotoba repo path |
| I | **Linter** | `70-tools/scripts/lint/substrate-boundary.mjs` | update the kotoba import-boundary path |
| J | **Docs / ADRs** | ~256 in `90-docs/adr/**` + historical prose | **DO NOT rewrite** — historical record; leave as-is |

## Kotoba-repo side (separate PR, after fleet live)

- Delete the **18,343 `c<code>.py`** UNSPSC agents + the old Python `kotoba-kotodama`
  organism/executor (replaced by `etzhayyim/kotodama`). This lives in the
  `etzhayyim/kotoba` repo, **not** root (root only held the gitlink).
- Keep the 17 Rust substrate crates (kotoba stays the canonical engine; only its
  in-root embedding changes from submodule → external dependency).

## Atomic sequence

1. Branch from `origin/main`; apply classes A–I in ONE commit.
2. `git config -f .gitmodules --remove-section submodule.40-engine/kotoba` (or edit) + `git rm --cached 40-engine/kotoba` + `rm -rf .git/modules/40-engine/kotoba`.
3. Run the full CI locally where possible; the kotodama image job must build from the new repo.
4. Open the PR; founder review = ratify (CLAUDE.md "Council attestation = PR review").
5. Merge; watch fleet healthz (joseph/issachar/dan) stays green.
6. Then merge the kotoba-repo `.py` deletion PR.

## Rollback

- Pre-merge: close the PR (no effect — gitlink untouched on main).
- Post-merge regression: revert the PR; `git submodule update --init 40-engine/kotoba`
  restores the gitlink; CI/image rebuild from the restored path.

## Verification (definition of done)

- `git submodule status` in root shows **no** `40-engine/kotoba`.
- CI green (kotodama image builds from `etzhayyim/kotodama`).
- Fleet healthz green; no consumer resolves the old `40-engine/kotoba/...` path.
- `substrate-boundary` linter green at the new path.
