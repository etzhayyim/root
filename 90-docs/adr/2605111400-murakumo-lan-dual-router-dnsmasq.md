---
id: adr-2605111400-murakumo-lan-dual-router-dnsmasq
title: "Murakumo Mac mini Fleet LAN — dual-router topology + dnsmasq on jacob (.murakumo.lan)"
status: active
doc_type: adr
topic: murakumo-fleet-lan-topology
authoritative: true
last_verified: 2026-05-11
priority: 7.5
axis: infra
weight: 0.75
priority_note: "fleet 物理 LAN 安定化の決定ポイント。dnsmasq SSoT 化と dual-router (NTT HGW + Sony NCP) cascade の段階的解消方針"
authoritative_for:
  - murakumo-fleet-lan-resolution
  - dnsmasq-jacob-murakumo-lan-domain
  - mac-mini-fleet-ethernet-migration-policy
  - sony-ncp-broadcom-bridge-mode-target
related:
  - adr-2604251758-murakumo-yoro-actor-worker-fleet
  - adr-2604251821-vke-murakumo-multicluster-control
  - adr-0061-murakumo-platform-auth-unification
supersedes: []
superseded_by: []
amends: []
amended_by: []
---

# Goal

Mac mini fleet (10 nodes: judah / benjamin / joseph / issachar / simeon / dan / naphtali / levi / zebulun / asher) + control node jacob + auxiliary `main` の **物理 LAN を 1 つの L2 segment に統合**し、`.murakumo.lan` ドメインで安定的に名前解決できる状態を作る。
WiFi 起因の mDNS 不安定・jitter・モデル pull 飽和・スリープ復帰失敗を恒久解消する。

# Scope

- jacob (control plane, LiteLLM gateway, dnsmasq host)
- 10 inference mini (Ollama `:11434`)
- `main` (役割未確定の 12 番目 mac mini)
- broadcom 192.168.1.1 (Sony NCP NURO 系 WiFi router)
- NTT HGW 192.168.1.1 (`ntt.setup`, Ethernet 側 router/DHCP)

CF Tunnel (`murakumo-fleet ae341542`) / LiteLLM (`judah:4000`) / k3s (`lima-murakumo-gpu` on jacob) は本 ADR の scope 外 (上位レイヤーで吸収)。

# Executive Summary

- **jacob に dnsmasq を導入し、`.murakumo.lan` を fleet SSoT 命名空間とした** (2026-05-11)。`/etc/hosts` の手書きエントリ (古い IP) は purge、`dnsmasq.d/murakumo-fleet.conf` を唯一の roster とする。
- **broadcom router (Sony NCP) と NTT HGW が同一サブネット `192.168.1.0/24` を別々の DHCP / L2 で配っていることが判明** (cascaded、unbridged)。WiFi clients (jacob 含む) ⇄ Ethernet clients (有線化済 6 mini) は **L2 で相互到達不能**。
- 物理ケーブルを差した 5 mini (dan / zebulun / joseph / benjamin / levi) のうち **levi のみ Ethernet primary**、他 4 台は macOS service order で WiFi 優先のまま。Ethernet 側でも IP `.11`-`.16` を別途取得。
- **解決方針** (forward-only):
  1. jacob を NTT HGW Ethernet に有線接続 → Ethernet L2 に jacob を移す
  2. 残り 4 mini (judah / simeon / asher / naphtali) も Ethernet 配線、en0 link を active 化
  3. 各 mini で `service order = Ethernet > WiFi`、`pmset -c sleep 0`、`networksetup -setdnsservers ... 192.168.1.37 192.168.1.1` をansible で適用
  4. dnsmasq roster を Ethernet IP (`.11`-`.20`) に書き換え
  5. broadcom (Sony NCP) を bridge mode 化 (admin 物理アクセス必要)、Ethernet 側 NTT HGW に DHCP/router 機能を統一
