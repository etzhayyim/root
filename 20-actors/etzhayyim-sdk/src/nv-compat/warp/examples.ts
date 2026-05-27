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

// ── Franka 7-DoF forward kinematics (env-parallel) ───────────────────────
//
// Computes EE position for N envs in parallel from per-env q[7]. Real
// Franka FCI joint origins (iter 85). Foundation for future Jacobian
// + IK kernels — proves complex multi-joint FK with rpy frame rotations
// runs correctly on WebGPU.
//
// Per-env input: q[7]
// Per-env output: ee_pos[3]
//
// Storage layout (struct-of-arrays for coalesced GPU access):
//   q_in:    array<f32>  length 7*N  — q[i] = q_in[env*7 + i]
//   ee_out:  array<f32>  length 3*N  — ee[i] = ee_out[env*3 + i]
//
// Algorithm: 7 successive frame compositions. Each joint applies
//   R_origin (from URDF rpy)  ·  Rodrigues(axis_body_z, q_i)
// to the cumulative world-frame rotation, plus xyz translation.
// All inlined per-thread (~150 lines of WGSL).

/** Bindings:
 *    @group(0) @binding(0) q_in    (storage read,  N*7 floats; writeback false)
 *    @group(0) @binding(1) ee_out  (storage read_write, N*3 floats)
 */
export const frankaFkKernel: WgpuKernel = wgpuKernel({
  js: (qIn: WpArray<number>, eeOut: WpArray<number>) => {
    const env = tid();
    const q0 = qIn.get(env * 7 + 0);
    const q1 = qIn.get(env * 7 + 1);
    const q2 = qIn.get(env * 7 + 2);
    const q3 = qIn.get(env * 7 + 3);
    const q4 = qIn.get(env * 7 + 4);
    const q5 = qIn.get(env * 7 + 5);
    const q6 = qIn.get(env * 7 + 6);
    const ee = frankaFkInline([q0, q1, q2, q3, q4, q5, q6]);
    eeOut.set(env * 3 + 0, ee[0]);
    eeOut.set(env * 3 + 1, ee[1]);
    eeOut.set(env * 3 + 2, ee[2]);
  },
  wgsl: `
// Real Franka FCI joint origins (xyz triplet + rpy triplet per joint).
// Pre-computed: cos/sin of rpy values inlined as constants for speed.
// rpy values: (0,0,0), (-π/2,0,0), (π/2,0,0), (π/2,0,0), (-π/2,0,0), (π/2,0,0), (π/2,0,0)

@group(0) @binding(0) var<storage, read_write> q_in:    array<f32>;
@group(0) @binding(1) var<storage, read_write> ee_out:  array<f32>;

// Composed rotation R_world (3×3) stored row-major in 9 f32 locals.
// p_world stored in 3 f32 locals.
// Applies R_world ← R_world · R_origin · R_q (axis z, angle q[i])
// and p_world ← p_world + R_world_pre · xyz.

fn rot_rpy(r: f32, p: f32, y: f32) -> mat3x3<f32> {
  let cr = cos(r); let sr = sin(r);
  let cp = cos(p); let sp = sin(p);
  let cy = cos(y); let sy = sin(y);
  return mat3x3<f32>(
    vec3<f32>(cy*cp, sy*cp, -sp),
    vec3<f32>(cy*sp*sr - sy*cr, sy*sp*sr + cy*cr, cp*sr),
    vec3<f32>(cy*sp*cr + sy*sr, sy*sp*cr - cy*sr, cp*cr),
  );
}

fn rot_z(angle: f32) -> mat3x3<f32> {
  let c = cos(angle); let s = sin(angle);
  return mat3x3<f32>(
    vec3<f32>(c, s, 0.0),
    vec3<f32>(-s, c, 0.0),
    vec3<f32>(0.0, 0.0, 1.0),
  );
}

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let env = gid.x;
  let n_envs = arrayLength(&ee_out) / 3u;
  if (env >= n_envs) { return; }

  let base = env * 7u;
  let q = array<f32, 7>(
    q_in[base + 0u], q_in[base + 1u], q_in[base + 2u], q_in[base + 3u],
    q_in[base + 4u], q_in[base + 5u], q_in[base + 6u],
  );

  let half_pi: f32 = 1.5707963267948966;
  // Joint origins: xyz vec3 + rpy.r (rpy.p, rpy.y are 0 for all Franka joints)
  let xyz = array<vec3<f32>, 7>(
    vec3<f32>(0.0,      0.0,     0.333),
    vec3<f32>(0.0,      0.0,     0.0),
    vec3<f32>(0.0,     -0.316,   0.0),
    vec3<f32>(0.0825,   0.0,     0.0),
    vec3<f32>(-0.0825,  0.384,   0.0),
    vec3<f32>(0.0,      0.0,     0.0),
    vec3<f32>(0.088,    0.0,     0.0),
  );
  let rpy_r = array<f32, 7>(
    0.0,
    -half_pi,
    half_pi,
    half_pi,
    -half_pi,
    half_pi,
    half_pi,
  );

  var R_world = mat3x3<f32>(
    vec3<f32>(1.0, 0.0, 0.0),
    vec3<f32>(0.0, 1.0, 0.0),
    vec3<f32>(0.0, 0.0, 1.0),
  );
  var p_world = vec3<f32>(0.0, 0.0, 0.0);

  for (var i = 0u; i < 7u; i = i + 1u) {
    let R_origin = rot_rpy(rpy_r[i], 0.0, 0.0);
    let R_q = rot_z(q[i]);
    let R_iInP = R_origin * R_q;
    // p contribution: rotated xyz, in current world frame (before this
    // joint's rotation).
    let rotated = R_world * xyz[i];
    p_world = p_world + rotated;
    R_world = R_world * R_iInP;
  }

  ee_out[env * 3u + 0u] = p_world.x;
  ee_out[env * 3u + 1u] = p_world.y;
  ee_out[env * 3u + 2u] = p_world.z;
}
`,
  bindings: [
    { binding: 0, kind: "storage", inputIndex: 0, writeback: false },
    { binding: 1, kind: "storage", inputIndex: 1, writeback: true },
  ],
  workgroupSize: 64,
});

