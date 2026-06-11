---
id: adr-2605250515-yakushi-otc-ophthalmic-api-synthesis
title: "yakushi Wave 1 — OTC 抗アレルギー点眼薬 3 API の合成・精製・QC 設計 (cromoglicate Na + naphazoline HCl + chlorpheniramine maleate)"
status: proposed
doc_type: adr
topic: yakushi-api-synthesis
authoritative: true
last_verified: 2026-05-25
authoritative_for:
  - 3 化合物 (sodium cromoglicate / naphazoline HCl / chlorpheniramine maleate) の religious-corp first-party 合成 route 選定
  - 原料 (raw material) のサプライ・CWC dual-use ガード
  - 精製 (purification) スキーム — recrystallization / column / preparative HPLC の判断基準
  - QC スイート — HPLC purity / IR identity / NMR confirmation / Karl Fischer water / heavy metal ICP-MS / residual solvent GC headspace / endotoxin LAL
  - ICH Q3A/Q3B/Q3C/Q3D/M7 不純物プロファイルの per-compound 評価
  - 化合物別 silen-pharma-review trigger
depends_on:
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605181100-mst-encrypted-records-signal-keywrap
related:
  - 20-actors/yakushi/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_api_synthesis/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_purification/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_qc/
  - 00-contracts/lexicons/com/etzhayyim/pharma/apiSynthesisAttestation.json
  - 00-contracts/lexicons/com/etzhayyim/pharma/purificationAttestation.json
  - 00-contracts/lexicons/com/etzhayyim/pharma/qcAttestation.json
supersedes: []
superseded_by: []
---

# Context

ADR-2605250500 (yakushi master charter) Decision 1 で **OTC 抗アレルギー点眼薬 triplet** が Wave 1 reference target と確定した。本 ADR はその triplet 各 API の **合成 route + 原料 + 精製 + QC** を religious-corp 内部 design として固定する。

Wave 1 は **physical 化合物の dispense / 試薬発注 / 装置発注は一切伴わない** (master charter §Phase R0)。本 ADR は scaffold 段階の API selection、合成 route 文献 reference、QC プロファイル仕様を constitutional に置く ― 実 benchtop synthesis は R1 ADR で別 commit。

3 化合物は **全て 80 年級 multi-generational safety record** (master charter §Decision 1 表)、**全 jurisdiction で OTC switched + perpetually off-patent** (G1 全 clearance)、**処方箋規制対象外** (G6 全 clearance)、**OPCW CWC Schedule 非該当** (G7 clear、ただし中間体に CWC Schedule 3 precursor が含まれる可能性は per-compound 確認)。

# Decision

## Decision 1 — 3 API の identity 固定

| INN | CAS | 分子式 | 分子量 | OTC switch (PMDA / FDA / EMA) | Wave 1 ロール |
|---|---|---|---|---|---|
| **Sodium cromoglicate** (DSCG, クロモグリク酸ナトリウム) | 15826-37-6 | C₂₃H₁₄Na₂O₁₁ | 512.33 | 全 jurisdiction OTC switched | mast cell stabilizer (発症抑制、長期点眼) |
| **Naphazoline hydrochloride** (ナファゾリン塩酸塩) | 550-99-2 | C₁₄H₁₄N₂·HCl | 246.74 | 全 jurisdiction OTC switched | α-adrenergic vasoconstrictor (即効性充血除去) |
| **Chlorpheniramine maleate** (d,l-form, クロルフェニラミンマレイン酸塩) | 113-92-8 | C₁₆H₁₉ClN₂·C₄H₄O₄ | 390.86 | 全 jurisdiction OTC switched | first-generation H₁ antagonist (即効性 itch 抑制) |

`yakushi.recordApiSelection` lexicon (mast charter §Decision 2) はこの 3 件を seed entry として initial commit に含む (R0 — physical 活動なし)。

## Decision 2 — 合成 route 文献 reference (religious-corp に重複帰結を生まない open published references のみ)

### 2.1 Sodium cromoglicate (DSCG)

