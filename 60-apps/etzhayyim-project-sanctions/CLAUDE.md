# etzhayyim-project-sanctions — OFAC + EU + UN + JP-MOF Sanctions Screening

> **T2 Logical Actor**: Manifest-driven (`20-actors/sanctions/actor-manifest.jsonld`).

`sanctions.etzhayyim.com` (nanoid: `sn4c8t1x`) — 50K sanctioned entities across OFAC SDN + EU consolidated + UN Security Council + JP MOF + UK OFSI + AU DFAT + CA OSFI.

## Lexicons
`sanctions/` (5 files): screening + ingestion procedures.

## cross-actor
- `yabai` — AML investigation escalation
- `malak` — CTI fusion
- `legal-entity` — corporate match (LEI lookup)
- `crypto-asset-freeze` — LE escalation if wallet hit
- `oil-shipping` — tanker dark-fleet screening
- `business-person` — PEP screening

## Governance
- daily refresh SLA (≤24h, alert if >48h)
- screen-every-call writes OCEL audit event
- authoritative source only (treasury.gov/eur-lex/un.org/mof.go.jp 等)

## Design
→ ADR-0013: 海運 + エネルギー クラスタ cross-actor (sanctions escalation chain)
