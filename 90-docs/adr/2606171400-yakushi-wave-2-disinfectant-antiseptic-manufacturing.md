---
id: adr-2606171400-yakushi-wave-2-disinfectant-antiseptic-manufacturing
title: "yakushi Wave 2 — disinfectant / antiseptic (消毒薬) formulation manufacturing (ethanol / hypochlorite / povidone-iodine / chlorhexidine / BAK / IPA / H₂O₂) with efficacy-window + no-toxic-gas gates"
status: proposed
doc_type: adr
topic: yakushi-wave-2-disinfectant
authoritative: true
last_verified: 2026-06-17
authoritative_for:
  - 7 公定書 (日局/USP/EP) off-patent disinfectant/antiseptic actives across the FORMULATION (dilute/blend) manufacturing model
  - 1 new Pregel cell (formulation) + 1 new lexicon (com.etzhayyim.yakushi.formulationAttestation)
  - 1 new kotoba EAVT entity (:formulationAttestation/*)
  - 4 new constitutional gates G21..G24 (efficacy-window / no-toxic-gas / flammable-label / use-class)
  - clj-native (SSoT) implementation in 20-actors/yakushi/py/agent.clj + test_agent.clj (no Python counterpart — clj-as-SSoT direction)
depends_on:
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605250530-yakushi-sterile-fill-finish-and-container
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - 20-actors/yakushi/
  - 20-actors/yakushi/py/agent.clj
  - 20-actors/yakushi/cells/formulation_attestation.edn
  - 20-actors/yakushi/lex/formulationAttestation.edn
supersedes: []
superseded_by: []
---

# Context

ADR-2605250500/515/530/545/600/615 (Wave 1 / 1b / 1c) は yakushi 薬師 を OTC **医薬品** (eye drop + oral tablet + topical cream) の de-novo **synthesis** actor として確立した。User direction 2026-06-17 (current session): *「薬や消毒液などの医薬品などの製造 actor は設計されているか」*。

監査の結果: 医薬品 (薬) は yakushi で網羅されているが、**消毒液 (disinfectant / antiseptic) は roster 全体で未設計の gap** だった (`kiyome` は清掃工程の sanitization、`mizuho` は水処理の chlorination — どちらも消毒**剤の製造**ではない)。

消毒薬は yakushi の §2(e) anti-gatekeeping mission の **最も低リスク・最も公衆衛生価値の高い** category である:

- 7 actives すべて **公定書 (日局/USP/EP) monograph grade** + multi-generational safety record (ethanol 古来 / povidone-iodine 1955 / chlorhexidine 1954 / BAK 1935)。
- すべて **perpetually off-patent** — Wave 1 の G1 (PMDA/FDA/EMA all-3 off-patent) を自然に満たす。
- de-novo synthesis ではなく **FORMULATION (希釈・配合)** — proprietary 合成 route の IP リスクが原理的に存在しない。

ただし消毒薬には Wave 1 医薬品にない **固有の安全 / dual-use リスク**があり、新 gate を要する:

1. **濃度効力窓**: ethanol は <60% で殺菌力なし・>90% で蛋白変性前に flash 蒸発し効力低下。「濃ければ強い」は誤り。
2. **毒ガス生成 (dual-use / weaponizable)**: 次亜塩素酸ナトリウム + 酸 → 塩素ガス (Cl₂)、+ アンモニア → クロラミン。これは Charter §1.12 (兵器化可能性の表現不能化) / Rider §2(a) に直接抵触する。
3. **可燃性**: アルコール系は消防法上の危険物 — ラベルに火気厳禁が必須。
4. **用途クラス**: 環境表面用 vs 皮膚消毒用 vs 手指衛生 — 製造要件 (bioburden) が異なる。

# Decision

## Decision 1 — Wave 2 disinfectant reference set (7 公定書 off-patent actives)

| active (INN slug) | 和名 | 代表濃度 | use class |
|---|---|---|---|
| `ethanol` | 消毒用エタノール | 76.9–81.4 vol% | hand-hygiene / skin-antiseptic |
| `isopropanol` | イソプロパノール (IPA) | 70% | surface / hand-hygiene |
| `sodium-hypochlorite` | 次亜塩素酸ナトリウム | 0.05–0.1% (環境) | surface |
| `benzalkonium-chloride` | 塩化ベンザルコニウム (逆性石鹸) | 0.01–0.1% | skin-antiseptic / surface |
| `povidone-iodine` | ポビドンヨード | 10% | skin-antiseptic |
| `chlorhexidine-gluconate` | クロルヘキシジングルコン酸塩 | 0.05–0.5% | skin-antiseptic |
| `hydrogen-peroxide` | オキシドール (過酸化水素) | 2.5–3.5% | skin-antiseptic / surface |

INN slug は安定 — CAS / local code は不可 (Wave 1 の substrate-port rule 継承)。

## Decision 2 — FORMULATION manufacturing model (synthesis とは別)

Wave 2 の製造 verb は **synthesis ではなく formulation** (希釈・配合)。新 cell `formulation` + 新 lexicon `com.etzhayyim.yakushi.formulationAttestation` + 新 kotoba entity `:formulationAttestation/*` を追加。`record_synthesis` (de-novo) と `record_formulation` (dilute/blend) は別関数として共存する。

## Decision 3 — 4 new constitutional gates (G21..G24)

| gate | name | rule |
|---|---|---|
| **G21** | efficacy-window | active 濃度は evidence-based 効力窓内 (ethanol 60–90 / IPA 60–80 / NaOCl 0.05–0.5 / BAK 0.01–0.2 / PVP-I 1–10 / CHG 0.05–0.5 / H₂O₂ 1–6 %)。窓外は構造的に blocked |
| **G22** | no-toxic-gas-formulation | 次亜塩素酸 + 酸 (Cl₂) / + アンモニア (クロラミン) の配合は **表現不能** (§1.12 / Rider §2(a))。`record_formulation` が拒否 |
| **G23** | flammable-labeling | アルコール系 (ethanol / isopropanol) はラベルに火気厳禁 / flammable 必須 (G11 label lint の拡張) |
| **G24** | use-class | 各製品は {surface, skin-antiseptic, hand-hygiene} のいずれかを宣言 |

G1..G20 (Wave 1) はすべて継承し一切 weaken しない。G3 silen-pharma-review baseline + G4 QP co-sign + G9 witness N≥2 + G13/G18 no-server-key + G15 Murakumo-only + G16/G17 substrate/tithe は Wave 2 にもそのまま適用。

## Decision 4 — clj-native SSoT (Python counterpart なし)

進行中の clj-port wave (cljc = SSoT) と整合し、Wave 2 ロジックは `20-actors/yakushi/py/agent.clj` (babashka) + `test_agent.clj` に **clj-native** で実装。Wave 1 のような py→clj port ではなく、最初から clj が SSoT (Python counterpart を作らない)。+22 tests (計 48, 0 failure)。

# Consequences

- 消毒液製造の roster gap が閉じる。yakushi は「薬」+「消毒液」両方を網羅する第一級 pharmaceutical actor になる。
- G22 により、次亜塩素酸製品は毒ガス兵器化が原理的に不可能 (Charter §1.12 invariant の actor-level 実装例)。
- 全 cell は R0 で import-time RuntimeError gated のまま — Council Lv6+ ≥3 silen-pharma-review + QP-equivalent 登録までは実製造に進めない (master charter の phasing gate 不変)。
- products.edn に 3 SKU (消毒用エタノール / ポビドンヨード液 / 次亜塩素酸環境消毒) を追加 — okaimono Ring 1 へ供給 (`:representative` pricing)。

# Alternatives Considered

## A. 消毒液を別 actor (`shoudoku` 等) として分離
却下: 消毒薬は医薬品/医薬部外品であり、yakushi の QP / GMP / witness / tithe substrate を完全に再利用できる。別 actor は重複。

## B. 効力窓を gate にせず note に留める
却下: 「濃ければ強い」誤解は実害 (効かない消毒・アルコール中毒) を生む。G21 を構造的 block にすることで誤製造を表現不能化。

## C. 次亜塩素酸を scope 除外して毒ガスリスクを回避
却下: 次亜塩素酸は最重要の環境消毒剤。除外ではなく G22 (酸/アンモニア配合の表現不能化) で安全に内包するのが charter-aligned (route-around not prohibition)。

# References

- [ADR-2605250500](2605250500-yakushi-pharmaceutical-rd-charter.md) — master charter (G1..G14 + phasing)
- [ADR-2605192100](2605192100-etzhayyim-mission-charter.md) §1.12 — 兵器化可能性の表現不能化 (G22 の憲法根拠)
- [ADR-2605262130](2605262130-kotoba-storage-substrate-unification.md) — kotoba EAVT substrate
- WHO Guidelines on Hand Hygiene in Health Care (2009) — alcohol 60–80% efficacy window
- 日本薬局方 消毒用エタノール (76.9–81.4 vol%) / オキシドール / ポビドンヨード monographs
