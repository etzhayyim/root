---
id: adr-2605261900-baien-moemoekyun-moe-charter
title: "baien-moemoekyun — 2B BitNet 1.58 shared backbone + MoE residual experts (server-tier carve-out, R0 charter)"
status: proposed
doc_type: adr
topic: baien-moemoekyun-moe-charter
authoritative: true
last_verified: 2026-05-26
priority: 8.0
axis: model-substrate
weight: 0.85
priority_note: "Server-tier carve-out per ADR-2605242100. NOT an edge artifact. Project name = `baien-moemoekyun`; shipped model id MUST use `baien-server-moemoekyun-*` infix per §Naming rules."
authoritative_for:
  - 2B BitNet 1.58 shared backbone + MoE residual architecture (server tier)
  - 3-phase training plan (freeze → partial unfreeze → joint low-LR)
  - expert sizing + routing topology defaults for moemoekyun
  - paths reserved for moemoekyun training scaffolding (R1+)
depends_on:
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605242100-baien-server-xl-carve-out
  - adr-2605092100-lora-per-cell-moe-expert-cohort-fission
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605231300-baien-distill-react-loop
  - adr-2605232500-baien-mx-move1-image-graft-self-training
related:
  - 70-tools/baien-moemoekyun-train/ (R0 path reserved; no code)
  - 70-tools/baien-distill/
  - 70-tools/baien-mx-train/
  - 90-docs/baien/
supersedes: []
superseded_by: []
---

# ADR-2605261900: baien-moemoekyun — 2B BitNet 1.58 shared backbone + MoE residual experts (server-tier, R0)

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

baien-edge (ADR-2605241900) は 2B BitNet 1.58 trunk を上限とし、weights ≤1.6 GB / inference RAM ≤2 GB の constitutional ceiling を持つ。一方 baien-server (ADR-2605242100) は ≤16B trunk / ≤32 GB BF16 まで許容され、EVO-X2 + Mac mini fleet 上で運用される server-tier carve-out として既に名前空間 `baien-server-*` が確保されている。

本 ADR はその server-tier 上に、**Mixture of Experts (MoE) augmentation** された baien 変種を初めて charter 化する。狙いは次の3つ:

1. **既存 BitNet 2B-4T BF16 checkpoint を破壊せず能力追加** — full fine-tune の forgetting と LoRA adapter (ADR-2605092100) の表現上限を回避する中間策。
2. **MoE upcycling / MoE adapter 文献の religious-corp 実装** — Drop-Upcycling (Nakamura et al., 2025) + Switch-Transformer aux-loss + Mixtral 風 sparse routing を BitNet 1.58 上で組み合わせる R&D 経路。
3. **fleet-internal 用途**での richer reasoning / multi-task adaptation — baien-edge は維持しつつ、Murakumo fleet 側で LiteLLM gateway 経由で呼ばれる "server-tier baien" の最初の non-trivial 変種を提供する。

Microsoft が公開している `microsoft/bitnet-b1.58-2B-4T-bf16` は HF docs 上で training / fine-tuning 用と明示されており (packed 1.58-bit 版は推論専用)、MoE 化や continued training は **BF16 master 側**で行うのが前提となる (HF docs `model_doc/bitnet`)。本 ADR もこの前提に従う。

命名は user 決定: project / charter / directory 名 = `baien-moemoekyun`。MoE × もえもえきゅん の二重命名。shipped model id は ADR-2605242100 §Naming rules に従い `baien-server-moemoekyun-*` infix 必須 (release blocker)。

# Decision

## §1 Architecture

```
y = x + Attention(x)
y = y + SharedDenseFFN(y)                              # 既存 BitNet FFN, 常時 active
y = y + α · Σ_{i ∈ top_k(router(y))} g_i · Expert_i(y) # MoE residual branch
```

