---
id: runbook-baien-moemoekyun-r1-bringup
title: "Operator runbook — baien-moemoekyun R1 (Phase 0 freeze-train) on EVO-X2 Windows ROCm"
status: active
doc_type: how-to
topic: baien-moemoekyun-r1-bringup
authoritative: true
last_verified: 2026-05-26
related:
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
  - adr-2605261900-baien-moemoekyun-moe-charter
  - 70-tools/baien-moemoekyun-train/scripts/probe_rocm_moe.py
  - 70-tools/baien-moemoekyun-train/configs/r1.4-iter01.yaml
---

# Runbook — baien-moemoekyun R1 (Phase 0) on EVO-X2

## Charter status

**R1 is charter-clean and executable today**. No amendment dependency:
- Train host = EVO-X2 (Murakumo fleet member per ADR-2605202345)
- Train compute = AMD Radeon 8060S iGPU (gfx1151, ROCm 7.2.1)
- Charter Rider §2(i) Murakumo-only invariant fully respected

(R2+ RunPod is gated on ADR-2605262200 amendment — see [`baien-moemoekyun-runpod-bringup.md`](baien-moemoekyun-runpod-bringup.md))

## Sub-phase ladder (R1.0 → R1.5 per ADR-2605262100 §7)

| Sub-phase | What | Acceptance |
|---|---|---|
| R1.0 | ROCm probe + matmul throughput grounding | finite output + no OOM + RAM ≤30GB + G5 α init ±1e-3 |
| R1.1 | Module surgery + α=0 step-0 verify | `pytest tests/test_alpha_init.py tests/test_step0_match.py` all PASS |
| R1.2 | aux-loss (G6) + frozen grad verify (G8) | `pytest tests/test_frozen_grad.py` all PASS |
| R1.3 | 100-sample × 10-step smoke (Magicoder) | no NaN/Inf + loss decrease + expert utilization > 1/E × 0.1 |
| R1.4 | 5,000 ex × 1 epoch (Magicoder + reasoning + commitpack + harvest + CodeAlpaca) | wall ≤6h (revised from ≤3h, see below) + final loss < initial × 0.85 + aux loss mean < 0.05 |
| R1.5 | langgraph-coding + HumanEval+ Δ gate | Δ_lg ≥ +3pp AND Δ_he+ ≥ 0 → commit; else abort + R2 escalation |

## Wall budget revision (informed by 2026-05-26 probe)

ADR-2605262100 §7 originally specified R1.4 wall ≤3h. Throughput probe of `90-docs/baien/bit-packed-xnor-kernels-260524/pytorch-rocm-evo-reference.json` shows **~9.5 TFLOPS BF16 measured** on B=256/K=4096/N=4096 matmul (~16% of theoretical 59 TFLOPS peak). Train-loop sustained ≈ 5-7 TFLOPS → R1.4 5K ex × 1 ep estimate **~5-7h wall**, not 3h.

**Recommended amendment to ADR-2605262100 §7 R1.4 acceptance**: wall ≤8h. To be propagated via in-line edit + commit (not separate ADR — non-constitutional iteration). R1.0 probe (this runbook step 2) will produce actual ground truth.

## Step 0: Operator prerequisites (T-1 day, EVO-X2)

- [ ] Windows 11 + ROCm 7.2.1 + Python 3.12 + torch 2.9.1+rocm7.2.1 installed (per ADR-2605250400 §1.2 confirmed working)
- [ ] Clone `etzhayyim/root` repo: `git clone https://github.com/etzhayyim/root C:\Users\gad\etzhayyim-root`
- [ ] Hugging Face token configured (`huggingface-cli login`)
- [ ] Disk space ≥ 50 GB free on `C:\Users\gad\` (BitNet 2B ~4GB + corpus ~1GB + checkpoints + eval outputs)
- [ ] Network access to `https://huggingface.co` (model + datasets download)
- [ ] Network access to mac-260317 LAN (192.168.1.x) for checkpoint push

## Step 1: Install (T-0, EVO-X2)

```pwsh
cd C:\Users\gad\etzhayyim-root\70-tools\baien-moemoekyun-train
pip install -e ".[dev]"

# Verify torch + ROCm
python -c "import torch; print(f'torch={torch.__version__} hip={torch.version.hip} cuda_avail={torch.cuda.is_available()}')"
# Expected: torch=2.9.1+rocm7.2.1 hip=7.2.53211-158bd99533 cuda_avail=True
```

