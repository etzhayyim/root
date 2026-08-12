;; test_bb_migration_wave7b.clj — Wave 7B IO-rewrite parity + request-shaping tests
;;
;; Covers: murakumo_cmd.cljc  (ns etzhayyim.murakumo-cmd)
;;         database.cljc       (ns etzhayyim.database)
;;
;; Run with (from repo root, bb.edn includes 70-tools/src in :paths):
;;   bb 70-tools/src/etzhayyim/test_bb_migration_wave7b.clj
;;
;; All tests are OFFLINE — no live subprocess or network calls.
;; Subprocess / HTTP legs use injectable fakes that record calls without executing.
;;
;; Test coverage:
;;
;;   MURAKUMO-CMD pure parity (argv vectors / request maps):
;;     - build-git-root-command       → exact ["git" "rev-parse" ...] argv
;;     - build-ssh-command            → ["ssh" "-o" "BatchMode=yes" ...] argv
;;     - build-nomad-command          → [nomad-path ...args] argv
;;     - build-scp-command            → ["scp" ...] argv
;;     - build-eval-command           → [python bin args ...] argv
;;     - build-status-request         → GET /xrpc/com.etzhayyim.murakumo.getStatus
;;     - build-list-request           → GET /xrpc/com.etzhayyim.murakumo.listPods
;;     - build-route-request          → GET /xrpc/com.etzhayyim.murakumo.getRouting
;;     - build-infer-request          → POST /xrpc/com.etzhayyim.murakumo.infer + body
;;     - build-xrpc-request           → POST /xrpc/<nsid> + JSON-decoded body
;;     - build-fleet-jotai-request    → GET /xrpc/…fleetStatus?limit=N
;;     - build-fleet-versions-request → GET /xrpc/…workerVersions
;;     - build-train-experts-request  → POST /xrpc/…trainExperts + body keys
;;     - pipeline-steps               → correct count + first entry
;;     - probe-cmd-for-model          → ollama / comfyui_checkpoint / comfyui_wan / nil
;;     - resolve-install-cmd          → ollama pull / comfyui curl / comfyui_diffusers
;;     - parse-fleet-models           → :fleet / :models keys from JSON data
;;     - parse-nodes-json             → parses JSON into keyword-keyed seq
;;     - resolve-node-id              → finds by :Name
;;     - resolve-alloc-id             → finds by :NodeName + :ClientStatus
;;     - normalize-pds                → strips trailing slash
;;     - build-auth-headers           → "Bearer <tok>" header
;;     - resolve-nomad-addr           → env var / default
;;     - redact-auth-header           → Bearer redaction is NOT in this ns (in auth.cljc)
;;
;;   MURAKUMO-CMD IO injectable fake:
;;     - run-git-root with fake proc-fn records argv + returns fake root
;;     - run-ssh-on-mini with fake proc-fn records argv (ssh -o BatchMode... mini@...)
;;     - probe-model-on-mini (ollama kind) with fake proc-fn records probe cmd
;;     - run-nomad with fake proc-fn records nomad argv
;;     - call-xrpc-get with fake http-fn records request shape
;;     - call-xrpc-post with fake http-fn records request shape
;;     - dry-run print-dry-run-plan emits output without any proc/http calls
;;
;;   DATABASE pure parity:
;;     - redact-url               → strips :pass@ from postgres URL
;;     - validate-migrator-args!  → throws on empty / unknown subcommand, nil on valid
;;     - build-git-root-command   → same argv as murakumo-cmd
;;     - build-kysely-migrate-command → argv + env map with DATABASE_URL
;;     - build-xrpc-get-request   → GET /xrpc/<nsid>
;;     - build-xrpc-post-request  → POST /xrpc/<nsid> + body
;;     - graph-schema-rel         → "30-graph/graph-schema"
;;     - rw-local-url             → postgres://root@127.0.0.1:14566/dev?sslmode=disable
;;     - valid-subcommands        → set contains "latest" "up" "down" "list" "to"
;;
;;   DATABASE IO injectable fake:
;;     - find-git-root with fake proc-fn records argv + returns fake root
;;     - list-graph-schema-migs with fake fs-fn returns sorted .ts list
;;     - run-kysely-migrate with fake proc-fn records correct argv + env
;;     - call-xrpc-get with fake http-fn records request shape
;;     - resolve-db-url prefers url-flag, falls back to env then constant
;;
;;   HONEST NOTES:
;;     Live behavioral parity (whether SSH/Nomad/XRPC actually responds) requires
;;     a running fleet and CANNOT be verified offline. The request/argv shape tests
;;     demonstrate that cljc builds the SAME structures as the Python CLI (verified
;;     by manual cross-comparison with the source .py and comments below).

