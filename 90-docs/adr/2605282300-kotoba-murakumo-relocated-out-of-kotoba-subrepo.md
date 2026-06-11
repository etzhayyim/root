---
id: adr-2605282300-kotoba-murakumo-relocated-out-of-kotoba-subrepo
title: "ADR-2605282300: kotoba_murakumo relocated out of the kotoba subrepo to 40-engine/kotoba_murakumo/ (downstream-consumer placement)"
status: proposed
doc_type: adr
topic: kotoba-murakumo-subrepo-relocation
authoritative: true
last_verified: 2026-05-28
priority: 5.5
axis: architecture
weight: 0.40
priority_note: "Closes the structural gap surfaced by the first git subrepo push attempt: kotoba_murakumo was placed inside the kotoba subrepo working tree but is a religious-corp downstream consumer, not part of kotoba's canonical external surface. When the upstream kotoba repo had force-pushed away the merge-base commit recorded in .gitrepo, the subrepo push became impossible without manual surgery. The honest fix is structural — move the consumer outside the upstream mirror — not a git workflow patch. This ADR documents the relocation, the root-cause analysis, and the pattern for future religious-corp downstream consumers of any subrepo."
authoritative_for:
  - placement of religious-corp downstream consumers vs upstream subrepo mirrors
  - kotoba_murakumo canonical filesystem location
  - subrepo-relocation pattern (when to move out vs stay in)
depends_on:
  - "2605282000"  # kotoba_murakumo facade (the subject of this relocation)
  - "2605282100"  # kotoba mKOTO economy (lives alongside; same relocation applies)
  - "2605262130"  # kotoba canonical storage substrate (the subrepo)
related: []
supersedes: []
superseded_by:
  - "2606074000"  # re-integrated into the kotoba submodule (subrepo hazard dissolved)
---

> **Superseded by ADR-2606074000 (2026-06-07)**: kotoba is now a git submodule,
> not a git-subrepo, so the merge-base force-push hazard that forced this
> relocation no longer exists. `kotoba_murakumo` has been re-integrated into the
> submodule at `40-engine/kotoba/py/kotoba_murakumo/`. The "downstream consumer
> must live outside the upstream mirror" rule below was a subrepo-era rule.

# ADR-2605282300: kotoba_murakumo relocated out of the kotoba subrepo to 40-engine/kotoba_murakumo/ (downstream-consumer placement)

**Status**: proposed
**Date**: 2026-05-28
**Deciders**: Jun Kawasaki

## Context

ADR-2605282000 R0/R1.1/R1.2 + ADR-2605282100 R1.3 landed `kotoba_murakumo`
as a Modal-compatible Python facade for the Murakumo Mac mini fleet. The
original placement, chosen for "filesystem-collocation with the substrate
it consumes", was inside the kotoba subrepo at
`40-engine/kotoba/py/kotoba_murakumo/`, sibling of `kotoba_langgraph`.

The first attempt to propagate the work upstream via
`git subrepo push 40-engine/kotoba` revealed:

1. The `.gitrepo` metadata recorded the subrepo base at commit
   `17e30d9db5738f0e3a5f92f37783f2491bf293ac`.
2. The upstream `github.com/etzhayyim/kotoba` HEAD was at `23d615ac7`
   (~20+ commits ahead, including 2 `git subrepo push --force` operations
   from another agent / clone — implying the upstream history was rewritten).
3. The recorded base `17e30d9db5...` no longer existed in upstream's
   history (force-pushed away). git-subrepo refused all three sync paths:
   `pull` ("Local repository does not contain ..."), `branch` (same), and
   `pull --force` (would replace the subdir with upstream content, deleting
   my work in the process — confirmed by an aborted dry-run).

This is not a one-off workflow accident. The upstream kotoba repo is
actively developed by multiple agents / clones (the 2 force-push commits
in the upstream log are evidence). The recorded merge-base will go stale
again on the next force-push, and the same blockage will recur.

The structural mistake — surfaced by user prompt 2026-05-28 evening: "kotoba
subrepo をもっとスムーズに管理するには? submodule の方がいいかな?" — was
**placing a religious-corp downstream consumer inside an upstream mirror**.
`kotoba_murakumo` does not extend kotoba's canonical surface:

| What kotoba_murakumo consumes | Lives where |
|---|---|
| `50-infra/murakumo/fleet.toml` | monorepo-only |
| Religious-corp ADRs (2605215000, 2605262200, 2605282000, ...) | monorepo-only |
| `00-contracts/lexicons/com/etzhayyim/kotoba/economy/` | monorepo-only |
| `etzhayyim_organism.sensors.charter_rider` scanner | monorepo-only |
| `kotoba-vm` Invoke XRPC (R2 binding) | upstream-canonical (consumed via HTTP) |
| `kotoba-llm::http_infer` OpenAI-compat wire format | upstream-canonical (mirrored in Python) |

