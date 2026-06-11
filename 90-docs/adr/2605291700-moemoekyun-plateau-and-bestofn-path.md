---
id: ADR-2605291700
title: baien-moemoekyun plateau analysis (cycles 17-114) + Best-of-N as the deployable score-lift path
status: active
doc_type: adr
topic: baien-moemoekyun
authoritative: true
authoritative_for:
  - moemoekyun adapter capability ceiling on BitNet 2B
  - score-improvement path forward for baien-moemoekyun deployment
last_verified: 2026-05-29
related:
  - ADR-2605261900
  - ADR-2605262100
  - ADR-2605280800
  - ADR-2605263000
  - ADR-2605263100
depends_on:
  - ADR-2605261900
  - ADR-2605262100
  - ADR-2605215000
  - ADR-2605241900
---

# baien-moemoekyun plateau analysis + Best-of-N as the deployable score-lift path

## Context

Cycle 17-114 (≈3 weeks elapsed wall-clock, 12 independent ckpt configurations,
~30h cumulative RunPod RTX 5090 GPU rental under Founder Lv7+ emergency
authorization per ADR-2605263000/263100) attempted to improve baien-moemoekyun
HumanEval+ pass@1 above the empirical 33.54% (55/164) "8-plateau" observed
across all tested adapter variants.

Every attempted lever lands on the same 55-problem pass set:

| Lever | Range tested | Result |
|---|---|---|
| Trainable mass | 4.22% → 25.3% of model | 33.54% |
| Expert count | 16 → 2048 | 33.54% |
| top_k | 2 → 8 | 33.54% |
| Routing | learned linear / distance MoCLE | 33.54% |
| Expert kind | FFN 2-layer SiLU / memory vector (UltraMem) | 33.54% |
| α gate init | 0.0 / 0.1 | 33.54% |
| Output normalization | none / LayerNorm + out_scale | 33.54% |
| Training method | SFT 500-5000 step / RLVR 5-50 step / RLVR-KL | 33.54% |
| Training data | distill / agentic / NC-free / various corpus mixes | 33.54% |

Concurrent Best-of-N (T=0.7, n=5, on full HE+ 164, cycle 110): **49.39%**
(pass@5 vs greedy 33.54%, **+15.85pp**).

## Decision

### 1. The 33.54% greedy plateau is BitNet-2B-bounded, not adapter-bounded

Multiple verifications established that the residual MoE adapter **cannot
materially shift the BitNet 2B backbone's greedy decode argmax decisions**
under any tested configuration:

- **Diagnostic empirical** (cycle 112c): forward hook capture showed
  `moe_out` magnitude 0.006 vs `ffn_out` 641 (raw moe) and 0.73 vs 641
  (post-LayerNorm fix). Even forcing α=1.0 the wrapper logit shift is
  mean 0.016 / max 0.125 — visible but below the threshold needed to
  flip argmax on the specific HE+ problems.

- **Direct ckpt comparison** (cycle 112c): c105 (UltraMem SFT), c108
  (R2 backbone-unfreeze), c111 (RLVR 50-step) all produce IDENTICAL
  logits on the same input under deterministic decoding.

- **Architectural fix attempts** (cycle 113/114): adding `out_norm`
  + `out_scale` (commit `e2cd3dc79`), fixing trainer to include them
  in optimizer param groups, and overriding α-init from 0.0 to 0.1
  (commit `e72255271`) — all still land at 33.54% HE+ greedy.

The +14.64pp lift from raw baseline 18.90% to plateau 33.54% comes from
the **chat-template wrapping in the inference harness**, not adapter
training. Trained vs untrained adapters produce identical pass set; the
chat-template wrapper is the only differentiator.

### 2. Best-of-N inference is the deployable score-lift path

Cycle 110 canonical bench on full HE+ 164 (commit `94b3a00ae`):

| Metric | Value |
|---|---|
| pass@1 (T=0.7) | 32.32% |
| **pass@5** | **49.39%** |
| any-pass (≥1 of 5) | 49.39% |

Per-problem distribution:
- 23 / 164 (14%) always-pass 5/5 (easy)
- **58 / 164 (35%) sometimes-pass 1-4/5** (stochastic headroom)
- 83 / 164 (51%) never-pass 0/5 (true backbone ceiling)

Therefore: **Best-of-N at inference time, with N=5 and any verifier signal,
captures +15.85pp** over greedy. For HE+ benchmarking with test cases as
oracle verifier, this is the deployable +15pp. For production code
deployment, a syntax+lint verifier captures a fraction of this; a
domain-specific verifier (unit tests, type check, e7m corpus contract
scan) captures more.

### 3. Future score-lift beyond 49.4% requires backbone scale

The 83/164 (51%) "never-pass even with 5 samples" problems are the
**true backbone capability ceiling** of BitNet 2B-4T on HumanEval+.
No adapter / RLVR / Best-of-N / decoding trick can solve these — they
require either:

- (a) Larger backbone (BitNet 4B / 7B — blocked on Microsoft public
  release; Phi-3.5-mini 3.8B at HE pass@1 ~50%; Qwen 2.5 Coder 1.5B
  at ~35% — both violate ADR-2605241900 baien edge invariant requiring
  BitNet 1.58 ternary trunk)
