---
id: adr-2605262300-baien-moemoekyun-r2-runpod-b200-train-architecture
title: "baien-moemoekyun R2+ train architecture on commercial GPU rental (B200 SXM sparse FP4/FP8/BF16 precision ladder; inference path UNCHANGED Murakumo-only)"
status: "proposed (gated on ADR-2605262200 ratification)"
doc_type: adr
topic: baien-moemoekyun-r2-runpod-b200
authoritative: true
last_verified: 2026-05-26
priority: 8.5
axis: model-substrate
weight: 0.85
priority_note: "Sibling of ADR-2605262200 (charter amendment). Train architecture cannot execute until amendment effective (~2026-07-19). This ADR specifies the architecture, runbook, and per-rental attestation Lexicon so execution is plug-and-play on amendment effective date."
authoritative_for:
  - "baien-moemoekyun R2 / R3 / R4 train host = commercial GPU rental (B200 SXM primary, H100 SXM fallback)"
  - "Precision ladder R2 BF16 → R3 FP8 (TransformerEngine) → R4 sparse FP4 (engineering work itemized per phase)"
  - "Checkpoint pipeline: rented GPU → HuggingFace Hub draft OR direct upload → IPFS pin via mac-260317 → Murakumo fleet pull"
  - "Inference architecture (Mac mini + EVO-X2 fleet) — UNCHANGED, references ADR-2605215000"
  - "Per-rental kotoba-datomic attestation Lexicons com.etzhayyim.train.rentalAttestation + rentalCostLog spec"
  - "Cost / wall budget caps + runbook for rental orchestration"
depends_on:
  - adr-2605262200-charter-rider-2i-baien-train-rental-carveout
  - adr-2605261900-baien-moemoekyun-moe-charter
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
  - adr-2605242100-baien-server-xl-carve-out
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605241500-etzhayyim-dataset-cid-substrate
related:
  - 70-tools/baien-moemoekyun-train/ (extended for rental orchestration)
  - 90-docs/runbooks/baien-moemoekyun-runpod-bringup.md (R2 deliverable)
  - 00-contracts/lexicons/com/etzhayyim/train/ (rentalAttestation + rentalCostLog Lexicon定義 deliverable)
supersedes: []
superseded_by: []
---

# ADR-2605262300: baien-moemoekyun R2+ RunPod B200 train architecture (inference UNCHANGED)

**Status**: proposed (gated on ADR-2605262200 Council ratification + 30-day public objection; effective earliest ~2026-07-19)
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

ADR-2605262100 で baien-moemoekyun R1.4 (5K ex × 1 ep) は EVO-X2 単機実行で 5-7h wall として設計済。R2 (50K × 2 ep ≈ 2.46 EFLOPs) は実測 5-7 TFLOPS sustained で **~4 日**、R3 / R4 は単機 infeasible (前 turn 数値検証)。

ADR-2605262200 で Charter Rider §2(i) train carve-out が proposed (Council ratification pending)。本 ADR はその amendment 効力発生後に実行される train architecture を **事前に固定** し、 amendment 効力発生日 (~2026-07-19) に即実行可能とする。

User 選好 (2026-05-26): "B200 Blackwell sparse" — B200 SXM 主、H100 SXM fallback、sparse FP4 まで段階的に precision optimization。

# Decision

## §1 Hardware target (R2 → R4 ladder)

### §1.1 Primary: NVIDIA B200 SXM (Blackwell)

| Spec | Value | Note |
|---|---|---|
| BF16 Tensor Core peak | ~4,500 TFLOPS (per GPU) | 既存 GPU の中で BitNet BF16 master 学習が即動く |
| FP8 Tensor Core peak | ~9,000 TFLOPS | TransformerEngine 経由で MoE expert 部分のみ FP8 化可能 |
| FP4 sparse peak | ~18,000 TFLOPS (sparse 2:4) | 工事必要 (sparse regularization + FP4 cast) |
| HBM3e | 192 GB | Adam state 65 GB (E=256 全層) 余裕 |
| NVLink intra-node | 1.8 TB/s | 8-GPU node で expert-parallel が高速 |
| RunPod 2026 pricing (estimate) | community $5-7/h, secure $7-9/h | availability 限定的、確保困難な場合 H100 SXM fallback |

### §1.1b Secondary: NVIDIA RTX 5090 (consumer Blackwell, added 2026-05-26)

