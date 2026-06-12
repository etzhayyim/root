;; ported from 20-actors/kamado/methods/feedstock_guard.py — gold reference (Fable)
;; kamado 竈 — feedstock-class guard (G1 enforcement point #3 of 3). ADR-2606051500.
;; 構造的不変条件: 精製 feedstock は closed-loop carbon でなければならない。
;; :fossil-virgin-crude は表現不能 — set に無いので screen が必ず拒否する
;; (「fossil refinery を自動化する」が単なる非推奨ではなく構造的に不可能になる)。
(ns kamado.methods.feedstock-guard
  (:require [clojure.string :as str]))

;; G1: 表現可能な feedstock クラスはこれだけ。他は全て charter 違反。
(def allowed-feedstock
  #{:biogenic :captured-co2 :recycled-carbon :existing-inventory-decommission})

;; G3: 既存 fossil 資産への表現可能な介入種別はこれだけ。
;; 延命 (:expand / :restart-fossil / :revamp-throughput) は表現不能。
(def allowed-intervention
  #{:decommission :remediate :convert :monitor})

(defn- normalize-keyword
  "文字列/キーワードを先頭 ':' を剥がしたキーワードへ正規化する。"
  [v]
  (cond
    (keyword? v) v
    (string? v) (keyword (str/replace-first v #"^:" ""))
    :else (keyword (str v))))

(defn screen-feedstock
  "G1: closed-loop carbon でない feedstock を拒否する。許可ならキーワードを返す。"
  ([feedstock] (screen-feedstock feedstock ""))
  ([feedstock ctx]
   (let [fk (normalize-keyword feedstock)]
     (when-not (contains? allowed-feedstock fk)
       (throw (ex-info (str "G1 violation" (when (seq ctx) (str " (" ctx ")"))
                            ": feedstock-class " (pr-str feedstock)
                            " is not representable")
                       {:g :G1 :feedstock feedstock :allowed allowed-feedstock})))
     fk)))

(defn screen-intervention
  "G3: 既存 fossil 資産は縮退/転換のみ可、延命は不可。"
  ([kind] (screen-intervention kind ""))
  ([kind ctx]
   (let [ik (normalize-keyword kind)]
     (when-not (contains? allowed-intervention ik)
       (throw (ex-info (str "G3 violation" (when (seq ctx) (str " (" ctx ")"))
                            ": intervention " (pr-str kind) " is not representable")
                       {:g :G3 :kind kind :allowed allowed-intervention})))
     ik)))
