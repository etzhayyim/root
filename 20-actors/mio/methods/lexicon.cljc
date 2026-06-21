#!/usr/bin/env bb
;; 澪 mio — flow-improvement claim lexicon validator (the write-surface contract).
(ns mio.methods.lexicon
  "lexicon.cljc — validates a flow-improvement CLAIM against the
  com.etzhayyim.mio.flowClaim schema (kotoba/lexicon.flowClaim.edn).

  This is the TYPED CONTRACT for the suite's central write surface: each leg
  (撓/燠/樋/委) emits claims; mio verifies them. `validate-claim` returns a (possibly
  empty) list of human-readable error strings; `valid?` is the boolean. Pure /
  offline. The schema declares required fields, types, enums, ranges, non-blank, a
  const, and a :forbidden set (consumption-reward / currency / trade / person — the
  PoW→PoUF + map-not-market gates enforced at the interface)."
  (:require [clojure.string :as str]
            #?(:clj [clojure.edn :as edn])
            #?(:clj [clojure.java.io :as io])))

#?(:clj
   (defn load-schema [path]
     (with-open [r (io/reader path)] (edn/read-string (slurp r)))))

(defn- type-ok? [t v]
  (case t
    :keyword (keyword? v)
    :string (string? v)
    :number (number? v)
    :boolean (boolean? v)
    true))

(defn validate-claim
  "Return a vector of error strings for `claim` against `schema` (empty = valid)."
  [schema claim]
  (let [fields (:fields schema)
        required (:required schema)
        forbidden (set (:forbidden schema))]
    (vec
     (concat
      ;; required present
      (for [k required :when (not (contains? claim k))]
        (str "missing required field " k))
      ;; forbidden absent (the interface-level charter gates)
      (for [k (keys claim) :when (contains? forbidden k)]
        (str "forbidden field present: " k))
      ;; per-field constraints
      (mapcat
       (fn [[k spec]]
         (when (contains? claim k)
           (let [v (get claim k)]
             (cond-> []
               (not (type-ok? (:type spec) v))
               (conj (str k " must be of type " (:type spec)))
               (and (contains? spec :const) (not= v (:const spec)))
               (conj (str k " must equal " (:const spec)))
               (and (:enum spec) (not (contains? (:enum spec) v)))
               (conj (str k " value " v " not in enum"))
               (and (:enum-strings spec) (not (contains? (:enum-strings spec) v)))
               (conj (str k " value " (pr-str v) " not an allowed source-actor"))
               (and (:min spec) (number? v) (< v (:min spec)))
               (conj (str k " below min " (:min spec)))
               (and (:max spec) (number? v) (> v (:max spec)))
               (conj (str k " above max " (:max spec)))
               (and (:non-blank spec) (string? v) (str/blank? v))
               (conj (str k " must not be blank"))))))
       fields)))))

(defn valid? [schema claim] (empty? (validate-claim schema claim)))
