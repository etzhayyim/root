# etzhayyim-project-anima — Project Runbook

## Project Overview

`anima.etzhayyim.com` — 動物 intelligence platform。種の分類学、品種カタログ、シェルター/保護施設、獣医記録、野生動物保全プログラム。1 Worker + N path-based DID。

**Component**: `wasm/etzhayyim-wasm-anima-czj1f6yv/`
**nanoid**: `czj1f6yv`
**Runtime**: Single Worker (account-level)

## Multi-DID Architecture (app ≠ profile)

**1 app = 1 primary DID (controller) + N cohort DIDs + N species DIDs + N breed DIDs + N shelter DIDs + N conservation DIDs。**

### DID 種別

| DID | 用途 |
|---|---|
| `did:web:anima.etzhayyim.com` (primary) | Platform agent (controller) |
| `did:web:anima.etzhayyim.com:{cohort-hash}` | **コホート動物** (統計的個体群、natural-person パターン準拠) |
| `did:web:anima.etzhayyim.com:species:{slug}` | 生物種 (例: `species:canis-lupus-familiaris`) |
| `did:web:anima.etzhayyim.com:breed:{slug}` | 品種 (例: `breed:shiba-inu`, `breed:maine-coon`) |
| `did:web:anima.etzhayyim.com:shelter:{slug}` | シェルター/保護施設 (例: `shelter:ueno-zoo`) |
| `did:web:anima.etzhayyim.com:conservation:{slug}` | 保全プログラム (例: `conservation:ibis-reintroduction`) |

### Cohort DID Architecture (natural-person パターン準拠)

**statistics-first**: 個体動物を多次元コホートの構成員として統計的にモデル化。各コホート = 一意の次元組み合わせ = 1 path-based DID。

**コホート次元 (17 軸):**

| 次元 | 型 | 例 |
|---|---|---|
| `species_slug` | string | `canis-lupus-familiaris` |
| `breed_slug` | option | `shiba-inu`, `null` (wild) |
| `country` | string (alpha-3) | `jpn`, `usa`, `gbr` |
| `region` | option | `13` (Tokyo), `CA` |
| `municipality` | option | `shibuya` |
| `sex` | enum | male, female, neutered-male, spayed-female |
| `age_class` | enum | neonate, juvenile, subadult, adult, geriatric |
| `registration_type` | enum | pet, livestock, working, zoo, sanctuary, wild-tracked, stray, feral |
| `domestication` | enum | domestic, feral, wild, semi-wild, captive-bred |
| `body_condition` | option | emaciated, thin, ideal, overweight, obese |
| `vital_status` | enum | alive, deceased, missing, released, euthanized |
| `shelter_slug` | option | `ueno-zoo`, `null` |
| `conservation_status` | option | endangered, vulnerable, least-concern |
| `habitat` | option | terrestrial, marine, arboreal |
| `sterilized` | option | true, false |
| `vaccinated` | option | true, false |
| `microchipped` | option | true, false |

**Cohort hash 生成 (DJB2):**

```go
func cohortHash(d CohortDimensions) string {
    parts := []string{
        d.SpeciesSlug, optStr(d.BreedSlug), d.Country, optStr(d.Region),
        optStr(d.Municipality), string(d.Sex), string(d.AgeClass),
        string(d.RegistrationType), string(d.Domestication),
        optStr(d.BodyCondition), string(d.VitalStatus), optStr(d.ShelterSlug),
        optStr(d.ConservationStatus), optStr(d.Habitat),
        optBool(d.Sterilized), optBool(d.Vaccinated), optBool(d.Microchipped),
    }
    canonical := strings.Join(parts, "|")
    var h uint32 = 5381
    for i := 0; i < len(canonical); i++ {
        h = h*33 + uint32(canonical[i])
    }
    return fmt.Sprintf("c%08x%04x", h, len(canonical)&0xFFFF) // "c" prefix → alpha-start, 13 chars
}
```

**Phase 設計:**

| Phase | 内容 |
|---|---|
| **Phase 1A** | Census/Survey データ取り込み (FAO, OIE, 環境省, AKC/JKC) |
| **Phase 1B** | コホートプロファイル生成 — 次元交差表 → DIDCreate per cohort |
| **Phase 1C** | 野生動物/歴史コホート (deceased, extinct, fossil record) |
| **Phase 2** | 個体 identity linkage — microchip/pedigree/tattoo で実個体をコホート DID にリンク |

