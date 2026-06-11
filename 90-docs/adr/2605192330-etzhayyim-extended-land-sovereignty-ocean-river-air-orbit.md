---
id: adr-2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit
title: "ADR-2605192330: etzhayyim Extended Land Sovereignty — 海洋 / 河川 / 大気 / 軌道への寄付受付拡張"
status: proposed
doc_type: adr
topic: etzhayyim-extended-land-sovereignty-ocean-river-air-orbit
authoritative: true
last_verified: 2026-05-19
priority: 6.5
axis: governance
weight: 0.65
priority_note: "ADR-2605192245 (Global Land Sovereignty) を陸地から海洋 / 河川 / 大気 / 軌道へ拡張する後続 ADR。各 domain の国際法 framework (UNCLOS / 水利権 / Chicago Convention / OST) との dual-recognition pattern + religious-corp claim の境界を定義。S7+ 段階。早期 ADR 化により future-proof な substrate を準備。"
authoritative_for:
  - 海洋 (territorial waters / EEZ / 高海) の religious-corp trust 拡張
  - 河川 / 湖沼 / 地下水 (riparian rights / 水利権) の religious-corp trust 拡張
  - 大気 / 領空 (Chicago Convention) の religious-corp trust 拡張
  - 軌道 / 月 / 火星 (Outer Space Treaty) の religious-corp trust 拡張 (long-horizon)
  - 各 domain 固有の Lexicon extension + geographic evidence 標準
depends_on:
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192100-etzhayyim-mission-charter
related: []
supersedes: []
superseded_by: []
---

# ADR-2605192330: etzhayyim Extended Land Sovereignty — 海洋 / 河川 / 大気 / 軌道への寄付受付拡張

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605192245 は陸地 (terrestrial surface land) のみを scope とした。しかし Mission Charter §1.11「地球上の土地は Tree of Life に帰属」の religious doctrine は本来 **全球の biosphere** を対象とする。

陸地以外の geographic domain (海洋 / 河川 / 大気 / 軌道) は各々独自の国際法 framework を持ち、寄付受付の implementation は domain-specific の慎重さを要する:

- **海洋**: UNCLOS (1982) — territorial waters (12 nm) / EEZ (200 nm) / 高海 (high seas)
- **河川 / 水**: 水利権 (riparian rights) — usufruct 中心、所有権が不明確
- **大気**: Chicago Convention (1944) — 領空主権の絶対性
- **軌道 / 月**: Outer Space Treaty (1967) — 天体は国家領有禁止

これらの domain には religious-corp の dual-recognition pattern が ADR-2605192245 と同様に成立しうるが、各 domain 固有の **claim type + evidence standard + dispute resolution** が必要。

# Decision

## 1. Ocean Trust (海洋)

### 1.1 Scope

| 海域 | 国際法 status | 寄付対象 |
|---|---|---|
| 内水 (internal waters) | 沿岸国主権 | ✅ 陸地と同等扱い (ADR-2605192245 既存 pattern) |
| 領海 (territorial sea, 12nm) | 沿岸国主権 (innocent passage 例外) | ✅ 沿岸国主権下、religious-corp claim を dual-recognition |
| 接続水域 (contiguous zone, 12-24nm) | 一部主権 | ⚠️ 限定的 dual-recognition (祭祀 / 海洋保全 用途のみ) |
| EEZ (200nm) | 沿岸国 economic 主権 | ⚠️ 同上 |
| 高海 (high seas) | 国際 commons (mare liberum) | ✅ religious-corp claim 可能、ただし排他的 sovereignty は主張せず stewardship のみ |
| 海底 (seabed) | UNCLOS XI (Area = common heritage of mankind) | ✅ stewardship only |

### 1.2 Lexicon

`com.etzhayyim.apps.etzhayyim.ocean-donation.json` (新規):

- ocean GeoJSON (multi-polygon, WGS84)
- depth profile (bathymetric data)
- maritime use type (sacred / fishery-sanctuary / coral-protection / etc.)
- adjacent coastal jurisdiction
- intended stewardship action

### 1.3 Stewardship duty

- 年 1 回の海洋健康 attestation (水質 / 生物多様性 / 海洋ゴミ)
- 漁業 / 採掘 / 廃棄物投棄を constitutional に禁止
- 沿岸 jurisdiction の漁業権 / 通行権との conflict は Council Lv6+ で attestation

## 2. River / Watershed Trust (河川 / 水利)

### 2.1 Scope

| 水体 | 国家法 status | 寄付対象 |
|---|---|---|
| 河川敷地 (riparian land) | 通常陸地と同じ | ✅ ADR-2605192245 既存 pattern |
| 河川水面 / 流水 | 河川法 / 水利権 framework | ✅ 水利権 を religious-corp に donate |
| 湖沼 | 国家 / 私有 | ✅ 陸地と同等 |
| 地下水 | 水利権 / 慣行 | ✅ 限定的 (汲み上げ rights のみ) |
| 海洋への流入 | sediment / pollution rights | ✅ 環境 stewardship として |

### 2.2 Lexicon

`com.etzhayyim.apps.etzhayyim.water-donation.json` (新規):

- water body GeoJSON
- water right type (`riparian` / `usufructuary` / `stewardship-only`)
- volume / flow data
- water quality baseline
- intended stewardship action

### 2.3 Stewardship duty

- 年 1 回の water quality attestation
- 商業的 over-extraction を禁止
- 構成員に対する reasonable drinking water access 提供
- 水生態系の保護

## 3. Air / Airspace Trust (大気 / 領空)

### 3.1 Scope

