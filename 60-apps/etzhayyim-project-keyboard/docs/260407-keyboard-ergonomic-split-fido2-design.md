# KB-SPLIT — Ergonomic Dual-Body Split Keyboard + FIDO2 設計書

**Date**: 2026-04-07
**Status**: `[DESIGN]`
**Product**: keyboard.etzhayyim.com
**Sales**: okaimono.etzhayyim.com D2C 専売 (OEM CTO)

---

## 1. Product Overview

普通のキーボード2台を並列結合した人体工学 split keyboard。FIDO2 MOC 指紋センサー内蔵。OEM 調達でコスパ最適化。

**Target**: エンジニア・長時間タイピングワーカー。腕の内旋 (pronation) による手首痛・腱鞘炎を予防。

---

## 2. Mechanical Design

### 2.1 全体構成図 (Top View)

```
                         680mm (60% model)
    ├──────────── 310mm ────────────┤60mm├──────────── 310mm ────────────┤
    ┌───────────────────────────────┬────┬───────────────────────────────┐
    │                               │    │                               │
    │   ┌───────────────────────┐   │    │   ┌───────────────────────┐   │
    │   │                       │   │ ◉  │   │                       │   │
    │   │     Left 60% PCB      │   │ FP │   │     Right 60% PCB     │   │
    │   │     (61 keys)         │   │    │   │     (61 keys)         │   │
    │   │                       │   │    │   │                       │   │
    │   └───────────────────────┘   │    │   └───────────────────────┘   │
    │                               │    │                               │ 130mm
    │   Left Frame (CNC/ABS)        │    │   Right Frame (CNC/ABS)       │
    │                               │    │                               │
    └───────────────┬───────────────┴────┴───────────────┬───────────────┘
                    │          Center Bridge              │
                    │     (hinge + hub + sensor)          │
                    └────────────────┬───────────────────-┘
                                     │
                               USB-C out
```

### 2.2 側面図 (Side View — Tenting)

```
    Tenting 0° (flat)                    Tenting 15° (ergonomic)

    ┌─────────────┐ ┌─────────────┐     ┌─────────────┐ ┌─────────────┐
    │  L keyboard │ │  R keyboard │      \  L keyboard  / \  R keyboard /
    └─────────────┘ └─────────────┘       \─────────────/   \───────────/
    ═══════════════════════════════         ════════╤════     ════╤══════
              desk surface                       hinge         hinge

    Tenting 30° (maximum)

          ┌───────────┐   ┌───────────┐
           \  L keybd  │   │  R keybd  /
            \──────────│   │──────────/
             ╲─────────╡   ╞─────────╱
              ═════════╧═══╧════════
                     desk surface
```

### 2.3 前面図 (Front View — Splay)

```
    Splay 0° (parallel)              Splay 10° (natural)

    ┌──────┐  ┌──────┐              ╲──────╱  ╲──────╱
    │  L   │  │  R   │               \  L  /    \  R  /
    │      │  │      │                \    / 10°  \   /
    └──────┘  └──────┘                 \──/        \─/
```

### 2.4 Center Bridge 詳細 (断面図)

```
              60mm
    ├────────────────────┤
    ┌────────────────────┐
    │  ┌──────────────┐  │
    │  │  USB Hub IC   │  │  ← 2 HID Keyboard + 1 HID FIDO → 1 USB-C
    │  └──────────────┘  │
    │  ┌──┐              │
    │  │◉ │ FP Sensor    │  ← Synaptics FS7600 MOC (6×6mm, surface flush)
    │  └──┘ (FIDO2)      │
    │  ┌──────────────┐  │
    │  │  Hinge Mech   │  │  ← Tenting 0°〜30° + Splay 0°〜15°
    │  │  (dual-axis)  │  │
    │  └──────────────┘  │
    │  ┌──────────────┐  │
    │  │  USB-C Port   │  │  ← detachable, to host PC
    │  └──────────────┘  │
    └────────────────────┘
```

### 2.5 Split Distance Rail

```
    ←── slide rail (0〜30cm adjustment) ──→

    ┌──────────┐                              ┌──────────┐
    │  L Frame │══════════╤════════════════════│  R Frame │
    └──────────┘    Center Bridge              └──────────┘
                   (slides on rail)

    Collapsed (transport):
    ┌──────────┬────┬──────────┐   total: 310+60+310 = 680mm
    │  L Frame │ CB │  R Frame │
    └──────────┴────┴──────────┘

    Expanded (shoulder-width):
    ┌──────────┐    ┌────┐    ┌──────────┐   total: ~1000mm
    │  L Frame │    │ CB │    │  R Frame │
    └──────────┘    └────┘    └──────────┘
```