**例: コホート DID 作成**

```go
// 統計コホート生成
hash := cohortHash(CohortDimensions{
    SpeciesSlug:      "canis-lupus-familiaris",
    BreedSlug:        "shiba-inu",
    Country:          "jpn",
    Region:           "13",  // Tokyo
    Sex:              "male",
    AgeClass:         "adult",
    RegistrationType: "pet",
    Domestication:    "domestic",
    VitalStatus:      "alive",
    Sterilized:       true,
    Vaccinated:       true,
    Microchipped:     true,
})
// hash = "c7f3a9b2c020" → did:web:anima.etzhayyim.com:c7f3a9b2c020

did, _ := magatama.DIDCreate(hash, map[string]any{
    "displayName": "Shiba Inu / 柴犬 — Adult Male, Tokyo, Pet",
    "description": "[AI Agent — unofficial] Statistical cohort: domestic shiba-inu, male adult, Tokyo, pet, sterilized+vaccinated+microchipped",
})

// コホートデータ書き込み
magatama.WRecord("cohortAnimal", map[string]any{
    "cohort_hash":          hash,
    "did":                  "did:web:anima.etzhayyim.com:" + hash,
    "species_slug":         "canis-lupus-familiaris",
    "breed_slug":           "shiba-inu",
    "country":              "jpn",
    "region":               "13",
    "sex":                  "male",
    "age_class":            "adult",
    "registration_type":    "pet",
    "domestication":        "domestic",
    "vital_status":         "alive",
    "population_estimate":  42000,
    "population_source":    "JKC-2025-registration",
    "survey_year":          2025,
    "org_id":               ctx.OrgID,
    "user_id":              ctx.UserID,
    "actor_id":             "czj1f6yv",
})

// Phase 2: 個体リンク (microchip → cohort)
magatama.WRecord("individualLinkage", map[string]any{
    "id":            "hachi-001",
    "cohort_hash":   hash,
    "name_ja":       "ハチ",
    "name_en":       "Hachi",
    "microchip_id":  "392000001234567",
    "birth_date":    "2023-04-15",
    "owner_did":     "did:web:natural-person.etzhayyim.com:c8a2b1f3",
    "weight_kg":     10.5,
    "org_id":        ctx.OrgID,
    "user_id":       ctx.UserID,
    "actor_id":       ctx.UserID,
})

// コホート DID として投稿
magatama.ATPost(did, "Tokyo 柴犬 adult male cohort: 42,000 registered in 2025", nil)
```

**その他 DID の例:**

```go
// 生物種 DID
speciesDID, _ := magatama.DIDCreate("species:ailuropoda-melanoleuca", map[string]any{
    "displayName": "ジャイアントパンダ / Giant Panda",
    "description": "Ailuropoda melanoleuca — endangered bear species native to central China",
})

// シェルター DID
shelterDID, _ := magatama.DIDCreate("shelter:ueno-zoo", map[string]any{
    "displayName": "恩賜上野動物園 / Ueno Zoological Gardens",
    "description": "Japan's oldest zoo — Tokyo, established 1882",
})

// 保全プログラム DID
consDID, _ := magatama.DIDCreate("conservation:ibis-reintroduction", map[string]any{
    "displayName": "トキ野生復帰プログラム / Crested Ibis Reintroduction",
    "description": "Nipponia nippon reintroduction program — Sado Island, Niigata",
})
```

## W Protocol Lexicon (CRITICAL)

**全 AT Record は `com.etzhayyim.apps.anima.*` namespace。** WIT = `etzhayyim:anima@1.0.0` (`wit/anima/package.wit`)。

