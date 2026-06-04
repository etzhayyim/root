# ai-gftd-project-hatsubai — Console Publishing Pipeline (BPMN-as-actor)

`hatsubai.gftd.ai` (発売 = "release / put on sale") — game-console
publishing actor covering **Nintendo Switch 2 / PlayStation 5 / Xbox
Series X|S / Steam (PC)** under one set of XRPC + Lexicon contracts.
**No CF Worker** — BPMN-as-actor (ADR-0056) running on `bpmn.gftd.ai`,
mirroring `ai-gftd-project-gameka`.

## Topology

| 項目 | 値 |
|---|---|
| Layer (ADR-2604231811) | Actor Worker (Layer 10 GFTD ext.) |
| Worker host | `bpmn.gftd.ai` (LangGraph/Pregel/LangChain + LangServer shim) — no dedicated CF Worker |
| Primary DID | `did:web:hatsubai.gftd.ai` |
| Sub-DID per platform release | `did:web:hatsubai.gftd.ai:platform:{nsw2,ps5,xbsx,steam}` |
| Sub-DID per shipped title (P3) | `did:web:hatsubai.gftd.ai:title:{platform}-{slug}` |
| NSID prefix | `ai.gftd.apps.hatsubai.*` |
| Persistence (ADR-0036) | domain → Worker-direct Hyperdrive (Kysely), social → `sdk.pds.dispatch` |
| Ratings boards | CERO / ESRB / PEGI / IARC / GRAC / DJCTQ / SGRB / RARS |
| Scope boundary | upstream of any **vendor portal automation** — we model state, not scrape Nintendo Developer Portal / DevNet / Partner Center / Steamworks |

## Why one actor for 4 platforms

Per-platform variation is captured by a single `platform_code` column
(`nsw2` / `ps5` / `xbsx` / `steam`). Cross-platform queries — release
calendar, blocker rollup, devkit utilization, age-rating coverage —
stay one-statement. Platform-specific cert vocabulary (Lotcheck /
SUBMIT / Mainline Cert / Steamworks Self-Cert) is namespaced via
`platform`'s `cert_program_name` and TRC `rule_id` strings.

## Pipeline (target, 5 BPMN)

| Phase | BPMN | Triggers | Status |
|---|---|---|---|
| Setup | `setupPartnerAccount.bpmn` | manual | 🟡 contract |
| Devkit | `allocateDevkit.bpmn` | manual / partner request | 🟡 contract |
| Submit | `submitToCert.bpmn` (this folder, P1) | XRPC `submitToCert` | ✅ skeleton |
| Track | `advanceCertSubmission.bpmn` | timer R/PT12H + reviewer webhook | 🟡 contract |
| Publish | `publishToStore.bpmn` | XRPC `publishToStore` (gated on cert pass + ratings) | 🟡 contract |
| Calendar | `tickReleaseCalendar.bpmn` | timer R/PT24H | 🟡 contract |

**Loop closure** (cert round retry):

```
submitToCert
  └─ certSubmission(round=N, result=pending)
       └─ advanceCertSubmission (R/PT12H polling reviewer status)
            ├─ pass        → derive publishToStore (precondition met)
            ├─ fail        → critic emits TRC fixlist (vertex_hatsubai_trc_check
            │                rows with severity=must), waits for new build
            ├─ withdrawn   → END
            └─ pending     → re-arm timer
```

**Bounded**: cert rounds have no hard cap, but `submitToCert` refuses
when `latest round result = pending` (one open submission per build).
Operators manually `withdrawn` to unblock.

## Lexicons (`00-contracts/lexicons/ai/gftd/apps/hatsubai/`)

| NSID | type | Status |
|---|---|---|
| `ai.gftd.apps.hatsubai.platform`         | record    | ✅ |
| `ai.gftd.apps.hatsubai.partnerAccount`   | record    | ✅ |
| `ai.gftd.apps.hatsubai.devkit`           | record    | ✅ |
| `ai.gftd.apps.hatsubai.sdkVersion`       | record    | ✅ |
| `ai.gftd.apps.hatsubai.title`            | record    | ✅ |
| `ai.gftd.apps.hatsubai.titleBuild`       | record    | ✅ |
| `ai.gftd.apps.hatsubai.trcCheck`         | record    | ✅ |
| `ai.gftd.apps.hatsubai.certSubmission`   | record    | ✅ |
| `ai.gftd.apps.hatsubai.ageRating`        | record    | ✅ |
| `ai.gftd.apps.hatsubai.storeListing`     | record    | ✅ |
| `ai.gftd.apps.hatsubai.storeAsset`       | record    | ✅ |
| `ai.gftd.apps.hatsubai.submitToCert`     | procedure | ✅ |
| `ai.gftd.apps.hatsubai.publishToStore`   | procedure | ✅ |

## RisingWave schema

`30-graph/graph-schema/sql_migrations/20260510160000_vertex_hatsubai_console_publishing.up.sql`
(alembic: `r_20260510160000_vertex_hatsubai_console_publishing`)

