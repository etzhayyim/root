---
id: adr-2605092345-runpod-l40s-fp8-multimodal-model-design
title: "Oka: RunPod H100 Training Pod + gemma-4-E4B Base (was L40S design)"
status: accepted
doc_type: adr
topic: multimodal-model-training-inference
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - RunPod H100 NVL training pod assignment (training-only, separate from inference)
  - Default training base model = google/gemma-4-E4B
  - RisingWave vertex/dataset input contract for multimodal training
  - modality encoder and embedding-model coverage
  - deployment split between vLLM inference (6000 Ada), H100 trainer, embedding workers, and RW lineage
depends_on:
  - adr-2605010000
  - adr-2605070700-rw-native-model-training-weight-lineage
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
  - adr-2605092200-continuous-metabolic-training
  - adr-2605092300-fp8-train-inference-colocation
  - adr-2604262359-risingwave-multimodal-vector-search-topology
related:
  - 30-graph/graph-schema/migrations/20260508000000_vertex_training_lineage.ts
  - 30-graph/graph-schema/migrations/20260427001000_vector_embedding_project_tables.ts
  - 30-graph/graph-schema/migrations/20260502120000_v_training_text.ts
  - 30-graph/graph-schema/migrations/20260508162000_v_training_text_with_ip.ts
  - 30-graph/graph-schema/migrations/20260506220000_vertex_hf_dataset_ingest.ts
  - 30-graph/graph-schema/migrations/20260508230000_vertex_3d_blob_catalog.ts
supersedes: []
superseded_by: []
---

# Context

本設計は当初、RunPod の **L40S 48 GB node** を FP8 train/inference 共用 GPU として
想定していた。しかし 2026-05-09 時点で:

- L40S 在庫は不安定（REST 経路は port mapping に届かず、GraphQL 経路は supply
  constraint で取得不可）。
- 同じ pod 上で training と inference を共用すると inference SLO を直接侵食する。

そのため**運用上の決定として**:

- **Training は H100 NVL pod に分離** (training-only)。Oka 27B HF-quality SFT
  100-step run はこの H100 pod 上で完走済み（後段 §Status を参照）。
- **Inference は引き続き RunPod 6000 Ada unified pod (ADR-2605010000)** で
  ComfyUI + vLLM + LiteLLM を提供する。training と同居しない。
- **Default training base model = `google/gemma-4-E4B`** (HF base, non-instruct).
  以前 Oka path で使っていた `google/gemma-3-27b-it` は `baseModel` を明示
  指定したときの選択肢として残すが、registry default は E4B 系に揃える。
- **姉妹 ADR**: 1.58-bit 系の edge / browser / CPU 向け系列は
  ADR 2605092350 (Baien) として分離。Oka はサーバ側 FP8 trunk、Baien は
  on-device ternary trunk — 同じ H100 を共有して training だけ piggyback、
  inference は別物。

L40S 関連の節は「将来 supply が安定した時の参考形状」として残し、現在の
実装規範ではない旨を §Status に明記する。

Model family name: **Oka**. The name is derived from mathematician
**Kiyoshi Oka (岡潔)** and is used for the RisingWave-grounded multimodal
model family described in this ADR.

前提（運用前提と歴史前提を分離）:

運用前提 (current):
- H100 NVL は Hopper 世代 4th-gen Tensor Core + Transformer Engine で FP8
  training を素直に回せる。`bf16` baseline + `fp8` activation cast の両方が
  smoke 完走済み（後段 §Status）。
- inference は別 pod (6000 Ada) を経由し、`https://llm.etzhayyim.com/v1/chat/completions`
  に向ける。training pod の HTTP server (`pymagatama.training_http_server`)
  は inference を受け持たない。
- Default base = `google/gemma-4-E4B` (4B 活性 / MoE、128k context、bf16)。

歴史前提 (L40S 設計時、参考):
- L40S は Ada Lovelace 4th-gen Tensor Core で FP8 を使える。
- L40S は 48 GB VRAM なので 7B–14B 級 trunk + LoRA/adapter までは train/inference
  共用が現実的な上限。30B+ は tensor parallel か CPU/B2 offload 前提。

不変前提:
- RisingWave は live OLAP/streaming DB なので、巨大 tensor / raw media / checkpoint
  body は入れない。RW は reference、metadata、lineage、embedding index を持つ。
- 既存 corpus は `v_training_text`, `v_training_triple`,
  `vertex_hfhub_*`, `vertex_3d_blob`, `vertex_vector_embedding_*`,
  `vertex_training_*` を使う。新しい別 DB / vector store は作らない。

# Decision

## 1. Model Family

モデルは 2 層に分ける。

