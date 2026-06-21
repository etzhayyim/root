---
id: adr-2605181040-uhl-medical-institution-registry
title: "ADR-2605181040: UHL-R 医療機関レジストリ — data schema + 公開ポリシー (公的情報のみ・PII無し)"
status: proposed
doc_type: adr
topic: uhl-right-neural-institution-registry
authoritative: true
last_verified: 2026-05-18
priority: 6.5
axis: data-contract
weight: 0.60
priority_note: "uhl-right-neural project (先天性片側感音難聴/neural軸) の InstitutionMatcherActor (V16) が消費するレジストリの schema と公開ポリシーを凍結する。患者 PII を一切含まない公的情報のみで構成し、kotoba 制約と整合する。"
authoritative_for:
  - Institution / Capability / ProcedureRecord / ReferralPath schema
  - public-only data policy for medical institution registry
  - last_verified_at staleness window (180 days)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172000-etzhayyim-kotoba-substrate
related:
  - adr-2605180900-unispsc-isic-langserver-actor-lexicon-xrpc-mcp
supersedes: []
superseded_by: []
---

# ADR-2605181040: UHL-R 医療機関レジストリ — data schema + 公開ポリシー

**Status**: proposed
**Date**: 2026-05-18
**Deciders**: Jun Kawasaki

# Context

`uhl-right-neural` プロジェクト (先天性右側感音難聴・neural軸研究 Pregel) の終端 vertex として `InstitutionMatcherActor (V16)` を置く。V06 (substrate classifier — SGN/nerve/HC の4-way 分類) の出力 + 患者 locale を入力とし、対応可能な医療機関を ranking して返す。

このマッチング actor が消費する**機関レジストリ**を定義する必要がある。スコープと制約:

1. **kotoba 制約 (ADR-2605172000)**: state は AT Protocol MST + IPFS + Base L2 anchor のみ。中央集権 DB を持たない。
2. **PII zero**: レジストリは「施設の capability claim」だけを含む。患者-施設マッチ結果は患者 DID で encrypt された別レコード (本 ADR の対象外)。
3. **データ鮮度問題**: 文献調査で発見した実例数は古い (例: 「ABI 国内11例」は 2011 時点)。**`last_verified_at` を必須にし、staleness を強制可視化**する必要がある。
4. **多言語**: 国内 8 施設 + 国際参照 7 施設で開始。フィールド名は英語、表示名は ja/en 並記。

国内施設候補 (初期 seed):

| 機関 | 主 capability |
|---|---|
| 信州大学 耳鼻咽喉科 (宇佐美研) | 遺伝学的検査 (保険診療 2012〜, GJB2/SLC26A4/CDH23/OTOF panel) |
| 国立病院機構 東京医療センター 人工内耳センター | 小児 CI 500+ 症例 (2007〜)、内耳奇形対応 |
| 慶應義塾大学 耳鼻咽喉科 (藤岡/細谷) | iPSC→otic organoid (SGN-like), Notch阻害 HC再生 |
| 横浜市立大学附属市民総合医療センター | CI 200症例 (2000〜) |
| 東京医科大学 聴覚・人工内耳センター | CI |
| 東京大学 耳鼻咽喉科 | CND/内耳神経低形成評価 |
| 福島県立医大 脳神経外科 × 日本医大 脳神経外科 | ABI (自費診療、国内主要拠点) |
| AMED 視覚聴覚二重障害研究班 | コンサル/referral hub |

国際参照 (referral path は ADR-2605181050 で別途):

| 機関 | 主 capability |
|---|---|
| Mass Eye and Ear / Eaton-Peabody (Chen Zheng-Yi) | OTOF gene tx 開発、Usher gene editing |
| Manchester University NHS FT / Royal Manchester Children's Hospital | 小児 ABI (NHS指定2拠点、CND/aplasia 9症例) |
| Guy's and St Thomas NHS FT | 小児 ABI (NHS指定2拠点) |
| Universität Göttingen / EKFZ OT (Moser) | Optogenetic CI (ChReef opsin, 霊長類成功) |
| University of Sheffield (Rivolta) | hESC→otic neural progenitor 移植 |
| Regeneron / Decibel Therapeutics | Otarmeni (lunsotogene parvec-cwha) sponsor |
| DZNE / DZHK | optogenetic clinical 橋渡し |

