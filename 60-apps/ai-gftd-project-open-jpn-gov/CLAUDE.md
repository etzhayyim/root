# open-jpn-gov.gftd.ai — Japanese Gov Directory + e-Gov Law Proxy (OSS)

**Status**: MVP scaffold (2026-04-15). OSS mirror: `github.com/gftdcojp/ai-gftd-project-open-jpn-gov` (Apache-2.0).

## Scope

- **Roster**: 1府11省 + 3庁 (デジタル/復興/こども家庭) + 独立機関 (人事院/会計検査院) + 主要外局・委員会 ≈ 35 entries embedded as TS (`worker/src/roster.ts`).
- **Law proxy**: live fetch of e-Gov 法令API v2 (`laws.e-gov.go.jp/api/2`) with 1h CF edge cache.
- **5 XRPC methods** under `ai.gftd.apps.openJpnGov.*`:
  - `listMinistries` / `getMinistry` / `listAgencies` — roster queries
  - `searchLaws` / `getLaw` — e-Gov passthrough

## DID Pattern

```
did:web:open-jpn-gov.gftd.ai:{category}:{code}
# e.g. did:web:open-jpn-gov.gftd.ai:ministry:mof
#      did:web:open-jpn-gov.gftd.ai:agency:digital
#      did:web:open-jpn-gov.gftd.ai:cabinet:cao
#      did:web:open-jpn-gov.gftd.ai:independent:jinji
```

`category ∈ {cabinet, ministry, agency, independent}`. `kind` (for agency): `gaikyoku / tokubetsu / iinkai`.

## Not in MVP

- 47 都道府県 / 市区町村 (prefectural / municipal roster)
- e-Stat 統計 API proxy
- 官報 (Kampō) ingestion
- Procurement (電子調達) / 入札
- マイナンバー / 法人番号 lookup
- Cross-ref with existing monorepo actors (moj ↔ bengoshi, etc.)

## Relationship to existing actors

This app is a **public directory + law proxy**, not a sovereign actor. Existing monorepo actors like `bengoshi` / `judge` / `legal-aid` (see ADR-0016) remain independent. This app can be *referenced* by them for ministry DID lookups.

## Deploy

```bash
cd 60-apps/ai-gftd-project-open-jpn-gov/worker
gftd deploy     # or: wrangler deploy
```

No DB. No auth. Pure read-only public service.
