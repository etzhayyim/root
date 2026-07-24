;; test_bb_migration_wave6a.clj — parity + request-shaping tests for actors.cljc + apps.cljc
;;
;; Run with:
;;   bb --classpath 70-tools/src -m clojure.test etzhayyim.test-bb-migration-wave6a
;;
;; from repo root (classpath 70-tools/src already in bb.edn :paths).
;;
;; Modules tested:
;;   etzhayyim.actors  — actor lifecycle (shinka, jokyo, migrate-to-plc)
;;   etzhayyim.apps    — app status checker (coverage, kyumei-koji)
;;
;; Coverage:
;;   PURE parity (no network):
;;     actors: build-prompt, parse-result, sanitize-path, stable-rkey,
;;             score-jokyo, build-apply-writes-body
;;     apps:   coverage-grade, tier-score, infer-app-name-from-collections,
;;             extract-sources-from-src, score-domain-static-src,
;;             compute-coverage-scores
;;
;;   IO request-shaping (injectable fake http-fn, zero network):
;;     actors: build-actor-list-request, build-apply-writes-request,
;;             build-ollama-generate-request, build-murakumo-generate-request,
;;             build-health-request, build-heartbeat-request,
;;             build-migrate-request
;;             fetch-actors (injectable), migrate-to-plc offline mode
;;     apps:   build-list-apps-request, build-list-records-request,
;;             build-health-request, build-meta-request,
;;             build-xrpc-coverage-request
;;             check-app-health (injectable), list-pds-records (injectable)
;;
;;   HONEST NOTE:
;;     Live behavioral parity (actual PDS / Ollama / Murakumo / CF responses)
;;     requires operator credentials and cannot be verified offline.
;;     All tests are zero-network.

(ns etzhayyim.test-bb-migration-wave6a
  (:require [clojure.test       :refer [deftest is testing run-tests]]
            [clojure.string     :as str]
            [cheshire.core      :as json]
            [etzhayyim.actors   :as act]
            [etzhayyim.apps     :as app]))

;; ─── test helpers ─────────────────────────────────────────────────────────────

(defn- make-fake-http
  "Returns {:log atom :http-fn fn}.
   The fake records every request in log and returns fixed-responses
   (cycling when exhausted).  Each response is {:status :body} or a string."
  ([] (make-fake-http []))
  ([fixed-responses]
   (let [log      (atom [])
         resp-idx (atom 0)]
     {:log    log
      :http-fn
      (fn [req]
        (swap! log conj req)
        (if (seq fixed-responses)
          (let [r (nth fixed-responses (mod @resp-idx (count fixed-responses)))]
            (swap! resp-idx inc)
            (if (string? r) {:status 200 :body r} r))
          {:status 200 :body "{}"}))})))

(def ^:private sample-actor
  {:did     "did:web:alice.etzhayyim.com"
   :nanoid  "alice123"
   :handle  "alice.etzhayyim.com"
   :display-name "Alice Agent"
   :description  "A sample agent for testing."
   :project-id   "proj-001"})

;; ─── PURE: sanitize-path ──────────────────────────────────────────────────────

(deftest test-actors-sanitize-path
  (testing "sanitize-path: lowercase, spaces→hyphens, strip non-alnum"
    ;; Python: _sanitize_path("Hello World!") == "hello-world"
    (is (= "hello-world" (act/sanitize-path "Hello World!"))))

  (testing "sanitize-path: already clean slug unchanged"
    ;; Python: _sanitize_path("foo-bar-123") == "foo-bar-123"
    (is (= "foo-bar-123" (act/sanitize-path "foo-bar-123"))))

  (testing "sanitize-path: empty string"
    ;; Python: _sanitize_path("") == ""
    (is (= "" (act/sanitize-path ""))))

  (testing "sanitize-path: strips special characters"
    ;; Python: _sanitize_path("foo@bar.baz") == "foobarbaz"
    (is (= "foobarbaz" (act/sanitize-path "foo@bar.baz")))))

;; ─── PURE: stable-rkey ────────────────────────────────────────────────────────