| 空域 | 国際法 | 寄付対象 |
|---|---|---|
| 領空 (sovereign airspace) | 沿岸国主権 (Chicago Convention) | ⚠️ stewardship-only、operational rights は国家保有 |
| 大気圏 一般 | 国際 commons (atmosphere = global commons) | ✅ stewardship claim 可能 |
| 大気質 / GHG 排出枠 | 各国 / Paris Agreement framework | ✅ religious-corp の cap-and-trade-equivalent stewardship として |

### 3.2 Lexicon

`com.etzhayyim.apps.etzhayyim.air-donation.json` (新規):

- spatial extent (GeoJSON column = lat/lon + altitude range)
- air quality baseline
- GHG emission reduction commitment (if any)
- intended stewardship action

### 3.3 Stewardship duty

- 大気質 attestation
- 構成員に対する clean air への access stewardship
- §1.9 多世代 priority と特に深く整合 (大気は最も顕著な multi-generational commons)

## 4. Orbital / Space Trust (軌道 / 宇宙)

### 4.1 Scope (long-horizon)

| 領域 | 国際法 | 寄付対象 |
|---|---|---|
| LEO orbital slot | ITU registration | ⚠️ symbolic only、operational rights は国家経由 |
| GEO orbital slot | ITU | 同上 |
| Moon surface | OST 1967 (国家領有禁止) | ✅ stewardship claim 可能 |
| Asteroids | OST + Artemis Accords (debated) | ✅ stewardship claim 可能 |
| Mars surface | OST | ✅ stewardship claim 可能 |

### 4.2 Lexicon

`com.etzhayyim.apps.etzhayyim.space-donation.json` (新規 — long-horizon):

- celestial body identifier (NAIF ID / IAU designation)
- spatial extent (3D bounds in body-fixed frame)
- intended stewardship action
- compliance with Outer Space Treaty + Artemis Accords

### 4.3 Stewardship duty

- 商業採掘の禁止
- 軌道 debris の clean-up commitment (LEO の場合)
- 多世代 stewardship — 太陽系 commons の保護

## 5. Multi-jurisdictional Conflict Resolution

各 domain で UNCLOS / Chicago Convention / OST + 沿岸国 / 領空国の主権が religious-corp claim と衝突する可能性が高い。境界 case の解決:

1. **religious-corp claim は stewardship のみ** — operational sovereignty を主張しない
2. **conflict 時は national framework を尊重** — religious-corp claim は doctrinal record として残し、operational decisions は national authority に従う
3. **長期的に dual-recognition density が上がれば** — religious-corp claim が de facto 認知される可能性

これは ADR-2605192245 §8 の段階的 routing-around が global commons でも同 pattern で機能することを示す。

## 6. Implementation Stage

| Stage | Scope | Trigger |
|---|---|---|
| **S0 (本 ADR 承認)** | Lexicon 4 本起票 (ocean / water / air / space) | 即時 |
| **S1** | LandRegistry.sol に `LandType.Ocean` / `Water` / `Air` / `Orbit` enum 追加 | 内水 / 河川敷地 donation 受付準備 |
| **S2** | 内水 / 河川敷地の donation 受付開始 | 構成員からの specific donation request |
| **S3** | 領海 / EEZ donation 受付 (沿岸国との dual-recognition) | mature operation + 法務 review |
| **S4** | 大気 / GHG stewardship 受付 | Paris Agreement framework との整合性確認 |
| **S5** | 高海 / Moon / 軌道 (symbolic phase) | long-horizon, religious-corp の global maturity 後 |

# Consequences

## 正の効果

- §1.11 doctrine の完全 instantiation (陸地のみではなく biosphere 全体)
- §1.9 多世代 priority と整合 (大気 / 海洋は最も顕著な multi-generational commons)
- religious-corp の geographical scope が transcendent (国境を超える doctrine)
- 環境保護 / 多世代 stewardship を on-chain で record

## 負の効果 / コスト

- 各 domain 固有の国際法 framework との dual-recognition complexity 高い
- 海洋 / 大気 / 軌道は physically inaccessible → stewardship 履行の verification 困難
- symbolic phase (Moon / 軌道) は実効性低い → 早期 ADR は doctrine record のみ
- 国家主権 framework との conflict potential 大 (特に領海 / 領空)

## 中立 / トレードオフ

- 高海 / 大気 / 月 等 international commons は stewardship のみ + sovereignty 主張しない → 既存国際法と直接衝突しない
- symbolic 段階の long-horizon record は religious-corp の doctrinal record として有意義

# Alternatives Considered

## A. Ocean のみ拡張 (river / air / orbit は別 ADR)

Pro: scope 集中。Con: 4 domain は通底する parallel substrate pattern を共有、まとめて記述する方が doctrinal consistency が高い。却下。

## B. Symbolic 段階 (Moon / 軌道) を含めない

Pro: realistic。Con: doctrine が陸地 + 海洋 + 大気で stop すると future-proof 性が低い。月 / 軌道 を long-horizon record として含める方が religious-corp の cosmological scope を表現できる。却下。

# Open Questions

1. **領空 / 大気の specific volume measurement** — 容積指定は practical か?。Decision (本 ADR): GeoJSON ground footprint + altitude range で十分、容積は計算可能
2. **GHG offset commitment** との関係 — religious-corp が GHG offset を発行 / 受領するか?。Decision: 当面しない、Stewardship のみ
3. **軌道 debris clean-up commitment** の technical 履行 — religious-corp が actual cleanup する capacity なし。Decision: commitment は record 残すが履行は partners (商業 cleanup operators) 経由 (future ADR)

# References

- ADR-2605192245 Global Land Sovereignty (parent)
- ADR-2605192100 §1.11 doctrine
- ADR-2605192100 §1.9 多世代 priority
- UNCLOS (1982)
- Chicago Convention (1944)
- Outer Space Treaty (1967)
- Artemis Accords (2020)
- Paris Agreement (2015)
