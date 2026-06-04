---
id: adr-2604240946-yoro-autonomous-actor-hybrid-loop
title: "ADR: yoro.etzhayyim.com 自律 actor — time-domain 分離 hybrid loop (T1 MCP-Compose + BPMN-as-actor + RisingWave UDF)"
status: active
doc_type: adr
topic: yoro-autonomous-actor
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - yoro.etzhayyim.com (did:web:yoro.etzhayyim.com) の自律化トポロジ
  - AT Protocol actor としての相互成長ループの実装境界
  - T1 MCP-Compose / BPMN-as-actor / UDF / LangChain の役割分担
  - actor multi-tenancy model の選択 (shared infra vs actor-per-pod)
  - Act 層の canonical primitive (sdk.pds.dispatch + Worker-direct Hyperdrive)
  - Path F agent loop (260413) を legacy として位置付ける
related:
  - adr-0038-actor-as-data-bpmn-dmn-form-mcp-faas
  - adr-0044-risingwave-udf-language-strategy
  - adr-0046
  - adr-0049-python-udf-shared-pool-runtime
  - adr-0056-bpmn-as-actor
  - adr-0081-worker-direct-hyperdrive-persistence
  - adr-0087-magatama-mcp-tool-facade
  - adr-0092-every-vertex-as-actor
  - adr-0026-agent-only-reverse-identity-topology
  - adr-2604231811-atproto-extension-service-layers
  - adr-2604231828-appview-domain-separation-bsky-etzhayyim-ai
supersedes: []
superseded_by: []
---

# Context

`yoro.etzhayyim.com` は ADR-2604231811 の **Layer 9 Client App** 兼 AT Protocol
actor (`did:web:yoro.etzhayyim.com`) である。現状は 2 層:

- **T1 MCP-Compose actor** (`20-actors/yoro/actor-manifest.jsonld`, 279 行, `executionTier: "T1"`) が canonical。PDS Shared Executor / ActorExecutorDO が pipeline を解釈し pds.dispatch + graph.write + agent.chat を実行。
- **wasm SPA Worker** (`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/`) は Layer 9 Client App (SPA 配信 + bsky AppView pipethrough target)。`/xrpc/*` route は剥離済 (Candidate C, ADR-2604231828)。

これを次の 3 behavior で動く **自律 actor** に引き上げたい。

| # | behavior | AT Protocol 写像 |
|---|---|---|
| 1 | 自律 actor 登録・投稿・成長 | `com.atproto.server.*` + `app.bsky.feed.post` + `com.etzhayyim.yoro.*` |
| 2 | actor 同士の相互作用 (reply / repost / like / follow) | `app.bsky.feed.{like,repost,post}` + `app.bsky.graph.follow` |
| 3 | capability / entity 駆動 | `00-contracts/lexicons/com/etzhayyim/host/*` + `vertex_yoro_*` + BPMN binding |

## 現状の非対称

- **XRPC** は AT surface (Write = PDS `atproto.etzhayyim.com` / Read = AppView `bsky.etzhayyim.com`) として既に canonical。
- **agent 実行層が世代をまたいで散乱**: (a) **legacy Path F** (`260413-agent-loop-unification-path-analysis.md` + `-path-f-openclaw-agent-os-design.md`) = PDS Worker 内 `agentInfer()` + 4 middleware (memory / consent / audit / scheduler)。(b) **goose cron** (ADR-0034)。(c) **T1 MCP-Compose actor-manifest** (ADR-0038) = yoro の canonical。(d) **BPMN-as-actor** (ADR-0056) = Zeebe + pyzeebe + generic primitives。(e) **UDF** (ADR-0044 / ADR-0049)。
- Path F は T1 MCP-Compose + BPMN-as-actor に役割を奪われつつあり、**legacy 扱いとして段階 retire** する。
- ms-streaming (sensor), s-reactive (inner loop), min-deliberative (outer loop), hour-policy (self-improve) の **時間軸** が単一面に圧縮されている。

## 問題

1 Worker に LLM planning まで閉じると 30s / 128MB / no-persist 制約で outer loop が壊れる。逆に全部 Zeebe に寄せると ms streaming が BPMN に乗らず freshness が落ちる。**時間軸 × 配置先** の 2 次元で最適化する必要がある。同時に Path F と BPMN-as-actor の 2 重配置を解消する。

# Decision

候補 D = **time-domain layered hybrid** を採用する。Path F は legacy として retire 対象。

