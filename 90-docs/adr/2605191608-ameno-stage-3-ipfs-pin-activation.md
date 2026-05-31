---
id: 2605191608-ameno-stage-3-ipfs-pin-activation
title: Ameno Stage 3 — IPFS pin activation
status: proposed
doc_type: adr
topic: ameno-substrate-pipeline
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191559-ameno-mst-checkpointer-stage-2-activation
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605181100-mst-encrypted-records-signal-keywrap
---

# ADR 2605191608: Ameno Stage 3 — IPFS pin activation

## Context

ADR-2605191559 が Stage 2(MST projection via sidecar)を起動した。
Stage 3 は **MST から projected された CAR を IPFS にピン留め**する
段階。コードは TS sidecar(`@etzhayyim/sdk` checkpointer)に既に
存在(`#pinIpfs` ハンドラ)、 deployment.yaml の env を 1 行解除する
だけで activate する。

## Decision

`50-infra/k8s/lg-ameno/deployment.yaml` の checkpointer サイドカー
env に追加:

```yaml
- name: ETZ_IPFS_API_URL
  value: "http://simeonnomac-mini.local:5001"
```

これで sidecar が以下を実施:

1. Python → sidecar の `put` 呼び出し
2. AEAD seal(XChaCha20-Poly1305、 ADR-2605181100)
3. MST projection → root CID 計算
4. **CAR エンコード → `POST /api/v0/add` で kubo に pin**(Stage 3)
5. Stage 4(L2 anchor)は別 ADR

### kubo node 前提条件

- `simeonnomac-mini.local:5001` で kubo HTTP API を listen
- pod から到達可能(K3s が同 LAN、DNS 解決可能、または `/etc/hosts`
  代替)
- API allowlist が pod の CIDR を含む

ADR-2605191346 §2 で Mac mini fleet が Tier-1 と定められている。
`simeonnomac-mini.local` はその一員。

### Verify

```sh
# pod から
kubectl -n etzhayyim-langserver exec deploy/lg-ameno -c checkpointer -- \
  curl -fsS http://simeonnomac-mini.local:5001/api/v0/version

# checkpointer ログで pin 実行確認
kubectl -n etzhayyim-langserver logs deploy/lg-ameno -c checkpointer | grep -i "ipfs.pin"
```

### Fallback

kubo 到達不能時、sidecar は per-call で warning ログを吐き Stage 1-2
だけで継続(MST projection は完了、IPFS pin は skip)。Stage 4 が
これら未 pin の root CID を anchor しない設計なので、一貫性は維持。

## Consequences

- **substrate 完全性が一段上がる**:MST root CID が IPFS に永続化
  され、cluster 障害時も AEAD payload を取り戻せる
- ADR-2605181100 の暗号化が Stage 3 にも自動適用(sidecar が pin する
  bytes は ciphertext)
- kubo node の稼働が pod の hot path に入る — single point of
  failure。Stage 1-2 への自動 fallback で軽減
- 帯域 / 容量増:1 turn checkpoint ~1-5 KiB × IPFS rep factor。
  実測は M1 K3s dry-run の後に measure 必須

## Alternatives Considered

1. **w3up / Storacha / Filecoin direct** — IPFS pin より重い、未要
2. **Mac mini ローカル CAR ストア(IPFS なし)** — content-addressable
   不在で ADR-2605171800 不整合
3. **CF R2 + ipfs.io 経由 pin** — etzhayyim.com に同じ手法あり、 etzhayyim は
   self-host を優先

## References

- ADR-2605171800(MST → IPFS → L2 anchor pipeline)
- ADR-2605181100(MST encrypted records)
- ADR-2605191559(Stage 2 activation)
- kubo HTTP API: <https://docs.ipfs.tech/reference/kubo/rpc/>
