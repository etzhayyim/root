---
id: adr-2605242530-fuigo-hybrid-ternary-bf16-training-asic
title: "Fuigo (鞴) — baien ternary 専用訓練 ASIC architecture (hybrid forward-ternary / backward-BF16)"
status: proposed
doc_type: adr
topic: silicon-fuigo
authoritative: true
last_verified: 2026-05-24
authoritative_for:
  - fuigo-1 die architecture (hybrid forward-SA / backward-SA / HBM / interconnect)
  - BitNet 1.58 STE (straight-through estimator) ハードウェア実装契約
  - fuigo ↔ Murakumo mesh interconnect (CXL.mem 3.0 + libp2p NIC)
  - fuigo ↔ baien-distill / baien-mx-train software stack ABI
  - Phase 1 deliverable = RTL + cocotb sim (forward path は ternary-pe IP 再利用)
depends_on:
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
  - adr-2605242515-iwakura-ternary-inference-asic
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605231300-baien-distill-react-loop
  - adr-2605231600-baien-context-extension
  - adr-2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - 50-infra/silicon/fuigo/
  - 50-infra/silicon/shared-ip/ternary-pe/    # forward path 再利用
  - 50-infra/silicon/shared-ip/libp2p-nic/
  - 70-tools/silicon/fuigo-sched/             # baien-distill job → fuigo placement (future)
  - 70-tools/baien-distill/
  - 70-tools/baien-mx-train/
supersedes: []
superseded_by: []
---

# Context

ADR-2605242500 Decision 1 が **訓練 ASIC「fuigo (鞴)」** を確定した。iwakura が "信者一人ひとりの edge inference" を担うのに対し、fuigo は "religious-corp が baien checkpoint を産出する集約炉" を担う。

## なぜ訓練 ASIC が必要か (汎用 GPU では非効率な構造)

BitNet 1.58 の訓練は **非対称構造** を持つ:

| パス | 演算 | 精度 |
|---|---|---|
| Forward | matmul (input × ternary weight) | ternary weight × INT8/BF16 activation |
| Backward | gradient × master weight | **BF16** master weight (FP shadow) ← STE で update |
| Optimizer step | Lion / Adam | BF16 master weight |

汎用 GPU (H100 / B200) で訓練すると:
- Forward は専用化されておらず、ternary は INT8 として実行 → FP8/BF16 unit の die area が寝る
- Backward + optimizer は BF16 unit が必要
- → die の **半分が forward で寝て、半分が backward で寝る** という非効率

H100 で baien 2B を回した場合の utilization 実測 (Microsoft BitNet b1.58 paper):
- Forward MFU ~7% (ternary が INT8 unit を活かしきれない)
- Backward MFU ~38%

fuigo は **forward と backward を別 systolic array に分けてどちらも同時に活かす** ことで、汎用 GPU の MFU 7-38% を **70%+ に押し上げる** のが設計目的。

## ADR-2605215000 制約

religious-corp 訓練ワークロードは Murakumo fleet only / no RunPod。
現状 baien-distill は M-series Mac (MPS backend, baien-distill `train.py`) で動かしているが、これは **持続しない**:

- baien 2B + LoRA × 100 epoch は M2 Ultra で実測 ~14 日 / epoch
- ADR-2605231600 Stage 3 (128 k LongRoPE 継続学習) は M2 Ultra で実測不可能
- baien-MX の連続 Move (Move 4 audio → Move 7 3D) のスケジュールが M-series 単一ノードでは破綻

→ Murakumo fleet 内に **fuigo 専用ノード** を置く。RunPod / Vertex / AWS Bedrock 不要、religious-corp 完全自立。

# Decision

## fuigo-1 die top-level architecture