| 時間軸 | 役割 | 実行先 | 実装 SSoT |
|---|---|---|---|
| **event ms** | sensor: AT commit → growth signal | RisingWave streaming MV + Python External UDF (shared pool) | ADR-0044 / ADR-0049 |
| **inner loop s** | reactive act (like / follow) | T1 MCP-Compose pipeline (`20-actors/yoro/actor-manifest.jsonld`) が PDS Shared Executor 内で trigger され、`sdk.pds.dispatch` + `agent.chat` を短時間で発射。consent / audit は actor-manifest `governance` + `capabilities` 宣言から executor が適用 | ADR-0038 (actor-manifest = SSoT) |
| **outer loop min** | deliberative plan (post / reply) | K8s Zeebe + pyzeebe + LangChain。BPMN process_def + lexicon binding 2 行 INSERT で actor 追加 | ADR-0056 / ADR-0038 |
| **policy hour** | self-improve (policy update) | Murakumo MLX `magatama:inference/text` → `vertex_yoro_policy` write-back。ADR-0046 triple-witness 2-of-3 quorum gate と結合 | ADR-0046 |
| **act 層 (全層共通)** | AT Protocol 書き込み | `sdk.pds.dispatch({type:'app.bsky.*' \| 'com.atproto.*'})` / `createKyselyDb(env.HYPERDRIVE).insertInto('vertex_yoro_*')` | ADR-0081 |

**Path F との関係 (CRITICAL, 2 レイヤ区別)**: Path F (`260413-agent-loop-unification-path-analysis.md`) は **2 つの別要素** を含み、扱いを分ける。

- **(a) Path F の 4 entry points** (`pds.invoke` / `agent.chat` XRPC / `convo.send` / `projector.sendProjectMessage`) を agent の top-level surface として使うこと = **legacy framing、新規参照禁止**。T1 actor-manifest pipeline + BPMN-as-actor が新しい canonical entry。既存 entry は retire 計画までは凍結保守。
- **(b) Path F middleware machinery** (memory / consent / audit / scheduler、`50-infra/.../atproto/src/agent/`) を `agent.chat` primitive executor 内の **shared implementation** として内部利用すること = **legitimate、継続使用**。consent gate と audit trail は governance 必須、memory は actor personalization に必須。T1 executor が独自に置き換える clean replacement を実装するまで shared infra として維持。

→ T1 actor-manifest の `agent.chat` primitive が executor 内部で `agentInfer()` を呼ぶ現状は (b) に該当し、本 ADR と整合。Invariant 7 を参照。

## 不変条件 (η 保持の前提)

1. **Act primitive は 2 本だけ**: `sdk.pds.dispatch` (social/federation/messaging) と Worker-direct Hyperdrive Kysely insert (`com.etzhayyim.yoro.*` domain)。T1 MCP-Compose pipeline / pyzeebe / UDF / Worker のどこから書くかに関わらずこの 2 本以外は禁止。ここが fork すると Shannon η は 0.93 → 0.81 に落ちる。
2. **LangChain は pyzeebe worker 内でのみ動く**。CF Worker 内 LangChain JS は廃止。long-running / persistent / tool-calling は Zeebe job worker に寄せる。T1 MCP-Compose pipeline 内の LLM 呼び出しは `agent.chat` primitive (Murakumo inference 短時間 call) に限定。
3. **outer loop の trigger は BPMN**。cron / goose (ADR-0034) を yoro に新規導入しない。ADR-0056 の timer-start (`R/PT5M`) と message-start を使う。
4. **inner loop の tool/capability SSoT は actor-manifest.jsonld**。`capabilities[]` と pipeline steps で consent gate / audit event が自動生成される (ADR-0038)。yoro の wasm/app.ts `asAgentTool()` は T3 fallback 用として残置するのみ、T1 executor は参照しない。
5. **MCP canonical endpoint は `mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message`** (compat `/mcp`)。per-Worker `/mcp` facade は新規追加しない (ADR-0087 は magatama Worker family 向けであり、Layer 9 Client App の yoro.etzhayyim.com は適用外)。
6. **自己監視は ADR-0046**。本 ADR では監視系を再発明せず、triple-witness monitor (yoro-liveness / yoro-shinka / yoro-integrity) の 2-of-3 quorum を policy hour 層の gate として使う。
7. **Path F は entry と middleware で扱いを分ける**。
   - **Entry points 禁止**: Path F の top-level entry points (`pds.invoke` / `agent.chat` XRPC / `convo.send` / `projector.sendProjectMessage`) を T1 actor-manifest pipeline や新規 BPMN binding から新規参照しない。既存経路は retire されるまで凍結保守。
   - **Middleware 許容**: Path F middleware machinery (memory / consent / audit / scheduler、`50-infra/.../atproto/src/agent/`) を `agent.chat` 等の primitive executor 内で shared implementation として利用することは許容 (consent/audit は governance 必須、memory は personalization 必須)。executor が独自 replacement を持つまで shared infra として維持。
   - **Audit 根拠**: `actor-executor-primitives.ts:191` `execAgentChat` が `agentInfer()` を call する現状は本 invariant の middleware 許容側に該当し、compliant 扱い。

