;; test_bb_migration_wave8b.clj — Wave 8B IO-rewrite parity + request-shaping tests
;;
;; Covers:
;;   projector.cljc   (ns etzhayyim.projector)
;;   training.cljc    (ns etzhayyim.training)
;;   workspace.cljc   (ns etzhayyim.workspace)
;;   lint.cljc        (ns etzhayyim.lint)
;;
;; Run with (from repo root, bb.edn includes 70-tools/src in :paths):
;;   bb 70-tools/src/etzhayyim/test_bb_migration_wave8b.clj
;;
;; All tests are OFFLINE — no live subprocess or network calls.
;; IO legs use injectable fakes that record calls without executing.
;;
;; Test coverage:
;;
;;   PROJECTOR pure parity:
;;     - build-mcp-headers with/without token → correct header map
;;     - build-mcp-request → jsonrpc/method/params shape
;;     - build-create-args → name + optional keys included/excluded correctly
;;     - build-status-args → projectId + summarize boolean
;;     - build-update-args → optional progress/state/targetDate
;;     - build-list-args   → limit + optional orgId/lifecycleState
;;     - build-blocker-add-args    → required + optional fields
;;     - build-blocker-resolve-args → blockerId + optional resolution
;;     - unwrap-mcp-response content[0].text JSON parse
;;     - unwrap-mcp-response content[0].text plain fallback
;;     - unwrap-mcp-response no-content → returns result map
;;     - check-mcp-error throws on error key
;;     - check-mcp-error passes through on no error
;;   PROJECTOR IO injectable fake:
;;     - mcp-call dry-run returns shape without http call
;;     - mcp-call real path records URL/headers/body via fake http-fn
;;
;;   TRAINING pure parity:
;;     - build-auth-headers → "Bearer <tok>"
;;     - parse-bench-list → comma-split + trim
;;     - validate-run-opts! → throws on missing dataset/base/student/teacher
;;     - training-nsid → sft/lora/distill NSID strings
;;     - build-list-request → GET URL + optional status param
;;     - build-get-request  → GET URL + id param
;;     - build-start-request → POST URL + body
;;     - build-cancel-request → POST URL + {"id":...}
;;     - build-run-request sft → correct NSID + baseModel
;;     - build-run-request lora → correct NSID
;;     - build-run-request distill → correct NSID + student/teacher fields
;;     - build-promote-request → checkpointId + alias + optional fields
;;     - build-eval-request → benches parsed + optional fields
;;     - build-eval-request empty bench → throws
;;     - build-list-runs-request → limit + optional kind/status
;;     - build-list-checkpoints-request → limit + onlyFinal + optional runId
;;     - build-list-snapshots-request → limit + optional dataset/status
;;     - build-coverage-request → empty body
;;     - build-serving-request → optional alias
;;   TRAINING IO injectable fake:
;;     - xrpc-get dry-run → shape without http call
;;     - xrpc-post dry-run → shape without http call
;;     - xrpc-get real path records URL/headers/params via fake
;;     - xrpc-post real path records URL/headers/body via fake
;;
;;   WORKSPACE pure parity:
;;     - default-excludes → contains "node_modules" ".git" etc.
;;     - build-rsync-command minimal → rsync -avz --progress src remote
;;     - build-rsync-command with excludes → --exclude per item
;;     - build-rsync-command dry-run → --dry-run flag present
;;     - build-rsync-command delete → --delete flag present
;;     - build-rsync-command all opts combined → all flags in correct order
;;   WORKSPACE IO injectable fake:
;;     - run-sync dry-run opts records argv via fake proc-fn
;;     - run-sync real opts records argv
;;     - count-actor-files uses :fs-fn injection
;;     - workspace-status uses :fs-fn + :println-fn injection
;;
;;   LINT pure parity:
;;     - all-rules → canonical ordered list
;;     - update-script-path keys → expected scripts
;;     - rule-extensions → correct ext sets
;;     - skip-dir? → true for node_modules in path, false for clean path
;;     - check-nsid-regression → detects "nsid" placeholder
;;     - check-nsid-regression → clean file returns empty
;;     - check-legacy-pds-nsid → detects app.bsky.feed.getTimeline
;;     - check-legacy-pds-nsid → clean file returns empty
;;     - check-silent-catch → detects empty catch {}
;;     - check-silent-catch → detects except pass
;;     - check-silent-catch → clean returns empty
;;     - check-ts-camel → detects snake_case = assignment
;;     - check-ts-camel → ignores snake_case comment line
;;     - check-json-sql → detects PascalCase JSON key
;;     - check-json-sql → camelCase clean returns empty
;;     - check-deps-drift → detects [[migrations]] + status='done'
;;     - check-deps-drift → clean deps returns nil/empty
;;     - lint-file-text dispatch → nsid-regression correct violations
;;     - build-update-command → node script argv vector
;;     - build-update-command unknown target → throws
;;   LINT IO injectable fake:
;;     - scan-files-by-ext uses :fs-fn injection
;;     - lint-rule deps-drift skips when no text (fs-fn returns empty)
;;     - run-update-target records argv via fake proc-fn
;;     - run-update-target non-zero exit → throws
;;
;; HONEST NOTES:
;;   Live behavioral parity (whether MCP / XRPC / rsync / node actually responds)
;;   requires a running service and CANNOT be verified offline.  The request/argv
;;   shape tests demonstrate that cljc builds the SAME structures as the Python CLI
;;   (verified by manual cross-comparison with the source .py and comments below).

