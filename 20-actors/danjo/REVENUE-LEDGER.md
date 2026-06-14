# danjo 弾正 — revenue ledger (源泉所得税・復興特別所得税 の使途追跡)

`methods/revenue_ledger.clj` + `data/gov-revenue-seed.jp.edn` + `methods/test_revenue_ledger.clj`

Answers, **in Clojure on the kotoba EAVT Datom log**, the question:

> 日本政府の **源泉所得税** 及び **復興特別所得税** が、どこに、どのように使われているかを
> **1円単位** で追えるか?

## The honest answer is structural, and it differs by tax-kind

Japanese public finance gives two different answers, and the code encodes the difference
**structurally** (not as a disclaimer):

| 税目 | 会計 | `:earmark?` | 1円単位の追跡 |
|---|---|---|---|
| **源泉所得税** | 一般会計 | `false` | **不可** — ノン・アフェクタシオン原則(財源は代替可能/fungible)。特定の1円が特定の歳出に充てられたという会計的事実は存在しない。 |
| **復興特別所得税** | 一般会計 → 繰入 → 東日本大震災復興特別会計 | `true` | **可** — 特定財源。閉じた特別会計境界の中で 繰入額 → 歳出 が1円単位で照合できる。 |

`trace` の判定は「税がどこで徴収されたか」ではなく **「その税を earmarked(特別会計)へ繰入する
`:gov.transfer` が存在するか」** という構造的事実で行う。だから 復興特別所得税(一般会計で徴収・
徴収後に特会へ繰入)は traceable、源泉所得税(繰入なし)は non-traceable と正しく分かれる。

## Honesty gate (danjo G4 の歳入側アナログ)

`outlay-datoms` は、**非 earmarked(一般会計)の歳出に `:gov.outlay/funded-by-tax` を付けようと
すると RAISE する**。一般会計という代替可能な境界を通した「特定税目→特定歳出」の1円単位の出所主張は
**表現不能(unrepresentable)**。danjo が「判決(verdict)」を表現不能にしているのと同じ構造で、
ここでは「偽の出所主張」を表現不能にしている。

加えて受け継ぐ danjo 規律: **G4** 判決トークン禁止 / **G5** 出典 CID ≥2 / `:non-adjudicating true`。

## Data model (kotoba EAVT, `[:db/add E A V]` append-only)

```
account:<id>                 :gov.account/{kind earmark? note}
revenue-line:jp:<fy>:<tax>   :gov.revenue/{tax-kind account fiscal-year amount-jpy source-record-cids sourcing}
transfer:<from>-><to>:<fy>   :gov.transfer/{from to tax-kind fiscal-year amount-jpy source-record-cids}
outlay:<program>:<fy>        :gov.outlay/{account program-code program-name cofog recipient-class
                                          fiscal-year amount-jpy source-record-cids sourcing [funded-by-tax]}
```

金額は exact integer(`amount-jpy`)で **1円精度**。トランザクションは sha256 の content-addressed
commit-DAG(`:tx/cid` = `"b"`+sha256)として `kotoba.py` と同形でローカル append-only ログに積まれ、
`verify-chain` で改竄検知・resume-safe。`run-cycle!` は1サイクル=1tx。

すべての数値は `:representative`(財務省 一般会計 / 復興特別会計 予算の実構造に基づくが、IPFS-pinned
`jp_yosan` / `jp_fukko` corpus の G7 ライブ検証前)。集計・プログラム単位の端点のみ(danjo G10
aggregate-first)。**権威ある予算書ではない。**

## Run

```bash
# tests (bb: fast / clojure: JVM)              22 + EAVT/DAG checks
./run_tests_clj.sh                  # or: CLJ_RUNNER=clojure ./run_tests_clj.sh

# demo trace for both taxes
cd methods && bb -e '(load-file "revenue_ledger.clj") \
  ((resolve (symbol "root.danjo.methods.revenue-ledger" "-main")) "../data/gov-revenue-seed.jp.edn")'
```

```clojure
;; programmatic
(require 'root.danjo.methods.revenue-ledger)            ; or load-file
(def seed (rl/load-seed "data/gov-revenue-seed.jp.edn"))
(rl/trace seed :reconstruction-surtax 2024)  ; => {:traceable? true :per-yen? true :residual 0 :path [...]}
(rl/trace seed :withholding-income    2024)  ; => {:traceable? false :reason :non-earmarked-general-account ...}
(rl/run-cycle! {:seed-path "data/gov-revenue-seed.jp.edn"})  ; persist 1 tx to the local Datom log
```

## Boundary

これは danjo の歳入側拡張であり、**会計検査院でも国家公認の監査機関でもない**(danjo の任意団体・
非断定規律をそのまま継承)。源泉所得税については「予算→支出の相互参照と乖離の事実指摘」までに留まり、
特定の使途を主張しない。R1 で実 corpus の G7 ライブ検証・lexicon 化・fleet 登録。