// ── JS reference impl (used by frankaFkKernel.js fallback) ──────────────

const _FRANKA_FK_HALF_PI = Math.PI / 2;
const _FRANKA_FK_XYZ: ReadonlyArray<readonly [number, number, number]> = [
  [0, 0, 0.333],
  [0, 0, 0],
  [0, -0.316, 0],
  [0.0825, 0, 0],
  [-0.0825, 0.384, 0],
  [0, 0, 0],
  [0.088, 0, 0],
];
const _FRANKA_FK_RPY_R: ReadonlyArray<number> = [
  0, -_FRANKA_FK_HALF_PI, _FRANKA_FK_HALF_PI, _FRANKA_FK_HALF_PI,
  -_FRANKA_FK_HALF_PI, _FRANKA_FK_HALF_PI, _FRANKA_FK_HALF_PI,
];

function _rotRpy(r: number): number[][] {
  const cr = Math.cos(r), sr = Math.sin(r);
  return [[1, 0, 0], [0, cr, -sr], [0, sr, cr]];   // p=y=0, so only x-rotation
}

function _rotZ(angle: number): number[][] {
  const c = Math.cos(angle), s = Math.sin(angle);
  return [[c, -s, 0], [s, c, 0], [0, 0, 1]];
}

function _mat3MulSmall(a: number[][], b: number[][]): number[][] {
  const out: number[][] = [[0,0,0],[0,0,0],[0,0,0]];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      let s = 0;
      for (let k = 0; k < 3; k++) s += a[i][k] * b[k][j];
      out[i][j] = s;
    }
  }
  return out;
}

function _matVec3Small(m: number[][], v: readonly number[]): [number, number, number] {
  return [
    m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
    m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
    m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2],
  ];
}

/** Reference Franka 7-DoF FK in pure JS — used by the kernel's JS
 *  fallback AND callable directly for cross-validation.
 *  Returns the world-frame EE position from q[7].
 */
