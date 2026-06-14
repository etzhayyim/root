---
id: adr-2606141200-matsurigoto-tax-collect-jp-withholding-remittance
title: "ADR-2606141200: matsurigoto tax-collect — JP 法人源泉所得税・復興特別所得税の納付処理 (Clojure)"
status: accepted
doc_type: adr
topic: matsurigoto-tax-collect-jp-withholding-remittance
authoritative: true
last_verified: 2026-06-14
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - matsurigoto tax-collect module (源泉徴収納付 / withholding remittance)
  - JP corporate 源泉所得税 + 復興特別所得税 reference computation + 納付処理
depends_on:
  - adr-2606062300-matsurigoto-egov-execution-commons
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605231525-etzhayyim-no-server-key
supersedes: []
superseded_by: []
---

# ADR-2606141200: matsurigoto tax-collect — JP 法人源泉所得税・復興特別所得税の納付処理 (Clojure)

**Status**: accepted (R0 reference-impl landed)
**Date**: 2026-06-14
**Deciders**: Jun Kawasaki

# Context

ADR-2606062300 が matsurigoto の COFOG e-gov standard を定め、`tax-collect` module / サービス
`tax.withholding.remit` (源泉徴収納付) を `:planned` として予約していた。実装は存在せず、唯一の
徴収系コードは申告税額を算定する Python の `tax-assess` (申告側) だった。

日本の法人は **源泉徴収義務者** として、給与・報酬・配当・利子・退職手当・非居住者への支払等から
**源泉所得税 + 復興特別所得税 (所得税額の2.1%, 復興財源確保法28条, 2013–2037)** を徴収し、
**所得税徴収高計算書 (納付書)** で国に納付する義務を負う。この「計算 → 納付書 → 納期限 →
加算税延滞税 → 政府手続き → 問い合わせ先」の一連の処理が未実装だった。本リポジトリは Tier-B
analyzer を Python→Clojure に移植中であり、新規実装は **Clojure (babashka)** で行う方針。

# Decision

matsurigoto の `tax-collect` module の R0 reference implementation を **Clojure** で実装し、
`20-actors/matsurigoto/tax_collect/` に置く (ns `matsurigoto.tax-collect.*`)。`tax.withholding.remit`
を `:planned → :reference-impl` に昇格する。`tax.payment` / `tax.collection.enforce` は範囲外
(`:planned` のまま)。

**スコープ (法人=源泉徴収義務者の全カテゴリ + 政府側手続き全般):**

- `withholding` — 源泉徴収税額の計算: 報酬・料金 (所得税法204条: 原則10.21% / 100万超20.42% /
  司法書士1万円控除 / 外交員12万円控除 / ホステス5000円×日数 / 広告賞金50万円控除) · 給与
  (電子計算機計算の特例; 別表は :representative パラメータ) · 賞与 (算出率) · 退職所得 (退職所得控除 +
  速算表 + 役員5年以下の1/2不適用 + 申告書なし一律20.42%) · 配当 (上場15.315% / 非上場20.42%) ·
  利子 (15.315%) · 非居住者 (20.42% + 条約軽減フラグ)。**合計税率を ppm 整数で保持し、1円未満
  切捨てを厳密整数演算で行う** → 官報「源泉徴収のための復興特別所得税及び所得税の合計税率」と一致。
- `payment` — 所得税徴収高計算書8様式 · 法定納期限 (原則=翌月10日 / 納期特例=1–6月分7/10・
  7–12月分翌1/20; 土日祝・年末年始は翌開庁日に繰下げ) · 不納付加算税 (10% / 自主5% / 5,000円未満
  不徴収 / 1か月以内猶予) · 延滞税 (通則法60条, 2か月境界, 特例基準割合は :representative) · 納付方法
  (e-Tax ダイレクト納付・ネットバンキング・クレカ・コンビニQR・スマホ・窓口) · unsigned 納付書。
- `jp_calendar` — 祝日法に基づく国民の祝日 (固定 + Happy-Monday + 春分/秋分近似 + 振替休日 +
  国民の休日) + 税務署閉庁日 (土日祝 + 12/29–1/3) + 翌開庁日繰下げ。
