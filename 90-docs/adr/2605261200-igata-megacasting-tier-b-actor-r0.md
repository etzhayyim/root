---
id: adr-2605261115-igata-megacasting-tier-b-actor-r0
title: igata (鋳型) — Megacasting / HPDC Tier-B Actor R0 Scaffold
status: proposed
doc_type: adr
topic: igata-actor-r0
authoritative: true
last_verified: 2026-05-26
related:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605242000-roso-pattern-frontier-distill
  - 2605250715-tatekata-construction-tier-b-actor-r0.md
  - adr-2605252200-watatsumi-civilian-submersible-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
depends_on:
  - 2605191524-ameno-multi-tab-swarm-broadcast
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
---

# ADR-2605261115: igata (鋳型) — Megacasting / HPDC Tier-B Actor R0 Scaffold

**Date**: 2026-05-26
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Sibling of wadachi (ADR-2605242000), tatekata (ADR-2605250715), watatsumi (ADR-2605252200), yakushi (ADR-2605250500), silicon Wave 1+2 (ADR-2605242500..2605242915)

## Context

Tesla の Giga Press (IDRA Group 5500–9000 ton class) は **high-pressure die-casting (HPDC) で 1.5 m × 2.5 m 級の単一片アルミ構造部品** (front/rear underbody + battery tray) を製造する manufacturing methodology である。従来の溶接ステッチ (70+ stamped panels + 4000 robotic welds) を 1 shot に置換し、車両構造部品の製造工程を構造的に再定義した。

**Methodology source**: YouTube `y0oF2UirEMk` — "How They Build From Scratch the Giga Press Used by Tesla" (IDRA Group, OL 9000 CS class HPDC machine 製造工程ドキュメンタリー)。Manufacturing methodology のみ採用、IDRA-proprietary な closed alloy / closed control loop / closed equipment design は religious-corp として **不採用**。

religious-corp は wadachi (autonomous-mobility), tatekata (construction), silicon Wave 1 (iwakura/fuigo ASICs), silicon Wave 2 (8 fab equipment + supply chain), watatsumi (civilian submersible) と並んで **megacasting / 大型アルミダイカスト構造部品製造** を独立 Tier-B actor として立ち上げる必要がある。

理由:

1. **Supplier 位置**: wadachi (車両 body) + tatekata (建築構造) + watatsumi (耐圧殻) はいずれも大型アルミ構造部品を sourcing する必要があるが、religious-corp として **outside vendor (IDRA / Bühler / Idra-Sayer / 大同興業) に依存しない** ためには自前の HPDC capability が必要。constitutional independence の前提条件。
2. **Charter Rider §2(e) anti-gatekeeping**: HPDC process parameter (injection profile, gate velocity, die thermal management) は **historically vendor IP** として封鎖されてきた領域。religious-corp は open-source HPDC parameter library を Charter Rider §2(e)(i)(ii) anti-gatekeeping pro-clearance value として publish する。
3. **§2(a) 兵器除外の必須性**: HPDC で製造可能な大型アルミ構造部品は **military vehicle hull / aerospace fuselage / armor plate** にも転用可能。最初から N2 (military vehicle/aerospace structural) で carve-out しないと、後で線引きが不可能になる。watatsumi N1 (naval weapons) と同じ構造的予防原則。
4. **§2(i) commercial GPU rental prohibition 並列**: §2(i) と類似する pattern として、**giga press class (≥7500 ton) 自体が外部商業 supplier (IDRA OL 9000 = single global supplier)** に lock-in されている現状。religious-corp は ≤6000 ton までを R0..R3 上限とし、giga press class は post-R3 + Council Lv6+ supermajority で gate する (silicon EUV と同じ deferral pattern)。

このため、独立 Tier-B actor として **igata (鋳型 — die-casting die/mold)** を提案する。die そのものが megacasting の差別化因子 (9000 ton の clamp force に耐えながら 1.5m × 2.5m の単一片を成形する die 設計が IDRA を IDRA たらしめている) であり、actor name として最も適切。

