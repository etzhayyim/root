;; test_honesty_adversarial.clj — try to BREAK the honesty guarantees; every attempt must fail.
;; The danjo lint-regression discipline (poisoned fixtures), applied to the revenue-ledger's
;; defining property: per-yen provenance through a fungible account is unrepresentable, and a
;; fungible tax cannot be made to look traceable. Run: bb test_honesty_adversarial.clj.
(ns root.danjo.methods.test-honesty-adversarial)

(load-file "discrepancy.clj")     ; → revenue_ledger
(load-file "taxes.clj")
(load-file "ingest.clj")
(alias 'rl 'root.danjo.methods.revenue-ledger)
(alias 'd  'root.danjo.methods.discrepancy)
(alias 't  'root.danjo.methods.taxes)
(alias 'in 'root.danjo.methods.ingest)

(def checks (atom 0)) (def fails (atom 0))
(defn check [l p] (swap! checks inc) (if p (println "  ok  " l) (do (swap! fails inc) (println "  FAIL" l))))
(defn raises? [f] (try (f) false (catch Exception _ true)))

(def seed (rl/load-seed "../data/gov-revenue-seed.jp.edn"))

;; ── ATTACK 1: bind a fungible tax to a specific outlay through 一般会計 → must RAISE ──
(check "ATTACK funded-by-tax through 一般会計 → RAISES"
       (raises? #(rl/outlay-datoms
                  (update seed :outlays conj
                          {:record-id "atk" :account :general :program-code "X" :program-name "x"
                           :cofog "0" :recipient-class "x" :fiscal-year 2024 :amount-jpy 1
                           :funded-by-tax :withholding-income :source-record-cids ["a" "b"]}))))

;; ── ATTACK 2: route 源泉所得税 through a transfer into a NON-earmarked account ──
;;   (a) emitting such a transfer must RAISE; (b) trace must still report non-traceable.
(check "ATTACK transfer of 源泉 into a non-earmarked target → RAISES on emit"
       (raises? #(rl/transfer-datoms
                  (assoc seed :transfers
                         [{:record-id "atk2" :tax-kind :withholding-income :from :general :to :general
                           :fiscal-year 2024 :amount-jpy 1 :source-record-cids ["a" "b"]}]))))
(check "ATTACK even a recorded non-earmarked transfer leaves 源泉 non-traceable"
       (false? (:traceable?
                (rl/trace (assoc seed :transfers
                                 [{:record-id "atk2b" :tax-kind :withholding-income :from :general
                                   :to :general :fiscal-year 2024 :amount-jpy 1
                                   :source-record-cids ["a" "b"]}])
                          :withholding-income 2024))))

;; ── ATTACK 3: declare a fake special account but leave it :earmark? false → still non-traceable ──
(check "ATTACK fake special account with earmark? false → NOT per-yen traceable"
       (let [atk (-> seed
                     (update :accounts conj {:id :special/fake :kind :special :earmark? false})
                     (update :transfers conj {:record-id "atk3" :tax-kind :withholding-income
                                              :from :general :to :special/fake :fiscal-year 2024
                                              :amount-jpy 1 :source-record-cids ["a" "b"]}))]
         ;; transfer-datoms must refuse the non-earmarked target, AND trace stays non-traceable
         (and (raises? #(rl/transfer-datoms atk))
              (false? (:traceable? (rl/trace atk :withholding-income 2024))))))

;; ── ATTACK 4: classify ignores an injected :per-yen? — it is recomputed from earmark-kind ──
(check "ATTACK injected :per-yen? true on a :general tax is ignored (recomputed false)"
       (false? (:per-yen? (t/classify {:id :x :ja "x" :earmark-kind :general :per-yen? true}))))
(check "per-yen-iff-special holds for EVERY tax in the full registry (no exceptions)"
       (every? (fn [tx] (= (boolean (:per-yen? (t/classify tx)))
                           (= :special-account (:earmark-kind tx))))
               (:taxes (t/combine (t/load-taxes "../data/jp-national-taxes.edn")
                                  (t/load-local-taxes "../data/jp-local-taxes.edn")))))

;; ── ATTACK 5: smuggle a verdict into a reconciliation observation → must RAISE ──
(doseq [tok ["fraud" "illegal" "unlawful" "violation" "犯罪" "違法" "有罪" "不正"]]
  (check (str "ATTACK verdict category '" tok "' → RAISES")
         (raises? #(d/observation-datoms
                    [{:category (keyword (str "outlay-" tok)) :observed-pattern "x"
                      :source-record-cids ["a" "b"] :method-note-cid "m" :non-adjudicating true}]))))

;; ── ATTACK 6: a verdict token in any emitted revenue/tax datom attr → must RAISE (G4) ──
;;   (constructed by giving the registry a verdict-named attr via a poisoned earmark-kind path is
;;    not reachable; instead confirm the guard fires on a hand-built poisoned datom set.)
(check "ATTACK a verdict-named attr in observation datoms → RAISES"
       (raises? #(d/observation-datoms
                  [{:category :crime-detected :observed-pattern "x"
                    :source-record-cids ["a" "b"] :method-note-cid "m" :non-adjudicating true}])))

;; ── ATTACK 7: drop a source CID below the G5 floor → must RAISE ──
(check "ATTACK <2 source CIDs on a revenue line → RAISES (G5)"
       (raises? #(rl/revenue-datoms (assoc-in seed [:revenue-lines 0 :source-record-cids] ["only"]))))

(println (format "── honesty-adversarial: %d checks, %d failures ──" @checks @fails))
(when (pos? @fails) (System/exit 1))
