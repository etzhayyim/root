---
id: adr-2604250900-gameka-bpmn-langgraph-game-studio
title: "ADR: gameka.etzhayyim.com — autonomous game studio actor on BPMN + LangGraph substrate"
status: proposed
doc_type: adr
topic: agentic-actor-game-studio
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - gameka-actor-placement
  - gameka-bpmn-process-suite
  - gameka-langgraph-graph-definition
  - kami-engine-codegen-pipeline
  - per-game-sub-did-issuance
related:
  - adr-0056-bpmn-as-actor
  - adr-2604250836-langgraph-as-zeebe-servicetask
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0046
  - adr-0019-atproto-native-identifier-topology
  - adr-0023-auth-shannon-optimal-4-layer
  - adr-0029-did-etzhayyim-method-specification
  - adr-2604241038-yoro-pds-ideal-topology
  - adr-2604241500-cad-bim-per-game-wasm-topology
  - adr-0031-kami-vrm-three-free-topology
supersedes: []
superseded_by: []
---

# Goal

`gameka.etzhayyim.com` を、ゲーム企画から WASM build、QA、公開、フォロー反応まで
自律的に回す **agentic actor** として、ADR-0056 (BPMN-as-actor) と
ADR-2604250836 (LangGraph as Zeebe ServiceTask) の上に置く。

# Scope

- 配置: gameka actor がどの runtime に乗るか
- 形状: ゲーム生成 pipeline の BPMN process 分割
- LangGraph: 企画 deliberation の graph 定義
- DID: per-game sub-DID 発行ポリシー
- 永続: Kotoba/Datomic vertex / B2 artifact / AT Repo record の責務分担

実装の手順 (P0–P5 rollout) は本 ADR が確定後に別 runbook に切り出す。

# Executive Summary

`gameka.etzhayyim.com` は **新規 Worker を建てない**。`bpmn.etzhayyim.com` 上に
`INSERT 2 rows` (ADR-0056 規約) で 5 BPMN process を登録し、企画 step
だけを `generic.langgraph.run` (ADR-2604250836) の ServiceTask として
LangGraph に委譲する。生成は `kami-engine` の `kami-app-{slug}` crate
template + `wasm-pack` build、公開は per-game sub-DID
(`did:web:gameka.etzhayyim.com:game:{slug}`) + `app.bsky.feed.post`。
trend scan からの自律企画 cadence は yoro と同形の R/PT2H timer-start。

# Decision

## D1. Actor placement

| 項目 | 採用 |
|---|---|
| AT 15-Layer (ADR-2604231811) | Layer 10 Actor Worker (etzhayyim ext.) |
| Worker host | `bpmn.etzhayyim.com` (Zeebe + pyzeebe)、新 Worker 不要 |
| Primary DID | `did:web:gameka.etzhayyim.com` (ADR-0019, did:web sub-actor path) |
| NSID prefix | `com.etzhayyim.gameka.*` |
| Persistence (ADR-0036) | domain write = Worker-direct Hyperdrive、social = `sdk.pds.dispatch` |
| Inference | Murakumo MLX → RunPod fallback (yoro `infer.ts` 同経路) |
| Game build | `kami-engine` `kami-app-{slug}` Rust crate + `wasm-pack` (Vultr build runner) |
| Hosting | 既存 `game-play-uploader` Worker (`game-play.etzhayyim.com/{slug}`) |
| Playtest | 既存 `playwright` actor を headless WebGPU runner として再利用 |

## D2. Multi-DID topology

```
did:web:gameka.etzhayyim.com                       # primary (controller agent)
├── did:web:gameka.etzhayyim.com:game:{slug}       # 1 game = 1 sub-DID (Title)
└── did:web:gameka.etzhayyim.com:critic:playtest   # QA/critic agent
```

per-game sub-DID は ADR-0023 multi-key rotation + host-sdk did.json
auto-serve 経路に乗せる。各 sub-DID は独立に social post でき、
media-gamers の game DID と同形の per-title timeline を形成する。

## D3. NSID surface (`00-contracts/lexicons/com/etzhayyim/apps/gameka/`)

