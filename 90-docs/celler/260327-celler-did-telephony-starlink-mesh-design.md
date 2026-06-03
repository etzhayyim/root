# Celler: DID-Addressed Encrypted Telephony over Starlink Mesh

**Status**: `[DESIGN]`
**Date**: 2026-03-27
**Author**: AI Agent
**Domain**: celler.etzhayyim.com

## 1. Problem Statement

従来の電話通信はキャリア (MNO) に完全依存する。基地局・SIM・番号管理すべてがキャリアの管理下にあり、災害時・僻地・紛争地では通信手段が断絶する。

Celler は Starlink 衛星インターネット + WiFi Direct mesh + Telnyx SIP trunk を組み合わせ、既存キャリアに依存しない DID ベースの暗号化電話通信網を構築する。

## 2. Honest Framing

これは「セルラーネットワーク」ではない。技術的には **DID-addressed, Signal-encrypted, Starlink-backhauled voice/data overlay network**。

| できること | できないこと |
|---|---|
| WiFi Direct P2P 通話 (Android) | LTE/5G 基地局の代替 (要免許) |
| BLE デバイス発見 | iOS での WiFi Direct mesh (API 非公開) |
| WebRTC 音声/映像 over Starlink | キャリアグレード QoS |
| Signal Protocol E2E 暗号化 | 緊急通報の法的保証 |
| DID ベースのアドレッシング | |
| Telnyx 70+ 国で電話番号取得 | |
| Telnyx eSIM 180+ 国 data | |
| AI リアルタイム翻訳 | |

免許不要: WiFi (ISM帯) + BLE (ISM帯) + Starlink (SpaceX licensed) のみ使用。

## 3. Provider Selection: Telnyx 一本化

### 3.1 Why Telnyx

eSIM + SIP trunk + 番号プロビジョニング + WebRTC gateway を単一 API で提供する唯一の provider。

| capability | Telnyx | Twilio (比較) |
|---|---|---|
| SIP trunk | 70+ 国 | 100+ 国 |
| eSIM | 180+ 国 (Telnyx Wireless) | 200+ 国 (Super SIM) |
| 統一 API | Yes (Mission Control) | Yes |
| 通話コスト | $0.005-0.02/分 | $0.01-0.05/分 |
| 番号コスト | $1-5/月 | $1-15/月 |
| eSIM コスト | $2/SIM + data 従量 | $2/SIM + $0.10/MB |
| WebRTC gateway | built-in | built-in |
| Private Wireless | Yes | No |

Telnyx は Twilio の 1/3〜1/5 のコストで同等機能を提供。

### 3.2 eSIM vs SIP Trunk (概念整理)

| | eSIM | SIP Trunk |
|---|---|---|
| 何か | スマホのデータ通信回線 (SIMのソフトウェア版) | 電話網 (PSTN) への接続回線 |
| 提供するもの | インターネット接続 (LTE/5G) | 電話番号 + 発着信 |
| 例え | 「道路」(データが通る道) | 「電話局との契約」(番号をもらう) |
| Celler での役割 | Starlink がない場所での data connectivity | 普通の電話への発着信 |

両方必要: eSIM でインターネットに繋がり、SIP trunk で電話番号を持つ。

### 3.3 SIP サーバー (OSS) vs SIP Trunk (有料)

SIP **サーバー** (PBX / Proxy) は OSS で自前構築可能。SIP **Trunk** (キャリアとの接続) は有料サービス。

| component | 自前? | 選択 |
|---|---|---|
| SIP Proxy / PBX | OSS (FreeSWITCH, Kamailio, Asterisk) | FreeSWITCH on CF Container |
| SIP ↔ WebRTC gateway | OSS (FreeSWITCH mod_verto) | 同上 |
| PSTN 接続 (SIP Trunk) | No (キャリア設備が必要) | Telnyx SIP Trunk |
| 番号プロビジョニング | No (キャリアが番号ブロック保有) | Telnyx Number API |
| eSIM プロビジョニング | No (RSP infra が必要) | Telnyx Wireless API |

## 4. Architecture

### 4.1 System Overview