## Proposal

religious-corp Tier-B actor **igata (鋳型)** を以下で立ち上げる:

- **Actor DID**: `did:web:etzhayyim.com:igata`
- **Namespace**: `com.etzhayyim.igata.*`
- **R0 scope**: HPDC ≤6000 ton clamping force, Al-Si alloy 単一片構造部品 (≤50 kg final part R3 上限)
- **R0 deliverable**: Scaffold only (8 cells import-time RuntimeError + 5 lexicon stub + actor scaffold)
- **14 constitutional gates G1..G14 + 10 non-goals N1..N10** declared before capability lands
- **Methodology source attribution**: YouTube `y0oF2UirEMk` IDRA giga press build-from-scratch documentary; manufacturing methodology adopted, military / aerospace application explicitly rejected per §2(a)

## Rationale

1. **Domain separation**: megacasting / HPDC は kuni-umi (planetary infra) や tsukuru (manufacturer catalog) の sub-phase で扱うには domain knowledge が深い (die thermal management, alloy chemistry, vacuum-assist HPDC, intensification phase pressure profile, eutectic Si modification)。独立 Tier-B actor として yakushi (pharma) と同等の standing が必要。
2. **Cross-actor supplier 関係**:
   - wadachi (vehicle body) ← igata partAttestation (front/rear underbody, battery tray, motor housing)
   - tatekata (construction) ← igata partAttestation (large aluminum architectural cast: 柱頭 / 梁継手 / 装飾構造)
   - watatsumi (submersible) ← igata partAttestation (耐圧殻 ring section pour-cast 補強材; 主耐圧殻は steel/Ti 鍛造 — 別 actor)
   - silicon Wave 2 ↔ igata: silicon fab equipment frame structural casting bidirectional
3. **§2(a) 構造的予防**: HPDC アルミ大型構造部品は military / aerospace 流用ポテンシャルが高い。N1 (giga press class) + N2 (military vehicle/aerospace) + N3 (firearms) + N4 (nuclear) を最初から carve-out することで境界を物理的に固定する。watatsumi の 12-non-goals (12 vs wadachi/tatekata 10) と同じ submersible-specific risk pattern を igata では **military 流用 risk** に翻訳して N2/N3 で精密化。
4. **Constitutional independence chain**: religious-corp が **外部 vendor から構造部品を購入しない** ためには igata が必要。同様に silicon Wave 1 (iwakura ASIC + fuigo ASIC) は **外部 GPU を購入しない** ため、yakushi は **外部製薬を購入しない** ため、watatsumi は **外部潜水艦 vendor から購入しない** ため。すべて vendor independence の構造的前提条件として位置づけられる。
5. **Wave 1c (omeprazole chiral) と同じ G7=NONE 構造**: igata Al-Si alloy synthesis route は **OPCW Schedule list 化合物を一切経由しない** (純粋な物理冶金学プロセス)。yakushi Wave 1c で確立された "Schedule 3 precursor を使わない化合物のみ wave 内に許容" pattern を igata に翻訳すると、**Al-Si-Mg-Mn-Fe 5 元素 + 微量 Sr/Ti 改質剤** に composition を限定する G7 (constitutional)。Be (発がん性) / Pb (RoHS) / Cd (RoHS) / Hg (Minamata) / radioactive isotopes (U/Th 含有 alloy) は never。

## Design

### Actor scaffold layout