---

## 3. Electronics Architecture

### 3.1 USB Topology

```
    Host PC (USB-C)
        │
        │  USB 2.0 (480 Mbps, HID は low-bandwidth)
        │
    ┌───┴───────────────────────────────────┐
    │  USB Hub IC (e.g. GL850G / FE1.1s)    │
    │  4-port USB 2.0 hub                    │
    │                                        │
    │  Port 1 ── Left Keyboard MCU ───── USB HID Keyboard (Interface 0)
    │  Port 2 ── Right Keyboard MCU ──── USB HID Keyboard (Interface 1)
    │  Port 3 ── FIDO2 Sensor MCU ───── USB HID FIDO    (Interface 2)
    │  Port 4 ── (reserved: RGB LED controller / future expansion)
    │                                        │
    └────────────────────────────────────────┘
```

### 3.2 MCU + Firmware Stack

```
    ┌─────────────────────────────────────────┐
    │  Left Keyboard                          │
    │  ┌─────────────┐  ┌──────────────────┐  │
    │  │ Key Matrix   │→│ MCU (ATmega32U4  │  │
    │  │ 61 keys      │  │  or RP2040)      │  │
    │  │ hot-swap     │  │                  │  │
    │  └─────────────┘  │ Firmware:         │  │
    │                    │  QMK / VIA        │  │
    │  ┌─────────────┐  │  (open-source)    │  │
    │  │ RGB LEDs     │→│                  │  │
    │  │ (per-key)    │  │ USB HID Keyboard │  │
    │  └─────────────┘  └──────┬───────────┘  │
    └──────────────────────────┼───────────────┘
                               │ USB
    ┌──────────────────────────┼───────────────┐
    │  Right Keyboard          │ (same as left) │
    └──────────────────────────┼───────────────┘
                               │ USB
    ┌──────────────────────────┼───────────────┐
    │  FIDO2 Module            │               │
    │  ┌─────────────┐  ┌─────┴────────────┐  │
    │  │ FP Sensor    │→│ Synaptics FS7600 │  │
    │  │ (capacitive  │  │ Match-on-Chip    │  │
    │  │  6×6mm)      │  │                  │  │
    │  └─────────────┘  │ FIDO2 CTAP2      │  │
    │                    │ USB HID FIDO     │  │
    │                    │                  │  │
    │                    │ Template storage │  │
    │                    │ (on-chip secure) │  │
    │                    └──────────────────┘  │
    └──────────────────────────────────────────┘
```

### 3.3 FIDO2 認証フロー

```
    ユーザー                Keyboard           Host OS              Web Service
       │                      │                  │                      │
       │  指紋タッチ           │                  │                      │
       │─────────────────────→│                  │                      │
       │                      │                  │                      │
       │               ┌──────┴──────┐           │                      │
       │               │ MOC 照合     │           │                      │
       │               │ (on-chip)    │           │                      │
       │               │ template     │           │                      │
       │               │ match?       │           │                      │
       │               └──────┬──────┘           │                      │
       │                      │                  │                      │
       │                      │  CTAP2 response  │                      │
       │                      │ (signed assertion)│                      │
       │                      │─────────────────→│                      │
       │                      │                  │                      │
       │                      │                  │  [Windows Hello]      │
       │                      │                  │  PC unlock ✓          │
       │                      │                  │                      │
       │                      │                  │  [WebAuthn]           │
       │                      │                  │─────────────────────→│
       │                      │                  │  signed challenge     │
       │                      │                  │                      │
       │                      │                  │  verify public key    │
       │                      │                  │←─────────────────────│
       │                      │                  │  login success ✓      │
```

---

## 4. BOM & Cost Structure

### 4.1 BOM Detail (KB-SPLIT-60-FIDO, @10,000 units)

