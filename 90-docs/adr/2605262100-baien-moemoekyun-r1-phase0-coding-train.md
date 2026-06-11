---
id: adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
title: "baien-moemoekyun R1 — Phase 0 freeze-train (router + experts + α) coding-emphasis SFT on EVO-X2 Windows ROCm (R1.0..R1.5)"
status: proposed
doc_type: adr
topic: baien-moemoekyun-r1
authoritative: true
last_verified: 2026-05-26
priority: 8.0
axis: model-substrate
weight: 0.85
priority_note: "R1 sub-charter of ADR-2605261900 (baien-moemoekyun R0). Phase 0 freeze-train only — backbone frozen, only router + experts + output gate α trainable. Reuses gemma-coder-distill EVO-X2 Windows ROCm stack (ADR-2605250400) verbatim."
authoritative_for:
  - "baien-moemoekyun R1 sub-phase ladder (R1.0..R1.5)"
  - "BaienMoEResidual module attachment spec (module-surgery, not peft adapter)"
  - "Tier A/B/C dataset tier + G13 distribution boundary gate"
  - "EVO-X2 Windows ROCm 7.2.1 + peft+trl runtime (inherited from ADR-2605250400)"
  - "coding-emphasis SFT corpus selection for R1.4"
  - "eval-gated commit policy (langgraph-coding pass@1 Δ ≥ +3pp primary; HumanEval+ Δ ≥ 0 sanity)"
depends_on:
  - adr-2605261900-baien-moemoekyun-moe-charter
  - adr-2605250400-gemma-coder-distill-rocm
  - adr-2605231300-baien-distill-react-loop
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605202345-evo-x2-gpu-pod-fleet-integration
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605242100-baien-server-xl-carve-out
related:
  - 70-tools/baien-moemoekyun-train/ (R0 path reserved; R1 lands implementation here)
  - 70-tools/baien-distill/ (adapters/hf_dataset.py + charter_rider scanner reuse via path import)
  - 70-tools/gemma-coder-distill/ (EVO-X2 ROCm reference stack)
  - 70-tools/scripts/bench/langgraph-coding/ (50-prompt exec-graded coding bench)
  - 50-infra/cluster/murakumo/litellm/config.yaml (judah LiteLLM gateway)
supersedes: []
superseded_by: []
---

# ADR-2605262100: baien-moemoekyun R1 — Phase 0 freeze-train coding-emphasis SFT (R1.0..R1.5)

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

ADR-2605261900 (baien-moemoekyun R0) charter は R0 = paths-reserved only (zero code) と定義し、R1+ を独立 ADR に明示的に押し出した。本 ADR は **R1 sub-charter** として:

1. **R1 acceptance** (ADR-2605261900 §7) を具体的に execution する経路を定める
2. user 指針 (2026-05-26): agentic coding 性能を強めたい / EVO Windows 使う を取り込む
3. user 指針 (2026-05-26 同セッション): baien 系列は **非商用 dataset / model を train 用途で使用 OK** を取り込む (artifact 配布境界は G13 で別途定義)
4. 既に EVO-X2 Windows + ROCm 7.2.1 + peft+trl で実証済みの gemma-coder-distill stack (ADR-2605250400) を **runtime substrate として verbatim 流用** する

R1 は Phase 0 のみ — backbone 完全凍結、trainable は MoE residual branch (router + experts + per-layer α) のみ。R2 で shared FFN + layernorm 部分解凍、R3 で joint low-LR。

## なぜ peft adapter ではなく custom Module surgery か

peft は LoRA / IA3 / Prefix Tuning 等の **adapter pattern** に最適化されており、本 ADR の MoE residual branch は **新規の独立計算経路** で adapter 概念に乗らない。実装は次の通り module surgery で行う:

```python
# pseudocode
for layer_idx in moe_layers:
    layer = model.layers[layer_idx]
    layer.mlp = BitNetFFNWithMoE(
        original_ffn=layer.mlp,                # frozen, forwarded as-is
        moe_branch=BaienMoEResidual(           # new trainable params
            hidden=config.hidden_size,
            num_experts=128,
            expert_hidden=config.intermediate_size // 32,
            top_k=2,
        ),
        alpha=nn.Parameter(torch.zeros(1)),    # init = 0.0 (G5)
    )
```