| Spec | Value | Note |
|---|---|---|
| BF16 Tensor Core peak | ~165 TFLOPS (per GPU) | ~37× less than B200 |
| FP8 Tensor Core peak | ~330 TFLOPS | TransformerEngine compatible |
| FP4 sparse peak | ~1,318 TFLOPS | dense 659 / sparse 2:4 1,318 |
| GDDR7 | 32 GB | tight but fits moemoekyun (1.1B trainable + 2.4B frozen + Adam ≈ 25 GB) |
| NVLink | NONE (consumer card) | multi-GPU train inefficient |
| RunPod 2026 pricing | community $0.69-1.99/h | very cheap per-hour |

**Use cases on RTX 5090**:
- Dev iteration (smaller experiments, quick turnaround, low $)
- **Hparam sweep parallelism** (10× 5090 = ~$10/h, 10 parallel R2 runs in 7h vs 1× B200 in 15 min — same total $)
- Bench / eval runs (Phase 2-3 of moemoekyun-bench-plan-260526.md)
- Single-GPU experiments (no NVLink penalty)

**NOT use cases**:
- Main R2/R3/R4 runs (B200 wins on cost + wall)
- Multi-GPU train (no NVLink = stall on all-reduce)
- E=256 全 30 層 (8.2B trainable Adam fp32 = 65 GB > 32 GB 5090 capacity)

### §1.2 Fallback: NVIDIA H100 SXM

| Spec | Value | Note |
|---|---|---|
| BF16 Tensor Core peak | ~1,979 TFLOPS | B200 の 44% |
| FP8 Tensor Core peak | ~3,958 TFLOPS | TransformerEngine 成熟、即動く |
| HBM3 | 80 GB | Adam state 65 GB ぎりぎり、E=256 全層は工夫必要 |
| RunPod 2026 pricing | community $2.50-3.50/h, secure $3.50-4.50/h | 確実に確保可能 |

### §1.3 Sustained efficiency assumption (60% of peak)

実 train loop で TransformerEngine + flash-attention + grad ckpt + dataloader 込みで sustained は theoretical peak の 50-70%。本 ADR は **60% sustained** で wall 計算。

| Hardware | BF16 sustained | FP8 sustained | sparse FP4 sustained |
|---|---|---|---|
| B200 | 2,800 TFLOPS | 5,500 TFLOPS | ~10,000 TFLOPS |
| H100 | 1,200 TFLOPS | 2,400 TFLOPS | (sparse FP4 unsupported) |
| **RTX 5090** | **~100 TFLOPS** | **~200 TFLOPS** | **~800 TFLOPS** |

### §1.4 Cost/wall matrix (R2/R3/R4 × hardware)

R2 (2.46 EFLOPs):

| GPU | wall | cost |
|---|---|---|
| B200 BF16 | 15 min | $1.75 |
| RTX 5090 BF16 | 6.8h | $4.70 |
| H100 SXM BF16 | 34 min | $2.30 |

R4 (36.9 EFLOPs):

| GPU | wall | cost |
|---|---|---|
| B200 BF16 | 3.6h | $25 |
| RTX 5090 BF16 | 102h | $70 |
| H100 SXM BF16 | 8.5h | $34 |

→ **B200 primary** (cost + wall both winner). **RTX 5090 secondary**
(hparam sweep parallelism / cheap dev iter). **H100 fallback** if B200
unavailable.

## §2 Precision ladder (engineering 段階)

### §2.1 R2 (今期最優先): BF16 master, baseline

- **Engineering**: ZERO (BitNet 1.58 backbone は HF docs 上 BF16 master training canonical; MoE experts は std bf16 FFN, ADR-2605261900 §2)
- **Wall on B200**: R2 = ~15 分 / R3 = ~25 分 / R4 = ~3.6h
- **Cost on B200 @ $7/h**: R2 ~$1.75 / R3 ~$2.90 / R4 ~$25
- **Verdict**: B200 amendment 効力発生日に即実行可能

### §2.2 R3 enhancement: FP8 mixed-precision (MoE experts のみ)

- **Engineering**: TransformerEngine 統合 (1-2 週) — MoE expert FFN を `te.LayerNormLinear` + FP8 mixed-precision に置換、BitNet backbone は BF16 master のまま, gradient scaling adopted
- **Constraint**: BitLinear (backbone) を FP8 化しない (BitNet semantics 毀損リスク)
- **Wall on B200**: R3 = ~13 分 / R4 = ~1.8h
- **Cost on B200 @ $7/h**: R3 ~$1.50 / R4 ~$13
- **Engineering ROI**: R4 grade 10 iter sweep で BF16 $250 → FP8 $130 (差額 $120 で 1-2 週工事ペイ)

