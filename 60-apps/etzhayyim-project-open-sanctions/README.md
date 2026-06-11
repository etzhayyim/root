# open-sanctions — OFAC / UN / EU sanctions list mirror

Tranche F scaffolding placeholder. Open mirror of the public sanctions lists
(OFAC SDN, UN Consolidated, EU Restrictive Measures) with name search and
versioning.

## Status

Phase 2 (scaffolding) per ADR-2605172400. No content yet — Phase 3 will set
up the ingest pipeline (cron → IPFS-pinned snapshot → MST publish).

## Scope

- Daily mirror of OFAC SDN, UN Consolidated, EU Restrictive
- Fuzzy name search lexicon (`com.etzhayyim.sanctions.searchByName`)
- Per-source snapshot versioning anchored to Base L2 (so an entry's presence-at-time-T is verifiable)

## Out of scope (stays vendor)

- Screening service for customer transactions (`screenTransaction`, `screenCounterparty`)
- AML audit log
- False-negative liability (controllership stays with vendor SaaS operator)

## See also

- [`00-contracts/lexicons/com/etzhayyim/sanctions/`](../../00-contracts/lexicons/com/etzhayyim/sanctions) — Tranche F lexicons
- ADR-2605172400 (vendor: 3-axis split rule + Tranche F)
- OFAC SDN: https://www.treasury.gov/ofac/downloads/
- UN Consolidated: https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list
