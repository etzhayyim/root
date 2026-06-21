# etzhayyim → etzhayyim 移行漏れマトリクス (gov / admin / legal scope)

**Date**: 2026-05-24
**Audit by**: claude session ("この世の全ての政府機関、行政手続きの pregel, mcp の実装カバレッジ?")
**Trigger**: user observation that initial "coverage = ~0%" estimate looked like a migration miss, not a true gap.

## TL;DR

| Layer | Initial estimate | Real coverage (post-audit) |
|---|---|---|
| Pregel cell (religious-corp `40-engine/kotoba/crates/kotoba-kotodama/cells/`) | 0 gov | **0 gov** (unchanged — gov-specific cells were never religious-corp scope) |
| MCP server (`40-engine/kotoba/crates/kotoba-kotodama/mcp/`) | 0 gov | **0 gov** (unchanged — same reason) |
| App appview (`60-apps/`) | 4 gov-adjacent scaffolds | **9 apps** including the 1229-file `etzhayyim-project-cofog` covering UN COFOG × country |
| BPMN namespace (`00-contracts/bpmn/com/etzhayyim/`) | 1127 .bpmn / 140国 | unchanged |
| Ingest script (`70-tools/scripts/gov/`) | 6 (5 IN + 1 AGO) | unchanged |

The "real" gov coverage was always in `etzhayyim-project-cofog` (already 99.9% migrated, 1229/1230) and `etzhayyim-project-gov` (gov.etzhayyim.com public-services hub), not in religious-corp Pregel cells. The substrate boundary (ADR-2605172000) was the reason the etzhayyim→etzhayyim migration left some apps as scaffold-only — the etzhayyim code uses Kysely + HyperDrive Postgres which is prohibited on the etzhayyim side.

## Per-app migration gap matrix

| App | etzhayyim-side files (archive) | etzhayyim-side files (pre-audit) | Files restored (audit) | Substrate-port-pending? |
|---|---|---|---|---|
| `etzhayyim-project-gov` | 13 | 1 | **+12** (gov-mcp-component) | ✅ yes (Kysely + HyperDrive in src/app.ts) |
| `etzhayyim-project-lawfirm-admin` | 12 | 1 | **+11** (lawfirm-admin-mcp-component) | ✅ yes (likely same pattern) |
| `etzhayyim-project-legal-entity` | 20 | 7 | **+13** (wasm/ subtree) | ✅ yes (verify Kysely usage) |
| `etzhayyim-project-cofog` | 1230 | 1229 | (.DS_Store skip only) | NO further action needed |
| `etzhayyim-project-government-body` | 7 | 7 | (already complete) | n/a |
| `etzhayyim-project-lawfirm` | 296 | 306 | (dest already ahead) | n/a |
| `etzhayyim-project-lawyer` | 20 | 20 | (already complete) | n/a |
| `etzhayyim-project-legal-aid` | 0 (no archive) | 1 | (dest-only) | n/a |
| `etzhayyim-project-legal-corpus` | 0 (no archive) | 2 | (dest-only) | n/a |
| `etzhayyim-project-open-jpn-gov` | 0 (no archive) | 25 | (dest-only) | n/a |

Plus `60-apps/etzhayyim-project-gov/scaffold/actor-manifest.jsonld` (23 JP ministry path-based-DID entries: MOJ / METI / Cabinet Office / MoE / MoF / MHLW / MEXT / MLIT / MAFF / MOFA / ...) restored from `_archive/actor-scaffolds-2026-05-21/gov/`.

## Items intentionally NOT migrated

- `_archive/10-protocol/capabilities/wproto-governance-registry/deps.graph.jsonld` — etzhayyim's pre-migration archive (not the migrate-out archive), obsolete.
- `50-infra/cloudflare/workers/gov-fetch-proxy` — still live in etzhayyim source repo, serves `*.etzhayyim.com` traffic. Per the religious-corp routing-around stance, etzhayyim should not depend on etzhayyim-side proxies.
- DEPRECATED.md files from each source app — etzhayyim-side markers, irrelevant on etzhayyim side. Replaced with `SUBSTRATE-PORT-PENDING.md` per app.

## Cofog appview — already-migrated world gov coverage

`60-apps/etzhayyim-project-cofog/appview/` has **203 entries** organized as one actor-bundle per (COFOG class × country variant). Sample country-coded actors visible:

| COFOG class | Country variants present | What it covers |
|---|---|---|
| 01.11 executive-legislative | (universal) | Heads of state / parliaments |
| 02.10 military-defense | (universal) | Armed forces |
| 03.10 police-services | DE BKA cyber / JP NPA cyber / UK Action Fraud / US FBI IC3 + universal | Police, cybercrime intake |
| 03.20 fire-protection | (universal) | Fire service |
| 03.30 law-courts | (universal) | Court system |
| 08.40 religious-community-services | (universal) | Directly relevant to etzhayyim |
| ... | ... | ... |

This is the canonical answer to "world gov coverage" — not Pregel cells, but a 203-actor COFOG×country bundle under `etzhayyim-project-cofog`.

## Substrate-port follow-up (deferred)

Per user direction "blind copy して、後から修正", the 3 newly-restored apps carry `SUBSTRATE-PORT-PENDING.md` markers documenting the Kysely → MST port required. To be processed under a future migration ADR (working name: ADR-2605212100 if not yet authored, otherwise a follow-up ADR-2605240xxx).

## Cross-links

- ADR-2605172000 (kotoba substrate, the boundary)
- ADR-2605172100 (substrate ladder)
- ADR-2605214000 (Murakumo mesh + lexicon port verdict taxonomy)
- ADR-2605212100 (etzhayyim→etzhayyim migration batch — **referenced by source DEPRECATED.md, not yet authored**)
- CLAUDE.md Step 8 (`amanomibashira → etzhayyim` cutover — 118 files, etzhayyim → etzhayyim package-name cutover still pending per ADR-2605214000 §3)
- Source archive root: `/Users/junkawasaki/github/etzhayyim-apps-etzhayyimcojp/_archive/migrated-to-etzhayyim-2026-05-21/60-apps/`
