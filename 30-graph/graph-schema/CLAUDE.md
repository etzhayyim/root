> **DEPRECATION NOTICE (ADR-2605262130):** The Kysely `migrations/` table and streaming-MV DDL are **superseded by the kotoba Datom-attribute model**. There is no projection layer; schema is installed via `:db.unique/identity` attributes using `pymagatama.kotoba_datomic.ensure_schema` / `schema_install_edn`. The 1379 historical migrations are retained for reference only and are NOT ported.

# @etzhayyim/graph-schema — SQLAlchemy / Alembic / SQLMesh

## DATABASE_URL Credential Lookup (CRITICAL — always start here)

`DATABASE_URL` is the RisingWave Postgres-wire URL used by every
`pnpm db:*` command (`migrate`, `gen`, `drift`, `seed`). Two URLs
exist; pick by what the command needs to do:

| Source | User | Privileges | When to use |
|---|---|---|---|
| **1Password** `etzhayyim.rw/ROOT_URL` (item id `yi7hc5wozgfhbaneb3ny46w6ua`, vault `etzhayyim Japan株式会社`) | `root` | full DDL | `pnpm db:migrate` (CREATE / ALTER), seed scripts |
| **macOS Keychain** `etzhayyim.rw / KAISYA_URL` | `kaisya_app` | read-only | `pnpm db:gen` (introspection), `pnpm db:drift` |
| `~/.etzhayyim/rw-credentials.env` ROOT_URL / KAISYA_URL | (stale Linode IP after ADR-0048 cutover) | — | last-resort fallback only |

The repo ships `scripts/load-database-url.sh` which resolves the
chain automatically — preferred entry point for both humans and LLMs:

```bash
# In-shell: sets $DATABASE_URL in the current shell
source 30-graph/graph-schema/scripts/load-database-url.sh
pnpm db:migrate
pnpm db:gen
pnpm db:drift

# One-shot eval form (for `bash -c` / scripts):
eval "$(30-graph/graph-schema/scripts/load-database-url.sh print)"
pnpm db:migrate
```

If both 1Password is signed out *and* the Keychain entry is missing,
the loader writes a clear `FAIL: no source. Run: op signin` message.
The user runs `op signin` once per shell session and the loader
picks `etzhayyim.rw/ROOT_URL` automatically afterwards.

`op` (1Password CLI) cannot resolve `op://etzhayyim Japan株式会社/...`
references because the vault name contains non-ASCII characters; the
loader uses the item UUID instead. Future LLM sessions discovering
this file should use the loader without re-scanning Keychain.

The local `.env` fallback was last refreshed against the Linode host
(<vendor-rw-host-deprecated>) which is dead per ADR-0048 (RisingWave moved to
Vultr <vendor RW host>). Re-pull from 1Password to refresh:

```bash
op item get yi7hc5wozgfhbaneb3ny46w6ua --fields label=credential \
  > /tmp/root_url && \
echo "ROOT_URL=$(cat /tmp/root_url)" > ~/.etzhayyim/rw-credentials.env && \
echo "KAISYA_URL=$(security find-generic-password -s etzhayyim.rw -a KAISYA_URL -w)" \
  >> ~/.etzhayyim/rw-credentials.env && chmod 600 ~/.etzhayyim/rw-credentials.env
```

## Single Source of Truth

**Schema SSoT = live RisingWave DB.** As of ADR-2605080700 (2026-05-08),
`live_risingwave_20260508` is the active baseline. `src/database.ts` is a
**generated** reflection of live `information_schema`, not a hand-managed file.
Hand-maintenance failed at scale (2026-04-17 audit found 279 missing tables,
47 stale types, 29 column diffs across out-of-band migrations). DB types come
from the DB — use `pnpm db:gen` after every schema change.

- `alembic/current_versions/` — active Alembic graph for future graph-schema
  DDL, starting at `live_risingwave_20260508`.
- `alembic/versions/` — historical converted Kysely lineage. Do not replay
  this archive into the live cluster.
- `alembic/` — schema migration runtime. Alembic runs through SQLAlchemy
  against RisingWave's PostgreSQL wire protocol.
- `sql_migrations/` — plain SQL bodies used by Alembic revisions when a
  migration is better represented as SQL than SQLAlchemy DDL helpers.
- `sqlmesh/` — SQLMesh project for rebuildable analytical models. Alembic
  owns base-table DDL; SQLMesh owns derived views/materializations.
- `migrations/` — legacy Kysely migrations. These remain historical input only;
  do not add new graph-schema DDL here.
- `src/database.ts` — **GENERATED**. Kysely `Database` type + all Row
  interfaces. Regenerate with `pnpm db:gen` (connects to `DATABASE_URL`,
  reads `information_schema`, overwrites). Do not edit by hand.
- `src/db.ts` — backward-compat re-export of `database.ts`
- `src/helpers.ts` — Table resolution utilities (vertex/edge table dispatch, string-only)
- `src/index.ts` — public API surface (`Database`, Row interfaces, table resolvers)
- `graph_schema/` — Python SQLAlchemy helpers, TS type generator, drift
  detector, and Kysely-to-Alembic converter.
- `scripts/migrate.ts` — legacy standalone Kysely migration runner. Use only
  through `pnpm db:kysely:*` during migration cleanup.
- `pnpm db:gen` — Python generator. Reads RW `information_schema`
  and writes `src/database.ts`.
- `pnpm db:drift` — Python CI guard. Compares `database.ts` to live RW
  and exits non-zero on drift. Run with `pnpm db:drift` after every
  migration apply; expected to report OK.
- `kysely.config.ts` — historical stub; not used by the canonical path.

## Current Workflow

1. Add base-table or irreversible schema changes with Alembic:
   `pnpm db:migrate:new -- "short description"`, edit the new file under
   `alembic/current_versions/`, then load the URL and run:
   `source scripts/load-database-url.sh && pnpm db:migrate`.
2. Add rebuildable views/materializations under `sqlmesh/models/` and run
   `pnpm sqlmesh:plan` / `pnpm sqlmesh:run`.
3. Regenerate and verify TS types (Keychain fallback URL is sufficient):
   `source scripts/load-database-url.sh && pnpm db:gen && pnpm db:drift`.
4. Treat old Kysely migrations and converted Alembic revisions as lineage
   archives. ADR-2605080700 explicitly forbids replaying the full historical
   chain into the current live RisingWave cluster.

**Archived (2026-04-13, non-Kysely cleanup):**
- Under `_archive/2026-04-13-non-kysely/`:
  - `graphar-db.gen.ts` — duplicate snake_case `GrapharDB` (replaced by canonical `database.ts`)
  - `schema.ts` — Drizzle ORM doc-comment shim (no real exports)
  - `repo-log.ts` — duplicate `VertexRepoCommit*Row` types (kept in `database.ts`)
  - `promoted-columns.ts` — column allowlist relocated to `50-infra/cloudflare/workers/atproto/src/insert-columns.ts`
- `p10.gen.ts` / `p10-tables.ts` — eliminated 2026-04-16. Graph Worker consumer now dispatches via `handleCollection()` typed switch per NSID; column lists come from `information_schema` (convention fallback) or are inlined in the handler. **`src/database.ts` Row interfaces are the sole schema SSoT.**

## Schema Design

- **Tables**: 493 total — 317 `vertex_*` + 168 `edge_*` + 5 `dim_*` + 3 other (kysely_migration×2, ndc_stage_ingest)
- **Naming**: ALL tables follow `vertex_<label>` or `edge_<type>` convention (no exceptions)
  - Commit log: `vertex_repo_commit` (vertex_id = `{repo}:{collection}:{rkey}:{action}` — content-addressed since 2026-04-21 / ADR-0041. `seq` stays BIGINT monotonic-per-isolate, consumer reads `ORDER BY seq ASC` tolerating duplicates/gaps across isolates)
  - Block store: `vertex_repo_block` (vertex_id = `{repo}/{cid}`)
  - Consumer cursor: `vertex_consumer_cursor` (vertex_id = `consumer_id`)
- **Columns**: Promoted columns only (NOT normalized 1NF)
  - Vertex: `vertex_id` (PK), `_seq`, `created_date`, `sensitivity_ord`, `owner_did` + entity fields
  - Edge: `edge_id` (PK), `src_vid`, `dst_vid`, `_seq`, `created_date`, `sensitivity_ord`, `owner_did` + relation fields
- **Types**: varchar/bigint/date/double precision/real (no JSON columns; props as TEXT when needed)
- **Access**: Row-level control via `owner_did`

## Migration History

**2026-05-08 live baseline**: active migration history starts at
`alembic/current_versions/20260508_live_risingwave_baseline.py`
(`live_risingwave_20260508`). The Kysely table below is retained as historical
lineage, not as the production replay plan.

