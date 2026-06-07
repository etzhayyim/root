---
id: adr-2605070700-rw-native-model-training-weight-lineage
title: Kotoba/Datomic-native Model Training + Weight Lineage (SFT / LoRA / Distill)
status: proposed
doc_type: adr
topic: model-training-weight-lineage
authoritative: true
last_verified: 2026-05-07
authoritative_for:
  - rw-native-model-training-pipeline
  - weight-checkpoint-lineage-schema
  - sft-lora-distill-bpmn-actor
  - student-teacher-edge-projection
related:
  - adr-2604300135-hume-distillation-artifact-persistence
  - adr-2604261936-ipfs-self-hosted-vultr-b2
  - adr-0056-bpmn-as-actor
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-2604292130
  - adr-2605010000
  - adr-2604282100
  - adr-0044-kotoba-udf-language-strategy
supersedes: []
superseded_by: []
---

# Goal

Kotoba/Datomic schema を一次情報源として、自前モデルの **train run / checkpoint /
eval** を repo 内で宣言・追跡し、weight を世代を超えて育てられる経路を引く。
serving (Murakumo / RunPod / Vultr GPU) と完全分離した上で、AppView や agent
loop から **「現役 weight はどれか」「どの corpus shard で学習したか」「teacher
は誰か」** を SQL で答えられる状態を SSoT にする。

# Scope

In:
- `vertex_training_run` / `vertex_training_checkpoint` / `vertex_training_eval`
  / `vertex_training_dataset_snapshot` の 4 vertex
- `edge_training_distilled_from` (teacher → student) /
  `edge_training_consumed_dataset` (run → dataset shard) /
  `edge_training_promoted_to` (checkpoint → serving alias) の 3 edge
- BPMN-as-actor (ADR-0056) で `train.sft.run` / `train.lora.run` /
  `train.distill.run` / `train.eval.run` / `train.promote.checkpoint` の
  5 pyzeebe primitive
- Vultr GPU pod (ADR-0068) を Zeebe worker target とした実行
- Weight artifact の B2 永続化 (`etzhayyim-training-data/v1/checkpoints/...`)
  と Kotoba/Datomic 側 reference の分離

Out:
- 既に live な corpus export 経路 (`v_training_text` / `v_training_triple`
  → B2 shard → HF Hub `etzhayyim/etzhayyim-corpus`) — このまま train run の
  入力として使う。再設計しない
- Hume distillation artifact (ADR-2604300135) — `vertex_ingest_artifact`
  に既に永続化されている。本 ADR はそれを **train run の入力と teacher
  source として参照** するのみで、Hume 側の経路は変更しない
- Browser side (Ameno / `2604291630-yoro-guest-projector-browser-gemma-e2b`)
  の WebGPU per-actor LoRA — そちらは LoRA artifact が browser-local で、
  本 ADR は server-side の base model + adapter weight 育成に閉じる
- Pretraining from scratch — base は HF / 既存 OSS から開始する前提

# Executive Summary

Corpus → shard → HF push までは既に live。足りないのは **weight 側の
lineage と train run actor**。Kotoba/Datomic schema 4 vertex + 3 edge と
BPMN-as-actor 5 primitive を加え、weight artifact 自体は B2 に置いて
RW には reference だけを持たせる (Hume と同型、ADR-2604300135 の
2-store layout を継承)。serving への昇格は `edge_training_promoted_to`
を 1 行追加する操作で表現し、Murakumo / RunPod 側はその alias を
読むだけにする。

# Decision

## 1. Schema (Kotoba/Datomic, ADR-0036 / ADR-0044 準拠)

新規 migration 1 本 (`30-graph/graph-schema/migrations/{ts}_vertex_training_lineage.ts`):

### vertex (4)

| table | 役割 | 主要列 |
|---|---|---|
| `vertex_training_dataset_snapshot` | corpus shard セットの不変スナップショット (HF push 単位 or B2 prefix 単位) | `vertex_id`, `dataset_name`, `b2_prefix`, `shard_count`, `row_count`, `content_hash`, `hf_revision`, `created_at` |
| `vertex_training_run` | 1 回の train run | `vertex_id`, `run_id`, `kind` (`sft`/`lora`/`dpo`/`distill`), `base_model`, `dataset_snapshot_id`, `hyperparams_json`, `gpu_target`, `status` (`queued`/`running`/`done`/`failed`), `started_at`, `ended_at` |
| `vertex_training_checkpoint` | run の途中・最終 weight | `vertex_id`, `run_id`, `step`, `weight_b2_uri`, `weight_byte_size`, `weight_sha256`, `is_final`, `created_at` |
| `vertex_training_eval` | checkpoint の評価結果 | `vertex_id`, `checkpoint_id`, `bench_name`, `metrics_json`, `eval_dataset_snapshot_id`, `created_at` |