```
┌──────────────────────────────────────────────────────┐
│                 Telnyx (単一 Provider)                │
│                                                      │
│  SIP Trunk ──── eSIM API ──── Number API             │
│  (70+ 国)      (180+ 国)     (番号 provision)        │
│                                                      │
└────────┬──────────┬──────────────┬───────────────────┘
         │SIP       │eSIM data     │API
         ▼          ▼              ▼
┌────────────────────────────────────────────┐
│           Cloudflare Edge                  │
│                                            │
│  FreeSWITCH (Container) ── SIP ↔ WebRTC   │
│  Calls (SFU/TURN) ──────── media relay     │
│  PDS (Worker) ───────────── signaling      │
│  yata (Container) ──────── CDR / graph     │
└────────────────────┬───────────────────────┘
                     │ WebRTC / XRPC
         ┌───────────┼───────────────┐
         ▼           ▼               ▼
    [Phone A]   [Phone B]      [Phone C]
         │           │
         └─WiFi Direct mesh─┘
```

### 4.2 Network Layer Stack

#### Layer 0: Discovery

| method | range | platform | purpose |
|---|---|---|---|
| BLE Beacon | ~30m indoor, ~100m outdoor | Android + iOS | discovery only (DID hash 8 bytes) |
| WiFi Aware (NAN) | ~70m | Android 8+ | service discovery without association |
| mDNS/DNS-SD | LAN | all | `_etzhayyim-celler._tcp.local.` |

BLE scanning: 2s active, 8s passive (battery optimization)。

#### Layer 1: Transport

| transport | bandwidth | latency | when |
|---|---|---|---|
| WiFi Direct | 50-250 Mbps | <5ms | nearby devices (mesh) |
| Starlink | 50-200 Mbps | 25-60ms | WAN backhaul |
| Telnyx eSIM (LTE/5G) | 10-100 Mbps | 20-50ms | no Starlink available |
| WiFi LAN | varies | <5ms | same network |

Starlink 制約: CGNAT → TURN 必須。衛星 handoff 15 秒ごと → 0-50ms jitter spike。

#### Layer 2: Mesh Routing

B.A.T.M.A.N. 簡易版 (application-layer over WiFi Direct)。

Routing table: `Map<DID, NextHopDID, HopCount, RTT, LastSeen>`

Route discovery:
1. `ROUTE_REQUEST(src_did, dst_did, seq, ttl=5)` を WiFi Direct neighbor に flood
2. 各 hop が自 DID を append して forward
3. Destination が `ROUTE_REPLY` を reverse path で返す
4. Source が lowest RTT / fewest hops を選択

Route maintenance:
- Heartbeat 10s to direct neighbors
- 3 missed heartbeats (30s) → link failure
- `ROUTE_ERROR` propagation → alternative route
- Max mesh diameter: 5 hops (voice quality degrades beyond 3)

#### Layer 3: Voice/Video

| media | codec | bitrate | use case |
|---|---|---|---|
| Voice (normal) | Opus 24kHz | 16kbps VBR | Starlink / eSIM |
| Voice (mesh) | Opus 8kHz SILK | 6kbps | multi-hop mesh (low BW) |
| Video | VP9 | adaptive | Starlink / eSIM |
| Video fallback | H.264 | adaptive | older devices |

WebRTC signaling:
- Internet available: `com.etzhayyim.rtc.*` XRPC via PDS
- Local mesh (no internet): WiFi Direct data channel + CBOR-serialized W Protocol messages

Encryption (2 layers):
1. **SRTP** (WebRTC native): DTLS-SRTP per session
2. **Signal Protocol E2E**: X3DH + Double Ratchet on SDP + optional insertable streams for media frames

#### Layer 4: Telephony

DID-based identity: `did:web:celler.etzhayyim.com:{user_path}` (電話番号不要)。

Call routing priority:
1. Local mesh (WiFi Direct range) — direct P2P, zero server
2. Same Starlink LAN (mDNS) — direct P2P
3. Starlink → Internet → Starlink — WebRTC via STUN
4. TURN relay — NAT traversal failure fallback
5. PSTN bridge — Telnyx SIP trunk (calling traditional phones)

### 4.3 Number Provisioning per Country

Telnyx API が国別の番号体系の違いを吸収。

| country | VoIP number | type | regulation |
|---|---|---|---|
| JP | 050-XXXX-XXXX | IP phone | 電気通信事業届出 |
| US | +1-XXX-XXX-XXXX | local (VoIP区別なし) | FCC不要 (reseller) |
| UK | +44-56-XXXX | VoIP | 一般認可 |
| DE | +49-32-XXXX | VoIP | KYC 必須 |
| FR | +33-09-XXXX | VoIP | KYC 必須 |
| AU | +61-0550-XXXX | VoIP | 即日 |
| KR | +82-070-XXXX | VoIP | 現地法人必要 |
| SG | +65-3XXX | local | 登録必要 |

