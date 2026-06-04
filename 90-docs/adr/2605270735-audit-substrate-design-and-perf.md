---
id: adr-2605270735-audit-substrate-design-and-perf
title: "ADR-2605270735: Audit substrate — design, perf, and operator workflow"
status: accepted
doc_type: adr
topic: audit-substrate
authoritative: true
last_verified: 2026-05-27
priority: 4.0
axis: tooling
weight: 0.40
priority_note: "Tooling ADR — documents the audit-substrate state at iter-62 of /loop"
authoritative_for:
  - audit-aggregator-design
  - audit-script-perf-pattern
  - audit-test-coverage-conventions
depends_on:
  - adr-2605211845-etzhayyim-org-cleanup-completion-and-kami-engine-sdk-standalone
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2604231349-timestamp-numbering-policy
  - adr-2605190900-kg-as-lexicon-ipld-oxigraph-appview
related:
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
supersedes: []
superseded_by: []
---

# ADR-2605270735: Audit substrate — design, perf, and operator workflow

**Status**: accepted
**Date**: 2026-05-27
**Deciders**: Jun Kawasaki

## Context

Across iterations 30-62 of `/loop` (2026-05-26 → 2026-05-27) the
audit substrate at `70-tools/scripts/audit/` was built up from
zero to a feature-complete, performant, well-tested, regression-
guarded surface. This ADR captures the state at iter-62 as
institutional memory — so a new operator (or LLM agent) landing
on the directory can understand the design at a glance instead
of reverse-engineering it from 30+ commits.

## Decision

The audit substrate consists of two layers:

### Layer 1 — six aggregator scripts (in `all.sh`)

Each script audits one structural drift class. Each emits a final
summary line ending in `: <int>$` so the aggregator can roll up
the count via `tail -1 | grep -oE '[0-9]+$'`.

| Script | Drift class | Iter-62 finding count |
|---|---|---|
| `dependabot-defunct.py` | `.github/dependabot.yml` entries pointing at non-existent dirs | 0 |
| `sdk-exports-dist.py` | `package.json` subpath exports → non-existent dist files | 0 |
| `sibling-convention-drift.py` | `@etzhayyim/*` packages missing standard fields | 0 |
| `subrepo-upstream-health.sh` | `.gitrepo` URLs returning 404 | 7 (documented-deferred ADR-2605211845) |
| `subrepo-symlink-health.sh` | Symlinks inside subrepos escaping subrepo boundary | 18 (documented-deferred ADR-2605262130) |
| `manifest-lexicon-drift.py` | Actor manifest declares lexicon NSIDs without matching JSON files | 0 |

Total aggregator baseline: **25 findings**, all documented-deferred
awaiting upstream coordination.

### Layer 2 — three standalone scripts (operator on-demand)

High-volume audits that would obscure new drift if folded into the
aggregator:

| Script | Findings | Why standalone |
|---|---|---|
| `adr-cross-ref-health.py` | 118 orphan ADR refs across 3 categories | Each orphan needs per-case operator judgment between typo-fix / write-ADR / drop-cite |
| `validate-lexicons.py --root` (pre-existing) | 3,198 lexicon-spec violations | Mostly legacy `etzhayyim/` namespace; per-case judgment |
| `repo-record-allowlist.mjs` (pre-existing) | (operator-invoked) | XRPC repo-record allowlist guard |

## Performance design pattern

**The single most important pattern**: replace filesystem walking
with git-index reads + parallelize subprocess-bound work.

| Anti-pattern | Replace with |
|---|---|
| `find . -name "..."` | `git ls-files \| grep "..."` |
| `Path(repo).rglob("...")` | `git ls-files "*.ext"` via subprocess |
| Serial network calls in shell loop | `xargs -I {} -P 10 bash -c '...'` |
| Sequential Python CPU/IO checks | `concurrent.futures.ThreadPoolExecutor` |

`git ls-files` reads the git index directly (~25 ms for the whole
repo) instead of walking the worktree (~2.5 s + walking node_modules
/ dist / build / etc. trees that would be filtered out anyway).
`git ls-files` also honours .gitignore for free, so filter lists
shrink.

### Cumulative perf wins (iters 5-7, 56, 57, 61)

| Tool | Pre-optimization | Post-optimization | Cumulative speedup |
|---|---|---|---|
| `e7m verify` (iters 5-7 pathlib→git ls-files + iter-56 threading) | 121 s | 0.71 s | **170x** |
| `audit aggregator` (iter-57 + iter-61) | 47.5 s | 1.1 s | **43x** |

Both wins are regression-guarded by perf-budget tests in
`test_subrepo_scripts.py` (TestSubrepoUpstreamHealth /
TestSubrepoSymlinkHealth `test_performance_budget`) and by
structural canaries that fail if the optimization patterns are
removed from the script body (`test_uses_git_ls_files_not_find`).

## Test coverage

Four pytest suites lock in the substrate's invariants (67 tests,
combined wall ~5 s):

