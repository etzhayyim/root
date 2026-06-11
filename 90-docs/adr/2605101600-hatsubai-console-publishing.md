---
id: adr-2605101600-hatsubai-console-publishing
title: hatsubai — Console Publishing Pipeline (Switch 2 / PS5 / Xbox / Steam)
status: proposed
doc_type: adr
topic: hatsubai-console-publishing
authoritative: true
last_verified: 2026-05-10
authoritative_for:
  - hatsubai-actor-charter
  - console-publishing-graph-shape
  - console-publishing-platform-axis
  - console-publishing-float-ban-scaling
  - hatsubai-vendor-portal-scope-boundary
related:
  - adr-2604250900-gameka-bpmn-langgraph-game-studio
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0056-bpmn-as-actor
  - adr-2605081200-spiffworkflow-bpmn-engine-replacement
  - adr-2604231811-atproto-extension-service-layers
supersedes: []
superseded_by: []
---

# Context

Game console publishing is a multi-month, partner-gated pipeline. Each
platform holder (Nintendo / Sony Interactive / Microsoft / Valve) runs its
own developer-vetting, devkit-allocation, SDK + TRC (Technical Requirements
Checklist) compliance, multi-round cert (Lotcheck / SUBMIT / Mainline Cert
/ Steamworks Self-Cert), age-rating-board interlock (CERO / ESRB / PEGI /
IARC / GRAC / DJCTQ / SGRB / RARS), and store-listing pipeline. The state
needs a single source of truth so cross-platform questions ("where is
Title X stuck across all four consoles?", "what TRC must-fails are open
for build B?", "which regions are missing required age-rating boards for
listing L?") become one SQL statement, not four manual checks across
vendor portals.

The existing `gameka` (`gameka.etzhayyim.com`) actor already covers in-house
browser game ideation → generation → playtest → publish for the kami-engine
substrate. It owns the cross-platform title identity row
(`vertex_games_title`). It does **not** model partner accounts, devkit
inventory, SDK / TRC / cert submissions, age-rating board interlock, or
console-storefront listings, and it is intentionally scoped to browser
games only.

Three design pressures shape the new actor:

1. **One axis, four platforms.** Per-platform variation should be a
   `platform_code` column (`nsw2` / `ps5` / `xbsx` / `steam`), not separate
   tables. Cross-platform reporting is the primary query shape.
2. **AT Protocol Lexicon forbids floats.** Money, revenue splits, and
   minimum-age values must be stored as scaled BIGINT or PDS validation
   fails silently with `float value at <field>` and the record write
   hangs. This is a recurring rake the codebase steps on — it is part of
   the LLM Coding Guardrails table.
3. **No vendor-portal scraping.** NDA + AUP terms with Nintendo / Sony /
   Microsoft / Valve forbid automated scraping of their developer
   portals. Adapter integration must be opt-in, sit in L8 k8s pods, and
   be explicit about which API surface (export CSV / SUBMIT API / Partner
   Center API / Steamworks Web API) it consumes.

# Decision

Stand up a new actor `hatsubai.etzhayyim.com` (発売 = "release / put on sale")
under the BPMN-as-actor pattern (ADR-0056), mirroring `gameka`'s topology.
**No CF Worker.** The actor is one set of XRPC + Lexicon contracts plus a
graph schema, executed by `bpmn.etzhayyim.com` (SpiffWorkflow + pyzeebe shim per
ADR-2605081200).

## Topology

| Aspect | Value |
|---|---|
| Layer (ADR-2604231811) | Actor Worker (Layer 10 etzhayyim ext.) |
| Worker host | `bpmn.etzhayyim.com` (no dedicated CF Worker) |
| Primary DID | `did:web:hatsubai.etzhayyim.com` |
| Sub-DID per platform | `did:web:hatsubai.etzhayyim.com:platform:{nsw2,ps5,xbsx,steam}` |
| Sub-DID per shipped title (P3) | `did:web:hatsubai.etzhayyim.com:title:{platform}-{slug}` |
| NSID prefix | `com.etzhayyim.apps.hatsubai.*` |
| Persistence (ADR-0036) | domain → Worker-direct Hyperdrive (Kysely); social → `sdk.pds.dispatch` |

## Graph shape (1 forward-only migration)

`30-graph/graph-schema/sql_migrations/20260510160000_vertex_hatsubai_console_publishing.{up,down}.sql`
+ alembic `r_20260510160000`.

**11 vertex tables:**

| Table | Role | Key promoted columns |
|---|---|---|
| `vertex_hatsubai_platform` | Switch 2 / PS5 / Xbox / Steam master | `platform_code`, `holder_legal_entity_did`, `cert_program_name`, `submission_portal_url` |
| `vertex_hatsubai_partner_account` | DevNet / Nintendo Dev Portal / Partner Center / Steamworks partner | `platform_code`, `legal_entity_did`, `vetting_status`, `nda_signed_at`, `partner_id` |
| `vertex_hatsubai_devkit` | DevKit / TestKit individual unit | `platform_code`, `serial`, `kit_kind`, `assigned_to_did`, `firmware_version`, `status` |
| `vertex_hatsubai_sdk_version` | platform SDK version + cert window | `platform_code`, `sdk_version`, `cert_window_open_at`, `cert_window_close_at` |
| `vertex_hatsubai_title` | per-platform title projection | `games_title_did` (FK → `vertex_games_title`), `platform_code`, `title_id` (NSUID / CUSA / 9PXX / Steam appId), `master_status`, `target_release_date` |
| `vertex_hatsubai_title_build` | submitted master ROM / package build | `title_did`, `build_cid`, `sdk_version`, `version_label`, `size_bytes`, `signed_at`, `manifest_cid` |
| `vertex_hatsubai_trc_check` | TRC / Lotcheck rule result | `build_did`, `rule_id`, `severity` (`must` / `should` / `info`), `result` (`pass` / `fail` / `waived` / `not_applicable`) |
| `vertex_hatsubai_cert_submission` | cert submission round | `build_did`, `round_no`, `submitted_at`, `result` (`pending` / `pass` / `fail` / `withdrawn`), `must_fail_count` |
| `vertex_hatsubai_age_rating` | rating board grant per region | `title_did`, `board` (`cero` / `esrb` / `pegi` / `iarc` / `grac` / ...), `region_iso3166`, `rating_label`, `rating_age_min` |
| `vertex_hatsubai_store_listing` | per-region storefront page | `title_did`, `region_iso3166`, `locale`, `price_minor`, `currency_iso4217`, `release_date`, `publish_status` |
| `vertex_hatsubai_store_asset` | screenshot / trailer / key art / icon | `listing_did`, `asset_kind`, `cid`, `width_px`, `height_px`, `duration_ms` |

**7 edge tables** (relation fields only, no payload duplication):

| Edge | src → dst | Relation columns |
|---|---|---|
| `edge_hatsubai_partner_devkit_holds` | partner → devkit | `assigned_at`, `returned_at` |
| `edge_hatsubai_title_targets_platform` | `vertex_games_title` → platform | `port_status`, `lead_studio_did` |
| `edge_hatsubai_build_of_title` | title_build → title | `is_master_candidate` |
| `edge_hatsubai_submission_for_build` | cert_submission → title_build | `round_no` |
| `edge_hatsubai_publisher_publishes` | legal_entity → title | `revshare_bps`, `territory_iso3166`, `term_starts_at`, `term_ends_at` |
| `edge_hatsubai_localized_into` | title → store_listing | `lead_translator_did`, `locale` |
| `edge_hatsubai_rating_required_for_listing` | store_listing → age_rating | `is_blocking` |

TRC ↔ build, asset ↔ listing, sdk ↔ build are intentionally **not**
edges — they are 1:N FK columns on the child vertex (existing GraphAr
promoted-columns convention). Adding edges for these would duplicate state.

**5 streaming MVs** (all bounded cardinality; clear of the
high-cardinality `MAX(varchar)` MV-safety rake):

- `mv_hatsubai_title_cert_status_latest` — `(title, platform) → latest round + result`
- `mv_hatsubai_title_trc_open_failures` — `(title, severity) → open fail count`
- `mv_hatsubai_title_age_rating_coverage` — `(title, region) → granted board count`
- `mv_hatsubai_partner_devkit_utilization` — `(partner, platform) → active / idle / returned counts`
- `mv_hatsubai_release_calendar` — `(release_date, platform, region) → upcoming title count`

The pipeline-blocker rollup ("what is title X waiting on?") is
intentionally a plain `VIEW`, not an MV — it has high branching and would
violate the §MV Memory Safety Guardrails.

## Lexicon surface

`00-contracts/lexicons/com/etzhayyim/apps/hatsubai/` — 13 NSIDs:

- 11 record types matching the 11 vertex tables
- 2 procedures:
  - `submitToCert` — open a new cert submission round (auto-increments `round_no`, refuses when prior round result is `pending`)
  - `publishToStore` — promote `storeListing` from `scheduled` to `live`, gated on (a) latest cert pass and (b) every required age-rating board granted for the listing region. Emits `app.bsky.feed.post` on success.

## BPMN pipeline (target)

`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/hatsubai/`:

| BPMN | Trigger | Status |
|---|---|---|
| `setupPartnerAccount.bpmn` | manual / XRPC | 🟡 contract |
| `allocateDevkit.bpmn` | manual / partner request | 🟡 contract |
| `submitToCert.bpmn` | XRPC `submitToCert` | ✅ skeleton |
| `advanceCertSubmission.bpmn` | timer R/PT12H + reviewer webhook | 🟡 contract |
| `publishToStore.bpmn` | XRPC `publishToStore` | 🟡 contract |
| `tickReleaseCalendar.bpmn` | timer R/PT24H | 🟡 contract |

**Cert round retry loop closure:**

```
submitToCert
  └─ certSubmission(round=N, result=pending)
       └─ advanceCertSubmission (R/PT12H polling)
            ├─ pass        → derive publishToStore precondition
            ├─ fail        → emit TRC fix-list (severity=must rows),
            │                wait for new build
            ├─ withdrawn   → END
            └─ pending     → re-arm timer
```

`submitToCert` refuses a new round when the prior round is still
`pending` (one open submission per build). Operators flip to `withdrawn`
manually to unblock.

## Float ban — BIGINT scaling

| Logical | Column | Encoding |
|---|---|---|
| Price | `price_minor BIGINT` | minor units (cents / sen). `1500` = ¥15.00 = $15.00 |
| Revenue split | `revshare_bps BIGINT` | basis points 0-10000. `7000` = 70.0% |
| Min age | `rating_age_min BIGINT` | integer years. `18` |
| Asset width / height / duration | `width_px` / `height_px` / `duration_ms BIGINT` | always integer |

# Consequences

## Positive

- One graph answers cross-platform questions in one statement
  (`SELECT * FROM mv_hatsubai_title_cert_status_latest WHERE title_did = ?`).
- Per-platform vocabulary differences (Lotcheck rule codes vs Sony TRC
  R-codes vs Xbox TCR codes vs Steam VAC checks) are namespaced via the
  `platform` row's `cert_program_name` and the `trcCheck.rule_id` string.
  No schema migration is needed when a vendor revises its rule numbering.
- AT Lexicon float ban is enforced by construction — there is no
  `number` field anywhere in the lexicon set; PDS validator can never
  silently hang on this surface.
- The graph is useful even with zero adapter automation: operators write
  rows manually via XRPC or `psql` until vendor-portal adapters land.
  This decouples "have a single source of truth" from "have automated
  ingestion".

## Negative / risk

- The `vertex_hatsubai_title` ↔ `vertex_games_title` peerage means a
  title can drift between layers (a `vertex_games_title` row exists
  with no per-platform projection, or the projection's
  `master_status` lags the cross-platform parent). A reconciliation
  view is deferred to Phase 2.
- BPMN-as-actor implies `bpmn.etzhayyim.com` is in the critical path for cert
  submissions. SpiffWorkflow scaling and the pyzeebe shim are addressed
  in ADR-2605081200 but increase blast radius compared to a CF Worker.
- TRC fail evidence (screenshots, repro logs) lives behind `evidence_uri`
  CIDs. Vault-encrypting this content is a deliberate choice — vendor
  reviewer notes can carry NDA-protected information that must not
  federate. Operators must remember to upload to vault, not raw B2.

## Out of scope (explicit)

- **Vendor-portal scraping** (Nintendo Developer Portal / DevNet /
  Partner Center / Steamworks). NDA / AUP forbid it. Adapters that do
  consume these surfaces must use the documented API (NDPP export CSV,
  DevNet SUBMIT API, Partner Center / Game Stack APIs, Steamworks Web
  API) and live as L8 k8s pods.
- **Per-platform separate vertex tables** (`vertex_nsw2_title` etc.).
  Forbidden by design — `platform_code` on every row is the SSoT axis
  for cross-platform queries.
- **PII** in AT Records (reviewer names, certificate body text). Kept
  as `*_uri` references to vault-side blobs only.
- **Direct Steam-page automation** (Steamworks editor). Steamworks
  permits store-page automation via API but submission requires a human
  click-through. We model the state, not the click.

# Alternatives Considered

## A. Per-platform separate actors (`switch2.etzhayyim.com`, `ps5.etzhayyim.com`, ...)

Rejected. Cross-platform reporting becomes UNION ALL across four
schemas; release-calendar / blocker-rollup queries fan-out to four DIDs;
TRC vocabulary pivots into four type systems. The whole point of the
unified actor is that "where is Title X stuck across all four
consoles?" is one query.

## B. Extend `gameka` to cover console publishing

Rejected. `gameka` is intentionally scoped to in-house browser games on
the kami-engine substrate and has its own loop (ideate → generate →
playtest → publish). Console publishing is a different lifecycle (no
ideation, partner gating dominates, multi-month cert), and conflating
the two surfaces would mean every change to either pipeline requires
re-reviewing the other. The two share `vertex_games_title` as the
cross-platform identity layer; that is enough.

## C. CF Worker actor instead of BPMN-as-actor

Rejected. Cert submissions are inherently long-running with timer-based
reviewer polling (`R/PT12H` over weeks). CF Worker's 30s / 128 MB cap
forces every cert flow to delegate to L7 anyway, at which point the CF
Worker is just a thin XRPC entrypoint adding latency and a deploy unit.
BPMN-as-actor is the right shape — same as `gameka`.

## D. Store ratings as a single comma-joined string instead of separate `vertex_hatsubai_age_rating` rows

Rejected. Each board × region grant has independent metadata
(`granted_at`, `expires_at`, `descriptor_codes`, `certificate_uri`,
`rating_age_min`). A single string field would need parse-and-rebuild on
every update. The `mv_hatsubai_title_age_rating_coverage` MV would
collapse — no way to ask "which regions are missing required boards?".

## E. Float `price` and `revshare` columns

Rejected. AT Protocol Lexicon forbids `number` (float). PDS validator
silently hangs with `float value at <field>` and the bug surfaces only
in production write paths. The codebase has been bitten enough that
this is a CRITICAL guardrail. Scaled BIGINT (`price_minor`,
`revshare_bps`, `rating_age_min`) is the cheap, robust answer.

# References

- `30-graph/graph-schema/sql_migrations/20260510160000_vertex_hatsubai_console_publishing.up.sql`
- `30-graph/graph-schema/sql_migrations/20260510160000_vertex_hatsubai_console_publishing.down.sql`
- `30-graph/graph-schema/alembic/current_versions/r_20260510160000_vertex_hatsubai_console_publishing.py`
- `00-contracts/lexicons/com/etzhayyim/apps/hatsubai/` (13 lexicons)
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/hatsubai/submitToCert.bpmn` (P1 skeleton)
- `60-apps/etzhayyim-project-hatsubai/CLAUDE.md`
- `90-docs/adr/2604250900-gameka-bpmn-langgraph-game-studio.md` — peer
  BPMN-as-actor for browser games, owns `vertex_games_title`
- `90-docs/adr/0036-worker-direct-hyperdrive-persistence.md` — domain
  write topology
- `90-docs/adr/0056-bpmn-as-actor.md` — BPMN-as-actor pattern
- `90-docs/adr/2605081200-spiffworkflow-bpmn-engine-replacement.md` —
  SpiffWorkflow + pyzeebe shim runtime
- `90-docs/adr/2604231811-atproto-extension-service-layers.md` — Layer
  taxonomy
