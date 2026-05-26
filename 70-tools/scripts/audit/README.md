# Audit scripts (`70-tools/scripts/audit/`)

Reusable audit scripts that surface specific classes of latent / silent / drift-prone issues in the monorepo. Each script is single-file, dep-free (stdlib Python or POSIX bash), and idempotent.

Pattern: discovery in a `/loop` iteration → fix in the same iteration → codify the audit script here for future maintenance. See the cited iteration history in each script's docstring for the original discovery context.

## Quick start — run all audits

```bash
bash 70-tools/scripts/audit/all.sh            # report
bash 70-tools/scripts/audit/all.sh --strict   # exit 1 if any finding (CI integration)
```

Current baseline (as of iter-52 of /loop, 2026-05-27): **25 total findings** — 0 dependabot + 0 SDK exports/dist + 7 stale subrepo URLs (documented in ADR-2605211845 as gftd-org-cleanup leftovers, operator choice per file) + 18 kotoba escape-symlinks (documented in ADR-2605262130 as deferred to upstream coordination) + 0 sibling-convention-drift outliers + **0 manifest-lexicon-drift** (iter-52 closed kuni-umi 6/6; full category zeroed; all 21 initial findings resolved across iters 48-52). **Both batched-fix categories now fully closed.** Remaining 25 findings are all documented-deferred awaiting upstream coordination.

The "documented + deferred" findings will fail `--strict` mode until the upstream coordination work lands. That's by design — `--strict` is the operator's gate for "I want to publish or PR-merge and don't want to accidentally take on debt." Mode without `--strict` is for "give me the current health snapshot."

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

Find `.gitrepo` files whose `remote` URL no longer resolves to a live GitHub repo (404). Excludes the COFOG tree by default (hundreds of small subrepos that warrant separate audit cadence).

```bash
bash 70-tools/scripts/audit/subrepo-upstream-health.sh                   # exclude cofog
bash 70-tools/scripts/audit/subrepo-upstream-health.sh --include-cofog
bash 70-tools/scripts/audit/subrepo-upstream-health.sh --strict          # exit 1 on findings
```

Requires: `gh` CLI authenticated.

Discovery: iter-28 (SDK `.gitrepo` was stale `gftdcojp/...`, fixed to `etzhayyim/...` in commit `957ec4c0a`) + iter-29 (broader audit found 7 more stale entries from the gftd → etzhayyim org cleanup; documented in ADR-2605211845 §"Orphaned `.gitrepo` files post-cleanup" with 3 resolution options per file).

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
**Progression**: iter-48 closed wadachi (3/3); iter-49 closed gov-municipality (3/3); iter-50 closed infra-utility-connect (4/4); iter-51 closed yoro-supply (5/5); iter-52 closed kuni-umi (6/6) + migrated legacy NSID prefix `ai.gftd.apps.etzhayyim.kuniUmi.*` → `app.etzhayyim.kuniUmi.*`. **Current: 0 missing — category FULLY CLOSED.**

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

`adr-cross-ref-health.py` has a pytest suite at
`test_adr_cross_ref_health.py` (21 tests) that locks in the
structural invariants of the 5 categories + 3 filters. Run with:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python3 -m pytest 70-tools/scripts/audit/test_adr_cross_ref_health.py -v
```

The `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` env is required because
this system's `langsmith` pytest plugin auto-loads but has a
pydantic version mismatch that crashes pytest collection. The
opt-out env bypasses third-party autoloading and lets the local
tests run cleanly. Existing tests under `70-tools/scripts/lint/`
and `70-tools/scripts/open-ot/` have the same requirement.

The tests are pure — no live filesystem dependency for category /
filter tests; only the end-to-end smoke tests touch the disk. Tests
should always pass in <1s.

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
