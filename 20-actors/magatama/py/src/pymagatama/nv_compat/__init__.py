"""pymagatama.nv_compat — NVIDIA Omniverse stack public-API drop-in compat facade.

R1.0 path reservation per ADR-2605261800.
See README.md for trademark notice and sub-phase delivery plan.

Canonical implementations live in 40-engine/kami-engine/ (WebGPU + WASM):
  Omniverse Kit  → amenominaka
  Nucleus        → yatachain-nucleus
  Isaac Sim      → e7m-sim
  Isaac Lab      → e7m-shugyo
  OptiX          → hikari-rt
  RTX Renderer   → kami-rtx
  Replicator     → utsushimi
  DriveSim       → wadachi-sim
  Omniverse Cloud→ murakumo-render
"""

ADR = "ADR-2605261800"
PHASE = "R1.0-path-reservation"

NV_COMPAT_MAP = {
    "Omniverse Kit":   "amenominaka",
    "Nucleus":         "yatachain-nucleus",
    "Isaac Sim":       "e7m-sim",
    "Isaac Lab":       "e7m-shugyo",
    "OptiX":           "hikari-rt",
    "RTX Renderer":    "kami-rtx",
    "Replicator":      "utsushimi",
    "DriveSim":        "wadachi-sim",
    "Omniverse Cloud": "murakumo-render",
}
