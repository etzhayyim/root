---
id: adr-2605172800-gftd-cli-migration-strategy
title: "ADR-2605172800: 70-tools/gftd CLI migration strategy — git-subrepo unwind + open-scope fork"
status: proposed
doc_type: adr
topic: gftd-cli-migration-strategy
authoritative: true
last_verified: 2026-05-17
priority: 6.0
axis: organization
weight: 0.60
priority_note: "Defines the migration plan for the main gftd CLI (legacy upstream 70-tools/gftd, ~2599 files). Blocks final Step 8 completion in ADR-2605152100. Not yet executed — this ADR is the plan."
authoritative_for:
  - gftd CLI migration plan from upstream → etzhayyim
  - git-subrepo unwind decision (gftd-cli upstream relationship)
  - open vs legacy-scope command surface split
  - etzhayyim-cli (existing) vs etzhayyim CLI (new from gftd) relationship
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
related:
  - 
  - 
supersedes: []
superseded_by: []
---

# ADR-2605172800: 70-tools/gftd CLI migration strategy — git-subrepo unwind + open-scope fork

**Status**: proposed
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

`ADR-2605152100 Step 8` ("upstream-side open scope cleanup") cannot be marked ✅ while the main developer CLI `70-tools/gftd` remains upstream as the canonical open-scope build/auth/deploy/seed/coverage/xrpc tool. As of 2026-05-17, the following has been completed:

| Step 8 sub-scope | Status |
|---|---|
| `50-infra/k8s/murakumo-kubelet` + `60-apps/ai-gftd-project-comfyui` (mac mini fleet) | ✅ |
| 27 `50-infra/k8s/*-langserver|actor|worker|ingester` (open k8s entries) | ✅ |
| `50-infra/k8s/bpmn-timers` (scope-split: 127 open kept, 14 legacy-business dropped) | ✅ |
| 5 `70-tools/` open dirs (cost-analysis, maps-osm-ingest, mf-ingest-extension, templates, reports/yoro) | ✅ |
| 30 `60-apps/` open dirs (open-*, public-*, ameno, atproto, yoro) [MOVED] stubs upstream | ✅ |
| **`70-tools/gftd` main CLI** | ⏳ this ADR |
| `70-tools/gftd-py` (Python port, parallel) | ⏳ |
| `70-tools/scripts/` (411 files, 20 leak files, mixed scope) | ⏳ |
| `70-tools/config/` (2 mixed-scope JSON manifests) | ⏳ |

## Why `70-tools/gftd` is harder than the other migrations

A naive bulk migration (`git archive | tar xf -` + sed + drop legacy-scope leaks) was attempted in this session and failed because:

### 1. It is a `git-subrepo` of an upstream repository

```
$ cat 70-tools/gftd/gftd/.gitrepo
[subrepo]
    remote = 
    branch = main
    commit = bc8051245bf0c5c1b48708369eaf316ea205ce82
    parent = 773cc98cbc05c47efbdc724332bbac856451ddc2
```

