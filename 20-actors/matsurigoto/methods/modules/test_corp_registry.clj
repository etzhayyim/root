;; test_corp_registry.clj — matsurigoto corp-registry: ISO 7064 MOD 97-10 LEI parity with
;; corp_registry.py + append-only registry discipline. Run via `bb test:matsurigoto`. ADR-2606142300.
(ns matsurigoto.methods.modules.test-corp-registry
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [matsurigoto.methods.modules.corp-registry :as cr]))

(deftest iso7064-lei-parity
  (testing "ISO 17442 LEI + ISO 7064 MOD 97-10 reproduced exactly (golden from corp_registry.py)"
    (is (= "68" (cr/compute-lei-check-digits "EZHY00000000000001")))
    (is (= "EZHY0000000000000168" (cr/assign-lei "EZHY" "000000000001")))
    (is (= "549300ACME0000000169" (cr/assign-lei "5493" "ACME00000001")))
    (is (true? (cr/validate-lei "EZHY0000000000000168")))
    (is (true? (cr/validate-lei "549300ACME0000000169")))))

(deftest lei-validation-rejects-corruption
  (testing "flipping any character breaks the MOD 97-10 check (prob 96/97)"
    (is (false? (cr/validate-lei "EZHY0000000000000169")))   ; last digit flipped
    (is (false? (cr/validate-lei "EZHY000000000000016")))    ; wrong length (19)
    (is (false? (cr/validate-lei "EZHY00000000000001688")))  ; wrong length (21)
    (is (false? (cr/validate-lei nil)))
    (is (false? (cr/validate-lei "EZHY000000000000016!")))))  ; non [0-9A-Z]

(deftest assign-lei-guards
  (testing "LEI assembly input guards"
    (is (thrown? Exception (cr/assign-lei "EZH" "000000000001")))    ; LOU not 4
    (is (thrown? Exception (cr/assign-lei "EZHY" "0001")))           ; entity not 12
    (is (thrown? Exception (cr/compute-lei-check-digits "TOOSHORT")))))

(deftest incorporation-record
  (testing "incorporation assigns registry number + valid LEI (golden)"
    (let [r (cr/register-incorporation {:entity-name "Tree of Life K.K." :officers ["officer:rin"]
                                        :capital 10000000 :articles "articles-hash"
                                        :address "東京都新宿区" :jurisdiction "JPN" :sequence 1})]
      (is (= "JPN-00000001" (:registry-number r)))
      (is (= "EZHY0000000000000168" (:lei r)))
      (is (true? (cr/validate-lei (:lei r))))
      (is (true? (:immutable (:record r))))                  ; G5
      (let [c (:certificate r)]
        (is (nil? (:proof c)))                               ; G1
        (is (false? (:server-held-authority c)))             ; G1
        (is (= "issued-unsigned" (:status c)))
        (is (= ["VerifiableCredential" "IncorporationCertificate"] (:type c)))))))

(deftest incorporation-guards
  (testing "incorporation validation guards"
    (let [base {:entity-name "X" :officers ["o"] :capital 0 :articles "a" :address "addr"
                :jurisdiction "JPN" :sequence 0}]
      (is (map? (cr/register-incorporation base)))            ; valid baseline
      (is (thrown? Exception (cr/register-incorporation (assoc base :entity-name ""))))
      (is (thrown? Exception (cr/register-incorporation (assoc base :officers []))))
      (is (thrown? Exception (cr/register-incorporation (assoc base :capital -1))))
      (is (thrown? Exception (cr/register-incorporation (assoc base :sequence -1)))))))

(deftest append-only-change
  (testing "G5 — a change is an appended amendment, never an overwrite"
    (let [inc (cr/register-incorporation {:entity-name "X" :officers ["o"] :capital 0 :articles "a"
                                          :address "addr" :jurisdiction "JPN" :sequence 1})
          chg (cr/register-change "JPN-00000001" {:address "大阪市"} "2026-06-15")
          hist (-> [] (cr/append inc) (cr/append chg))]
      (is (= "JPN-00000001#chg@2026-06-15" (:record-id (:record chg))))
      (is (= "change" (:kind (:record chg))))
      (is (= 2 (count hist)))                                 ; append-only: both records retained
      (is (= "incorporation" (:kind (first hist))))
      (is (true? (:immutable (:record chg))))
      (is (thrown? Exception (cr/register-change "" {:a 1} "2026-06-15")))
      (is (thrown? Exception (cr/register-change "JPN-1" {} "2026-06-15"))))))

(deftest live-registration-gated
  (testing "G1 — live registration against a real register is Council+operator gated"
    (is (thrown? Exception (cr/solve)))
    (is (false? cr/server-held-authority))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'matsurigoto.methods.modules.test-corp-registry)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
