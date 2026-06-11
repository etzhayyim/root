---
id: adr-2606034800-manako-browser-local-yolo26-object-detection
title: "ADR-2606034800: manako 眼 — browser-local YOLO26 object detection (WebGPU/wasm)"
status: accepted
doc_type: adr
topic: manako-browser-local-yolo26
authoritative: true
last_verified: 2026-06-03
priority: 5.0
axis: architecture
weight: 0.55
priority_note: "Browser-local object detection over ONNX Runtime Web; extends the ameno edge-inference carve-out to a vision model."
authoritative_for:
  - manako-browser-local-yolo26
  - yolo26-onnx-dual-mode-postprocessing
depends_on:
  - adr-2606012100-donation-funded-operation-and-compute-node-donation
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
supersedes: []
superseded_by: []
---

# ADR-2606034800: manako 眼 — browser-local YOLO26 object detection (WebGPU/wasm)

**Status**: accepted
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

Request: *「yolo26 を wasm browser で動くように設計実装」* — run YOLO26 object detection
fully in the browser via WebAssembly/WebGPU.

Survey of the repo before this ADR:

- **No YOLO26.** The only object-detection code present was `Yolov8FaceOnnxBackend`
  in `70-tools/e7m-dataset/src/e7m_dataset/vision_pii_filter.py` — a **server-side
  Python + onnxruntime (CPU/CoreML)** face detector used for dataset PII blurring
  (ADR-2605262500). Not browser, not wasm, not general object detection.
- **A proven browser-wasm ONNX path already exists**: `gazo` runs Stable Diffusion
  entirely in-browser via `onnxruntime-web` (WebGPU → wasm fallback), Web-Worker +
  OPFS-cached CDN model files. `ameno` is the canonical "browser WebGPU/WebNN
  inference, zero install" node class (ADR-2606012100).

So the missing piece is purely a vision *detector* on the existing edge-inference
substrate — not new infra.

Two constraints shape the design:

1. **License.** Ultralytics YOLO26 (weights + train/export toolchain) is **AGPL-3.0**.
   The repo default is **Apache-2.0 + Charter Rider v2.0**, and bundling weights also
   violates the no-git-lfs rule. We must keep AGPL artifacts out of the tree.
2. **Murakumo-only inference invariant** (ADR-2605215000). Browser WebGPU/wasm is the
   explicit *edge carve-out* (ameno node class) — allowed precisely because it runs on
   the user's/donor's device, not commercial GPU rental.

# Decision

Ship **`60-apps/etzhayyim-project-manako`** (眼 "manako" = eye) — a self-contained
Svelte 5 + `onnxruntime-web` app that mirrors the `gazo` architecture, with one
genuinely new technical component: a **dual-mode YOLO26 output postprocessor**.

## Architecture

```
File / <img> / video frame
  → detect.svelte.ts (main thread, transfers ImageBitmap)
    → detect-worker.ts (Web Worker)
        fetch .onnx (operator CDN, OPFS-cached) → ort session [webgpu, wasm]
        letterbox → OffscreenCanvas → NCHW Float32 /255 → session.run
        → postprocess()  [yolo26-core.ts — pure]
    → detections (original-image px) → canvas overlay
```

## Dual-mode postprocessing (`src/lib/yolo26-core.ts`, pure + unit-tested)

A YOLO26 ONNX can be exported in two shapes; manako auto-detects via `detectLayout()`:

| Mode | Shape | Handling |
|---|---|---|
| **NMS-free / end-to-end** (`nms=True`) | `(1, N, 6)` `[x1,y1,x2,y2,score,cls]` | threshold + un-letterbox, no NMS |
| **Raw head** (`nms=False`) | `(1, 4+nc, A)` chw / `(1, A, 4+nc)` hwc | argmax → cxcywh→xyxy → class-aware NMS → un-letterbox |

The core is DOM-free and onnxruntime-free, so it runs under Node and is the honest
verifiable surface. Letterbox geometry, IoU, class-aware NMS, layout detection, and
both decoders are covered by **12/12 passing tests** (`tsx --test`).

## Empirical verification (2026-06-03)

The design was validated against the **real** model, not just synthetic tensors:

- `yolo26n.pt` (Ultralytics 8.4.60, GitHub assets v8.4.0) exported to ONNX →
  output shape **`(1, 300, 6)`** — i.e. YOLO26 is inherently NMS-free, exactly the
  flagship path the dual-mode core anticipated.
