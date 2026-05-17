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
priority_note: "Defines the migration plan for the main gftd CLI (vendor 70-tools/gftd, ~2599 files). Blocks final Step 8 completion in ADR-2605152100. Not yet executed — this ADR is the plan."
authoritative_for:
  - gftd CLI migration plan from vendor → etzhayyim
  - git-subrepo unwind decision (gftd-cli upstream relationship)
  - open vs vendor command surface split
  - etzhayyim-cli (existing) vs etzhayyim CLI (new from gftd) relationship
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
related:
  - https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605152100-etzhayyim-github-org-boundary.md
  - https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605151500-gftd-py-cli-parallel-operation.md
supersedes: []
superseded_by: []
---

# ADR-2605172800: 70-tools/gftd CLI migration strategy — git-subrepo unwind + open-scope fork

**Status**: proposed
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

`ADR-2605152100 Step 8` ("gftdcojp 側 open scope cleanup") cannot be marked ✅ while the main developer CLI `70-tools/gftd` remains in vendor as the canonical open-scope build/auth/deploy/seed/coverage/xrpc tool. As of 2026-05-17, the following has been completed:

| Step 8 sub-scope | Status |
|---|---|
| `50-infra/k8s/murakumo-kubelet` + `60-apps/ai-gftd-project-comfyui` (mac mini fleet) | ✅ |
| 27 `50-infra/k8s/*-langserver|actor|worker|ingester` (open k8s entries) | ✅ |
| `50-infra/k8s/bpmn-timers` (scope-split: 127 open kept, 14 vendor-business dropped) | ✅ |
| 5 `70-tools/` open dirs (cost-analysis, maps-osm-ingest, mf-ingest-extension, templates, reports/yoro) | ✅ |
| 30 `60-apps/` open dirs (open-*, public-*, ameno, atproto, yoro) [MOVED] stubs in vendor | ✅ |
| **`70-tools/gftd` main CLI** | ⏳ this ADR |
| `70-tools/gftd-py` (Python port, parallel) | ⏳ |
| `70-tools/scripts/` (411 files, 20 leak files, mixed scope) | ⏳ |
| `70-tools/config/` (2 mixed-scope JSON manifests) | ⏳ |

## Why `70-tools/gftd` is harder than the other migrations

A naive bulk migration (`git archive | tar xf -` + sed + drop vendor leaks) was attempted in this session and failed because:

### 1. It is a `git-subrepo` of an upstream repository

```
$ cat 70-tools/gftd/gftd/.gitrepo
[subrepo]
    remote = https://github.com/gftdcojp/gftd-cli.git
    branch = main
    commit = bc8051245bf0c5c1b48708369eaf316ea205ce82
    parent = 773cc98cbc05c47efbdc724332bbac856451ddc2
```