The `70-tools/gftd/gftd/` subdirectory is **not** plain monorepo content. It is a `git-subrepo` (https://github.com/ingydotnet/git-subrepo) of a standalone legacy `gftd-cli` repository on GitHub, embedded into the legacy upstream monorepo. This means:

- The upstream legacy `gftd-cli` repo is the canonical source.
- Changes flow bidirectionally via `git subrepo pull` / `git subrepo push`.
- A simple file-content rewrite (sed) in the embedded copy would be **silently overwritten** the next time anyone runs `git subrepo pull`.

A real migration must address the upstream repo as well.

### 2. Two nested Go modules with different identities

```
70-tools/gftd/go.mod          : module github.com/<legacy-org>/kyber-erp/pkg
70-tools/gftd/gftd/go.mod     : module github.com/<legacy-org>/gftd-cli
```

The outer module exists for some shared `pkg` (Kyber-ERP); the inner module is the `gftd-cli` upstream. Both must be renamed coherently, plus all import paths inside the inner module (~180 .go files use `github.com/<legacy-org>/gftd-cli/...` imports).

### 3. Mixed open + legacy-scope data, large surface

```
70-tools/gftd/                        9.4M total
├── go.mod                            (outer, kyber-erp/pkg)
├── tools.go
├── sql/                              (queries — open scope)
├── CLAUDE.md                         67K of doc
└── gftd/                             (git-subrepo — 178 .go + 2404 .json files)
    ├── .gitrepo                      (subrepo marker)
    ├── go.mod                        (inner, gftd-cli)
    ├── *.go                          (122 cmd + 56 test files)
    ├── db/                           (Go db helpers)
    └── collectors/                   (2404 JSON configs)
        ├── malak_*.json              (624 files — LEGACY SURVEILLANCE)
        └── (other 1779 files)        (open data: FDA NDC, character refs,
                                       ATC drug codes, anime/literary
                                       references, satellites, gov data)
```

Leak distribution from `git grep` across `70-tools/gftd/`:
- **624 files** under `gftd/collectors/malak_*` (legacy cyber-crime intel data)
- **~10 .go command files** with explicit legacy-scope refs (vault.go, vault_share.go, some seed_*.go, world_coverage.go domain categories, etc.)
- Hundreds of strings in lint patterns / docstrings referring to legacy import namespaces (e.g., legacy `magatama-go`, `appshellv2/w` packages) — used as scan targets, not as live dependencies

### 4. `etzhayyim-cli` already exists as a separate small scaffold

```
70-tools/etzhayyim-cli/    (5 files, ~50 LoC)
├── go.mod  (module github.com/etzhayyim/root/70-tools/etzhayyim-cli — fixed in commit 3b83b9f0)
├── build_server.go
├── build.go
├── deploy.go
├── main.go         (// gftd — magatama build/deploy CLI (Cloudflare Containers))
└── plugin.go
```

This is a 0.2.0 build/deploy scaffold, **not** the full developer CLI. The "renamed from gftd-cli" comment in CLAUDE.md (root) refers to an earlier rename intention, not to this being the canonical `gftd` successor. The main CLI surface (122 commands) has never been migrated.

# Decision

Adopt a **three-phase migration**:

## Phase A — git-subrepo unwind (upstream side, prep)

Detach `70-tools/gftd/gftd/` from its upstream subrepo relationship before any content moves. Steps:

1. Run `git subrepo absorb 70-tools/gftd/gftd` in the legacy upstream monorepo, which converts the subrepo into plain monorepo content (drops the `.gitrepo` marker, ensures all history is in the parent repo).
2. Commit the absorb upstream.
3. **Optionally** archive the legacy upstream `gftd-cli` repo on GitHub with a `[MOVED →]` redirect notice. Decision: archive the upstream repo after Phase B completes, since some external pipelines may still pull from it.

## Phase B — open-scope fork to etzhayyim, legacy-business shed

In etzhayyim/root, create `70-tools/gftd/` as a **plain monorepo directory** (no subrepo, no nested go.mod). Two sub-decisions:

### B.1 — Binary name and module path

Keep the binary name `gftd` for v1 (avoid breaking existing scripts that invoke `gftd ...`). Rename only the module path and the import surface:

```
legacy gftd-cli module          → github.com/etzhayyim/root/70-tools/gftd
legacy kyber-erp/pkg module     → github.com/etzhayyim/root/70-tools/gftd-pkg
legacy cdn module               → github.com/etzhayyim/root/70-tools/cdn (matches existing 70-tools/cdn entry)
legacy magatama-go module       → github.com/etzhayyim/root/20-actors/magatama-go (existing)
```

`gftd` as binary name is a "follow-up cutover" item (CLAUDE.md), to be renamed to `etzhayyim` (the existing `etzhayyim-cli` scaffold remains; see B.4).

### B.2 — Strip legacy-scope content

Drop from the etzhayyim copy:

- `gftd/collectors/malak_*.json` (624 files — legacy cyber-crime intelligence data)
- `gftd/vault.go`, `gftd/vault_share.go` + tests (legacy business)
- `gftd/seed_naphtha_supply.go`? — naphtha supply chain seeding may be legacy business (oil trading). Inspect; if legacy, drop.
- Other commands explicitly marked legacy-scope (TBD inspection)

Legacy-business **references in strings** (e.g., `world_coverage.go` listing `malak` and `lawfirm` as coverage domains) stay as historical descriptive metadata — they describe the world the tool maps, not the tool's own business logic. Same policy as `reports/yoro` historical NSIDs.

### B.3 — Legacy-business code keeps living upstream

The legacy upstream monorepo retains `70-tools/gftd/` as the canonical home for legacy-business commands. That upstream copy may be reduced to only the dropped-in-Phase-B.2 set, or kept full for now; that decision is separate and depends on whether upstream still has dev users invoking those commands.

### B.4 — Reconcile with existing `70-tools/etzhayyim-cli` scaffold

`etzhayyim-cli/` (5-file scaffold) overlaps with `gftd/`'s build/deploy commands (`build.go`, `deploy.go`, `build_container.go`, `build_desktop.go`). Decision:

- **Keep both as separate tools for v1.** `gftd` (post-migration) is the full developer CLI; `etzhayyim-cli` (existing) is a smaller domain-specific tool for Cloudflare Containers (different scope). Coexistence is fine.
- Document the relationship in `70-tools/CLAUDE.md` (currently absent).
- Cutover ADR (future) can decide whether to merge.

## Phase C — upstream-side cleanup ([MOVED] stub)

After Phase B verified-built:

- `git rm -r` of all open-scope code from the legacy upstream `70-tools/gftd/`
- Replace with `[MOVED →]` stub README pointing at etzhayyim/root canonical
- Legacy-business commands either stay (in a stripped upstream `70-tools/gftd/`) or move to `70-tools/gftd-legacy/` for clarity

## Verification gates

Phase B is complete only when:

1. `cd 70-tools/gftd && go build ./...` succeeds with no errors
2. `go vet ./...` is clean
3. Unit tests pass: `go test ./...`
4. `gftd help` runs (smoke test the binary executes)
5. Leak scan (kaisya|keiei|malak|akuma|kenkyusha|kiyo|lawfirm|bengoshi|tsuru|shinshi|gameka|<legacy-org>): only acceptable matches are in `world_coverage.go` and similar descriptive metadata, not in command logic
6. No residual legacy-org import paths in Go source

# Consequences

## 正の効果

- **Step 8 unblocks.** The biggest remaining sub-scope becomes addressable.
- **CLI ownership clarified.** The main developer CLI is published under Apache 2.0 in etzhayyim/root, distinct from legacy-business CLIs.
- **Upstream subrepo simplification.** The git-subrepo arrangement is opaque to most contributors; absorbing it into plain monorepo content lowers the barrier to entry.
- **Legacy scope sharpens.** The upstream `70-tools/gftd/` (post-migration) contains only the commands relevant to legacy-business workflows.

## 負の効果 / コスト

- **External pipelines pulling the legacy `gftd-cli` upstream** may break after the upstream repo is archived. Inventory required before archive: who still uses `gftd-cli` upstream directly? Mitigation: 30-day grace period with `[MOVED]` notice; archive after that.
- **Two CLIs (`gftd` + `etzhayyim-cli`)** in `70-tools/` may confuse new contributors. Mitigation: clear `70-tools/CLAUDE.md` (currently missing) explaining the split. Eventual merge ADR may consolidate.
- **The 1779 non-malak collector configs** are open data that the CLI needs. They migrate. ~7MB.
- **Refactor risk.** Import path rewriting across ~180 .go files is mechanical but can introduce subtle issues; the verification gates above catch most.
- **Legacy commands marked as "TBD inspection"** in Phase B.2 require manual review. Estimate: 1-2 hours of careful reading per ambiguous command (`seed_*`, `world_coverage`, `coverage_*`, etc.).

## Out of scope

- Renaming binary `gftd` → `etzhayyim` (deferred follow-up cutover).
- Migrating `70-tools/gftd-py` (separate ADR; ADR-2605151500 governs its parallel operation).
- Migrating `70-tools/scripts/` (411 files, mixed-scope; separate ADR).
- Merging `etzhayyim-cli` + `gftd` (deferred; coexistence acceptable for v1).
- Decision about archiving the legacy upstream `gftd-cli` GitHub repo.

## Rollout

This ADR is the **plan**. Execution is staged:

- [ ] **Phase 0 — this ADR** (now). Plan published.
- [ ] **Phase A — git-subrepo absorb** upstream (~5 min op + 1 commit)
- [ ] **Phase B.1 — Bulk copy + sed import rewrites** in etzhayyim (~30 min)
- [ ] **Phase B.2 — Legacy-business strip** (drop malak, vault, ambiguous-then-inspected commands)
- [ ] **Phase B verification** (build + tests + smoke)
- [ ] **Phase B commit** in etzhayyim/root
- [ ] **Phase C — upstream [MOVED] stub** for the open-scope portion
- [ ] Update CLAUDE.md Step 8 status to ✅ (or ✅-with-followups for gftd-py + scripts + config)

# Alternatives Considered

## A. Bulk sed + drop, ignore the subrepo

What I attempted this session: extract, drop malak/vault, sed-rewrite, commit. Failed because the inner `gftd/gftd/go.mod` is a separate Go module and rewriting it without absorbing the subrepo leaves the relationship broken and the build broken.

却下理由: the next `git subrepo pull` upstream would re-overwrite the inner content from the legacy upstream, undoing the migration. Need to absorb first.

## B. Migrate everything except touch nothing in the subrepo

Keep `70-tools/gftd/gftd/.gitrepo` intact in etzhayyim, but use it pointing at a new etzhayyim-owned upstream repo.

却下理由: creates a new external repo dependency. Subrepo workflow is opaque; better to absorb. The whole point of monorepo consolidation is to NOT have external sub-repos pinned by commit hash.

## C. Two separate CLIs from day 1: `etzhayyim` (open commands only) and `gftd` (legacy commands only)

Aggressive split: take only the open commands into a new `etzhayyim` CLI in etzhayyim/root, leave `gftd` entirely upstream for legacy commands.

却下理由: requires identifying open vs legacy for every one of the 122 commands. Most commands are open-scope; the legacy-business surface is small (~10 commands). Bulk-migrate-and-strip is faster than split-from-scratch, and the result is the same end state. Plus: the existing `etzhayyim-cli` (5-file scaffold) already occupies the `etzhayyim` binary name lane.

## D. Defer entirely

Leave `70-tools/gftd` upstream; mark Step 8 ⏳ permanently and move on.

却下理由: contradicts ADR-2605152100's Step 8 commitment. The CLI is the developer's daily tool; it must follow the org boundary.

# References

- ADR-2605152100 — establishes Step 8 obligation (cross-repo)
- ADR-2605151500 — gftd-py parallel CLI design
- CLAUDE.md (this repo, root) — Step 8 status table, 70-tools layout note
- `git-subrepo` upstream — https://github.com/ingydotnet/git-subrepo
- Existing `70-tools/etzhayyim-cli/` scaffold — small build/deploy tool, 5 files
- Migration session report 2026-05-17:
  - 27 k8s langservers migrated (commit `44a3d85d` etzhayyim, `c931d249b80` upstream)
  - 5 70-tools open dirs migrated (commit `3b83b9f0` etzhayyim, `264f542fefa` upstream)
  - 30 60-apps stubbed upstream (commit `e7fe971d8af` upstream)
  - bpmn-timers scope-split + deep ref sweep (commit `dc45e314` etzhayyim)
- This ADR's session: bulk migration attempted, rolled back after detecting git-subrepo / nested module / build break.
