# etzhayyim-project-crypto-asset-freeze — Blockchain Freeze LE Coordination

> **T2 Logical Actor**: Manifest-driven (`20-actors/crypto-asset-freeze/actor-manifest.jsonld`). **Restricted: LE-only**.

`crypto-asset-freeze.etzhayyim.com` (nanoid: `qjp7mjyb`) — 100K LE-grade incidents. Issuer-level (Tether/Circle), CEX wallet, smart contract pause coordination.

## Lexicons
`cryptoAssetFreeze/` (5 files): createIncident, requestFreeze, traceWallet, getIncident, listIncidents.

## cross-actor
- `sanctions` — OFAC SDN match trigger
- `malak` — CTI indicator fusion
- `yabai` — AML investigation
- `legal-aid` — due process notification (jurisdiction-required)

## Governance (LE-only)
- requestFreeze: caller DID `performer.role=law-enforcement` 必須 + HAR per incident
- cryptographic audit chain: court order CID + LE agency DID 署名
- due process notification on-chain message + legal-aid link

## Design
- ADR-0013: 海運 + エネルギー クラスタ cross-actor