# Decision

## Schema 凍結

レジストリ 1 レコード = 1 機関。本体は MST レコードとして PDS に書き込み、IPFS に CAR pin。L2 anchor (ADR-2605172100) は seed batch 単位で 1 回。

### `Institution` (top-level)

```yaml
$type: jp.etzhayyim.med.uhl.institution
id: <slug, lowercase, e.g. "jp-shinshu-u-orl">
did: <optional, did:web:... if institution is a substrate participant>
name_ja: <Japanese display name>
name_en: <English display name>
country: <ISO 3166-1 alpha-2>
locale: <city + prefecture/state>
website: <https url>
contact:
  ja_phone: <optional, public general line only>
  en_email: <optional, public contact only>
capabilities: [<Capability>]  # 1..N
referral_paths: [<ReferralPathRef>]  # 0..N, foreign keys to ADR-2605181050 paths
last_verified_at: <ISO-8601 date>
verified_by: <person responsible (jun@etzhayyim.com for now)>
```

### `Capability` (enum + procedure record)

```yaml
$type: jp.etzhayyim.med.uhl.capability
kind:
  - GENETIC_TEST           # hereditary deafness panel
  - PED_CI                 # pediatric cochlear implant
  - CND_CI                 # CI with cochlear nerve deficiency
  - ABI                    # auditory brainstem implant
  - GENE_TX_OTOF           # Otarmeni or equivalent
  - OPTO_CI_TRIAL          # optogenetic CI (research / trial)
  - NEURAL_REGEN_RESEARCH  # SGN regen / reprogramming / stem cell
  - CONSULT_HUB            # diagnostic & referral coordination only
procedure_record:
  cumulative_count: <int|null>
  count_as_of: <ISO-8601 date|null>
  evidence_url: <https url>             # MUST be public source
  reimbursement: <hoken|self_pay|trial|unknown>
notes_ja: <optional, plain text>
```

### `ReferralPathRef` (foreign key only here, defined in ADR-2605181050)

```yaml
$type: jp.etzhayyim.med.uhl.referralPathRef
path_id: <slug, defined in ADR-2605181050>
```

## 公開ポリシー

1. **PII zero**: 個別患者・個別医師個人 (公的責任者ポジションでない) は記載しない。研究室名は principal investigator の公表 affiliation に限る。
2. **Public sources only**: `evidence_url` は学会誌・公式サイト・査読論文・規制機関 (FDA/PMDA/EMA) のみ。SNS・個人ブログ不可。
3. **`last_verified_at` 必須**: 全レコード必須。staleness window = **180 日**。180 日超は `InstitutionMatcherActor` が "stale" フラグ付きで返す (除外はしない)。
4. **法的 disclaimer**: レジストリは medical advice ではない。マッチ結果は必ず「主治医・倫理委・家族との人間判断に escalate」する旨を schema レベルで強制 (`output.requires_human_review: true` を Lexicon で固定)。
5. **Update procedure**: 機関側からの更新要求は GitHub issue 経由。事務局 (jun@etzhayyim.com) が verify → PR → merge → MST 反映の固定フロー。
6. **License**: レジストリ全体は CC-BY-4.0 (本 repo Apache 2.0 とは別、データセット標準に合わせる)。

## 配置

```
40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/projects/uhl_right_neural/
├── schemas/
│   └── institution.py                  # Pydantic v2 models (above schema)
├── seed/
│   ├── institutions_jp.yaml            # 8 institutions (above table)
│   ├── institutions_intl.yaml          # 7 institutions
│   └── README.md                       # update procedure + source policy
└── actors/
    └── institution_matcher.py          # V16 actor (separate PR)

00-contracts/lexicons/jp/etzhayyim/med/uhl/institution/
├── defs.json                           # Institution / Capability schemas
└── matchQuery.json                     # XRPC: substrate → ranked institutions
```

