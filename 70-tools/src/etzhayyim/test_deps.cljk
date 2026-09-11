;; etzhayyim.test-deps — deps pure-helper invariants (cljc port).
;; Run: bb test:deps
;; Covers the pure helpers (IO _load / _cf_* / _fetch_* deferred): build-kv-records,
;; filter-layers, deps-summary, migrations-by-status, governance-score/verdict,
;; deps-mv-name — mirroring the Python deps CLI command bodies.
(ns etzhayyim.test-deps
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.deps :as deps]))

(deftest build-kv-records-sorts-and-indexes
  (let [recs (deps/build-kv-records
              [{"name" "beta" "did" "did:b" "domain" "beta.example"}
               {"name" "alpha" "did" "did:a" "handles" ["alpha.example"]}
               {"name" ""}])                       ;; blank name dropped
        by-key (into {} (map (juxt :key :value) recs))]
    (testing "one entry per named actor + an actors:index, blank names dropped"
      (is (= 3 (count recs)))
      (is (= #{"actor:alpha" "actor:beta" "actors:index"} (set (keys by-key)))))
    (testing "actors:index lists the sorted names"
      (is (= (pr-str ["alpha" "beta"]) (get by-key "actors:index"))))
    (testing "handle = the domain when present"
      (is (str/includes? (get by-key "actor:beta") "beta.example")))
    (testing "actual behaviour: domain-less actor gets an empty handle"
      ;; NOTE latent port bug — `(or (get a \"domain\" \"\") (first handles) \"\")`
      ;; uses clj `or` where \"\" is TRUTHY (unlike Python), so the `(first handles)`
      ;; fallback is unreachable. This test pins current behaviour; a fix would use
      ;; the module's own `py-or` (or a blank check). Not fixed here (coverage-only).
      (is (str/includes? (get by-key "actor:alpha") "\"handle\" \"\"")))))

(deftest filter-layers-by-section-and-tag
  (let [layers [{:section "packages" :tags ["x"]}
                {:section "infra"    :tags ["y"]}
                {:section "packages" :tags ["y"]}]]
    (is (= 2 (count (deps/filter-layers layers "packages" ""))))
    (is (= 3 (count (deps/filter-layers layers "all" ""))))
    (is (= 2 (count (deps/filter-layers layers "" "y"))))
    (is (= 1 (count (deps/filter-layers layers "packages" "y"))))))

(deftest deps-summary-counts
  (is (= {:has-deps-toml true :migrations 2 :conventions 1 :projects 0 :mitama-actors 3}
         (deps/deps-summary {"migrations" [1 2] "conventions" [1]
                             "projects" [] "mitama_actors" [1 2 3]})))
  (is (= {:has-deps-toml false :migrations 0 :conventions 0 :projects 0 :mitama-actors 0}
         (deps/deps-summary {}))))

(deftest migrations-by-status-filter
  (let [data {"migrations" [{"status" "pending"} {"status" "done"} {"status" "pending"}]}]
    (is (= 2 (count (deps/migrations-by-status data "pending"))))
    (is (= 3 (count (deps/migrations-by-status data ""))))
    (is (= 0 (count (deps/migrations-by-status data "blocked"))))))

(deftest governance-scoring
  (testing "score = fraction of (wit/app/gov) ok × 100"
    (is (= 100.0 (deps/governance-score {:wit-ok true :app-ok true :gov-ok true})))
    (is (= 0.0 (deps/governance-score {:wit-ok false :app-ok false :gov-ok false})))
    (is (< 33.0 (deps/governance-score {:wit-ok true :app-ok false :gov-ok false}) 34.0)))
  (testing "verdict: <60 not-suitable · findings → partial · else suitable"
    (is (= "not-suitable" (deps/governance-verdict 50.0 [])))
    (is (= "partial" (deps/governance-verdict 100.0 ["finding"])))
    (is (= "suitable" (deps/governance-verdict 100.0 [])))))

(deftest deps-mv-name-extraction
  (is (= "my_view"
         (deps/deps-mv-name "CREATE MATERIALIZED VIEW IF NOT EXISTS my_view AS SELECT 1;")))
  (is (= "plain_view"
         (deps/deps-mv-name "CREATE MATERIALIZED VIEW plain_view AS SELECT 1")))
  (is (= "?" (deps/deps-mv-name "SELECT * FROM nope"))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-deps)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
