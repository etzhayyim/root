// @etzhayyim/sdk/nv-compat
// NVIDIA Omniverse stack public-API drop-in compat facade.
// R1.0 path reservation per ADR-2605261800; first implementation
// surface (dynamics) landed iter 71 as TypeScript port of the Python
// nv_compat reference impl (iter 68-70).
// See README.md for trademark notice and sub-phase delivery plan.

export * as dynamics from "./dynamics/index.js";
export * as controllers from "./controllers/index.js";
export * as actions from "./actions/index.js";
export * as assets from "./assets/index.js";
export * as warp from "./warp/index.js";
export * as policies from "./policies/index.js";

export const ADR = "ADR-2605261800";
export const PHASE = "R1.7-wgpu-backend";

export const NV_COMPAT_MAP: Readonly<Record<string, string>> = Object.freeze({
  "Omniverse Kit":     "amenominaka",
  "Nucleus":           "kotoba-datomic-nucleus",
  "Isaac Sim":         "e7m-sim",
  "Isaac Lab":         "e7m-shugyo",
  "OptiX":             "hikari-rt",
  "RTX Renderer":      "kami-rtx",
  "Replicator":        "utsushimi",
  "DriveSim":          "wadachi-sim",
  "Omniverse Cloud":   "murakumo-render",
});
