;; ported from 20-actors/hakoniwa/methods/datom_emit.py — real port replacing the unit_refactor
;; stage-0 "TODO: port-failed" stubs. NS fixed root.hakoniwa.* → hakoniwa.* (20-actors source root).
(ns hakoniwa.methods.datom-emit
  "datom_emit.py — hakoniwa 箱庭 kotoba Datom-log emitter (canonical EAVT state). 1:1 Clojure port.
  ADR-2605312345 + 2606111500.

  Projects the 箱庭 world graph into append-only kotoba Datoms [e a v tx op]. GROUND (op :add) =
  durable world (every persona ground datom carries :persona/synthetic true, G1). DERIVED
  (:bond/is-transient) = the outcome DISTRIBUTION quantiles, computed on read; there is NO
  :forecast/point datom (G2).

  House style: ':kw' strings, string-keyed maps, %g floats. The Python `__main__` file-writer is
  omitted (emit is the API)."
  (:require [clojure.string :as str]))

(def ^:private node-attrs
  [":sim/kind" ":sim/label" ":sim/sourcing" ":entity/public-ref"
   ":persona/synthetic" ":persona/cohort" ":persona/susceptibility"
   ":persona/initial-stance" ":persona/weight"
   ":signal/push" ":signal/at-step"
   ":outcome/measures" ":outcome/statistic" ":outcome/use"])
(def ^:private edge-attrs [":en/from" ":en/to" ":en/kind" ":en/weight" ":en/sourcing"])

(defn- fmt-g
  "Python-`%g`-equivalent float formatting."
  [^double v]
  (if (and (== v (Math/rint v)) (not (Double/isInfinite v)) (<= (Math/abs v) 1.0e15))
    (str (long v))
    (let [s (format "%.6g" v)]
      (if (str/includes? s "e")
        (let [[m e] (str/split s #"e")
              m (if (str/includes? m ".") (str/replace (str/replace m #"0+$" "") #"\.$" "") m)]
          (str m "e" e))
        (if (str/includes? s ".")
          (str/replace (str/replace s #"0+$" "") #"\.$" "")
          s)))))

(defn- fmt [v]
  (cond
    (true? v) "true"
    (false? v) "false"
    (nil? v) "nil"
    (and (string? v) (str/starts-with? v ":")) v
    (string? v) (str "\"" (-> v (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")) "\"")
    (and (number? v) (not (integer? v))) (fmt-g (double v))
    :else (str v)))

(defn- lstrip-colon [^String s] (str/replace s #"^:+" ""))

(defn emit
  "Flatten the box + distribution into the kotoba Datom-log EDN text (mirrors emit)."
  ([nodes edges dist meta] (emit nodes edges dist meta 1))
  ([nodes edges dist meta tx]
   (let [L (transient [])]
     (conj! L ";; hakoniwa 箱庭 — GENERATED kotoba Datom log (ADR-2606111500). DO NOT hand-edit.")
     (conj! L ";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
     (conj! L ";; GROUND op :add = durable world. DERIVED :bond/is-transient = distribution on read (N1/G2).")
     (conj! L ";; G1: every :persona is SYNTHETIC (:persona/synthetic true) — the box holds no real people.")
     (conj! L "[")
     ;; ── GROUND: node datoms
     (doseq [nid (keys nodes)]
       (let [n (get nodes nid)]
         (doseq [a node-attrs]
           (when (and (contains? n a) (some? (get n a)))
             (conj! L (str "[" (fmt nid) " " a " " (fmt (get n a)) " " tx " :add]"))))))
     ;; ── GROUND: edge datoms (content-stable edge id)
     (doseq [e edges]
       (let [eid (str "en." (get e ":en/from") "." (lstrip-colon (get e ":en/kind")) "." (get e ":en/to"))]
         (doseq [a edge-attrs]
           (when (and (contains? e a) (some? (get e a)))
             (conj! L (str "[" (fmt eid) " " a " " (fmt (get e a)) " " tx " :add]"))))))
     ;; ── GROUND: run config
     (let [run "run.hakoniwa"]
       (doseq [[a v] [[":run/steps" (get meta "steps")] [":run/replicas" (get meta "replicas")]
                      [":run/seed" (get meta "seed")] [":run/jitter" (get meta "jitter")]
                      [":run/kernel" ":friedkin-johnsen"]]]
         (conj! L (str "[" (fmt run) " " a " " (fmt v) " " tx " :add]"))))
     ;; ── DERIVED (transient — the DISTRIBUTION; N1/G2). NO point datom.
     (conj! L ";; ── DERIVED outcome distribution (transient; computed on read from the ensemble) ──")
     (doseq [[qk qv] (get dist "quantiles")]
       (conj! L (str "[outcome.adoption :bond/distribution-" (lstrip-colon qk) " " (fmt-g (double qv)) " " tx " :derived] "
                     ";; :bond/is-transient true")))
     (conj! L (str "[outcome.adoption :bond/distribution-mean " (fmt-g (double (get dist "mean"))) " " tx " :derived] "
                   ";; :bond/is-transient true"))
     (conj! L (str "[outcome.adoption :bond/point-asserted false " tx " :derived] "
                   ";; G2: distribution-only — never a point"))
     (conj! L "]")
     (str (str/join "\n" (persistent! L)) "\n"))))
