---
id: adr-2605211845-etzhayyim-org-cleanup-completion-and-kami-engine-sdk-standalone
title: "ADR-2605211845: etzhayyim org cleanup completion + kami-engine-sdk standalone publication"
status: accepted
doc_type: adr
topic: etzhayyim-org-cleanup-completion
authoritative: true
last_verified: 2026-05-21
priority: 4.0
axis: operations
weight: 0.40
priority_note: "Closes the long-running etzhayyim [MOVED → etzhayyim/root] cleanup. Records the kami-engine-sdk standalone mirror as the only intentional carve-out from the monorepo SoT rule."
authoritative_for:
  - etzhayyim MOVED-tagged repo deletion completion (0 remaining)
  - etzhayyim/kami-engine-sdk standalone mirror policy (monorepo = SoT, standalone = read-only mirror)
  - @etzhayyim/kami-engine-sdk → @etzhayyim/kami-engine-sdk npm scope rename
  - public-global late-fetch reconciliation pattern
related:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605265200-kami-engine-sdk-20-actors-legacy-duplicate-retirement
depends_on: []
supersedes: []
superseded_by:
  - adr-2605265200-kami-engine-sdk-20-actors-legacy-duplicate-retirement
---

# ADR-2605211845: etzhayyim org cleanup completion + kami-engine-sdk standalone publication

**Status**: **partially superseded** by ADR-2605265200 (the "monorepo subdir `20-actors/kami-engine-sdk/` is SoT" portion of this ADR was reversed on 2026-05-26 — canonical is now `40-engine/kami-engine/kami-engine-sdk/`, the 20-actors duplicate was deleted in Phase 3 commit `2d199cca9`)
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

> ⚠️ **Partial supersession note (added 2026-05-26 iter-18 of /loop):**
>
> The "**monorepo subdir `20-actors/kami-engine-sdk/` is SoT**" decision
> in §"kami-engine-sdk standalone publication" below is **superseded by
> ADR-2605265200**. The canonical SDK location is now
> `40-engine/kami-engine/kami-engine-sdk/` (git subrepo of
> `github.com/etzhayyimcojp/kami-engine-sdk`). The `20-actors/kami-engine-sdk/`
> directory was retired in a 3-phase deprecation completed 2026-05-26:
> Phase 1 `491ff8ee6` (deprecation marker + workspace registration),
> Phase 2 `243470dc8` (verification log), Phase 3 `2d199cca9` (atomic
> 80-file `git rm -r`).
>
> The rest of this ADR (etzhayyim org cleanup completion, MOVED-tag deletions,
> public-global reconciliation, the standalone-mirror policy concept)
> remains historically accurate and is NOT superseded.

# Context

Between 2026-04 and 2026-05, ~15 etzhayyim public repos were progressively migrated into `etzhayyim/root` (this monorepo) per the Shannon-Optimal 8-Layer Architecture (ADR-2604251830). Each migrated source repo was left at etzhayyim with description prefix `[MOVED → github.com/etzhayyim/root]` and archived.

The migration left two operational tails:

1. **Stale source repos**. Archived ≠ deleted. The MOVED-tagged copies were still publicly listed under etzhayyim, with their pre-cleanup tree (which in some cases pre-dated substrate-boundary purges and vendor-business-actor sweeps per commit `393da1ce`).
2. **One repo (public-global)** carried the MOVED description but had never actually been imported into the monorepo. The description was inaccurate.

A separate question — surfaced by `etzhayyim/kami-engine-sdk` — was whether some SDKs should be republished as standalone repos (mirror pattern) for downstream consumers who prefer pinning to a focused repo rather than a monorepo subdir.

# Decision

## (a) Delete all MOVED-tagged etzhayyim repos

All 15 etzhayyim repos with `[MOVED → github.com/etzhayyim/root]` in their description are physically deleted from GitHub. archived-only retention is rejected: the leaked pre-cleanup trees (vendor business actors, Stripe lexicons, etc.) shouldn't remain publicly discoverable just because the source side is archived.

Verified outcome (2026-05-21 18:00 JST): `etzhayyim` has **0** MOVED-tagged repos remaining.

## (b) Reconcile public-global before deleting

`etzhayyim/etzhayyim-project-public-global` was MOVED-tagged but never imported. Before deletion, it was cloned into `60-apps/etzhayyim-project-public-global/` (16 files, 2 WasmCloud components) to make the MOVED claim accurate retroactively. Committed as `690135d3`.

## (c) Publish kami-engine-sdk standalone

