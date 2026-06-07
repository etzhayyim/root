# Session History

完了済みセッションの記録。CLAUDE.md から移動 (2026-05-07)。
現在進行中の作業・設計判断は `deps.toml [[migrations]]` / `90-docs/adr/` を参照。

---

## Kotoba/Datomic primary cutover Linode → Vultr+B2 (2026-04-22, ADR-0048)

**Migration**: Linode LKE (sg-sin-2, $364/mo) → Vultr VKE LAX (`vhf-8c-32gb`, $241/mo, **$123/mo savings**).

**Method**: B2 server-side copy of Hummock state (7.63 TiB / 173k SST objects, ~2h 20m, zero egress via Bandwidth Ally) + PostgreSQL metastore `pg_dump`/`pg_restore` + 3 `system_parameter` rewrites (state_store / data_directory / backup_storage_url).

**Cutover**: Hyperdrive config `e84c0a2b…` → `45.32.79.245:4566` (no Worker redeploy). All 772 tables / 172 MVs preserved with row counts intact (vertex_did 16,450 / vertex_repo_record 15.6M / edge_follows 15.6k).

**Lessons**:
- Per-row SQL migration via `psycopg2` was abandoned — projected 13h for `vertex_repo_record` alone, hit Linode upstream connection drops on tables >1M rows. B2 server-side copy is the canonical state-migration path.
- Initial `vhp-8c-16gb-amd` (16 GB, $96/mo) caused 17 compute OOM-kills in 9h. Scaled to `vhf-8c-32gb` (32 GB, $192/mo) which matches Linode `g6-dedicated-16` RAM.
- ~~B2 has no per-bucket rps quota → Linode's Foyer `recover_mode=Quiet` + `cache_refill` workarounds are now defense-in-depth, not load-bearing.~~ **RETRACTED 2026-04-25**: B2 *does* enforce a per-account request rate (observed ~12 SlowDown/sec = ~1700/2min during compute-0 cold-start refill). The Linode-era defense-in-depth blocks (`[storage.cache_refill]` with `data_refill_levels=0-6`, `insert_rate_limit_mb=450/50`, `statement_timeout_secs=120`) were **not ported** to `50-infra/vultr/kotoba/helm/values.yaml` during the ADR-0048 cutover. On 2026-04-25 a compute-0 OOMKill (patent-ingest bulk INSERT load) triggered a Foyer cold-start storm that tripped B2's quota and cascaded into a multi-hour Hummock `ObjectStore RateLimited` outage. Config ported from `50-infra/linode/kotoba-iceberg/helm/values-dedicated-32.yaml` 2026-04-25; see `50-infra/vultr/kotoba/deps.toml [kotoba_vultr.incident_2026_04_25]`. Bulk ingest paths must also `SET dml_rate_limit` (rows/sec per parallelism — official RW INSERT throttle, see `[[conventions]] rw-bulk-insert-throttle`).

**Decommissioned**: Linode LKE 589404 deleted, Vultr `vhp-8c-16gb-amd` pool deleted, `kagami-graphar` bucket deleted. `etzhayyim-iceberg` bucket purged (7.86 TiB / 174k objects) and deleted 2026-04-23 — **Linode Object Storage fully retired, B2 is the sole object storage provider**.

See: `90-docs/adr/0048-kotoba-vultr-b2-primary.md`, `50-infra/vultr/kotoba/`, supersedes ADR-0020.

---

## Recent Completion: ARIA 6-axis signal pipeline — attention checkpoint fix (2026-05-05)

**Status**: ✅ **COMPLETE — all 6 signal axes live, mv_signal_entropy + mv_signal_area_integral restored**

**Scope**: ARIA signal pipeline diagnosis and repair. All 6 Zeebe BPMNs (attention/emotion/market/influence/money/request) were deployed; emotion/market/influence INSERTs were invisible initially, and attention was frozen at 11 rows for 1+ hour.

### Root Cause

`mv_vessel_with_lei` foreground DDL backfill (380M-row JOIN of vessel + legal_entity) blocked Kotoba/Datomic streaming checkpoint barriers globally. The `vertex_signal_attention` streaming fragment was stuck at an older barrier epoch — INSERTs returned rowcount=1 but data never checkpointed. Emotion/market/influence recovered after ~9 min (checkpoint eventually caught up); attention did not (stuck for 20+ min beyond the checkpoint window).

### Fix

1. Confirmed `mv_vessel_with_lei` DDL completed (`rw_ddl_progress` = 0 rows)
2. Verified attention INSERTs were now accepted by Kotoba/Datomic (test row visible in 3 min post-DDL)
3. `DROP MATERIALIZED VIEW mv_signal_area_integral` → `DROP MATERIALIZED VIEW mv_signal_entropy` — reset all 6 UNION ALL streaming actors
4. Recreated both MVs from migration `20260501970000_alter_signal_tables_generic_cols.ts` DDL — fresh actors started, attention branch immediately current

### Final State (09:51 UTC)

| Axis | Rows | Last write |
|---|---|---|
| attention | 12 | 09:42 UTC ✅ |
| market | 4 | 09:23 UTC ✅ |
| emotion | 3 | 09:23 UTC ✅ |
| influence | 1 | 09:19 UTC ✅ |
| money | 1 | 2026-05-03 (timer pending) |
| request | 0 | R/PT1H — not yet fired |

**Convention added**: `rw-foreground-ddl-blocks-streaming-checkpoint` — フォアグラウンドDDL（大規模バックフィル）はストリーミングチェックポイントバリアを阻害する。INSERT rowcount=1 なのにデータが不可視な場合は `rw_ddl_progress` を確認し、DDL完了後に依存MVをDROP+RECREATEしてアクターをリセットする。

---

## Recent Completion: kotodama 0.3.35 — whois RDAP + CC entity cursor fixes (2026-05-05)

**Status**: ✅ **COMPLETE — 0.3.35 deployed, vertex_whois_record populating, CC cursors advancing**

**Scope**: Two ingest pipeline fixes + one RW query performance fix

### Fix 1: whois RDAP endpoint (rdap.iana.org → rdap.org)

**Root cause**: `_RDAP_IANA = "https://rdap.iana.org/domain/"` serves only TLD metadata per RFC 7484. SLDs like `cloudflare.com`, `github.com` return 404 → `_rdap_fetch` returned `{}` → all WHOIS records had empty registrar/nameservers/dates.

**Fix**: Changed to `_RDAP_BOOTSTRAP = "https://rdap.org/domain/"` which implements RFC 7484 bootstrap routing to the correct registrar endpoint per domain.

**Verified**: `_rdap_fetch("cloudflare.com")` → `registrar: "Cloudflare, Inc."`, nameservers, expiry dates, DNSSEC status all populated.