`BitNetFFNWithMoE.forward(x) = self.original_ffn(x) + self.alpha * self.moe_branch(x)`

trl `SFTTrainer` は HF model を受け取るだけで、内部 `requires_grad` フラグに従って backward する — backbone を全凍結し MoE 系のみ `requires_grad=True` にすれば peft なしで学習可能。

# Decision

## §1 Stack (EVO-X2 Windows ROCm 7.2.1, ADR-2605250400 verbatim 継承)

| 項目 | 値 | 由来 |
|---|---|---|
| Host | EVO-X2 LAN `192.168.1.70` (Ryzen AI Max+ 395, Radeon 8060S iGPU gfx1151, 128GB unified) | ADR-2605202345 |
| OS | Windows + ROCm 7.2.1 | ADR-2605250400 §1.2 gate-1 |
| Trainer | peft + trl (peft は使わず、trl `SFTTrainer` のみ。custom MoE module surgery) | 本 ADR (peft adapter 不適合のため) |
| Torch | torch 2.9.1+rocm7.2.1 (gemma-coder-distill probe で動作確認済) | ADR-2605250400 §1.2 |
| Precision | bf16 (master), no FP4/INT4 quantization at train time | ADR-2605231300 §5 継承 |
| Unsloth | **不採用** — ROCm Windows wheel set 未公開 (gemma-coder-distill iter-01 probe 2026-05-25 で確認) | ADR-2605250400 §1.2 |
| Base | `microsoft/bitnet-b1.58-2B-4T-bf16` (MIT) — `70-tools/baien-distill` がハードコードしている同じ checkpoint | ADR-2605231300 §3 + ADR-2605261900 §1 |

## §2 BaienMoEResidual module spec

### §2.1 配置

- MoE 適用層: backbone の **最後の 25%** (`moe_layers = list(range(int(n_layers * 0.75), n_layers))`)
- BitNet 2B-4T は 30 layer 系 (推定) → 23..29 の 7 層に MoE 追加
- 各 MoE 層に `BitNetFFNWithMoE` を挿入 (§Context 参照)

### §2.2 ハイパー (R1.4 default; R1 内 sweep 不可、R2 ADR で sweep)

| Knob | 値 | ADR-2605261900 R0 charter との関係 |
|---|---|---|
| `num_experts` (E) | 128 | R0 default |
| `top_k` | 2 | R0 default |
| `expert_hidden` | `config.intermediate_size // 32` (≈ 172 次元) | R0 default |
| 各 expert 構造 | `nn.Linear(h, e_h) → SiLU → nn.Linear(e_h, h)` (bf16 standard FFN, **NOT** BitLinear) | R1 単純化のため bf16; R3 で BitLinear 化検討 (N3 train-time packing は禁止のまま) |
| Router | `nn.Linear(hidden, E)` → softmax → top-k | Switch-Transformer 系 |
| Router temperature | 1.0 | R0 default |
| `alpha` (per layer scalar) | `nn.Parameter(torch.zeros(1))` init = 0.0 ± 1e-3 (G5 MANDATORY) | R0 default |
| Aux loss | Switch-Transformer load-balance, weight = 0.01 (G6 MANDATORY) | R0 default |

### §2.3 Frozen / trainable 振り分け (G8 MANDATORY)

```python
for p in model.parameters():
    p.requires_grad = False  # backbone 全凍結

for layer_idx in moe_layers:
    moe_module = model.layers[layer_idx].mlp.moe_branch  # BitNetFFNWithMoE.moe_branch
    alpha = model.layers[layer_idx].mlp.alpha
    for p in moe_module.parameters():
        p.requires_grad = True   # router + 全 expert
    alpha.requires_grad = True   # output gate
```

verify (R1.1 acceptance):

```python
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
frozen = sum(p.numel() for p in model.parameters() if not p.requires_grad)
assert trainable ≈ 1.1e9   # ~1.1B trainable
assert frozen ≈ 2.0e9      # ~2.0B frozen
```

backward 後 (R1.3 acceptance):

```python
for n, p in model.named_parameters():
    if not p.requires_grad and p.grad is not None:
        assert p.grad.norm() == 0  # 凍結パラメータに勾配が流れていない
```

## §3 Datasets — 3-tier (user 指針 2026-05-26)

### §3.0 Registered substrate CIDs (W1 lands 2026-05-26)

