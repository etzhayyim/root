;; test_bb_migration_wave6b.clj — parity + subprocess injection tests for wave-6b.
;;
;; Run with:  bb 70-tools/src/etzhayyim/test_bb_migration_wave6b.clj
;; from repo root (classpath 70-tools/src already in bb.edn :paths).
;;
;; Modules tested:
;;   etzhayyim.deploy    — wrangler/pnpm/git command builders + pure cfg logic
;;   etzhayyim.agent-cmd — XRPC request builders + parse logic + git command builder
;;
;; SUBPROCESS PATTERN:
;;   build-X-command → argv vector (pure, asserted without executing)
;;   IO functions accept :proc-fn / :http-fn — tests inject fakes that record
;;   calls in an atom; NO live subprocesses or HTTP in any test.
;;
;; All assertions verified against Python baseline runs on identical inputs.
;; parity marker: # Python: <original call> → <result>

(ns etzhayyim.test-bb-migration-wave6b
  (:require [clojure.test   :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [cheshire.core  :as json]
            [etzhayyim.deploy    :as dep]
            [etzhayyim.agent-cmd :as ac]))

;; ---------------------------------------------------------------------------
;; Test helpers — fake subprocess + HTTP injection
;; ---------------------------------------------------------------------------

(defn make-fake-proc
  "Returns {:log atom :proc-fn fn}.
  proc-fn records every {:argv v :cwd d} call in log WITHOUT executing.
  fixed-result — the map to return from every call, default {:exit 0 :out \"\" :err \"\"}."
  ([] (make-fake-proc {:exit 0 :out "" :err ""}))
  ([fixed-result]
   (let [log (atom [])]
     {:log    log
      :proc-fn (fn [call]
                 (swap! log conj call)
                 fixed-result)})))

(defn make-fake-http
  "Returns {:log atom :http-fn fn}.
  http-fn records every request in log WITHOUT making network calls.
  fixed-responses — seq of {:status N :body string} to cycle through."
  ([] (make-fake-http []))
  ([fixed-responses]
   (let [log    (atom [])
         idx    (atom 0)
         resps  (if (seq fixed-responses)
                  fixed-responses
                  (repeat {:status 200 :body "{}"}))
         n      (count fixed-responses)]
     {:log     log
      :http-fn (fn [req]
                 (swap! log conj req)
                 (let [i @idx
                       r (if (pos? n)
                           (nth resps (mod i n))
                           {:status 200 :body "{}"})]
                   (swap! idx inc)
                   r))})))

;; ---------------------------------------------------------------------------
;; etzhayyim.deploy — pure config accessors
;; ---------------------------------------------------------------------------

(deftest test-deploy-app-id-from-nanoid
  (testing "app-id returns nanoid when present"
    ;; Python: _app_id({"nanoid": "abc123", "name": "MyApp"}) → "abc123"
    (is (= "abc123" (dep/app-id {"nanoid" "abc123" "name" "MyApp"})))))

(deftest test-deploy-app-id-from-name
  (testing "app-id falls back to name when nanoid empty"
    ;; Python: _app_id({"nanoid": "", "name": "MyApp"}) → "MyApp"
    (is (= "MyApp" (dep/app-id {"nanoid" "" "name" "MyApp"})))))

(deftest test-deploy-app-id-empty
  (testing "app-id returns empty string when both absent"
    (is (= "" (dep/app-id {})))))

(deftest test-deploy-ui-type-explicit
  (testing "ui-type returns explicit uiType"
    ;; Python: _ui_type({"uiType": "iframe"}) → "iframe"
    (is (= "iframe" (dep/ui-type {"uiType" "iframe"})))))

(deftest test-deploy-ui-type-default
  (testing "ui-type defaults to appview"
    ;; Python: _ui_type({}) → "appview"
    (is (= "appview" (dep/ui-type {})))))

(deftest test-deploy-ui-type-empty-string
  (testing "ui-type defaults to appview when empty string"
    ;; Python: _ui_type({"uiType": ""}) → "appview"
    (is (= "appview" (dep/ui-type {"uiType" ""})))))

;; ---------------------------------------------------------------------------
;; etzhayyim.deploy — actor handle derivation
;; ---------------------------------------------------------------------------

(deftest test-deploy-actor-handle-from-profile
  (testing "actor-handle prefers profile.handle"
    ;; Python: _actor_handle_from_cfg({"profile":{"handle":"mybot"}}, "etzhayyim-wasm-mybot-abcd1234")
    ;; → "mybot"
    (is (= "mybot"
           (dep/actor-handle {"profile" {"handle" "mybot"}}
                              "etzhayyim-wasm-mybot-abcd1234")))))

(deftest test-deploy-actor-handle-from-dir
  (testing "actor-handle derives from dir name when no profile.handle"
    ;; Python: _actor_handle_from_cfg({}, "etzhayyim-wasm-myslug-abcd1234") → "myslug"
    (is (= "myslug"
           (dep/actor-handle {}
                              "etzhayyim-wasm-myslug-abcd1234")))))

(deftest test-deploy-actor-handle-no-match
  (testing "actor-handle returns empty when dir name doesn't match pattern"
    (is (= "" (dep/actor-handle {} "some-other-dir")))))

;; ---------------------------------------------------------------------------
;; etzhayyim.deploy — WIT import extraction
;; ---------------------------------------------------------------------------

(deftest test-deploy-extract-wit-imports-empty
  (testing "extract-wit-imports returns [] for blank content"
    ;; Python: _extract_wit_imports("") → []
    (is (= [] (dep/extract-wit-imports "")))))

(deftest test-deploy-extract-wit-imports-basic
  (testing "extract-wit-imports finds import lines"
    ;; Python: _extract_wit_imports("world foo {\n  import kotodama:agent/governance@1.0.0;\n}")
    ;; → ["kotodama:agent/governance@1.0.0"]
    (let [content "world foo {\n  import kotodama:agent/governance@1.0.0;\n  import kotodama:agent/tools@1.0.0;\n}"]
      (is (= ["kotodama:agent/governance@1.0.0" "kotodama:agent/tools@1.0.0"]
             (dep/extract-wit-imports content))))))

(deftest test-deploy-extract-wit-imports-no-imports
  (testing "extract-wit-imports returns [] when no import lines"
    (let [content "world foo {\n  export kotodama:agent/handler@1.0.0;\n}"]
      (is (= [] (dep/extract-wit-imports content))))))

;; ---------------------------------------------------------------------------
;; etzhayyim.deploy — validation functions (pure string scan)
;; ---------------------------------------------------------------------------

(deftest test-deploy-validate-no-cors-clean
  (testing "validate-no-cors passes on clean content"
    ;; Python: _validate_no_cors("const x = 1;", "app.ts") → None (no exception)
    (is (nil? (dep/validate-no-cors "const x = 1;" "app.ts")))))

(deftest test-deploy-validate-no-cors-violation
  (testing "validate-no-cors throws on CORS header"
    ;; Python: _validate_no_cors('res.headers["Access-Control-Allow-Origin"] = "*";', "app.ts") → ClickException
    (is (thrown? Exception
                 (dep/validate-no-cors
                  "response.headers[\"Access-Control-Allow-Origin\"] = \"*\";"
                  "app.ts")))))

(deftest test-deploy-validate-no-pds-hardcode-clean
  (testing "validate-no-pds-hardcode passes on clean content"
    (is (nil? (dep/validate-no-pds-hardcode "const appId = 'myapp';" "index.ts")))))

(deftest test-deploy-validate-no-pds-hardcode-violation
  (testing "validate-no-pds-hardcode throws on hardcoded pds appId"
    ;; Python: _validate_no_pds_hardcode('appId: "pds"', "index.ts") → ClickException
    (is (thrown? Exception
                 (dep/validate-no-pds-hardcode "appId: \"pds\"" "index.ts")))))

(deftest test-deploy-validate-governance-import-pass
  (testing "validate-governance-import passes with governance import"
    (is (nil? (dep/validate-governance-import
               "world foo {\n  import kotodama:agent/governance@1.0.0;\n}"
               "world.wit")))))

(deftest test-deploy-validate-governance-import-include
  (testing "validate-governance-import passes with kotodama include"
    (is (nil? (dep/validate-governance-import
               "world foo {\n  include kotodama:runtime/kotodama-component@1.0.0;\n}"
               "world.wit")))))

(deftest test-deploy-validate-governance-import-fail
  (testing "validate-governance-import throws when missing"
    (is (thrown? Exception
                 (dep/validate-governance-import
                  "world foo {\n  export kotodama:agent/handler@1.0.0;\n}"
                  "world.wit")))))

(deftest test-deploy-validate-profile-missing
  (testing "validate-profile throws when no profile block"
    (is (thrown? Exception (dep/validate-profile {})))))

(deftest test-deploy-validate-profile-missing-display-name
  (testing "validate-profile throws when displayName missing"
    (is (thrown? Exception
                 (dep/validate-profile
                  {"profile" {"description" "some desc"}})))))

(deftest test-deploy-validate-profile-missing-description
  (testing "validate-profile throws when description missing"
    (is (thrown? Exception
                 (dep/validate-profile
                  {"profile" {"displayName" "My App"}})))))

(deftest test-deploy-validate-profile-pass
  (testing "validate-profile passes when both fields present"
    (is (nil? (dep/validate-profile
               {"profile" {"displayName" "My App"
                           "description" "Does things"}})))))

(deftest test-deploy-validate-required-missing-governance
  (testing "validate-required throws when governance missing"
    (is (thrown? Exception
                 (dep/validate-required {})))))

;; ---------------------------------------------------------------------------
;; etzhayyim.deploy — build-wrangler-vars (pure)
;; ---------------------------------------------------------------------------

(deftest test-deploy-build-wrangler-vars-basic
  (testing "build-wrangler-vars includes APP_NANOID and APP_FRAMEWORK"
    (let [cfg {"nanoid"        "abc123"
               "name"          "TestApp"
               "performerType" "worker"
               "profile"       {"displayName" "Test App" "description" "Test"}
               "framework"     "ts-native"}
          vars (dep/build-wrangler-vars cfg "test-dir" "abcdef1" "2026-01-01T00:00:00Z" "")]
      (is (= "abc123"    (get vars "APP_NANOID")))
      (is (= "ts-native" (get vars "APP_FRAMEWORK")))
      (is (= "worker"    (get vars "APP_PERFORMER_TYPE")))
      (is (= "Test App"  (get vars "APP_DISPLAY_NAME")))
      (is (= "Test"      (get vars "APP_DESCRIPTION"))))))

(deftest test-deploy-build-wrangler-vars-signing-key
  (testing "build-wrangler-vars includes SIGNING_PUBLIC_KEY when provided"
    (let [cfg  {"nanoid" "id1" "profile" {"displayName" "A" "description" "B"}}
          vars (dep/build-wrangler-vars cfg "" "" "" "MYPUBKEY")]
      (is (= "MYPUBKEY" (get vars "SIGNING_PUBLIC_KEY"))))))

(deftest test-deploy-build-wrangler-vars-no-signing-key
  (testing "build-wrangler-vars omits SIGNING_PUBLIC_KEY when empty"
    (let [cfg  {"nanoid" "id1" "profile" {"displayName" "A" "description" "B"}}
          vars (dep/build-wrangler-vars cfg "" "" "" "")]
      (is (nil? (get vars "SIGNING_PUBLIC_KEY"))))))

;; ---------------------------------------------------------------------------
;; etzhayyim.deploy — command builders (argv vectors, no execution)
;; ---------------------------------------------------------------------------

(deftest test-deploy-build-pnpm-command
  (testing "build-pnpm-command produces correct argv vector"
    ;; Python: _run_cmd(dir, 'pnpm', 'install', '--frozen-lockfile') → ['pnpm', 'install', '--frozen-lockfile']
    (is (= ["pnpm" "install" "--frozen-lockfile"]
           (dep/build-pnpm-command ["install" "--frozen-lockfile"])))))

(deftest test-deploy-build-wrangler-deploy-command
  (testing "build-wrangler-deploy-command produces npx wrangler deploy"
    ;; Python: _run_cmd(path, 'npx', 'wrangler', 'deploy') → ['npx', 'wrangler', 'deploy']
    (is (= ["npx" "wrangler" "deploy"]
           (dep/build-wrangler-deploy-command)))))

(deftest test-deploy-build-git-sha-command
  (testing "build-git-sha-command produces git rev-parse --short HEAD"
    ;; Python: subprocess.run(['git','rev-parse','--short','HEAD'], ...)
    (is (= ["git" "rev-parse" "--short" "HEAD"]
           (dep/build-git-sha-command)))))

(deftest test-deploy-build-svelte-check-command
  (testing "build-svelte-check-command produces correct argv"
    (is (= ["pnpm" "exec" "svelte-check" "--fail-on-warnings"]
           (dep/build-svelte-check-command)))))

(deftest test-deploy-build-vite-build-command
  (testing "build-vite-build-command produces correct argv"
    (is (= ["pnpm" "build"]
           (dep/build-vite-build-command)))))

;; ---------------------------------------------------------------------------
;; etzhayyim.deploy — subprocess injection: git-short-sha
;; ---------------------------------------------------------------------------

(deftest test-deploy-git-short-sha-injectable
  (testing "git-short-sha calls build-git-sha-command argv via :proc-fn"
    (let [{:keys [log proc-fn]} (make-fake-proc {:exit 0 :out "deadbee\n" :err ""})
          sha (dep/git-short-sha "/fake/comp" {:proc-fn proc-fn})]
      (is (= "deadbee" sha))
      (is (= 1 (count @log)))
      (is (= ["git" "rev-parse" "--short" "HEAD"]
             (:argv (first @log)))))))

(deftest test-deploy-git-short-sha-fails-gracefully
  (testing "git-short-sha returns empty string on non-zero exit"
    (let [{:keys [proc-fn]} (make-fake-proc {:exit 128 :out "" :err "not a git repo"})]
      (is (= "" (dep/git-short-sha "/not/git" {:proc-fn proc-fn}))))))

;; ---------------------------------------------------------------------------
;; etzhayyim.deploy — dry-run: no proc-fn called
;; ---------------------------------------------------------------------------

(deftest test-deploy-run-cmd-dry-run-no-execution
  (testing "run-cmd with :dry-run? true never calls proc-fn"
    (let [{:keys [log proc-fn]} (make-fake-proc)]
      (dep/run-cmd ["pnpm" "build"] {:proc-fn proc-fn :dry-run? true :cwd "."})
      (is (empty? @log) "proc-fn must NOT be called in dry-run mode"))))

;; ---------------------------------------------------------------------------
;; etzhayyim.deploy — HTTP injection: evaluate-deps-score
;; ---------------------------------------------------------------------------

(deftest test-deploy-evaluate-deps-score-success
  (testing "evaluate-deps-score calls /score.json and parses result"
    (let [body (json/generate-string {:scoring {:overall_score 8.5}})
          {:keys [log http-fn]} (make-fake-http [{:status 200 :body body}])
          score (dep/evaluate-deps-score "https://example.com/actor" {:http-fn http-fn})]
      (is (= 1 (count @log)))
      (is (str/includes? (:url (first @log)) "score.json"))
      (is (= 8.5 score)))))

(deftest test-deploy-evaluate-deps-score-failure
  (testing "evaluate-deps-score returns nil on HTTP error"
    (let [{:keys [http-fn]} (make-fake-http [{:status 404 :body "not found"}])
          score (dep/evaluate-deps-score "https://example.com/actor" {:http-fn http-fn})]
      (is (nil? score)))))

;; ---------------------------------------------------------------------------
;; etzhayyim.agent-cmd — pure: auth header builder
;; ---------------------------------------------------------------------------

(deftest test-ac-build-auth-headers
  (testing "build-auth-headers assembles correct Authorization header"
    ;; Python: _auth_headers() with token "mytoken" → {"Authorization": "Bearer mytoken", ...}
    (let [hdrs (ac/build-auth-headers "mytoken")]
      (is (= "Bearer mytoken" (get hdrs "Authorization")))
      (is (= "application/json" (get hdrs "Content-Type"))))))

;; ---------------------------------------------------------------------------
;; etzhayyim.agent-cmd — pure: XRPC URL builders
;; ---------------------------------------------------------------------------

(deftest test-ac-build-list-agents-url
  (testing "build-list-agents-url produces correct XRPC URL"
    ;; Python: f"{pds_url}/xrpc/com.etzhayyim.agent.listAgents"
    (is (= "https://pds.example.com/xrpc/com.etzhayyim.agent.listAgents"
           (ac/build-list-agents-url "https://pds.example.com")))))

(deftest test-ac-build-list-agents-url-trailing-slash
  (testing "build-list-agents-url strips trailing slash"
    (is (= "https://pds.example.com/xrpc/com.etzhayyim.agent.listAgents"
           (ac/build-list-agents-url "https://pds.example.com/")))))

;; ---------------------------------------------------------------------------
;; etzhayyim.agent-cmd — pure: request builders
;; ---------------------------------------------------------------------------

(deftest test-ac-build-list-agents-request
  (testing "build-list-agents-request has correct method and URL"
    (let [hdrs {"Authorization" "Bearer tok" "Content-Type" "application/json"}
          req  (ac/build-list-agents-request "https://pds.example.com" hdrs)]
      (is (= :get         (:method req)))
      (is (str/includes? (:url req) "listAgents"))
      (is (= hdrs         (:headers req))))))

(deftest test-ac-build-list-agents-request-filters
  (testing "build-list-agents-request passes filters as params"
    (let [req (ac/build-list-agents-request
               "https://pds.example.com"
               {}
               {"status" "running"})]
      (is (= {"status" "running"} (:params req))))))

(deftest test-ac-build-get-agent-request
  (testing "build-get-agent-request has correct method and id param"
    ;; Python: GET {pds}/xrpc/com.etzhayyim.agent.getAgent?id=abc
    (let [req (ac/build-get-agent-request "https://pds.example.com" {} "abc")]
      (is (= :get    (:method req)))
      (is (str/includes? (:url req) "getAgent"))
      (is (= {"id" "abc"} (:params req))))))

(deftest test-ac-build-stop-body
  (testing "build-stop-body produces correct id map"
    ;; Python: {"id": agent_id} sent as POST body
    (is (= {"id" "agent-1"} (ac/build-stop-body "agent-1")))))

(deftest test-ac-build-stop-agent-request
  (testing "build-stop-agent-request is POST with JSON body containing id"
    ;; Python: httpx.post(url, json={"id": agent_id}, headers=_auth_headers())
    (let [req (ac/build-stop-agent-request "https://pds.example.com" {} "agent-1")]
      (is (= :post (:method req)))
      (is (str/includes? (:url req) "stopAgent"))
      ;; body is a JSON string
      (let [body (json/parse-string (:body req))]
        (is (= "agent-1" (get body "id")))))))

(deftest test-ac-build-organism-status-request
  (testing "build-organism-status-request is GET at /status"
    ;; Python: httpx.get(f"{url.rstrip('/')}/status", timeout=10)
    (let [req (ac/build-organism-status-request "http://localhost:8088")]
      (is (= :get (:method req)))
      (is (str/ends-with? (:url req) "/status")))))

(deftest test-ac-build-organism-status-request-trailing-slash
  (testing "build-organism-status-request strips trailing slash before /status"
    (let [req (ac/build-organism-status-request "http://localhost:8088/")]
      (is (= "http://localhost:8088/status" (:url req))))))

;; ---------------------------------------------------------------------------
;; etzhayyim.agent-cmd — pure: subprocess command builder
;; ---------------------------------------------------------------------------

(deftest test-ac-build-git-toplevel-command
  (testing "build-git-toplevel-command returns correct argv vector"
    ;; Python: subprocess.run(['git','rev-parse','--show-toplevel'], ...)
    (is (= ["git" "rev-parse" "--show-toplevel"]
           (ac/build-git-toplevel-command)))))

;; ---------------------------------------------------------------------------
;; etzhayyim.agent-cmd — pure: response parsers
;; ---------------------------------------------------------------------------

(deftest test-ac-parse-list-response-agents-key
  (testing "parse-list-response extracts :agents from JSON body"
    ;; Python: response.json()["agents"]
    (let [body (json/generate-string {"agents" [{"id" "a1"} {"id" "a2"}]})]
      (is (= 2 (count (ac/parse-list-response body)))))))

(deftest test-ac-parse-list-response-rows-key
  (testing "parse-list-response extracts :rows as fallback"
    (let [body (json/generate-string {"rows" [{"id" "r1"}]})]
      (is (= 1 (count (ac/parse-list-response body)))))))

(deftest test-ac-parse-list-response-empty-on-error
  (testing "parse-list-response returns [] on malformed JSON"
    (is (= [] (ac/parse-list-response "not-json")))))

(deftest test-ac-parse-get-response
  (testing "parse-get-response returns parsed map"
    (let [body (json/generate-string {"id" "a1" "status" "running"})]
      (is (= :running (keyword (get (ac/parse-get-response body) :status)))))))

;; ---------------------------------------------------------------------------
;; etzhayyim.agent-cmd — IO: list-agents injectable http-fn
;; ---------------------------------------------------------------------------

(deftest test-ac-list-agents-injectable
  (testing "list-agents calls build-list-agents-request URL via :http-fn"
    (let [body  (json/generate-string {"agents" [{"id" "a1" "status" "running"}]})
          {:keys [log http-fn]} (make-fake-http [{:status 200 :body body}])
          agents (ac/list-agents {:http-fn  http-fn
                                  :auth-fn  (fn [] {"Authorization" "Bearer tok"
                                                     "Content-Type"  "application/json"})
                                  :pds-url  "https://pds.example.com"})]
      (is (= 1 (count @log)))
      (is (= :get (:method (first @log))))
      (is (str/includes? (:url (first @log)) "listAgents"))
      (is (= 1 (count agents))))))

;; ---------------------------------------------------------------------------
;; etzhayyim.agent-cmd — IO: stop-agent injectable http-fn
;; ---------------------------------------------------------------------------

(deftest test-ac-stop-agent-injectable
  (testing "stop-agent fires POST stopAgent via :http-fn"
    (let [{:keys [log http-fn]} (make-fake-http [{:status 200 :body "{}"}])
          result (ac/stop-agent "agent-1"
                                {:http-fn  http-fn
                                 :auth-fn  (fn [] {"Authorization" "Bearer tok"
                                                    "Content-Type"  "application/json"})
                                 :pds-url  "https://pds.example.com"})]
      (is (true? result))
      (is (= 1 (count @log)))
      (is (= :post (:method (first @log))))
      (is (str/includes? (:url (first @log)) "stopAgent"))
      ;; body contains agent-id
      (let [sent-body (json/parse-string (:body (first @log)))]
        (is (= "agent-1" (get sent-body "id")))))))

;; ---------------------------------------------------------------------------
;; etzhayyim.agent-cmd — IO: organism-status injectable http-fn
;; ---------------------------------------------------------------------------

(deftest test-ac-organism-status-injectable
  (testing "organism-status calls /status URL via :http-fn and parses result"
    (let [body (json/generate-string {"status" "healthy" "beats" 42})
          {:keys [log http-fn]} (make-fake-http [{:status 200 :body body}])
          result (ac/organism-status {:http-fn      http-fn
                                      :organism-url "http://localhost:8088"})]
      (is (= 1 (count @log)))
      (is (= "http://localhost:8088/status" (:url (first @log))))
      (is (= "healthy" (:status result))))))  ; JSON string, not keyword

;; ---------------------------------------------------------------------------
;; etzhayyim.agent-cmd — IO: verify-agent injectable proc-fn + read-fn
;; ---------------------------------------------------------------------------

(deftest test-ac-verify-agent-injectable
  (testing "verify-agent calls build-git-toplevel-command via :proc-fn"
    (let [{:keys [log proc-fn]} (make-fake-proc {:exit 0 :out "/repo-root\n" :err ""})
          proof-calls (atom [])
          fake-read   (fn [p] (swap! proof-calls conj p) nil)  ; files don't exist in test
          result      (ac/verify-agent "/some/comp"
                                       {:proc-fn proc-fn
                                        :read-fn fake-read})]
      ;; subprocess was called with the git rev-parse argv
      (is (= 1 (count @log)))
      (is (= ["git" "rev-parse" "--show-toplevel"] (:argv (first @log))))
      ;; git-root extracted from proc output
      (is (= "/repo-root" (:git-root result)))
      ;; proof files were read
      (is (= 3 (count @proof-calls))))))

;; ---------------------------------------------------------------------------
;; etzhayyim.agent-cmd — stubs: Go-binary-required ops throw ex-info
;; ---------------------------------------------------------------------------

(deftest test-ac-agent-run-throws
  (testing "agent-run throws ex-info (Go binary required)"
    (let [ex (try (ac/agent-run) nil (catch Exception e e))]
      (is (some? ex))
      (is (instance? clojure.lang.ExceptionInfo ex))
      (is (true? (get (ex-data ex) :go-binary-required))))))

(deftest test-ac-agent-organism-publish-throws
  (testing "agent-organism-publish throws ex-info (Go binary required)"
    (let [ex (try (ac/agent-organism-publish) nil (catch Exception e e))]
      (is (some? ex))
      (is (true? (get (ex-data ex) :go-binary-required))))))

;; ---------------------------------------------------------------------------
;; run tests
;; ---------------------------------------------------------------------------

(defn -main [& _args]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-bb-migration-wave6b)]
    (System/exit (+ fail error))))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
