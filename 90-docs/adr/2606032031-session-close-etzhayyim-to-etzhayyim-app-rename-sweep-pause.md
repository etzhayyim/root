---
id: adr-2606032031-session-close-etzhayyim-to-etzhayyim-app-rename-sweep-pause
title: "ADR-2606032031: Session close — etzhayyim/kotoba-datomic app rename sweep pause (etzhayyim + kotoba Datomic/EDN)"
status: active
doc_type: adr
topic: session-close-etzhayyim-to-etzhayyim-app-rename-sweep
authoritative: false
last_verified: 2026-06-03
related:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605212100-etzhayyim-to-etzhayyim-migration-batch
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
supersedes: []
superseded_by: []
---

# ADR-2606032031: Session close — etzhayyim/kotoba-datomic app rename sweep pause

**Status**: active — progress ledger / pause point
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

Closure for the user direction:

- `wproto` prune is allowed.
- `kotoba-datomic` is deprecated; app state/projection references should be kotoba Datomic + EDN.
- App/project naming portions `etzhayyim` / `etzhayyim` should move to `etzhayyim`.
- Work must stay in small git batches: no 50+ staged/uncommitted files; commit and push frequently.

## What landed before pausing

The sweep completed and pushed the following app directories to `main`, with each completed project audited for:

- old `60-apps/etzhayyim-project-*` file count = 0,
- no `etzhayyim`, `Etzhayyim`, `etzhayyim`, `.etzhayyim.com`, `kotoba-datomic`, or `kotoba-datomic-projection.edn` residue under the new project tree,
- no Kubernetes default namespace resources in YAML/JSON/Jsonnet surfaces.

Completed projects:

- `maps`
- `hrse`
- `mangaka`
- `open-isic`
- `yoro`
- `cofog`
- `yabai`
- `states`

The sweep also fixed substrate-boundary issues encountered while moving code:

- Yoro AT Protocol direct imports moved off `@atproto/api` and onto `@etzhayyim/sdk/atproto` where runtime imports remained.
- Yoro derived read-path storage surfaces were documented with `kotoba-datomic-projection.edn` manifests where appropriate.
- Generated/web asset cookie lint exceptions were scoped to bundled fallback lines only.

## Pause point

`news` is the only non-empty legacy app tree remaining.

Pause state:

- last pushed news commits: `Rename 37th news project files` + `Update 37th news references`
- `60-apps/etzhayyim-project-news` remaining file count: `20192`
- worktree status at pause: clean
- branch/worktree used: `chore/rename-hrse-etzhayyim` in `/Users/junkawasaki/github/etzhayyim-rename-apps-work`

Zero-file legacy directories still visible at pause are directory shells only:

- `60-apps/etzhayyim-project-browser`
- `60-apps/etzhayyim-project-cofog`
- `60-apps/etzhayyim-project-maps`
- `60-apps/etzhayyim-project-open-isic`
- `60-apps/etzhayyim-project-open-ot`
- `60-apps/etzhayyim-project-states`
- `60-apps/etzhayyim-project-yabai`

## Resume rules

Resume with the same discipline:

- Move at most 48 files per rename batch.
- If reference rewrites leave modified files, commit them separately and keep the status count under 50.
- Run `git diff --check`, `git diff --cached --check`, deprecated-reference scans, and default-namespace scans before commit.
- Push each batch to `origin main` after fetch/rebase.

Known local hook condition:

- `e7m-verify` fails in this environment with `etzhayyim: unknown command: verify`.
- Normal commit should still be attempted first.
- Use `--no-verify` only when all other hooks pass and the only failure is that broken local `e7m verify` subcommand.

The paused session deliberately did **not** continue into the remaining `news` batches after the user stop request.
