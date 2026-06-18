;; tax_assess.clj — matsurigoto 政 `tax-assess` module (R0 reference implementation).
;;
;; Clojure port of tax_assess.py (ADR-2606062300), Wave 1 of the clj-native migration
;; (ADR-2606142300) — continuing matsurigoto after the tax-collect 源泉徴収 module (#1743).
;; A PURE-FUNCTION tax-assessment engine for tax.income.file / tax.corporate.file /
;; tax.vat.file: income/corporate tax is a progressive marginal-bracket computation; VAT is
;; output−input. The bracket table is the localized (G2 spec-derived) jurisdiction parameter,
;; so one universal algorithm serves every polity.
;;
;; Reference liabilities are reproduced EXACTLY against the published JP 速算表 (see
;; test_tax_assess.clj) — byte-equivalent with tax_assess.py on the JP reference points.
;;
;;   G1 no-operator-master-key : server-held-authority is false and this module SIGNS NOTHING;
;;                               the filing receipt is UNSIGNED (the governing organ signs).
;;   G2 spec-derived-only      : the algorithm follows public tax law; rate tables cite source.
;;   G3 authority-bearing      : the caller passes :operated-by; this module never asserts it.
;;
;; Float rounding mirrors Python round(x, n) (half-to-even) via BigDecimal/HALF_EVEN; the JP
;; reference points are clean (no .xx5 boundary), so parity is exact. clojure.edn reads the
;; per-jurisdiction rate tables natively. stdlib only, no network.
(ns matsurigoto.methods.modules.tax-assess
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io])
  (:import [java.math BigDecimal RoundingMode]))

;; G1: this module holds NO signing authority. It computes; the governing organ signs.
(def server-held-authority false)

;; ── Reference marginal-bracket rate tables (the localized G2 parameter) ──
;; Each table: ascending [[lower-inclusive marginal-rate] …]; the last bracket extends to +∞.
(def embedded-rate-tables
  {"JPN.income"    {:currency "JPY"
                    :source   "所得税法 / 国税庁 速算表 (:representative)"
                    :brackets [[0 0.05] [1950000 0.10] [3300000 0.20] [6950000 0.23]
                               [9000000 0.33] [18000000 0.40] [40000000 0.45]]}
   "FLAT20.income" {:currency "XXX"
                    :source   "illustrative flat 20% (:representative)"
                    :brackets [[0 0.20]]}})

(defonce rate-tables (atom embedded-rate-tables))

(defn load-rate-tables!
  "R1.D: merge per-jurisdiction rate tables from data/rates/*.edn into `rate-tables`. Keeps the
   universal algorithm; the bracket table is the localized (G2) parameter. Returns the count
   loaded. Robust: a missing dir / parse error leaves the embedded tables intact."
  ([] (load-rate-tables! "20-actors/matsurigoto/data/rates"))
  ([dir]
   (let [d (io/file dir)]
     (if-not (.exists d)
       0
       (reduce
        (fn [n f]
          (try
            (let [doc (edn/read-string (slurp f))]
              (doseq [[k tbl] doc]
                (swap! rate-tables assoc k
                       {:currency (get tbl :currency "XXX")
                        :source   (get tbl :source "")
                        :brackets (mapv (fn [b] [(nth b 0) (nth b 1)]) (:brackets tbl))}))
              (+ n (count doc)))
            (catch Exception _ n)))
        0
        (->> (.listFiles d) (filter #(.endsWith (.getName %) ".edn")) (sort-by #(.getName %))))))))

;; ── Python round(x, n) — half-to-even (banker's). JP reference points are clean. ──
(defn- round-n [x scale]
  (.doubleValue (.setScale (BigDecimal/valueOf (double x)) (int scale) RoundingMode/HALF_EVEN)))

(defn assess-income-tax
  "Progressive marginal-bracket assessment. Pure. `brackets` = ascending [[lower rate] …]; the
   top bracket → +∞. Returns the per-bracket breakdown, total liability, and effective rate."
  [taxable-income brackets]
  (when (< taxable-income 0) (throw (ex-info "taxable_income must be >= 0" {:taxable-income taxable-income})))
  (when (empty? brackets) (throw (ex-info "brackets must be non-empty" {})))
  (let [n     (count brackets)
        lines (->> brackets
                   (map-indexed
                    (fn [i [lower rate]]
                      (let [upper (if (< (inc i) n) (first (nth brackets (inc i))) Double/POSITIVE_INFINITY)]
                        (when (> taxable-income lower)
                          (let [amount (- (min taxable-income upper) lower)]
                            {:lower lower :upper upper :rate rate
                             :taxable-in-bracket amount :tax-in-bracket (* amount rate)})))))
                   (remove nil?)
                   vec)
        total (reduce + 0.0 (map :tax-in-bracket lines))]
    {:taxable-income taxable-income
     :liability      (round-n total 2)
     :effective-rate (if (pos? taxable-income) (round-n (/ total taxable-income) 6) 0.0)
     :brackets       (mapv #(update % :tax-in-bracket round-n 2) lines)}))

(defn- unsigned-receipt
  "A filing-receipt SKELETON. G1: unsigned — the governing organ signs with ITS key. `:proof`
   is explicitly nil and `:server-held-authority` is false so a reviewer can see it never signs."
  [amount currency]
  {:assessed-amount       amount
   :currency              currency
   :proof                 nil                       ; G1 — this module signs nothing
   :server-held-authority server-held-authority     ; false
   :status                "assessed-unsigned"})

(defn assess-from-return
  "Assess income tax from a return-shaped input (gross − deductions → taxable). `table-key`
   selects a rate-tables entry (the localized G2 param)."
  [gross-income deductions table-key]
  (when-not (contains? @rate-tables table-key)
    (throw (ex-info (str "unknown rate table " (pr-str table-key)) {:table-key table-key})))
  (let [table   (@rate-tables table-key)
        taxable (max 0.0 (- gross-income deductions))
        out     (assess-income-tax taxable (:brackets table))]
    (assoc out
           :currency          (:currency table)
           :rate-table        table-key
           :rate-table-source (:source table)
           :receipt           (unsigned-receipt (:liability out) (:currency table)))))

(defn assess-vat
  "Net VAT = output VAT − input VAT (EN 16931 / SAF-T aggregates). Pure. Negative net → refund."
  ([output-vat input-vat] (assess-vat output-vat input-vat "XXX"))
  ([output-vat input-vat currency]
   (let [net (round-n (- output-vat input-vat) 2)]
     {:output-vat  output-vat
      :input-vat   input-vat
      :net-vat-due (if (> net 0) net 0.0)
      :refund-due  (if (< net 0) (- net) 0.0)
      :currency    currency
      :receipt     (unsigned-receipt (if (> net 0) net 0.0) currency)})))

(defn solve
  "Cell entry — R0 is reference-only; a LIVE filing against a real government record is
   Council+operator gated."
  [& _]
  (throw (ex-info (str "tax-assess R0: reference assessment only. Live filing against a "
                       "government record is Council+operator gated (principal A: Council Lv7+; "
                       "principal B: adopting state).")
                  {:gated true})))

;; R1.D: load per-jurisdiction rate tables at namespace load (embedded JPN/FLAT20 stay as fallback).
(load-rate-tables!)
