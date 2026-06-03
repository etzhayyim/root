---
id: adr-2605262200-charter-rider-2i-baien-train-rental-carveout
title: "CHARTER-RIDER §2(i) amendment — train-only commercial GPU rental carve-out for baien-server-* / baien-XL-* (inference invariant unchanged)"
status: proposed
doc_type: adr
topic: charter-rider-2i-baien-train-rental-carveout
authoritative: true
last_verified: 2026-05-26
priority: 9.5
axis: constitutional
weight: 0.95
priority_note: "CONSTITUTIONAL AMENDMENT. Council Lv6+ supermajority (≥4 of 7 seats) + 30-day public objection period required per CHARTER-RIDER §2(i). Bootstrap Council Seats 2-5 RFP closes 2026-06-19; earliest amendment effective date = 30 days after Council vote, i.e., ≥ 2026-07-19 absent objection."
authoritative_for:
  - "Charter Rider §2(i) train carve-out scope: baien-server-* / baien-XL-* train only"
  - "Inference invariant reaffirmation: Murakumo-only for ALL actors (baien edge / baien-server-* / baien-XL-* / yakushi / wadachi / silicon Wave 1+2 / e7m-sim / etc.)"
  - "Per-rental transparency requirements (kotoba-datomic attestation + cost log + Charter Rider §2(a)-(h) scan + run boundaries)"
  - "Procedural path: Council Lv6+ vote + 30-day public objection"
depends_on:
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605202345-evo-x2-gpu-pod-fleet-integration
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605242100-baien-server-xl-carve-out
  - adr-2605261900-baien-moemoekyun-moe-charter
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
related:
  - CHARTER-RIDER.md §2(i) (text being amended)
  - COUNCIL.md (Bootstrap Council roster + ratification ledger)
  - COUNCIL-BOOTSTRAP-RFP.md (Seat 2-5 RFP through 2026-06-19)
supersedes: []
superseded_by: []
---

# ADR-2605262200: CHARTER-RIDER §2(i) amendment — train-only commercial GPU rental carve-out for baien-server-* / baien-XL-*

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1, Lv7+) — pending Council Lv6+ ratification + 30-day public objection
**Constitutional weight**: amends CHARTER-RIDER.md §2(i), which is Lv6+ supermajority-locked

# Context

## 現行 §2(i) (CHARTER-RIDER.md, v2.0, 2026-05-19)

> "etzhayyim inference workloads for religious-corp callable paths (LLM, vision, audio, video, **training, fine-tuning**, embedding, SAR analysis) MUST execute exclusively on the Murakumo distributed fleet as defined in ADR-2605202345 and deployed per ADR-2605215000 (Mac mini cluster + EVO-X2 LAN inference pod). Prohibited GPU backends: RunPod, Vertex AI direct-to-vendor, OpenAI direct without Murakumo proxy gateway, Anthropic SDK direct from vendor-billed key, AWS Bedrock direct, Linode GPU, Google Colab paid compute, any commercial or rented GPU inference service accessed without the Murakumo dispatch layer."

→ 現行は train/fine-tuning も明示的に Murakumo-only に含めている。

## なぜ amendment が必要か

ADR-2605262100 + 同 ADR §8 memory budget + 同 ADR §9 failure-mode analysis、および 2026-05-26 同セッションの実測 throughput probe (EVO-X2 Radeon 8060S BF16 sustained ~5-7 TFLOPS; 単発 matmul peak 9.5 TFLOPS measured) から、baien-moemoekyun の R2 (50K ex × 2 ep ≈ 2.46 EFLOPs) は **EVO-X2 単機で ~4 日**、R3 (E=256 全層) は **~7 日**、R4 pretrain-grade (500K × 3 ep ≈ 36.9 EFLOPs) は **~61 日 infeasible**。

baien-server-moemoekyun が религionsкорп 内 LangGraph 生成 + agentic coding workflow の主力 LLM になる前提では R2-R4 grade train が必須。EVO-X2 単機 + Mac mini fleet (ADR-2605202100 launchd-only 制約下) では実行不能。