### §2.3 R4 enhancement: sparse FP4 (BitNet-friendly 概念整合)

- **Engineering**: TransformerEngine FP4 (Blackwell-only, Hopper 未対応) + 2:4 structured sparsity training-time regularization (3-4 週)
- **Constraint**: BitNet 1.58 backbone は frozen + fwd-only なので sparse 適用対象外、trainable MoE 部のみ sparse 化
- **Wall on B200**: R4 = ~50 分
- **Cost on B200 @ $7/h**: R4 ~$6
- **Engineering ROI**: R4 grade 10 iter sweep で FP8 $130 → sparse FP4 $60 (差額 $70 で 3-4 週工事はやや微妙、R5 / R6 までの ROI 累積で正当化)

### §2.4 Precision ladder 採用順序

| Phase | Precision | Engineering wall | Train wall (R4) | Train cost (R4) |
|---|---|---|---|---|
| **P4 即実行 (~2026-07-19+)** | BF16 | 0 | 3.6h | $25/run |
| **P4 + 1-2 週 engineering** | FP8 (MoE only) | 1-2 週 | 1.8h | $13/run |
| **P4 + 1-2 ヶ月 engineering** | sparse FP4 (MoE only) | 3-4 週 | 50 分 | $6/run |

R2 immediate execution は BF16 で開始、FP8 engineering を並行進行、R3+ で FP8 採用。sparse FP4 は R4 iteration sweep が始まってから ROI 判断。

## §3 Wall + cost matrix (R2/R3/R4 × precision × hardware)

| Phase | Compute | B200 BF16 | B200 FP8 | B200 sparse FP4 | H100 BF16 | H100 FP8 |
|---|---|---|---|---|---|---|
| R1.4 (EVO 継続) | 0.12 EFLOPs | (skip) | (skip) | (skip) | (skip) | (skip) |
| **R2** (50K×2ep) | 2.46 EFLOPs | 15 min, **$1.75** | 7 min, $0.80 | 3 min, $0.35 | 34 min, $2.30 | 17 min, $1.20 |
| **R3** (E=256 全層) | 4.2 EFLOPs | 25 min, **$2.90** | 13 min, $1.50 | 5 min, $0.60 | 58 min, $3.90 | 29 min, $2.00 |
| **R4** (500K×3ep) | 36.9 EFLOPs | 3.6h, **$25** | 1.8h, $13 | 50 min, $6 | 8.5h, $34 | 4.3h, $17 |
| R4 × 10 iter sweep | 369 EFLOPs | $250 | $130 | $60 | $340 | $170 |

(Pricing は 2026 RunPod community + secure 中点 estimate; actual 確認 R2.0 deliverable)

## §4 Checkpoint pipeline (rented GPU → IPFS → Murakumo)

```
┌─────────────────────────────┐
│  RunPod B200 instance       │
│  (rental duration: R2 ~15m, │
│   R3 ~25m, R4 ~3.6h)         │
└──────────────┬──────────────┘
               │ snapshot every N step (configurable: R2=every 100, R4=every 1K)
               ↓
┌─────────────────────────────┐
│ Pre-flight attestation emit │
│ com.etzhayyim.train.        │
│ rentalAttestation           │
│ (vendor, GPU spec, est wall,│
│  est cost, dataset CID,     │
│  Charter Rider scan PASS,   │
│  attesting DID)             │
└──────────────┬──────────────┘
               │
               ↓ (rental train executes)
               │
┌─────────────────────────────┐
│ Final checkpoint upload     │
│ Option A: HuggingFace Hub   │
│   (Tier A/B datasets only,  │
│    public artifact)         │
│ Option B: Direct rsync to   │
│   mac-260317.etzhayyim.com  │
│   (Tier C datasets, G13     │
│    distribution boundary)   │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│ mac-260317 ipfs add         │
│ /Volumes/260317/etzhayyim/  │
│   annex-store/HF/           │
│   moemoekyun-rN.K-iterMM/   │
│ → publish-ipfs → CID 取得   │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│ Post-flight cost log emit   │
│ com.etzhayyim.train.        │
│ rentalCostLog               │
│ (actual wall, actual USD,   │
│  output checkpoint CID,     │
│  IPFS pin verify CID,       │
│  attesting DID)             │
└──────────────┬──────────────┘
               │
               ↓ (Murakumo fleet pull)
               │
┌─────────────────────────────┐
│  Mac mini fleet (judah +    │
│  others) llama.cpp serve    │
│  + LiteLLM gateway route    │
│  baien-server-moemoekyun-   │
│  rN.K → 各 SBT-gated client │
│  ADR-2605215000 inference   │
│  invariant 100% 適合        │
└─────────────────────────────┘
```