## Step 2: R1.0 ROCm probe (EVO-X2)

```pwsh
# Fast skip BitNet load for matmul-only throughput
python scripts/probe_rocm_moe.py --skip-bitnet-load --output-json probe_r1.0_matmul.json

# Full probe with BitNet load + MoE forward
python scripts/probe_rocm_moe.py --output-json probe_r1.0_full.json
```

Expected output (full probe):
```
[stage 1] matmul throughput grounding...
  B=   8 K= 2048 N= 2048 -> X.XX TFLOPS BF16
  B= 256 K= 4096 N= 4096 -> ~9.5 TFLOPS BF16
[stage 2] loading microsoft/bitnet-b1.58-2B-4T-bf16...
  loaded in 15-30s
  config: hidden=2048, intermediate=5504, n_layers=30
  installing MoE on layers: [29]
  param summary: {'trainable': ~15M, 'frozen': ~2.0B, 'moe_wrappers': 1}
  forward 0.X s, logits shape=(1, 256, vocab), finite=True
  G5 alpha init check: [...] (all within ±1e-3: True)

[acceptance R1.0]
  finite_output: True
  no_oom:        True
  ram_under_30gb: True (peak 8.X GB for 1-layer probe)
  G5 alpha init: True

  4/4 R1.0 acceptance criteria PASS
```

Copy `probe_r1.0_full.json` back to `mac-260317` via rsync/scp/SMB to commit:
```sh
# On mac-260317:
scp gad@192.168.1.70:C:/Users/gad/etzhayyim-root/70-tools/baien-moemoekyun-train/probe_r1.0_full.json \
    /Users/junkawasaki/github/etzhayyim-root/90-docs/baien/r1.0-probe-260526.json
```

## Step 3: R1.1 + R1.2 module + verify tests (EVO-X2)

```pwsh
pytest tests/ -v

# Expected:
#   tests/test_alpha_init.py::test_alpha_init_within_jitter PASSED
#   tests/test_alpha_init.py::test_alpha_is_trainable PASSED
#   tests/test_alpha_init.py::test_alpha_init_repeated_within_jitter PASSED
#   tests/test_alpha_init.py::test_alpha_dtype_fp32 PASSED
#   tests/test_step0_match.py::test_step0_forward_match_within_1pct[42] PASSED
#   tests/test_step0_match.py::test_step0_forward_match_within_1pct[123] PASSED
#   tests/test_step0_match.py::test_step0_forward_match_within_1pct[2026] PASSED
#   tests/test_step0_match.py::test_alpha_zero_means_exact_match PASSED
#   tests/test_frozen_grad.py::test_freeze_backbone_grad_norm_zero PASSED
#   tests/test_frozen_grad.py::test_param_count_summary_consistent PASSED
```

## Step 4: R1.3 smoke (EVO-X2, 100 ex × 10 steps)

```pwsh
# Override config for smoke
python -m baien_moemoekyun.train --config configs/r1.4-iter01.yaml \
    --override corpus.total_examples=100 training.num_train_epochs=0.1

# Expected: ~5-10 min wall, no NaN/Inf
# (Note: R1.0 scaffold's train.py has TODO for SFTTrainer subclass with aux_loss + per-group LR;
#  current scaffold may run but won't have full G6 compliance. Full impl deliverable: R1.1.)
```

Inspect `90-docs/baien/moemoekyun-r1.4-eval.jsonl` (appended); verify reproducibility envelope present (G15).

## Step 5: R1.4 main train (EVO-X2, 5,000 ex × 1 epoch)

```pwsh
# Background process so SSH session can disconnect
nohup python -m baien_moemoekyun.train --config configs/r1.4-iter01.yaml \
    > C:\Users\gad\baien-moemoekyun-train\logs\r1.4-iter01.log 2>&1 &
echo $!  # capture PID

# Or run with screen / Windows Task Scheduler for unattended execution
```

Monitor:
```pwsh
# Tail log
Get-Content C:\Users\gad\baien-moemoekyun-train\logs\r1.4-iter01.log -Wait

# Memory + GPU watch
while ($true) { Get-Process python | Format-Table Id, WorkingSet, PrivateMemorySize; Start-Sleep -Seconds 60 }
```

Expected wall: ~5-7h. Checkpoints at `${output_dir}/checkpoint-{step}/` every 100 steps.