### Fix 2: whois INSERT CURRENT_DATE in Kotoba/Datomic prepared statement

**Root cause**: `INSERT INTO vertex_whois_record ... VALUES (..., CURRENT_DATE)` fails after psycopg3 auto-promotes the query to a server-side prepared statement (after 5 executions). Kotoba/Datomic error: `Failed to bind expression: CURRENT_DATE / Item not found: Invalid column: current_date`.

**Fix**: Extract date in Python: `created_date = ts[:10]` and pass as `%s::date` parameter.

**Convention**: `[[conventions]] rw-no-current-date-prepared-stmt` — applies to all `CURRENT_DATE` / `NOW()` / `CURRENT_TIMESTAMP` in psycopg3 hot-path write queries.

### Fix 3: CC entity extraction IS NULL scan → cursor-based pagination

**Root cause**: `WHERE domain IN (...) AND extracted_for_media_gamers IS NULL` caused full table scan on `vertex_page` (985M rows, column not in index INCLUDE) → 120s timeout on every invocation.

**Fix**: cursor-based pagination via new table `vertex_cc_entity_cursor`:
- `WHERE domain IN (...) AND vertex_id > %s ORDER BY vertex_id ASC LIMIT {int(limit)}` — uses existing domain index INCLUDE(vertex_id)
- Cursor persisted per domain in `vertex_cc_entity_cursor (domain PK, last_vertex_id, updated_at)`
- Wrap-around: when batch is empty after non-empty cursor, reset cursor to `""` and continue from beginning
- Migration: `30-graph/graph-schema/migrations/20260505120000_vertex_cc_entity_cursor.ts` (applied out-of-band via psql per ADR-2604241342)

**Performance**: 3s for 60 rows across 4 domains vs 120s timeout previously.

**Convention**: `[[conventions]] rw-large-table-no-is-null-scan`

### Deployment

- **Image**: `ghcr.io/etzhayyim/kotodama:0.3.35-202605050833-amd64` (built `docker buildx --platform linux/amd64 --no-cache --push`)
- **Helm**: `mitama-udf-pool` revision 346, `50-infra/vultr/mitama-udf-pool/values.yaml` updated
- **Hot-patch**: whois fix applied to running 0.3.34 pod via `kubectl exec | tee` while OrbStack was restarting — confirmed insert worked before 0.3.35 image was ready
- **Verified**: `vertex_whois_record` 18+ rows, `vertex_cc_entity_cursor` cursors advancing for all 4 domains (kuruma, media_anime, media_gamers, handotai)

**Conventions added**: `rw-rdap-bootstrap-endpoint`, `rw-no-current-date-prepared-stmt`, `rw-large-table-no-is-null-scan`

---

## Recent Completion: OWL QL/EL/DL/RL + SHACL Reasoning Schema + owl_reasoner.py fixes (2026-05-01, ADR-0044)

**Status**: ✅ **Schema live, BPMN deployed, owl_reasoner.py bugs fixed, kotodama 0.3.26 running**

**Scope**: 3-tier OWL/SHACL reasoning over the existing vertex_/edge_ graph.

**Schema (19 objects in Kotoba/Datomic)**:
- T-Box: `vertex_owl_class`, `vertex_owl_property`, `edge_owl_subclass`, `edge_owl_property_domain`, `edge_owl_property_range`, `edge_owl_property_chain`
- A-Box derived: `vertex_owl_inferred`, `edge_owl_derivation`, `vertex_owl_benchmark`
- SHACL: `vertex_shacl_shape`, `vertex_shacl_result`, `edge_shacl_violation`
- QL: `vertex_ql_rewrite`
- View: `v_rdf_triple` (pure VIEW over existing tables, no dual-write, ADR-0036 compliant)
- Streaming MVs: `mv_owl_rl_type_d1`, `mv_owl_rl_subproperty`, `mv_owl_rl_domain`, `mv_owl_rl_range`, `mv_owl_el_dl_diff`, `mv_shacl_violation`
- SQL UDFs (6): `owl_rl_is_type`, `owl_rl_check_functional`, `shacl_min_count`, `shacl_max_count`, `shacl_pattern`, `shacl_class`

**BPMN (Zeebe key=2251799825517334)**:
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/owl/owlReasonerBatch.bpmn` — R/PT1H timer-start
- Flow: `owl.el.classify` → `owl.ql.precompute` → [P7D gate] → `owl.dl.classify` → `owl.benchmark.compare`
- DL (HermiT) gated weekly via FEEL `(today() - date(last_dl_run_date)) >= duration("P7D")`

**owl_reasoner.py bug fixes (commit 8c011aeb593, 2026-05-01)**:
- Added `_load_all_profiles(conn)` — queries `DISTINCT profile FROM edge_owl_subclass` with fallback `["etzhayyim_core_v1"]`; all 3 task handlers now use it instead of hardcoded `["EL","ALL"]` etc.
- `_run_el_plus_plus` fallback changed from `except ImportError` → `except Exception` so Pellet/Java subprocess failure (JVM not in pod) correctly routes to `_run_el_naive`
- First fire verified in pod: 26 axioms loaded (profile=etzhayyim_core_v1), 16 triples inferred, written to `vertex_owl_inferred`

**Deployed**: `kotodama:0.3.26-202605011151-amd64` (helm rev 321). R/PT1H timer correctly classifies on each fire.

**Migrations**: `20260501140000_vertex_owl_reasoner_schema` + `20260501160000_seed_owl_tbox_etzhayyim_ontology` applied out-of-band (ADR-2604241342).

**EL++ vs DL comparison**: `mv_owl_el_dl_diff` Streaming MV tracks agreed/el_only/dl_only triples. `vertex_owl_benchmark.el_completeness_pct` = agreed/dl_inferred × 100.

---

## Recent Completion: Training Export Pipeline + HuggingFace Hub Phase D (2026-05-01)

**Status**: ✅ **COMPLETE — text + triple export to B2 verified, HF push wired, BPMN v2 live**

**Triple export verified (2026-05-01)**:
- `task_training_export_triple(dataset_name='etzhayyim-triples', shard_index=0)` → `{status:'ok', row_count:50000, b2_key:'training/v1/etzhayyim-triples/triples/shard-00000.jsonl.gz', has_more:True}`
- `v_training_triple`: 2,381,555 rows = ~48 shards at 50K/shard. B2 key scope confirmed (`etzhayyim-nats`, prefix `training/v1`).

**HuggingFace Hub push Phase D (commit dc707059974)**:
- `trainingExport.bpmn` updated: after triple loop completes → `training.push.huggingface` → End
- `task_training_push_huggingface()` in kotodama 0.3.26: reads `vertex_training_shard` (status=done), downloads from B2, uploads to `etzhayyim/etzhayyim-corpus` on HF Hub via `huggingface_hub.HfApi`
- K8s Secret `training-hf-creds` created (`HF_TOKEN` from 1Password `etzhayyim.hf/HF_TOKEN`, `HF_REPO_ID=etzhayyim/etzhayyim-corpus`)
- Keychain `etzhayyim.huggingface/HF_TOKEN` saved
- BPMN redeployed to Zeebe (key=2251799825707622) via F5 watcher

---

## Recent Fix: maps fill layer invisible at zoom ≥ 5.5 (2026-04-30)

**Status**: ✅ **COMPLETE — deployed maps.etzhayyim.com Worker 808128a4, commit b51c27053d0**

**Root cause**: `polygon_to_fill_earcut` in `kami-geo/src/mesh.rs` produces CCW-in-2D triangles. In the XZ ground plane (2D X→3D X, 2D Y→3D Z), these triangles have surface normal −Y (down). wgpu PBR pipeline uses `FrontFace::Ccw + cull_mode::Back` → downward-facing triangles are back-face culled → fill invisible.

**Why zoom 2–5.5 appeared to work**: `sync_projection_mode()` switches to Globe/Cosmic mode at low zoom, which calls `globe_polygon_to_fill_earcut` — a separate code path with correct winding. Flat mode (zoom ≥ ~5.5) uses `polygon_to_fill_earcut` — the broken path.

**Fix** (`kami-geo/src/mesh.rs`): swap `indices[1]↔indices[2]` per triangle after earcut in `polygon_to_fill_earcut` + roof section of `polygon_to_extrude_earcut`. Sidewalls use centroid-derived outward normals, unaffected. 9/9 unit tests pass.

**Closed migrations**: `maps-highzoom-fill-layer-invisible` (done), `maps-pds-graph-projection-all-spatial-labels` (done — stale, ADR-0036 Hyperdrive direct writes already in place).

---

## Recent Completion: generic.pds.dispatch K8s-internal routing (2026-04-30, ADR-2604282300)

**Status**: ✅ **Routing implemented + old CF-edge call sites eliminated. Image build pending (99915209ec9-amd64).**

**Problem**: Zeebe/UDF/LangGraph の `generic.pds.dispatch` が `https://atproto.etzhayyim.com` (CF edge) を経由していた。K8s Pod 内で完結すべき処理が CF WAF/ネットワークを踏む構造上の違反。

