# Audit scripts (`70-tools/scripts/audit/`)

Reusable audit scripts that surface specific classes of latent / silent / drift-prone issues in the monorepo. Each script is single-file, dep-free (stdlib Python or POSIX bash), and idempotent.

Pattern: discovery in a `/loop` iteration → fix in the same iteration → codify the audit script here for future maintenance. See the cited iteration history in each script's docstring for the original discovery context.

## Quick start — run all audits

```bash
bash 70-tools/scripts/audit/all.sh            # report
bash 70-tools/scripts/audit/all.sh --strict   # exit 1 if any finding (CI integration)
```

Current baseline (as of iter-39 of /loop, 2026-05-27): **25 total findings** — 0 dependabot + 0 SDK exports/dist + 7 stale subrepo URLs (documented in ADR-2605211845 as gftd-org-cleanup leftovers, operator choice per file) + 18 kotoba escape-symlinks (documented in ADR-2605262130 as deferred to upstream coordination) + **0 sibling-convention-drift outliers** (iter-38 filled in 10 missing-`license` with `"license": "Apache-2.0"` per religious-corp default ADR-2605192200; iter-39 filled in 4 missing-`description` with package-specific content via Edit tool — bpmn-sdk-dmn / bpmn-sdk-form / svelte/auth / svelte/design-system).

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

### `adr-cross-ref-health.py`

Find `ADR-NNNN` references in any tracked file that don't resolve to an actual ADR file under `90-docs/adr/`. Catches typos, mis-pastes, and planned-but-never-written ADRs.

```bash
python3 70-tools/scripts/audit/adr-cross-ref-health.py
python3 70-tools/scripts/audit/adr-cross-ref-health.py --strict
```

**Initial baseline (iter-40, 2026-05-27): 127 orphaned references** across the monorepo — too many for blind batch-fix (each one needs operator triage between three resolution paths):

1. **Typo / mis-paste** → rename to the nearest valid ID
2. **Planned ADR** → actually write the missing ADR file
3. **Legit-removable stub** → delete the reference

Because the resolution is operator-judgment-per-case, this audit is **deliberately NOT included in `all.sh`** today — it would add a 127-finding cliff to the aggregator total and force a global decision when what we want is per-citation review. Operators run it on demand:

```bash
python3 70-tools/scripts/audit/adr-cross-ref-health.py | less
```

When the 127 are triaged down to a stable floor, this audit can be folded into `all.sh` like the others. Until then it lives as a standalone operator tool.

Discovery: iter-40 of /loop (2026-05-27). The 472 ADR files on disk are referenced 563 times across tracked content; 127 of those references (~23%) don't resolve to a file. Round-number suffixes (3 IDs ending in `0000`) are obvious placeholders never authored; the other 124 are either typos near a real ADR ID or planned-but-deferred work.

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