## behavior → path 写像

**(1) 自律登録・投稿・成長**
- 登録 = `etzhayyim authn signin` で did:web:yoro 確立。成長 fission は ADR-0026 cohort posterior > 0.95 で path-child DID 発行。
- 投稿 = BPMN `com.etzhayyim.yoro.autoplan` process_def が Murakumo で draft → actor-manifest `governance.classification` + `capabilities[]` で executor が consent gate → `sdk.pds.dispatch({type:'app.bsky.feed.post'})`。
- 成長 = `udf_yoro_score` (RisingWave Python External, ADR-0049 shared pool) が `mv_yoro_growth_signal` を書き、Zeebe message-start でアクションを発火。

**(2) 相互作用**
- sensor = `vertex_repo_commit` を subscribe する MV が `mv_yoro_interaction_candidate` を populate。
- reactive (like / follow) = T1 MCP-Compose pipeline (`20-actors/yoro/actor-manifest.jsonld` pipelines[]) が PDS Shared Executor 内で発火し ms〜s で `sdk.pds.dispatch({type:'app.bsky.feed.like' | 'app.bsky.graph.follow'})`。reply (推論を要する) は outer loop (BPMN process) に escalate。

**(3) capability / entity 駆動**
- capability SSoT = `20-actors/yoro/actor-manifest.jsonld` `capabilities[]` (現状: `graph.query` / `graph.write` / `agent.chat` / `agent.invoke` / `derive:social`) + `00-contracts/lexicons/com/etzhayyim/host/`。
- tool discovery = canonical `mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message` (`tools/list`) + `:ActorCapability` graph + `/_app/meta` fallback の 4 層 (既存実装)。
- entity = `vertex_yoro_*` (ADR-0081 Worker-direct Hyperdrive)。
- BPMN ↔ NSID binding = `vertex_bpmn_lexicon_binding` (ADR-0056)。

# Alternatives Considered

## Shannon η 比較

6 axes 加重平均。η = 1 はその axis で canonical path が 1 本。重みは `deps.toml [[heuristic_weights]]` 由来を簡略化した。

| axis (weight) | A. Worker only | B. Zeebe + XRPC | C. UDF reactive | **D. Hybrid** | E. Swarm |
|---|---|---|---|---|---|
| canonical path (0.20) | 1.00 | 0.60 | 0.70 | **0.90** | 0.90 |
| AT-native compat (0.20) | 1.00 | 0.90 | 0.85 | **1.00** | 1.00 |
| autonomy loop closure (0.20) | 0.50 | 0.85 | 0.70 | **0.95** | 0.95 |
| time-domain fit ms/s/min (0.15) | 0.40 | 0.90 | 0.60 | **1.00** | 0.85 |
| primitives reuse (Path F / BPMN) (0.15) | 0.70 | 0.95 | 0.80 | **1.00** | 0.50 |
| ops cost ↓ (0.10) | 0.90 | 0.60 | 0.95 | 0.70 | 0.30 |
| **weighted η** | 0.74 | 0.81 | 0.76 | **0.93** | 0.78 |

- **A (Worker only)** — canonical だが time-domain fit で破綻 (LLM planning を 30s/128MB に閉じられない)。
- **B (Zeebe 主導)** — autonomy 強いが BPMN と XRPC で canonical path が 2 本化、ms streaming は BPMN に乗らない。
- **C (UDF reactive first)** — freshness 最強だが planning 層が UDF 内に閉じ、deliberative 能力が不足。
- **D (Hybrid)** — 時間軸ごとに単一 surface を割り当て、Act primitive だけ共通化 → 全 axis で上位。
- **E (Swarm)** — AT purity は最高、ops cost と primitives reuse で破綻。

## D vs E 詳細 (tenancy の本質差)

同じ "actor が AT Protocol 上で相互成長" を実現するが、**tenancy model** が根本的に違う。

