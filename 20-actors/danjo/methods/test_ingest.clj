;; test_ingest.clj — standalone suite for the danjo revenue-corpus ingest (G3 passive-only).
;; Run: bb test_ingest.clj   (or: clojure -M test_ingest.clj)   from methods/.
(ns root.danjo.methods.test-ingest)

(load-file "revenue_ledger.clj")
(load-file "ingest.clj")
(alias 'rl 'root.danjo.methods.revenue-ledger)
(alias 'in 'root.danjo.methods.ingest)

(def corpus-path "../data/gov-revenue-corpus.jp.edn")
(def checks (atom 0)) (def fails (atom 0))
(defn check [l p] (swap! checks inc) (if p (println "  ok  " l) (do (swap! fails inc) (println "  FAIL" l))))
(defn throws? [f] (try (f) false (catch Exception _ true)))

(let [corpus (in/load-corpus corpus-path)
      model  (in/ingest-corpus corpus)]

  ;; ── projection shape ──
  (check "ingest yields 2 revenue-lines" (= 2 (count (:revenue-lines model))))
  (check "ingest yields 1 transfer"      (= 1 (count (:transfers model))))
  (check "ingest yields 3 outlays"       (= 3 (count (:outlays model))))
  (check "account-EARMARK is law (constant), not ingested"
         (= in/account-law (:accounts model)))

  ;; ── G5: every projected entry carries ≥2 source CIDs (own record + dataset manifest) ──
  (check "G5: revenue-lines ≥2 source CIDs"
         (every? #(>= (count (:source-record-cids %)) 2) (:revenue-lines model)))
  (check "G5: outlays ≥2 source CIDs"
         (every? #(>= (count (:source-record-cids %)) 2) (:outlays model)))
  (check "record CIDs are gov.dataset locators"
         (every? #(clojure.string/starts-with? (first (:source-record-cids %)) "gov.dataset.")
                 (:revenue-lines model)))
  (check "2nd CID is the dataset manifest"
         (= (:dataset-cid model) (second (:source-record-cids (first (:revenue-lines model))))))

  ;; ── determinism: same corpus → same CIDs ──
  (check "record-cid deterministic"
         (= (in/record-cid (first (:records corpus))) (in/record-cid (first (:records corpus)))))

  ;; ── amounts: exact integers, 1円 precision ──
  (check "amounts are exact integers"
         (every? integer? (map :amount-jpy (:revenue-lines model))))
  (check "negative amount-local RAISES"
         (throws? #(in/ingest-corpus (update corpus :records conj
                     {:record-id "bad" :record-kind :revenue :tax-kind :x :account :general
                      :fiscal-year 2024 :amount-local -1 :source-sensor "s"}))))

  ;; ── the ingested model drives trace identically to the hand seed ──
  (let [r (rl/trace model :reconstruction-surtax 2024)
        w (rl/trace model :withholding-income 2024)]
    (check "ingested 復興 traceable, residual 0" (and (:traceable? r) (zero? (:residual r))))
    (check "ingested 源泉 non-traceable"          (false? (:traceable? w))))

  ;; ── all-datoms over the ingested model passes G4/G5 ──
  (let [ds (rl/all-datoms model)]
    (check "ingested model emits datoms"  (pos? (count ds)))
    (check "all :db/add"                   (every? #(= :db/add (first %)) ds))))

(println (format "── ingest: %d checks, %d failures ──" @checks @fails))
(when (pos? @fails) (System/exit 1))