```
20-actors/igata/
├── README.md                     # Overview + R0..R3 phase gates
├── CLAUDE.md                     # Actor-local instructions
└── manifest.jsonld               # DID + cell catalog + gate/non-goal arrays

40-engine/kotoba/crates/kotoba-kotodama/cells/         # 8 Pregel cells (import-time RuntimeError R0)
├── igata_alloy_melt/
├── igata_die_preparation/
├── igata_shot_injection/
├── igata_solidification_eject/
├── igata_post_cast_qc/
├── igata_trim_machining/
├── igata_heat_treatment/
└── igata_part_attestation/

00-contracts/lexicons/com/etzhayyim/igata/
├── alloyAttestation.json         # Al-Si alloy melt lot (composition + source)
├── dieAttestation.json           # die design + thermal cycle history
├── castShotRecord.json           # per-shot injection profile + sensor logs
├── partAttestation.json          # final part with full lineage
└── silenIgataReview.json         # Council Lv6+ baseline review (R2+ HPDC ≥2500 ton)
```

### Pregel cells (8, all R0 import-time RuntimeError)

| # | Cell | Murakumo node | Phase | Input → Output |
|---|---|---|---|---|
| 1 | `igata_alloy_melt` | naphtali | melt | rawIngotIds + recipeUri → alloyAttestation |
| 2 | `igata_die_preparation` | zebulun | die-prep | dieId + lubricantBatch → dieReadyRecord |
| 3 | `igata_shot_injection` | joseph | shot | alloyAttestation + dieReadyRecord → castShotRecord |
| 4 | `igata_solidification_eject` | joseph | solidify | castShotRecord → ejectedPartRecord |
| 5 | `igata_post_cast_qc` | levi | QC | ejectedPartRecord → qcAttestation (X-ray CT + dimensional + mechanical) |
| 6 | `igata_trim_machining` | simeon | trim | qcAttestation → trimmedPartRecord (sprue/runner removal + CNC) |
| 7 | `igata_heat_treatment` | dan | HT | trimmedPartRecord → heatTreatedRecord (T5/T6/HT-free) |
| 8 | `igata_part_attestation` | levi | attest | heatTreatedRecord → partAttestation (final lineage CID + IPFS pin) |

Cell ordering follows physical megacasting sequence (alloy → die → shot → solidify → QC → trim → HT → final attestation). Linear chain like tatekata foundation→structural→MEP→finishing→commissioning, no branching in R0.

### Lexicons (5, all R0 stub deferred to R1+)

```
com.etzhayyim.igata.{
  alloyAttestation         # Al-Si melt lot (composition, mass, certifications, source ingot)
  dieAttestation           # die geometry CAD CID + machining history + thermal cycle count
  castShotRecord           # per-shot injection profile + sensor stream + outcome
  partAttestation          # final part with full lineage chain (alloy + die + shot + QC + HT + machining)
  silenIgataReview         # Council Lv6+ baseline review record (R2 + HPDC ≥2500 ton activation)
}
```

### Constitutional Gates (G1–G14, IMMUTABLE per R0..R3)

