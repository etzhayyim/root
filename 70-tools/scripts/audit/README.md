# Audit scripts (`70-tools/scripts/audit/`)

Reusable audit scripts that surface specific classes of latent / silent / drift-prone issues in the monorepo. Each script is single-file, dep-free (stdlib Python or POSIX bash), and idempotent.

Pattern: discovery in a `/loop` iteration → fix in the same iteration → codify the audit script here for future maintenance. See the cited iteration history in each script's docstring for the original discovery context.

## Quick start — run all audits

```bash
bash 70-tools/scripts/audit/all.sh                       # aggregator report (~1.1 s wall)
bash 70-tools/scripts/audit/all.sh --strict              # exit 1 if any finding (CI integration)
bash 70-tools/scripts/audit/all.sh --test                # full pytest suite (~8 s wall)
bash 70-tools/scripts/audit/all.sh --test test_foo.py    # single test file (~3 s wall)
bash 70-tools/scripts/audit/all.sh --all                 # pytest + aggregator (~9 s wall)
```

The `--test` and `--all` modes wrap the canonical pytest invocation
(`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest ...`) so operators
don't have to remember the env var or the five test file paths. The
env var is required because this system's `langsmith` pytest plugin
crashes on load (pydantic version mismatch); the env bypasses
third-party autoloading.

Pytest failures always exit non-zero (regressions should never silently
pass); `--strict` only applies to the aggregator's findings count.

`--test <file>` targets one suite for fast reruns during development
(no need to wait for all 87 tests to validate one filter change).

Current baseline (as of iter-61 of /loop, 2026-05-27): **25 total findings** — 0 dependabot + 0 SDK exports/dist + 7 stale subrepo URLs (documented in ADR-2605211845 as etzhayyim-org-cleanup leftovers, operator choice per file) + 18 kotoba escape-symlinks (documented in ADR-2605262130 as deferred to upstream coordination) + 0 sibling-convention-drift outliers + **0 manifest-lexicon-drift** (iter-52 closed kuni-umi 6/6; full category zeroed; all 21 initial findings resolved across iters 48-52). **Both batched-fix categories now fully closed.** Remaining 25 findings are all documented-deferred awaiting upstream coordination.

The "documented + deferred" findings will fail `--strict` mode until the upstream coordination work lands. That's by design — `--strict` is the operator's gate for "I want to publish or PR-merge and don't want to accidentally take on debt." Mode without `--strict` is for "give me the current health snapshot."

## Performance

The aggregator's wall time was reduced from 47.5 s to ~1.1 s across iters 57 + 61 (43x cumulative). The pattern: replace filesystem walking (`find` / `pathlib.rglob`) with `git ls-files` reads of the git index, and parallelize subprocess-bound work (e.g. `gh repo view` calls via `xargs -P10`).

| Iter | Tool | Anti-pattern → Fix | Speedup |
|---|---|---|---|
| 57 | `subrepo-upstream-health.sh` | `find . -name` → `git ls-files`; serial `gh` → `xargs -P10` | 35x (20.7s → 0.6s) |
| 57 | `subrepo-symlink-health.sh` | nested `find -type l` → single `git ls-files -s` mode-120000 scan | 35x (16.9s → 0.5s) |
| 61 | `sibling-convention-drift.py` | `repo.rglob("package.json")` → `git ls-files *package.json` | 45x (9.07s → 0.20s) |
| **agg.** | `all.sh` total | (cumulative of above) | **43x (47.5s → 1.1s)** |

The same pattern was applied to `e7m verify` across iters 5-7 + 56 (170x cumulative). All wins are regression-guarded by perf-budget and structural-canary tests in `test_subrepo_scripts.py`.

## Scripts

### `dependabot-defunct.py`

Find `.github/dependabot.yml` `directory:` entries pointing at paths that don't exist on disk. GitHub Actions' dependabot silently no-ops on missing directories; removing defunct entries reduces background noise.

```bash
python3 70-tools/scripts/audit/dependabot-defunct.py        # report
python3 70-tools/scripts/audit/dependabot-defunct.py --strict  # exit 1 on findings (for CI)
```

Discovery: iter-18 (20-actors/kami-engine-sdk retirement, commit `18967431a`) + iter-23 (7 Foundry-vendored-lib subpath entries, commit `931cf9156`).