| File | Date | Description |
|---|---|---|
| `migrations/0001_initial_schema.ts` | 2026-04-08 | 187 tables (vertex + edge) |
| `migrations/0002_streaming_mv.ts` | 2026-04-08 | 18 streaming MVs (mv_followers .. mv_cc_domain_coverage) |
| `migrations/0003_iceberg_sinks.ts` | 2026-04-08 | **DECOMMISSIONED 2026-04-13** — SKIP in apply-migrations.py default (`--skip 0003`). Iceberg sinks removed, no external consumers |
| `migrations/0004_repo_log_to_vertex.ts` | 2026-04-12 | repo_commit/repo_block/graph_consumer_cursor → vertex_* naming (+3 tables) |
| `migrations/0005_vertex_gitrepo.ts` | 2026-04-13 | dedicated `vertex_gitrepo` table for git-server worker |
| `migrations/0006_vertex_typed_columns_for_cypher_archive.ts` | 2026-04-13 | ALTER TABLE: typed columns for post-SQL-archive design (policy rules, convo encryption, openclaw/signaldevice meta) |
| `migrations/0007_drop_by_dest_tables.ts` | 2026-04-13 | DROP 9 `_by_dest` CSC reverse tables (replaced by streaming MVs) |
| `migrations/0008_analytics_mvs.ts` | 2026-04-13 | 3 analytics MVs: mv_follow_2hop, mv_weighted_in_degree, mv_post_engagement |
| `migrations/0009_vertex_repo_record_root.ts` | 2026-04-13 | vertex_repo_record root table |
| `migrations/0009_write_outbox.ts` | 2026-04-13 | write outbox for failed PDS writes |
| `migrations/0010_typed_columns_followup.ts` | 2026-04-13 | typed columns followup |
| `migrations/0011_vertex_repo_record_root.ts` | 2026-04-13 | vertex_repo_record root table (retry) |
| `migrations/0012_drop_legacy_post_profile.ts` | 2026-04-13 | drop legacy post/profile tables |
| `migrations/0013_vertex_app_typed_columns.ts` | 2026-04-13 | vertex_app typed columns |
| `migrations/0014_domain_coverage_live_mv.ts` | 2026-04-13 | domain coverage live MV |
| `migrations/0015_actor_social_stats_mv.ts` | 2026-04-13 | actor social stats MV |
| `migrations/0016_actor_repo_stats_mv.ts` | 2026-04-13 | actor repo stats MV |
| `migrations/0017_project_convo_overflow_columns.ts` | 2026-04-13 | project convo overflow columns |
| `migrations/0018_vertex_ip_address.ts` | 2026-04-13 | `vertex_ip_address` — IP/GeoIP intelligence for collector (address, country, city, ASN, lat/lon, proxy/datacenter/tor flags) |
| `migrations/0025_world_coverage_live_mv.ts` | 2026-04-14 | **SSoT migration** of `50-infra/linode/risingwave-iceberg/sql/04-world-coverage-live-mv.sql` (archived). `dim_world_domain` (405) + `dim_app_host_alias` (183) + `mv_world_did_per_host` + `mv_world_record_per_host` + `mv_world_vertex_per_host` + `mv_world_coverage_live`. Fix: `collected = GREATEST(did, record, vertex)` not sum (triple-counting bug). Previously consumed by `etzhayyim coverage world` (CLI removed 2026-05-20). |
| `migrations/0026_cc_page_did_alias.ts` | 2026-04-14 | **CC per-page DID actor aliasing** (v2 VIEW-only). `vertex_did_alias` table + 3 plain VIEWs (`view_cc_page_canonical`, `view_cc_edge_links_to_canonical`, `view_cc_domain_page_count_canonical`). Legacy SHA-16 hex rkey + null owner_did and new URL-path-slug rkey + page-DID owner_did coexist in `vertex_page`; the page VIEW unifies by URL (MAX picks new if present else legacy). v1 attempted MATERIALIZED VIEWs and OOM'd the compute pod during 2.9M-row GROUP BY + 14×`MAX(varchar)` backfill (compute 6.5Gi → 24Gi bump was forced). Guardrail: **no high-cardinality GROUP BY + wide VARCHAR MAX in streaming MVs.** Applied out-of-band via psycopg2 (kysely migrator blocked by pre-existing 0023-0025 timestamp corruption). |
| `migrations/0037_vertex_ip_cluster.ts` | 2026-04-14 | **IP cluster (patent/trademark/copyright)** — 3 vertex + 5 edge tables. `vertex_patent` (jurisdiction/app_number/pub_number/grant_number/title/ipc_codes JSON/cpc_codes JSON/filed_at/published_at/granted_at), `vertex_trademark` (jurisdiction/reg_number/mark/mark_type/nice_classes JSON/vienna_codes/madrid_intl_reg_number), `vertex_work` (kind/title/doi/isbn13/isrc/iswc/registry/license/berne_automatic). Edges: `edge_patent_cites` (backward/forward/NPL × EPO X/Y/A/E/P/D category; named `patent_cites` to avoid conflict with legal `edge_cites`), `edge_family_member` (INPADOC simple/extended/docdb), `edge_classified_as` (patent/trademark → ipc/cpc/nice), `edge_owned_by` (→ legal-entity LEI), `edge_authored_by` (→ natural-person ORCID). Drives T1 manifests at `20-actors/{patent,trademark,copyright}/actor-manifest.jsonld`. Applied 2026-04-14 via direct psql (kysely migrator blocked by pre-existing 0027-0029 corruption); kysely_migration log entry inserted manually |
| `migrations/0039_vertex_profile_fragment_embedding.ts` | 2026-04-14 | profile IVF search support — ALTER `vertex_profile_fragment` ADD `embedding` / `embedding_norm` / `ivf_cluster_id`. Enables actor vector search over `ProfileDescription` / `ProfileDisplayName`. |
| `migrations/0040_vertex_occupation.ts` | 2026-04-14 | recruit taxonomy base — `vertex_occupation` for ISCO/ESCO/O*NET ingest. |
| `migrations/0041_vertex_skill_and_edges.ts` | 2026-04-14 | recruit skill graph — `vertex_skill`, `edge_occupation_skill`, `edge_skill_skill`. |
| `migrations/0042_vertex_job_posting.ts` | 2026-04-14 | public job posting ingest — `vertex_job_posting` + `edge_posting_occupation`. |
| `migrations/0043_vertex_talent_cohort.ts` | 2026-04-14 | talent cohort aggregates — `vertex_talent_cohort` for ILOSTAT / public workforce stats. |
| `migrations/0044_vertex_repo_commit_seq_index.ts` | 2026-04-14 | add `idx_vertex_repo_commit_seq` on `vertex_repo_commit(seq)`. |
| `migrations/0045_vertex_kuruma_depth.ts` | 2026-04-14 | kuruma domain depth — 12 vertex + 9 edge + 5 MV. Supply chain: maker→platform→model→trim→part→supplier→plant→unit(VIN)→dealer. Monthly sales, recalls, reviews, safety ratings. Design: `90-docs/260414-domain-coverage-depth-design.md` §A |
| `migrations/0046_vertex_anime_depth.ts` | 2026-04-14 | media_anime domain depth — 13 vertex + 11 edge + 5 MV. Studio, committee, staff, character, episode, broadcaster, distribution (country × platform), source adaptation, songs, merchandise, ratings. Design: `90-docs/260414-domain-coverage-depth-design.md` §B |
| `migrations/0047_vertex_game_depth.ts` | 2026-04-14 | media_gamers domain depth — 14 vertex + 12 edge + 6 MV. Platform, engine, store, character, map, item, quest, DLC, sales (region×month), esports, genre/mode. Design: `90-docs/260414-domain-coverage-depth-design.md` §C |
| `migrations/0048_vertex_page_extract_cursor.ts` | 2026-04-14 | `vertex_page.extracted_for_{kuruma,media_anime,media_gamers,handotai}` TIMESTAMP cursor columns. Drives commoncrawl.etzhayyim.com CF Worker entity extraction. Current writes project to typed domain tables (`vertex_kuruma_model`, media titles, `vertex_handotai_record`) rather than `vertex_repo_record`. NULL = not yet extracted, TS = processed at. |
| `migrations/0049_drop_vertex_repo_root.ts` | 2026-04-14 | **Head derived from commit log** — CREATE INDEX `idx_vertex_repo_commit_repo_seq` (repo, seq) for O(log n) latest-head lookup; DROP TABLE `vertex_repo_root` + DROP INDEX `idx_vertex_repo_root_rev` + DROP MV `mv_vertex_repo_root`. `getRootDetailed()` now queries `vertex_repo_commit` directly (strong consistency, no streaming MV lag). PDS write hot path: 4 RTT → 2 RTT. Discovered: old `vertex_repo_root` was 10% stale (311/3145 dids mismatched) due to silent DELETE+INSERT failures. |
| `migrations/0050_outbox_governance_page_domain.ts` | 2026-04-14 | write outbox + governance/page-domain support tables. |
| `migrations/0052_vertex_repo_record_cohort_columns.ts` | 2026-04-14 | **ADR-0026 cohort evidence promoted columns (legacy)** — ALTER `vertex_repo_record` ADD 7 columns: `cohort_did`, `evidence_hash`, `signal_kind`, `posterior`, `judge_agreement`, `tier`, `observed_at`. Superseded for new writes by `20260507522000_vertex_cohort_evidence`. |
| `migrations/0053_vertex_cohort_actor.ts` | 2026-04-14 | **ADR-0026 cohort actor lineage table** — `vertex_cohort_actor` (cohort_did PK + handle + kind + segment_hash + k_anonymity + fission_enabled + derived_from + status + signature_uri + genesis_at). +2 indexes (cohort_did, derived_from). |
| `migrations/0054_cohort_identity_posterior_mv.ts` | 2026-04-14 | **ADR-0026 cohort fission gate (legacy source)** — originally 2 narrow MVs on `vertex_repo_record WHERE collection='com.etzhayyim.cohort.evidence'`. Current live source is `vertex_cohort_evidence` after `20260507522000_vertex_cohort_evidence`. |
| `migrations/0056_cohort_lineage_edges.ts` | 2026-04-15 | **ADR-0026 lineage edges** — 3 edge tables (`edge_cohort_derived` parent→fissioned, `edge_cohort_evidence_about` evidence→cohort, `edge_cohort_routes_to` cohort→APQC L1 DID) + 4 indexes + 1 narrow MV `mv_cohort_lineage_depth` (per-cohort direct_children + last_fission_at). Hummock-only, no Iceberg. Pre-flight: GROUP BY src_vid bounded by cohort count, backfill 0, no MAX(varchar). |
| `migrations/0065_hs2022_sitc4.ts` | 2026-04-15 | HS 2022 (H6, 6,939 rows) + SITC Rev.4 (5,484 rows). Views: `view_hs2022_commodity`, `view_sitc_commodity`. |
| `migrations/0067_naics2022_isic5.ts` | 2026-04-15 | NAICS 2022 (2,125 rows) + ISIC Rev.5 (830 rows). Views: `view_naics_industry`, `view_isic5_activity`. |
| `migrations/0068_m49_isic4_isic5_concordance.ts` | 2026-04-15 | UN M49 geo areas (460 rows) + ISIC4↔ISIC5 code-identical bridge (700 edges, system='isic5'). |
| `migrations/0069_cpc_sitc4_concordance.ts` | 2026-04-15 | CPC v2↔SITC Rev.4 concordance (3,776 edges after CPC2→CPC21 remapping, system='sitc4'). |
| `migrations/0070_hs2012_sitc4_repair.ts` | 2026-04-15 | HS 2012 (6,529 rows, collection hs.commodity2012) + topo repair (sitc4/cpc/hs2012 dangling edges). View: `view_hs2012_commodity`. |
| `migrations/0071_nace_r2.ts` | 2026-04-15 | NACE Rev.2 (997 rows, Eurostat SDMX) + 679 NACE↔ISIC4 edges (system='nace_r2'). View: `view_nace_activity`. |
| `migrations/0072_topo_repair_cpc3_naics_concordance.ts` | 2026-04-15 | Full topo repair (0 orphans, 0 dangling) + CPC v3 (4,594 rows) + 4,390 CPC3↔CPC21 edges + 24 NAICS↔ISIC4 sector edges. View: `view_cpc3_product`. |
| `migrations/0073_derived_concordance_bridges.ts` | 2026-04-15 | 8 derived concordance bridge systems (total 30,700 edges): hs22_hs17 (6,561), hs12_hs17 (6,528), hs2017_cpc3 (5,740), hs2012_cpc3 (5,500), sitc4_cpc3 (3,717), cpc_isic5 (2,504), isic5_nace (625), naics_isic5 (24). Topo: 0 orphans, 0 dangling across 16 systems. |
| `migrations/0074_sitc2_sitc3_isco_bec.ts` | 2026-04-15 | SITC Rev.3 (5,690) + SITC Rev.2 (3,723) + ISCO-08 (393) + BEC Rev.5 (31). Bridges: sitc3_sitc4 (5,408), sitc2_sitc3 (2,805), sitc2_sitc4 (2,693). Views: view_sitc3_commodity, view_sitc2_commodity, view_isco_occupation, view_bec_category. |
| `migrations/0075_cofog_isic31_isic2.ts` | 2026-04-15 | COFOG (188) + ISIC Rev.3.1 (538) + ISIC Rev.2 (277, +2 synthetic nodes). Bridges: isic31_isic4 (229), isic31_isic5 (231), isic2_isic31 (76). Views: view_cofog_function, view_isic31_activity, view_isic2_activity. ISIC chain Rev.2→Rev.3.1→Rev.4→Rev.5 complete. |
| `migrations/0076_hs_version_chain_sitc1.ts` | 2026-04-15 | HS 2007 (6,373) + HS 2002 (6,569) + HS 1996 (6,474) + SITC Rev.1 (2,784). Bridges: hs07_hs12 (6,197), hs02_hs07 (6,108), hs96_hs02 (6,226), sitc1_sitc2 (1,334). HS chain 1996→2022 complete. SITC chain Rev.1→Rev.4 complete. |
| `migrations/0077_atc_drug_classification.ts` | 2026-04-15 | WHO ATC 2021-12-03 (6,440 codes, 5 levels: 14+94+269+909+5154). Standalone hierarchy, 0 orphans. View: view_atc_substance. |
| `migrations/0078_iso4217_currency.ts` | 2026-04-15 | ISO 4217 active currencies (178 codes, flat). View: view_iso4217_currency. HS chain 1996→2022 + SITC chain Rev.1→Rev.4 + ISIC chain Rev.2→Rev.5 all complete. 27 concordance systems, 86,167 total edges. |
| `migrations/0079_locode_iso3166_geo.ts` | 2026-04-15 | UN LOCODE 2024-1 (116,067 locations: 17,520 ports + 9,029 airports + 13,143 rail) + ISO 3166-1 (296 countries). Geo bridges: sovereign_m49 (219), iso3166_sovereign (215). Views: view_locode_location, view_iso3166_country. |
| `migrations/0080_iso639_languages.ts` | 2026-04-15 | ISO 639-1 (184 language codes, 2+3 char, native name, language family). Bridge: iso3166_m49 (215). View: view_iso639_language. 30 concordance systems, 86,816 total edges. |
| `migrations/0081_who_gho_sdg.ts` | 2026-04-15 | WHO GHO (3,057 health indicators, 28 prefix groups) + UN SDG framework (437 nodes: 17 goals + 169 targets + 251 indicators, 3-level hierarchy, 0 orphans). Views: view_who_gho_indicator, view_sdg_indicator. |
| `migrations/0082_asfis_fda_ndc.ts` | 2026-04-15 | FAO ASFIS 2025 (13,761: 13,708 species + 53 ISSCAAP groups, 0 orphans) + FDA NDC bulk 2025 (131,664 drug products). Bridge: atc_ndc (69,740 ATC chemical substance → NDC generic name). 31 systems, 156,556 total edges. |
| `migrations/0083_locode_iso3166_bridge.ts` | 2026-04-15 | UN LOCODE ↔ ISO 3166-1 concordance bridge: locode_iso3166 (115,687 LOCODE location → ISO 3166-1 country, SUBSTRING(rkey,1,2) = iso2_code JOIN). 32 systems, 272,243 total edges. |
| `migrations/0084_icd10_iso4217_iso3166.ts` | 2026-04-15 | WHO ICD-10-CM 2019 (90,168 nodes: 22 chapters + 1,513 3-char codes + 14,804 4-char codes + leaf codes up to 7 chars, 0 orphans). Bridge: iso4217_iso3166 (164 ISO 4217 currency → ISO 3166-1 country, entity name JOIN). 34 systems, ~272,407 total edges. View: view_icd10_disease. |
| `migrations/0085_sitc_hs_derived_bridges.ts` | 2026-04-15 | 6 derived SITC↔HS concordance bridges: sitc4_hs2017 (29,861), sitc4_hs2012 (28,354), sitc3_hs2017 (14,756), sitc2_hs2017 (10,053), sitc1_sitc4 (1,115), sitc1_hs2017 (1,053). All derived via shared CPC3 JOIN or chain composition. 40 systems, 517,336 total edges (excl. openalex_concept). |
| `migrations/0086_hs_sitc_bidirectional_bridges.ts` | 2026-04-15 | 3 HS→SITC4 derived bridges: hs2017_sitc4 (29,861), hs2022_sitc4 (29,052), hs2012_sitc4 (27,868). Completes bidirectional SITC↔HS cross-classification. 44 systems, 632,471 total edges. |
| `migrations/0087_isic4_cross_bridges.ts` | 2026-04-15 | 4 ISIC4 cross-bridges: isic4_cpc21 (2,504), isic4_hs2017 (5,764), isic4_sitc4 (3,213), isic4_nace (679). Derived via shared ISIC5 JOIN + CPC21 chain. ISIC4→trade goods fully connected. 48 systems, ~686,757 total edges. |
| `migrations/0091_isic_cross_version_naics_extended.ts` | 2026-04-15 | **ISIC Rev.2↔3.1↔4↔5 full bidirectional + NAICS extensions.** Reverse bridges: isic5_isic4 (700), isic4_isic31 (229), isic5_isic31 (231), isic31_isic2 (76). Chain bridges: isic4_isic2 (43), isic5_isic2 (44), isic2_isic4 (43), isic2_isic5 (44). NAICS: naics_nace (63), naics_cpc21 (67). 79 systems, 601,415 total edges. |
| `migrations/0092_sitc_isic4_hs_sitc3_cpc_nace.ts` | 2026-04-15 | **SITC→ISIC4 + HS→SITC3 + NACE/CPC reversals.** 9 bridges (~99K edges): hs2017_sitc3 (27,428), hs2022_sitc3 (28,592), hs2012_sitc3 (27,427), sitc3_isic4 (3,968), sitc2_isic4 (1,328), sitc1_isic4 (275), hs2022_isic4 (5,591), cpc3_cpc21 (4,391), nace_isic5 (625). SITC Rev.1–3 now linked to ISIC4 via HS2017 pivot. ~88 systems, ~720K+ total edges. |
| `migrations/0093_hs_sitc2_isic_cpc3_extended.ts` | 2026-04-15 | **HS→SITC2 + ISIC extended + 0092 reversals.** 11 systems: hs2017_sitc2 (9,353), hs2022_sitc2 (9,766), hs2012_sitc2 (9,344), isic4_cpc3 (2,600), isic5_cpc (2,504), cpc3_isic4 (~2,600), hs2017_isic5 (5,655), hs2022_isic5 (~5,600), isic4_sitc3 (3,968), isic4_sitc2 (1,328), isic4_sitc1 (275). Extra: sitc3_hs2017_r (27,428, reverse of new hs2017_sitc3). ISIC4 now fully connected to all SITC revisions both directions. ~100 systems. |
| `migrations/0094_hs_legacy_isic4_nace_cpc21_chains.ts` | 2026-04-15 | **HS legacy editions + HS/SITC/CPC3→NACE/CPC21.** 17 bridges: hs2012_isic4 (5,429), hs2007_isic4 (4,998), hs2002_isic4 (4,754), hs1996_isic4 (4,470), hs2017/2022/2012_nace (3634/3547/3382), hs2017/2022/2012_cpc21 (~2600 ea), sitc3/2/1_nace, sitc3/2/1_cpc21, cpc3_nace. HS 1996–2022 all editions linked to ISIC4, NACE Rev.2, CPC21. ~118 systems, ~932K edges. |
| `migrations/0095_reversal_completion_isic5_extended.ts` | 2026-04-15 | **Reversal of 0094 bridges + ISIC5 extended.** 22 bridges: isic4_hs2012/2007/2002/1996, nace_hs2017/2022/2012, cpc21_hs2017/2022/2012, nace_sitc3/2/1, cpc21_sitc3/2/1, nace_cpc3, isic5_hs2017/2022, isic5_sitc3/nace2/cpc21. All HS editions fully bidirectional with ISIC4, NACE, CPC21. |
| `migrations/0096_cpc3_direction_repair_naics_isic2_chains.ts` | 2026-04-15 | **CPC3 direction repair + NAICS/ISIC2/3.1 chains.** CPC3 mislabeled bridges: hs2017/2012_cpc3_r (5740/5500), sitc4_cpc3_r (3717), sitc2_hs2017/2022/2012_r. NAICS: naics_isic4, naics_hs2017, naics_cpc3. ISIC2: isic2_hs2017/nace/cpc21. ISIC3.1: isic31_hs2017/nace/cpc21. ~130 systems. |
| `migrations/0097_isic5_cpc21_nace_geo_iso639.ts` | 2026-04-15 | **ISIC5 extended + CPC21/NACE + geo + ISO639.** isic5_sitc4 (3159), isic5_cpc3 (2450), cpc21_nace (1819), nace_cpc21 (1819), sitc4_nace/cpc21, locode_m49 (~116K), m49_iso3166/sovereign (↔), sovereign_iso3166 (↔), iso639_iso639_3 (183), macro_iso639_3 (444). **Milestone: 1M+ edges.** 131 systems, 1,078,815 total edges. |
| `migrations/0098_isic5_complete_integration.ts` | 2026-04-15 | **ISIC5 complete + ISO4217/M49 + NAICS extended.** sitc3/2/1_isic5 (3904/1322/274) + isic5_sitc3/2/1 (reverse), hs2012/2007/2002/1996_isic5 (5350/4921/4689/4405) + reversals, cpc3_isic5 (2450), iso4217_m49 (100), m49_iso4217 (100), naics_nace_r (24). Also quick-build: sitc4_isic5 (3159), cpc21_cpc3 (4391), nace_sitc4 (2039). ISIC5 fully bidirectional with all 7 HS editions, all 4 SITC revisions, CPC3. 170 systems, 1,570,154 edges. |
| `migrations/0099_hs_legacy_full_coverage_naics_repair.ts` | 2026-04-15 | **HS 2007/2002/1996 full coverage + completeness fixes.** hs2007/2002/1996 → SITC4/3/2/1 + NACE + CPC21 + CPC3 (via HS succession chain, not ISIC4 mediation). sitc3/2/1 ↔ CPC3 (6 chains). ISIC3.1/ISIC2 bidirectional reverses. cpc21_isic5. Transit bridges: hs2002_hs2012 (5,949), hs1996_hs2007 (5,900±), hs1996_hs2012 (5,800±). NACE/CPC21 ↔ SITC3/2/1 (6 chains via isic4 mediation). All 7 HS editions symmetrically linked to all SITC revisions, NACE, CPC21, CPC3. ~2.0M+ total edges, ~270 systems. |
| `migrations/0100_ndc_atc_cpc3_hs_isic31_isic2.ts` | 2026-04-15 | **NDC↔ATC bidirectional + CPC3↔HS extended + ISIC3.1/2 HS chains.** ndc_atc (69,740 reverse of atc_ndc). cpc3_hs2022/hs2012/sitc4 + hs2022/2012_cpc3. hs2022/2012/2007/2002/1996_isic31 + reversals. hs2022_isic2 + isic2_hs2022. All HS editions ↔ ISIC Rev.3.1 and Rev.2. ~1.85M+ edges target. |
| `migrations/0101_sitc_hs_isic31_isic2_cpc3_completeness.ts` | 2026-04-15 | **SITC↔ISIC3.1/2 + HS→ISIC2 completeness.** hs2012/2007/2002/1996 ↔ ISIC2 (8 bridges). SITC4/3/2/1 ↔ ISIC3.1 (8 bridges). SITC4/3/2/1 ↔ ISIC2 (8 bridges). NACE ↔ ISIC3.1/2 (nace_isic31=207, nace_isic2=41). CPC3 ↔ ISIC3.1/2 (4 bridges). Full ISIC temporal chain (Rev.2↔3.1↔4↔5) universally accessible. ~1.87M+ edges target. |
| `migrations/0102_geo_chain_bridges.ts` | 2026-04-15 | **Geographic chain bridges.** iso3166_iso4217 (116, reverse). iso4217_sovereign (116) + sovereign_iso4217 (116). locode_sovereign (109,687) + sovereign_locode (109,687). Full geo chain: LOCODE ↔ ISO3166 ↔ M49 ↔ Sovereign ↔ ISO4217. ~1.98M+ edges target. |
| `migrations/0103_classification_hierarchy_bridges.ts` | 2026-04-15 | **Classification hierarchy bridges (parent/children).** atc_parent/children (6,426). icd10_parent/children (90,141). sdg_parent/children (420). cofog_parent/children (178). cpc3_parent/children (4,587). nace_parent/children (976). bec_parent/children (~23). ~2.15M+ edges target. |
| `migrations/0104_classification_hierarchy_extended.ts` | 2026-04-15 | **Extended hierarchy bridges + SITC chain completeness + geo reverses.** HS (5 editions) parent/children (6,842/6,431/6,275/6,471/6,376 each). SITC (4 revisions) parent/children (5,474/5,680/3,713/2,774 each). naics_parent/children (2,105). isic5/4/31/2 parent/children (721/657/459/267 each). cpc21_parent/children (4,586). isco_parent/children (383). SITC chain: sitc4/3/2/1_sitc1 reverses + hs2017/2022/2012_sitc1. Geo: m49_locode (97,319), sovereign_iso3166 (188), m49_iso4217 (100). ~2.7M+ edges, ~272 systems. |
| `migrations/0105_hs_legacy_succession_chain_bridges.ts` | 2026-04-15 | **HS 2007/2002/1996 full coverage via succession chain + CPC21/CPC3 completeness.** hs2012_isic31 (1,354) prerequisite. Fixes: sitc4_hs2007 (26,347 rebuilt), cpc3_sitc3 (72,248 rebuilt). HS 2007 bridges (via hs07_hs12): sitc4(26,347)/sitc3(25,918)/sitc2(8,829)/sitc1(994)/nace(3,029)/cpc21(99,549)/cpc3(~5.5K)/isic31(1,175)/isic2(18) + all reverses. HS 2002 (via hs2002_hs2012=5,949) + HS 1996 (via hs1996_hs2012=5,634): full parallel set. sitc2/1↔CPC3 completeness: sitc2_cpc3/cpc3_sitc2(~24K ea), sitc1_cpc3/cpc3_sitc1(~5K ea). cpc21_isic5(2,450). cpc21_sitc3/2/1 (72K/24K/5K). All 7 HS editions symmetrically linked to all SITC revisions, NACE, CPC21, CPC3. Succession chain approach (not ISIC4 mediation) for SITC/NACE/CPC3 bridges. ~4.5M+ total edges, ~310+ systems. |
| `migrations/0106_bec_asfis_hierarchy_naics_extended.ts` | 2026-04-15 | **BEC/ASFIS hierarchy + hs2017/2022 ISIC3.1/2 reverses + NAICS extended.** bec_parent/children (24 ea). asfis_parent/children (13,499 ea, FAO ASFIS species → ISSCAAP groups). hs2017_isic31(1,418)/hs2017_isic2(19) reverses. hs2022_isic31(1,371)/isic31_hs2022/hs2022_isic2(18)/isic2_hs2022. NAICS extended (via naics_isic4=24): naics_cpc3/sitc4/3/2/1/hs2022/hs2012 + reverses (~65-130 pairs each). cpc3_hs2007/2002/1996 reverses (after 0105). ~3.8M+ edges. |
| `migrations/0107_cpc21_reverses_naics_extended_sitc_cpc3.ts` | 2026-04-15 | **CPC21 missing reverses + NAICS extended + SITC↔CPC3 completeness.** cpc21_sitc4(61,697)/cpc21_isic31(608)/cpc21_isic2(23) reverses. NAICS via naics_cpc21 pivot (class-level, 67 edges): naics_sitc4/hs2017/hs2007/isic31/isic2 (87/157/152/4/2) + reverses. nace_naics(21). HS 2002 reverses: nace_hs2002(2,860) + sitc4/3/2/1_hs2002(25,335/25,024/8,449/917). SITC↔CPC3 completeness: sitc2_cpc3/cpc3_sitc2(24,628) + sitc1_cpc3/cpc3_sitc1(5,196). Fixed icd10_children to 90,141 (complete reverse of icd10_parent). Deduped cpc3_sitc1 and nace_hs2002. CPC21 now fully bidirectional with all SITC (1-4) and all HS (1996-2022). ~4.3M+ edges. |
| `migrations/0108_hs2002_1996_completion_naics_cleanup.ts` | 2026-04-15 | **HS 2002/1996 completion + NAICS cleanup.** hs2002_cpc21(81,500)/cpc21_hs2002(81,500). naics_hs2002/hs2002_naics(140). HS 1996 full set: hs1996_sitc4(23,694)/sitc3(23,475)/sitc2(7,838)/sitc1(856)/nace(2,678)/cpc21(90,375) + all reverses. naics_hs1996/hs1996_naics(140). NOTE: hs1996/2002/2007_cpc3=0 (domain mismatch in succession chain; no direct CPC3 concordance for these editions). All 6 HS editions (1996-2022) now fully connected to NAICS. ~5M+ edges. |
| `migrations/0110_naics_reverses_cpc3_sitc4_repair_iso639.ts` | 2026-04-15 | **NAICS small reverses + cpc3_sitc4 repair + ISO 639-3 macro + sovereign_locode fix.** cpc21_naics(67)/isic5_naics(74)/isic4_naics(24) — NAICS now fully bidirectional with CPC21, ISIC4, ISIC5. cpc3_sitc4 repaired 61,436→3,717 (fan-out noise → exact reverse of sitc4_cpc3). macro_iso639_3(444) — ISO 639-3 macro language bidirectional complete. sovereign_locode gap: +1,500 missing pairs → 109,687 (matches locode_sovereign). ~4.638M edges, 384 systems. |
| `migrations/0109_bidirectional_coverage_repair.ts` | 2026-04-15 | **Bidirectional coverage repair + HS1996/2002 CPC21 completion.** Missing reverses: isic4_isic5(700), iso3166_locode(109,687), cpc3_hs2017(5,740), hs2012_hs2002(5,949), hs2007_hs1996(5,787), hs2012_hs1996(5,634). Data quality: cpc3_hs2012 rebuilt 109,697→5,500 (CPC21 fan-out noise → exact reverse of hs2012_cpc3). HS1996 CPC21 final: cpc21_hs1996(90,375)/naics_hs1996(144)/hs1996_naics(144). HS2002 CPC21 race fix: cpc21_hs2002(95,740)/naics_hs2002(152)/hs2002_naics(152). Namespace dedup: deleted nace_r2/naics_nace2/isic5_nace2 (exact dups of nace_isic4/naics_nace_v2/isic5_nace). HS succession skip-hops bidirectional. ~4.7M+ edges (net lower due to cpc3_hs2012 repair -104K). |
| `migrations/0111_r_suffix_cleanup_sitc_asym_fix.ts` | 2026-04-15 | **_r suffix namespace cleanup + SITC4↔HS asymmetry repair.** Deleted 5 exact _r dups: hs2017_cpc3_r(5,740)/hs2012_cpc3_r(5,500)/sitc4_cpc3_r(3,717)/sitc2_hs2022_r(9,766)/sitc2_hs2012_r(9,344). Replaced chain-derived with exact reverses: sitc2_hs2017(10,037→9,353)/sitc3_hs2017(29,391→27,428) — chain had CPC3 fan-out noise (+684/+1,963). Deleted _r variants after canonical rename. SITC4↔HS asymmetry: hs2017_sitc4(27,861→29,861)/hs2012_sitc4(27,868→28,354) rebuilt as exact reverses (mismatch from 0088 re-derivation with different path). naics_nace_r(24) kept — distinct coarse sector mapping (2-digit NAICS→section NACE), not a dup. ~4.60M edges, 377 systems. |
| `migrations/0112_bec_hs_sitc_bridges.ts` | 2026-04-15 | **BEC Rev.4 ↔ HS (all 6 editions) + SITC (all 4 revisions) direct concordance bridges.** Source: UN Statistics "HS-SITC-BEC Correlations_2022.xlsx" (165,258 rows). BEC was previously isolated (hierarchy only). 40 systems added (20 forward + 20 reverse): hs2017/22/12/07/02/1996_bec + reverses (5,489/5,890/5,263/5,070/5,329/5,318 ea), sitc4/3/2/1_bec + reverses (3,041/3,391/2,583/1,970 ea). NOTE: BEC is a coarse economic interpretation layer (20 categories over thousands of HS/SITC codes) — high fan-out is by design, not noise. BEC now connects to entire classification universe via HS/SITC chains. ~4.77M+ edges, 417 systems. |
| `migrations/0113_cpc21_fanout_repair.ts` | 2026-04-15 | **CPC21 fan-out noise repair** — replaced ~800K chain-derived noise edges with direct UN concordances. cpc21_hs2017(118K→5,843)/cpc21_hs2012(110K→5,584)/cpc21_isic4(2,663→2,715)/cpc21_sitc4(61K→3,638). HS legacy editions via hs2022 pivot (vertex ID format mismatch in hs07_hs12 bridge): cpc21_hs2022(5,692)/hs2007_cpc21(3,853)/cpc21_hs2007(4,921)/hs2002_cpc21(3,647)/cpc21_hs2002(4,678)/hs1996_cpc21(3,401)/cpc21_hs1996(3,591). SITC chains via cpc21_hs2017×hs2017_sitcN: cpc21_sitc3(71K→4,673)/cpc21_sitc2(24K→1,554)/cpc21_sitc1(5K→314). 22 systems total. DB: 3,146,204 edges, 397 systems. |
| `migrations/0114_bec_extended_chains.ts` | 2026-04-15 | **BEC extended chains** — connect BEC to ISIC4/NACE/CPC21/CPC3/NAICS via HS2017 pivot. isic4_bec(477)/nace_bec(340)/cpc21_bec(1,881)/cpc3_bec(1,850)/naics_bec(14) + all reverses. NOTE: small counts expected (BEC is goods-only; service sectors in ISIC4/NACE don't map to HS). NOTE: cpc3_bec uses `hs2017_cpc3` as pivot (mislabeled system: actual src=CPC3, dst=HS2017). BEC now hub connecting HS/SITC trade to ISIC4/NACE/CPC21/CPC3/NAICS. DB: 3,155,328 edges, 407 systems. |
| `migrations/0115_isic_chain_bec_isic5_extended.ts` | 2026-04-15 | **Complete ISIC temporal chain → BEC.** isic5_bec(457)/isic31_bec(99)/isic2_bec(5) + reverses. Low counts for ISIC3.1/2 reflect narrow HS coverage of legacy editions. ISIC5 cross-bridge completeness verified: cpc21(2,504)/cpc3(2,450)/nace(625)/naics(74) all present. BEC now bidirectional with ALL classification systems (HS×6 + SITC×4 + ISIC×4 + NACE + CPC21 + CPC3 + NAICS). DB: 3,156,450 edges, 413 systems. |
| `migrations/0121_cofog_hs_legacy_isco_sitc.ts` | 2026-04-15 | **COFOG remaining HS legacy + ISCO × SITC revisions.** cofog_hs2007(241)/hs2002(235)/hs1996(231) + reverses. isco_sitc3(165)/sitc2(45)/sitc1(17) + reverses. cofog_sitc2(52)/sitc1(16) + reverses. ISCO now connected to ALL classification systems. DB: 3,167,376 edges, 481 systems. |
| `migrations/0122_cofog_hs2012_asfis_isic4_bridges.ts` | 2026-04-16 | **cofog_hs2012 gap repair + ASFIS ISSCAAP×ISIC4 bridge.** cofog_hs2012(299)/hs2012_cofog(299) — was missing from 0121 (race condition fix via dedup). asfis_isic4(73)/isic4_asfis(73) — FAO ISSCAAP groups G11-G94 → ISIC4 0311/0312/0321/0322 fishing activities. COFOG now connected to all 6 HS editions. DB: 3,168,120 edges, 485 systems. |
| `migrations/0123_asfis_hs_sitc_full_connectivity.ts` | 2026-04-16 | **ASFIS full connectivity — all HS editions + SITC all revisions.** asfis_hs2017(206)/hs2017_asfis(206) — direct FAO ISSCAAP→HS2017 6-digit species concordance (24 groups × 206 codes). asfis_hs2022(3492)/hs2012(2705)/hs2007(1209)/hs2002(1113)/hs1996(994) via isic4 chain + reverses. asfis_sitc4(776)/sitc3(1454)/sitc2(350)/sitc1(317) via isic4 chain + reverses. ASFIS now connected to all HS editions (6) and SITC revisions (4). DB: 3,193,352 edges, 505 systems. |
| `migrations/0124_asfis_remaining_atc_sdg_isic4.ts` | 2026-04-16 | **ASFIS remaining chains + ATC→ISIC4 + SDG→ISIC4 bridges.** asfis_isic5(73)/nace(73)/cpc21(1911)/cpc3(1911)/bec(248) + reverses — ASFIS now fully connected. atc_isic4(42)/isic4_atc(42) — all 14 ATC L1 therapeutic groups (A-V) → ISIC4 2100 pharma manufacturing. sdg_isic4(197)/isic4_sdg(197) — 17 SDG goals → relevant ISIC4 sectors. SDG extended: sdg_hs2017(300)/isic5(196)/nace(189)/cpc21(276)/sitc4(101) + reverses. DB: 3,204,386 edges, 529 systems. |
| `migrations/0125_sdg_atc_extended_chains.ts` | 2026-04-16 | **SDG extended chains (all HS editions + remaining SITC/BEC/CPC3/COFOG/ISCO) + ATC extended chains.** SDG: sdg_hs2022(297)/hs2012(242)/hs2007(157)/hs2002(151)/hs1996(124)/sitc3(154)/sitc2(45)/sitc1(20)/bec(20)/cpc3(264)/cofog(24)/isco(46) + reverses. SDG now connected to ALL trade/industry/employment systems. ATC: atc_hs2017(1428)/hs2022(1414)/isic5(42)/nace(14)/cpc21(112)/sitc4(686)/bec(28) + reverses. DB: 3,214,922 edges, 567 systems. |
| `migrations/0133_atc_hs_legacy_sitc_ndc_bec.ts` | 2026-04-16 | **ATC HS legacy editions + ATC SITC remaining + NDC BEC.** ATC HS complete: atc_hs2012(1,120)/hs2007(1,092)/hs2002(1,064)/hs1996(798) + reverses — ATC now fully bidirectional with all 6 HS editions. ATC SITC: atc_sitc3(826)/sitc2(196)/sitc1(14) + reverses — ATC↔SITC all revisions complete. NDC BEC: ndc_bec(83,560)/bec_ndc(83,560) — pharma goods → BEC end-use. Confirmed 0: atc_cofog/isco + gho_hs2017/sitc4. DB: 8,199,686 edges, 645 systems. |
| `migrations/0134_atc_isic2_asfis_isic31.ts` | 2026-04-16 | **ATC↔ISIC2 + ASFIS↔ISIC3.1 tail completeness.** atc_isic2(28)/isic2_atc(28) — ATC now connected to all 4 ISIC revisions (2/3.1/4/5). asfis_isic31(24)/isic31_asfis(24) — via asfis_hs2017×hs2017_isic31 pivot (direct asfis_isic4×isic4_isic31=0 due to vertex ID granularity mismatch at fishing group vs sector level). ASFIS now connected to all 4 ISIC revisions. Reverse-topo pass exhausted: gho/icd10↔hs/sitc=0 (healthcare≠goods), atc_naics=0, ndc_icd10=0. DB: 8,199,790 edges, 649 systems. |
| `migrations/0132_ndc_icd10_asfis_sdg_bridges.ts` | 2026-04-16 | **NDC historical ISIC + ASFIS↔SDG.** asfis_sdg(96)/sdg_asfis(96) — fishing species → SDG 14. ndc_isic31(83,560)/isic31_ndc + ndc_isic2(83,560)/isic2_ndc — pharma ISIC history (83,560 = 2/3 of 125,340 ndc_isic4 — only ISIC4 div/group levels bridge, not 4-digit class). ndc_icd10=0 (ATC L5/L1 vertex mismatch); ndc_naics/cofog/isco=0. DB: 8,022,346 edges, 629 systems. |
| `migrations/0131_atc_cpc3_naics_isic31_isic2_chains.ts` | 2026-04-16 | **ATC completeness + ISIC3.1/ISIC2 SDG/ATC bridges.** atc_cpc3(98)/cpc3_atc(98) — pharma → service product. isic31_sdg(100)/sdg_isic31(100) + isic31_atc(28)/atc_isic31(28). isic2_sdg(35)/sdg_isic2(35). NAICS remaining = all 0 (coarse sector codes don't reach healthcare/pharma ISIC4). isic31/2 → icd10/gho = 0. DB: 7,687,914 edges, 623 systems. |
| `migrations/0130_gho_fixes_icd10_sdg_ndc_extended.ts` | 2026-04-16 | **GHO repairs + ICD-10↔SDG + NDC extended + ATC/GHO↔SDG.** isic4_gho(45,855)/cpc21_gho(58,083) repairs. gho_cpc3(58,083)/isco(55,026)/cofog(12,228) + reverses — GHO extended chains complete. icd10_sdg(18,802)/sdg_icd10(18,802) — ICD-10 diseases ↔ SDG goals. NDC: ndc_isic5(125,340)/nace(41,780)/cpc21(334,240)/cpc3(292,460)/sdg(83,560) + reverses — FDA drugs fully embedded. atc_sdg(28)/sdg_atc(28) + gho_sdg(6,114)/sdg_gho(6,114). NOTE: gho_icd10 skipped (56.4M Cartesian). qchain() hardened with 20-attempt retry. DB: 7,687,392 edges, 615 systems. |
| `migrations/0129_icd10_cpc3_gho_bridges.ts` | 2026-04-16 | **ICD-10→CPC3 bridge + WHO GHO isolation fix.** icd10_cpc3(134,533)/cpc3_icd10(134,533) — via icd10_isic4 × isic4_cpc3. gho_isic4(45,855)/isic4_gho(45,855) — 3,057 WHO GHO indicators × 15 ISIC4 healthcare codes (cross-product bridge, GHO was fully isolated). gho_isic5(45,855)/nace(39,741)/cpc21(58,083)/cpc3(58,083)/isco(55,026)/cofog(12,228) + reverses — GHO extended chains. gho_icd10 skipped (Cartesian product). DB: +2.6M edges after 0129+0130 repair. |
| `migrations/0128_icd10_extended_chains.ts` | 2026-04-16 | **ICD-10 extended classification chains (ISIC5 + NACE + CPC21).** icd10_isic5(98,918)/isic5_icd10(98,918) — via icd10_isic4 × isic4_isic5 (1-to-1). icd10_nace(80,116)/nace_icd10(80,116) — via isic4_nace. icd10_cpc21(134,533)/cpc21_icd10(134,533) — via isic4_cpc21 (healthcare service product codes). ICD-10 now connected to ISIC4/ISIC5/NACE/ATC/ISCO/COFOG/CPC21. DB: 4,983,936 edges, 583 systems. |
| `migrations/0127_icd10_healthcare_bridges.ts` | 2026-04-16 | **ICD-10 healthcare + drug class + occupation bridges.** icd10_isic4(98,918)/isic4_icd10(98,918) — all 18,463 ICD disease codes → ISIC4 healthcare sector (86/87/88) via chapter-letter concordance. icd10_atc(23,646)/atc_icd10(23,646) — ICD chapter → ATC L1 therapeutic group. icd10_isco(282,444)/isco_icd10(282,444) — via icd10_isic4 × isic4_isco chain. icd10_cofog(40,592)/cofog_icd10(40,592) — via icd10_isic4 × isic4_cofog chain. ICD-10 now connected to ISIC4/ATC/ISCO/COFOG. DB: 4,356,802 edges, 577 systems. |
| `migrations/0126_ndc_isic4_bridge.ts` | 2026-04-16 | **NDC→ISIC4 pharma bridge.** ndc_isic4(125,340)/isic4_ndc(125,340) — 41,780 FDA NDC drug products → ISIC4 21/210/2100 via ndc_atc L5→L1 prefix extraction. NDC extended chains (ndc_hs2017 etc.) intentionally not built — the chain JOIN would create ~4.26M Cartesian product pairs with no semantic value. DB: 3,465,602 edges, 569 systems. |
| `migrations/20260415223000_flight_graph_spine.ts` | 2026-04-15 | **Flight graph spine.** `vertex_aircraft` + `vertex_flight_operation` + 6 topology edges (`edge_aircraft_*`, `edge_flight_*`) + 2 MVs (`mv_flight_operation_latest_by_aircraft`, `mv_flight_operator_kpi_daily`). Captures operator/owner/delay/occupancy/revenue/cost/profit snapshots. |
| `migrations/20260416110000_vertex_flight_offer.ts` | 2026-04-16 | **Flight fare offers.** Adds `vertex_flight_offer` (provider/route/date/price/currency/booking_url/deeplink_url) and `mv_flight_offer_cheapest_by_route_date` for cheapest fare lookup per route/date/currency. |
| `migrations/20260416140000_udf_did_normalization_and_safe_divide.ts` | 2026-04-16 | **SQL UDFs — DID normalization + safe division.** 3 IMMUTABLE SQL UDFs: `did_web_root(varchar)` (3-segment root extraction, replaces 12 inline `split_part` concat calls in `mv_actor_repo_stats`), `normalize_actor_did(varchar)` (site.etzhayyim.com aliasing + root extraction, replaces 4 CASE blocks in `mv_profile_page_stats`), `safe_divide(float8, float8, float8)` (zero-safe division, replaces 5 inline CASE expressions in `mv_domain_coverage_live`). |
| `migrations/20260416150000_mv_rebuild_with_udfs.ts` | 2026-04-16 | **MV rebuild using UDFs from 20260416140000.** DROP+CREATE for `mv_actor_repo_stats`, `mv_profile_page_stats` (with indexes), `mv_domain_coverage_live`. **Option A (2026-04-16)**: `mv_profile_page_stats` excludes `vertex_page` (985M rows). Page counts served by `view_page_count_by_canonical_did` (plain VIEW). down() restores pre-UDF inline SQL (also without vertex_page). |
| `migrations/20260416160000_mv_canonical_did_intermediate.ts` | 2026-04-16 | **Intermediate MVs for canonical DID pre-computation + page count VIEW.** `view_page_count_by_canonical_did` (plain VIEW — query-time page count from vertex_page, no streaming state). `mv_actor_canonical_did` (DISTINCT raw_did→canonical_did from actor sources only: social_stats + governance_policy + tool_grants). `mv_did_web_root_index` (DISTINCT sub_did→root_did from vertex_did WHERE did LIKE 'did:web:%', ~16K rows). Applied out-of-band via psql; kysely_migration row inserted manually. |
| `migrations/20260416180000_hospitality_talent_world_coverage.ts` | 2026-04-16 | **Hospitality + Talent world coverage.** Exposes 876K+ previously untracked vertex rows to `mv_world_coverage_live`. Adds 8 `dim_world_domain` entries (accommodation/hotel/minpaku/ryokan for hospitality; occupation_code/skill_taxonomy/job_posting/talent_cohort_stat for talent). Rebuilds `mv_world_vertex_per_host` with `vertex_accommodation` (828K) + `vertex_talent_cohort` + `vertex_skill` + `vertex_occupation` + `vertex_job_posting`. Expected: accommodation ~55%, hotel ~118%, occupation_code 100%. Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260416090000_world_collection_coverage_and_keiyaku_quality.ts` | 2026-04-16 | **collection-level world coverage + keiyaku dedupe graph + data quality snapshots.** Adds `vertex_keiyaku_contract_canonical`, `vertex_keiyaku_contract_observation`, `edge_keiyaku_canonicalizes`, `dim_world_domain_collection`, `mv_world_record_per_host_collection`, `mv_world_collection_coverage_live`, `vertex_data_quality_daily`, `mv_data_quality_latest`. Purpose: stop treating all domain rows under one `app_host` as sharing the same record count, expose per-collection coverage, materialize contract canonicalization as first-class vertex/edge topology, and persist daily quality metrics (`bad_json`, duplicate business keys, invalid geo, missing core fields). Note: Kysely migration file is canonical SSoT, but live apply may require out-of-band `psql` because migrator is blocked by historical missing migration `20260415140000_strategy_graph`; when applied manually, insert matching `kysely_migration` row. |
| `migrations/20260416190000_adhoc_count_rollup_mvs.ts` | 2026-04-16 | **Ad-hoc COUNT rollup MVs** — 9 count MVs replacing per-request full-table scans: `mv_vertex_app_total_count` (vertex_app WHERE did IS NOT NULL), `mv_collector_dashboard_counts` (6-metric UNION: collectorRuns/dnsObservations/btcAddresses/ethAddresses/scanResults/archiveSnapshots), `mv_malak_dashboard_counts` (threatActors/btcRiskSignals), `mv_vertex_ip_address_total` (vertex_ip_address), `mv_site_page_total` (vertex_page 985M rows, BACKGROUND), `mv_site_job_total` (vertex_collection_job), `view_page_count_by_domain` (plain VIEW), `mv_site_wet_chunk_total` (vertex_wet_chunk), `mv_site_wat_total` (vertex_wat), `mv_site_screenshot_total` (vertex_screenshot). Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260416210000_belief_system_emotion_graph.ts` | 2026-04-16 | **Belief system vertex + karma graph.** `vertex_belief_system` (7 rows: YHWH ~4.3B, Dharma ~2B, Secular ~1.2B, Dialectical Materialism ~1B, Confucian ~400M, Orthodox Christianity ~260M, Shinto ~4M) + ALTER `edge_constrained_by` (binding_strength/constraint_type/evidence_type/epoch) + ALTER `edge_seeks_recognition_from` + `mv_belief_actor_coverage`. Applied 2026-04-16 06:53:31 UTC via `pnpm db:migrate`. |
| `migrations/20260416230000_vertex_page_count_cache.ts` | 2026-04-16 | **vertex_page COUNT(*) cache table + mv_vertex_page_count** — `vertex_page_count_cache` (1-row static cache table, fallback) + `mv_vertex_page_count` (streaming MV `SELECT COUNT(*) AS cnt FROM vertex_page`). Problem: direct scan of vertex_page (985M rows) in mv_world_vertex_per_host caused repeated cluster resets (S3 Hummock write timeout). Fix: pre-aggregate to 1-row MV; upstream MVs reference `mv_vertex_page_count` instead of scanning vertex_page directly. Stability achieved via: `SET enable_locality_backfill=true` (★★★, weight 0.7) + `ALTER SYSTEM SET barrier_interval_ms=5000` (★★, weight 0.2) + `ALTER SYSTEM SET checkpoint_frequency=30` (★★, weight 0.1). Applied out-of-band; `mv_vertex_page_count` BACKGROUND backfill in progress (job 4686, リセットなし). |
| `migrations/20260416220000_collection_domain_coverage_mappings.ts` | 2026-04-16 | **Collection-domain coverage mappings** — 84 INSERT entries into `dim_world_domain_collection` mapping actual data collections to world domains. Previously only 75 actual collection mappings existed (358 were bootstrap placeholders); this adds mappings for all top collections with >1K records across 40+ app_hosts (bus/religious/tentai/media-gamers/gakko/iryo/food/douro/gov/railway/recycle/character/sports/haikibutsu/pharma/water/handotai/gas-station/kuruma/manga/ev/toshokan/fda/ndc/locode/vessel/shizen/denki/aircraft/icd10/hakubutsukan/drama/sanctions/mine/energy/culture/finance/talent/legal-entity). `mv_world_collection_coverage_live` now shows 157 actual mappings (up from 75), 50 collections at ≥90% coverage. Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260416260000_plc_record_attribution_coverage.ts` | 2026-04-16 | **did:plc record attribution fix.** `mv_plc_record_per_host` — new streaming MV extracting app_host from NSID for `did:plc:*` repos (e.g. `did:plc:etzhayyim-collector`). Routes 42,786 previously unattributed records: chizai(15,835) + maps(13,936) + dns(7,621) + gtin(2,939) + patent(2,455). `mv_world_coverage_live` rebuilt to include `+ COALESCE(plc.record_count, 0)`. Impact: maps 0.0027%→0.0096% (3.6x), gtin 0.0001%→0.0004% (4.6x), patent 0.0007%→0.0019% (2.9x). Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260416300000_world_total_calibration_iso639_malak.ts` | 2026-04-16 | **dim_world_domain world_total calibration.** iso639: 184→7929 (ISO 639-1→ISO 639-3 living language count). malak 6 domains: apt_group/exploit_kit/bulletproof_host/cybercrime_group/ransomware_family/malicious_registrar: world_total 300-500→300,000 (over-coverage artifacts). Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260416290000_gov_municipality_talent_bls_vertex_coverage.ts` | 2026-04-16 | **gov_municipality + occupation_bls vertex coverage.** Final mv_world_vertex_per_host rebuild (job 5204) adding `vertex_gov_municipality`(gov +190) + `vertex_occupation_bls`(talent +23). gov vertex_count: 2,286→2,476. talent: 53,899→53,922. All vertex tables with meaningful data now covered. Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260417220000_vertex_ipaddress_access_log.ts` | 2026-04-17 | **PII Tier 3 visitor access log (ADR-0018).** `vertex_ipaddress_access_log` — PDS OCEL middleware が 全 XRPC/HTTP request を fire-and-forget INSERT。AT Record / createRecord / MST / federation は経由しない (Tier 3 = 非 federable)。ipaddress.etzhayyim.com actor が論理 owner。columns: ip / ip_did / ip_version / user_agent (512 char) / nsid / http_method / path / status / latency_ms / colo / country / referer / auth_level / caller_did + RLS 3 col + created_at。`sensitivity_ord=3`。bot/crawler UA フィルタなし (分析対象)。Write hook: `50-infra/cloudflare/workers/atproto/src/middleware/index.ts` `ocelLogging`。GDPR Art 17 cascade purge は後続 ADR で対応。 |
| `migrations/20260420130000_vertex_isekai_world.ts` | 2026-04-20 | **ADR-0040 ISEKAI world map SSoT (Phase 1).** 3 vertex + 3 edge table: `vertex_isekai_world_map` (name/width_m/height_m/seed/biome_mask_cid), `vertex_isekai_world_scene` (world_map_uri/scene_type/x_dm/z_dm/radius_dm/label/params_json — coords in BIGINT decimeters since AT Lexicon forbids float), `vertex_isekai_world_portal` (from/to scene URIs, fade_ms, bidirectional), `edge_map_contains_scene`, `edge_scene_adjacent` (distance_dm + coupling_strength DOUBLE PRECISION), `edge_scene_portal`. 5 indexes (world_map_uri / scene_type / map_contains src / adjacent src+dst / portal src). Feeds `com.etzhayyim.apps.isekai.listScenes` XRPC + `isekai.etzhayyim.com/world-map.htm` minimap preview + future `run_isekai_world` distance-LOD scene pool. Applied out-of-band via psql (kysely migrator blocked by pre-existing 20260419010000 corruption); kysely_migration row inserted manually. |
| `migrations/20260419180000_vertex_translation_link.ts` | 2026-04-19 | **ADR-0034 typed translation linkage projection.** `vertex_translation_link` — 6-segment NSID `com.etzhayyim.apps.media_gamers.record.translationLink` の projection (convention fallback は 5-segment のみ対応のため graph worker `handleCollection()` に explicit case を追加)。columns: source_uri / source_lang / translated_uri / lang / source / quality_score / created_at + RLS 3 col。Indexes: `(source_uri)` + `(translated_uri)` で双方向 lookup を O(log N) に。Replaces value_json parsing in media-gamers `cmdListLinks` with typed Kysely `.selectFrom("vertex_translation_link")`. Backfill: 6 rows from `vertex_repo_record` via `value_json::jsonb->>` 一回。Applied out-of-band via psql (kysely migrator blocked by pre-existing 20260417200000 corruption); `kysely_migration` row inserted manually。`pnpm db:gen` で `database.ts` 826 tables / 10,439 cols 再生成。 |
| `migrations/20260417210000_did_etzhayyim_cidv1_path.ts` | 2026-04-17 | **ADR-0029 did:etzhayyim CIDv1 + path schema** — `vertex_etzhayyim_identity` に CIDv1 metadata 7 col 追加 (`cid_version`, `multicodec`, `multihash_code`, `multibase_prefix`, `genesis_op_cid`, `root_did`, `path_segment`)。`parent_did` / `depth` は既に `20260417150000_etzhayyim_did_recursive_tree` で追加済 (重複追加なし)。新テーブル: `edge_etzhayyim_path_child` (parent→child path lineage) + `vertex_etzhayyim_op_log` (signed op history per DID, op_type ∈ {create,update,deactivate})。新 MV 2 件: `mv_etzhayyim_op_log_head` (latest op per DID) + `mv_etzhayyim_path_depth_dist` (path 深さ分布)。Reference impl: `10-protocol/did-etzhayyim/`。Resolver: `did.etzhayyim.com`。XRPC: `com.etzhayyim.identity.submitOp`。Applied 2026-04-17 out-of-band via psql; `kysely_migration` row inserted manually. |
| `migrations/20260417200000_vertex_email_message_bec_columns.ts` | 2026-04-17 | **BEC/phishing screening schema.** ALTER `vertex_email_message` ADD 8 columns: `from_name` / `reply_to` / `return_path` / `spf_result` / `dkim_result` / `dmarc_result` / `auth_results_raw` / `first_seen_from_domain`. `mv_email_first_contact_senders` (first-contact senders per account×domain, GROUP BY cardinality bounded by ~4 users × ~10K domains). `mv_email_auth_fail` (SPF/DKIM/DMARC fail hits). 3 indexes: idx_email_first_contact / idx_email_from_name / idx_email_dmarc. Populated by m365_mail_ingest.py parse_auth_results() + from_name extraction from internetMessageHeaders. Applied out-of-band via psql; kysely_migration row inserted manually. |
| `migrations/20260417190000_vertex_m365_sync_state.ts` | 2026-04-17 | **M365 ingest state tracking.** `vertex_m365_user` (tenant user cache: upn/user_id/display_name/mail/account_enabled/upn_domain/first_seen_at/last_seen_at). `vertex_m365_sync_state` (per-upn watermark: upn/data_kind/last_sync_at/last_received_at/record_count/error_count/last_error/throttle_until/status/run_id). Used by m365-ingest T1 actor pipeline for delta-sync state management. Applied out-of-band via psql. |
| `migrations/20260417180000_vertex_yabai_attacker_tracking.ts` | 2026-04-17 | **BEC attacker tracking schema.** `vertex_yabai_bait_url` (bait URLs planted in replies to BEC actors for attribution). `edge_bait_sent_to` (bait→threat_actor link). `vertex_yabai_bait_hit` (IP access logs when bait URL is fetched: ip/user_agent/headers/geo). `mv_yabai_bait_hit_summary` (per-bait hit count + last seen). Enables attacker IP tracking + C2 infrastructure correlation. Applied out-of-band via psql. |
| `migrations/20260417140000_vertex_google_workspace_tables.ts` | 2026-04-17 | **Google Workspace shared ingest schema** — broader per-service vertex/edge tables spanning calendar/drive/contacts/tasks/docs/sheets/slides/meet. Companion to `20260417130000_vertex_gmail_tables`. Design: `90-docs/260417-google-workspace-ingest-runbook.md`. **Applied 2026-04-17 out-of-band** via `scripts/run-one-migration.mjs` (kysely migrator blocked by pre-existing drift `20260416240000_vertex_game_title_natural_person_coverage` missing); `kysely_migration` row inserted + `FLUSH`. 41 tables created: 33 vertex + 8 edge across 8 services. Fix: line 4 JSDoc comment had `vertex_*/edge_*` which terminated block comment mid-way; renamed to `vertex_ / edge_` so TS parser no longer fails on the header. |
| `migrations/20260417130000_vertex_gmail_tables.ts` | 2026-04-17 | **Gmail ingest schema** — 7 vertex (`vertex_gmail_{account,thread,email,contact,sync_job,outbound_email,phishing_alert}`) + 4 edge (`edge_gmail_{email_in_thread,email_from_contact,email_to_contact,account_owns_thread}`). GraphAr-native (1 AT record = 1 row, typed columns, no val_json). RLS 3-col + created_at on every table. Private text columns (subject/snippet/body/to/cc/bcc) carry Signal-encrypted ciphertext (`signal:v1:{ct}`). Driven by `60-apps/etzhayyim-project-gmail/appview/etzhayyim-wasm-gmail-gm4il0x1/src/app.ts` commits. Applied out-of-band via psql (kysely migrator blocked by pre-existing `20260416240000_vertex_game_title_natural_person_coverage` drift); kysely_migration row inserted. |
| `migrations/20260417120000_vertex_yabai_tables.ts` | 2026-04-17 | **vertex_yabai_* tables for yabai Risk Intelligence (AML/CTI) app.** Landing tables for `com.etzhayyim.apps.yabai.{entity,evidence,risk,alert,enforcement,flag,intel_access_log,registration_ban}` writes that previously returned `[]` on read (no tables). Columns mirror `60-apps/etzhayyim-project-yabai/appview/etzhayyim-wasm-yabai-y8b41k0x/src/app.ts` emissions. |
| `migrations/20260417070000_isic4_duplicate_cleanup.ts` | 2026-04-17 | **isic4 duplicate domain cleanup.** `dim_world_domain` の `isic4` 行 (app_host='isic4.etzhayyim.com', world_total=766) を DELETE。`isic` 行 (app_host='isic', world_total=766) と完全重複 — DID `did:web:isic.etzhayyim.com` の AT records は `isic` として正常カウント済み。`isic4.etzhayyim.com` は alias 未設定のため 0 coverage の phantom entry だった。FLUSH 後 `mv_world_coverage_live` 更新: 461→460 domains, empty 2→1 (残 yoro)。Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260417200000_moneyforward_replacement_base.ts` | 2026-04-17 | **ADR-0031 MoneyForward replacement base.** 11 vertex + 5 edge + 1 MATERIALIZED VIEW + 4 plain VIEW across 4 actors (kaikei/seikyu/keiyaku/kousuu). Multi-tenant via `owner_did` = did:plc:etzhayyim-{works,japan,labo}. Monetary columns forced DOUBLE PRECISION (RW unsupported NUMERIC(p,s)). `mv_kaikei_trial_balance` sole MV (UNION ALL dr/cr, GROUP BY owner×period×account — low cardinality). `view_seikyu_invoice_aging` plain VIEW (NOW() forbidden in MV SELECT). `view_kousuu_project_burn` plain VIEW (compute node reset on empty LEFT JOIN — promote to MV at ~100K timeEntry rows). β4 schema evolution: ALTER TABLE `vertex_atrecord_kaikei_journal_entry` ADD transaction_id/line_no/debit_amount/credit_amount for composite N:M dr/cr + exact 税抜/税込 matching. Applied via psql (kysely migrator blocked by ordering corruption). |
| `migrations/20260421000000_vertex_projector_flow_tables.ts` | 2026-04-21 | **Design A / ADR-0036 — projector flow state to Hyperdrive.** 5 tables + 5 indexes for the BPMN Projector agent-flow extension: `vertex_projector_flow` (DAG metadata), `vertex_projector_flow_node` (node config with promoted LLM columns: model_id/temperature_bps/max_tokens/prompt_template/tools_json), `edge_projector_flow_edge` (GraphAr-native transitions with condition_expr + edge_kind), `vertex_projector_flow_run` (execution instances + parent_run_id for ToT lineage + runner_kind ∈ cron/durable_object/on_commit), `vertex_projector_flow_step` (append-only step log with per-step LLM token accounting + ocel_event_id/bpmn_activity_id cross-ref). Retires AT records `com.etzhayyim.projector.{flow,branch,reflection}`; NSID XRPC surface unchanged. Pilot actor: projector. `kyber-projector.etzhayyim.com` keeps catalog + RACI + OCEL (audit sink), holds no flow state. deps.toml: `[[migrations]] projector-flow-to-hyperdrive`. |
| `migrations/20260419130000_vertex_yabai_infra_track.ts` | 2026-04-19 | **Yabai phishing-infrastructure tracking.** `vertex_yabai_infra_track` — one row per (domain, probe) snapshot of DNS A/AAAA/NS/MX/CNAME + WHOIS (registrar/created/updated/expires) + Team Cymru ASN (asn/asn_org/bgp_prefix/hosting_provider) + crt.sh CT + HTTP HEAD + TLS s_client banner (subject/issuer/SAN/notAfter/version/cipher). 5 indexes. 2 streaming MVs: `mv_yabai_infra_latest` (DISTINCT ON domain) + `mv_yabai_infra_hosting_rollup` (domain_count per hosting_provider×asn×country). Also: `edge_yabai_operated_by` linking yabai ASN/registrar entities → GLEIF LEI legal-entity DIDs. Populated by `60-apps/etzhayyim-project-yabai/tools/track-phishing-infra/` (local node scripts: track-phishing-infra.mjs / expand-coverage.mjs / enrich-legal-entity.mjs / abuse-drafts/generate-drafts.mjs). Initial load: 173 phishing domains (152 existing + 21 sibling discovered via reverse-IP pivot). 4 ASN-level PhishingInfrastructure evidence (AS135377 UCLOUD HK 73 / AS152194 CTG Server 51 / AS45102 Alibaba SG 14 / AS47583 Hostinger 9). 3 legal-entity DIDs linked via LEI (Alibaba Cloud US LLC / Hostinger UAB / GMO Internet). |
| `migrations/20260418013944_kaikei_pl_bs_reporting.ts` | 2026-04-18 | **ADR-0031 Phase C — P/L + B/S streaming MVs.** `mv_kaikei_pl_period` (revenue/expense flow per owner×period×account_type, UNION ALL debit-expense + credit-revenue, GROUP BY bounded by ~3×80×5 < 2K rows). `mv_kaikei_bs_delta` (asset/liability/equity delta per period, 4-UNION normalized flows — asset +dr/-cr, liability/equity +cr/-dr). `view_kaikei_monthly_summary` (P/L + B/S union VIEW, feeds `com.etzhayyim.apps.kaikei.getMonthlySummary` XRPC). Built on `debit_amount`/`credit_amount` columns from β4. Applied out-of-band via psycopg2; kysely_migration row inserted manually. |
| `migrations/20260417050000_shinka_yukkuri_oil_ongakuka_aliases_domains_vertices.ts` | 2026-04-17 | **shinka + yukkuri + oil-coverage + ongakuka coverage bootstrap.** dim_app_host_alias: sh1nk4ev→shinka, y5kk5r1x→yukkuri, ong4k4k4→ongakuka (3 aliases). dim_world_domain: ongakuka(50K) + oil_company(200) + oil_field(10K) + oil_basin(2K) + oil_pipeline(5K) + oil_terminal(1K) + oil_trade(5M) + oil_cargo(2M) + crude_grade(300) + oil_refinery(2K) + pricing_benchmark(100) = 11 new domains. dim_world_domain_collection: 20 new entries (autorace.venue, shinka×2, yukkuri×2, ongakuka×2, maps×3, oil×10). mv_world_vertex_per_host rebuilt (job 5392, BACKGROUND, 25 app_hosts): +yukkuri(video 16+generation 3+line 1) + shinka(evolution 6) + oil-coverage(10 tables, ~41 rows). mv_world_coverage_live rebuilding. Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260417040000_yoro_auth_domains_final_collection_mappings.ts` | 2026-04-17 | **yoro + auth domain gaps + final collection mappings.** Added `yoro` (1M, platform activity) + `auth` (10K, auth worker records) to dim_world_domain. Added 5 collection mappings: ipaddress.ipAddress + ipaddress.geolocation, maps.building + maps.ownership, yoro.browsingHistory. All app_hosts with >50 records now have dim_world_domain entries. `dim_world_domain`: 450 entries. `dim_world_domain_collection`: 630 total (272 actual). Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260417030000_final_collection_mappings_yukkuri_shinka_domains.ts` | 2026-04-17 | **Final collection mappings + yukkuri/shinka domain gaps — 27 entries + 2 domains.** Added `yukkuri` (10K, video generation) + `shinka` (1K, evolution events) to dim_world_domain. Collection mappings: cofog.function, iso639.language, media_gamers.graphEdge+graphVertex, maps.naturalZone+layerCoordinator+verticalZone+airport+port+profile+spot+landRegistry+infraSegment+station+operator+businessRegistry (13 maps), recruit.demandForecast+occupationBls, site.collectionJob, malak.malware, keirin.velodrome, bec.category, keiba.venue, kyotei.venue, yukkuri.video, shinka.kyumeiResult+shinkaEvolution. `dim_world_domain_collection`: 625 total (267 actual). `dim_world_domain`: 448 entries. Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260417020000_sitc_cpc_gho_naics_chizai_isic4_collection_mappings.ts` | 2026-04-17 | **SITC/CPC/GHO/NAICS/chizai/ISIC4 collection mappings + isic4 domain — 27 entries + 1 domain.** Added `isic4` to dim_world_domain (766, ISIC Rev.4). Collection→domain mappings: sitc1.code + sitc.commodity + sitc.commodity_rev2 + sitc.commodity_rev1 (4 SITC), cpc.commodity_item_v3 + cpc.commodity_item (2 CPC), chizai.chosakuken + chizai.shohyo (2 chizai), gho.indicator + who.gho_indicator (2 GHO), gtin.product, malak.nvd + malak.asn, maps.geoAlias + maps.legalEntity, naics.industry, keiba.venue_global, isco.occupation, ethics.conduct, open_isic × 3 (isic4/isic31/isic2), drone.drone, tentai.moon, recycle.rate, society6.state, handotai.microprocessor. `dim_world_domain_collection`: 598 total (240 actual). Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260417010000_classification_standard_collection_mappings.ts` | 2026-04-17 | **Classification standard collection mappings — 28 entries.** Added actual collection→domain mappings for: hs1996/hs2002/hs2007/hs2012/hs2022/hs (10 HS code collections), iso639_3.language, atc.code+atc.substance, sitc.commodity_rev3, dns.observation, nace.activity, handotai.chip, maps.adminArea+mapsPoi, isic5.economic_activity_rev5, gtin.gtin, sdg.indicator, iso3166.country, iso4217.currency, m49_region, mine.mineRecord, uchu.mission, sovereign.sovereign. `dim_world_domain_collection`: 571 total (213 actual, 358 bootstrap). All classification standard domains now have actual collection→domain mappings. Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260417000000_tentai_cluster_nebula_kyber_collection_coverage.ts` | 2026-04-17 | **tentai_cluster + tentai_nebula domain gaps + kyber collection mapping.** `com.etzhayyim.apps.tentai.cluster` (7,106 rows) and `com.etzhayyim.apps.tentai.nebula` (1,679 rows) had no `dim_world_domain` entries. Added tentai_cluster (15K world_total, stellar clusters) + tentai_nebula (5K, nebulae). Added 3 `dim_world_domain_collection` entries: tentai.cluster, tentai.nebula, kyber.inbox.documentSignal. Both show >100% coverage via tentai record_count (1,288,237). Total: 445 domains. Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260416330000_kyber_office_document_vertex_coverage.ts` | 2026-04-16 | **kyber office document vertex coverage.** `vertex_office_document` (124,913 rows, collection=`com.etzhayyim.apps.kyber.inbox.documentSignal`) had no `dim_world_domain` entry. Added `kyber` domain (world_total=500K, unit='business documents (office ingest)', sector='enterprise'). Rebuilt `mv_world_vertex_per_host` (job 5297, BACKGROUND, 126M rows) adding `kyber → vertex_office_document`. Rebuilt `mv_world_coverage_live` (job 5362). kyber coverage: 124,913/500,000 = 24.98%. Total: 20 app_hosts in mv_world_vertex_per_host. Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260416270000_vertex_keiyaku_ipaddress_bengoshi_judge_coverage.ts` | 2026-04-16 | **keiyaku + ipaddress + bengoshi + judge vertex coverage.** `dim_world_domain` に bengoshi(45K, registered lawyers JP) + judge(3K, professional judges JP) INSERT (FLUSH 必須)。`mv_world_vertex_per_host` 再構築 (job 5115, BACKGROUND, locality_backfill, 126M rows) 追加: `vertex_occupation_wikidata`(talent +923) + `vertex_ip_address`(ipaddress +1,671) + `vertex_keiyaku_contract_canonical`(keiyaku +5,362) + `vertex_keiyaku_contract_observation`(keiyaku +6,402) + `vertex_lawyer`(bengoshi +102) + `vertex_judge`(judge +58)。`mv_world_coverage_live` 再構築完了。19 app_hosts。Applied out-of-band; kysely_migration row inserted manually. |
| `migrations/20260416240000_vertex_game_title_natural_person.ts` | 2026-04-16 | **vertex_game_title + vertex_natural_person + vertex_domain coverage.** `mv_world_vertex_per_host` rebuilt adding: `vertex_game_title`(media-gamers +13K) + `vertex_natural_person`(natural-person +108K, collected 1→108,803) + `vertex_domain`(dns +2.47M, coverage 0.0004%→0.71%). 3 BACKGROUND jobs (4958, 5020) completed without cluster reset using locality_backfill. Applied out-of-band; kysely_migration rows inserted manually. |
| `migrations/20260416230000_actor_belief_karma.ts` | 2026-04-16 | **Actor belief karma MVs + edge seeding.** `mv_actor_belief_karma` (JOIN `edge_constrained_by` × `vertex_belief_system`, column aliases matching `BeliefRow` TS interface) + `mv_actor_karma_aggregate` (per-actor belief_count/avg_individuation/total_binding/weighted_individuation) + `mv_belief_actor_coverage`. Seeds `edge_constrained_by` for ~10 key actors (pmc-ncbi-nlm-nih-gov/yhwh/etzhayyim/news/handotai/society6/iryo/dojo/shizen/murakumo). Applied 2026-04-16 07:53:17 UTC via `pnpm db:migrate`. Enables live graph queries in `BeliefKarmaTab.svelte` (yoro appview) — static `fallbackBeliefs` removed. |
| `migrations/0120_isco_cofog_completeness.ts` | 2026-04-15 | **ISCO/COFOG completeness.** ISCO to all HS editions: isco_hs2022(255)/hs2012(255)/hs2007(220)/hs2002(214)/hs1996(210) + reverses. COFOG: cofog_hs2022(297)/sitc4(183)/sitc3(182)/isic31(8)/isic2(1) + reverses. ISCO extended: isco_isic31(33)/cpc3(442)/cofog(84) + reverses. ISCO now fully embedded in classification graph. DB: 3,165,372 edges, 465 systems. |
| `migrations/0119_isco_cofog_hs_sitc_cpc21_chains.ts` | 2026-04-15 | **ISCO/COFOG→HS/SITC/CPC21 chains.** isco_hs2017(255)/cofog_hs2017(299)/isco_sitc4(160)/cofog_cpc21(364) + reverses. ISCO now fully embedded: ISIC4+ISIC5+NACE+BEC+CPC21+HS2017+SITC4. COFOG: ISIC4+ISIC5+NACE+BEC+CPC21+HS2017. DB: 3,160,604 edges, 439 systems. |
| `migrations/0118_isco_cofog_bec_cpc21_isic_gaps.ts` | 2026-04-15 | **ISCO/COFOG→BEC/CPC21 + ISIC legacy gaps.** isco_bec(12)/cofog_bec(12) + reverses. isco_cpc21(456)/cpc21_isco(456) — occupation→product classification. isic31_naics repaired 4→22 (via isic31_isic4×isic4_naics). isic2_naics chain=0 (genuine empty: ISIC2 too sparse). isic31_cpc3(597)/isic2_cpc3(22) already present. DB: 3,158,448 edges, 431 systems. |
| `migrations/0117_isco_cofog_extended_chains.ts` | 2026-04-15 | **ISCO/COFOG extended chains.** isco_isic5(104)/isco_nace(120)/cofog_isic5(42)/cofog_nace(43) + reverses. Derived via isco_isic4×isic4_isic5/isic4_nace and cofog_isic4×isic4_isic5/isic4_nace chain JOINs. ISCO now linked to ISIC4+ISIC5+NACE. COFOG now linked to ISIC4+ISIC5+NACE. Both can chain further to HS/SITC/BEC/CPC21. DB: 3,157,452 edges, 425 systems. |
| `migrations/0116_isco_cofog_isic4_bridges.ts` | 2026-04-15 | **ISCO-08 ↔ ISIC-4 + COFOG ↔ ISIC-4 concordance bridges.** isco_isic4(140)/isic4_isco(140) — ILO ISCO-08 Vol I Annex III: occupation groups → primary industry (agriculture/health/education/ICT/construction/transport). cofog_isic4(52)/isic4_cofog(52) — UN SNA Ch.17: COFOG function divisions → delivering industry. ISCO and COFOG were previously isolated (hierarchy only). Now both bridge to ISIC-4 and can chain to HS/SITC/BEC/NACE/CPC21. DB: 3,156,834 edges, 417 systems. |
| `migrations/0090_cross_version_hs_chain_bridges.ts` | 2026-04-15 | **HS cross-version transitive chains + SITC/ISIC4 extended.** 15 bridges: hs2022↔hs2012/2007/2002/1996 (both dirs), sitc3/2/1→hs2022, sitc3/2/1→hs2012, isic4_hs2022. Any HS edition now navigable to any other via direct bridge. |
| `migrations/0089_reverse_bidirectional_bridges.ts` | 2026-04-15 | **13 reverse bridges for full bidirectionality.** All derived via dst_vid↔src_vid swap + INSERT+FLUSH. New: hs2017_isic4 (5,736), sitc4_isic4 (3,231), nace_isic4 (679), cpc21_isic4 (2,663), sitc4_hs2022 (29,052), sitc4_sitc3 (5,408), sitc3_sitc2 (2,805), sitc4_sitc2 (2,688), hs17_hs22 (6,561), hs17_hs12 (6,528), hs12_hs07 (6,197), hs07_hs02 (6,108), hs02_hs96 (6,226). After: full bidirectional ISIC4↔HS↔SITC, HS version chain 1996↔2022 bidirectional. 60 systems, 543,060 total edges (excl. openalex_concept). |
| `migrations/0088_bridge_rebuild_flush_fix.ts` | 2026-04-15 | **FLUSH fix + ISO 639-3 taxonomy.** Root cause: RisingWave buffers DML until checkpoint FLUSH — all prior bridge inserts (0083–0087) were lost on cluster recovery. Fix: INSERT+FLUSH pattern. Renamed: isic5_hs2017→isic4_hs2017 (5,736), isic5_sitc4→isic4_sitc4 (3,231). New taxonomy: ISO 639-3 (7,929 languages: SIL iso-639-3.tab, 3-letter codes, scope/type fields). New bridges: locode_iso3166 (109,687), cpc_isic5 (2,504), isic5_nace (625), isic4_cpc21 (2,663), sovereign_m49 (219), iso3166_m49 (188), iso4217_iso3166 (116), hs2017_sitc4 (27,861), hs2022_sitc4 (29,052), hs2012_sitc4 (27,868), sitc3_hs2017 (29,391), sitc2_hs2017 (10,037), sitc1_hs2017 (1,053), isic4_hs2017 (5,736), isic4_sitc4 (3,231), iso639_3_iso639 (183), iso639_3_macro (444). 47 active systems, 463,904 total edges (excl. openalex_concept). |
| `migrations/20260425100000_vertex_mcp_tool_def.ts` | 2026-04-25 | **ADR-2604261000 — MCP tool registry as Kysely schema** (amends ADR-0042 §D3, replaces `gen-tool-manifest.mjs` codegen). 1 vertex table `vertex_mcp_tool_def` (PK `vertex_id` = `at://did:web:{actor-host}.etzhayyim.com/com.etzhayyim.mcp.toolDef/{nsid.replace('.','-')}`) + 3 indexes (nsid / actor_did / enabled+actor_did). Promoted columns: nsid / actor_did / actor_host / lexicon_type / description / input_schema (VARCHAR JSON, no JSONB) / output_schema / lxm_scope / visibility / version / enabled / source_path / schema_hash / deployed_at + RLS 3-col + GraphAr promoted columns. Source of truth = `00-contracts/lexicons/com/etzhayyim/apps/**/*.json`; sync via `70-tools/scripts/contract/sync-mcp-registry.py --apply` (mirror of `sync-bpmn-actors.py`). host-sdk `/mcp` reads via Kysely SELECT + 60s in-memory cache (`mcp-registry-loader.ts`); `tools/call` forwards to `app.handleXRPC()`, runtime input validation by handler-side `parseLexiconInput()` (no AJV/Zod at MCP boundary, ADR-0005). Opt-in: `createWorkerExport(setup, { mcpRegistry: {} })` or env `APP_MCP_REGISTRY=1`. Same `INSERT N rows` regime as ADR-0056. |

**Cluster state (2026-04-18 verified)**: 493 base tables (317 vertex + 168 edge + 5 dim + 3 other) + 147 streaming MVs (ADR-0031 Phase C: mv_kaikei_pl_period + mv_kaikei_bs_delta; BEC: mv_email_first_contact_senders + mv_email_auth_fail) + 39 plain views (+view_kaikei_monthly_summary) + 3 SQL UDFs + 0 sinks + 0 connections. BEC columns (from_name/reply_to/return_path/spf_result/dkim_result/dmarc_result/auth_results_raw/first_seen_from_domain) added to vertex_email_message (2026-04-17). m365_sync_state + m365_user tables added (2026-04-17). Compactor scaled 3 replicas/16GiB (2026-04-17, SSTable backlog 11K draining).
Plain hummock, no ENGINE=iceberg, no Lakekeeper catalog. Compute memory limit raised 6.5Gi → 24Gi (2026-04-14) after 0026 v1 OOM. `force_two_phase_agg = true` system-wide (values.yaml `[streaming]`, 2026-04-16).
**System params tuned (2026-04-16)**: `ALTER SYSTEM SET barrier_interval_ms = 5000` (default 1000) + `checkpoint_frequency = 30` (default 1) — reduces S3 checkpoint write frequency during large backfills. Persistent across restarts (system-level, not session).
**CC LIVE (2026-04-16, phase3k S3 connector SWAP complete)**: `vertex_page`=985,469,916 | `edge_links_to`=4,603,156,096 | `edge_links_to_domain`=2,328,938,130. 148,773 parquet files (49,591 × 3 types). Staging tables dropped. Views (`view_cc_page_canonical`, `view_cc_edge_links_to_canonical`, `view_cc_domain_page_count_canonical`) and MVs (`mv_cc_domain_out_degree`, `mv_cc_domain_in_degree`) recreated pointing at live tables (backfilling from 2.3B-row `edge_links_to_domain`).
`edge_classified_as`: 8,199,790 edges, 649 systems (0127–0134 complete: ICD-10/GHO/NDC/ATC/SDG/ASFIS/BEC fully bridged; ATC↔HS all 6 editions + all 4 SITC revisions + all 4 ISIC revisions complete; ASFIS↔all 4 ISIC revisions complete; gho_icd10 intentionally skipped — 56.4M Cartesian; ndc_icd10=0 ATC L5/L1 mismatch; gho_hs/sitc=0 healthcare services≠goods; reverse-topo pass exhausted).
`mv_world_coverage_live`: **460 domains**, 307 meaningful, 112 full ≥100%, 1 empty (yoro), 347 partial. `mv_world_vertex_per_host`: 27 app_hosts (job 5515, 2026-04-17) — webpage(985M) + legal-entity(122M) + dns(2.47M) + hospitality(828K) + kyber(125,519: +calendar 106 + email 500) + natural-person(108K) + talent(54,125: +demand_forecast 203) + chizai(37K) + media-gamers(13K) + keiyaku(11,764) + maps(2.8K) + gov(2,476) + ipaddress(1,671) + bengoshi(102) + patent(81) + judge(58) + railway(49) + gtin(30) + bank(0) + blockchain(0) + yukkuri(20) + shinka(6) + oil-coverage(41) + ongakuka(0). telecom: 8,116 records confirmed. `mv_vertex_page_count`: 985,469,916 (BACKGROUND complete, locality_backfill, リセットなし)。`dim_world_domain`: **460 entries** — isic4 (重複、app_host='isic4.etzhayyim.com') を 2026-04-17 に DELETE (isic entry と同一データ)。bengoshi/judge/kyber/tentai_cluster/tentai_nebula/yukkuri/shinka/yoro/auth/ongakuka/oil_company/oil_field/oil_basin/oil_pipeline/oil_terminal/oil_trade/oil_cargo/crude_grade/oil_refinery/pricing_benchmark 新設 (2026-04-16-17)。`dim_app_host_alias`: sh1nk4ev→shinka + y5kk5r1x→yukkuri + ong4k4k4→ongakuka 追加 (2026-04-17)。world_total 較正: iso639(184→7929, ISO 639-3), malak 6 domain (300→300K)。shinka: 0→36 records (3.6%). yukkuri: 0→28 records (0.28%). pricing_benchmark: 41/100=41%.
`dim_app_host_alias`: 227 entries (fao→asfis.etzhayyim.com added 2026-04-16; car-dealer→kuruma, recruit→talent added 2026-04-16; sh1nk4ev→shinka, y5kk5r1x→yukkuri, ong4k4k4→ongakuka added 2026-04-17; isic2/isic31/isic5 short-name aliases confirmed existing).

**SQL UDFs (2026-04-16, migration 20260416140000)**:
- `did_web_root(varchar) → varchar` — extracts 3-segment root from hierarchical did:web path
- `normalize_actor_did(varchar) → varchar` — site.etzhayyim.com aliasing + root extraction
- `safe_divide(float8, float8, float8) → float8` — zero-safe division with fallback

**SQL UDFs (2026-04-21, migration 20260421160000, pending apply)**:
- `classify_t1(spf, dkim, dmarc, reply_to, from_addr, subject, body_urls_json) → int` — yabai T1 phishing classifier (ADR-0032 port from `app.ts:352-366 computePhishingScore`). Plan-time inlined to native vector eval (verified via `EXPLAIN VERBOSE`). Bench 2026-04-21: 1.97x wall-clock speedup vs Worker TS at N=10K, 14.7x wire compression. Semantic note: RW lacks `~*` → use `LOWER(s) ~ 'lowercase_pattern'`.

**UDF language strategy (ADR-0044, 2026-04-21)**:
- Rule-based / CASE / regex / aggregate → **SQL UDF** (this file)
- Heavy per-row compute (hash / protobuf / custom parser / ML feature) → **Embedded Rust (WASM)** — `regex` crate not vendored, use stdlib `str::contains`
- External IO / LLM / heavy Python lib → **Python External UDF** — MUST set `@udf(io_threads=100)` (default=1 silently caps at ~7.5 parallel, 10x slow)
- Java External UDF = not recommended (no public batch API in v0.2.1, bounded ~7.5 parallel)
- High-concurrency burst web fetch = CF Worker `Promise.all(50..100)`, NOT External UDF
- See: `90-docs/adr/0044-risingwave-udf-language-strategy.md`

**Option A (2026-04-16)**: `vertex_page` (985M rows) is **never scanned by a streaming MV**.
Page counts served by `view_page_count_by_canonical_did` (plain VIEW, query-time).
`mv_profile_page_stats` uses actor sources only (social + governance + tools).

**S3 Hummock write timeout (2026-04-16)**: Concurrent background DDL (95M row scan +
multiple MV backfills) caused `write part timeout` on SSTable upload to S3 at ~228MB.
Root cause: S3 write stall under heavy streaming checkpoint load. Mitigation: avoid
multiple large BACKGROUND DDL jobs concurrently; use `SET background_ddl = true` one at
a time and wait for each to complete before starting the next.

**Completed (2026-04-16)**:
- `mv_vertex_page_count` — BACKGROUND backfill COMPLETE (job 4686→4958, locality_backfill + barrier_interval_ms=5000 + checkpoint_frequency=30、リセットなし)。`mv_world_vertex_per_host` + `mv_world_coverage_live` 再構築済み。
- `vertex_page_count_cache` テーブル作成済み (不使用、cleanup 可)。
- `mv_world_vertex_per_host` — 2026-04-16に `vertex_game_title`(media-gamers +13K) + `vertex_natural_person`(natural-person +108K) + `vertex_domain`(dns +2.47M) を追加。dns coverage: 0.0004% → 0.71%。natural-person app_host は初めて vertex_count に反映 (collected: 1 → 108,803)。
- `mv_plc_record_per_host` — 2026-04-16新設。`did:plc:etzhayyim-collector` の 42,786 件が従来どおり app_host=NULL で coverage に反映されていなかった問題を修正。NSID の第4セグメントで app_host routing。maps 0.0027%→0.0096%、gtin 4.6x、patent 2.9x。`mv_world_coverage_live` に `COALESCE(plc.record_count,0)` 加算で統合。
- `mv_world_vertex_per_host` 2回目再構築 (2026-04-16, job 5115) — 7テーブル追加: `vertex_occupation_wikidata`(talent +923) + `vertex_ip_address`(ipaddress +1,671) + `vertex_keiyaku_contract_canonical`(keiyaku +5,362) + `vertex_keiyaku_contract_observation`(keiyaku +6,402) + `vertex_lawyer`(bengoshi +102) + `vertex_judge`(judge +58)。`dim_world_domain` に bengoshi(45K) + judge(3K) 新規 INSERT。FLUSH 必須 (RisingWave DML は checkpoint 後に可視化)。19 app_hosts に拡張。
- `mv_world_vertex_per_host` 3回目再構築 (2026-04-16, job 5204) — 2テーブル追加: `vertex_gov_municipality`(gov +190) + `vertex_occupation_bls`(talent +23)。全 vertex テーブルのうち意味のあるデータを持つものはすべて追加済み (残りは 0 行か infra テーブル)。`mv_world_coverage_live` も再構築 (job 5267)。
- `dim_world_domain` world_total 較正 第2回 (2026-04-16): tentai_moon 1,300,000→300 (自然衛星 ~300個、前回誤変更を修正); tunnel 100K→600K (実測499K道路トンネル); handotai 100K→1M (実測300K半導体デバイスを反映)。
- **外部権威リポジトリ調査**: did:web:fda.hhs.gov/unece.org/who.int 等の 280K+ records は did:web:*.etzhayyim.com ミラーリポジトリ経由で mv_world_record_per_host に既収録 (etzhayyim.com mirror > external count)。追加 MV 不要。
- **collection-level coverage**: dim_world_domain_collection 650 mappings (total, 292 actual + 358 bootstrap)。20260417 Round4 (5 entries): ipaddress.ipAddress + ipaddress.geolocation + maps.building + maps.ownership + yoro.browsingHistory。20260417 Round5 (20 entries, 2026-04-17): autorace.venue + shinka.kyumeiResult + shinka.shinkaEvolution + yukkuri.generation + yukkuri.line + ongakuka.track + ongakuka.generation + maps.road + maps.railway + maps.weatherPoint + oil_company/field/basin/pipeline/terminal/trade/cargo/crude_grade/oil_refinery/pricing_benchmark collections。dim_app_host_alias: sh1nk4ev→shinka, y5kk5r1x→yukkuri, ong4k4k4→ongakuka 追加 (2026-04-17)。`mv_world_record_per_host_collection` ベースの gap scan により全既知 collection → domain マッピング完了。
- `mv_world_vertex_per_host` 4回目再構築 (2026-04-16, job 5297) — `kyber` app_host 新設: `vertex_office_document`(124,913 rows, com.etzhayyim.apps.kyber.inbox.documentSignal) を追加。`dim_world_domain` に kyber(500K, business documents) INSERT。24.98% coverage。20 app_hosts に拡張。
- **現在の上限**: 152 domains が collected=1 (placeholder only)。残り向上は実データ収集 (aircraft/kuruma/anime/energy ingest) が必要。schema 構造的改善は完了。

**CC bulk ingest COMPLETE (2026-04-16)**: phase3k S3 connector SWAP done — vertex_page (985,469,916), edge_links_to (4,603,156,096), edge_links_to_domain (2,328,938,130). Staging tables dropped. CC views/MVs fixed to reference live tables.

## PR #1032 Deployment Summary (2026-04-18/19)

**Status**: ✅ **PRODUCTION LIVE**
**Date**: 2026-04-18 (staging) → 2026-04-19 (production)
**Migrations**: 40 new migrations (20260415–20260417 timestamp-based)
**Coverage**: 461 world domains, 649 classification concordance systems, 8,199,790 edges

**Key Additions**:
- `vertex_orbital_system` / `vertex_orbital_body` — Space mapping (ISS, planets, celestial bodies)
- `vertex_maps_job` — Street-chunk collection job tracking + 5 indexes
- `vertex_flight_offer` + `vertex_flight_operation` — Flight operations & fare data
- 46 new lexicon definitions (legalEntity, hospitality, ongakuka, onion, maps extensions)
- Complete classification concordance: HS (6 editions 1996–2022) ↔ SITC (4 revisions) ↔ ISIC (4 versions) ↔ NACE ↔ BEC ↔ ATC ↔ ICD-10 ↔ SDG ↔ GHO ↔ ASFIS ↔ NDC

**Deployment Results**:
- Staging: 6h, 40/40 migrations, zero incidents, RW peak memory 78%
- Production: 5h, 40/40 migrations, zero incidents, zero rollbacks
- 24h post-deploy monitoring: Clean (zero errors, 100% uptime)
- All new endpoints responding (<100ms latency)

**Documentation**:
- Deployment runbook: `90-docs/260417-codex-etzhayyim-mv-live-reads-deployment-runbook.md`
- Monitoring setup: `90-docs/260417-codex-staging-monitoring-setup.md`
- Post-deployment report: `90-docs/260420-codex-etzhayyim-mv-live-reads-post-deployment-report.md`

**Follow-Up Items**:
- ISS TLE live sync job (next sprint)
- Ongakuka seed data load (before appview launch)
- Migration automation docs (next month)

## Multi-Head Alembic Workaround (2026-05-12)

`pnpm db:migrate` currently fails with `Multiple head revisions are present`
because at least one in-tree migration (~0509 series) forked the chain.
Targeted upgrade (`alembic upgrade r_<id>`) also fails with
`Requested revision X overlaps with other requested revisions Y` for a
neighboring pre-existing fork. Until the chain is repaired upstream,
apply new schema directly via psycopg2 in 3 phases — **tables first,
then indexes (after a 1-2s settle), then materialized views**. RW's
catalog visibility is async; a CREATE INDEX issued in the same script
as its CREATE TABLE will see `table not found` if not phase-separated.
Reference apply pattern is in
`r_20260512100000_vertex_network_topology` (see deps.toml migration entry
`vertex-network-device-app-screen-ipfs-2026-05-12`).

## Reserved Vertex Names — CC Page Schema

`vertex_screenshot` already exists in this cluster as part of the
CommonCrawl page-ingest pipeline (`rkey, url, domain, blob_ref, ...`)
and `CREATE TABLE IF NOT EXISTS` will silently no-op against it. New
domain-specific screenshot tables must pick a non-colliding name (e.g.
`vertex_app_screenshot` for application-config screen captures). Check
`information_schema.tables` before adding a new `vertex_<noun>` if the
noun is generic.

## How to Add a New Table

Migration filenames are now **timestamp-based** for all new work.
Do not add new `000N_...` files. The repo contains legacy sequential
migrations plus newer timestamp migrations; keep old names as-is for
history integrity and add all new files as UTC timestamps:

- `migrations/20260415131000_<name>.ts`
- `migrations/20260415131100_<name>.ts`

1. Write DDL in a new `migrations/YYYYMMDDHHMMSS_<name>.ts`
2. Load credentials once: `source scripts/load-database-url.sh`
3. Apply: `pnpm db:migrate`
4. Regenerate types: `pnpm db:gen`
5. Verify zero drift: `pnpm db:drift`
6. Commit the migration file **and** the regenerated `src/database.ts`

Never hand-edit `src/database.ts`. If the types you want differ from
what `pnpm db:gen` emits, the DB is the source of truth — change the
DDL, not the TypeScript.

## How to Query

```typescript
import { createKyselyDb } from "@etzhayyim/magatama-host-sdk";
import type { Database } from "@etzhayyim/graph-schema";

const db = createKyselyDb(sql, env.HYPERDRIVE);
const actors = await db.selectFrom('vertex_actor')
  .where('did', '=', userDid)
  .selectAll()
  .execute();

// Commit log
const commits = await db.selectFrom('vertex_repo_commit')
  .where('seq', '>', lastSeq)
  .orderBy('seq', 'asc')
  .limit(100)
  .selectAll()
  .execute();
```

## CSR / CSC / SpMV Query Patterns

Edge テーブル = COO (Coordinate) 形式。クエリ時に CSR/CSC アクセスパターンを SQL で表現する。

### CSR (出エッジ: src → dst)

```typescript
// ユーザ X の follow 先
const rows = await db.selectFrom('edge_follows')
  .select(['dst_vid'])
  .where('src_vid', '=', actorDid)
  .execute();
```

### CSC (入エッジ: dst ← src)

**推奨: MV を使う** (streaming incremental、`_by_dest` テーブルとの dual-write 不要)

```typescript
// ユーザ X のフォロワー (MV 経由)
const rows = await db.selectFrom('mv_followers' as any)
  .select(['src_vid'])
  .where('dst_vid', '=', actorDid)
  .execute();
```

### SpMV (Sparse Matrix-Vector multiply)

PageRank / Label Propagation の 1 イテレーション:

```sql
SELECT e.dst_vid,
       SUM(v.score / d.out_degree) AS new_score
FROM edge_follows e
JOIN mv_follow_out_degree d ON d.src_vid = e.src_vid
JOIN vertex_actor v ON v.vertex_id = e.src_vid
GROUP BY e.dst_vid
```

degree MV (`mv_follow_out_degree` / `mv_follow_in_degree`) が正規化因子を提供。

### CSC 実装: MV vs `_by_dest` テーブル (重複問題)

| 方式 | 現状 | 問題 |
|---|---|---|
| `edge_*_by_dest` テーブル | 物理テーブル、INSERT 時に dual-write 必要 | write 側の複雑性 |
| `mv_followers` 等 MV | RisingWave streaming MV、自動 incremental 更新 | MV1-4 と `_by_dest` が重複 |

**方針**: MV に統一し `_by_dest` テーブルへの dual-write を廃止する。
→ `deps.toml [[migrations."csc-mv-consolidation"]]`

## Key Conventions

| Topic | Source |
|---|---|
| P10v2 GraphAr-native schema design | `90-docs/260407-kagami-p10v2-graphar-native-design.md` |
| CSR/CSC/SpMV query patterns | this file §CSR / CSC / SpMV Query Patterns |
| Field-level encrypt (signal:v1 ciphertext for private data) | `docs/260325-field-encrypt-design.md` |
| Promoted columns (NOT 1NF, performance tradeoff) | `docs/260324-graphar-promote-columns-design.md` |
| Hyperdrive (Cloudflare D1 Postgres wire) | `infra/CLAUDE.md` |
| PDS Commit Log = Queue | `deps.toml [[conventions]] "PDS Commit Log = Queue"` |
| MV memory safety (no wide MAX + high-cardinality GROUP BY) | this file §MV Memory Safety Guardrails |
| DID alias pattern (vertex_did_alias + view) | `migrations/0026_cc_page_did_alias.ts` |

## MV Memory Safety Guardrails (2026-04-14, post-0026-v1 OOM)

**Learned the hard way**: migration 0026 v1 created `mv_cc_page_canonical`
as a MATERIALIZED VIEW with `GROUP BY url` + 14 × `MAX(varchar)` over
2.9M `vertex_page` rows. Streaming operator held ~5 GiB of aggregation
state in RAM and OOM-killed the 6.5Gi compute pod. Cluster entered
recovery mode, blocked all DML until replay finished (~20 min).

### Forbidden MV shapes

| Anti-pattern | Why | Alternative |
|---|---|---|
| `GROUP BY <N>` where N>500k distinct keys, with MAX(varchar) over 5+ columns | Agg state = cardinality × column-count × avg-value-bytes, easily 5-20 GiB | Plain `CREATE VIEW` (query-time compute) OR narrow MV (2-3 columns only) |
| **`GROUP BY vertex_page.rkey`, `edge_links_to.src_vid`, or `edge_links_to.dst_vid`** (URL-hash columns, 985M–4.5B unique values) | Hash agg state overflows even with `force_two_phase_agg=true` (system default since 2026-04-16). 985M groups × any payload > 48 GiB RSS | Pre-aggregate to domain level (`edge_hosts_page.src_vid`, ~hundreds of thousands) OR use plain `CREATE VIEW` |
| MV that scans >10M rows on initial backfill | CREATE MV blocks until backfill completes + OOM risk | Use `BACKGROUND DDL` pattern below OR filter to zero/small initial set |
| MV fanning MAX over every payload column | Memory-linear in column count | Emit only keys + computed columns; JOIN back to source table at query time for payload |
| Multiple concurrent BACKGROUND DDL jobs over large tables | Compete for Hummock S3 write quota → `write part timeout` SSTable stalls (observed 2026-04-16, 95M row scan + MV backfill concurrent) | Serialize: wait for each `rw_ddl_progress` entry to clear before starting the next |

### Required pre-flight checks before `CREATE MATERIALIZED VIEW`

```sql
-- 1. Cardinality check
SELECT COUNT(DISTINCT <group_by_key>) FROM <source_table>;
-- If > 500,000 → use VIEW, not MV.
-- If GROUP BY key is vertex_page.rkey / edge_links_to.{src,dst}_vid → FORBIDDEN, always use VIEW.

-- 2. Row count (use rw_table_stats for tables > 100M rows to avoid S3 SlowDown)
SELECT t.name, s.total_key_count
FROM rw_catalog.rw_table_stats s JOIN rw_catalog.rw_tables t ON s.id = t.id
WHERE t.name = '<source_table>';
-- If > 10M rows → use BACKGROUND DDL pattern (see below).
-- If > 100M rows → BACKGROUND DDL required; no concurrent other background jobs.
```

### BACKGROUND DDL Pattern (large table backfill)

For MVs/tables that **must** touch > 10M rows, use `SET background_ddl = true`:

```sql
-- ALWAYS set before CREATE, reset after. Never leave background_ddl = true.
SET background_ddl = true;
CREATE MATERIALIZED VIEW mv_xxx AS ...;
SET background_ddl = false;

-- Monitor completion (poll until row disappears):
SELECT * FROM rw_catalog.rw_ddl_progress;
-- or: SHOW JOBS;
```

**Rules (learned 2026-04-16):**
1. **One job at a time** — concurrent background DDL competes for Hummock S3 write quota.
   Start the next job only after the previous `rw_ddl_progress` entry is gone.
2. Do **not** use for trivial creates (< 1M row backfill) — reset overhead is not worth it.
3. Do **not** combine with COUNT(*) on same heavy table during backfill — both hit S3 Hummock.
   Use `rw_catalog.rw_table_stats` for size estimation instead.

### 985M 行 COUNT(*) MV 安定化パターン (2026-04-16 実験結果・重み付き)

**症状**: `CREATE MV ... COUNT(*) FROM vertex_page` が S3 Hummock checkpoint write timeout でリセットを繰り返す。`background_ddl` 単独では 0.00% のまま進まない。

**実験した対策と効果:**

| 対策 | 効果 | 重み | 備考 |
|---|---|---|---|
| `SET enable_locality_backfill = true` | **高** ★★★ | 0.7 | データシャッフルを削減、S3 write 圧力が下がる。RisingWave v2.7+ 必須。これ単体が最も効果的 |
| `ALTER SYSTEM SET barrier_interval_ms = 5000` | **中** ★★ | 0.2 | checkpoint 頻度を 1/5 に下げる。S3 write 回数が減り timeout しにくい |
| `ALTER SYSTEM SET checkpoint_frequency = 30` | **中** ★★ | 0.1 | barrier ×30 回に 1 回だけ checkpoint → さらに S3 write を間引く |
| `background_ddl = true` 単独 | **低** ★ | — | S3 write 圧力を下げる効果なし。依存 MV に対する ordering 制約あり |
| `SELECT COUNT(*) FROM vertex_page` (read-only) | **失敗** ✗ | — | クラスタリセット時に TCP 接続断で kill される。read-only でも安全ではない |

**実績 (2026-04-16)**: 上記 3 つを組み合わせて job 4686 がリセットなしで 12%+ 到達 (従来は 0% → reset → 0% の無限ループ)。

**推奨コマンド:**
```sql
-- Step 0: system params (永続、再起動不要)
ALTER SYSTEM SET barrier_interval_ms = 5000;
ALTER SYSTEM SET checkpoint_frequency = 30;

-- Step 1: pre-aggregate MV (1 行) を locality_backfill + background で作成
SET enable_locality_backfill = true;
SET background_ddl = true;
CREATE MATERIALIZED VIEW mv_vertex_page_count AS
  SELECT COUNT(*) AS cnt FROM vertex_page;
-- SHOW JOBS で完了を確認

-- Step 2: 上位 MV は 1 行参照のみ (985M 行スキャン不要)
CREATE MATERIALIZED VIEW mv_world_vertex_per_host AS
  SELECT app_host, SUM(cnt) AS vertex_count FROM (
    ...
    UNION ALL SELECT 'webpage', cnt FROM mv_vertex_page_count  -- 1 行のみ
  ) sub GROUP BY app_host;
```

**依存 MV の作成タイミング**: `background_ddl` で作成した MV が SHOW JOBS に残っている間は、それに依存する下流 MV は `table or source not found` エラーになる。upstream backfill 完了を待ってから downstream を作成すること。

### Escape hatch

If a hot read path truly needs an MV over a high-cardinality key,
**increase compute memory first** (helm values `computeComponent.resources.limits.memory`)
and run the MV creation off-peak with a human watching `kubectl top pod`.
Cluster compute limit is 24Gi as of 2026-04-14 (was 6.5Gi).
`force_two_phase_agg = true` is ON system-wide (values.yaml `[streaming]`, 2026-04-16) —
this distributes hash agg across 14 vCPU tasks but does NOT eliminate the memory requirement,
only delays OOM for cardinalities < ~50M unique keys.

## CRITICAL: Hyperdrive + pg.Pool Configuration (2026-04-14)

**Hyperdrive `origin_connection_limit` が真の上限 — pg.Pool max は無意味。** Cloudflare 公式 docs (https://developers.cloudflare.com/hyperdrive/) に基づく:

| Layer | プール | 制限値 (現状) | 役割 |
|---|---|---|---|
| **pg.Pool** (app code) | logical slot per isolate | `max: 10` | Worker 内 concurrent query slot |
| **Hyperdrive proxy** | TCP socket per isolate | (header 受信後は無制限) | Worker → CF infra bridge |
| **Hyperdrive origin pool** | origin TCP connections | **`origin_connection_limit: 60`** | **全 Worker 共有 — 真の上限** |
| **RisingWave** | (max_connections 概念なし) | unbounded | RW は session-less |

### Worker pg.Pool 設定 (DEFAULT)

```typescript
new Pool({
  connectionString: env.HYPERDRIVE.connectionString,
  max: 10,
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 10_000,  // fail fast on origin pool exhaustion
})
```

per-isolate singleton として保持 (毎リクエストで `new Pool()` 禁止 — TCP handshake 重複)。

### CRITICAL: 並列 query 禁止 (Promise.all)

**1 request 内で `Promise.all([q1, q2, q3])` は禁止。** 3 connection を瞬間的に奪い、Hyperdrive origin pool (60) を全 Worker 競合で枯渇させる。
- Symptom: `Error: timeout exceeded when trying to connect`
- Fix: serial `await` で 1 connection ずつ順次

例外: 確実に 1 connection per Worker invocation で済む read query は parallel OK。**Write 系は必ず serial**。

### Hyperdrive 設定確認

```bash
npx wrangler hyperdrive list
# → origin_connection_limit を表示
```

設計詳細: `90-docs/260414-hyperdrive-pool-tuning-analysis.md` (TODO)

## Related

- `deps.toml [[migrations."drizzle-to-kysely"]]` — app client migration tracking
- `deps.toml [[migrations."repo-log-to-vertex"]]` — vertex naming migration (completed 2026-04-12)
- `deps.toml [[migrations."csc-mv-consolidation"]]` — CSC MV 統一 (MV1-4 に統一、`_by_dest` dual-write 廃止)
- `20-actors/magatama/sdk/magatama-host-sdk/src/kysely.ts` — `createKyselyDb()` implementation
- `_archive/30-graph/2026-04-13-kagami-sql/` — archived SQL transpiler subtree (kagami/src/sql, kagami-sql-compiler, kagami-provider)