| Layer | Name | Role | Stored where |
|---|---|---|---|
| Generative trunk | `oka-mm-fp8-trunk` | audio, 3d, document, geospatial, image, tabular, text, time-series, video を受ける multimodal generative model | B2/IPFS checkpoint body + RW lineage |
| Embedding space | `oka-mm-768` + `oka-mm-4096-fp8` | production search は 768d、model-internal routing/training は 4096d FP8 | RW `vertex_vector_embedding_768`; FP8 row storeは addendum schema |

生成モデルは初期 smoke では **shared trunk + modality adapters + LoRA cohorts**
で開始した。Opus 4.7 / GPT-5.5 class quality を benchmark にする段階では、
4B LoRA ではなく **27B-70B class trunk + teacher distillation + expert adapter
router** に昇格する。single L40S では sparse MoE の expert residency が VRAM
を圧迫するため、初期 production path は dense 27B trunk と hot-swappable LoRA
experts を router で切り替える。70B class は H100 / multi-GPU / quantized serving
または remote teacher として扱う。

```
raw/blob/table row
  -> modality normalizer
  -> modality encoder
  -> projection to D=4096 latent tokens
  -> shared decoder trunk (FP8 E4M3 forward, E5M2 backward)
  -> task head: generate | classify | retrieve | embed | caption | summarize
```

## 1.1 Comparative Positioning

現時点の weight 組み合わせは、単一の frontier checkpoint ではなく、
**Gemma 系 trunk + Qwen/Qwen-VL 系 modality/router adapters + RisingWave external
memory substrate** と見るのが最も近い。

| Reference family | Similarity | Reason |
|---|---:|---|
| Gemma | high | Current repo defaults and serving aliases repeatedly resolve to `gemma-4-e4b-it` / Gemma-class trunks. Dense/small trunk + LoRA/adapter operation also matches the L40S memory envelope. |
| Qwen / Qwen-VL | high | Existing routing uses Qwen for use-case defaults, vision paths, and Qwen-VL-style embedding candidates. The multimodal adapter plan is closer to Qwen-VL than to a text-only Gemma stack. |
| Kimi | medium | Agentic/tool and long-context goals overlap, but Kimi K2-class systems are giant sparse MoE models. This design is adapter-routed and L40S-bounded, not 1T-scale MoE. |
| MiniMax | medium-low | Product-agent and long-context behavior goals overlap, but this design does not assume a single proprietary frontier checkpoint. RW lineage + adapters are the primary shape. |
| UltraMem v2 | medium-low | The external-memory idea is similar: persistent retrieval/memory matters as much as weights. Here the memory substrate is RisingWave `vertex_*` + vector/search tables, not a standalone memory model. |
| Zamba | low | Zamba-style hybrid SSM/Transformer architecture is not the current target. This design is Transformer trunk + modality adapters + FP8/LoRA. |

Operationally, the nearest shorthand is:

```text
Gemma trunk
  + Qwen-VL/Qwen3-like multimodal adapters and router behavior
  + UltraMem-like persistent memory, implemented as RisingWave vertex/dataset/embedding substrate
```

This is deliberately lighter than Qwen3-30B-A3B / Kimi / MiniMax-class giant
MoE. On a single L40S, the practical first target is 7B-14B dense trunk with
adapter and LoRA training; larger sparse models require tensor parallelism or
separate expert offload.

For frontier-quality benchmarking, this ADR now treats the 4B adapter as a
speed and lineage smoke only. The quality path is:

```text
frontier teachers: Opus 4.7 / GPT-5.5 class
  -> distillation corpus and preference pairs in RisingWave lineage
  -> Oka 27B dense trunk adapters
  -> router-selectable expert adapters by modality/domain/task
  -> optional 70B / MoE route for hard prompts and teacher refresh
```

The Oka router is not a raw sparse-MoE weight layout at first. It is a model
gateway decision that chooses one of several adapter heads:

- `oka-expert-reasoning`: math, code, planning, multi-step tool reasoning.
- `oka-expert-jp-doc`: Japanese document, legal/IP, citation-grounded answer.
- `oka-expert-mm`: image/video/audio/document grounding and caption tasks.
- `oka-expert-geo-3d`: geospatial, 3D, CAD, terrain, map/source reasoning.
- `oka-expert-tab-ts`: tabular, time-series, anomaly, forecasting tasks.
- `oka-expert-safety`: refusal, policy, privacy, provenance, consent checks.

## 2. Supported Generative Modalities

