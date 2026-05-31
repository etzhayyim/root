---
id: 2605191625-ameno-stage-4-l2-anchor
title: Ameno Stage 4 — Base L2 anchor CronJob
status: proposed
doc_type: adr
topic: ameno-substrate-pipeline
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191608-ameno-stage-3-ipfs-pin-activation
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
related:
V05191559-ameno-mst-checkpointer-stage-2-activation
---

# ADR 2605191625: Ameno Stage 4 — Base L2 anchor CronJob

## Context

ADR-2605191559(Stage 2 MST projection)+ ADR-2605191608(Stage 3 IPFS
pin)が完了。 Stage 4 = **MST root CID を Base L2 の
`EtzhayyimAnchor` コントラクトにアンカーする**段階。

uhl-right-neural は既に `50-infra/anchor-cron/k8s/cronjob.yaml`
(anchor-cron-uhl)で 15 分間隔の CronJob として運用中。 ameno も
**同 image・同パターン**で 1 CronJob 追加するだけ。

## Decision

新規 manifest:`50-infra/anchor-cron/k8s/cronjob-ameno.yaml`。
`anchor-cron-uhl` から以下のみ変更:

| field | uhl | ameno |
|---|---|---|
| name | `anchor-cron-uhl` | `anchor-cron-ameno` |
| namespace | `mitama-udf` | `etzhayyim-langserver` |
| ETZ_ANCHOR_CELL_DIDS | `did:web:uhl-right-neural.etzhayyim.com` | `did:web:ameno.etzhayyim.com` |
| podAffinity target | `lg-uhl-right-neural` | `lg-ameno` |
| Secret name | `anchor-cron-signer` | `anchor-cron-signer-ameno` |

それ以外(image, schedule, ETZ_ANCHOR_RPC_URL, CONFIRMATIONS,
BATCH_MAX, BALANCE_WEI, securityContext)は uhl と一致。

### Apply

```sh
kubectl -n etzhayyim-langserver create secret generic anchor-cron-signer-ameno \
  --from-literal=key="<your-funded-base-signer-private-key>"

kubectl apply -f 50-infra/anchor-cron/k8s/cronjob-ameno.yaml
```

### Verify

```sh
# CronJob exists and is scheduled
kubectl -n etzhayyim-langserver get cronjob anchor-cron-ameno

# Trigger a one-off run
kubectl -n etzhayyim-langserver create job --from=cronjob/anchor-cron-ameno manual-anchor-ameno-$(date +%s)

# Watch logs
kubectl -n etzhayyim-langserver logs -l app.kubernetes.io/name=anchor-cron --tail=200 -f
```

### EtzhayyimAnchor 必要事項

- **既デプロイ済**(`deps.toml [platform.l2.anchor_contract]` の
  `address_testnet` 参照)で本 ADR は使用するだけ。未デプロイなら
  別 ADR(`etzhayyim-anchor-deploy`)で扱う
- **Signer**:Base に gas ETH を含む EOA。warning balance(0.01 ETH)
  を下回ると Job が警告ログを残す

### chainId / network

| env | testnet | production |
|---|---|---|
| `ETZ_ANCHOR_RPC_URL` | `https://sepolia.base.org` | `https://mainnet.base.org` |
| chain ID | 84532 | 8453 |

testnet で M5 まで運用、mainnet 切替は別 ADR で。

## Consequences

- ameno graph state が **Base L2 上に anchor された Merkle root** で
  時間軸的に検証可能になる(ADR-2605171800 の終端)
- Stage 2-4 完全活性化:Python put → AEAD seal → MST projection → IPFS
  pin → L2 anchor receipt return
- gas spend は brief 流量に比例。15 分 1 anchor 設計で 1 day ~96 tx、
  base sepolia なら無料テストネット、production base で月 ~$5
  (現状 base gas 価格基準)
- CronJob の Pod は **lg-ameno と同ノード** に schedule(podAffinity)
- 障害ケース:Stage 4 が失敗してもサイドカーは pending として再試行
  可能(ADR-2605171800 §retry-semantics)

## Alternatives Considered

1. **anchor-cron-ameno を lg-ameno Pod のサイドカーとして同居** —
   socket 共有が emptyDir で済むが anchor Pod が常駐になり gas-burn
   検証時にローテートが効きづらい。 uhl-right-neural と同じ CronJob
   分離を採用
2. **Sequencer-pushed anchor**(sidecar が L2 を直接叩く)— signer key
   を sidecar に持たせる必要、鍵管理境界が混乱。CronJob に専用権限
3. **オンチェーン anchoring を skip し IPFS pin だけで終わる**(Stage
  3 まで)— substrate `verify` の時間軸属性が失われる。 reject

## References

- ADR-2605171800(LangGraph MST IPFS L2 pipeline)
- ADR-2605181000(uhl-right-neural、本パターンの先行運用)
- ADR-2605191559 / 2605191608(Stage 2-3 activation)
- `50-infra/anchor-cron/k8s/cronjob.yaml`(uhl 版、参照元)
- EtzhayyimAnchor:`deps.toml [platform.l2.anchor_contract]`
