---
id: adr-2605211925-phase-6-archive-markers-runbook
title: "ADR-2605211925: Phase 6 runbook — archive markers on cut-over etzhayyim repos (ADR-2605152100 finale)"
status: proposed
doc_type: adr
topic: phase-6-archive-markers-runbook
authoritative: true
last_verified: 2026-05-21
priority: 7.5
axis: operations
weight: 0.55
priority_note: "Final phase of the ADR-2605152100 6-phase cutover (org split). After the per-repo `git rm` + DNS cutover, this runbook applies the `[MOVED → github.com/etzhayyim/root]` description prefix + GitHub archive flag to the etzhayyim-side repos whose open scope has been relocated. Closes the org-split loop at the GitHub-repo-metadata layer."
authoritative_for:
  - Phase 6 archive-marker procedure for cut-over etzhayyim repos
  - description-prefix convention + archive-flag policy
  - rollback (un-archive) procedure
depends_on:
  - adr-2605212100-magatama-worker-3-axis-tranche-f-closure
  - adr-2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com
  - adr-2605211913-vendor-refactor-and-git-rm-phase-4-5-runbook
related:
  - adr-2605152100-etzhayyim-github-org-boundary
  - doc-2605211800-vendor-importer-survey-gate-d
  - doc-2605211900-tranche-f-all-gates-closure-confirmation
supersedes: []
superseded_by: []
---

# ADR-2605211925: Phase 6 runbook — archive markers on cut-over etzhayyim repos

**Status**: proposed
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

ADR-2605152100 (etzhayyim GitHub org boundary) defines a 6-phase cutover:

1. Catalog freeze ✅
2. etzhayyim/root scaffolding ✅
3. Content copy ✅
4. Vendor business-app dependency switch — ADR-2605211913 §1 runbook
5. Vendor open-scope deletion — ADR-2605211913 §2 runbook
6. **Archive markers** — `[MOVED → github.com/etzhayyim/root]` description prefix
   on archived etzhayyim repos (this ADR)

The CLAUDE.md status table records that Tranches A-E + Wave 2 already produced
"26 旧 etzhayyim open repos archived with [MOVED] prefix" as of 2026-05-17.
That Wave 2 batch is **already done**. This ADR is the runbook for the
**Tranche F follow-on archive markers** — the additional repos that get
archived once Phase 5 `git rm` (ADR-2605211913 §2) lands and the routing-
gateway 410 Gone is in place (ADR-2605211757 Step 3.7).

Two distinct archive targets exist:

- **A. Whole-repo archive**: repos like `etzhayyim/<single-purpose-repo>` whose
  entire content moved to etzhayyim/root. Mark the GitHub repo as Archived +
  add `[MOVED → github.com/etzhayyim/root/<subpath>]` to the description.
- **B. Subtree archive**: subdirectories of `etzhayyim-root` whose
  content was relocated (e.g. the 3 lg subtrees from gate (d), the 27
  workers + 4 ingest + 4 primitive from Phase 5). Subtrees inside a still-
  active monorepo cannot be GitHub-archived; they get a `_archive/` move +
  a top-level README stub instead.

# Decision

Adopt the 4-step Phase 6 runbook. The runbook fires AFTER ADR-2605211913
Phase 5 `git rm` commits land in `etzhayyim-root`.

## 0. Pre-flight

These conditions MUST hold:

1. **Phase 5 deletion landed**: ADR-2605211913 Step 2.A-2.D commits exist in
   `etzhayyim-root` main + the verification protocol (Step 2.E) returned
   green.
2. **DNS cutover complete (all waves)**: ADR-2605211757 Wave A-D operator-
   confirmed; routing-gateway returning 410 Gone (or 301) for the cut-over
   `{actor}.etzhayyim.com` hosts.
3. **etzhayyim/root mirror live**: each Phase 6 target's relocated content is
   reachable via `https://github.com/etzhayyim/root/blob/main/<subpath>`.
4. **operator authority**: GitHub repo settings changes (archive + description
   edit) require admin access to the etzhayyim organization.

## 1. Inventory

### 1.A — Whole-repo Phase 6 targets