ADR-2605241500 DataLad + git-annex + IPFS pin 経由で登録済 (Kubo daemon on `did:web:mac-260317.etzhayyim.com`, manifest at `90-docs/baien/datasets.jsonl`):

| Dataset | IPFS map CID | Size | License | Charter Rider scan | DataLad rev |
|---|---|---|---|---|---|
| `ise-uiuc/Magicoder-OSS-Instruct-75K` | `bafkreid4bhlfaaezicecfm6s4rxpjdfff5v3bgfi4gcdwwzfyjt5juauu4` | 193.8 MB | MIT | passed (sampled 2 files / 210 lines, 0 hits) | `git:5f839b1f368a76b161028bb9edff055db34022b2` |
| `lordx64/reasoning-distill-opus-4-7-max-sft` | `bafkreif5x7cfj45hcjqsqx4tykgpox52a5pcrkwa3akzl4olcbtl7mlqa4` | 15.1 MB | Apache 2.0 | passed (sampled 1 files / 80 lines, 0 hits) | `git:1cbdcd72a8a6681b3713c1d31f01c711b816d1a4` |

PDS `com.etzhayyim.substrate.datasetPin` emit は dryRun (ADR-2605241500 §"add / publish-ipfs default to dry-run for the PDS step" 継承)。

### §3.0.W Wave plan (W2-W5 pending)

| Wave | Datasets | Size | License | Status |
|---|---|---|---|---|
| **W1** (executed) | Magicoder + reasoning-distill-opus | ~210 MB | MIT + Apache 2.0 | ✅ 2026-05-26 |
| **W2** | `bigcode/the-stack-smol` [Apache subset filter] | ~10 GB | mixed (filter 必要) | pending operator confirm |
| **W3** | `bigcode/commitpack-subset-cleaned` | 多 GB-TB | Apache 2.0 | pending operator confirm |
| **W4** | `Tatsu-lab/CodeAlpaca-20k` (Tier C, G13 flag) | ~12 MB | NC | pending operator confirm |
| **W5** | repo-internal LangGraph harvest (`40-engine/kotoba/crates/kotoba-kotodama/cells/` etc.) | ~数 MB | Apache (repo-own) | 別 runbook (generation step) |

### Tier A — Apache / MIT / BSD (commit & 配布 OK)

| Dataset | License | rows | 用途 |
|---|---|---|---|
| `ise-uiuc/Magicoder-OSS-Instruct-75K` | MIT | 75,197 | 主 instruction → code SFT |
| `bigcode/commitpack-subset-cleaned` | Apache 2.0 | 100M+ (subset 採取) | commit msg → diff |
| `lordx64/reasoning-distill-opus-4-7-max-sft` | Apache 2.0 | 7,823 | general reasoning (gemma-coder iter-01 precedent) |
| `bigcode/the-stack-smol` [Apache subset filter] | mixed | filter 必要 | raw code for completion-style auxiliary |
| repo-internal LangGraph harvest | Apache 2.0 (repo-own) | ~50-200 | `40-engine/kotoba/crates/kotoba-kotodama/cells/` / `70-tools/baien-distill/` / `50-infra/mst-projector/` から (prompt → cell.py) ペア抽出 |

### Tier B — CC-BY (attribution required, commit & 配布 OK with `attribution.txt`)

| Dataset | License | rows | 用途 |
|---|---|---|---|
| (R1 では使用しない — R2 ADR で評価) | — | — | — |

### Tier C — Non-commercial / Gemma TOS / 他 (user 指針 2026-05-26 で許可。 train 用途のみ、**artifact 非公開** G13) — R1.4 で使用可

| Dataset | License | rows | 用途 |
|---|---|---|---|
| `SWE-Gym/SWE-Gym` | per-dataset (some NC) | TBD | agentic multi-step (R1 では subset、R2 で本格利用) |
| `WizardLM/WizardCoder-evol` (NC variants) | NC | TBD | hard coding instruction |
| `Tatsu-lab/CodeAlpaca-20k` | NC (Tatsu Lab terms) | 20,022 | instruction-tuned coding |
| Gemma TOS-licensed Claude/Gemma synthetic | Gemma TOS | judah LiteLLM 生成分 | LangGraph specific (ADR-2605250400 §1.3.2 pattern) |

