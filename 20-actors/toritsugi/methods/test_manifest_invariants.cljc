(ns toritsugi.methods.test-manifest-invariants
  "toritsugi — manifest invariants (ported from 70-tools/scripts/audit/test_toritsugi_invariants.py; reads manifest.edn blob, jsonld retired)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str] [clojure.edn :as edn]))
(def ^:private here (.getParentFile (java.io.File. ^String *file*)))
(def ^:private actor-dir (.getParentFile here))
(def ^:private root (.. actor-dir getParentFile getParentFile))
(def ^:private lexdir (java.io.File. root "00-contracts/lexicons/com/etzhayyim/toritsugi"))
(def ^:private cells-dir (java.io.File. root "20-actors/kotodama/cells"))
(defn- manifest [] (:actor/manifest (edn/read-string (slurp (java.io.File. actor-dir "manifest.edn")))))
(deftest manifest-gates-namespaces-cells
  (let [m (manifest)
        gates (get-in m ["constitutionalGates" "gates"])]
    (is (= (count gates) 15) "ADR-2605312030 pins 15 gates G1..G15")
    (is (= (set (keys gates)) (set (map #(str "G" %) (range 1 16)))) "gates are exactly G1..G15")
    (let [ns (get m "lexiconNamespaces")]
      (is (= (count ns) 6) "6 lexiconNamespaces")
      (doseq [n ns]
        (let [leaf (last (str/split n #"\."))]
          (is (.exists (java.io.File. lexdir (str leaf ".json"))) (str "missing lexicon: " leaf)))))
    (let [cells (get m "cells")]
      (is (= (count cells) 7) "7 cells")
      (doseq [c cells]
        (is (str/starts-with? (get c "module") "kotodama.cells.toritsugi_") (get c "module"))))))
;; NOTE: the Python original also asserted <module>/cell.py exists on disk — obsolete
;; (the toritsugi cells were ported off cell.py to cljc), already failing in the Python
;; audit suite, so it is dropped here (not a regression).
(defn -main [& _] (let [r (run-tests 'toritsugi.methods.test-manifest-invariants)] (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1))))
