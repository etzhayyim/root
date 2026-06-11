---
id: ameno-end-to-end-runbook
title: ameno end-to-end runbook — laptop dev → Murakumo fleet
status: active
doc_type: how-to
topic: ameno-deployment
authoritative: true
last_verified: 2026-05-19
related:
V05190824-ameno-mediapipe-llm-browser-runtime
V05191000-ameno-browser-pregel-reflection
V05191113-ameno-active-inference-lexical-surprise
V05191120-ameno-embedding-surprise-tier-c
V05191129-ameno-browser-tool-use-react
V05191135-ameno-tier2-daemon-residency
V05191206-ameno-long-term-memory-vault
V05191229-ameno-daemon-path-a-bun-langgraph
V05191257-ameno-daemon-path-b-kotodama-python
V05191346-etzhayyim-vultr-free-murakumo-control-plane
V05191407-ameno-browser-viewer-mode
V05191524-ameno-multi-tab-swarm-broadcast
V05191559-ameno-mst-checkpointer-stage-2-activation
V05191603-ameno-swarm-leader-election
V05191608-ameno-stage-3-ipfs-pin-activation
V05191625-ameno-stage-4-l2-anchor
V05191638-ameno-substrate-swarm-lease-lex
V05191645-ameno-browser-daemon-checkpoint-sync
V05191657-ameno-daemon-did-auth
---

# ameno — end-to-end runbook

ameno は 4 つの実行モードを持つ:

| mode | substrate | LLM |
|---|---|---|
| **Tier 2 browser**(local) | browser localStorage + IndexedDB | MediaPipe Gemma 4 / WebGPU |
| **Tier 2 daemon, Path A** | `~/.ameno/` JSON | Ollama localhost |
| **Tier 2 daemon, Path B** | 同上 (laptop) / **MST + IPFS + L2 anchor (K3s)** | Ollama localhost |
| **Tier 1 fleet (K3s, lg-ameno)** | MST + IPFS + L2 anchor | ollama-fleet DaemonSet |

このランブックは **laptop dev → K3s dry-run → Mac-mini fleet**
の段階で全モードを通すための手順を一本化する。

---

## Layer 0 — laptop dev(in-browser のみ、最速)

```sh
cd 60-apps/etzhayyim-project-ameno/appview/etzhayyim-wasm-ameno-d94d27cb/svelte
pnpm install                       # workspace-level でも可
pnpm dev                           # http://localhost:5173
```

- Compute: `local` (default)
- Model select: `gemma-4-e2b-mediapipe` → **Load Model**(~2 GB DL、Cache API)
- メッセージ送信 → reflection + active inference + tools + memory vault が browser 内で完結
- Daemon panel に "Swarm: 0 peers · ★ leader" と表示

トラブル: WebGPU が無い場合 Baien fallback、`gemma-4-*-mediapipe` 系は
Chrome 113+ / Edge / Safari 18+ 限定。

---

## Layer 1 — Path A daemon(TS、Bun + Hono)

```sh
brew install bun ollama
ollama serve &
ollama pull gemma3:4b
cd 60-apps/etzhayyim-project-ameno/daemon
bun run src/server.ts              # http://127.0.0.1:12480
```

別 terminal で確認:

```sh
curl http://127.0.0.1:12480/workerInfo
curl -N -X POST http://127.0.0.1:12480/threads/demo/stream \
  -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"What time is it?"}],"toolsEnabled":true}'
```

svelte appview を Compute = `daemon @12480 (Path A, TS)` に切替 →
header chip の embed-pill が `daemon ✓ gemma3:4b · TS` に。

**真の常駐化(macOS launchd):**

```sh
# plist を編集して YOUR_USERNAME と YOUR_REPO_PATH を置換
cp 60-apps/etzhayyim-project-ameno/daemon/com.etzhayyim.ameno-daemon.plist \
   ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.etzhayyim.ameno-daemon.plist
```

Logs:`tail -f ~/.ameno/daemon.stdout.log`