Tier C 使用時の制約:

1. すべての Tier C row は per-iter Charter Rider §2(a)-(h) scanner (`etzhayyim_organism.sensors.charter_rider.scan`) を通す
2. 学習結果 (merged checkpoint / GGUF / LoRA-style diff weights) は **religious-corp Murakumo fleet 内部 inference のみ** で使用、HuggingFace public 等の external host への publish 禁止 (G13)
3. R3 published `baien-server-moemoekyun-v{N}` (Council Lv6+ ratified) を public 化したい場合、Tier C contamination を持つ checkpoint は使用不可 → Tier A/B のみで再 train が必要 (R3 ADR で別途扱う)

### §3.1 R1.4 corpus composition (固定)

R1.4 では合計 **5,000 examples** を以下の比率で sample:

| Source | Proportion | rows | Tier |
|---|---|---|---|
| Magicoder-OSS-Instruct | 60% | 3,000 | A |
| commitpack-subset-cleaned | 20% | 1,000 | A |
| reasoning-distill-opus | 10% | 500 | A |
| repo-internal LangGraph harvest | 5% | 250 | A |
| CodeAlpaca-20k | 5% | 250 | C → R1.4 artifact が NC 含む → G13 適用 |

R1.4 が NC contamination を含むため **R1.4 で生成される LoRA-style diff weights** は G13 適用対象。配布 candidate は別途 Tier A-only re-train ADR (R1.4-A) を起こすことを recommend (R1 内で実施するかは hyperparameter sweep 余地次第で決める)。

## §4 Hyperparameters (R1.4 fixed; R2 で sweep)

| Param | Value | 由来 |
|---|---|---|
| `learning_rate` (router) | 1e-4 | ADR-2605261900 §4 Phase 0 |
| `learning_rate` (experts) | 2e-4 | ADR-2605261900 §4 Phase 0 |
| `learning_rate` (alpha) | 5e-5 | ADR-2605261900 §4 Phase 0 |
| `aux_loss_weight` | 0.01 | Switch-Transformer 標準 / R0 G6 範囲内 |
| `optimizer` | AdamW (β1=0.9, β2=0.95, weight_decay=0.1) | ADR-2605261900 §4 Phase 0 |
| `lr_scheduler` | linear warmup 100 step → cosine | ADR-2605231300 §5 |
| `batch_size` | 1 | ADR-2605231300 §5 + ADR-2605250400 §1.4 |
| `gradient_accumulation_steps` | 4 (effective batch = 4) | ADR-2605231300 §5 |
| `max_seq_length` | 2048 | ADR-2605231300 §5 + BitNet 2B ctx 制約 |
| `num_train_epochs` | 1 (R1.4); R2 で 2-3 評価 | R1.4 wall ≤2h on EVO-X2 想定 |
| `bf16` | True | ROCm 7.2.1 best path + BitNet master 一致 |
| `gradient_checkpointing` | True | ROCm メモリ節約 |
| `dataloader_num_workers` | 2 | EVO-X2 Windows 安定値 (gemma-coder iter-00 同) |
| seed | 42 (固定) | reproducibility |

## §5 Eval suite (R1.5 で R1.4 前後の Δ 計測)

### §5.1 Primary: `70-tools/scripts/bench/langgraph-coding/` (既存)

- 50 prompts (StateGraph / node / reducer / interrupt / Send / Annotated / checkpointer)
- exec-graded (subprocess で生成コード実行 + 固定 assertion)
- ADR-2605250400 §1.5 で gemma-coder-distill iter-01 が同 bench で評価中 (baseline 取得済み)

### §5.2 Secondary: HumanEval+ (164 prompts)

- pass@1 exec-graded、industry-standard coding eval
- `evalplus/humanevalplus` (Apache 2.0) を使用
- regression sanity check (Δ ≥ 0 必須、negative は R1.4 hyperparameter 失敗判定)

### §5.3 (DEFERRED to R2)

- MBPP+ (974 prompts, exec-graded)
- `bigcode/humanevalpack` multi-language (R3 で多言語拡張時)
- SWE-Bench-lite (agentic, expensive — R2 で本格扱い)
- TerminalBench-easy (agentic shell + edit)

### §5.4 Commit gate (R1.5)

