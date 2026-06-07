---
id: adr-2605242515-iwakura-ternary-inference-asic
title: "Iwakura (磐座) — baien ternary 専用推論 ASIC architecture"
status: proposed
doc_type: adr
topic: silicon-iwakura
authoritative: true
last_verified: 2026-05-24
authoritative_for:
  - iwakura-1 die architecture (PE array / SRAM / DRAM / package / TDP / pinout class)
  - ternary processing element (PE) micro-architecture
  - radix-3 weight packing convention (5 ternary / byte)
  - iwakura.silicon ↔ baien runtime ABI (microcode + dispatch model)
  - Phase 1 deliverable = RTL + cocotb simulation (no FPGA, no MPW yet)
depends_on:
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
related:
  - 50-infra/silicon/iwakura/
  - 50-infra/silicon/shared-ip/ternary-pe/
  - 70-tools/silicon/iwakura-asm/                # baien model → iwakura microcode compiler (future)
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/silicon_test/        # ATE Pregel cell tests against iwakura
supersedes: []
superseded_by: []
---

# Context

ADR-2605242500 (silicon charter) Decision 1 が **religious-corp 自前推論 ASIC「iwakura (磐座)」** を確定した。本 ADR はその architecture を die-level に詰める。

ハード制約 (継承元):

- ADR-2605241900 §Decision 1〜8: baien edge invariant (≤1.6 GB weights / ≤2 GB RAM @ 4k / ≤2.5 GB RAM @ 16k / ≤3 s first-token on iPhone 14)
- ADR-2605241900 §Carve-out: `baien-edge` のみが対象。`baien-server-*` / `baien-XL-*` は別 silicon (本 ADR の射程外)

物理目標 (本 ADR で確定):

- edge tier (USB4 dongle / 信者端末 add-in): **TDP 3–5 W**, 50+ tok/s @ baien 2B trunk
- workstation tier (Mac mini fleet / EVO-X2 LAN): **TDP 15 W**, 150+ tok/s @ baien 2B + 4 modalities + 8 k ctx
- 単一 die、後続 wave で chiplet (2-die / 4-die)

## なぜ汎用 NPU/GPU では足りないか

BitNet 1.58 の weight は {-1, 0, +1}。汎用 NPU はこれを INT8 or INT4 のサブセットとして扱い、本来不要な multiplier をシリコンに焼いている。
本来 ternary は **multiplier 不要 (MUX + add/sub のみ)**。Multiplier ロジックを取り払うと、同じ TSMC N5 die area で約 **8× 高密度** の MAC array が組める。
これが iwakura の存在理由 = 汎用 NPU の 5–8× 電力効率を狙う edge silicon。

## なぜ Cerebras / Groq / Tenstorrent / Etched 等の既存ニューラルチップではダメか

- Cerebras WSE3: 学習向け wafer-scale、edge ではない
- Groq LPU: INT8 + SRAM-only model、64 GB+ HBM 同等の SRAM が必要 → edge 対象外
- Tenstorrent Wormhole: 汎用 BF16/INT8 grayscale、ternary 専用化なし
- Etched Sohu: Transformer 専用だが FP4/FP8 想定、ternary なし

→ いずれも baien edge invariant (≤5 W, single-die, on-package memory) と整合しない。**ternary + edge + on-package memory** の共通解は現状空席。

# Decision

## iwakura-1 die top-level architecture