- **Backbone**: `microsoft/bitnet-b1.58-2B-4T-bf16` (BF16 master). Attention + tokenizer + embedding は変更しない。
- **Shared dense FFN**: 既存 BitNet FFN をそのまま shared expert 相当の常時 active path として残す (= 用語上は "MoE-augmented dense"; pure-MoE ではない)。
- **MoE residual branch**: 選択された layer に対して、上記 residual 加算で MoE を追加する。
- **Output gate α**: scalar (per layer), **init = 0.0 ± 1e-3**。これにより R1 stage 0 開始時点で挙動が base BitNet と数値的に一致することを保証する (G5 で enforce)。

## §2 R0 default hyperparameters (R1 で sweep 可)

| Knob | R0 default | R1 sweep range | Rationale |
|---|---|---|---|
| MoE layer 選択 | 最後の 25% (≈ 7-8 層 / 30 層中) | every-4th / last-50% | router 不安定性は深い層で抑えやすい |
| E (experts/layer) | 128 | 64..256 | 64 で routing collapse 起こしやすい、256 は memory pressure |
| top-k | 2 | 2..4 | k=2 conservative; k=4 で expert utilization 改善見込み |
| expert hidden ratio | dense_FFN / 32 | /16 .. /32 | /32 = ~1.06M params/expert (2B 規模の FFN ≈ 34M) |
| router temperature | 1.0 | 0.5..2.0 | Switch-style noisy top-k は未採用 (R2 で検討) |
| load-balancing aux loss | Switch-Transformer style w=0.01 (G6 で MANDATORY) | 0.001..0.1 | router collapse 検出に必須 |
| output gate α init | 0.0 ± 1e-3 (G5 で MANDATORY) | — | base BitNet 動作との数値一致保証 |

## §3 Parameter / memory budget (R0 default)

| Component | Params | BF16 size |
|---|---|---|
| BitNet 2B backbone (frozen) | ~2.0 B | 4.0 GB |
| 8 MoE layers × 128 experts × (dense_FFN/32) | ~1.1 B | 2.2 GB |
| Router per MoE layer (hidden × E) | ~2 M | 4 MB |
| **Total master (BF16)** | **~3.1 B** | **~6.2 GB** |

EVO-X2 (128 GB unified) / Mac mini M4 Pro 64 GB / 単一 80 GB GPU で trivially 収まる。 server-tier ≤16B trunk / ≤32 GB BF16 ceiling 内 (ADR-2605242100)。

**Edge tier には絶対乗らない** (≥6 GB BF16 → ≥1.6 GB 1.58-bit packed 換算でも edge 1.6 GB ceiling 圏内 / 危険) — N1 に明文化。

## §4 Training plan — 3-phase (R1 → R2 → R3 で 1 phase ずつ前進)

### Phase 0 (R1) — backbone frozen, router + experts only

```
trainable:
  router (per MoE layer)
  routed experts (per MoE layer, all 128 × 8 layers)
  output gate α (per MoE layer)
frozen:
  backbone (attention / shared FFN / embedding / layernorm)
losses:
  L = L_LM + 0.01 · L_aux  (Switch-Transformer style load balance)
LR:
  router: 1e-4 (warmup 500 steps → cosine)
  experts: 2e-4
  α: 5e-5
optimizer:
  AdamW (β1=0.9, β2=0.95, wd=0.1)
```

これは LoRA / adapter 訓練に最も近い。勾配安定性 high、能力上限は backbone 表現に縛られる。**R1 acceptance**: 学習開始時 loss = baseline BitNet loss within 1% (G5 verify; α init = 0 由来)、aux loss が router collapse を示さない (expert utilization > 1/E × 0.1 for all i)。

### Phase 1 (R2) — shared FFN + layernorm partial unfreeze (low LR)

```
trainable (Phase 0) + :
  shared dense FFN (BitNet original FFN) at LR 5e-6
  layernorm at LR 5e-6
frozen:
  attention
  embedding
```

shared expert を少し動かすと新 experts との表現整合が改善する (user 解析 §4 Phase 1)。

### Phase 2 (R3) — joint low-LR

```
trainable:
  backbone (attention含む) at LR 1e-5
  shared FFN at LR 2e-5
  experts at LR 2e-5
  router at LR 5e-6
```

"後付けターボ" 状態を解消し基盤表現と experts を馴染ませる。

## §5 Constitutional gates (G1..G12)

