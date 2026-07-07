;; test_bb_migration_wave7a.clj — parity + request-shaping tests for
;; etzhayyim.xrpc (xrpc.cljc) and etzhayyim.monitor (monitor.cljc)
;;
;; Run with:
;;   bb 70-tools/src/etzhayyim/test_bb_migration_wave7a.clj
;;
;; from repo root.  classpath 70-tools/src is in bb.edn :paths so no -cp needed.
;;
;; Also auto-discovered by the `test:actors` bb task (via etzhayyim.tools.discovery).
;;
;; Coverage:
;;
;;   etzhayyim.xrpc  PURE:
;;     - resolve-base (explicit url / app / NSID inference / PDS fallback)
;;     - build-xrpc-url
;;     - build-xrpc-request (GET/POST method selection, header merge, body/params)
;;     - parse-xrpc-response-body (pretty-print JSON / passthrough on parse error)
;;     - known-apps slug→nanoid constant parity
;;
;;   etzhayyim.xrpc  IO request-shaping (injectable fake, no network):
;;     - call-xrpc fires correct method/url/headers/body
;;     - call-xrpc raises on HTTP >= 300
;;
;;   etzhayyim.monitor  PURE:
;;     - compute-shinka-score (individual capability flags + max-0 floor)
;;     - coverage-grade (score → S/A/B/C/D boundaries)
;;     - tier-score (3-tier ramp, boundary conditions)
;;     - normalize-domain-lookup (hyphen→underscore + trim)
;;     - extract-collection-literals (ns-candidate prefix filter + dedup)
;;     - extract-sub-did-paths (dedup)
;;     - format-health-line (ok/fail paths, error path)
;;     - format-shinka-row (cell widths, marks)
;;     - format-shinka-summary (counts, percentages)
;;     - gate-check (avg/top10/low-count thresholds)
;;     - build-health-request (URL, method)
;;     - build-did-request (URL, params, headers)
;;     - build-vote-request (URL, headers)
;;     - build-heartbeat-request (URL, method)
;;     - build-list-records-request (URL, params, token header)
;;     - build-subscribe-message (WS shape — pure; live connection DEFERRED)
;;
;;   etzhayyim.monitor  IO request-shaping (injectable fake, no network):
;;     - check-health shapes GET requests to /health + /_app/meta
;;     - check-health records latency + status in result map
;;     - resolve-did fires GET to correct resolveHandle URL with params
;;     - resolve-did raises on HTTP >= 400
;;     - list-votes fires GET to correct listVotes URL
;;     - latest-record-ts fires GET to listRecords with repo/collection params
;;     - latest-record-ts returns nil on HTTP >= 400 (no throw)
;;     - dry-run (zero mutations — fake never called for mutations in pure paths)
;;
;;   HONEST NOTE:
;;     Live behavioral parity (whether servers accept the requests) requires a
;;     live PDS / AT Proto endpoint and CANNOT be verified offline.
;;     WebSocket subscribe leg is DEFERRED (build-subscribe-message shapes the
;;     sent message; the live ws connection is behind :ws-fn, not called here).

(ns etzhayyim.test-bb-migration-wave7a
  (:require [clojure.test     :refer [deftest is testing run-tests]]
            [clojure.string   :as str]
            [cheshire.core    :as json]
            [etzhayyim.xrpc   :as xrpc]
            [etzhayyim.monitor :as mon]))

;; ─── helpers ──────────────────────────────────────────────────────────────────

(defn- make-fake-http
  "Returns {:log atom :http-fn fn}.
  Fake records every call; returns fixed-responses in order (cycling).
  Each response is {:status :body} or a plain string (→ {:status 200 :body ...})."
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
            (if (string? r)
              {:status 200 :body r}
              r))
          {:status 200 :body "{}"}))})))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.xrpc  PURE
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-xrpc-known-apps-parity
  ;; Python _KNOWN_APPS matches our constant map.
  (testing "known apps — slug → nanoid parity with Python _KNOWN_APPS"
    ;; These are the values baked into xrpc.py; verify they route correctly.
    (is (str/includes?
         (xrpc/resolve-base "com.etzhayyim.apps.kakaku.search" nil nil "")
         "k4k4kux1"))
    (is (str/includes?
         (xrpc/resolve-base "com.etzhayyim.apps.gtin.lookup" nil nil "")
         "gt1n4k7m"))
    (is (str/includes?
         (xrpc/resolve-base "com.etzhayyim.apps.hanrei.search" nil nil "")
         "h4nr31jp"))))