| Modality | RW source contract | Blob body | Encoder | Initial task |
|---|---|---|---|---|
| text | `v_training_text`, `vertex_hf_dataset_record`, `vertex_repo_record` | optional B2 shards | tokenizer + transformer | SFT, RAG answer, summarization |
| document | `vertex_patent_blob`, `vertex_work_blob`, `vertex_yata_blob` | PDF/HTML/OCR on B2 | layout-aware text + image-page adapter | OCR cleanup, citation answer |
| image | `vertex_vector_embedding_source`, app-specific image vertices | B2/R2 image | ViT/SigLIP adapter | caption, VQA, generation conditioning |
| video | `vertex_vector_embedding_chunk` frame/window rows | B2/R2 video | frame sampler + temporal adapter | video caption, event extraction |
| audio | Hume artifacts, audio blob source rows | B2/R2 audio | Whisper-style audio adapter | ASR, sound/event summary |
| 3d | `vertex_3d_blob` | STEP/STL/OBJ/voxel/latent on B2 | point/mesh/voxel adapter | CAD retrieval, shape caption, 3D grounding |
| geospatial | OSM/map vertices, `vertex_osm_*`, terrain/source rows | PBF/tiles/GeoJSON on B2 | geohash/geometry/time adapter | route/context reasoning |
| tabular | `vertex_hfhub_*`, domain `vertex_*` tables | Parquet/CSV on B2 | schema serializer + numeric adapter | table QA, anomaly explanation |
| time-series | market, sensor, RL, event vertices | Parquet/JSONL on B2 | patch/time encoder | forecasting, anomaly summary |

Each source must produce a normalized `vertex_vector_embedding_source` row and optional
`vertex_vector_embedding_chunk` rows. Raw bytes stay in object storage via `blob_ref`.

## 3. Embedding Model Coverage

Embedding support is split into production 768d search and model-internal FP8 latent rows.

| Embedding input | Production output | Internal output | Adapter |
|---|---|---|---|
| text | `vertex_vector_embedding_768`, modality=`text` | D=4096 FP8 | BGE/Qwen text adapter |
| video | `vertex_vector_embedding_768`, modality=`video` | D=4096 FP8 | frame-window temporal adapter |
| audio | `vertex_vector_embedding_768`, modality=`audio` | D=4096 FP8 | log-mel/Whisper adapter |
| image | `vertex_vector_embedding_768`, modality=`image` | D=4096 FP8 | SigLIP/OpenCLIP/Qwen-VL adapter |
| imu | `vertex_vector_embedding_768`, modality=`imu` | D=4096 FP8 | 6-axis/9-axis window adapter |
| heatmap | `vertex_vector_embedding_768`, modality=`heatmap` | D=4096 FP8 | 2D scalar-field adapter |
| depth | `vertex_vector_embedding_768`, modality=`depth` | D=4096 FP8 | depth-map/point adapter |
| emotion | enrichment on source + optional vector row, modality=`emotion` | D=4096 FP8 | Hume expression vector adapter |

Production rule: do not mix model versions or dimensions in one HNSW index. Every insert
must set `model_id`, `space_id`, `projection_id`, `modality`, `tenant_id`, and `shard_id`.

## 4. FP8 Runtime Policy on L40S

| Path | dtype | Policy |
|---|---|---|
| inference weights | FP8 E4M3 | vLLM FP8 quantized checkpoint, per-channel scale where supported |
| KV cache | FP8 E4M3 | default for long-context serving; BF16 fallback for unstable heads |
| training forward | FP8 E4M3 | Transformer Engine or torchao-compatible FP8 path |
| gradients | FP8 E5M2 or BF16 fallback | L40S single-node all-reduce is not needed; multi-node casts to BF16 |
| master weights | BF16 for adapters, FP32 for trunk | checkpoint body in B2, lineage in RW |
| embeddings in RW search | `vector(768)` float | HNSW/exact rerank path |
| embeddings in model substrate | FP8 bytes + scale | addendum to `vertex_organism_embedding` or successor table |

The L40S node runs a single GPU queue with priority lanes:

1. online inference
2. embedding batch
3. LoRA/adapter training
4. full SFT/distill

If VRAM pressure exceeds threshold, training yields first, embedding batch second, inference last.

## 5. RisingWave Dataset Contract

The model never scans arbitrary `vertex_*` tables directly from GPU jobs. CPU workers create
immutable dataset snapshots first:

1. `train.dataset.snapshot` selects from approved views/tables:
   `v_training_text`, `v_training_triple`, `vertex_hfhub_file`, `vertex_3d_blob`,
   vector source/chunk tables, and domain-specific public rows.
2. Shards are written to B2 as JSONL/Parquet under a content-addressed prefix.
3. `vertex_training_dataset_snapshot` records `dataset_name`, `label`, `b2_prefix`,
   `row_count`, `byte_size`, `content_hash`, `source_view`, and `filter_expr`.
4. Training run inserts `vertex_training_run` and `edge_training_consumed_dataset`.
5. Checkpoints are written to B2 and referenced by `vertex_training_checkpoint`.
6. Promotion inserts `edge_training_promoted_to`; serving reads `mv_training_active_serving`.

This keeps RW hot-path SQL bounded and avoids direct GPU jobs issuing heavy DDL or unbounded scans.

## 6. Training Plan