### edge (3)

| edge | semantics |
|---|---|
| `edge_training_consumed_dataset` | `run_id → dataset_snapshot_id` (input corpus) |
| `edge_training_distilled_from` | `student_run_id → teacher_did_or_run_id` (LLM teacher = `did:web:llm.etzhayyim.com` Murakumo の logits、Hume teacher = `vertex_ingest_artifact.run_id`) |
| `edge_training_promoted_to` | `checkpoint_id → serving_alias` (`alias` = `murakumo:gemma4-e4b-it@20260507`, `runpod:9z9l2nzwugnqyu` 等)。alias 1 つに対して **active な edge は最大 1 本** (UNIQUE は RW 非対応、app-layer で enforce) |

### MV (2 streaming, < 100ms freshness)

- `mv_training_run_status` — kind 別の queued/running/done/failed 内訳
- `mv_training_active_serving` — `edge_training_promoted_to` の最新行のみを
  alias 別に出す (serving 側はこれを読む)

## 2. BPMN-as-actor (ADR-0056)

新規 BPMN 5 本を `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/training/` に追加し、
`vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding` に seed (F5 watcher が
Zeebe deploy する既存規約)。

| BPMN process | trigger | task chain |
|---|---|---|
| `train_sft_run` | XRPC `com.etzhayyim.apps.training.runSft` | `train.dataset.snapshot` → `train.sft.run` (GPU pod) → `train.eval.run` → audit |
| `train_lora_run` | XRPC `com.etzhayyim.apps.training.runLora` | 同上 (LoRA adapter only) |
| `train_distill_run` | XRPC `com.etzhayyim.apps.training.runDistill` | `train.dataset.snapshot` → `train.teacher.label` (Murakumo bulk infer) → `train.distill.run` → `train.eval.run` → audit |
| `train_eval_run` | XRPC `com.etzhayyim.apps.training.runEval` | `train.eval.run` → audit |
| `train_promote_checkpoint` | XRPC `com.etzhayyim.apps.training.promote` | `train.promote.checkpoint` (edge insert) → audit |

`generic.audit.emit` (ADR-0056 primitive) を全 BPMN の終端に置き、
OCEL event を `vertex_repo_commit` に残す。

## 3. pyzeebe primitives (`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/training_run.py`)

5 task handler を追加し、`zeebe_worker_main.py` に register hook を加える。
GPU が要る handler は **`mitama-training-pool` Helm release** (新設、ADR-0048
の shosha-pool 同型) に分離してデプロイし、`mitama-udf-pool` の CPU worker
を妨げない。

| task type | 実装方針 |
|---|---|
| `train.dataset.snapshot` | `v_training_text` / `v_training_triple` の指定 label を B2 に shard 化 (既存 `task_training_export_text` を再利用) → `vertex_training_dataset_snapshot` insert |
| `train.sft.run` / `train.lora.run` | `transformers` + `trl` (or `peft`) で fine-tune、step ごとに `vertex_training_checkpoint` insert + B2 PUT。base model = HF revision pin |
| `train.distill.run` | teacher logits は (a) Murakumo bulk infer の出力 JSONL を B2 に置き Hume と同型で `vertex_ingest_artifact` に index、(b) Hume distillation artifact (ADR-2604300135) を直接 input にする、の 2 経路を受ける |
| `train.eval.run` | lm-eval-harness 互換の thin wrapper、`metrics_json` に MMLU / 自前 bench (ADR-2604282100) のスコアを格納 |
| `train.promote.checkpoint` | `edge_training_promoted_to` に 1 行 insert、同 alias の旧行は `_alive` 削除 (ADR-0036 hard delete) |

## 4. Weight artifact 永続化 (Hume と同型の 2-store)

