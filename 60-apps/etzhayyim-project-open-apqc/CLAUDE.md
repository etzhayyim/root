# open-apqc CLAUDE.md

Tranche F scaffolding (Phase 2). See README.md.

## Boundary

- **etzhayyim (here)**: PCF reference catalog + BPMN task catalog + projection spec + open lexicons
- **vendor** (`etzhayyim/etzhayyim-root`): customer-specific mappings, RisingWave projector runtime, tenant deploys

## NSIDs

See `orgs/etzhayyim/com-etzhayyim-apqc/lex/`.

## Dependencies

- AT MST + IPFS substrate (ADR-2605172000) — no RisingWave, no Kysely, no pg imports
- On-chain payment for any paid feature (ADR-2605172100) — no Stripe / PayPal / fiat

## Status

Phase 2 scaffolding only. Phase 3 content copy is a separate work item.