---

## Layer 2 — Path B daemon(Python kotodama)

```sh
cd 40-engine/kotoba/crates/kotoba-kotodama/py
uv sync
python -m kotodama.projects.ameno  # http://127.0.0.1:12481
```

`/workerInfo` returns `kind: "path-b-python"`. svelte で Compute =
`daemon @12481 (Path B, Python)` に。

`MST_CHECKPOINT_SOCKET` 未設定なら `~/.ameno/checkpointer.json`、
設定すれば(K3s 配下のみ)MstCheckpointSaver。

**Linux 常駐化(systemd):**

```sh
sudo cp 40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/projects/ameno/ameno-daemon.service \
        /etc/systemd/system/
# User= / paths / ExecStart 編集
sudo systemctl daemon-reload
sudo systemctl enable --now ameno-daemon
journalctl -u ameno-daemon -f
```

---

## Layer 3 — K3s dry-run on Lima(1 Mac mini で 3 VM)

```sh
brew install lima socket_vmnet kubectl jq
sudo brew services start socket_vmnet
cd 50-infra/k8s/lima-k3s
./bring-up.sh
export KUBECONFIG=$(pwd)/kubeconfig
./verify.sh                        # 5 gates pass
```

3-node K3s embedded etcd HA がローカルで起動。ADR-2605191346 M1。

---

## Layer 4 — Ollama fleet(K3s 上)

```sh
kubectl label node k3s-server-01 etzhayyim.com/role=murakumo-host --overwrite
kubectl apply -f 50-infra/k8s/ollama-fleet/daemonset.yaml
kubectl -n etzhayyim-langserver exec ds/ollama -- ollama pull gemma3:4b
kubectl -n etzhayyim-langserver get pods
```

---

## Layer 5 — lg-ameno pod(Stage 2-4 全活性)

### 5a. Image 構築・push(local registry でも可)

```sh
cd 50-infra/k8s/lg-ameno
docker build -f Dockerfile -t ghcr.io/etzhayyim/lg-ameno:$(git rev-parse --short HEAD) ../../..
docker push ghcr.io/etzhayyim/lg-ameno:$(git rev-parse --short HEAD)
# kustomization.yaml の `newTag: main` を新 tag に上書きする想定
```

### 5b. apply

```sh
kubectl apply -k 50-infra/k8s/lg-ameno
kubectl -n etzhayyim-langserver rollout status deploy/lg-ameno
```

Pod 内訳:
- **server**(uvicorn + kotodama):port 8080
- **checkpointer sidecar**(`etzhayyim-sdk-checkpointer:main`):Unix
  socket `/run/etzhayyim/checkpointer.sock`

env `MST_CHECKPOINT_SOCKET` 設定済 → **MstCheckpointSaver auto-attach**
(ADR-2605191559)。 `ETZ_IPFS_API_URL` 設定済 → **Stage 3 IPFS pin**
(ADR-2605191608)。

### 5c. Stage 4(L2 anchor)

```sh
kubectl -n etzhayyim-langserver create secret generic anchor-cron-signer-ameno \
  --from-literal=key="<funded Base sepolia private key>"
kubectl apply -f 50-infra/anchor-cron/k8s/cronjob-ameno.yaml
kubectl -n etzhayyim-langserver get cronjob anchor-cron-ameno
# 15 分待つか手動:
kubectl -n etzhayyim-langserver create job --from=cronjob/anchor-cron-ameno manual-$(date +%s)
kubectl -n etzhayyim-langserver logs -l app.kubernetes.io/name=anchor-cron --tail=200 -f
```

---

## Layer 6 — public ingress(CF Tunnel + bearer / DID auth)