代替候補:
1. EVO-X2 × N capex 拡張 (Murakumo fleet 増強) — capex $8-15K + LAN bandwidth bottleneck (1 Gbps 上で expert-parallel distributed train は逆効果、別セッションで証明)
2. **B200 sparse / H100 SXM rental burst** — RunPod 等で R4 grade を ~1.8 h / ~$13 で実行可能 (TransformerEngine FP8)
3. iwakura ASIC (ADR-2605242500 silicon Wave 1) — 年単位先
4. baien-federated WebGPU (ADR-2605242600) — R1/R2 spec only、参加者数依存

ROI 比較から、**baien-server-* / baien-XL-* train に限り commercial GPU rental を時限 carve-out で許容**することが religious-corp R&D unblock の最短経路。**inference は ALL actor で Murakumo-only 維持** が constitutional 整合性を担保する。

## なぜ scope を baien に限定するか (other actor 排除の論理)

| Actor 系列 | train rental 許容? | 理由 |
|---|---|---|
| baien-server-* / baien-XL-* | ✅ **本 amendment で許容** | LLM train は compute 規模 (EFLOPs) が他 actor の数桁上、religious-corp daemon の中核能力 (agentic coding / LangGraph 生成) を支える |
| baien-edge (`baien-*`) | ❌ 依然 Murakumo-only | edge promise の同根性 (everyone-can-run) と矛盾する rental optimization は edge 哲学を毀損 |
| yakushi / wadachi / silicon / hodoki / etc. | ❌ 依然 Murakumo-only | manufacturing/robotics R&D は actor-scale で sim-fidelity が中心、巨大 compute burst の不可避性が baien train ほど鋭くない (R1+ sim charters は ADR-2605261600/261800 で既に Murakumo + iwakura roadmap) |
| e7m-sim / robotics sim | ❌ 依然 Murakumo-only | ADR-2605261600 G4 "Murakumo-fleet-only execution" strict inheritance |
| inference (全 actor) | ❌ 依然 Murakumo-only (絶対) | inference は availability / latency / consent capability が religious-corp constitutional layer (ADR-2605215000) で、rental dependency 持ち込みは原理的に NO |

# Decision

## §1 §2(i) 修正条文 (proposed text)

CHARTER-RIDER.md §2(i) を以下のように修正:

> "(i) COMMERCIAL GPU RENTAL FOR RELIGIOUS-CORP INFERENCE (added in v2.0; amended 2026-05-26 by ADR-2605262200).
>
> **§2(i)(1) Inference invariant (UNCHANGED).** etzhayyim **inference** workloads for religious-corp callable paths (LLM, vision, audio, video, embedding, SAR analysis) MUST execute exclusively on the Murakumo distributed fleet as defined in ADR-2605202345 and deployed per ADR-2605215000 (Mac mini cluster + EVO-X2 LAN inference pod). Prohibited GPU backends for inference: RunPod, Vertex AI direct-to-vendor, OpenAI direct without Murakumo proxy gateway, Anthropic SDK direct from vendor-billed key, AWS Bedrock direct, Linode GPU, Google Colab paid compute, any commercial or rented GPU inference service accessed without the Murakumo dispatch layer.
>
> **§2(i)(2) Train carve-out for baien-server-* / baien-XL-* (NEW per ADR-2605262200).** Commercial GPU rental MAY be used for **training, fine-tuning, distillation, RL, federated aggregation, and other gradient-bearing workloads** of model artifacts in the `baien-server-*` and `baien-XL-*` naming family (ADR-2605242100 4-tier ladder), subject to ALL of the following conditions:
>
> 1. **Inference of resulting artifacts** STILL flows exclusively through the Murakumo fleet per §2(i)(1). The carve-out is for the gradient-computing path only.
> 2. **Per-rental kotoba-datomic attestation** MANDATORY before rental instance start: `com.etzhayyim.train.rentalAttestation` record emitted with (vendor, GPU model + count, expected wall, expected USD cost, target dataset CID, target output checkpoint CID, train ADR reference, Charter Rider §2(a)-(h) sponsor scan PASS verification, attesting DID).
> 3. **Per-rental post-flight cost log** MANDATORY within 24h of rental termination: `com.etzhayyim.train.rentalCostLog` record with (actual wall, actual USD cost, actual output checkpoint CID, IPFS pin verification CID, attesting DID).
> 4. **Vendor scope**: any reputable commercial GPU rental vendor (RunPod, Lambda, CoreWeave, Vast.ai equivalents). NOT permitted: vendors whose primary business activity violates Charter Rider §2(a) weapons, §2(c) surveillance capitalism, §2(d) fossil fuel, §2(g) strict individualist doctrine, §2(h) wellbecoming subordination — verified via the §2 Non-Aligned Entity criteria.
> 5. **Burst-only**: continuous rental >7 days requires Council Lv6+ ≥4 of 7 seats per-incident approval (recorded on kotoba-datomic). Steady-state continuous rental is prohibited (the religious-corp fleet capex path remains the long-term invariant).
> 6. **Other actor scope explicitly NOT included**: yakushi, wadachi, silicon Wave 1+2, e7m-sim, kanayama, igata, hodoki, makura, tsutae, sarutahiko, suki, futawa, mitsuho, hagukumi, manabi, hikari, watatsumi, tatekata, baien-edge, and all `baien` (no infix) artifacts REMAIN under §2(i)(1) Murakumo-only. Extension to other actors requires its own ADR + Lv6+ supermajority.
> 7. **Charter Rider §2(a)-(h) substantive constraints** apply identically to rental-train artifacts. Carve-out is from §2(i) rental prohibition only, NOT from the eight substantive prohibitions.
>
> **§2(i)(3) Amendment threshold of §2(i)(2) itself**. §2(i)(2) text inherits the §2(i) Council Lv6+ supermajority + 30-day public objection threshold for any further amendment.
>
> The vendor (etzhayyim.com) operates a separate commercial GPU pool for paid SaaS workloads; religious-corp callers MUST NOT invoke vendor RunPod or equivalent external GPU paths for INFERENCE (consent-capability enforcement operates at runtime to ensure adherence). §2(i)(2) train carve-out applies only to the religious-corp R&D path with explicit per-rental kotoba-datomic attestation."