The `70-tools/gftd/gftd/` subdirectory is **not** plain monorepo content. It is a `git-subrepo` (https://github.com/ingydotnet/git-subrepo) of the standalone `gftdcojp/gftd-cli` repository on GitHub, embedded into the vendor monorepo. This means:

- The upstream `gftdcojp/gftd-cli` repo is the canonical source.
- Changes flow bidirectionally via `git subrepo pull` / `git subrepo push`.
- A simple file-content rewrite (sed) in the embedded copy would be **silently overwritten** the next time anyone runs `git subrepo pull`.

A real migration must address the upstream repo as well.

### 2. Two nested Go modules with different identities

```
70-tools/gftd/go.mod          : module github.com/gftdcojp/kyber-erp/pkg
70-tools/gftd/gftd/go.mod     : module github.com/gftdcojp/gftd-cli
```

The outer module exists for some shared `pkg` (Kyber-ERP); the inner module is the `gftd-cli` upstream. Both must be renamed coherently, plus all import paths inside the inner module (~180 .go files use `github.com/gftdcojp/gftd-cli/...` imports).

### 3. Mixed open + vendor data, large surface

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
        ├── malak_*.json              (624 files — VENDOR SURVEILLANCE)
        └── (other 1779 files)        (open data: FDA NDC, character refs,
                                       ATC drug codes, anime/literary
                                       references, satellites, gov data)
```

Leak distribution from `git grep` across `70-tools/gftd/`:
- **624 files** under `gftd/collectors/malak_*` (vendor cyber-crime intel data)
- **~10 .go command files** with explicit vendor refs (vault.go, vault_share.go, some seed_*.go, world_coverage.go domain categories, etc.)
- Hundreds of strings in lint patterns / docstrings referring to vendor namespaces (e.g., `github.com/gftdcojp/magatama-go`, `@gftdcojp/appshellv2/w`) — used as scan targets, not as live dependencies

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

## Phase A — git-subrepo unwind (vendor side, prep)

Detach `70-tools/gftd/gftd/` from its upstream subrepo relationship before any content moves. Steps:

1. Run `git subrepo absorb 70-tools/gftd/gftd` in vendor monorepo, which converts the subrepo into plain monorepo content (drops the `.gitrepo` marker, ensures all history is in the parent repo).
2. Commit the absorb in vendor.
3. **Optionally** archive the upstream `gftdcojp/gftd-cli` repo on GitHub with a `[MOVED →]` redirect notice. Decision: archive the upstream repo after Phase B completes, since some external pipelines may still pull from it.

## Phase B — open-scope fork to etzhayyim, vendor-business shed

In etzhayyim/root, create `70-tools/gftd/` as a **plain monorepo directory** (no subrepo, no nested go.mod). Two sub-decisions:

### B.1 — Binary name and module path

Keep the binary name `gftd` for v1 (avoid breaking existing scripts that invoke `gftd ...`). Rename only the module path and the import surface:

```
github.com/gftdcojp/gftd-cli                 → github.com/etzhayyim/root/70-tools/gftd
github.com/gftdcojp/kyber-erp/pkg            → github.com/etzhayyim/root/70-tools/gftd-pkg
github.com/gftdcojp/cdn                      → github.com/etzhayyim/root/70-tools/cdn (matches existing 70-tools/cdn entry)
github.com/gftdcojp/magatama-go              → github.com/etzhayyim/root/20-actors/magatama-go (existing)
```

`gftd` as binary name is a "follow-up cutover" item (CLAUDE.md), to be renamed to `etzhayyim` (the existing `etzhayyim-cli` scaffold remains; see B.4).

### B.2 — Strip vendor-scope content

Drop from the etzhayyim copy:

- `gftd/collectors/malak_*.json` (624 files — vendor cyber-crime intelligence data)
- `gftd/vault.go`, `gftd/vault_share.go` + tests (vendor business)
- `gftd/seed_naphtha_supply.go`? — naphtha supply chain seeding may be vendor business (oil trading). Inspect; if vendor, drop.
- Other commands explicitly marked vendor (TBD inspection)

Vendor-business **references in strings** (e.g., `world_coverage.go` listing `malak` and `lawfirm` as coverage domains) stay as historical descriptive metadata — they describe the world the tool maps, not the tool's own business logic. Same policy as `reports/yoro` historical NSIDs.

### B.3 — Vendor-business code keeps living in vendor

Vendor monorepo retains `70-tools/gftd/` as the canonical home for vendor-business commands. The vendor copy may be reduced to only the dropped-in-Phase-B.2 set, or kept full for now; that decision is separate and depends on whether vendor still has dev users invoking those commands.

### B.4 — Reconcile with existing `70-tools/etzhayyim-cli` scaffold

`etzhayyim-cli/` (5-file scaffold) overlaps with `gftd/`'s build/deploy commands (`build.go`, `deploy.go`, `build_container.go`, `build_desktop.go`). Decision:

- **Keep both as separate tools for v1.** `gftd` (post-migration) is the full developer CLI; `etzhayyim-cli` (existing) is a smaller domain-specific tool for Cloudflare Containers (different scope). Coexistence is fine.
- Document the relationship in `70-tools/CLAUDE.md` (currently absent).
- Cutover ADR (future) can decide whether to merge.

## Phase C — vendor-side cleanup ([MOVED] stub)

After Phase B verified-built:

- `git rm -r` of all open-scope code from vendor `70-tools/gftd/`
- Replace with `[MOVED →]` stub README pointing at etzhayyim/root canonical
- Vendor-business commands either stay (in a stripped vendor `70-tools/gftd/`) or move to `70-tools/gftd-vendor/` for clarity

## Verification gates

Phase B is complete only when:

1. `cd 70-tools/gftd && go build ./...` succeeds with no errors
2. `go vet ./...` is clean
3. Unit tests pass: `go test ./...`
4. `gftd help` runs (smoke test the binary executes)
5. Leak scan (kaisya|keiei|malak|akuma|kenkyusha|kiyo|lawfirm|bengoshi|tsuru|shinshi|gameka|gftdcojp): only acceptable matches are in `world_coverage.go` and similar descriptive metadata, not in command logic
6. No residual `github.com/gftdcojp/` imports in Go source

# Consequences

## 正の効果

- **Step 8 unblocks.** The biggest remaining sub-scope becomes addressable.
- **CLI ownership clarified.** The main developer CLI is published under Apache 2.0 in etzhayyim/root, distinct from vendor-business CLIs.
- **Upstream subrepo simplification.** The git-subrepo arrangement is opaque to most contributors; absorbing it into plain monorepo content lowers the barrier to entry.
- **Vendor scope sharpens.** Vendor `70-tools/gftd/` (post-migration) contains only the commands relevant to vendor-business workflows.

## 負の効果 / コスト

- **External pipelines pulling `gftdcojp/gftd-cli`** may break after the upstream repo is archived. Inventory required before archive: who still uses `gftd-cli` upstream directly? Mitigation: 30-day grace period with `[MOVED]` notice; archive after that.
- **Two CLIs (`gftd` + `etzhayyim-cli`)** in `70-tools/` may confuse new contributors. Mitigation: clear `70-tools/CLAUDE.md` (currently missing) explaining the split. Eventual merge ADR may consolidate.
- **The 1779 non-malak collector configs** are open data that the CLI needs. They migrate. ~7MB.
- **Refactor risk.** Import path rewriting across ~180 .go files is mechanical but can introduce subtle issues; the verification gates above catch most.
- **Vendor commands marked as "TBD inspection"** in Phase B.2 require manual review. Estimate: 1-2 hours of careful reading per ambiguous command (`seed_*`, `world_coverage`, `coverage_*`, etc.).

## Out of scope

- Renaming binary `gftd` → `etzhayyim` (deferred follow-up cutover).
- Migrating `70-tools/gftd-py` (separate ADR; ADR-2605151500 vendor governs its parallel operation).
- Migrating `70-tools/scripts/` (411 files, mixed-scope; separate ADR).
- Merging `etzhayyim-cli` + `gftd` (deferred; coexistence acceptable for v1).
- Decision about archiving upstream `gftdcojp/gftd-cli` GitHub repo.

## Rollout

This ADR is the **plan**. Execution is staged:

- [ ] **Phase 0 — this ADR** (now). Plan published.
- [ ] **Phase A — git-subrepo absorb** in vendor (~5 min op + 1 commit)
- [ ] **Phase B.1 — Bulk copy + sed import rewrites** in etzhayyim (~30 min)
- [ ] **Phase B.2 — Vendor-business strip** (drop malak, vault, ambiguous-then-inspected commands)
- [ ] **Phase B verification** (build + tests + smoke)
- [ ] **Phase B commit** in etzhayyim/root
- [ ] **Phase C — vendor [MOVED] stub** for the open-scope portion
- [ ] Update CLAUDE.md Step 8 status to ✅ (or ✅-with-followups for gftd-py + scripts + config)

# Alternatives Considered

## A. Bulk sed + drop, ignore the subrepo

What I attempted this session: extract, drop malak/vault, sed-rewrite, commit. Failed because the inner `gftd/gftd/go.mod` is a separate Go module and rewriting it without absorbing the subrepo leaves the relationship broken and the build broken.

却下理由: the next `git subrepo pull` in vendor would re-overwrite the inner content from upstream, undoing the migration. Need to absorb first.

## B. Migrate everything except touch nothing in the subrepo

Keep `70-tools/gftd/gftd/.gitrepo` intact in etzhayyim, but use it pointing at a new etzhayyim-owned upstream repo.

却下理由: creates a new external repo dependency. Subrepo workflow is opaque; better to absorb. The whole point of monorepo consolidation is to NOT have external sub-repos pinned by commit hash.

## C. Two separate CLIs from day 1: `etzhayyim` (open commands only) and `gftd` (vendor commands only)

Aggressive split: take only the open commands into a new `etzhayyim` CLI in etzhayyim/root, leave `gftd` entirely in vendor for vendor commands.

却下理由: requires identifying open vs vendor for every one of the 122 commands. Most commands are open-scope; the vendor-business surface is small (~10 commands). Bulk-migrate-and-strip is faster than split-from-scratch, and the result is the same end state. Plus: the existing `etzhayyim-cli` (5-file scaffold) already occupies the `etzhayyim` binary name lane.

## D. Defer entirely

Leave `70-tools/gftd` in vendor; mark Step 8 ⏳ permanently and move on.

却下理由: contradicts ADR-2605152100's Step 8 commitment. The CLI is the developer's daily tool; it must follow the org boundary.

# References

- ADR-2605152100 vendor monorepo — establishes Step 8 obligation (vendor cross-repo URL)
- ADR-2605151500 vendor — gftd-py parallel CLI design
- CLAUDE.md (this repo, root) — Step 8 status table, 70-tools layout note
- `git-subrepo` upstream — https://github.com/ingydotnet/git-subrepo
- Existing `70-tools/etzhayyim-cli/` scaffold — small build/deploy tool, 5 files
- Migration session report 2026-05-17:
  - 27 k8s langservers migrated (commit `44a3d85d` etzhayyim, `c931d249b80` vendor)
  - 5 70-tools open dirs migrated (commit `3b83b9f0` etzhayyim, `264f542fefa` vendor)
  - 30 60-apps stubbed in vendor (commit `e7fe971d8af` vendor)
  - bpmn-timers scope-split + deep ref sweep (commit `dc45e314` etzhayyim)
- This ADR's session: bulk migration attempted, rolled back after detecting git-subrepo / nested module / build break.
