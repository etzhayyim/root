;; kudamori 管守 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).
;;
;; Projects the sewer graph into append-only kotoba Datoms [e a v tx op].
;;   GROUND (op :add, durable) — node / segment / robot node datoms + entry-gas reading
;;     + cleans 縁. This IS the Datom log.
;;   DERIVED (op :derived, transient :bond/is-transient true) — entry-permitted gate,
;;     route hops, debris removed, water effluent; computed on READ, NOT persisted
;;     (N1/G2 pattern, mirrors asobi/kuramori datom_emit).
;;
;; Pure Clojure, no deps → babashka-runnable AND kotoba-pywasm-portable.
;; Per ADR-2606142030 (kudamori R0).
(ns kudamori.methods.datom-emit
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [kudamori.methods.analyze :as az]))

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
  "Emit the sewer Datom log as an EDN string. `seed` is the loaded map,
   `res` the analyze/run result, `tx` the transaction number."
  [seed res tx]
  (let [L (atom [])
        add! (fn [s] (swap! L conj s))
        gated? (= :gated (:jetting res))]
    (add! ";; kudamori 管守 — GENERATED kotoba Datom log (ADR-2606142030). DO NOT hand-edit.")
    (add! ";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    (add! ";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (N1/G2).")
    (add! "[")
    ;; GROUND — nodes (manholes)
    (doseq [n (:nodes seed)]
      (add! (datom (:id n) :kuda.node/kind (:kind n) tx :add))
      (add! (datom (:id n) :kuda.node/access (boolean (:access n)) tx :add)))
    ;; GROUND — pipe segments (+ from/to 縁)
    (doseq [s (:segments seed)]
      (add! (datom (:id s) :kuda.pipe/id-mm (:id-mm s 0) tx :add))
      (add! (datom (:id s) :kuda.pipe/material (:material s) tx :add))
      (add! (datom (:id s) :kuda.pipe/length-m (double (:length-m s 0)) tx :add))
      (add! (datom (:id s) :kuda.pipe/blocked (boolean (:blocked? s)) tx :add))
      (add! (datom (:id s) :kuda.pipe/from (:from s) tx :add))
      (add! (datom (:id s) :kuda.pipe/to (:to s) tx :add)))
    ;; GROUND — robot (crawler)
    (let [r (:robot seed)]
      (add! (datom (:id r) :kuda.robot/kind (:kind r) tx :add))
      (add! (datom (:id r) :kuda.robot/od-mm (:od-mm r 0) tx :add)))
    ;; GROUND — entry-manhole gas reading (the safety record)
    (let [g (:gas-reading seed)]
      (add! (datom (:node g) :kuda.node/o2-pct (double (:o2-pct g 0)) tx :add))
      (add! (datom (:node g) :kuda.node/h2s-ppm (double (:h2s-ppm g 0)) tx :add))
      (add! (datom (:node g) :kuda.node/ch4-lel (double (:ch4-lel g 0)) tx :add))
      (add! (datom (:node g) :kuda.node/co-ppm (double (:co-ppm g 0)) tx :add)))
    ;; GROUND — cleans 縁 (robot → target segment), only when entry was permitted
    (when-not gated?
      (let [r (:robot seed)
            tgt (get-in res [:navigation :target])
            en (str "en." (:id r) ".cleans." tgt)]
        (add! (datom en :en/from (:id r) tx :add))
        (add! (datom en :en/to tgt tx :add))
        (add! (datom en :en/kind :cleans tx :add))))
    ;; DERIVED — transient readouts (computed on read; not durable)
    (add! ";; ── DERIVED readouts (transient; computed on read) ──")
    (let [fid (:id (:facility seed))]
      (add! (datom fid :bond/entry-permitted (get-in res [:entry :permitted?]) tx :derived))
      (if gated?
        (add! (datom fid :bond/jetting-gated true tx :derived))
        (do
          (add! (datom fid :bond/route-hops (get-in res [:navigation :hops]) tx :derived))
          (add! (datom fid :bond/debris-removed-m3
                       (double (get-in res [:jetting :debris-removed-m3])) tx :derived))
          (add! (datom fid :bond/effluent-l
                       (double (get-in res [:jetting :water :effluent-l])) tx :derived)))))
    (add! "]")
    (str (str/join "\n" @L) "\n")))

(defn -main [& args]
  (let [path (or (first args) "20-actors/kudamori/data/network.edn")
        seed (az/load-seed path)
        res (az/run seed)]
    (print (emit seed res 1))
    (flush)))
