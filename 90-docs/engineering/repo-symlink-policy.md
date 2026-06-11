---
id: repo-symlink-policy
title: "ADR-0008: active tree での repo 内 symlink を全面禁止する"
status: active
doc_type: adr
topic: repo-symlink-policy
authoritative: true
last_verified: 2026-04-11
authoritative_for:
  - repo symlink policy
  - shared contract / script path reference standard
related: []
supersedes: []
superseded_by: []
---

# Repo Symlink Policy

## Rule

- active tree では repo 内 symlink を禁止する。
- 外部パスを指す symlink は特に禁止する。
- alias 目的の symlink も禁止し、正規 path を直接参照する。

## Why

- symlink は editor / CI / tarball / container build / cross-platform checkout で挙動差を生みやすい。
- 絶対 symlink は clone 先や別マシンで高確率に壊れる。
- contract や infra の正規配置を曖昧にし、SSoT を崩す。
- broken symlink が残ると、repo が見た目上は存在していても実行時まで壊れ方が遅延する。

## Applies To

- active tree 全体
- 特に `20-actors/**`, `50-infra/**`, `60-apps/**` の build/deploy 対象

## Required Alternative

- 正規の source path を直接参照する。
- 共有 contract は `00-contracts/wit` を SSoT とする。
- 共有 script は `70-tools/scripts/**` を正規 path とする。
- 外部 repo 依存を置きたい場合は symlink ではなく vendoring か明示的な checkout 手順にする。

## Enforcement

- `node 70-tools/scripts/lint/validate-deps.mjs` が active tree の symlink を fail させる。
- ignore 対象は `.git`, `node_modules`, `_archive`, build cache のみ。

## Migration Note

- 既存 symlink は削除し、必要なら参照先を正規 path に置換する。
- repo 外 path を向く symlink は再導入しない。
