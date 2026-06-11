---
id: moemoekyun-bench-plan-260526
title: "baien-moemoekyun bench plan — Phase 1-5 with category-honesty + RTX 5090/B200 cost matrix"
status: active
doc_type: how-to
topic: moemoekyun-bench-plan
authoritative: true
last_verified: 2026-05-26
related:
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
  - adr-2605262300-baien-moemoekyun-r2-runpod-b200-train-architecture
  - 70-tools/baien-moemoekyun-train/scripts/bench_gpqa_diamond.py
  - 90-docs/baien/bench-snapshot-260526-bitnet2b-gpqa-diamond.jsonl
  - doc-260523-frontier-bench-snapshot
---

# baien-moemoekyun bench plan — Phase 1-5 (2026-05-26)

User-supplied 5-model 26-35B comparison table (Qwen3.5-27B / Gemma4-31B /
Qwen3.5-35BA3B / Gemma4-26BA4B / Qwen3.6-35BA3B) lists ~30 benches across 4
categories. Honest assessment **before** committing compute: most are either
agentic-harness-bound or Qwen-proprietary. Baseline BitNet 2B is expected
**substantially below** the reference column (frontier non-goal per
ADR-2605241900); the value of benching is **directional signal** for moemoekyun
R1.4 corpus rebalance, not parity claim.

## Bench categorization

| Category | Benches | Runnable today? | Wall (BitNet 2B) | Verdict |
|---|---|---|---|---|
| **A. Academic loglikelihood** | MMLU-Pro / MMLU-Redux / SuperGPQA / C-Eval / GPQA-diamond | ✅ lm-eval-harness on EVO ROCm | ~30 min - 2h each | **Phase 1 today** |
| **B. Generative math** | HMMT Feb25 / Nov25 / Feb26 / AIME26 / IMOAnswerBench | △ lm-eval-harness generative path, slow on BitNet 2B (100 q × 2 min/q ≈ 3h each) | 2-3h each | **Phase 2 (EVO online or RunPod)** |
| **C. Exec-graded coding** | LiveCodeBench v6 | △ exec sandbox + generation, 500+ tasks | 数時間 | **Phase 3 (RunPod RTX 5090 cheapest)** |
| **D. Agentic coding** | SWE-bench Verified / Multilingual / Pro / Terminal-Bench 2.0 | ❌ needs SWE-agent + docker isolation per task, harness未scaffold | days + train compute | **Phase 4 (R3 ADR)** |
| **E. Agentic general** | TAU3-Bench / VITA-Bench / DeepPlanning / Tool Decathlon / MCPMark / MCP-Atlas / WideSearch | ❌ complex agentic harnesses, mostly未scaffold | weeks | **Phase 5 (R3+ ADR)** |
| **F. Proprietary / Qwen-specific** | Claw-Eval Avg / Pass^3 / SkillsBench Avg5 / QwenClawBench / NL2Repo / QwenWebBench | ❌ public eval not available (Qwen-internal) | impossible | **REJECTED** |

→ **Phase 1 (A) + Phase 2 (B) + Phase 3 (C)** = ~10 of ~30 benches runnable
without harness engineering. The other 20 benches require R3+ engineering
(SWE-agent integration / agentic harnesses) or are rejected (F).

## Phase 1 — Academic loglikelihood (target: 2026-05-27)

| Bench | HF dataset | Items | Eval mode | EVO wall (estimated) |
|---|---|---|---|---|
| MMLU-Pro | TIGER-Lab/MMLU-Pro | 12,032 | 5-shot loglikelihood | ~45 min |
| MMLU-Redux | edinburgh-dawg/mmlu-redux | 3,000 | 5-shot loglikelihood | ~15 min |
| SuperGPQA | m-a-p/SuperGPQA | 26,529 | 5-shot loglikelihood | ~90 min |
| C-Eval | ceval/ceval-exam | 13,948 (test) | 5-shot loglikelihood | ~45 min |
| GPQA-diamond | Idavidrein/gpqa (GATED — HF auth required) | 198 | 5-shot loglikelihood | ~5 min |

**Phase 1 total wall on EVO ROCm: ~3.5h**

Runner: `lm-eval-harness 0.4+` (per ADR-2605232400 §A revised strategy, _completions
variants for ~30 min/task vs _generative ~28h/task).

Note: GPQA gated; requires `huggingface-cli login` before run. Stand-in =
MMLU-domain subsets (high_school_physics / college_physics / college_chemistry /
high_school_mathematics) approximate GPQA's STEM character.

