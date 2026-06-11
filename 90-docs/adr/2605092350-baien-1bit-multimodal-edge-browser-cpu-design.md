---
id: adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
title: "Baien: 1-bit Multimodal LLM for Edge / Browser / CPU (BitNet b1.58 2B 4T trunk)"
status: proposed
doc_type: adr
topic: edge-multimodal-model-1bit
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - 1-bit (ternary) multimodal model family `baien`
  - Edge / browser / CPU deployment topology for the 1-bit trunk
  - Default base = `microsoft/bitnet-b1.58-2B-4T-bf16` for fine-tunes / multimodal grafts
  - Runtime target matrix: native CPU (bitnet.cpp / llama.cpp), browser (WebGPU + WASM), embedded edge (mobile / Pi-class boards)
depends_on:
  - adr-2605092345-runpod-l40s-fp8-multimodal-model-design        # Oka, sibling design (data-center FP8 trunk)
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast         # cultivar / cell metaphor
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
  - adr-2605070700-rw-native-model-training-weight-lineage        # vertex_training_* lineage shared with Oka
related:
  - 40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts
  - 40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/training_run.py
  - 30-graph/graph-schema/migrations/20260508000000_vertex_training_lineage.ts
supersedes: []
superseded_by: []
---

# Goal

Provide a **1-bit (BitNet b1.58 ternary) multimodal LLM family** that runs
**without a data-center GPU**. Targets:

1. **Native CPU pods** (Vultr / on-prem laptops / pyzeebe sidecars) using
   `bitnet.cpp` or `llama.cpp` BitNet kernels.
2. **Browser tabs** via `transformers.js` + WebGPU and a WASM ternary kernel
   fallback so it loads in a Cloudflare Worker / Svelte page with no GPU
   required.
3. **Embedded edge** (Apple Silicon, Raspberry Pi-class boards, Android NPU)
   for fully-offline scenarios.

Baien is **not** a replacement for Oka. Oka stays the high-quality FP8 trunk
trained on the H100 pod. Baien is the **always-available, all-modalities,
zero-server tier** for low-latency on-device inference, edge fallback, and
privacy-first paths where uploading prompts to a server-side LLM is not
acceptable.

The name *Baien* (梅園) is from **Miura Baien (三浦梅園, 1723–1789)**, the
Edo-period philosopher of *jōri* (条理): paired-opposites reasoning. The
mapping is intentional — BitNet b1.58 weights are the ternary alphabet
{−1, 0, +1}, the most literal possible "paired-opposites with rest" basis.

# Scope

**In scope** (this ADR is authoritative for these):

- Model family naming, sizing, and modality coverage for `baien`.
- Default trunk = `microsoft/bitnet-b1.58-2B-4T-bf16`.
- Edge / browser / CPU runtime target matrix and the kernel each target
  uses.
- LoRA-on-bf16-master fine-tune flow (because direct ternary fine-tunes
  are unstable; we fine-tune the bf16 master then re-quantize).
- Lineage rows in `vertex_training_*` (shared with Oka).
- Registry SSoT placement (`llm-model-registry.ts`).

**Out of scope** (deferred or owned elsewhere):

- The data-center FP8 multimodal trunk (Oka, ADR 2605092345).
- The 6000 Ada inference pod (ADR-2605010000).
- The H100 training pod assignment (ADR 2605092345).
- Any change to `vertex_training_run` schema; Baien reuses it as-is and
  records `kind="baien-lora"` / `kind="baien-multimodal-graft"`.

# Executive Summary

