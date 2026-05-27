// Reference WGSL+JS kernel pairs that exercise the wgpuLaunch path.
//
// These are pedagogical examples — they prove the architectural
// pattern: a kernel author writes both a JS implementation (for the
// sync `launch` path and as the WebGPU fallback) and a WGSL compute
// shader (for actual GPU dispatch via `wgpuLaunch`). The runtime
// picks WGSL when navigator.gpu is available.

import { cos, sin, tid, type WpArray } from "./warp.js";
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

// ── Cartpole semi-implicit Euler step (env-parallel) ─────────────────────
//
// Mirrors the Python iter 68 _kernel.cartpole_step (Sutton & Barto /
// OpenAI Gym CartPole-v1 closed-form) stepped across N envs in parallel.
// 2-DoF coupled dynamics — revolute pole on a prismatic cart — closer
// to actual robot work than iter 78's single-pendulum.
//
// Per-env state: x (cart position), x_dot (cart velocity), theta
//   (pole angle from vertical, +θ = pole leans in +x direction), theta_dot.
// Per-env input: force (clamped to ±force_mag externally; this kernel
//   does NOT clamp — caller is responsible).
// Uniform params: dt, gravity, cart_mass, pole_mass, pole_half_length.
//
// Closed-form per Sutton & Barto:
//   temp = (force + m_pole·L·θ̇²·sin θ) / total_mass
//   θ̈   = (g·sin θ - cos θ · temp) / (L · (4/3 - m_pole·cos²θ / total_mass))
//   ẍ   = temp - m_pole·L·θ̈·cos θ / total_mass
//
// Semi-implicit Euler:
//   ẋ' = ẋ + dt·ẍ        x' = x + dt·ẋ'
//   θ̇' = θ̇ + dt·θ̈        θ' = θ + dt·θ̇'

/** Bindings:
 *    @group(0) @binding(0) x         (storage read_write)
 *    @group(0) @binding(1) x_dot     (storage read_write)
 *    @group(0) @binding(2) theta     (storage read_write)
 *    @group(0) @binding(3) theta_dot (storage read_write)
 *    @group(0) @binding(4) force     (storage read, writeback false)
 *    @group(0) @binding(5) dt        (uniform vec4<f32>.x)
 *    @group(0) @binding(6) gravity   (uniform vec4<f32>.x)
 *    @group(0) @binding(7) cart_mass (uniform vec4<f32>.x)
 *    @group(0) @binding(8) pole_mass (uniform vec4<f32>.x)
 *    @group(0) @binding(9) pole_half_length (uniform vec4<f32>.x)
 */
