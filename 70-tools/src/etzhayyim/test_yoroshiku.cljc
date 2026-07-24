;; etzhayyim.test-yoroshiku — yoroshiku readiness pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure readiness/format/request helpers (fs + HTTP legs deferred):
;; compute-readiness-checks · build-register-request · format-check-line ·
;; format-readiness-summary.
(ns etzhayyim.test-yoroshiku
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.yoroshiku :as y]))

(deftest readiness-checks-from-signals
  (testing "all-present → 4 OK checks in canonical order"
    (let [cs (y/compute-readiness-checks
              {:deps-toml true :claude-md true :apps-dir true :app-count 5 :auth true})]
      (is (= ["deps.toml" "CLAUDE.md" "60-apps" "authn"] (mapv :name cs)))
      (is (every? :ok cs))
      (is (= "5 apps" (:detail (nth cs 2))))      ;; 60-apps detail shows count
      (is (= "signed in" (:detail (nth cs 3))))))
  (testing "empty signals → all WARN, app-count defaults to 0"
    (let [cs (y/compute-readiness-checks {})]
      (is (every? (complement :ok) cs))
      (is (= "deps.toml missing" (:detail (first cs))))
      (is (= "missing" (:detail (nth cs 2))))
      (is (= "not signed in" (:detail (nth cs 3)))))))

(deftest register-request-shape
  (let [r (y/build-register-request "https://pds.example" "/ws/path" "tok")]
    (is (= :post (:method r)))
    (is (= "https://pds.example/xrpc/com.etzhayyim.yoroshiku.registerWorkspace" (:url r)))
    (is (= "Bearer tok" (get-in r [:headers "Authorization"])))
    (is (= {:workspace "/ws/path"} (:body r)))))

(deftest format-check-line-display
  (is (= "  [OK  ] deps.toml  found" (y/format-check-line {:name "deps.toml" :ok true :detail "found"})))
  (is (= "  [WARN] authn  not signed in"
         (y/format-check-line {:name "authn" :ok false :detail "not signed in"}))))

(deftest readiness-summary-line
  (is (= "yoroshiku (よろしく): 2/3 checks passing"
         (y/format-readiness-summary [{:ok true} {:ok false} {:ok true}])))
  (is (= "yoroshiku (よろしく): 0/0 checks passing" (y/format-readiness-summary []))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-yoroshiku)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
