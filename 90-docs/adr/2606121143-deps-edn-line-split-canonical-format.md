---
id: adr-2606121143-deps-edn-line-split-canonical-format
title: "ADR-2606121143: deps.edn canonical line-split format + structural append — 1 行 EDN の merge-conflict/破損隠蔽の根治"
status: accepted
doc_type: adr
topic: deps-edn-line-split-format
authoritative: true
last_verified: 2026-06-12
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "deps.edn を 1 行 → canonical 行分割フォーマットに移行し、pre-commit gate (--check = parse + canonical) と構造的 append (--append-adrs) を導入。1 行フォーマットが隠していた実破損 (string 内へのエントリ挿入 ×2) も同時修復。"
authoritative_for:
  - deps.edn canonical format
  - deps.edn append protocol (--append-adrs)
  - deps-edn-canonical lefthook gate
depends_on: []
related:
  - adr-2606120750-session-close-search-audit-parquet-free-ingest-readpath-cache
supersedes: []
superseded_by: []
---

# ADR-2606121143: deps.edn canonical line-split format + structural append

**Status**: accepted
**Date**: 2026-06-12
**Deciders**: Jun Kawasaki

# Context

toml→edn 移行は deps.edn を **1 行 ~1.3 MB** で出力した。EDN は whitespace
非依存なので valid だが、運用上 2 つの実害が出た (2026-06-12 に実測):

1. **全変更が全ファイル merge conflict になる。** 1 行なので git は行単位
   merge が一切できず、`:adrs` への並行 append が毎回 conflict。session-close
   PR #1679 は 3 回 rebuild を要し、その rebase 中に #1680 tree-wipe を踏んだ。
2. **破損を隠蔽する。** 調査の過程で deps.edn が**数 merge にわたり invalid
   EDN のまま**だったことが判明: agent の append が「生 bracket カウント」で
   位置決めしていたため、エントリが**別エントリの title 文字列の内部**に
   挿入されていた (#1678 で 1 件、#1679 で 2 件 — 自分のも含む)。quote parity
   が反転し、文字列外に出た `;` が 1 行ファイルの残り全部をコメント化。
   diff が 1 行 vs 1 行なので review でも見えない。

# Decision

## 1. Canonical line-split format

`70-tools/scripts/lint/format-deps-edn.py` (pure stdlib ~240 行) を導入:

- **tokenizer**: EDN 文字列 (escape 対応) / comment / char literal / `#{` set /
  tagged literal (`#inst` は次 form と結合し map pairing を保つ) / atom。
- **layout**: top-level map は 1 key = 1 行。値が「map のみの vector」
  (`:adrs` 等) なら 1 要素 = 1 行 + 閉じ `]` 単独行 — **append が純粋な
  1 行挿入**になり、行単位 merge が機能する (同一 anchor への同時 append は
  なお conflict するが、解決が 1 行 vs 1.3 MB)。それより深い構造は inline。
- **安全性は構成的**: 出力の token 列 == 入力の token 列を assert (whitespace-
  only 変換の証明) + 冪等性 assert。どちらか破れたら書き込まない。
- 適用結果: 1 行 → **920 行**、`:adrs` 384 entries。

## 2. 構造的 append (`--append-adrs`) — 破損の根治

文字列手術での append を廃止する。
`format-deps-edn.py --append-adrs '{:id "…" …}'` は**ファイル全体を parse して
から** `:adrs` vector に node を append し canonical に書き戻す — invalid な
入力は ValueError で止まるため、**この経路ではファイルを壊すことが不可能**。

## 3. Lefthook gate `deps-edn-canonical`

deps.edn が staged されたら `--check` (= full parse + canonical 一致) を必須化。
parse を含むので**破損 gate を兼ねる** — 今回のような string 内挿入は commit
時点で検出される。死んでいた `deps-toml-paths` hook (glob が存在しない
deps.toml のまま) を置換。

## 4. 破損修復 (本 ADR と同 PR)

最後の valid 版 `637528a935` を基底に、以降の全 diff が**純挿入** (removed=0)
であることを検証した上で、誤位置の 3 エントリ (2606121620 / 2606111900 /
2606120750) を parser 経由で `:adrs` へ再配置。**データ喪失ゼロ**。

# Consequences

- 19 unit tests green (tokenizer edge cases: 文字列内 `;`/`{}`/escape、char
  literal、set、tagged、comma-as-whitespace; layout; 冪等性; append 安全性)。
- deps.edn は valid EDN に復帰し、以後 invalid な状態は pre-commit で落ちる。
- agent 運用ルール: **deps.edn への登録は `--append-adrs` を使う** (本 ADR の
  登録自体を同コマンドで実施 = dogfood)。
- ~~残課題 (follow-up): 旧 `verify_deps_toml_paths.py` (orphan path 検査) の
  deps.edn 移植~~ → **DONE 同日**: `verify_deps_edn_paths.py` (marker/duplicate
  意味論を継承 + 新規: submodule-unverifiable / external 分類で checkout 非依存の
  決定的判定 + shrink-only baseline ratchet `deps-edn-paths-baseline.json` =
  既存 drift 12 件を凍結し NEW drift のみ FAIL)。`deps-edn-canonical` hook に
  併設、旧 toml 版 script は削除。初回実測: 707/883 resolve / 19
  accepted-reserved / 13 duplicate ADR id (既知の id race) / legacy drift 12
  (sonae の ADR+actor+lexicon 不在を含む — 別途要調査)。`:modules` 等
  vector-of-maps 以外の大型値の分割は現状不要。

# Alternatives Considered

- **babashka / clojure で公式 pretty-print** — 開発機に未導入のランタイム追加
  が必要; pure-stdlib tokenizer で十分 (値の semantics は不要、token 保存のみ)。
- **jet / zprint 等の外部 formatter** — 同上 + canonical 形の制御が難しい。
- **エントリの :id ソート挿入** (append 位置分散で conflict 削減) — 並行追加は
  通常 id が近接 (同日) なので分散効果が薄い。必要になれば追補。
- **1 行のまま運用で耐える** — 2026-06-12 の実績 (3 rebuild + 破損隠蔽) が反証。

# References

- `70-tools/scripts/lint/{format-deps-edn.py,test_format_deps_edn.py}`
- `lefthook.yml` `deps-edn-canonical`
- ADR-2606120750 (session close — conflict 連鎖と #1680 incident の記録)
