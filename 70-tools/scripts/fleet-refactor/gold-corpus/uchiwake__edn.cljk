;; ported from orgs/etzhayyim/com-etzhayyim-uchiwake/methods/uchiwake_edn.py — gold reference (Fable)
;; uchiwake 内訳 — GTIN 正規化 + GS1 mod-10 チェックディジット検証 + EDN 文字列エスケープ。
;; GTIN は GS1 mod-10 で検証し、不正/欠落なら record を SKIP する (admit しない)。
(ns uchiwake.methods.edn
  (:require [clojure.string :as str]))

(defn- digits-only [s]
  (apply str (filter #(Character/isDigit ^char %) (str s))))

(defn normalize-gtin
  "GTIN-8/12/13 を canonical な 14 桁 GTIN-14 へ左ゼロ詰めする。"
  [gtin]
  (let [d (digits-only gtin)]
    (str (apply str (repeat (max 0 (- 14 (count d))) \0)) d)))

(defn gtin-check-digit-ok?
  "GTIN (長さ 8/12/13/14) の GS1 mod-10 チェックディジットを検証する。"
  [gtin]
  (let [d (digits-only gtin)]
    (if-not (contains? #{8 12 13 14} (count d))
      false
      (let [body (butlast d)
            check (Character/digit ^char (last d) 10)
            ;; GS1: body 右端を ×3、交互に重み付け
            total (->> (reverse body)
                       (map-indexed (fn [i ch]
                                      (* (Character/digit ^char ch 10)
                                         (if (even? i) 3 1))))
                       (reduce + 0))]
        (= (mod (- 10 (mod total 10)) 10) check)))))

(defn edn-str
  "python 文字列を quoted EDN 文字列リテラルへエスケープする。"
  [s]
  (str \" (-> (str s)
              (str/replace "\\" "\\\\")
              (str/replace "\"" "\\\"")) \"))
