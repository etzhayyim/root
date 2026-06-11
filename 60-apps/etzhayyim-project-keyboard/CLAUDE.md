# keyboard.etzhayyim.com — Ergonomic Dual-Body Split Keyboard (OEM D2C)

**URL**: `https://keyboard.etzhayyim.com`

## Product Concept

人体工学 split keyboard。**普通のキーボード2台を並列結合** する OEM 設計でコスパ最適化。腕の内旋 (pronation) を排除し、自然な手首角度でタイピング可能。

### Design Philosophy

| 原則 | 詳細 |
|---|---|
| **Dual-Body Split** | 左右独立した2台の標準キーボードを結合フレームで並列配置。角度調整可能 (0°〜30° tenting) |
| **OEM コスパ最適化** | 専用金型ではなく、既存60%キーボード (Baroccomistel MD600 Alpha 級) の OEM 調達 + カスタムフレーム結合 |
| **FIDO2 指紋センサー** | フレーム中央に MOC (Match-on-Chip) 指紋センサー搭載。Windows Hello ログイン + FIDO2 WebAuthn パスワードレス認証。macOS は FIDO2 WebAuthn (Web/SSH/sudo) 対応 |
| **BTO/CTO 対応** | switch 種類・keycap material・フレーム色・tenting 角度をオーダー時に選択 |

### Hardware Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Adjustable Frame                       │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐       │
│  │  Left 60%    │  │  FIDO2   │  │  Right 60%   │       │
│  │  Keyboard    │  │ ◉ FP     │  │  Keyboard    │       │
│  │  (OEM unit)  │  │ Sensor   │  │  (OEM unit)  │       │
│  │              │  │ (6×6mm)  │  │              │       │
│  │  USB-C out ──┼──┼── Hub ───┼──┼── USB-C out  │       │
│  └──────────────┘  └──────────┘  └──────────────┘       │
│         Tenting: 0°〜30° adjustable per side             │
│         Splay: 0°〜15° outward angle                     │
└─────────────────────────────────────────────────────────┘
                         │
              Single USB-C to host PC
          (USB HID Keyboard + USB HID FIDO2)
