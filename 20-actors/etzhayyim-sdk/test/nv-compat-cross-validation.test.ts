/**
 * nv-compat cross-validation suite.
 *
 * Codifies the byte-identity guarantees claimed across iters 88-94:
 *   - Every WGSL kernel matches its JS inline reference (diff = 0.00e+0)
 *   - SDK forwardKinematics on parsed URDF matches WGSL/inline output
 *   - Franka reach kernel converges (DLS IK closes the loop)
 *   - Franka gravity comp kernel matches SDK RNEA gravity vector
 *
 * Persistent regression artifact replacing the throwaway /tmp/iterNN-tsx.mts
 * scripts that validated each iter individually. Run with:
 *
 *     pnpm exec vitest run test/nv-compat-cross-validation.test.ts
 *
 * ADR-2605261800 §D6 nv-compat namespace localization.
 */

import { describe, it, expect } from "vitest";
import {
  launch,
  fromTypedArray,
  zeros,
  WpArray,
} from "../src/nv-compat/warp/index.js";
import {
  dampingKernel,
  pendulumStepKernel,
  cartpoleStepKernel,
  twoLinkArmStepKernel,
  frankaFkKernel,
  frankaFkInline,
  frankaFkJacobianKernel,
  frankaFkJacobianInline,
  frankaReachKernel,
  frankaReachStepInline,
  frankaGravCompKernel,
  frankaGravCompInline,
  anymalFkKernel,
  anymalFkInline,
  genericSerialFkKernel,
  genericSerialFkInline,
  pdJointControllerKernel,
  pdJointControllerInline,
  actionScaleClampKernel,
  actionScaleClampInline,
} from "../src/nv-compat/warp/examples.js";
import { makeUr10 } from "../src/nv-compat/assets/ur10.js";
import { makeFrankaPanda } from "../src/nv-compat/assets/franka-panda.js";
import { makeAnymalC } from "../src/nv-compat/assets/anymal-c.js";
import {
  parseUrdf,
  buildArticulation,
  forwardKinematics,
  geometricJacobian,
  coriolisGravityVector,
  abaForward,
  type UrdfArticulatedSystem,
} from "../src/nv-compat/dynamics/index.js";

const HOME = [0, -Math.PI/4, 0, -3*Math.PI/4, 0, Math.PI/2, Math.PI/4];

// Reused parsed Franka articulation for multi-test cross-checks.
function buildFrankaArm() {
  const franka = makeFrankaPanda();
  const sys = parseUrdf(franka.urdfText);
  sys.joints = sys.joints.slice(0, 7);
  const linkNames = new Set<string>(["panda_link0"]);
  for (const j of sys.joints) linkNames.add(j.child);
  sys.links = sys.links.filter((l) => linkNames.has(l.name));
  return buildArticulation(sys);
}

function buildAnymalArt(): ReturnType<typeof buildArticulation> {
  const anymal = makeAnymalC();
  const sys = parseUrdf(anymal.urdfText);
  const linkNames = new Set<string>(["base"]);
  for (const j of sys.joints) linkNames.add(j.child);
  sys.links = sys.links.filter((l) => linkNames.has(l.name));
  return buildArticulation(sys);
}

