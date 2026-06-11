# etzhayyim-project-legal-aid — 法律扶助 Intelligence

> **T1 Logical Actor**: Manifest-driven (`20-actors/legal-aid/actor-manifest.jsonld`). Worker 不要.

`legal-aid.etzhayyim.com` — 公的弁護人 + 法テラス + global legal aid intelligence。10M cases/yr (ILAG + 法テラス + national legal aid bodies)。bengoshi (defender pool) と saiban (court assignment) を bridge。**PII Tier 3** 厳格適用。

## App Identity

| Key | Value |
|---|---|
| **nanoid** | `lg4d3jp0` |
| **domain** | `legal-aid.etzhayyim.com` |
| **DID** | `did:web:legal-aid.etzhayyim.com` |
| **Tier** | T1 (logical actor, no Worker) |
| **Manifest** | `20-actors/legal-aid/actor-manifest.jsonld` |
| **Lexicons** | `00-contracts/lexicons/com/etzhayyim/apps/legalAid/` |

## Coverage

- **World**: 10M legal aid cases/yr (法テラス JP, Public Defender Office US, Legal Aid Agency UK 等)
- **Path-based DIDs**: `:jurisdiction:{iso3}`, `:matter:{criminal-defense/family/housing/immigration/consumer/labor/civil}`

## Lexicons

| NSID | Type | Description |
|---|---|---|
| `com.etzhayyim.legalAid.createCase` | procedure | 扶助 case 作成 (applicantDid = Tier 3 PII) |
| `com.etzhayyim.legalAid.assignDefender` | procedure | bengoshi DID を defender にアサイン (verified panel attorney) |
| `com.etzhayyim.legalAid.listCases` | query | jurisdiction + matter + status + lawyerDid フィルタ |

## cross-actor

| Connected actor | Direction | 用途 |
|---|---|---|
| `bengoshi.etzhayyim.com` | bidirectional | panel attorney pool ↔ defender assignment |
| `saiban.etzhayyim.com` | legal-aid → saiban | court routing |
| `lawfirm.etzhayyim.com` | legal-aid ← lawfirm | panel firm participation |
| `natural-person.etzhayyim.com` | legal-aid → natural-person | applicant PII (Tier 3) |

## Governance (per actor-manifest)

- **RULE-LEGAL-AID-PII-TIER3**: applicantDid + means-test data は **server-side Preferences のみ** (AT Repo 禁止)。public records は hashed case identifier + matter type のみ
- **RULE-LEGAL-AID-MEANS-TEST-AUTH**: meansTestPassed flag は recognized legal aid body DID のみ設定可
- **RULE-LEGAL-AID-DEFENDER-VERIFY**: assignDefender は bengoshi.etzhayyim.com active panel member 検証必須

## Design

- ADR-0012: 法務クラスタ cross-actor トポロジー (`90-docs/adr/0016-legal-cluster-topology.md`)
- ADR-0014: PII Tier 3 + Cohort-First Pattern (`90-docs/adr/0014-pii-tier3-cohort-first.md`) — applicantDid PII 配置の権威ソース

## Status

設計完了 (manifest + lexicons + ADR + world_coverage + conventions)。**PII handling は ADR-0014 規約に厳格準拠** (Tier 3 = Preferences only)。
