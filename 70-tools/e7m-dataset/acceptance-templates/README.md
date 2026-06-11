# Per-source acceptance flag templates

Templates for the operator-acceptance receipts read by
`e7m_dataset.fetchers._acceptance.require_acceptance(source)` per
**ADR-2605262400 §W3** (and reused by ADR-2605263800 + ADR-2605263900
for `corp/` + `gov/` bucket families).

## When required vs optional

| Tier | Acceptance flag | Notes |
|---|---|---|
| **A** (public-domain / open-government) | OPTIONAL (audit trail) | Most `corp/` + `gov/` W1 anchor sources are Tier-A. Operators MAY drop an acceptance template for clean audit lineage. Fetcher does NOT check. |
| **B** (e.g. CC-BY-SA derivative — OpenCorporates open-data) | **REQUIRED at W3+** | `-tierB-` infix mandatory on derivative corpus; acceptance attests the operator has read the upstream SA propagation terms. |
| **C** (research-use NC — Rapid7 / OpenINTEL / CAIDA / CZDS / Common Crawl URL index) | **MANDATORY** | Fetcher raises `MissingAcceptanceFlag` and fails closed if absent. G13 `-nc-` infix + judah LiteLLM + SBT-gate enforcement applies to the resulting artifact. |
| **D** (paid commercial vendor feeds: Bloomberg Terminal / S&P Capital IQ / Refinitiv Eikon / FactSet / Moody's Orbis / D&B Hoovers / Pitchbook / Crunchbase Pro / GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ Roll Call Pro / Westlaw / LexisNexis / Bloomberg Law / Wolters Kluwer) | **CONSTITUTIONALLY PROHIBITED** | Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor concern. No template available; fetcher MUST NOT be authored. |

## Workflow

1. Pick a template from this directory matching the source you intend to fetch.
2. Copy it to `~/.etzhayyim/source-acceptance/<source>.toml` (or override the directory via `ETZ_SOURCE_ACCEPTANCE_DIR` env var for ephemeral / test runs).
3. Fill `accepted_at` (ISO-8601 UTC), `accepted_by_did` (your operator DID), and any notes specific to your jurisdiction.
4. Run the fetcher via `e7m-dataset pull <source>` or directly from Python.

Acceptance schema validated by `_acceptance.require_acceptance()`:

- The file MUST contain an `[acceptance]` table
- `accepted_at` MUST be a non-empty string
- All other keys (`source`, `accepted_by_did`, `upstream_tos_url`, `notes`, plus arbitrary extras) are optional but recommended for audit

## Templates available (this directory)

| File | Tier | Source | Required? |
|---|---|---|---|
| `_generic-tierA-optional.toml.example` | A | generic | optional (audit trail) |
| `_generic-tierB-required.toml.example` | B | generic | required for `-tierB-` derivative |
| `_generic-tierC-required.toml.example` | C | generic | mandatory (fail-closed) |
| `opencorporates-opendata.toml.example` | B | OpenCorporates open-data fork (CC-BY-SA 4.0) | required at W3 per ADR-2605263800 |

W1 `corp/` + `gov/` fetchers are all Tier-A and do NOT require an acceptance flag at fetch time. The generic Tier-A template is provided for operators who want to record an explicit audit lineage in their `ETZ_SOURCE_ACCEPTANCE_DIR`.

## Related

- `/70-tools/e7m-dataset/src/e7m_dataset/fetchers/_acceptance.py` — runtime validator
- `/70-tools/e7m-dataset/tests/test_w3_fetchers.py` — acceptance-flag test pattern
- `/90-docs/adr/2605262400-public-data-organism-ipfs-ingestion.md` — §W3 acceptance-gate spec
- `/90-docs/adr/2605263800-public-data-corporate-disclosure-ipfs-ingestion.md` — `corp/` bucket consumer
- `/90-docs/adr/2605263900-public-data-open-government-ipfs-ingestion.md` — `gov/` bucket consumer
- `/CHARTER-RIDER.md` — §2 vendor commercial terminal deny-list