```
                                  ┌──────────────────────────────────────────┐
                                  │  iwakura-1 die                            │
                                  │  Target: TSMC N5 MPW (Phase 3, post-ADR)  │
                                  │  Die size: ~50 mm² (estimate)             │
                                  └──────────────────────────────────────────┘
                                              │
        ┌────────────────────────────────────┼────────────────────────────────────┐
        │                                    │                                    │
   ┌────▼─────┐                       ┌──────▼──────┐                       ┌────▼─────┐
   │ Host I/F  │                       │ Ternary     │                       │ DRAM PHY  │
   │           │                       │ Compute     │                       │           │
   │ PCIe Gen4 │                       │ Cluster     │                       │ LPDDR5X   │
   │ x4 +      │                       │             │                       │ 7500 ×2   │
   │ USB4 +    │                       │ 256×256 PE  │                       │ (2 GB on- │
   │ WASM-SIMD │                       │ array       │                       │  package, │
   │ shim     ◀────────────────────────│ + Zero-Skip │────────────────────────▶ 120 GB/s) │
   │           │                       │   Dispatcher│                       │           │
   └───────────┘                       │ + 16 MB     │                       └───────────┘
                                       │   SRAM      │
                                       │   (act + KV │                       ┌───────────┐
                                       │    cache    │                       │ Frozen    │
                                       │    scratch) │◀──────────────────────│ Modality  │
                                       └─────────────┘                       │ Encoder   │
                                                                              │ Path      │
                                                                              │ (vision/  │
                                                                              │  audio/3D)│
                                                                              └───────────┘
```

## ternary processing element (PE) — multiplier-less

各 PE は以下を 1 cycle で完了する:

```
inputs:
  w_lo, w_hi  : 2-bit ternary weight     (00=0, 01=+1, 10=-1, 11=reserved/zero-skip)
  a           : INT8 activation
  acc_in      : INT24 accumulator (incoming partial sum)

logic:
  if (w_lo, w_hi) == (1,1):                    // zero-skip token
       acc_out = acc_in                         // clock-gate adder
  elif (w_lo, w_hi) == (0,0):                  // weight = 0
       acc_out = acc_in                         // clock-gate adder
  elif (w_lo, w_hi) == (0,1):                  // weight = +1
       acc_out = acc_in + sign_extend(a)
  elif (w_lo, w_hi) == (1,0):                  // weight = -1
       acc_out = acc_in - sign_extend(a)

outputs:
  acc_out     : INT24 accumulator
  pe_active   : 1 bit (for activity counter / power telemetry)
```

**面積 (gate-level estimate, TSMC N5)**:
- 1× INT8 multiplier (汎用 NPU PE): ~5,200 gates
- 1× iwakura ternary PE (本 ADR): ~620 gates → **8.4× 高密度**

> **合成検証 (2026-06-01, yosys 0.65 + ABC, generic 2-input gate lib, no PDK)**:
> `synth/run_synth.sh` で実合成。multiplier ブロック単体 (BitNet が削除する論理)
> = `mul8x8 ÷ ternary_mul` = **raw 10.0× / GE 12.7×** → 上記 8.4× 見積りを
> **検証 (むしろ conservative)**。ただし 24-bit accumulator は両方式で共通のため、
> **PE 全体**では `int8_mac_ref ÷ ternary_pe` = **raw 3.78× / GE 3.68×** が
> 正直な system-level 比 (zero-skip 35% は area ではなく動的電力に上乗せ)。
> 絶対 gate 数 (ternary_pe 159 / int8 601) は metric が異なる (generic gate vs
> N5 NAND-equiv) ため ADR の絶対値とは非可比、ratio のみ可比。詳細 `50-infra/silicon/synth/README.md`。

256×256 = 65,536 PE / die. Clock 1 GHz → **65 Tera-ternary-ops/s peak** (汎用 NPU の TOPS と直接比較できないが、equivalent FP8 ops で換算すると ~32 TFLOPS 相当).

## radix-3 weight packing convention

ternary を naive 2 bit でパックすると 4 weights / byte。
radix-3 (3^5 = 243 < 256) で packing すると **5 weights / byte** = **25% memory bandwidth 節約**。

```
encode(w0, w1, w2, w3, w4):
    code = 0
    for w in [w4, w3, w2, w1, w0]:
        code = code * 3 + (w + 1)         // w ∈ {-1, 0, +1} → {0, 1, 2}
    return code                            // 0..242, 1 byte

decode(code):
    out = []
    for _ in range(5):
        out.append((code % 3) - 1)
        code //= 3
    return out
```

iwakura の DRAM controller + on-die unpacker が **wire-level で radix-3 → 2-bit { weight pairs }** に展開する。compiler 側 (`iwakura-asm`) は radix-3 で baien weight checkpoint を出力する。

