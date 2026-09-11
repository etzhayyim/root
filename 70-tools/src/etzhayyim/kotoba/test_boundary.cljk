;; etzhayyim.kotoba.test-boundary — the root↔subrepo data-boundary guard. Run: bb test:kotoba
;; Verifies the .kotoba.edn marker rule against a constructed temp tree:
;; religious-corp data artifacts inside the (simulated) subrepo are flagged;
;; the engine's own *.json/*.edn fixtures are not.
(ns etzhayyim.kotoba.test-boundary
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [etzhayyim.kotoba.boundary :as b]))

(def ^:private tmp
  (str (System/getProperty "java.io.tmpdir") "/kotoba-boundary-test-fixture"))

(defn- rmrf [f] (when (.exists f)
                  (run! rmrf (.listFiles f))
                  (.delete f)))

(defn- build! [base]
  (rmrf (io/file base))
  (.mkdirs (io/file base "sub"))
  (spit (io/file base "sub" "x-datoms.kotoba.edn") "[]")    ;; data artifact → violation
  (spit (io/file base "sub" "engine.json") "{}")            ;; engine fixture → ignored
  (spit (io/file base "ok.edn") "{}"))                       ;; plain .edn (not .kotoba.edn) → ignored

(deftest scan-flags-only-kotoba-edn
  (build! tmp)
  (try
    (let [found (b/scan tmp)]
      (is (= 1 (count found)))
      (is (str/ends-with? (first found) "x-datoms.kotoba.edn"))
      (is (not-any? #(str/ends-with? % ".json") found))
      (is (not-any? #(str/ends-with? % "ok.edn") found)))
    (finally (rmrf (io/file tmp)))))

(deftest check-reports-violations
  (build! tmp)
  (try
    (let [c (b/check tmp)]
      (is (false? (:clean? c)))
      (is (= 1 (count (:violations c))))
      (is (= tmp (:root c))))
    (finally (rmrf (io/file tmp)))))

(deftest clean-and-missing-roots
  (testing "a tree with no .kotoba.edn is boundary-clean"
    (let [empt (str tmp "-empty")]
      (rmrf (io/file empt))
      (.mkdirs (io/file empt "sub"))
      (spit (io/file empt "sub" "engine.json") "{}")
      (try
        (let [c (b/check empt)]
          (is (true? (:clean? c)))
          (is (= [] (:violations c))))
        (finally (rmrf (io/file empt))))))
  (testing "a non-existent root scans to nil (no crash)"
    (is (nil? (b/scan (str tmp "-does-not-exist"))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.kotoba.test-boundary)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