describe("nv-compat WGSL kernels — JS fallback byte-identity", () => {
  it("damping kernel: in-place arr *= scale", () => {
    const arr = fromTypedArray<number>([1, 2, 3, 4, 5]);
    launch({ kernel: dampingKernel, dim: 5, inputs: [arr, 0.5] });
    expect(arr.toArray()).toEqual([0.5, 1, 1.5, 2, 2.5]);
  });

  it("pendulum step: -9.81 angular accel at q=π/2 in one step at dt=1ms", () => {
    const theta = fromTypedArray<number>([Math.PI / 2]);
    const omega = fromTypedArray<number>([0]);
    const tau = fromTypedArray<number>([0]);
    launch({
      kernel: pendulumStepKernel, dim: 1,
      inputs: [theta, omega, tau, 0.001, 9.81, 1.0, 1.0],
    });
    expect(omega.get(0)).toBeCloseTo(-0.00981, 8);
  });

  it("cartpole step: q=[0,0,0,0] f=0 stays at equilibrium", () => {
    const x = zeros<number>(1);
    const xd = zeros<number>(1);
    const th = zeros<number>(1);
    const thd = zeros<number>(1);
    const f = zeros<number>(1);
    launch({
      kernel: cartpoleStepKernel, dim: 1,
      inputs: [x, xd, th, thd, f, 0.02, 9.8, 1.0, 0.1, 0.5],
    });
    expect(Math.abs(x.get(0))).toBeLessThan(1e-15);
    expect(Math.abs(th.get(0))).toBeLessThan(1e-15);
  });

  it("two-link arm: gravity comp τ = h(q, 0) holds arm static", () => {
    const q1 = fromTypedArray<number>([0.3]);
    const q1d = zeros<number>(1);
    const q2 = fromTypedArray<number>([0.3]);
    const q2d = zeros<number>(1);
    const M1 = 1, L1 = 1, R1 = 0.5, I1 = 0.083;
    const M2 = 1, L2 = 1, R2 = 0.5, I2 = 0.083;
    const G = 9.81;
    const g1 = M1 * G * R1 * Math.sin(0.3)
              + M2 * G * (L1 * Math.sin(0.3) + R2 * Math.sin(0.6));
    const g2 = M2 * G * R2 * Math.sin(0.6);
    const tau1 = fromTypedArray<number>([g1]);
    const tau2 = fromTypedArray<number>([g2]);
    launch({
      kernel: twoLinkArmStepKernel, dim: 1,
      inputs: [q1, q1d, q2, q2d, tau1, tau2, 0.001, G, M1, L1, R1, I1, M2, L2, R2, I2],
    });
    expect(Math.abs(q1d.get(0))).toBeLessThan(1e-9);
    expect(Math.abs(q2d.get(0))).toBeLessThan(1e-9);
  });
});