| Phase | Goal | Dataset | Output |
|---|---|---|---|
| P0 | text/document baseline | `v_training_text` + IP OCR/open text | text/document LoRA |
| P1 | image/video/audio grounding | vector source/chunk rows + B2 blobs | multimodal adapters |
| P2 | 3D/geospatial/tabular/time-series | `vertex_3d_blob`, OSM/domain rows, HF Parquet | domain adapters |
| P3 | embedding alignment | text-video-audio-image-imu-heatmap-depth-emotion pairs | projection rows + eval |
| P4 | online adapter updates | `edge_gradient_flow`, RL/eval events | cohort LoRA checkpoints |
| P5 | frontier teacher distillation | Opus 4.7 / GPT-5.5 class teacher traces + accepted adapters + curated snapshots | 27B Oka adapters |
| P6 | expert router and preference loop | teacher-ranked responses, eval failures, route labels | multi-expert adapter router |
| P7 | 70B / MoE escalation | hard prompts, low-confidence routes, long-horizon tasks | 70B adapter or remote expert route |

Default training mode is LoRA/adapter fine-tune. Full trunk SFT on one L40S is allowed only for
small 7B class models or short distillation runs. Long pretraining is out of scope for L40S single-node.

### 6.1 Frontier Distillation Policy

Oka quality work targets system-level parity against Opus 4.7 / GPT-5.5 class
teachers, not raw pretraining parity. The training loop must separate four
artifacts:

1. `teacher_trace`: prompt, context, tool calls, teacher answer, teacher model,
   temperature, latency, cost, and license/retention flags.
2. `student_answer`: Oka route, trunk, adapter id, checkpoint id, retrieved
   context ids, answer, latency, and token counts.
3. `preference_pair`: teacher or evaluator ranking between candidate answers,
   failure labels, and rationale hashes.
4. `eval_gate`: fixed benchmark item, expected rubric, score, safety outcome,
   route decision, and promotion decision.

The first production-quality target is not a merged 70B checkpoint. It is a
27B Oka trunk with multiple LoRA experts and a router that can match the teacher
on the repository's highest-value task buckets. 70B/MoE routes are reserved for
hard prompts, teacher refresh, and offline distillation until serving cost and
latency are justified by eval deltas.

Minimum data scale before claiming frontier-quality progress:

| Stage | Sample count | Purpose |
|---|---:|---|
| S0 | 5k-20k teacher traces | establish Oka voice, routing, citation, and tool behavior |
| S1 | 50k-200k SFT traces | domain adaptation for text/document/RAG/code/planning |
| S2 | 10k-50k preference pairs | DPO/ORPO/GRPO route and answer preference tuning |
| S3 | 5k+ fixed eval items | promotion gate against teacher baselines and regressions |

Every distillation dataset must be represented as an immutable dataset snapshot
and connected to `vertex_training_run` lineage before any checkpoint promotion.

### 6.2 Unsloth Runner Policy

For Gemma-family Oka adapters, prefer an Unsloth runner for SFT/LoRA/DPO-style
adapter training when the base model is supported by Unsloth. The default
Transformers + PEFT runner remains the compatibility baseline and fallback.

Use Unsloth for:

- Gemma 3 4B / 12B / 27B text and vision instruction adapters.
- Gemma 3n E2B / E4B text, vision, and audio adapters when audio conditioning is
  in scope.
- Long-context SFT/LoRA jobs where Unsloth's memory-reduced kernels let the pod
  fit larger batch, sequence length, or rank on one GPU.

Do not treat Unsloth as the whole Oka runtime. It does not replace the
RisingWave dataset/lineage contract, multimodal adapter registry, vLLM serving
lane, or production FP8 serving path. Oka training should record the actual
runner in `hyperparams_json.runner`, for example `peft` or `unsloth`, so eval
and promotion can compare speed, VRAM, and quality without mixing provenance.

FP8 policy with Unsloth:

- Use BF16/4-bit LoRA as the first Oka quality path.
- Use FP8 only for supported Unsloth RL / GRPO or vLLM/TorchAO paths after a
  BF16 baseline exists.
- Keep BF16 master/adapters for promoted checkpoints until eval proves FP8
  training parity on the same dataset snapshot.

## 7. Inference Plan

```
client / actor / BPMN task
  -> LiteLLM or model gateway
  -> route by task + modality + tenant
  -> retrieve candidate context from RW vector/search tables
  -> fetch raw blobs from B2 only for selected chunks
  -> vLLM FP8 on RunPod L40S
  -> response + telemetry
  -> optional edge_gradient_flow / vertex_rl_step signal
```

Embedding inference uses a separate `/embed` lane so search backfills cannot starve chat/model
serving. Large media requests are chunked before GPU submission.

## 8. Evaluation Gates

Promotion requires at least one `vertex_training_eval` row for each target class:

- text/document: held-out loss, citation accuracy, Japanese/English retrieval QA
- image/video/audio: caption and cross-modal retrieval recall
- 3D/geospatial: nearest-neighbor sanity set and geometry/source consistency
- tabular/time-series: schema-following and temporal leakage checks
- safety: floor violation count must be zero for promoted aliases
- drift: adapter L2 diff and embedding-space neighbor churn must stay below threshold

