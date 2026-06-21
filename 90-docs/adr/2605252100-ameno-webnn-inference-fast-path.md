---
id: adr-2605252100-ameno-webnn-inference-fast-path
title: "ameno WebNN inference fast path — CoreML / DirectML / NNAPI / Qualcomm AI Engine via the W3C WebNN API (inference-only; training stays on WebGPU)"
status: accepted
doc_type: adr
topic: ameno-webnn-fast-path
authoritative: true
last_verified: 2026-05-25
status_note: "R0 scaffold landed 2026-05-25 session-close (6 files changed, +49 LoC against existing ameno + 268 LoC new `webnn.ts` + 340 LoC this ADR). WebNN is a W3C Candidate Recommendation Draft (2026-05-21) for **neural network INFERENCE acceleration**; training (backward / gradient / optimizer) is explicitly out of scope. ameno adopts WebNN as the inference fast path that maps to OS-native NPU stacks (CoreML on Apple Neural Engine / DirectML on Copilot+ PC NPU / NNAPI → QNN HTP delegate on Snapdragon Hexagon / NNAPI → TFLite on other Android). Federated training (ADR-2605242600 / 2605242630) MUST remain on WebGPU — WebNN cannot carry it by design (the 95-op spec has no backward / gradient / optimizer). Safari/WebKit has no WebNN implementation signal as of 2026-05-25, so WebGPU is the mandatory universal fallback (W3). R0 deliverables landed: this ADR + `20-actors/ameno/src/inference/webnn.ts` (`detectWebnnSupport` async UA + MLContext probe across npu/gpu/cpu deviceType + `selectInferenceBackend` ladder webnn-npu → webnn-gpu → webgpu → wasm + `probeAndSelect` convenience + `dispatchWebnnInference` throw-on-use with R1 marker, mirrors train/kernels.ts dispatchLoraForward) + `'webnn'` added to `InferenceDevice` union in inference.ts with R0 honesty guard in `loadModel` (throws cleanly when device='webnn' until R1 wires ORT WebNN EP) + index.ts re-exports (5 symbols: detectWebnnSupport, selectInferenceBackend, probeAndSelect, dispatchWebnnInference, types WebnnSupport/WebnnDeviceType/InferenceBackend) + package.json `./inference/webnn` export entry + deps.toml + adr/README.md + CLAUDE.md row 44. `tsc --noEmit` clean. No new lexicon, no Pregel cell, no Murakumo placement — client-side only, substrate boundary (ADR-2605172000) untouched. R1 remaining: wire `onnxruntime-web/webnn` EP + MLContext acquisition + session options; flip `loadModel(device='webnn')` from throw to working; per-device run-log capture across Snapdragon-Chromium / Copilot+ PC / macOS-Chromium 3-device matrix. R2 + R3 wait on Safari/iOS shipping WebNN and Chromium landing direct `qnn` deviceType respectively."
authoritative_for:
  - WebNN feature-detection + capability-probe contract in ameno
  - inference-backend selection policy (NPU > GPU > CPU) for baien / RAG / SBT-gated chat
  - boundary statement: WebNN = inference fast path only; training NEVER routed through WebNN
  - mapping table from WebNN deviceType to OS-native NPU stack
  - Qualcomm AI Engine integration path (NNAPI-QNN delegate; direct QNN backend deferred)
  - phased R0..R3 activation rule (each subsequent phase requires its own ADR)
depends_on:
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605242600-baien-federated-train-via-ameno-webgpu
  - adr-2605242630-baien-federated-r1-webgpu-backward-poc
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - 20-actors/ameno/src/inference.ts
  - 20-actors/ameno/src/inference/webnn.ts
  - 20-actors/ameno/src/train/kernels.ts
  - 20-actors/ameno/src/train/device.ts
  - https://www.w3.org/TR/webnn/
  - https://webmachinelearning.github.io/webnn-status/
supersedes: []
superseded_by: []
---

# Context

baien (BitNet 1.58 trunk) + ameno (browser PWA) target the
constitutional edge envelope of ADR-2605241900: **WASM-32 + iPhone 12+
+ Android 4 GB**, ≤2 GB inference @ 4k ctx / ≤2.5 GB @ 16k ctx, all
modality encoders frozen. Today the inference path is
transformers.js → ONNX Runtime → WebGPU (Apple Silicon, Adreno,
desktop dGPU) or WASM SIMD (fallback). This path does not reach the
**NPU** silicon that ships on every target device:

