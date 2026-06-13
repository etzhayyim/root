(ns ake.methods.test-ingest
  "Tests for ingest.cljc — genesis revision history over the actor-profile SSoT.
  ADR-2606052100. Port of `methods/test_ingest.py` (imports ingest + revision),
  plus a Python↔Clojure parity test (the genesis bridge produces a byte-identical
  revision history on both implementations — there is no content-addressing in these
  modules, so parity is over the plain revision-history shape, not a CID).

  HERMETIC: asserted against the committed FIXTURE
  (20-actors/ake/data/sample-profile-seed.kotoba.edn) with exact, known counts."
  (:require [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is]]
            [ake.methods.ingest :as ingest]
            [ake.methods.revision :as rev]))

(defn- repo-root []
  (let [cwd (io/file (System/getProperty "user.dir"))]
    (loop [d cwd]
      (cond
        (nil? d) cwd
        (.exists (io/file d "20-actors" "ake" "data" "sample-profile-seed.kotoba.edn")) d
        :else (recur (.getParentFile d))))))

(def ^:private fixture
  (io/file (repo-root) "20-actors" "ake" "data" "sample-profile-seed.kotoba.edn"))

(def ^:private methods-dir
  (io/file (repo-root) "20-actors" "ake" "methods"))

;; ── hermetic: exact behaviour on the committed fixture (3 records / 7 revisions) ──

(deftest fixture-record-and-revision-counts-are-exact
  (let [res (ingest/genesis-revisions fixture)]
    (is (= 3 (:records res)))
    (is (= 7 (count (:history res))))))   ;; ake 3 + sample-corp 3 + sample-svc 1

(deftest fixture-covers-every-record-with-a-description-genesis
  (let [res (ingest/genesis-revisions fixture)]
    (doseq [h ["ake" "sample-corp" "sample-svc"]]
      (is (seq (rev/history-of (:history res) h "description"))
          (str "no genesis for " h)))))

(deftest fixture-ake-genesis-is-authoritative-with-value
  (let [res (ingest/genesis-revisions fixture)
        cur (rev/current (:history res) "ake" "description")]
    (is (some? cur))
    (is (= ":authoritative" (get cur ":revision/sourcing")))
    (is (str/includes? (get cur ":revision/value") "community-edit membrane"))))

(deftest fixture-description-only-record-yields-one-revision
  (let [res (ingest/genesis-revisions fixture)]
    ;; sample-svc has no display-name fields → exactly one (description) genesis revision
    (is (= 1 (count (rev/history-of (:history res) "sample-svc" "description"))))
    (is (nil? (rev/current (:history res) "sample-svc" "display-name-ja")))))

(deftest genesis-is-append-only-member-edit-layers-on-top
  (let [res (ingest/genesis-revisions fixture)
        h (:history res)
        base-n (count (rev/history-of h "ake" "description"))
        genesis-at (get (rev/current h "ake" "description") ":revision/as-of")
        member-edit {":edit/target-entity" "ake"
                     ":edit/target-attr" ":actor/description"
                     ":edit/proposed-value" "(member-proposed tweak)"
                     ":edit/sourcing" ":representative"
                     ":edit/author" "did:web:etzhayyim.com:member:abel"
                     ":edit/op" ":assert"}
        h2 (rev/append-revision h member-edit (+ genesis-at 1000))]
    (is (= (inc base-n) (count (rev/history-of h2 "ake" "description"))))   ;; grew by one
    (is (= "(member-proposed tweak)" (get (rev/current h2 "ake" "description") ":revision/value")))
    ;; time-travel: before the member edit, the authoritative genesis is still current
    (is (= ":authoritative"
           (get (rev/as-of h2 "ake" "description" genesis-at) ":revision/sourcing")))))

(deftest as-of-base-is-deterministic
  (let [a (ingest/genesis-revisions fixture ingest/genesis-as-of-base)
        b (ingest/genesis-revisions fixture ingest/genesis-as-of-base)]
    (is (= (mapv #(get % ":revision/as-of") (:history a))
           (mapv #(get % ":revision/as-of") (:history b))))))

(deftest report-renders-from-fixture
  (let [md (ingest/report (ingest/genesis-revisions fixture))]
    (is (str/includes? md "genesis revision history"))
    (is (str/includes? md "| ake |"))))

;; ── soft: membrane-over-REAL-data, validated only when ake is registered in the shared seed ──

(deftest real-repo-seed-integration-when-registered
  (let [res (ingest/genesis-revisions)]   ;; default = the REAL 00-contracts/.../actor-profile-seed
    (if-not (some #{"ake"} (:actors res))
      (is true "soft pass: ake not yet registered in the shared seed")
      (do
        (is (>= (:records res) 19))       ;; the real seed registers the full actor fleet
        (let [cur (rev/current (:history res) "ake" "description")]
          (is (some? cur))
          (is (= ":authoritative" (get cur ":revision/sourcing"))))))))

;; ── Python↔Clojure parity: the genesis bridge produces the SAME revision history ──
;; revision.py / ingest.py carry no content-addressing (no sha256+canonical-JSON CID),
;; so parity is over the plain genesis-revision history shape: run the REAL Python
;; ingest.py over the same fixture via babashka.process and assert the per-revision
;; (entity, attr, sourcing, op, value, as-of) tuples are identical on both sides.

(deftest python-clojure-genesis-parity
  (let [sh (requiring-resolve 'babashka.process/sh)
        script (str "import sys, json\n"
                    "import ingest\n"
                    "res = ingest.genesis_revisions(sys.argv[1])\n"
                    "rows = [[r[':revision/entity'], r[':revision/attr'],\n"
                    "         r[':revision/sourcing'], r[':revision/op'],\n"
                    "         r[':revision/value'], r[':revision/as-of']]\n"
                    "        for r in res['history']]\n"
                    "print(json.dumps({'records': res['records'], 'rows': rows},\n"
                    "                 ensure_ascii=False), end='')\n")
        r (sh {:dir (str methods-dir)} "python3" "-c" script (str fixture))]
    (is (zero? (:exit r)) (str "python ingest failed: " (:err r)))
    (let [parse-json (requiring-resolve 'cheshire.core/parse-string)
          py (parse-json (:out r))
          py-rows (get py "rows")
          py-records (get py "records")
          cres (ingest/genesis-revisions fixture)
          clj-rows (mapv (fn [r]
                           [(get r ":revision/entity")
                            (get r ":revision/attr")
                            (get r ":revision/sourcing")
                            (get r ":revision/op")
                            (get r ":revision/value")
                            (get r ":revision/as-of")])
                         (:history cres))]
      (is (= py-records (:records cres)))
      (is (= py-rows clj-rows)))))    ;; byte-identical genesis history, Python ⟷ Clojure
