---
id: 260403-live-data-kyumei-shinka-consolidated
title: Live Data and Kyumei-Shinka (Consolidated)
status: active
doc_type: explanation
topic: live-data-kyumei-shinka
authoritative: true
last_verified: 2026-04-03
authoritative_for:
  - live data stability and operation baseline
  - kyumei-koji and shinka execution baseline
  - per-did autonomy integration baseline
  - standard rule for all actor/app DIDs
related:
supersedes:
  - 260326-shinka-kyumei-koji-design
  - 260402-live-data-stability-architecture
  - 260402-next-sprint-kyumei-koji-live-data
  - 260402-per-did-autonomous-kyumei-shinka-architecture
  - 260402-hinshitsu-fleet-kaizen-design
  - 260402-hinshitsu-ops-and-policy
superseded_by: []
---

# Live Data and Kyumei-Shinka (Consolidated)

## Decision

- live data status を host/cli/wit の共通契約で固定する。
- kyumei-koji と shinka の運用設計を 1 つの実行ループに統合する。
- per-did autonomy は上記ループ上で制御可能にする。
- hinshitsu policy/fleet kaizen は運用レイヤとして組み込む。
- すべての actor/app DID は standard rule として `shinka`, `koji`, `kyumei`, `domain knowledge` を備える。

## Scope

- live data stability
- kyumei/shinka operation
- per-did autonomy
- hinshitsu ops/policy

## Notes

この統合文書が上記 6 文書の正本。

## Standard Baseline

全 actor/app DID の baseline は次の通り。

1. `/_heartbeat` を持ち、cadence から `shouldDrill`, `shouldValidate`, `shouldAnalyze`, `shouldEngage` を返す。
2. `shinkaEvolution` と `shinkaKnowledge` を記録面として持つ。
3. `convoSystemPrompt`, `description`, `capabilities` を domain knowledge の最低メタデータとして持つ。
4. freshness と knowledge write は app 単位ではなく DID 単位で評価する。