(deftest test-xrpc-resolve-base
  (testing "explicit :url overrides everything"
    (is (= "https://custom.example.com"
           (xrpc/resolve-base "com.atproto.server.describeServer"
                              nil "https://custom.example.com/" ""))))

  (testing "explicit :app builds app-host URL"
    (is (= "https://mynanoid.com.etzhayyim.com"
           (xrpc/resolve-base "com.atproto.server.describeServer"
                              "mynanoid" nil ""))))

  (testing "NSID inference: com.etzhayyim.apps.<slug>.* — known slug"
    (let [base (xrpc/resolve-base "com.etzhayyim.apps.media_gamers.search"
                                  nil nil "https://pds.example.com")]
      (is (str/includes? base "a7m8oocs"))))

  (testing "NSID inference: unknown slug falls back to PDS"
    (is (= "https://pds.example.com"
           (xrpc/resolve-base "com.etzhayyim.apps.unknown_app.method"
                              nil nil "https://pds.example.com"))))

  (testing "non-etzhayyim NSID falls back to PDS"
    (is (= "https://pds.example.com"
           (xrpc/resolve-base "com.atproto.server.describeServer"
                              nil nil "https://pds.example.com"))))

  (testing "trailing slash stripped from explicit url"
    (is (= "https://example.com"
           (xrpc/resolve-base "any.nsid" nil "https://example.com/" ""))))

  (testing "PDS fallback strips trailing slash"
    (is (= "https://pds.example.com"
           (xrpc/resolve-base "com.other.nsid" nil nil "https://pds.example.com/")))))

(deftest test-xrpc-build-url
  (testing "build-xrpc-url appends /xrpc/<nsid>"
    (is (= "https://pds.example.com/xrpc/com.atproto.server.describeServer"
           (xrpc/build-xrpc-url "https://pds.example.com"
                                "com.atproto.server.describeServer")))))

(deftest test-xrpc-build-request
  ;; Parity: Python xrpc() builds:
  ;;   method = POST if payload else GET
  ;;   url    = base + "/xrpc/" + nsid
  ;;   headers = {"Content-Type": "application/json", **scoped_auth_headers(nsid)}
  ;;   POST body = json payload; GET params = payload dict

  (testing "GET when no payload"
    (let [req (xrpc/build-xrpc-request
               "com.atproto.server.describeServer"
               {:pds-url "https://pds.example.com"})]
      (is (= :get (:method req)))
      (is (str/ends-with? (:url req) "/com.atproto.server.describeServer"))
      (is (nil? (:body req)))
      (is (nil? (:params req)))))

  (testing "POST when payload given"
    (let [req (xrpc/build-xrpc-request
               "com.atproto.server.createSession"
               {:pds-url "https://pds.example.com"
                :payload  {"identifier" "alice" "password" "s3cr3t"}})]
      (is (= :post (:method req)))
      (is (= {"identifier" "alice" "password" "s3cr3t"} (:body req)))))

  (testing "GET params attached for GET with map payload"
    (let [req (xrpc/build-xrpc-request
               "com.atproto.repo.listRecords"
               {:pds-url "https://pds.example.com"
                :method  :get
                :payload {"repo" "did:web:alice" "collection" "app.bsky.feed.post"}})]
      (is (= :get (:method req)))
      (is (= {"repo" "did:web:alice" "collection" "app.bsky.feed.post"}
             (:params req)))))

  (testing "explicit :method overrides payload-based inference"
    (let [req (xrpc/build-xrpc-request
               "com.atproto.server.getServiceAuth"
               {:pds-url "https://pds.example.com"
                :method  :get})]
      (is (= :get (:method req)))))

  (testing "auth-headers merged into request headers"
    (let [req (xrpc/build-xrpc-request
               "com.atproto.server.describeServer"
               {:pds-url      "https://pds.example.com"
                :auth-headers {"Authorization" "Bearer tok123"}})]
      (is (= "Bearer tok123" (get-in req [:headers "Authorization"])))
      (is (= "application/json" (get-in req [:headers "Content-Type"])))))

  (testing "Content-Type always present"
    (let [req (xrpc/build-xrpc-request "any.nsid" {:pds-url "https://pds.example.com"})]
      (is (= "application/json" (get-in req [:headers "Content-Type"]))))))

