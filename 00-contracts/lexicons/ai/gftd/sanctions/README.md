# `ai.gftd.sanctions.*` — OFAC / UN / EU sanctions list mirror

Open spec for the sanctions list mirror (OFAC SDN, UN Consolidated List, EU
Restrictive Measures). This is the **list data + lookup lexicon only**.
The screening service that runs against customer transactions stays in
vendor scope per the Custody + Liability axes (false-negative AML liability,
customer-side screening log).

## Status

Tranche F scaffolding (Phase 2) per ADR-2605172400.

## NSIDs (planned)

- `ai.gftd.sanctions.getEntry` — fetch one sanctioned entity by listId
- `ai.gftd.sanctions.searchByName` — fuzzy name search across all lists
- `ai.gftd.sanctions.listSources` — enumerate source lists (OFAC, UN, EU, ...)
- `ai.gftd.sanctions.getListVersion` — current snapshot version per source

## See also

- `60-apps/ai-gftd-project-open-sanctions/` (this repo, scaffolding)
- ADR-2605172400 (vendor: 3-axis split rule + Tranche F)
- OFAC SDN: https://www.treasury.gov/ofac/downloads/
- UN Consolidated: https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list

## Boundary note

- **etzhayyim**: list mirror + lookup API (read-only, no customer data)
- **vendor**: screening service (`screenTransaction`, `screenCounterparty`, customer audit log, AML liability)