**Implementation (commit `39bd3166dbc`, ADR-2604282300 §Addendum 2026-04-30)**:
`zeebe_worker_main.py:task_generic_pds_dispatch` を 3-way K8s-internal routing に置換:
1. `app.bsky.*` / `chat.bsky.*` / `com.atproto.repo.*` → **C-path**: `insert_social_post_record(row, flush=False)` 直接 INSERT
2. `com.etzhayyim.*` → **bpmn-dispatcher ClusterIP**: `http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080` (`x-internal-trust` 認証)
3. その他 → legacy PDS HTTP フォールバック

**CF-edge call site 排除 (4箇所)**:
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/atproto/cronTick.bpmn` — `generic.http.fetch` + hardcoded URL → `generic.pds.dispatch` (`ea250eef838`)
- `ingest/arbitrage.py:_pds_post()` — direct `app.bsky.feed.post` HTTP → C-path (`ea250eef838`)
- `ingest/ads.py:_create_record()` — `com.atproto.repo.createRecord` HTTP → C-path (`ea250eef838`)
- `primitives/gov_ken.py` — 重複 `_pds_xrpc("app.bsky.feed.post")` × 3 削除 + `graph.follow` → C-path (`63c2699f4fa`)

**Helm values**: `zeebeWorker.bpmnDispatcher.{internalUrl,authSecretName,authSecretKey}` 追加。K8s Secret `bpmn-dispatcher-auth` key `internal-secret` を参照。

**Docs updated**: ADR-2604282300 §Addendum 2026-04-30、`deps.toml [[conventions]] generic-pds-dispatch-k8s-internal-routing`。

---

## Recent Fix: psycopg3 parameterized LIMIT + crawlAds BPMN first-deploy (2026-04-28)

**Status**: ✅ **Live — zeebe-worker helm rev 153, all 3 task families registered and verified**

**Root cause discovered**: psycopg3 v3 auto-promotes SQL to server-side Prepared Statements after 5 executions. Kotoba/Datomic rejects `LIMIT $N` in prepared statements with `"expects an integer after LIMIT, found non-const expression"`. Three kotodama primitives were silently failing on their 6th+ invocation.

**Fixes shipped (commit `91bfbf86435`)**:
- `onion_crawl._claim_stale_seeds` — `LIMIT %s` → `LIMIT {int(limit)}`
- `os_messaging_open_channels._claim_runs` — `LIMIT %s` → `LIMIT {int(max_runs)}`
- `public_malak_ads._claim_runs` — `LIMIT %s` → `LIMIT {int(max_runs)}`

**public-malak `crawlAds.bpmn` first-deploy (commit `ab4ac6a9adf`)**: Had BPMN 2.0 XSD ordering bug — `<timerEventDefinition>` appeared before `<outgoing>` inside `<startEvent>`. F5 watcher silently rejected it; BPMN was never deployed despite being in the repo. Fixed + added `Start_Manual` none-start event. Zeebe key=2251799818163684.

**Image deployment lessons (codified in `[[conventions]] kotodama-helm-image-deploy`)**:
- Mac arm64 `docker build` → arm64 image → `exec format error` on amd64 VKE nodes
- Use `docker buildx build --platform linux/amd64 --no-cache --push`
- `image.fullRef` pinned by a prior `--set` survives `--reuse-values` and silently overrides `image.tag`; must `--set "image.fullRef="` to clear

See: `deps.toml [[conventions]] rw-psycopg3-no-param-limit`, `[[conventions]] kotodama-helm-image-deploy`, `[[migrations]] kotodama-rw-limit-fix-20260428`.

---

## Recent Stabilization: yoro/PDS/AppView topology + γ2 cutover automation (2026-04-24/25, ADR-2604241038)

**Status**: ✅ **Topology refactor live, γ2 in 14-day observation (day 3/14)**

**Shipped via PR #1115 + #1117 + #1118 + #1120**:
- `bsky.etzhayyim.com` Layer-2 AppView Worker (`etzhayyim-appview` v `d085c7bf`)
  — first deploy. sh1n5h1x.etzhayyim.com postsCount 0 → 1476 fixed end-to-end
  (MV `mv_actor_social_stats` GROUP BY → `normalize_actor_did(repo)` +
  AppView Worker route claim + Kysely `.limit(1)` → `sql` template
  for RW MV LIMIT incompat).
- pg.Pool → `createKyselyDb(env.HYPERDRIVE)` sweep across 5 Workers
  (appview/{profile,feed,search} + chat + signal) per ADR-0007.
- γ2 one-button cutover automation: runbook + LaunchAgent
  (`com.etzhayyim.legacy-trust-tally.plist`, daily 09:17 local) + tally
  log + pre-written cleanup script + DRY_RUN-verified.
- 4 baseline pre-existing CI failures → **2 cleared** in 2 days.
- Out-of-band migration helper `30-graph/graph-schema/scripts/apply-pending.sh`
  + ADR-2604241342 codifies 4 failure modes of `pnpm db:migrate latest` on Kotoba/Datomic.

See: ADR-2604241038 (topology), ADR-2604241121, ADR-2604241342, `90-docs/260424-session-summary-topology-refactor.md`.

---

## Recent Fix: yoro social BPMN flush guard + kotodama 0.3.3 deploy (2026-04-30)

**Status**: ✅ **COMPLETE — platformPulse firing correctly, DB write verified**

**Root cause**: `yoro.social.{post,platformPulse,respondToMention,respondToFollow}GraphFallback` の 4 Zeebe task handler が `flush: bool = True` をデフォルト引数に持ち、`insert_social_post_record(row, flush=True)` → `cur.execute("FLUSH")` → `RW_DDL_GUARD` 例外で silent fail していた。2026-04-24 以降 `murakumo-platform-pulse-*` が `vertex_repo_record` に書き込まれなかった真の原因。

**Fix (commit `826d768d23e`)**: `yoro_social.py` — 4 関数の `flush: bool = True` → `flush: bool = False`。version bump 0.3.2 → 0.3.3。

**Deploy**: `kotodama:0.3.3-202604301414-amd64` → `mitama-udf/zeebe-worker` helm rollout。

---

## Recent Verification: yoro autonomous BPMN R/PT4H cadence (2026-04-25, ADR-2604240946)

**Status**: ✅ P2 outer loop live — `platformPulse` BPMN timer-start `R/PT4H` fires autonomously on Zeebe (4 consecutive fires 2026-04-24 11:42/15:42/19:42/23:42 UTC).

**Files**:
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/yoro/platformPulse.bpmn` — timer-start R/PT4H
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/yoro/respondToMention.bpmn`
- `50-infra/cloudflare/workers/atproto/src/yoro-reactive-dispatch.ts`

See: `90-docs/adr/2604240946-yoro-autonomous-actor-hybrid-loop.md` §Verification.

---

## Recent Stabilization: Murakumo fleet + RunPod retirement (2026-04-27)

**Status**: ✅ `murakumo.etzhayyim.com` fleet (10 mac mini Ollama backends + judah:4000 LiteLLM) を canonical inference path に復帰、RunPod Serverless 暫定経路を退役。

**Root cause**: CF Zero Trust tunnel `ae341542` (`murakumo-fleet`) の remote ingress 設定で `murakumo-serve.etzhayyim.com` が欠落。

**Fix**: CF Zero Trust API で tunnel ingress に `{"hostname":"murakumo-serve.etzhayyim.com","service":"http://localhost:4000"}` 追加 (config version 32 → 33)。PDS Worker から RunPod secrets DELETE。10 fleet ノードで legacy Nomad プロセスを停止。

---

## Recent Stabilization: PDS commit content-PK (2026-04-21, ADR-0041)

**Problem**: 10-parallel `createWork` → 1/10 persisted (90% silent drop). Root cause: `vertex_repo_commit.vertex_id = ${repo}:seq:${seq}` PK collided because different CF isolates read different `MAX(seq)` and independently computed clashing seqs.

**Fix**: Content-addressed PK `${repo}:${collection}:${rkey}:${action}`. **Result**: 10-parallel burst 1/10 → 10/10 persistence (100% end-to-end).

See: `90-docs/adr/0041-pds-commit-content-addressed-pk.md`, `90-docs/260421-pds-throughput-tuning.md`.

---

## Recent Deployment: PR #1032 (2026-04-18/19)

**Status**: ✅ Production Live
**Migrations**: 40 new timestamp-based migrations (20260415–20260417)
**Features**: Orbital systems graph, flight operations, legal-entity ingest, hospitality domain, ongakuka music, 649 classification concordances
**Outcome**: Staging (6h, zero incidents) → Production (5h, zero incidents), 24h monitoring clean

See `90-docs/260417-*` for runbook, monitoring, post-deploy report.

---

## Recent Completion: maps Transit Pipeline Phase 2+3 bring-up (2026-04-28, ADR-2604280900)

**Status**: ✅ **Production live (Phase 2+3 gated scaffold)**

**Blocking fixes shipped**:
- BPMN re-deploy loop: `_deployed_in_flight: set[str]` guard in `dispatcher_main.py watcher_loop()`.
- B2 credentials: `maps-bulk-ingest-credentials` Secret patched from Keychain `etzhayyim.b2`.
- GTFS-JP feed index: `GTFS_JP_FEED_INDEX_URL=file:///config/gtfs-jp.json` via ConfigMap mount.
- `maps-tile-server-deploy` migration marked **superseded** (PMTiles/R2 dead, replaced by `tileGeoJson` XRPC).

