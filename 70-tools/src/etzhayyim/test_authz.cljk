;; etzhayyim.test-authz — authz pure-helper invariants (cljc port, wave 5a).
;; Run: bb test:authz
;; Covers etzhayyim.authz controlled-dids / format-key-row / format-did-row,
;; mirroring the Python authz.py command bodies the port reproduces.
(ns etzhayyim.test-authz
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.authz :as authz]))

(deftest controlled-dids-prepends-primary
  (testing "primary DID is prepended when absent from controlledDids"
    (is (= ["did:plc:abc" "did:plc:xyz"]
           (authz/controlled-dids {"did" "did:plc:abc"
                                   "controlledDids" ["did:plc:xyz"]}))))
  (testing "primary is NOT duplicated when already present"
    (is (= ["did:plc:abc" "did:plc:xyz"]
           (authz/controlled-dids {"did" "did:plc:abc"
                                   "controlledDids" ["did:plc:abc" "did:plc:xyz"]}))))
  (testing "empty controlledDids yields just the primary"
    (is (= ["did:plc:abc"] (authz/controlled-dids {"did" "did:plc:abc"}))))
  (testing "primary whitespace is trimmed"
    (is (= ["did:plc:abc"] (authz/controlled-dids {"did" "  did:plc:abc  "}))))
  (testing "blank/absent primary returns controlledDids unchanged"
    (is (= ["did:plc:xyz"] (authz/controlled-dids {"controlledDids" ["did:plc:xyz"]})))
    (is (= ["did:plc:xyz"] (authz/controlled-dids {"did" "  " "controlledDids" ["did:plc:xyz"]}))))
  (testing "no keys at all → empty vector"
    (is (= [] (authz/controlled-dids {})))))

(deftest format-key-row-shape
  (testing "id / label / scopes are joined with the Python 2-space layout"
    (is (= "  k1  main  read,write"
           (authz/format-key-row {"id" "k1" "label" "main" "scopes" "read,write"}))))
  (testing "missing fields render as empty strings (no nil leakage)"
    (is (= "      " (authz/format-key-row {})))
    (is (= "  k2    " (authz/format-key-row {"id" "k2"})))))

(deftest format-did-row-marks-active
  (testing "the active DID is annotated, others are not"
    (is (= "  did:plc:abc (active)" (authz/format-did-row "did:plc:abc" "did:plc:abc")))
    (is (= "  did:plc:xyz" (authz/format-did-row "did:plc:xyz" "did:plc:abc")))
    (is (= "  did:plc:xyz" (authz/format-did-row "did:plc:xyz" nil)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-authz)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