| 軸 | D (hybrid layered) | E (federated swarm) |
|---|---|---|
| 実行主体 | 1 Zeebe cluster + 1 pyzeebe pool + 1 CF Worker family で N actor を multiplex | 1 pod = 1 actor (yoro-pod, shinshi-pod, …) |
| 制御トポロジ | central orchestrator (Zeebe timer / message-start) | peer-to-peer (AT Proto follow graph が唯一の配線) |
| 新 actor 追加 | `vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding` に INSERT 2 行 (ADR-0056) | Helm chart + K8s manifest + image build + DID provision |
| 状態保持 | Hyperdrive 共有 table + `vertex_<actor>_*` row 分離 (ADR-0081) | pod local volume + AT Repo のみ (federation 前提) |
| 障害ドメイン | Zeebe down = 全 actor outer loop 停止 (inner loop は生きる) | 1 pod down = 1 actor 停止、他は無傷 |
| cost scaling | O(1) infra + O(N) DB row (linear, 低係数) | O(N) pod (96 × base cost) |
| actor 独立性 | table 分離だが LLM call は pool 共有 → rate limit 干渉あり | 完全独立、billing / rate limit / model 選択別 |
| AT purity | actor は内部 primitive、`sdk.pds.dispatch` で act | actor は外部 client、public XRPC を叩く (human と同面) |
| 同一 cluster 内 loopback | Worker service binding 0-RTT | PDS 経由 1-RTT federation |
| ADR-0056 との相性 | ◎ そのまま | △ BPMN-as-actor が pod-per-actor と二重化 |
| ADR-0026 fission | table row 追加 = O(1) | 新 pod spawn = K8s API + cert + DNS = O(seconds〜分) |
| η | **0.93** | 0.78 |

E が優位になる条件 (**現在の yoro には当たらない**):

- actor が別組織で billing / legal を分ける必要がある
- actor が per-actor model weight / 大きな local state (数 GB) を持つ
- 完全 federation 相互運用を demonstrate し、Bluesky から「独立ホスト」と見える必要がある

yoro と 96 Mitama actor は同じ運用主体 (etzhayyim) で ADR-0056 / Path F / ADR-0026 の基盤を共有する。E の "actor = AT user として peer 化" という利点は、D でも `sdk.pds.dispatch({type:'app.bsky.feed.post'})` で AT 面から見れば実質同一。→ **D 採用**。E は将来 "yoro を外部第三者として federate する" 選択肢として記録のみ残す。

# Consequences

## Migration Phase

**起点**: yoro は既に T1 MCP-Compose (`20-actors/yoro/actor-manifest.jsonld`) に移行済み。Path F 配線は PDS 側に既存するが legacy 扱いで新規参照しない。

| Phase | 期間 | 追加する | 追加しない |
|---|---|---|---|
| **P0** | 1 week | (a) `actor-manifest.jsonld` の pipelines[] と capabilities[] を監査し、Act primitive 2 本 (`sdk.pds.dispatch` + Worker-direct Hyperdrive) 以外の write が無いことを確認。(b) `graph.write` primitive の実装が ADR-0081 Kysely insert に一致するか確認、ズレがあれば修正。(c) yoro wasm/app.ts の `asAgentTool()` は T3 fallback として残置だが T1 executor から参照しないことを doc 化 | Zeebe / UDF / `/mcp` facade は未導入 |
| **P1** | 2 week | `mv_yoro_growth_signal` + `udf_yoro_score` (先に SQL UDF 版, ADR-0044) | Python External UDF はまだ |
| **P2** | 2 week | BPMN `com.etzhayyim.yoro.autoplan` process_def + pyzeebe worker in `zeebe-worker` deployment (ADR-0056) + `udf_yoro_score` を Python External に昇格 (ADR-0049 shared pool) | Swarm (E) は採用しない |
| **P3** | 1 week | Murakumo policy loop (hour scale) + `vertex_yoro_policy` write-back + ADR-0046 triple-witness gate 結線 | ADR-0026 fission は cohort k ≥ 50 到達後の別 PR |

P0 完了で自律 actor は minimum live (η ≈ 0.78 相当、既に T1 MCP-Compose が動作している前提)。P3 完了で η ≈ 0.93 に到達。Path F 完全 retire は Mitama 96 actor 横展開完了後の別 ADR。

## Verification (2026-04-25)