| Device | NPU | OS-native stack |
|---|---|---|
| iPhone 12+ / M-series Mac | Apple Neural Engine | **CoreML** (`MLComputeUnits.cpuAndNeuralEngine`) |
| Windows 11 Copilot+ PC | Intel/AMD/Qualcomm NPU | **DirectML** (DML 1.13+ exposes NPU device) |
| Android (Snapdragon 8 Gen 2+) | Qualcomm Hexagon | **NNAPI → QNN delegate** (HTP backend) |
| Android (MediaTek/Samsung) | APU / NPU | **NNAPI → TFLite delegate** (NNAPI HAL) |
| ChromeOS / Pixel | Edge TPU | **NNAPI → TFLite delegate** |

The web platform's answer to this fragmentation is the **WebNN API**:
a W3C Candidate Recommendation Draft (snapshot **2026-05-21**, 100+
substantive changes since the CR snapshot of 2026-01-22). Browsers
map WebNN graph calls to whichever native acceleration is available
locally — Core ML on Apple builds, DirectML on Windows, TFLite +
NNAPI on Android, XNNPACK on Linux/ChromeOS. The implementation
matrix (webmachinelearning/webnn-status) shows the 95 spec'd ops now
covered across **Core ML, Windows ML, DirectML, ONNX Runtime WebNN-EP,
and LiteRT/XNNPACK**, with only a handful in flight.

**Three constraints from the spec we must hard-code into ameno:**

1. **WebNN is inference-only.** The spec abstract is unambiguous —
   "a dedicated low-level API for neural network **inference**
   hardware acceleration". There is no `backward`, no `gradient`, no
   `optimizer`, no `autograd` operator in the catalog of 95 ops, and
   training is explicitly out of scope. Any attempt to use WebNN for
   the federated LoRA backward pass (ADR-2605242600 / 2605242630)
   will fail; the backward dispatch MUST stay on WebGPU.
2. **WebNN is not yet shipping in Safari/WebKit.** Apple participates
   in the WG but has made no public implementation commitment. iPhone
   12+ is a primary baien target — therefore WebGPU MUST remain the
   universal fallback. WebNN is a *fast path*, never a *required path*.
3. **WebNN is gated behind browser flags / origin trials.** Chrome /
   Edge / Opera / Brave / Samsung Internet ship it as an experimental
   feature in 2026. Production code MUST feature-detect (`navigator.ml`)
   and route to WebGPU on absence — no flag-required dependency.

This ADR codifies the boundary so we never accidentally route training
through WebNN, and so the inference fast-path lands without
re-litigating the design every time a new device class appears.

# Scope

In scope:

- WebNN feature detection contract (`navigator.ml`, `MLContext`
  acquisition with `deviceType ∈ {npu, gpu, cpu}`, capability probe).
- Backend selection policy (`selectInferenceBackend(profile)`) — the
  ordered fallback ladder used by `loadModel` / `generate`.
- Mapping table from WebNN `deviceType` to OS-native NPU stack
  (CoreML / DirectML / NNAPI → TFLite or QNN delegate).
- Hard rules (W1..W4) preventing accidental misuse.
- R0 deliverables (this commit) + R1..R3 phased activation gates.

Out of scope:

- Routing baien LoRA backward through WebNN. **W1** below makes this
  a constitutional invariant for this ADR; only a future ADR that
  observes a spec change (training ops added to WebNN) may revisit.
- Replacing transformers.js as the model loader. WebNN is invoked
  *below* transformers.js (via ONNX Runtime's WebNN execution
  provider) — model fetching, tokenization, and prompting unchanged.
- Direct Qualcomm AI Engine (QNN SDK) JavaScript bindings. QNN is
  reached via the NNAPI-QNN delegate today; a future ADR may add a
  dedicated `qnn` deviceType once Chromium ships the in-progress WebNN
  QNN backend.
