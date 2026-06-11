---
id: moemoekyun-bench-cycle6-260526
title: "moemoekyun bench cycle 6 (2026-05-26 16:20+ JST) — RunPod RTX 5090 SSH established + Phase 1 lm-eval 5-shot canonical running"
status: active
doc_type: reference
topic: moemoekyun-bench-cycle6
authoritative: true
last_verified: 2026-05-26
related:
  - 90-docs/baien/moemoekyun-bench-cycle{1,2,3,4,5}-260526.md
  - adr-2605263000-founder-lv7-emergency-authorization-runpod-5090-bench-interim
  - runpod-5090-access-status-260526
  - 90-docs/baien/runpod-5090-runlog-260526.jsonl
---

# moemoekyun bench cycle 6 — 2026-05-26 16:20+ JST

**/loop fire 6** (cron `13,43 * * * *`, job `c8acb432`).

## State change: 5090 SSH unblocked

User added `private_key` field to 1Password vault item
`runpod/oka-lm-train RTX5090` (etzhayyimcojp/`scclefhmwawwpf6pljf4gf3ibq`).
mac-260317 retrieved via:
```sh
op item get scclefhmwawwpf6pljf4gf3ibq --format=json --reveal | \
  python3 -c "import json,sys; d=json.load(sys.stdin); ..." \
  > ~/.ssh/runpod-oka-lm-train
chmod 600 ~/.ssh/runpod-oka-lm-train
# ssh config Host runpod-oka-lm-train entry added
```

**Quirks encountered:**
1. `op item get --fields private_key --reveal` wrapped value in JSON quotes →
   used `--format=json` + python json.load to extract raw multi-line value
2. Trailing newline missing → `echo "" >> ~/.ssh/runpod-oka-lm-train`
3. After fix: `ssh runpod-oka-lm-train 'echo OK'` → CONNECTED ✓

## RTX 5090 pod environment

| Item | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 5090 |
| VRAM | 32607 MiB (32 GB GDDR7) |
| Driver | 580.126.09 |
| Python | 3.11.10 |
| torch | 2.12.0.dev20260408+cu128 (dev build for Blackwell) |
| transformers | 5.9.0 → downgraded to 4.57.6 (BitNet + lm-eval compat) |
| datasets | downgraded 4.x → 3.6.0 (trust_remote_code support for hails/mmlu_no_train) |

## BitNet 2B inference on 5090

After torchvision uninstall (was 0.19.1+cu124 ABI-mismatched with cu128 torch):

```
torch=2.12.0.dev20260408+cu128 cuda=True device=NVIDIA GeForce RTX 5090
load: 8.2s (warm cache)
gen 40 tok in 3.42s = 11.7 tok/s on RTX 5090
def fibonacci(n):
     if n == 0:
         return 0
     elif n == 1:
         return 1
     ...
```

→ **11.7 tok/s** (Mac MPS baseline 3-4 tok/s, **3-4× speedup**). Output bit-identical
to Mac MPS smoke (G5 invariant verified across runtime change).

## Phase 1 lm-eval-harness 5-shot run (in progress)

```
lm_eval --model hf \
    --model_args pretrained=microsoft/bitnet-b1.58-2B-4T-bf16,dtype=bfloat16,device=cuda \
    --tasks mmlu_stem,arc_challenge \
    --num_fewshot 5 \
    --batch_size 8 \
    --output_path /workspace/baien-bench/results/phase1-5shot \
    --log_samples --seed 42
```

**Tasks excluded from this run**:
- `gpqa` / `leaderboard_gpqa` — gated dataset, user-account `com-junkawasaki` HF access denied (manual approval needed on dataset page)
- `mmlu_redux_2` — task name not in lm-eval 0.4.5 (must use just `mmlu` or `mmlu_stem`)

**Tasks running**:
- `mmlu_stem` (6 STEM subjects from MMLU default; ~3000 questions)
- `arc_challenge` (1172 test questions)

Expected wall: ~30-60 min on 5090 batch 8. Cost: ~$0.50-1.00 per ADR-2605263000 budget.

## Issues encountered during bringup (resolved)

| Issue | Root cause | Fix |
|---|---|---|
| `torchvision::nms does not exist` | torchvision 0.19.1+cu124 ABI mismatched with torch 2.12.0+cu128 | `pip uninstall torchvision` (text-only BitNet doesn't need it) |
| `BitNetForCausalLM not importable` | downstream of torchvision crash | resolved by torchvision uninstall |
| `AutoModelForVision2Seq missing` (lm-eval startup) | transformers 5.9.0 renamed/removed this; lm-eval 0.4.5 expects 4.x | `pip install transformers==4.57.6` |
| `trust_remote_code is not supported anymore` | datasets 4.8.5 removed legacy script loading | `pip install datasets<4.0,>=3.0` (resulted in 3.6.0) |
| `Feature type 'List' not found` | parquet cache from 4.x had non-3.x feature type | `rm -rf ~/.cache/huggingface/datasets ~/.cache/huggingface/hub/datasets--*` |

After all fixes: lm-eval datasets generate splits successfully and proceeds to model evaluation.

## Score lift attribution (cycle 6)

| Source | Lift |
|---|---|
| SSH unblock (5090 accessible from mac) | infra (no score yet, gates canonical bench) |
| BitNet 5090 inference 11.7 tok/s | 3-4× speedup vs Mac MPS (no score, faster iter) |
| **Phase 1 5-shot canonical bench** | **(pending completion)** — first canonical numbers since cycles 1-3 broken/limited |

## Security notes

1. **HF_TOKEN leak**: bringup.sh has `set -x` (debug trace) which logged the env
   variable `HF_TOKEN=hf_ZHuu...` to `/workspace/bringup.log` on the pod.
   **Action**: rotate HF token after bench completes (https://huggingface.co/settings/tokens)
2. **RunPod API key leak (earlier)**: `rpa_WU1RIXAS...` was exposed in chat paste.
   **Action**: rotate via RunPod console (still recommended).
3. **bringup.log NOT committed to repo** (contains token); only structured bench outputs go to repo.

## Cycle 7 plan (~16:43 JST fire)

If lm-eval completes by then:
1. scp result tarball → mac-260317 `90-docs/baien/`
2. Extract + parse phase1-5shot JSON → emit canonical 5-shot numbers entry to
   `bench-snapshot-260526-bitnet2b-gpqa-diamond.jsonl` (or new file)
3. Compare canonical 5-shot vs cycle 1-3 Mac MPS 0-shot fixed-evaluator numbers
4. Write final "BitNet 2B canonical baseline established" doc consolidating cycles 1-7

If lm-eval still running:
1. Wait + check
2. Queue HumanEval+ via evalplus (proper chat template, fixes cycle 3-4 markdown bug)
3. Continue substrate adds (BoolQ, HellaSwag, etc.)

## ADR-2605263000 compliance check (per-rental attestation)

Pre-flight runlog entry exists (`90-docs/baien/runpod-5090-runlog-260526.jsonl`).
Post-flight entry will append after lm-eval completes, with:
- actual_wall_minutes
- actual_usd_cost_millicents (RunPod billing query at end)
- output_checkpoint_cid (n/a for inference-only; substitute = result tarball IPFS pin TBD)
- ipfs_pin_verify_cid (n/a for this run; substitute = e7m-dataset register of result JSONL)
- eval_metrics (parsed from lm-eval output JSON)
- commit_decision: `bench-baseline-recorded` (new variant since this is bench-eval, not train commit)