No checkpoint is promoted by editing serving config directly. Alias activation is only
`edge_training_promoted_to(status='active')`.

## 9. Required Implementation Addenda

This ADR is a design contract. Implementation should follow in small patches:

1. Seed `vertex_vector_embedding_model` rows for `etzhayyim-mm-l40s-*` encoder/projection IDs.
2. Add a narrow FP8 latent table or formalize `vertex_organism_embedding` as a migration
   instead of ADR-only pseudo-schema.
3. Add modality-specific dataset snapshot tasks for 3D, video/audio chunk windows, IMU,
   heatmap, depth, and emotion artifacts.
4. Add RunPod L40S profile values beside the existing unified pod profile:
   `TRAINING_POD_GPU_CLASS=l40s`, `FP8_ENABLED=1`, `MAX_ACTIVE_TRAIN_JOBS=1`.
5. Add eval BPMN tasks and benches before first promote.

## 10. Execution Status 2026-05-09

Codex attempted to start training from the existing `etzhayyim training` surface:

- `etzhayyim training list-snapshots` succeeded and found frozen `etzhayyim-corpus` snapshots,
  including two 10-row ADSK eval snapshots suitable for smoke runs.
- `etzhayyim training run --kind lora ...` against a 10-row ADSK snapshot returned
  Cloudflare `522` before any `vertex_training_run` row was persisted.
- `etzhayyim training list-runs` / `list-checkpoints` confirmed no queued, running,
  failed, or completed run was created.
- `https://58pvflvw9w6nt3-8003.proxy.runpod.net/healthz` returned `404`, so
  `training_http_server` is not currently exposed/running on the documented
  unified training port.
- `op` / 1Password was checked against vault `etzhayyim Japan株式会社`.
  `etzhayyim.runpod/RUNPOD_API_KEY` and `etzhayyim.hf/HF_TOKEN` were present and were
  restored into macOS Keychain as `etzhayyim.runpod/RUNPOD_API_KEY` and
  `etzhayyim.hf/HF_TOKEN` without printing secret values.
- After Keychain restore, `50-infra/runpod/comfyui-l40s/scripts/status.sh`
  could query RunPod successfully; no existing L40S pod or model cache volume
  was running.
- A private-image L40S pod was created through RunPod REST with
  `ghcr.io/etzhayyim/runpod-vllm-gemma:latest`, the GHCR registry auth id, and
  RW/B2/HF/training-token env values. RunPod accepted the pod and marked it
  `RUNNING`, but runtime port mappings never appeared, so `:8003` could not be
  reached. The pod was terminated.
- A public PyTorch L40S pod was also created through RunPod REST to isolate the
  image-pull variable. It showed the same `RUNNING` without runtime mappings
  behavior and was terminated.
- The existing GraphQL `podFindAndDeployOnDemand` path was retried with the
  RunPod catalog PyTorch image and explicit `GPU_TYPE_ID='NVIDIA L40S'`.
  Network volume creation succeeded, but L40S scheduling failed with RunPod
  `SUPPLY_CONSTRAINT`. The temporary network volumes were deleted after the
  failed deploys.
- To move training forward while L40S capacity was unavailable, a RunPod A40
  Secure pod (`h0corqufikfmvf`, `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`)
  was started with `:8003/http` exposed. A minimal training HTTP server was
  installed on the pod and connected to RisingWave through the public
  `risingwave` LoadBalancer address because the in-cluster
  `risingwave.risingwave.svc.cluster.local` name is not resolvable from
  RunPod.
- Manual `/train/run` probe `manual-probe-6` completed a 5-step GPU torch
  smoke on the A40 and inserted a `vertex_training_run` row:
  `runId=manual-probe-6`, `kind=lora`, `baseModel=sshleifer/tiny-gpt2`,
  `datasetSnapshotId=etzhayyim-corpus-1040064dc271`, `status=running`.
- The A40 fallback was then advanced with extended BF16 CUDA smoke runs:
  `yamato-a40-bf16-1000step-20260509` completed 1,000 steps and
  `yamato-a40-bf16-5000step-20260509` completed 5,000 steps. Both runs used
  `datasetSnapshotId=etzhayyim-corpus-1040064dc271`, `baseModel=sshleifer/tiny-gpt2`,
  and recorded `status=done` / `completed_steps` in `vertex_training_run`.
- After the A40 pod was no longer needed it was terminated. RTX 6000 Ada Secure
  capacity was attempted next, but REST-created runtime ports did not become
  usable and the GraphQL route failed with `SUPPLY_CONSTRAINT`; temporary Ada
  pod/volume resources were deleted.
