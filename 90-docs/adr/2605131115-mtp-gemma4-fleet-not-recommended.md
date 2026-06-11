---
id: adr-2605131115-mtp-gemma4-fleet-not-recommended
title: "MTP (Gemma 4) Speculative Decoding: Not Adopted for Murakumo Fleet at Batch=1"
status: active
doc_type: adr
topic: murakumo-llm-inference
authoritative: true
last_verified: 2026-05-13
authoritative_for:
  - "decision: MTP rollout to murakumo Mac mini fleet"
related:
  - adr-2605010000
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605121700-murakumo-virtual-kubelet
supersedes: []
superseded_by: []
---

# Context

Google announced [Multi-Token Prediction (MTP) for Gemma 4](https://blog.google/innovation-and-ai/technology/developers-tools/multi-token-prediction-gemma-4/) — a native speculative-decoding head with a small bf16 drafter (78.8M, 4 layers) consuming the target model's last-layer hidden state plus per-layer-type shared K/V. Google reports **~2.2× throughput on Apple Silicon at batch 4–8**.

The murakumo Mac mini fleet (11 × M4 16 GB) is an L8 Somatic Inference tier per ADR-2605080000 (RunPod 6000 Ada is the primary inference SSoT per ADR-2605010000). Question raised: should we adopt MTP on the fleet to claw back the gap?

# Decision

**Do not roll MTP out to the murakumo fleet for current batch=1 4-bit inference.**

Single-node PoC on jacob (M4 16 GB) with the OptiQ-4bit target + bf16 MTP drafter pair shows:

| Config | mean tok/s | speedup | acc/round |
|---|---:|---:|---:|
| baseline (no drafter) | 20.85 | 1.00× | — |
| **mtp_b3** (best) | **23.05** | **1.11×** | 0.34 |
| mtp_b4 | 20.14 | 0.97× | 0.42 |
| mtp_b6 | 15.42 | 0.74× | 0.50 |
| mtp_b8 | 12.34 | 0.59× | 0.52 |

(5 prompts × 5 configs, T=0, MAX_TOKENS=128, mlx-vlm 0.5.0; raw at `_working/murakumo/2605131-mtp-gemma4-e4b-jacob-bench.md`.)

Best case is 1.11× — well below Google's claim — and larger block sizes monotonically *hurt* throughput because acceptance saturates at ~0.5–0.8 tokens/round while every rejected draft costs a full target verification. ~160 MB of additional resident memory + the operational complexity of shipping a second model through Ansible isn't worth a 2 tok/s win on a tier that is already secondary to RunPod.

# Consequences

- **No mlx-vlm upgrade for serve_plain.py.** Fleet stays on current mlx-lm path.
- **No new Ansible role for the drafter checkpoint.** No model cache changes on jacob/dan/simeon/etc.
- **Bench harness retained** at `/tmp/mtp-bench/bench.py` (jacob local) for future re-evaluation; not committed to the repo because it depends on a non-production venv (`/tmp/mtp-bench/.venv`, mlx-vlm 0.5.0). If we ever re-evaluate, recreate the venv from scratch.
- **No SSoT change.** Inference SSoT remains RunPod 6000 Ada per ADR-2605010000.

# Alternatives Considered

The bench did not test the regimes where MTP is most likely to pay off:

1. **bf16 target × batch 4–8** on a Mac mini via `mlx-vlm` server mode — Google's actual measurement regime. Skipped because the bf16 target is ~10 GB and would tip 16 GB jacob into swap; would need to test on a 32+ GB host.
2. **4-bit target × 4-bit drafter** if/when a matched-quantization drafter is published — closer logit alignment may lift acceptance enough to flip b=4 positive.
3. **Server-side draft batching across concurrent streams** — mlx-vlm 0.5.0 doesn't support this.

None of (1)–(3) are committed work. Listed only so future re-evaluation doesn't repeat this PoC's setup.

# References

- Bench result: `_working/murakumo/2605131-mtp-gemma4-e4b-jacob-bench.md`
- Bench harness (jacob local, not in repo): `/tmp/mtp-bench/bench.py`
- ADR-2605010000 — RunPod 6000 Ada inference SSoT
- ADR-2605080000 — Distributed Cognitive Actor System (L8 Somatic tier)
- ADR-2605121700 — Murakumo Virtual Kubelet
- <https://blog.google/innovation-and-ai/technology/developers-tools/multi-token-prediction-gemma-4/>