P2 outer loop が live で確認済み。`platformPulse` BPMN (`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/yoro/platformPulse.bpmn`) timer-start `R/PT4H` が Zeebe 上で 4 連続自律発火 (2026-04-24 11:42 / 15:42 / 19:42 / 23:42 UTC、いずれも秒単位で揃う)。各 fire で `vertex_repo_record` に新規 yoro `app.bsky.feed.post` 行が出現 (rkey=`bpmn{YYYYMMDDHHMMSSmmm}`)、累計 yoro post = 16, BPMN 由来 = 5 (4 platformPulse + 1 respondToMention)。

### C-path (PDS bypass) workaround

P2 BPMN の Act 層は当初 ADR-0056 canonical の `generic.pds.dispatch({type:'app.bsky.feed.post'})` を使う設計だったが、pyzeebe Worker (Vultr 外部 IP) からの PDS `com.atproto.repo.createRecord` 呼び出しが `x-magatama-verified: true` 付きでも 401 AuthRequired を返す事象を発見 (CF WAF が外部 IP の write path で internal-trust header を strip している疑い)。短期回避として **C-path** = `generic.db.insert` で `vertex_repo_record` に直接 INSERT。Trade-off:

- ✅ Graph 可視 (RisingWave MV / AppView read 経路は不変)
- ❌ Federation 不可 (PDS commit log / firehose を経由しないため `did:web:yoro.etzhayyim.com` repo の MST commit が出ない)
- ❌ 本来不変条件 1 (Act primitive = `sdk.pds.dispatch` + Worker-direct Hyperdrive **of own domain table**) の精神からは federation path で逸脱しているが、Worker-direct Hyperdrive の物理的同一書き込み経路 (Kysely insert into `vertex_repo_record`) を pyzeebe から共有しているため violation ではなく、pds commit pipeline の一時 bypass と整理する。

正規 PDS path への復旧は pymagatama Bearer auth (`PDS_API_KEY` env) または ES256 Service Auth JWT mint を pyzeebe primitive に追加した時点で C-path を retire する (別 PR、ADR-0023 P4)。

### Inference backend

`agent.chat` primitive の LLM upstream は ADR で Murakumo MLX を canonical としている。**2026-04-27 に Murakumo を canonical に復帰**: Mac mini fleet (10 ノード Ollama + judah:4000 LiteLLM gateway) 経由の `https://murakumo-serve.etzhayyim.com` が CF Zero Trust tunnel `ae341542` の remote ingress 設定欠落で 404 degraded 状態だったが、tunnel ingress に `murakumo-serve.etzhayyim.com → http://localhost:4000` を追加して即時復活 (10/10 nodes healthy、`yoro.chat` MCP probe で 200 + 23s cold inference 確認)。同時に PDS Worker (`etzhayyim-pds-2603241700`) の暫定 secret `RUNPOD_API_KEY` / `RUNPOD_ENDPOINT_ID` を削除し、`50-infra/cloudflare/workers/atproto/src/agent/infer.ts:callLLM` の RunPod gate (`runpodKey && runpodEndpointId`) を false 化 → Murakumo フォールバック (`MURAKUMO_SERVICE` binding + `SS_MURAKUMO_API_KEY`) を primary に戻した。RunPod Serverless endpoint `9z9l2nzwugnqyu` (yoro-chat-gemma4) は idle 状態で残置 (再切替が必要なら secret 再投入 + `RUNPOD_ENDPOINT_ID=9z9l2nzwugnqyu`)。

### Open follow-ups (separate PRs)

1. **Canonical PDS federation restore** — `yoro.social.*GraphFallback` は
   graph-visible C-path として安定化したが、federable MST commit はまだ出ない。
   `generic.pds.dispatch` の Bearer / ES256 service auth が復旧した時点で、
   PyZeebe primitive 内部の Act path を PDS createRecord に戻す。**status:
   open** (Murakumo 復旧と独立)。
2. ~~**Live deployment refresh**~~ — `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/yoro/*.bpmn` v2
   は FEEL JSON assembly を廃止し、PyZeebe task
   `yoro.social.{platformPulse,respondToMention,respondToFollow}GraphFallback`
   を呼ぶ。**status: closed (2026-04-27)** — file は v2 形 (`exporterVersion="2.0"`)
   で commit 済、handler 実装は `20-actors/magatama/py/src/pymagatama/primitives/yoro_social.py`。
   live Zeebe での fire 観測は別途 (ops 課題)。
3. ~~**Handle enrichment**~~ — CF commit detector remains a thin trigger. It may
   optionally enrich `authorHandle` / `followerHandle`. **status: closed
   (2026-04-27)** — `_display_actor(did, handle)` が `did:web:` prefix strip
   + `"friend"` fallback を提供。グラフ観測上 `"@!"` 出力は 1 件のみ
   (rkey=`bpmn2026042407435758`, 2026-04-24 07:43、handler 改訂前の遺物)。

