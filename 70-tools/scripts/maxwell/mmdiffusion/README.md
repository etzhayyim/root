# maxwell mmdiffusion — multimodal image-diffusion graft (R1: real architecture, runnable)

**Status**: **R1 — real, runnable architecture** (NumPy DiT computes end-to-end offline;
torch trainable twin; NO trained weights yet → output is noise-shaped until trained).
R0 wiring scaffold (`*.py` interfaces + `smoke.py`) is retained beneath it.
**ADR**: ADR-2606061000 D6 M3 (Maxwell multimodal graft) · license: ADR-2606172300 (ECL).

## R1 — real implementation (LanguageBind + DiT)

The R0 stubs are now backed by a faithful, runnable Diffusion Transformer:

| File | What it really is |
|---|---|
| `model.py` | **Real DiT** in NumPy: patch-embed → sinusoidal t-embed → N×[adaLN self-attn + **cross-attn to the joint-embedding context** + MLP] → adaLN final → unpatchify. Real attention/softmax/gelu/layernorm. |
| `diffusion.py` | **Real DDPM**: cosine β schedule, `q_sample` (forward noising), `p_sample_loop` (reverse sampling), eps-MSE `training_loss`. |
| `languagebind_encoder.py` | **Real LanguageBind (MIT)** adapter — frozen; imports the real lib when present, deterministic offline fallback embedding otherwise (runs without the multi-GB download). |
| `projection_np.py` | **Real** trainable ProjectionNP (D=768 → L×C MLP). |
| `pipeline.py` | Wires encoder → projection → DiT → DDPM; `generate()` runs real reverse diffusion; Charter gates (G1/G3/G4) reused from `conditioning.py`. |
| `dit_torch.py` | **Trainable torch twin** (real `nn.Module`, adaLN-zero init, real `train_step` = eps-MSE + AdamW) — the training artifact (runs when torch installed). |
| `smoke_real.py` | **Runs the real computation** — encode→project→DiT→sample; asserts shapes, finiteness, determinism, **conditioning truly flows** (output depends on context + timestep), Charter G3. 16/16. |

```bash
python3 70-tools/scripts/maxwell/mmdiffusion/smoke_real.py   # real end-to-end (numpy, 16/16)
python3 70-tools/scripts/maxwell/mmdiffusion/smoke.py        # R0 wiring (17/17)
```

**Honest status**: the *architecture* is real and computes; weights are seed-initialised
(untrained), so generated images are noise-like until trained via `dit_torch.py` on the
baien Move pipeline (Murakumo-preferred, ADR-2606172359). LanguageBind = MIT commons path
(outputs ECL-on-Apache); ImageBind stays CC-BY-NC internal (Path A).

---

## R0 scaffold (retained)

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