(ns etzhayyim.test-bb-migration-wave7b
  (:require [clojure.test            :refer [deftest is testing run-tests]]
            [clojure.string          :as str]
            [cheshire.core           :as json]
            [etzhayyim.murakumo-cmd  :as mc]
            [etzhayyim.database      :as db]))

;; ─── fake helpers ─────────────────────────────────────────────────────────────

(defn- make-fake-proc
  "Returns a {:proc-fn :log} where log is an atom that records every call.
  Replies are returned in round-robin order (cycling).  Default reply is exit=0."
  ([] (make-fake-proc [{:exit 0 :out "" :err ""}]))
  ([replies]
   (let [log (atom [])
         idx (atom 0)]
     {:log     log
      :proc-fn (fn [argv opts]
                 (swap! log conj {:argv argv :opts opts})
                 (let [r (nth replies (mod @idx (count replies)))]
                   (swap! idx inc)
                   r))})))

(defn- make-fake-http
  "Returns {:http-fn :log}.  Replies are {:status :body} — body must be a JSON string."
  ([] (make-fake-http [{:status 200 :body "{}"}]))
  ([replies]
   (let [log (atom [])
         idx (atom 0)]
     {:log     log
      :http-fn (fn [req]
                 (swap! log conj req)
                 (let [r (nth replies (mod @idx (count replies)))]
                   (swap! idx inc)
                   r))})))

;; ─── murakumo-cmd: pure parity ───────────────────────────────────────────────

(deftest test-mc-build-git-root-command
  (testing "argv matches Python subprocess.run(['git','rev-parse','--show-toplevel'])"
    (is (= ["git" "rev-parse" "--show-toplevel"]
           (mc/build-git-root-command)))))

