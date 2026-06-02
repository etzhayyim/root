# etzhayyim-project-business-person — Public Business Person Registry

> **T1 Logical Actor**: Manifest-driven (`20-actors/business-person/actor-manifest.jsonld`). Worker 不要.

`business-person.etzhayyim.com` — Public business person registry (corporate officers + executives + board members). 100M public profiles globally. Sources: corporate registries + XBRL filings + Wikipedia + official disclosures.

## App Identity

| Key | Value |
|---|---|
| **nanoid** | `bp3r5n0x` |
| **DID** | `did:web:business-person.etzhayyim.com` |
| **Tier** | T1 |
| **Lexicons** | `businessPerson/` (registerPerson, listPersons) |

## Schema 特徴

11 primaryRole: ceo / cfo / coo / cto / chairman / president / vice-president / director / founder / secretary / treasurer

Path-based DID: `did:web:business-person.etzhayyim.com:bp:{slug}`

## cross-actor

- `legal-entity` — primaryEntityDid (corporate identity)
- `shinshi` — public person profile (politicians + executives + celebrities)
- `natural-person` — naturalPersonDid (full PII Tier 3 link)
- `sanctions` — beneficial ownership screening (PEP — Politically Exposed Persons)

## PII handling (per ADR-0014)

- public role / appointment data: Tier 1 (AT Repo, federable)
- private contact info / non-public history: **Tier 3 (Preferences only)** via natural-person.etzhayyim.com DID link
- Wikipedia/XBRL データは public source なので Tier 1 OK

## Design

- ADR-0013: 海運 + エネルギー クラスタ cross-actor (business-person ↔ legal-entity bind)
- ADR-0014: PII Tier 3 + Cohort-First Pattern (PII handling)