- **B2**: `etzhayyim-training-data/v1/checkpoints/{run_id}/step-{NNNNNN}.safetensors`
  + `tokenizer.json` + `training_args.json`。LoRA は adapter のみで数十 MB
  〜数百 MB、SFT 全 weight は数 GB。Hummock に置かない (ADR-2604261900 の
  hot-path DDL 回避と同じ理由で巨大 blob を OLAP に持たせない)
- **Kotoba/Datomic**: `vertex_training_checkpoint` に `weight_b2_uri` + `weight_sha256`
  + `weight_byte_size` のみ。serving 側はこの URI を読み、Murakumo /
  RunPod の起動時に B2 から pull する

## 5. Serving 側との接続 (read-only)

- Murakumo (`murakumo.etzhayyim.com`, ADR-2604292130) と RunPod fleet は
  `mv_training_active_serving WHERE alias = ?` で現役 weight URI を取得
- `train.promote.checkpoint` の edge insert が serving alias 切替の唯一の操作
- 旧 alias の checkpoint は B2 上に残す (rollback 可能、retention は別ポリシー)

## 6. CLI / XRPC entry

- `etzhayyim training run --kind sft --base gemma-4-e4b-it --dataset etzhayyim-corpus@latest`
  → bpmn-dispatcher ClusterIP `http://dispatcher.etzhayyim.com:8080/xrpc/com.etzhayyim.apps.training.runSft`
- `etzhayyim training promote <checkpoint_id> --alias murakumo:gemma4-e4b-it`
- `etzhayyim training list-runs` / `list-checkpoints` / `eval <checkpoint_id>`
- 全 XRPC は ADR-2604282300 に従い T2 (BPMN-as-actor) で CF Worker を持たない

# Rationale

- **既存資産の最大活用**: corpus export と Hume distillation artifact は
  すでに RW + B2 + IPFS で persist されている。本 ADR はその上に **run +
  checkpoint + eval** という縦の lineage を 1 層足すだけ
- **Hummock 非肥大化**: weight body は B2、RW は metadata のみ。ADR-0048
  の B2 server-side copy 教訓 (Linode → Vultr 7.63 TiB 移行) を踏まえ、
  巨大 blob を Hummock 上で動かす負債を作らない
- **Serving と train の分離**: 切替は edge 1 行 insert、serving Worker は
  MV を読むだけ。train pod の落ちは serving に波及しない
- **BPMN-as-actor 規約遵守**: 新規 actor = INSERT N rows + F5 watcher で
  Zeebe deploy という ADR-0056 規約に乗る。CF Worker 増やさない
- **Distillation の対称性**: LLM teacher (Murakumo logits) と Hume teacher
  (expression labels) を同じ `edge_training_distilled_from` で表現でき、
  multi-modal な student も将来表現可能

# Comparison

| 案 | weight 保管 | lineage SSoT | 採否 |
|---|---|---|---|
| **本 ADR** (B2 + RW reference + BPMN actor) | B2 | RW vertex + edge | ✅ |
| weight も RW (Hummock) に bytea で保存 | RW | RW | ❌ — Hummock 肥大、ADR-0048 教訓に反する |
| 全部 HF Hub に投げて lineage も HF model card に書く | HF | HF | ❌ — repo の SSoT が外部依存になり、`etzhayyim training list-runs` が SQL で答えられない |
| MLflow / W&B を立てる | 外部サーバー | 外部 | ❌ — 既存 RW + BPMN + Vultr GPU stack に追加運用コスト。Shannon η 低下 |
| Hume ADR-2604300135 を train run にも流用 (`vertex_ingest_artifact` に全部) | B2 + RW (汎用) | RW (kind 列で識別) | △ — 短期は可、ただし `run` / `checkpoint` / `eval` の関係 (run → step → eval) を edge で表現できないので長期は専用 vertex が要る |

# Exceptions

- **Browser-local LoRA** (Ameno / yoro-guest-projector) は本 ADR の対象外。
  WebGPU 上の per-actor adapter は browser-local IndexedDB に置き、
  RW lineage には乗せない。server に持ち上げる場合のみ
  `vertex_training_checkpoint` に登録する
- **Pretraining**: from-scratch pretrain は本 ADR の `kind` enum に含めない
  (`sft` / `lora` / `dpo` / `distill` の 4 種で開始)。必要になった時点で
  `kind = 'pretrain'` を addendum で足す