| NSID | type | 役割 |
|---|---|---|
| `com.etzhayyim.gameka.proposeGame` | procedure | brief → `gameSpec` (LangGraph deliberation) |
| `com.etzhayyim.gameka.generateGame` | procedure | spec → kami-app crate scaffold + WASM build |
| `com.etzhayyim.gameka.playtestGame` | procedure | headless WebGPU QA → score |
| `com.etzhayyim.gameka.publishGame` | procedure | sub-DID 発行 + B2 upload + social post |
| `com.etzhayyim.gameka.tickStudio` | timer-start (R/PT2H) | 自律企画 cadence |
| `com.etzhayyim.gameka.respondToPlaytest` | procedure | playtest feedback → patch 判断 |
| `com.etzhayyim.gameka.gameSpec` | record | 仕様 (genre/mechanic/scene/budget) |
| `com.etzhayyim.gameka.gameTitle` | record | 公開 title (slug/playUrl/version) |
| `com.etzhayyim.gameka.buildArtifact` | record | wasm cid/size |

## D4. BPMN process suite (5 process)

`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/gameka/` に格納。**全 task は ADR-0056 の 7
generic primitives + ADR-2604250836 の `generic.langgraph.run` 8 種で
構成し、新 primitive を追加しない**。

### D4.1 `proposeGame.bpmn`

```
Start (XRPC com.etzhayyim.gameka.proposeGame)
  → Task_LoadMemory      generic.db.select  vertex_gameka_spec (last 10)
  → Task_Deliberate      generic.langgraph.run
                         { graph_id: "gameka.studio.v1", state: { brief, prior_specs }, mode: "oneshot" }
  → Task_ConsentGate     generic.audit.emit  gameka.spec.consent_check
                         (Path F consent middleware が gate を持つ)
  → Task_PersistSpec     generic.db.insert  vertex_gameka_spec
  → Task_Audit           generic.audit.emit  gameka.spec.proposed
  → Task_DeriveGenerate  generic.pds.dispatch com.etzhayyim.gameka.generateGame
  → End
```

### D4.2 `generateGame.bpmn`

```
Start (chained from spec)
  → Task_RenderScaffold  generic.http.fetch  POST kami-codegen runner
                         (kami-app-{slug} crate template, scene + adapters from spec)
  → Task_BuildWasm       generic.http.fetch  POST kami-build runner (Vultr)
                         returns { cid, size, log_url }
  → Task_StoreArtifact   generic.http.fetch  PUT B2 etzhayyim-gameka/builds/{cid}.wasm
  → Task_PersistArtifact generic.db.insert   vertex_gameka_artifact
  → Task_Audit           generic.audit.emit  gameka.artifact.built
  → Task_DerivePlaytest  generic.pds.dispatch com.etzhayyim.gameka.playtestGame
  → End
```

### D4.3 `playtestGame.bpmn`

```
Start
  → Task_HeadlessRun  generic.http.fetch  POST playwright actor (WebGPU + screenshots)
                      returns { fps_p50, crashes, asset_404, scene_load_ms }
  → Task_LLMCritic    generic.llm.json    Murakumo
                      schema: { score, issues[], publish }
  → Gateway publish ?
       ├ true  → Task_DerivePublish  generic.pds.dispatch publishGame
       └ false → Task_PersistFail    generic.db.insert vertex_gameka_qa_fail
                  → Task_DeriveRevise generic.pds.dispatch proposeGame (iter+1, cap 3)
```

### D4.4 `publishGame.bpmn`

```
Start
  → Task_MintSubDid       generic.http.fetch  POST authn.etzhayyim.com (sub-actor path key)
  → Task_RegisterTitle    generic.db.insert   vertex_gameka_title
  → Task_RegisterUploader generic.http.fetch  POST game-play-uploader register
  → Task_SocialPost       generic.pds.dispatch app.bsky.feed.post
                          repo = did:web:gameka.etzhayyim.com:game:{slug}
  → Task_Audit            generic.audit.emit  gameka.title.published
  → End
```

### D4.5 `tickStudio.bpmn` (autonomous, R/PT2H)

```
Start (timerEventDefinition R/PT2H)
  → Task_TrendScan       generic.db.select  vertex_repo_record
                          (media-gamers posts, last 24h)
  → Task_BuildBrief      script (FEEL) trend keywords → brief
  → Task_DeriveProposal  generic.pds.dispatch com.etzhayyim.gameka.proposeGame
  → End
```

yoro `platformPulse` と同骨格。**最初の 14 日は β2 lesson に従い
silently log のみ** (publish 経路を `mode: dry_run` で skip) で誤発射を抑える。