```

OS からは **2 デバイス** として認識:
- USB HID Keyboard — 通常キー入力
- USB HID FIDO — FIDO2/CTAP2 認証器 (指紋センサー)

### FIDO2 Fingerprint Sensor

| 項目 | 仕様 |
|---|---|
| **推奨チップ** | Synaptics FS7600 (Match-on-Chip) |
| **代替** | FPC1035 MOC / Goodix GF5288 / ELAN eKT |
| **センサー面積** | 6×6mm (フレーム中央ベゼルに埋込) |
| **OEM 原価** | ¥600〜1,050 (@10K units) |
| **プロトコル** | FIDO2 CTAP2 over USB HID |
| **テンプレート保存** | Match-on-Chip (センサー内蔵、ホスト送信なし) |

| OS | PC ログイン | Web 認証 (Passkey) | SSH | sudo |
|---|---|---|---|---|
| **Windows** | ◎ Windows Hello | ◎ WebAuthn | ◎ sk-ecdsa | — |
| **macOS** | ✗ (Secure Enclave 専用) | ◎ WebAuthn | ◎ sk-ecdsa | ◎ pam-u2f |
| **Linux** | ◎ libfido2 + fprintd | ◎ WebAuthn | ◎ sk-ecdsa | ◎ pam-u2f |

### BOM (Bill of Materials) — Target OEM

| Part | Spec | OEM Source | Est. 原価 |
|---|---|---|---|
| **Left/Right PCB + Switch Plate** | 60% layout (61-key), hot-swap socket | 深圳 OEM (Cherry MX 互換) | ¥3,000×2 |
| **Switch** | Gateron Brown (default) / Cherry MX / Kailh (BTO) | switch supplier | ¥1,500×2 |
| **Keycap** | PBT double-shot (default) / ABS (CTO) | keycap OEM | ¥1,000×2 |
| **Frame** | CNC アルミ or injection-mold ABS | フレーム専用金型 (唯一のカスタムパーツ) | ¥2,000 |
| **Hinge mechanism** | tenting 0°〜30°, splay 0°〜15° | ヒンジ OEM | ¥500 |
| **FIDO2 指紋センサー** | Synaptics FS7600 MOC, 6×6mm | Synaptics / FPC | ¥800 |
| **USB Hub IC** | 内蔵 hub (2 keyboard HID + 1 FIDO HID → 1 USB-C) | hub IC OEM | ¥300 |
| **Cable** | detachable USB-C to USB-C (coiled option) | cable OEM | ¥300 |
| **合計 (Est.)** | | | **¥13,900** |

### SKU Variants

| SKU | Layout | Switch | FIDO2 | 想定価格 | 粗利率 |
|---|---|---|---|---|---|
| **KB-SPLIT-60-FIDO** | 2×60% | Gateron Brown | ◎ 指紋 | ¥24,800 | ~44% |
| **KB-SPLIT-60-BASE** | 2×60% | Gateron Brown | なし | ¥19,800 | ~42% |
| **KB-SPLIT-75-FIDO** | 2×75% | Gateron Brown | ◎ 指紋 | ¥29,800 | ~43% |
| **KB-SPLIT-TKL-FIDO** | 2×TKL | Gateron Brown | ◎ 指紋 | ¥34,800 | ~42% |

CTO options: switch (+¥0〜¥5,000), keycap material (+¥0〜¥3,000), frame color (black/silver/white), tenting angle preset

### Ergonomic Specifications

| Parameter | Range | Default |
|---|---|---|
| **Tenting angle** | 0°〜30° (stepless or 5° step) | 10° |
| **Splay angle** | 0°〜15° (frame hinge) | 5° |
| **Split distance** | 0cm〜30cm (frame rail slide) | 肩幅 (~40cm total) |
| **Keyboard height** | standard (no wrist rest) + optional magnetic wrist rest | — |
| **Key travel** | switch-dependent (MX: 4mm, Low-profile: 3mm) | 4mm (MX) |

## Write-Only Derived Architecture

**Handler は write のみ。social post / cross-actor invoke は PDS commit pipeline の derive rule で自動導出。**

| Data | Storage | Reason |
|---|---|---|
| SKU catalog, firmware | in-memory (static) / Repo (public) | 公開カタログ情報 |
| `crowdfundingRequest` | Repo (public) | 公開 intent — derive rule → auto invoke crowdfunding.etzhayyim.com |
| `configuration` | Preferences (private) | user-specific CTO 構成 |
| `ergonomicProfile` | Preferences (private) | 身体情報 (PII) |

Derive rules: `kotodama.jsonld` `"derive"` section。設計: `90-docs/260407-write-only-derived-architecture-design.md`

## Component

| Component | nanoid | 役割 |
|---|---|---|
| `etzhayyim-wasm-keyboard-kb0ard1x` | `kb0ard1x` | Product intelligence + CTO configurator |

## Actor Composition

| Actor DID | Role |
|---|---|
| `did:web:keyboard.etzhayyim.com` | controller — product intelligence + catalog management |
| `did:web:keyboard.etzhayyim.com:actor:designer` | hardware CAD + BOM optimization |
| `did:web:keyboard.etzhayyim.com:actor:firmware` | keyboard firmware intelligence (QMK/VIA/ZMK) |
| `did:web:keyboard.etzhayyim.com:actor:configurator` | CTO configurator UI (switch/keycap/frame selector) |

## Domain WIT (Lexicon)

**AT Lexicon namespace**: `com.etzhayyim.apps.keyboard.*`

| WIT interface | Lexicon prefix | Record kinds |
|---|---|---|
| `product` | `com.etzhayyim.apps.keyboard.product` | SKU definition, BOM |
| `configuration` | `com.etzhayyim.apps.keyboard.configuration` | CTO options, user config |
| `firmware` | `com.etzhayyim.apps.keyboard.firmware` | firmware version, keymap |
| `ergonomics` | `com.etzhayyim.apps.keyboard.ergonomicProfile` | user ergonomic measurements |

## Sales Channel

**okaimono.etzhayyim.com 経由 D2C 専売。** OEM 製造品として `fulfillment_mode: "cto"` (Configure-to-Order) で catalog 登録。

- okaimono catalog に `com.etzhayyim.apps.okaimono.catalogItem` として登録
- `manufacturer_did`: OEM factory DID
- `factory_did`: 深圳 keyboard factory DID
- UNSPSC: `43211706` (Computer keyboards)

## Competitive Analysis

| Product | Price | Split | FIDO2 | 備考 |
|---|---|---|---|---|
| Baroccomistel MD600 Alpha | ¥15,000〜 | ✓ (2-piece) | ✗ | 60% split, RGB, cherry |
| ErgoDox EZ | ¥40,000〜 | ✓ (custom) | ✗ | ortholinear, 専用設計 |
| Kinesis Advantage360 | ¥50,000〜 | ✓ (contoured) | ✗ | contoured well, 高価 |
| Mistel BAROCCO | ¥12,000〜 | ✓ (2-piece) | ✗ | closest competitor |
| **KB-SPLIT-60-FIDO (ours)** | **¥24,800** | **✓** | **◎ 指紋** | **OEM 2台結合 + FIDO2 パスワードレス** |

**差別化**: FIDO2 指紋センサー搭載 split keyboard は市場に存在しない。OEM 2台結合でエルゴ split のコスト障壁を破壊 + パスワードレス認証を統合。

## Contract

`contract-category: product-safety` (電気用品安全法 PSE, CE marking, FCC Part 15)

## Firmware Intelligence

keyboard.etzhayyim.com actor が QMK/VIA keymap を AI 最適化:
- typing pattern analysis → layout recommendation
- per-user ergonomic profile → tenting/splay angle suggestion
- firmware OTA update via USB-C (QMK DFU)
