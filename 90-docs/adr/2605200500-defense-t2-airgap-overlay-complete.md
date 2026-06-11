---
id: adr-2605200500-defense-t2-airgap-overlay-complete
title: "Defense T2 Air-Gap Overlay — Phase 3 完全実装"
status: active
doc_type: adr
topic: defense-t2-airgap
authoritative: true
last_verified: 2026-05-20
authoritative_for:
  - T2 air-gap K8s overlay structure
  - deny-all-egress NetworkPolicy for defense namespace
  - OPA configmap patch for EW + mission ≥ 3 clearance rules
  - DEPLOYMENT_TIER=T2-airgap classification unlock (level 3 + 4)
  - physical isolation scope boundary (ops-layer, not code-layer)
priority: 9.0
axis: architecture
weight: 0.90
depends_on:
  - adr-2605190100-defense-cluster-topology
  - adr-2605200100-defense-mission-orchestration-lattice
  - adr-2605200200-defense-platform-control-autonomous
  - adr-2605200300-defense-isr-sensor-fusion
  - adr-2605200400-defense-ew-counteruas-judgment
related: []
supersedes: []
superseded_by: []
---

# Defense T2 Air-Gap Overlay — Phase 3 完全実装

## Context

ADR-2605190100 Phase 3 (T2 Air-Gap) は +24-36 ヶ月先として計画されていた。
物理隔離はコードで実装できないが、K8s オーバーレイ・NetworkPolicy・OPA 拡張は現時点で deliverable として整備可能。
Phase 1 v8.0.0 完了を受け、オーバーレイを deploy-ready 状態に引き上げる。

## Decision

`50-infra/k8s/lg-defense/overlays/t2-airgap/` を以下 4 コンポーネントで拡張する。

### 1. NetworkPolicy — deny-all-egress

```yaml
# network-policy-deny-egress.yaml
kind: NetworkPolicy
spec:
  podSelector:
    matchLabels:
      app: lg-defense
  policyTypes: [Egress]
  egress: []   # 外部エグレスゼロ
```

外部 API (Anthropic / OpenRouter / B2 / CF) への接続を全遮断。
on-prem モデル + MinIO + pod-local PDS のみ許可 (podSelector 内部通信として別途 allow ルール追加)。

### 2. OPA Configmap パッチ

```yaml
# opa-configmap-patch.yaml
data:
  defense-t2.rego: |
    # EW 介入 ≥ 3 クリアランスルール
    # ミッション classificationLevel ≥ 3 実行許可ルール
    # T2 環境での autonomous モード (electronic_jamming のみ) 許可
```

既存 `etzhayyim.defense.ew.escalation` パッケージへのパッチマージ。

### 3. Deployment パッチ — 新規グラフ追加

```yaml
# deployment-patch.yaml
# 追加コンテナ引数:
#   --graph mission_orchestration
#   --graph platform_control
#   --graph sensor_fusion
#   --graph ew_counteruas
env:
  - name: DEPLOYMENT_TIER
    value: "T2-airgap"
  - name: CLASSIFICATION_MAX_LEVEL
    value: "4"
```

`DEPLOYMENT_TIER=T2-airgap` により classificationLevel 3 + 4 のロックを解除。

### 4. 物理隔離スコープ境界

以下は **ops-layer であり code-layer ではない** — このオーバーレイのスコープ外:

| 物理要件 | 担当 |
|---|---|
| HSM (Hardware Security Module) | 調達・設置 (ops) |
| TEMPEST シールディング | 施設工事 (ops) |
| 生体認証ゲート | 物理セキュリティ (ops) |
| ATLA 秘密取扱者適性確認 | 人事・コンプライアンス (ops) |

### kustomization.yaml

```yaml
resources:
  - ../../base
patches:
  - network-policy-deny-egress.yaml
  - opa-configmap-patch.yaml
  - deployment-patch.yaml
```

## Consequences

- オーバーレイは deploy-ready; `kubectl apply -k overlays/t2-airgap/` で適用可能
- 物理隔離層は ATLA 秘密取扱業者資格取得後の ops アクティベーションが前提
- T2 有効化前に on-prem LLM (Murakumo fleet / VLLM) + MinIO の国内設置が必要
- classificationLevel 4 (特定秘密) は T2 物理層アクティベーション後のみ unlock
