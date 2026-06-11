---
id: doc-260514-murakumo-fleet-lan-phase5-dhcp-reservation
title: "Murakumo fleet LAN Phase 5 — NTT RX-600KI DHCP reservation runbook"
status: active
doc_type: how-to
topic: murakumo-fleet-lan-topology
authoritative: false
last_verified: 2026-05-14
related:
  - adr-2605111400-murakumo-lan-dual-router-dnsmasq
---

# Phase 5 — NTT HGW (RX-600KI) DHCP 固定 IP アドレス設定 runbook

ADR-2605111400 Phase 5 の実行手順。dnsmasq roster (`/opt/homebrew/etc/dnsmasq.d/murakumo-fleet.conf` on jacob) と物理 DHCP 割当を一致させる。

## 前提

- NTT 西日本 RX-600KI の機器設定用パスワードが既知 (初回ログイン時 user 設定、factory default なし)
- jacob から en0 経由で http://192.168.1.1/ または http://ntt.setup/ に到達可能
- Phase 1-3 完了済 (jacob + 10 mini が NTT HGW Ethernet L2 上)

## 手順 (公式ガイド準拠)

参考: [NTT 公式 RX-600KI Web 設定起動ガイド](https://flets.com/support/device/hgw/guide/600ki/4-w/8w_m1.html)

1. ブラウザで `http://ntt.setup/` (または `http://192.168.1.1/`) を開く
2. ユーザー名 `user` / パスワード <user-set> でログイン
3. **詳細設定 → DHCPv4サーバ設定 → DHCP固定IPアドレス設定** を開く
4. 「新規追加」を 11 回繰り返し、下表の MAC ↔ IP を投入
5. 各エントリ保存 → 最後に「設定保存」→ ホームゲートウェイ再起動 (オプション、推奨)

## 投入する 11 エントリ (jacob + 10 mini)

| host | MAC アドレス | 固定 IP | 用途メモ |
|---|---|---|---|
| jacob     | `1c:f6:4c:35:21:a5` | `192.168.1.9`  | control plane (dnsmasq + fleet_router + cloudflared) |
| zebulun   | `1c:f6:4c:57:c8:4d` | `192.168.1.11` | wai-real + ollama |
| issachar  | `1c:f6:4c:55:db:4b` | `192.168.1.12` | LTX + T5 + ollama |
| dan       | `1c:f6:4c:5a:34:d9` | `192.168.1.13` | animagine + ollama |
| benjamin  | `1c:f6:4c:53:5b:d4` | `192.168.1.14` | animagine + ollama |
| joseph    | `1c:f6:4c:4e:b9:2b` | `192.168.1.15` | wai-real + ollama |
| levi      | `1c:f6:4c:62:84:7d` | `192.168.1.16` | LTX + T5 + ollama |
| judah     | `1c:f6:4c:56:a9:52` | `192.168.1.17` | LiteLLM gateway + goose cron (ComfyUI なし) |
| naphtali  | `1c:f6:4c:51:1b:e7` | `192.168.1.18` | LTX + T5 + ollama |
| simeon    | `1c:f6:4c:51:5e:ec` | `192.168.1.19` | wai-real + ollama |
| asher     | `1c:f6:4c:4f:46:5c` | `192.168.1.21` | wai-real + ollama |

注: `main` (`192.168.1.66`) は NSD-G3000T WiFi 側 (broadcom 192.168.1.1 配下) なので NTT HGW DHCP 範囲外。Phase 4 の判断 (NURO 機器交換 or WiFi disable) に従う。

## 投入後の検証

```bash
# 1. mini を re-DHCP させ、固定 IP が adopt されたか確認
for h in zebulun issachar dan benjamin joseph levi judah naphtali simeon asher; do
  ssh ${h}@${h}.murakumo.lan 'sudo ifconfig en0 down && sudo ifconfig en0 up'
  sleep 5
  expected_ip=$(dig @127.0.0.1 +short ${h}.murakumo.lan | tail -1)
  actual_ip=$(ssh ${h}@${h}.murakumo.lan "ifconfig en0 | awk '/inet /{print \$2}'")
  printf "%-10s expected=%s actual=%s %s\n" "$h" "$expected_ip" "$actual_ip" \
    "$([ "$expected_ip" = "$actual_ip" ] && echo "✓" || echo "✗")"
done

# 2. dnsmasq roster と DHCP reservation が一致しているか確認
grep "address=/" /opt/homebrew/etc/dnsmasq.d/murakumo-fleet.conf
```

## Rollback

万一 NTT HGW DHCP reservation で誤った IP を設定し fleet 不通になった場合:

1. NTT HGW admin → DHCPv4 サーバ設定 → 該当エントリ削除
2. 該当 mini で `sudo ifconfig en0 down && sudo ifconfig en0 up` で再 lease
3. dnsmasq roster と arp 一致を確認

最悪、NTT HGW を工場出荷時リセット (背面 INIT ボタン長押し) — 再 PPPoE 設定が必要なので最後の手段。