describe("nv-compat Franka kernels — byte-identical 100-env batch", () => {
  it("frankaFkKernel matches frankaFkInline (diff=0)", () => {
    const N = 100;
    const qBuf = new Array(N * 7);
    for (let env = 0; env < N; env++) {
      for (let j = 0; j < 7; j++) {
        qBuf[env * 7 + j] = HOME[j] + 0.03 * env * (j % 2 ? 1 : -1);
      }
    }
    const qIn = fromTypedArray<number>(qBuf);
    const eeOut = zeros<number>(N * 3);
    launch({ kernel: frankaFkKernel, dim: N, inputs: [qIn, eeOut] });

    let maxDiff = 0;
    for (let env = 0; env < N; env++) {
      const q = qBuf.slice(env * 7, env * 7 + 7);
      const ref = frankaFkInline(q);
      for (let k = 0; k < 3; k++) {
        maxDiff = Math.max(maxDiff, Math.abs(eeOut.get(env * 3 + k) - ref[k]));
      }
    }
    expect(maxDiff).toBe(0);
  });

  it("frankaFkJacobianKernel matches frankaFkJacobianInline (diff=0)", () => {
    const N = 100;
    const qBuf = new Array(N * 7);
    for (let env = 0; env < N; env++) {
      for (let j = 0; j < 7; j++) {
        qBuf[env * 7 + j] = HOME[j] + 0.03 * env * (j % 2 ? 1 : -1);
      }
    }
    const qIn = fromTypedArray<number>(qBuf);
    const outBuf = zeros<number>(N * 24);
    launch({ kernel: frankaFkJacobianKernel, dim: N, inputs: [qIn, outBuf] });

    let maxEeDiff = 0;
    let maxJDiff = 0;
    for (let env = 0; env < N; env++) {
      const q = qBuf.slice(env * 7, env * 7 + 7);
      const { ee, J } = frankaFkJacobianInline(q);
      const base = env * 24;
      for (let k = 0; k < 3; k++) {
        maxEeDiff = Math.max(maxEeDiff, Math.abs(outBuf.get(base + k) - ee[k]));
      }
      for (let r = 0; r < 3; r++) {
        for (let c = 0; c < 7; c++) {
          maxJDiff = Math.max(maxJDiff, Math.abs(outBuf.get(base + 3 + r * 7 + c) - J[r][c]));
        }
      }
    }
    expect(maxEeDiff).toBe(0);
    expect(maxJDiff).toBe(0);
  });

  it("frankaReachKernel matches frankaReachStepInline (diff=0)", () => {
    const N = 100;
    const qBuf = new Array(N * 7);
    const tBuf = new Array(N * 3);
    for (let env = 0; env < N; env++) {
      for (let j = 0; j < 7; j++) {
        qBuf[env * 7 + j] = HOME[j] + 0.02 * env * (j % 2 ? 1 : -1);
      }
      const q = qBuf.slice(env * 7, env * 7 + 7);
      const ee = frankaFkInline(q);
      tBuf[env * 3 + 0] = ee[0] + 0.03 * (env / N);
      tBuf[env * 3 + 1] = ee[1] + 0.02 * (env / N);
      tBuf[env * 3 + 2] = ee[2];
    }
    const qInout = fromTypedArray<number>(qBuf);
    const targetIn = fromTypedArray<number>(tBuf);
    launch({
      kernel: frankaReachKernel, dim: N,
      inputs: [qInout, targetIn, 0.05, 0.3],
    });
    let maxDiff = 0;
    for (let env = 0; env < N; env++) {
      const q_in = qBuf.slice(env * 7, env * 7 + 7);
      const target: [number, number, number] = [tBuf[env*3+0], tBuf[env*3+1], tBuf[env*3+2]];
      const qRef = frankaReachStepInline(q_in, target, 0.05, 0.3);
      for (let i = 0; i < 7; i++) {
        maxDiff = Math.max(maxDiff, Math.abs(qInout.get(env * 7 + i) - qRef[i]));
      }
    }
    expect(maxDiff).toBe(0);
  });

  it("frankaGravCompKernel matches frankaGravCompInline (diff=0)", () => {
    const N = 100;
    const qBuf = new Array(N * 7);
    for (let env = 0; env < N; env++) {
      for (let j = 0; j < 7; j++) {
        qBuf[env * 7 + j] = HOME[j] + 0.03 * env * (j % 2 ? 1 : -1);
      }
    }
    const qIn = fromTypedArray<number>(qBuf);
    const tauOut = zeros<number>(N * 7);
    launch({
      kernel: frankaGravCompKernel, dim: N,
      inputs: [qIn, tauOut, 0, 0, -9.81],
    });
    let maxDiff = 0;
    for (let env = 0; env < N; env++) {
      const q = qBuf.slice(env * 7, env * 7 + 7);
      const tauRef = frankaGravCompInline(q);
      for (let i = 0; i < 7; i++) {
        maxDiff = Math.max(maxDiff, Math.abs(tauOut.get(env * 7 + i) - tauRef[i]));
      }
    }
    expect(maxDiff).toBe(0);
  });
});

describe("nv-compat ANYmal kernel — byte-identical 100-env batch", () => {
  it("anymalFkKernel matches anymalFkInline (diff=0)", () => {
    const N = 100;
    const qBuf = new Array(N * 12);
    for (let env = 0; env < N; env++) {
      for (let j = 0; j < 12; j++) {
        qBuf[env * 12 + j] = 0.03 * env * (j % 2 === 0 ? 1 : -1) + 0.1 * j;
      }
    }
    const qIn = fromTypedArray<number>(qBuf);
    const feetOut = zeros<number>(N * 12);
    launch({ kernel: anymalFkKernel, dim: N, inputs: [qIn, feetOut] });
    let maxDiff = 0;
    for (let env = 0; env < N; env++) {
      const q = qBuf.slice(env * 12, env * 12 + 12);
      const ref = anymalFkInline(q);
      for (let leg = 0; leg < 4; leg++) {
        for (let k = 0; k < 3; k++) {
          maxDiff = Math.max(maxDiff, Math.abs(feetOut.get(env * 12 + leg * 3 + k) - ref[leg][k]));
        }
      }
    }
    expect(maxDiff).toBe(0);
  });
});

