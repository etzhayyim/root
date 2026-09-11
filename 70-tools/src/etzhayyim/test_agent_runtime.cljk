;; etzhayyim.test-agent-runtime — agent-runtime pure-builder invariants (cljc port).
;; Run: bb test:agent-runtime
;; Covers the pure result/plan builders (subprocess/httpx/fs legs are IO-deferred):
;; build-runtime-doc · build-publish-result · build-holochain-plan.
(ns etzhayyim.test-agent-runtime
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.agent-runtime :as ar]))

(deftest runtime-doc-shape
  (let [d (ar/build-runtime-doc "prod" [{:path "a.yaml" :content "x"}])]
    (is (= "prod" (get d "cluster")))
    (is (= "k8s-runtime" (get d "kind")))
    (is (= [{:path "a.yaml" :content "x"}] (get d "manifests")))
    (is (string? (get d "$schema")))))

(deftest publish-result-ipfs-base
  (testing "ipfsBase trailing slashes are stripped"
    (is (= "https://ipfs.example"
           (get (ar/build-publish-result "c" "0xabc" 100 true "https://ipfs.example/") "ipfsBase"))))
  (testing "nil ipfs-base falls back to the default gateway"
    (is (= "https://ipfs.etzhayyim.com"
           (get (ar/build-publish-result "c" "0xabc" 100 true nil) "ipfsBase"))))
  (testing "core fields"
    (let [r (ar/build-publish-result "mycluster" "0xdeadbeef" 42 true "https://g/")]
      (is (true? (get r "ok")))
      (is (true? (get r "dryRun")))
      (is (false? (get r "published")))
      (is (= "0xdeadbeef" (get r "sha256")))
      (is (= 42 (get r "bytes")))
      (is (= "mycluster" (get r "cluster"))))))

(deftest holochain-plan-defaults-and-overrides
  (testing "required fields placed + optional fields default"
    (let [p (ar/build-holochain-plan {:agent-did "did:x" :happ-uri "ipfs://h" :dna-hash "dna1"})]
      (is (= "did:x" (get p "agentDid")))
      (is (= "local-dev" (get p "cluster")))                       ;; default
      (is (= "etzhayyim-agent-actor-runtime" (get-in p ["hApp" "name"])))  ;; default
      (is (= "ipfs://h" (get-in p ["hApp" "uri"])))
      (is (= "dna1" (get-in p ["hApp" "dnaHash"])))
      (is (= "agent_actor_runtime" (get-in p ["hApp" "roleName"])))
      (testing "k8s env carries the identity vars"
        (let [env (get-in p ["k8s" "env"])]
          (is (some #(and (= "AGENT_DID" (get % "name")) (= "did:x" (get % "value"))) env))
          (is (some #(and (= "DNA_HASH" (get % "name")) (= "dna1" (get % "value"))) env))))))
  (testing "explicit cluster overrides the default"
    (is (= "prod" (get (ar/build-holochain-plan
                        {:agent-did "d" :happ-uri "u" :dna-hash "h" :cluster "prod"})
                       "cluster")))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-agent-runtime)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
