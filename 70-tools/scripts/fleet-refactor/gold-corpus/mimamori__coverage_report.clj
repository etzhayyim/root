;; ported from 20-actors/mimamori/methods/coverage_report.py — gold reference (Fable)
;; mimamori 見守り — AGGREGATE-ONLY coverage report (G5: NEVER-a-throne)。
;; 誰の保持者でもない人間を作らない — 名指さず数える。レポートは COUNT のみ。
;; DID も per-person 行も決して含めない (test-enforced: 出力に "did:" は現れない)。
;;
;; engine は {:kept {bond keeper} :state {bond status} :datoms […]} の純データとして渡す。
(ns mimamori.methods.coverage-report
  (:require [clojure.string :as str]
            [clojure.set :as set]))

(defn coverage-of-engine
  "engine と roster から aggregate-only coverage を計算する (G5)。"
  [engine roster-list]
  (let [roster (set roster-list)
        state (:state engine)
        kept (:kept engine)
        keepers-in (fn [status]
                     (set (for [[b st] state :when (= st status)] (kept b))))
        kept-active (keepers-in :active)
        kept-pending (keepers-in :offered)]
    {:members-total (count roster)
     :with-keeper (count (set/intersection kept-active roster))
     :offers-pending (count (set/intersection
                             (set/difference kept-pending kept-active) roster))
     :unkept-count (count (set/difference roster kept-active kept-pending))
     :active-bonds (count (filter #(= % :active) (vals state)))
     :relays (count (filter #(= % :handed-off) (vals state)))
     :datoms (count (:datoms engine))}))

(defn render
  "coverage map を Markdown へ。DID は構造的に現れない。"
  [c]
  (str/join "\n"
            ["# mimamori 見守り — coverage report (AGGREGATE-ONLY, G5)"
             ""
             "GENERATED — do not hand-edit. No DID appears here, by construction."
             ""
             (str "- members (synthetic roster): " (:members-total c))
             (str "- with an active keeper:      " (:with-keeper c))
             (str "- offers pending:             " (:offers-pending c))
             (str "- **unkept (the gap)**:       " (:unkept-count c))
             (str "- active bonds:               " (:active-bonds c))
             (str "- relays (継ぎ):              " (:relays c))
             (str "- datoms (append-only):       " (:datoms c))
             ""
             "The unkept are not listed (G5). The offer-matching cell reaches them"
             "directly, one covenant offer at a time."
             ""]))