**First production dumps (2026-04-28)**: `bulkRefreshFerryRoutes` 5,393 SeaRoutes + `bulkRefreshOpenflights` 74,790 rows.

See: `90-docs/adr/2604280900-maps-transit-pipeline-gtfs-rt.md`

---

## Recent Completion: maps Sentinel Phase 2 (2026-04-28, ADR-2604271800)

**Status**: ✅ **Phase 2 COMPLETE** — `maps_sentinel.py` rewrite + BPMN v2 XML cutover to typed tables (`vertex_satellite_scene` / `vertex_satellite_analysis`). 36/36 tests passing.

See: `90-docs/adr/2604271800-maps-l8-sentinel-pipeline.md`

---

## Recent Completion: Well-Becoming BPMN pipeline + Lean 4 formal proof (2026-04-29, ADR-2604291800)

**Status**: ✅ **COMPLETE — 5 BPMNs live in Zeebe, formal proof compiled**

**Scope**: Well-Becoming Spirit 目的関数の BPMN-as-actor 実装 (ADR-0056) + Lean 4 機械検証済み公理

**5 BPMNs deployed to Zeebe**:

| BPMN process ID | Zeebe key |
|---|---|
| `wellbecoming_process_mining` | `2251799816309098` |
| `wellbecoming_detect_bottleneck` | `2251799816311150` |
| `wellbecoming_proactive_connect` | `2251799816311147` |
| `wellbecoming_floor_violation_alert` | `2251799816311153` |
| `wellbecoming_agent_loop` | `2251799816311145` |

**Lean 4 formal proof**: `90-docs/proof/WellBecoming.lean` (Lean 4.14.0 + Mathlib4 v4.14.0) — 非負性・有界性・床制約・Spirit優位性・ボトルネック支配定理・Shannon双対性の機械検証済み。