User registration flow:
```
1. Sign up → DID: did:web:celler.etzhayyim.com:{user}
2. Country detect (IP/GPS/manual)
3. Telnyx API: provision local number
4. Bind: DID ↔ E.164
5. Telnyx API: provision eSIM profile → QR code → install
6. Complete: DID + number + data connectivity in 1 step
```

### 4.4 eSIM Provisioning

Telnyx Wireless eSIM flow:
```
Telnyx API: Create SIM profile
  → eSIM activation code (QR code)
  → User scans QR on smartphone
  → eSIM profile downloaded via SM-DP+
  → LTE/5G data active (180+ countries)
```

API management: SIM status, data usage, plan changes, suspend/resume all via Telnyx Mission Control API.

## 5. Entity Model (Cypher)

### 5.1 Nodes

```cypher
(:Device {
  device_id, did, device_type, os,
  ble_uuid, wifi_direct_mac,
  last_seen, latitude, longitude, battery_pct,
  org_id, user_id, actor_id
})

(:Gateway {
  gateway_id, did, starlink_dish_id,
  latitude, longitude,
  uplink_mbps, downlink_mbps, latency_ms, status,
  org_id, user_id, actor_id
})

(:Cell {
  cell_id, did, name,
  center_lat, center_lon, radius_m,
  device_count, gateway_id, status,
  org_id, user_id, actor_id
})

(:Call {
  call_id, caller_did, callee_did,
  state, start_time, connect_time, end_time, duration_ms,
  codec, transport, quality_mos,
  org_id, user_id, actor_id
})

(:Channel {
  channel_id, did, name,
  max_participants, encryption,
  org_id, user_id, actor_id
})

(:PhoneNumber {
  e164, did, provider, sip_uri,
  country_code, number_type, status,
  org_id, user_id, actor_id
})

(:ESimProfile {
  iccid, provider, coverage,
  data_remaining_mb, activated_at, expires_at, status,
  org_id, user_id, actor_id
})

(:NumberPool {
  country_code, number_type, prefix,
  provider, available_count,
  org_id
})
```

### 5.2 Edges

```cypher
(:Device)-[:MESH_LINK { rssi, throughput_mbps, latency_ms, hop_count, link_type, last_ping }]->(:Device)
(:Device)-[:UPLINKS_TO { via, signal_strength, connected_since }]->(:Gateway)
(:Device)-[:MEMBER_OF]->(:Cell)
(:Device)-[:HAS_NUMBER]->(:PhoneNumber)
(:Device)-[:HAS_ESIM]->(:ESimProfile)
(:Gateway)-[:SERVES]->(:Cell)
(:Device)-[:PARTICIPATES_IN { role, joined_at, left_at }]->(:Call)
(:Call)-[:ROUTES_THROUGH { direction, latency_added_ms }]->(:Gateway)
(:Device)-[:JOINED { role, joined_at }]->(:Channel)
(:PhoneNumber)-[:FROM_POOL]->(:NumberPool)
```

## 6. WIT Capabilities

Package: `etzhayyim:celler@1.0.0`

### 6.1 Interfaces

| interface | NSID prefix | operations |
|---|---|---|
| call | `com.etzhayyim.apps.celler.call` | initiate, answer, reject, hold, resume, end, get, list |
| mesh | `com.etzhayyim.apps.celler.mesh` | register_device, discover_peers, report_link, get_topology, find_route, report_heartbeat |
| gateway | `com.etzhayyim.apps.celler.gateway` | register, get, list, report_metrics |
| phone_number | `com.etzhayyim.apps.celler.phone_number` | provision, release, bind_to_did, lookup_did_by_number, lookup_number_by_did |
| sip_gateway | `com.etzhayyim.apps.celler.sip_gateway` | handle_inbound, initiate_outbound |
| esim | `com.etzhayyim.apps.celler.esim` | provision, activate, suspend, resume, get_usage |
| voice_ai | `com.etzhayyim.apps.celler.voice_ai` | transcribe_voicemail, classify_call, translate_stream |

### 6.2 Existing NSID Reuse

| NSID | purpose |
|---|---|
| `com.etzhayyim.rtc.sendCallOffer` | SDP offer |
| `com.etzhayyim.rtc.sendCallAnswer` | SDP answer |
| `com.etzhayyim.rtc.sendCallICE` | ICE candidates |
| `com.etzhayyim.rtc.hangupCall` | Call termination |
| `com.etzhayyim.signal.*` | Signal Protocol E2E |
| `chat.bsky.convo.*` | Text messaging |

## 7. AI Agent Integration

