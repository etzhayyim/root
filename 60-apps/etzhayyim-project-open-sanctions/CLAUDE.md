# open-sanctions CLAUDE.md

Tranche F scaffolding (Phase 2). See README.md.

## Boundary

- **etzhayyim (here)**: list mirror + lookup lexicon, read-only public data, no customer log
- **vendor**: screening service that runs against customer transactions (AML liability, customer log custody)

## NSIDs

See `00-contracts/lexicons/com/etzhayyim/sanctions/`.

## Dependencies

- AT MST + IPFS substrate (ADR-2605172000)
- Daily snapshot anchor to Base L2 (per ADR-2605171800 anchor pipeline)
- No RisingWave / Kysely / pg

## Status

Phase 2 scaffolding only.
