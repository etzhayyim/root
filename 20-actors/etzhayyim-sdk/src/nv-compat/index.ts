// @etzhayyim/sdk/nv-compat
// NVIDIA Omniverse stack public-API drop-in compat facade.
// R1.0 path reservation per ADR-2605261800.
// See README.md for trademark notice and sub-phase delivery plan.

export const ADR = "ADR-2605261800";
export const PHASE = "R1.0-path-reservation";

export const NV_COMPAT_MAP: Readonly<Record<string, string>> = Object.freeze({
  "Omniverse Kit":     "amenominaka",
  "Nucleus":           "yatachain-nucleus",
  "Isaac Sim":         "e7m-sim",
  "Isaac Lab":         "e7m-shugyo",
  "OptiX":             "hikari-rt",
  "RTX Renderer":      "kami-rtx",
  "Replicator":        "utsushimi",
  "DriveSim":          "wadachi-sim",
  "Omniverse Cloud":   "murakumo-render",
});