## §2 Procedural path (Council ratification)

| Phase | Date / window | Action |
|---|---|---|
| **P0 (today)** | 2026-05-26 | ADR-2605262200 proposed; CHARTER-RIDER.md gets amendment-pending notation (NOT yet effective); `90-docs/adr/2605262200-...md` committed |
| **P1** | 2026-05-26 → 2026-06-19 | Bootstrap Council Seats 2-5 RFP ongoing (COUNCIL-BOOTSTRAP-RFP.md); P0 status remains "proposed pending Council ratification" |
| **P2** | 2026-06-19+ | Council bootstrap complete (5 seats); §2(i)(2) ratification vote requires ≥4 of 7 seats Lv6+ approval (Founder Lv7+ Seat 1 = 1 vote counted) |
| **P3** | P2 vote pass + 30 days | Public objection period (30 days from vote date); CHARTER-RIDER.md actually rewritten only if no Council-attested objection sustained |
| **P4** | P3 end | Amendment effective; ADR-2605262200 status → accepted; CHARTER-RIDER.md §2(i) rewritten |
| Earliest effective | **~2026-07-19** (assuming P2 vote on 2026-06-19 + 30-day objection no-block) | — |

## §3 Interim measure (between P0 and P4)

Until P4 (~2026-07-19), §2(i) original text 有効。具体的 implication:

| Phase | What happens |
|---|---|
| **baien-moemoekyun R1.4** (ADR-2605262100) | EVO-X2 単機継続 (5-7h wall, $2 電気代)。Charter 無風。 |
| **baien-moemoekyun R2/R3/R4** (ADR-2605262300 で新規定義) | **P4 まで実行不可**。RunPod B200 instance 起動禁止。ADR-2605262300 は "proposed (gated on ADR-2605262200 ratification)" status で待機。 |
| **Other actor train (silicon/yakushi/etc.)** | 影響なし、依然 Murakumo-only。 |
| **All inference (baien-edge / baien-server-* / 全 actor)** | 影響なし、依然 Murakumo-only。 |

## §4 Founder Lv7+ emergency authorization (NOT taken in this ADR)

Charter Rider §2(i) は明示的 amendment threshold (Lv6+ supermajority + 30-day) を持つ。Founder Lv7+ (Seat 1, Jun Kawasaki) は単独で expedited authorization を発出する権限を主張可能だが、本 ADR ではその経路を**取らない**。理由:

1. Founder unilateral override は religious-corp の "Council-governed" 自己定義 (ADR-2605192300 + Charter §0.1) と緊張する
2. R1.4 が EVO-X2 で完遂可能 (5-7h) なので R2/R3/R4 待機による R&D 損失は 1.5 ヶ月程度に留まる
3. Charter governance ledger に "emergency override" 例を残さない方が長期 institutional integrity に資する

