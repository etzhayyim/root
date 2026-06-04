# ai-gftd-project-adr — Mediation & Arbitration Intelligence

> **T1 Logical Actor**: Manifest-driven (`20-actors/adr/actor-manifest.jsonld`). Worker 不要.

`adr.gftd.ai` — Alternative Dispute Resolution intelligence (mediation/arbitration/conciliation/expert determination/adjudication)。1M cases/yr globally via ICC + JCAA + AAA + UNCITRAL + national ADR centers。saiban (litigation) の代替経路。

## App Identity

| Key | Value |
|---|---|
| **nanoid** | `adr1m4d0` |
| **domain** | `adr.gftd.ai` |
| **DID** | `did:web:adr.gftd.ai` |
| **Tier** | T1 (logical actor, no Worker) |
| **Manifest** | `20-actors/adr/actor-manifest.jsonld` |
| **Lexicons** | `00-contracts/lexicons/ai/gftd/apps/adr/` |

## Coverage

- **World**: 1M ADR cases/yr (ICC + JCAA + AAA + SIAC + UNCITRAL + national centers)
- **Path-based DIDs**: `:institution:{icc/jcaa/aaa/siac/uncitral}`

## Lexicons

| NSID | Type | Description |
|---|---|---|
| `ai.gftd.apps.adr.createCase` | procedure | ADR case 作成 (5 caseType + 8 subjectMatter) |
| `ai.gftd.apps.adr.registerArbitrator` | procedure | 仲裁人/調停人登録 (5 role enum) |
| `ai.gftd.apps.adr.listCases` | query | caseType + jurisdiction + institution + status フィルタ |

## cross-actor

| Connected actor | Direction | 用途 |
|---|---|---|
| `saiban.gftd.ai` | bidirectional | 訴訟 ↔ ADR の case routing + enforcement |
| `lawfirm.gftd.ai` | bidirectional | matter ↔ ADR case 代理 |
| `bengoshi.gftd.ai` | bengoshi → adr | arbitrator / mediator pool |

## Governance (per actor-manifest)

- **RULE-ADR-CONFIDENTIALITY**: per-institution confidentiality (ICC: confidential by default, AAA: per-case, UNCITRAL Article 28); claimant/respondent DIDs hashed in public firehose
- **RULE-ADR-AWARD-FINALITY**: Issued awards = append-only; corrections via separate awardCorrection record

## Design

→ ADR-0012: 法務クラスタ cross-actor トポロジー (`90-docs/adr/0016-legal-cluster-topology.md`)

## Status

設計完了 (manifest + lexicons + ADR + world_coverage + conventions)。
