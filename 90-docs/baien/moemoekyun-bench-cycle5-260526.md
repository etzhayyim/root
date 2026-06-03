---
id: moemoekyun-bench-cycle5-260526
title: "moemoekyun bench cycle 5 (2026-05-26 15:55 JST) — W13-W17 dataset expansion + 5090 SSH key authorization pending"
status: active
doc_type: reference
topic: moemoekyun-bench-cycle5
authoritative: true
last_verified: 2026-05-26
related:
  - 90-docs/baien/moemoekyun-bench-cycle{1,2,3,4}-260526.md
  - adr-2605263000-founder-lv7-emergency-authorization-runpod-5090-bench-interim
---

# moemoekyun bench cycle 5 — 2026-05-26 15:55 JST

**/loop fire 5** (cron `13,43 * * * *`, job `c8acb432`).

## State at cycle 5 entry

- EVO-X2: still offline (operator power-on pending since cycle 1)
- RunPod 5090: provisioned + SSH active (per user setup), but mac-260317
  SSH key NOT yet authorized on pod → mac cannot drive bench remotely
- Founder Emergency Authorization (ADR-2605263000): committed `e2dc3fab5`
- Bench-results from 5090: not yet returned (bringup script /tmp/runpod-5090-bench-bringup.sh
  pending user execution in pod SSH session)

## Cycle 5 productive deliverables (no GPU dependency)

### A. Bench dataset substrate expansion (W13-W17)

5 new datasets pinned to IPFS+DataLad. Total Phase 1/2/3 coverage:

| Wave | Dataset | Phase | Size | License |
|---|---|---|---|---|
| W13 | `evalplus/mbppplus` | 3 (coding) | 1.13 MB | Apache 2.0 |
| W14 | `openai/gsm8k` | 2 (math) | 5.90 MB | MIT |
| W15 | `lighteval/MATH-Hard` | 2 (advanced math) | 4.60 MB | MIT |
| W16 | `HuggingFaceH4/MATH-500` | 2 (math benchmark distillation) | 0.45 MB | MIT |
| W17 | `allenai/ai2_arc` (ARC-Challenge) | 1 (academic, lm-eval canonical) | 1.22 MB | CC-BY-SA-4.0 |

Cumulative substrate now spans:
- **Train (5 datasets, 354.8 MB)**: Magicoder + commitpackft@python + reasoning-distill + LangGraph harvest + CodeAlpaca-20k
- **Phase 1 academic (5 datasets, 12.7 MB)**: MMLU-Redux 2.0 + MMLU-Pro + SuperGPQA + ARC-Challenge + (smoke fixtures)
- **Phase 2 math (5 datasets, 11.2 MB)**: AIME26 + HMMT Feb 2025 + GSM8K + MATH-Hard + MATH-500
- **Phase 3 coding (3 datasets, 149.8 MB)**: HumanEval+ + MBPP+ + LiveCodeBench v6 (test6.jsonl)

**Total: 18 datasets, ~528 MB** pinned to mac-260317 Kubo IPFS + DataLad superdataset.

W15 hendrycks/competition_math failed (401 — gated despite no explicit gating UI);
substituted with `lighteval/MATH-Hard` (Apache 2.0 mirror of similar content).

### B. RunPod 5090 SSH key authorization runbook

mac-260317 SSH keys (id_ed25519, id_ed25519_github_etzhayyim, id_ed25519_performer)
not authorized on pod 157.157.221.30:51691. User one-liner to fix
(in user's existing pod SSH terminal):

```sh
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOvzaMbhK0JiiSNj5gkaY6Hi7Hz7P587IJaohN6YqQlK' >> ~/.ssh/authorized_keys
```

Once added, mac-260317 can SSH directly + drive bench scripts:

```sh
# Test
ssh -p 51691 root@157.157.221.30 nvidia-smi
# Push bringup
scp -P 51691 /tmp/runpod-5090-bench-bringup.sh root@157.157.221.30:/workspace/bringup.sh
# Run
ssh -p 51691 root@157.157.221.30 'HF_TOKEN=hf_... bash /workspace/bringup.sh'
```

## Cycle 5 score lift attribution

| Source | Lift |
|---|---|
| Substrate expansion (W13-W17) | 0 score, +infrastructure for cycle 6+ benches (5 more bench categories ready) |
| 5090 actual run | pending user SSH key authorization or user-driven execution |

## Cycle 6 plan (~16:13 JST fire)

Two scenarios:

### Scenario A — User authorized SSH key
1. mac → 5090 SSH test
2. scp bringup script to /workspace
3. Execute (HF_TOKEN via env)
4. lm-eval-harness Phase 1 5-shot canonical numbers (MMLU-Redux + ARC + GPQA)
5. evalplus HumanEval+ proper chat template (cycle 3-4 blocker fix)
6. Pack + retrieve + commit

### Scenario B — Still pending
1. Add 2-3 more datasets (BBH / Open-Orca / etc.)
2. Cycles 1-5 synthesis doc consolidating BitNet 2B baseline findings
3. R1.4 corpus rebalance proposal based on per-subject weaknesses observed:
   - **math**: 29-30% (HS + college) — boost reasoning-distill 10% → 20%
   - **biology**: 54% (MMLU-Redux) / 52% (MMLU-Pro 10-opt) — already strong
   - **HumanEval+**: 0% (harness bug, not real) — defer to real eval
4. EVO online check