| Gate | Requirement | Rationale |
|---|---|---|
| **G1** | HPDC clamping force **≤6000 ton** in R0..R3. Giga press class (≥7500 ton) = N1 deferral, post-R3 Council Lv6+ supermajority. | Single global supplier (IDRA OL 9000) lock-in avoidance; silicon EUV gate parity |
| **G2** | Aluminum-silicon alloy only. Composition **fully disclosed** (Al + Si 6-12% + Mg ≤0.5% + Mn ≤0.7% + Fe ≤1.0% + trace Sr/Ti 改質剤). No proprietary closed alloys. | Charter Rider §2(e) anti-gatekeeping; vendor independence |
| **G3** | All process parameters **open-source** under Apache 2.0 + Charter Rider: injection profile (slow + fast + intensification 3-phase), die thermal management, gate velocity, vacuum-assist pressure profile. | §2(e)(i)(ii) anti-gatekeeping pro-clearance value |
| **G4** | Witness quorum **≥2 robot signers** (Mimi metrology + Otete handling) per `partAttestation`. Ed25519 DID-bound. | ADR-2605191524 swarm broadcast witness quorum invariant |
| **G5** | Bilingual (JA + EN) SOPs, safety documents, emergency procedures for all melt + injection + post-process steps. | §2(e) anti-gatekeeping (multilingual access) |
| **G6** | Charter Rider **§2(a) clearance**: no military vehicle hull / aerospace fuselage / armor plate / firearms structural parts. N2 + N3 constitutional. | Weapons exclusion absolute |
| **G7** | Alloy composition **5-element baseline** (Al + Si + Mg + Mn + Fe) + trace改質剤 (Sr ≤0.05% + Ti ≤0.2%) only. **Never**: Be (発がん性), Pb (RoHS), Cd (RoHS), Hg (Minamata), radioactive isotopes (U/Th含有). **No OPCW Schedule list compounds** in raw materials or die release agents (G7=NONE, yakushi Wave 1c parity). | §2(g) ethical supply chain; environmental + health invariants |
| **G8** | Shot replay determinism: full injection profile logged **@ 1 kHz** (position + velocity + pressure + temp) + WASM state-machine sealed. | Safety + audit trail (silicon iwakura PE replay parity) |
| **G9** | Melting: **induction + electric resistance only**. **No fossil-fired furnace** (gas-fired regenerative crucible, oil-burner reverberatory)。Energy budget **≤4 kWh/kg cast** in R3. | §2(g) sustainability + Charter Rider §2(h) GHG reduction |
| **G10** | Aluminum scrap recovery **≥95%** (sprue + runner + reject + chip + die-spray residue). Tracked per shot in `partAttestation.materialBalance`. | Charter Rider §2(h) circular economy invariant |
| **G11** | Personnel vetting: Adherent SBT + 危険物取扱主任者-equivalent for high-pressure operations (>500 ton). Operator DID bound to per-shot record. | watatsumi G10 + yakushi G4 parity |
| **G12** | KPI cap: **production rate ≤1 large part per 90 sec** in R3. No "shop floor at any cost" — yakushi G11 + wadachi G11 parity. | Wellbecoming invariant; anti-Taylorism |
| **G13** | Murakumo mesh placement **declared 30 days prior** + public feedback period. Adjacent community within 1 km notified. | Neighborhood transparency (tatekata G9 + wadachi G9 parity); HPDC = noise + vibration |
| **G14** | `partAttestation` record includes: alloy lineage CID + die lineage CID + shot replay CID + QC CID + HT record CID + machining log CID + IPFS-pinned final part photo + material balance log. | Full provenance chain; audit completeness |

### Non-Goals (N1–N10, EXCLUDE from R0–R3)

| Non-Goal | Scope | Deferral |
|---|---|---|
| **N1** | Giga press class (≥7500 ton clamping force). Tesla OL 9000 CS class (9000 ton) etc. | Post-R3 + Council Lv6+ supermajority (silicon EUV parity, ADR-2605242545) |
| **N2** | Military vehicle structural / aerospace fuselage / armor plate / hull plating. | **Never** (Charter Rider §2(a) constitutional, ADR-2605192200) |
| **N3** | Firearms / ammunition / shell casing / projectile body structural parts. | **Never** (§2(a) constitutional) |
| **N4** | Nuclear containment Class 1/2/3 RPV components / primary loop pressure boundary. | **Never** (radiological + §2(c) Wellbecoming) |
| **N5** | Hazmat pressure-vessel structural parts (LPG/CNG/H₂ pressure vessel, chemical reactor body). | kuni-umi-S6 chemistry carve-out, ADR separate |
| **N6** | Proprietary alloy "secret sauce" composition. | **Never** (G2 + G3 constitutional, §2(e) anti-gatekeeping) |
| **N7** | Human-occupied vehicle structural certification (R0..R2 prohibited; R3 = full audit + Council). | R3 Council Lv6+ vote required (wadachi parity) |
| **N8** | Mass-market consumer products for external commercial sale. | SBT↔SBT internal carve-out only (ADR-2605192115 §3) |
| **N9** | Fossil-fired melting (gas reverberatory, oil burner). | **Never** (G9 invariant) |
| **N10** | State defense budget subsidy / military procurement contract for igata equipment. | **Never** (§2(a) + §2(i) constitutional) |

