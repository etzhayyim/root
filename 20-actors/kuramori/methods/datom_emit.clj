;; kuramori 倉守 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).
;;
;; Projects the warehouse graph into append-only kotoba Datoms [e a v tx op].
;;   GROUND (op :add, durable) — zone / slot / sku / robot node datoms + placement 縁.
;;     This IS the Datom log.
;;   DERIVED (op :derived, transient :bond/is-transient true) — slotting weighted-travel,
;;     dispatch makespan, battery gate; computed on READ, NOT persisted (N1/G2 pattern,
;;     mirrors asobi/datom_emit).
;;
;; Pure Clojure, no deps → babashka-runnable AND kotoba-pywasm-portable.
;; Per ADR-2606142000 (kuramori R0).
(ns kuramori.methods.datom-emit
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [kuramori.methods.analyze :as az]))

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
  "Emit the warehouse Datom log as an EDN string. `seed` is the loaded map,
   `res` the analyze/run result, `tx` the transaction number."
  [seed res tx]
  (let [L (atom [])
        add! (fn [s] (swap! L conj s))]
    (add! ";; kuramori 倉守 — GENERATED kotoba Datom log (ADR-2606142000). DO NOT hand-edit.")
    (add! ";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    (add! ";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (N1/G2).")
    (add! "[")
    ;; GROUND — zones
    (doseq [z (:zones seed)]
      (add! (datom (:id z) :wh.zone/kind (:kind z) tx :add)))
    ;; GROUND — slots (+ slot-in-zone 縁)
    (doseq [s (:slots seed)]
      (add! (datom (:id s) :wh.slot/dist-from-face (double (:dist-from-face s 0)) tx :add))
      (add! (datom (:id s) :wh.slot/max-kg (:max-kg s 0) tx :add))
      (add! (datom (:id s) :wh.slot/in-zone (:zone s) tx :add)))
    ;; GROUND — SKUs (+ ABC class)
    (doseq [k (:skus seed)]
      (add! (datom (:id k) :wh.sku/velocity (:velocity k 0) tx :add))
      (add! (datom (:id k) :wh.sku/weight-kg (:weight-kg k 0) tx :add))
      (add! (datom (:id k) :wh.sku/abc (get-in res [:abc (:id k)]) tx :add)))
    ;; GROUND — robots (fleet)
    (doseq [r (:fleet seed)]
      (add! (datom (:id r) :wh.robot/kind (:kind r) tx :add)))
    ;; GROUND — placement 縁 (sku → slot)
    (doseq [[sku-id slot-id] (get-in res [:slotting :placement])]
      (add! (datom (str "en." sku-id ".slotted-in." slot-id) :en/from sku-id tx :add))
      (add! (datom (str "en." sku-id ".slotted-in." slot-id) :en/to slot-id tx :add))
      (add! (datom (str "en." sku-id ".slotted-in." slot-id) :en/kind :slotted-in tx :add)))
    ;; DERIVED — transient readouts (computed on read; not durable)
    (add! ";; ── DERIVED readouts (transient; computed on read) ──")
    (add! (datom (:id (:facility seed)) :bond/weighted-travel
                 (double (get-in res [:slotting :weighted-travel])) tx :derived))
    (add! (datom (:id (:facility seed)) :bond/dispatch-makespan
                 (double (get-in res [:dispatch :makespan])) tx :derived))
    (add! (datom (:id (:facility seed)) :bond/charge-needed
                 (get-in res [:battery :charge-needed]) tx :derived))
    (add! "]")
    (str (str/join "\n" @L) "\n")))

(defn -main [& args]
  (let [path (or (first args) "20-actors/kuramori/data/warehouse.edn")
        seed (az/load-seed path)
        res (az/run seed)]
    (print (emit seed res 1))
    (flush)))