See: `90-docs/adr/2604291800-well-becoming-formal-model.md`, `90-docs/adr/2604291800-well-becoming-spirit-objective-function.md`

---

## Recent Completion: Public Malak ad artifact pipeline + smoke monitoring (2026-05-07)

**Status**: ✅ **Production live** — Public Malak BPMN/Job path now persists HTML and HAR-lite crawl evidence to Backblaze B2 S3-compatible storage and verifies the public read path continuously.

**Scope shipped**:
- Backblaze B2 application keys saved in 1Password and projected to `mitama-udf/public-malak-r2-creds`.
- `public-malak-zeebe-worker` and `bpmn-dispatcher` deployed with B2 artifact env.
- Public appview serves `/artifacts/html/:cid` and `/artifacts/har/:cid` from S3 fallback with `x-artifact-store: s3`.
- `listSnapshots` ordering fixed to `ORDER BY scraped_at DESC, vertex_id DESC`.
- Helm test `public-malak-smoke` and hourly CronJob `public-malak-smoke-cron` validate write → RW snapshot → `listSnapshots` → public HTML/HAR routes.
- Smoke logic moved from Helm inline Python into `kotodama.public_malak_smoke`; chart calls `python -u -m kotodama.public_malak_smoke`.
- Optional `PrometheusRule` template added but disabled until the cluster has `monitoring.coreos.com/PrometheusRule`.

**Live verification**:
- Helm revision `444`.
- Image: `ghcr.io/etzhayyim/kotodama:public-malak-smoke-module-e7580bb1bd08-20260507052544-amd64`.
- `helm -n mitama-udf test mitama-udf-pool --timeout 1200s` succeeded.
- CronJob-derived manual job succeeded with HTML/HAR `200`, `store=s3`, and `listSnapshots.status=200`.

See: `90-docs/260507-public-malak-smoke-runbook.md`.

---

## Repo Record Minimization Follow-Up (2026-05-07)

`vertex_repo_record` is now treated as the Kotoba/Datomic hot mirror for
`app.bsky.feed.post` only. Non-post state is projected to typed graph tables:

- `app.bsky.actor.profile` reads use `vertex_profile`.
- follows use `edge_follows`.
- cohort evidence writes/read MVs use `vertex_cohort_evidence`.
- Yoro worker, collector, PDS tick, graph consumer, OS, gov, projector,
  wellbecoming, kotodama, murakumo, organizer, handotai, and related state use
  domain `vertex_*` tables.

`30-graph/deps.toml` was updated for the live Tier C additions
`vertex_cohort_evidence` and `vertex_agent_development_document`.

Follow-up guard: `70-tools/scripts/lint/repo-record-social-post-only.mjs` is
wired into the root `build` script. New runtime direct writes to
`vertex_repo_record` must be guarded for `app.bsky.feed.post`; profile, social
graph, cohort, and domain state must use typed graph tables.

PDS create guard: `com.atproto.repo.createRecord` now rejects non-post
collections before repo write. `com.atproto.repo.applyWrites` rejects non-post
create/update entries, while delete-only legacy cleanup remains available.

Private graph write helper: `@etzhayyim/kotodama-host-sdk` now exports
`writePrivate()`. App handlers can write non-social state directly to typed
`vertex_*` / `edge_*` tables over Kysely, and the helper rejects repo-public
tables such as `vertex_repo_record`.

Repo-record legacy audit: `pnpm audit:repo-record-allowlist` now reports
`vertex_repo_record` collections against the social-post allowlist. Non-post
collections are reported as legacy/grandfathered findings and can be exported
as JSON for targeted graph migration planning.

Repo-record guard extension: `lint:repo-record-social-post-only` now also
checks graph migrations and gov generators for `write_table_allowlist` /
`writeTableAllowlist` regressions. Gov BPMN allowlists remove
`vertex_repo_record` and use typed gov graph tables.

Repo-record legacy materialization: grandfathered `actorManifest` rows in
`vertex_repo_record` are copied into `vertex_gov_actor_manifest` so gov domain
state is available from the typed graph table while keeping the historical repo
records intact.

## 2026-05-07 — Web Marketing Proposal Agent (webmk.etzhayyim.com) — ① of 5

Introduced **LangGraph agent loop pattern** (ADR-2605072000) and implemented the
first of five marketing business models: `webmk.etzhayyim.com`.

**ADR**: `90-docs/adr/2605072000-langgraph-agent-loop-pattern.md`
- LangGraph handles intra-job state transitions (≥3 LLM steps with branching).
- PyZeebe owns durable orchestration (retries, timers, escalation).
- No LangGraph checkpointer — durability via `vertex_webmk_proposal` rows.
- New deps: `langchain-anthropic>=0.3.0`, `resend>=2.0.0`.

**Actor**: `did:web:webmk.etzhayyim.com` / nanoid `wbmk0001`

**Lexicons** (`00-contracts/lexicons/com/etzhayyim/apps/webmk/`):
- `createProposal` — trigger LangGraph loop, returns proposalId immediately
- `getProposal` — fetch proposal status + strategyJson + copyMarkdown
- `listProposals` — paginated list with status filter
- `deliverProposal` — re-deliver completed proposal via Resend

**LangGraph nodes** (research → competitors → strategy → copy → quality_gate → store):
- `research_company`: Claude claude-sonnet-4-6 extracts company context from URL+industry
- `analyze_competitors`: 3-competitor diff + opportunity gap
- `generate_strategy`: full JSON strategy (channels, milestones, ROI estimate)
- `generate_copy`: Markdown ad copy (hero headlines, SNS, email, Google Ads)
- `quality_gate`: scores 0.0–1.0 on specificity/actionability/creativity/completeness, retries once if <0.7
- `store_proposal`: INSERT into `vertex_webmk_proposal` (Kotoba/Datomic)

**BPMN** (`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/webmk/`):
- `createProposal.bpmn`: RunAgentLoop → DeliverEmail → (optional) CreateAdCampaign
- `deliverProposal.bpmn`: re-deliver flow

**PyZeebe job types**:
- `webmk.run_proposal_agent` — LangGraph loop (180s timeout, 2 retries)
- `webmk.deliver_via_resend` — Resend transactional email (60s, 3 retries)
- `webmk.create_ad_campaign` — XRPC to ads.etzhayyim.com createCampaign (30s, 2 retries)

**Kotoba/Datomic migration**: `30-graph/graph-schema/migrations/20260507800000_vertex_webmk_tables.ts`
- `vertex_webmk_client`, `vertex_webmk_proposal`, `edge_webmk_campaign_link`