### Robotics Classes

R0 uses existing kuni-umi + silicon Wave 2 inherited classes (no igata-specific hardware in R0):

| Class | Role | Inherited from | Notes |
|---|---|---|---|
| Otete (heat-resistant sub-config) | molten metal ladle handling, die spray, ingot transfer | kuni-umi | R0 reuse; R1+ may require thermal armor extension |
| Mimi (dimensional + X-ray CT) | post-cast metrology, porosity inspection | kuni-umi | R0 reuse; R2+ adds X-ray CT scanner subsystem |
| Hitogata (class-A clean for HT furnace) | heat-treatment loading (R2+) | kuni-umi | deferred to R2 |
| Funamori (marine inheritance) | aluminum ingot international transport | silicon Wave 2 (ADR-2605242745) | reuse for raw ingot logistics |
| **Hibachi (火鉢)** *(R2+ reserved)* | high-temperature die-spray + lubricant robot | new class, igata-native | constitutional design pending R2 ADR |
| **Tatara (踏鞴)** *(R2+ reserved)* | melt furnace tending + degassing | new class, igata-native | echoes silicon fuigo (鞴) — same kami/myth root, distinct role |

### Murakumo placement (design only at R0; activation requires R1+ ADR)

| Node | igata cells |
|---|---|
| naphtali | igata_alloy_melt |
| zebulun | igata_die_preparation |
| joseph | igata_shot_injection + igata_solidification_eject |
| levi | igata_post_cast_qc + igata_part_attestation |
| simeon | igata_trim_machining |
| dan | igata_heat_treatment |

6 existing nodes reused; **no new node added** in R0 (silicon Wave 1 added `judah`; igata does not require similar). Matches yakushi Wave 1 pattern (6 nodes reused).

## Roadmap (R0 → R3)

| Phase | Scope | Murakumo fleet | Trigger |
|---|---|---|---|
| **R0** (this ADR) | Scaffold only. No live HPDC. 8 cells import-time RuntimeError. | No deployment | Immediate |
| **R1** | Benchtop **≤500 ton HPDC**; small parts **≤200 g** (bracket, hinge, sensor housing). Single-cavity die. Vacuum-assist optional. | naphtali + zebulun + joseph (3 nodes) | ADR-2605261130 (reserved) + Council Lv6+ vote + SME (HPDC engineer + metallurgist) onboarded + Hibachi PoC firmware |
| **R2** | Pilot **≤2500 ton HPDC**; medium parts **≤5 kg** (suspension knuckle, control arm, transmission housing). Multi-cavity. Full vacuum-assist. | naphtali + zebulun + joseph + levi + simeon + dan (6 nodes) | ADR-2605261145 (reserved) + 30-day public comment + Annex-equivalent facility audit + 3-shot media-fill equivalent (consistency batch) + Hibachi + Tatara onboarded |
| **R3** | Community-scale **≤6000 ton HPDC**; large structural parts **≤50 kg** (vehicle cradle segment, subframe section, tatekata column casting). Full structural certification (human-occupied = G11 + N7 gate). | Full 10-node fleet | ADR-2605261160 (reserved) + 60-day public review + 法務 (建築基準法 + 道路運送車両法) 適合 audit + cross-actor wadachi + tatekata + watatsumi Council multi-domain vote |

Each subsequent phase **requires its own ADR + Council Lv6+ ratification** (wadachi/yakushi/tatekata/watatsumi parity).

## Consequences

### Positive

