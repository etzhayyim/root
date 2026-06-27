;; etzhayyim.test-murakumo-cmd — murakumo-cmd pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure request/command/parse helpers (HTTP/SSH/nomad dispatch deferred):
;; build-auth-headers · normalize-pds · build-{status,infer,xrpc,fleet-jotai}-request ·
;; build-{ssh,scp,nomad}-command · parse-fleet-models · probe-cmd-for-model ·
;; resolve-install-cmd · parse-nodes-json · resolve-node-id · resolve-alloc-id.
(ns etzhayyim.test-murakumo-cmd
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.murakumo-cmd :as mc]))

(deftest headers-and-pds
  (is (= {"Authorization" "Bearer t" "Content-Type" "application/json"} (mc/build-auth-headers "t")))
  (is (= "https://p" (mc/normalize-pds "https://p/")))
  (is (= "https://p" (mc/normalize-pds "https://p"))))

(deftest http-request-builders
  (testing "status GET strips slash + targets getStatus"
    (is (= "https://p/xrpc/com.etzhayyim.murakumo.getStatus"
           (:url (mc/build-status-request "https://p/" "t")))))
  (testing "infer body omits model when blank, includes when set"
    (is (= {:prompt "hi"} (:body (mc/build-infer-request "https://p" "t" "hi" ""))))
    (is (= {:prompt "hi" :model "gemma"} (:body (mc/build-infer-request "https://p" "t" "hi" "gemma")))))
  (testing "generic xrpc parses the JSON payload string into the body"
    (is (= {:k 1} (:body (mc/build-xrpc-request "https://p" "t" "com.x" "{\"k\":1}")))))
  (testing "fleet-jotai encodes the limit in the query string"
    (is (str/ends-with? (:url (mc/build-fleet-jotai-request "https://p" "t" 10)) "fleetStatus?limit=10"))))

(deftest argv-command-builders
  (testing "ssh argv: batch flags + host + remote command"
    (let [c (mc/build-ssh-command "amaterasu" "echo hi")]
      (is (= "ssh" (first c)))
      (is (some #{"amaterasu@amaterasu.murakumo.lan"} c))
      (is (= "echo hi" (last c)))))
  (is (= ["scp" "-o" "StrictHostKeyChecking=no" "/src" "host:/dest"]
         (mc/build-scp-command "/src" "host" "/dest")))
  (is (= ["/usr/bin/nomad" "node" "status"] (mc/build-nomad-command "/usr/bin/nomad" "node" "status"))))

(deftest fleet-models-parsing
  (is (= {:fleet ["a"] :models {"m" {}}} (mc/parse-fleet-models {"fleet" ["a"] "models" {"m" {}}})))
  (is (= {:fleet [] :models {}} (mc/parse-fleet-models {}))))

(deftest probe-and-install-commands
  (testing "ollama probe hits the tags API and greps the tag"
    (let [cmd (mc/probe-cmd-for-model {"kind" "ollama" "ollama_tag" "gemma:4b"})]
      (is (str/includes? cmd "api/tags"))
      (is (str/includes? cmd "gemma:4b"))))
  (testing "comfyui checkpoint probe is a test -s on the file path"
    (is (= "test -s ~/comfyui/ckpt/f.safetensors"
           (mc/probe-cmd-for-model {"kind" "comfyui_checkpoint" "path" "ckpt" "filename" "f.safetensors"}))))
  (testing "unsupported kind → nil"
    (is (nil? (mc/probe-cmd-for-model {"kind" "mystery"}))))
  (testing "ollama install is an ollama pull; unsupported → nil"
    (is (= "ollama pull g:4b" (mc/resolve-install-cmd {"kind" "ollama" "ollama_tag" "g:4b"} "tok")))
    (is (nil? (mc/resolve-install-cmd {"kind" "nope"} "tok")))))

(deftest nomad-json-resolution
  (testing "node id resolved by :Name or :Meta/:fleet_node"
    (is (= "id2" (mc/resolve-node-id [{:Name "n1" :ID "id1"} {:Name "n2" :ID "id2"}] "n2")))
    (is (= "id3" (mc/resolve-node-id [{:Meta {:fleet_node "fn"} :ID "id3"}] "fn")))
    (is (nil? (mc/resolve-node-id [{:Name "n1" :ID "id1"}] "missing"))))
  (testing "alloc id resolves only a running allocation for the node"
    (is (= "a1" (mc/resolve-alloc-id [{:NodeName "n1" :ClientStatus "running" :ID "a1"}
                                      {:NodeName "n1" :ClientStatus "complete" :ID "a2"}] "n1")))
    (is (nil? (mc/resolve-alloc-id [{:NodeName "n1" :ClientStatus "complete" :ID "a2"}] "n1")))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-murakumo-cmd)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