`etzhayyim/kami-engine-sdk` is created as a public repo at `github.com/etzhayyim/kami-engine-sdk`, seeded from `20-actors/kami-engine-sdk/`. The monorepo subdir remains the **source of truth**; the standalone repo is a read-only mirror.

Package name renamed from `@etzhayyim/kami-engine-sdk` to `@etzhayyim/kami-engine-sdk`. Six in-tree referrers updated (`20-actors/kami-engine-sdk/{package.json,README.md,src/lib/{index,document/index,document/scene-bridge}.ts}`, `20-actors/magatama/sdk/magatama-host-sdk/package.json`, `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/genko-stub.ts`).

## (d) Scope of standalone mirror policy

`kami-engine-sdk` is **the only** intentional carve-out at the time of this ADR. Other public SDKs left at etzhayyim (bpmn-engine-ts, bpmn-sdk-rs, rs-jsonnet, effect-actor, ontology, shigarami, sparql-ts) and the etzhayyim README repo remain at etzhayyim by user direction — they are vendor-tier SDKs without etzhayyim Charter Rider applied, and replicating them under etzhayyim would imply etzhayyim sponsorship that does not exist. No automatic mirror rule.

Future SDK standalone publications follow the same one-by-one explicit decision pattern. No bulk republication.

# Consequences

## Positive

- Public surface area of `etzhayyim` no longer advertises etzhayyim work via stale archived repos. Discoverability matches actual canonical location (etzhayyim/root + the one standalone mirror).
- `public-global` description is now true (it really is in etzhayyim/root).
- Downstream consumers of `kami-engine-sdk` can pin `github:etzhayyim/kami-engine-sdk` without depending on the full monorepo. npm scope aligns with the rest of `@etzhayyim/*`.

## Negative / accepted

- Old git SHAs that referenced the etzhayyim repos as remotes will 404. Acceptable: these were already archived (read-only); deletion was the next step.
- Standalone mirror introduces a sync surface (monorepo → standalone). For v0 this is a manual one-time push. If divergence appears (e.g. someone pushes to the standalone), the monorepo wins.
- Charter Rider is not (yet) auto-applied to the standalone — it is bundled in the snapshot pushed (CHARTER-RIDER.md + NOTICE come from the monorepo subdir copy).

## Operational note (lost cross-cutting work)

During the same session that performed (a)–(c), a 6-wave commit plan was attempted for the religious-corp Pregel cell substrate (yoro / shinka / etzhayyim-sdk-py / joucho / council + 1 cross-cutting cleanup, CLAUDE.md milestones 28–32). Waves 1–5 landed locally as commits `64804ab2`, `88e97621`, `06946371`, `20d6c958`, `0b6bfa55`. The cross-cutting wave (94 staged entries: CLAUDE.md row 28–32 additions, deps.toml + lockfile bumps, 5 ADR additions, fleet.toml placement edits, magatama worker_main refactor under ADR-2605214000/2605215000, generic etzhayyim platform lexicons, Stripe-purge migrations) was committed externally as part of `e4868a8e` and then wiped by a parallel `git reset --hard origin/main` (reflog HEAD@{2}). Working-tree restoration of the cross-cutting did not happen.

Waves 1–5 were pushed to `260521-cell-waves` and opened as PR #254, but CI failed across the board (vitest + tsc) because the supporting cross-cutting (lockfile + pyproject + fleet.toml) was missing. The user is reconstructing the same work in parallel in the working tree (untracked `shinka_murakumo.py` / `joucho_murakumo.py` / etc. verified byte-identical to the wave commits); PR #254 was closed and `260521-cell-waves` deleted to avoid duplication.

No durable loss to etzhayyim/root because the user's parallel reconstruction will land via a fresh PR with proper cross-cutting included. Recorded here so the reflog window is searchable by future audits.

## Orphaned `.gitrepo` files post-cleanup (audit 2026-05-26 iter-29 of /loop)