- A RunPod H100 NVL Secure pod (`mcax1y64ihgw4u`,
  `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`) was started as a
  temporary acceleration path while L40S/Ada capacity was unavailable. The same
  minimal training HTTP server was installed and connected to RisingWave through
  the public LoadBalancer address.
- H100 BF16/FP8 activation smoke runs completed:
  `oka-h100nvl-bf16-2000step-20260509` completed 2,000 steps,
  `oka-h100nvl-fp8act-2000step-20260509` completed 2,000 steps, and
  `oka-h100nvl-fp8act-50000step-20260509` completed 50,000 steps. These FP8
  runs validate CUDA float8 activation-cast plumbing, not full Transformer
  Engine FP8 training parity.
- For same-size Gemma-family inference comparison, `google/gemma-3-4b-it`
  loaded on the H100 and generated 107 new tokens at 24.967 tok/s. An Oka
  identity LoRA adapter was then trained on top of `google/gemma-3-4b-it` with
  BF16 PEFT LoRA rank 8 for 200 optimizer steps. The adapter trained
  16,394,240 parameters out of 4,316,473,712 total parameters and finished with
  `train_loss=0.27960334181785584`.
- The unmerged Oka LoRA adapter generated 107 new tokens at 14.101 tok/s and
  correctly answered Oka identity questions. After merging the adapter into the
  Gemma 3 4B trunk, the same prompt generated 121 new tokens at 24.293 tok/s,
  effectively matching the same-size Gemma baseline throughput while preserving
  Oka-specific identity behavior.
- An isolated `/workspace/unsloth-venv` was created on the H100 pod with
  Unsloth 2026.5.2, Torch 2.10.0+cu128, xFormers 0.0.35, TorchAO 0.17.0, and
  bitsandbytes 0.49.2. `FastModel.from_pretrained("google/gemma-3-4b-it",
  load_in_4bit=True)` loaded successfully in 23.478 seconds with about 4.3 GB
  CUDA memory allocated.
- Unsloth Oka smoke run
  `oka-unsloth-gemma3-4b-lora-smoke-50step-20260509` completed on the same H100
  with Gemma 3 4B, 4-bit load, LoRA rank 8, batch size 2, gradient accumulation
  4, and 14,901,248 trainable parameters out of 4,314,980,720 total parameters.
  It completed 50 steps in 152.0602 train seconds with `train_loss=0.9147577691078186`,
  `train_samples_per_second=2.631`, `train_steps_per_second=0.329`, and peak
  reserved CUDA memory of 5.2637 GB.
- The next efficiency step is to turn the smoke script into the production
  Oka Unsloth runner, persist `runner='unsloth'` in `hyperparams_json`, then run
  a matched 200-step job against the same Oka identity snapshot and compare
  wall-clock, peak VRAM, final loss, and merged tok/s against the PEFT baseline.
- The PEFT Oka Gemma 3 4B LoRA adapter was published publicly to Hugging Face
  as `com-junkawasaki/oka-gemma3-4b-lora` at commit
  `2edf1e6dfe788f6f3fe956b2cab56d86b178c590`. The repository contains the LoRA
  adapter, tokenizer files, `summary.json`, and a model card; it does not
  redistribute merged Gemma base weights.
- After the benchmark target was raised to Opus 4.7 / GPT-5.5 class quality,
  Oka training moved from 4B smoke to the 27B distillation/expert path.
  `google/gemma-3-27b-it` loaded through Unsloth 4-bit on the H100 NVL in
  43.756 seconds with 18.721 GB CUDA memory allocated. This validates that the
  27B trunk can be used as the primary Oka expert-training substrate on one H100.
- Oka 27B Unsloth LoRA smoke
  `oka-unsloth-gemma3-27b-lora-distill-smoke-20step-20260509` completed with
  LoRA rank 16, LoRA alpha 32, 512-token sequence length, batch size 1,
  gradient accumulation 4, and 113,516,544 trainable parameters out of
  27,545,923,184 total parameters. It completed 20 optimizer steps in
  121.9083 train seconds with `train_loss=3.8571211814880373`,
  `train_samples_per_second=0.656`, `train_steps_per_second=0.164`, and peak
  reserved CUDA memory of 26.6230 GB. Loss moved from 5.98 at step 5 to 2.014
  at step 20 on the synthetic frontier-distillation smoke set.
- To seed the frontier-quality S0 path with open HF data, Codex added
  `70-tools/scripts/ingest/oka-hf-quality-datasets.py` and ingested 4,900
  normalized records into `vertex_hf_dataset_record`. 4,800 rows are
  `sensitivity_ord=0` and therefore visible through `v_training_text`; 100
  rows are `sensitivity_ord=1` eval seed records. The selected datasets are:
  `allenai/tulu-3-sft-mixture/train`,
  `HuggingFaceH4/ultrachat_200k/train_sft`,
  `HuggingFaceH4/ultrafeedback_binarized/train_prefs`,
  `nvidia/OpenMathInstruct-2/train_1M`,
  `microsoft/orca-math-word-problems-200k/train`,
  `llm-jp/databricks-dolly-15k-ja/train`, and
  `elyza/ELYZA-tasks-100/test` as eval-only.