- **Vendor independence chain closes**: religious-corp が wadachi (vehicle body) + tatekata (construction structural) + watatsumi (submersible reinforcement casting) を外部 IDRA / Bühler に依存せず製造可能になる。constitutional独立性が物理的に成立。
- **§2(e) anti-gatekeeping pro-clearance**: open-source HPDC parameter library (injection profile, die thermal management, gate velocity, vacuum-assist) は世界初の religious-corp 公開 reference として位置づく。yakushi (off-patent OTC 化合物) + watatsumi (modular shipbuilding methodology) と並ぶ anti-gatekeeping triplet。
- **§2(a) 構造的予防成立**: military vehicle hull + aerospace fuselage の流用経路を N2 + N3 で物理的に carve-out。watatsumi N1/N3/N4/N7/N8/N12 と同じ "manufacturing methodology adopted, military application rejected" pattern。
- **G7=NONE achievement**: yakushi Wave 1c (omeprazole chiral, OPCW Schedule 3 不使用) と並ぶ **G7=NONE** wave (Al-Si alloy 物理冶金は Schedule list 非経由)。yakushi Wave 1 acetic anhydride (Schedule 3) DSCG 経路との大きなコントラスト。
- **Circular economy invariant**: G10 (≥95% scrap recovery) は HPDC が物理的に達成可能 (sprue/runner remelt は industry-standard ~98%)。Charter Rider §2(h) GHG 削減と整合。

### Negative / Risk

- **Capital cost**: ≤6000 ton HPDC machine (R3 target) は ~5-15 M USD class equipment。kuni-umi S2 microgrid (2.3-3.1 M USDC) より高い。R3 activation には Public Fund grant + Council 多数決が必要。yakushi Annex 1 facility と同等の capital scale。
- **Energy density**: 大型 HPDC は瞬間電力 high (peak 数 MW 級 induction melt + injection servo)。G9 (≤4 kWh/kg) は実現可能だが、Murakumo node のうち kuni-umi S2 microgrid 電源強化が前提。R2 activation の hard gate。
- **Noise / vibration neighborhood**: HPDC は瞬間衝撃音 + 振動 source。G13 (30-day prior notice + 1 km community feedback) で対応するが、urban 適地が限られる。地方適地 (kuni-umi LandRegistry 山中湖 等) で R2 pilot 想定。
- **§2(a) boundary line continuous tension**: 大型アルミ構造部品は "本質的に dual-use" — civilian vehicle / aerospace civilian airliner にも、military vehicle / military aircraft にも転用可能。N2 (constitutional carve-out) + customer DID 検証 (SBT↔SBT internal carve-out only per N8) + Council Lv6+ supermajority for any external sale (N10) で **3 層 enforcement** を構築。watatsumi G7 (active sonar) と同じく "閾値で線引きできない物理連続量の constitutional handling" pattern。
- **Giga press class deferral (N1)**: Tesla OL 9000 級 (9000 ton) は post-R3 + Council Lv6+ supermajority。実質的に永久 deferral 可能性が高い (vendor lock-in + capital scale + neighborhood impact が乗算)。silicon EUV と同じ "理論的に許可可能だが事実上永久 deferral" pattern。

### Cross-actor integration

| Consumer actor | igata 提供 part | Cell-to-cell wire (R2+) |
|---|---|---|
| wadachi (autonomous mobility) | front/rear underbody segment + battery tray + motor housing | wadachi `vehicle_body_assembly` ← igata `part_attestation` (R3 only, G11+N7 gate) |
| tatekata (construction) | 大型アルミ柱頭 + 梁継手 + 装飾構造 + curtain-wall structural | tatekata `structural_assembly` ← igata `part_attestation` (R2 pilot OK) |
| watatsumi (submersible) | 耐圧殻 ring section pour-cast 補強材 (主耐圧殻は steel/Ti forging 別 actor) | watatsumi `hull_ring_fabrication` ← igata `part_attestation` (R3 only; ≤200m depth class) |
| silicon Wave 2 (fab equipment) | fab equipment frame structural casting | silicon `silicon_packaging` ← igata `part_attestation` (bidirectional) |

R0 では cross-actor wire は declaration only. R2+ activation で actual lexicon record flow が成立。

