// Reference WGSL+JS kernel pairs that exercise the wgpuLaunch path.
//
// These are pedagogical examples — they prove the architectural
// pattern: a kernel author writes both a JS implementation (for the
// sync `launch` path and as the WebGPU fallback) and a WGSL compute
// shader (for actual GPU dispatch via `wgpuLaunch`). The runtime
// picks WGSL when navigator.gpu is available.

import { sin, tid, type WpArray } from "./warp.js";
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

// ── Pendulum semi-implicit Euler step (env-parallel) ─────────────────────
//
// Mirrors the iter 71 single-pendulum integrator stepped across N envs in
// parallel. This is the canonical workload Warp / Isaac Lab were
// designed for — thousands of envs advancing one timestep in lock-step
// on the GPU.
//
// Per-env state: theta (angle), omega (angular velocity).
// Per-env input: tau (applied torque).
// Uniform params: dt (timestep), g (gravity magnitude), L (pendulum
// length, COM distance from pivot), mass.
//
// Dynamics: τ_total = τ_applied - m·g·L·sin(θ);  α = τ_total / (m·L²)
// Semi-implicit Euler:  ω' = ω + dt·α;  θ' = θ + dt·ω'
//
// At equilibrium (θ=0, ω=0, τ=0): α=0, ω' = 0, θ' = 0 (no drift).
// At θ=π/2, ω=0, τ=0: α = -g·L·sin(π/2)/(m·L²) = -g/L ≈ -9.81 (m=L=1)
// — matches Python iter 68 PASS 5 and TS iter 71 PASS 5.

/** State + input bindings (in this order):
 *    @group(0) @binding(0) theta  (storage read_write, N floats)
 *    @group(0) @binding(1) omega  (storage read_write, N floats)
 *    @group(0) @binding(2) tau    (storage read, N floats; writeback false)
 *    @group(0) @binding(3) dt     (uniform f32)
 *    @group(0) @binding(4) g      (uniform f32)
 *    @group(0) @binding(5) length (uniform f32)
 *    @group(0) @binding(6) mass   (uniform f32)
 */
export const pendulumStepKernel: WgpuKernel = wgpuKernel({
  js: (
    theta: WpArray<number>,
    omega: WpArray<number>,
    tau: WpArray<number>,
    dt: number,
    g: number,
    length: number,
    mass: number,
  ) => {
    const i = tid();
    const t = theta.get(i);
    const w = omega.get(i);
    const tor = tau.get(i);
    const alpha = (tor - mass * g * length * sin(t)) / (mass * length * length);
    const wNew = w + dt * alpha;
    const tNew = t + dt * wNew;
    omega.set(i, wNew);
    theta.set(i, tNew);
  },
  wgsl: `
@group(0) @binding(0) var<storage, read_write> theta:  array<f32>;
@group(0) @binding(1) var<storage, read_write> omega:  array<f32>;
@group(0) @binding(2) var<storage, read_write> tau:    array<f32>;
@group(0) @binding(3) var<uniform>             dt_u:     vec4<f32>;
@group(0) @binding(4) var<uniform>             g_u:      vec4<f32>;
@group(0) @binding(5) var<uniform>             length_u: vec4<f32>;
@group(0) @binding(6) var<uniform>             mass_u:   vec4<f32>;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let i = gid.x;
  if (i >= arrayLength(&theta)) {
    return;
  }
  let t = theta[i];
  let w = omega[i];
  let tor = tau[i];
  let dt = dt_u.x;
  let g = g_u.x;
  let L = length_u.x;
  let m = mass_u.x;
  let alpha = (tor - m * g * L * sin(t)) / (m * L * L);
  let w_new = w + dt * alpha;
  let t_new = t + dt * w_new;
  omega[i] = w_new;
  theta[i] = t_new;
}
`,
  bindings: [
    { binding: 0, kind: "storage", inputIndex: 0, writeback: true },
    { binding: 1, kind: "storage", inputIndex: 1, writeback: true },
    { binding: 2, kind: "storage", inputIndex: 2, writeback: false },
    { binding: 3, kind: "uniform", inputIndex: 3 },
    { binding: 4, kind: "uniform", inputIndex: 4 },
    { binding: 5, kind: "uniform", inputIndex: 5 },
    { binding: 6, kind: "uniform", inputIndex: 6 },
  ],
  workgroupSize: 64,
});
