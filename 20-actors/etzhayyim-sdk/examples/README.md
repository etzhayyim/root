# `@etzhayyim/sdk` — examples

End-to-end demos that exercise the `nv-compat` substrate in real
browser / Node contexts.

## `cartpole-webgpu-demo.html` (iter 80)

Self-contained HTML demo of the cartpole WGSL kernel from iter 79
(canonical source: `../src/nv-compat/warp/examples.ts`).

**Open the file directly in any modern browser:**

- Chrome 113+ / Edge / Safari TP / Firefox (`about:config` →
  `dom.webgpu.enabled = true`): runs N=256 cartpole envs in parallel
  via WGSL on the GPU.
- Older browsers without `navigator.gpu`: falls back transparently to
  sequential JS (the same algorithm, same numerics — verified by the
  iter 79 cross-validation suite).

**Controls:**

- `←` / `→` — apply ±10 N to the foreground (env 0) cart.
- `R` — reset all envs to small randomized initial tilts.
- `C` — force CPU (JS) fallback even if WebGPU is available, useful
  for measuring the GPU vs CPU step-rate difference.

**What you'll see:**

- A green cart on a ground line with an orange pole-bob.
- 255 faint ghost-poles representing the other envs running in
  parallel (alpha tracks |θ| so balanced poles fade out).
- Live readout: mode (WebGPU / JS), env count, step number, steps/sec,
  current foreground θ.

**Zero build step.** All code (cartpole step kernel JS + WGSL,
state buffers, WebGPU init, canvas renderer, input loop) is inlined
in the single HTML file. The inlined cartpole kernel is byte-for-byte
the canonical SDK version at
`../src/nv-compat/warp/examples.ts` (`cartpoleStepKernel`, iter 79).

ADR-2605261800 §D6 nv-compat namespace localization.
