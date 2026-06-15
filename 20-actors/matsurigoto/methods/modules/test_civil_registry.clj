;; test_civil_registry.clj — matsurigoto civil-registry: CRVS validation + append-only parity
;; with civil_registry.py. Run via `bb test:matsurigoto`. ADR-2606142300.
(ns matsurigoto.methods.modules.test-civil-registry
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [matsurigoto.methods.modules.civil-registry :as cv]))

(deftest birth-registration
  (testing "birth registration record + unsigned certificate (golden from civil_registry.py)"
    (let [b (cv/register-birth "birth-1" "child:aoi" ["parent:rin"] "東京都新宿区"
                               "2026-06-01T09:00:00Z" "2026-06-05T00:00:00Z")
          r (:record b) c (:certificate b)]
      (is (= "birth-1" (:record-id r)))
      (is (= "birth" (:vital-kind r)))
      (is (= "2026-06-01T09:00:00Z" (:occurred-at r)))
      (is (= {:child "child:aoi" :parents ["parent:rin"] :place "東京都新宿区"} (:fields r)))
      (is (true? (:immutable r)))                                   ; G5
      (is (= ["VerifiableCredential" "BirthCertificate"] (:type c)))
      (is (nil? (:proof c)))                                        ; G1
      (is (false? (:server-held-authority c)))                      ; G1
      (is (= "issued-unsigned" (:status c))))))

(deftest birth-guards
  (testing "birth validation"
    (is (thrown? Exception (cv/register-birth "b" "" ["p"] "x" "2026-01-01" "2026-06-01")))   ; no child
    (is (thrown? Exception (cv/register-birth "b" "c" [] "x" "2026-01-01" "2026-06-01")))      ; no parent
    (is (thrown? Exception (cv/register-birth "b" "c" ["p"] "" "2026-01-01" "2026-06-01")))    ; no place
    (is (thrown? Exception (cv/register-birth "b" "c" ["p"] "x" "2027-01-01" "2026-06-05")))   ; future
    (is (thrown? Exception (cv/register-birth "b" "c" ["p"] "x" "not-a-date" "2026-06-05"))))) ; bad ISO

(deftest marriage-distinct-and-monogamy
  (testing "marriage requires two distinct, unmarried partners; partners stored sorted (golden)"
    (let [m (cv/register-marriage "m-1" "z:bob" "a:alice" "渋谷" "2026-06-01" "2026-06-10")]
      (is (= ["a:alice" "z:bob"] (get-in m [:record :fields :partners])))   ; sorted
      (is (= "marriage" (:vital-kind (:record m)))))
    (is (thrown? Exception (cv/register-marriage "m" "x" "x" "p" "2026-01-01" "2026-06-01")))  ; same partner
    (is (thrown? Exception
                 (cv/register-marriage "m-2" "a:alice" "c:carol" "x" "2026-06-02" "2026-06-10"
                                       [["a:alice" "z:bob"]])))))                               ; bigamy

(deftest death-registration
  (testing "death registration, optional ICD-11 cause"
    (let [d  (cv/register-death "d-1" "person:rin" "病院" "2026-05-01" "2026-06-01")
          dc (cv/register-death "d-2" "person:aoi" "病院" "2026-05-01" "2026-06-01" "ICD11:XX")]
      (is (= "death" (:vital-kind (:record d))))
      (is (not (contains? (:fields (:record d)) :cause)))           ; G6 data-minimization
      (is (= "ICD11:XX" (get-in dc [:record :fields :cause])))
      (is (thrown? Exception (cv/register-death "d" "" "p" "2026-01-01" "2026-06-01"))))))      ; no decedent

(deftest residency-append-only-current-address
  (testing "G5 — move-in is a new record; current-address = latest residency (非終末論)"
    (let [h (-> []
                (cv/append (cv/register-residency "r1" "p:rin" "東京" "2025-01-01" "2026-06-05"))
                (cv/append (cv/register-residency "r2" "p:rin" "大阪" "2026-03-01" "2026-06-05")))]
      (is (= 2 (count h)))                                          ; both retained, not overwritten
      (is (= "大阪" (cv/current-address h "p:rin")))                 ; latest by occurred-at
      (is (nil? (cv/current-address h "p:unknown")))
      (is (thrown? Exception (cv/register-residency "r" "" "addr" "2026-01-01" "2026-06-01"))))))

(deftest live-registration-gated
  (testing "G1 — live registration against a real register is Council+operator gated"
    (is (thrown? Exception (cv/solve)))
    (is (false? cv/server-held-authority))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'matsurigoto.methods.modules.test-civil-registry)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