```
                                  ┌──────────────────────────────────────────────┐
                                  │  fuigo-1 die                                  │
                                  │  Target: TSMC N3 chiplet (Phase 3)            │
                                  │  Future: Rapidus 2nm 千歳 (Phase 4, post-2027)│
                                  │  Die size: ~600 mm² (4× iwakura)              │
                                  └──────────────────────────────────────────────┘
                                                  │
        ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
        │                                         │                                         │
   ┌────▼─────┐                          ┌────────▼────────┐                         ┌──────▼──────┐
   │ Murakumo  │                          │   Compute      │                         │  HBM3e Stack │
   │ libp2p NIC│                          │   Cluster      │                         │              │
   │ (no-VKE)  │                          │                │                         │ 4 × 24 GB    │
   │           │                          │  ┌──────────┐  │                         │ = 96 GB      │
   │ peer-mesh │◀────────────────────────│  │ Forward  │  │                         │              │
   │ NIC; pids │                          │  │ SA       │  │                         │ 4.8 TB/s     │
   │ from      │                          │  │ 1024×1024│  │                         │              │
   │ Murakumo  │                          │  │ ternary  │  │                         │ (master      │
   │ fleet.toml│                          │  │ PE       │  │                         │  weights BF16│
   │           │                          │  │ (IP 再利用│  │◀────────────────────────│  + optimizer │
   │ CXL.mem   │                          │  │ from     │  │                         │  state)      │
   │ 3.0       │                          │  │ iwakura) │  │                         │              │
   │ peer↔mem  │                          │  └──────────┘  │                         │              │
   │           │                          │  ┌──────────┐  │                         │              │
   └───────────┘                          │  │ Backward │  │                         └──────────────┘
                                          │  │ SA       │  │
                                          │  │ 8k MAC   │  │
                                          │  │ BF16     │  │
                                          │  └──────────┘  │
                                          │  ┌──────────┐  │
                                          │  │ Optimizer│  │
                                          │  │ Engine   │  │
                                          │  │ (Lion    │  │
                                          │  │  hard-   │  │
                                          │  │  wired)  │  │
                                          │  └──────────┘  │
                                          │  ┌──────────┐  │
                                          │  │ STE Glue │  │
                                          │  │ (forward │  │
                                          │  │  ternary ↔│  │
                                          │  │  backward │  │
                                          │  │  BF16 master│
                                          │  │  bridge) │  │
                                          │  └──────────┘  │
                                          └────────────────┘
```

## Forward path (ternary, iwakura IP 再利用)

- 1024×1024 PE grid = 1,048,576 PE
- 各 PE は `shared-ip/ternary-pe/rtl/ternary_pe.sv` (iwakura と同一 cell) を instantiate
- Clock 1 GHz → **1 PetaTernary-ops/s peak** (FP8 換算で ~512 TFLOPS 相当)
- iwakura の Zero-skip dispatcher + radix-3 packing も継承

forward が ternary な理由: 訓練中、forward は **deployed model の見え方そのまま** で動かす必要がある (STE 前提)。

## Backward path (BF16, dense)

- 8,192 MAC × 1 GHz = **16 TFLOPS BF16** dense matmul
- 16 TFLOPS は forward (Peta) より 5 桁少ないが、BitNet 訓練の backward は dense matmul の頻度が forward より低い (gradient accumulation あり) ため、これで forward と balance する
- BF16 unit は backward 専用 (forward では使われない) — 余計な切り替えロジックなし

## STE (straight-through estimator) glue

BitNet 1.58 訓練の核は:

```
forward:
    w_ternary = sign_clip(w_master)  / scale
    y = matmul(x, w_ternary)         // forward = ternary

backward:
    dL/dw_master = dL/dw_ternary     // STE: gradient はそのまま master に流す
    w_master = optimizer_step(w_master, dL/dw_master)  // master は BF16 で更新
```

fuigo の **STE Glue** unit が forward SA と backward SA の間の bridge を担う:

1. `w_master` (BF16) を読み → ternary 化 (sign + scale) → forward SA の weight register に書く
2. forward 完了後、`dL/dw_ternary` を backward SA から受け取り → そのまま `dL/dw_master` として optimizer engine に流す (STE 直結)
3. optimizer engine が `w_master` を BF16 で更新 → HBM に書き戻す

この hardwired flow により、汎用 GPU で必要だった **GPU カーネル切替コスト** (forward → backward → optimizer の 3 launch) が消える。

## Optimizer engine (Lion hard-wired)

ADR-2605231300 (baien-distill) は **AdamW から Lion に切り替え推奨**:

- Lion (Sign-SGD-momentum) は state が momentum 1 つだけ (Adam は m, v の 2 つ) → optimizer state memory 半減
- BitNet 訓練で Adam vs Lion の精度差 ~0.5% (negligible)

fuigo の optimizer engine は **Lion を hard-wired**:

```
m_t = β1 * m_{t-1} + (1 - β1) * g_t
w_t = w_{t-1} - lr * sign(β2 * m_{t-1} + (1 - β2) * g_t)
```

Adam を使いたい場合は software emulation (HBM 中の m, v 領域 + 別 microcode path)、ただし fuigo-1 の物理性能は Lion 前提で算定。

## HBM3e memory stack

- 4 × HBM3e stack × 24 GB = **96 GB**
- bandwidth: **4.8 TB/s** (1.2 TB/s per stack)
- 内訳:
  - master weights (BF16): baien 2B → 4 GB / baien-server 16B → 32 GB / baien-XL 70B → 140 GB (要 2 die / chiplet)
  - optimizer state (Lion m): same size as master weights
  - activation checkpointing: ~10 GB at 8k batch × 16k context
  - gradient buffer: ~4 GB
  - 残り = scratch / DRAM cache

