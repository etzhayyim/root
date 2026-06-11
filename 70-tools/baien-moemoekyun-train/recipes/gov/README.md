# Open-government-data corpus training recipes

Recipes for assembling Tier-A open-government-data training artifacts per **ADR-2605263900**. Each recipe is consumed by `70-tools/baien-moemoekyun-train/scripts/assemble-public-corpus.py` per the contract in **ADR-2605262400 §4**.

## Recipes (W1 anchor; +3 deferred to W3+)

| Recipe | Purpose | Tier max | Consumer artifact |
|---|---|---|---|
| `gov-civic-literacy-foundations-r1.toml` | Civic-literacy primary-source baseline (US Congress.gov + UK Hansard + JP 国会会議録 + Eurostat + World Bank + open-data portals) | A | `baien-server-gov-civic-literacy-r1` |
| `gov-statistics-foundations-r1.toml` | Numerical-reasoning IGO statistics anchor (Eurostat + OECD.Stat + WB + IMF + UN data) | A | `baien-server-gov-statistics-foundations-r1` |
| `gov-budget-transparency-r1.toml` (W3) | Public-spending transparency (USAspending + EU FTS + UK Treasury + JP 予算書) | A | `baien-server-gov-budget-transparency-r1` |
| `gov-procurement-transparency-r1.toml` (W3) | Tender + award transparency (EU TED + US SAM.gov + JP 政府調達 + UK Contracts Finder) | A | `baien-server-gov-procurement-transparency-r1` |
| `gov-parliament-procedural-r1.toml` (W3) | Procedural-knowledge anchor for chigiri Charter §1.12 routing-around evidence base (Congress.gov + Hansard + OEIL + 国会会議録 + Bundestag + Assemblée) | A | `baien-server-gov-parliament-procedural-r1` |

## Discipline

- All W1 recipes are Tier-A only; CN data **CONSCIOUSLY EXCLUDED** at W1 recipes (`state_aligned_flag_filter = "exclude"`) to keep these corpora cleanly free-redistributable. CN sources may appear in W4 recipe with §2(g) display obligation (parallel to ADR-2605262800 CN NPC handling).
- Tier-C **CONSTITUTIONALLY PROHIBITED** at this recipe family per Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor concern. GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ Roll Call Pro hostnames + SDK imports MUST NOT appear; deny-list enforced at lint integration per recipe `[scan].vendor_terminal_denylist`.
- Per-jurisdiction publication-rule honoring (G3 in ADR-2605263900): parliament transcripts + member-statements + procurement awardees + budget recipients pass-through (transparency-regime reason for publication); GDPR right-to-be-forgotten DSARs route through `chigiri.data_privacy` to upstream publisher; religious-corp NEVER performs unilateral removal.
- Inference of resulting artifacts UNCHANGED Murakumo-only per ADR-2605215000.
- Training may use the train-rental carve-out per ADR-2605262200 once Council ratifies (~2026-07-19 earliest); until then, training is EVO-X2 single GPU only.
- All recipes embed Charter Rider §2 re-scan + PII filter + per-jurisdiction publication-rule honoring at assembly time (defense in depth).

## Related

- `/90-docs/adr/2605263900-public-data-open-government-ipfs-ingestion.md` — corpus ADR
- `/90-docs/adr/2605262400-public-data-organism-ipfs-ingestion.md` — recipe contract parent
- `/90-docs/adr/2605263600-ossekai-information-arbitrage-tier-b-actor-r0.md` — primary aggregate-publication consumer
- `/90-docs/adr/2605262900-toritate-accounting-audit-tier-b-actor-r0.md` — recipient-vendor cross-reference consumer (budget + procurement)
- `/90-docs/adr/2605262700-chigiri-legal-procedure-tier-b-actor-r0.md` — Charter §1.12 state-function-routing-around evidence base consumer
- `../corp/` — sibling recipe family (corporate disclosure)
- `../legal/` — sibling recipe family (legal corpus)