export function frankaFkInline(q: readonly number[]): [number, number, number] {
  let R_world: number[][] = [[1,0,0],[0,1,0],[0,0,1]];
  let p_world: [number, number, number] = [0, 0, 0];
  for (let i = 0; i < 7; i++) {
    const R_origin = _rotRpy(_FRANKA_FK_RPY_R[i]);
    const R_q = _rotZ(q[i]);
    const R_iInP = _mat3MulSmall(R_origin, R_q);
    const rotated = _matVec3Small(R_world, _FRANKA_FK_XYZ[i]);
    p_world = [p_world[0]+rotated[0], p_world[1]+rotated[1], p_world[2]+rotated[2]];
    R_world = _mat3MulSmall(R_world, R_iInP);
  }
  return p_world;
}

// ── Franka 7-DoF FK + linear Jacobian (env-parallel) ─────────────────────
//
// Extends frankaFkKernel (iter 88) with the 3×7 linear Jacobian. Each
// thread runs FK, stores all 7 joint poses in private memory, then
// computes per-joint Jacobian columns via axis_world_i × (p_ee - p_i).
//
// Per-env input: q[7]
// Per-env output: ee_pos[3] + J[3][7] = 24 floats
//
// Storage layout (struct-of-arrays):
//   q_in:    array<f32>  length 7*N
//   out_buf: array<f32>  length 24*N
//     env-i layout: [ee_x, ee_y, ee_z, J[0][0..6], J[1][0..6], J[2][0..6]]

/** Bindings:
 *    @group(0) @binding(0) q_in    (storage read,  N*7 floats)
 *    @group(0) @binding(1) out_buf (storage read_write, N*24 floats)
 */