### `sdk-exports-dist.py`

Find `package.json` subpath-export targets that don't exist in `dist/`. When the build script doesn't generate an exports target, TypeScript / bundlers silently fall back to `any` types — a regression vs. a working `types` pointer.

```bash
python3 70-tools/scripts/audit/sdk-exports-dist.py                # audits SDK by default
python3 70-tools/scripts/audit/sdk-exports-dist.py <pkg-dir>      # audits another package
python3 70-tools/scripts/audit/sdk-exports-dist.py <pkg-dir> --strict
```

Discovery: iter-26 / iter-27 (`./genko/components` `types` pointed at non-existent `index.d.ts`, commit `66feacc5f`).

### `subrepo-upstream-health.sh`

Find `.gitrepo` files whose `remote` URL no longer resolves to a live GitHub repo (404). The former COFOG exception was removed when that application moved to its standalone repository.

```bash
bash 70-tools/scripts/audit/subrepo-upstream-health.sh
bash 70-tools/scripts/audit/subrepo-upstream-health.sh --strict          # exit 1 on findings
```

Requires: `gh` CLI authenticated.

Discovery: iter-28 (SDK `.gitrepo` was stale `etzhayyimcojp/...`, fixed to `etzhayyim/...` in commit `957ec4c0a`) + iter-29 (broader audit found 7 more stale entries from the etzhayyim → etzhayyim org cleanup; documented in ADR-2605211845 §"Orphaned `.gitrepo` files post-cleanup" with 3 resolution options per file).

### `subrepo-symlink-health.sh`

Find symlinks INSIDE git-subrepo trees whose targets escape the subrepo boundary (`../../...` going above the subrepo root) and therefore dangle when the subrepo is cloned standalone or extracted as an npm tarball.

```bash
bash 70-tools/scripts/audit/subrepo-symlink-health.sh
bash 70-tools/scripts/audit/subrepo-symlink-health.sh --strict
```

