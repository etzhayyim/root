;; etzhayyim.test-xrpc — xrpc request-shaping pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure base/url/request/response helpers (HTTP dispatch deferred):
;; resolve-base · build-xrpc-url · build-xrpc-request · parse-xrpc-response-body.
(ns etzhayyim.test-xrpc
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.auth :as auth]
            [etzhayyim.xrpc :as x]))

(deftest resolve-base-priority
  (testing "explicit url wins and trailing slash is stripped"
    (is (= "https://u.example" (x/resolve-base "com.x" nil "https://u.example/" "https://pds"))))
  (testing "explicit app → app host template"
    (is (= "https://myid.com.etzhayyim.com" (x/resolve-base "com.x" "myid" nil "https://pds"))))
  (testing "NSID inference resolves a known apps slug"
    (is (= "https://q7v8yed1k.com.etzhayyim.com"
           (x/resolve-base "com.etzhayyim.apps.autorace.list" nil nil "https://pds"))))
  (testing "unknown slug / non-apps NSID falls back to the PDS url"
    (is (= "https://pds" (x/resolve-base "com.etzhayyim.apps.nosuchslug.x" nil nil "https://pds/")))
    (is (= "https://pds" (x/resolve-base "com.atproto.repo.get" nil nil "https://pds/")))))

(deftest build-xrpc-url-shape
  (is (= "https://base.example/xrpc/com.x" (x/build-xrpc-url "https://base.example" "com.x"))))

(deftest build-xrpc-request-shape
  (testing "GET with no payload → no body, content-type header"
    (let [r (x/build-xrpc-request "com.x" {:url "https://u"})]
      (is (= :get (:method r)))
      (is (= "https://u/xrpc/com.x" (:url r)))
      (is (= "application/json" (get-in r [:headers "Content-Type"])))
      (is (nil? (:body r)))))
  (testing "POST with payload → body + merged auth headers"
    (let [r (x/build-xrpc-request "com.x" {:url "https://u" :payload {"k" 1}
                                           :auth-headers {"Authorization" "Bearer t"}})]
      (is (= :post (:method r)))
      (is (= {"k" 1} (:body r)))
      (is (= "Bearer t" (get-in r [:headers "Authorization"])))))
  (testing "GET with a map payload → :params"
    (let [r (x/build-xrpc-request "com.x" {:url "https://u" :method :get :payload {"q" "1"}})]
      (is (= {"q" "1"} (:params r)))
      (is (nil? (:body r))))))

(deftest parse-xrpc-response-body-formatting
  (testing "pretty-print valid JSON → [pretty true]"
    (let [[s ok?] (x/parse-xrpc-response-body "{\"a\":1}" true)]
      (is (true? ok?))
      (is (re-find #"\"a\"" s))))
  (testing "pretty with invalid JSON → [raw false]"
    (is (= ["not json" false] (x/parse-xrpc-response-body "not json" true))))
  (testing "no pretty → [raw false]"
    (is (= ["raw" false] (x/parse-xrpc-response-body "raw" false)))))

;; ── CLI leg: which PDS gets contacted ────────────────────────────────────────
;;
;; `xrpc` resolves its base from --url > --app > NSID inference > the PDS
;; fallback. Any NSID that is not an App Worker lands on that fallback, and
;; --execute really sends, so the host must always be one somebody chose: the
;; --pds passed here, or the workspace-wide constant `etzhayyim.auth/default-pds`.
;;
;; This CLI had both halves of the problem PR #3235 closed. The fallback was a
;; literal "https://pds.local" — `.local` is the mDNS/Bonjour namespace
;; (RFC 6762), claimable by any host on the same link — and the value ahead of it
;; came from an ambient read of E7M_PDS, so the host could change with nothing on
;; the command line to show it.
;;
;; SEVERITY NOTE — unlike `yoroshiku register`, this CLI transmits no credential:
;; -main passes :auth-headers {} and build-xrpc-request adds only Content-Type.
;; A wrong host here leaks the -d payload and the NSID being called, not a bearer
;; token.
;;
;; These read the dry-run plan (no --execute), so nothing is sent.

(defn- plan-url
  "Resolve the URL `xrpc` would call, by parsing the dry-run plan it prints.
   Plan shape: line 1 is the banner, line 2 is \"<METHOD> <url>\"."
  [& argv]
  (-> (with-out-str (apply x/-main argv))
      (str/split-lines)
      (nth 1)
      (str/split #"\s+")
      (nth 1)))

(deftest xrpc-cli-never-invents-a-pds-host
  (testing "no --pds → the workspace's chosen default PDS, not an invented name"
    (let [url (plan-url "com.atproto.repo.getRecord")]
      (is (= (str auth/default-pds "/xrpc/com.atproto.repo.getRecord") url))
      ;; The specific regression: an mDNS-squattable host reached by default.
      (is (not (str/includes? url "pds.local"))
          "xrpc must not default to a .local (mDNS) host")))

  (testing "an unknown apps slug falls back to the default too"
    (is (= (str auth/default-pds "/xrpc/com.etzhayyim.apps.nosuchslug.list")
           (plan-url "com.etzhayyim.apps.nosuchslug.list"))))

  ;; The ambient half. E7M_PDS was this module's invention — nothing in the repo
  ;; sets or documents it, this was its only reader, and the Python twin
  ;; (xrpc.py) resolves the same base through auth.resolve_pds() with no such
  ;; flag. Reinstating an ambient read is exactly what #3235 removed.
  ;;
  ;; A JVM cannot set its own environment, so this assertion only bites when the
  ;; suite is RUN with the variable set. That is a deliberate part of the check —
  ;; run it as:
  ;;
  ;;   E7M_PDS=https://ambient.invalid bb --classpath 70-tools/src \
  ;;     -m etzhayyim.test-xrpc
  ;;
  ;; With the env read still in place that invocation fails here; without it the
  ;; result is identical either way. Left in the suite so a re-added ambient read
  ;; is caught by anyone who runs it under a set variable.
  (testing "the environment cannot redirect the host"
    (is (= (str auth/default-pds "/xrpc/com.atproto.repo.getRecord")
           (plan-url "com.atproto.repo.getRecord"))
        "resolution must not consult E7M_PDS or any other ambient variable"))

  ;; POSITIVE CONTROLS — pass both before and after the fix. If either fails, the
  ;; breakage is in flag parsing or base resolution, not in the default-host
  ;; change above.
  (testing "explicit --url still overrides everything"
    (is (= "https://u.example/xrpc/com.atproto.repo.getRecord"
           (plan-url "com.atproto.repo.getRecord" "--url" "https://u.example"))))

  (testing "a known apps NSID still routes to its App Worker, not the PDS"
    (is (= "https://q7v8yed1k.com.etzhayyim.com/xrpc/com.etzhayyim.apps.autorace.list"
           (plan-url "com.etzhayyim.apps.autorace.list"))))

  (testing "explicit --pds is honoured"
    (is (= "https://pds.example/xrpc/com.atproto.repo.getRecord"
           (plan-url "com.atproto.repo.getRecord" "--pds" "https://pds.example"))))

  (testing "explicit --pds is trailing-slash normalized"
    (is (= "https://pds.example/xrpc/com.atproto.repo.getRecord"
           (plan-url "com.atproto.repo.getRecord" "--pds" "https://pds.example///"))))

  (testing "blank --pds falls back to the default rather than building a bare path"
    (is (= (str auth/default-pds "/xrpc/com.atproto.repo.getRecord")
           (plan-url "com.atproto.repo.getRecord" "--pds" "  ")))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-xrpc)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