| # | Part | Specification | Qty | Unit Cost | Total |
|---|---|---|---|---|---|
| 1 | PCB + Switch Plate | 60% (61-key), FR4 1.6mm, hot-swap Kailh socket | 2 | ¥2,500 | ¥5,000 |
| 2 | Key Switch | Gateron G Pro 3.0 Brown (tactile, 55gf) | 122 | ¥25 | ¥3,050 |
| 3 | Keycap | PBT double-shot, OEM profile, laser legend | 2 set | ¥800 | ¥1,600 |
| 4 | MCU | ATmega32U4 (QMK) or RP2040 (QMK/ZMK) | 2 | ¥250 | ¥500 |
| 5 | Frame (L+R) | ABS injection mold (¥800K amortized @10K) | 1 set | ¥1,500 | ¥1,500 |
| 6 | Center Bridge | ABS + アルミヒンジ + rail mechanism | 1 | ¥800 | ¥800 |
| 7 | FIDO2 Sensor | Synaptics FS7600 MOC + flex cable | 1 | ¥800 | ¥800 |
| 8 | USB Hub IC | GL850G 4-port USB 2.0 hub | 1 | ¥150 | ¥150 |
| 9 | Hub PCB | Center bridge PCB (hub + sensor + USB-C) | 1 | ¥200 | ¥200 |
| 10 | USB-C Connector | Receptacle (host side) + internal cables | 3 | ¥50 | ¥150 |
| 11 | Cable | USB-C to USB-C, 1.8m, braided | 1 | ¥300 | ¥300 |
| 12 | RGB LED | Per-key SK6812MINI-E (optional) | 122 | ¥8 | ¥976 |
| 13 | Stabilizer | PCB-mount screw-in (spacebar, shift, enter) | 8 | ¥30 | ¥240 |
| 14 | Rubber feet | Anti-slip silicone | 8 | ¥10 | ¥80 |
| 15 | Packaging | Box + foam insert + manual + USB-C cable | 1 | ¥300 | ¥300 |
| | **部材原価合計** | | | | **¥15,346** |
| | 組立工賃 (深圳 EMS) | | | | ¥1,500 |
| | QC + 検品 | | | | ¥300 |
| | **製造原価合計** | | | | **¥17,146** |

### 4.2 金型費用 (初期投資)

| 金型 | 費用 | Amortization |
|---|---|---|
| Frame (L) ABS injection mold | ¥400,000 | ¥40/unit @10K |
| Frame (R) ABS injection mold | ¥400,000 | ¥40/unit @10K |
| Center Bridge mold | ¥200,000 | ¥20/unit @10K |
| **金型合計** | **¥1,000,000** | **¥100/unit @10K** |

### 4.3 SKU 別原価・価格

| SKU | 製造原価 | 販売価格 | 粗利 | 粗利率 |
|---|---|---|---|---|
| KB-SPLIT-60-FIDO | ¥17,146 | ¥24,800 | ¥7,654 | 30.9% |
| KB-SPLIT-60-BASE | ¥15,346 | ¥19,800 | ¥4,454 | 22.5% |
| KB-SPLIT-75-FIDO | ¥19,646 | ¥29,800 | ¥10,154 | 34.1% |
| KB-SPLIT-TKL-FIDO | ¥22,146 | ¥34,800 | ¥12,654 | 36.4% |

### 4.4 CTO Options (追加原価 → 追加価格)

| Option | 原価差分 | 販売価格差分 |
|---|---|---|
| Switch: Cherry MX (Brown/Red/Blue) | +¥1,500 | +¥3,000 |
| Switch: Kailh BOX | +¥500 | +¥1,000 |
| Keycap: ABS (downgrade) | -¥400 | -¥1,000 |
| Frame: CNC アルミ (upgrade) | +¥3,000 | +¥8,000 |
| RGB LED: なし (downgrade) | -¥976 | -¥2,000 |
| Wrist rest: magnetic PU leather | +¥500 | +¥2,000 |

---

## 5. Certification & Compliance

| 認証 | 要件 | 費用概算 | 期間 |
|---|---|---|---|
| **PSE** (電気用品安全法) | 特定電気用品以外 (USB 5V) | ¥200,000 | 2〜4 weeks |
| **FCC Part 15** (US) | Class B unintentional radiator | ¥300,000 | 4〜6 weeks |
| **CE** (EU) | EMC Directive + RoHS | ¥300,000 | 4〜6 weeks |
| **FIDO2 Certification** | FIDO Alliance L1 (authenticator) | ¥500,000 | 8〜12 weeks |
| **TELEC** (技適, if wireless) | USB only → 不要 | ¥0 | — |
| **合計** | | **¥1,300,000** | |

---

## 6. Manufacturing Process

