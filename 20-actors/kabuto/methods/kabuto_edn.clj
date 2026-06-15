#!/usr/bin/env bb
;; Working Clojure port of methods/kabuto_edn.py.
(ns kabuto.methods.kabuto-edn
  "kabuto 兜 — shared EDN reader + datom classifier (ADR-2606022000).

  The Python source ships a hand-rolled minimal EDN tokenizer (Python has no EDN). Clojure reads
  EDN natively (clojure.edn) — keyword keys/values are real keywords. The classifier buckets the
  flat datom vector into company / address / contact / supply-edge / process entities."
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]))

(defn load-edn [path] (edn/read-string (slurp (io/file path))))

(defn classify
  "→ {:companies {id→rec} :addresses [] :contacts [] :edges [] :processes []}."
  [rows]
  (reduce
   (fn [out r]
     (if-not (map? r)
       out
       (cond
         (:company/id r)         (assoc-in out [:companies (:company/id r)] r)
         (:company.address/id r) (update out :addresses conj r)
         (:company.contact/id r) (update out :contacts conj r)
         (:supply.edge/id r)     (update out :edges conj r)
         (:company.process/id r) (update out :processes conj r)
         :else out)))
   {:companies {} :addresses [] :contacts [] :edges [] :processes []}
   rows))