export const frankaFkJacobianKernel: WgpuKernel = wgpuKernel({
  js: (qIn: WpArray<number>, outBuf: WpArray<number>) => {
    const env = tid();
    const q: number[] = [
      qIn.get(env * 7 + 0), qIn.get(env * 7 + 1), qIn.get(env * 7 + 2),
      qIn.get(env * 7 + 3), qIn.get(env * 7 + 4), qIn.get(env * 7 + 5),
      qIn.get(env * 7 + 6),
    ];
    const { ee, J } = frankaFkJacobianInline(q);
    const base = env * 24;
    outBuf.set(base + 0, ee[0]);
    outBuf.set(base + 1, ee[1]);
    outBuf.set(base + 2, ee[2]);
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 7; c++) {
        outBuf.set(base + 3 + r * 7 + c, J[r][c]);
      }
    }
  },
  wgsl: `
@group(0) @binding(0) var<storage, read_write> q_in:    array<f32>;
@group(0) @binding(1) var<storage, read_write> out_buf: array<f32>;

fn rot_rpy_x(r: f32) -> mat3x3<f32> {
  let cr = cos(r); let sr = sin(r);
  return mat3x3<f32>(
    vec3<f32>(1.0, 0.0, 0.0),
    vec3<f32>(0.0, cr, sr),
    vec3<f32>(0.0, -sr, cr),
  );
}

fn rot_z(angle: f32) -> mat3x3<f32> {
  let c = cos(angle); let s = sin(angle);
  return mat3x3<f32>(
    vec3<f32>(c, s, 0.0),
    vec3<f32>(-s, c, 0.0),
    vec3<f32>(0.0, 0.0, 1.0),
  );
}

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let env = gid.x;
  let n_envs = arrayLength(&out_buf) / 24u;
  if (env >= n_envs) { return; }

  let base_q = env * 7u;
  let q = array<f32, 7>(
    q_in[base_q + 0u], q_in[base_q + 1u], q_in[base_q + 2u], q_in[base_q + 3u],
    q_in[base_q + 4u], q_in[base_q + 5u], q_in[base_q + 6u],
  );

  let half_pi: f32 = 1.5707963267948966;
  let xyz = array<vec3<f32>, 7>(
    vec3<f32>(0.0,      0.0,     0.333),
    vec3<f32>(0.0,      0.0,     0.0),
    vec3<f32>(0.0,     -0.316,   0.0),
    vec3<f32>(0.0825,   0.0,     0.0),
    vec3<f32>(-0.0825,  0.384,   0.0),
    vec3<f32>(0.0,      0.0,     0.0),
    vec3<f32>(0.088,    0.0,     0.0),
  );
  let rpy_r = array<f32, 7>(0.0, -half_pi, half_pi, half_pi, -half_pi, half_pi, half_pi);

  // Pass 1: forward kinematics, store every joint's world-frame pose.
  var poses_R: array<mat3x3<f32>, 7>;
  var poses_p: array<vec3<f32>, 7>;
  var R_world = mat3x3<f32>(
    vec3<f32>(1.0, 0.0, 0.0),
    vec3<f32>(0.0, 1.0, 0.0),
    vec3<f32>(0.0, 0.0, 1.0),
  );
  var p_world = vec3<f32>(0.0, 0.0, 0.0);
  for (var i = 0u; i < 7u; i = i + 1u) {
    let R_origin = rot_rpy_x(rpy_r[i]);
    let R_q = rot_z(q[i]);
    let R_iInP = R_origin * R_q;
    let rotated = R_world * xyz[i];
    p_world = p_world + rotated;
    R_world = R_world * R_iInP;
    poses_R[i] = R_world;
    poses_p[i] = p_world;
  }

  let ee_pos = poses_p[6];
  let base_out = env * 24u;
  out_buf[base_out + 0u] = ee_pos.x;
  out_buf[base_out + 1u] = ee_pos.y;
  out_buf[base_out + 2u] = ee_pos.z;

  // Pass 2: Jacobian columns J[:,i] = axis_world_i × (p_ee - p_i)
  // axis_world_i = R_world_i · (0,0,1) = third column of R_world_i
  for (var i = 0u; i < 7u; i = i + 1u) {
    let Ri = poses_R[i];
    let a_world = vec3<f32>(Ri[2].x, Ri[2].y, Ri[2].z);
    let dp = ee_pos - poses_p[i];
    let col = vec3<f32>(
      a_world.y * dp.z - a_world.z * dp.y,
      a_world.z * dp.x - a_world.x * dp.z,
      a_world.x * dp.y - a_world.y * dp.x,
    );
    out_buf[base_out + 3u + 0u * 7u + i] = col.x;
    out_buf[base_out + 3u + 1u * 7u + i] = col.y;
    out_buf[base_out + 3u + 2u * 7u + i] = col.z;
  }
}
`,
  bindings: [
    { binding: 0, kind: "storage", inputIndex: 0, writeback: false },
    { binding: 1, kind: "storage", inputIndex: 1, writeback: true },
  ],
  workgroupSize: 64,
});

/** Reference Franka FK + linear Jacobian in pure JS. Used by
 *  frankaFkJacobianKernel's JS fallback AND callable directly.
 *  Returns { ee, J } where ee is the EE world-frame position and
 *  J is the 3×7 linear Jacobian.
 */
export function frankaFkJacobianInline(q: readonly number[]): {
  ee: [number, number, number];
  J: number[][];
} {
  // Pass 1: store per-joint world poses.
  const poses_R: number[][][] = [];
  const poses_p: [number, number, number][] = [];
  let R_world: number[][] = [[1,0,0],[0,1,0],[0,0,1]];
  let p_world: [number, number, number] = [0, 0, 0];
  for (let i = 0; i < 7; i++) {
    const R_origin = _rotRpy(_FRANKA_FK_RPY_R[i]);
    const R_q = _rotZ(q[i]);
    const R_iInP = _mat3MulSmall(R_origin, R_q);
    const rotated = _matVec3Small(R_world, _FRANKA_FK_XYZ[i]);
    p_world = [p_world[0]+rotated[0], p_world[1]+rotated[1], p_world[2]+rotated[2]];
    R_world = _mat3MulSmall(R_world, R_iInP);
    poses_R.push(R_world.map((row) => [...row]));
    poses_p.push([...p_world]);
  }
  const ee = poses_p[6];
  // Pass 2: Jacobian columns.
  const J: number[][] = [[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0]];
  for (let i = 0; i < 7; i++) {
    const Ri = poses_R[i];
    // axis_world = third column of R_world_i = R_i[:,2]
    const a: [number, number, number] = [Ri[0][2], Ri[1][2], Ri[2][2]];
    const dp: [number, number, number] = [ee[0] - poses_p[i][0], ee[1] - poses_p[i][1], ee[2] - poses_p[i][2]];
    J[0][i] = a[1] * dp[2] - a[2] * dp[1];
    J[1][i] = a[2] * dp[0] - a[0] * dp[2];
    J[2][i] = a[0] * dp[1] - a[1] * dp[0];
  }
  return { ee, J };
}