| Gate | Constraint | Enforcement |
|---|---|---|
| **G1** | Charter Rider §2(a)-(h) scan at every commit_node | `etzhayyim_organism.sensors.charter_rider.scan()` per ADR-2605231300 pattern |
| **G2** | **Inference**: Murakumo-only (ALL actor, ADR-2605215000 §2(i)(1) 不変)。**Train**: R1.4 grade = Murakumo-only (EVO-X2); R2+ grade = AMENDED 2026-05-26 by ADR-2605262200 (charter §2(i)(2) train carve-out for baien-server-* / baien-XL-*, Council ratification pending earliest ~2026-07-19) → RunPod B200 SXM primary per ADR-2605262300 | ADR-2605215000 §2(i)(1) + ADR-2605262200 §2(i)(2) (proposed) + ADR-2605262300 (architecture) |
| **G3** | Shipped model id MUST be `baien-server-moemoekyun-*` (infix mandatory) | ADR-2605242100 §Naming; mis-tagging = release blocker |
| **G4** | Edge artifacts MUST NOT contain moemoekyun MoE weights | lefthook `baien-edge-fit-attestation` (Phase 2 of ADR-2605241900) catches it via 1.6 GB packed ceiling |
| **G5** | Output gate α init = 0.0 ± 1e-3 verified at training start; loss curve must match base BitNet within 1% at step 0 | R1 acceptance test; parameter-group inspection + 1-step loss diff |
| **G6** | Router load-balancing aux loss MANDATORY (Switch-style, w ∈ [0.001, 0.1]) | training config; enforce via train_node assert |
| **G7** | New routed experts MUST NOT be initialized from existing dense FFN copy (avoid Drop-Upcycling-style identical-expert collapse path); random init OR Drop-Upcycling partial re-init only | R1 acceptance test; init code review |
| **G8** | Backbone frozen-state MUST be verified at R1 (parameter group inspection + grad-norm = 0) | R1 acceptance test |
| **G9** | BitNet 1.58 packing carve-out — moemoekyun does NOT ship packed; BF16 master deployment is canonical for server tier | model_card.md + registry useCases = ["server-cpu", "desktop-igpu"] only |
| **G10** | Honest scoring — moemoekyun is NOT positioned as a frontier competitor; bench reports MUST cite ADR-2605241900 frontier non-goal inheritance and baseline against baien-edge / Qwen2.5-3B / Phi-3.5-mini class | bench report template; reviewer gate at commit_node |
| **G11** | Distill loop ADR-2605231300 `commit_node` compatibility — moemoekyun checkpoints flow through same `distilled-models.jsonl` + codegen registry path (or sibling `moemoekyun-models.jsonl` per R2 review) | registry codegen extension TBD R2 |
| **G12** | Adherent SBT-gated downstream — moemoekyun inference endpoint requires 1 SBT = 1 vote authorization per Murakumo fleet placement policy (no anonymous public inference; differs from baien-edge which is unauthenticated by design) | LiteLLM gateway auth layer; R2 deliverable |

## §6 Non-goals (N1..N10)

