// Reference WGSL+JS kernel pairs that exercise the wgpuLaunch path.
//
// These are pedagogical examples — they prove the architectural
// pattern: a kernel author writes both a JS implementation (for the
// sync `launch` path and as the WebGPU fallback) and a WGSL compute
// shader (for actual GPU dispatch via `wgpuLaunch`). The runtime
// picks WGSL when navigator.gpu is available.

import { tid, type WpArray } from "./warp.js";
import { wgpuKernel, type WgpuKernel } from "./wgpu-backend.js";

/** Damping kernel: multiply each element of an array by a scalar.
 *
 *  Bindings:
 *    @group(0) @binding(0) = WpArray<number> (storage, read_write)
 *    @group(0) @binding(1) = scalar damping (uniform)
 *
 *  Workgroup size 64 matches the kami-cartpole-wasm precedent
 *  (per CLAUDE.md note: "kami-genesis/src/wgsl/cartpole_step.wgsl
 *  workgroup_size 64 WGSL kernel").
 */
export const dampingKernel: WgpuKernel = wgpuKernel({
  js: (arr: WpArray<number>, damping: number) => {
    const i = tid();
    arr.set(i, arr.get(i) * damping);
  },
  wgsl: `
struct DampingUniform {
  damping: f32,
  _pad: vec3<f32>,
};

@group(0) @binding(0) var<storage, read_write> arr: array<f32>;
@group(0) @binding(1) var<uniform> uni: DampingUniform;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let i = gid.x;
  if (i >= arrayLength(&arr)) {
    return;
  }
  arr[i] = arr[i] * uni.damping;
}
`,
  bindings: [
    { binding: 0, kind: "storage", inputIndex: 0, writeback: true },
    { binding: 1, kind: "uniform", inputIndex: 1 },
  ],
  workgroupSize: 64,
});