| Kind (W Protocol) | AT Collection NSID | WIT Source | 説明 |
|---|---|---|---|
| `anima.species` | `com.etzhayyim.apps.anima.species` | `taxonomy` | 生物種 (分類学) |
| `anima.breed` | `com.etzhayyim.apps.anima.breed` | `breed` | 品種 (ペット/家畜) |
| `anima.cohort_animal` | `com.etzhayyim.apps.anima.cohort_animal` | `cohort` | **コホート動物** (統計的個体群、1 DID per cohort) |
| `anima.individual_linkage` | `com.etzhayyim.apps.anima.individual_linkage` | `cohort` | 個体 identity linkage (Phase 2: microchip/pedigree → cohort) |
| `anima.adoption` | `com.etzhayyim.apps.anima.adoption` | `cohort` | 譲渡記録 (cohort or individual) |
| `anima.shelter` | `com.etzhayyim.apps.anima.shelter` | `shelter` | シェルター/保護施設 |
| `anima.medical_event` | `com.etzhayyim.apps.anima.medical_event` | `veterinary` | 医療記録 (診察/手術/ワクチン) |
| `anima.health_condition` | `com.etzhayyim.apps.anima.health_condition` | `veterinary` | 健康状態 (慢性疾患等) |
| `anima.conservation_program` | `com.etzhayyim.apps.anima.conservation_program` | `conservation` | 保全プログラム |
| `anima.observation` | `com.etzhayyim.apps.anima.observation` | `conservation` | 野生動物観察記録 |

## SQL Graph Schema

```
// ── Taxonomy hierarchy ──
(:Species)-[:BELONGS_TO_GENUS]->(:Genus)
(:Genus)-[:BELONGS_TO_FAMILY]->(:Family)
(:Family)-[:BELONGS_TO_ORDER]->(:Order)
(:Order)-[:BELONGS_TO_CLASS]->(:Class)
(:Class)-[:BELONGS_TO_PHYLUM]->(:Phylum)
(:Phylum)-[:BELONGS_TO_KINGDOM]->(:Kingdom)

// ── Breed ──
(:Breed)-[:BREED_OF]->(:Species)
(:Breed)-[:IN_GROUP {group}]->(:BreedGroup)

// ── Cohort animal (statistics-first) ──
(:CohortAnimal {cohort_hash, did})-[:OF_SPECIES]->(:Species)
(:CohortAnimal)-[:OF_BREED]->(:Breed)
(:CohortAnimal)-[:IN_COUNTRY]->(:Country)
(:CohortAnimal)-[:IN_REGION]->(:Region)
(:CohortAnimal)-[:AT_SHELTER]->(:Shelter)
(:CohortAnimal)-[:HAS_CONSERVATION_STATUS {status}]->(:ConservationStatus)

// ── Individual linkage (Phase 2) ──
(:IndividualLinkage {microchip_id, pedigree_id})-[:MEMBER_OF]->(:CohortAnimal)
(:IndividualLinkage)-[:OWNED_BY]->(:DID)
(:IndividualLinkage)-[:HOUSED_AT]->(:Shelter)

// ── Adoption ──
(:DID)-[:ADOPTED {date, status}]->(:CohortAnimal)
(:DID)-[:ADOPTED_INDIVIDUAL {date}]->(:IndividualLinkage)
(:CohortAnimal)-[:ADOPTED_FROM]->(:Shelter)

// ── Shelter/Facility ──
(:Shelter)-[:SUBSIDIARY_OF]->(:Shelter)
(:Shelter)-[:HANDLES_SPECIES]->(:Species)
(:Shelter)-[:LOCATED_IN {lat, lng}]->(:Region)

// ── Veterinary ──
(:MedicalEvent)-[:FOR_COHORT]->(:CohortAnimal)
(:MedicalEvent)-[:FOR_INDIVIDUAL]->(:IndividualLinkage)
(:MedicalEvent)-[:PERFORMED_BY]->(:DID)
(:MedicalEvent)-[:AT_CLINIC]->(:Shelter)
(:HealthCondition)-[:DIAGNOSED_IN_COHORT]->(:CohortAnimal)
(:HealthCondition)-[:DIAGNOSED_IN_INDIVIDUAL]->(:IndividualLinkage)

// ── Conservation ──
(:ConservationProgram)-[:TARGETS]->(:Species)
(:ConservationProgram)-[:LED_BY]->(:DID)
(:ConservationProgram)-[:IN_REGION]->(:Region)
(:Observation)-[:OF_SPECIES]->(:Species)
(:Observation)-[:IN_PROGRAM]->(:ConservationProgram)
(:Observation)-[:BY_OBSERVER]->(:DID)
(:Species)-[:CITES {appendix}]->(:CitesTreaty)
```

## Cross-App Integration

### Upstream (Import)

