> **DEPRECATED**: Actor migrated to `20-actors/nist/actor-manifest.jsonld` (T1 MCP-Compose). This project wasm/*/src/app.ts is retained as T3 fallback only.

# nist.gftd.ai — NIST Cybersecurity Framework Intelligence

NIST CSF 2.0 の 6 Function + Tier Gap + CMMC L2 + SP 1302 Community Profile を Multi-DID logical actor として管理。106 subcategory 全量 + cross-framework mapping。

## App Identity

| Key | Value |
|---|---|
| **nanoid** | `n1st0csf` |
| **domain** | `nist.gftd.ai` |
| **performer_id** | `n1st0csf` |
| **AT bot DID** | `did:web:nist.gftd.ai` |
| **Runtime** | Logical Actor (Worker なし、SQL `:Actor` node) |
| **UI** | yoro (profile-based) |

## Architecture — Logical Actor Only

全 actor は SQL graph node として存在。PDS が XRPC 代理応答。データは RisingWave graph。

```
did:web:n1st0csf.gftd.ai                          → root coordinator
  ├─ did:web:n1st0csf.gftd.ai:csf:govern          → GV (ガバナンス)
  ├─ did:web:n1st0csf.gftd.ai:csf:identify        → ID (識別)
  ├─ did:web:n1st0csf.gftd.ai:csf:protect         → PR (防御)
  ├─ did:web:n1st0csf.gftd.ai:csf:detect          → DE (検知)
  ├─ did:web:n1st0csf.gftd.ai:csf:respond         → RS (対応)
  ├─ did:web:n1st0csf.gftd.ai:csf:recover         → RC (復旧)
  ├─ did:web:n1st0csf.gftd.ai:tier:gap            → Tier 3→4 gap analysis
  ├─ did:web:n1st0csf.gftd.ai:cmmc:level2         → CMMC L2 (SP 800-171)
  └─ did:web:n1st0csf.gftd.ai:sp:communityProfile → SP 1302 community profiles
```

## Multi-DID Actor Definitions (10 actors)

| DID Path | Role | Description |
|---|---|---|
| (root) | Coordinator | CSF 2.0 framework coordinator。cross-function aggregation |
| `csf:govern` | Govern (GV) | GV.OC/RM/RR/PO/OV/SC — 31 subcategories |
| `csf:identify` | Identify (ID) | ID.AM/RA/IM — 22 subcategories |
| `csf:protect` | Protect (PR) | PR.AA/AT/DS/PS/IR — 28 subcategories |
| `csf:detect` | Detect (DE) | DE.CM/AE — 17 subcategories |
| `csf:respond` | Respond (RS) | RS.MA/AN/CO/MI — 18 subcategories |
| `csf:recover` | Recover (RC) | RC.RP/CO — 10 subcategories |
| `tier:gap` | Tier Gap | Tier 3→4 gap per subcategory × 6 dimension = 636 gap records |
| `cmmc:level2` | CMMC L2 | SP 800-171 r2, 14 families, 110 practices, CSF cross-mapping |
| `sp:communityProfile` | SP 1302 | Sector-specific community profile templates |

## Graph Labels

| Label | Count | Properties |
|---|---|---|
| `NistCsfFunction` | 6 | `code`, `name`, `description`, `version`, `ownerDid` |
| `NistCsfCategory` | 22 | `code`, `name`, `functionCode`, `subcategoryCount` |
| `NistCsfSubcategory` | 106 | `code`, `name`, `categoryCode`, `version` |
| `NistTierGap` | 636 | `subcategoryCode`, `categoryCode`, `dimension`, `tier3State`, `tier4State`, `ownerDid` |
| `NistCmmcFamily` | 14 | `code`, `name`, `practiceCount`, `csfPrimary`, `level`, `framework` |
| `NistCmmcPractice` | 110 | `code`, `sp800171`, `familyCode`, `csfPrimaryMapping`, `level` |
| `NistCmmcCsfMapping` | ~150 | `cmmcFamily`, `csfSubcategoryCode`, `relationship`, `gap` |
| `NistCommunityProfile` | 6+ | `name`, `sector`, `tier`, `highPriority`, `description` |
| `NistCsfProfile` | 0+ | `name`, `tier`, `targetState`, `currentState` |
| `NistCsfAssessment` | 0+ | `subcategoryCode`, `score`, `evidence`, `assessedAt` |

## Graph Relationships

```sql
-- Core taxonomy
(:Actor)-[:MANAGES]->(:NistCsfFunction)
(:NistCsfFunction)-[:HAS_CATEGORY]->(:NistCsfCategory)
(:NistCsfCategory)-[:HAS_SUBCATEGORY]->(:NistCsfSubcategory)

-- Tier gap
(:NistCsfSubcategory)-[:HAS_TIER_GAP]->(:NistTierGap)

-- CMMC mapping
(:NistCmmcFamily)-[:CONTAINS]->(:NistCmmcPractice)
(:NistCmmcPractice)-[:MAPS_TO]->(:NistCsfSubcategory)
(:NistCmmcCsfMapping {gap:true})-[:NOT_COVERED]->(:NistCsfSubcategory)

-- Community profile
(:NistCommunityProfile)-[:PRIORITIZES]->(:NistCsfCategory)

-- Assessment
(:NistCsfAssessment)-[:ASSESSES]->(:NistCsfSubcategory)
(:NistCsfProfile)-[:COVERS]->(:NistCsfSubcategory)
```

## W Protocol Event Stream

| Record Kind (camelCase) | Description |
|---|---|
| `ai.gftd.apps.nist.csfFunction` | CSF 2.0 Function definition |
| `ai.gftd.apps.nist.csfCategory` | CSF 2.0 Category definition |
| `ai.gftd.apps.nist.csfSubcategory` | CSF 2.0 Subcategory definition |
| `ai.gftd.apps.nist.tierGap` | Tier 3→4 gap per subcategory × dimension |
| `ai.gftd.apps.nist.cmmcFamily` | CMMC L2 family (14) |
| `ai.gftd.apps.nist.cmmcPractice` | CMMC L2 practice (110) |
| `ai.gftd.apps.nist.cmmcCsfMapping` | CMMC→CSF cross-mapping |
| `ai.gftd.apps.nist.communityProfile` | SP 1302 community profile |
| `ai.gftd.apps.nist.csfProfile` | Organization CSF Profile |
| `ai.gftd.apps.nist.csfAssessment` | Subcategory assessment result |

## Seed Script

`npx tsx 60-apps/ai-gftd-project-nist/seed.ts` — 全 ~1,060 records を PDS XRPC 経由で登録。

## Cross-actor Integration

| Target | Method | Direction | Purpose |
|---|---|---|---|
| scap.gftd.ai | `runScan` | nist → scap | NVD/OVAL スキャン実行 (ID.RA, DE.CM) |
| completer.gftd.ai | `evaluate` | completer → nist | CSF subcategory 準拠評価 |
| yabai.gftd.ai | `ingestThreatIntel` | yabai → nist | 脅威情報 → DE.AE |
| ct-monitor.gftd.ai | `pollVulnFeeds` | ct-monitor → nist | CVE/KEV → ID.RA |
| sbom.gftd.ai | `getBlastRadius` | nist → sbom | 影響範囲 → RS.AN |
| trust.gftd.ai | `evaluateTrust` | nist → trust | CSF tier → trust score 反映 |

## Cross-Framework Mapping

| Target Framework | Relationship | Purpose |
|---|---|---|
| CMMC 2.0 Level 2 | bidirectional | SP 800-171 r2 practice mapping (110 practices) |
| ISO 27001:2022 | bidirectional | ISMS control mapping |
| CIS Controls v8 | bidirectional | Implementation guidance |
| SOC 2 Type II | nist → soc2 | Trust Services Criteria mapping |
| NIST SP 800-53 r5 | nist → sp800 | Detailed control expansion |
| MITRE ATT&CK | detect/respond → attack | Technique coverage analysis |

## CMMC L2 Gap Summary

CSF subcategories NOT covered by CMMC L2 (主な gap):
- **GV 全体 (31)**: CMMC はガバナンス要件を直接定義しない
- **RC 全体 (10)**: 復旧計画は CMMC L2 スコープ外
- **ID.IM (4)**: 改善プロセスは CMMC L2 で部分的
- **ID.AM 一部**: 資産管理の一部サブカテゴリ
- **合計 ~50 subcategories** が CMMC L2 でカバーされない
