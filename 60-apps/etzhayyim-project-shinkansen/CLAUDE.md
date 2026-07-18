# etzhayyim-project-shinkansen — 新幹線 Reservation Intelligence

> **T2 Logical Actor**: Manifest-driven (`orgs/etzhayyim/com-etzhayyim-shinkansen/actor-manifest.jsonld`). **Reservation PII = Tier 3**.

`shinkansen.etzhayyim.com` (nanoid: `sh1nk4n0`) — 新幹線予約 cross-source intelligence (スマートEX / EX予約 / えきねっと). 9 line, 13 train type, 4 seat class.

## Lexicons
`shinkansen/` (3 files): searchAvailability, reserveSeat, listOperations.

## cross-actor
- `calendar` — confirmed reservation auto-sync
- `railway` — rolling stock + route data
- `maps` — station geo

## PII (per ADR-0014)
- AT Repo: anonymized fare comparison のみ
- Preferences (Tier 3): reservation (name + payment + seat number)

## Governance
- per-source rate limit (JR provider ToS 準拠)

## Design
- ADR-0014: PII Tier 3 + Cohort-First Pattern