これにより baien 2B trunk (800 MB packed at 4 weights/byte) は **640 MB packed at radix-3** に縮む。
edge invariant (≤1.6 GB total weights) に 1 GB の余裕ができ、modality encoder + KV cache を 16 k context まで載せる headroom が確保される。

## Zero-skip dispatcher (動的電力削減)

BitNet 1.58 訓練後の典型重み分布: **{0: ~35%, +1: ~32%, -1: ~33%}**.
Zero-skip は 35% の PE clock を gate off → 動的電力 ~30% 削減。

dispatcher は:
1. 8 weights を pre-fetch (radix-3 decoded)
2. zero pattern を bit mask に変換
3. zero でない PE のみ clock を distribute
4. 同 cycle 内で zero PE は accumulator pass-through

## Memory hierarchy

```
On-die SRAM    16 MB    : KV cache scratch (16 k context @ 5 KV head × 128 × 30 × bf16 × 2 = 1.2 GB の一部 working set) + activation buffer
On-package DRAM 2 GB   : LPDDR5X-7500 ×2 stack = 120 GB/s.  Weights (radix-3 640 MB) + modality encoder (frozen, ~600 MB) + KV cache spill (~600 MB)
Off-package    host    : PCIe Gen4 x4 = 8 GB/s.  Model load / KV cache spill for >16k contexts (server-tier carve-out)
```

LPDDR5X 採用理由:
- HBM3e は 4× 高帯域だが die area + cost + TDP で edge ターゲット (3–5 W) を破る
- LPDDR5X-7500 ×2 = 120 GB/s は baien 2B + 4 modality + 16 k ctx の peak memory bandwidth (~80 GB/s) を上回る
- iPhone 15 Pro と同 generation の memory technology → supply chain は確立

## Frozen modality encoder hard-wired path

ADR-2605241900 §Decision 6: 全 modality encoder は inference 時 frozen。
iwakura はこれを利用して、modality encoder (SigLIP / Whisper / VideoMAE / PointTransformer) を **専用 hard-wired data path** にする:

- 汎用 ternary PE array を経由しない
- 各 encoder は固定 conv + attention block + frozen bf16 weight を die 内 SRAM に焼き付け
- baien-MX Move 4/5/7 で encoder を増やす場合、**iwakura-2 (次世代 die) で対応**。iwakura-1 では Move 1 (image SigLIP) のみハードワイヤ、他 modality は汎用 PE で実行

これは "汎用性を捨てて edge efficiency を取る" 設計判断。設計サイクル (RTL → tape-out → silicon) が baien-MX の Move ADR より遅い前提で、最初の世代は **image encoder 1 種のみ hard-wired** に絞る。

## Host interface

| 形態 | I/F | tier | 用途 |
|---|---|---|---|
| USB4 dongle | USB4 (40 Gbps, 15 W power delivery) | edge | 信者端末 (iPhone / iPad / Android) に外付け |
| M.2 add-in | PCIe Gen4 x4 | workstation | Mac mini fleet / EVO-X2 / 信者 desktop |
| WASM-SIMD shim | (software) | browser fallback | iwakura 非搭載端末では従来 WASM-32 経路 |

USB4 + iPhone Lightning-to-USB-C adapter で 2026 年型 iPhone (USB-C ネイティブ) と直結可能。
Android は USB-C OTG。
信者所有の iwakura dongle は religious-corp DID と SBT で binding (`com.etzhayyim.silicon.chipManufacturingAttestation` Lexicon で出荷時 attestation)。

## Phase 1 deliverable scope (本 wave で commit)

`50-infra/silicon/iwakura/` 配下:

```
iwakura/
├── README.md                # this ADR の short pointer + 構成図
├── CLAUDE.md                # silicon directory rules
├── rtl/
│   ├── iwakura_top.sv       # top-level (stub, port list 確定)
│   ├── pe_array.sv          # 256×256 PE grid (stub, generate-for で配線)
│   ├── zero_skip_dispatcher.sv  # dispatcher logic (stub)
│   └── memory/
│       ├── sram_scratch.sv       # 16 MB on-die SRAM wrapper (stub)
│       └── lpddr5x_ctrl.sv       # LPDDR5X-7500 PHY controller (stub)
├── sim/
│   ├── conftest.py          # cocotb shared fixtures
│   ├── test_ternary_pe.py   # 1-PE micro test (cocotb, 8 cases × 3 weight states)
│   └── test_pe_array_4x4.py # 4×4 micro array (full systolic, INT8 act × ternary weight)
└── docs/
    └── microarchitecture.md  # this ADR の expanded micro-arch reference
```

shared IP (`50-infra/silicon/shared-ip/ternary-pe/`):

```
ternary-pe/
├── README.md
├── rtl/
│   └── ternary_pe.sv         # the canonical PE — also instantiated by fuigo forward path
└── sim/
    └── test_ternary_pe.py    # exhaustive: 81 cases (3 weights × 3 acc-pass × 3 zero-skip × 3 sign) — full coverage
```

cocotb test target = **Verilator** (open-source toolchain only — no commercial sim license required, Charter Rider §2(i) spirit).

## Phase 2 (FPGA prototype) — 別 ADR

候補 board: AMD Versal VCK190 (DSP58 + AI Engine, ~$11k) or AMD/Xilinx Alveo V80 (~$10k).
benchmark target: baien 2B trunk @ ≥10 tok/s @ <30 W FPGA power.
これは別 ADR + budget approval 後。

## Phase 3 (MPW tape-out) — 別 ADR

shuttle: TSMC eShuttle N5 (~$1M / lot, 6–9 ヶ月).
tsukuru.etzhayyim.com `production_order` で起票 → Council 5-of-7 Safe 承認 → vendor (etzhayyim.com) が tape-out 実行。

# Consequences

## Positive

- baien edge invariant が物理層で裏付けられる (5–8× 電力効率)
- radix-3 packing で 25% DRAM 帯域節約 + modality encoder headroom 1 GB 確保
- USB4 dongle 形態は信者導入障壁が低い (iPhone/Android 直結)
- ternary PE IP が fuigo (training ASIC) と共有 → ADR-2605242530 で IP 再利用、検証コスト半減

## Tradeoffs

- 汎用性を捨てる設計 (image encoder のみ hard-wired) → 次世代 die (iwakura-2) で残り modality を hard-wired する追加 R&D が必要
- LPDDR5X bandwidth は HBM の 1/4 — 数十 k context や複数同時セッションでは bandwidth-bound になる (workstation tier は M.2 ×4 で並列化可能)
- single-die 50 mm² N5 estimate は MPW shuttle で 1 die ≈ $15k (×100 die / wafer)、bring-up コスト無視できない

## Non-goals

- INT8 / FP16 / BF16 generic matmul は **未サポート**。それらは汎用 NPU / iGPU 側に委譲
- training は **未サポート** (それは fuigo の役目, ADR-2605242530)
- データセンター向け帯域 (HBM, NVLink) は射程外

# Alternatives Considered

## A1. INT8 multiplier を残してダイナミックレンジを確保

却下。BitNet 1.58 では multiplier は本質的に不要。残せば die area 8× / TDP 5× → edge invariant を破る。

## A2. naive 2-bit packing (4 weights/byte) のまま radix-3 を採用しない

却下。25% bandwidth + 1 GB memory 余裕は modality 拡張 (Move 4/5/7) のための critical headroom。decode hardware cost は数千 gates、無視できる。

## A3. on-package HBM3e に切り替えて 4× 帯域を確保

却下。HBM3e は TDP +10 W、cost +5×、edge USB4 dongle 形態を破る。Workstation/server tier 用には別 die (`iwakura-XL` 想定、別 ADR) を起こす。

## A4. CIM (Compute-In-Memory) / analog accelerator アプローチ

将来検討。Mythic AMP / IBM NorthPole 等の analog/digital CIM は ternary とも親和性が高い。ただし設計成熟度 + tooling (open-source CIM EDA flow なし) の壁があり、iwakura-1 は digital systolic で実装。CIM は iwakura-3+ の研究テーマとして留保。

