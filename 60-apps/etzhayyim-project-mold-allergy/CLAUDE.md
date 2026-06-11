# etzhayyim-project-mold-allergy

カビアレルギー (真菌アレルゲン) の疫学・分子アレルゲン解析と、舌下免疫療法 (SLIT) 錠剤 ─ シダキュア / アシテア lineage の真菌版 ─ を設計・研究する AI actor。

## Architecture

- **Runtime**: TS Native + Lexicon Contract (Cloudflare Worker)
- **Domain**: `mold-allergy.etzhayyim.com`
- **nanoid**: `m0ldalg1`
- **DID**: `did:web:mold-allergy.etzhayyim.com` (ADR-0019 did:plc 移行候補)
- **NSID stem**: `com.etzhayyim.apps.moldAllergy.*`

## Research Scope

### 対象アレルゲン (4 major fungi + minor)

| 属種 | 主要アレルゲン | 生息環境 | 通年 / 季節 |
|---|---|---|---|
| *Alternaria alternata* | Alt a 1 (15 kDa), Alt a 6 | 屋外 / 土壌 / 穀類 | 夏〜秋 |
| *Cladosporium herbarum* | Cla h 8, Cla h 9 | 屋外 / 葉面 | 夏〜秋 |
| *Aspergillus fumigatus* | Asp f 1, Asp f 2, Asp f 3 | 室内 / 堆肥 / エアコン | 通年 |
| *Penicillium chrysogenum* | Pen ch 13, Pen ch 18 | 室内 / 食品 | 通年 |
| *Malassezia* spp. | Mala s 1, Mala s 11 | 皮膚 / 頭皮 | 通年 |
| *Trichophyton* spp. | Tri r 2, Tri r 4 | 皮膚 / 爪 | 通年 |

### 疾患エンドポイント

- アレルギー性鼻炎 (年間 carry: Aspergillus / Penicillium、秋 peak: Alternaria / Cladosporium)
- 気管支喘息 (Severe Asthma with Fungal Sensitization, SAFS)
- アレルギー性気管支肺アスペルギルス症 (ABPA)
- アトピー性皮膚炎増悪 (*Malassezia* sensitization)

### SLIT 錠剤設計目標 (Shidakure / Acitea 同型)

- **剤形**: 舌下速溶錠 (freeze-dried orodispersible tablet)
- **アレルゲン標準化**: JAU / SQ-U 単位 (Torii / ALK-Abelló 準拠)
- **用量漸増**: 1 週 build-up → 維持量 3 年継続 (ARIA guideline 準拠)
- **候補 1st in class**: *Alternaria alternata* rAlt a 1 recombinant SLIT (未承認 gap)
- **候補 2nd**: *Aspergillus fumigatus* 混合抽出 SLIT (SAFS / ABPA 対象、Phase I 設計)
- **Safety target**: WAO Grade 1–2 local reaction, no systemic anaphylaxis

## Agent Architecture

| Agent | role |
|---|---|
| `MycologistAgent` | 真菌同定 / 環境 air sampling / 分子アレルゲン DB (Alt a 1 FASTA, IUIS) |
| `EpidemiologyAgent` | 感作率 (ImmunoCAP f sIgE)・地域別 spore count (花粉観測ネットワーク拡張) |
| `FormulationAgent` | SLIT 錠剤処方 (凍結乾燥マトリクス、糖アルコール賦形剤、溶解時間) |
| `ClinicalAgent` | DBPC-RCT プロトコル (TNSS / CSMS / ACT) / adverse event 追跡 |
| `RegulatoryAgent` | PMDA / FDA BLA / EMA AIT guideline、薬機法コンプライアンス |

5 Matrix rooms: `#mold-allergen-science` / `#mold-slit-formulation` / `#mold-clinical` / `#mold-regulatory` / `#mold-supply-chain`。

## Record Types (`com.etzhayyim.apps.moldAllergy.*`)

- `moldAllergen` — allergen molecule (species, Uniprot, epitope, MW)
- `airSampling` — site, date, genus count, method (Burkard / MAS-100)
- `patientProfile` — sIgE tier, symptom TNSS, comorbidity (private, Signal E2E)
- `slitCandidate` — formulation spec, dose escalation schedule
- `trialProtocol` — DBPC-RCT design, endpoints, sample size
- `adverseEvent` — WAO grade, resolution, causality
- `literatureNote` — PubMed / ClinicalTrials.gov / PMDA 審査報告書 annotation

## PII / Consent

- Patient sIgE / symptom score = **Tier 3** (Preferences, cohort-first per ADR-0018)
- 生検・ゲノム (TLR / FLG / IL-33 SNP) = Tier 3 + Signal E2E
- Air sampling / 気象 spore = Tier 1 public

## Related Actors

- `pharma` (OTC 販路・薬剤師問診レビュー再利用)
- `researcher-bio-gene` (allergen FASTA / epitope prediction pipeline)
- `bunken` (論文 ingest: J-STAGE / PubMed / Cochrane AIT review)
- `kami-sabiotoshi` (住環境・黴除去 domain 連携)

## Next Steps

1. `00-contracts/lexicons/com/etzhayyim/apps/moldAllergy/*.json` の NSID lexicon stub を作成
2. `30-graph/graph-schema/` に `vertex_mold_allergen` / `vertex_air_sampling` / `edge_sensitization` 追加
3. Phase 0: *Alternaria alternata* rAlt a 1 recombinant SLIT 文献レビューと特許 landscape 調査
4. Phase 1: 凍結乾燥オロディスパーシブル錠プロトタイプの賦形剤スクリーニング (mannitol / gelatin / HPMC)