## Phase 1.0 smoke (TODAY 2026-05-26, custom evaluator)

To validate pipeline before EVO online, ran custom GPQA-stand-in (MMLU mixed
200 questions, zero-shot loglikelihood, no few-shot, no chain-of-thought) on
Mac MPS via venv. **Smoke results** at
`90-docs/baien/bench-snapshot-260526-bitnet2b-gpqa-diamond.jsonl`:

| Run | Task | n_q | Accuracy | Δ vs random 25% |
|---|---|---|---|---|
| smoke-1 | MMLU high_school_physics 30 q 0-shot loglikelihood | 30 | 33.3% | +8.3pp |
| smoke-2 | MMLU mixed (`all`) 200 q 0-shot loglikelihood | 200 | 19.5% | **-5.5pp** (below random) |

**Honest interpretation**:
- Microsoft model card for `microsoft/bitnet-b1.58-2B-4T-bf16` reports MMLU
  **52% (5-shot)** — proper few-shot scoring significantly improves
- My 0-shot custom evaluator gives **19.5% on mixed MMLU**, well below the
  52% 5-shot reference + below 25% random baseline
- Likely causes: (i) zero-shot vs 5-shot gap for small model (5-shot helps a lot),
  (ii) position bias in single-letter scoring, (iii) suboptimal prompt template
- **Conclusion**: smoke validates the *pipeline* (model load + dataset load +
  scoring function + JSONL emit), but **proper Phase 1 numbers require lm-eval-harness**
  with standard prompt templates + 5-shot context

## Phase 2 — Generative math (target: R2+ on RunPod)

| Bench | Items | Eval mode | Wall (RunPod RTX 5090 BF16) |
|---|---|---|---|
| HMMT Feb25 | ~100 | greedy + extract answer | ~30 min |
| HMMT Nov25 | ~100 | greedy + extract answer | ~30 min |
| HMMT Feb26 | ~100 | greedy + extract answer | ~30 min |
| AIME26 | 30 | greedy + extract answer | ~10 min |
| IMOAnswerBench | ~50 | greedy + extract answer | ~15 min |

**Phase 2 total on RTX 5090: ~2h, ~$1.40 ($0.69/h × 2h)**
**Phase 2 total on B200: ~12 min, ~$1.40 ($7/h × 0.2h)** — wall+cost equivalent.

## Phase 3 — Exec-graded coding (target: R2+ on RunPod)

| Bench | Items | Eval mode | Wall (RTX 5090) |
|---|---|---|---|
| LiveCodeBench v6 | ~500 | generate + sandbox exec | ~3-5h |
| HumanEval+ (existing, ADR-2605262100) | 164 | generate + sandbox exec | ~30 min |
| MBPP+ (existing, R2 deferred) | 974 | generate + sandbox exec | ~2h |
| langgraph-coding (existing, ADR-2605250400 §1.5) | 50 | exec | ~10 min |

**Phase 3 RTX 5090: ~6h, ~$4.15**

## Phase 4 — Agentic coding (R3 ADR scope)

| Bench | Items | Harness | Estimated wall (B200, agentic) |
|---|---|---|---|
| SWE-bench Verified | 500 | SWE-agent + docker per task | ~25h, ~$175 |
| SWE-bench Multilingual | 300 | SWE-agent multi-lang | ~18h, ~$130 |
| SWE-bench Pro | 240 | SWE-agent + pro spec | ~14h, ~$100 |
| Terminal-Bench 2.0 | 80 | terminal-bench-agent | ~10h, ~$70 |

**Phase 4 total: ~67h, ~$475 (excluding harness engineering ~weeks)**

Engineering blockers:
- SWE-agent installation + 1-shot test (~2-3 days)
- Docker-per-task isolation infra (Murakumo cell or RunPod-side)
- Per-task budget cap + early-termination logic

## Phase 5 — Agentic general (R3+ ADR scope, mostly deferred)

| Bench | Public eval? | Harness | Status |
|---|---|---|---|
| TAU3-Bench | TAU v2 public, v3 unclear | TAU agent | Defer |
| VITA-Bench | unclear | unclear | Defer |
| DeepPlanning | unclear | unclear | Defer |
| Tool Decathlon | unclear | likely custom | Defer |
| MCPMark | new | MCP harness needed | Defer |
| MCP-Atlas | new | MCP harness needed | Defer |
| WideSearch | new | search harness needed | Defer |

Most Phase 5 benches lack documented public eval harnesses. Defer to R3+
unless specific benches become priority via Council direction.

