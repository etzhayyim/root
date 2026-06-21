# etzhayyim-project-public-malak — Sanitized Public Cybercrime Feed (etzhayyim)

> **T2 Logical Actor**: Manifest-driven (`20-actors/public-malak/actor-manifest.jsonld` — to be mirrored from vendor in Phase 2).

`public-malak.etzhayyim.com` (nanoid: `pb1ml4k0`) — Sanitized version of `malak.etzhayyim.com` (vendor-side parent). **TLP CLEAR + GREEN only**. Audience: SOC analysts, security researchers, journalists.

## Tranche F migration status

Per `etzhayyim/etzhayyim-root` deps.toml `tranche-f-public-malak-classification-2026-05-20` (status `judgment-recorded`): 3-axis OR-test all clean (`Liability`/`Custody`/`Settlement`) → confirmed etzhayyim move target.

**Inverted partial-migration shape** (as of 2026-05-20):
- Vendor (etzhayyim) retains: project scaffold (CLAUDE.md, kotodama.jsonld), 14 lexicons under `publicMalak/`, 280 MB crawled corpus (`60-apps/etzhayyim-project-public-malak/data/ingest/`).
- etzhayyim already had: BPMN definitions (`00-contracts/bpmn/com/etzhayyim/public-malak/{analyzeAd,crawlAds}.bpmn`).

This commit lands the etzhayyim-side scaffold mirror (CLAUDE.md + OWNERS + PROJECT.jsonld + kotodama.jsonld) and 14 lexicons. The worker (`src/app.ts`), kotoba reference impl, and corpus residency follow separately:

- **kotoba**: deferred per user direction (kotoba fixes happen post-migration).
- **corpus residency**: Option A (vendor RW mirror, etzhayyim worker ingests fresh). Same architectural pattern as ADR-2605202400 GTFS-RT carve-out and `tranche-f-public-malak-classification-2026-05-20`. Vendor retains the 923-file `data/ingest/` mirror as historical artifact; etzhayyim deploy ingests directly from public ad-library APIs.

## Substrate (etzhayyim — kotoba per ADR-2605172000)

| Concern | Vendor (etzhayyim.com) | etzhayyim (this repo) |
|---|---|---|
| Write path | `createKyselyDb` → RisingWave `vertex_ads_*` | PDS XRPC `com.atproto.repo.createRecord` against `ai.etzhayyim.apps.publicMalak.*` (Phase 2 rewrite) |
| Read path | Hyperdrive + Kysely | `mst-projector` (Phase 3 indexed views) |
| Crawl orchestrator | LangServer pod (vendor) | LangServer pod (etzhayyim Murakumo, Phase 2 rewrite) |
| Corpus storage | `data/ingest/blobs/` (vendor B2) | IPFS pinner (`50-infra/ipfs-pinner/`) or fresh-ingest only |

## Lexicons
`00-contracts/lexicons/com/etzhayyim/apps/publicMalak/` (14 files):

- procedures: `crawlAds`, `analyzeAd`, `analyzeRecentAds`, `clusterRecentAds`, `processScraperQueue`
- queries: `getAdvertiser`, `getAnalysis`, `getCampaignCluster`, `getCreative`, `listAds`, `listAnalyses`, `listCampaignClusters`, `listScraperRuns`, `listSnapshots`

All surface the ad-library scraper graph (Meta / Facebook / Instagram / WhatsApp, Google Ads Transparency, LinkedIn, TikTok, X, LINE, Telegram). NSID prefix is `com.etzhayyim.apps.publicMalak.*` mirroring the vendor scope; an etzhayyim-namespaced alias (`ai.etzhayyim.apps.publicMalak.*`) may be added in Phase 2 if substrate divergence requires it.

## Ad crawl execution

- BPMN: `00-contracts/bpmn/com/etzhayyim/public-malak/crawlAds.bpmn` (`public_malak_crawl_ads`, timer `R/PT6H`) and `analyzeAd.bpmn` (`public_malak_analyze_ad`, on-demand). Both already present in this repo.
- Python tasks: `publicMalak.ads.queueSeedRuns`, `publicMalak.ads.processQueue`, `publicMalak.ads.analyzeCreative` — to be ported from vendor `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/public_malak_ads.py` in Phase 2.
- Writes: PDS XRPC (Phase 2). Worker appview XRPC remains as the read/manual control surface.

## cross-actor

- `malak` ← vendor-side parent (TLP-filtered indicators flow from vendor RW into etzhayyim via Option A mirror).
- `tia` — account protection feed (cross-repo reference; vendor today).
- `news` — security news consumption (cross-repo reference; vendor today).

## Governance

- TLP CLEAR/GREEN only (AMBER/RED dropped by the vendor `malak` upstream filter before any indicator is exposed to public-malak).
- victim identifier redaction (names → generic descriptors).
- 30-day investigation embargo (active-investigation flagged).

## Substrate-boundary notes

Per `etzhayyim/root/CLAUDE.md` §"Substrate boundary":
- This project is kotoba. No `createKyselyDb` / `env.HYPERDRIVE` in any deploy from this directory.
- All paid-tier / fiat-billed features stay in vendor (`malak.etzhayyim.com` parent).
- Ad-library API ingestion uses public APIs only — no fiat-billed transparency-data resellers.

## References

- vendor parent: `etzhayyim/etzhayyim-root` `60-apps/etzhayyim-project-public-malak/` + `60-apps/etzhayyim-project-malak/`
- tranche-F judgment: vendor deps.toml `tranche-f-public-malak-classification-2026-05-20`
- ADR-2605172000 — etzhayyim kotoba substrate
- ADR-2605172400 — etzhayyim vendor 3-axis split rule
- ADR-2605203000 — Phase E kotoba write-target options
- ADR-2605202400 — GTFS-RT vendor-mirror carve-out pattern (same shape as corpus residency Option A)