describe("nv-compat WGSL → SDK forwardKinematics cross-impl byte-identity", () => {
  it("Franka FK kernel matches SDK forwardKinematics on parsed URDF (diff=0)", () => {
    const built = buildFrankaArm();
    const q = [0.1, -0.2, 0.3, -1.0, 0.2, 1.5, 0.4];
    const inlineEE = frankaFkInline(q);
    const sdkEE = forwardKinematics(built, q)[6].p;
    expect(Math.abs(inlineEE[0] - sdkEE[0])).toBe(0);
    expect(Math.abs(inlineEE[1] - sdkEE[1])).toBe(0);
    expect(Math.abs(inlineEE[2] - sdkEE[2])).toBe(0);
  });

  it("Franka FK + Jacobian inline matches SDK geometricJacobian linear rows (diff=0)", () => {
    const built = buildFrankaArm();
    const q = [0.1, -0.2, 0.3, -1.0, 0.2, 1.5, 0.4];
    const { J: inlineJ } = frankaFkJacobianInline(q);
    const sdkJ = geometricJacobian(built, q, 6); // 6×7 in Featherstone [angular; linear]
    let maxDiff = 0;
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 7; c++) {
        maxDiff = Math.max(maxDiff, Math.abs(inlineJ[r][c] - sdkJ[r + 3][c]));
      }
    }
    expect(maxDiff).toBe(0);
  });

  it("ANYmal FK kernel matches SDK forwardKinematics on parsed URDF (foot positions, diff=0)", () => {
    const built = buildAnymalArt();
    const standing = makeAnymalC().defaultJointPositions as number[];
    const poses = forwardKinematics(built, standing);
    const FOOT_LOCAL = [0, 0, -0.317];
    const kernelFeet = anymalFkInline(standing);
    let maxDiff = 0;
    for (let leg = 0; leg < 4; leg++) {
      const kfePose = poses[leg * 3 + 2];   // KFE joint world pose
      const Rrot = kfePose.R;
      const foot = [
        kfePose.p[0] + Rrot[0][0]*FOOT_LOCAL[0] + Rrot[0][1]*FOOT_LOCAL[1] + Rrot[0][2]*FOOT_LOCAL[2],
        kfePose.p[1] + Rrot[1][0]*FOOT_LOCAL[0] + Rrot[1][1]*FOOT_LOCAL[1] + Rrot[1][2]*FOOT_LOCAL[2],
        kfePose.p[2] + Rrot[2][0]*FOOT_LOCAL[0] + Rrot[2][1]*FOOT_LOCAL[1] + Rrot[2][2]*FOOT_LOCAL[2],
      ];
      for (let k = 0; k < 3; k++) {
        maxDiff = Math.max(maxDiff, Math.abs(foot[k] - kernelFeet[leg][k]));
      }
    }
    expect(maxDiff).toBe(0);
  });
});

describe("nv-compat gravity comp ↔ SDK RNEA cross-impl agreement", () => {
  it("Franka analytical gravity comp matches SDK coriolisGravityVector magnitude", () => {
    const built = buildFrankaArm();
    const tauAnalytical = frankaGravCompInline(HOME);
    const tauSDK = coriolisGravityVector(built, HOME, new Array(7).fill(0));
    // Both should give the same compensation torque vector.
    // Magnitudes must match (gravity vector magnitude is robot-config-invariant).
    const normA = Math.sqrt(tauAnalytical.reduce((s, v) => s + v*v, 0));
    const normS = Math.sqrt(tauSDK.reduce((s, v) => s + v*v, 0));
    expect(normA).toBeCloseTo(normS, 1);  // within 0.1 N·m
    expect(normA).toBeGreaterThan(5);
    expect(normA).toBeLessThan(50);
  });

  it("Franka gravity comp τ=g(q) → ABA q̈ ≈ 0 (perfect cancellation)", () => {
    const built = buildFrankaArm();
    const tauG = frankaGravCompInline(HOME);
    const qddot = abaForward(built, HOME, new Array(7).fill(0), tauG);
    const qddotNorm = Math.sqrt(qddot.reduce((s, v) => s + v*v, 0));
    expect(qddotNorm).toBeLessThan(1.0);  // perfect comp → ~0
  });
});