export const cartpoleStepKernel: WgpuKernel = wgpuKernel({
  js: (
    x: WpArray<number>,
    x_dot: WpArray<number>,
    theta: WpArray<number>,
    theta_dot: WpArray<number>,
    force: WpArray<number>,
    dt: number,
    gravity: number,
    cart_mass: number,
    pole_mass: number,
    pole_half_length: number,
  ) => {
    const i = tid();
    const t = theta.get(i);
    const td = theta_dot.get(i);
    const xd = x_dot.get(i);
    const f = force.get(i);
    const sinT = sin(t);
    const cosT = cos(t);
    const totalMass = cart_mass + pole_mass;
    const pml = pole_mass * pole_half_length;
    const temp = (f + pml * td * td * sinT) / totalMass;
    const thetaAcc =
      (gravity * sinT - cosT * temp) /
      (pole_half_length * (4 / 3 - pole_mass * cosT * cosT / totalMass));
    const xAcc = temp - pml * thetaAcc * cosT / totalMass;
    const xDotNew = xd + dt * xAcc;
    const xNew = x.get(i) + dt * xDotNew;
    const thetaDotNew = td + dt * thetaAcc;
    const thetaNew = t + dt * thetaDotNew;
    x_dot.set(i, xDotNew);
    x.set(i, xNew);
    theta_dot.set(i, thetaDotNew);
    theta.set(i, thetaNew);
  },
  wgsl: `
@group(0) @binding(0) var<storage, read_write> x:         array<f32>;
@group(0) @binding(1) var<storage, read_write> x_dot:     array<f32>;
@group(0) @binding(2) var<storage, read_write> theta:     array<f32>;
@group(0) @binding(3) var<storage, read_write> theta_dot: array<f32>;
@group(0) @binding(4) var<storage, read_write> force:     array<f32>;
@group(0) @binding(5) var<uniform>             dt_u:      vec4<f32>;
@group(0) @binding(6) var<uniform>             g_u:       vec4<f32>;
@group(0) @binding(7) var<uniform>             cm_u:      vec4<f32>;
@group(0) @binding(8) var<uniform>             pm_u:      vec4<f32>;
@group(0) @binding(9) var<uniform>             L_u:       vec4<f32>;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let i = gid.x;
  if (i >= arrayLength(&theta)) {
    return;
  }
  let t = theta[i];
  let td = theta_dot[i];
  let xd = x_dot[i];
  let f = force[i];
  let dt = dt_u.x;
  let g = g_u.x;
  let cart_mass = cm_u.x;
  let pole_mass = pm_u.x;
  let L = L_u.x;
  let sinT = sin(t);
  let cosT = cos(t);
  let totalMass = cart_mass + pole_mass;
  let pml = pole_mass * L;
  let temp = (f + pml * td * td * sinT) / totalMass;
  let theta_acc = (g * sinT - cosT * temp) /
                    (L * (4.0 / 3.0 - pole_mass * cosT * cosT / totalMass));
  let x_acc = temp - pml * theta_acc * cosT / totalMass;
  let xDotNew = xd + dt * x_acc;
  let xNew = x[i] + dt * xDotNew;
  let thetaDotNew = td + dt * theta_acc;
  let thetaNew = t + dt * thetaDotNew;
  x_dot[i] = xDotNew;
  x[i] = xNew;
  theta_dot[i] = thetaDotNew;
  theta[i] = thetaNew;
}
`,
  bindings: [
    { binding: 0, kind: "storage", inputIndex: 0, writeback: true },
    { binding: 1, kind: "storage", inputIndex: 1, writeback: true },
    { binding: 2, kind: "storage", inputIndex: 2, writeback: true },
    { binding: 3, kind: "storage", inputIndex: 3, writeback: true },
    { binding: 4, kind: "storage", inputIndex: 4, writeback: false },
    { binding: 5, kind: "uniform", inputIndex: 5 },
    { binding: 6, kind: "uniform", inputIndex: 6 },
    { binding: 7, kind: "uniform", inputIndex: 7 },
    { binding: 8, kind: "uniform", inputIndex: 8 },
    { binding: 9, kind: "uniform", inputIndex: 9 },
  ],
  workgroupSize: 64,
});

// ── Two-link arm step (env-parallel) ─────────────────────────────────────
//
// Closed-form 2-DoF planar arm dynamics — both joints revolute about
// world Y-axis, both links pendulum-like (gravity pulls toward -Z).
// Mirrors the iter 71 compound-pendulum reference (Python iter 68
// PASS 9-10 / TS iter 71 PASS 9-10) but generalised for arbitrary
// torques.
//
// Standard manipulator equation:
//
//   M(q) · q̈ + C(q, q̇) · q̇ + g(q) = τ
//
// For 2-link arm (link i has mass m_i, full length L_i, COM offset r_i
// from joint i, inertia I_i about COM):
//
//   M(q) = [[a + b + 2c·cosθ₂, b + c·cosθ₂],
//           [b + c·cosθ₂,       b           ]]
//
//   where a = m₁r₁² + I₁ + m₂L₁²
//         b = m₂r₂² + I₂
//         c = m₂·L₁·r₂
//
//   C(q,q̇)·q̇ = [[-c·sinθ₂·θ̇₂, -c·sinθ₂·(θ̇₁+θ̇₂)],     [θ̇₁]
//                [ c·sinθ₂·θ̇₁,  0                  ]] · [θ̇₂]
//
//   g(q) = [m₁·g·r₁·sin θ₁ + m₂·g·(L₁·sin θ₁ + r₂·sin(θ₁+θ₂)),
//           m₂·g·r₂·sin(θ₁+θ₂)]
//
// Invert M(q) by hand (2×2 closed form), solve for q̈, semi-implicit
// Euler integrate. Reference: Spong, Robot Modeling & Control, Ch. 7.