| Suite | Tests | Locks in |
|---|---|---|
| `test_adr_cross_ref_health.py` | 21 | 5 ADR-orphan categories + 3 structural filters (range / forward-ref / historical-orphan) |
| `test_manifest_lexicon_drift.py` | 13 | NSID regex + NSID→path mapping + post-closure-zero-drift CANARY |
| `test_subrepo_scripts.py` | 16 | stale-URL + escape-symlink counts + iter-57 perf budgets + structural canaries |
| `test_simple_audits.py` | 17 | 3 simple-audit smoke tests + aggregator-format-contract for all 3 |

The **`test_post_closure_zero_drift` canary** in
`test_manifest_lexicon_drift.py` walks every actor's
`manifest.jsonld` and asserts every declared lexicon NSID has a
matching JSON file. If a future PR introduces drift, CI fails
fast before the aggregator's report-only output.

Run combined:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python3 -m pytest 70-tools/scripts/audit/ -v
```

The `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` env bypasses a broken
`langsmith` pytest plugin in the dev box's Python install (the
CI image is clean; the env is safe to set unconditionally).

## CI workflow

`.github/workflows/audit-health.yml` runs on push to main, pull
requests to main, and `workflow_dispatch`. Triggers on:

- Audit infrastructure: `.github/dependabot.yml`,
  `.github/workflows/audit-health.yml`, `70-tools/scripts/audit/**`
- Things audits check:
  `40-engine/kami-engine/kami-engine-sdk/package.json`,
  `**/.gitrepo`, `20-actors/**/manifest.jsonld`,
  `00-contracts/lexicons/**/*.json`, `90-docs/adr/**/*.md`

Workflow steps:

1. Checkout
2. Python 3.12 setup
3. `pip install pytest`
4. **Strict pytest** (fails CI on any test regression)
5. **Non-strict aggregator** (reports findings vs baseline, never fails)

## Drift category closures

Two drift categories were fully zeroed during the substrate buildout:

- `sibling-convention-drift` closed iter-39 (14 outliers fixed —
  10 missing-license filled with Apache-2.0 default per
  ADR-2605192200; 4 missing-description authored)
- `manifest-lexicon-drift` closed iter-52 (21 lexicons authored
  across 5 actors: wadachi/gov-municipality/infra-utility-connect/
  yoro-supply/kuni-umi; iter-58 added 4 more for yobel — total 25
  lexicons across 6 actors)

The 25-lexicon corpus encodes constitutional gates (Council Lv6+ ≥3
signatures, ≥2 robot DID witnesses per CLAUDE.md witness invariant,
Charter Rider compliance, IPFS-pinned content) as JSON-schema
const / minLength / knownValues constraints — clients can verify
gate-compliance from the Lexicon alone without invoking the actor.

## Consequences

**Positive**:

- Audit aggregator runs in ~1.1 s — operators can invoke pre-PR
  with no friction.
- 67 tests catch regressions in CI before merge.
- Two drift categories are at 0 with regression canaries.
- New contributors discover the perf pattern (git ls-files +
  parallelize) via `audit/README.md` and apply it consistently.

**Negative**:

- 4 of the 6 aggregator scripts now depend on git being present
  + the working directory being inside a git repo. Pre-clone or
  detached-HEAD edge cases fall back to slower `pathlib.rglob`
  paths where wired in.

**Documented-deferred**:

- 7 stale subrepo URLs (`subrepo-upstream-health`) — operator
  choice per file per ADR-2605211845 (3 options: Update / Detach /
  Leave-as-is).
- 18 kotoba escape-symlinks (`subrepo-symlink-health`) — upstream
  coordination per ADR-2605262130 (charter-rider symlink
  standalone-distribution issue).
- 118 ADR cross-ref orphans across 3 open categories — per-case
  triage.
- 3,198 lexicon-spec violations (mostly legacy `etzhayyim/` namespace
  carrying pre-ADR-2605190900 `type: "number"` floats).

## Alternatives Considered

1. **Single-Python orchestrator instead of bash `all.sh`** — would
   centralize but lose per-script `python3` / `bash` independence.
   Rejected; aggregator format contract (`: <int>$` final line) is
   simple and verified by `test_simple_audits.py
   TestAggregatorFormatContract`.

2. **Fold all standalone audits into `all.sh`** — would balloon the
   baseline 25 → 3,341 and obscure new drift. Rejected; standalone
   pattern is the right shape for high-volume per-case-triage audits.

3. **`ripgrep` / `fd` instead of `git ls-files`** — both faster than
   the optimized state, but introduce a binary dependency. git is
   already universal. Marginal gain not worth the deps.

## References

- `70-tools/scripts/audit/README.md` — current operator entry point
- `70-tools/scripts/audit/all.sh` — aggregator
- `.github/workflows/audit-health.yml` — CI integration
- ADR-2605211845 — etzhayyim-org-cleanup leftovers (7 stale subrepo URLs)
- ADR-2605262130 — kotoba storage substrate (18 escape-symlinks)
- ADR-2605262400 — public-data ingestion (manifest format precedent)
- ADR-2605262700 — chigiri (Tier-B actor charter pattern)
- ADR-2604231349 — timestamp-numbering-policy (ADR IDs in
  `adr-cross-ref-health.py`)
- ADR-2605190900 — Lexicon-spec (no float, integer with implied units)
- ADR-2605231525 — no-server-key invariant (verified by `e7m verify`)
- ADR-2605192200 — Charter Rider (Apache-2.0 default license)