- `60-apps/etzhayyim-project-murakumo/cmd/murakumo-netd` の WireGuard mesh 案は **不採用継続** (LAN 物理を綺麗にすれば overlay 不要)。Tailscale は SaaS 依存・ライセンス・privacy で同様に **不採用継続** (path-b roll-back 維持)。

# Decision

## D1. `.murakumo.lan` を fleet 命名空間とする

- dnsmasq on jacob (`192.168.1.37:53` LAN + `127.0.0.1:53` loopback)
- 全 fleet host は `<name>.murakumo.lan` で参照する (新規 ansible playbook / scripts / 内部 doc)
- `.local` (mDNS) 依存は段階的廃止 (WiFi 切断 / Bonjour reflector noise 耐性のため)
- `/etc/hosts` を fleet roster の SSoT として使用しない (drift しやすい)

## D2. dnsmasq SSoT location

- 設定: `/opt/homebrew/etc/dnsmasq.conf` (LAN bind, upstream forward, `local=/murakumo.lan/`)
- roster: `/opt/homebrew/etc/dnsmasq.d/murakumo-fleet.conf` (`address=/<host>.murakumo.lan/<ip>` 12 行)
- リロード: `sudo brew services restart dnsmasq` または `sudo killall -HUP dnsmasq`
- `conf-dir` は `,*.conf` suffix を**付けない** (dnsmasq の `--conf-dir,<ext>` は「skip extensions」セマンティクスで、付けると `.conf` ファイルが除外される。実装バグ的仕様)
- `expand-hosts` は **無効化** (`/etc/hosts` に手書きエントリが残ると drift を生むため)

## D3. dual-router cascade の段階的解消

Phase 1 (immediate): jacob を NTT HGW Ethernet に有線接続。Ethernet L2 segment に jacob を移し、他の有線 mini と相互到達可能にする。
Phase 2 (short-term): 残り 4 mini (judah / simeon / asher / naphtali) を Ethernet 配線。en0 link active 化。
Phase 3 (short-term): 全 mini で macOS Service Order を `Ethernet > WiFi` に変更、`pmset` で sleep 完全停止。dnsmasq roster を Ethernet IP に書き換え。
Phase 4 (medium-term): broadcom (Sony NCP) admin にアクセスし、**bridge mode (AP only, DHCP off)** に変更。WiFi/Ethernet を同一 L2 broadcast domain に統一。
Phase 5 (after Phase 4): NTT HGW で DHCP reservation 全 12 host (jacob + 10 mini + main) を MAC 固定。dnsmasq roster と reservation が物理 source-of-truth として一致する状態。

### D3.amend (2026-05-14) Phase 4 — NSD-G3000T 公式 admin UI に bridge mode なし

Sony NSD-G3000T 公式マニュアル §5.2-5.3 全項目を確認した結果、**admin UI に「ブリッジモード」「AP モード」「ルーター機能 OFF」設定は存在しない**。XGS-PON ONU 一体型仕様のため、ONU 部分はキャリア管理で bridge 化不可。

公式機能内で実行可能な dual-router 影響緩和策:
- **A. DHCP server を OFF** (§5.2.2 `DHCP サーバー` toggle) — IP 配信競合解消
- **B. 無線 LAN 2.4G/5G を OFF** (ホーム画面 toggle) — WiFi traffic を NTT HGW に強制 (※ jacob en1 も使用不可になる)
- **C. LAN IP を別 subnet に変更** (§5.2.2 `192.168.2.1` 等) — sub-net 分離で競合根絶
- **D. NURO サポート連絡** → bridge-mode 対応機種 (HG8045Q 等) への交換依頼

判断: Phase 1-3 完了で fleet 安定動作中、Phase 4 は cosmetic。判断は機器交換 (D) または DHCP/WiFi disable (A+B) の trade-off。本 ADR は **Phase 4 を deferred** とし、必要時に判断する。`main` (.66 WiFi only) は NSD-G3000T WiFi 廃止と運命を共にする。