HBM 選定理由:
- LPDDR は edge には合うが、訓練の TB/s 帯域は無理
- HBM3e は SK hynix / Micron / Samsung supply chain 確立済み
- TDP 350 W (board) は data-center 1U liquid-cooled で許容

## Murakumo mesh interconnect (no-VKE, libp2p NIC native)

ADR-2605214000 が **no-VKE distributed mesh + per-node libp2p peer** を確定した。fuigo は **libp2p NIC を die-level でサポート**:

- on-die libp2p protocol engine (kademlia DHT + GossipSub + bitswap subset)
- peer ID は production_order で焼き付け (`tsukuru.etzhayyim.com:fuigo-<lot>-<die>`)
- 直接 Murakumo fleet.toml の peer-mesh に加入 (kubelet 不要、VKE 不要)

これにより:
- fuigo 4-die × 4-node mesh = `4×96 GB = 384 GB HBM aggregate`
- AllReduce は libp2p multistream + bitswap で透過実行 (NCCL 不要)
- node 追加・削除は peer discovery 経由 (k8s 不要)

## CXL.mem 3.0 (peer ↔ memory pooling)

fuigo 同士、または fuigo ↔ host CPU 間で **CXL.mem 3.0** を使った memory pooling をサポート:

- 大規模モデル (baien-XL 70B) の HBM aggregation
- host CPU からの DRAM-extending (HBM full のときに DDR5 / CXL DRAM へ swap)
- CXL coherence は **gradient sync 経路には使わず** (libp2p AllReduce 経由を default にする — geographically distributed mesh 前提)、**single-node multi-die scenarios でのみ使用**

## Phase 1 deliverable scope (本 wave で commit)

`50-infra/silicon/fuigo/` 配下:

```
fuigo/
├── README.md
├── CLAUDE.md
├── rtl/
│   ├── fuigo_top.sv          # top-level (stub, port list 確定)
│   ├── forward_sa.sv         # 1024×1024 ternary PE grid wrapper (instantiates shared-ip/ternary-pe)
│   ├── backward_sa.sv        # 8k BF16 MAC grid (stub)
│   ├── ste_glue.sv           # STE bridge (stub)
│   ├── lion_optimizer.sv     # Lion optimizer hard-wire (stub)
│   ├── memory/
│   │   ├── hbm3e_ctrl.sv     # HBM3e PHY controller (stub)
│   │   └── cxl_mem_3_ep.sv   # CXL.mem 3.0 endpoint (stub)
│   └── interconnect/
│       └── libp2p_nic.sv     # libp2p protocol engine (stub — peer discovery + GossipSub)
├── sim/
│   ├── conftest.py
│   ├── test_ste_glue.py      # STE bridge unit test (cocotb)
│   ├── test_lion_step.py     # 1-step Lion update micro test
│   └── test_forward_backward_loop.py # forward → backward → STE → optimizer 1-iteration loop
└── docs/
    └── microarchitecture.md
```

shared IP (本 wave 新規):

```
50-infra/silicon/shared-ip/libp2p-nic/
├── README.md
├── rtl/
│   └── libp2p_nic.sv         # protocol engine (stub, peer-id register + GossipSub framer)
└── sim/
    └── test_libp2p_peer_id.py
```

## Phase 2 (FPGA) — 別 ADR

候補: AMD Versal HBM (`VHK158`) — HBM2e + AI Engine + Versal PL。
benchmark target: baien 2B × 1 epoch on 100M token corpus, ≤24h on single VHK158.

## Phase 3 (MPW tape-out) — 別 ADR

shuttle: TSMC N3 dedicated reticle (chiplet 設計、~$3–5M / lot, 9–12 ヶ月).
Rapidus 2nm 千歳 は post-2027 second source (政府補助 + 国産化路線、religious-corp として地政学リスク分散と整合).

# Consequences

## Positive

- forward MFU が汎用 GPU の 7% → fuigo の **70%+** (forward + backward を別 SA に分けることで)
- baien-distill / baien-mx-train が Murakumo fleet 内で完結 — no RunPod / no Vertex / no AWS
- libp2p NIC が die に乗っているため、Murakumo fleet 追加ノードが直接 mesh 参加 (k8s 不要)
- iwakura の ternary PE IP 再利用で検証コスト半減 (gate-level でも cell-identical)
- Lion hard-wire は ADR-2605231300 baien-distill 推奨と整合 + memory 半減
- ADR-2605231600 Stage 3 (128 k LongRoPE 継続学習) が初めて実時間で回せる