`respondToPlaytest.bpmn` は yoro `respondToMention` と同パターンで
subscribeRepos からの reactive trigger。本 ADR の最小確定面には含めない。

## D5. LangGraph graph `gameka.studio.v1`

`etzhayyim-root/50-infra/vultr/zeebe-worker/graphs/gameka.studio.v1.py` に置き、
ADR-2604250836 の registry (`vertex_langgraph_def`) に 1 行登録する。

State (≤ 100 KB → `mode=oneshot`、Zeebe variable で完結):

```python
class GamekaState(TypedDict):
    brief: str
    prior_specs: list[dict]
    candidates: list[dict]
    research: dict
    critique: list[dict]
    selected: dict | None
    score: float
    iteration: int
    max_iterations: int  # = 3
```

Graph:

```
START → planner (Murakumo: propose 3 specs)
      → researcher (XRPC media_gamers.searchGames + kami.listSceneTemplates)
      → critic (Murakumo: score on fun/feasibility/kami-coverage/novelty)
      → should_loop?  iteration<max AND best_score<0.8 ?
           ├ yes → planner (revise)
           └ no  → finalizer (emit GameSpec dict) → END
```

`finalizer` 出力 = `vertex_gameka_spec` 1 行に等価な dict。BPMN 側は
これを `Task_PersistSpec` で 1 回 INSERT する (write-once)。

Path F middleware (memory / consent / audit) は LangGraph 内には置かず、
**BPMN task 配置で表現** する (`Task_LoadMemory` 前置, `Task_ConsentGate`
中置, `Task_Audit` 後置)。これは ADR-2604261000 (MCP-as-tool registry)
が tool 側に middleware を持たない原則と整合する。

## D6. Persistence

`30-graph/graph-schema/migrations/{ts}-gameka-actor.ts`:

| Table | 主列 |
|---|---|
| `vertex_gameka_spec` | spec_id (ULID) pk, brief, genre, mechanic_json, scene_json, budget_usd, score, lineage_parent, created_at |
| `vertex_gameka_artifact` | artifact_id pk, spec_id fk, wasm_cid, wasm_size, build_log_url, created_at |
| `vertex_gameka_qa` | qa_id pk, artifact_id fk, fps_p50, crashes, llm_score, publish bool, issues_json |
| `vertex_gameka_title` | title_id pk, slug uniq, sub_did, parent_spec_id, parent_artifact_id, play_url, version, published_at |
| `edge_gameka_spec_revises` | (spec_id, parent_spec_id) — LangGraph iteration lineage |
| `edge_gameka_title_published_by` | (title_id, did_actor) |

ADR-0048 RW 制約: `ON CONFLICT` 禁止 → spec_id は ULID で衝突無し。
bulk INSERT 経路ではないので `dml_rate_limit` 不要。

B2 layout: `etzhayyim-gameka/{builds,assets,playtest-recordings}/`、
ADR-0029 CIDv1 (`b` base32 + `raw` codec + sha2-256) で content-addressed。

# Comparison (Pipeline shape η)

LangGraph 配置軸は ADR-2604250836 で settled。本 ADR が決めるのは
**pipeline 分割粒度**。

| 軸 | w | A. monolithic 1 BPMN | B. 5 BPMN chain (採用) | C. CF Worker orchestrator + LangGraph pod |
|---|---:|---:|---:|---:|
| Re-execution / partial retry | 0.20 | 0.40 | **0.95** | 0.70 |
| Operate UI 観測性 | 0.15 | 0.50 | **0.95** | 0.40 |
| ADR-0056 規約整合 (INSERT 2 rows) | 0.15 | 0.80 | **1.00** | 0.30 |
| 既存 actor 再利用 (playwright/uploader/media-gamers) | 0.10 | 0.70 | **0.90** | 0.50 |
| 状態原子性 | 0.10 | **1.00** | 0.70 | 0.60 |
| LLM cost 効率 (cache hit) | 0.10 | 0.50 | **0.85** | 0.85 |
| 失敗の blast radius | 0.10 | 0.40 | **0.85** | 0.65 |
| Audit shape (triple-witness 親和) | 0.10 | 0.60 | **0.95** | 0.50 |
| **加重 η** | | **0.59** | **0.91** | **0.55** |

### 軸ごとの根拠

- **Re-execution / partial retry**: A は 1 process が落ちると spec→build→QA→publish
  全てやり直し。B は失敗 step だけを Operate UI から再開できる (yoro 既証)。