Each `:Cell` gets a path-based DID with AI agent: `did:web:celler.etzhayyim.com:cell:{name}`

| capability | method | latency |
|---|---|---|
| Real-time translation | Murakumo STT → LLM → TTS | ~500ms |
| Voicemail-to-text | Murakumo Whisper STT | <5s |
| Spam detection | DID trust score + Murakumo classifier | <100ms |
| Routing optimization | Mesh topology graph analysis | continuous |
| Network health | Per-cell monitoring + alerting | 10s interval |

Translation uses WebRTC insertable streams to intercept, process, and re-inject audio frames.

## 8. Infrastructure

### 8.1 Cloudflare Components

| component | type | purpose |
|---|---|---|
| FreeSWITCH | Container | SIP ↔ WebRTC gateway |
| STUN server | Container | NAT type detection |
| TURN relay | Container (multi-region) | Media relay for CGNAT |
| Cloudflare Calls | Managed | WebRTC SFU (group calls) |
| PDS | Worker | Signaling + DID resolution |
| yata | Container | CDR + graph storage |

### 8.2 Hardware

| required | optional |
|---|---|
| Starlink Dish + Router ($299-599) | GL.iNet travel router ($70) — mesh relay |
| Android smartphone (WiFi Direct capable) | Raspberry Pi ($50-80) — dedicated mesh node |
| Telnyx account | iOS (WebRTC only, no mesh) |

## 9. Regulatory

### 9.1 Spectrum

免許不要。WiFi (2.4/5/6 GHz ISM) + BLE (2.4 GHz ISM) + Starlink (Ku/Ka, SpaceX licensed)。

### 9.2 Telecom Registration

| country | 050-equivalent | requirement |
|---|---|---|
| JP | 050 | 電気通信事業届出 (簡易) |
| US | local number | FCC 登録不要 (reseller) |
| UK | 056 | Ofcom 一般認可 |
| EU | varies | eIDAS 準拠 |

### 9.3 Emergency Calls

Celler は licensed carrier ではないため、緊急通報の法的義務なし (OTT app 扱い)。

Design: 緊急番号検出 → native dialer にハンドオフ。SIM なし + Starlink only → PSTN bridge + GPS。

### 9.4 Lawful Intercept

Signal Protocol E2E のためサーバー側でのコンテンツ復号は不可能。Metadata (CDR: caller/callee DID, timestamp, duration) は yata graph に保存され、legal order で提出可能。

## 10. Cost Model (1,000 users)

| item | monthly |
|---|---|
| Telnyx numbers (1,000) | ~$2,000 |
| Telnyx voice (10 min/user/day) | ~$1,500 |
| Telnyx eSIM (1,000) | ~$2,000 |
| Cloudflare (Calls + Containers) | ~$700 |
| **Total** | **~$6,200/mo (~¥930/user)** |

## 11. Phased Implementation

### Phase 1: MVP — WebRTC + Telnyx (8 weeks)

- App (main.go) + WIT + magatama.jsonld
- Telnyx SIP trunk integration
- Telnyx Number API: 番号自動プロビジョニング
- Telnyx Wireless API: eSIM プロビジョニング
- FreeSWITCH on CF Container (SIP ↔ WebRTC)
- Signal Protocol E2E on signaling
- STUN/TURN deployment
- Call UI (iframe mode)
- CDR → yata graph

### Phase 2: Local Mesh (8 weeks)

- Android native companion (WiFi Direct + BLE require native API)
- BLE discovery → WiFi Direct negotiation
- Local signaling over WiFi Direct data channel
- Application-layer mesh routing (2-3 hops)
- Gateway registration (Starlink terminal as uplink)
- Cell formation logic (auto-cluster nearby devices)

### Phase 3: Full Network + AI (8 weeks)

- Per-cell AI agent (Murakumo integration)
- Real-time translation (STT → LLM → TTS)
- Voicemail-to-text, spam detection
- Network health dashboard (maps.etzhayyim.com integration)
- Multi-cell handoff
- 080 番号 (MVNE 契約 + 電気通信事業登録)
- iOS companion (WebRTC only mode)

## 12. Related Projects

| project | relationship |
|---|---|
| etzhayyim-project-phone | PSTN bridge legacy path (AWS Connect) |
| etzhayyim-project-network-mobile | Mesh infrastructure sibling |
| etzhayyim-project-murakumo | AI inference (STT/TTS/translation) |
| etzhayyim-project-maps | Mesh topology spatial visualization |
| etzhayyim-project-trust | DID trust score for spam detection |
| etzhayyim-project-device | Device registry |
