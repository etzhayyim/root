---
id: adr-2606074000-iryo-rezept-claims-engine-charter
title: "ADR-2606074000: iryo 医療 — Japan レセプト / 医療保険請求 engine (electronic karte → claims)"
status: proposed
doc_type: adr
topic: iryo-rezept-claims-engine
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/iryo
depends_on:
  - adr-2605231100-karute-emr-phase1
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605263000-iyashi-clinical-care-provider-tier-b-actor-r0
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605250500-yakushi-pharmaceutical-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
supersedes: []
superseded_by: []
---

# ADR-2606074000: iryo 医療 — Japan レセプト / 医療保険請求 engine

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

The roster carries a 電子カルテ (EMR) actor — `karute` (ADR-2605231100) — modelling
Patient / Encounter / SOAP / Condition / MedicationRequest as FHIR-shaped encrypted
records. But `karute` was **design/lexicon scaffolding only**: it has no implementation
and it explicitly delegates 保険請求 (insurance billing) to an unbuilt `iryo`
counterpart (`iryo.etzhayyim.com (vendor) | 保険請求 (DPC/DRG)`).

Japan's outpatient/inpatient reimbursement runs on the **レセプト** (診療報酬請求明細書):
a per-patient, per-month claim of 点数 (1点 = 10円) computed from the 診療録, aggregated by
診療識別 区分 (初診/再診/医学管理/在宅/投薬/注射/処置/手術/検査/画像診断/その他), reduced to a
一部負担金 (window copay) by 負担割合 and capped by 高額療養費, then transmitted to the
審査支払機関 (社会保険診療報酬支払基金 / 国保連) as a **レセ電** (レセプト電算処理システム) record
stream over the closed オンライン請求 IP-VPN.

There is a charter tension. `iyashi` (clinical care, ADR-2605263000) carries **G13: NO
insurance billing**, because the religious-corp is constitutionally NOT registered under
宗教法人法 (Preamble §0.4) and direct insurance-billing **inflow to the corp** is excluded.
So who runs レセプト?

The resolution mirrors `warifu` (open card, member settles), `toritsugi` (procedure
concierge, default self-submit), and `chigiri` (legal-procedure substrate, not a law
firm): build the レセプト computation as an **open tool a licensed member 保険医療機関
self-operates**, where the clinic — not etzhayyim — is the billing principal and bears the
保険医療機関 license, and no insurance inflow accrues to the corp. This is the charter-clean
inversion of a proprietary レセコン / EHR-billing vendor (ORCA-proprietary / Epic / Cerner).

# Decision

Build **`iryo` (医療)** as a Tier-B R0 actor: the レセプト計算 + レセ電生成 + FHIR-claim engine,
the billing counterpart `karute` already references. Self-contained, pure-stdlib +
pywasm-ready, with a verifiable arithmetic core and 51 green tests.

**全件対応 (all 診療行為 / 薬剤 / 特定器材 / 病名).** The official 厚労省 / 支払基金 master is
tens of thousands of copyrighted rows; iryo does not embed it but **ingests** it
(`master_loader.py`) so every code becomes resolvable. Two paths: an iryo-defined normalized
CSV (fully tested), and the raw 厚労省 基本マスター CSV via an overridable `ColMap` (column
positions documented as approximate, verified by the operator against the current 記録条件仕様).
`Masters.merge()` composes seed + official master. The seed remains representative; the
engine arithmetic is the verifiable contract.

**Full computation coverage.** 診療区分: 初診/再診/医学管理/在宅/投薬(内服・屯服・外用)/
注射(皮下・静注・点滴)/処置/手術/麻酔/検査/病理/画像診断/その他/入院. Plus 年齢区分
(乳幼児/成人/前期高齢/後期高齢)→負担割合 (`insurance.py`); 公費負担医療 (生活保護/難病/自立支援
…) の重ね合わせ + 負担区分; 高額療養費 全区分 (70歳未満 ア〜オ + 70歳以上 現役並み・一般・低所得、
外来個人上限/世帯上限, `kogaku.py`); 入院時食事療養 標準負担額. レセ電 records:
IR/RE/TY/HO/KO/SY/SI/IY/TO/CO/SJ.

**Pipeline** (3 Pregel cells):

1. `rezept` (`handle_rezept`) — encounter(codes only) → 点数計算. 診療行為 / 薬剤料 / 特定器材料
   resolved through a loaded master, grouped by 診療識別 → 区分集計 → 総点数 → 総医療費(×10円)
   → 一部負担金(10円未満四捨五入) → 高額療養費 自己負担限度額 調整.