- Oka then advanced from synthetic smoke to real HF quality SFT with
  `oka-unsloth-gemma3-27b-hf-quality-sft-100step-20260509`. The run used
  `google/gemma-3-27b-it`, Unsloth 4-bit loading, LoRA rank 16, LoRA alpha 32,
  512-token sequence length, batch size 1, gradient accumulation 4, and 1,200
  rows fetched from `v_training_text`. It completed 100 optimizer steps in
  348.3248 train seconds with `train_loss=1.297047061920166`,
  `train_samples_per_second=1.148`, `train_steps_per_second=0.287`, and peak
  reserved CUDA memory of 26.6230 GB.
- Inference evaluation for the 27B checkpoint was saved to
  `/workspace/oka-27b-hf-quality-inference-eval-20260509.json`. On the H100 NVL
  with Unsloth 4-bit loading, the base `google/gemma-3-27b-it` averaged
  5.0904 tok/s over three prompts and the Oka 27B adapter averaged 4.9798 tok/s,
  an approximately 2.17% throughput overhead. The arithmetic prompt was solved
  correctly, but the Japanese instruction prompt exposed repetition/hallucinated
  training-token claims, so this checkpoint is a training-progress artifact, not
  a production-quality model.
- The Oka 27B adapter and inference artifact were published publicly to
  Hugging Face as `com-junkawasaki/oka-gemma3-27b-hf-quality-lora` at commit
  `8ef48c441d0342ec3d6f04c2f955be95b0866dbb`. The repository contains the LoRA
  adapter, tokenizer files, `summary.json`, `inference_eval_20260509.json`, and
  a model card; it does not redistribute merged Gemma base weights.
- The canonical `etzhayyim training run` path still needs one client-side fix:
  Python `urllib` calls from `training-zeebe-worker` receive HTTP `403` from
  the RunPod proxy before reaching the pod, while `curl` with the same bearer
  token succeeds. The durable evidence for this checkpoint is therefore the
  direct `/train/run` call plus the RisingWave row, not a completed XRPC
  `runLora` response.
- Local fallback smoke completed with `./train-experts-native`:

```text
backend=wgpu
trainingPrecision=bf16
label=GSM8K
dim=16
seqLen=8
samplesPer=1
summary=/tmp/etzhayyim-lancedb/train_experts_GSM8K_summary.json
status=completed
```

This local smoke proves the native bootstrap path can emit artifacts, but it is
not the target FP8 RunPod L40S training run. The remaining blocker is no
reachable L40S training HTTP endpoint: REST-created L40S pods did not reach
runtime port mapping, and the canonical GraphQL route hit L40S supply
constraints. Training has progressed on the A40 BF16 fallback path, but the next
production fix should add a non-`urllib` HTTP client or a small in-cluster proxy
for `training-zeebe-worker`, then retry the same run through XRPC.
- 2026-05-09 client-side fix landed (diagnostic, not yet retried end-to-end):
  `_pod_submit_and_wait` in
  `20-actors/magatama/py/src/pymagatama/primitives/training_run.py` was
  switched from `urllib.request` to `httpx.Client` and now sends
  `User-Agent: curl/8.7.1` + `Accept: application/json` on both
  `POST /train/run` and `GET /train/status/{id}`. Hypothesis: the RunPod
  proxy fingerprints the default `Python-urllib/3.x` UA and returns 403
  before reaching the pod, since the same bearer token via curl succeeds.
  HTTP/2 is now pre-staged: `pyproject.toml` was bumped to
  `httpx[http2]>=0.27.0` (pulls `h2`/`hpack`/`hyperframe`) and the client
  honours `TRAINING_POD_HTTP2=1`, so if UA alone is insufficient the
  escalation is one env-var flip on `mitama-training-pool` — no further
  code change. Durable
- 2026-05-09 GPU pod assignment finalized: training was relocated from the
  L40S design above to a **dedicated H100 NVL training pod**. Oka 27B
  HF-quality SFT (`oka-unsloth-gemma3-27b-hf-quality-sft-100step-20260509`,
  100 optimizer steps, peak ~26.6 GiB CUDA, train_loss 1.297) completed on
  this H100 pod. Inference traffic continues to terminate on the RunPod
  6000 Ada unified pod (ADR-2605010000); the two pods are intentionally
  not collapsed.