References:
- [Sony NSD-G3000T 取扱説明書](https://www.nuro.jp/pdf/device/manual_NSD-G3000T.pdf)

## D4. macOS Service Order + WiFi Private Address policy

- 全 mac mini で `networksetup -ordernetworkservices Ethernet "Thunderbolt Bridge" Wi-Fi` を強制
- 全 mac mini で `defaults write /Library/Preferences/com.apple.airport.preferences PrivateMACAddressEnabled -bool NO` (Wi-Fi MAC 安定化、最終的に WiFi disable する前提)
- Phase 3 完了後、各 mini で `sudo networksetup -setnetworkserviceenabled Wi-Fi off` で WiFi を完全 disable
- `sudo pmset -c sleep 0 disksleep 0 womp 1 autorestart 1 powernap 0 standby 0 hibernatemode 0` を全 mini で適用 (AC 電源時 sleep 完全停止 + WoL + 停電復帰)

## D5. DNS forwarding for fleet

- 全 mini の DNS は `192.168.1.37` (jacob) primary + `192.168.1.1` (router) secondary
- `sudo networksetup -setdnsservers Ethernet 192.168.1.37 192.168.1.1`
- jacob 側 dnsmasq upstream は `192.168.1.1` (router)。ループ無し
- broadcom router 自身の DHCP option 6 (DNS) は **変更しない**。家庭 LAN 他デバイス (iPhone / iPad / 家電) への巻き込み副作用を避ける。fleet 専用 surgical override

# Comparison

| 案 | 物理 LAN | overlay | SaaS依存 | 解説 |
|---|---|---|---|---|
| A. 採用案 (本 ADR) | NTT HGW Ethernet 単一 L2 | なし | なし | broadcom を bridge mode 化、`.murakumo.lan` で fleet 解決 |
| B. WireGuard mesh (`murakumo-netd`) | WiFi のまま | wg0 10.77.0.0/24 | なし | LAN 物理問題をソフト overlay で隠す。複雑度 high。本 ADR で**不採用維持** |
| C. Tailscale mesh | WiFi のまま | Tailscale net | あり (Tailscale Inc.) | ADR-path-b で既に rollback。SaaS 依存 + ACL コスト |
| D. macOS Internet Sharing (jacob hotspot) | jacob を AP 化 | なし | なし | mac mini 1 台で 11 client は不安定、Apple Silicon は WiFi→WiFi share 不可、検証で却下 |
| E. 別 WiFi router 追加 (mesh AP) | WiFi 経由 backhaul | なし | なし | 物理ケーブルが通せない場合の選択肢。本案件はケーブル通せるので不採用 |

# Exceptions

- `main` (`192.168.1.66`) は役割未確定。Ollama 反応なし、Bonjour `_ssh._tcp` には advertise。当面 dnsmasq roster に "auxiliary node" としてエントリのみ残す。物理 wiring は user 判断。
- jacob 自身は dnsmasq host + DNS server なので、jacob 落下 = 全 mini の DNS 解決が secondary (`192.168.1.1`) に fallback。`.murakumo.lan` は引けなくなるが外部 DNS は維持。jacob HA は本 ADR では不要 (single-operator workflow)。

# Consequences

### Positive
- `.local` mDNS の不安定さから完全離脱
- `judah.murakumo.lan` 等の安定 FQDN で全 fleet 参照可能、ansible inventory / scripts / runbook の安定化
- WiFi 起因の jitter / 切断 / 8-of-11 unresolved 問題が物理 Ethernet 化で消滅予定
- broadcom bridge 化後、DHCP / ARP / L2 が単一化、fleet topology が直感どおりに動く
- `60-apps/etzhayyim-project-murakumo/cmd/murakumo-netd` (WireGuard overlay) や Tailscale を導入しなくて済む。コード surface 縮小

### Negative / Risk
- Phase 1-3 完了まで「物理は cascaded だが dnsmasq 上は統一」という乖離状態が続く。fleet 内通信は Ethernet 側に集約され、jacob 経由 LiteLLM / CF Tunnel は WiFi 経由のまま (移行期間)
- broadcom bridge 化 (Phase 4) は admin 物理アクセスが必要。NURO 提供 HGW の admin block (jacob から TCP connect 後 silent drop) を解除する手段が現状未確認
- `/etc/hosts` を purge したことで、libc gethostbyname で `judah` (bare) を解決していたスクリプトがあれば破綻。**`.murakumo.lan` FQDN への置換を要請**

# Live Inventory Snapshot (2026-05-11)

| host | en0 (Ethernet) MAC | en0 IP | WiFi IP (現状) | Ollama | wiring status |
|---|---|---|---|---|---|
| jacob | `1c:f6:4c:35:21:a5` | (link inactive) | `192.168.1.37` | 200 (LAN side via bridge100) | **要 wiring (Phase 1)** |
| judah | `1c:f6:4c:56:a9:52` | (link inactive) | `192.168.1.56` | 200 | 要 wiring |
| benjamin | `1c:f6:4c:53:5b:d4` | `192.168.1.14` | `192.168.1.51` | 200 | 物理済、service order 未 |
| joseph | `1c:f6:4c:4e:b9:2b` | `192.168.1.15` | `192.168.1.49` | 200 | 物理済、service order 未 |
| issachar | `1c:f6:4c:55:db:4b` | `192.168.1.12` | `192.168.1.60` | 200 | 物理済、service order 未 |
| simeon | `1c:f6:4c:51:5e:ec` | (link inactive) | `192.168.1.55` | 200 | 要 wiring |
| dan | `1c:f6:4c:5a:34:d9` | `192.168.1.13` | `192.168.1.58` | 200 | 物理済、service order 未 |
| naphtali | `1c:f6:4c:51:1b:e7` | (link inactive) | `192.168.1.64` | transient | 要 wiring |
| levi | `1c:f6:4c:62:84:7d` | `192.168.1.16` | `192.168.1.50` | 200 | 物理済、Ethernet primary ✅ |
| zebulun | `1c:f6:4c:57:c8:4d` | `192.168.1.11` | `192.168.1.67` | 200 | 物理済、service order 未 |
| asher | `1c:f6:4c:4f:46:5c` | (link inactive) | `192.168.1.63` | 200 | 要 wiring |
| main | (unknown) | — | `192.168.1.66` | — | auxiliary, 役割未確定 |

注: en0 IP `.11`-`.16` は **NTT HGW Ethernet 側の DHCP リース**。WiFi IP `.37`-`.67` は **broadcom (Sony NCP) WiFi 側の DHCP リース**。両者は別 L2、jacob (WiFi) からは Ethernet IP に直接到達**不可**。

# Migration tracking

`deps.toml [[migrations]] murakumo-fleet-lan-dnsmasq-ethernet-unification` を SSoT とする。Phase 1-5 の進捗はこの migration entry で追跡。

# References

- `/opt/homebrew/etc/dnsmasq.conf` (jacob, 2026-05-11)
- `/opt/homebrew/etc/dnsmasq.d/murakumo-fleet.conf` (jacob, 2026-05-11)
- `/etc/resolver/murakumo.lan` (jacob, 2026-05-11) — macOS Stub Resolver
- `/etc/hosts.bak-20260511-murakumo` (jacob, 2026-05-11) — pre-purge backup
- `60-apps/etzhayyim-project-murakumo/CLAUDE.md` — fleet architecture overview
- `60-apps/etzhayyim-project-murakumo/cmd/murakumo-netd/README.md` — WireGuard overlay (不採用継続)
- `60-apps/etzhayyim-project-murakumo/ansible/inventory/hosts.yml` — ansible fleet inventory
- `50-infra/multicluster/murakumo-vke/README.md` — Karmada multi-cluster topology
- ADR-2604251758 (yoro-actor-worker-fleet)
- ADR-2604251821 (vke-murakumo-multicluster-control)