- **緊急 hotfix**: 評価をスキップして直接 promote する経路は **設けない**。
  `train.eval.run` を必ず 1 回通す。eval が落ちても `metrics_json` に
  失敗を残せば promote 自体は可能 (ガードレールではなく audit trail)

# Addendum 2026-05-07 — GPU 実行先は RunPod Serverless

初版の §3 / §6 / Comparison は GPU 実行先として **Vultr GPU node pool** を仮置き
していたが、運用上の負担と費用効率から **RunPod Serverless** を canonical な
GPU バックエンドとして採用する。CPU pod (`mitama-training-pool`) は orchestrator
のまま、heavy task (sft / lora / distill / eval) は RunPod に job submit して
poll する形に変更する。

## 変更点

- §1 schema (4 vertex + 3 edge + 2 MV) — **無変更**。lineage は GPU 実行先に
  非依存
- §2 BPMN-as-actor (5 process + 5 binding) — **無変更**。task 名 (`train.sft.run`
  等) は RunPod 経路でも同じ
- §3 pyzeebe primitives — **変更**:
  - `train.dataset.snapshot` / `train.promote.checkpoint` / `train.teacher.label`
    は CPU 上の primitive のまま (snapshot は SQL aggregate、promote は edge
    insert、teacher.label は Murakumo HTTP)
  - `train.sft.run` / `train.lora.run` / `train.distill.run` / `train.eval.run`
    は **RunPod Serverless client** に refactor: payload を `/v2/{endpoint}/run`
    に POST → status poll → 完了時に handler 側が `vertex_training_checkpoint` /
    `vertex_training_eval` に直接 INSERT (RunPod handler が kotodama を同梱
    し KOTOBA_URL Secret を持つため、worker と同じ書き込み経路)
- §3 GPU pod 用 helm 値 (`gpuEnabled` / `nvidia.com/gpu`) — **削除**。
  CPU pod は worker profile=training の薄い orchestrator として固定。GPU
  capacity 計画不要、idle 時 cost 0
- §6 CLI — **無変更**。`etzhayyim training run` の payload は同じで、PDS →
  bpmn-dispatcher → CPU worker → RunPod の経路に流れるだけ

## RunPod Serverless 構成

| 項目 | 値 |
|---|---|
| Endpoint id | `RUNPOD_TRAINING_ENDPOINT_ID` (Secret `training-runpod-creds`) |
| Handler image | `ghcr.io/etzhayyim/kotodama-runpod-trainer:{tag}` (`90-docs/adr/2605010000-runpod-6000ada-unified-pod.md` の image 系統に合流可能) |
| Handler entry | `runpod.serverless.start({"handler": handler})` — `handler(event)` が `event["input"]` (kind / runId / baseModel / datasetSnapshotId / hyperparams / teacherLabelArtifactRunId) を受けて training を実行 |
| 重みアップロード | handler 内で B2 PUT (`B2_*` Secret 同じものを RunPod env に注入) |
| RW write | handler 内で psycopg + Hyperdrive 経由で `vertex_training_checkpoint` INSERT (KOTOBA_URL を Secret から RunPod env に注入) |
| GPU type | RTX 6000 Ada / RTX 4090 / A40 / A100 (Serverless template で flashboot=on, workersMin=0, workersMax=4) |
| Job kind | sync (`/runsync`, ≤ 30s) は使わない / async (`/run` + `/status/{id}` poll) を使用、TTL ≤ 24h |
| Auth | API key `Bearer ${RUNPOD_API_KEY}` (Secret `training-runpod-creds`) |
| Output | `{ ok, runId, runVertexId, finalCheckpointId, finalCheckpointVertexId, stepCount, error }` ── 構造は worker 側 task が直接返す形と同型 |

## CPU pod 側の責務 (refactor 後)

```
etzhayyim training run --kind sft ...
  ↓ atproto.etzhayyim.com PDS
  ↓ bpmn-dispatcher (K8s ClusterIP)
  ↓ Zeebe service task → mitama-training-pool worker
[CPU pod]
  ├─ train.dataset.snapshot              直接 RW write
  ├─ train.teacher.label                 Murakumo HTTP + B2 PUT + vertex_ingest_artifact
  ├─ train.sft.run / .lora.run /         RunPod /run POST → poll /status → return
  │  .distill.run / .eval.run            (heavy GPU work は RunPod 側、checkpoint
  │                                       INSERT も RunPod handler 内)
  └─ train.promote.checkpoint            edge_training_promoted_to の retire+insert
```

