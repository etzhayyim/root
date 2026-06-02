# etzhayyim-project-social-contract

social-contract.etzhayyim.com — 契約本質分類 DID management。**legal-entity.etzhayyim.com の法人 identity 機能を吸収** — 法人 = 法域が付与する法人格 (incorporation social contract)。

## Architecture: 3-Layer DID

| Layer | DID pattern | 数 | 用途 |
|---|---|---|---|
| Primary | `did:web:social-contract.etzhayyim.com` | 1 | App controller |
| Type (path) | `did:web:social-contract.etzhayyim.com:{category}:{subcategory}` | 69 | 契約類型 (states pattern) |
| Entity (hash) | `did:web:social-contract.etzhayyim.com:entity:{country_alpha3}:{blake3_prefix12}` | N | 法人個体 (deterministic content-addressable) |
| Cohort (hash) | `did:web:social-contract.etzhayyim.com:cohort:{12-char hash}` | N | 契約人口統計セグメント (natural-person pattern) |

### Type DID 例
```
did:web:social-contract.etzhayyim.com:asset-acquisition:land-sale
did:web:social-contract.etzhayyim.com:financial:housing-loan
did:web:social-contract.etzhayyim.com:implicit:terms-of-service
did:web:social-contract.etzhayyim.com:incorporation:corporation
```

### Entity DID 例 (法人個体)
```
did:web:social-contract.etzhayyim.com:entity:jpn:c7f2a9b3e1d4   — 日本法人
did:web:social-contract.etzhayyim.com:entity:usa:de:a8b3f1e2c9d7 — Delaware 法人
did:web:social-contract.etzhayyim.com:entity:gbr:b7c1d3e5f2a9    — UK 法人
```

Hash input: `country + national_id + name_normalized + incorporated_date` → FNV-1a → 12-char hex prefix。
中央発行機関不要。同一法人は同一 DID。Secondary IDs: LEI (ISO 17442), 法人番号, DUNS。

### Cohort DID 例
```
did:web:social-contract.etzhayyim.com:cohort:7a3f2e1b9c0d
→ 日本 B2C 住宅ローン medium 2025年
```

## 7 Categories × 69 Type DIDs

| # | Category | Essence | Subcategories |
|---|---|---|---|
| ① | `asset-acquisition` | 所有権/使用権の移転 | land-sale, land-lease, building-sale, building-lease, fixed-term-land-lease, vehicle-purchase, vehicle-lease, equipment-lease, equipment-rental, parking, storage |
| ② | `continuous-service` | 継続的役務提供 | mobile-telecom, internet, electricity, gas, water, video-streaming, music-streaming, cloud-storage, saas, it-maintenance, equipment-maintenance |
| ③ | `risk-transfer` | 確率的損失の分散 | life-insurance, medical-insurance, auto-insurance, fire-insurance, liability-insurance, extended-warranty, guarantee-service |
| ④ | `financial` | 時間価値+信用リスク | housing-loan, auto-loan, credit-card, financial-lease, investment-trust, securities-account, futures, options, swap |
| ⑤ | `labor` | 人的リソースの市場取引 | employment, outsourcing, freelance, consulting, temporary-staffing, internship, apprenticeship |
| ⑥ | `implicit` | 暗黙的同意 | terms-of-service, privacy-policy, data-processing, cookie-agreement, membership-gym, membership-school, software-license, ip-license, franchise |
| ⑦ | `incorporation` | 法域が付与する法人格 | corporation, llc, partnership, limited-partnership, sole-proprietor, cooperative, foundation, trust, npo, ngo, state-owned, branch-office, joint-venture, holding-company, special-purpose-vehicle |

## Legal Entity as Social Contract

法人 = jurisdiction (国/州) が承認した social contract。設立登記 → 法人格付与 → 権利義務の主体。contract 失効 (解散/破産) → 法人格消滅。

### Lifecycle = DID Lifecycle

| Event | DID Operation | Status |
|---|---|---|
| 設立登記 | `DIDCreate` | `active` |
| 商号変更 | `DIDUpdate` | `active` (name 更新) |
| 合併 | `DIDUpdate` | `merged` (merged_into: new_did) |
| 解散 | `DIDDeactivate` | `dissolved` |
| 破産 | `DIDUpdate` → `DIDDeactivate` | `suspended` → `dissolved` |

### Graph Model (法人)

| Label | Properties |
|---|---|
| `LegalEntity` | did, country, national_id, name, entity_type, lei, duns, isic, status, hash |
| `Officer` | entity_did, name, role, appointed_at, resigned_at |
| `SubsidiaryRel` | parent_did, subsidiary_did, ownership_pct, effective_date |

### Authority Chain 統合

```
(:Authority {kind: "sovereign", did: "did:web:contract.etzhayyim.com:jpn"})
  -[:GRANTS {contract_type: "incorporation"}]->
(:LegalEntity {did: "did:web:social-contract.etzhayyim.com:entity:jpn:c7f2a9b3e1d4"})
  -[:SUBSIDIARY_OF {ownership_pct: 100}]->
(:LegalEntity {did: "did:web:social-contract.etzhayyim.com:entity:usa:de:a8b3f1e2c9d7"})
```

## Cohort Dimensions (13 axes)

category, subcategory, jurisdiction, governing_law, duration, party_type, value_band, risk_level, regulated, digital, transferable, industry_isic, year

## Data Collections

`com.etzhayyim.apps.social_contract.*`: contract_type, cohort, cohort_stat, contract_instance, party, obligation, lifecycle_event, legal_entity, officer, subsidiary_rel

## Component

| Key | Value |
|---|---|
| nanoid | `sc01cntr7` |
| wasm dir | `wasm/etzhayyim-wasm-social-contract-sc01cntr7/` |
| runtime | TS Native (W Protocol Event Stream) |

## Relationship to legal-entity.etzhayyim.com

`legal-entity.etzhayyim.com` は **データ収集** (JP NTA, SEC EDGAR, UK CH, GLEIF API crawl) に特化。
`social-contract.etzhayyim.com` が法人の **DID identity + contract lifecycle** を管理。
legal-entity は Follow → ComAtprotoSyncSubscribeRepos で収集データを social-contract に流す。
