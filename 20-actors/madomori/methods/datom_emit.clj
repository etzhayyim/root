;; madomori 窓守 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).
;;
;; Projects the building-façade graph into append-only kotoba Datoms [e a v tx op].
;;   GROUND (op :add, durable) — face / pane-grid / robot node datoms + anchor 縁.
;;     This IS the Datom log.
;;   DERIVED (op :derived, transient :bond/is-transient true) — coverage length,
;;     consumable budget, sway amplitude, permit + adhesion-safe gate readouts;
;;     computed on READ, NOT persisted (N1/G2 pattern, mirrors asobi/kuramori).
;;
;; G3 (privacy-by-construction) is STRUCTURAL here: no imagery / interior /
;; person / biometric attribute is emittable. The robot's only imagery datom is
;; `:mado.robot/imagery-on-device` = true — imagery off-device is unrepresentable.
;;
;; Pure Clojure, no deps → babashka-runnable AND kotoba-pywasm-portable.
;; Per ADR-2606142020 (madomori R0).
(ns madomori.methods.datom-emit
  (:require [clojure.string :as str]
            [madomori.methods.analyze :as az]))

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
  "Emit the façade Datom log as an EDN string. `seed` is the loaded map,
   `res` the analyze/run result, `tx` the transaction number."
  [seed res tx]
  (let [L (atom [])
        add! (fn [s] (swap! L conj s))
        face (:face seed)
        robot (:robot seed)]
    (add! ";; madomori 窓守 — GENERATED kotoba Datom log (ADR-2606142020). DO NOT hand-edit.")
    (add! ";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    (add! ";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (N1/G2).")
    (add! ";; G3 STRUCTURAL: only the on-device imagery flag is emittable.")
    (add! "[")
    ;; GROUND — the building face
    (add! (datom (:id face) :mado.face/surface (:surface face) tx :add))
    (add! (datom (:id face) :mado.face/height-m (double (:height-m face 0)) tx :add))
    (add! (datom (:id face) :mado.face/rows (:rows face 0) tx :add))
    (add! (datom (:id face) :mado.face/cols (:cols face 0) tx :add))
    (add! (datom (:id face) :mado.face/panes (* (:rows face 0) (:cols face 0)) tx :add))
    ;; GROUND — panes as a grid attribute (one course-count per face; per-pane nodes
    ;;          are not exploded in R0 — the coverage plan derives them on read)
    (add! (datom (:id face) :mado.pane/h-m (double (:pane-h-m face 0)) tx :add))
    (add! (datom (:id face) :mado.pane/w-m (double (:pane-w-m face 0)) tx :add))
    ;; GROUND — robot envelope
    (add! (datom (:id robot) :mado.robot/mode (:mode robot) tx :add))
    (add! (datom (:id robot) :mado.robot/mass-kg (double (:mass-kg robot 0)) tx :add))
    (add! (datom (:id robot) :mado.robot/suction-force-n (double (:suction-force-n robot 0)) tx :add))
    (add! (datom (:id robot) :mado.robot/required-fos (double (:required-fos robot 0)) tx :add))
    ;; G3 — the ONLY imagery datom; imagery off-device is unrepresentable
    (add! (datom (:id robot) :mado.robot/imagery-on-device true tx :add))
    ;; GROUND — anchor 縁 (face → anchor; ≥2 independent = fall-arrest redundancy, G5)
    (doseq [a (:anchors seed)]
      (add! (datom (str "en." (:id face) ".anchored-by." (:id a)) :en/from (:id face) tx :add))
      (add! (datom (str "en." (:id face) ".anchored-by." (:id a)) :en/to (:id a) tx :add))
      (add! (datom (str "en." (:id face) ".anchored-by." (:id a)) :en/kind :anchored-by tx :add))
      (add! (datom (:id a) :mado.anchor/independent (boolean (:independent a)) tx :add)))
    ;; DERIVED — transient readouts (computed on read; not durable)
    (add! ";; ── DERIVED readouts (transient; computed on read) ──")
    (add! (datom (:id face) :bond/coverage-complete
                 (boolean (get-in res [:coverage :coverage :complete?])) tx :derived))
    (add! (datom (:id face) :bond/path-length-m
                 (double (get-in res [:coverage :length-m])) tx :derived))
    (add! (datom (:id face) :bond/water-l
                 (double (get-in res [:coverage :budget :water-l])) tx :derived))
    (add! (datom (:id face) :bond/agent-ml
                 (double (get-in res [:coverage :budget :agent-ml])) tx :derived))
    (add! (datom (:id face) :bond/sway-amplitude-m
                 (double (get-in res [:envelope :sway-amplitude-m])) tx :derived))
    (add! (datom (:id face) :bond/wind-permitted
                 (boolean (get-in res [:envelope :permitted?])) tx :derived))
    (add! (datom (:id robot) :bond/adhesion-fos
                 (double (get-in res [:adhesion :factor-of-safety])) tx :derived))
    (add! (datom (:id robot) :bond/adhesion-safe
                 (boolean (get-in res [:adhesion :safe?])) tx :derived))
    (add! (datom (:id (:facility seed)) :bond/go (boolean (:go? res)) tx :derived))
    (add! "]")
    (str (str/join "\n" @L) "\n")))

(defn -main [& args]
  (let [path (or (first args) "20-actors/madomori/data/facade.edn")
        seed (az/load-seed path)
        res (az/run seed)]
    (print (emit seed res 1))
    (flush)))
