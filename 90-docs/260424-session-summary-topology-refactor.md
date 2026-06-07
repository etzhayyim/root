---
id: doc-260424-session-summary-topology-refactor
title: "Session summary: yoro/PDS/AppView topology refactor + γ2 one-button cutover (2026-04-24)"
status: active
doc_type: reference
topic: session-log
authoritative: false
last_verified: 2026-04-24
related:
  - adr-2604241038-yoro-pds-ideal-topology
  - adr-2604241121-repo-commit-stays-on-pds
  - adr-2604241342-kotoba-out-of-band-migration-pattern
  - doc-260424-ephemeral-runbook-convention
---

# Scope

Long-running session on 2026-04-24 that started as "why does
`yoro.etzhayyim.com/profile/sh1n5h1x.etzhayyim.com` show 0 posts" and ended with a
production topology refactor (yoro purified, bsky AppView Worker live,
γ2 cutover fully automated). 2 PRs merged (#1115 + #1117), 3 new
ADRs, ~30 commits, LaunchAgent on the operator's machine for the
14-day γ2 observation window.

This doc is the record — not authoritative for any single decision,
just the log of what happened and where to find the pieces.

# What shipped

## PR #1115 — `feat(topology): γ2 cutover + sh1n5h1x fix + migration pattern` (merged 06:54:34Z → `fd749574c56`)

- **γ2 legacy-trust cutover automation (`com.etzhayyim.legacy-trust-tally`)**
  - Runbook `90-docs/260424-legacy-trust-headers-cutover-runbook.md` with
    real-log `[trust][legacy] hit did=... matched=...` pre-flip query.
  - Daily observation probe `70-tools/scripts/legacy-trust-tally-probe.sh`
    (60 s `wrangler tail` sample of `etzhayyim-appview`, appends to
    `90-docs/260424-legacy-trust-tally.log`).
  - macOS LaunchAgent `50-infra/launchd/com.etzhayyim.legacy-trust-tally.plist`
    firing daily at 09:17 local for the full 14-day window (Claude's
    `/schedule` caps at 7 d; launchd carries the rest).
  - Pre-written cleanup `70-tools/scripts/cleanup-legacy-trust-headers.sh`
    (DRY_RUN-capable) that removes `LEGACY_TRUST_HEADERS` from 4
    wranglers + both code surfaces in one invocation.
  - Strict-mode preflight `50-infra/cloudflare/workers/atproto/scripts/
    oauth-strict-mode-preflight.sh` — 3 gates (deploy age, warn-log
    rates, smoke) exit-coded so the operator can't flip without green.
  - ADR-2604241038 addendum "β2 lesson" — 2-stage deploy budget for any
    new Worker against Kotoba/Datomic, because the first deploy typically
    exposes a parameterized-LIMIT or sql-dialect mismatch.

- **sh1n5h1x postsCount fix (0 → 1425+)**
  - Migration `20260424014529_mv_actor_social_stats_root_normalization`
    rebuilt 3 MVs (`mv_actor_social_stats` + `mv_actor_canonical_did`
    + `mv_profile_core_stats`) with `GROUP BY normalize_actor_did(repo)`
    so path-DID posts aggregate under the root DID.
  - First-ever deploy of `etzhayyim-appview` Worker — claimed
    `bsky.etzhayyim.com/*` route (was falling through to routing-gateway's
    BPMN-as-actor catch-all, which returned "no active binding").
  - `profile.ts` MV LIMIT fix — Kysely's `.limit(1)` generates
    `LIMIT $N` which RW's sql_parser rejects for MV SELECTs; replaced
    with `sql` template inlining `LIMIT 1` literal.
  - `feed.ts` MV LIMIT fix — same pattern applied to 2 viewer-context
    MV queries.
  - Smoke `70-tools/scripts/sh1n5h1x-profile-smoke.sh` — end-to-end
    gate: bsky.etzhayyim.com getProfile postsCount ≥ 1 + getAuthorFeed
    counter-check + yoro SSR resolves + yoro `/xrpc/*` returns 410
    (ADR-2604241038 Phase ε).

- **Out-of-band migration reality codified (ADR-2604241342)**
  - Helper `30-graph/graph-schema/scripts/apply-pending.sh` — one
    command wraps macOS Keychain DATABASE_URL resolve + ON-CONFLICT
    preflight + `run-one-migration.mjs` + kysely_migration row
    insert + `pnpm db:drift` + `pnpm db:gen`.
  - ADR documents 4 distinct failure modes of `pnpm db:migrate
    latest` on this repo (kysely corruption guard / ON CONFLICT in
    RW / vitest files next to migrations / unsupported DDL like
    `CREATE UNIQUE INDEX` + `DROP CASCADE`).
  - Migrations retired via the helper in this session:
    datacenter × 2, open_seiyaku × 2, lawyer, yabai-batch-3,
    sh1n5h1x MV rebuild, animeka (rewritten),
    gyosei (rewritten), vertex_datacenter, + 7 UDF
    kysely_migration row backfills.
  - Queue empty at end-of-session.

- **BPMN yabai batch-3 routing**
  - `NSID_EXACT_MATCH_TABLE` entries for `crtshFuzzySearch` +
    `reverseIpLookup` + `enrichLegalEntity` so PDS dispatch hits
    `dispatcher.etzhayyim.com` for these 3 pivots.
  - Graph migration
    `20260424120000_seed_yabai_batch3_bpmn_actors.ts` registers
    both the `vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding`
    rows. F5 watcher deploys to Zeebe within ~30 s.
  - `70-tools/scripts/yabai/expand-coverage.mjs` driver posts
    per-target to the dispatcher.

- **Compat cleanup**
  - `BPMN_DISPATCHED_NSIDS` alias retired — all call sites in
    `dispatch.ts` moved to `resolveExactMatchEntry`.
  - `migrate:list` filter bug (stray `.test.ts` in pending list)
    fixed.

## PR #1117 — `fix(trust): complete pg.Pool → createKyselyDb sweep (ADR-0007)` (merged 07:40:03Z → `0bfcde4ab2c`)

5 Workers (`appview/{profile,feed,search}`, `chat`, `signal`) migrated
off hand-rolled `Kysely+PostgresDialect+pg.Pool` to
`createKyselyDb(env.HYPERDRIVE)` from `@etzhayyim/kotodama-host-sdk`
(HyperdriveDialect + single `pg.Client`). Fixes the ADR-0007 CI lint
gate and removes the CF 1101 risk from idle-Pool-client errors.
Refresh of `90-docs/rules/waituntil-requires-catch-baseline.txt`
(13 line-number drifts, no new offenders).

# Production state at end-of-session

| Surface | State |
|---|---|
| `bsky.etzhayyim.com` | Live — `etzhayyim-appview` version `d085c7bf` with pg.Pool refactor + MV LIMIT fix |
| `atproto.etzhayyim.com` | Routing unchanged; BPMN yabai batch-3 NSIDs now land at dispatcher |
| `dispatcher.etzhayyim.com` | 12 yabai BPMN actors live in `vertex_bpmn_lexicon_binding` |
| `sh1n5h1x.etzhayyim.com` | `postsCount = 1476` (was 0), did-web root row in `mv_actor_social_stats` |
| LaunchAgent | `com.etzhayyim.legacy-trust-tally` bootstrapped in `gui/501`, fires 09:17 daily |
| Tally log | `90-docs/260424-legacy-trust-tally.log` seeded with first samples (0/0 hits) |
| Kotoba/Datomic | 1236 tables / 17152 columns, drift clean |

# Known pre-existing CI failures (not caused by this session)

Both PRs merged through these; they predate the session:

- ADR-0013 DNS sync plan (offline)
- ADR-0026 cohort fleet count + schema
- plc-directory Worker vitest
- routing-gateway map + bindings drift

They fail on `main` too. Individual fixes are each ≤ 1 h of focused
work; best tackled outside a feature-PR window.

# One-button cutover template — the pattern that emerged

Documented in ADR-2604241038 β2 addendum. A future ephemeral cutover
(`X`) lands as 5 artifacts:

1. **Runbook** `90-docs/YYMMDD-X-cutover-runbook.md`
2. **Observation probe** `70-tools/scripts/X-tally-probe.sh`
3. **Scheduler** `50-infra/launchd/com.etzhayyim.X-tally.plist`
4. **Preflight validator** `.../scripts/X-preflight.sh`
5. **Pre-written cleanup** `70-tools/scripts/cleanup-X.sh`
6. **End-to-end smoke** `70-tools/scripts/X-smoke.sh`

γ2 hits all 6 slots. Next cutover copies the shapes instead of
reinventing them.

# Design constraints surfaced this session

1. **Kotoba/Datomic parameterized LIMIT** — Kysely's `.limit(N)` generates
   `LIMIT $n` which RW's sql_parser rejects for MV SELECTs. Any new
   Worker doing MV reads must use `sql` template with inline literal.
   Pre-deploy grep target documented in ADR β2 addendum.

2. **Claude scheduled tasks** cap at 7 days, session-bound regardless
   of `durable: true`. Multi-week observation windows must use macOS
   launchd / systemd timers with the plist committed to `50-infra/
   launchd/`.

3. **pg.Pool** in CF Workers leaks idle-client `'error'` EventEmitter
   rejections — surface as CF 1101 platform errors. `createKyselyDb(
   env.HYPERDRIVE)` (HyperdriveDialect + single pg.Client) is the
   sanctioned path; lint rule `no-pg-pool-in-worker` enforces.

4. **`pnpm db:migrate latest` is not the happy path on this repo.**
   Stale kysely_migration rows (from deleted files), RW-incompat SQL
   (`ON CONFLICT`, `CREATE UNIQUE INDEX`, `DROP CASCADE`), and vitest
   snapshot files next to migrations each block the migrator.
   `scripts/apply-pending.sh` is the new default; ADR-2604241342
   explains why.

5. **2-stage deploy budget** for any new Worker against RW — first
   deploy exposes the code-vs-RW-dialect mismatch; budget a same-day
   follow-up deploy. β2 addendum.

# References

- PR #1115: https://github.com/etzhayyim/etzhayyim-root/pull/1115
- PR #1117: https://github.com/etzhayyim/etzhayyim-root/pull/1117
- Merge commits: `fd749574c56`, `0bfcde4ab2c`
- ADRs: `90-docs/adr/{2604241038, 2604241121, 2604241342}-*.md`
- Ephemeral-runbook convention:
  `90-docs/260424-ephemeral-runbook-convention.md`
- Session tally log (live):
  `90-docs/260424-legacy-trust-tally.log` (gitignored)
