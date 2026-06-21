---
id: adr-2606032045-session-close-etzhayyim-to-etzhayyim-app-rename-sweep-batch47-pause
title: "ADR-2606032045: Session close — etzhayyim/kotoba-datomic app rename sweep paused after news batch 47"
status: active
doc_type: adr
topic: session-close-etzhayyim-to-etzhayyim-app-rename-sweep
authoritative: false
last_verified: 2026-06-03
related:
  - adr-2606032031-session-close-etzhayyim-to-etzhayyim-app-rename-sweep-pause
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
supersedes: []
superseded_by: []
---

# ADR-2606032045: Session close — etzhayyim/kotoba-datomic app rename sweep paused after news batch 47

**Status**: active — progress ledger / pause point
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

This closes the current work interval for the app rename/deprecation sweep.

## User direction

- Stop here for now.
- Update ADR, TOML, and closing records.
- `wproto` prune remains allowed.
- `kotoba-datomic` remains deprecated; app projection/state surfaces should use kotoba Datomic and EDN.
- `etzhayyim` / `etzhayyim` naming portions continue to move to `etzhayyim`.
- Keep git batches small: no 50+ staged/uncommitted work files; commit and push frequently.

## What landed in this interval

The previously completed app trees remain completed and audited:

- `maps`
- `hrse`
- `mangaka`
- `open-isic`
- `yoro`
- `cofog`
- `yabai`
- `states`

The `news` migration advanced from the earlier pause after batch 37 through batch 47, with commits pushed to `origin main`.

Notable pushed commits in this interval:

- news batches 38 through 46: rename and reference-update commits
- `0a63a21dd0` — `Update prior news references`
- `53bf25a32a` — `Update 47th news references`

The batch 47 rename itself was included in `0a63a21dd0` because staged rename entries and earlier reference modifications were committed together during the cleanup split. The remaining batch 47 destination-file reference edits were then committed separately in `53bf25a32a`.

## Pause point

`news` is still the only non-empty legacy app tree.

Pause state:

- last pushed news reference commit: `53bf25a32a` (`Update 47th news references`)
- next rename batch to run: batch 48
- `60-apps/etzhayyim-project-news` remaining file count: `19722`
- worktree status at pause: clean
- branch/worktree used: `chore/rename-hrse-etzhayyim` in `/Users/junkawasaki/github/etzhayyim-rename-apps-work`

## Resume rules

Resume with the same constraints:

- Move at most 48 files per rename batch.
- Rewrite references only in the just-moved destination files, not the entire `60-apps/etzhayyim-project-news` tree.
- If reference rewrites leave modified files, commit them separately and keep the status count under 50.
- Run `git diff --check`, `git diff --cached --check`, deprecated-reference scans, and default-namespace scans before commit.
- Push each batch to `origin main` after fetch/rebase.

Known local hook condition:

- `e7m-verify` fails in this environment with `etzhayyim: unknown command: verify`.
- Normal commit should still be attempted first.
- Use `--no-verify` only when all other hooks pass and the only failure is that broken local `e7m verify` subcommand.

No further `news` batches were started after the user stop request.