```
    Phase 1: Prototype (Month 1-3)
    ┌────────────────────────────────────────────────────────────┐
    │  既存 60% PCB 入手 → Center Bridge 3D print prototype      │
    │  → FIDO2 sensor 評価基板 → 動作検証 → ergonomic user test   │
    └────────────────────────────────────────────────────────────┘
                                │
    Phase 2: EVT (Month 4-5)    ▼
    ┌────────────────────────────────────────────────────────────┐
    │  金型発注 (Frame L/R + Center Bridge)                       │
    │  → Hub PCB 設計・製造 → FIDO2 integration → 30 units EVT    │
    └────────────────────────────────────────────────────────────┘
                                │
    Phase 3: DVT (Month 6-7)    ▼
    ┌────────────────────────────────────────────────────────────┐
    │  金型修正 (T1→T2) → 組立ライン trial → 100 units DVT        │
    │  → PSE/FCC/CE 認証サンプル提出 → FIDO2 L1 認証開始          │
    └────────────────────────────────────────────────────────────┘
                                │
    Phase 4: PVT (Month 8-9)    ▼
    ┌────────────────────────────────────────────────────────────┐
    │  量産ライン確立 → 500 units PVT → QC pass rate ≥ 98%        │
    │  → 認証取得完了 → firmware final (QMK + FIDO2)              │
    └────────────────────────────────────────────────────────────┘
                                │
    Phase 5: MP (Month 10〜)     ▼
    ┌────────────────────────────────────────────────────────────┐
    │  Mass Production 10,000 units → okaimono.etzhayyim.com 販売開始   │
    │  → CTO order → 2-week lead time → 出荷                     │
    └────────────────────────────────────────────────────────────┘
```

---

## 7. Initial Investment Summary

| 項目 | 費用 |
|---|---|
| 金型 (Frame L/R + Center Bridge) | ¥1,000,000 |
| Hub PCB 設計・製造 (NRE) | ¥300,000 |
| FIDO2 評価・統合 (NRE) | ¥200,000 |
| 認証 (PSE + FCC + CE + FIDO2) | ¥1,300,000 |
| Prototype (3D print, 10 units) | ¥200,000 |
| EVT (30 units) | ¥600,000 |
| DVT (100 units) | ¥1,800,000 |
| PVT (500 units) | ¥8,500,000 |
| **初期投資合計** | **¥13,900,000** |

### 損益分岐点

| SKU mix (assumed) | Avg. 粗利/unit |
|---|---|
| 60% FIDO (70%) + 60% BASE (20%) + 75% FIDO (10%) | ¥7,174 |

**BEP = ¥13,900,000 ÷ ¥7,174 ≈ 1,938 units**

10,000 units 完売時の粗利: **¥71,740,000** (初期投資回収後 net: ¥57,840,000)

---

## 8. Firmware Architecture

### 8.1 QMK/VIA Keymap

```
    ┌─────────────────────────────────────────────┐
    │  QMK Firmware (ATmega32U4 / RP2040)         │
    │                                              │
    │  Layer 0: Default (QWERTY)                   │
    │  Layer 1: Function (F1-F12, media)           │
    │  Layer 2: Navigation (arrows, PgUp/Dn)       │
    │  Layer 3: Numpad (right hand)                │
    │                                              │
    │  VIA support: real-time keymap editing        │
    │  via VIA configurator (no reflash needed)     │
    │                                              │
    │  Split communication:                        │
    │  (not needed — each half is independent USB)  │
    └─────────────────────────────────────────────┘
```

**独立 USB 設計の利点**: 左右間の通信 (TRRS/serial) が不要。各半分が独立した USB HID デバイス。片方だけでも使用可能。

### 8.2 keyboard.etzhayyim.com AI Optimization

```
    User typing data (opt-in, local analysis)
        │
        ▼
    keyboard.etzhayyim.com actor
        │
        ├── typing pattern analysis
        │   → heatmap → underused keys → layout suggestion
        │
        ├── ergonomic profile
        │   → wrist angle sensor data (future) → tenting recommendation
        │
        └── firmware update
            → QMK DFU over USB-C → keymap push
```

---

## 9. Packaging & Unboxing

```
    ┌──────────────────────────────────────────┐
    │  ┌────────────────────────────────────┐   │
    │  │          KB-SPLIT-60-FIDO          │   │
    │  │     Ergonomic Split Keyboard       │   │
    │  │         + FIDO2 Fingerprint        │   │
    │  └────────────────────────────────────┘   │
    │                                           │
    │  Box contents:                            │
    │  ┌─────┐ ┌─────┐  ┌────┐                │
    │  │  L  │ │  R  │  │ CB │  assembled      │
    │  └─────┘ └─────┘  └────┘                 │
    │  ┌──────────────────────┐                 │
    │  │ USB-C cable (1.8m)   │                 │
    │  └──────────────────────┘                 │
    │  ┌──────────────────────┐                 │
    │  │ Keycap puller + switch puller          │
    │  └──────────────────────┘                 │
    │  ┌──────────────────────┐                 │
    │  │ Quick start guide    │                 │
    │  │ + FIDO2 setup card   │                 │
    │  └──────────────────────┘                 │
    │  ┌──────────────────────┐                 │
    │  │ Extra switches (×5)  │ (CTO option)    │
    │  └──────────────────────┘                 │
    └───────────────────────────────────────────┘
```