## Step 6: R1.5 eval-gated commit (mac-260317 + Mac mini fleet)

```sh
# On mac-260317
# 1. Pull final checkpoint from EVO-X2
rsync -av gad@192.168.1.70:C:/Volumes/...etzhayyim/checkpoints/moemoekyun-r1.4-iter01/ \
    /Volumes/260317/etzhayyim/checkpoints/moemoekyun-r1.4-iter01/

# 2. IPFS pin + verify
export ETZ_DATASET_ROOT=/Volumes/260317/etzhayyim
e7m-dataset add local:///Volumes/260317/etzhayyim/checkpoints/moemoekyun-r1.4-iter01 \
    --name "moemoekyun-r1.4-iter01" --kind model-checkpoint
e7m-dataset verify moemoekyun-r1.4-iter01

# 3. Run baseline + post-train eval on Mac mini fleet (split-role per ADR-2605262100 §3.3)
# (R2.0 deliverable: launchd cells for naphtali bench-langgraph + simeon bench-humanevalplus)
# Manual fallback until cells land:
ssh naphtali bash -lc "cd ~/baien-eval && python langgraph-coding-bench.py --model moemoekyun-r1.4-iter01 --output ~/results-r1.4.json"
ssh simeon   bash -lc "cd ~/baien-eval && python humanevalplus-bench.py --model moemoekyun-r1.4-iter01 --output ~/results-r1.4.json"

# 4. commit_node gate (ADR-2605262100 §5.4)
python 70-tools/baien-moemoekyun-train/scripts/commit-gate.py \
    --baseline 90-docs/baien/baseline-pre-r1.4.json \
    --post-train 90-docs/baien/results-r1.4.json
# Output: "committed-to-registry" or "aborted-{reason}"
```

## Step 7: Commit results to repo (mac-260317)

```sh
cd /Users/junkawasaki/github/etzhayyim-root
git add 90-docs/baien/moemoekyun-r1.4-corpus-manifest.jsonl  # G14
git add 90-docs/baien/moemoekyun-r1.4-eval.jsonl
git add 90-docs/baien/moemoekyun-models.jsonl                # if committed
git add 90-docs/baien/r1.0-probe-260526.json                 # if not yet committed
git commit -m "feat(baien-moemoekyun): R1.4 iter-01 results + R1.0 probe evidence"
```

## Failure recovery

| Failure | Phase | Recovery |
|---|---|---|
| `probe_rocm_moe.py` BitNet load fails (HF auth / cache miss) | R1.0 | Re-run after `huggingface-cli login`; verify network |
| pytest tests/ FAIL (G5/G8) | R1.1/R1.2 | Inspect failed assert; likely numerical issue in module surgery — review `attach.py` |
| R1.3 smoke NaN/Inf | R1.3 | Reduce LR (router 1e-4 → 5e-5; experts 2e-4 → 1e-4); check aux_loss not exploding |
| R1.3 expert utilization collapse (some experts get <1/E × 0.1) | R1.3 | Increase aux_loss_weight 0.01 → 0.05 (G6 acceptable range [0.001, 0.1]) |
| R1.4 ROCm OOM | R1.4 | Reduce moe_layers from "last_25_percent" (7-8 layers) to "last_3_layers" (3 layers); reduces trainable params 1.1B → 470M |
| R1.4 α 発散 (>10) | R1.4 | Add gradient clipping max=5.0; reduce LR_alpha 5e-5 → 1e-5 |
| R1.5 langgraph-coding Δ < +3pp | R1.5 | Inspect per-prompt failures; if pattern (e.g., StateGraph syntax), escalate to R2 ADR with corpus rebalance |
| R1.5 HumanEval+ regression (Δ < 0) | R1.5 | **MANDATORY abort** per G10 honest scoring; do NOT publish; escalate to R2 hyperparameter sweep |

## Next steps after R1.5 success

1. Append entry to `90-docs/baien/moemoekyun-models.jsonl`
2. Push `moemoekyun-r1.4-iter01` to LiteLLM gateway (judah) — model id `moemoekyun-r1.4-iter01` (NOT yet `baien-server-` prefixed; that's R3 publish status only)
3. Smoke inference via judah on 5-10 langgraph prompts manually to sanity-check
4. Plan R2 (post amendment effective 2026-07-19) — see [`baien-moemoekyun-runpod-bringup.md`](baien-moemoekyun-runpod-bringup.md)
