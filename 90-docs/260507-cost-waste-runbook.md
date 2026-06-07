---
id: 260507-cost-waste-runbook
title: 契約支払い無駄削減 runbook (Task #1-#3 詳細プラン + minimax リスク分析)
status: active
doc_type: how-to
topic: infra-cost
authoritative: true
last_verified: 2026-05-07
related:
  - adr-2605010000
  - 90-docs/adr/0048-kotoba-vultr-b2-primary.md
  - adr-2604292130
  - 50-infra/vultr/cloudflared/blockscout-tunnel.yaml
---

# Goal

経路依存で生じた支払い無駄 (Task #1-#3) を、ダウンタイム最小・rollback 完備で削減する。

# Executive Summary

| Task | Δmonth | execution risk | rollback cost | 推奨順 | 状態 |
|---|---|---|---|---|---|
| #1 orphan volume `bskaa2wrjo` 削除 | −$7 | 0 (別 region で mount 不可) | 不可 (volume 再作成は別 ID) | **1st** | ✅ done 2026-05-07 |
| #7 (新発見) orphan volume `3zgavabooi` 削除 | −$14 | 0 (同上) | 不可 | (parallel) | ✅ done 2026-05-07 |
| #7 (新発見) volume `p9riuzhrvf` 100→250 GB doc drift | (実払いは元から +$10.50) | 0 | 0 | (parallel) | ✅ done 2026-05-07 (doc fix only, 実費は不変) |
| #2 geth LB → CF Tunnel | −$11 | low (precedent: blockscout) | 数分で LB 戻し可 | **2nd** | 🟡 Stage A-C/F done 2026-05-07、Stage E 待機 (24h soak、明日 #8 で cleanup) |
| #3 6000 Ada pod を unified image に復元 | $0 (LLM スロット復活) | medium (Docker build 失敗、cold start) | 旧 template に切替 5 min | **3rd** | 🟡 Stage A done 2026-05-07 (image `sha256:5ca9dd05…2624f2ce` in ghcr.io)、Stage B-E pending |
| **2026-05-07 確定削減** | **−$21/mo** | | | | (Stage E 完了後 −$32/mo) |

# Task #1 — Orphan RunPod Volume 削除

## 経路依存

`90-docs/adr/2605010000-runpod-6000ada-unified-pod.md:185` の retire 履歴。旧 4090 pod (EUR-IS-1 region) を再作成する際に RunPod が同 region に Network Volume を auto-create。後に pod は US-KS-2 の 6000 Ada (`vyp99t9px7h4dl`) に移行 → 別 region の volume は orphan 化。**path tail = region mismatch**。

## Minimax

| 行動 \ 環境 | retain | terminate |
|---|---|---|
| EUR-IS-1 で 6000 Ada が将来再生する | $7/mo (節約 $0) | $7/mo の再作成 |
| 6000 Ada 在庫枯渇で別 region に移行 | $7/mo (使えない) | $7/mo の再作成 |
| 現状維持 (US-KS-2 安定) | $7/mo の純損失 | $0 |

支配戦略 = terminate。max-loss は terminate 側が常に小さい (volume 再作成は GraphQL 1 発、5 分)。

## 手順

```bash
# 1) Keychain から API key
RUNPOD_API_KEY=$(security find-generic-password -s etzhayyim.runpod -a API_KEY -w)

# 2) volume 状態確認 (mount されていないことの最終確認)
curl -sS https://api.runpod.io/graphql \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"query { myself { networkVolumes { id dataCenterId size } } }"}' \
  | jq '.data.myself.networkVolumes[] | select(.id=="bskaa2wrjo")'
# 期待: {"id":"bskaa2wrjo","dataCenterId":"EUR-IS-1","size":100}
# pod に attach されているなら GraphQL の podId フィールドが返る — 0 を確認

# 3) 削除
curl -sS https://api.runpod.io/graphql \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { deleteNetworkVolume(input:{id:\"bskaa2wrjo\"}) }"}'
# 期待: {"data":{"deleteNetworkVolume":true}}

# 4) 確認
curl -sS https://api.runpod.io/graphql \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"query { myself { networkVolumes { id } } }"}' \
  | jq '.data.myself.networkVolumes[].id'
# 期待: bskaa2wrjo が含まれない
```

## Repo 更新

- `90-docs/adr/2605010000-runpod-6000ada-unified-pod.md:185` の「未削除」エントリを「削除済 2026-05-07」に書き換え
- `deps.toml:19234` の orphan エントリを削除

## Rollback

不可。ただし volume 中身は 4090 pod 用の transient cache のみ。

# Task #2 — geth LB → CF Tunnel

## 経路依存

geth-private は Coinbase Smart Wallet 等の external RPC を必要とする → 外部公開が要件。当初 deploy (2026-04-25 ADR-0074 Phase 2-A) では Vultr LoadBalancer + caddy TLS sidecar + CF Origin Cert の 3 段構成を採用 (CF Worker `geth-rpc-proxy` → Vultr LB `149.248.2.241:443` → caddy → geth pod)。

その後 blockscout / bpmn-dispatcher が CF Tunnel pattern を確立 (`50-infra/vultr/cloudflared/blockscout-tunnel.yaml`)。geth は **historical pattern のまま $11/mo を払い続けている**。

## Minimax

| 行動 \ 環境 | smooth | tunnel pod failure | regional CF outage |
|---|---|---|---|
| LB retain ($11/mo) | $11 | $11 (LB は CF 経由で生きる) | $11 (LB 直叩き fallback 可) |
| Tunnel migrate ($0/mo) | $0 | replicas=2 で吸収 | RPC 死 (但し CF Worker geth-rpc-proxy も同 outage で死ぬので net loss = 0) |

CF Worker proxy が既に CF 依存なので、Tunnel への置換は CF 依存度を増やさない。**支配 = migrate**。

## 手順 (staged, rollback 容易)

### Stage A: tunnel 作成 (LB は残す、並列稼働)

```bash
cloudflared tunnel create geth-rpc
# → ~/.cloudflared/{TUNNEL_ID}.json
TUNNEL_ID=$(cloudflared tunnel list --output json | jq -r '.[] | select(.name=="geth-rpc") | .id')
cloudflared tunnel route dns geth-rpc geth.etzhayyim.com  # 既存 CNAME を上書き
# 注意: 既存 CNAME は CF Worker geth-rpc-proxy の route。route dns コマンドで CNAME を {TUNNEL_ID}.cfargotunnel.com に書き換える前に既存 Worker route を unbind するか、別 hostname (例: geth-rpc.etzhayyim.com) でテストすること
```

### Stage B: tunnel manifest 作成 + 適用

`50-infra/vultr/cloudflared/geth-tunnel.yaml` を blockscout-tunnel.yaml をテンプレに新規作成:

```yaml
# (略 — blockscout-tunnel.yaml と同形、namespace=geth-private、ingress 1 本)
ingress:
  - hostname: geth.etzhayyim.com
    service: http://geth-private.geth-private.svc.cluster.local:8545
    originRequest:
      connectTimeout: 10s
      noTLSVerify: true
  - service: http_status:404
```

```bash
kubectl apply -f 50-infra/vultr/cloudflared/geth-tunnel.yaml
kubectl -n geth-private rollout status deploy/cloudflared-geth-rpc
```

### Stage C: smoke test (tunnel 経路、LB 経路 両方)

```bash
# 直接 tunnel 経由 (DNS 切替前なら別 hostname で)
curl -sS https://geth.etzhayyim.com \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
# 期待: {"jsonrpc":"2.0","id":1,"result":"0x3f9a9"}  (260425 hex)

# Smart Wallet add-chain flow (yoro UI から手動)
# yoro.etzhayyim.com の Smart account add-chain で chainId 260425 を追加し、
# eth_blockNumber / eth_getBalance が成功することを確認
```

### Stage D: LB 撤去

```bash
# 1) Service を ClusterIP に降格 (caddy-tls-proxy は不要に)
kubectl -n geth-private patch svc caddy-blockscout-tls -p '{"spec":{"type":"ClusterIP"}}'
# 2) caddy Deployment を削除 (CF Origin Cert も不要)
kubectl -n geth-private delete deploy caddy-tls-proxy
# 3) Vultr LB 削除 (Vultr API 経由)
VULTR_API_KEY=$(security find-generic-password -s etzhayyim.vultr -a API_KEY -w)
LB_ID=$(curl -sS https://api.vultr.com/v2/load-balancers \
  -H "Authorization: Bearer $VULTR_API_KEY" \
  | jq -r '.load_balancers[] | select(.ipv4=="149.248.2.241") | .id')
curl -X DELETE https://api.vultr.com/v2/load-balancers/$LB_ID \
  -H "Authorization: Bearer $VULTR_API_KEY"
```

### Stage E: repo 更新

- `50-infra/vultr/geth-private/deps.toml:13` `monthly_cost_usd = 11` → `0`
- `50-infra/vultr/geth-private/CLAUDE.md` の topology 図を CF Tunnel 経路に書き換え
- `50-infra/vultr/geth-private/manifests/40-tls-proxy.yaml` を `_archive/` に移動 or 削除

## Rollback

- Stage D で LB 削除した後に問題発覚 → caddy-tls-proxy を redeploy + Vultr LB 再作成 (15 分)
- Stage C で tunnel 不調 → DNS を CF Worker geth-rpc-proxy → Vultr LB の旧経路に戻す (CF Dashboard で 1 click、TTL 60s)

## リスク

| リスク | 確率 | 影響 | 緩和 |
|---|---|---|---|
| CNAME 切替で DNS 伝播待ち | high | 数分の既存 client RPC 失敗 | low TTL 60s で事前に下げる |
| chainId mismatch (Smart Wallet キャッシュ) | medium | client side のみ、reload で復旧 | yoro UI で chain remove → re-add |
| caddy 削除後に CF Tunnel が node 再起動で死 | low | replicas=2 で吸収済 | blockscout precedent で実績 |

# Task #3 — 6000 Ada pod を unified image に復元

## 経路依存 (重要)

ADR-2605010000 の Decision = **1 pod に ComfyUI :8188 + vLLM :8000 + LiteLLM :4000 同居** で旧 $1100/mo (4090 + serverless standby + Murakumo overhead) → $561/mo を達成 (月 $539 削減)。

しかし root deps.toml L1089 (`runpod-comfyui-pod-active`) に明記:

> Image: `runpod/comfyui:latest` (public, **ComfyUI :8188 only — no co-located vLLM/LiteLLM in this revision**; LLM path needs separate pod or Murakumo fallback). Predecessor `58pvflvw9w6nt3` (terminated 2026-05-05) hosted unified pod with `ghcr.io/etzhayyim/runpod-vllm-gemma:latest`...

つまり **2026-05-05 の pod 再作成時に unified image を使わず public ComfyUI image で起動** → LLM スロットを silent regression。**価格は据え置き $554/mo、価値だけ消えた**。

## Minimax

| 行動 \ 環境 | LLM トラフィック平常 | LLM burst | RunPod outage |
|---|---|---|---|
| 現状 (ComfyUI only $554) | $554 + Murakumo $200 = $754 | $754 + RunPod Serverless burst | Murakumo fallback ($754) |
| Unified 復元 ($554) | $554 (Murakumo 縮退可、$554 単独) | $554 + Serverless burst | Serverless fallback (RunPod 全部死は同じ) |

Unified 復元は worst-case (RunPod outage) が現状と等価、それ以外で勝つ。**支配 = restore**。

加えて Task #4 (Murakumo 縮退 4→2 node、−$100/mo) の前提条件が揃う。

## 手順

### Stage A: Docker build (✅ done 2026-05-07)

**Canonical build path** = `50-infra/runpod/vllm-gemma-image/` (NOT `60-apps/etzhayyim-project-runpod/unified-pod` — runbook 初版の誤記。ADR-2605010000 L147 が正)。

**経路選択**: 本 repo は GH Actions 不使用方針 (lefthook ローカル hook のみ)。`.github/workflows/runpod-vllm-gemma-image.yml` は legacy。2026-05-07 以降は **BuildKit remote build (`etzhayyim-vke`) で push** が canonical。

```bash
echo "$(gh auth token)" | docker login ghcr.io -u "$(gh api user -q .login)" --password-stdin

TS=$(date +%Y%m%d-%H%M)
docker buildx build \
  --platform linux/amd64 \
  --builder etzhayyim-vke \
  --tag ghcr.io/etzhayyim/runpod-vllm-gemma:${TS}-amd64 \
  --tag ghcr.io/etzhayyim/runpod-vllm-gemma:v1 \
  --tag ghcr.io/etzhayyim/runpod-vllm-gemma:latest \
  --push \
  --progress=plain \
  50-infra/runpod/vllm-gemma-image
```

**verify**:

```bash
docker manifest inspect ghcr.io/etzhayyim/runpod-vllm-gemma:latest \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['config']['digest'], 'layers:', len(d['layers']), 'size:', sum(l['size'] for l in d['layers']))"
# 期待: sha256:... layers: 19 size: ~10.58 GB
```

2026-05-07 18:58 JST 時点の digest = `sha256:5ca9dd058deb25866f1f6f86ce44f78e7603d54730c40c669d81925b2624f2ce` (3 tag 全一致)。

### Stage B: RunPod Pod template 更新

Pod を terminate せず in-place で template image を変更 → RunPod が pod restart で新 image pull。

```bash
RUNPOD_API_KEY=$(security find-generic-password -s etzhayyim.runpod -a API_KEY -w)

# 現 pod template を取得
curl -sS https://api.runpod.io/graphql \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"query { pod(input:{podId:\"vyp99t9px7h4dl\"}) { imageName ports env { key value } } }"}' \
  | jq

# Pod restart with new image (RunPod podEditJob mutation)
# 正確な mutation 名は API doc 参照。下は schema 例:
curl -sS https://api.runpod.io/graphql \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { podEditJob(input:{podId:\"vyp99t9px7h4dl\",imageName:\"ghcr.io/etzhayyim/runpod-vllm-gemma:latest\"}) { id } }"}'
```

### Stage C: 検証

```bash
# Pod ID は不変 (vyp99t9px7h4dl)
POD=vyp99t9px7h4dl

# ComfyUI :8188
curl -sS "https://${POD}-8188.proxy.runpod.net/" | head -5
# 期待: ComfyUI HTML

# vLLM :8000
curl -sS "https://${POD}-8000.proxy.runpod.net/v1/models" | jq
# 期待: gemma-4-26B-A4B-it 系 model alias

# LiteLLM :4000
curl -sS "https://${POD}-4000.proxy.runpod.net/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer dummy' \
  -d '{"model":"gemma4","messages":[{"role":"user","content":"OK?"}]}' | jq
# 期待: choices[0].message.content = "OK"
```

### Stage D: LLM_CHAT_COMPLETIONS_URL 切替

ADR §163 に列挙された箇所が pod ID 維持のため **変更不要**:

- `50-infra/cloudflare/workers/comfyui/wrangler.jsonc` `UPSTREAM_URL` (pod ID 同じ)
- `50-infra/vultr/mitama-udf-pool/templates/zeebe-worker.yaml` `LLM_CHAT_COMPLETIONS_URL` + `etzhayyim_LLM_URL`
- `60-apps/etzhayyim-project-shinshi/.../wrangler.jsonc` `COMFY_POD_URL`

ただし wait, image 変更で port が変わるなら URL 確認。LiteLLM :4000 と vLLM :8000 が起動することを Stage C で確認後、`LLM_CHAT_COMPLETIONS_URL` が `:4000` を指していることを再確認。

### Stage E: Repo 更新

- root deps.toml L1089 `runpod-comfyui-pod-active` の image 記述を unified に書き戻す
- ADR-2605010000 に 「2026-05-07 unified image 復元 (regression 修正)」追記

## Rollback

```bash
# 5 分以内: 旧 ComfyUI-only image に template 戻す
curl -sS https://api.runpod.io/graphql \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { podEditJob(input:{podId:\"vyp99t9px7h4dl\",imageName:\"runpod/comfyui:latest\"}) { id } }"}'
```

## リスク

| リスク | 確率 | 影響 | 緩和 |
|---|---|---|---|
| ~~Docker build 失敗 (依存解決)~~ | ~~medium~~ | ~~0 (build 段階で発覚、pod 触らず)~~ | ✅ 2026-05-07 build 成功、cache hit で全層 push 済 |
| vLLM 起動失敗 (model download timeout) | medium | ComfyUI も巻き込まれて down 数分 | Network Volume `p9riuzhrvf` に model cache 確認、timeout 5min |
| supervisord で 3 process 同居 OOM (48 GiB VRAM split) | low | LLM か ComfyUI が OOM kill | ADR §47 で gpu-memory-utilization 0.70 + max-model-len 4096 検証済 |
| ComfyUI workflow 互換性 (image 切替で plugin 欠落) | low | shinshi 画像生成 fail | Stage C に shinshi smoke test 追加 |

# Path-Dependency 図

```
2026-04-22 ADR-0048 Linode→Vultr/B2 cutover  ──→  $364→$241 (−$123)
2026-04-25 B2 SlowDown cascade  ──→  ADR-0094 2-node floor  ──→  $241→$640 (compute) +$46 B2 = $689
                                       └─ 1-node $320 saving は B2 cascade リスクで bad minimax
2026-05-01 ADR-2605010000 unified pod 設計  ──→  $1100→$561 (−$539)
2026-05-05 pod 再作成時に unified image 忘れ  ──→  価値消失、価格据え置き  ◆ Task #3 で復元
2026-04-30 旧 4090 pod 再作成で auto volume  ──→  bskaa2wrjo orphan  ◆ Task #1 で削除
2026-04-25 ADR-0074 Phase 2-A geth deploy  ──→  Vultr LB pattern $11/mo
2026-04-27 blockscout で CF Tunnel pattern 確立  ──→  geth は historical pattern のまま  ◆ Task #2 で migrate
```

# 推奨実行順

1. **Task #1** (5 min, 不可逆だが downside 0)
2. **Task #2 Stage A-C** (parallel deploy で旧経路維持、検証 OK まで切替なし)
3. **Task #2 Stage D-E** (LB 撤去) — 最低 24h smoke 後
4. **Task #3 Stage A** (Docker build、pod 触らず) — 並行可
5. **Task #3 Stage B-C** (in-place image 切替) — Stage A 成功後
6. **Task #3 Stage D-E** (URL 確認 + repo 更新)
7. (Task #4) Murakumo 縮退 — Task #3 安定 1 週間後

# Out of Scope (この runbook では扱わない)

- RW 1-node 化 ($320 saving 余地、ADR-0094 で hard freeze)
- EDINET 契約 (capability 復元側、Task #5)
- blockscout deploy/delete (Task #6)
- Vultr Serverless Inference 切替 (ADR-0068 deferred)