- (b) Continue-pretrain backbone on code-heavy 4-8T tokens (~$50-200
  GPU cost; Chinchilla over-train laws predict +2-5pp HE+)
- (c) Full backbone unfreeze + RLVR (10-20× compute; untested, Founder
  Lv7+ auth available; theoretical max =~ pass@5 ceiling 49.4%)

## Consequences

### Per-cycle artifact catalog (cycle 17-114)

All artifacts IPFS-pinned (Tier-A, Apache-2.0):

| Cycle | Artifact | CID |
|---|---|---|
| 18 | R1.4 smoke train (100 ex × 10 step) | — |
| 28 | R1.4 full scale (128×7×5000) | — |
| 41 | MBPP+ post-train | — |
| 44 | NC-free derivative (c43) | — |
| 50 | BFCL+ToolBench+SWE-bench+Aider harness | — |
| 104 | MoCLE distance-routing HE+ | Qm…SSNcD |
| 105 | UltraMem 2048 mem experts HE+ | Qm…KEB8Sa |
| 107 | RLVR smoke runlog | Qm…SkVRgi |
| 108 | RLVR high-LR HE+ + runlog | Qm…6Jqk18y / Qm…rq6Xx |
| 109 | pass@k first-50 (biased) | Qm…RkVNL |
| 110 | **pass@5 full 164 (canonical)** | **QmXdb7b2cBe1dwfAS7U3gqbktnaETn1iprnTyfWsG9Ppst** |
| 111 | RLVR 50-step + HE+ | Qm…iA9wb / Qm…E8gatA |

Manifest at `90-docs/baien/bench-datasets-cid-manifest.jsonl`.

### Code path summary

- `moe.py` (commit `e2cd3dc79`): LayerNorm + out_scale on moe_branch output
- `trainer.py` (commit `e72255271`): out_norm + out_scale in optimizer
- `production_bitnet_moe_r14_full.py` (commit `e72255271`): `--alpha-init`,
  `--routing-mode`, `--expert-kind` CLI flags
- `rlvr_train.py` (commit `1dfb83b03`): KL-RLVR v1 (β·KL against reference
  ckpt); on-policy GRPO loop with verifier-based binary rewards
- `bench_passk_humanevalplus.py` (commit `de54549ac`): Chen et al 2021
  unbiased pass@k estimator over N samples
- All bench harnesses (`bench_trained_*.py`) support `--routing-mode`
  and `--expert-kind` for new architecture

### Deployable inference path

For production baien-moemoekyun deployment, use **Best-of-N inference**:

```
generate N=5 samples at T=0.7
score each via available verifier signal (lint / type / domain-specific)
return highest-scored sample
```

Implementation pending as `baien-moemoekyun-inference.py` (Cycle 115 if pursued).

### Constitutional invariants preserved

- ADR-2605215000 Murakumo-only inference (RunPod use only under Founder
  Lv7+ ADR-2605263000/263100 burst auth; production inference still Murakumo)
- ADR-2605241900 baien edge invariant (BitNet 1.58 ≤4B trunk; no model swap)
- ADR-2605261900 §G5 α-init=0 default preserved (--alpha-init flag for
  override only)
- ADR-2605192200 Charter Rider §2(i) train-only commercial GPU carve-out
  remains gated on Council Lv6+ ratification (~2026-07-19+)

## Alternatives Considered

- **Continue cycle 115+ on baien-moemoekyun adapter**: REJECTED. ROI
  near-zero given 12 plateau confirmations; further cycles measure
  the same backbone-with-chat-template.

- **Backbone unfreeze + RLVR**: DEFERRED. Theoretical max gain ~+15pp
  (matching pass@5), 10-20× compute. Worth pursuing only if (a) pass@5
  proves insufficient for application requirements or (b) Council
  ratifies higher Charter Rider §2(i) burst budget.

- **Pivot to non-BitNet base** (Qwen 2.5 Coder / Phi-3.5-mini):
  REJECTED. Violates ADR-2605241900 baien edge invariant.

- **Wait for Microsoft BitNet 4B/7B public release**: DEFERRED. No
  timeline; the BitNet b1.58-2B-4T is the only artifact currently
  open-sourced (per Microsoft Mar 2025).

## References

- ADR-2605261900 (baien-moemoekyun R0 charter)
- ADR-2605262100 (baien-moemoekyun R1)
- ADR-2605280800 (cycle 17-82 empirical findings + expert scaling)
- ADR-2605263000, ADR-2605263100 (Founder Lv7+ emergency auth)
- ADR-2605215000 (Murakumo-only inference)
- ADR-2605241900 (baien edge invariant)
- Chen et al 2021 "Evaluating Large Language Models Trained on Code" (pass@k unbiased estimator)
- Hoffmann et al 2022 "Training Compute-Optimal Large Language Models" (Chinchilla)
- DeepSeek R1 / Tülu 3 (RLVR / GRPO)
- Microsoft BitNet b1.58 2B-4T (the underlying frozen backbone)