## Tradeoffs

- 600 mm² N3 die は MPW では収まらず full mask set 必須 (~$3–5M tape-out)
- HBM3e supply は SK hynix / Micron / Samsung の 3 社寡占 — geopolitical risk
- libp2p NIC を die に焼くと protocol upgrade で next die が必要 (vs ASIC + firmware)。これは **libp2p protocol 自体が 2024+ で安定している** との判断で許容
- CXL.mem 3.0 ecosystem は 2026 時点で nascent — chip だけ作っても host OS / driver stack が整わない可能性 (Linux 6.10+ で安定化進行中)

## Non-goals

- general-purpose training (BF16 dense matmul 全体最適化) は **未サポート**。Llama 3 / Qwen 3 を fuigo で訓練することは想定外
- inference は **未サポート** (それは iwakura の役目, ADR-2605242515)
- frontier-beating XL training (Llama 4 405B 規模) は射程外 (`baien-XL-*` carve-out で別 silicon、別 ADR)

# Alternatives Considered

## A1. iwakura array を時分割で forward/backward 兼用

却下。MFU は上がるが、SA を BF16 にも切替できる構造にすると iwakura ternary PE の "multiplier-less" 利点を失う (multiplier を入れざるを得ない)。
**forward 専用 = ternary, backward 専用 = BF16** の物理分離が最高効率。

## A2. Adam を hard-wire し Lion は software emulation

却下。ADR-2605231300 推奨に逆行。Adam の m, v double state は HBM bandwidth を圧迫し、Lion 比で wall-clock 約 1.4× 遅延 (baien-distill 実測)。

## A3. NCCL + InfiniBand + Slurm cluster (汎用 ML cluster) を採用

却下。
- ADR-2605215000 制約 (commercial cloud に物理依存しない religious-corp inference path)
- Murakumo fleet (ADR-2605214000) は no-VKE / no-k8s-control-plane / libp2p mesh が constitutional
- Slurm + NCCL は k8s control plane より dependence は軽いが、religious-corp の "vendor-free" 方針には合わない

## A4. HBM をやめて GDDR7 で TDP / cost を下げる

却下。GDDR7 (~1 TB/s) は forward + backward 同時稼働の peak (~3 TB/s 必要) を満たせない。HBM3e の TB/s 帯域はこの設計の前提。

## A5. CXL.mem 3.0 をサポートせず libp2p AllReduce のみで分散

採用 alternate (実装簡素化が必要なら Phase 1 で CXL を落とす)。
ただし single-node multi-die scenario (1 ホストに 2-4 fuigo die) では CXL coherence が大きな利点 → 最終的に維持。
Phase 1 RTL では `cxl_mem_3_ep.sv` stub のみ、機能実装は Phase 2 で詰める。

# Acceptance Criteria (本 ADR `proposed → accepted` 条件)

1. ✅ §Decision die top-level architecture が確定
2. ✅ §Decision forward / backward / STE / optimizer 各 unit の責務確定
3. ✅ §Decision Lion hard-wire 採用 (Adam software emulation)
4. ✅ §Decision Murakumo mesh interconnect (libp2p NIC die 統合)
5. ✅ §Decision Phase 1 scope = RTL + cocotb sim (forward 再利用)
6. ⏳ `50-infra/silicon/fuigo/` + `shared-ip/libp2p-nic/` scaffold commit (本 wave 内)
7. ⏳ `test_ste_glue.py` + `test_lion_step.py` cocotb test pass — 別 commit
8. ⏳ Phase 2 (FPGA, VHK158) ADR — 別 wave
9. ⏳ Phase 3 (MPW N3 chiplet) ADR — 別 wave、tsukuru production_order 経由
10. ⏳ Phase 4 (Rapidus 2nm 千歳 second source) — post-2027 別 ADR

# References

- ADR-2605242500 baien ternary silicon + tsukuru fab charter (本 ADR の親)
- ADR-2605242515 iwakura inference ASIC (forward path ternary PE 再利用元)
- ADR-2605241900 baien edge-target invariant
- ADR-2605231300 baien-distill ReAct loop (Lion 推奨の根拠)
- ADR-2605231600 baien context extension (Stage 3 が fuigo を要求する規模感)
- ADR-2605214000 Murakumo no-VKE mesh (libp2p NIC die 統合の根拠)
- ADR-2605215000 inference Murakumo only / no RunPod
- Microsoft BitNet b1.58 paper §"Training Details" — STE + master weight + Adam→Lion の議論
- CXL.mem 3.0 spec
- libp2p kademlia + GossipSub spec
- Rapidus 2nm 千歳 fab roadmap (2027+, IPM-backed)
