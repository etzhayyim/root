(ns meibo.tests.test-directory
  "meibo 名簿 — directory-registry tests (ADR-2607062200). clojure.test."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [meibo.methods.directory :as dir]))

(deftest test-10-jurisdictions-covered
  (is (= (count (dir/jurisdictions-covered)) 10))
  (is (= (set (dir/jurisdictions-covered))
         #{":jp" ":us" ":uk" ":de" ":kr" ":fr" ":au" ":ca" ":it" ":es"})))

(deftest test-every-entry-verified-https-url
  (doseq [d (dir/load-directory)]
    (is (str/starts-with? (get d ":dir/url") "https://"))
    (is (some? (get d ":dir/kind")))
    (is (some? (get d ":dir/label")))))

(deftest test-every-jurisdiction-has-bar-association
  (doseq [j (dir/jurisdictions-covered)]
    (is (some #(= (get % "kind") ":bar-association") (dir/by-jurisdiction j))
        (str j " missing a :bar-association entry"))))

(deftest test-jp-flags-gyoseishoshi-court-submission-limit
  (let [jp (dir/by-jurisdiction ":jp")
        gyosei (some #(when (= (get % "id") "dir:jp-gyoseishoshi") %) jp)]
    (is (some? gyosei))
    (is (str/includes? (get gyosei "note") "訴訟書類"))))

(deftest test-uncovered-jurisdiction-degrades-empty
  (is (= (dir/by-jurisdiction ":br") [])))

(deftest test-institution-level-only-no-pii-fields
  ;; G1 — no per-individual field names anywhere in the schema
  (doseq [d (dir/load-directory)]
    (is (nil? (get d ":dir/attorney-name")))
    (is (nil? (get d ":dir/bar-number")))))