An audit during iter-29 enumerated all `.gitrepo` files in the
monorepo and tested each `remote` URL via `gh repo view`. Excluding
the etzhayyim-project-cofog tree (hundreds of per-COFOG-code subrepos
that are a separate concern):

  - `40-engine/kami-engine/kami-engine-sdk/.gitrepo` — was stale
    (pointed at `etzhayyimcojp/kami-engine-sdk`, 404); fixed in iter-28
    commit `957ec4c0a` to point at `etzhayyim/kami-engine-sdk`
    (which exists, was created per the §"kami-engine-sdk standalone
    publication" Decision above)
  - `40-engine/kotoba/.gitrepo` — points at `etzhayyim/kotoba`,
    confirmed alive

The following 7 `.gitrepo` files remained stale post-cleanup, with
NO surviving `etzhayyim/<name>` equivalent (all `gh repo view
etzhayyim/<name>` calls returned NOT FOUND):

  60-apps/etzhayyim-project-intel/.gitrepo               → etzhayyimcojp/etzhayyim-intel (404)
  60-apps/etzhayyim-project-news/.gitrepo                → etzhayyimcojp/etzhayyim-apps-media (404)
  60-apps/etzhayyim-project-watashi/.gitrepo             → etzhayyimcojp/watashi (404)
  60-apps/etzhayyim-project-os/.gitrepo                  → etzhayyimcojp/etzhayyim-project-os (404)
  60-apps/etzhayyim-project-activity-monitor/etzhayyim-performer-sys-etzhayyim-app-activity-monitor-ui-xgng091s/.gitrepo
                                                        → etzhayyimcojp/etzhayyim-performer-sys-etzhayyim-app-activity-monitor-ui-xgng091s (404)
  50-infra/yata/yata-wasm/lance-fork/.gitrepo          → etzhayyimcojp/lancedb-wasm (404)
  60-apps/etzhayyim-project-har/appview/har-app-5ugfx2n1/svelte/.gitrepo
                                                        → etzhayyimcojp/etzhayyim-har (404)

These are consistent with the §"6 deletion batches" table — the etzhayyim
cleanup deleted upstream repos that were imported into the monorepo
prior to deletion. The in-monorepo content remains canonical; the
`.gitrepo` metadata is now historical bookkeeping that cannot be
acted on (any `git subrepo push` / `git subrepo pull` will 404).

Three options exist for resolving each:

  1. **Update `remote` to a live successor** — only viable for the
     kami-engine-sdk case (iter-28); no etzhayyim/<name> successors
     exist for any of the 7 above.
  2. **Detach the subrepo** by `git rm .gitrepo` — drops the subrepo
     tooling marker; the directory becomes plain monorepo content.
     Reversible by re-running `git subrepo init` later if needed.
  3. **Leave as-is** — bookkeeping accurately reflects historical
     import; nobody will operate on it because the live upstream is
     gone.

This ADR does NOT prescribe Option 1/2/3 for each — that's a per-app
operator decision. Audit recorded here so the choice is informed.
Audit script (reproducible):

  for f in $(find . -name '.gitrepo' -not -path '*/node_modules/*' \\
              -not -path '*/.claude/*' -not -path '*/etzhayyim-project-cofog/*'); do
    remote=$(grep 'remote =' "$f" | awk '{print $3}')
    orgrepo=$(echo "$remote" | grep -oE 'github\\.com[:/]([^/]+/[^/.]+)' \\
              | head -1 | sed 's|github.com[:/]||')
    [ -n "$orgrepo" ] && \\
      gh repo view "$orgrepo" --json visibility >/dev/null 2>&1 || \\
      echo "STALE: $f → $orgrepo"
  done

# Alternatives Considered

## Keep etzhayyim MOVED repos archived (not delete)

Was the user's initial pattern. Rejected on this pass because:
- Archive ≠ public removal. Pre-cleanup vendor-business content (Stripe lexicons, malak/keiei/akuma/manimani/ses subpackages) was still discoverable.
- Maintenance burden: future auditors must reason about which side is canonical.
- 0 MOVED-tagged repos is a clearer post-condition than 15-archived.

## Standalone-mirror everything publishable

Rejected — see Decision (d). Implicit etzhayyim sponsorship of vendor-tier SDKs is not desired.

## Reset main to delete the 5 wave commits without saving them

Rejected during the session. Saved to `260521-cell-waves` first, then closed the PR rather than discarding. Reflog still holds the SHAs; if the user's parallel reconstruction loses a specific change, recovery is `git cherry-pick 88e97621` (etc.) within the gc window.

# References

- ADR-2605170900 (etzhayyim/root as canonical home for religious-corp open ADRs)
- ADR-2605172000 (etzhayyim/root open apps MUST be RW-free)
- ADR-2605192200 (Apache 2.0 + etzhayyim Charter Compliance Rider v2.0)
- Commit `393da1ce` (Remove vendor business actors leaked into public seed — Tier 1)
- Commit `690135d3` (60-apps: import etzhayyim-project-public-global from etzhayyim)
- Commit `d302f274` (20-actors/kami-engine-sdk: rename @etzhayyim/* → @etzhayyim/* + publish mirror)
- PR #254 (closed — Religious-corp Pregel cell waves; see Operational note)