```sh
# CF dashboard で `ameno-daemon` tunnel 作成、token を取得
kubectl -n etzhayyim-langserver create secret generic ameno-daemon-tunnel-token \
  --from-literal=token="<paste>"
kubectl -n etzhayyim-langserver create secret generic ameno-daemon-auth \
  --from-literal=token="$(openssl rand -hex 32)"
# lg-ameno に AMENO_AUTH_TOKEN env を patch:
kubectl -n etzhayyim-langserver patch deploy lg-ameno --patch '
spec:
  template:
    spec:
      containers:
        - name: server
          env:
            - name: AMENO_AUTH_TOKEN
              valueFrom: { secretKeyRef: { name: ameno-daemon-auth, key: token } }
'
kubectl apply -f 50-infra/k8s/ameno-ingress/cloudflared-deploy.yaml
# CF dashboard で ingress rule:
#   hostname:  ameno-daemon.etzhayyim.com
#   service:   http://lg-ameno.etzhayyim-langserver.svc.cluster.local:8080
```

Verify:

```sh
curl https://ameno-daemon.etzhayyim.com/healthz                          # 200
curl https://ameno-daemon.etzhayyim.com/workerInfo                       # 401
curl -H "Authorization: Bearer <secret>" https://ameno-daemon.etzhayyim.com/workerInfo
# → 200 { kind: "path-b-python", checkpointer: "mst", ... }
```

---

## Layer 7 — browser viewer mode(remote daemon)

svelte appview を開く:

- Compute: `custom`
- URL: `https://ameno-daemon.etzhayyim.com`
- Bearer token: paste the same value as the K8s secret(ADR-2605191407)
- もしくは DID auth で:browser が自動生成した did:key 鍵で署名
  (ADR-2605191657)— bearer 入力を空にすれば DIDSig が自動付与

**Pull from daemon** ボタンで viewer thread の過去履歴を取り込み
(ADR-2605191645)。

---

## Layer 8 — multi-tab swarm 確認

1. 同 origin で 2 タブ開く
2. それぞれ Daemon panel を開く
3. **lex-smallest DID** タブに `★ leader`、もう一方に `· follower`
   が出る(ADR-2605191603)
4. Auto-respond to PDS firehose を両タブで ON にしても brief は
   leader タブのみが処理。follower タブの panel に
   "briefs skipped as follower: N" がカウントアップ

leader タブを閉じる → 5 秒以内に follower が leader に昇格、ADR の
通り。

---

## Smoke checklist(まとめ)

| layer | status check |
|---|---|
| 0 browser local | `pnpm dev` で `localhost:5173` → メッセージ送信成功 |
| 1 Path A daemon | `/workerInfo` returns `kind: undefined`(or absent), `ollamaReachable: true` |
| 2 Path B daemon | `/workerInfo` returns `kind: "path-b-python"`, `checkpointer: "file"` |
| 3 K3s HA | `kubectl get nodes` → 3 Ready, 3 etcd members |
| 4 ollama-fleet | `kubectl exec ds/ollama -- ollama list` → gemma3:4b 含む |
| 5 lg-ameno | `/workerInfo` returns `checkpointer: "mst"`, `ollamaReachable: true` |
| 6 ingress | `curl https://ameno-daemon.etzhayyim.com/healthz` → 200 |
| 7 viewer mode | browser から remote へ送信 → SSE で chunk 受信、 "Pull from daemon" で履歴復元 |
| 8 swarm | 2 タブで leader/follower 分担、 brief 二重処理なし |

---

## Decommission

```sh
# Layer 8 → 6: kubectl delete -f ... + kubectl delete secret ...
# Layer 5: kubectl delete -k 50-infra/k8s/lg-ameno
# Layer 4: kubectl delete -f 50-infra/k8s/ollama-fleet/daemonset.yaml
# Layer 3: bash 50-infra/k8s/lima-k3s/teardown.sh
# Layer 1/2: launchctl unload / systemctl disable
# Layer 0: pnpm dev を Ctrl+C
```

`~/.ameno/` 配下(DID + checkpointer.json)は手動で消す必要がある。
localStorage / IndexedDB は browser から `localStorage.clear()` で。

---

## License

Apache-2.0.