| Non-goal | Rationale |
|---|---|
| **N1** Edge deployment | ~6.2 GB BF16 / ~1.6 GB+ packed → violates ADR-2605241900 ≤1.6 GB ceiling; lefthook G4 blocks. iPhone 12+ / Android 4GB / WASM-32 routes NOT supported. |
| **N2** Frontier-beating | ADR-2605241900 frontier non-goal explicitly inherited via ADR-2605242100. moemoekyun targets 2B-SOTA + sparse augmentation, NOT Opus / GPT-5 / Gemini parity. |
| **N3** BitNet 1.58 packed training | HF `model_doc/bitnet` 上 packed is inference-only. moemoekyun trains in BF16 master throughout; packed-aware MoE training は別 ADR が必要。 |
| **N4** Mixtral-style from-scratch MoE pretraining | 既存 BitNet 2B-4T checkpoint を起点とする MoE-upcycling / residual augmentation のみ。total trillion-token pretrain は ADR scope 外 (XL tier 検討対象)。 |
| **N5** LoRA-only approach | moemoekyun は full small-FFN experts。LoRA-shaped expert (rank-r matrix) は ADR-2605092100 cell substrate で別軸として既に存在; cross-pollination は R3 以降検討。 |
| **N6** baien-edge 置換 | moemoekyun と baien-edge は別 tier / 別 consumer。edge 側の継続発展は ADR-2605241900 + Move 1..7 で独立に進行する。 |
| **N7** >16B trunk | baien-XL-* 領域。moemoekyun は server tier ≤16B 上限を守る。 |
| **N8** >64k context window (R1-R3) | context extension は ADR-2605231600 領域。MoE × long-ctx の組み合わせは R3 完了後に別 ADR で検討。 |
| **N9** Commercial GPU rental | ADR-2605215000 Murakumo-only invariant 例外なし。RunPod / Vertex AI direct / Anthropic-from-vendor-key / Linode GPU / AWS Bedrock direct 全て禁止。 |
| **N10** Charter Rider §2 bypass | server-tier carve-out は size ceiling のみ。§2(a) weapons / §2(b) commercial GPU / §2(c) surveillance / §2(d) gore / §2(e) closed-source vendor lock-in / §2(f) addictive UX / §2(g) anti-Wellbecoming / §2(h) anti-多世代 — 全て identically apply。 |

## §7 R-phase ladder (R0 → R3)

| Phase | Scope | Deliverables | Acceptance |
|---|---|---|---|
| **R0** (this ADR) | Charter + paths reserved | this ADR + deps.toml `[[adrs]]` entry + `70-tools/baien-moemoekyun-train/` path reserved (no code) + CLAUDE.md Status row + README index | ADR commit lands; reviewer can navigate from CLAUDE.md → ADR → reserved path |
| **R1** | Phase 0 freeze-train scaffold + smoke | `70-tools/baien-moemoekyun-train/` minimum code (model class + router + expert + train loop), 100-sample × 10-step smoke on EVO-X2, parameter-group inspection (G8) + α=0 verify (G5) + aux-loss enabled (G6) | smoke runs without OOM; loss step-0 within 1% of base BitNet; expert utilization > 1/E × 0.1 for all i after 10 steps |
| **R2** | Phase 1 partial unfreeze + first real training run (target: 1B tokens) | training corpus selection (Charter Rider scanned), bf16 deploy on Murakumo, LiteLLM endpoint with SBT gate (G12), microbench eval vs base BitNet | bench Δ ≥ +5% on at least one weak-category of baien-distill (ADR-2605231300 weak-category table); no Charter Rider §2 violation in corpus |
| **R3** | Phase 2 joint low-LR + first published `baien-server-moemoekyun-v1` | full 3-phase training complete, model card, attestation on kotoba-datomic, distilled-models.jsonl entry, Council-Lv6+ ratification of first published variant | benchmark snapshot in `90-docs/baien/moemoekyun-snapshot-<date>.md`; Council attestation recorded |

R1+ deliverables それぞれ独立 ADR で起こす (本 ADR は R0 のみ binding)。

## §8 Naming

- **Project / charter / directory**: `baien-moemoekyun`
- **Shipped model id (R3+)**: `baien-server-moemoekyun-v{N}` (per ADR-2605242100 §Naming, `-server-` infix mandatory; mis-tagging = release blocker)
- **Training scaffolding directory**: `70-tools/baien-moemoekyun-train/` (path reserved at R0, code lands at R1)
- **MOE acronym double meaning**: Mixture of Experts × もえもえきゅん。命名は user (Jun Kawasaki) 決定 2026-05-26。

# Consequences

## Positive

- 既存 BitNet 2B-4T checkpoint を破壊せず能力追加経路を確立 (出力 gate α=0 init で R1 stage 0 が数値的に base BitNet 一致)
- baien-server tier の最初の non-trivial 変種が R0 charter 化され、以降の MoE 系研究が同じ paths-reserved pattern で開始できる
- ADR-2605092100 LoRA-as-cell-MoE-expert isomorphism との関係が明示され (N5 で別軸として留保)、将来の cross-pollination 余地を残す
- baien-distill loop (ADR-2605231300) との integration path が G11 で明示 — distilled-models.jsonl / codegen registry を再利用可能