## RTX 5090 vs B200 cost matrix (for bench + train both)

| GPU | BF16 sustained | RunPod ~$/h | R2 train wall | R2 cost | R4 train wall | R4 cost | Best for |
|---|---|---|---|---|---|---|---|
| **RTX 5090** (32GB GDDR7, consumer Blackwell, NO NVLink) | ~100 TFLOPS | $0.69-1.99 | 6.8h | $4.70 | 102h | $70 | dev iteration, parallel hparam sweep, cheap eval |
| **B200 SXM** (192GB HBM3e, NVLink 1.8 TB/s) | ~2,800 TFLOPS | $5-9 | 15 min | $1.75 | 3.6h | $25 | main R2/R3/R4 runs (cost+wall both win) |
| **H100 SXM** (fallback) | ~1,200 TFLOPS | $2.50-4 | 34 min | $2.30 | 8.5h | $34 | B200 unavailable |

Recommendation:
- **Main R2/R3/R4 train runs → B200** (winner on both axes)
- **Hparam sweeps (10× parallel) → RTX 5090** (cheap, total $ ~$50 for 10 R2 runs)
- **Phase 1-3 benches → EVO ROCm (free) or RTX 5090 ($0.69/h)** if EVO busy

## Reproducibility envelope (per bench run, G15)

All bench runs MUST emit:
- torch.version + cuda/rocm version
- gpu_name + gpu_count
- env_hash (sha256 of env state)
- model_id + model_revision (HF resolvedSha)
- dataset CIDs (per Phase 1 dataset, register via e7m-dataset add to
  90-docs/baien/datasets.jsonl with W6+ wave)
- prompt template hash
- few-shot config (n-shot, exemplar source)
- bench seed

Output schema = `etzhayyim.baien.bench.v1` (see bench_gpqa_diamond.py).

## Execution timeline

| Phase | Window | Target |
|---|---|---|
| Phase 1.0 (smoke) | 2026-05-26 today | ✅ Custom evaluator validates pipeline (BitNet 2B + MMLU 200q + JSONL emit) |
| Phase 1 (academic, 5 benches) | 2026-05-27 (EVO online) | lm-eval-harness on EVO ROCm, ~3.5h wall, ~5 result JSONLs |
| Phase 2 (generative math) | post-amendment ~2026-07-19 | RunPod RTX 5090 ~$1.40 |
| Phase 3 (exec coding) | post-amendment ~2026-07-19 | RunPod RTX 5090 ~$4.15 |
| Phase 4 (agentic coding) | R3 ADR | SWE-agent integration + ~$475 B200 |
| Phase 5 (agentic general) | R3+ deferred | Council-direction triggered |

## Frontier-comparison expectation (set expectations honest)

Reference column scores (Qwen3.5-27B / Gemma4-31B / Qwen3.5-35BA3B /
Gemma4-26BA4B / Qwen3.6-35BA3B) range 50-90% on most benches. BitNet 2B is
~10× smaller. Expected baseline:

| Bench | Reference column range | BitNet 2B expected baseline | moemoekyun R3 target |
|---|---|---|---|
| MMLU-Pro | 82-86% | ~25-30% (per MS card 52% 5-shot → -ish for MMLU-Pro) | +5pp from baseline |
| GPQA | 82-86% | ~25-30% | +3pp |
| LiveCodeBench v6 | 75-81% | ~10-15% (BitNet not coding-trained) | +10pp from corpus exposure |
| HumanEval+ | (not in table) | ~30-35% (MS card) | +5pp (R1.5 commit gate) |
| SWE-bench | 17-75% | ~0% (no agentic capability) | +5pp via R3 agentic train |
| HMMT | 87-92% | ~5-10% (math weakness) | +5pp via reasoning-distill |

**Frontier-non-goal per ADR-2605241900** — moemoekyun positioning is "fleet-internal LLM that gets noticeably better than base BitNet on the workloads we care about", not "frontier parity".

## Next operator actions

1. **EVO power-on** → install `lm-eval-harness` in EVO Python env → execute Phase 1
2. Result commit format: 1 JSONL line per (bench, model, run) appended to
   `90-docs/baien/bench-snapshot-{date}-bitnet2b.jsonl` + `bench-snapshot-{date}-moemoekyun-r1.4-iter01.jsonl`
3. Baseline established → R1.4 train delta evaluation per ADR-2605262100 §5.4
4. Identify weak categories → R2 corpus rebalance (e.g., if HMMT score very low → boost reasoning-distill from 10% → 20%)
