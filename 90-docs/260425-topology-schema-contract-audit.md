# 260425 Topology / Schema / Contract Audit

Status: active audit note

## Summary

- Kotoba/Datomic live connection: `45.32.79.245:4566/dev`.
- Keychain item `etzhayyim.vultr / RW_LB_IP` was stale and has been updated to `45.32.79.245`.
- Kysely schema was regenerated from live Kotoba/Datomic and `pnpm --dir 30-graph/graph-schema run db:drift` now reports zero drift.
- Lexicon generated artifacts were regenerated from `00-contracts/lexicons`.
- BPMN coverage gate passes for all 16 covered processes.
- Kotoba/Datomic topology docs now point to ADR-0094: 3-node floor, 2 compute pod floor, no hot-path `FLUSH`.

## Live Kotoba/Datomic Counts

From `information_schema.tables` on `dev`:

| Relation type | Count |
|---|---:|
| BASE TABLE | 1520 |
| INDEX | 622 |
| MATERIALIZED VIEW | 241 |
| VIEW | 51 |
| Total | 2434 |

Name-prefix counts reflected in generated Kysely `Database`:

| Prefix | Count |
|---|---:|
| `vertex_*` | 1191 |
| `edge_*` | 320 |
| `mv_*` | 242 |

`mv_maps_coverage_gap_ranked` uses an `mv_` prefix but is a `VIEW`, so the
materialized-view count is 241 while the `mv_*` prefix count is 242.

## Contract Gates

| Gate | Result |
|---|---|
| Kysely live drift | pass, 0 drift |
| deps metadata lint | pass |
| dependency boundary lint | pass |
| lexicon prebuild contract check | pass |
| BPMN coverage | pass, 16/16 |

## Remaining Gap

ADR-0040 vertex DID tier registry is not yet reconciled with the current live
schema. Current audit numbers:

| Metric | Count |
|---|---:|
| Live `vertex_*` relations | 1191 |
| Registry entries | 1226 |
| Live vertices missing from registry | 0 |
| Registry entries missing from live schema | 35 |

The 35 registry entries missing from live schema are relations declared by
migration but not present in the current live Kotoba/Datomic schema. They are
tracked as `declared_pending`, not as unexpected stale rows.

This is not a Kysely drift issue. It is a policy registry audit gap. Until the
Phase 3 audit is completed, unclassified vertex relations must be treated as
Tier C by default and must not be assumed to receive DID issuance.

Progress in this audit:

- Added `vertex_auth_account` to Tier A.
- Added actor/account/profile-derived extensions to Tier B.
- Added open-data registry/reference candidates from the identity keyword pass
  to Tier C.
- Reconciled all live `vertex_*` relations into ADR-0040 Tier A/B/C registry.
- Added migration-declared-but-not-live vertex relations as `declared_pending`
  registry entries.
- Added inline `// tier: A|B|C` comments to legacy vertex-creating migrations.

ADR-0040 gate status: `pnpm --dir 30-graph/graph-schema run tier:lint` reports
0 issues. Registry drift and legacy migration annotation debt are closed for the
current repository state.