## Trade-offs (Vultr GPU pool 案との比較)

| 軸 | RunPod Serverless (採用) | Vultr GPU node pool (却下) |
|---|---|---|
| Idle cost | $0 (workersMin=0) | 月額固定 ($800-2000/GPU node) |
| Spin-up latency | flashboot 5-15s + cold start ~30s | K8s schedule + image pull (既存 pool なら ~10s) |
| Capacity 調整 | autoscale 0..N (RunPod 側) | manual node pool 増減 + helm reconcile |
| GPU 種類変更 | endpoint template 切替 | node pool 再作成 |
| Long-running job | TTL 24h、超過は Pod モードへ | 無制限 |
| 既存運用知見 | RunPod 9z9l2nzwugnqyu (yoro-chat-gemma4) で実績あり | Vultr GPU pool は未経験 |
| Lineage 整合性 | RunPod handler が同じ kotodama image を持ち、同じ RW + B2 経路で書く → 一致 | 同上 (worker pod が直接書くだけ) |

判定: **idle cost 0 と既存運用知見** が決定的。GPU 専有が必要になる将来案件
(72h+ pretrain 等) は Pod モード or Vultr GPU pool の addendum で再評価する。

## Follow-up

1. `ghcr.io/etzhayyim/kotodama-runpod-trainer` image を別 Dockerfile で build
   (handler.py + runpod-python + transformers + peft + trl + accelerate +
   torch CUDA wheel)。CPU pool image (`kotodama:0.3.78+`) からは peft /
   accelerate を削除して image を軽くする
2. Secret `training-runpod-creds` (`RUNPOD_API_KEY` + `RUNPOD_TRAINING_ENDPOINT_ID`)
   を `mitama-udf` namespace に provision (Keychain `etzhayyim.runpod` から)
3. `mitama-training-pool/values.yaml` の `gpuEnabled` flag と nvidia.com/gpu
   block を削除し、`runpod` env block を追加
4. `task_train_sft_run` / `task_train_lora_run` / `task_train_distill_run` /
   `task_train_eval_run` を `_runpod_submit_and_wait()` 経由の thin client
   に refactor

# Addendum-of-Addendum 2026-05-07 — 統合 RunPod Pod 上の HTTP 同居に切替 (cost 最適化)

直前 Addendum (RunPod Serverless) を **退役** し、**ADR-2605010000 で既に立て
ている always-on RunPod 6000 Ada Pod (`58pvflvw9w6nt3`)** を training にも
転用する。同 Pod は ComfyUI :8188 / vLLM :8000 / LiteLLM :4000 を 24/7 host
しており GPU 48 GB は idle 時間に余裕があるため、training を 4 つ目の process
(:8003) として同居させて GPU を再利用する。

## なぜ Serverless でなく同居か

| 観点 | RunPod Serverless (中止) | 統合 Pod 同居 (採用) |
|---|---|---|
| 月額コスト (training 専用) | $0 idle + per-job $0.000388/sec × 累計 | $0 incremental ($554/mo Pod は ComfyUI/vLLM で既に必要) |
| spin-up latency | 30s flashboot | 0s (常駐) |
| 別 image build/push 工数 | 必要 (~5 GB CUDA image) | 不要 (既存 image に layer 追加) |
| operator 認知負荷 | endpoint id + API key + workersMin/Max + flashboot 設定 | URL 1 つ + auth token (任意) |
| GPU 競合 | なし (隔離) | ComfyUI 推論と GPU 取り合い (48 GB は十分余裕、queue で直列化) |

判定: **incremental cost = $0**、**operator 認知負荷低下**、**両 Pod の image
重複排除**。GPU 競合は queue (HTTP server で 1 job ずつ実行) で吸収可能。

## 変更点 (Addendum 1 から)

- §3 pyzeebe primitive: `_runpod_submit_and_wait` (RunPod Serverless API) →
  `_pod_submit_and_wait` (統合 Pod の HTTP server)。wire-format は両方とも
  `{"input": {...}}` POST + `/status/{id}` poll なので、`runpod_handler(event)`
  の中身は無変更