/** State + input + uniform bindings (11 total):
 *    @group(0) @binding(0)  theta1     (storage read_write)
 *    @group(0) @binding(1)  theta1_dot (storage read_write)
 *    @group(0) @binding(2)  theta2     (storage read_write)
 *    @group(0) @binding(3)  theta2_dot (storage read_write)
 *    @group(0) @binding(4)  tau1       (storage read, writeback false)
 *    @group(0) @binding(5)  tau2       (storage read, writeback false)
 *    @group(0) @binding(6)  dt         (uniform vec4<f32>.x)
 *    @group(0) @binding(7)  gravity    (uniform vec4<f32>.x)
 *    @group(0) @binding(8)  link1      (uniform vec4<f32>: m1, L1, r1, I1)
 *    @group(0) @binding(9)  link2      (uniform vec4<f32>: m2, L2, r2, I2)
 *                                       (L2 unused — arm-tip is at r2 + L2/2
 *                                        in conventional layout, but free
 *                                        for caller's interpretation)
 */
export const twoLinkArmStepKernel: WgpuKernel = wgpuKernel({
  js: (
    theta1:     WpArray<number>,
    theta1_dot: WpArray<number>,
    theta2:     WpArray<number>,
    theta2_dot: WpArray<number>,
    tau1:       WpArray<number>,
    tau2:       WpArray<number>,
    dt:         number,
    g:          number,
    m1: number, L1: number, r1: number, I1: number,
    m2: number, L2: number, r2: number, I2: number,
  ) => {
    const i = tid();
    const q1 = theta1.get(i);
    const q2 = theta2.get(i);
    const dq1 = theta1_dot.get(i);
    const dq2 = theta2_dot.get(i);
    const t1 = tau1.get(i);
    const t2 = tau2.get(i);
    void L2; // L2 reserved for future tip-frame variants
    const a = m1 * r1 * r1 + I1 + m2 * L1 * L1;
    const b = m2 * r2 * r2 + I2;
    const c = m2 * L1 * r2;
    const cosT2 = cos(q2);
    const sinT2 = sin(q2);
    // M(q)
    const M11 = a + b + 2 * c * cosT2;
    const M12 = b + c * cosT2;
    const M22 = b;
    // h = C·q̇ + g
    const h1 = -c * sinT2 * dq2 * dq1
                - c * sinT2 * (dq1 + dq2) * dq2
                + m1 * g * r1 * sin(q1)
                + m2 * g * (L1 * sin(q1) + r2 * sin(q1 + q2));
    const h2 =  c * sinT2 * dq1 * dq1
                + m2 * g * r2 * sin(q1 + q2);
    // Solve M·q̈ = τ - h via 2×2 inverse:
    //   det = M11·M22 - M12²
    //   q̈₁ = (M22·b₁ - M12·b₂) / det   where b = τ - h
    //   q̈₂ = (M11·b₂ - M12·b₁) / det
    const b1 = t1 - h1;
    const b2 = t2 - h2;
    const det = M11 * M22 - M12 * M12;
    const ddq1 = (M22 * b1 - M12 * b2) / det;
    const ddq2 = (M11 * b2 - M12 * b1) / det;
    // Semi-implicit Euler
    const dq1New = dq1 + dt * ddq1;
    const dq2New = dq2 + dt * ddq2;
    theta1_dot.set(i, dq1New);
    theta1.set(i, q1 + dt * dq1New);
    theta2_dot.set(i, dq2New);
    theta2.set(i, q2 + dt * dq2New);
  },
  wgsl: `
@group(0) @binding(0)  var<storage, read_write> theta1:     array<f32>;
@group(0) @binding(1)  var<storage, read_write> theta1_dot: array<f32>;
@group(0) @binding(2)  var<storage, read_write> theta2:     array<f32>;
@group(0) @binding(3)  var<storage, read_write> theta2_dot: array<f32>;
@group(0) @binding(4)  var<storage, read_write> tau1:       array<f32>;
@group(0) @binding(5)  var<storage, read_write> tau2:       array<f32>;
@group(0) @binding(6)  var<uniform>             dt_u:       vec4<f32>;
@group(0) @binding(7)  var<uniform>             g_u:        vec4<f32>;
@group(0) @binding(8)  var<uniform>             link1_u:    vec4<f32>;
@group(0) @binding(9)  var<uniform>             link2_u:    vec4<f32>;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let i = gid.x;
  if (i >= arrayLength(&theta1)) { return; }
  let q1 = theta1[i];
  let q2 = theta2[i];
  let dq1 = theta1_dot[i];
  let dq2 = theta2_dot[i];
  let t1 = tau1[i];
  let t2 = tau2[i];
  let dt = dt_u.x;
  let g  = g_u.x;
  let m1 = link1_u.x; let L1 = link1_u.y; let r1 = link1_u.z; let I1 = link1_u.w;
  let m2 = link2_u.x;                     let r2 = link2_u.z; let I2 = link2_u.w;
  let a = m1 * r1 * r1 + I1 + m2 * L1 * L1;
  let b = m2 * r2 * r2 + I2;
  let c = m2 * L1 * r2;
  let cosT2 = cos(q2);
  let sinT2 = sin(q2);
  let M11 = a + b + 2.0 * c * cosT2;
  let M12 = b + c * cosT2;
  let M22 = b;
  let h1 = -c * sinT2 * dq2 * dq1
           - c * sinT2 * (dq1 + dq2) * dq2
           + m1 * g * r1 * sin(q1)
           + m2 * g * (L1 * sin(q1) + r2 * sin(q1 + q2));
  let h2 =  c * sinT2 * dq1 * dq1
           + m2 * g * r2 * sin(q1 + q2);
  let b1 = t1 - h1;
  let b2 = t2 - h2;
  let det = M11 * M22 - M12 * M12;
  let ddq1 = (M22 * b1 - M12 * b2) / det;
  let ddq2 = (M11 * b2 - M12 * b1) / det;
  let dq1New = dq1 + dt * ddq1;
  let dq2New = dq2 + dt * ddq2;
  theta1_dot[i] = dq1New;
  theta1[i] = q1 + dt * dq1New;
  theta2_dot[i] = dq2New;
  theta2[i] = q2 + dt * dq2New;
}
`,
  bindings: [
    { binding: 0, kind: "storage", inputIndex: 0, writeback: true },
    { binding: 1, kind: "storage", inputIndex: 1, writeback: true },
    { binding: 2, kind: "storage", inputIndex: 2, writeback: true },
    { binding: 3, kind: "storage", inputIndex: 3, writeback: true },
    { binding: 4, kind: "storage", inputIndex: 4, writeback: false },
    { binding: 5, kind: "storage", inputIndex: 5, writeback: false },
    { binding: 6, kind: "uniform", inputIndex: 6 },
    { binding: 7, kind: "uniform", inputIndex: 7 },
    { binding: 8, kind: "uniform", inputIndex: 8 },
    { binding: 9, kind: "uniform", inputIndex: 9 },
  ],
  workgroupSize: 64,
});