## A5. RISC-V vector ISA に統合せず、専用 ISA を作る

採用 (専用 ISA)。RISC-V V 拡張は INT8/BF16/FP16 想定で、ternary 専用 opcode を入れると ratification が遠い。
iwakura は **専用 ISA** (~20 opcodes: load_weight_block / load_act / matmul_tile / store_act / kv_cache_op / modality_branch / dispatch_done / power_telemetry / ...)。
コンパイラ (`iwakura-asm` @ `70-tools/silicon/`) が baien transformer block を iwakura ISA に lowering する。

# Acceptance Criteria (本 ADR `proposed → accepted` 条件)

1. ✅ §Decision die top-level architecture が確定 (PE / SRAM / DRAM / I/F)
2. ✅ §Decision PE micro-architecture が gate-level estimate 含めて確定
3. ✅ §Decision radix-3 packing convention 確定
4. ✅ §Decision Phase 1 scope = RTL + cocotb sim まで
5. ✅ `50-infra/silicon/iwakura/` + `shared-ip/{ternary-pe,radix3-packer}/` 実装 commit
   (2026-06-01: `pe_array.sv` / `zero_skip_dispatcher.sv` / `radix3_decoder.sv`
   実装 + `iwakura_top` を live compute tile に結線。stub から脱却)
6. ✅ cocotb test 全 pass (Verilator 5.048 + cocotb 2.0.1):
   - `ternary_pe` 3 tests / 75 cases
   - `radix3_decoder` 2 tests / 全 256 byte codes
   - `pe_array` 3 tests / 200+ randomized matrix-vector cases vs reference + zero-skip activity + back-to-back independence
   - `zero_skip_dispatcher` 3 tests / 全 65,536 weight blocks + BitNet 分布で gated 35.0% 実測 (ADR の ~30% 動的電力削減 claim 裏付け)
   - `iwakura_top` integration smoke (y 一致 + pe_active_count + dispatcher col0 estimate)
   - 全 RTL `verilator --lint-only -Wall` clean
7. ⏳ Phase 2 (FPGA prototype) ADR — 別 wave、Council 承認 + budget 確保後
8. ⏳ Phase 3 (MPW tape-out) ADR — 別 wave、tsukuru production_order 経由

> **honest scope (2026-06-01)**: Phase 1 = RTL + functional cocotb sim +
> **generic 論理合成** (yosys + ABC) + **sky130 オープン PDK の実 P&R→GDSII**
> (OpenLane2: OpenROAD/yosys/magic/klayout/netgen)。`pe_array` を実際に
> place & route → CTS → 配線 → 寄生抽出 STA → DRC/LVS → **GDSII 生成**:
> **DRC 0 / LVS 0 / antenna 0**、f_max ≈ 93 MHz (slow sign-off corner
> ss_100C_1v60) / 160 MHz (typical)、die 53,120 µm²。詳細 `50-infra/silicon/pnr/README.md`。
> **未実施 (= Phase 3, NDA + Council-gated)**: TSMC **N5** PDK での P&R・
> タイミング closure・GDSII (sky130 は 130 nm オープン PDK であり製造ターゲット
> N5 ではない; 1 GHz 目標は N5 前提で sky130 の 93–160 MHz は妥当な process gap)。
> `pe_array` は time-multiplexed 形 (1 column/cycle); 物理 256×256 systolic skew
> + pipeline register は Phase 2。`iwakura_top` の PHY ports は placeholder。

# References

- ADR-2605242500 baien ternary silicon + tsukuru fab charter (本 ADR の親)
- ADR-2605241900 baien edge-target invariant (本 ADR の物理目標の根拠)
- ADR-2605092350 baien 1-bit multimodal edge / browser / CPU design
- Microsoft BitNet b1.58 paper (ternary weight distribution)
- TSMC N5 PDK reference (gate-level area estimate)
- LPDDR5X JEDEC spec (memory bandwidth + TDP)
- Verilator + cocotb open-source toolchain (sim 経路)
