---
id: doc-baien-browser-runtime-probe
title: "Baien browser runtime probe — what blocks transformers.js + WebGPU today"
status: active
doc_type: explanation
topic: edge-multimodal-model-1bit
authoritative: false
last_verified: 2026-05-10
related:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - 60-apps/etzhayyim-project-ameno/CLAUDE.md
---

# Goal

Decide whether the Baien runtime matrix's "Browser (WebGPU + WASM)"
cell can be filled in with existing tooling, or whether it depends on
upstream work that does not yet exist.

# State of the world (2026-05-10)

The repo already ships browser-side WebGPU LLM inference for Gemma 4
E2B in the Ameno project
(`60-apps/etzhayyim-project-ameno/`), backed by:

- `@huggingface/transformers` ^3.8.1 (transformers.js v3 — supports ONNX
  models with WebGPU EP)
- `onnxruntime-web` ^1.24.3 (yoro-ui)

So the browser-side tooling exists. The question is whether BitNet
b1.58 has a working ONNX export that ORT-web can run.

## What's published for `microsoft/BitNet-b1.58-2B-4T`

Queried `https://huggingface.co/api/models` for the BitNet 2B 4T
family (2026-05-10):

| Repo | Format | Size | Notes |
|---|---|---|---|
| `microsoft/bitnet-b1.58-2B-4T` | safetensors | ~2 GB packed | Trunk weights, ternary-encoded, requires `transformers>=4.46` BitNet support to load. |
| `microsoft/bitnet-b1.58-2B-4T-bf16` | safetensors | 4.5 GB | bf16 master used for fine-tunes. |
| `microsoft/bitnet-b1.58-2B-4T-gguf` | GGUF | 1.2 GB | i2_s-packed, used by `bitnet.cpp`. |
| `sushraja/bitnet-b1.58-2B-4T-fp16-onnx` | ONNX | ~4 GB | **Community fp16 export** — does not preserve the ternary kernel; defeats the 1.58-bit size win. |

**Microsoft has not published a ternary-aware ONNX.** ONNX core op
set does not include a `BitLinear` 1.58-bit primitive; an export
would need a custom op (and matching ORT kernel) for the ternary
weight × int8 activation matmul.

## Implication for the browser cell

| Path | Blocker | Estimated effort |
|---|---|---|
| ORT-web + community fp16 ONNX | 4 GB asset, no WebGPU memory budget on most laptops, no 1.58-bit speed win — only buys "browser deployment", not "1.58-bit edge" | Low effort, low value. Skip. |
| ORT-web + ternary ONNX with custom `BitLinear` op | No upstream ONNX, no upstream ORT kernel, no upstream WebGPU shader. Need at least one of those. | High — needs upstream work or a vendored fork. |
| `bitnet.cpp` compiled to WASM (emscripten) | `microsoft/BitNet` has no WASM/emscripten target; `i2_s` arm64 path is also broken (see ADR Status). The WASM build would inherit whichever path it lands on. | Medium — emscripten support is feasible but still depends on the i2_s correctness fix being in place. |
| transformers.js native (Python `transformers` BitNet → JS) | transformers.js v3 only runs ONNX-exported models. There is no JS-native BitLinear at all. Same blocker as ORT-web. | Same as ORT-web row. |

The honest answer is: **Baien's browser cell is upstream-blocked
today.** Either Microsoft (or a community contributor) ships a
ternary-aware ONNX with a matching ORT-web kernel, or someone ports
`bitnet.cpp` to emscripten with the arm64-i2_s decode bug already
fixed.

# What we will do

Track the browser cell as **deferred** in ADR 2605092350. Do not
build a fork until one of the upstream paths lands. Watch:

- `microsoft/BitNet` issues — did the ARM i2_s bug get fixed? Is
  there an emscripten build target?
- `microsoft/onnxruntime` extensions — does it gain a `BitLinear`
  custom op?
- Hugging Face `optimum` / `transformers.js` releases — do they ship
  a BitNet ONNX export script?

When any of those land, the implementation is short — wire the asset
into the existing Ameno-style `transformers.js` pipeline.

In the meantime, the Baien runtime matrix has:

- ✅ **Server-CPU pod (linux/amd64)** — verified coherent + fast on
  Skylake, ADR 2605092350 Status. Production-ready.
- ⚠️ **Edge ARM (Apple Silicon, Pi, Android)** — upstream-blocked on
  the arm64 i2_s decode bug.
- ⏸️ **Browser (WebGPU + WASM)** — upstream-blocked on a
  ternary-aware ONNX or a `bitnet.cpp` WASM target. Tracked here.

# References

- microsoft/BitNet: https://github.com/microsoft/BitNet
- transformers.js BitNet support tracker (none yet, file feature
  requests via Optimum / transformers.js issues if needed).
- Existing browser ML wiring in this repo:
  `60-apps/etzhayyim-project-ameno/` (Gemma 4 E2B WebGPU).
