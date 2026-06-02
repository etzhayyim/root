---
id: 260403-atproto-reference-coverage-compliance-consolidated
title: "AT Protocol Reference, Coverage, and Compliance (Consolidated)"
status: active
doc_type: reference
topic: atproto-reference-coverage-compliance
authoritative: true
last_verified: 2026-04-03
authoritative_for:
  - AT Protocol lexicon reference baseline used in this repo
  - atproto.etzhayyim.com implementation coverage summary
  - AT Protocol normative compliance summary
related:
  - atproto-permission-scope-design
  - w-protocol-at-superset
supersedes:
  - at-protocol-lexicon-reference
  - at-protocol-coverage-audit
  - atproto-spec-compliance-analysis
superseded_by: []
---

# AT Protocol Reference, Coverage, and Compliance (Consolidated)

## Goal

AT Protocol の「一覧」「実装カバレッジ」「仕様準拠」を1つの正本に統合し、重複更新を止める。

## Scope

- Lexicon namespace のカタログ基準
- atproto.etzhayyim.com 実装カバレッジの集約値
- normative requirement 準拠状況の要約

## Lexicon Baseline

現行の集計基準:

- Total lexicons: 287
- 実装対象: 272 (object / permission-set を除外)

Namespace 別の詳細列挙は、実装コード生成/検証の入力と同期することを優先し、個別ドキュメントでの重複管理は行わない。

## Coverage Summary (atproto.etzhayyim.com)

- Route coverage: 272/272
- Full implementation: 65+
- Stub/shape-compatible responses: 残差分を許容

方針:

1. `com.atproto.repo.*` と `com.atproto.sync.*` を優先維持
2. `app.bsky.*` は利用頻度の高い read path から段階実装
3. 互換維持が必要な endpoint は shape-compatible stub を許容

## Compliance Summary

- Normative requirements: 192/192 準拠
- 対象領域: TID / Record Key / AT-URI / Data Model / Repository / Label / Permission
- 追加コスト: Worker in-memory 運用で $0 前提

## Repository Contract

この repo では次を canonical とする。

- Write authority: `com.atproto.repo.*` (PDS)
- Sync/firehose: `com.atproto.sync.*` (PDS)
- Domain query: `com.etzhayyim.apps.*` service proxy 経由

## Superseded Docs

以下は本書に統合済み。

- `90-docs/260322-at-protocol-lexicon-reference.md`
- `90-docs/260322-at-protocol-coverage-audit.md`
- `90-docs/260325-atproto-spec-compliance-analysis.md`