Discovery: iter-24 (SDK's `CHARTER-RIDER.md` was a dangling symlink to `../../../CHARTER-RIDER.md`; replaced with real-file mirror in commit `bdecb113e`) + iter-31 (broader audit found 18 same-pattern symlinks in `40-engine/kotoba/` subrepo — 1 root + 17 per-crate; documented in ADR-2605262130 §"Charter Rider symlink standalone-distribution issue" with the iter-24 fix pattern as precedent).

### `sibling-convention-drift.py`

Find `@etzhayyim/*` package.json files missing standard top-level fields (publishConfig / license / repository / engines / description) that ≥80% of sibling packages declare. Catches convention-drift outliers — the kind of bug that doesn't surface until someone tries to publish or install.

```bash
python3 70-tools/scripts/audit/sibling-convention-drift.py
python3 70-tools/scripts/audit/sibling-convention-drift.py --strict
```

Discovery: iter-36 (SDK was missing `publishConfig` while every sibling `@etzhayyim/*` package had a standard 2-field block `{access: public, registry: npm.pkg.github.com}`; fixed in commit `488021b6e`). iter-37 codified the audit pattern + surfaced 14 more outliers (4 missing `description` + 10 missing `license`) for per-package operator decision.

### `manifest-lexicon-drift.py`

Find lexicons declared in actor `manifest.jsonld` files (under `20-actors/<actor>/`) that don't have a corresponding JSON file in `00-contracts/lexicons/`. Distinguished from the pre-existing `nsid-lexicon-exists.mjs` lefthook lint: that linter scans static code patterns (`atProcedure("nsid")` / `atQuery("nsid")` / `.api.call("nsid")`). Manifest declarations are a separate surface — the actor's planning artifact lists which lexicons it intends to ship; if those lexicons never got authored, the contract surface is incomplete.

```bash
python3 70-tools/scripts/audit/manifest-lexicon-drift.py
python3 70-tools/scripts/audit/manifest-lexicon-drift.py --strict
```

**Initial baseline (iter-47): 21 missing lexicons across 5 actors.**
**Progression**: iter-48 closed wadachi (3/3); iter-49 closed gov-municipality (3/3); iter-50 closed infra-utility-connect (4/4); iter-51 closed yoro-supply (5/5); iter-52 closed kuni-umi (6/6) + migrated legacy NSID prefix `com.etzhayyim.apps.etzhayyim.kuniUmi.*` → `com.etzhayyim.kuniUmi.*`. **Current: 0 missing — category FULLY CLOSED.**

| Actor | Missing | Status |
|---|---|---|
| gov-municipality | 0 | ✅ closed iter-49 |
| infra-utility-connect | 0 | ✅ closed iter-50 |
| kuni-umi | 0 | ✅ closed iter-52 (+ NSID migration to canonical prefix) |
| wadachi | 0 | ✅ closed iter-48 |
| yoro-supply | 0 | ✅ closed iter-51 |

Per-actor resolution is operator-judgment-per-case: either (a) author the lexicon JSON files (real implementation work) or (b) drop the manifest declaration (acknowledge the planning didn't reach implementation). Same operator-gated pattern as the documented kotoba escape-symlinks + stale subrepo URLs.

Discovery: iter-47 of /loop (2026-05-27).

### `adr-cross-ref-health.py`

Find `ADR-NNNN` references in any tracked file that don't resolve to an actual ADR file under `90-docs/adr/`. Catches typos, mis-pastes, and planned-but-never-written ADRs.

```bash
python3 70-tools/scripts/audit/adr-cross-ref-health.py
python3 70-tools/scripts/audit/adr-cross-ref-health.py --strict
```

**Baseline (iter-45, 2026-05-27): 118 orphaned references** across the monorepo, bucketed by category:

| Category | Count | Resolution |
|---|---|---|
| `legacy-4digit` | 74 | Pre-ADR-2604231349-timestamp-policy IDs. Rename to successor / delete |
| `placeholder-0000-suffix` | 0 | (Closed iter-42/43; was 3 at iter-40 start) |
| `invalid-mm-overflow` | 0 | (Closed iter-44; was 2 — :60 clock-impossibility bugs) |
| `quarter-hour-planned-slot` | 39 | Planned-but-unauthored ADRs. Author or downgrade citation to parent wave |
| `non-canonical-mm` | 5 | MM not in {00,15,30,45} but valid — wave-numbering reservations (e.g., kotoba uses :04/:05/:06 as sub-index). Per-case judgment |

Progression: iter-40 = 127 → iter-41 = 123 → iter-42 = 121 → iter-43 = 120 → iter-44 = 119 → iter-45 = 118 (historical-orphan filter added — citations containing both "drafted" AND one of {"not retained", "originally", "standalone", "inline", "merged"} are self-documenting forensic notes, not bugs).

The historical-orphan filter was specifically motivated by the ADR-2605211653 case (mst-projector standalone ADR drafted during tranche-f cutover then merged inline into ADR-2605211757; all 5 citations are session post-mortem notes explicitly describing the merge).

Operators run on demand:

```bash
python3 70-tools/scripts/audit/adr-cross-ref-health.py | less
```

Each orphan needs operator judgment between three resolution paths (typo-fix / write-the-ADR / delete-the-cite). Because the resolution is per-case, this audit is **deliberately NOT included in `all.sh`** today — folding it in would add a 123-finding cliff to the aggregator total and force a global decision when what's needed is per-citation review.

When the 123 are triaged down to a stable floor, this audit can be folded into `all.sh` like the others. Until then it lives as a standalone operator tool.

Discovery: iter-40 of /loop (2026-05-27); filter improvements + categorization in iter-41.

## Testing

Seven pytest suites lock in the substrate's structural invariants
so future refactors don't silently break filter/regex/path-mapping
logic, undo perf optimizations, change operator-facing CLI shape,
or revert config-file fixes:

| Suite | Tests | Locks in |
|---|---|---|
| `test_adr_cross_ref_health.py` | 21 | 5 categories + 3 filters (range / forward-ref / historical-orphan) |
| `test_manifest_lexicon_drift.py` | 13 | NSID regex + NSID-to-path mapping + post-closure-zero-drift canary |
| `test_subrepo_scripts.py` | 16 | Stale-URL + escape-symlink counts + iter-57 perf budgets + structural canaries (git ls-files / xargs -P / no `find .`) |
| `test_simple_audits.py` | 17 | dependabot-defunct + sdk-exports-dist + sibling-convention-drift smoke + aggregator format contract |
| `test_e7m_verify_perf.py` | 7 | e7m verify 9-invariant correctness + iter-56 perf budget (5 s) + structural canaries (ThreadPoolExecutor + git-grep) |
| `test_gitmodules.py` | 5 | iter-65 `.gitmodules ignore = dirty` fix + behavioral verification (git status emits no symlink-loop warning) |
| `test_all_sh.py` | 13 | Aggregator end-to-end (rollup count = 25 baseline + all 6 scripts invoked + `--strict` / `--test` / `--all` modes + arg validation + perf budgets) |

All six run via the same pytest invocation:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python3 -m pytest 70-tools/scripts/audit/ -v
```

Combined: **92 tests, ~26 s total** (subrepo + e7m + all_sh tests run real subprocess invocations; correctness tests <0.1 s combined).

Every aggregator script (6/6) + the standalone adr-cross-ref-health + the e7m verify pre-commit hook + the aggregator orchestration + the .gitmodules config fix are now test-covered.

`test_all_sh.py` uses `@pytest.fixture(scope="module")` to memoize the 4 distinct `bash all.sh` invocations across its 13 tests (52 s → 20 s).

The `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` env is required because
this system's `langsmith` pytest plugin auto-loads but has a
pydantic version mismatch that crashes pytest collection. The
opt-out env bypasses third-party autoloading and lets the local
tests run cleanly. Existing tests under `70-tools/scripts/lint/`
and `70-tools/scripts/open-ot/` have the same requirement.

The tests are pure — no live filesystem dependency for category /
filter / mapping tests; only the end-to-end smoke tests touch the
disk. Combined suite runs in <0.1s.

The `test_post_closure_zero_drift` canary in
`test_manifest_lexicon_drift.py` is a regression guard: it walks
all `20-actors/*/manifest.jsonld` files and asserts every declared
lexicon NSID has a corresponding JSON file. If a future PR
introduces new manifest-lexicon drift, this test fails fast
(prior to the aggregator's report-only output).

### `validate-lexicons.py` (pre-existing, standalone full-tree mode)

The religious-corp Lexicon-spec validator at `70-tools/scripts/validate-lexicons.py` is the source of truth for `lexicon: 1` AT-Protocol-Lexicon-spec + religious-corp invariants (no float types, integer-with-implied-units per ADR-2605190900, refs over inline objects, etc.).

The lefthook hook `validate-religious-corp-lexicons` runs it in staged-files mode (one commit's worth of touched JSON). For a full-tree health check across all `00-contracts/lexicons/com/etzhayyim/`:

```bash
python3 70-tools/scripts/validate-lexicons.py \
  --root 00-contracts/lexicons/com/etzhayyim/ \
  --exit-on-error
```

**Standalone full-tree baseline (iter-59, 2026-05-27): 3,198 errors across 6,292 lexicons:**

| Error class | Count | Location concentration |
|---|---|---|
| `type='number'` (float type forbidden) | 2,473 | `etzhayyim/` legacy 1,687; newer actor dirs ~786 |
| `inline type='object'` (use `ref` instead) | 547 | spread across actor lexicons |
| `invalid format` | 168 | various |
| `other` | 8 | various |
| `lexicon != 1` (spec version) | 2 | pre-spec-v1 holdouts |

This audit is **deliberately NOT folded into `all.sh`** today because:
- It would add a 3,198-finding cliff to the 25-finding aggregator baseline.
- The `etzhayyim/` subdirectory (1,687 errors / 53% of the total) is legacy cutover residue — fixing requires either bulk rename of the namespace or accepting that legacy lexicons keep their pre-spec syntax.
- Each non-etzhayyim violation requires per-file judgment (some `number` types are deliberate where decimal precision is needed; the religious-corp spec was tightened post-authoring).

Operators run it on demand. The lefthook hook in staged-files mode continues to enforce the spec on NEW lexicons (verified across iters 48-58 where 30 newly-authored lexicons all pass validation).

Authored-and-clean lexicon directories (iters 48-58):
`wadachi/` / `gov/` (the 3 newly-authored ones — 5 pre-existing files in this dir use the older spec) / `infra/` / `supply/` / `kuniUmi/` / `yobel/`. Combined: 30 lexicons / 0 errors.

### `repo-record-allowlist.mjs` (pre-existing)

XRPC repo-record allowlist guard. See the script's docstring for usage. Unrelated to the `/loop` iter-18..29 audit scripts above.

## When to add a new script here

If a `/loop` iteration surfaces a class of latent issue via a one-off audit that's likely to recur (because the underlying drift pattern — directories deleted without cleanup, build configs evolving, org renames not propagating, etc. — is structural rather than one-shot), codify the audit as a script here.

Naming: `<surface>-<problem>.{py,sh,mjs}`. Each script should:

1. Single-file (no install step beyond `python3` / `bash` / `node` being available)
2. Self-documenting (docstring with usage + history references)
3. Idempotent + read-only (no mutation of the repo)
4. Default exit code 0; `--strict` makes findings fatal (for CI integration)
5. Pull repo root via `Path(__file__).resolve().parents[N]` (Python) or `cd "$(dirname "$0")/../../.."` (bash) so the script works regardless of caller's `cwd`

## How to add a new audit (recipe)

If you're adding a 7th aggregator script (or beyond), follow this 6-step recipe so the new audit fits the existing aggregator + test + CI conventions. Each step is small; missing one creates silent drift.

### 1. Write the audit script

Create `70-tools/scripts/audit/<surface>-<problem>.py` (or `.sh`). It MUST:

- Discover files via `git ls-files` (never `find` or `pathlib.rglob` — see "Performance" section above)
- Emit a final summary line in the format `<label>: <int>` (the aggregator's `tail -1 | grep -oE '[0-9]+$'` extractor depends on this)
- Accept `--strict` and exit 1 when findings > 0 (otherwise exit 0)
- Have a top-of-file docstring with: purpose, history (which `/loop` iter discovered the drift), `Usage:` examples

### 2. Wire it into the aggregator

Edit `70-tools/scripts/audit/all.sh`:

```bash
run "<surface>-<problem>" python3 70-tools/scripts/audit/<surface>-<problem>.py
```

Insert in declaration order (matches the script-list comment block at the top of the file). Update the comment block's history entry with the `/loop` iter that introduced this audit.

### 3. Write a pytest suite

Create `70-tools/scripts/audit/test_<surface>_<problem>.py`. Follow the iter-46/53/60/61 patterns:

- Load the script via `importlib.util.spec_from_file_location` (for Python scripts) or `subprocess.run(["bash", str(path)])` (for shell scripts)
- Test: script exists + runs clean (exit 0 non-strict) + emits the aggregator-compatible summary line + `--strict` semantics (exit 1 with findings)
- If the script has non-trivial regex/filter/mapping logic, add per-function unit tests too (see `test_adr_cross_ref_health.py` as the gold standard)
- If the script has a perf optimization to preserve, add a wall-time budget test AND a structural canary asserting the optimization pattern still appears in the source (see `test_subrepo_scripts.py`)

### 4. Wire pytest into `all.sh --test` and the workflow

Two locations need the new test file path:

- `70-tools/scripts/audit/all.sh` — the pytest invocation inside the `if [ "$TEST" -eq 1 ]` block. Update the comment line `"── pytest suite (N files / M tests) ──"` count.
- `.github/workflows/audit-health.yml` — the `python3 -m pytest ...` invocation under "Run audit script tests".

### 5. Update this README

Add a row in the "Scripts" section (above) with the script's purpose + initial baseline. If the finding count is high-volume and per-case-triage-y, document it as a standalone audit instead and skip step 2 (the aggregator-wire step) — see the `adr-cross-ref-health.py` + `validate-lexicons.py` precedents.

Update the testing table near the top with the new pytest suite row.

### 6. Run the full pipeline + verify baseline

```bash
bash 70-tools/scripts/audit/all.sh --all
```

The aggregator total should match the previous baseline + your new audit's count. Update the README's `Current baseline (as of iter-NN of /loop)` line. Update the `audit-health.yml` workflow's job-summary section to match.

For the iter-39 precedent of how to phrase "documented + deferred" findings (the kotoba 18-symlink case + the 7-subrepo case), see the existing entries in the README's "Quick start" section.

Optional 7th step: if your new audit closes drift that's discussed in CLAUDE.md (root or sub-CLAUDE), update those references. The audit substrate's institutional memory ADR (ADR-2605270735) is also a place to extend if your audit fits the design.