- iOS App Store / Play Store native apps. PWA only, browser WebNN only.
- Murakumo / server-side inference. ADR-2605215000 keeps server
  inference on Ollama + LiteLLM; this ADR is browser-only.

# Decision

## 1. Hard rules (NOT relaxable without an explicit superseding ADR)

| # | Rule | Source |
|---|---|---|
| W1 | WebNN MUST be used for **inference only**. Training (forward+backward+optimizer) MUST remain on WebGPU per ADR-2605242630 §3. Any call site that touches `MLGraphBuilder` from inside a training loop is a violation. | this ADR + W3C WebNN CR Draft 2026-05-21 (training out of scope) |
| W2 | All inference call sites MUST feature-detect (`navigator.ml` ≠ undefined && `MLContext` acquisition succeeds) before dispatching to WebNN. On absence, MUST fall back to WebGPU (ADR-2605241900). | this ADR |
| W3 | WebGPU is the **universal fallback** and remains the inference path for Safari/WebKit (where WebNN has no implementation signal as of 2026-05-25). WebNN is a fast path, NEVER a required path. | this ADR |
| W4 | The OS-native NPU stack reached via WebNN (CoreML / DirectML / NNAPI / QNN delegate) MUST be selected by the browser, NOT by app code. ameno passes `deviceType: 'npu' \| 'gpu' \| 'cpu'`; the browser-internal mapping (e.g. Chromium's `webnn_context_provider_impl.cc` order Windows → ONNX Runtime → DirectML → TFLite) is opaque to ameno. | Chromium WebNN backend selection |

## 2. Three-layer architecture (inference-only)

```
L3  Model exec       transformers.js v3 + ONNX Runtime (Web)
                     onnxruntime-web/webnn execution provider (EP)
L2  Backend select   20-actors/ameno/src/inference/webnn.ts
                     selectInferenceBackend(profile) → 'webnn-npu'
                                                     | 'webnn-gpu'
                                                     | 'webgpu'
                                                     | 'wasm'
L1  Native NPU       CoreML / DirectML / NNAPI (TFLite or QNN delegate)
                     selected by browser via WebNN deviceType
```

### L1 — Native NPU mapping (browser-controlled)

| WebNN `deviceType` | Windows | macOS / iOS | Android | ChromeOS / Linux |
|---|---|---|---|---|
| `'npu'` | DirectML on NPU device (Copilot+ PC) | CoreML on Apple Neural Engine | NNAPI → QNN HTP delegate (Snapdragon) or NNAPI → TFLite (others) | NNAPI → TFLite on Edge TPU |
| `'gpu'` | DirectML on dGPU/iGPU | CoreML on Apple GPU | NNAPI → GPU delegate (OpenCL/Vulkan) | TFLite GPU delegate |
| `'cpu'` | TFLite/XNNPACK | TFLite/XNNPACK | TFLite/XNNPACK | TFLite/XNNPACK |

ameno does not address these stacks directly. It requests a
`deviceType` and the browser picks one — that is the whole point of
the spec abstraction.

### L2 — Backend select (`20-actors/ameno/src/inference/webnn.ts`)

```ts
type InferenceBackend =
  | "webnn-npu"   // WebNN with deviceType='npu' (preferred where present)
  | "webnn-gpu"   // WebNN with deviceType='gpu' (Chromium fallback before WebGPU)
  | "webgpu"     // existing transformers.js+ORT path (universal fallback)
  | "wasm";      // CPU SIMD (last resort)

interface WebnnSupport {
  readonly hasNavigatorML: boolean;
  readonly hasNpuContext: boolean;
  readonly hasGpuContext: boolean;
  readonly hasCpuContext: boolean;
  readonly deviceClass: "ios" | "android" | "wasm-desktop";
}

function detectWebnnSupport(): Promise<WebnnSupport>;
function selectInferenceBackend(
  support: WebnnSupport,
  preferred?: "npu" | "gpu" | "cpu",
): InferenceBackend;
```

Selection ladder (default `preferred='npu'`):

1. `hasNpuContext` → `'webnn-npu'`
2. `hasGpuContext` && Chromium → `'webnn-gpu'`
3. existing WebGPU adapter (Safari included) → `'webgpu'`
4. `'wasm'`

### L3 — Model exec (transformers.js + ORT WebNN EP)

transformers.js v3 already routes through ONNX Runtime Web. We add
`'webnn'` to ameno's `InferenceDevice` union; when selected, the
model is loaded with ORT's WebNN execution provider configured for
the chosen `deviceType`. R0 ships the union extension and detection;
R1 wires the actual ORT EP option (sub-ADR).

## 3. Dispatch path (R0 throw-on-use; R1 wires ORT WebNN EP)

R0 ships every piece *except* the actual ORT WebNN EP wiring:

- `detectWebnnSupport()` — fully implemented, callable today.
- `selectInferenceBackend()` — fully implemented, callable today.
- `dispatchWebnnInference()` — **throws with R1 marker**, same
  pattern as `train/kernels.ts` `dispatchLoraForward`. R1 plugs in
  `onnxruntime-web/webnn` + `MLContext` acquisition + session
  options.

R1 = WebNN EP wired through `onnxruntime-web` for the existing
`baien-bitnet-2b` / `gemma-4-e2b-it` / `gemma-4-e4b-it` model
catalog. Per-device run-log capture parallels the
ADR-2605242630 R1b plan.

## 4. Phased roadmap

| Phase | Scope | Activation gate |
|---|---|---|
| **R0** | This ADR + scaffolds (`webnn.ts` detect+select, `dispatchWebnnInference` throw-on-use, `InferenceDevice` union extension, README + deps.toml registry). No real WebNN dispatch yet. | `tsc --noEmit` clean; `detectWebnnSupport()` returns a non-throwing result on at least one Chromium build |
| **R1** | ORT WebNN EP wired; `dispatchWebnnInference()` actually runs transformers.js+ORT on `deviceType='npu'`; run-log capture; first 3-device matrix (Snapdragon Android Chromium / Windows Copilot+ PC / macOS Chromium). Safari stays on WebGPU. New ADR. | `e7m bench micro` runs E2E on `deviceType='npu'` on at least 2 of the 3 device classes; baseline tok/s recorded |
| **R2** | iOS Safari adoption gate: if Apple ships WebNN in Safari (any version), wire that path; until then iOS stays WebGPU. New ADR (waiting on Apple). | Safari Technology Preview ships `navigator.ml` |
| **R3** | Direct `qnn` deviceType (Qualcomm Hexagon AI Engine via WebNN QNN backend, currently in flight in Chromium). New ADR. | Chromium lands the WebNN QNN backend in stable |

Each subsequent phase requires its own ADR, matching the wadachi
(ADR-2605242000) / yakushi (ADR-2605250500) / federated train
(ADR-2605242600 / 2605242630) pattern.

## 5. R0 deliverables (this commit)

1. This ADR — `90-docs/adr/2605252100-ameno-webnn-inference-fast-path.md`.
2. WebNN detection + routing module —
   `20-actors/ameno/src/inference/webnn.ts`.
3. `InferenceDevice` union extension in
   `20-actors/ameno/src/inference.ts` (`'webnn'` added).
4. Re-export from `20-actors/ameno/src/index.ts` +
   `package.json` exports entry (`./inference/webnn`).
5. `deps.toml` ADR registry + module registry entries.
6. `90-docs/adr/README.md` index row.
7. CLAUDE.md Status row 44.

# Consequences

## Positive

- baien on every Copilot+ PC / Snapdragon Android phone / M-series
  Mac / iPhone 12+ (when Apple ships) reaches the NPU **without
  ameno needing per-OS code paths**. The W3C spec is the single
  abstraction.
- Inference energy budget drops by 5–10× on NPU vs GPU on the same
  silicon (vendor numbers, to be re-measured in R1) — directly
  supports ADR-2605241900 edge invariant.
- The WebGPU path stays for training (ADR-2605242630) and for
  Safari/WebKit fallback. No duplicated state, no rewriting of
  transformers.js — the WebNN EP is below the model-loader layer.
- Constitutional consistency: ADR-2605215000 keeps server inference
  on Murakumo only; ADR-2605242630 keeps training on WebGPU only;
  this ADR keeps client *inference* on WebNN (fast path) + WebGPU
  (fallback). Three orthogonal layers, three explicit rules.

## Negative

- WebNN ship status is still experimental in Chromium (origin trial
  / flag in 2026). Until R1 + a production-stable Chromium release,
  the NPU path is opt-in. R0 lands the contract; R1 lands the
  dispatch wire; production rollout follows browser stability.
- Safari/WebKit has no signal of WebNN implementation. iPhone 12+
  remains on WebGPU until Apple ships — this is acceptable (W3 hard
  rule) but a measurable performance gap will persist on iOS for the
  duration.
- The ORT WebNN EP imposes a model-format constraint (ONNX); models
  outside the existing `MODELS` registry will need ONNX conversion
  before they can use the NPU path. transformers.js + the existing
  `onnx-community/*` models are unaffected.

## Constraint side-effects

- `ameno` package gains one new submodule export (`./inference/webnn`).
  No existing import paths break.
- `InferenceDevice` union grows by one variant (`'webnn'`). Callers
  that pattern-match exhaustively will need to handle the new case
  (TypeScript will surface this at typecheck).
- No new lexicon, no new Pregel cell, no new Murakumo placement —
  this ADR is entirely client-side. Substrate boundary
  (ADR-2605172000) untouched.

# Alternatives Considered

## B1 — Skip WebNN; stay on WebGPU + WASM only

Rejected: gives up the NPU silicon on every target device. The whole
constitutional purpose of running baien on edge (ADR-2605241900) is
to minimize energy + maximize accessibility; NPUs are the energy win
the device manufacturers already shipped. Refusing to use them
because the spec is "only" CR Draft is a poor trade.

## B2 — Per-OS native bindings (CoreML.js / DirectML.js / NNAPI bridges)

Rejected: violates the substrate boundary (PWA only, no native app),
explodes maintenance burden across 4 platforms, and bypasses the
browser-controlled security model. WebNN is the standardized
abstraction precisely so we don't have to do this.

## B3 — Try WebNN for training too (custom op composition)

Rejected by W1 — the spec is inference-only, the 95 ops do not
compose into a backward pass without inventing gradient ops that
don't exist in the spec. Even if we could compose them, R1+ browsers
would refuse to JIT a graph containing un-spec'd ops. Training stays
on WebGPU (ADR-2605242630). If a future WebNN revision adds gradient
ops, that's a new ADR.

## B4 — Direct ONNX Runtime Web (no transformers.js abstraction)

Rejected for R0: transformers.js is the existing model loader
contract in ameno (`MODELS` registry, `AutoTokenizer`,
`AutoModelForCausalLM`). Bypassing it would duplicate tokenizer
handling, chat templating, and progress reporting. ORT-WebNN EP
plugs in *under* transformers.js; nothing above the EP needs to
change.

## B5 — Wait for Safari to ship WebNN before landing the contract

Rejected: Safari shipping is an external timeline we don't control,
and the Chromium / Edge / Samsung Internet / Android Chromium share
of baien participants is already large enough to justify the path.
The contract (W2 + W3) explicitly tolerates Safari absence — when
Apple ships, the path activates automatically via feature detection
(R2 ADR will tune defaults).

# References

- ADR-2605241900 (Baien edge-target invariant) — what these phones
  must fit under.
- ADR-2605242600 (Baien federated training via ameno WebGPU) —
  R0 federated scaffold; this ADR's W1 boundary keeps that ADR's
  training path on WebGPU.
- ADR-2605242630 (Baien federated R1 — WebGPU LoRA backward PoC) —
  the training path WebNN MUST NOT touch.
- ADR-2605192200 (Charter Rider v2.0) — license + Rider on every
  first-party module including `webnn.ts`.
- ADR-2605172000 (kotoba substrate) — untouched (client-side only).
- ADR-2605215000 (Murakumo-only inference) — server inference path;
  this ADR is client-side and does not affect it.
- W3C WebNN API CR Draft, 2026-05-21 — https://www.w3.org/TR/webnn/
- WebNN implementation status (95 ops across Core ML / Windows ML /
  DirectML / ONNX Runtime WebNN-EP / LiteRT/XNNPACK) —
  https://webmachinelearning.github.io/webnn-status/
- ADR-2605242000 (wadachi R0 scaffold) — phased-ADR-per-phase
  pattern this ADR follows.