- `procedures` — 政府側手続き registry 10種 (給与支払事務所開設届 / 納期特例承認申請 / 扶養控除等
  申告 / 基礎控除等申告 / 年末調整 / 退職所得申告 / 給与源泉徴収票 / 退職源泉徴収票 / 報酬支払調書 /
  法定調書合計表) + トリガー引き当て + 起算日からの提出期限算定。
- `contacts` — 問い合わせ先 registry (国税庁 03-3581-4161 / e-Tax ヘルプデスク 0570-01-5901 を
  :authoritative、12国税局=47都道府県管轄 + 国税局電話相談センター + 税務署「法人課税部門」を案内) +
  都道府県→所轄国税局ルーティング。
- `datom_emit` — 納付イベントを append-only EAVT datom (`:gensen.*`, ADR-2605312345) に変換。
- `tax_collect` — module facade (`process-period` でオフライン納付書 + Datom 生成)。

**不変条件 (matsurigoto G1/G2/G3 を継承):**

- **G1 no-operator-master-key** — 各 ns で `SERVER-HELD-AUTHORITY = false`。モジュールは何も
  署名せず、納付書は unsigned (`:proof nil`)。
- **G2 spec-derived-only** — 所得税法181-230条 / 復興財源確保法28条 / 国税通則法36・60・67条 /
  国税庁様式に準拠。年次改定される値 (給与月額表の別表、延滞税の特例基準割合) は
  `:representative` パラメータとして data EDN に分離し、確定値は deployment が `:authoritative`
  供給 (tax-assess の「universal algorithm + localized parameter」方式)。
- **G3 authority-bearing** — 納付主体 `:operated-by` は呼び出し側が渡す。
- **G5 sourcing-honest** — 個別の国税局/税務署の電話番号は fabrication せず
  `:pending-verification` / `:pending-live-ingest` + 出典URL とする (確定は国税庁サイトからの
  G7-gated live ingest)。
- **G8 outward-gated** — 実際の納付 (e-Tax送信・口座引落・法定調書提出・canonical Datom log への
  ingest) は Council+operator gated。全 `solve()` / `ingest!` は raise する。
- **Murakumo-only** (ADR-2605215000) — 本 module は推論を呼ばないが、将来の narration は Murakumo 経由。

# Consequences

- `tax.withholding.remit` が R0 reference-impl として動作 (オフライン・unsigned)。`bb test:matsurigoto`
  = **44 tests / 157 assertions green** (babashka)。
- 法人の源泉徴収実務 (計算→納付書→納期限→加算税延滞税→政府手続き→問い合わせ先) が一貫して
  データ化・参照可能になり、kotoba Datom log への投入形 (`:gensen.*`) も用意された。
- 給与月額表の別表と延滞税の特例基準割合は年次で確定値を要する (`:representative` のまま)。
  正本値の供給と live 納付 (e-Tax/eLTAX) は Council+operator gated の R1 以降。
- 個別税務署 (約520署) の所在地・電話の完全 registry は live ingest 待ち (G5/G7)。

# Alternatives Considered

- **Python (`methods/modules/tax_collect.py`) で実装** — 既存 module 群と揃うが、リポジトリは
  Clojure 移行中であり、ユーザ要請も Clojure。babashka で純関数 + clojure.test が揃うため Clojure を選択。
- **給与月額表を官報の確定値で埋め込む** — 年次改定のため陳腐化し、誤った authoritative 主張になる
  リスク。`:representative` パラメータ + アルゴリズム検証に留め、確定値は deployment 供給とした (G2/G5)。
- **個別税務署の電話番号を seed する** — 変更され得る数百件を fabrication するのは G5 違反。中央2窓口
  のみ :authoritative とし、残りは出典URL + provenance マーカーで honest に未確定を明示。

# References

- ADR-2606062300 — matsurigoto e-gov execution commons (parent; `tax-collect` module 予約)
- ADR-2605312345 — kotoba Datom = first-class canonical state (`:gensen.*` EAVT)
- ADR-2605215000 — Murakumo-only inference
- ADR-2605231525 — no-server-key
- 実装: `20-actors/matsurigoto/tax_collect/` · data: `20-actors/matsurigoto/data/{withholding,procedures,contacts}/`
- 国税庁 源泉徴収のあらまし: https://www.nta.go.jp/publication/pamph/gensen/aramashi/