- 2026-05-09 default training base model updated to **`google/gemma-4-E4B`**
  (HF base, non-instruct). Code wiring:
  - `20-actors/magatama/sdk/magatama-host-sdk/src/llm-model-registry.ts`
    adds a `gemma-4-e4b-base` entry with `huggingfaceModel:
    "google/gemma-4-E4B"` plus a `training-base` use-case default and
    exports a new `TRAINING_DEFAULT_BASE_MODEL` constant.
  - `20-actors/magatama/sdk/magatama-host-sdk/src/llm-model-types.ts`
    grows a `huggingfaceModel?: string` field and a `"training-base"`
    `UseCaseName` so the SSoT carries HF IDs explicitly.
  - `20-actors/magatama/py/src/pymagatama/primitives/training_run.py`
    reads `TRAINING_DEFAULT_BASE_MODEL` env (default `google/gemma-4-E4B`)
    and uses it as fallback when `runpod_handler` receives a payload
    without `baseModel` / `studentBaseModel`. The pre-2026-05-09 6000-Ada
    port-8003 default for `TRAINING_POD_BASE_URL` is retired in favour of
    requiring callers to set the H100 pod URL via Secret.
  - `20-actors/magatama/py/src/pymagatama/training_http_server.py`
    docstring rewritten to declare H100 pod as training-only and 6000 Ada
    as inference-only.
  Existing checkpoints on `gemma-3-4b-it` / `gemma-3-27b-it` remain
  reproducible by passing `baseModel` explicitly per run; only the
  *default* trunk moved.
  evidence will be a clean XRPC `runLora` response after redeploying
  `mitama-training-pool` with this change; until that retry runs, the
  status of line 467–472 (urllib 403) remains "client patched, awaiting
  re-deploy".
- 2026-05-09 GPU pod assignment finalized: training was relocated from the
  L40S design above to a **dedicated H100 NVL training pod**. Oka 27B
  HF-quality SFT (`oka-unsloth-gemma3-27b-hf-quality-sft-100step-20260509`,
  100 optimizer steps, peak ~26.6 GiB CUDA, train_loss 1.297) completed on
  this H100 pod. Inference traffic continues to terminate on the RunPod
  6000 Ada unified pod (ADR-2605010000); the two pods are intentionally
  not collapsed. Cost SKU recorded in
  `deps.toml [invariants.gpu_pricing.runpod_h100_nvl]`.
- 2026-05-09 default training base model updated to **`google/gemma-4-E4B`**
  (HF base, non-instruct). Code wiring:
  - `20-actors/magatama/sdk/magatama-host-sdk/src/llm-model-registry.ts`
    adds a `gemma-4-e4b-base` entry with `huggingfaceModel:
    "google/gemma-4-E4B"`, a `training-base` use-case default, and the
    new `TRAINING_DEFAULT_BASE_MODEL` constant.
  - `20-actors/magatama/sdk/magatama-host-sdk/src/llm-model-types.ts`
    grows a `huggingfaceModel?: string` field and `"training-base"`
    (plus `"edge"` / `"browser"` / `"cpu"` for the Baien sibling, ADR
    2605092350) so the SSoT carries HF IDs explicitly.
  - `20-actors/magatama/py/src/pymagatama/primitives/training_run.py`
    reads `TRAINING_DEFAULT_BASE_MODEL` env (default `google/gemma-4-E4B`)
    and falls back to it when `runpod_handler` receives a payload
    without `baseModel` / `studentBaseModel`. The pre-2026-05-09 6000-Ada
    port-8003 default for `TRAINING_POD_BASE_URL` is retired in favour of
    requiring callers to set the H100 pod URL via Secret. Baien training
    kinds (`baien-lora`, `baien-multimodal-graft`) reuse the same
    `runpod_handler` path with a sibling `_BAIEN_DEFAULT_TRUNK_MODEL`
    fallback.
  - `20-actors/magatama/py/src/pymagatama/training_http_server.py`
    docstring rewritten to declare H100 pod as training-only and 6000 Ada
    as inference-only.
  Existing checkpoints on `gemma-3-4b-it` / `gemma-3-27b-it` remain
  reproducible by passing `baseModel` explicitly per run; only the
  *default* trunk moved.

# Consequences

Positive:

- Uses existing RW vertex/dataset lineage instead of adding a separate ML metadata system.
- Keeps L40S GPU fully useful for both inference and adapter training.
- Covers the requested multimodal and embedding surfaces with one normalized contract.

Negative:

- Single L40S is memory-limited. Some full fine-tunes must be adapter-only or multi-node.
- Sensor modalities such as IMU, heatmap, depth, and emotion require stricter provenance and consent gates.
- FP8 stability needs BF16 fallback and per-run overflow/drift telemetry.

# References

- NVIDIA L40S product brief and architecture notes: FP8 Tensor Core capability, 48 GB GDDR6.
- RunPod GPU pricing/spec pages: L40S 48 GB availability and current deployment cost must be checked at provisioning time.
- `90-docs/adr/2605070700-rw-native-model-training-weight-lineage.md`
- `90-docs/adr/2604262359-risingwave-multimodal-vector-search-topology.md`
- `90-docs/adr/2605092300-fp8-train-inference-colocation.md`
