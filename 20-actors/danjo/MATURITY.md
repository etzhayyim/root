# danjo (弾正) — Maturity Ledger

`/loop` (30分毎) の進捗台帳。各イテレーションで **1項目** だけ成熟度を上げ、ここに
記録する。honest framing: できていないことは「未」と明記する。

- Actor: `did:web:danjo.etzhayyim.com` · ADR-2605301600 (+ ADR-2605302245 global
  fiscal-flow extension) · **R0 scaffold**
- 不変条件(全イテレーション厳守): R0 では cell 非実行 · live ingestion/dispatch なし ·
  **NON-adjudicating (G4)** — 犯罪/不正/法令違反 を断定しない、verdict なし ·
  **passive-only ingestion (G3)** — 既公開 IPFS-pinned `gov.dataset.*` のみ、portal 再 scrape 禁止 ·
  source-provenance 必須 (G5) · open method (G6) · Transparent Force discipline (G11/§1.12) ·
  Murakumo-only inference (ADR-2605215000) · G8 非捏造 · G14 verified-source-only ·
  コミットはユーザー明示時のみ

## 成熟度チェックリスト

| # | 項目 | 状態 | 完了イテレーション |
|---|---|---|---|
| 1 | ADR-2605301600 (master) + ADR-2605302245 (fiscal-flow) | ✅ | init |
| 2 | manifest.jsonld + README + CLAUDE.md | ✅ | init |
| 3 | Lexicon skeletons (`com.etzhayyim.danjo.*`) | ✅ | init |
| 4 | worldwide fiscal-source registry seed (`registry/sources.seed.json`, 全件 unverified-seed) | ✅ | seed |
| 5 | fail-closed registry invariants test + G14 VERIFICATION.md | ✅ | この iter |
| 6 | `run_tests_clj.sh` の3 suite (`test_budget_ledger.clj`/`test_kotoba.clj`/`test_autorun.clj`) が dormant (実行不能) | 🔴 未 (診断のみ) | 2026-07-10 |

## イテレーション記録

### 2026-07-10 (loop) — dormant test-suite drift の正確な診断(修正は未実施、honest framing)
`run_tests_clj.sh` の3 suiteが `FileNotFoundException` で全滅していた件(前 iteration で発見)を実際に
調査。**単純なファイル名ズレではなく、複数の独立した根深い問題と判明**したため、今回は診断のみに留め、
誤った"fix"を主張しない:

1. **`test_budget_ledger.clj`**: `(load-file "budget_ledger.clj")` は存在しない(実体は
   `budget_ledger.cljc`)。ロードパスを `.cljc` に直しても、テストが呼ぶ `bl/canonical-json` は
   現行の `budget_ledger.cljc` に存在しない — 実際の関数名は `canonical-json-utf8`(かつ `defn-`
   private)。`record-cid`/`normalize-record`/`build-ledger`/`load-seed` 等、他の呼び出しも
   現行APIと1件ずつ突き合わせが必要(未実施)。
2. **`test_kotoba.clj`**: 同様に `(load-file "kotoba.clj")` → `kotoba.cljc` へのロードパス修正で
   起動はするが、末尾の "tamper located at the corrupted tx index" チェックで
   `(ko/verify-chain path)` の `:broken-at` が `nil` を返し `(>= nil 0)` が例外になる —
   ロードパスを直して初めて実行された結果、`kotoba.cljc` の tamper-detection ロジック自体に
   **未検証の潜在バグがある可能性**が判明(このテストは .cljc 移行後、一度も実行されていなかった)。
3. **`test_autorun.clj`**: 実体は存在せず `test_autorun.cljc` のみ。こちらは単純な rename では済まず、
   `(:require [danjo.methods.autorun :as autorun] [danjo.methods.kotoba :as kotoba])` という
   namespace-qualified require を使っており(他の sibling test は load-file 方式)、bb 実行時に
   classpath 上で `danjo/methods/autorun.cljc` を解決できず失敗する — `bb.edn`/`deps.edn` の
   `:paths` 整備か、他ファイルと同じ load-file 方式への変更が必要(未実施)。