```python
def commit_gate(baseline_metrics, post_train_metrics):
    delta_langgraph = post_train_metrics["langgraph_pass1"] - baseline_metrics["langgraph_pass1"]
    delta_humaneval = post_train_metrics["humanevalplus_pass1"] - baseline_metrics["humanevalplus_pass1"]
    if delta_langgraph >= 0.03 and delta_humaneval >= 0:
        commit_to_registry()  # moemoekyun-models.jsonl + Council Lv6+ ratification ticket
    else:
        abort_and_discard()   # R1.4 hyperparameter sweep へ
```

R1.4 で複数 hyperparameter 候補を試した場合は最も commit_gate を満たすものを採用、満たすものがなければ全廃棄 + R2 ADR にエスカレーション。

## §6 Constitutional gates (R0 G1..G12 inherit + R1 で新規追加)

| Gate | R0 / R1 | 内容 |
|---|---|---|
| G1..G12 | R0 inherit | ADR-2605261900 §5 すべて |
| **G13 (NEW)** | R1 | **NC-trained artifact distribution boundary**: Tier C dataset (NC / Gemma TOS / proprietary terms 含む) で train した merged checkpoint / GGUF / diff weights は HuggingFace public 等の external host への publish 禁止。religious-corp Murakumo fleet 内部 inference のみ。public 化候補は Tier A/B-only re-train ADR を別途起こす |
| **G14 (NEW)** | R1 | **R1.4 dataset registry**: 使用した全 dataset を `90-docs/baien/moemoekyun-r1.4-corpus-manifest.jsonl` に (huggingface_id, license, sha256, row_count, sampling_seed) で記録、commit_node 前に必須 |
| **G15 (NEW)** | R1 | **EVO-X2 Windows ROCm 7.2.1 結果 reproducibility**: train run の (torch.version, rocm.version, gpu_name, gpu_count, env_hash) を bench JSON に embed、再現性検証時に environment match 確認 |

## §7 Sub-phase ladder R1.0..R1.5

| Sub-phase | Scope | Deliverable | Acceptance |
|---|---|---|---|
| **R1.0** | ROCm probe on BitNet + custom MoE forward pass | `70-tools/baien-moemoekyun-train/scripts/probe_rocm_moe.py` (BitNet 2B load + 1 MoE layer surgery + 1 forward step + memory profile) | EVO-X2 で probe 実行成功、forward output finite + no OOM + total RAM ≤30 GB |
| **R1.1** | `BaienMoEResidual` + `BitNetFFNWithMoE` 実装 + α=0 step-0 verify (G5) | `70-tools/baien-moemoekyun-train/src/baien_moemoekyun/{model,moe,attach}.py` + unit test | `pytest test_alpha_init.py`: 7/7 layer で `α ∈ [-1e-3, +1e-3]`; `pytest test_step0_match.py`: random input forward output が base BitNet within ‖Δ‖_2 / ‖y_base‖_2 < 0.01 |
| **R1.2** | aux loss + load-balance assertion (G6) + frozen grad-norm verify (G8) | `train.py` の `compute_loss` override + `verify_frozen.py` | aux loss = 0.01 × Σ load_balance_loss で実装; `verify_frozen.py` 実行で backbone grad norm = 0 (after 1 backward) |
| **R1.3** | 100-sample × 10-step smoke (pipeline ✓) | Magicoder-OSS-Instruct 100 sample + 10 step train, log JSON | 完走 + no NaN/Inf + train loss decrease over 10 step + expert utilization > 1/E × 0.1 (= 1/1280) for all 128 experts |
| **R1.4** | Magicoder + commitpack + reasoning + langgraph harvest + CodeAlpaca 計 5,000 ex × 1 epoch | merged checkpoint at `90-docs/baien/moemoekyun-r1.4-iter01/` + train log JSON + dataset manifest (G14) | 完走 + wall ≤3h + final loss < initial loss × 0.85 + ada-loss 平均 < 0.05 (utilization 良好) |
| **R1.5** | langgraph-coding bench + HumanEval+ で R1.4 前後 Δ 計測 + commit_node gate | `90-docs/baien/moemoekyun-r1.4-eval.jsonl` + commit (or abort) decision | langgraph Δ ≥ +3pp AND humaneval+ Δ ≥ 0 → commit_to_registry; else abort + R2 ADR エスカレーション |