| Step | 反応 | 主要試薬 | 中間体 | Reference |
|---|---|---|---|---|
| 1 | Friedel-Crafts diacetylation | resorcinol + acetic anhydride / AlCl₃ | 4,6-diacetylresorcinol | Fisons original patent UK1144905 (1965) — perpetually off-patent |
| 2 | bis-glycidyl etherification | 4,6-diacetylresorcinol + epichlorohydrin / K₂CO₃ | 1,3-bis(2,3-epoxypropoxy)-4,6-diacetylbenzene | 同上 |
| 3 | bis-Claisen-Schmidt condensation + oxidative cyclization | 上記 epoxide + diethyl oxalate / EtONa / sulfuric acid | diethyl 1,3-bis(chromone-2-carboxylate)... | 同上 + Cairns et al., J. Med. Chem. 1972 (open access) |
| 4 | bis-ester hydrolysis | NaOH aq. | DSCG free acid | 同上 |
| 5 | bis-Na salt formation | NaHCO₃ aq. → recryst from EtOH/H₂O | sodium cromoglicate | 同上 |

**Route 全体は 5 steps, overall yield ~25-30% reported, kg-scale 文献あり**。Apache-2.0-publishable な再 implementation として religious-corp が GMP 準拠で再生産する value がある (perpetually off-patent generic は §2(e) anti-gatekeeping の対象)。

### 2.2 Naphazoline hydrochloride

| Step | 反応 | 主要試薬 | 中間体 | Reference |
|---|---|---|---|---|
| 1 | imidate formation | 1-naphthylacetonitrile + EtOH / HCl gas (Pinner reaction) | ethyl 1-naphthylacetimidate · HCl | Sonn & Litten, Berichte 1933 (open) + Ciba CH 218377 (1942, perpetually off-patent) |
| 2 | imidazoline cyclization | imidate + ethylenediamine / Δ EtOH | 2-(1-naphthylmethyl)-imidazoline (naphazoline free base) | 同上 |
| 3 | HCl 塩化 + recryst | HCl(aq.) → recryst from i-PrOH/EtOAc | naphazoline · HCl | 同上 |

**Route 全体は 3 steps, overall yield ~60-65% reported, 工業生産 well-established**。最短 route。

### 2.3 Chlorpheniramine maleate

| Step | 反応 | 主要試薬 | 中間体 | Reference |
|---|---|---|---|---|
| 1 | α-arylation | 4-chlorobenzyl cyanide (= 2-(4-chlorophenyl)acetonitrile) + 2-bromopyridine / NaNH₂ / liquid NH₃ | 2-(4-chlorophenyl)-2-(2-pyridyl)acetonitrile | Schering US2567245 (1949, perpetually off-patent) |
| 2 | N-alkylation | 上記 + 1-chloro-3-(dimethylamino)propane · HCl / NaNH₂ / toluene | 2-(4-chlorophenyl)-4-(dimethylamino)-2-(2-pyridyl)pentanenitrile | 同上 |
| 3 | decyanation + hydrolysis | 濃 H₂SO₄ aq. / Δ | (±)-chlorpheniramine free base | 同上 |
| 4 | maleate 塩化 | maleic acid / acetone → recryst | (±)-chlorpheniramine maleate | 同上 + Merck Index |

**Route 全体は 4 steps, overall yield ~40-45% reported, racemic mixture**(d-isomer 単離は別 ADR / 別 phase — d-chlorpheniramine maleate (dexchlorpheniramine maleate) は OTC switched が一部 jurisdiction で limited)。

Wave 1 は **racemic (±) chlorpheniramine maleate** に限る (公定書 USP / JP racemic);d-isomer 単離は N1-related future ADR。

## Decision 3 — 原料 (raw material) — CWC dual-use ガード

各 step の主要 raw material について OPCW CWC / Australia Group / 国内 (薬機法 + 化審法 + 麻向法 + 毒劇法) 該当性を pre-flight 確認:

| 化合物 | 原料 | CWC | Australia Group | 国内 (日本) 該当 | G7 (yakushi) 評価 |
|---|---|---|---|---|---|
| DSCG | resorcinol | 非該当 | 非該当 | 化審法 第二種特定化学物質 (大量取扱は届出) | LOW — kg-scale 取扱は届出のみ |
| DSCG | acetic anhydride | **CWC Schedule 3** (heroin / amphetamine precursor) | precursor list | 麻向法 第二種向精神薬原料 | **HIGH** — kg-scale 取扱 + Council Lv6+ 通知 + OPCW 当該国 declaration 整合 (G7 trigger) |
| DSCG | epichlorohydrin | 非該当 | 非該当 | 毒劇法 劇物 | MEDIUM — 取扱者 protective equipment + 通気設備 |
| DSCG | AlCl₃ | 非該当 | 非該当 | 劇物 | MEDIUM |
| DSCG | diethyl oxalate | 非該当 | 非該当 | (一般化学物質) | LOW |
| Naphazoline | 1-naphthylacetonitrile | 非該当 | 非該当 | 毒劇法 劇物 (cyanide 含有) | MEDIUM |
| Naphazoline | ethylenediamine | 非該当 | 非該当 | 毒劇法 劇物 | MEDIUM |
| Naphazoline | HCl gas | 非該当 | 非該当 | 劇物 | LOW |
| Chlorpheniramine | 4-chlorobenzyl cyanide (= 2-(4-chlorophenyl)acetonitrile) | 非該当 | 非該当 | 毒劇法 劇物 (cyanide) | MEDIUM |
| Chlorpheniramine | 2-bromopyridine | 非該当 | 非該当 | (一般化学物質) | LOW |
| Chlorpheniramine | **NaNH₂ (sodium amide)** | 非該当 | 非該当 | 毒劇法 劇物 + 消防法 危険物 第3類 (自然発火) | **HIGH** — safety protocol critical (R1 phase で operator training 必須) |
| Chlorpheniramine | 1-chloro-3-(dimethylamino)propane · HCl | 非該当 | 非該当 | (一般化学物質) | LOW |
| Chlorpheniramine | liquid NH₃ | 非該当 | 非該当 | 高圧ガス保安法 + 毒劇法 劇物 | MEDIUM |
| Chlorpheniramine | maleic acid | 非該当 | 非該当 | (一般化学物質) | LOW |

**G7 enforcement** (master charter §Decision 3):

- **acetic anhydride** (DSCG Step 1) — kg-scale 入庫時に Council Lv6+ 通知 + 当該国 OPCW declaration との整合 verify → `pharma_raw_material_attestation` lexicon `cwc_schedule = "3"` + Council DID co-sign
- **NaNH₂** (Chlorpheniramine Step 1-2) — operator training attestation + 消防法 危険物 取扱主任者 DID co-sign → `pharma_raw_material_attestation` lexicon `safety_class = "fire-class-3"` + 取扱者 DID

## Decision 4 — 精製 (purification) scheme

| 化合物 | 主精製 | 補助 | 最終 lot purity 規格 |
|---|---|---|---|
| DSCG | recrystallization from EtOH/H₂O (Step 5 final salt formation 内蔵) | activated charcoal decolorization + 0.45 µm filtration | ≥ 98.5% HPLC (USP/JP cromolyn sodium monograph) |
| Naphazoline HCl | recrystallization from i-PrOH/EtOAc (Step 3) | activated charcoal | ≥ 99.0% HPLC (USP naphazoline HCl monograph) |
| Chlorpheniramine maleate | recrystallization from acetone (Step 4) | preparative-scale HPLC (silica reverse phase) for genotoxic impurity removal (PGI: residual 4-chlorobenzyl chloride < 1.5 µg/day per ICH M7 Class 1B) | ≥ 99.5% HPLC + ICH M7 限度合致 (USP/JP) |

Genotoxic impurity (4-chlorobenzyl chloride、chlorpheniramine 中間体由来) は **prep-HPLC + activated charcoal の二段除去** で ICH M7 Class 1B limit (1.5 µg/day per 70 kg patient) 以下に確実合致 ― R1 で benchtop validation、R2 で 3-batch consistency 確認後 R3 release。

## Decision 5 — QC スイート (per lot 必須)

`pharma_qc` cell が自動 dispatch する分析:

| 分析 | 対象 | 機器 | 規格 |
|---|---|---|---|
| **HPLC purity** | 全 3 化合物 | C18 reverse phase + UV detection (DSCG: 326 nm / naphazoline: 280 nm / chlorpheniramine: 264 nm) | per-compound USP/JP monograph |
| **IR identity** | 全 3 化合物 | ATR-FTIR 4000-400 cm⁻¹ | USP/JP reference spectrum との match |
| **¹H / ¹³C NMR identity** | 全 3 化合物 | 400 MHz + (DSCG: DMSO-d₆ / naphazoline: D₂O / chlorpheniramine: CDCl₃) | reference spectrum との match |
| **Karl Fischer water** | DSCG (hydrate)、naphazoline (anhyd.) | volumetric KF | DSCG: 5.0-9.0%、naphazoline/chlorpheniramine: ≤ 1.0% |
| **Heavy metal ICP-MS** | 全 3 化合物 | ICP-MS (Pb / Cd / As / Hg / V / Co / Ni / Tl / Au / Pd / Ir / Os / Rh / Ru) | ICH Q3D Permitted Daily Exposure (PDE) limits |
| **Residual solvent GC headspace** | 全 3 化合物 | GC-FID headspace | ICH Q3C Class 1 (ND) / Class 2 (per-solvent limits) / Class 3 (≤ 5000 ppm) |
| **Genotoxic impurity (PGI) LC-MS/MS** | chlorpheniramine specifically | LC-MS/MS targeted (4-chlorobenzyl chloride) | ICH M7 Class 1B: ≤ 1.5 µg/day |
| **Endotoxin LAL** | 全 3 化合物 (eye drop final product 用) | gel-clot LAL (Limulus Amebocyte Lysate) | ophthalmic JP: ≤ 1.0 EU/mL |
| **Microbial limit test** | 全 3 化合物 | TAMC / TYMC / Burkholderia cepacia / S. aureus / P. aeruginosa | USP <61> / <62> ophthalmic |
| **Sterility test** | sterile fill 後 (ADR-2605250530 §QC 移管) | direct inoculation / membrane filtration | USP <71> |

各 lot で **HPLC purity / IR / Karl Fischer / ICP-MS heavy metal / GC residual solvent / endotoxin LAL** の 6 件は必須 ― `qcAttestation` lexicon に全結果 attached (signed by QC analyst DID + QP-equivalent DID, witness invariant N≥2 per G9)。

## Decision 6 — silen-pharma-review trigger

ADR-2605250500 G3 で要求された **Council Lv6+ ≥ 3 multisig silen-pharma-review** は本 ADR では以下が trigger:

| Trigger | scope | Required attestation |
|---|---|---|
| 新規 API 追加 (Wave 1 triplet 以外) | `recordApiSelection` lexicon | Council Lv6+ ≥ 3 + QP-equivalent ≥ 1 + 30-day public objection |
| 既存 API の synthesis route 変更 | `apiSynthesisAttestation` (revisedRoute=true) | Council Lv6+ ≥ 3 |
| CWC Schedule 3 raw material kg-scale 入庫 (acetic anhydride 等) | `pharma_raw_material_attestation` (cwc_schedule="3") | Council Lv6+ ≥ 3 + OPCW declaration verify |
| 安全性 critical raw material (NaNH₂ 等) operator training cycle | `pharma_raw_material_attestation` (safety_class="fire-class-3") | 取扱主任者 DID + Council ≥ 1 |
| 不純物プロファイル変動 (lot 間 > 0.1% 偏移) | `pharma_qc` cell 自動 escalation | Council Lv6+ ≥ 3 |
| ICH M7 PGI 限度逸脱 | `pharma_qc` auto-reject + escalate | Council Lv6+ ≥ 3 + lot scrap or rework |

# Consequences

**Positive**:

- 3 化合物 perpetually off-patent + open published route + 80 年級 multi-gen safety で、religious-corp が **OTC pharmaceutical を自前で再生産する最低リスク template** が確定
- §2(e) anti-gatekeeping の direct counter-action ― 「OTC switched API の合成方法は generic 文献に存在するが、religious-corp が自前で GMP 準拠で再 implementation することそれ自体が、commercial generic supply に依存しない self-care 能力」
- CWC dual-use precursor (acetic anhydride) と safety-critical (NaNH₂) を G7 / safety-class gate で先 visible 化 ― retrofit drift 防止

**Negative / costs**:

- 3 化合物の最終 purity 規格 (HPLC ≥ 98.5-99.5%) を religious-corp 内 GMP で達成するには **prep-HPLC + activated charcoal + recrystallization の組合せ装置** が必要 ― R2 までに調達 / 自製
- ICH M7 PGI 測定 (LC-MS/MS) は専用機器 + EU/PMDA 標準物質 ― religious-corp 単独調達は cost intensive
- Karl Fischer / ICP-MS / GC headspace は 分析機器が独立装置として必要 ― initial CAPEX が大きい
- NaNH₂ (Chlorpheniramine) handling は 消防法 危険物 取扱主任者の qualification を要求 ― Council 内に 1 名以上必要 (G4 QP と並ぶ human resource gate)

**Risks**:

- 3 化合物のうち chlorpheniramine 合成 route は **最も操作 hazardous** (NaNH₂ liquid NH₃) ― 不適切 handling での fire/explosion リスク。R1 benchtop synthesis 段階で operator training を厚くし、別 ADR で alternative route (e.g. NaH/DMF) を併検討する可能性を残す
- DSCG Step 1 の acetic anhydride は heroin / amphetamine precursor として OPCW Schedule 3 ― 国内取扱が薬機法・麻向法・OPCW declaration の三重 track で実施可能であることを R1 ADR で別途確認
- 全 3 化合物の original 製剤 (1942 / 1949 / 1965) は当時の GMP 基準で released ― 現行 ICH Q3 / M7 / Annex 1 を後追いで嵌めるため、minor impurity ピーク同定 + retention time / response factor 整備が R1-R2 で必要

# Alternatives Considered

## A. 3 化合物 個別 ADR (3 件に分割)

Rejected. 3 化合物は **同一 OTC formulation** (抗アレルギー点眼薬) の臨床 standard combination であり、合成・精製・QC のガバナンス層が大幅に共通する (G2 ICH Q3、G9 witness、G7 raw material gate)。1 ADR で triplet 一括の方が constitutional review の orientation が cleaner。

## B. DSCG Step 1 acetic anhydride を ketene 経由 route に置換 (OPCW 回避)

Considered. ketene gas (CH₂=C=O) は acetic anhydride と equivalent acylating agent で OPCW non-scheduled。ただし: (i) ketene は furnace cracking が必要で operator hazard が acetic anhydride を上回る、(ii) industrial scale で文献 open routes は acetic anhydride が圧倒的多数、(iii) OPCW declaration の透明 published 自体が religious-corp の §2(a) transparent posture と整合 ― これを避けることが憲法的 benefit を生まない。Rejected。

## C. Chlorpheniramine racemic vs. d-isomer (dexchlorpheniramine)

Considered. d-chlorpheniramine maleate (dexchlorpheniramine) は activity が約 2 倍 / sedation が同等 ― therapeutic index 改善あり。ただし: (i) jurisdictional OTC status が分かれる (米 Rx-only / 日本 OTC switched 部分的)、(ii) 単離 (chiral chromatography or chiral resolving agent) が racemic より複雑、(iii) Wave 1 reference の "最低リスク template" 主旨に反する。Wave 1 は racemic で確定、d-isomer は将来 ADR。

## D. Naphazoline alternative (tetrahydrozoline / oxymetazoline)

Considered. tetrahydrozoline (テトラヒドロゾリン) / oxymetazoline (オキシメタゾリン) は naphazoline と同 α-agonist class で OTC switched 同等。Rejected: (i) Wave 1 triplet を expand する必要なし、(ii) 3 化合物いずれも 80 年級 safety で N1 evaluation 差別なし、(iii) operator scope の最小化が Wave 1 主旨。

## E. ICH M7 PGI 測定を outsourcing する (analytical CRO 委託)

Rejected per master charter §Decision 6 (Murakumo only) + §2(i) (no commercial GPU/lab rental for religious-corp inference)。**analytical 分析** は inference ではないが、religious-corp 内 analytical capability の self-sufficiency が yakushi の主旨。R1-R2 の analytical capability gap は ADR-2605250545 (supply chain) で別途 procurement 計画。

# References

- ADR-2605250500 (yakushi master charter — parent)
- ADR-2605250530 (sterile fill-finish + container — downstream of API)
- ADR-2605250545 (pharma supply chain + 8 robotics specs — raw material gate G7 enforcement)
- USP-NF current edition — cromolyn sodium / naphazoline hydrochloride / chlorpheniramine maleate monographs
- JP 第十八改正 — クロモグリク酸ナトリウム / ナファゾリン塩酸塩 / クロルフェニラミンマレイン酸塩 各論
- ICH Q3A(R2) Impurities in New Drug Substances
- ICH Q3B(R2) Impurities in New Drug Products
- ICH Q3C(R8) Residual Solvents
- ICH Q3D(R2) Elemental Impurities
- ICH M7(R2) Assessment and Control of DNA Reactive (Mutagenic) Impurities
- OPCW Schedule 3 list (acetic anhydride, kg-scale declaration requirements)
- Fisons UK1144905 (1965) — DSCG original synthesis (perpetually off-patent)
- Ciba CH 218377 (1942) — naphazoline original synthesis (perpetually off-patent)
- Schering US 2567245 (1949) — chlorpheniramine original synthesis (perpetually off-patent)