- §3 GPU image: `Dockerfile.runpod-trainer` (Serverless) を **削除**。
  `50-infra/runpod/vllm-gemma-image/Dockerfile` (ADR-2605010000) に
  training tooling layer を追加 (peft / trl / accelerate / lm_eval /
  kotodama を `/opt/venv-train` にインストール)
- §3 GPU 起動: 新規 `start-train.sh` が `kotodama.training_http_server` を
  :8003 で起動。base image の `/start.sh` wrapper が ComfyUI 後にこれも
  background-launch
- §3 Helm values: `RUNPOD_API_KEY` / `RUNPOD_TRAINING_ENDPOINT_ID` env →
  `TRAINING_POD_BASE_URL` + `COMFYUI_POD_BASE_URL` + `TRAINING_POD_AUTH_TOKEN`
  (Secret `training-runpod-creds` → `training-pod-creds` に rename)
- §3 image-domain LoRA training: ComfyUI workflow 経由 (path C native)。
  `kijai/ComfyUI-FluxTrainer` custom node を base image に同梱、pyzeebe
  primitive が ComfyUI :8188 `/prompt` に workflow JSON を POST
- 削除: `kotodama.runpod_trainer_handler` / `kotodama.runpod_trainer_entry`
  (Serverless 専用、Pod HTTP では `kotodama.training_http_server` が直接
  `runpod_handler` を呼ぶので不要)

## 統合 Pod のポート割当

| Port | Process | Purpose |
|---|---|---|
| :22 | sshd | RunPod ops debugging (base image) |
| :4000 | LiteLLM | OpenAI-compat gateway (LLM read path) |
| :8000 | vLLM | LLM inference |
| :8003 | **training_http_server** | **`/train/run` + `/train/status/{id}`** |
| :8188 | ComfyUI | image generation + image LoRA training (custom node) |

## Auth model

- **CPU pod → :8003**: `Authorization: Bearer ${TRAINING_POD_AUTH_TOKEN}` 必須
  (k8s Secret `training-pod-creds`)。Pod side の HTTP server が同 token を env
  から読み突合。RunPod proxy URL `https://58pvflvw9w6nt3-8003.proxy.runpod.net`
  はパス予測不能だが public なので token gate を必ず立てる
- **CPU pod → :8188 (ComfyUI)**: 既存 ComfyUI auth (none / API key) を継承。
  workflow JSON だけ送る、weight upload は handler 内で B2 SigV4 直書き

## 残作業 (この addendum 採用時)

1. 既存 `50-infra/runpod/vllm-gemma-image/` image の rebuild + RunPod template
   image tag 更新 (CI workflow `runpod-vllm-gemma-image.yml` を `push` で trigger)
2. RunPod Pod `58pvflvw9w6nt3` の env vars 追加: `KOTOBA_URL`, `B2_*`,
   `HF_TOKEN`, `TRAINING_POD_AUTH_TOKEN`
3. K8s Secret `training-pod-creds` (`TRAINING_POD_AUTH_TOKEN` のみ) を
   `mitama-udf` namespace に provision (既存 `training-runpod-creds` は退役)
4. `kotodama:0.3.80` image rebuild + helm upgrade
5. ComfyUI custom node `ComfyUI-FluxTrainer` の動作確認 + image LoRA training
   primitive (`task_train_image_lora_run`) 追加 (Phase 2、本 PR では未着手)

# References

- `30-graph/graph-schema/migrations/20260502120000_v_training_text.ts`
- `30-graph/graph-schema/migrations/20260502130000_seed_training_export_bpmn.ts`
- `30-graph/graph-schema/migrations/20260502140000_update_training_export_bpmn_phase_d.ts`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/training_export.py`
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/training/trainingExport.bpmn`
- `90-docs/adr/2604300135-hume-distillation-artifact-persistence.md`
- `90-docs/adr/0056-bpmn-as-actor.md` (`90-docs/adr/2604231150-bpmn-as-actor.md`)
- `90-docs/adr/0036-worker-direct-hyperdrive-persistence.md`
- `90-docs/adr/0044-kotoba-udf-language-strategy.md`
- `90-docs/adr/2604282100-llm-bench-gemma4-default-self-hosted.md`
- `90-docs/adr/2604292130-llm-etzhayyim-ai-runpod-pass.md`
- `90-docs/adr/2605010000-runpod-6000ada-unified-pod.md`