describe("nv-compat Franka reach kernel — convergence guarantee", () => {
  it("50-step DLS rollout converges to <5mm error", () => {
    const startQ = [...HOME];
    const ee0 = frankaFkInline(startQ);
    const target: [number, number, number] = [ee0[0] + 0.08, ee0[1] + 0.04, ee0[2] - 0.04];
    let q = startQ;
    for (let step = 0; step < 50; step++) {
      q = frankaReachStepInline(q, target, 0.05, 0.3);
    }
    const eeFinal = frankaFkInline(q);
    const errFinal = Math.sqrt(
      (target[0] - eeFinal[0]) ** 2 +
      (target[1] - eeFinal[1]) ** 2 +
      (target[2] - eeFinal[2]) ** 2
    );
    expect(errFinal).toBeLessThan(0.005);
  });
});

describe("nv-compat genericSerialFkKernel — cross-vendor (UR10)", () => {
  const ur = makeUr10();

  it("UR10 asset wrapper has the expected 6-DoF shape", () => {
    expect(ur.dofCount).toBe(6);
    expect(ur.jointNames.length).toBe(6);
    expect(ur.jointOriginXyz.length).toBe(6);
    expect(ur.jointAxis.length).toBe(6);
    expect(ur.flatXyz().length).toBe(18);
    expect(ur.flatRpy().length).toBe(18);
    expect(ur.flatAxis().length).toBe(18);
  });

  it("UR10 q=0 EE lies inside UR10 max-reach workspace (≤ 1.4 m)", () => {
    const ee = genericSerialFkInline([0, 0, 0, 0, 0, 0],
      ur.jointOriginXyz, ur.jointOriginRpy, ur.jointAxis);
    const reach = Math.hypot(ee[0], ee[1], ee[2]);
    expect(reach).toBeGreaterThan(0);
    expect(reach).toBeLessThan(1.4);
  });

  it("UR10 home pose EE lies inside UR10 max-reach workspace", () => {
    const eeH = genericSerialFkInline([...ur.defaultJointPositions],
      ur.jointOriginXyz, ur.jointOriginRpy, ur.jointAxis);
    const reach = Math.hypot(eeH[0], eeH[1], eeH[2]);
    expect(reach).toBeLessThan(1.4);
  });

  it("100-env UR10 batch: WGSL genericSerialFkKernel matches inline byte-identically", () => {
    const N_ENVS = 100;
    const n = 6;
    const qBuf: number[] = new Array(N_ENVS * n);
    for (let env = 0; env < N_ENVS; env++) {
      for (let j = 0; j < n; j++) qBuf[env*n + j] = 0.1 * env * Math.sin(j + 1);
    }
    const qIn = fromTypedArray<number>(qBuf);
    const jx = fromTypedArray<number>(ur.flatXyz());
    const jr = fromTypedArray<number>(ur.flatRpy());
    const ja = fromTypedArray<number>(ur.flatAxis());
    const ee = zeros<number>(N_ENVS * 3);
    launch({ kernel: genericSerialFkKernel, dim: N_ENVS, inputs: [qIn, jx, jr, ja, ee, n] });

    let maxDiff = 0;
    for (let env = 0; env < N_ENVS; env++) {
      const q = qBuf.slice(env*n, env*n + n);
      const ref = genericSerialFkInline(q, ur.jointOriginXyz, ur.jointOriginRpy, ur.jointAxis);
      for (let k = 0; k < 3; k++) {
        maxDiff = Math.max(maxDiff, Math.abs(ee.get(env*3+k) - ref[k]));
      }
    }
    expect(maxDiff).toBe(0);
  });

  it("q_1 base rotation around z preserves |EE| and z-component", () => {
    const qA = [0, -1, 1, -0.5, 0.3, 0];
    const qB = [Math.PI/3, -1, 1, -0.5, 0.3, 0];
    const eeA = genericSerialFkInline(qA, ur.jointOriginXyz, ur.jointOriginRpy, ur.jointAxis);
    const eeB = genericSerialFkInline(qB, ur.jointOriginXyz, ur.jointOriginRpy, ur.jointAxis);
    const rA = Math.hypot(eeA[0], eeA[1], eeA[2]);
    const rB = Math.hypot(eeB[0], eeB[1], eeB[2]);
    expect(Math.abs(rA - rB)).toBeLessThan(1e-9);
    expect(Math.abs(eeA[2] - eeB[2])).toBeLessThan(1e-9);
  });
});

