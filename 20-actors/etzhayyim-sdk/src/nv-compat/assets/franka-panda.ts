// TypeScript port of pymagatama.nv_compat.isaacsim.assets.franka_panda
//
// Franka Emika Panda asset wrapper — 7-DoF arm + 2-finger gripper (9 DoF).
//
// Specs sourced from the public Franka Robotics FCI documentation
// (frankarobotics.github.io/docs/control_parameters.html — joint
// ranges, velocity limits, effort limits) and the publicly-distributed
// Franka URDF (github.com/frankaemika/franka_ros, Apache 2.0). No
// proprietary content (no mesh references, no Isaac Sim USD refs);
// the URDF is a minimal kinematic-chain reproduction with unit-mass
// placeholder inertias so the wrapper is self-contained and substrate-
// publishable.
//
// Trademark: "Franka Emika" and "Panda" are trademarks of Franka
// Robotics GmbH; this wrapper is API namespace localization only
// (matching the public FCI spec — Google v. Oracle 2021 API fair use).
//
// ADR-2605261800 §D6.

import { buildSerialChainUrdf, type UrdfJointSpec } from "./urdf-builder.js";

// Joint specs from public Franka FCI documentation.
const PANDA_ARM_JOINTS: ReadonlyArray<{
  name: string;
  lower: number;
  upper: number;
  velocity: number;
  effort: number;
}> = [
  { name: "panda_joint1", lower: -2.8973, upper: 2.8973, velocity: 2.1750, effort: 87 },
  { name: "panda_joint2", lower: -1.7628, upper: 1.7628, velocity: 2.1750, effort: 87 },
  { name: "panda_joint3", lower: -2.8973, upper: 2.8973, velocity: 2.1750, effort: 87 },
  { name: "panda_joint4", lower: -3.0718, upper: -0.0698, velocity: 2.1750, effort: 87 },
  { name: "panda_joint5", lower: -2.8973, upper: 2.8973, velocity: 2.6100, effort: 12 },
  { name: "panda_joint6", lower: -0.0175, upper: 3.7525, velocity: 2.6100, effort: 12 },
  { name: "panda_joint7", lower: -2.8973, upper: 2.8973, velocity: 2.6100, effort: 12 },
];

const PANDA_FINGER_JOINTS: ReadonlyArray<{
  name: string;
  lower: number;
  upper: number;
  velocity: number;
  effort: number;
}> = [
  { name: "panda_finger_joint1", lower: 0, upper: 0.04, velocity: 0.2, effort: 20 },
  { name: "panda_finger_joint2", lower: 0, upper: 0.04, velocity: 0.2, effort: 20 },
];

function buildFrankaUrdf(): string {
  const joints: UrdfJointSpec[] = [];
  for (const j of PANDA_ARM_JOINTS) {
    joints.push({
      name: j.name,
      type: "revolute",
      axis: [0, 0, 1],
      lower: j.lower,
      upper: j.upper,
      velocity: j.velocity,
      effort: j.effort,
      originXyz: [0, 0, 0.1],
    });
  }
  for (const j of PANDA_FINGER_JOINTS) {
    joints.push({
      name: j.name,
      type: "prismatic",
      axis: [0, 1, 0],
      lower: j.lower,
      upper: j.upper,
      velocity: j.velocity,
      effort: j.effort,
      originXyz: [0, 0, 0.05],
    });
  }
  return buildSerialChainUrdf("panda", joints);
}

/** Franka Panda 9-DoF asset. Pairs directly with iter 72 DiffIK (arm 7-DoF)
 *  / iter 73 OSC (arm 7-DoF) / iter 74 DifferentialInverseKinematicsAction
 *  (arm) / iter 74 BinaryJointPositionAction (gripper).
 */
export interface FrankaPanda {
  primPath: string;
  name: string;
  urdfText: string;
  jointNames: readonly string[];
  armJointNames: readonly string[];
  fingerJointNames: readonly string[];
  dofCount: number;
  armDofCount: number;
  fingerDofCount: number;
  defaultJointPositions: readonly number[];
  defaultJointVelocities: readonly number[];
  jointLowerLimits: readonly number[];
  jointUpperLimits: readonly number[];
  jointVelocityLimits: readonly number[];
  effortLimits: readonly number[];
  gripperOpenCommand: readonly [number, number];
  gripperCloseCommand: readonly [number, number];
  eeLinkName: string;
  homePose(): readonly number[];
  armIndices(): readonly [number, number, number, number, number, number, number];
  fingerIndices(): readonly [number, number];
}

export function makeFrankaPanda(opts: Partial<{ primPath: string; name: string }> = {}): FrankaPanda {
  const primPath = opts.primPath ?? "/World/Franka";
  const name = opts.name ?? "franka_panda";
  const armJointNames = PANDA_ARM_JOINTS.map((j) => j.name);
  const fingerJointNames = PANDA_FINGER_JOINTS.map((j) => j.name);
  const jointNamesAll = [...armJointNames, ...fingerJointNames] as const;
  // Canonical Franka "home" pose (arm) + open gripper.
  const defaultJointPositions: readonly number[] = [
    0, -0.7854, 0, -2.3562, 0, 1.5708, 0.7854,
    0.04, 0.04,
  ];
  const defaultJointVelocities: readonly number[] = new Array(9).fill(0);
  const jointLowerLimits: readonly number[] = [
    ...PANDA_ARM_JOINTS.map((j) => j.lower),
    ...PANDA_FINGER_JOINTS.map((j) => j.lower),
  ];
  const jointUpperLimits: readonly number[] = [
    ...PANDA_ARM_JOINTS.map((j) => j.upper),
    ...PANDA_FINGER_JOINTS.map((j) => j.upper),
  ];
  const jointVelocityLimits: readonly number[] = [
    ...PANDA_ARM_JOINTS.map((j) => j.velocity),
    ...PANDA_FINGER_JOINTS.map((j) => j.velocity),
  ];
  const effortLimits: readonly number[] = [
    ...PANDA_ARM_JOINTS.map((j) => j.effort),
    ...PANDA_FINGER_JOINTS.map((j) => j.effort),
  ];

  return {
    primPath,
    name,
    urdfText: buildFrankaUrdf(),
    jointNames: jointNamesAll,
    armJointNames,
    fingerJointNames,
    dofCount: 9,
    armDofCount: 7,
    fingerDofCount: 2,
    defaultJointPositions,
    defaultJointVelocities,
    jointLowerLimits,
    jointUpperLimits,
    jointVelocityLimits,
    effortLimits,
    gripperOpenCommand: [0.04, 0.04],
    gripperCloseCommand: [0, 0],
    eeLinkName: "panda_hand",
    homePose() {
      return defaultJointPositions;
    },
    armIndices() {
      return [0, 1, 2, 3, 4, 5, 6] as const;
    },
    fingerIndices() {
      return [7, 8] as const;
    },
  };
}