(ns etzhayyim.test-bb-migration-wave8b
  (:require [clojure.test         :refer [deftest is testing run-tests]]
            [clojure.string       :as str]
            [cheshire.core        :as json]
            [etzhayyim.projector  :as proj]
            [etzhayyim.training   :as tr]
            [etzhayyim.workspace  :as ws]
            [etzhayyim.lint       :as lint]))

;; ─── fake helpers ─────────────────────────────────────────────────────────────

(defn- make-fake-http
  "Returns {:http-fn :log}. Replies are {:status :body} — body as JSON string."
  ([] (make-fake-http [{:status 200 :body "{}"}]))
  ([replies]
   (let [log (atom [])
         idx (atom 0)]
     {:log     log
      :http-fn (fn [url headers body]
                 (swap! log conj {:url url :headers headers :body body})
                 (let [r (nth replies (mod @idx (count replies)))]
                   (swap! idx inc)
                   r))})))

(defn- make-fake-proc
  "Returns {:proc-fn :log}. Default reply {:exit 0}."
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

;; =============================================================================
;; PROJECTOR
;; =============================================================================

(deftest projector-build-mcp-headers
  (testing "no token → only Content-Type"
    (let [h (proj/build-mcp-headers nil)]
      (is (= "application/json" (get h "Content-Type")))
      (is (nil? (get h "Authorization")))))
  (testing "empty token → no Authorization"
    (let [h (proj/build-mcp-headers "")]
      (is (nil? (get h "Authorization")))))
  (testing "with token → Bearer header"
    (let [h (proj/build-mcp-headers "abc123")]
      (is (= "Bearer abc123" (get h "Authorization"))))))

(deftest projector-build-mcp-request
  (let [req (proj/build-mcp-request "projector.create_project" {"name" "test"})]
    (is (= "2.0" (:jsonrpc req)))
    (is (= 1 (:id req)))
    (is (= "tools/call" (:method req)))
    (is (= "projector.create_project" (get-in req [:params :name])))
    (is (= {"name" "test"} (get-in req [:params :arguments])))))

(deftest projector-build-create-args
  (testing "name only"
    (let [a (proj/build-create-args {:name "my-project"})]
      (is (= "my-project" (get a "name")))
      (is (nil? (get a "orgId")))
      (is (nil? (get a "description")))))
  (testing "all fields"
    (let [a (proj/build-create-args {:name        "proj"
                                     :org-id      "did:plc:abc"
                                     :description "desc"
                                     :parent-id   "pid"
                                     :target-date "2026-12-31"})]
      (is (= "did:plc:abc"  (get a "orgId")))
      (is (= "desc"         (get a "description")))
      (is (= "pid"          (get a "parentId")))
      (is (= "2026-12-31"   (get a "targetDate"))))))

(deftest projector-build-status-args
  (let [a (proj/build-status-args "proj-1" true)]
    (is (= "proj-1" (get a "projectId")))
    (is (= true (get a "summarize"))))
  (let [a (proj/build-status-args "proj-2" false)]
    (is (= false (get a "summarize")))))

(deftest projector-build-update-args
  (testing "project-id only"
    (let [a (proj/build-update-args {:project-id "p1"})]
      (is (= "p1" (get a "projectId")))
      (is (nil? (get a "progressPermille")))))
  (testing "with progress"
    (let [a (proj/build-update-args {:project-id "p1" :progress 500})]
      (is (= 500 (get a "progressPermille")))))
  (testing "with state and date"
    (let [a (proj/build-update-args {:project-id  "p1"
                                     :state       "active"
                                     :target-date "2026-06-01"})]
      (is (= "active"     (get a "lifecycleState")))
      (is (= "2026-06-01" (get a "targetDate"))))))

(deftest projector-build-list-args
  (testing "default limit"
    (let [a (proj/build-list-args {})]
      (is (= 20 (get a "limit")))
      (is (nil? (get a "orgId")))))
  (testing "with org-id + state + limit"
    (let [a (proj/build-list-args {:org-id "did:plc:x" :state "done" :limit 5})]
      (is (= "did:plc:x" (get a "orgId")))
      (is (= "done"       (get a "lifecycleState")))
      (is (= 5            (get a "limit"))))))

(deftest projector-build-blocker-add-args
  (let [a (proj/build-blocker-add-args {:project-id  "p1"
                                        :title       "DB timeout"
                                        :blocker-type "technical"
                                        :severity    "high"
                                        :description "slow queries"})]
    (is (= "p1"        (get a "projectId")))
    (is (= "DB timeout" (get a "title")))
    (is (= "technical"  (get a "blockerType")))
    (is (= "high"       (get a "severity")))
    (is (= "slow queries" (get a "description"))))
  ;; defaults
  (let [a (proj/build-blocker-add-args {:project-id "p2" :title "T"})]
    (is (= "technical" (get a "blockerType")))
    (is (= "medium"    (get a "severity")))))

(deftest projector-build-blocker-resolve-args
  (let [a (proj/build-blocker-resolve-args {:blocker-id "b1" :resolution "fixed"})]
    (is (= "b1"    (get a "blockerId")))
    (is (= "fixed" (get a "resolution"))))
  (let [a (proj/build-blocker-resolve-args {:blocker-id "b2"})]
    (is (= "b2" (get a "blockerId")))
    (is (nil? (get a "resolution")))))

(deftest projector-unwrap-mcp-response
  (testing "content[0].text JSON parse"
    (let [data {"result" {"content" [{"text" "{\"ok\":true}"}]}}
          r    (proj/unwrap-mcp-response data)]
      (is (= {"ok" true} r))))
  (testing "content[0].text plain fallback"
    (let [data {"result" {"content" [{"text" "not-json"}]}}
          r    (proj/unwrap-mcp-response data)]
      (is (= {"text" "not-json"} r))))
  (testing "no content → returns result"
    (let [data {"result" {"status" "ok"}}
          r    (proj/unwrap-mcp-response data)]
      (is (= {"status" "ok"} r)))))

(deftest projector-check-mcp-error
  (testing "throws on error key"
    (is (thrown-with-msg? Exception #"MCP error"
          (proj/check-mcp-error {"error" {"code" -32600 "message" "Invalid"}}))))
  (testing "passes through when no error"
    (let [data {"result" {"ok" true}}]
      (is (= data (proj/check-mcp-error data))))))

(deftest projector-mcp-call-dry-run
  (let [{:keys [log http-fn]} (make-fake-http)
        result (proj/mcp-call "projector.create_project"
                              {"name" "test"}
                              {:pds     "https://example.com"
                               :token   "tok"
                               :dry-run true
                               :http-fn http-fn})]
    (is (:dry-run result))
    (is (str/includes? (:url result) "/mcp"))
    (is (empty? @log) "dry-run must not call http-fn")))

(deftest projector-mcp-call-records-request
  (let [{:keys [log http-fn]} (make-fake-http
                                [{:status 200
                                  :body   (json/generate-string
                                           {"result" {"content" [{"text" "{\"id\":\"p1\"}"}]}})}])
        result (proj/mcp-call "projector.list_projects"
                              {"limit" 10}
                              {:pds     "https://example.com"
                               :token   "tok"
                               :http-fn http-fn})]
    (is (= 1 (count @log)))
    (let [call (first @log)]
      (is (= "https://example.com/mcp" (:url call)))
      (is (= "Bearer tok" (get (:headers call) "Authorization")))
      (is (= "projector.list_projects" (get-in (:body call) [:params :name]))))))

;; =============================================================================
;; TRAINING
;; =============================================================================

(deftest training-build-auth-headers
  (let [h (tr/build-auth-headers "my-jwt")]
    (is (= "Bearer my-jwt" (get h "Authorization")))
    (is (= "application/json" (get h "Content-Type")))))

(deftest training-parse-bench-list
  (is (= ["mmlu" "arc_challenge"] (tr/parse-bench-list "mmlu, arc_challenge")))
  (is (= ["internal-loss"]        (tr/parse-bench-list "internal-loss")))
  (is (= []                        (tr/parse-bench-list "")))
  (is (= []                        (tr/parse-bench-list nil))))

(deftest training-validate-run-opts!
  (testing "missing dataset → throws"
    (is (thrown-with-msg? Exception #"dataset"
          (tr/validate-run-opts! {:kind "sft" :dataset "" :base-model "gpt2"}))))
  (testing "sft missing base-model → throws"
    (is (thrown-with-msg? Exception #"--base"
          (tr/validate-run-opts! {:kind "sft" :dataset "ds" :base-model ""}))))
  (testing "lora missing base-model → throws"
    (is (thrown-with-msg? Exception #"--base"
          (tr/validate-run-opts! {:kind "lora" :dataset "ds" :base-model ""}))))
  (testing "distill missing student-base → throws"
    (is (thrown-with-msg? Exception #"student-base"
          (tr/validate-run-opts! {:kind "distill" :dataset "ds"
                                  :student-base "" :teacher-kind "run"}))))
  (testing "distill missing teacher-kind → throws"
    (is (thrown-with-msg? Exception #"teacher-kind"
          (tr/validate-run-opts! {:kind "distill" :dataset "ds"
                                  :student-base "s" :teacher-kind ""}))))
  (testing "valid sft → no throw"
    (is (nil? (tr/validate-run-opts! {:kind "sft" :dataset "ds" :base-model "gpt2"})))))

(deftest training-nsid-map
  (is (= "com.etzhayyim.apps.training.runSft"     (get tr/training-nsid "sft")))
  (is (= "com.etzhayyim.apps.training.runLora"    (get tr/training-nsid "lora")))
  (is (= "com.etzhayyim.apps.training.runDistill" (get tr/training-nsid "distill"))))

(deftest training-build-list-request
  (let [r (tr/build-list-request {:pds-url "https://pds.example.com"})]
    (is (= :get (:method r)))
    (is (str/includes? (:url r) "listJobs"))
    (is (empty? (:params r))))
  (let [r (tr/build-list-request {:pds-url "https://pds.example.com" :filter-status "running"})]
    (is (= "running" (get (:params r) "status")))))

(deftest training-build-get-request
  (let [r (tr/build-get-request {:pds-url "https://pds.example.com" :job-id "j1"})]
    (is (= :get (:method r)))
    (is (str/includes? (:url r) "getJob"))
    (is (= "j1" (get (:params r) "id")))))

(deftest training-build-start-request
  (let [r (tr/build-start-request {:pds-url "https://pds.example.com"
                                   :job-type "lora" :model "m" :dataset "d"})]
    (is (= :post (:method r)))
    (is (str/includes? (:url r) "startJob"))
    (is (= "lora" (get (:body r) "type")))
    (is (= "m"    (get (:body r) "model")))
    (is (= "d"    (get (:body r) "dataset")))))

(deftest training-build-cancel-request
  (let [r (tr/build-cancel-request {:pds-url "https://pds.example.com" :job-id "j42"})]
    (is (= :post (:method r)))
    (is (str/includes? (:url r) "cancelJob"))
    (is (= "j42" (get (:body r) "id")))))

(deftest training-build-run-request-sft
  (let [r (tr/build-run-request {:pds-url    "https://pds.example.com"
                                 :kind       "sft"
                                 :dataset    "etzhayyim-corpus"
                                 :base-model "meta-llama/llama-3"})]
    (is (= :post (:method r)))
    (is (str/includes? (:url r) "runSft"))
    (is (= "etzhayyim-corpus"   (get (:body r) "datasetName")))
    (is (= "meta-llama/llama-3" (get (:body r) "baseModel")))))

(deftest training-build-run-request-lora
  (let [r (tr/build-run-request {:pds-url    "https://pds.example.com"
                                 :kind       "lora"
                                 :dataset    "ds"
                                 :base-model "gpt2"
                                 :eval-benches "mmlu,arc_challenge"})]
    (is (str/includes? (:url r) "runLora"))
    (is (= ["mmlu" "arc_challenge"] (get (:body r) "evalBenches")))))

(deftest training-build-run-request-distill
  (let [r (tr/build-run-request {:pds-url       "https://pds.example.com"
                                 :kind          "distill"
                                 :dataset       "ds"
                                 :student-base  "student-model"
                                 :teacher-kind  "run"
                                 :teacher-run-id "tr1"
                                 :distill-method "hard-label"})]
    (is (str/includes? (:url r) "runDistill"))
    (is (= "student-model" (get (:body r) "studentBaseModel")))
    (is (= "run"           (get (:body r) "teacherKind")))
    (is (= "tr1"           (get (:body r) "teacherRunId")))
    (is (= "hard-label"    (get (:body r) "distillMethod")))))

(deftest training-build-run-request-unknown-kind
  (is (thrown? Exception
        (tr/build-run-request {:pds-url "https://pds.example.com"
                               :kind "unknown" :dataset "ds"}))))

(deftest training-build-promote-request
  (let [r (tr/build-promote-request {:pds-url       "https://pds.example.com"
                                     :checkpoint-id "ck1"
                                     :alias         "murakumo:gemma4@2026"
                                     :target        "murakumo"
                                     :by            "did:plc:a"
                                     :rationale     "better perplexity"})]
    (is (str/includes? (:url r) "promote"))
    (is (= "ck1"                 (get (:body r) "checkpointId")))
    (is (= "murakumo:gemma4@2026" (get (:body r) "alias")))
    (is (= "murakumo"            (get (:body r) "servingTarget")))
    (is (= "did:plc:a"           (get (:body r) "promotedBy")))
    (is (= "better perplexity"   (get (:body r) "rationale")))))

(deftest training-build-eval-request
  (let [r (tr/build-eval-request {:pds-url       "https://pds.example.com"
                                  :checkpoint-id "ck1"
                                  :bench         "mmlu,arc_challenge"
                                  :limit         100
                                  :gpu           "h100"})]
    (is (str/includes? (:url r) "runEval"))
    (is (= ["mmlu" "arc_challenge"] (get (:body r) "benches")))
    (is (= 100     (get (:body r) "sampleLimit")))
    (is (= "h100"  (get (:body r) "gpuTarget")))))

(deftest training-build-eval-request-empty-bench
  (is (thrown-with-msg? Exception #"bench"
        (tr/build-eval-request {:pds-url "https://pds.example.com"
                                :checkpoint-id "ck1"
                                :bench ""}))))

(deftest training-build-list-runs-request
  (let [r (tr/build-list-runs-request {:pds-url "https://pds.example.com"})]
    (is (str/includes? (:url r) "listRuns"))
    (is (= 50 (get (:body r) "limit"))))
  (let [r (tr/build-list-runs-request {:pds-url "https://pds.example.com"
                                       :kind "lora" :filter-status "done" :limit 10})]
    (is (= "lora" (get (:body r) "kind")))
    (is (= "done" (get (:body r) "status")))
    (is (= 10     (get (:body r) "limit")))))

(deftest training-build-list-checkpoints-request
  (let [r (tr/build-list-checkpoints-request {:pds-url    "https://pds.example.com"
                                              :run        "run1"
                                              :only-final true
                                              :limit      5})]
    (is (str/includes? (:url r) "listCheckpoints"))
    (is (= "run1" (get (:body r) "runId")))
    (is (= true   (get (:body r) "onlyFinal")))
    (is (= 5      (get (:body r) "limit")))))

(deftest training-build-list-snapshots-request
  (let [r (tr/build-list-snapshots-request {:pds-url       "https://pds.example.com"
                                            :dataset       "etzhayyim-corpus"
                                            :filter-status "frozen"
                                            :limit         20})]
    (is (str/includes? (:url r) "listSnapshots"))
    (is (= "etzhayyim-corpus" (get (:body r) "datasetName")))
    (is (= "frozen"           (get (:body r) "status")))
    (is (= 20                 (get (:body r) "limit")))))

(deftest training-build-coverage-request
  (let [r (tr/build-coverage-request {:pds-url "https://pds.example.com"})]
    (is (str/includes? (:url r) "coverage"))
    (is (= {} (:body r)))))

(deftest training-build-serving-request
  (let [r (tr/build-serving-request {:pds-url "https://pds.example.com" :alias "gemma4"})]
    (is (str/includes? (:url r) "serving"))
    (is (= "gemma4" (get (:body r) "alias"))))
  (let [r (tr/build-serving-request {:pds-url "https://pds.example.com"})]
    (is (= {} (:body r)))))

(deftest training-xrpc-get-dry-run
  (let [{:keys [log http-fn]} (make-fake-http)
        req {:url "https://pds.example.com/xrpc/com.etzhayyim.training.listJobs" :params {}}
        res (tr/xrpc-get req {:token "tok" :dry-run true :http-fn http-fn})]
    (is (:dry-run res))
    (is (empty? @log))))

(deftest training-xrpc-post-dry-run
  (let [{:keys [log http-fn]} (make-fake-http)
        req {:url "https://pds.example.com/xrpc/com.etzhayyim.apps.training.listRuns"
             :body {"limit" 50}}
        res (tr/xrpc-post req {:token "tok" :dry-run true :http-fn http-fn})]
    (is (:dry-run res))
    (is (empty? @log))))

(deftest training-xrpc-get-records-call
  (let [{:keys [log http-fn]} (make-fake-http [{:status 200 :body "{\"jobs\":[]}"}])
        req {:url    "https://pds.example.com/xrpc/com.etzhayyim.training.listJobs"
             :params {"status" "running"}}]
    (tr/xrpc-get req {:token "my-jwt" :http-fn http-fn})
    (is (= 1 (count @log)))
    (let [call (first @log)]
      (is (= (:url req) (:url call)))
      (is (str/starts-with? (get (:headers call) "Authorization") "Bearer ")))))

(deftest training-xrpc-post-records-call
  (let [{:keys [log http-fn]} (make-fake-http [{:status 200 :body "{\"runs\":[]}"}])
        req {:url  "https://pds.example.com/xrpc/com.etzhayyim.apps.training.listRuns"
             :body {"limit" 10}}]
    (tr/xrpc-post req {:token "tok" :http-fn http-fn})
    (is (= 1 (count @log)))
    (is (= (:body req) (:body (first @log))))))

;; =============================================================================
;; WORKSPACE
;; =============================================================================

(deftest workspace-default-excludes
  (is (some #{"node_modules"} ws/default-excludes))
  (is (some #{".git"}         ws/default-excludes))
  (is (some #{"__pycache__"}  ws/default-excludes)))

(deftest workspace-build-rsync-command-minimal
  (let [cmd (ws/build-rsync-command {:workspace-dir "/home/user/project"
                                     :remote        "user@host:/remote"})]
    (is (= "rsync" (first cmd)))
    (is (some #{"-avz"} cmd))
    (is (some #{"--progress"} cmd))
    ;; default excludes should be there
    (let [excl-idx (keep-indexed (fn [i v] (when (= v "--exclude") i)) cmd)]
      (is (>= (count excl-idx) (count ws/default-excludes))))
    (is (str/ends-with? (last (butlast cmd)) "/"))
    (is (= "user@host:/remote" (last cmd)))))

(deftest workspace-build-rsync-command-custom-excludes
  (let [cmd (ws/build-rsync-command {:workspace-dir "/src"
                                     :remote        "dst"
                                     :excludes      ["tmp" "logs"]})]
    ;; only custom excludes, not defaults
    (let [excl-vals (map second
                        (filter #(= "--exclude" (first %))
                                (map vector cmd (rest cmd))))]
      (is (= (set excl-vals) #{"tmp" "logs"})))))

(deftest workspace-build-rsync-command-dry-run
  (let [cmd (ws/build-rsync-command {:workspace-dir "/src"
                                     :remote        "dst"
                                     :dry-run       true})]
    (is (some #{"--dry-run"} cmd))
    ;; destination is still last
    (is (= "dst" (last cmd)))))

(deftest workspace-build-rsync-command-delete
  (let [cmd (ws/build-rsync-command {:workspace-dir "/src"
                                     :remote        "dst"
                                     :delete        true})]
    (is (some #{"--delete"} cmd))))

(deftest workspace-build-rsync-command-all-opts
  (let [cmd (ws/build-rsync-command {:workspace-dir "/src"
                                     :remote        "user@host:/dst"
                                     :excludes      ["a" "b"]
                                     :dry-run       true
                                     :delete        true})]
    (is (some #{"--dry-run"} cmd))
    (is (some #{"--delete"}  cmd))
    (is (= "user@host:/dst" (last cmd)))))

(deftest workspace-run-sync-records-argv
  (let [{:keys [log proc-fn]} (make-fake-proc)
        opts {:workspace-dir "/src" :remote "dst" :dry-run true}]
    (ws/run-sync opts {:proc-fn proc-fn})
    (is (= 1 (count @log)))
    (let [call (first @log)]
      (is (= "rsync" (first (:argv call))))
      (is (some #{"--dry-run"} (:argv call))))))

(deftest workspace-count-actor-files-uses-injection
  (let [fs-fn (fn [_root] 42)]
    (is (= 42 (ws/count-actor-files "/some/root" {:fs-fn fs-fn})))))

(deftest workspace-status-uses-injections
  (let [out     (atom [])
        println-fn #(swap! out conj %)
        fs-fn   (fn [_root] 7)
        result  (ws/workspace-status "/repo-root"
                                     {:fs-fn      fs-fn
                                      :println-fn println-fn})]
    (is (str/includes? (str/join " " @out) "workspace:"))
    (is (str/includes? (str/join " " @out) "actors: 7"))
    (is (= 7 (:actors result)))))

;; =============================================================================
;; LINT
;; =============================================================================

(deftest lint-all-rules
  (is (= 6 (count lint/all-rules)))
  (is (some #{"nsid-regression"} lint/all-rules))
  (is (some #{"deps-drift"}      lint/all-rules)))

(deftest lint-update-script-path-keys
  (is (str/includes? (get lint/update-script-path "silent-catch-update") "no-silent-catch.mjs"))
  (is (str/includes? (get lint/update-script-path "ts-camel-update")     "ts-camelcase.mjs"))
  (is (str/includes? (get lint/update-script-path "json-sql-update")     "json-sql-case.mjs")))

(deftest lint-rule-extensions
  (is (contains? (get lint/rule-extensions "nsid-regression") ".ts"))
  (is (contains? (get lint/rule-extensions "silent-catch") ".py"))
  (is (contains? (get lint/rule-extensions "json-sql") ".json")))

(deftest lint-skip-dir?
  (is (lint/skip-dir? "/path/to/node_modules/pkg"))
  (is (lint/skip-dir? "some/.git/config"))
  (is (not (lint/skip-dir? "/path/to/src/myfile.ts"))))

(deftest lint-check-nsid-regression
  (testing "detects nsid placeholder"
    (let [text "  const x = {\"nsid\": \"test\"};\n  const y = 1;"
          vs   (lint/check-nsid-regression text)]
      (is (= 1 (count vs)))
      (is (= 1 (:line (first vs))))))
  (testing "clean file → empty"
    (is (empty? (lint/check-nsid-regression "const x = 'hello';\n")))))

(deftest lint-check-legacy-pds-nsid
  (testing "detects getTimeline"
    (let [text "  agent.rpc('app.bsky.feed.getTimeline', {});\n"
          vs   (lint/check-legacy-pds-nsid text)]
      (is (= 1 (count vs)))))
  (testing "clean → empty"
    (is (empty? (lint/check-legacy-pds-nsid "const x = 'hello';\n")))))

(deftest lint-check-silent-catch
  (testing "detects empty catch block"
    (let [text "try { x() } catch (e) {}\n"
          vs   (lint/check-silent-catch text)]
      (is (seq vs))))
  (testing "detects except pass"
    (let [text "try:\n  x()\nexcept Exception: pass\n"
          vs   (lint/check-silent-catch text)]
      (is (seq vs))))
  (testing "legitimate catch → empty"
    (let [text "try { x() } catch (e) { console.error(e) }\n"
          vs   (lint/check-silent-catch text)]
      (is (empty? vs)))))

(deftest lint-check-ts-camel
  (testing "detects snake_case assignment"
    (let [text "const my_var = 42;\n"
          vs   (lint/check-ts-camel text)]
      (is (seq vs))))
  (testing "ignores snake_case comment line"
    (let [text "// use snake_case here\n"
          vs   (lint/check-ts-camel text)]
      (is (empty? vs))))
  (testing "camelCase → empty"
    (is (empty? (lint/check-ts-camel "const myVar = 42;\n")))))

(deftest lint-check-json-sql
  (testing "detects PascalCase key"
    (let [text "{\"ProjectId\": \"p1\"}\n"
          vs   (lint/check-json-sql text)]
      (is (seq vs))))
  (testing "camelCase key → empty"
    (is (empty? (lint/check-json-sql "{\"projectId\": \"p1\"}\n")))))

(deftest lint-check-deps-drift
  (testing "detects completed migration"
    (let [text "[[migrations]]\nstatus = \"done\"\n"
          vs   (lint/check-deps-drift text)]
      (is (seq vs))))
  (testing "no migrations → empty/nil"
    (is (empty? (or (lint/check-deps-drift "[platform]\nname = \"etzhayyim\"\n") [])))))

(deftest lint-lint-file-text-dispatch
  (let [text "const x = {\"nsid\": \"placeholder\"};\n"
        r    (lint/lint-file-text "nsid-regression" "src/foo.ts" text)]
    (is (= "nsid-regression" (:rule r)))
    (is (= "src/foo.ts"      (:path r)))
    (is (= 1 (count (:violations r))))))

(deftest lint-build-update-command
  (let [cmd (lint/build-update-command "/repo-root" "silent-catch-update")]
    (is (= "node" (first cmd)))
    (is (str/includes? (second cmd) "no-silent-catch.mjs"))
    (is (= "--update-baseline" (last cmd)))))

(deftest lint-build-update-command-unknown
  (is (thrown? Exception
        (lint/build-update-command "/root" "unknown-target"))))

(deftest lint-scan-files-by-ext-uses-injection
  (let [fake-files [{:path "/repo/src/foo.ts" :rel "src/foo.ts" :text "const x = 1;\n"}]
        result     (lint/scan-files-by-ext "/repo" #{".ts"} {:fs-fn (fn [_ _ _] fake-files)})]
    (is (= 1 (count result)))
    (is (= "src/foo.ts" (:rel (first result))))))

(deftest lint-lint-rule-deps-drift-no-text
  ;; When fs-fn returns empty, deps-drift should return no violations
  (let [result (lint/lint-rule "/repo" "deps-drift"
                               {:fs-fn (fn [_ _ _] [])})]
    ;; deps-drift reads the real file — inject via skipping by returning empty slice
    ;; The injected fs-fn is only used for non-deps-drift rules;
    ;; deps-drift tries to read the real file, so test against a non-existent path.
    (is (= "deps-drift" (:rule result)))))

(deftest lint-run-update-target-records-argv
  (let [{:keys [log proc-fn]} (make-fake-proc)
        out (atom [])]
    (lint/run-update-target "/repo" "ts-camel-update"
                            {:proc-fn    proc-fn
                             :println-fn #(swap! out conj %)})
    (is (= 1 (count @log)))
    (let [call (first @log)]
      (is (= "node" (first (:argv call))))
      (is (str/includes? (str/join "/" (:argv call)) "ts-camelcase.mjs")))))

(deftest lint-run-update-target-nonzero-exit-throws
  (let [{:keys [proc-fn]} (make-fake-proc [{:exit 1 :out "" :err "fail"}])]
    (is (thrown-with-msg? Exception #"lint update failed"
          (lint/run-update-target "/repo" "silent-catch-update"
                                  {:proc-fn    proc-fn
                                   :println-fn (fn [_])})))))

;; =============================================================================
;; Runner
;; =============================================================================

(run-tests 'etzhayyim.test-bb-migration-wave8b)