Identify etzhayyim-org repos that are 100% relocated to etzhayyim/root and have
no remaining vendor-only content. As of 2026-05-21, the Wave 2 batch of 26
repos is already archived per CLAUDE.md status. New Tranche F additions from
this session: **none at the whole-repo level** (the Tranche F closure operates
on subtrees inside `etzhayyim-root`, not on standalone repos).

Operator check (re-run before executing):

```bash
gh repo list etzhayyim --limit 500 --json name,description,isArchived \
  | jq -r '.[] | select(.isArchived == false) | "\(.name)\t\(.description // "")"' \
  > /tmp/etzhayyim-active.tsv

# Cross-reference with etzhayyim/root content to find unintended duplicates:
gh api repos/etzhayyim/root/contents \
  | jq -r '.[].name' \
  > /tmp/etzhayyim-toplevel.txt

# Any repo whose entire purpose has moved should appear in the second file
# OR have content fully covered by an etzhayyim/root subtree.
```

If a new whole-repo target appears at re-run time, extend the script in Step 2
to cover it.

### 1.B — Subtree Phase 6 targets

Within `etzhayyim-root`, the Tranche F subtrees that have been moved
to etzhayyim/root and `git rm`'d per Phase 5 need archive-marker stubs.
Concretely:

| Subtree | etzhayyim/root mirror | Archive stub treatment |
|---------|------------------------|------------------------|
| `60-apps/etzhayyim-project-ki/lg/` | `etzhayyim/root/60-apps/etzhayyim-project-ki/lg/lg_organism/` | Top-level `60-apps/etzhayyim-project-ki/README.md` MOVED stub if the entire project relocates; otherwise just keep the wasm/ side and add a `lg/MOVED.md` pointer |
| `60-apps/etzhayyim-project-legal-entity/lg/` | `etzhayyim/root/60-apps/etzhayyim-project-legal-entity/lg/` | Same pattern |
| `60-apps/etzhayyim-project-curpus2skill/lg/` | `etzhayyim/root/60-apps/etzhayyim-project-curpus2skill/lg/` | Same pattern (curpus2skill currently has only lg/, so the entire project moves) |
| `20-actors/magatama/py/src/pymagatama/{27 worker_main + 4 ingest + 4 primitive}` | `etzhayyim/root/20-actors/magatama/py/src/pymagatama/` | Per-file `MOVED → etzhayyim/...` pointer is excessive (~37 files); instead add ONE top-level `20-actors/magatama/py/MOVED-FILES.md` listing the relocated files |

## 2. Execute

### Step 2.A — Whole-repo archive (if any new targets from §1.A)

For each `<repo>` in the §1.A inventory:

```bash
# 1. Update description with MOVED prefix
gh repo edit etzhayyim/<repo> \
  --description "[MOVED → github.com/etzhayyim/root/<subpath>] <original description>"

# 2. Archive the repo (read-only flag)
gh repo archive etzhayyim/<repo> --yes
```

Verify:

```bash
gh repo view etzhayyim/<repo> --json isArchived,description
# expect: { "isArchived": true, "description": "[MOVED → github.com/etzhayyim/root/...] ..." }
```

### Step 2.B — Subtree MOVED.md stubs

For the 3 lg subtrees:

```bash
# Example for ki — repeat with legal-entity and curpus2skill substituted:
cat > /Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-ki/lg/MOVED.md <<EOF
# Moved to etzhayyim/root

This subtree was relocated as part of Tranche F (ADR-2605212100) gate (d)
closure on 2026-05-21.

**New location**:
https://github.com/etzhayyim/root/tree/main/60-apps/etzhayyim-project-ki/lg/

The previous etzhayyim-side copy lives in git history; current development happens
in etzhayyim/root.

See also:
- etzhayyim/root/90-docs/2605211800-vendor-importer-survey-gate-d.md (target file list)
- etzhayyim/root/90-docs/adr/2605211913-vendor-refactor-and-git-rm-phase-4-5-runbook.md (Phase 4-5 runbook)
EOF
```

