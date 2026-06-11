# etzhayyim-project-judge — 裁判官 Registry

> **T1 Logical Actor**: Manifest-driven (`20-actors/judge/actor-manifest.jsonld`). Worker 不要 (PDS Shared Executor / ActorExecutorDO で pipeline 実行).

`judge.etzhayyim.com` — 200K judges & magistrates グローバルレジストリ。CEPEJ + ABA + 最高裁人事 + national judicial councils。saiban (court) と hanrei (case-law) を bridge。

## App Identity

| Key | Value |
|---|---|
| **nanoid** | `jdg3wrld` |
| **domain** | `judge.etzhayyim.com` |
| **DID** | `did:web:judge.etzhayyim.com` |
| **Tier** | T1 (logical actor, no Worker) |
| **Manifest** | `20-actors/judge/actor-manifest.jsonld` |
| **Lexicons** | `00-contracts/lexicons/ai/etzhayyim/apps/judge/` |

## Coverage

- **World**: 200K judges & magistrates (CEPEJ + ABA + 最高裁人事 + national judicial councils)
- **Path-based DIDs**: `:jurisdiction:{iso3}` (per country), `:international` (ICJ/ICC/ECHR/CJEU/IACHR/ACHPR/ITLOS/WTO AB)

## Lexicons

| NSID | Type | Description |
|---|---|---|
| `ai.etzhayyim.apps.judge.registerJudge` | procedure | 裁判官プロファイル登録 (jurisdiction + court + appointment + specializations) |
| `ai.etzhayyim.apps.judge.listJudges` | query | jurisdiction + courtLevel + activeOnly フィルタ |
| `ai.etzhayyim.apps.judge.getJudge` | query | DID 単体取得 (full profile) |

## cross-actor

| Connected actor | Direction | 用途 |
|---|---|---|
| `saiban.etzhayyim.com` | bidirectional | court ↔ judge assignment |
| `hanrei.etzhayyim.com` | judge → hanrei | opinion authoring |
| `lawfirm.etzhayyim.com` | judge ← lawfirm | recusal / conflict of interest check |

## Governance (per actor-manifest)

- **RULE-JUDGE-PRIVACY**: PII redacted from public firehose; full profile only via authorized cross-actor
- **RULE-JUDGE-DISCLOSURE-PER-JURISDICTION**: Field-level visibility scoped to issuing jurisdiction's disclosure rules

## Design

→ ADR-0012: 法務クラスタ cross-actor トポロジー (`90-docs/adr/0016-legal-cluster-topology.md`)

## Status

設計完了 (manifest + lexicons + ADR + world_coverage + conventions)。実装は PDS Shared Executor で T1 logical actor として動作。専用 Worker 不要。