2. `receden` (`handle_receden`) — karte + encounter → レセ電 record stream
   IR/RE/HO/KO/SY/SI/IY/TO + 件数 reconciliation; 和暦(GYYMMDD)変換; **PHI-free by default**.
3. `validate` (`handle_validate`) — 算定整合性チェック → discrepancy observations
   (病名なし投薬 / 主傷病なし / 空レセプト / 高額療養費上限); **non-adjudicating**.

Plus `export_fhir` — Coverage / Condition(ICD-10-JP) / Claim R4 Bundle (codes-only).

**Exact, tested arithmetic** (the verifiable core, never hard-coded):

- 1点 = 10円 (master-driven `tensu_tanka_yen`).
- **薬剤料 五捨五超四入**: 薬価 ≤15円→1点; >15円→ 薬価/10 の端数を「五捨五超」(0.5以下切捨,
  0.5超切上); 内服は投与日数を乗じる.
- **一部負担金 端数処理**: 総医療費 × 負担割合 を 10円未満四捨五入.
- **高額療養費 (70歳未満 月額)**: ア 252,600+(医療費-842,000)×1% / イ 167,400+(-558,000)×1%
  / ウ 80,100+(-267,000)×1% / エ 57,600 / オ 35,400.

**Seven gates** (manifest.edn): G1 member-principal · G2 PHI-encrypted · G3 no-server-key ·
G4 master-honest · G5 non-adjudicating · G6 Murakumo-only · G7 no-religious-corp-inflow.

**PHI discipline** (structural, not policy): rotating pseudonym patient DID
(ADR-2605181200, never a stable MRN); `Karte.public_meta()` codes-only with
`Karte.assert_no_phi()` guard; `SoapNote` refuses construction without an `encrypted_cid`;
レセ電 氏名/生年月日 injected **only** via the operator `phi` callback at submission, over the
closed 審査支払機関 IP-VPN, never the public substrate.

**Master honesty (G4)**: every point value resolves through `masters.Masters`. The bundled
`py/seed_masters.json` is a **representative seed for engine verification only**; a
production 保険医療機関 loads the official 厚労省 / 支払基金 診療行為・医薬品・特定器材・傷病名
master. The engine arithmetic is exact and tested; the seed values are not authoritative.

# Consequences

- The roster gains a working, tested 電子カルテ→レセプト pipeline (the karute EMR's missing
  billing half), charter-clean: the member clinic is the billing principal; the corp takes
  no insurance inflow (iyashi G13 preserved via iryo G7).
- レセ電 output is PHI-free by default → safe to compute / draft / store on the public
  substrate; PHI is materialised only at the operator's online-請求 step.
- iryo is **non-adjudicating**: it surfaces alg'n discrepancies but never 査定/返戻 — the
  審査支払機関 and the clinic decide.
- R0 ships the engine + cells + lexicons + schema + tests + demo. R1 (gated): wire
  `karute` encrypted-envelope → iryo codes-only projection handoff; load an official master;
  Council + ≥1 保険医療機関 member operator; online-請求 connector (operator-keyed, no-server-key).

# Alternatives Considered

1. **Put レセプト inside `karute`.** Rejected: karute is the PHI store (clean 3-axis,
   religious-corp custody); billing is deliberately the separate vendor-side counterpart so
   the corp takes no insurance inflow. Keeping them separate preserves the iyashi G13 line.
2. **Let `iyashi` bill.** Rejected: iyashi G13 forbids it (corp not 宗教法人法-registered).
3. **Hard-code the 2024 点数表 into the engine.** Rejected (G4): tariffs change each 改定;
   a hard-coded tariff is both wrong-over-time and dishonest. The engine stays master-driven
   and the seed is explicitly representative.
4. **Emit faithful レセ電 with 氏名/生年月日 inline.** Rejected (G2): PHI on the public
   substrate is prohibited; PHI is injected only at the closed-VPN submission boundary.

# References

- `20-actors/iryo/` — engine, cells, lexicons, schema, tests, demo
- `90-docs/adr/2605231100-karute-emr-phase1.md` — karute EMR (handoff source)
- `90-docs/adr/2605181100-mst-encrypted-records-signal-keywrap.md` — PHI envelope
- `90-docs/adr/2605263000-iyashi-clinical-care-provider-tier-b-actor-r0.md` — L4 / G13 boundary
- `90-docs/adr/2605215000-etzhayyim-inference-murakumo-only-no-runpod.md` — G6 inference
- 厚生労働省 診療報酬点数表 (令和6年度改定) / 社会保険診療報酬支払基金 レセプト電算処理システム 記録条件仕様
