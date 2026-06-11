# etzhayyim-project-obebe — Project Runbook

## Project Overview

`obebe.etzhayyim.com` — **obebe**: Luxury pet fashion brand. Haute couture for pets — apparel, collars, harnesses, carriers, and accessories. Seasonal collections, designer ateliers, material sourcing.

**Component**: `wasm/etzhayyim-wasm-obebe-sq42sjsd/`
**nanoid**: `sq42sjsd`
**Runtime**: Single Worker (account-level)

## Multi-DID Architecture

| DID | 用途 |
|---|---|
| `did:web:obebe.etzhayyim.com` (primary) | Platform agent (controller) |
| `did:web:obebe.etzhayyim.com:brand:{slug}` | ブランド entity (例: `brand:louis_vuitton_pet`) |
| `did:web:obebe.etzhayyim.com:atelier:{slug}` | アトリエ/ブティック entity |
| `did:web:obebe.etzhayyim.com:writer:{source}` | データソース entity |

## W Protocol Lexicon

| Kind | AT Collection NSID | 説明 |
|---|---|---|
| `obebe.brand` | `com.etzhayyim.apps.obebe.brand` | ブランド |
| `obebe.product` | `com.etzhayyim.apps.obebe.product` | 商品 |
| `obebe.collection` | `com.etzhayyim.apps.obebe.collection` | シーズンコレクション |
| `obebe.atelier` | `com.etzhayyim.apps.obebe.atelier` | アトリエ/ブティック |
| `obebe.entity_did` | `com.etzhayyim.apps.obebe.entity_did` | Entity DID 登録 |
| `obebe.source` | `com.etzhayyim.apps.obebe.source` | データソース |

## SQL Graph Schema

```
(:ObebeBrand {slug, name, tier, origin_country})-[:HAS_PRODUCT]->(:ObebeProduct)
(:ObebeBrand)-[:HAS_COLLECTION]->(:ObebeCollection)
(:ObebeBrand)-[:HAS_ATELIER]->(:ObebeAtelier)
(:ObebeProduct)-[:IN_COLLECTION]->(:ObebeCollection)
(:ObebeProduct)-[:TARGET_SPECIES {species}]->(:AnimaSpecies)
(:ObebeAtelier)-[:LOCATED_IN {lat, lng}]->(:Region)
(:ObebeCollection)-[:SEASON {type, year}]->(:ObebeSeason)
```

## Cross-App Integration

### Upstream (Import)

| App | Integration | 用途 |
|---|---|---|
| `anima.etzhayyim.com` | `etzhayyim:anima/breed@1.0.0` | ペット種/品種情報 |
| `okaimono.etzhayyim.com` | EC marketplace | 商品販売連携 |

### Downstream (Export via Invoke/Serve)

| Method | 用途 |
|---|---|
| `list_brands` | ブランド一覧 |
| `get_brand` | ブランド詳細 |
| `list_products` | 商品一覧 |
| `list_collections` | コレクション一覧 |
| `list_ateliers` | アトリエ一覧 |

## Contract

- **contract-category**: `service-agreement`
- **依存**: `kotodama:contract/agreement@1.0.0`, `etzhayyim:anima/breed@1.0.0`

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-obebe/wasm/etzhayyim-wasm-obebe-sq42sjsd
etzhayyim deploy --no-svelte --smoke-url https://obebe.etzhayyim.com/health
```

## API Endpoints

- App: `https://sq42sjsd.etzhayyim.com`
- Route: `https://obebe.etzhayyim.com`
