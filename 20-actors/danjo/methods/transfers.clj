;; transfers.clj — 弾正 (danjo) 国→地方 財政移転 (地方交付税 法定率繰入). ADR-2605301600.
;;
;; The honest insight this layer encodes: a tax can be fungible OVERALL (源泉所得税 → 一般会計,
;; per-yen 不可) yet have a LEGALLY-DEFINED PORTION (法定率分, 地方交付税法6条) that flows per-yen-
;; traceably to 地方 via the closed 交付税特会. transfers.clj reports that PORTION as its own
;; traceable flow WITHOUT flipping the tax's overall classification — portion-based honesty.
;;
;; rate-bp = 法定率 (basis points). amount = floor(source-tax × rate-bp / 10000), 1円-exact integer
;; math (no float). Pure + JVM stdlib; bb / clojure.
(ns root.danjo.methods.transfers
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(load-file "taxes.clj")
(alias 't  'root.danjo.methods.taxes)
(alias 'rl 'root.danjo.methods.revenue-ledger)

(defn load-transfers
  ([] (load-transfers nil))
  ([path]
   (let [f (io/file (or path "20-actors/danjo/data/jp-fiscal-transfers.edn"))
         f (if (.exists f) f (io/file "../data/jp-fiscal-transfers.edn"))]
     (edn/read-string (slurp f)))))

(defn- tax-amount [tax-reg id]
  (or (->> (:taxes tax-reg) (filter #(= id (:id %))) first :fy2024-amount-jpy) 0))

(defn compute
  "Resolve each 法定率 allocation against the tax registry → exact 1円 amounts. Returns the
   transfer registry enriched with :amount-jpy on each allocation + a :total-inflow + the
   per-distribution amounts (share of the pooled inflow)."
  [transfer-reg tax-reg]
  (let [allocs (mapv (fn [a]
                       (let [src (tax-amount tax-reg (:from-tax a))]
                         (assoc a :source-amount-jpy src
                                  :amount-jpy (quot (* src (:rate-bp a)) 10000)
                                  :traceable? true :per-yen? true)))
                     (:allocations transfer-reg))
        total (reduce + 0 (map :amount-jpy allocs))
        dists (mapv (fn [d] (assoc d :amount-jpy (quot (* total (:share-bp d)) 10000)))
                    (:distributions transfer-reg))
        grants (mapv #(assoc % :traceable? true :per-yen? true) (:grants transfer-reg))]
    (assoc transfer-reg :allocations allocs :distributions dists :grants grants
           :total-inflow total :grants-total (reduce + 0 (map :amount-jpy grants)))))

(defn- add [e a v] [:db/add e a v])

(defn transfer-datoms
  "Flatten the 法定率 transfers + 交付 distributions → append-only EAVT. The 交付税特会 account is
   declared earmarked here; inflows are :gov.transfer/* (per-yen traceable); distributions are
   :gov.alloc/* (交付税特会 → 地方団体)."
  [computed]
  (let [acct (str "account:" (subs (str (:to-account computed)) 1))]
    (vec
     (concat
      [(add acct :gov.account/kind :special)
       (add acct :gov.account/earmark? true)
       (add acct :gov.account/ja (:to-account-ja computed))]
      (mapcat
       (fn [a]
         (let [e (str "transfer:" (name (:id a)))]
           [(add e :gov.transfer/from :general)
            (add e :gov.transfer/to (:to-account computed))
            (add e :gov.transfer/from-tax (:from-tax a))
            (add e :gov.transfer/rate-bp (:rate-bp a))
            (add e :gov.transfer/amount-jpy (:amount-jpy a))
            (add e :gov.transfer/statutory-basis (:statutory-basis a))
            (add e :gov.transfer/per-yen? true)
            (add e :gov.transfer/sourcing :representative)]))
       (:allocations computed))
      (mapcat
       (fn [d]
         (let [e (str "alloc:" (name (:id d)))]
           [(add e :gov.alloc/from (:to-account computed))
            (add e :gov.alloc/to (:to d))
            (add e :gov.alloc/ja (:ja d))
            (add e :gov.alloc/cofog (:cofog d))
            (add e :gov.alloc/amount-jpy (:amount-jpy d))
            (add e :gov.alloc/sourcing :representative)]))
       (:distributions computed))
      (mapcat
       (fn [g]
         (let [e (str "grant:" (name (:id g)))]
           [(add e :gov.grant/from :general)
            (add e :gov.grant/to (:to g))
            (add e :gov.grant/ja (:ja g))
            (add e :gov.grant/amount-jpy (:amount-jpy g))
            (add e :gov.grant/statutory-basis (:statutory-basis g))
            (add e :gov.grant/per-yen? true)
            (add e :gov.grant/sourcing :representative)]))
       (:grants computed))))))

(defn report
  "国→地方 財政移転 summary: total 法定率繰入 (per-yen traceable), per-tax breakdown, and the
   reconciliation inflow vs distributed."
  [computed]
  {:to-account (:to-account computed)
   :total-inflow-jpy (:total-inflow computed)
   :distributed-jpy (reduce + 0 (map :amount-jpy (:distributions computed)))
   :residual (- (:total-inflow computed) (reduce + 0 (map :amount-jpy (:distributions computed))))
   :grants-total-jpy (:grants-total computed)
   :intergovernmental-total-jpy (+ (:total-inflow computed) (or (:grants-total computed) 0))
   :per-yen-traceable? true
   :grants (mapv (fn [g] {:id (:id g) :to (:to g) :amount-jpy (:amount-jpy g)}) (:grants computed))
   :allocations (mapv (fn [a] {:from-tax (:from-tax a) :rate-bp (:rate-bp a)
                               :amount-jpy (:amount-jpy a)}) (:allocations computed))
   :note (str "法定率分は 地方交付税法6条 で率が定まり 交付税特会 を経由するため per-yen 追跡 可。"
              "税全体の fungible 性 (源泉所得税等) はこのレイヤーで覆らない — 法定率分のみが traceable。")})

(defn -main [& args]
  (let [tax-reg (t/load-taxes nil)
        comp    (compute (load-transfers (first args)) tax-reg)
        r       (report comp)]
    (println "国 → 地方 法定率繰入 (地方交付税原資):")
    (doseq [a (:allocations r)]
      (println (format "  %s × %.1f%% = %d JPY" (name (:from-tax a)) (/ (:rate-bp a) 100.0) (:amount-jpy a))))
    (println (format "  合計 inflow = %d JPY (≈ %.1f兆) → 交付 %d JPY, residual %d, per-yen追跡可"
                     (:total-inflow-jpy r) (/ (:total-inflow-jpy r) 1.0e12)
                     (:distributed-jpy r) (:residual r)))))