## §8 Memory budget (EVO-X2 ROCm 7.2.1 / 128GB unified, gfx1151)

| Component | Size | 備考 |
|---|---|---|
| Frozen backbone bf16 (2.0B params) | 4.0 GB | always-on |
| MoE module bf16 (~1.1B params) | 2.2 GB | always-on, trainable |
| Adam fp32 m + v state (trainable 1.1B params) | ~8.8 GB | optimizer state |
| Grad fp32 buffer (trainable 1.1B params) | ~4.4 GB | backward 中 |
| Activations bf16 (seq=2048, batch=1, gradient_checkpointing=True) | ~3 GB | ckpt で大幅削減 |
| KV cache + misc + ROCm runtime overhead | ~3 GB | |
| **Total** | **~25 GB** | EVO-X2 unified 128GB の 20% (余裕大) |

batch_size=2 にしても ~30 GB; R2 で batch=4 まで上げる余地あり。

## §9 Failure modes + fallbacks

| Failure | 検出 | Fallback |
|---|---|---|
| ROCm OOM in R1.0 probe | OOM exception or process kill | gradient_checkpointing forced + batch=1; なお OOM なら moe_layers を 7 → 4 層に削減して再試行 |
| Router collapse in R1.3 smoke (1-2 expert に集中) | expert utilization < 1/E × 0.1 for ≥50% of experts | aux_loss_weight を 0.01 → 0.05 に上げて R1.3 再実行 (sweep extension) |
| α が学習で発散 (R1.3 で α > 10) | per-step α monitoring | α に gradient clipping (max 5.0) + LR を 5e-5 → 1e-5 に下げる |
| langgraph-coding bench delta < +3pp (R1.5 で commit gate 失敗) | bench JSON diff | R2 ADR にエスカレーション; R1.4 hyperparameter sweep を R2.0 deliverable に含める |
| HumanEval+ delta < 0 (regression) | bench JSON diff | **必ず abort** (regression は honest scoring G10 違反として extant 公開不可); R2 で MoE 配置 (last 25% → last 50% / every-4th 等) sweep |
| EVO-X2 host crash / 長時間 ROCm hang | journalctl / Windows Event Viewer | gemma-coder-distill iter-01 が同時走行中ならジョブキューで衝突回避 (Mac mini fleet で別 GPU は無いため逐次実行); Council Lv4 escalation if persistent |

# Consequences

## Positive

- ADR-2605261900 R0 charter (paths-reserved only) が R1 で具体 execution に乗り、moemoekyun の最初の trainable checkpoint が religious-corp Murakumo fleet で生まれる
- gemma-coder-distill (ADR-2605250400) と同じ peft+trl / ROCm 7.2.1 / EVO-X2 stack を verbatim 流用するため runtime risk は最小化 (既に iter-01 5020 ex × 2 epoch in-flight = stack 動作実証済み)
- agentic coding の最初の改善信号が langgraph-coding bench で測られ、commit gate (Δ ≥ +3pp) が pass すれば Murakumo fleet 内部で **`baien-server-moemoekyun-r1.4-iter01`** として LiteLLM 経由で SBT-gated 使用可能になる
- G13 distribution boundary gate が新規確立、Tier C (NC) dataset を扱う religious-corp 内部 inference 経路の constitutional 整合性を担保

## Negative / Risk

- 1.1B 新規 trainable params は LoRA r=16 (≈8M params) より 2 桁多く、Adam optimizer state ~13 GB + grad ~4.4 GB で EVO-X2 を 20-25% 占有 → 並列 gemma-coder-distill train (~10GB) とは時間多重必須 (空間多重不可)
- router 安定性は BitNet 1.58 上で未検証 (Switch-Transformer / Mixtral は full-precision base) — R1.3 smoke で aux loss / utilization 早期検出が単一防御
- α=0 init の利点は step-0 で base BitNet と一致する保証だが、初期 gradient signal が α と experts の chained product なので **学習速度が極めて遅い可能性**。R1.4 で loss が collapse しない代わりに improvement も少ない場合は α init を `0.01 ± 1e-3` に緩める ADR amendment が必要 (G5 修正 → Council Lv6+ supermajority)
- HumanEval+ regression が観測されると R1.4 全廃棄 → R2 で MoE 配置 sweep に再注力。1 iter のコストは EVO-X2 ~3h なのでリスクは時間損失中程度