**Integration**: `ads.etzhayyim.com` optional campaign creation → `edge_webmk_campaign_link`.
Proposals non-federable (internal, sensitivity_ord=2).

---

## 2026-05-07 — Newsletter Factory (newsletter.etzhayyim.com) — ② of 5

**Actor**: `did:web:newsletter.etzhayyim.com` / nanoid `nwsl0001`

**Schedule**: Weekly BPMN timer (Tue 09:00 JST, `0 0 * * 2`). On-demand via `createCampaign` XRPC.

**Lexicons** (`00-contracts/lexicons/com/etzhayyim/apps/newsletter/`):
- `createCampaign` — trigger on-demand curation + send
- `getCampaign` — fetch campaign status + subjectLine + bodyHtml + qualityScore
- `listCampaigns` — paginated list with status/cohort filter
- `addSubscriber` — register subscriber (email, name, cohortName — Tier 3 PII)
- `sendCampaign` — trigger batch send for a stored campaign

**LangGraph nodes** (ingest → filter → rank → draft → personalize → quality_gate → store):
- `ingest_signals`: queries `vertex_news_article` + `vertex_narou_chapter` (last 7d)
- `filter_relevant`: Claude relevance scoring per topic + cohortName
- `rank_content`: Claude engagement potential ranking (top 10)
- `draft_newsletter`: Claude subject line + HTML body
- `personalize`: per-cohort subject variants
- `quality_gate`: score ≥0.7 → proceed, else retry once back to `draft_newsletter`
- `store_campaign`: INSERT into `vertex_newsletter_campaign`

**BPMN** (`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/newsletter/`):
- `weeklySend.bpmn`: timer `0 0 * * 2` → RunCurationAgent → SendViaResend → (optional) CreateSponsorSlot
- `sendCampaign.bpmn`: on-demand triggered send

**PyZeebe job types**:
- `newsletter.run_curation_agent` — LangGraph loop (180s, 2 retries)
- `newsletter.send_via_resend` — Resend batch per-subscriber (120s, 3 retries)
- `newsletter.create_sponsor_slot` — XRPC to ads.etzhayyim.com createCampaign (30s, 2 retries)

**Kotoba/Datomic migration**: `30-graph/graph-schema/migrations/20260507810000_vertex_newsletter_tables.ts`
- `vertex_newsletter_subscriber` (sensitivity_ord=3, Tier 3 PII: email/name/cohortName)
- `vertex_newsletter_campaign` (subjectLine, bodyHtml, qualityScore, recipientCount, sentAt)
- `vertex_newsletter_engagement` (open/click events from Resend webhook, no PII)
- `edge_newsletter_sent` (campaign → subscriber, resend_email_id)

**subscribeRepos** (kotodama.jsonld triggers):
- `com.etzhayyim.apps.news.article` — fresh articles from news.etzhayyim.com
- `com.etzhayyim.narou.chapter` — chapters from narou.etzhayyim.com

**Governance**: Subscriber PII (email) is Tier 3 (ADR-0018). Never logged or included in AT Repo records. Cohort-first grouping. GDPR Art 17 cascade purge applies.

## 2026-05-07 — Sales Outreach Automation (outreach.etzhayyim.com) — ③ of 5

**Actor**: `did:web:outreach.etzhayyim.com` · nanoid `otch0001`
**ADR**: ADR-2605072000 (LangGraph agent loop pattern)

### Files created

| Path | Purpose |
|---|---|
| `00-contracts/lexicons/com/etzhayyim/apps/outreach/createSequence.json` | Start outreach sequence |
| `00-contracts/lexicons/com/etzhayyim/apps/outreach/getSequence.json` | Get sequence status |
| `00-contracts/lexicons/com/etzhayyim/apps/outreach/listSequences.json` | List sequences |
| `00-contracts/lexicons/com/etzhayyim/apps/outreach/addProspect.json` | Register prospect (Tier 3 PII) |
| `00-contracts/lexicons/com/etzhayyim/apps/outreach/addDnc.json` | Add to DNC list |
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/outreach/outreachSequence.bpmn` | Multi-step sequence flow |
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/outreach/replyDetected.bpmn` | Reply correlation sub-flow |
| `60-apps/etzhayyim-project-outreach/appview/outreach-otch0001/src/app.ts` | Thin edge CF Worker |
| `60-apps/etzhayyim-project-outreach/appview/outreach-otch0001/wrangler.jsonc` | Routes |
| `60-apps/etzhayyim-project-outreach/appview/outreach-otch0001/kotodama.jsonld` | subscribeRepos config |
| `60-apps/etzhayyim-project-outreach/CLAUDE.md` | Runbook |
| `60-apps/etzhayyim-project-outreach/actor-manifest.jsonld` | Actor declaration |
| `30-graph/graph-schema/migrations/20260507820000_vertex_outreach_tables.ts` | 5 tables |
| `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/outreach_worker_main.py` | Python Zeebe worker |

### Files updated

- `deps.toml` — `[[mitama_actors]]` entry for outreach
- `40-engine/kotoba/crates/kotoba-kotodama/py/pyproject.toml` — `kotodama-outreach-worker` script
- `90-docs/session-history.md` — this entry

### LangGraph nodes (intra-job, outreach.run_research_agent)

1. `research_prospect` — fetch prospect context from vertex_outreach_prospect + structured data
2. `draft_opening` — LLM personalized cold email (subject + body, ≤120 words)
3. `quality_gate` — score for relevance/length/personalization (threshold 0.75)
4. `store_step` — INSERT to vertex_outreach_step (no onConflict, PK implicit)
- Conditional edge: retry once (draft_opening) if score < 0.75

### PyZeebe job types

| Type | Timeout | Purpose |
|---|---|---|
| `outreach.check_dnc` | 15s | DNC gate — abort if email on vertex_outreach_dnc |
| `outreach.run_research_agent` | 180s | LangGraph loop |
| `outreach.send_via_resend` | 60s | Resend send per step (step 1 + step 2 follow-up) |
| `outreach.correlate_reply` | 30s | Correlate gmail/m365Ingest reply to active sequence |
| `outreach.create_sponsor_slot` | 30s | Optional ads.etzhayyim.com createCampaign |

### BPMN flow (outreachSequence.bpmn)

Start → CheckDnc → DncGateway:
  - isDnc=true → DncEnd
  - isDnc=false → RunResearchAgent → SendEmail → WaitReply(3d) → ReplyGateway:
    - replied=true → RepliedEnd
    - replied=false → FollowUp → CreateSponsorSlot → End

### Kotoba/Datomic tables

