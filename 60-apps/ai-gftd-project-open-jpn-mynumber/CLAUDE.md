# open-jpn-mynumber.gftd.ai — public-spec My Number reference architecture

**Status**: design scaffold (2026-04-26). This is not a government production
system and does not contain private J-LIS, Digital PMO, GCAS, or agency-only
interface material.

## Scope

This project models the public functional boundary of Japan's My Number-related
platforms as an open Japanese public-sector BPMN + Python worker application:

- JPKI-based identity proofing and certificate status checks.
- Person registration and local-agency subject resolution.
- Non-resident address-number lookup and assignment.
- Inter-agency information request brokering with consent, purpose, and audit
  checks.
- Citizen self-information and information-provision-history disclosure.
- Myna Portal-style API consent session orchestration.
- File exchange and OAuth token lifecycle boundaries used by local-government
  common functions.
- Public-source ingest for government pages and public assets, with PDF pages
  rendered to WebP derivatives and artifacts prepared for IPFS add/pin.

## Public Sources Used

- Digital Agency, `地方公共団体情報システム共通機能標準仕様書`, latest public
  link set updated 2026-02-27 and page updated 2026-03-25.
- Digital Agency, Myna Portal API specification site, API list and update
  history, including 2026-04 and 2025-09 updates.
- Digital Agency, Local Authentication Platform page for JPKI use on LGWAN and
  My Number-use administrative networks.

## Hard Boundaries

- Store a `person_ref` and agency-scoped aliases, not raw My Number values.
- Use tokenized identifiers, encrypted payload references, and immutable audit
  events for all special personal information flows.
- Require explicit legal purpose, requester agency, dataset class, and retention
  policy on every information request.
- Mock JPKI, Myna Portal, information-provision-network, and local-government
  adapters until a real connector is approved and separately reviewed.
- Do not put production PII, Individual Number, certificate private keys, or
  government credentials in this repository.

## Runtime Pattern

- BPMN is the orchestration contract, deployable to LangServer/BPMN-contract-compatible
  engines.
- Python worker owns adapter calls, input normalization, policy checks, and
  audit writes.
- `ingest/ingest_public_sources.py` owns public document collection, PDF to
  WebP conversion, manifest generation, and optional IPFS writes.
- Runtime state is RisingWave-only through the Kysely graph-schema migrations;
  the worker requires `RW_URL` or `DATABASE_URL` when executing write tasks.
