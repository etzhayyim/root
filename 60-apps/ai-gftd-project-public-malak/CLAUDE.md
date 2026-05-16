# ai-gftd-project-public-malak — Sanitized Public Cybercrime Feed

> **T2 Logical Actor**: Manifest-driven (`20-actors/public-malak/actor-manifest.jsonld`).

`public-malak.gftd.ai` (nanoid: `pb1ml4k0`) — Sanitized version of malak.gftd.ai. **TLP CLEAR + GREEN only**. Audience: SOC analysts, security researchers, journalists.

## Lexicons
`publicMalak/` (7 files): `crawlAds` (procedure — trigger a scraper run), `listAds` (query + `#creativeView`), `getCreative` (query), `listSnapshots` (query + `#snapshotView`), `listScraperRuns` (query + `#scraperRunView`), `getAdvertiser` (query + `#advertiserView`), `analyzeAd` (procedure — intel analysis).

All surface the ad-library scraper graph (Meta/Facebook/Instagram/WhatsApp, Google Ads Transparency, LinkedIn, TikTok, X, LINE, Telegram). Read path is Hyperdrive + Kysely against `vertex_ads_*` / `edge_ads_*` per ADR-0036; no AT Repo records are written.

## Ad crawl execution
Periodic collection is owned by LangServer/Python worker, not Cloudflare Worker cron.

- BPMN: `00-contracts/bpmn/ai/gftd/public-malak/crawlAds.bpmn` (`public_malak_crawl_ads`, timer `R/PT6H`) and `analyzeAd.bpmn` (`public_malak_analyze_ad`, on-demand)
- Python tasks: `publicMalak.ads.queueSeedRuns`, `publicMalak.ads.processQueue`, and `publicMalak.ads.analyzeCreative` in `20-actors/magatama/py/src/pymagatama/primitives/public_malak_ads.py`
- Writes: direct `RW_URL` / `sync_cursor()` inserts into `vertex_ads_scraper_run`, `vertex_ads_advertiser`, `vertex_ads_creative`, `vertex_ads_snapshot`, and `vertex_ads_analysis`
- Worker appview XRPC remains as the read/manual control surface; its `wrangler.jsonc` has no cron trigger.

## cross-actor
- `malak` ← (TLP-filtered indicators flow from)
- `tia` — account protection feed
- `news` — security news consumption

## Governance
- TLP CLEAR/GREEN only (AMBER/RED dropped)
- victim identifier redaction (names → generic descriptors)
- 30日 investigation embargo (active-investigation flagged)

## Design
→ malak parent actor manifest, TLP v2.0 spec