| Table | sensitivity_ord | Key columns |
|---|---|---|
| `vertex_outreach_prospect` | 3 | email, prospect_name, title, company, cohort_name |
| `vertex_outreach_sequence` | 0 | sequence_id, prospect_id, goal, current_step, reply_detected |
| `vertex_outreach_step` | 0 | sequence_id, step_number, subject_line, body_text, quality_score |
| `vertex_outreach_dnc` | 0 | email (UNIQUE), reason |
| `edge_outreach_sent` | 3 | sequence_id, prospect_id, step_number, resend_email_id |

### subscribeRepos triggers (kotodama.jsonld)

- `com.etzhayyim.apps.gmail.message` — reply detection from Gmail ingest
- `com.etzhayyim.apps.m365Ingest.email` — reply detection from M365 ingest

### Governance

Prospect PII (email, name, title, company) is Tier 3 (ADR-0018, sensitivity_ord=3).
DNC table checked before every send. GDPR Art 17 cascade purge applies.
Reply detection via existing gmail/m365Ingest actors — no new inbound infra.

## 2026-05-07 — Competitive Intelligence Dashboard (compintel.etzhayyim.com) — ④ of 5

**Actor**: `did:web:compintel.etzhayyim.com` · nanoid `cpti0001`
**ADR**: ADR-2605072000 (LangGraph agent loop pattern)

### Files created

| Path | Purpose |
|---|---|
| `00-contracts/lexicons/com/etzhayyim/apps/compintel/trackCompetitor.json` | Add competitor |
| `00-contracts/lexicons/com/etzhayyim/apps/compintel/getSnapshot.json` | Latest intelligence |
| `00-contracts/lexicons/com/etzhayyim/apps/compintel/listCompetitors.json` | List competitors |
| `00-contracts/lexicons/com/etzhayyim/apps/compintel/getAlert.json` | High-severity alerts |
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/compintel/weeklyRefresh.bpmn` | Monday 08:00 JST refresh |
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/compintel/trackCompetitor.bpmn` | Initial deep research |
| `60-apps/etzhayyim-project-compintel/appview/compintel-cpti0001/` | CF Worker |
| `30-graph/graph-schema/migrations/20260507830000_vertex_compintel_tables.ts` | 4 tables |
| `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/compintel_worker_main.py` | Python Zeebe worker |

### LangGraph nodes (compintel.run_research_agent)

fetch_signals → analyze_pricing → analyze_product → analyze_hiring → score_threat → store_snapshot

### PyZeebe job types

| Type | Timeout | Purpose |
|---|---|---|
| `compintel.run_research_agent` | 300s | LangGraph multi-dimension research (batch or single) |
| `compintel.score_threats` | 60s | Diff snapshots, emit alerts for threat_score ≥ 0.7 |
| `compintel.send_digest` | 60s | Resend weekly digest for high-severity alerts |

### Tables: vertex_compintel_competitor, vertex_compintel_snapshot, vertex_compintel_alert, edge_compintel_snapshot. No PII.

## 2026-05-07 — Personalized Content Engine (contentengine.etzhayyim.com) — ⑤ of 5

**Actor**: `did:web:contentengine.etzhayyim.com` · nanoid `cten0001`
**ADR**: ADR-2605072000 (LangGraph agent loop pattern)

### Files created