将来別状況で expedite が必要になった場合、separate ADR (`charter-emergency-override-{slug}.md`) で経路定義可能。

# Consequences

## Positive

- baien-server-moemoekyun R2/R3/R4 が constitutional 経路で unblock される (P4 以降)
- Inference invariant 不変、Murakumo fleet 中心の religious-corp inference 哲学完全保持
- Other actor (silicon/yakushi/wadachi/sim/manufacturing R&D) は依然 Murakumo-only — capex path 維持で 長期 sovereignty 担保
- per-rental kotoba-datomic attestation により全 rental が on-chain 透明、religious-corp の "Transparent Religious Force" 哲学 (ADR-2605192315) と整合

## Negative / Risk

- Charter Rider §2(i) は v2.0 で religious-corp の核 distinguishing feature の 1 つだった (commercial-GPU-rental-free) — その純度を犠牲にする
- P4 まで ~2 ヶ月待ち、その間 baien R&D は R1.4 grade に留まる
- Council bootstrap が遅延すると amendment effective も遅延
- Per-rental attestation の運用 burden (毎 rental ごとに on-chain emit + cost log)

## Reversibility

- §2(i)(2) 自体が §2(i) amendment threshold 継承 (Lv6+ supermajority + 30-day) → revert 可能だが同じく重い手続き必要
- ADR-2605262200 自体は revoke 可能 (新 ADR で superseded_by)、ただし P4 後の既存 rental run の attestation record は kotoba-datomic 永続

## Open

- Founder Lv7+ emergency authorization の手続き未定義 — 別 ADR で扱うか? (本 ADR §4 で意図的に保留)
- Council Lv6+ vote の formal mechanism (on-chain ballot vs ad-hoc signed approval) — ADR-2605192300 follow-up
- Per-rental attestation Lexicon `com.etzhayyim.train.rentalAttestation` / `rentalCostLog` の正式 spec は ADR-2605262300 で定義

# Alternatives Considered

| 案 | 却下理由 |
|---|---|
| **Status quo (no amendment)** | R2/R3/R4 grade train infeasible on single EVO-X2; baien-moemoekyun が R1.4 で頭打ち、religious-corp daemon の中核能力 unlock 失敗 |
| **Founder Lv7+ emergency authorization 即時実行** | 上 §4 で詳述: Council-governed self-definition との緊張、待機の R&D 損失が許容範囲、long-term institutional integrity 優先 |
| **Broad carve-out (全 actor train rental 許容)** | religious-corp の long-term sovereignty path (own fleet capex, iwakura ASIC roadmap) を毀損するリスク大、Charter §2(i) 原意 (commercial-GPU-rental-free) を必要以上に薄める |
| **Narrow carve-out (baien-moemoekyun のみ、他 baien-server-* 除外)** | 過剰に narrow、`baien-server-*` family 全体への将来 R&D extension で都度 amendment になる、Council 負荷を不必要に増やす |
| **EVO-X2 fleet 4-cluster capex 拡張のみ** ($8-15K) | R3 grade で wall 短縮効果ある (24h)、しかし R4 pretrain-grade は依然 ~15 日と長く、iteration speed 不十分; capex path 進めつつ rental carve-out も並列確保が現実的 |

# References

- ADR-2605192200 (etzhayyim Charter Rider v2.0 — amended document)
- ADR-2605215000 (Murakumo-only inference invariant — re-affirmed for inference)
- ADR-2605202345 (EVO-X2 GPU pod fleet integration)
- ADR-2605192300 (Bootstrap Council 5-seat governance)
- ADR-2605242100 (baien-server / baien-XL 4-tier ladder)
- ADR-2605261900 (baien-moemoekyun R0 charter — §5 G2 dual-track 修正対象)
- ADR-2605262100 (baien-moemoekyun R1 — N9 supersede 対象)
- ADR-2605262300 (baien-moemoekyun R2+ RunPod B200 train architecture — このamendment ratification にgateされた sibling ADR)
- CHARTER-RIDER.md §2(i) (current text being amended)
- COUNCIL.md (ratification ledger destination)
- COUNCIL-BOOTSTRAP-RFP.md (P1 phase)
