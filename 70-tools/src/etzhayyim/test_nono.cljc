;; etzhayyim.test-nono — nono worker-lifecycle pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure parse/build helpers (fs/HTTP/subprocess legs deferred):
;; parse-manifest-data · find-manifest-by-nanoid · build-deploy-reg-body ·
;; build-build-command · build-deploy-command · build-register-manifest-request.
(ns etzhayyim.test-nono
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.nono :as n]))

(deftest parse-manifest
  (testing "keyword-keyed manifest"
    (is (= {:nanoid "n1" :name "x" :bindings ["b"] :skills ["s"]}
           (n/parse-manifest-data {:nanoid "n1" :name "x" :bindings ["b"] :skills ["s"]}))))
  (testing "string-keyed manifest + defaults for missing fields"
    (is (= {:nanoid "n2" :name "y" :bindings [] :skills []}
           (n/parse-manifest-data {"nanoid" "n2" "name" "y"}))))
  (testing "no nanoid → nil"
    (is (nil? (n/parse-manifest-data {:name "x"})))
    (is (nil? (n/parse-manifest-data {})))))

(deftest find-by-nanoid
  (is (= {:nanoid "b"} (n/find-manifest-by-nanoid [{:nanoid "a"} {:nanoid "b"}] "b")))
  (is (nil? (n/find-manifest-by-nanoid [{:nanoid "a"}] "missing"))))

(deftest deploy-reg-body
  (let [b (n/build-deploy-reg-body {"name" "X" "nanoid" "n1" "bindings" ["b"]} "fallback")]
    (is (= "https://etzhayyim.com/ns/nono/v1" (get b "@context")))
    (is (= "X" (get b "name")))
    (is (= "n1" (get b "nanoid")))
    (is (= "nono" (get b "type")))
    (is (= "active" (get b "status")))
    (is (= ["b"] (get b "bindings")))
    (is (= [] (get b "skills"))))
  (testing "nanoid falls back to the supplied argument when absent in data"
    (is (= "fb" (get (n/build-deploy-reg-body {} "fb") "nanoid")))))

(deftest build-command-selection
  (testing "package.json build script → pnpm vs npm by lockfile presence"
    (is (= ["pnpm" "run" "build"] (n/build-build-command {"scripts" {"build" "tsc"}} true false)))
    (is (= ["npm" "run" "build"]  (n/build-build-command {"scripts" {"build" "tsc"}} false false))))
  (testing "no build script but wrangler.jsonc → dry-run wrangler build"
    (is (= ["npx" "wrangler" "deploy" "--dry-run" "--outdir" "dist"]
           (n/build-build-command nil false true)))
    (is (= ["npx" "wrangler" "deploy" "--dry-run" "--outdir" "dist"]
           (n/build-build-command {"scripts" {}} false true))))
  (testing "nothing buildable → nil"
    (is (nil? (n/build-build-command nil false false)))))

(deftest deploy-command-and-request
  (is (= ["npx" "wrangler" "deploy"] (n/build-deploy-command)))
  (let [r (n/build-register-manifest-request "https://p" "tok" {"x" 1})]
    (is (= :post (:method r)))
    (is (= "https://p/xrpc/com.etzhayyim.actor.registerManifest" (:url r)))
    (is (= "Bearer tok" (get-in r [:headers "Authorization"])))
    (is (= {"x" 1} (:body r)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-nono)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