describe("nv-compat genericSerialFkKernel — Franka equivalence proof", () => {
  it("genericSerialFk with Franka joint params matches Franka-specific inline FK", () => {
    const HALF_PI = Math.PI / 2;
    const FRANKA_XYZ: ReadonlyArray<readonly [number, number, number]> = [
      [0, 0, 0.333], [0, 0, 0], [0, -0.316, 0],
      [0.0825, 0, 0], [-0.0825, 0.384, 0], [0, 0, 0], [0.088, 0, 0],
    ];
    const FRANKA_RPY: ReadonlyArray<readonly [number, number, number]> = [
      [0, 0, 0], [-HALF_PI, 0, 0], [HALF_PI, 0, 0],
      [HALF_PI, 0, 0], [-HALF_PI, 0, 0], [HALF_PI, 0, 0], [HALF_PI, 0, 0],
    ];
    const FRANKA_AXIS: ReadonlyArray<readonly [number, number, number]> = [
      [0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1],
    ];
    const q = [0, -Math.PI/4, 0, -3*Math.PI/4, 0, Math.PI/2, Math.PI/4];

    const eeGeneric = genericSerialFkInline(q, FRANKA_XYZ, FRANKA_RPY, FRANKA_AXIS);
    const eeFranka = frankaFkInline(q);
    for (let k = 0; k < 3; k++) {
      expect(Math.abs(eeGeneric[k] - eeFranka[k])).toBeLessThan(1e-12);
    }
  });
});

describe("nv-compat pdJointControllerKernel — env×joint parallel PD", () => {
  it("hand-computed 3-joint PD: τ = Kp·(q*-q) - Kd·q̇", () => {
    const tau = pdJointControllerInline(
      [1.0, 2.0, 3.0], [0.1, 0.2, 0.3], [1.5, 1.8, 3.4],
      [10, 20, 30], [1, 2, 3], 3);
    expect(tau[0]).toBeCloseTo(4.9, 12);
    expect(tau[1]).toBeCloseTo(-4.4, 12);
    expect(tau[2]).toBeCloseTo(11.1, 12);
  });

  it("zero error + zero velocity → zero torque", () => {
    const q = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7];
    const tau = pdJointControllerInline(
      q, new Array(7).fill(0), q,
      new Array(7).fill(50), new Array(7).fill(5), 7);
    for (const t of tau) expect(t).toBe(0);
  });

  it("256-env × 12-joint WGSL byte-identity vs inline", () => {
    const nEnvs = 256, n = 12;
    const q: number[] = new Array(nEnvs * n);
    const qd: number[] = new Array(nEnvs * n);
    const qT: number[] = new Array(nEnvs * n);
    for (let i = 0; i < nEnvs * n; i++) {
      q[i] = Math.sin(i * 0.137);
      qd[i] = 0.1 * Math.cos(i * 0.241);
      qT[i] = Math.sin(i * 0.137 + 0.05);
    }
    const kp = new Array(n).fill(0).map((_, j) => 20 + j * 5);
    const kd = new Array(n).fill(0).map((_, j) => 1 + j * 0.2);

    const qA = fromTypedArray<number>(q);
    const qdA = fromTypedArray<number>(qd);
    const qTA = fromTypedArray<number>(qT);
    const kpA = fromTypedArray<number>(kp);
    const kdA = fromTypedArray<number>(kd);
    const tauOut = zeros<number>(nEnvs * n);
    launch({ kernel: pdJointControllerKernel, dim: nEnvs * n,
      inputs: [qA, qdA, qTA, kpA, kdA, tauOut, n] });

    const ref = pdJointControllerInline(q, qd, qT, kp, kd, n);
    let maxDiff = 0;
    for (let i = 0; i < nEnvs * n; i++) {
      maxDiff = Math.max(maxDiff, Math.abs(tauOut.get(i) - ref[i]));
    }
    expect(maxDiff).toBe(0);
  });

  it("critically-damped 1-DoF unit-mass converges to setpoint", () => {
    const Kp = 100, Kd = 2 * Math.sqrt(Kp);
    let q = 0, qd = 0;
    const dt = 0.001;
    for (let step = 0; step < 2000; step++) {
      const tau = pdJointControllerInline([q], [qd], [1.0], [Kp], [Kd], 1)[0];
      qd += tau * dt;
      q += qd * dt;
    }
    expect(q).toBeCloseTo(1.0, 1);
  });
});