## §5 Per-rental kotoba-datomic attestation Lexicon (deliverable)

### §5.1 `com.etzhayyim.train.rentalAttestation` (pre-flight)

```typescript
// 00-contracts/lexicons/com/etzhayyim/train/rentalAttestation.json (NSID schema)
{
  "lexicon": 1,
  "id": "com.etzhayyim.train.rentalAttestation",
  "description": "Pre-flight attestation for commercial GPU rental train run under CHARTER-RIDER §2(i)(2) carve-out (ADR-2605262200).",
  "defs": {
    "main": {
      "type": "record",
      "key": "tid",
      "record": {
        "type": "object",
        "required": [
          "createdAt", "trainAdrRef", "vendor", "gpuModel", "gpuCount",
          "expectedWallMinutes", "expectedUsdCost", "datasetCidsTrain",
          "datasetCidsEval", "charterRiderScanPass", "attestingDid"
        ],
        "properties": {
          "createdAt": {"type": "string", "format": "datetime"},
          "trainAdrRef": {"type": "string", "description": "e.g., ADR-2605262300"},
          "vendor": {"type": "string", "knownValues": ["runpod-community", "runpod-secure", "lambda-labs", "coreweave", "vast-ai"]},
          "gpuModel": {"type": "string", "knownValues": ["nvidia-b200-sxm", "nvidia-h100-sxm", "nvidia-h200-sxm", "nvidia-b300-sxm", "nvidia-rubin-hgx"]},
          "gpuCount": {"type": "integer", "minimum": 1, "maximum": 8},
          "expectedWallMinutes": {"type": "integer", "description": "minutes (integer per AT Protocol)"},
          "expectedUsdCostMillicents": {"type": "integer", "description": "USD × 100000 (integer per AT Protocol)"},
          "datasetCidsTrain": {"type": "array", "items": {"type": "string"}, "description": "IPFS CIDs of train corpus from datasets.jsonl"},
          "datasetCidsEval": {"type": "array", "items": {"type": "string"}},
          "modelTier": {"type": "string", "knownValues": ["baien-server", "baien-XL"]},
          "modelArtifactName": {"type": "string", "description": "e.g., baien-server-moemoekyun-r2-iter01"},
          "precisionMode": {"type": "string", "knownValues": ["bf16", "fp8-mixed", "sparse-fp4"]},
          "charterRiderScanPass": {"type": "boolean", "description": "All train + eval datasets passed §2(a)-(h) scan"},
          "charterRiderScanRunCid": {"type": "string", "description": "Scan report IPFS CID"},
          "attestingDid": {"type": "string", "description": "DID of person/Council seat attesting (typically did:web:etzhayyim.com or did:web:mac-260317.etzhayyim.com)"}
        }
      }
    }
  }
}
```

### §5.2 `com.etzhayyim.train.rentalCostLog` (post-flight)

