# maxwell mmdiffusion — multimodal image-diffusion graft (R0 scaffold)

**Status**: R0 scaffold (design + wiring only; NO trained weights, NO real inference).
**ADR**: ADR-2606061000 D6 M3 (Maxwell multimodal graft) · license: ADR-2606172300 (ECL).
**Distinct from**: ADR-2606170840 / 2606171100 `maxwell-diffusion` — that is a *text*
diffusion-LM (DiffusionGemma 26B-A4B). **This** is the *image / any-modality → image*
diffusion graft conditioned on a frozen joint-embedding encoder (ImageBind / LanguageBind).

## Architecture (BindDiffusion / CoDi pattern)

```
[any modality]                                 trainable           frozen diffusion
 text / image / audio / depth / IMU            (the only           backbone (DiT/UNet)
        │                                        learned part)            │
        ▼                                            │                     ▼
  JointEncoder ──z (joint embed, D-dim)──▶ ProjectionAdapter ──ctx──▶ DiffusionConditioner
   (FROZEN)                                  (D → L×C context)        (cross-attention)  ──▶ image
```

- **Frozen joint-encoder** — satisfies the baien edge invariant "全 modality encoder 凍結"
  (ADR-2605241900). Two adapters:
  - `ImageBindEncoder` — 6-modality, **CC-BY-NC 4.0**, `vendor/imagebind-fork/` (NOT shipped).
    Path A: internal-only, outputs CC-BY-NC, never redistributed as commons.
  - `LanguageBindEncoder` — **MIT**, commons-shippable path (ECL-on-Apache outputs).
- **ProjectionAdapter** — the ONLY trainable module; maps the joint embedding to diffusion
  cross-attention context. Trained via the baien Move pipeline on the Murakumo fleet.
- **DiffusionConditioner** — backbone-agnostic cross-attention conditioning hook.

## Charter gates (enforced in code)

| Gate | Rule | Where |
|---|---|---|
| G1 Murakumo-only | inference/train on the fleet only (Rider §2(i), ADR-2605215000) | `MURAKUMO_ONLY = True` |
| G2 Path A license boundary | ImageBind non-redistributable; outputs CC-BY-NC; internal-use only | `JointEncoder.redistributable` / `.output_license` |
| G3 no-biometric | image modality not pointed at faces/biometric id (manako pattern) | `conditioning.py` note + `assert_no_biometric` |
| G4 internal-commerce firewall | NC outputs MUST NOT feed SBT↔SBT internal economy | `assert_internal_use_only` |
| G5 honest R0 | no trained weights; real model paths raise `NotImplementedError` | every model call |

## Files

- `joint_encoder.py` — `JointEncoder` ABC + ImageBind / LanguageBind adapters (frozen, stub)
- `projection.py` — `ProjectionAdapter` (trainable; shape logic, forward stubbed)
- `conditioning.py` — `DiffusionConditioner` cross-attention hook (backbone-agnostic)
- `smoke.py` — wiring smoke: builds the pipeline with a deterministic `FakeEncoder`
  (stdlib-only, no torch/numpy) and asserts shapes + Charter invariants. **Runnable today.**
- `LICENSE-NOTE.md` — the two-layer license boundary for this directory.

## Run the smoke (no models needed)

```bash
python3 70-tools/scripts/maxwell/mmdiffusion/smoke.py
```

It proves the wiring + the Path A / Charter invariants without any model weights.
Real encoder/backbone integration is the M3.1 step (gated; weights internal).