Repeat for `legal-entity` and `curpus2skill` lg subtrees. (Note: if Phase 5
Step 2.A actually `git rm -r`'d the entire `lg/` directory, the MOVED.md
either sits at the project root or in a re-created `lg/` shell directory with
ONLY the stub. Operator picks based on what's cleaner for vendor `gh repo`
browsing.)

### Step 2.C — pymagatama MOVED-FILES.md catalog

```bash
cat > /Users/junkawasaki/github/etzhayyim-root/20-actors/magatama/py/MOVED-FILES.md <<EOF
# Files moved to etzhayyim/root

The following Python modules were relocated to etzhayyim/root as part of
Tranche F Phase 5 (ADR-2605211913) on 2026-MM-DD (operator fills date).

## Workers (29 total)

\`\`\`
hakkou_worker_main.py            → etzhayyim/root/20-actors/magatama/py/src/pymagatama/hakkou_worker_main.py
kabi_worker_main.py              → etzhayyim/root/...
ki_worker_main.py                → etzhayyim/root/...
... (full list, generate via deps.toml [[mitama_actors]] etzhayyim-classified subset)
\`\`\`

## Ingest modules (4 total)

\`\`\`
ingest/blockchain.py    → etzhayyim/root/20-actors/magatama/py/src/pymagatama/ingest/blockchain.py
ingest/houbun.py        → etzhayyim/root/...
ingest/curpus2skill.py  → etzhayyim/root/...
ingest/site_common_crawl.py → etzhayyim/root/...
ingest/core.py          → etzhayyim/root/...
\`\`\`

## Substrate primitives (4 total)

\`\`\`
primitives/active_inference_substrate.py → etzhayyim/root/...
primitives/at_ipfs_belief_store.py       → etzhayyim/root/...
primitives/legal_entity.py               → etzhayyim/root/...
worker_runtime.py                        → etzhayyim/root/...
\`\`\`

## Why moved

- 3-axis OR-test (Liability/Custody/Settlement) returned "etzhayyim" — see
  ADR-2605172400.
- Per-worker re-impl follows the 6 patterns documented in ADR-2605211757
  + ADR-2605211913.

## Git history

The pre-2026-MM-DD history for these files lives in this repo's git log
(use \`git log --follow <path>\` to trace). Post-move history lives in the
etzhayyim/root repo.

## See also

- ADR-2605212100 (Tranche F closure — gate definitions + classification table)
- ADR-2605211913 (Phase 4-5 runbook — deletion procedure)
- ADR-2605152100 (org-split root ADR)
EOF
```

### Step 2.D — Top-level CLAUDE.md amendment

Update `etzhayyim-root/CLAUDE.md` to add a new line in the org-split
section noting the Tranche F archive markers:

```markdown
# In §Operating Entity Boundary (CRITICAL), append after the existing
# "26 旧 etzhayyim open repos archived with [MOVED] prefix" clause:

、Tranche F の 3 lg subtree (lg_organism / lg_legal_entity / lg_curpus2skill)
+ 37 pymagatama files (workers 29 + ingest 4 + primitive 4) は
ADR-2605211913 Phase 5 で git rm 済 + `20-actors/magatama/py/MOVED-FILES.md`
+ 3 subtree MOVED.md stub で archive marker 完了 (ADR-2605211925, 2026-MM-DD)
```

## 3. Verify

```bash
# 1. All Phase 6 stubs exist:
for stub in \
  60-apps/etzhayyim-project-ki/lg/MOVED.md \
  60-apps/etzhayyim-project-legal-entity/lg/MOVED.md \
  60-apps/etzhayyim-project-curpus2skill/lg/MOVED.md \
  20-actors/magatama/py/MOVED-FILES.md; do
  test -f "/Users/junkawasaki/github/etzhayyim-root/$stub" \
    && echo "  ✓ $stub" \
    || echo "  ✗ MISSING: $stub"
done

# 2. CLAUDE.md amendment landed:
grep -c "ADR-2605211925" /Users/junkawasaki/github/etzhayyim-root/CLAUDE.md

# 3. deps.toml records the phase 6 completion timestamp:
grep "phase_6_archive_markers_completed_at" /Users/junkawasaki/github/etzhayyim-root/deps.toml
```

## 4. `deps.toml` post-Phase-6 amendment

Append to `[[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17`:

```toml
phase_6_archive_markers_completed_at = "2026-MM-DDTHH:MMZ"  # operator fills
```

This completes the 6-phase cross-repo log at the deps.toml level. Tranche F
is now `[MOVED]` marked end-to-end.

# Rollback

Phase 6 is the **least destructive** phase — rollback is straightforward:

- **Whole-repo archive rollback** (Step 2.A): `gh repo unarchive etzhayyim/<repo>`
  + `gh repo edit ... --description "<original>"`. Restores write access.
- **Subtree MOVED.md rollback** (Step 2.B/2.C): `git rm MOVED.md` + re-add the
  relocated files via `git revert` of the Phase 5 commits. Two commits per
  affected subtree (revert + remove stub).
- **CLAUDE.md amendment rollback** (Step 2.D): single-line `git revert`.
- **deps.toml rollback** (Step 4): single-field `git revert`.

# Consequences

**Positive**

- ADR-2605152100 6-phase cutover is now operator-runbook-complete end-to-end
  (Phase 1-2-3 done historically; Phase 4-5 = ADR-2605211913; Phase 6 = this
  ADR).
- Future operators / agents reading the etzhayyim repo see explicit MOVED markers
  rather than mysterious deletions. Discoverability of the relocated content
  is preserved.
- The pymagatama MOVED-FILES.md catalog gives operators a single grep target
  to find "where did file X go" without needing to know about the org-split.

**Negative / risks**

- Per-file MOVED.md stubs were considered (one stub per relocated file) but
  rejected as excessive (~37 stubs). The single `MOVED-FILES.md` catalog
  trades stub-redundancy for slightly worse discoverability when an operator
  greps for a single filename. Mitigation: the catalog itself is greppable.
- Whole-repo archive (Step 2.A) is a GitHub Org admin operation. If org admin
  access is lost (e.g. operator turnover), Phase 6 stalls. Mitigation: the
  subtree stubs in Step 2.B-D do NOT require GitHub Org admin and can land
  via regular PR.
- Newly-added repos under etzhayyim (post-2026-05-21) that should also be
  archived will require a re-run of Step 1.A. There is no automation for
  "detect a new repo that's eligible for archive". Mitigation: quarterly
  audit per the §"Re-judgment triggers" rhythm in Tranche F migration entry.

**Mitigations**

- Single `MOVED-FILES.md` catalog instead of per-file stubs → 1 file vs 37.
- The runbook can land **without** waiting for Phase 5 to finish (the §1
  inventory + §3 verify scripts are read-only and idempotent). Only Step 2
  is gated on Phase 5.

# Alternatives Considered

1. **Skip Phase 6 entirely** (no archive markers).
   Rejected: violates ADR-2605152100 §"Step 8 vendor open-scope cleanup".
   The "archived with [MOVED] prefix" treatment was applied to the 26
   Wave 2 repos; consistency requires the Tranche F additions get the same
   treatment.

2. **Per-file MOVED.md stubs** (one per relocated file, ~37 total).
   Rejected as excessive (see Negative / risks above).

3. **Use GitHub repo redirect / "MOVED" UI feature**.
   Considered. GitHub does not have a native "moved-to" feature for
   subtrees, only for whole-repo renames. The subtree MOVED.md stubs are
   the closest substitute.

4. **Delete the subtree entirely with no marker** (Phase 5 is enough).
   Rejected: future operators grep'ing the etzhayyim repo for legacy code would
   see a deletion in git log with no destination pointer. The marker is
   navigational metadata that costs ~50 LoC across 4 files.

# References

- ADR-2605152100 (etzhayyim GitHub org boundary — defines Phase 6 archive markers)
- ADR-2605212100 (Tranche F closure — classification table)
- ADR-2605211757 (DNS cutover runbook — gate (b))
- ADR-2605211913 (Phase 4-5 runbook — deletion procedure that precedes this Phase 6)
- ADR-2605172400 (3-axis split rule)
- `etzhayyim-root/CLAUDE.md` §"Operating Entity Boundary" (status table —
  records the Wave 2 26-repo archive already done 2026-05-17)
- `etzhayyim-root/deps.toml [[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17`