// ── Franka full DLS-IK reach (env-parallel) ──────────────────────────────
//
// All-in-one IK kernel — combines iter 88 FK + iter 89 Jacobian + the
// 3×3 cofactor DLS solve from iter 86's CPU demo. Per env, runs one
// DLS step entirely on GPU:
//
//   Pass 1: FK at q → store all 7 joint poses (R, p) in private memory
//   Pass 2: Linear Jacobian columns J[:,i] = axis_i × (p_ee - p_i)
//   Pass 3: err = target - p_ee
//   Pass 4: A = J·Jᵀ + λ²·I   (3×3)
//   Pass 5: A⁻¹ via cofactor expansion
//   Pass 6: y = A⁻¹ · err
//   Pass 7: Δq = Jᵀ · y       (7-vec)
//   Pass 8: q_new = q + α·Δq  (semi-implicit-equivalent step)
//
// Per-env input: q[7] + target[3] = 10 floats
// Per-env output: q_new[7] = 7 floats (in-place over q_in)
// Uniforms: lambda (DLS damping), alpha (step gain)
//
// Total per-thread temp memory: ~150 floats ≈ 600 bytes (well within
// per-invocation private memory limits for any WebGPU adapter).

/** Bindings:
 *    @group(0) @binding(0) q_inout    (storage read_write, N*7 floats — q is overwritten)
 *    @group(0) @binding(1) target_in  (storage read,       N*3 floats; writeback false)
 *    @group(0) @binding(2) lambda     (uniform vec4<f32>.x — DLS damping)
 *    @group(0) @binding(3) alpha      (uniform vec4<f32>.x — step gain)
 */
