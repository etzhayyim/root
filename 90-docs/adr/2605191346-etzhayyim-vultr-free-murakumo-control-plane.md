---
id: 2605191346-etzhayyim-vultr-free-murakumo-control-plane
title: etzhayyim is Vultr-free — Murakumo Mac-mini fleet as the only Tier-1 substrate
status: proposed
doc_type: adr
topic: etzhayyim-decentralized-control-plane
authoritative: true
last_verified: 2026-05-19
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172800-geth-private-migration-to-etzhayyim
  - 2605182312-local-bring-up-murakumo-gemma4
related:
V05191229-ameno-daemon-path-a-bun-langgraph
V05191257-ameno-daemon-path-b-kotodama-python
supersedes:
  - "(strengthens, does not delete) 2605172800-geth-private-migration-to-etzhayyim §Option C"
---

# ADR 2605191346: etzhayyim is Vultr-free — Murakumo Mac-mini fleet as the only Tier-1 substrate

## Context

Two governance contexts share the monorepo today:

| brand | governance | substrate | Vultr policy |
|---|---|---|---|
| **etzhayyim.com** (legacy commercial) | etzhayyim Co., Ltd. | Vultr VKE + Cloudflare | **keep** (out of scope for this ADR — operator's choice) |
| **etzhayyim** (open religious-corp, this repo) | 宗教法人 任意団体 (on-chain) | Murakumo Mac-mini fleet + Cloudflare edge | **fully exit** (this ADR) |

ADR-2605172000 already declared "kotoba / no centralized DB" but did NOT explicitly state "no commercial K8s control plane". ADR-2605172800-geth ("geth-private migration") left the cluster question staged ("can stay on Vultr ... until natural infra-refresh time") with three migration Options A/B/C.

Grep evidence(2026-05-19 時点)で残る Vultr 依存:

- `50-infra/vultr/{geth-private, blockscout, ipfs, kotoba, zeebe}` — VKE manifests
- `ADR-2605172800-geth.md:50` — "K8s deployment can stay on Vultr under etzhayyim's governance contract"
- `ADR-2605173100:134` — past `45.32.79.245` Vultr IP released, audit trail
- `50-infra/k8s/atproto-pds/README.md:37` — references `50-infra/vultr/geth-private/manifests/` as cloudflared sidecar precedent

User mandate(2026-05-19):

> "vulter は etzhayyim.com 用に残します。etzhayyim は完全に分離"

これを **architectural hard rule** に昇格させる。

## Decision

**etzhayyim/* に属する全ワークロードは Vultr 一切非依存。Tier-1 実行基盤は Murakumo Mac-mini fleet のみ。**

### 1. Substrate hard rule

| 階層 | 役割 | 唯一の実行基盤 |
|---|---|---|
| **Tier 0 — edge delivery** | static asset + DID + thin XRPC routing | Cloudflare Workers / Pages (CDN として retain) |
| **Tier 1 — long-running compute** | langserver pods, geth-private, atproto-pds, lg-* Pregel | **Murakumo Mac-mini fleet(10 nodes、ADR-2605182312)** |
| **Tier 2 — host-resident daemon** | ameno-daemon (Path A / B), other user daemons | user's macOS / Linux box(launchd / systemd) |
| **Tier 3 — browser edge** | ameno svelte appview, viewer modes | user's browser(WebGPU / WASM) |

**禁止**: etzhayyim/* 配下のいかなる manifest / Dockerfile / service が:
- Vultr VKE / VPS / Object Storage を指す
- 他社 commercial K8s(EKS / GKE / AKS / DigitalOcean Kubernetes 等)を target
- "we will deploy this to Vultr later" の含意を持つ

### 2. Repository directory split — Hard boundary

| パス | 帰属 | Vultr OK? |
|---|---|---|
| `50-infra/vultr/*` | **etzhayyim.com legacy** | ✅(本 ADR 範囲外) |
| `50-infra/k8s/*` | **etzhayyim Murakumo target** | ❌ Murakumo のみ |
| `50-infra/etzhayyim-*` | etzhayyim 専用 | ❌ Murakumo / Cloudflare のみ |
| `60-apps/etzhayyim-project-*` | etzhayyim app(legacy 名前は移行中) | ❌ |
| `20-actors/*` | etzhayyim Python/TS package | ❌ |

`50-infra/vultr/` ディレクトリは **将来別 repo(`etzhayyim-co-jp/legacy-vultr-manifests` 等)に物理分離**することを follow-up タスクとして登録(本 ADR 内では rename しない、repo-root `CLAUDE.md` Step 8 cutover の一部として実施)。

### 3. Control plane choice — primary / secondary

ameno daemon の Path A (launchd) / Path B (systemd) を作る過程で「K8s 非依存の OS-resident daemon が現実的に十分軽量」と確認済。本 ADR でも **可能な限り native OS daemon を優先**、K3s は重い workload にだけ採用する:

| Workload 種別 | 推奨 control plane |
|---|---|
| **stateless agent loop**(ameno-daemon Path A/B、agent_daemon_main) | **native systemd / launchd**(K8s なし) |
| **HA stateful service**(geth-private statefulset、atproto-pds、PDS firehose) | **K3s on 3 Mac minis HA**(Lima/OrbStack で Linux VM、`murakumo-kubelet` を unwind して通常の k3s nodes に) |
| **ad-hoc burst compute**(comfyui, training runs) | **murakumo-kubelet on top of K3s**(virtual-kubelet を on-prem K3s に接続、cloud K8s 廃止) |

K3s 採用基準: 単一 Mac mini ノード障害で復旧が困難な永続状態を持つ service のみ。それ以外は native daemon 一択。

#### K3s HA topology(採用ケース)

```
3× Mac mini (kishu-mac-{01,02,03}.local)
  └─ Lima or OrbStack で Ubuntu 24.04 VM
     └─ k3s server (--cluster-init for 01, --server https://01:6443 for 02/03)
        └─ embedded etcd HA(3-node 自動 leader election)

7× Mac mini (kishu-mac-{04..10}.local)
  └─ macOS native + murakumo-agent
     └─ murakumo-kubelet → virtual-kubelet node を上記 K3s に登録
        └─ kubectl apply 時に nodeSelector で macOS native node に schedule

control plane access:
  kubectl --kubeconfig ~/.kube/etzhayyim.yaml  → kishu-mac-01.local:6443
```

ingress / external 公開は **Cloudflare Tunnel(`cloudflared`)** で K3s service → public hostname。Vultr VKE で使ってた tunnel pattern と同形。

#### Native daemon path(優先採用)

ADR-2605191229 / 2605191257 が確立した pattern:

```
launchd plist / systemd unit
  → bun / node / python
     → graph + ollama + checkpointer(file-backed)
       → ~/.ameno/{worker-did, checkpointer.json}
```

新規 etzhayyim service が小さい / stateful 度が低いなら、K3s ではなくこの pattern で書く。

### 4. geth-private migration — Option C 確定

ADR-2605172800-geth の **Option C(Mac-mini fleet 移管)を本 ADR で確定**:

| ADR-2605172800 Options | 本 ADR での判断 |
|---|---|
| Option A: "Vultr 残置 + governance contract 継続" | **却下**(Vultr 完全離脱方針と矛盾) |
| Option B: "別 cloud K8s(EKS/GKE 等)に rehome" | **却下**(commercial K8s 依存を残す) |
| Option C: "Mac-mini fleet にローカル rehome" | **採用** |

migration plan:
1. Mac-mini fleet に K3s HA(上記 topology)を bring-up
2. `50-infra/k8s/geth-private/`(本 ADR 内で新設)に Vultr manifest を K3s 互換に書き換えて移植
3. statefulset PVC を `local-path-provisioner`(K3s 同梱)に置き換え、Mac-mini SSD を data path に
4. genesis block 同一性確認 → Cloudflare Tunnel ingress 切替
5. 旧 Vultr namespace を destroy(本 ADR の deadline 内で)

ただし geth-private は **chain 整合性が最優先** なので、tested migration script + rollback plan が揃うまで実施しない。Follow-up ADR で migration runbook を作成。

### 5. Cloudflare の扱い

Cloudflare Workers / Pages / Tunnel / Registrar は **本 ADR では retain**(理由):

| 機能 | 性格 | etzhayyim の自律性に対する影響 |
|---|---|---|
| Workers(stateless edge handler) | ephemeral compute | 小。state は MST/IPFS/L2 に存在、Workers は薄い router |
| Pages / Workers Assets | static delivery | 小。CDN 役割 |
| Tunnel(cloudflared) | ingress | 小。代替は Headscale + Tailscale など |
| Registrar | DNS | 中。`etzhayyim.com` 所有権は CF account に紐づく |

完全 CF 離脱は別 ADR(`etzhayyim-cf-exit-self-host-pds`、未起草)で検討する。本 ADR の **Vultr 離脱** とは独立の議論。

### 6. Deadlines

| マイルストーン | 期限(JST) | 内容 |
|---|---|---|
| M0 — 本 ADR active 化 | 2026-05-31 | review 完了、status → active |
| M1 — K3s HA on 3 Mac minis bring-up | 2026-06-15 | 3-node embedded etcd、kubectl 接続可能 |
| M2 — `50-infra/k8s/` migration matrix 完成 | 2026-06-30 | 各 manifest の deploy target 明文化 |
| M3 — geth-private rehome run-book | 2026-07-15 | tested migration script + rollback |
| M4 — geth-private dry-run on Murakumo | 2026-08-01 | parallel run、original Vultr 維持 |
| M5 — geth-private production switch | 2026-08-15 | Cloudflare Tunnel 切替、24h soak |
| M6 — 旧 Vultr namespace decommission | 2026-09-01 | etzhayyim governance 下の Vultr namespace 全削除 |
| M7 — `50-infra/vultr/*` 物理分離 | 2026-09-15 | 別 repo(etzhayyim-co-jp 側)へ移動、本 repo から削除 |

deadline 不達時は対応 ADR 起草で説明責任。

## Consequences

- **architectural sovereignty**: etzhayyim は単一の commercial cloud に支配されない構造を確立。Tier 1 Mac-mini fleet 障害以外で全停止しない
- **etzhayyim.com / etzhayyim の構造的境界が確定**: 同 monorepo 内でも directory レベルで分かれ、deploy target が混在しない
- **K3s on Mac-mini 学習コスト**: Lima/OrbStack の Linux VM、embedded etcd、local-path-provisioner、cloudflared sidecar の運用 know-how を新規習得必要
- **geth-private migration risk**: chain state を Vultr から Mac-mini に移す operation はリスクが高い。十分な runbook + dry-run 後にのみ実施
- **Cloudflare 依存は残る**(本 ADR 範囲外)— "decentralized" としては不完全だが、step-wise なので明示
- **既存 ADR との整合**:
  - ADR-2605172000(kotoba)に "no commercial K8s" を追加する形で強化
  - ADR-2605172800-geth-private の Option C を確定 = `supersedes` でなく `strengthens`
  - ADR-2605191229 / 2605191257(ameno daemon Path A/B)は K8s 非依存なので本 ADR の直系
  - ADR-2605191135(Tier-2 daemon residency)の "true 常駐化 path forward" を本 ADR が回収

## Alternatives Considered

1. **Status quo(Vultr 残置)** — etzhayyim.com と inseparable な状態が固定。governance / sovereignty 主張が空文化。reject(user の明示判断)
2. **EKS / GKE / DigitalOcean K8s に rehome** — Vultr 離脱だけど commercial K8s 依存は維持。"decentralized" の意味が薄まる。reject
3. **K8s を完全に捨てて native systemd / launchd only** — 既存 manifest 投資を失う。geth-private のような HA stateful service の運用が手作業に。**K3s on Mac-mini を採用するが、軽い service は native** という hybrid を選択
4. **Self-host K3s on rented bare metal**(Hetzner / OVH 等) — Vultr 同等の commercial 依存度。reject
5. **HashiCorp Nomad on Mac-mini** — K8s より軽量だが学習コスト + community 規模で K3s に劣る。reject

## References

- ADR-2605170900(etzhayyim/root が ADR canonical home)
- ADR-2605172000(kotoba substrate — 本 ADR が "K8s-cloud-free" を追加)
- ADR-2605172800-geth-private-migration-to-etzhayyim(Option C を本 ADR で確定)
- ADR-2605182312(Murakumo Mac-mini bring-up)
- ADR-2605191229 / 2605191257(ameno daemon Path A/B — K8s-free reference impl)
- ADR-2605191135(Tier-2 daemon residency)
- K3s docs: <https://docs.k3s.io>
- murakumo-kubelet README: `50-infra/k8s/murakumo-kubelet/README.md`
- Lima(Linux VM on macOS): <https://lima-vm.io>
- OrbStack: <https://orbstack.dev>