```typescript
{
  "lexicon": 1,
  "id": "com.etzhayyim.train.rentalCostLog",
  "description": "Post-flight cost + outcome log for commercial GPU rental train run.",
  "defs": {
    "main": {
      "type": "record",
      "key": "tid",
      "record": {
        "type": "object",
        "required": [
          "createdAt", "rentalAttestationUri", "actualWallMinutes",
          "actualUsdCost", "outputCheckpointCid", "ipfsPinVerifyCid",
          "evalMetrics", "attestingDid"
        ],
        "properties": {
          "createdAt": {"type": "string", "format": "datetime"},
          "rentalAttestationUri": {"type": "string", "description": "AT URI of preceding rentalAttestation record"},
          "actualWallMinutes": {"type": "integer", "description": "minutes"},
          "actualUsdCostMillicents": {"type": "integer", "description": "USD × 100000"},
          "outputCheckpointCid": {"type": "string", "description": "IPFS CID of merged checkpoint (HF dir or .safetensors)"},
          "ipfsPinVerifyCid": {"type": "string", "description": "Verification round-trip CID (e7m-dataset verify output)"},
          "evalMetrics": {
            "type": "object",
            "properties": {
              "langgraphCodingPass1Permille": {"type": "integer", "minimum": 0, "maximum": 1000, "description": "permille (× 1000 for integer-only Lexicon; +30 = +3pp commit gate)"},
              "humanevalplusPass1Permille": {"type": "integer", "minimum": 0, "maximum": 1000},
              "mbppPlusPass1Permille": {"type": "integer", "minimum": 0, "maximum": 1000}
            }
          },
          "commitDecision": {"type": "string", "knownValues": ["committed-to-registry", "aborted-delta-insufficient", "aborted-regression", "aborted-engineering-failure"]},
          "registryEntry": {"type": "string", "description": "If committed: AT URI of moemoekyun-models.jsonl entry"},
          "attestingDid": {"type": "string"}
        }
      }
    }
  }
}
```

両 Lexicon は P4 以降に `00-contracts/lexicons/com/etzhayyim/train/` 配下に commit、Pregel cell 経由で auto-emit する。

## §6 Cost / wall budget caps (constitutional ceiling)

ADR-2605262200 §2(i)(2)(5) "burst-only" 条件を operational に固定:

| Cap | 値 | Enforcement |
|---|---|---|
| Single rental session continuous wall | ≤ **24 h** | rental orchestrator hard-kill |
| Single rental session USD cost | ≤ **$200** | rental orchestrator hard-kill |
| Monthly aggregate rental wall (across all sessions) | ≤ **100 h** | kotoba-datomic attestation 累計 monitor + cell warn |
| Monthly aggregate rental USD cost | ≤ **$1,000** | kotoba-datomic attestation 累計 monitor + cell warn |
| Continuous rental >7 days | ❌ prohibited per §2(i)(2)(5) | Council Lv6+ ≥4/7 seats per-incident approval 必要 |

R4 grade 10-iter sweep (BF16) は累計 $250 / ~36 h → 月予算内。Sparse FP4 で $60 / ~8h → 月数回 grade 可能。

## §7 Runbook: rental orchestration script (deliverable)

`70-tools/baien-moemoekyun-train/scripts/rental-orchestrator.py` (R2.0 deliverable):

```python
# pseudocode
def run_rental_train(adr_ref, vendor, gpu, dataset_cids_train, ...):
    # Pre-flight
    scan_result = charter_rider_scan(dataset_cids_train + dataset_cids_eval)
    assert scan_result.passed, "Charter Rider §2 scan failed"

    attestation = create_rental_attestation_record(
        adr_ref=adr_ref,
        vendor=vendor, gpu=gpu, ...,
        charter_scan_run_cid=scan_result.cid,
    )
    publish_to_pds(attestation)  # com.etzhayyim.train.rentalAttestation

    # Provision + train
    start = time.time()
    instance = vendor.start_instance(gpu)
    instance.run_train_script(adr_ref, dataset_cids_train, ...)
    checkpoint_local = instance.fetch_final_checkpoint()
    actual_cost = instance.terminate_and_bill()
    actual_wall = (time.time() - start) / 60

    # IPFS pin (on mac-260317)
    checkpoint_cid = e7m_dataset_add(checkpoint_local, "moemoekyun-rN.K-iterMM")
    verify_cid = e7m_dataset_verify(checkpoint_cid)

    # Eval (on Mac mini fleet, ADR-2605262100 split-role)
    eval_results = run_fleet_eval(checkpoint_cid, datasets=dataset_cids_eval)

    # Commit gate (ADR-2605262100 R1.5 logic, scaled)
    decision = commit_gate(eval_results)

    # Post-flight cost log
    cost_log = create_rental_cost_log(
        attestation_uri=attestation.uri,
        actual_wall=actual_wall, actual_cost=actual_cost,
        output_cid=checkpoint_cid, verify_cid=verify_cid,
        eval_metrics=eval_results, commit_decision=decision,
    )
    publish_to_pds(cost_log)  # com.etzhayyim.train.rentalCostLog

    return decision
```

## §8 Inference architecture (NO CHANGE)

Resulting `baien-server-moemoekyun-rN.K-iterMM` checkpoints serve via Murakumo fleet **unchanged**:

| Component | Role | Reference |
|---|---|---|
| `judah` Mac mini :17 LiteLLM gateway :4000 | route `baien-server-moemoekyun-*` requests | ADR-2605215000 §1.1 |
| Mac mini fleet (10 nodes, llama.cpp Ollama serve) | per-node loaded model variant | ADR-2605202100 launchd cells |
| EVO-X2 .70 :11434 Ollama | parallel inference pod | ADR-2605202345 |
| G12 (ADR-2605261900) SBT-gated endpoint | 1 SBT = 1 vote authorization | ADR-2605231525 server-side signing |

→ **inference path zero change**, §2(i)(1) invariant 100% 適合。

# Consequences

## Positive

- baien-moemoekyun R2/R3/R4 grade train が constitutional 経路で unblock、religious-corp daemon agentic coding capability が 1.5 ヶ月で立ち上がる
- BF16 baseline で即実行可能、precision optimization (FP8/sparse FP4) は ROI 駆動で段階的進行
- Per-rental kotoba-datomic attestation で全 commercial GPU 使用が on-chain 透明、religious-corp の "Transparent" 哲学保持
- Inference 路線完全不変、Mac mini + EVO-X2 fleet が baien-server-moemoekyun を SBT-gated に serve
- Lexicon spec が固定されるので、P4 効力発生直後にコード scaffolding が plug-and-play

## Negative / Risk

- amendment 効力発生まで ~1.5 ヶ月待機、その間 R&D loop は R1.4 grade (EVO 5-7h iter) 維持
- B200 RunPod availability が limited (2026 時点)、H100 SXM fallback 想定必須
- FP8/sparse FP4 engineering は内部投資 (1-4 週); precision degradation observed time に re-baseline 必要
- Per-rental attestation の運用 burden — cell 自動化 (R2.0 deliverable) 完成までは手動 attestation

## Reversibility

- ADR-2605262300 自体は revoke 可能だが、既に rental 実行 + IPFS pin した artifact は永続
- Precision ladder downgrade (sparse FP4 → FP8 → BF16) は安全、upgrade は engineering 工事
- 全体方針 revert: ADR-2605262200 amendment 自体を Council Lv6+ で repeal して原 §2(i) (Murakumo-only train) 復帰可能、ただし重い手続き

## Open

- B200 availability monitoring — 確保困難時の H100 fallback 自動切替 logic は R2.0 で実装
- FP4 sparse + BitNet semantics preservation — research-grade open question、R3 で empirical 検証
- Continuous rental >7 日 が必要な場合 (e.g., R4 sweep 10 iter consecutive) の Council 申請 mechanics は ADR-2605192300 follow-up

# Alternatives Considered

| 案 | 却下理由 |
|---|---|
| H100 SXM 主、B200 fallback | user 明示選好で B200 primary; H100 は availability fallback 位置 |
| Lambda Labs / CoreWeave 専属 | RunPod 同等 (charter §2 scan 通れば等価)、vendor lock-in 回避で multi-vendor allowed (§2(i)(2)(4)) |
| BF16 のみ採用、FP8/FP4 engineering 諦め | R4 grade で wall 3.6h × $25/run、10 iter sweep で $250 高すぎ; FP8 1-2 週工事の ROI 明白 |
| 自家 fleet capex (MI300X / used H100) | ADR-2605262200 §4 で議論済: capex path 並列に進める価値あるが本 ADR scope 外 (`baien-fleet-capex-*` 別 ADR) |
| Founder Lv7+ emergency authorization で即実行 | ADR-2605262200 §4 で却下 (institutional integrity 優先) |

# References

- ADR-2605262200 (Charter Rider §2(i) amendment — parent constitutional ADR)
- ADR-2605261900 (baien-moemoekyun R0 charter — architecture base)
- ADR-2605262100 (baien-moemoekyun R1 — corpus + eval gate logic 継承)
- ADR-2605242100 (baien-server / baien-XL carve-out — naming + tier 制約)
- ADR-2605215000 (Murakumo-only inference — inference invariant 不変参照)
- ADR-2605241500 (DataLad + IPFS dataset substrate — checkpoint pin pipeline base)
- NVIDIA TransformerEngine documentation (FP8 mixed-precision integration reference)
- NVIDIA B200 datasheet (FP4/FP8/BF16 spec source)
- RunPod B200/H100 community pricing (2026 estimate, R2.0 で actual 確認)