| Path | Purpose |
|---|---|
| `00-contracts/lexicons/com/etzhayyim/apps/contentengine/generateContent.json` | Generate for cohort |
| `00-contracts/lexicons/com/etzhayyim/apps/contentengine/getContent.json` | Get content by ID |
| `00-contracts/lexicons/com/etzhayyim/apps/contentengine/listContent.json` | List with filters |
| `00-contracts/lexicons/com/etzhayyim/apps/contentengine/registerCohortProfile.json` | Register cohort profile |
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/contentengine/generateContent.bpmn` | Generate + sponsor flow |
| `60-apps/etzhayyim-project-contentengine/appview/contentengine-cten0001/` | CF Worker |
| `30-graph/graph-schema/migrations/20260507840000_vertex_contentengine_tables.ts` | 2 tables |
| `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/contentengine_worker_main.py` | Python Zeebe worker |

### LangGraph nodes (contentengine.run_content_agent)

load_cohort_profile → match_sources → draft_content → rank_variants → quality_gate → store_content
- Conditional edge: retry once (draft_content) if quality_score < 0.65

### PyZeebe job types

| Type | Timeout | Purpose |
|---|---|---|
| `contentengine.run_content_agent` | 180s | LangGraph personalization loop |
| `contentengine.create_sponsor_slot` | 30s | Optional ads.etzhayyim.com createCampaign |

### Tables: vertex_contentengine_cohort_profile, vertex_contentengine_content. No PII (sensitivity_ord=0, ADR-0018 cohort-first).

### subscribeRepos: com.etzhayyim.apps.news.article + com.etzhayyim.narou.chapter (signals for personalization)

## 2026-05-07 — All 5 Business Models Complete

| # | Actor | Domain | Nanoid | Status |
|---|---|---|---|---|
| ① | webmk | webmk.etzhayyim.com | wbmk0001 | ✅ |
| ② | newsletter | newsletter.etzhayyim.com | nwsl0001 | ✅ |
| ③ | outreach | outreach.etzhayyim.com | otch0001 | ✅ |
| ④ | compintel | compintel.etzhayyim.com | cpti0001 | ✅ |
| ⑤ | contentengine | contentengine.etzhayyim.com | cten0001 | ✅ |

## 2026-05-07 — Recruit Cohort Matching: listMatchDecisionEvents + matchStats

### Lexicons created / confirmed

| File | Type | Purpose |
|---|---|---|
| `00-contracts/lexicons/com/etzhayyim/apps/recruit/matchStats.json` | query | Cohort-first matching stats (candidateCount / decisionEventCount) |
| `00-contracts/lexicons/com/etzhayyim/apps/recruit/listMatchDecisionEvents.json` | query | List decision events per proposal (cohort-first, PII-free) |
| `00-contracts/lexicons/com/etzhayyim/apps/recruit/getMatchProposal.json` | query | Single proposal retrieval by proposalId |

### actor-manifest.jsonld additions

- `matchStats` pipeline: two-step graph query → `count(m) AS candidateCount` + `count(e) AS decisionEventCount`
- `proposeCohortMatch` pipeline: extended with `MERGE (p)-[:FOR_POSTING]->(jp)` + `MERGE (p)-[:FOR_COHORT]->(tc)` edge creation
- `decideMatchProposal` pipeline: extended with inline `CREATE (e:RecruitMatchDecisionEvent {...}) SET e.privacyMode = 'cohort-first'`
- `listMatchDecisionEvents` pipeline: `MATCH (e:RecruitMatchDecisionEvent)` query with proposalId/proposalState filters

### Tests: 7/7 ✅

- `20260507770000_recruit_cohort_matching.test.ts` — 4 tests
- `20260507860000_recruit_real_job_ingest.test.ts` — 3 tests

## 2026-05-07 — Recruit Real Job Ingest (Phase A)

### Files

| Path | Purpose |
|---|---|
| `30-graph/graph-schema/migrations/20260507860000_recruit_real_job_ingest.ts` | ADD COLUMN source_homepage + 2 indexes on vertex_job_posting |
| `00-contracts/lexicons/com/etzhayyim/apps/recruit/ingestJobPostings.json` | Public-postings-only ATS ingest (greenhouse/lever/ashby allowlist) |
| `70-tools/scripts/recruit-ingest-ats-direct.mjs` | Idempotent ATS direct ingest (PROHIBITED_HOST_FRAGMENTS gate, WHERE NOT EXISTS, DRY_RUN) |

### Compliance

- `PROHIBITED_HOST_FRAGMENTS` + `assertNotProhibited()` block LinkedIn/Indeed/Wantedly etc.
- `WHERE NOT EXISTS` ensures idempotent upsert
- PII-free: no candidateEmail / candidatePhone fields

## 2026-05-07 — Recruit Real Job Ingest Worker + Live Smoke

### Runtime

| Path | Purpose |
|---|---|
| `50-infra/k8s/recruit-job-ingester/` | Dockerfile + Kustomize Deployment/Service/CronJob for internal XRPC ingest worker |
| `70-tools/scripts/recruit-job-ingest-worker.mjs` | Long-running HTTP worker: `/healthz`, `/readyz`, `/xrpc/com.etzhayyim.apps.recruit.ingestJobPostings` |
| `70-tools/scripts/recruit-run-job-ingest.mjs` | Operational wrapper: DB readiness, optional migration, ATS ingest, run history |
| `30-graph/graph-schema/migrations/20260507860000_recruit_real_job_ingest.ts` | `source_homepage` + `vertex_recruit_job_ingest_run` |

### Live smoke

- Required live schema confirmed: `vertex_job_posting.source_homepage`, `vertex_recruit_job_ingest_run`.
- Command used: `pnpm run recruit:jobs:ingest -- --platform lever --limit 1 --batch-size 1 --skip-migrate --ignore-checkpoint --allow-unanchored`.
- Result: `inserted=1`, latest run `status=succeeded`.
- Observed live counts after smoke: `ashby=176`, `greenhouse=6877`, `lever=21`.

### Operational notes

- Full live migration/index creation can run long; smoke used `--skip-migrate` after required DDL was present.
- `ignoreCheckpoint` is now wired through Lexicon → actor-manifest → worker → runner → direct ingest for smoke/replay.
- Broad `vertex_legal_entity` fuzzy scans timed out on live RW; default strict mode skips unanchored rows unless `RECRUIT_ENABLE_LIVE_ANCHOR_LOOKUP=1`. `allowUnanchored` remains explicit.

## 2026-05-07 — Myco-Yeast Organism Workers: kabi / kobo / kinoko / hakkou (Phase B)

**ADR**: ADR-2605071200 (Myco-Yeast Artificial Organism, 日本語 alphabet naming)

### New Python workers

| Worker | Layer | Task types |
|---|---|---|
| `kabi_worker_main.py` | カビ (mycelium network) | extendHypha / pruneHypha / fusionProbe / getNutrientFlow |
| `kobo_worker_main.py` | 酵母 (individual agents) | spawnAgent / budAgent / sporulate / ferment / germinate |
| `kinoko_worker_main.py` | キノコ (PoNF consensus) | checkFlowThreshold / formBlock / getBlock |
| `hakkou_worker_main.py` | 発酵 (fermentation pipeline) | startFerment / llmTransform / finalizeFerment |

### Helm / infra

- `organism-workers.yaml` — 7 Deployments: koke / saikin / ki / hakkou / kabi / kinoko / kobo
- `values.yaml` — organismWorkers.{hakkou,kabi,kinoko,kobo}.replicas = 1 added
- `pyproject.toml` — 4 new `[project.scripts]` entries

### Pure-logic tests: 18/18 ✅

| Test file | Count | Coverage |
|---|---|---|
| `test_kobo_worker_pure.py` | 10 | bud_agent / sporulate / germinate quorum logic |
| `test_hakkou_worker_pure.py` | 8 | create_ferment_record / llm_transform / finalize_ferment |

## 2026-05-13 — CRM Open LEI Bridge Review Loop Closed

**ADR**: ADR-2605130900 (`90-docs/adr/2605130900-crm-open-lei-bridge-review-loop.md`)

### Implemented

| Area | State |
|---|---|
| Schema | CRM Open LEI bridge + review queue migrations added and applied live |
| MCP | `openLei.crm.bridge.{query,resolve,review,autoreview,enrich,reviewQueue,submitEvidence}` |
| Lexicons | 9 CRM LEI lexicons under `00-contracts/lexicons/com/etzhayyim/apps/crm/` |
| Review loop | Candidate rejection, evidence submission, selected-LEI verification |

### Live closing state

- Verified CRM-to-LEI edges: 8.
- Remaining Indian lawfirm review rows: 5.
- Review rows with evidence attached: `azb-2026`, `luthra-2026`, `nishith-desai-2026`, `sandbox-nishith`, `sr-2026`.
- `sr-2026` has multiple normalized exact `S R ASSOCIATES` candidates and must be selected manually.
- `pnpm db:drift` from `30-graph/graph-schema`: OK, no drift detected.

### Resume

Query review queue with `openLei.crm.bridge.query mode=review`. Apply human decisions with `openLei.crm.bridge.reviewQueue action=verify_selected_lei` when a selected LEI is confirmed.

## 2026-05-14 — Shinshi Review Generation Quality Loop Session Close

**ADR**: ADR-2605141500 (`90-docs/adr/2605141500-shinshi-review-generation-quality-loop.md`)

### Committed

| Commit | Purpose |
|---|---|
| `8e595f6da6a` | Added `reviewGenerationBatch`, deterministic review scoring, scene quality gate retry/quarantine wiring, MCP/XRPC registration, lexicon, generated contract, and smoke coverage. |
| `f4d5e741653` | Added optional VLM/aesthetic review gate with `includeAesthetic` / `aestheticLimit`, downgrade-only merge semantics, contract updates, server schema `0.2.10`, and tests. |

### Verification

- `node scripts/generate-shinshi-mcp-contract.mjs`
- `node scripts/check-api-surface.mjs`
- `npm run check` in the Shinshi Svelte appview: 0 errors, existing 27 warnings
- `.venv-test/bin/python -m pytest tests/test_smoke.py -q`: 16 passed

### Closing State

Branch `240424-open` is ahead of `origin/240424-open` by the Shinshi/deps commits made in this session. Remaining dirty worktree entries at close are unrelated legal-corpus, animeka, naphtha, tooling, infra values, and OpenZeppelin submodule changes; they were intentionally left untouched.