## Alternatives Considered

### A1: tsukuru manufacturing wave 内に HPDC sub-wave を追加

- **Pros**: Tier-B actor 新設なし; tsukuru の 465-company catalog actor pattern と同居
- **Cons**: tsukuru は **既存 manufacturer の catalog** (vendor を index する actor)。religious-corp 自前の HPDC capability を入れると tsukuru の identity (catalog ≠ producer) が壊れる。yakushi が pharma actor として独立した理由と同じ。
- **Decision**: REJECT — tsukuru catalog + igata producer 分離が正解

### A2: wadachi sub-wave (vehicle body megacasting) として実装

- **Pros**: 主用途 (Tesla giga press = vehicle underbody) と直接整合
- **Cons**: igata の使用先は wadachi だけではない (tatekata 建築 + watatsumi 補強材 + silicon Wave 2 fab equipment frame)。wadachi 内に閉じると cross-actor 供給 supplier 機能が成立しない。tatekata が kuni-umi sub-phase ではなく独立 actor になった理由と並列。
- **Decision**: REJECT — supplier 位置として独立 Tier-B が正しい階層

### A3: R0 で giga press class (≥7500 ton) を最初から scope に含める

- **Pros**: Tesla parity; methodology source (y0oF2UirEMk) と直接整合
- **Cons**: (1) Single global supplier (IDRA OL 9000) lock-in; (2) capital scale 100+ M USD class (religious-corp Public Fund scale を逸脱); (3) noise/vibration neighborhood impact が ≤6000 ton と桁違い; (4) §2(a) military 流用 risk が桁違いに増大。silicon EUV と同じ "理論可能・事実上永久 deferral" が適切。
- **Decision**: REJECT — N1 deferral pattern を採用

### A4: Al-Si alloy 以外 (Mg-alloy / Zn-alloy / Cu-alloy) も R0 に含める

- **Pros**: HPDC industry 全範囲をカバー
- **Cons**: Mg-alloy = 発火 risk (HPDC で smelting fire 多数事例); Zn-alloy = Pb 不純物 RoHS 違反 risk; Cu-alloy = die life 大幅短縮 + 高温作業環境。R0 では Al-Si baseline に固定し、R3+ で Mg-alloy (発火対策 ADR + Council Lv6+ supermajority) を再評価。
- **Decision**: REJECT — Al-Si limit に絞る (yakushi Wave 1 が OTC eye-drop triplet に絞った precedent と並列)

## References

- ADR-2605201400 — kuni-umi planetary-infra fleet (parent Tier-B precedent)
- ADR-2605242000 — wadachi autonomous-mobility R0 (Tier-B R0 scaffold pattern)
- ADR-2605250715 — tatekata construction Tier-B R0 (5-cell linear chain precedent)
- ADR-2605252200 — watatsumi civilian submersible R0 (YouTube methodology adoption + military exclusion pattern)
- ADR-2605250500 — yakushi pharmaceutical R&D master charter (14 gates + 10 non-goals canonical pattern)
- ADR-2605250615 — yakushi Wave 1c (G7=NONE achievement precedent)
- ADR-2605242500 — baien ternary silicon + tsukuru fab charter (constitutional first-party manufacturing pattern)
- ADR-2605242545 — tsukuru fab 8-equipment Pregel charter (8 fab equipment Pregel cells parity)
- ADR-2605191524 — transparent force swarm broadcast witness quorum
- ADR-2605192200 — Charter Compliance Rider v2.0 (§2 prohibited categories — §2(a) weapons, §2(g) sustainability, §2(h) circular economy)
- ADR-2605192100 — etzhayyim Mission Charter (§1.12 Transparent Force, §1.13 Wellbecoming)
- YouTube `y0oF2UirEMk` — "How They Build From Scratch the Giga Press Used by Tesla" (IDRA Group OL 9000 CS class HPDC machine build documentary) — manufacturing methodology source, military application rejected per §2(a)