**honest (G8)**: この3 suiteは now も dormant のまま — 今回のiterationでは "1項目" の範囲を
「壊れたテストを直す」から「壊れ方を正確に診断し、誤ったgreen主張をしない」に絞った。次のiteration
候補: (a) `budget_ledger.cljc` の現行public APIに合わせて `test_budget_ledger.clj` を書き直す、
(b) `kotoba.cljc` の `verify-chain`/`:broken-at` ロジックを個別に検証する、(c) `test_autorun.cljc`
の require を load-file 方式に統一するか `bb.edn` を追加する。いずれも本iterationの「1項目」原則を
超える(複数ファイル・複数根本原因)ため、意図的に見送った。

## イテレーション記録 (承前)

### worldwide fiscal-source catalog hardening (2026-06-02)
**WORLDWIDE fiscal-source 台帳の fail-closed 固定 + G14 検証ワークフロー文書化。**
既存の `registry/sources.seed.json`(166 件 / 34 distinct jurisdiction + 国際機関
[IMF / World Bank / OECD / UN / IATI / OGP] / sourceKind 6種: audit-institution /
budget-portal / intl-aggregator / legislature-record / open-spending /
procurement-system)に対し、sibling toritsugi 方式で 2 層の hardening を追加:
(1) `70-tools/scripts/audit/test_danjo_registry_seed.py`(**8 test, 全 green**)—
①JSON parse + `sources` 非空 ②`sourceId` 一意(重複で fail)③全件
`verificationStatus="unverified-seed"`(G14)④全件 https provenance + ISO-8601
`lastVerified` ⑤≥12 distinct jurisdiction(worldwide guard; JP-only 退行ガード)
⑥全件 `sourceKind` が allowed catalog set 内 ⑦全件 notes 非空 + 台帳が
NON-adjudicating / observational 境界を参照 ⑧top-level 整数 `freshnessWindowDays`。
test-only・network-free・cell 実行なし(R0 ceiling 不変)。
(2) `20-actors/danjo/registry/VERIFICATION.md` — G14 三層(unverified-seed →
maintainer-verified → council-verified)の人手チェックリスト。per-field 10項目 +
**per-jurisdiction official-domain provenance check**(.gov / .go.jp / .gouv.fr /
.gov.uk / europa.eu / .gob.* / .go.kr / 国際機関ドメイン、fail-closed)+
NON-adjudicating / observational 境界 re-check を明記。
**honest (G8)**: **検証済みソースは 0 件** — 全件 unverified-seed のまま。台帳は
既公開公式データの ingestion scaffold であり authoritative inventory ではない。
実際の verification 実行は R1(Council ratify + fiscal-source-verification
maintainer DID 登録後)。danjo finds + cross-references; kanae renders; neither
adjudicates。

### 2026-06-17 (loop) — manifest+lexicon charter-gate test (構造ゲート pin)
新設 `methods/test_charter_gates.cljc`(**7 tests green**)で manifest G1–G13 + 4 lexicon の非裁定ゲートを固定: G4 discrepancyObservation/oversightReport const nonAdjudicatingNotice=true + 全lexicon に verdict/accusation/guilt/ruling フィールド不在(censor's eye, never sword)/ G5 observation が sourceRecordCids + methodNoteCid、crossReferenceLink が basisRecordCids(≥2 source)/ G6 methodNote が definition+inputs+version / G11 publiclyNamedBasis={procurement-awardee, diet-member-on-record, budget-recipient, contracting-authority} / governance oversightReport が councilAttestations + councilReviewCid + oneSbtOneVoteChainCid。`run_tests.sh` 新設。working-tree edits only。

> **2026-06-17 substrate-native migration (ADR-2606160842):** the charter-gate test above was ported Python→Clojure (`methods/test_charter_gates.py` → `methods/test_charter_gates.cljc`, ns `danjo.methods.test-charter-gates`, reads the lexicons via cheshire/edn) and the Python was pruned. Run via `./run_tests.sh` (now `exec bb`) or `bb run test:charter` (all 34 charter suites; 244 tests / 924 assertions green). Assertions unchanged (1:1 port).
