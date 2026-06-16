(ns keizu.methods.test-registry
  "test_registry.py — 系図 (keizu) source-registry access + runtime deny guard. ADR-2606066000.
  1:1 Clojure port (stdlib _t harness → clojure.test)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [keizu.methods.registry :as registry]))

(deftest test-source-ids-nonempty-and-known
  (let [ids (registry/source-ids)]
    (is (some #(= % "jpn-procurement-pportal") ids))
    (is (some #(= % "usa-fec") ids))))

(deftest test-get-source-fields
  (let [s (registry/get-source "eu-ted")]
    (is (= "eu" (get s "jurisdiction")))
    (is (= "procurement" (get s "sourceKind")))))

(deftest test-get-source-unknown-raises
  (is (thrown-with-msg? #?(:clj Exception :cljs js/Error) #"no such source"
                        (registry/get-source "no-such"))))

(deftest test-sourcing-for-seed-is-representative
  ;; every seed source is unverified-seed → :representative (G11, never auto-authoritative)
  (doseq [sid (registry/source-ids)]
    (is (= ":representative" (registry/sourcing-for sid)) sid)))

(deftest test-sourcing-for-unknown-is-representative
  (is (= ":representative" (registry/sourcing-for "ghost"))))

(deftest test-assert-source-allowed-passes-public
  (is (nil? (registry/assert-source-allowed "https://www.usaspending.gov/" "https://www.fec.gov/"))))

(deftest test-assert-source-allowed-refuses-terminal
  (is (thrown-with-msg? #?(:clj Exception :cljs js/Error) #"prohibited"
                        (registry/assert-source-allowed "https://bloomberg.com/gov/x"))))

#?(:clj (defn -main [& _] (run-tests 'keizu.methods.test-registry)))