## CI/validation

- `lefthook` pre-commit hook (future): `evidence_url` の HTTP 200 verification (sampling), `last_verified_at` 形式 check
- `90-docs/_registry/docs.json` generator が institution count を集計

# Consequences

## 正の効果

- **InstitutionMatcherActor (V16) の入力契約が確定** — 他の actor 開発と並行して進められる
- **Schema が JSON-LD で参照可能** — 将来の AppView (`60-apps/open-otology-uhl-r/`) と XRPC 経由のリクエストに直接使える
- **kotoba 制約と整合** — 中央 DB を持たない、MST + IPFS で完結
- **staleness が可視** — 古い実例数 (ABI 11例 / 2011) のような問題が UI で自動的に flag される

## 負の効果 / コスト

- **手動 seed の運用負荷** — 自動更新は将来課題。当面は事務局 1 名 (jun@etzhayyim.com) のスループット律速
- **15 機関では sparse** — 国内に小児 CI 実施施設は 40+ あるが、CND 対応・遺伝学的検査対応で絞ると seed の 8 施設で実質網羅
- **国際参照の現実性** — Manchester/Göttingen への referral は渡航・通訳・術後ケアまで含めると非常に高コスト。レジストリに載せても適用可能症例は少数

## Out of scope

- **患者-施設マッチ結果の永続化** — 患者 DID で encrypt した個別レコードは別 ADR
- **保険適用判定** — レジストリには `reimbursement` enum のみ。個別保険会社の適用判断はしない
- **施設側からの bi-directional API** — 当面 read-only registry。書き込みは GitHub PR 経由のみ

# Alternatives Considered

## A. 機関名のみのフラット list (capability 構造化なし)

却下理由: `InstitutionMatcherActor` が「SGN absent + nerve present → 誰に referral?」のような構造クエリを実行不可能。capability enum は必須。

## B. 国際 registry をハードコードせず、 ClinicalTrials.gov / WHO ICTRP からの実行時 fetch

却下理由: 鮮度は上がるが、(1) network 依存で actor が deterministic でなくなる、(2) institutional capability (CND-CI 経験など) は ClinicalTrials.gov に乗らない。手動 seed + 180日 staleness の組み合わせが現実解。

## C. 患者-施設マッチを actor 内で実行せず、UI で人間が選ぶ

却下理由: V06 出力 (substrate class) を理解して機関を選べる利用者は限定的。Actor で ranking + 人間 escalate が正しい責任分割。本 ADR の `requires_human_review: true` 強制で安全側に倒している。

## D. CC0 vs CC-BY-4.0

却下選択: CC0 だと "source of truth" が消失する。CC-BY-4.0 で出典明示を強制。

# References

- ADR-2605170900 — etzhayyim/root as canonical home for open ADRs
- ADR-2605172000 — kotoba substrate
- ADR-2605181050 — UHL-R 海外 referral path (this PR sibling)
- ADR-2605181060 — Otarmeni access path (this PR sibling)
- [Clinical Perspectives on Pediatric CI in Cochlear Nerve Aplasia/Hypoplasia (PMC 2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12382941/)
- [信州大学 耳鼻咽喉科 難聴の遺伝学的検査](https://www.shinshu-jibi.jp/examination/index.html)
- [国立病院機構 東京医療センター 人工内耳センター](https://tokyo-mc.hosp.go.jp/section/cochlear_implant_center.html)
- [日本耳鼻咽喉科 ABI 国内手術 (福島県立医大 × 日本医大)](https://www.jstage.jst.go.jp/article/jibiinkoka/114/11/114_11_851/_article/-char/ja/)
- [AMED 視覚聴覚二重障害 (盲ろう) 小児人工内耳マニュアル](https://dbmedj.org/manual/chapter/ch3-9/index.html)