- Python `onnxruntime` on the canonical `bus.jpg` → 1 bus + 4 persons.
- The **same raw tensor** fed through manako's TS `postprocess()` → identical boxes/scores.
- **`onnxruntime-web` v1.26.0 on its `wasm` execution provider** (the exact package the
  browser worker imports) loaded and ran the model in-runtime; manako's core reproduced
  the identical detections (input `images`, output `output0`, dims `[1,300,6]`).

So the end-to-end chain `YOLO26.onnx → onnxruntime-web (WASM) → postprocess → detections`
is empirically confirmed on the WebAssembly runtime the browser uses. The one unrun step
is a literal Chrome/WebGPU screenshot (the browser extension was not connected in the
verifying session); the WASM EP run covers the substantive "runs in the browser via wasm"
claim.

## Gates (constitutional alignment)

- **G1 on-device only** — 100% in-browser inference (WebGPU → wasm). No server
  inference, no image upload, no telemetry. (ADR-2606012100 + 2605215000)
- **G2 AGPL isolation / no bundled weights** — YOLO26 weights + Ultralytics source are
  AGPL-3.0 and never committed/vendored/derived. Operator exports + hosts the `.onnx`
  at runtime (CDN/IPFS), exactly like `gazo`'s SD weights. manako's pre/post code is
  original Apache-2.0 work. No git-lfs. (Charter Rider §2; ADR-2605192200)
- **G3 no surveillance / no biometric** — object detection only (COCO-80). NOT face
  recognition / person re-ID / identity tracking. Privacy-by-construction (mirrors
  kiyome G9, ADR-2606032100).
- **G4 Murakumo invariant preserved** — browser WebGPU/wasm carve-out only; no RunPod /
  commercial-GPU / vendor inference path introduced.
- **G5 honest R0** — pure logic + tests verified; live WebGPU run is operator-gated on
  an exported model being provisioned to the CDN.

## Non-goals

Weaponized targeting; mass surveillance; facial recognition; person re-identification;
license-plate/biometric harvesting. Frontier accuracy is not a target (edge model on
edge runtime, consistent with the baien edge-target spirit, ADR-2605241900).

# Consequences

**Positive**

- First browser-local vision *detector* on the etzhayyim edge substrate; reuses the
  proven gazo worker+ort+OPFS pattern, so deploy/runtime is well-trodden.
- License-clean: zero AGPL in the Apache tree; the dual-mode postprocessor is portable
  to any future YOLO export or a different detector head.
- Fully on-device → satisfies the Murakumo invariant and the privacy gate by
  construction.

**Negative / honest limits**

- **No weights shipped.** Until an operator exports `yolo26{n,s,m}.onnx` and hosts it on
  `cdn.etzhayyim.com/models/yolo26/` (or self-hosts via the `yolo26n-local`
  `/models/…` entry), the app loads nothing (states so in UI).
- The model+runtime path is verified on the **WASM EP** (above); the literal Chrome
  **WebGPU** EP run / UI screenshot is **not yet captured in CI** (needs a GPU browser
  session). This is R0.
- WebGPU availability varies (Chrome/Edge 113+); wasm fallback works but is slower.

# Alternatives Considered

1. **Add YOLO to the existing `e7m-dataset` Python path** — rejected: server-side, not
   browser/wasm; doesn't answer the request and pulls inference off-device.
2. **Bundle Ultralytics + weights in-repo** — rejected: AGPL-3.0 vs Apache/Charter; also
   no-git-lfs. Kept as runtime operator artifact instead.
3. **transformers.js detection pipeline** — rejected for the detector core: less control
   over YOLO26's two export layouts; a thin ort-web path + our own decoder is smaller
   and exactly matches the gazo precedent.
4. **WebNN instead of WebGPU** — deferred: ort-web WebNN EP is viable as a later fast
   path (ameno WebNN, ADR-2605252100); WebGPU→wasm covers R0.

# References

- `60-apps/etzhayyim-project-manako/` — app + `src/lib/yolo26-core.ts` (+ `.test.ts`)
- ADR-2606012100 — ameno browser node class (compute donation)
- ADR-2605215000 — Murakumo-only inference (browser edge carve-out)
- ADR-2605262500 — vision PII filter (yolov8-face, server-side; the PII-removal sibling)
- `60-apps/etzhayyim-project-gazo/` — browser SD precedent (worker + ort-web + OPFS)