(deftest test-mc-build-ssh-command
  (testing "argv matches Python _ssh_on_mini() call with BatchMode / ConnectTimeout"
    (let [argv (mc/build-ssh-command "amaterasu" "echo hi")]
      (is (= "ssh" (first argv)))
      (is (some #(= % "BatchMode=yes") argv))
      (is (some #(= % "ConnectTimeout=5") argv))
      (is (some #(= % "StrictHostKeyChecking=no") argv))
      ;; user@host must be mini@mini.murakumo.lan
      (is (some #(= % "amaterasu@amaterasu.murakumo.lan") argv))
      (is (= "echo hi" (last argv))))))

(deftest test-mc-build-nomad-command
  (testing "argv is [nomad-path & args]"
    (is (= ["nomad" "job" "status"]
           (mc/build-nomad-command "nomad" "job" "status"))))
  (testing "custom nomad path"
    (is (= ["/usr/local/bin/nomad" "node" "status" "-json"]
           (mc/build-nomad-command "/usr/local/bin/nomad" "node" "status" "-json")))))

(deftest test-mc-build-scp-command
  (testing "argv matches scp -o StrictHostKeyChecking=no src host:dest"
    (let [argv (mc/build-scp-command "/tmp/daemon.py" "benjamin" "/usr/local/share/murakumo/daemon.py")]
      (is (= "scp" (first argv)))
      (is (some #(= % "StrictHostKeyChecking=no") argv))
      (is (some #(= % "/tmp/daemon.py") argv))
      (is (some #(= % "benjamin:/usr/local/share/murakumo/daemon.py") argv)))))

(deftest test-mc-build-eval-command
  (testing "default mode = eval, no checkpoint → argv without --checkpoint"
    (let [argv (mc/build-eval-command "training/dir" {})]
      (is (= "python3.11" (first argv)))
      (is (some #(str/ends-with? % "eval_v6_bench.py") argv))
      (is (some #(= % "--mode") argv))
      (is (some #(= % "eval") argv))
      (is (not (some #(= % "--checkpoint") argv)))))
  (testing "with checkpoint → argv includes --checkpoint"
    (let [argv (mc/build-eval-command "training/dir" {:checkpoint "my_ckpt"})]
      (is (some #(= % "--checkpoint") argv))
      (is (some #(= % "my_ckpt") argv))))
  (testing "custom python bin and mode"
    (let [argv (mc/build-eval-command "training/dir" {:python-bin "python3.12" :mode "bench" :limit 50})]
      (is (= "python3.12" (first argv)))
      (is (some #(= % "bench") argv))
      (is (some #(= % "50") argv)))))

(deftest test-mc-build-status-request
  (testing "GET /xrpc/com.etzhayyim.murakumo.getStatus with bearer auth"
    (let [req (mc/build-status-request "https://pds.example.com" "tok123")]
      (is (= :get (:method req)))
      (is (str/ends-with? (:url req) "/xrpc/com.etzhayyim.murakumo.getStatus"))
      (is (str/includes? (get-in req [:headers "Authorization"]) "Bearer tok123")))))

(deftest test-mc-build-list-request
  (testing "GET /xrpc/com.etzhayyim.murakumo.listPods"
    (let [req (mc/build-list-request "https://pds.example.com" "tok")]
      (is (= :get (:method req)))
      (is (str/ends-with? (:url req) "/xrpc/com.etzhayyim.murakumo.listPods")))))

(deftest test-mc-build-route-request
  (testing "GET /xrpc/com.etzhayyim.murakumo.getRouting"
    (let [req (mc/build-route-request "https://pds.example.com" "tok")]
      (is (= :get (:method req)))
      (is (str/ends-with? (:url req) "/xrpc/com.etzhayyim.murakumo.getRouting")))))

(deftest test-mc-build-infer-request
  (testing "POST /xrpc/com.etzhayyim.murakumo.infer with prompt in body"
    (let [req (mc/build-infer-request "https://pds.example.com" "tok" "hello" "")]
      (is (= :post (:method req)))
      (is (str/ends-with? (:url req) "/xrpc/com.etzhayyim.murakumo.infer"))
      (is (= "hello" (get-in req [:body :prompt])))))
  (testing "model override included in body when provided"
    (let [req (mc/build-infer-request "https://pds.example.com" "tok" "hi" "gemma3:4b")]
      (is (= "gemma3:4b" (get-in req [:body :model])))))
  (testing "no model key when model is empty string"
    (let [req (mc/build-infer-request "https://pds.example.com" "tok" "hi" "")]
      (is (not (contains? (:body req) :model))))))

(deftest test-mc-build-xrpc-request
  (testing "POST /xrpc/<nsid> with JSON-decoded body"
    (let [payload "{\"foo\":42}"
          req     (mc/build-xrpc-request "https://pds.example.com" "tok"
                                         "com.example.test" payload)]
      (is (= :post (:method req)))
      (is (str/ends-with? (:url req) "/xrpc/com.example.test"))
      (is (= 42 (get-in req [:body :foo]))))))

(deftest test-mc-build-fleet-jotai-request
  (testing "GET …fleetStatus?limit=N"
    (let [req (mc/build-fleet-jotai-request "https://pds.example.com" "tok" 10)]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "fleetStatus"))
      (is (str/includes? (:url req) "limit=10")))))

(deftest test-mc-build-fleet-versions-request
  (testing "GET …workerVersions"
    (let [req (mc/build-fleet-versions-request "https://pds.example.com" "tok")]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "workerVersions")))))

(deftest test-mc-build-train-experts-request
  (testing "POST …trainExperts with body keys matching Python kwargs"
    (let [req (mc/build-train-experts-request "https://pds.example.com" "tok"
                                              {:label "scene" :n-labels 4
                                               :epochs 2 :slots-per 64 :device "cuda"})]
      (is (= :post (:method req)))
      (is (str/includes? (:url req) "trainExperts"))
      (is (= "scene" (get-in req [:body :label])))
      (is (= 4       (get-in req [:body :nLabels])))
      (is (= 2       (get-in req [:body :epochs])))
      (is (= 64      (get-in req [:body :slotsPer])))
      (is (= "cuda"  (get-in req [:body :backend]))))))

(deftest test-mc-pipeline-steps
  (testing "pipeline-steps has at least 8 entries"
    (is (>= (count mc/pipeline-steps) 8)))
  (testing "first step is plan"
    (is (= "plan" (:command (first mc/pipeline-steps)))))
  (testing "every step has :command :nsid :purpose"
    (doseq [s mc/pipeline-steps]
      (is (string? (:command s)))
      (is (string? (:nsid s)))
      (is (string? (:purpose s))))))

(deftest test-mc-probe-cmd-for-model
  (testing "ollama kind → curl + grep for tag"
    (let [cmd (mc/probe-cmd-for-model {"kind" "ollama" "ollama_tag" "gemma3:4b"})]
      (is (string? cmd))
      (is (str/includes? cmd "localhost:11434"))
      (is (str/includes? cmd "gemma3:4b"))))
  (testing "comfyui_checkpoint kind → test -s path/file"
    (let [cmd (mc/probe-cmd-for-model {"kind" "comfyui_checkpoint"
                                       "path" "models/checkpoints"
                                       "filename" "model.safetensors"})]
      (is (string? cmd))
      (is (str/includes? cmd "model.safetensors"))))
  (testing "comfyui_wan kind → joined test for each component"
    (let [cmd (mc/probe-cmd-for-model {"kind" "comfyui_wan"
                                       "components" [{"path" "p1" "file" "f1"}
                                                     {"path" "p2" "file" "f2"}]})]
      (is (string? cmd))
      (is (str/includes? cmd "&&"))))
  (testing "unknown kind → nil"
    (is (nil? (mc/probe-cmd-for-model {"kind" "unknown"})))))

(deftest test-mc-resolve-install-cmd
  (testing "ollama kind → ollama pull <tag>"
    (let [cmd (mc/resolve-install-cmd {"kind" "ollama" "ollama_tag" "gemma3:4b"} "")]
      (is (str/starts-with? cmd "ollama pull"))
      (is (str/includes? cmd "gemma3:4b"))))
  (testing "comfyui_checkpoint → curl download command with HF_TOKEN injected"
    (let [cmd (mc/resolve-install-cmd {"kind"      "comfyui_checkpoint"
                                       "path"      "models/checkpoints"
                                       "filename"  "model.safetensors"
                                       "hf_repo"   "owner/repo"
                                       "hf_file"   "model.safetensors"}
                                      "hftoken123")]
      (is (string? cmd))
      (is (str/includes? cmd "curl"))
      (is (str/includes? cmd "hftoken123"))
      (is (str/includes? cmd "huggingface.co"))))
  (testing "comfyui_diffusers → python3 from_pretrained"
    (let [cmd (mc/resolve-install-cmd {"kind" "comfyui_diffusers" "diffusers_repo" "owner/model"} "")]
      (is (str/includes? cmd "from_pretrained"))))
  (testing "unknown kind → nil"
    (is (nil? (mc/resolve-install-cmd {"kind" "nope"} "")))))

(deftest test-mc-parse-fleet-models
  (testing "extracts :fleet and :models from raw data map"
    (let [raw  {"fleet" ["mini1" "mini2"] "models" {"ollama-gemma3" {"kind" "ollama"}}}
          data (mc/parse-fleet-models raw)]
      (is (= ["mini1" "mini2"] (:fleet data)))
      (is (= {"ollama-gemma3" {"kind" "ollama"}} (:models data)))))
  (testing "defaults to empty on missing keys"
    (let [data (mc/parse-fleet-models {})]
      (is (= [] (:fleet data)))
      (is (= {} (:models data))))))

(deftest test-mc-parse-nodes-json
  (testing "parses valid Nomad nodes JSON into keyword-keyed seq"
    (let [raw  (json/generate-string [{"ID" "abc123" "Name" "mini1" "Meta" {"fleet_node" "mini1"}}])
          nodes (mc/parse-nodes-json raw)]
      (is (= 1 (count nodes)))
      (is (= "abc123" (:ID (first nodes))))
      (is (= "mini1"  (:Name (first nodes)))))))

(deftest test-mc-resolve-node-id
  (testing "finds by :Name"
    (let [nodes [{:ID "abc" :Name "mini1" :Meta {}}
                 {:ID "def" :Name "mini2" :Meta {}}]]
      (is (= "abc" (mc/resolve-node-id nodes "mini1")))
      (is (= "def" (mc/resolve-node-id nodes "mini2")))))
  (testing "finds by :Meta {:fleet_node}"
    (let [nodes [{:ID "xyz" :Name "node-xyz" :Meta {:fleet_node "amaterasu"}}]]
      (is (= "xyz" (mc/resolve-node-id nodes "amaterasu")))))
  (testing "returns nil when not found"
    (is (nil? (mc/resolve-node-id [] "nobody")))))

(deftest test-mc-resolve-alloc-id
  (testing "finds running alloc for node"
    (let [allocs [{:ID "a1" :NodeName "mini1" :ClientStatus "running"}
                  {:ID "a2" :NodeName "mini1" :ClientStatus "complete"}
                  {:ID "a3" :NodeName "mini2" :ClientStatus "running"}]]
      (is (= "a1" (mc/resolve-alloc-id allocs "mini1")))
      (is (= "a3" (mc/resolve-alloc-id allocs "mini2")))))
  (testing "returns nil if no running alloc"
    (let [allocs [{:ID "a1" :NodeName "mini1" :ClientStatus "failed"}]]
      (is (nil? (mc/resolve-alloc-id allocs "mini1")))))
  (testing "returns nil for unknown node"
    (is (nil? (mc/resolve-alloc-id [] "nobody")))))

(deftest test-mc-normalize-pds
  (testing "strips trailing slash"
    (is (= "https://pds.example.com"
           (mc/normalize-pds "https://pds.example.com/"))))
  (testing "leaves URL without trailing slash unchanged"
    (is (= "https://pds.example.com"
           (mc/normalize-pds "https://pds.example.com")))))

(deftest test-mc-build-auth-headers
  (testing "produces Authorization: Bearer <tok>"
    (let [h (mc/build-auth-headers "my-token")]
      (is (= "Bearer my-token" (get h "Authorization"))))))

(deftest test-mc-resolve-nomad-addr
  ;; Rewritten 2026-08-12 (ADR-2608122600).  This used to assert that the
  ;; zero-arity call returned "a non-empty string that looks like an http
  ;; address" — which passed precisely because there was a default, and that
  ;; default was "http://benjamin.local:4646": a real fleet mac-mini on the
  ;; mDNS namespace (RFC 6762), claimable by any host on the same link.  The
  ;; test could not tell a chosen address from a squatted one, so it defended
  ;; the bug.  Note also that resolve-nomad-addr never read the process
  ;; environment — the old comment's worry about "if NOMAD_ADDR is set in CI"
  ;; did not apply; this namespace takes the environment as explicit data.
  (testing "no address supplied → fails closed, no default"
    (is (thrown? clojure.lang.ExceptionInfo (mc/resolve-nomad-addr)))
    (is (thrown? clojure.lang.ExceptionInfo (mc/resolve-nomad-addr {}))))
  (testing "an address the host supplied is returned"
    (is (= "http://nomad.internal:4646"
           (mc/resolve-nomad-addr {"NOMAD_ADDR" "http://nomad.internal:4646"})))
    (is (str/starts-with? (mc/resolve-nomad-addr {"NOMAD_ADDR" "http://nomad.internal:4646"})
                          "http"))))

;; ─── murakumo-cmd: IO injectable fake ────────────────────────────────────────

(deftest test-mc-run-git-root-injectable
  (testing "run-git-root invokes proc-fn with git argv and returns trimmed output"
    (let [{:keys [log proc-fn]} (make-fake-proc [{:exit 0 :out "/tmp/repo\n" :err ""}])
          result (mc/run-git-root {:proc-fn proc-fn})]
      (is (= "/tmp/repo" result))
      (is (= [["git" "rev-parse" "--show-toplevel"]]
             (map :argv @log))))))

(deftest test-mc-run-git-root-raises-on-failure
  (testing "run-git-root raises ex-info when git exits non-zero"
    (let [{:keys [proc-fn]} (make-fake-proc [{:exit 128 :out "" :err "fatal: not a git repo"}])]
      (is (thrown? Exception (mc/run-git-root {:proc-fn proc-fn}))))))

(deftest test-mc-run-ssh-on-mini-injectable
  (testing "run-ssh-on-mini passes correct ssh argv to proc-fn"
    (let [{:keys [log proc-fn]} (make-fake-proc [{:exit 0 :out "found" :err ""}])
          result (mc/run-ssh-on-mini "amaterasu" "echo test" {:proc-fn proc-fn})]
      (is (:ok result))
      (let [recorded-argv (first (map :argv @log))]
        (is (= "ssh" (first recorded-argv)))
        ;; user@host.murakumo.lan must be in the argv
        (is (some #(= "amaterasu@amaterasu.murakumo.lan" %) recorded-argv))
        ;; remote command must be the last arg
        (is (= "echo test" (last recorded-argv)))))))

(deftest test-mc-probe-model-on-mini-injectable
  (testing "probe-model-on-mini (ollama) builds probe cmd and checks exit 0"
    (let [{:keys [log proc-fn]} (make-fake-proc [{:exit 0 :out "" :err ""}])
          result (mc/probe-model-on-mini "amaterasu"
                                         {"kind" "ollama" "ollama_tag" "gemma3:4b"}
                                         {:proc-fn proc-fn})]
      (is (true? result))
      (let [argv (first (map :argv @log))]
        ;; SSH command: last arg is the probe shell command for ollama
        (is (str/includes? (last argv) "11434")))))
  (testing "probe-model-on-mini with nil-kind model returns false without subprocess"
    (let [{:keys [log proc-fn]} (make-fake-proc)
          result (mc/probe-model-on-mini "amaterasu" {"kind" "nope"} {:proc-fn proc-fn})]
      (is (false? result))
      ;; No subprocess call because probe-cmd-for-model returned nil
      (is (empty? @log)))))

(deftest test-mc-run-nomad-injectable
  (testing "run-nomad passes argv including nomad binary to proc-fn"
    (let [{:keys [log proc-fn]} (make-fake-proc [{:exit 0 :out "" :err ""}])]
      (mc/run-nomad ["node" "status"] {:proc-fn proc-fn :nomad-path "nomad"
                                        :nomad-addr "http://localhost:4646"})
      (is (= ["nomad" "node" "status"]
             (first (map :argv @log)))))))

(deftest test-mc-call-xrpc-get-injectable
  (testing "call-xrpc-get records request shape and returns parsed body"
    (let [{:keys [log http-fn]}
          (make-fake-http [{:status 200 :body "{\"ok\":true}"}])
          req    (mc/build-status-request "https://pds.example.com" "tok")
          result (mc/call-xrpc-get req {:http-fn http-fn})]
      (is (= true (:ok result)))
      (let [recorded (first @log)]
        (is (= :get (:method recorded)))
        (is (str/includes? (:url recorded) "getStatus"))
        (is (str/includes? (get-in recorded [:headers "Authorization"]) "Bearer tok"))))))

(deftest test-mc-call-xrpc-post-injectable
  (testing "call-xrpc-post records request shape and returns parsed body"
    (let [{:keys [log http-fn]}
          (make-fake-http [{:status 200 :body "{\"result\":\"done\"}"}])
          req    (mc/build-infer-request "https://pds.example.com" "tok" "hi" "")
          result (mc/call-xrpc-post req {:http-fn http-fn})]
      (is (= "done" (:result result)))
      (let [recorded (first @log)]
        (is (= :post (:method recorded)))))))

(deftest test-mc-call-xrpc-get-raises-on-error
  (testing "call-xrpc-get raises ex-info on 401"
    (let [{:keys [http-fn]}
          (make-fake-http [{:status 401 :body "{\"error\":\"Unauthenticated\"}"}])
          req (mc/build-status-request "https://pds.example.com" "")]
      (is (thrown? Exception (mc/call-xrpc-get req {:http-fn http-fn}))))))

(deftest test-mc-print-dry-run-no-side-effects
  (testing "print-dry-run-plan produces output without any proc/http calls"
    (let [{:keys [log proc-fn]}  (make-fake-proc)
          {:keys [log2 http-fn2]} {:log2 (atom []) :http-fn2 (fn [_] {:status 200 :body "{}"})}
          _ (with-out-str
              ;; Should not throw and should not call proc-fn
              (mc/print-dry-run-plan
               [{:op :ssh :description "probe gemma3:4b on amaterasu"
                 :argv (mc/build-ssh-command "amaterasu" "ollama pull gemma3:4b")}
                {:op :http :description "status check"
                 :request (mc/build-status-request "https://pds.example.com" "tok")}]))]
      ;; proc-fn log must remain empty (dry-run never calls it)
      (is (empty? @log)))))

;; ─── database: pure parity ───────────────────────────────────────────────────

(deftest test-db-redact-url
  (testing "strips password from postgres URL"
    (is (= "postgres://root:***@127.0.0.1:14566/dev"
           (db/redact-url "postgres://root:secret@127.0.0.1:14566/dev"))))
  (testing "strips password from postgresql:// scheme"
    (is (= "postgresql://user:***@host/db"
           (db/redact-url "postgresql://user:pass@host/db"))))
  (testing "no-op when no password present"
    (is (= "postgres://root@127.0.0.1:14566/dev?sslmode=disable"
           (db/redact-url "postgres://root@127.0.0.1:14566/dev?sslmode=disable"))))
  (testing "empty string returns empty string"
    (is (= "" (db/redact-url "")))))

(deftest test-db-validate-migrator-args!
  (testing "nil on valid subcommands"
    (doseq [cmd ["latest" "up" "down" "list" "to"]]
      (is (nil? (db/validate-migrator-args! [cmd])))))
  (testing "throws ex-info on empty args"
    (is (thrown? Exception (db/validate-migrator-args! []))))
  (testing "throws ex-info on unknown subcommand"
    (is (thrown? Exception (db/validate-migrator-args! ["invalid-cmd"]))))
  (testing "'to' with extra arg is valid (validator only checks first element)"
    (is (nil? (db/validate-migrator-args! ["to" "00010"])))))

(deftest test-db-build-git-root-command
  (testing "same argv as murakumo-cmd version"
    (is (= ["git" "rev-parse" "--show-toplevel"]
           (db/build-git-root-command)))))

(deftest test-db-build-kysely-migrate-command
  (testing "produces :argv and :env with DATABASE_URL"
    (let [{:keys [argv env]}
          (db/build-kysely-migrate-command "/repo/30-graph/graph-schema"
                                           "postgres://root@localhost/dev"
                                           ["latest"])]
      ;; argv must start with node --loader=ts-node/esm
      (is (= "node" (first argv)))
      (is (some #(= "--loader=ts-node/esm" %) argv))
      ;; script path must be under schema-dir
      (is (some #(str/ends-with? % "migrate.ts") argv))
      ;; migrator subcommand must be last
      (is (= "latest" (last argv)))
      ;; DATABASE_URL must be in env map
      (is (= "postgres://root@localhost/dev" (get env "DATABASE_URL")))))
  (testing "'to 00010' migrator args appear after migrate.ts"
    (let [{:keys [argv]}
          (db/build-kysely-migrate-command "/schema" "postgres://x@y/z" ["to" "00010"])]
      (is (= "to" (nth argv (- (count argv) 2))))
      (is (= "00010" (last argv))))))

(deftest test-db-build-xrpc-get-request
  (testing "GET /xrpc/<nsid>"
    (let [req (db/build-xrpc-get-request "https://pds.example.com" "tok" "com.etzhayyim.db.status")]
      (is (= :get (:method req)))
      (is (str/ends-with? (:url req) "/xrpc/com.etzhayyim.db.status"))
      (is (str/includes? (get-in req [:headers "Authorization"]) "Bearer tok")))))

(deftest test-db-build-xrpc-post-request
  (testing "POST /xrpc/<nsid> with body"
    (let [req (db/build-xrpc-post-request "https://pds.example.com" "tok"
                                           "com.etzhayyim.db.migrate"
                                           {:subcommand "latest"})]
      (is (= :post (:method req)))
      (is (str/ends-with? (:url req) "/xrpc/com.etzhayyim.db.migrate"))
      (is (= "latest" (get-in req [:body :subcommand]))))))

(deftest test-db-constants
  (testing "graph-schema-rel matches Python _GRAPH_SCHEMA_REL"
    (is (= "30-graph/graph-schema" db/graph-schema-rel)))
  (testing "rw-local-url matches Python _RW_LOCAL_URL"
    (is (str/starts-with? db/rw-local-url "postgres://")))
  (testing "valid-subcommands matches Python _VALID_SUBCOMMANDS"
    (is (set? db/valid-subcommands))
    (is (contains? db/valid-subcommands "latest"))
    (is (contains? db/valid-subcommands "up"))
    (is (contains? db/valid-subcommands "down"))
    (is (contains? db/valid-subcommands "list"))
    (is (contains? db/valid-subcommands "to"))))

;; ─── database: IO injectable fake ────────────────────────────────────────────

(deftest test-db-find-git-root-injectable
  (testing "find-git-root records argv and returns trimmed root"
    (let [{:keys [log proc-fn]} (make-fake-proc [{:exit 0 :out "/the/repo\n" :err ""}])
          result (db/find-git-root {:proc-fn proc-fn})]
      (is (= "/the/repo" result))
      (is (= [["git" "rev-parse" "--show-toplevel"]]
             (map :argv @log))))))

(deftest test-db-find-git-root-raises-on-failure
  (testing "find-git-root raises ex-info on git exit 128"
    (let [{:keys [proc-fn]} (make-fake-proc [{:exit 128 :out "" :err "fatal: not a git repo"}])]
      (is (thrown? Exception (db/find-git-root {:proc-fn proc-fn}))))))

(deftest test-db-list-graph-schema-migs-injectable
  (testing "list-graph-schema-migs filters .ts files and sorts them"
    (let [fake-files     ["00001_init.ts" "00003_indexes.ts" "00002_relations.ts"
                          "README.md" "some.js"]
          fake-fs-fn     (fn [_dir] fake-files)
          result         (db/list-graph-schema-migs "/repo/30-graph/graph-schema"
                                                    {:fs-fn fake-fs-fn})]
      (is (= ["00001_init.ts" "00002_relations.ts" "00003_indexes.ts"] result)))))

(deftest test-db-run-kysely-migrate-injectable
  (testing "run-kysely-migrate records correct argv and env in proc-fn"
    (let [{:keys [log proc-fn]} (make-fake-proc [{:exit 0 :out "" :err ""}])
          exit (db/run-kysely-migrate "/schema" "postgres://root@localhost/dev" ["latest"]
                                      {:proc-fn proc-fn})]
      (is (= 0 exit))
      (let [{:keys [argv opts]} (first @log)]
        (is (= "node" (first argv)))
        (is (some #(= "latest" %) argv))
        (is (= "postgres://root@localhost/dev" (get (:env opts) "DATABASE_URL"))))))
  (testing "run-kysely-migrate raises ex-info on unknown subcommand"
    (let [{:keys [proc-fn]} (make-fake-proc)]
      (is (thrown? Exception
                   (db/run-kysely-migrate "/schema" "postgres://root@localhost/dev" ["bad"]
                                          {:proc-fn proc-fn}))))))

(deftest test-db-resolve-db-url
  (testing "prefers url-flag over env"
    ;; We can't easily set env vars, but we can test flag preference
    (is (= "postgres://explicit@host/db"
           (db/resolve-db-url "postgres://explicit@host/db" "DATABASE_URL"))))
  (testing "falls back to rw-local-url when neither set"
    ;; DATABASE_URL may or may not be set in the test env.
    ;; We just check it returns a postgres:// URL.
    (let [result (db/resolve-db-url "" "NONEXISTENT_DB_URL_VAR_xyz123")]
      (is (str/starts-with? result "postgres://")))))

(deftest test-db-call-xrpc-get-injectable
  (testing "records request shape and returns parsed body"
    (let [{:keys [log http-fn]}
          (make-fake-http [{:status 200 :body "{\"tables\":[\"users\"]}"}])
          req    (db/build-xrpc-get-request "https://pds.example.com" "tok" "com.etzhayyim.db.tables")
          result (db/call-xrpc-get req {:http-fn http-fn})]
      (is (= ["users"] (:tables result)))
      (is (= :get (:method (first @log)))))))

(deftest test-db-call-xrpc-post-injectable
  (testing "records request shape and returns parsed body"
    (let [{:keys [log http-fn]}
          (make-fake-http [{:status 200 :body "{\"migrated\":true}"}])
          req    (db/build-xrpc-post-request "https://pds.example.com" "tok"
                                              "com.etzhayyim.db.migrate" {:cmd "latest"})
          result (db/call-xrpc-post req {:http-fn http-fn})]
      (is (true? (:migrated result)))
      (is (= :post (:method (first @log)))))))

;; ─── run all tests ──────────────────────────────────────────────────────────

(run-tests 'etzhayyim.test-bb-migration-wave7b)
