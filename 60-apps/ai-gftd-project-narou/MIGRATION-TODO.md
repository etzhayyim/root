# Migration TODO — ai-gftd-project-narou

**Status**: 🔄 TRANSFORM (partial-merge) — net-new files merged from gftdcojp archive 2026-06-02.
Existing etzhayyim files were NOT overwritten (additive merge).

**Codemod pending** (substrate-boundary ADR-2605172000 / 2605172100):
- Reconcile archive-origin code with the etzhayyim rw-free/on-chain version where they overlap.
- Strip any RisingWave / fiat → AT MST + IPFS + Base L2 + USDC/ERC-4337.

## Excluded from this migration (2026-06-02)
- `ghosthacker/260208-spirit-in-physics/assets/**` binary image assets (~69 files, ~43 MB
  webp/jpg manga panels, ComfyUI-generated). Omitted to avoid bloating the public repo with
  regenerable creative output. Code + JSON-LD metadata + text sources were migrated.
  Re-add the assets here if they are required as canonical artifacts.
