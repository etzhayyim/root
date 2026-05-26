# Corporate-disclosure corpus training recipes

Recipes for assembling Tier-A (and optionally Tier-B with `-tierB-` infix) corporate-disclosure training artifacts per **ADR-2605263800**. Each recipe is consumed by `70-tools/baien-moemoekyun-train/scripts/assemble-public-corpus.py` per the contract in **ADR-2605262400 §4**.

## Recipes (W1 anchor; +2 deferred to W3+)

| Recipe | Purpose | Tier max | Consumer artifact |
|---|---|---|---|
| `corp-financial-disclosure-foundations-r1.toml` | Financial-literacy baseline (SEC EDGAR + JP EDINET + UK Companies House + GLEIF LEI L1+L2) | A | `baien-server-corp-financial-disclosure-r1` |
| `corp-ownership-graph-r1.toml` | UBO + parent-subsidiary cross-juris control graph (GLEIF L2 + OpenCorporates open-data) | B (`-tierB-` infix mandatory) | `baien-server-corp-ownership-graph-tierB-r1` |
| `corp-material-event-stream-r1.toml` (W3) | Low-latency material-event stream (SEC EDGAR RSS + JP EDINET API snapshots) | A | `baien-server-corp-material-event-stream-r1` |
| `corp-officer-network-r1.toml` (W3) | Officer + director network (SEC + Companies House + EDINET officer fields) | A (w/ §5 PII redaction) | `baien-server-corp-officer-network-r1` |

## Discipline

- All W1 recipes are Tier-A only; Tier-B inclusion (OpenCorporates open-data fork CC-BY-SA 4.0) requires `-tierB-` infix per G4 of ADR-2605263800.
- Tier-C **CONSTITUTIONALLY PROHIBITED** at this recipe family per Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor concern. Bloomberg Terminal / S&P Capital IQ / Refinitiv Eikon / FactSet / Moody's Orbis / D&B Hoovers / Pitchbook / Crunchbase Pro hostnames + SDK imports MUST NOT appear; deny-list enforced at lint integration per recipe `[scan].vendor_terminal_denylist`.
- Per-jurisdiction publication-redaction policy honored (G3 in ADR-2605263800): SEC / Companies House / EDINET pass-through (upstream publishes named officers); GDPR right-to-be-forgotten DSARs route through `chigiri.data_privacy` to upstream publisher; religious-corp NEVER performs unilateral removal.
- Inference of resulting artifacts UNCHANGED Murakumo-only per ADR-2605215000.
- Training may use the train-rental carve-out per ADR-2605262200 once Council ratifies (~2026-07-19 earliest); until then, training is EVO-X2 single GPU only.
- All recipes embed Charter Rider §2 re-scan + PII filter + per-jurisdiction publication-rule honoring at assembly time (defense in depth).

## Related

- `/90-docs/adr/2605263800-public-data-corporate-disclosure-ipfs-ingestion.md` — corpus ADR
- `/90-docs/adr/2605262400-public-data-organism-ipfs-ingestion.md` — recipe contract parent
- `/90-docs/adr/2605263600-ossekai-information-arbitrage-tier-b-actor-r0.md` — primary publication consumer
- `/90-docs/adr/2605262900-toritate-accounting-audit-tier-b-actor-r0.md` — recipient-vendor cross-reference consumer
- `/90-docs/adr/2605262700-chigiri-legal-procedure-tier-b-actor-r0.md` — entity-identity verification consumer
- `../gov/` — sibling recipe family (open-government data)
- `../legal/` — sibling recipe family (legal corpus)