export const frankaReachKernel: WgpuKernel = wgpuKernel({
  js: (
    qInout: WpArray<number>,
    targetIn: WpArray<number>,
    lambda: number,
    alpha: number,
  ) => {
    const env = tid();
    const base = env * 7;
    const q = [
      qInout.get(base+0), qInout.get(base+1), qInout.get(base+2),
      qInout.get(base+3), qInout.get(base+4), qInout.get(base+5),
      qInout.get(base+6),
    ];
    const tbase = env * 3;
    const target: [number, number, number] = [
      targetIn.get(tbase+0), targetIn.get(tbase+1), targetIn.get(tbase+2),
    ];
    const qNew = frankaReachStepInline(q, target, lambda, alpha);
    for (let i = 0; i < 7; i++) qInout.set(base + i, qNew[i]);
  },
  wgsl: `
@group(0) @binding(0) var<storage, read_write> q_inout:   array<f32>;
@group(0) @binding(1) var<storage, read_write> target_in: array<f32>;
@group(0) @binding(2) var<uniform>             lambda_u:  vec4<f32>;
@group(0) @binding(3) var<uniform>             alpha_u:   vec4<f32>;

fn rot_rpy_x(r: f32) -> mat3x3<f32> {
  let cr = cos(r); let sr = sin(r);
  return mat3x3<f32>(
    vec3<f32>(1.0, 0.0, 0.0),
    vec3<f32>(0.0, cr, sr),
    vec3<f32>(0.0, -sr, cr),
  );
}

fn rot_z(angle: f32) -> mat3x3<f32> {
  let c = cos(angle); let s = sin(angle);
  return mat3x3<f32>(
    vec3<f32>(c, s, 0.0),
    vec3<f32>(-s, c, 0.0),
    vec3<f32>(0.0, 0.0, 1.0),
  );
}

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let env = gid.x;
  let n_envs = arrayLength(&q_inout) / 7u;
  if (env >= n_envs) { return; }

  let base_q = env * 7u;
  let base_t = env * 3u;
  var q = array<f32, 7>(
    q_inout[base_q + 0u], q_inout[base_q + 1u], q_inout[base_q + 2u], q_inout[base_q + 3u],
    q_inout[base_q + 4u], q_inout[base_q + 5u], q_inout[base_q + 6u],
  );
  let target = vec3<f32>(target_in[base_t + 0u], target_in[base_t + 1u], target_in[base_t + 2u]);

  let half_pi: f32 = 1.5707963267948966;
  let xyz = array<vec3<f32>, 7>(
    vec3<f32>(0.0,      0.0,     0.333),
    vec3<f32>(0.0,      0.0,     0.0),
    vec3<f32>(0.0,     -0.316,   0.0),
    vec3<f32>(0.0825,   0.0,     0.0),
    vec3<f32>(-0.0825,  0.384,   0.0),
    vec3<f32>(0.0,      0.0,     0.0),
    vec3<f32>(0.088,    0.0,     0.0),
  );
  let rpy_r = array<f32, 7>(0.0, -half_pi, half_pi, half_pi, -half_pi, half_pi, half_pi);

  // ── Pass 1: FK with stored joint poses ──
  var poses_R: array<mat3x3<f32>, 7>;
  var poses_p: array<vec3<f32>, 7>;
  var R_world = mat3x3<f32>(
    vec3<f32>(1.0, 0.0, 0.0),
    vec3<f32>(0.0, 1.0, 0.0),
    vec3<f32>(0.0, 0.0, 1.0),
  );
  var p_world = vec3<f32>(0.0, 0.0, 0.0);
  for (var i = 0u; i < 7u; i = i + 1u) {
    let R_origin = rot_rpy_x(rpy_r[i]);
    let R_q = rot_z(q[i]);
    let R_iInP = R_origin * R_q;
    let rotated = R_world * xyz[i];
    p_world = p_world + rotated;
    R_world = R_world * R_iInP;
    poses_R[i] = R_world;
    poses_p[i] = p_world;
  }
  let ee_pos = poses_p[6];

  // ── Pass 2: Linear Jacobian columns ──
  var J: array<vec3<f32>, 7>;   // 7 cols of (vx, vy, vz)
  for (var i = 0u; i < 7u; i = i + 1u) {
    let Ri = poses_R[i];
    let a_world = vec3<f32>(Ri[2].x, Ri[2].y, Ri[2].z);
    let dp = ee_pos - poses_p[i];
    J[i] = vec3<f32>(
      a_world.y * dp.z - a_world.z * dp.y,
      a_world.z * dp.x - a_world.x * dp.z,
      a_world.x * dp.y - a_world.y * dp.x,
    );
  }

  // ── Pass 3: error ──
  let err = target - ee_pos;

  // ── Pass 4: A = J·Jᵀ + λ²·I (3×3) ──
  let lam = lambda_u.x;
  let lam2 = lam * lam;
  var A00 = lam2; var A01 = 0.0; var A02 = 0.0;
  var A11 = lam2; var A12 = 0.0;
  var A22 = lam2;
  for (var i = 0u; i < 7u; i = i + 1u) {
    A00 = A00 + J[i].x * J[i].x;
    A01 = A01 + J[i].x * J[i].y;
    A02 = A02 + J[i].x * J[i].z;
    A11 = A11 + J[i].y * J[i].y;
    A12 = A12 + J[i].y * J[i].z;
    A22 = A22 + J[i].z * J[i].z;
  }
  // A is symmetric (A10 = A01, A20 = A02, A21 = A12)

  // ── Pass 5: A⁻¹ via cofactor expansion (3×3 closed form) ──
  let det = A00 * (A11 * A22 - A12 * A12)
          - A01 * (A01 * A22 - A12 * A02)
          + A02 * (A01 * A12 - A11 * A02);
  if (abs(det) < 1e-18) { return; }
  let invDet = 1.0 / det;
  let inv00 = (A11 * A22 - A12 * A12) * invDet;
  let inv01 = (A02 * A12 - A01 * A22) * invDet;
  let inv02 = (A01 * A12 - A02 * A11) * invDet;
  let inv11 = (A00 * A22 - A02 * A02) * invDet;
  let inv12 = (A02 * A01 - A00 * A12) * invDet;
  let inv22 = (A00 * A11 - A01 * A01) * invDet;

  // ── Pass 6: y = A⁻¹ · err (3-vec) ──
  let y = vec3<f32>(
    inv00 * err.x + inv01 * err.y + inv02 * err.z,
    inv01 * err.x + inv11 * err.y + inv12 * err.z,
    inv02 * err.x + inv12 * err.y + inv22 * err.z,
  );

  // ── Pass 7+8: Δq = Jᵀ · y; q_new = q + α·Δq ──
  let alpha = alpha_u.x;
  for (var i = 0u; i < 7u; i = i + 1u) {
    let dq_i = J[i].x * y.x + J[i].y * y.y + J[i].z * y.z;
    q_inout[base_q + i] = q[i] + alpha * dq_i;
  }
}
`,
  bindings: [
    { binding: 0, kind: "storage", inputIndex: 0, writeback: true },
    { binding: 1, kind: "storage", inputIndex: 1, writeback: false },
    { binding: 2, kind: "uniform", inputIndex: 2 },
    { binding: 3, kind: "uniform", inputIndex: 3 },
  ],
  workgroupSize: 64,
});