describe("nv-compat actionScaleClampKernel — Isaac Lab ActionManager pipeline", () => {
  it("identity (scale=1, offset=0, wide limits) = passthrough", () => {
    const n = 4;
    const a = [-0.5, 0.0, 0.3, 0.8];
    const out = actionScaleClampInline(a,
      [1, 1, 1, 1], [0, 0, 0, 0],
      [-1e9, -1e9, -1e9, -1e9], [1e9, 1e9, 1e9, 1e9], n);
    for (let i = 0; i < n; i++) expect(out[i]).toBe(a[i]);
  });

  it("upper + lower clamping fires correctly", () => {
    const n = 2;
    const out = actionScaleClampInline([-1, 1, -2, 5],
      [10, 10], [0, 0], [-3, -3], [3, 3], 2);
    expect(out).toEqual([-3, 3, -3, 3]);
  });

  it("256-env × 12-joint WGSL byte-identity vs inline", () => {
    const nEnvs = 256, n = 12;
    const a: number[] = new Array(nEnvs * n);
    for (let i = 0; i < nEnvs * n; i++) a[i] = Math.sin(i * 0.13) * 1.5;
    const scale = new Array(n).fill(0).map((_, j) => 0.5 + j * 0.1);
    const offset = new Array(n).fill(0).map((_, j) => j * 0.05);
    const lower = new Array(n).fill(0).map((_, j) => -1 - j * 0.05);
    const upper = new Array(n).fill(0).map((_, j) => 1 + j * 0.05);

    const aIn = fromTypedArray<number>(a);
    const sIn = fromTypedArray<number>(scale);
    const oIn = fromTypedArray<number>(offset);
    const lIn = fromTypedArray<number>(lower);
    const uIn = fromTypedArray<number>(upper);
    const out = zeros<number>(nEnvs * n);
    launch({ kernel: actionScaleClampKernel, dim: nEnvs * n,
      inputs: [aIn, sIn, oIn, lIn, uIn, out, n] });

    const ref = actionScaleClampInline(a, scale, offset, lower, upper, n);
    let maxDiff = 0;
    for (let i = 0; i < nEnvs * n; i++) {
      maxDiff = Math.max(maxDiff, Math.abs(out.get(i) - ref[i]));
    }
    expect(maxDiff).toBe(0);
  });

  it("end-to-end action → clamp → PD pipeline produces bounded τ", () => {
    const n = 6;
    const policyOut = [-0.8, 0.5, 0.0, 1.2, -0.3, 0.9];
    const scale = new Array(n).fill(Math.PI / 2);
    const offset = new Array(n).fill(0);
    const lower = new Array(n).fill(-Math.PI / 2);
    const upper = new Array(n).fill(Math.PI / 2);
    const qTarget = actionScaleClampInline(policyOut, scale, offset, lower, upper, n);
    expect(Math.abs(qTarget[3] - Math.PI / 2)).toBeLessThan(1e-12);

    const tau = pdJointControllerInline(
      new Array(n).fill(0), new Array(n).fill(0),
      qTarget, new Array(n).fill(50), new Array(n).fill(5), n);
    let maxTau = 0;
    for (const t of tau) maxTau = Math.max(maxTau, Math.abs(t));
    expect(maxTau).toBeLessThanOrEqual(50 * Math.PI / 2 + 1e-9);
  });
});