| Layer | Component | Decision |
|---|---|---|
| Trunk | Text trunk | `microsoft/bitnet-b1.58-2B-4T-bf16` (HF) |
| Trunk format | Ship | bf16 master + ternary-packed `bitnet.cpp` blob (i2_s) |
| Vision encoder | SigLIP-So400m → ternary projector | bf16 encoder (~400M) + 1.58-bit projection head |
| Audio encoder | Whisper-tiny CTC head → ternary projector | int8 encoder + 1.58-bit projection head |
| Tokenizer | Reuse BitNet b1.58 tokenizer (LLaMA-2 SentencePiece) | no retrain |
| Context | 4,096 tokens | inherits from BitNet b1.58 2B |
| Training | LoRA-on-bf16-master, then re-quantize | adapter rank ≤ 64, qat-friendly |
| Training pod | RunPod H100 NVL (training-only, ADR 2605092345) — same pod as Oka | no new GPU SKU |
| Edge runtime | bitnet.cpp i2_s (Apple Silicon, x86 AVX2/AVX512, ARM NEON) | CPU |
| Browser runtime | transformers.js + WebGPU; WASM ternary kernel fallback | per-tab |
| Embedded runtime | llama.cpp BitNet kernel (mobile / Pi-class) | offline |
| Lineage | `vertex_training_run.kind ∈ {baien-lora, baien-multimodal-graft}` | shared with Oka |
| Registry alias | `baien-bitnet-1.58bit-base` | SSoT in `llm-model-registry.ts` |
| Cost | $0/hr serving (runs on the user's device) | training cost amortized on H100 |

# Decision

## 1. Trunk

The trunk is **`microsoft/bitnet-b1.58-2B-4T-bf16`**, downloaded from
Hugging Face. We ship two artefacts per Baien release:

- `baien-trunk-{ver}-bf16.safetensors` — the master, used for fine-tuning
  and as the source of truth for re-quantization. Stored in B2 keyed by
  sha256.
- `baien-trunk-{ver}-i2s.bnp` — the `bitnet.cpp` ternary-packed blob,
  used by all CPU / edge / browser runtimes. ~0.6 GiB on disk for the
  2B model.

The bf16 master is the **reference**; every quantized form is regenerated
from it (so checksums and lineage trace back to one row in
`vertex_training_checkpoint`).

## 2. Multimodal grafts

We do **not** train a from-scratch multimodal trunk on top of BitNet.
Instead we *graft* off-the-shelf encoders and learn only the projection
head. This keeps Baien a CPU/edge model: encoders run once at upload
time, then the BitNet trunk consumes a small embedding sequence.

| Modality | Encoder | Projector | Sequence length |
|---|---|---|---|
| Text | (none — direct tokenizer) | — | up to 4,096 tok |
| Image | SigLIP-So400m (frozen) | 1.58-bit linear projector to BitNet hidden dim | 64 image tokens |
| Audio (speech) | Whisper-tiny CTC encoder | 1.58-bit linear projector | 32 audio tokens |
| Audio (env) | YAMNet (frozen, mobile-friendly) | 1.58-bit linear projector | 16 tokens |

Encoders ship as **int8 ONNX** for CPU and **WebGPU** kernels for browser.
Projectors are themselves BitNet-b1.58 1-layer transformers so they fit
the same kernel as the trunk — no extra ALU path on the edge.

## 3. Training (lives on the H100 training pod)

Baien training **reuses the H100 NVL pod** owned by Oka (ADR 2605092345).
We do not provision a new GPU. Reasons:

- BitNet b1.58 fine-tunes are bf16-on-master + LoRA, so a single H100
  fits a 2B trunk + projectors easily (peak ~12 GiB).
- The H100 pod is ad-hoc; Baien runs slot in between Oka SFT runs.

Training kinds added to `vertex_training_run`:

- `baien-lora` — LoRA on the bf16 master, then re-quantize and verify
  perplexity drift ≤ 5 % vs the unquantized master on a held-out set.
- `baien-multimodal-graft` — projector training (image/audio/env), trunk
  frozen.

Recorded fields stay identical to Oka (`base_model`, `base_model_revision`,
`hyperparams_json` etc.). `base_model` for Baien defaults to
`microsoft/bitnet-b1.58-2B-4T-bf16`.

## 4. Runtime target matrix

| Target | Binary path | Quantization | Notes |
|---|---|---|---|
| Server CPU pod | `bitnet.cpp` (Microsoft, MIT) | i2_s | Slot into `kotodama.primitives.chat` as a CPU fallback when the 6000 Ada inference pod is rate-limited or unreachable. |
| Apple Silicon (laptop) | `bitnet.cpp` ARM NEON kernel | i2_s | Same blob; auto-detect at load. |
| Browser (WebGPU) | `transformers.js` + custom WebGPU shader | i2_s ⇒ packed-int8 dequant in shader | Shipped as static asset on `baien.etzhayyim.com`. |
| Browser (WASM) | `wasm-bitnet` (vendored, fallback) | i2_s | For browsers without WebGPU or with mobile GPU memory caps. |
| Embedded (Pi / mobile) | `llama.cpp` BitNet kernel | i2_s | Same blob; quality matches CPU. |

Inference SSoT routing is set in `llm-model-registry.ts` via a new
use-case set `{"edge", "browser", "cpu"}` so callers ask for "use-case
edge" and the registry returns Baien rather than a server-bound model.

## 5. SSoT placement

- **Lineage SSoT**: `vertex_training_run` / `vertex_training_checkpoint`
  in Kotoba/Datomic (no schema change).
- **Model alias SSoT**: `MODEL_REGISTRY["baien-bitnet-1.58bit-base"]` in
  `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts`.
  Carries `huggingfaceModel = "microsoft/bitnet-b1.58-2B-4T-bf16"` so
  trainers hit HF directly with no separate config.
- **Use-cases**: `UseCaseName` is extended with `"edge"`, `"browser"`,
  `"cpu"` — all three default to `baien-bitnet-1.58bit-base`.
- **Asset SSoT**: bf16 + i2_s blobs live under
  `b2://etzhayyim-models/baien/{ver}/`. Browser assets are mirrored to
  `baien.etzhayyim.com` static origin via Workers Assets.

## 6. Cost

| Item | Cost | Notes |
|---|---|---|
| Inference (any target) | $0/hr | Runs on the user's CPU / GPU / browser. |
| Training (LoRA + projector) | piggybacks H100 ad-hoc cost | See `[invariants.gpu_pricing.runpod_h100_nvl]` in `deps.toml`. |
| Trunk hosting | B2 ≪ $1/mo | ~0.6 GiB ternary + ~4 GiB bf16 master per release. |
| Browser asset egress | Workers free tier | Static blob, cached at edge. |

There is **no new always-on cost**. Baien's value proposition is exactly
that.

# Comparison

|  | Oka (FP8 H100) | Baien (BitNet 1.58) |
|---|---|---|
| Default trunk | `google/gemma-4-E4B` | `microsoft/bitnet-b1.58-2B-4T-bf16` |
| Param count (active) | 4 B (MoE) → 26 B total | 2 B dense |
| Precision | FP8 / bf16 | 1.58-bit ternary {−1, 0, +1} |
| Where it runs | RunPod 6000 Ada inference pod | User device / browser / edge |
| Where it trains | RunPod H100 NVL training pod | Same H100 pod (slot-in) |
| Multimodal | Native joint training (long-term) | Encoder graft + projector |
| Privacy story | Server-side, audit log only | On-device by default |
| Latency floor | network RTT to 6000 Ada | local CPU |
| Throughput ceiling | GPU batch | per-core dense matmul |

The two are **complementary**. The cell-membrane metaphor (ADR
2605091400) treats Oka as the cytoplasm-side rich model and Baien as the
membrane-side cheap-and-everywhere model — most external interactions
hit Baien first; only difficult work escalates to Oka via the kotodama
MCP facade.

# Rationale

- **Why BitNet b1.58, not int4 / int8?** b1.58 has matched-perplexity
  evidence (Microsoft 2024 paper) at 2B+ scale and ships with a real CPU
  kernel (`bitnet.cpp`). int4 / int8 GGUF do not give the same
  CPU-without-GPU latency profile, and the published 4 T-token training
  budget is enough that we do not need to redo pre-training.
- **Why bf16 checkpoint as base?** The bf16 release is the *master*: it
  is the form that supports stable LoRA fine-tunes. Direct ternary
  fine-tunes are unstable on small adapters.
- **Why graft encoders rather than train multimodal end-to-end?** A
  from-scratch multimodal BitNet at 2 B would require the whole
  pre-training budget again, which is infeasible on one H100. Grafting
  is the standard LLaVA-style path and lets us ship in weeks not
  quarters.
- **Why reuse the H100 pod?** Adding a second GPU SKU just for Baien
  doubles cost without doubling utilization (BitNet runs cleanly on
  hardware Oka already has).
- **Why three runtime targets, not one?** Edge ≠ browser ≠ CPU pod.
  Each has different memory and SIMD constraints, but `bitnet.cpp`'s
  i2_s blob is the same on all three so we keep one source-of-weights
  and three thin runtime adapters.

# Exceptions

- **No on-device training.** Baien trains on the H100 pod only. Edge
  devices download a checkpoint; they do not adapt locally. (Future work
  may add federated LoRA adapters, but not in this ADR.)
- **No PII in training data.** Baien shares the
  `[[critical_rules]] PII Tier 3 + Cohort-First` rule with Oka. Browser
  deployment makes this stricter, not looser.
- **No drop-in replacement for Oka in convo / shinka / kyumei-koji.**
  Quality at 2 B / ternary is sufficient for routing, summarization,
  small-talk, OCR-style tasks — but `kyumei-koji-validate` and
  `reasoning` use-cases stay on Oka / Qwq.
- **Browser bundle size cap.** The i2_s blob plus runtime must stay
  under 800 MiB compressed; if a future Baien-XL crosses this it ships
  only to native CPU pods, not browsers.

# Status

- 2026-05-10 local bitnet.cpp smoke on Apple M1 Max (32 GiB RAM,
  10-core, macOS 26.4):
  - Cloned `microsoft/BitNet`, built with the bundled
    `preset_kernels/bitnet_b1_58-large` path, downloaded
    `microsoft/BitNet-b1.58-2B-4T-gguf` (`ggml-model-i2_s.gguf`,
    1.2 GiB).
  - Inference loads cleanly and runs at **≈30 tok/s** generation
    (eval 33.57 ms/token over 31 runs; prompt eval 31.71 tok/s) at
    `-t 4 -temp 0 -ngl 0`. Load time after warm cache ≈430 ms.
  - **Quality issue (open)**: under the `i2_s` path on M1 Max, output
    is fluent English tokens but semantically incoherent — looks like
    a tokenizer/kernel mismatch rather than a vocabulary problem.
    `system_info` reports `NEON = 0`, `MATMUL_INT8 = 0` even on
    Apple Silicon, which suggests bitnet.cpp's preset kernels did not
    activate the ARM-optimized integer matmul path. The model is
    therefore "fast but wrong" right now on this host.
  - Next steps before relying on Baien for any user-facing path:
    1. Build `bitnet.cpp` with explicit ARM NEON / `MATMUL_INT8`
       enabled, or pull a TL1/TL2-quantized GGUF (Microsoft's repo
       only ships `i2_s` as of 2026-05-10) and confirm `NEON=1`.
    2. Run a short reference inference through `transformers` on the
       bf16 master and compare top-k outputs token-for-token.
    3. Verify coherent output before recording any latency claim in
       runtime advertising.
  - Bootstrap script:
    `70-tools/scripts/training/baien-bitnet-cpp-bootstrap.sh`
    (clone + build + download + smoke). Local cache:
    `~/.cache/baien/{BitNet,models/BitNet-b1.58-2B-4T}`. The script is
    idempotent (`--smoke-only` re-runs inference without rebuilding).

- 2026-05-10 follow-up bisection of the i2_s "fast but wrong" finding:
  ran a bf16 reference inference against the unquantized master and
  attempted a TL1-enabled rebuild of bitnet.cpp on the same M1 Max:
  - **bf16 master via `transformers` (CPU fp32, dynamo disabled)** —
    `microsoft/BitNet-b1.58-2B-4T-bf16`, prompt "The capital of France
    is", greedy 16 new tokens: completion = `" Paris. Paris is a city
    in the north of France, and it is the"`. Load 11.16 s, generate
    80.29 s (**0.199 tok/s** — slow, expected for fp32 CPU on a 2B
    BitNet without GPU). This proves the bf16 weights themselves are
    coherent; the issue is downstream of the master.
  - **bitnet.cpp i2_s same prompt, same greedy decode** — completion =
    `" Scotia delivered qualified expressed ding ..."` (incoherent,
    fluent-but-random English). Speed 30 tok/s. Therefore the
    incoherence is in the **bitnet.cpp arm64 i2_s decode path**, not
    in the model and not in the tokenizer.
  - **TL1-enabled rebuild attempt** (`-DBITNET_ARM_TL1=ON`,
    `setup_env.py` runs `codegen_tl1.py` for `bitnet_b1_58-3B`
    shapes): clang spent 30+ min compiling the generated
    `src/ggml-bitnet-lut.cpp` (the LUT-expanded kernel) before being
    killed manually. Two parallel cmake jobs hit the same wall. The
    ARM TL1 path ships in upstream microsoft/BitNet but does not
    finish a clean build on Apple clang 21 with the 2B-4T-mapped LUT
    shapes — treated as an upstream issue, not a Baien blocker, but
    means the immediate ARM-fast + correct path is not available
    locally today.
  - Net status for Baien edge runtime on Apple Silicon:
    correctness OK on bf16 master, speed not OK; speed OK on
    bitnet.cpp i2_s, correctness not OK; TL1 path not buildable
    locally yet. The browser (`transformers.js` + WebGPU) and
    server-CPU pod paths are not exercised by this finding and remain
    open. We will not advertise a Baien on-device latency number until
    a single configuration produces both coherent output and a real
    speed gain over fp32 CPU. Bisection scripts:
    `70-tools/scripts/training/baien-bf16-reference.py` (CPU fp32 ref,
    saved artifact `~/.cache/baien/runs/bf16-ref-20260510.txt`) and
    `70-tools/scripts/training/baien-bitnet-cpp-bootstrap.sh`.

- 2026-05-10 third bisect leg — **bitnet.cpp i2_s on linux/amd64
  Skylake** via a one-shot Job on the etzhayyim-vke (Vultr) cluster
  (manifest: `70-tools/scripts/training/baien-bitnet-cpp-vke-smoke.yaml`):
  - Same prompt, same greedy decode: completion =
    `" Paris. Paris is a city that is known for its rich history,
    culture, and architecture. It is also a major center for art,
    fashion, and cuisine"`. **Coherent.** ✅
  - Speed: load 0.62 s, prompt eval 24.78 tok/s (40.35 ms/token),
    generation **23.56 tok/s** (42.44 ms/token, 31 runs), 1.57 s total
    for 37 tokens. Skylake is older than even a baseline cloud x86 CPU,
    so 23 tok/s is the floor — modern x86 servers will be faster.
  - **Conclusion of the three-leg bisect**:
    | host | path | output | speed |
    |---|---|---|---|
    | Apple M1 Max | bitnet.cpp i2_s arm64 stock | incoherent ❌ | 30 tok/s |
    | Apple M1 Max | bitnet.cpp `BITNET_ARM_TL1=ON` rebuild | n/a (clang LUT compile hang) | n/a |
    | Apple M1 Max | bf16 master, `transformers` fp32 CPU | coherent ✅ | 0.20 tok/s |
    | linux/amd64 (Vultr Skylake) | bitnet.cpp i2_s tl2 | **coherent ✅** | **23.56 tok/s** |
    The bug is **specifically in bitnet.cpp's arm64 i2_s decode path**.
    Linux x86_64 CPU pods are a viable Baien edge runtime today; the
    server-CPU-pod cell of the runtime matrix flips from "open" to
    "verified". Apple Silicon and other arm64 hosts (mobile, Pi-class
    boards) inherit the upstream defect and stay open until microsoft/BitNet
    fixes the i2_s arm64 decoder or a TL1-only build path becomes
    practical on Apple clang.
  - Build steps the smoke had to add to make i2_s work on a clean
    Ubuntu 22.04 amd64 image:
    1. `sed` patch on `src/ggml-bitnet-mad.cpp` to convert
       `const int8_t * y = (int8_t *)vy;` and the matching `uint8_t *`
       cast into proper `const_cast<…>` so clang 14+ stops rejecting
       the const drop.
    2. Skip `setup_env.py`'s `convert-hf-to-gguf-bitnet.py` step (it
       fails on `transformers>=4.57` because the vendored converter
       targets older tokenizer config); pull
       `microsoft/BitNet-b1.58-2B-4T-gguf/ggml-model-i2_s.gguf` from
       Hugging Face directly via `huggingface_hub.hf_hub_download`.
    3. Use Ubuntu 22.04 (clang 14) — Ubuntu 24.04 (clang 18) rejects
       `ggml-bitnet-mad.cpp:811` even after the const-cast patch.
    Smoke artifact saved at
    `~/.cache/baien/runs/bitnetcpp-amd64-smoke-20260510.log` (889
    lines including the full llama-cli timing block).

# References

- Microsoft BitNet b1.58 paper: "The Era of 1-bit LLMs" (arXiv 2402.17764).
- HF model card: `https://huggingface.co/microsoft/bitnet-b1.58-2B-4T-bf16`.
- bitnet.cpp: `https://github.com/microsoft/BitNet`.
- `90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md` (Oka).
- `90-docs/adr/2605091300-bonsai-cultivar-layer-above-myco-yeast.md` (cell metaphor).
- `90-docs/adr/2605070700-rw-native-model-training-weight-lineage.md` (lineage).
- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts` (registry SSoT).
- `deps.toml [invariants.gpu_pricing.runpod_h100_nvl]` (training cost).