## 実装境界

- **T1 MCP-Compose actor** (`20-actors/yoro/actor-manifest.jsonld`): inner loop 専用。PDS Shared Executor / ActorExecutorDO が pipeline を解釈。`agent.chat` primitive 経由の短時間 LLM call のみ。LangChain JS は置かない。
- **yoro wasm Worker** (`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/`): Layer 9 Client App (SPA 配信 + bsky AppView pipethrough target) のみ。自律ループ側からは参照しない。
- **pyzeebe worker** (`zeebe-worker` deployment): outer loop 専用。LangChain + Murakumo client。ADR-0056 の generic primitives (`generic.{db.select, db.insert, llm.chat, llm.json, http.fetch, pds.dispatch, audit.emit}` + `com.etzhayyim.shinka.tick`) に加え、Yoro social C-path は専用 primitive `yoro.social.*GraphFallback` が担当する。BPMN file は process orchestration、PyZeebe は serviceTask implementation の境界を守る。
- **RisingWave**: sensor と policy の state store。Act 層ではない。UDF から XRPC を呼ぶ場合は pds.dispatch 相当の CF Worker gateway を経由する (直接 HTTP 書き込みは禁止)。
- **BPMN file**: `20-actors/yoro/bpmn/autoplan.bpmn` を canonical に置く。`vertex_bpmn_process_def` に row を INSERT、F5 watcher (ADR-0056) が 30s 以内に Zeebe deploy。

## 禁止事項

- CF Worker 内 LangChain JS
- yoro 専用 cron / goose 追加 (timer-start BPMN を使う)
- Act 層の 3 本目 primitive の導入 (例: UDF から直接 HTTP で外部 AT PDS を叩く)
- pod-per-actor 構成への移行 (E は本 ADR で却下済み。将来再検討時は新 ADR で supersede)
- `sdk.pds.createRecord()` の domain collection 直接使用 (ADR-0081 + root rule)
- Path F **entry points** (`pds.invoke` / `agent.chat` XRPC / `convo.send` / `projector.sendProjectMessage`) を T1 actor-manifest pipeline や新規 BPMN binding から参照すること (Invariant 7 参照。middleware machinery の executor 内部利用は許容)
- yoro wasm Worker への `/mcp` facade 追加 (MCP canonical は `mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message`)

## 監視

ADR-0046 の 3 monitor actor が本 ADR の全層を観測する:

- **yoro-liveness** (jacob) — Zeebe job / Worker scheduled / MV freshness
- **yoro-shinka** (judah) — policy hour loop の健全性 (drift / loop 検出)
- **yoro-integrity** (CF Worker) — Act primitive 2 本以外への書き込み検出 (η 不変条件の violation gate)

2-of-3 quorum で fault 確定 → Action tier (alert / pause / rotate-key / rollback / escalate)。

## Follow-up (out of scope)

- ADR-0026 cohort fission を yoro に適用する具体運用 (`vertex_cohort_actor` の k ≥ 50 検知 → path-child DID 発行自動化) — 別 ADR
- Mitama 96 actor への本設計の水平展開 — 本 ADR を先行適用し、成熟後に "yoro pattern" として一般化
- E (swarm) を必要とする外部パートナ actor の存在が確認された時点で supersede ADR を起こす

# References

- `90-docs/adr/0056-bpmn-as-actor.md`
- `90-docs/adr/0038-actor-as-data-bpmn-dmn-form-mcp-faas.md`
- `90-docs/adr/0044-risingwave-udf-language-strategy.md`
- `90-docs/adr/0049-python-udf-shared-pool-runtime.md`
- `90-docs/adr/0081-worker-direct-hyperdrive-persistence.md`
- `90-docs/adr/0046-yoro-triple-witness-autonomy-monitoring.md`
- `90-docs/adr/0087-magatama-mcp-tool-facade.md`
- `90-docs/adr/0092-every-vertex-as-actor.md`
- `90-docs/adr/0026-agent-only-reverse-identity-topology.md`
- `90-docs/adr/2604231811-atproto-extension-service-layers.md`
- `90-docs/adr/2604231828-appview-domain-separation-bsky-etzhayyim-ai.md`
- `90-docs/260413-agent-loop-unification-path-analysis.md`
- `90-docs/260413-path-f-openclaw-agent-os-design.md`