- **状態原子性**: A は単一 process variable で完結、B は `pds.dispatch`
  chain なので中間 row が graph に残る。idempotency key (spec_id ULID) で緩和。
- **ADR-0056 規約整合**: B は `INSERT 2 rows × 5 process = 10 rows` で
  全部表現できる。C は Helm rollout 経路に戻り規約を破る。

# Exceptions

次の **すべて** を満たす場合のみ、proposeGame の deliberation を
ADR-2604250836 §Exceptions の case B (LangGraph pod 直結) に escape させる:

1. typical run が 500 hop / 30 min を恒常的に超える
2. state が 10 MB を恒常的に超える
3. audit を `vertex_repo_commit` 以外の独立 logger で確保

`gameka.studio.v1` は ≤ 3 iteration × 3 candidate × 数 KB なので
oneshot で十分、本 ADR 時点で escape は **不要**。

# Consequences

## Positive

- 新 Worker / 新 deployment 0。`INSERT 10 rows` + B2 bucket 1 + lexicon JSON 9
  で gameka actor が live。
- 既存資産 (kami-engine kami-app-{game} pattern, playwright, game-play-uploader,
  media-gamers Multi-DID) を全て再利用、責務再配置なし。
- Path F middleware (memory/consent/audit/scheduler) が BPMN task 配置で
  自動適用される (ADR-2604261000)。
- yoro autonomous loop の β2 lesson (14 日 dry-run + triple-witness) が
  そのまま流用できる。

## Negative

- per-game sub-DID 発行で `did.json` rotate が累積する → ADR-0023
  multi-key の 3-key 制約に当たる頃 (~ 100 game) で sub-DID 整理 ADR が必要。
- `kami-codegen` runner と `kami-build` runner は新規構築 (Vultr 上)。
  ただし stateless / image 1 つで済むため Helm chart は薄い。
- LangGraph deliberation の Murakumo cost が autonomous tickStudio で
  常時走ると月次コスト押し上げ。R/PT2H × 30 日 = 360 run / 月で見積もる。

# Migration

| Step | 内容 | 完了条件 |
|---|---|---|
| 1 | 本 ADR ratify、`deps.toml` `[[bpmn_actors]] gameka` 行追加 | review pass |
| 2 | 9 lexicon JSON + RW migration apply | `etzhayyim graph migrate` clean |
| 3 | `gameka.studio.v1` LangGraph graph + unit test (offline LLM) | py test green |
| 4 | `proposeGame.bpmn` のみ live。手動 XRPC で 1 spec 生成 | `vertex_gameka_spec` 1 row |
| 5 | `kami-codegen` + `kami-build` runner Helm rollout | wasm cid B2 に着く |
| 6 | `generateGame.bpmn` + `playtestGame.bpmn` chain live | publish=false で止まる |
| 7 | `publishGame.bpmn` + sub-DID + game-play-uploader 連携 (1 件手動 review) | live game URL 1 つ |
| 8 | `tickStudio.bpmn` R/PT2H ON、最初 14 日 dry-run | tally log clean |
| 9 | `respondToPlaytest.bpmn` 追加 (subscribeRepos reactive) | feedback round-trip 1 件 |

各 Step は独立に rollback 可能。Step 7 までは autonomous emission なし。

# References

- ADR-0056 — BPMN-as-actor
- ADR-2604250836 — LangGraph as Zeebe ServiceTask (`generic.langgraph.run` 8th primitive)
- ADR-0036 / ADR-0081 — Worker-direct Hyperdrive persistence
- ADR-0046 — yoro triple-witness autonomy monitoring
- ADR-0019 — atproto-native identifier topology (did:web sub-actor path)
- ADR-0023 — Auth Shannon-optimal 4-Layer (multi-key rotation)
- ADR-0029 — did:etzhayyim method spec (CIDv1 content addressing)
- ADR-2604241038 — yoro/PDS/AppView ideal topology
- ADR-2604241500 — CAD/BIM per-game WASM topology
- ADR-0031 — kami VRM three-free topology
- `40-engine/kami-engine/CLAUDE.md` — kami-app-{game} crate pattern
- `60-apps/etzhayyim-project-media-gamers/CLAUDE.md` — Multi-DID per game pattern
- `60-apps/etzhayyim-project-game-play-uploader/` — play page hosting Worker
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/yoro/platformPulse.bpmn` — autonomous timer-start reference