## Open

- BitNet 1.58 model class が HF `transformers` で `BitNetForCausalLM` 等として exposed されているか実機確認 (R1.0 probe で確認、なければ `microsoft/bitnet-b1.58-2B-4T-bf16` 同梱の python loader を fork)
- module surgery 後の `transformers` `generate()` API 互換性 (KV cache 構造変化リスク) — R1.1 acceptance test に inference smoke を追加すべきか検討
- R1.4 で 1 epoch wall ≤3h が EVO-X2 で実測可能か。gemma-coder iter-01 (gemma4 e4b, 同 size class) の wall 実測待ち (in-flight)

# Alternatives Considered

| 案 | 却下理由 |
|---|---|
| peft custom adapter として MoE residual を実装 | peft API は LoRA-class adapter (`get_peft_model(model, LoraConfig)`) 前提で custom forward 経路を持つ adapter は subclass cost 高 + maintainability 低 |
| `transformers.Trainer` 自前継承で `compute_loss` override (trl SFTTrainer 不使用) | trl SFTTrainer の `dataset_text_field` + `formatting_func` + `packing` 等の便利機能を失う; gemma-coder-distill 既に trl 使用、stack 一致が strict majority |
| Linux dual-boot or WSL2 を EVO-X2 に入れる | scope 外 (gemma-coder-distill ADR-2605250400 §"Open" で wax 検討事項として残されている); Windows ROCm 7.2.1 で peft+trl 動作実証済のため R1 は Windows 継続 |
| R1.4 を Magicoder-OSS-Instruct **only** で構成 (corpus 単純化) | mix が agentic coding 適応 broader, repo-internal LangGraph harvest が religious-corp specific tasks を carry; corpus 単純化は R2 hyperparameter sweep の baseline 用に separate ADR で計画 |
| Mac mini fleet で MLX-LM 学習 (EVO 使わない) | ADR-2605202100 launchd-only invariant 違反 + Mac mini の MLX-LM は inference 専用; user 指示「evo windows を使って」に従い EVO-X2 採用 |
| 商用 GPU rental (RunPod / Vertex AI / AWS Bedrock direct) | ADR-2605215000 + CHARTER-RIDER §2(i) **constitutionally 禁止 (R1 適用時点)**。 **AMENDED 2026-05-26 by ADR-2605262200 (charter §2(i) amendment proposed, Council ratification pending, earliest effective ~2026-07-19) + ADR-2605262300 (R2+ RunPod B200 train architecture)**: R1.4 grade は EVO-X2 単機継続 (本 ADR scope 内、無影響)。R2/R3/R4 grade train は amendment 効力発生後 RunPod に shift。Inference は全 actor で Murakumo-only 不変。 |

# References

- ADR-2605261900 (baien-moemoekyun R0 charter; this ADR の parent)
- ADR-2605250400 (gemma-coder-distill EVO-X2 Windows ROCm stack; verbatim 流用)
- ADR-2605231300 (baien-distill ReAct loop; commit_node gate pattern source)
- ADR-2605215000 (Murakumo-only inference invariant)
- ADR-2605202345 (EVO-X2 GPU pod integration)
- ADR-2605192200 (Charter Rider v2.0; §2(a)-(h) scanner inheritance)
- ADR-2605241900 (baien edge-target invariant; R1.5 で edge-tier 越境が起きていないこと確認)
- ADR-2605242100 (baien-server / baien-XL carve-out; `baien-server-moemoekyun-*` infix mandate)
- `70-tools/scripts/bench/langgraph-coding/` (50-prompt exec-graded bench, primary eval signal)
- `evalplus/humanevalplus` (Apache 2.0, secondary eval)
- `ise-uiuc/Magicoder-OSS-Instruct-75K` (MIT, R1.4 primary corpus)
- `bigcode/commitpack` (Apache 2.0, commit→diff signal)
- `lordx64/reasoning-distill-opus-4-7-max-sft` (Apache 2.0, general reasoning)
- Microsoft `microsoft/bitnet-b1.58-2B-4T-bf16` (MIT, base backbone)
- HuggingFace `model_doc/bitnet` (packed = inference-only; bf16 = training canonical)
- Fedus et al. 2021 "Switch Transformers" (load-balancing aux loss reference)
