# ai-gftd-project-bengoshi — 弁護士 Registry

> **T1 Logical Actor**: Manifest-driven (`20-actors/bengoshi/actor-manifest.jsonld`). Worker 不要.

`bengoshi.gftd.ai` — 2.5M licensed lawyers グローバルレジストリ。IBA + ABA + 日弁連 + national bar associations。lawfirm (案件管理) と saiban (litigation) を bridge。ISCO-2611 HAR gate enforced。

## App Identity

| Key | Value |
|---|---|
| **nanoid** | `bng5h2x0` |
| **domain** | `bengoshi.gftd.ai` |
| **DID** | `did:web:bengoshi.gftd.ai` |
| **Tier** | T1 (logical actor, no Worker) |
| **Manifest** | `20-actors/bengoshi/actor-manifest.jsonld` |
| **Lexicons** | `00-contracts/lexicons/ai/gftd/apps/bengoshi/` |

## Coverage

- **World**: 2.5M licensed lawyers (日本 ~43K, US ~1.3M, global remainder)
- **Path-based DIDs**: `:jurisdiction:{iso3}`, `:specialization:{tax/ip/criminal/family/corporate/etc}`

## Lexicons

| NSID | Type | Description |
|---|---|---|
| `ai.gftd.apps.bengoshi.registerLawyer` | procedure | 弁護士登録 (bar admission + specializations + lawfirm 所属) |
| `ai.gftd.apps.bengoshi.searchLawyers` | query | jurisdiction + specialization + bar association フィルタ (exact match) |
| `ai.gftd.apps.bengoshi.recordDisciplinary` | procedure | 懲戒記録 (bar association DID 署名必須) |

## cross-actor

| Connected actor | Direction | 用途 |
|---|---|---|
| `lawfirm.gftd.ai` | bidirectional | matter ↔ leadLawyerDid 結合 |
| `saiban.gftd.ai` | bidirectional | jiken の代理人記録 |
| `adr.gftd.ai` | bengoshi → adr | arbitrator/representation |
| `legal-aid.gftd.ai` | bengoshi ← legal-aid | panel attorney pool |

## Governance (per actor-manifest)

- **RULE-BENGOSHI-VERIFY-BAR**: bar admission verification 必須 (HAR per ISCO-2611)
- **RULE-BENGOSHI-DISCIPLINARY-AUTH**: recordDisciplinary は recognized bar association DID のみ書き込み可

## Design

→ ADR-0012: 法務クラスタ cross-actor トポロジー (`90-docs/adr/0016-legal-cluster-topology.md`)

## Status

設計完了 (manifest + lexicons + ADR + world_coverage + conventions)。
