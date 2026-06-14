#!/usr/bin/env bb
;; Working Clojure port of methods/uchiwake_edn.py (replaces the failed unit_refactor stub).
(ns uchiwake.methods.uchiwake-edn
  "uchiwake 内訳 — shared EDN reader + datom classifier + GTIN helpers (ADR-2606081800).

  The Python source ships a hand-rolled minimal EDN reader because Python has no EDN. Clojure
  reads EDN natively (`clojure.edn/read-string`), so the reader collapses to that — keyword
  keys (:product/id …) and keyword values (:metal, :representative) are read as real keywords
  (the Python port kept them as \":ns/name\" strings). The classifier + GTIN check-digit
  validation are ported faithfully so the analysis is byte-for-byte equivalent."
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(defn load-edn [path] (edn/read-string (slurp (io/file path))))

(defn classify
  "Bucket a flat datom vector into uchiwake entity kinds. products/parts/materials are id→node
  maps; the rest are vectors (insertion order preserved)."
  [rows]
  (reduce
   (fn [out r]
     (if-not (map? r)
       out
       (cond
         (:product/id r)          (assoc-in out [:products (:product/id r)] r)
         (:part/id r)             (assoc-in out [:parts (:part/id r)] r)
         (:material/id r)         (assoc-in out [:materials (:material/id r)] r)
         (:bom.edge/id r)         (update out :bom conj r)
         (:process.step/id r)     (update out :process conj r)
         (:logistics.leg/id r)    (update out :logistics conj r)
         (:design.ref/id r)       (update out :design conj r)
         (:company.ownership/id r) (update out :ownership conj r)
         :else out)))
   {:products {} :parts {} :materials {}
    :bom [] :process [] :logistics [] :design [] :ownership []}
   rows))

;; ── GTIN helpers ──────────────────────────────────────────────────────────────
(defn- digits [gtin] (apply str (filter #(Character/isDigit ^char %) (str gtin))))

(defn normalize-gtin
  "Left-zero-pad any GTIN-8/12/13 to the canonical 14-digit GTIN-14."
  [gtin]
  (let [d (digits gtin)]
    (str (apply str (repeat (max 0 (- 14 (count d))) \0)) d)))

(defn gtin-check-digit-ok?
  "Validate the GS1 mod-10 check digit of a GTIN (length 8/12/13/14)."
  [gtin]
  (let [d (digits gtin)]
    (if-not (#{8 12 13 14} (count d))
      false
      (let [body (butlast d)
            check (Character/digit ^char (last d) 10)
            total (reduce + (map-indexed
                             (fn [i ch] (* (Character/digit ^char ch 10) (if (even? i) 3 1)))
                             (reverse body)))]
        (= (mod (- 10 (mod total 10)) 10) check)))))
