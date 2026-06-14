;; test_cofog_xcheck.clj — revenue-ledger COFOG codes are valid against matsurigoto's standard.
;; Run: bb test_cofog_xcheck.clj   (or: clojure -M test_cofog_xcheck.clj)   from methods/.
(ns root.danjo.methods.test-cofog-xcheck)

(load-file "cofog_xcheck.clj")
(alias 'x  'root.danjo.methods.cofog-xcheck)
(alias 'in 'root.danjo.methods.ingest)
(alias 'tr 'root.danjo.methods.transfers)
(alias 't  'root.danjo.methods.taxes)

(def checks (atom 0)) (def fails (atom 0))
(defn check [l p] (swap! checks inc) (if p (println "  ok  " l) (do (swap! fails inc) (println "  FAIL" l))))

(let [model (in/full-model)
      xfer  (tr/compute (tr/load-transfers "../data/jp-fiscal-transfers.edn")
                        (t/load-taxes "../data/jp-national-taxes.edn"))
      r (x/xcheck model xfer)]
  (check "matsurigoto standard has the full COFOG backbone (≥69 codes)" (>= (:canonical-count r) 69))
  (check "every revenue-ledger COFOG code is valid (cross-actor correctness)" (:all-valid? r))
  (check "no invalid codes" (empty? (:invalid r)))
  (check "expenditure spans multiple COFOG divisions (≥5)" (>= (:division-count r) 5))
  (check "10 (社会保障/social protection) division is spanned"
         (some #{"10"} (:divisions-used r)))

  ;; ── negative: a bogus COFOG code is caught ──
  (let [bad (update model :appropriations conj
                    {:program-code "X" :program-name "x" :account :general :cofog "99.9"
                     :fiscal-year 2024 :amount-jpy 1 :source-record-cids ["a" "b"]})
        rb (x/xcheck bad xfer)]
    (check "bogus COFOG code 99.9 is flagged invalid" (and (not (:all-valid? rb))
                                                           (some #{"99.9"} (:invalid rb))))))

(println (format "── cofog-xcheck: %d checks, %d failures ──" @checks @fails))
(when (pos? @fails) (System/exit 1))
