;; cofog_xcheck.clj — 弾正 (danjo) revenue-ledger × matsurigoto COFOG cross-check. ADR-2605301600.
;;
;; Cross-actor CORRECTNESS + coverage measurement (the uchiwake `crosscheck` pattern): validates
;; that every COFOG code the revenue-ledger assigns (一般会計 主要経費 / 復興特会 歳出 / 交付税交付)
;; is a REAL code in matsurigoto's canonical COFOG standard (the UN COFOG backbone, 10 divisions /
;; 69 groups, ADR-2606062300), and reports which COFOG divisions our expenditure spans.
;;
;; Reads matsurigoto's cofog-standard.kotoba.edn by regex over the raw text (robust to any
;; kotoba-edn reader tags). Pure + JVM stdlib; bb / clojure.
(ns root.danjo.methods.cofog-xcheck
  (:require [clojure.string :as str]
            [clojure.java.io :as io]))

(load-file "transfers.clj")        ; loads taxes + revenue_ledger
(load-file "ingest.clj")
(alias 'tr 'root.danjo.methods.transfers)
(alias 't  'root.danjo.methods.taxes)
(alias 'in 'root.danjo.methods.ingest)

(def cofog-standard-path "../../matsurigoto/data/cofog-standard.kotoba.edn")

(defn canonical-codes
  "The set of valid COFOG codes from matsurigoto's standard (regex over :cofog/code \"..\")."
  ([] (canonical-codes cofog-standard-path))
  ([path]
   (let [f (io/file path)
         f (if (.exists f) f (io/file "20-actors/matsurigoto/data/cofog-standard.kotoba.edn"))]
     (->> (re-seq #":cofog/code \"([0-9.]+)\"" (slurp f)) (map second) set))))

(defn used-codes
  "Every non-blank COFOG code the revenue-ledger assigns across outlays + appropriations +
   inter-governmental distributions."
  [model xfer]
  (->> (concat (map :cofog (:outlays model))
               (map :cofog (:appropriations model))
               (map :cofog (:distributions xfer)))
       (remove (fn [c] (or (nil? c) (str/blank? (str c)))))
       (map str)
       set))

(defn xcheck
  "Cross-check used COFOG codes against the canonical standard. Returns coverage + any invalids."
  [model xfer]
  (let [canon (canonical-codes)
        used  (used-codes model xfer)
        invalid (remove canon used)
        divisions-used (set (map #(subs % 0 2) used))
        canon-divisions (set (filter #(= 2 (count %)) canon))]
    {:canonical-count (count canon)
     :used used
     :invalid (vec invalid)
     :all-valid? (empty? invalid)
     :divisions-used (sort divisions-used)
     :division-count (count divisions-used)
     :canonical-division-count (count canon-divisions)
     :division-coverage (if (zero? (count canon-divisions)) 0.0
                            (double (/ (count divisions-used) (count canon-divisions))))}))

(defn -main [& _]
  (let [model (in/full-model)
        xfer  (tr/compute (tr/load-transfers "../data/jp-fiscal-transfers.edn")
                          (t/load-taxes "../data/jp-national-taxes.edn"))
        r (xcheck model xfer)]
    (println "COFOG cross-check vs matsurigoto (" (:canonical-count r) "canonical codes):")
    (println "  used codes:" (sort (:used r)))
    (println "  all valid?" (:all-valid? r) (when (seq (:invalid r)) (str "INVALID: " (:invalid r))))
    (println (format "  COFOG divisions spanned: %d/%d (%.0f%%) — %s"
                     (:division-count r) (:canonical-division-count r)
                     (* 100 (:division-coverage r)) (str/join "," (:divisions-used r))))))