- 11 vertex tables (`vertex_hatsubai_*`)
- 7 edge tables (`edge_hatsubai_*`)
- 5 streaming MVs:
  - `mv_hatsubai_title_cert_status_latest` — title × platform → latest round + result
  - `mv_hatsubai_title_trc_open_failures` — title × severity → open `must` / `should` fail count
  - `mv_hatsubai_title_age_rating_coverage` — title × region → granted boards
  - `mv_hatsubai_partner_devkit_utilization` — partner × platform → active/idle/returned
  - `mv_hatsubai_release_calendar` — date × platform × region → upcoming title count
- 8 indexes

`pnpm db:gen` after apply regenerates `src/database.ts`.

## Floats are forbidden (AT Lexicon constraint)

Money / proportions live as scaled BIGINT:

| Logical | Column | Encoding |
|---|---|---|
| Price | `price_minor BIGINT` | cents / sen — `1500` = ¥15.00 = $15.00 |
| Revenue split | `revshare_bps BIGINT` | basis points 0–10000 — `7000` = 70.0% |
| Age min | `rating_age_min BIGINT` | integer years — `18` |

## Data sourcing reality

`hatsubai` does **not** scrape vendor portals. Required adapters
(L8 k8s pod or external integration partner):

| Platform | Source | Frequency |
|---|---|---|
| Nintendo Switch 2 | Nintendo Developer Portal export (manual or partner-supplied CSV) | per submission |
| PS5 | DevNet SUBMIT API (SDK-keyed, partner contract) | per submission |
| Xbox | Partner Center / Game Stack APIs (Azure AD app reg required) | per submission |
| Steam | Steamworks Web API + Partner Site CSV | daily |
| All ratings | Board-issued PDF certificates → CID upload → `ageRating.certificateUri` | per grant |

Without an adapter the pipeline still works — operators write rows
manually via XRPC or `psql`. The graph stays useful as the SSoT for
"where is title X stuck across all 4 platforms?".

## Title peerage with `vertex_games_title`

- **`vertex_games_title`** = cross-platform identity row (1 game = 1 row, lives in `gameka` schema).
- **`vertex_hatsubai_title`** = per-platform projection (1 game × N target consoles = N rows here).

`vertex_hatsubai_title.games_title_did` is the FK upward.
`edge_hatsubai_title_targets_platform` lets a game declare intent to
ship on a platform without a full per-platform title row yet (early
discovery / port pitch stage).

## Smoke test

```bash
# 1. Apply migration
cd 30-graph/graph-schema
source scripts/load-database-url.sh
pnpm db:migrate
pnpm db:gen
pnpm db:drift

# 2. Bundle lexicons + register with PDS (when wiring the runtime)
node 50-infra/cloudflare/workers/atproto/scripts/bundle-lexicons.mjs
node 70-tools/scripts/contract/gen-pds-lexicon-registry.mjs
cd 50-infra/cloudflare/workers/atproto && npx wrangler deploy

# 3. (Future) Sync BPMN registry rows
python3 70-tools/scripts/contract/sync-bpmn-actors.py --apply --only hatsubai

# 4. Seed one platform row (manual until adapters land)
psql "$ROOT_URL" <<'SQL'
INSERT INTO vertex_hatsubai_platform
  (vertex_id, _seq, sensitivity_ord, owner_did,
   platform_code, display_name, holder_legal_entity_did,
   cert_program_name, submission_portal_url, developer_portal_url,
   region_locked, actor_did, org_did, at_did, created_at)
VALUES
  ('at://did:web:hatsubai.gftd.ai/ai.gftd.apps.hatsubai.platform/nsw2',
   0, 0, 'did:web:hatsubai.gftd.ai',
   'nsw2', 'Nintendo Switch 2', 'did:web:legal.gftd.ai:lei:353800XXXXXXXXXXXXXX',
   'Lotcheck', 'https://developer.nintendo.com/', 'https://developer.nintendo.com/',
   true, 'did:erc725:gftd:260425:hatsubai', 'did:erc725:gftd:260425:etzhayim',
   NULL, '2026-05-10T16:00:00Z');
SQL
```

## Prohibitions

- Do **not** create a CF Worker for `hatsubai`. ADR-0056 BPMN-as-actor is the contract (`bpmn.gftd.ai` LangGraph/Pregel/LangChain).
- Do **not** model platform-specific cert process as separate vertex tables. `platform_code` on every relevant vertex is the SSoT axis.
- Do **not** add `price`/`revshare`/`rating_age` as floats — AT Lexicon forbids `number`. Always scale to integers (`price_minor`, `revshare_bps`, `rating_age_min`).
- Do **not** write PII (reviewer names, certificate body text) into AT Records — keep them at `*_uri` references to vault-side blobs.
- Do **not** use `_alive` soft-delete or `ON CONFLICT` in RisingWave inserts (ADR-0036 + RW writer convention).