The consumer relationship runs only through HTTP and shared wire formats —
it does not need filesystem-collocation with the subrepo. `kotoba_langgraph`,
the in-subrepo Python sibling, is genuinely canonical kotoba (it compiles
to WASM Components for `kotoba-runtime` to embed). `kotoba_murakumo` is not.

## Decision

Relocate `kotoba_murakumo` and its tests + economy + clients out of the
kotoba subrepo to a sibling path. Revert the subrepo-internal doc additions
made by the original commits. Keep the Rust scaffold `economy_xrpc.rs` in
the subrepo because it IS intended for upstream eventually (R1.3d-wiring
will turn the `#[cfg(any())]` gate off and register the routes in
`kotoba-server/src/lib.rs`).

### Filesystem moves

```
# Move (preserved git history via `git mv`):
40-engine/kotoba/py/kotoba_murakumo/  →  40-engine/kotoba_murakumo/

# Revert subrepo doc additions:
git checkout <pre-relocation-parent> -- 40-engine/kotoba/README.md
git checkout <pre-relocation-parent> -- 40-engine/kotoba/CLAUDE.md

# Remove subrepo-side test plumbing (replaced by monorepo-side runner):
git rm 40-engine/kotoba/py/README.md
git rm 40-engine/kotoba/scripts/test-py.sh
git rm 40-engine/kotoba/.github/workflows/py-tests.yml

# Keep (legit kotoba-server scaffold; will sync upstream when wired):
40-engine/kotoba/crates/kotoba-server/src/economy_xrpc.rs
```

### Monorepo-side updates

| File | Change |
|---|---|
| `40-engine/kotoba_murakumo/README.md` | License link `../../../LICENSE` → `../../LICENSE` |
| `40-engine/kotoba_murakumo/tests/*.py` | `Path(__file__).resolve().parents[5]` → `parents[3]` (5 → 3 path segments to repo root) |
| `40-engine/kotoba_murakumo/tests/test_no_modal_labs_gate.py` | injected-violation fake-repo path `40-engine/kotoba/py/kotoba_murakumo/...` → `40-engine/kotoba_murakumo/...` |
| `70-tools/scripts/lint/verify_no_modal_labs_calls.py` | `_PACKAGE_ROOT` constant: `40-engine/kotoba/py/kotoba_murakumo/...` → `40-engine/kotoba_murakumo/...` |
| `70-tools/scripts/test-kotoba-murakumo.sh` (NEW) | replaces the subrepo-side `40-engine/kotoba/scripts/test-py.sh` |
| `90-docs/adr/2605282000-...md` §"Subrepo integration status" | rewritten as "Subrepo placement (final framing)" with the relocation rationale + permanent decision |
| `deps.toml` | every kotoba_murakumo path updated; integration_status field replaced with placement_note pointing at this ADR |

### Pattern: when does a Python sibling stay in a subrepo vs move out?

This ADR establishes a reusable rule. A Python (or any-language) sibling
stays **inside** a git subrepo iff:

1. **It IS canonical upstream-shipped content**. e.g. `kotoba_langgraph`
   compiles to WASM Components that `kotoba-runtime` embeds — the upstream
   kotoba binary distribution would be incomplete without it.
2. **It depends on monorepo-only files only through documented external
   interfaces** (e.g. via a config file path passed at runtime, not via
   imports of monorepo-only Python modules).
3. **The upstream repo's release tag includes it**.

A Python sibling moves **out** to a sibling monorepo path iff:

1. **It consumes the subrepo via HTTP or stable wire format** but is not
   itself part of the subrepo's external surface. (`kotoba_murakumo`)
2. **It imports monorepo-only modules** (charter scanner, organism
   sensors, religious-corp Lexicons by path). (`kotoba_murakumo` imports
   `etzhayyim_organism.sensors.charter_rider.scan` when available.)
3. **Its constitutional invariants are religious-corp-specific** (Charter
   Rider scan, Murakumo-only inference, anti-subscription) and shouldn't
   leak into the upstream public surface.

`kotoba_murakumo` matches all three "move out" criteria. `kotoba_langgraph`
matches all three "stay in" criteria. The boundary is durable.

### Honest gap (resolved, not deferred)