/** Reference Franka one-step DLS IK in pure JS — used by
 *  frankaReachKernel's JS fallback AND callable directly.
 *  Performs one DLS-IK step and returns the new q[7].
 */
export function frankaReachStepInline(
  q: readonly number[],
  target: readonly [number, number, number],
  lambda: number,
  alpha: number,
): number[] {
  const { ee, J } = frankaFkJacobianInline(q);
  const err: [number, number, number] = [target[0] - ee[0], target[1] - ee[1], target[2] - ee[2]];
  // A = J·Jᵀ + λ²I
  const lam2 = lambda * lambda;
  let A00 = lam2, A01 = 0, A02 = 0, A11 = lam2, A12 = 0, A22 = lam2;
  for (let i = 0; i < 7; i++) {
    A00 += J[0][i] * J[0][i];
    A01 += J[0][i] * J[1][i];
    A02 += J[0][i] * J[2][i];
    A11 += J[1][i] * J[1][i];
    A12 += J[1][i] * J[2][i];
    A22 += J[2][i] * J[2][i];
  }
  const det = A00 * (A11 * A22 - A12 * A12)
            - A01 * (A01 * A22 - A12 * A02)
            + A02 * (A01 * A12 - A11 * A02);
  if (Math.abs(det) < 1e-18) return [...q];
  const invDet = 1 / det;
  const inv00 = (A11 * A22 - A12 * A12) * invDet;
  const inv01 = (A02 * A12 - A01 * A22) * invDet;
  const inv02 = (A01 * A12 - A02 * A11) * invDet;
  const inv11 = (A00 * A22 - A02 * A02) * invDet;
  const inv12 = (A02 * A01 - A00 * A12) * invDet;
  const inv22 = (A00 * A11 - A01 * A01) * invDet;
  const y: [number, number, number] = [
    inv00 * err[0] + inv01 * err[1] + inv02 * err[2],
    inv01 * err[0] + inv11 * err[1] + inv12 * err[2],
    inv02 * err[0] + inv12 * err[1] + inv22 * err[2],
  ];
  const qNew: number[] = new Array(7);
  for (let i = 0; i < 7; i++) {
    const dq_i = J[0][i] * y[0] + J[1][i] * y[1] + J[2][i] * y[2];
    qNew[i] = q[i] + alpha * dq_i;
  }
  return qNew;
}
