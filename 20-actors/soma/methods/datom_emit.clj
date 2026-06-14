;; soma 杣 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).
;;
;; Projects the forest-stand graph into append-only kotoba Datoms [e a v tx op].
;;   GROUND (op :add, durable) — stand / tree / exclusion node datoms + felled 縁.
;;     This IS the Datom log.
;;   DERIVED (op :derived, transient :bond/is-transient true) — bucked total value,
;;     extraction max-grade/feasibility, refusal/unsafe counts; computed on READ,
;;     NOT persisted (N1/G2 pattern, mirrors asobi/kuramori datom_emit).
;;
;; Pure Clojure, no deps → babashka-runnable AND kotoba-pywasm-portable.
;; Per ADR-2606142010 (soma R0).
(ns soma.methods.datom-emit
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [soma.methods.analyze :as az]))

(defn fmt
  "Format a value as an EDN Datom field: keywords bare, strings quoted, bools/nil literal."
  [v]
  (cond
    (true? v) "true"
    (false? v) "false"
    (nil? v) "nil"
    (keyword? v) (str v)
    (string? v) (if (str/starts-with? v ":")
                  v
                  (str \" (str/escape v {\\ "\\\\" \" "\\\""}) \"))
    (float? v) (format "%g" v)
    :else (str v)))

(defn datom [e a v tx op]
  (str "[" (fmt e) " " (str a) " " (fmt v) " " tx " " (str op) "]"))

(defn emit
  "Emit the forest-stand Datom log as an EDN string. `seed` is the loaded map,
   `res` the analyze/run result, `tx` the transaction number."
  [seed res tx]
  (let [L (atom [])
        add! (fn [s] (swap! L conj s))
        felled? (set (map :tree (:fells res)))
        refused? (set (map :tree (:refused res)))]
    (add! ";; soma 杣 — GENERATED kotoba Datom log (ADR-2606142010). DO NOT hand-edit.")
    (add! ";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    (add! ";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (N1/G2).")
    (add! "[")
    ;; GROUND — stand
    (let [st (:stand seed)]
      (add! (datom (:id st) :soma.stand/slope-pct (double (:slope-pct st 0.0)) tx :add))
      (add! (datom (:id st) :soma.stand/soil (:soil st :firm) tx :add)))
    ;; GROUND — trees (+ protected / no-cut flags)
    (doseq [t (:trees seed)]
      (add! (datom (:id t) :soma.tree/species (:species t) tx :add))
      (add! (datom (:id t) :soma.tree/diameter-m (double (:diameter-m t 0.0)) tx :add))
      (add! (datom (:id t) :soma.tree/height-m (double (:height-m t 0.0)) tx :add))
      (add! (datom (:id t) :soma.tree/lean-deg (double (:lean-deg t 0.0)) tx :add))
      (add! (datom (:id t) :soma.tree/protected (boolean (or (:protected t) (:no-cut t))) tx :add)))
    ;; GROUND — exclusions (humans/road/watercourse, the fall-zone keep-outs)
    (doseq [x (:exclusions seed)]
      (add! (datom (:id x) :soma.exclusion/kind (:kind x) tx :add)))
    ;; GROUND — forwarder
    (let [f (:forwarder seed)]
      (add! (datom (:id f) :soma.forwarder/max-grade-pct (double (:max-grade-pct f 0.0)) tx :add)))
    ;; GROUND — felled 縁 (tree → log, with fall azimuth + hinge width)
    (doseq [fl (:fells res)]
      (let [en (str "en." (:tree fl) ".felled")]
        (add! (datom en :en/from (:tree fl) tx :add))
        (add! (datom en :en/kind :felled tx :add))
        (add! (datom en :soma.log/fall-az (double (:fall-az fl)) tx :add))
        (add! (datom en :soma.log/hinge-m (double (:hinge-m fl)) tx :add))
        (add! (datom en :soma.log/value (double (get-in fl [:buck :value] 0.0)) tx :add))))
    ;; GROUND — refusal 縁 (protected/no-cut trees, G7 — recorded, never felled)
    (doseq [r (:refused res)]
      (let [en (str "en." (:tree r) ".refused")]
        (add! (datom en :en/from (:tree r) tx :add))
        (add! (datom en :en/kind :refused-protected tx :add))))
    ;; DERIVED — transient readouts (computed on read; not durable)
    (add! ";; ── DERIVED readouts (transient; computed on read) ──")
    (let [sid (get-in seed [:stand :id])]
      (add! (datom sid :bond/total-value (double (:total-value res)) tx :derived))
      (add! (datom sid :bond/n-felled (count felled?) tx :derived))
      (add! (datom sid :bond/n-refused (count refused?) tx :derived))
      (add! (datom sid :bond/n-unsafe (count (:unsafe res)) tx :derived))
      (add! (datom sid :bond/extraction-feasible
                   (boolean (get-in res [:extraction :feasible])) tx :derived))
      (add! (datom sid :bond/extraction-max-grade
                   (double (get-in res [:extraction :max-grade-pct] 0.0)) tx :derived)))
    (add! "]")
    (str (str/join "\n" @L) "\n")))

(defn -main [& args]
  (let [path (or (first args) "20-actors/soma/data/stand.edn")
        seed (az/load-seed path)
        res (az/run seed)]
    (print (emit seed res 1))
    (flush)))