The original ADR-2605282000 §"Subrepo integration status" listed
"git subrepo push" as a pending closure. This relocation **resolves** that
gap by removing the need to push at all: there is nothing in
`40-engine/kotoba_murakumo/` that needs to flow upstream. The Rust scaffold
at `40-engine/kotoba/crates/kotoba-server/src/economy_xrpc.rs` will need a
real subrepo sync when R1.3d-wiring lands, but that is a separate, small,
single-file sync that can be done by a fresh clone + PR against upstream
HEAD (avoiding git-subrepo's merge-base requirement).

## Consequences

**Positive**:

- The structural mistake is fixed once and never recurs. Future religious-
  corp Python siblings have a documented rule for where to live.
- The kotoba subrepo stays a clean upstream mirror — `git subrepo pull`
  becomes reliable again because nothing in the subrepo working tree
  diverges from upstream except what upstream will accept back.
- `kotoba_murakumo` development cadence is decoupled from upstream kotoba's
  release cadence (homebrew formula releases, kotoba-cli refactors, etc.).
- Path arithmetic in tests + verifier becomes shorter and more readable
  (`parents[3]` instead of `parents[5]`).

**Negative / Tradeoffs**:

- External clones of `github.com/etzhayyim/kotoba` no longer see
  `kotoba_murakumo`. This is **the intended outcome** — `kotoba_murakumo`
  is religious-corp-internal (donation-routed compute, Murakumo-only
  invariant), not part of kotoba's open external surface. External
  consumers wanting Modal-shape decorators against an Ollama / vLLM /
  LiteLLM gateway should use the LiteLLM SDK directly.
- The R1.3d Rust scaffold (`economy_xrpc.rs`) still sits inside the subrepo
  and will need its own upstream-sync path when wired. That path will be
  a small, deliberate PR against upstream HEAD (not the broken
  git-subrepo flow that surfaced this ADR).

**Constitutional**:

- ADR-2605215000 Murakumo-only invariant **strengthened** (the religious-
  corp inference facade is now structurally separated from the upstream
  substrate that could in principle have other consumers).
- ADR-2605262130 kotoba substrate **preserved** (kotoba subrepo remains
  the canonical storage substrate engine; this ADR doesn't change that).
- ADR-2605192115 anti-subscription **preserved** (`kotoba_murakumo` carries
  the mKOTO economy + donation routing per ADR-2605282100; relocation
  doesn't change any constitutional behavior).

## Alternatives Considered

1. **git-submodule cutover for kotoba**. Considered. Rejected at this ADR
   scope: submodule requires `git submodule update --init --recursive` on
   every clone, is harder for tooling (lefthook, GHA matrix paths) to
   reason about, and doesn't actually solve the placement question for
   `kotoba_murakumo` (which still wants to be a downstream consumer
   regardless of whether kotoba is a subrepo or submodule). May be
   revisited in a future ADR if upstream force-pushes continue to break
   subrepo workflows; would require its own dedicated ADR for the migration.

2. **Direct PR against upstream kotoba (option C from the relocation
   decision)**. Considered. Rejected because (a) the structural mistake
   would still be there for any future religious-corp Python additions,
   (b) PR-merge cadence is upstream-controlled, blocking monorepo
   development of `kotoba_murakumo`, and (c) the PR would have to
   carry religious-corp-internal references (Lexicon paths,
   `etzhayyim_organism.sensors`) that don't belong in upstream's public
   surface.

3. **Manual `.gitrepo` surgery** (rewrite the recorded base commit to a
   surviving upstream commit, then `git subrepo pull`). Considered.
   Rejected: brittle (each force-push requires re-surgery), error-prone
   (wrong base commit corrupts the diff and may push noise upstream), and
   doesn't address the structural mistake.

4. **`git subrepo pull --force` then manually re-apply my work**. Tried
   and reverted. Rejected because `pull --force` replaces the subdir with
   upstream content, staging my work as deleted; the auto-commit then
   failed on a `trailing-whitespace` lefthook hook on upstream's content
   (which uses trailing whitespace deliberately in some `.md` files for
   formatting). The cleanup would itself be a manual surgery exercise on
   par with option 3.

5. **Leave the placement as-is and abandon the upstream-push goal**.
   Considered. Rejected because (a) the placement signal-to-noise is
   wrong (a downstream consumer claims canonical upstream placement),
   (b) future ADR work that wants to extend kotoba_murakumo would have
   to re-decide each time whether to push upstream, and (c) the structural
   mistake remains a latent trap.

## References

- ADR-2605282000 (kotoba_murakumo facade — subject of this relocation; §"Subrepo placement" amended to reflect this decision)
- ADR-2605282100 (kotoba mKOTO economy — lives alongside kotoba_murakumo; same relocation pattern)
- ADR-2605262130 (kotoba canonical storage substrate — unchanged by this ADR)
- ADR-2605282xxx (R1.3d-wiring, future) — when this lands, the Rust scaffold `economy_xrpc.rs` will need a small targeted upstream-sync PR (not git-subrepo)
- Pre-relocation commit chain: `81fe1db2c` (subrepo-internal R0+R1.1+R1.2+R1.3b) + `b8549d937` (non-subrepo ADRs + Lexicons + gate)
- Relocation commit chain: this commit + sibling (deps.toml + registry regen)
- `40-engine/kotoba_murakumo/` — new canonical path
- `70-tools/scripts/test-kotoba-murakumo.sh` — replacement test runner (replaces the deleted `40-engine/kotoba/scripts/test-py.sh`)
- `70-tools/scripts/lint/verify_no_modal_labs_calls.py` — `_PACKAGE_ROOT` updated to new path
