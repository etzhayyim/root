# baien-moemoekyun-train

Training scaffolding for **baien-moemoekyun** — a server-tier (ADR-2605242100) MoE-augmented baien variant on `microsoft/bitnet-b1.58-2B-4T-bf16`.

- **Architecture**: ADR-2605261900 (R0 charter)
- **R1 sub-charter** (current): ADR-2605262100 — Phase 0 freeze-train (router + 128 experts × 7 layers + per-layer α ≈ 1.1B trainable) on EVO-X2 Windows ROCm 7.2.1
- **R2+ sub-charter** (gated): ADR-2605262300 — RunPod B200 SXM rental architecture (gated on ADR-2605262200 amendment effective ~2026-07-19)

## Quick start (R1 — EVO-X2)

See [`90-docs/runbooks/baien-moemoekyun-r1-bringup.md`](../../90-docs/runbooks/baien-moemoekyun-r1-bringup.md) for full operator runbook.

```sh
# On EVO-X2 (192.168.1.70, Windows + ROCm 7.2.1)
cd C:\Users\gad\etzhayyim-root\70-tools\baien-moemoekyun-train

# Install
pip install -e ".[dev]"

# R1.0: ROCm probe
python scripts/probe_rocm_moe.py

# R1.1-R1.2: module + alpha=0 + aux-loss + frozen-grad verify
pytest tests/

# R1.3: 100-sample × 10-step smoke
python -m baien_moemoekyun.train --config configs/r1.3-smoke.yaml

# R1.4: 5,000 ex × 1 epoch coding-emphasis SFT
python -m baien_moemoekyun.train --config configs/r1.4-iter01.yaml
```

## Quick start (R2 — RunPod, post amendment effective)

See [`90-docs/runbooks/baien-moemoekyun-runpod-bringup.md`](../../90-docs/runbooks/baien-moemoekyun-runpod-bringup.md).

```sh
# On mac-260317 (operator)
python scripts/rental-orchestrator.py --config configs/r2-iter01.yaml --dry-run  # rehearsal
python scripts/rental-orchestrator.py --config configs/r2-iter01.yaml --live      # execute
```

## Architecture

```
y = x + Attention(x)                       # backbone, frozen
y = y + SharedDenseFFN(y)                  # existing BitNet FFN, frozen, always-on
y = y + α · Σ_{i ∈ top_k(router(y))}       # NEW: MoE residual branch
            g_i · Expert_i(y)
```

- `BaienMoEResidual` (`src/baien_moemoekyun/moe.py`): router + 128 small experts (dense_FFN/32 hidden)
- `BitNetFFNWithMoE` (`src/baien_moemoekyun/attach.py`): module-surgery wrapper that replaces selected `layer.mlp` modules

Output gate α init = 0.0 ± 1e-3 (G5 MANDATORY) → step-0 forward output bit-identical to base BitNet within `‖Δ‖_2 / ‖y_base‖_2 < 0.01`.

## Constitutional gates (full list in ADR-2605261900 §5 + ADR-2605262100 §6)

| Gate | Enforcement |
|---|---|
| G5 α=0 init | `tests/test_alpha_init.py` + `tests/test_step0_match.py` |
| G6 aux-loss MANDATORY | `tests/test_aux_loss.py` (W∈[0.001, 0.1]) |
| G8 backbone frozen | `tests/test_frozen_grad.py` (grad-norm = 0 after 1 backward) |
| G13 NC-trained artifact distribution | manual review at commit_node (Tier C dataset → fleet-internal only) |
| G14 dataset manifest | `90-docs/baien/moemoekyun-r1.4-corpus-manifest.jsonl` MANDATORY |
| G15 EVO-X2 reproducibility | env_hash embedded in bench JSON |

## License

Apache 2.0 + etzhayyim Charter Compliance Rider v2.0. See [`/CHARTER-RIDER.md`](../../CHARTER-RIDER.md).