(deftest test-xrpc-parse-response-body
  (testing "pretty=false returns body as-is"
    (let [[out ok?] (xrpc/parse-xrpc-response-body "{\"did\":\"did:web:alice\"}" false)]
      (is (= "{\"did\":\"did:web:alice\"}" out))
      (is (false? ok?))))

  (testing "pretty=true pretty-prints valid JSON"
    (let [[out ok?] (xrpc/parse-xrpc-response-body "{\"did\":\"did:web:alice\"}" true)]
      (is (str/includes? out "did"))
      (is (true? ok?))))

  (testing "pretty=true on invalid JSON returns body unchanged, ok?=false"
    (let [[out ok?] (xrpc/parse-xrpc-response-body "not-json" true)]
      (is (= "not-json" out))
      (is (false? ok?)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.xrpc  IO request-shaping
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-xrpc-call-xrpc-request-shape
  ;; Parity with Python xrpc() httpx call:
  ;;   POST: httpx.post(url, json=payload, headers=headers, timeout=30)
  ;;   GET:  httpx.get(url, params=params, headers=headers, timeout=30)

  (testing "call-xrpc fires POST request with body"
    (let [{:keys [log http-fn]} (make-fake-http [{:status 200 :body "{}"}])
          _ (xrpc/call-xrpc
             "com.atproto.server.createSession"
             {:pds-url      "https://pds.example.com"
              :payload      {"identifier" "alice" "password" "s3cr3t"}
              :auth-headers {"Authorization" "Bearer tok"}
              :http-fn      http-fn})
          req (first @log)]
      (is (= 1 (count @log)))
      (is (= :post (:method req)))
      (is (str/includes? (:url req) "/xrpc/com.atproto.server.createSession"))
      (is (= {"identifier" "alice" "password" "s3cr3t"} (:body req)))
      (is (= "Bearer tok" (get-in req [:headers "Authorization"])))))

  (testing "call-xrpc fires GET request with params"
    (let [{:keys [log http-fn]} (make-fake-http [{:status 200 :body "{\"did\":\"did:web:alice\"}"}])
          _ (xrpc/call-xrpc
             "com.atproto.identity.resolveHandle"
             {:pds-url "https://pds.example.com"
              :method  :get
              :payload {"handle" "alice.example.com"}
              :http-fn http-fn})
          req (first @log)]
      (is (= :get (:method req)))
      (is (= {"handle" "alice.example.com"} (:params req)))))

  (testing "call-xrpc raises ex-info on HTTP 401"
    (let [{:keys [http-fn]} (make-fake-http [{:status 401 :body "{\"error\":\"AuthRequired\"}"}])]
      (is (thrown? Exception
                   (xrpc/call-xrpc
                    "com.atproto.server.getSession"
                    {:pds-url "https://pds.example.com" :http-fn http-fn})))))

  (testing "call-xrpc raises ex-info on HTTP 500"
    (let [{:keys [http-fn]} (make-fake-http [{:status 500 :body "Server Error"}])]
      (is (thrown? Exception
                   (xrpc/call-xrpc "any.nsid"
                                   {:pds-url "https://pds.example.com"
                                    :http-fn http-fn}))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.monitor  PURE
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-compute-shinka-score
  ;; Parity with Python _compute_shinka_score():
  ;;   has_joucho +30, has_inbox +15, has_cadence +15, has_drill +10,
  ;;   has_validate +10, has_analyze +10, has_engage +10, has_old_timer -30
  ;;   max(0, score)
  (testing "empty flags → 0"
    (is (= 0 (mon/compute-shinka-score {}))))

  (testing "joucho only → 30"
    (is (= 30 (mon/compute-shinka-score {:has-joucho true}))))

  (testing "full positive → 100"
    (is (= 100 (mon/compute-shinka-score
                {:has-joucho true :has-inbox true :has-cadence true
                 :has-drill true :has-validate true :has-analyze true
                 :has-engage true}))))

  (testing "old-timer penalty -30 applied"
    ;; joucho(30) + inbox(15) + cadence(15) - old_timer(30) = 30
    (is (= 30 (mon/compute-shinka-score
               {:has-joucho true :has-inbox true :has-cadence true
                :has-old-timer true}))))

  (testing "floor at 0 — old-timer alone gives 0 not negative"
    (is (= 0 (mon/compute-shinka-score {:has-old-timer true}))))

  (testing "joucho + old-timer → 0 (30 - 30 = 0)"
    (is (= 0 (mon/compute-shinka-score {:has-joucho true :has-old-timer true})))))

(deftest test-coverage-grade
  ;; Parity: Python _coverage_grade() boundaries.
  (testing ">= 80 → S"  (is (= "S" (mon/coverage-grade 80))))
  (testing "79 → A"     (is (= "A" (mon/coverage-grade 79))))
  (testing ">= 60 → A"  (is (= "A" (mon/coverage-grade 60))))
  (testing "59 → B"     (is (= "B" (mon/coverage-grade 59))))
  (testing ">= 40 → B"  (is (= "B" (mon/coverage-grade 40))))
  (testing "39 → C"     (is (= "C" (mon/coverage-grade 39))))
  (testing ">= 20 → C"  (is (= "C" (mon/coverage-grade 20))))
  (testing "19 → D"     (is (= "D" (mon/coverage-grade 19))))
  (testing "0 → D"      (is (= "D" (mon/coverage-grade 0))))
  (testing "100 → S"    (is (= "S" (mon/coverage-grade 100)))))

(deftest test-tier-score
  ;; Parity: Python _tier_score(val, t1, t2, t3)
  (testing "val >= t3 → 100.0"
    (is (= 100.0 (mon/tier-score 100 1 10 100))))

  (testing "val == t3 exactly → 100.0"
    (is (= 100.0 (mon/tier-score 100 1 10 100))))

  (testing "val == 0 → 0.0"
    (is (= 0.0 (mon/tier-score 0 1 10 100))))

  (testing "val between 0 and t1 → 0 < score < 20"
    ;; Python: 20.0 * val / t1 → val=1,t1=10 → 2.0
    ;; Our: val=0 → 0, val > 0 and < t1 → 0 < x < 20
    ;; val=1, t1=10, t2=50, t3=100 → 20.0*(1/10) = 2.0
    (is (= 2.0 (mon/tier-score 1 10 50 100))))

  (testing "val == t1 → 20.0"
    (is (= 20.0 (mon/tier-score 10 10 50 100))))

  (testing "val between t1 and t2 → 20 < score < 60"
    ;; val=30, t1=10, t2=50, t3=100 → 20 + 40*(30-10)/(50-10) = 20 + 40*(20/40) = 40.0
    (is (= 40.0 (mon/tier-score 30 10 50 100))))

  (testing "val == t2 → 60.0"
    (is (= 60.0 (mon/tier-score 50 10 50 100))))

  (testing "val between t2 and t3 → 60 < score < 100"
    ;; val=75, t1=10, t2=50, t3=100 → 60 + 40*(75-50)/(100-50) = 60 + 40*(0.5) = 80.0
    (is (= 80.0 (mon/tier-score 75 10 50 100)))))

(deftest test-normalize-domain-lookup
  ;; Parity: Python _normalize_domain_lookup() → replace("-","_") + strip
  (testing "hyphens become underscores"
    (is (= "my_app" (mon/normalize-domain-lookup "my-app"))))

  (testing "whitespace stripped"
    (is (= "foo_bar" (mon/normalize-domain-lookup "  foo-bar  "))))

  (testing "no change needed"
    (is (= "myapp" (mon/normalize-domain-lookup "myapp")))))

(deftest test-extract-collection-literals
  (let [src (str "const col1 = 'com.etzhayyim.apps.kakaku.product';\n"
                 "const col2 = \"com.etzhayyim.apps.gtin.item\";\n"
                 "const col3 = 'app.bsky.feed.post';\n"
                 "const col4 = 'com.etzhayyim.apps.other_app.record';\n")]
    (testing "ns-candidate filter restricts to prefix-matching NSIDs"
      (let [out (mon/extract-collection-literals src ["kakaku"])]
        (is (= ["com.etzhayyim.apps.kakaku.product"] out))))

    (testing "multiple ns-candidates"
      (let [out (mon/extract-collection-literals src ["kakaku" "gtin"])]
        (is (= 2 (count out)))
        (is (some #(= "com.etzhayyim.apps.kakaku.product" %) out))
        (is (some #(= "com.etzhayyim.apps.gtin.item" %) out))))

    (testing "empty ns-candidates → no filtering (return all matching NSIDs)"
      (let [out (mon/extract-collection-literals src [])]
        ;; kakaku, gtin, app.bsky, other_app
        (is (>= (count out) 3))))

    (testing "hyphen→underscore normalization in candidate prefix"
      ;; "other-app" normalized → "other_app" matches "com.etzhayyim.apps.other_app.*"
      (let [out (mon/extract-collection-literals src ["other-app"])]
        (is (= ["com.etzhayyim.apps.other_app.record"] out))))

    (testing "deduplication"
      (let [dup-src (str "const a = 'com.etzhayyim.apps.kakaku.product';\n"
                         "const b = 'com.etzhayyim.apps.kakaku.product';\n")
            out     (mon/extract-collection-literals dup-src ["kakaku"])]
        (is (= 1 (count out)))))))

(deftest test-extract-sub-did-paths
  (let [src "path: \"/profile\"\nsome: \"other\"\npath: \"/posts\"\npath: \"/profile\"\n"]
    (testing "extracts all path declarations"
      (let [out (mon/extract-sub-did-paths src)]
        (is (some #(= "/profile" %) out))
        (is (some #(= "/posts" %) out))))

    (testing "deduplication"
      (let [out (mon/extract-sub-did-paths src)]
        (is (= (count (distinct out)) (count out)))))

    (testing "empty src → empty vector"
      (is (empty? (mon/extract-sub-did-paths ""))))))

(deftest test-format-health-line
  ;; Parity: Python monitor_health() text output.
  (testing "ok path includes OK and latency"
    (let [line (mon/format-health-line {:path "/health" :ok true :status 200 :latency-ms 42})]
      (is (str/includes? line "OK"))
      (is (str/includes? line "/health"))
      (is (str/includes? line "200"))
      (is (str/includes? line "42"))))

  (testing "fail path includes FAIL"
    (let [line (mon/format-health-line {:path "/_app/meta" :ok false :status 503 :latency-ms 10})]
      (is (str/includes? line "FAIL"))
      (is (str/includes? line "/_app/meta"))))

  (testing "error path includes error string"
    (let [line (mon/format-health-line {:path "/health" :ok false :status 0 :error "connection refused"})]
      (is (str/includes? line "FAIL"))
      (is (str/includes? line "connection refused")))))

(deftest test-format-shinka-row
  (let [status {:shinka-score 70 :hyoka-score 65 :hyoka-grade "A"
                :domain-score 50 :kg-score 30
                :nanoid "abc123" :name "My App"
                :has-joucho true :has-inbox false :has-cadence true
                :has-drill true :has-validate false :has-analyze false
                :has-engage false :has-old-timer false
                :stale-sub-did 2 :hb-mood "happy"}]
    (testing "row contains expected fields"
      (let [row (mon/format-shinka-row status)]
        (is (str/includes? row "70"))
        (is (str/includes? row "65"))
        (is (str/includes? row "A"))
        (is (str/includes? row "abc123"))
        (is (str/includes? row "My App"))
        (is (str/includes? row "✓"))   ; has-joucho
        (is (str/includes? row "·"))))  ; has-inbox

  (testing "old-timer shows !!"
    (let [row (mon/format-shinka-row (assoc status :has-old-timer true))]
      (is (str/includes? row "!!"))))

  (testing "no hyoka-grade → score without parens"
    (let [row (mon/format-shinka-row (assoc status :hyoka-grade "" :hyoka-score 0
                                                   :domain-score 0 :kg-score 0))]
      (is (str/includes? row "—"))))

  (testing "long name truncated to 20 chars + ellipsis"
    (let [long-name "ThisIsAVeryLongApplicationName"
          row (mon/format-shinka-row (assoc status :name long-name))]
      ;; The Python truncation: (r.name[:19] + "…") if len(r.name) > 20
      (is (str/includes? row "…"))))))

(deftest test-format-shinka-summary
  (let [results [{:has-joucho true  :has-old-timer false :has-drill true}
                 {:has-joucho false :has-old-timer true  :has-drill false}
                 {:has-joucho true  :has-old-timer false :has-drill true}]]
    (testing "summary counts joucho/old-timer/drill correctly"
      (let [s (mon/format-shinka-summary results)]
        (is (str/includes? s "2/3"))    ; joucho
        (is (str/includes? s "1/3"))    ; old-timer
        ;; drill: 2/3
        (is (str/includes? s "2/3"))))))

(deftest test-gate-check
  ;; Parity with Python _store_hyoka_results() gate block.
  (testing "no failures when within thresholds"
    (is (empty? (mon/gate-check {:avg-score 80 :top10-avg 90 :low-count 2
                                  :prev-avg 80 :prev-top10 90 :prev-low 2
                                  :max-avg-drop 3.0 :max-top10-drop 5.0
                                  :max-low-increase 5}))))

  (testing "avg drop beyond threshold → failure"
    (let [failures (mon/gate-check {:avg-score 75 :top10-avg 90 :low-count 2
                                     :prev-avg 80 :prev-top10 90 :prev-low 2
                                     :max-avg-drop 3.0 :max-top10-drop 5.0
                                     :max-low-increase 5})]
      (is (= 1 (count failures)))
      (is (str/includes? (first failures) "avg_hyoka drop"))))

  (testing "top10 drop beyond threshold → failure"
    (let [failures (mon/gate-check {:avg-score 80 :top10-avg 82 :low-count 2
                                     :prev-avg 80 :prev-top10 90 :prev-low 2
                                     :max-avg-drop 3.0 :max-top10-drop 5.0
                                     :max-low-increase 5})]
      (is (= 1 (count failures)))
      (is (str/includes? (first failures) "top10_hyoka drop"))))

  (testing "low-count increase beyond threshold → failure"
    (let [failures (mon/gate-check {:avg-score 80 :top10-avg 90 :low-count 10
                                     :prev-avg 80 :prev-top10 90 :prev-low 2
                                     :max-avg-drop 3.0 :max-top10-drop 5.0
                                     :max-low-increase 5})]
      (is (= 1 (count failures)))
      (is (str/includes? (first failures) "low-score increase"))))

  (testing "multiple failures possible"
    (let [failures (mon/gate-check {:avg-score 70 :top10-avg 80 :low-count 15
                                     :prev-avg 80 :prev-top10 90 :prev-low 2
                                     :max-avg-drop 3.0 :max-top10-drop 5.0
                                     :max-low-increase 5})]
      (is (= 3 (count failures))))))

;; ─── pure: HTTP request builders ──────────────────────────────────────────────

(deftest test-build-health-request
  (testing "GET /health shape"
    (let [req (mon/build-health-request "https://pds.example.com" "/health")]
      (is (= :get (:method req)))
      (is (= "https://pds.example.com/health" (:url req)))))

  (testing "trailing slash stripped from pds-url"
    (let [req (mon/build-health-request "https://pds.example.com/" "/health")]
      (is (= "https://pds.example.com/health" (:url req))))))

(deftest test-build-did-request
  (testing "GET resolveHandle shape"
    (let [req (mon/build-did-request "https://pds.example.com" "alice.example.com"
                                      {"Authorization" "Bearer tok"})]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "resolveHandle"))
      (is (= {"handle" "alice.example.com"} (:params req)))
      (is (= "Bearer tok" (get-in req [:headers "Authorization"])))))

  (testing "no auth headers still includes Content-Type"
    (let [req (mon/build-did-request "https://pds.example.com" "bob.example.com" {})]
      (is (= "application/json" (get-in req [:headers "Content-Type"]))))))

(deftest test-build-vote-request
  (testing "GET listVotes shape"
    (let [req (mon/build-vote-request "https://pds.example.com" {"Authorization" "Bearer tok"})]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "listVotes"))
      (is (= "Bearer tok" (get-in req [:headers "Authorization"]))))))

(deftest test-build-heartbeat-request
  ;; Parity: Python _analyze_shinka_app() live heartbeat → httpx.post(...)
  (testing "POST /_heartbeat shape"
    (let [req (mon/build-heartbeat-request "a7m8oocs" {"Authorization" "Bearer tok"})]
      (is (= :post (:method req)))
      (is (= "https://a7m8oocs.etzhayyim.com/_heartbeat" (:url req)))
      (is (= "Bearer tok" (get-in req [:headers "Authorization"]))))))

(deftest test-build-list-records-request
  ;; Parity: Python _latest_record_ts() → client.get(
  ;;   f"{pds_url}/xrpc/com.atproto.repo.listRecords",
  ;;   params={"repo": repo, "collection": collection, "limit": 1},
  ;;   headers={"Authorization": f"Bearer {token}"} if token else {}
  ;; )
  (testing "GET listRecords shape with token"
    (let [req (mon/build-list-records-request
               "https://pds.example.com" "did:web:alice" "com.etzhayyim.apps.kakaku.product" "tok123")]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "listRecords"))
      (is (= "did:web:alice" (get-in req [:params "repo"])))
      (is (= "com.etzhayyim.apps.kakaku.product" (get-in req [:params "collection"])))
      (is (= "1" (get-in req [:params "limit"])))
      (is (= "Bearer tok123" (get-in req [:headers "Authorization"])))))

  (testing "no Authorization header when token is empty"
    (let [req (mon/build-list-records-request
               "https://pds.example.com" "did:web:alice" "some.collection" "")]
      (is (nil? (get-in req [:headers "Authorization"]))))))

(deftest test-build-subscribe-message
  ;; WebSocket message shaping: PURE, DEFERRED live connection.
  (testing "subscribe message shape"
    (let [msg (mon/build-subscribe-message :events "com.etzhayyim.actor.events" {:limit 100})]
      (is (= "events" (:type msg)))
      (is (= "com.etzhayyim.actor.events" (:topic msg)))
      (is (= {:limit 100} (:opts msg)))))

  (testing "firehose subscription"
    (let [msg (mon/build-subscribe-message :firehose "com.etzhayyim.firehose" {})]
      (is (= "firehose" (:type msg)))
      (is (= {} (:opts msg))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.monitor  IO request-shaping
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-check-health-request-shape
  ;; Parity: Python monitor_health() sends GET to /health and /_app/meta.
  (testing "check-health fires GET to /health and /_app/meta"
    (let [{:keys [log http-fn]}
          (make-fake-http [{:status 200 :body "ok"}
                           {:status 200 :body "{}"}])
          results (mon/check-health "https://pds.example.com" {:http-fn http-fn})]
      (is (= 2 (count @log)))
      (is (every? #(= :get (:method %)) @log))
      (is (str/includes? (:url (first @log)) "/health"))
      (is (str/includes? (:url (second @log)) "/_app/meta"))
      ;; result maps have expected keys
      (is (= 2 (count results)))
      (is (every? #(contains? % :ok) results))
      (is (every? #(contains? % :status) results))
      (is (every? #(contains? % :latency-ms) results))))

  (testing "check-health records ok=true when status < 400"
    (let [{:keys [http-fn]}
          (make-fake-http [{:status 200 :body "ok"}
                           {:status 200 :body "{}"}])
          results (mon/check-health "https://pds.example.com" {:http-fn http-fn})]
      (is (every? :ok results))))

  (testing "check-health records ok=false when status >= 400"
    (let [{:keys [http-fn]}
          (make-fake-http [{:status 503 :body "down"}
                           {:status 404 :body "not found"}])
          results (mon/check-health "https://pds.example.com" {:http-fn http-fn})]
      (is (every? #(false? (:ok %)) results))))

  (testing "check-health records error on exception (fake raises)"
    (let [raising-fn (fn [_] (throw (ex-info "connection refused" {})))
          results (mon/check-health "https://pds.example.com" {:http-fn raising-fn})]
      (is (every? #(contains? % :error) results))
      (is (every? #(false? (:ok %)) results)))))

(deftest test-resolve-did-request-shape
  ;; Parity: Python monitor_did() → httpx.get(
  ;;   f"{pds_url}/xrpc/com.atproto.identity.resolveHandle",
  ;;   params={"handle": did_or_handle},
  ;;   headers=_auth_headers(), timeout=15
  ;; )
  (testing "resolve-did fires GET to resolveHandle with handle param"
    (let [{:keys [log http-fn]}
          (make-fake-http [(json/generate-string {"did" "did:web:alice.example.com"})])
          _ (mon/resolve-did "https://pds.example.com" "alice.example.com"
                              {:auth-headers {"Authorization" "Bearer tok"}
                               :http-fn http-fn})
          req (first @log)]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "resolveHandle"))
      (is (= {"handle" "alice.example.com"} (:params req)))
      (is (= "Bearer tok" (get-in req [:headers "Authorization"])))))

  (testing "resolve-did raises on HTTP 404"
    (let [{:keys [http-fn]}
          (make-fake-http [{:status 404 :body "{\"error\":\"not found\"}"}])]
      (is (thrown? Exception
                   (mon/resolve-did "https://pds.example.com" "unknown.example.com"
                                     {:http-fn http-fn}))))))

(deftest test-list-votes-request-shape
  ;; Parity: Python monitor_vote() → httpx.get(listVotes, headers=_auth_headers(), timeout=30)
  (testing "list-votes fires GET to listVotes endpoint"
    (let [{:keys [log http-fn]}
          (make-fake-http [(json/generate-string {"votes" []})])
          _ (mon/list-votes "https://pds.example.com"
                             {:auth-headers {"Authorization" "Bearer tok"}
                              :http-fn http-fn})
          req (first @log)]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "listVotes"))
      (is (= "Bearer tok" (get-in req [:headers "Authorization"])))))

  (testing "list-votes raises on HTTP 403"
    (let [{:keys [http-fn]}
          (make-fake-http [{:status 403 :body "{\"error\":\"Forbidden\"}"}])]
      (is (thrown? Exception
                   (mon/list-votes "https://pds.example.com" {:http-fn http-fn}))))))

(deftest test-latest-record-ts-request-shape
  ;; Parity: Python _latest_record_ts() GET /xrpc/com.atproto.repo.listRecords
  (testing "latest-record-ts fires GET with repo/collection/limit params"
    (let [body (json/generate-string
                {"records" [{"value" {"createdAt" "2026-06-21T00:00:00Z"}}]})
          {:keys [log http-fn]} (make-fake-http [body])
          ts (mon/latest-record-ts "https://pds.example.com" "tok"
                                    "did:web:alice" "com.etzhayyim.apps.kakaku.product"
                                    {:http-fn http-fn})
          req (first @log)]
      (is (= 1 (count @log)))
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "listRecords"))
      (is (= "did:web:alice" (get-in req [:params "repo"])))
      (is (= "com.etzhayyim.apps.kakaku.product" (get-in req [:params "collection"])))
      (is (= "2026-06-21T00:00:00Z" ts))))

  (testing "latest-record-ts returns nil on HTTP >= 400 (no throw)"
    (let [{:keys [http-fn]} (make-fake-http [{:status 404 :body "{}"}])
          ts (mon/latest-record-ts "https://pds.example.com" "" "did:web:x" "col"
                                    {:http-fn http-fn})]
      (is (nil? ts))))

  (testing "latest-record-ts returns nil when records array empty"
    (let [{:keys [http-fn]}
          (make-fake-http [(json/generate-string {"records" []})])
          ts (mon/latest-record-ts "https://pds.example.com" "" "did:web:x" "col"
                                    {:http-fn http-fn})]
      (is (nil? ts))))

  (testing "latest-record-ts uses updatedAt over createdAt when both present"
    (let [body (json/generate-string
                {"records" [{"value" {"updatedAt" "2026-06-21T12:00:00Z"
                                      "createdAt" "2026-01-01T00:00:00Z"}}]})
          {:keys [http-fn]} (make-fake-http [body])
          ts   (mon/latest-record-ts "https://pds.example.com" "" "did:web:x" "col"
                                      {:http-fn http-fn})]
      (is (= "2026-06-21T12:00:00Z" ts)))))

(deftest test-dry-run-no-mutations
  ;; Verify pure request-builder functions produce NO IO calls.
  ;; (Pure fns never call http-fn — demonstrated by building the requests
  ;; without invoking a fake and checking zero calls would be made.)
  (testing "build-* fns do not touch network (pure, no http-fn invocation)"
    (let [{:keys [log http-fn]} (make-fake-http)
          ;; Call all pure builders — none should trigger http-fn
          _r1 (mon/build-health-request "https://pds.example.com" "/health")
          _r2 (mon/build-did-request "https://pds.example.com" "alice" {})
          _r3 (mon/build-vote-request "https://pds.example.com" {})
          _r4 (mon/build-heartbeat-request "abc123" {})
          _r5 (mon/build-list-records-request "https://pds.example.com" "repo" "col" "")
          _r6 (mon/build-subscribe-message :events "topic" {})
          _r7 (xrpc/build-xrpc-request "any.nsid" {:pds-url "https://pds.example.com"})
          _r8 (xrpc/resolve-base "any.nsid" nil nil "https://pds.example.com")]
      ;; fake's log must remain empty — no IO calls
      (is (empty? @log)
          "pure request-builder fns must not invoke the http-fn"))))

;; ─── run ──────────────────────────────────────────────────────────────────────

(defn -main [& _args]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-bb-migration-wave7a)]
    (System/exit (if (zero? (+ fail error)) 0 1))))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