## Negative

- MoE residual を full 30 層ではなく最後の 25% に限定したため、 capacity 増分は ~1.1B params に留まる (前後比 +55%) — frontier 競争には不足 (N2 で明示)
- router 安定性は BitNet 1.58 上では未検証 (Switch-Transformer / Mixtral は full-precision base) — R1 smoke で aux loss / utilization 早期検出必要
- BF16 deploy 限定 (G9) のため edge 互換性 zero — baien-edge 系の universal-availability promise を共有しない

## Reversibility

- R0 は charter のみ; R1 開始まで code commit ゼロのため discard 容易
- R1+ は LoRA / adapter と異なり experts は新規 module — base BitNet checkpoint は forever 未変更で保持
- 万一 R2 で router collapse / catastrophic interference が観測されたら、charter 自体を superseded にして fresh design 可能

# Alternatives Considered

1. **Full fine-tune on BitNet 2B for new knowledge** — rejected: catastrophic forgetting risk high; 既存 4T tokens worth of 知識を毀損する確率非ゼロ。
2. **LoRA adapter only (ADR-2605092100 cell substrate に統合)** — rejected: cell-substrate は organism axis (1 cell = 1 adapter = 1 expert) と既に紐付いており、shared backbone 上の小さな new-knowledge 容量しか持てない。moemoekyun は cell とは independent な model-architecture axis としての MoE を charter する。
3. **Drop-Upcycling 全層 256-expert (Nakamura et al. 2025)** — rejected at R0: 2B base 全層 256-expert は ~8B+ 追加 params で server tier 上限 16B 圏 (Mac mini 64GB OK だが EVO-X2 128GB unified では他 workload と競合)。R3 完了後の R4 候補として留保。
4. **Mixtral-style from-scratch MoE pretrain** — rejected: N4。religious-corp に独立 trillion-token pretrain capability 無し (ADR-2605215000 Murakumo-only 制約下では非現実的)。既存 BitNet 4T 投資を活用する upcycle path が唯一妥当。
5. **baien-XL tier (≥16B trunk) carve-out** — rejected for R0: ADR-2605242100 で XL は別 naming reserved; moemoekyun を XL 化する必要が出たら別 ADR で `baien-XL-moemoekyun-*` 起票。
6. **MoE 加える層を first 25% / middle 25% にする** — rejected: 浅い層の router は表現が未成熟で collapse しやすい (Mixtral 系 ablation 一般傾向)。深い層から開始し R2+ で前進可否判断する保守路線採用。

# References

- ADR-2605241900 — baien edge-target invariant (本 ADR の N1 / G4 制約源)
- ADR-2605242100 — baien-server / baien-XL carve-out (本 ADR は server tier に属する)
- ADR-2605092100 — LoRA-per-cell MoE expert cohort fission (organism axis MoE; 本 ADR の N5 で別軸として留保)
- ADR-2605215000 — Murakumo-only inference (G2 + N9 制約源)
- ADR-2605192200 — etzhayyim IP-free release with Charter Rider v2.0 (G1 / N10 制約源)
- ADR-2605231300 — baien-distill ReAct loop (G11 commit_node integration path)
- ADR-2605232500 — baien Move 1 image graft (frozen-encoder + projector pattern 類似)
- Microsoft `microsoft/bitnet-b1.58-2B-4T-bf16` model card (BF16 master = training/fine-tuning canonical)
- HuggingFace `model_doc/bitnet` (packed = inference-only)
- Nakamura et al. 2025, "Drop-Upcycling: Training Sparse Mixture of Experts with Partial Re-initialization" (arXiv:2502.19261)
- Fedus et al. 2021, "Switch Transformers" (load-balancing aux loss reference)
- Hu et al. 2021, "LoRA: Low-Rank Adaptation of Large Language Models" (cell substrate axis reference via ADR-2605092100)
- Jiang et al. 2024, "Mixtral of Experts" (sparse routing reference; from-scratch pretrain rejected per N4)