| App | Integration | 用途 |
|---|---|---|
| `legal-entity.etzhayyim.com` | `Invoke("did:web:legal-entity.etzhayyim.com", "get-entity", {name: "WWF"})` | 保護団体の法人情報 |
| `isic.etzhayyim.com` | `G("Division").Match(Eq{"code": "01"})` | ISIC Section A (農業/畜産/漁業) |

### Downstream (Export via Invoke/Serve)

| Method | Handler | Caller | 用途 |
|---|---|---|---|
| `get-species` | `app.Handle("get-species", handler)` | Any | 種情報取得 |
| `get-breed` | `app.Handle("get-breed", handler)` | Any | 品種情報取得 |
| `list-endangered` | `app.Handle("list-endangered", handler)` | Any | 絶滅危惧種一覧 |
| `get-shelter` | `app.Handle("get-shelter", handler)` | Any | シェルター情報 |
| `query-cohorts` | `app.Handle("query-cohorts", handler)` | Any | コホート検索 (種/国/登録種別) |
| `list-adoptable` | `app.Handle("list-adoptable", handler)` | Any | 譲渡可能な動物一覧 |
| `get-adoption-statistics` | `app.Handle("get-adoption-statistics", handler)` | Any | 譲渡統計 (国/種別) |
| `get-vaccination-schedule` | `app.Handle("get-vaccination-schedule", handler)` | shelter, vet | ワクチン接種スケジュール |
| `get-population-trend` | `app.Handle("get-population-trend", handler)` | conservation orgs | 個体数推移 |

### Platform Integration

| Platform | Integration |
|---|---|
| **society6.etzhayyim.com** | Well-Becoming scoring — 保全活動参加で contribution、観察記録で competence 向上 |
| **trust.etzhayyim.com** | DID Trust Score — 各 path-based DID (species/shelter/conservation) の信頼スコア |
| **yabai.etzhayyim.com** | Risk check — 違法取引検知、密猟リスク、CITES 違反 |
| **i18n.etzhayyim.com** | 自動翻訳 — 10 言語 (ja/en/zh/es/hi/ar/pt/bn/ru/ko) |
| **okaimono.etzhayyim.com** | ペット用品 EC 連携 |
| **malak.etzhayyim.com** | 野生動物犯罪 intelligence (密猟/密輸) |

## WIT Architecture

| Package | Version | Interfaces | 説明 |
|---|---|---|---|
| `etzhayyim:anima` | `1.0.0` | taxonomy | 生物分類 (9 conservation-status, 13 habitat, 9 diet, 4 activity, 3 reproduction) |
| | | breed | 品種カタログ (16 domestic-species, 9 breed-group, 5 size, 8 coat-type) |
| | | cohort | **コホート動物** (17 次元統計モデル、11 registration-type、Phase 2 個体リンク) |
| | | shelter | シェルター/保護施設 (8 facility-type, 7 accreditation, geo-location) |
| | | veterinary | 獣医記録 (10 event-type, 11 vaccine-type, 5 severity, health conditions) |
| | | conservation | 保全プログラム (8 program-type, 3 CITES appendix, 8 observation-method, population tracking) |

## Contract

- **contract-category**: `treaty` (CITES) + `statute` (動物愛護管理法)
- **依存**: `magatama:contract/agreement@1.0.0`、`etzhayyim:legal-entity/entity@1.0.0` (org linkage)、`etzhayyim:isic-section-a/agriculture@1.0.0` (agriculture sector)

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-anima/wasm/etzhayyim-wasm-anima-czj1f6yv
etzhayyim build
etzhayyim deploy --smoke-url https://anima.etzhayyim.com/health
```

## API Endpoints

- App: `https://czj1f6yv.etzhayyim.com`
- XRPC: `https://czj1f6yv.etzhayyim.com/xrpc`
- Route: `https://anima.etzhayyim.com`

## Smoke Test

```bash
curl https://czj1f6yv.etzhayyim.com/health
curl -X POST https://czj1f6yv.etzhayyim.com/xrpc/etzhayyim.anima.v1.AnimaQueryService/ListSpecies \
  -H "Content-Type: application/json" -d '{"limit":10,"offset":0}'
curl -X POST https://czj1f6yv.etzhayyim.com/xrpc/etzhayyim.anima.v1.AnimaQueryService/ListEndangered \
  -H "Content-Type: application/json" -d '{"status":"endangered","limit":10}'
```
