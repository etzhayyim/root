# baien-mx-train

baien **Move 1** image graft self-training: frozen SigLIP image
encoder + 1.58-bit projector (trainable) + frozen baien BitNet trunk.

Authoritative ADR:
[`90-docs/adr/2605232500-baien-mx-move1-image-graft-self-training.md`](../../90-docs/adr/2605232500-baien-mx-move1-image-graft-self-training.md).

Move 2 / 3 (cross-modal fusion block, per-modality branches) follow
ADR-2605101000 once Move 1 hits its gate.

## Trainable parameter footprint

```
BitLinear(768, 2560)    = 1,966,080
BitLinear(2560, 2560)   = 6,553,600
biases                  =     5,120
─────────────────────────────────────
total                   ≈ 8,524,800   (= 0.42% of the 2 B trunk)
```

## Phases

| Phase | n_samples | epochs | wall (EVO-X2 ROCm) | purpose |
|---|---|---|---|---|
| A | 100 | 1 | ~80 s | smoke / wiring validation |
| B | 1 000 | 3 | ~40 min | bootstrap quality checkpoint |
| C | 10 000 | 3 | ~6.7 h | overnight production checkpoint |
| D | 50 000 | 3 | ~33 h | (deferred) scale-up |

## Quickstart

```bash
cd 70-tools/baien-mx-train
uv venv --python 3.10 .venv
. .venv/bin/activate
pip install -e .

# 1. Make sure baien-graft has produced at least 100 samples first:
#    bgp-submit --generator pixal3d --images chair.png,horse.png,...
#    (per 70-tools/baien-graft-pipeline/README.md)

# 2. Dry-run the trainer (validates wiring, no model loads, no GPU usage):
python -m baien_mx_train \
    --graft-data-dir ~/baien-graft/batch-001 \
    --phase A --dry-run

# 3. Phase A smoke (~80 s on EVO-X2 ROCm, real training):
#    (NB: real training path is gated behind --dry-run=False until the
#    SFT loop hookup in train.py lands per ADR Acceptance criterion #3)
python -m baien_mx_train \
    --graft-data-dir ~/baien-graft/batch-001 \
    --phase A

# 4. Via the etzhayyim CLI (uses ROCm python_embeded by default):
e7m bench mx-train --phase A
e7m bench mx-train --phase A --dry-run
```

## Status

Skeleton ships:
- ✅ `state.py` (Move1Config + Move1State + PHASE_DEFAULTS)
- ✅ `projector.py` (BitLinear 2-layer, average-pool downsample to 16 tokens)
- ✅ `adapters/graft_dataset.py` (baien-graft sample.json reader)
- ✅ `train.py` (dry-run path complete; real SFT loop is TODO at L150)
- ✅ `__main__.py` (CLI)
- ⏳ Real SFT loop (image embed → projector → trunk substitution hook)
- ⏳ `eval.py` (visual_microbench + text microbench regression check)
- ⏳ `commit.py` (sibling of baien-distill's commit_node, writes
   `90-docs/baien/multimodal-models.jsonl`)
- ⏳ `e7m bench mx-train` subcommand wiring (~30 LoC in bench.go)

The skeleton's purpose is to make the ADR Acceptance criterion #1
satisfied: the trainer setup is a python file that runs and walks
the configured phase without exploding.

## License

Apache 2.0 + etzhayyim Charter Compliance Rider v2.0.

Move 1 published weights inherit:
- **`google/siglip-base-patch16-224`** = Apache-2.0 (clean)
- **`microsoft/bitnet-b1.58-2B-4T-bf16`** = MIT (clean)
- **baien-graft data** = depends on generator (Hunyuan-Community for
   Hunyuan3D-2 backend / per-card for Pixal3D-T) — Charter Rider §2
   review at publish time per ADR-2605232500 §License pollution.