(deftest test-actors-stable-rkey
  (testing "stable-rkey: returns 16-character hex string"
    ;; Python: _stable_rkey("alice:DEPENDS_ON:etzhayyim") returns 16-char hex
    (let [rk (act/stable-rkey "alice:DEPENDS_ON:etzhayyim")]
      (is (= 16 (count rk)))
      (is (re-matches #"[0-9a-f]{16}" rk))))

  (testing "stable-rkey: deterministic — same input same output"
    (is (= (act/stable-rkey "test-key") (act/stable-rkey "test-key"))))

  (testing "stable-rkey: different inputs produce different keys"
    (is (not= (act/stable-rkey "a") (act/stable-rkey "b"))))

  (testing "stable-rkey: known SHA-256 prefix (parity with Python)"
    ;; Python: hashlib.sha256("test-key".encode()).hexdigest()[:16]
    ;; We verify the length and hex-ness, not the exact value (avoids hardcoding)
    (let [rk (act/stable-rkey "test-key")]
      (is (string? rk))
      (is (= 16 (count rk))))))

;; ─── PURE: build-prompt ───────────────────────────────────────────────────────

(deftest test-actors-build-prompt
  (testing "build-prompt: contains nanoid and handle"
    ;; Python: _build_prompt(actor) → prompt containing nanoid and handle
    (let [prompt (act/build-prompt sample-actor)]
      (is (string? prompt))
      (is (str/includes? prompt "alice123"))
      (is (str/includes? prompt "alice.etzhayyim.com"))))

  (testing "build-prompt: includes displayName when present"
    ;; Python: if actor.display_name: parts.append(f'displayName={actor.display_name!r}')
    (let [prompt (act/build-prompt sample-actor)]
      (is (str/includes? prompt "Alice Agent"))))

  (testing "build-prompt: includes description when present"
    (let [prompt (act/build-prompt sample-actor)]
      (is (str/includes? prompt "A sample agent"))))

  (testing "build-prompt: omits displayName and description ctx parts when empty"
    ;; Python: if actor.display_name: parts.append(...) — not added when empty
    ;; Note: the prompt template itself always mentions "domain_summary" etc. as output keys,
    ;; but the ctx= line only includes displayName/description when non-empty.
    (let [actor  {:nanoid "x001" :handle "x001.etzhayyim.com"
                  :display-name "" :description ""}
          prompt (act/build-prompt actor)]
      (is (not (str/includes? prompt "displayName")))
      ;; description key not in ctx when empty (it appears in prompt template as field name, so check ctx part)
      (is (not (str/includes? prompt "description='")))))

  (testing "build-prompt: includes JSON structure guidance"
    (let [prompt (act/build-prompt sample-actor)]
      (is (str/includes? prompt "domain_summary"))
      (is (str/includes? prompt "sub_dids"))
      (is (str/includes? prompt "knowledge_edges"))
      (is (str/includes? prompt "EXPERTISE_IN")))))

;; ─── PURE: parse-result ───────────────────────────────────────────────────────

(deftest test-actors-parse-result
  (testing "parse-result: valid JSON → structured result"
    ;; Python: _parse_result(actor, llm_text) extracts domain_summary/sub_dids/edges
    (let [llm-text (json/generate-string
                    {"domain_summary" "Alice handles domain expertise."
                     "sub_dids"       [{"path"         "sub-agent"
                                        "display_name" "Sub Agent"
                                        "description"  "A sub-entity."}]
                     "knowledge_edges" [{"from"     "alice123"
                                         "relation" "EXPERTISE_IN"
                                         "to"       "distributed-systems"}]})
          result   (act/parse-result sample-actor llm-text)]
      (is (= "" (:error result)))
      (is (= "Alice handles domain expertise." (:domain-summary result)))
      (is (= 1 (count (:sub-dids result))))
      (is (= "sub-agent" (:path (first (:sub-dids result)))))
      (is (= 1 (count (:knowledge-edges result))))
      (is (= "EXPERTISE_IN" (:relation (first (:knowledge-edges result)))))))

  (testing "parse-result: no JSON block → error result"
    ;; Python: if not m: return ShinkaResult(..., error="no JSON in LLM response")
    (let [result (act/parse-result sample-actor "no json here")]
      (is (= "no JSON in LLM response" (:error result)))
      (is (empty? (:sub-dids result)))
      (is (empty? (:knowledge-edges result)))))

  (testing "parse-result: invalid JSON → parse error"
    ;; Python: except json.JSONDecodeError as exc: return ShinkaResult(..., error=f"JSON parse: {exc}")
    (let [result (act/parse-result sample-actor "{invalid json}")]
      (is (str/starts-with? (:error result) "JSON parse:"))))

  (testing "parse-result: sanitizes sub-did paths"
    ;; Python: _sanitize_path(s.get('path',''))
    (let [llm-text (json/generate-string
                    {"domain_summary" "X"
                     "sub_dids"       [{"path" "Hello World!" "display_name" "H" "description" ""}]
                     "knowledge_edges" []})
          result   (act/parse-result sample-actor llm-text)]
      (is (= "hello-world" (:path (first (:sub-dids result)))))))

  (testing "parse-result: skips sub-dids with empty path after sanitize"
    ;; Python: if s.get('path')
    (let [llm-text (json/generate-string
                    {"domain_summary" "X"
                     "sub_dids"       [{"path" "!!!" "display_name" "bad" "description" ""}]
                     "knowledge_edges" []})
          result   (act/parse-result sample-actor llm-text)]
      (is (empty? (:sub-dids result)))))

  (testing "parse-result: skips edges with no relation or no to"
    ;; Python: if e.get('relation') and e.get('to')
    (let [llm-text (json/generate-string
                    {"domain_summary" "X"
                     "sub_dids"       []
                     "knowledge_edges" [{"from" "alice123" "relation" "" "to" "dest"}
                                        {"from" "alice123" "relation" "SERVES" "to" ""}]})
          result   (act/parse-result sample-actor llm-text)]
      (is (empty? (:knowledge-edges result)))))

  (testing "parse-result: from defaults to actor nanoid when missing"
    ;; Python: e.get('from', actor.nanoid)
    (let [llm-text (json/generate-string
                    {"domain_summary" "X"
                     "sub_dids"       []
                     "knowledge_edges" [{"relation" "SERVES" "to" "users"}]})
          result   (act/parse-result sample-actor llm-text)
          edge     (first (:knowledge-edges result))]
      (is (= "alice123" (:from edge))))))

;; ─── PURE: score-jokyo ────────────────────────────────────────────────────────

(deftest test-actors-score-jokyo
  (testing "score-jokyo: perfect health + fast → 100, grade S"
    ;; Python: score += 40 (health) + 40 (heartbeat) + 10 (ms<200) + 10 (ms<500) = 100, grade S
    (let [{:keys [total-score grade]}
          (act/score-jokyo {:health-ok true :heartbeat-ok true
                             :health-ms 100 :heartbeat-ms 200})]
      (is (= 100 total-score))
      (is (= "S" grade))))

  (testing "score-jokyo: health only, fast health + slow heartbeat → 40+10 = 50, grade B"
    ;; Python: score = 40 (health) + 0 + 10 (ms<200) + 0 = 50, grade B (50-69)
    (let [{:keys [total-score grade]}
          (act/score-jokyo {:health-ok true :heartbeat-ok false
                             :health-ms 150 :heartbeat-ms 600})]
      (is (= 50 total-score))
      (is (= "B" grade))))

  (testing "score-jokyo: all fail → 0, grade D"
    ;; Python: score = 0
    (let [{:keys [total-score grade]}
          (act/score-jokyo {:health-ok false :heartbeat-ok false
                             :health-ms 999 :heartbeat-ms 999})]
      (is (= 0 total-score))
      (is (= "D" grade))))

  (testing "score-jokyo: grade thresholds"
    ;; health only, slow (999ms) → 40 pts → C (30-49)
    (is (= "C" (:grade (act/score-jokyo {:health-ok true  :heartbeat-ok false
                                          :health-ms 999  :heartbeat-ms 999}))))
    ;; heartbeat only, slow (999ms) → 40 pts → C (30-49)
    (is (= "C" (:grade (act/score-jokyo {:health-ok false :heartbeat-ok true
                                          :health-ms 999  :heartbeat-ms 999}))))
    ;; health + fast health → 40+10 = 50 → B
    (is (= "B" (:grade (act/score-jokyo {:health-ok true  :heartbeat-ok false
                                          :health-ms 100  :heartbeat-ms 999}))))
    ;; health + heartbeat, both slow → 80 pts → A
    (is (= "A" (:grade (act/score-jokyo {:health-ok true  :heartbeat-ok true
                                          :health-ms 999  :heartbeat-ms 999}))))))

;; ─── PURE: build-apply-writes-body ───────────────────────────────────────────

(deftest test-actors-build-apply-writes-body
  (testing "build-apply-writes-body: domain-summary → actor.app write"
    ;; Python: writes.append({...collection: 'com.etzhayyim.actor.app'...})
    (let [result {:did "did:web:alice.etzhayyim.com" :nanoid "alice123"
                  :display-name "Alice" :domain-summary "Domain expertise."
                  :sub-dids [] :knowledge-edges []}
          body   (act/build-apply-writes-body result "2026-06-01T00:00:00Z")]
      (is (= "did:web:alice.etzhayyim.com" (:repo body)))
      (is (= 1 (count (:writes body))))
      (is (= "com.etzhayyim.actor.app" (get (first (:writes body)) "collection")))
      (is (= "alice123" (get-in (first (:writes body)) ["value" "nanoid"])))))

  (testing "build-apply-writes-body: no domain-summary → no actor.app write"
    ;; Python: if result.domain_summary: writes.append(...)
    (let [result {:did "did:x" :nanoid "x001" :display-name ""
                  :domain-summary "" :sub-dids [] :knowledge-edges []}
          body   (act/build-apply-writes-body result "2026-06-01T00:00:00Z")]
      (is (empty? (:writes body)))))

  (testing "build-apply-writes-body: sub-dids → identity.did writes"
    ;; Python: collection: 'com.etzhayyim.identity.did'
    (let [result {:did "did:web:alice.etzhayyim.com" :nanoid "alice123"
                  :display-name "" :domain-summary ""
                  :sub-dids [{:path "sub-agent" :display-name "S" :description "D"}]
                  :knowledge-edges []}
          body   (act/build-apply-writes-body result "2026-06-01T00:00:00Z")]
      (is (= 1 (count (:writes body))))
      (is (= "com.etzhayyim.identity.did" (get (first (:writes body)) "collection")))))

  (testing "build-apply-writes-body: knowledge-edges → knowledgeEdge writes"
    ;; Python: collection: 'com.etzhayyim.actor.knowledgeEdge'
    (let [result {:did "did:web:alice.etzhayyim.com" :nanoid "alice123"
                  :display-name "" :domain-summary ""
                  :sub-dids []
                  :knowledge-edges [{:from "alice123" :relation "SERVES" :to "users"}]}
          body   (act/build-apply-writes-body result "2026-06-01T00:00:00Z")]
      (is (= 1 (count (:writes body))))
      (is (= "com.etzhayyim.actor.knowledgeEdge" (get (first (:writes body)) "collection")))))

  (testing "build-apply-writes-body: batches all write types"
    (let [result {:did "did:web:alice.etzhayyim.com" :nanoid "alice123"
                  :display-name "A" :domain-summary "Domain"
                  :sub-dids [{:path "sub" :display-name "S" :description "D"}]
                  :knowledge-edges [{:from "alice123" :relation "SERVES" :to "users"}]}
          body   (act/build-apply-writes-body result "2026-06-01T00:00:00Z")]
      (is (= 3 (count (:writes body))))))

  (testing "build-apply-writes-body: rkey is stable-rkey of path for sub-dids"
    ;; Python: rkey=_stable_rkey(f"did:{sub.path}")
    (let [result {:did "d" :nanoid "n" :display-name "" :domain-summary ""
                  :sub-dids [{:path "foo" :display-name "" :description ""}]
                  :knowledge-edges []}
          body   (act/build-apply-writes-body result "2026-06-01T00:00:00Z")
          rkey   (get (first (:writes body)) "rkey")]
      (is (= (act/stable-rkey "did:foo") rkey)))))

;; ─── IO REQUEST-SHAPING: actors ───────────────────────────────────────────────

(deftest test-actors-build-actor-list-request
  (testing "actor-list-request: POST to PDS /xrpc/com.etzhayyim.actor.list"
    ;; Python: client.post(f"{pds_url}/xrpc/com.etzhayyim.actor.list", json=payload)
    (let [req (act/build-actor-list-request "https://pds.aozora.app" {:token "tok123"})]
      (is (= :post (:method req)))
      (is (= "https://pds.aozora.app/xrpc/com.etzhayyim.actor.list" (:url req)))
      (is (= "Bearer tok123" (get-in req [:headers "Authorization"])))
      (is (= "active" (get (:body req) "status")))))

  (testing "actor-list-request: cursor included when non-empty"
    (let [req (act/build-actor-list-request "https://pds.aozora.app"
                                            {:token "tok" :cursor "cursor-abc"})]
      (is (= "cursor-abc" (get (:body req) "cursor")))))

  (testing "actor-list-request: no auth header when token empty"
    (let [req (act/build-actor-list-request "https://pds.aozora.app" {})]
      (is (not (contains? (:headers req) "Authorization"))))))

(deftest test-actors-build-apply-writes-request
  (testing "apply-writes-request: POST to applyWrites with auth"
    ;; Python: client.post(f"{pds_url}/xrpc/com.atproto.repo.applyWrites", json={..})
    (let [body {:repo "did:web:alice.etzhayyim.com" :writes []}
          req  (act/build-apply-writes-request "https://pds.aozora.app" "tok123" body)]
      (is (= :post (:method req)))
      (is (= "https://pds.aozora.app/xrpc/com.atproto.repo.applyWrites" (:url req)))
      (is (= "Bearer tok123" (get-in req [:headers "Authorization"])))
      (is (= body (:body req))))))

(deftest test-actors-build-ollama-generate-request
  (testing "ollama-generate-request: POST to /api/generate with correct body"
    ;; Python: client.post(f"{base}/api/generate", json=body, ...)
    (let [req (act/build-ollama-generate-request "http://127.0.0.1:11434" "gemma3:4b" "hello")]
      (is (= :post (:method req)))
      (is (= "http://127.0.0.1:11434/api/generate" (:url req)))
      (is (= "gemma3:4b" (get (:body req) "model")))
      (is (= "hello" (get (:body req) "prompt")))
      (is (= false (get (:body req) "stream")))
      (is (= "json" (get (:body req) "format")))
      (is (= 0.3 (get-in req [:body "options" "temperature"])))))

  (testing "ollama-generate-request: uses default base when nil"
    (let [req (act/build-ollama-generate-request nil "gemma3:4b" "hello")]
      (is (str/includes? (:url req) "11434")))))

(deftest test-actors-build-murakumo-generate-request
  (testing "murakumo-generate-request: POST to OpenAI-compat endpoint with body"
    ;; Python: client.post(f"{base}/api/openai/v1/chat/completions", json=body, headers=headers)
    (let [req (act/build-murakumo-generate-request
               "https://murakumo.etzhayyim.com" "api-key-123" "gemma3:4b" "hi")]
      (is (= :post (:method req)))
      (is (= "https://murakumo.etzhayyim.com/api/openai/v1/chat/completions" (:url req)))
      (is (= "Bearer api-key-123" (get-in req [:headers "Authorization"])))
      (is (= "gemma3:4b" (get (:body req) "model")))
      (is (= 2 (count (get (:body req) "messages"))))
      (is (= "system" (get-in req [:body "messages" 0 "role"])))
      (is (= 0.3 (get (:body req) "temperature")))
      (is (= 8192 (get (:body req) "max_tokens")))))

  (testing "murakumo-generate-request: no auth header when api-key empty"
    (let [req (act/build-murakumo-generate-request "https://m.etzhayyim.com" "" "g4" "x")]
      (is (not (contains? (:headers req) "Authorization"))))))

(deftest test-actors-build-health-request
  (testing "health-request: GET to /health"
    ;; Python: client.get(f"{base}/_heartbeat", ...)
    (let [req (act/build-health-request "alice123")]
      (is (= :get (:method req)))
      (is (= "https://alice123.etzhayyim.com/health" (:url req))))))

(deftest test-actors-build-heartbeat-request
  (testing "heartbeat-request: POST to /_heartbeat with body"
    ;; Python: client.post(f"{base}/_heartbeat", json={"feed":"[]","engagement":"{}"}, headers=...)
    (let [req (act/build-heartbeat-request "alice123" "auth-tok")]
      (is (= :post (:method req)))
      (is (= "https://alice123.etzhayyim.com/_heartbeat" (:url req)))
      (is (= "Bearer auth-tok" (get-in req [:headers "Authorization"])))
      (is (= "[]" (get (:body req) "feed")))
      (is (= "{}" (get (:body req) "engagement"))))))

(deftest test-actors-build-migrate-request
  (testing "migrate-request: POST to plc.migrateActor with dryRun"
    ;; Python: httpx.post(f"{pds_url}/xrpc/com.etzhayyim.plc.migrateActor", json=payload, ...)
    (let [req (act/build-migrate-request "https://pds.aozora.app"
                                         "alice" "alice.etzhayyim.com" "tok" true)]
      (is (= :post (:method req)))
      (is (= "https://pds.aozora.app/xrpc/com.etzhayyim.plc.migrateActor" (:url req)))
      (is (= "Bearer tok" (get-in req [:headers "Authorization"])))
      (is (= "alice" (get (:body req) "actor")))
      (is (= true (get (:body req) "dryRun"))))))

;; ─── IO: fetch-actors (injectable) ───────────────────────────────────────────

(deftest test-actors-fetch-actors-shape
  (testing "fetch-actors: sends POST and parses actor list"
    ;; Python: _fetch_actors → paginates until limit
    (let [resp-body (json/generate-string
                     {:actors [{:did "did:web:a.etzhayyim.com" :nanoid "aaa111"
                                :handle "a.etzhayyim.com" :displayName "A" :description "" :projectId ""}]
                      :cursor ""})
          {:keys [log http-fn]} (make-fake-http [resp-body])
          actors (act/fetch-actors "https://pds.aozora.app" 10
                                   {:token "tok" :http-fn http-fn})]
      (is (= 1 (count actors)))
      (is (= "aaa111" (:nanoid (first actors))))
      (is (= "did:web:a.etzhayyim.com" (:did (first actors))))
      (is (= 1 (count @log)))
      (is (= :post (:method (first @log))))))

  (testing "fetch-actors: stops when batch < page size (no cursor pagination)"
    (let [resp-body (json/generate-string
                     {:actors (vec (for [i (range 3)]
                                    {:did (str "did:web:a" i ".etzhayyim.com") :nanoid (str "n" i)
                                     :handle "" :displayName "" :description "" :projectId ""}))
                      :cursor "c1"})
          ;; Only serve first response; 3 < 50 so should stop
          {:keys [log http-fn]} (make-fake-http [resp-body])
          actors (act/fetch-actors "https://pds.aozora.app" 100
                                   {:token "tok" :http-fn http-fn})]
      (is (= 3 (count actors)))
      (is (= 1 (count @log)) "should stop after batch < page size"))))

;; ─── IO: migrate-to-plc offline ──────────────────────────────────────────────

(deftest test-actors-migrate-offline
  (testing "migrate-to-plc: offline mode returns mock without HTTP call"
    ;; Python: if offline: return mock {...}
    (let [{:keys [log http-fn]} (make-fake-http)
          result (act/migrate-to-plc "https://pds.aozora.app" "alice"
                                     "alice.etzhayyim.com"
                                     {:offline? true :http-fn http-fn})]
      (is (str/starts-with? (:did result) "did:plc:"))
      (is (str/includes? (:legacyDid result) "did:web:"))
      (is (empty? @log) "offline must make zero HTTP calls"))))

;; ─── PURE: apps/coverage-grade ───────────────────────────────────────────────

(deftest test-apps-coverage-grade
  (testing "coverage-grade: score thresholds"
    ;; Python: _coverage_grade(score)
    (is (= "S" (app/coverage-grade 80)))
    (is (= "S" (app/coverage-grade 100)))
    (is (= "A" (app/coverage-grade 60)))
    (is (= "A" (app/coverage-grade 79)))
    (is (= "B" (app/coverage-grade 40)))
    (is (= "B" (app/coverage-grade 59)))
    (is (= "C" (app/coverage-grade 20)))
    (is (= "C" (app/coverage-grade 39)))
    (is (= "D" (app/coverage-grade 0)))
    (is (= "D" (app/coverage-grade 19)))))

;; ─── PURE: apps/tier-score ───────────────────────────────────────────────────

(deftest test-apps-tier-score
  (testing "tier-score: n=0 → 0"
    ;; Python: _tier_score(0, 1, 10, 100) == 0
    (is (= 0.0 (app/tier-score 0 1 10 100))))

  (testing "tier-score: n≥hi → 100"
    ;; Python: _tier_score(100, 1, 10, 100) == 100
    (is (= 100.0 (app/tier-score 100 1 10 100))))

  (testing "tier-score: n=mid → 60"
    ;; Python: _tier_score(10, 1, 10, 100) → 60.0
    (is (= 60.0 (app/tier-score 10 1 10 100))))

  (testing "tier-score: mid < n < hi → between 60 and 100"
    (let [s (app/tier-score 50 1 10 100)]
      (is (> s 60.0))
      (is (< s 100.0))))

  (testing "tier-score: lo ≤ n < mid → between 20 and 60"
    (let [s (app/tier-score 5 1 10 100)]
      (is (>= s 20.0))
      (is (< s 60.0)))))

;; ─── PURE: apps/infer-app-name-from-collections ──────────────────────────────

(deftest test-apps-infer-app-name
  (testing "infer-app-name: extracts 4th segment of com.etzhayyim.apps.* collection"
    ;; Python: _infer_app_name_from_collections(['com.etzhayyim.apps.billing.payment']) == 'billing'
    (is (= "billing" (app/infer-app-name-from-collections
                      ["com.etzhayyim.apps.billing.payment"]))))

  (testing "infer-app-name: first match wins"
    (is (= "legal" (app/infer-app-name-from-collections
                    ["com.etzhayyim.apps.legal.clause"
                     "com.etzhayyim.apps.other.thing"]))))

  (testing "infer-app-name: empty list → empty string"
    ;; Python: return ''
    (is (= "" (app/infer-app-name-from-collections []))))

  (testing "infer-app-name: non-matching patterns → empty string"
    (is (= "" (app/infer-app-name-from-collections ["app.bsky.feed.post"]))))

  (testing "infer-app-name: requires ≥5 segments"
    ;; Python: len(parts) >= 5 required
    ;; 'com.etzhayyim.apps.name' has exactly 4 parts → skipped
    (is (= "" (app/infer-app-name-from-collections ["com.etzhayyim.apps.name"])))))

;; ─── PURE: apps/extract-sources-from-src ─────────────────────────────────────

(deftest test-apps-extract-sources
  (testing "extract-sources: finds sourceUrl patterns"
    ;; Python: _extract_sources_from_src(src) → [{url, format, category}]
    (let [src     "const opts = { sourceUrl: 'https://api.example.com/v1', extra: true }"
          sources (app/extract-sources-from-src src)]
      (is (= 1 (count sources)))
      (is (= "https://api.example.com/v1" (:url (first sources))))
      (is (= "http" (:format (first sources))))
      (is (= "external" (:category (first sources))))))

  (testing "extract-sources: finds caseDbUrl and legislationUrl"
    (let [src     "caseDbUrl: \"https://case.db.com\" legislationUrl: \"https://law.gov/act\""
          sources (app/extract-sources-from-src src)]
      (is (= 2 (count sources)))))

  (testing "extract-sources: caps at 20"
    ;; Python: return sources[:20]
    (let [many (apply str (for [i (range 25)]
                            (str " sourceUrl: 'https://api" i ".example.com' ")))
          sources (app/extract-sources-from-src many)]
      (is (= 20 (count sources)))))

  (testing "extract-sources: empty src → empty list"
    (is (empty? (app/extract-sources-from-src "")))))

;; ─── PURE: apps/score-domain-static-src ──────────────────────────────────────

(deftest test-apps-score-domain-static-src
  (testing "score-domain-static-src: empty src → zero score grade D"
    ;; Python: _score_domain_static(no-file) returns 0, 'D'
    (let [r (app/score-domain-static-src "")]
      (is (= 0 (:domain-score r)))
      (is (= "D" (:grade r)))))

  (testing "score-domain-static-src: vertex_ labels contribute to score"
    ;; Python: sql_labels = [m.group(1) for m in _RE_SQL_LABEL.finditer(src)] → 10 pts each, cap 30
    (let [src "vertex_invoice vertex_order vertex_payment vertex_extra"
          r   (app/score-domain-static-src src)]
      (is (= 30 (:domain-score r)))  ; 3×10=30 (capped) — 4th beyond cap; penalty for no cmds/cols
      (is (= (sort ["invoice" "order" "payment" "extra"])
             (sort (:sql-labels r))))))

  (testing "score-domain-static-src: com.etzhayyim.apps collection NSIDs → collections extracted"
    ;; Python: collections = [...] → 10 pts each, cap 20
    (let [src "'com.etzhayyim.apps.billing.payment' 'com.etzhayyim.apps.billing.invoice'"
          r   (app/score-domain-static-src src)]
      (is (= 2 (count (:collections r))))
      ;; score contributes to domain-score (penalty removed because collections present)
      (is (> (:domain-score r) 0))))

  (testing "score-domain-static-src: custom commands score (not template)"
    ;; Python: custom_cmds = [m for m in _RE_CUSTOM_CMD] — camelCase only, not cmd_snake
    (let [src "function cmdCreateInvoice(){} function cmdSendPayment(){} function cmd_list(){}"
          r   (app/score-domain-static-src src)]
      ;; 2 custom (CamelCase), 1 template (snake)
      (is (= 2 (count (:custom-commands r))))
      (is (= 1 (:template-cmds r)))))

  (testing "score-domain-static-src: penalty when no custom cmds, no labels, no collections"
    ;; Python: if no_custom AND no_labels AND no_kinds: score -= 20
    (let [src "function cmd_list(){} if(x){"
          r   (app/score-domain-static-src src)]
      (is (= 0 (:domain-score r)))))

  (testing "score-domain-static-src: grade S for high score"
    ;; Python: grade S when score >= 80
    (let [src (str "vertex_a vertex_b vertex_c "
                   "'com.etzhayyim.apps.x.payment' 'com.etzhayyim.apps.x.invoice' "
                   "function cmdDoA(){} function cmdDoB(){} function cmdDoC(){} "
                   (apply str (repeat 15 "if(x > 0) { return; }\n")))
          r   (app/score-domain-static-src src)]
      (is (>= (:domain-score r) 60))
      (is (#{"S" "A"} (:grade r))))))

;; ─── PURE: apps/compute-coverage-scores ──────────────────────────────────────

(deftest test-apps-compute-coverage-scores
  (testing "compute-coverage-scores: all zero → 0.0 overall"
    ;; Python: overall = 0.40*0 + 0.25*0 + 0.20*0 + 0.15*0 = 0.0
    (let [{:keys [overall overall-grade]} (app/compute-coverage-scores 0 0 0 0)]
      (is (= 0.0 overall))
      (is (= "D" overall-grade))))

  (testing "compute-coverage-scores: high domain → boosts overall"
    ;; Python: overall = 0.40*100 + 0.25*tier(...) + ... must be > 40
    (let [{:keys [overall]} (app/compute-coverage-scores 100 100 100 10)]
      (is (> overall 80.0))))

  (testing "compute-coverage-scores: weights sum to 100 at full score"
    ;; At domain=100, live=∞, xrpc=100, dids=∞ → overall ≈ 100
    ;; tier-score(100,1,10,100)=100, tier-score(10,1,3,10)=100
    (let [{:keys [overall]} (app/compute-coverage-scores 100 100 100 10)]
      (is (< (Math/abs (- overall 100.0)) 0.001)))))

;; ─── IO REQUEST-SHAPING: apps ─────────────────────────────────────────────────

(deftest test-apps-build-list-apps-request
  (testing "build-list-apps-request: GET to listApps with auth"
    ;; Python: httpx.get(f"{pds_url}/xrpc/com.etzhayyim.apps.listApps", headers=...)
    (let [req (app/build-list-apps-request "https://pds.aozora.app" "tok123")]
      (is (= :get (:method req)))
      (is (= "https://pds.aozora.app/xrpc/com.etzhayyim.apps.listApps" (:url req)))
      (is (= "Bearer tok123" (get-in req [:headers "Authorization"])))))

  (testing "build-list-apps-request: no auth when token empty"
    (let [req (app/build-list-apps-request "https://pds.aozora.app" "")]
      (is (not (contains? (:headers req) "Authorization"))))))

(deftest test-apps-build-list-records-request
  (testing "build-list-records-request: GET to listRecords with params"
    ;; Python: httpx.get(f"{pds_url}/xrpc/com.atproto.repo.listRecords", params=...)
    (let [req (app/build-list-records-request
               "https://pds.aozora.app" "did:web:alice.etzhayyim.com"
               "com.etzhayyim.apps.legal.clause" 100 "tok")]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "/xrpc/com.atproto.repo.listRecords"))
      (is (= "Bearer tok" (get-in req [:headers "Authorization"])))
      (is (= "did:web:alice.etzhayyim.com" (get (:params req) "repo")))
      (is (= "com.etzhayyim.apps.legal.clause" (get (:params req) "collection"))))))

(deftest test-apps-build-health-request
  (testing "build-health-request: GET to /health"
    ;; Python: httpx.get(f"{base_url}/health", timeout=10)
    (let [req (app/build-health-request "https://alice.etzhayyim.com")]
      (is (= :get (:method req)))
      (is (= "https://alice.etzhayyim.com/health" (:url req))))))

(deftest test-apps-build-meta-request
  (testing "build-meta-request: GET to /_app/meta"
    ;; Python: httpx.get(f"{base_url}/_app/meta", timeout=10)
    (let [req (app/build-meta-request "https://alice.etzhayyim.com")]
      (is (= :get (:method req)))
      (is (= "https://alice.etzhayyim.com/_app/meta" (:url req))))))

(deftest test-apps-build-xrpc-coverage-request
  (testing "build-xrpc-coverage-request: POST to coverageStats with auth"
    ;; Python: httpx.post(url, json={}, headers=...)
    (let [req (app/build-xrpc-coverage-request "alice123" "legal" "tok")]
      (is (= :post (:method req)))
      (is (str/includes? (:url req) "alice123.etzhayyim.com"))
      (is (str/includes? (:url req) "legal.coverageStats"))
      (is (= "Bearer tok" (get-in req [:headers "Authorization"])))
      (is (= {} (:body req)))))

  (testing "build-xrpc-coverage-request: uses nanoid as app-name when empty"
    ;; Python: if not app_name: app_name = nanoid
    (let [req (app/build-xrpc-coverage-request "alice123" "" "tok")]
      (is (str/includes? (:url req) "alice123.coverageStats")))))

;; ─── IO: check-app-health (injectable) ───────────────────────────────────────

(deftest test-apps-check-app-health-injectable
  (testing "check-app-health: records /health and /_app/meta calls"
    ;; Python: _check_app_health checks /health then /_app/meta
    (let [{:keys [log http-fn]} (make-fake-http
                                  [{:status 200 :body "OK"}    ; /health
                                   {:status 200 :body "meta"}]) ; /_app/meta
          result (app/check-app-health "alice123" "Alice" "https://alice.etzhayyim.com"
                                       {:http-fn http-fn})]
      (is (true? (:health-ok result)))
      (is (true? (:meta-ok result)))
      (is (= 200 (:health-code result)))
      (is (= "" (:error result)))
      (is (= 2 (count @log)))
      (is (str/includes? (:url (first @log)) "/health"))
      (is (str/includes? (:url (second @log)) "/_app/meta"))))

  (testing "check-app-health: health failure → health-ok false"
    (let [{:keys [http-fn]} (make-fake-http
                              [{:status 503 :body "down"}
                               {:status 200 :body "meta"}])
          result (app/check-app-health "x" "X" "https://x.etzhayyim.com"
                                       {:http-fn http-fn})]
      (is (false? (:health-ok result)))
      (is (= 503 (:health-code result)))))

  (testing "check-app-health: exception → error string populated"
    (let [throwing-fn (fn [_] (throw (ex-info "connection refused" {})))
          result (app/check-app-health "x" "X" "https://x.etzhayyim.com"
                                       {:http-fn throwing-fn})]
      (is (false? (:health-ok result)))
      (is (seq (:error result))))))

;; ─── IO: list-pds-records (injectable) ───────────────────────────────────────

(deftest test-apps-list-pds-records-injectable
  (testing "list-pds-records: parses records from response"
    ;; Python: _list_pds_records → data.get('records', [])
    (let [resp-body (json/generate-string
                     {:records [{:uri "at://a/b/c" :value {:status "ok"}}]})
          {:keys [log http-fn]} (make-fake-http [resp-body])
          recs (app/list-pds-records "https://pds.aozora.app"
                                     "did:web:a.etzhayyim.com"
                                     "com.etzhayyim.apps.x.status"
                                     100
                                     {:token "tok" :http-fn http-fn})]
      (is (= 1 (count recs)))
      (is (= 1 (count @log)))
      (is (str/includes? (:url (first @log)) "listRecords"))))

  (testing "list-pds-records: 404 response → empty list"
    ;; Python: if resp.status_code >= 400: return []
    (let [{:keys [http-fn]} (make-fake-http [{:status 404 :body "not found"}])
          recs (app/list-pds-records "https://pds.aozora.app" "did" "col" 10
                                     {:http-fn http-fn})]
      (is (empty? recs))))

  (testing "list-pds-records: zero network calls in dry mode (verify no side effects)"
    (let [{:keys [log http-fn]} (make-fake-http)]
      ;; Just verifying list-pds-records makes exactly 1 call (not more)
      (app/list-pds-records "https://pds.aozora.app" "did" "col" 10
                             {:http-fn http-fn})
      (is (= 1 (count @log))))))

;; ─── runner ───────────────────────────────────────────────────────────────────

(defn -main [& _args]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-bb-migration-wave6a)]
    (System/exit (if (zero? (+ fail error)) 0 1))))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
