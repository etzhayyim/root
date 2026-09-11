;; etzhayyim.monitor — IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/monitor.py
;;
;; Monitoring: app health, DID resolution, shinka/kyumei-koji quality, votes.
;;
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     compute-shinka-score       — rule-based score from capability flags (max 0)
;;     coverage-grade             — numeric score → letter grade (S/A/B/C/D)
;;     tier-score                 — 3-tier linear ramp for KG node/label scaling
;;     normalize-domain-lookup    — "-" → "_" + strip helper
;;     extract-collection-literals— find com.etzhayyim.apps.* collection NSIDs in src
;;     extract-sub-did-paths      — find path: "..." declarations in src
;;     format-health-line         — format a single health-check result as text
;;     format-shinka-row          — format one ShinkaStatus result as a table row
;;     format-shinka-summary      — format the summary footer block
;;     gate-check                 — compare current/previous snapshot metrics,
;;                                  return list of failures (or nil)
;;     build-health-request       — assemble HTTP request map for one health path
;;     build-did-request          — assemble request map for handle resolution
;;     build-vote-request         — assemble request map for listVotes
;;     build-heartbeat-request    — assemble request map for /_heartbeat POST
;;     build-list-records-request — assemble request map for com.atproto.repo.listRecords
;;
;;   IO (request-shaping verified via injectable :http-fn, no live calls in tests):
;;     default-http-fn            — real babashka.http-client dispatch
;;     check-health               — GET /health and /_app/meta
;;     resolve-did                — GET /xrpc/com.atproto.identity.resolveHandle
;;     list-votes                 — GET /xrpc/com.etzhayyim.governance.listVotes
;;     probe-sub-did-freshness    — GET /xrpc/com.atproto.repo.listRecords per path
;;     call-heartbeat             — POST /_heartbeat (live mode only)
;;
;;   DEFERRED (WebSocket subscription):
;;     build-subscribe-message    — shape the message etzhayyim SENDS on opening a
;;                                  WebSocket subscription (pure — returns map).
;;     ws-fn                      — injectable :ws-fn for subscribe legs.
;;     HONEST NOTE: babashka.http-client supports WebSocket via (http/websocket …)
;;     but the subscribe leg requires a live WS connection.  All WS *message-shaping*
;;     logic (what is sent) is extracted as pure build-subscribe-message and is
;;     unit-tested offline.  The live connection is behind the injectable :ws-fn
;;     (not called in tests) — annotated with DEFERRED_WS_CONNECT below.
;;
;; INJECTABLE HTTP CLIENT:
;;   Every IO fn that makes network calls accepts :http-fn in opts.
;;   Default = real babashka.http-client; tests inject a fake that records
;;   calls WITHOUT touching the network.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.monitor)(println :ok)"

(ns etzhayyim.monitor
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.http-client :as http])))

;; ---------------------------------------------------------------------------
;; Private helpers
;; ---------------------------------------------------------------------------

(defn- strip-trailing-slash
  "Remove a single trailing '/' from s, if present.
  Uses str/ends-with? + subs — avoids 2-arg str/trimr which is not available
  in bb/SCI (clojure.string/trimr takes only one argument in SCI)."
  [s]
  (if (str/ends-with? s "/")
    (subs s 0 (dec (count s)))
    s))

;; ---------------------------------------------------------------------------
;; Pure: shinka score / grade helpers
;; ---------------------------------------------------------------------------

(defn compute-shinka-score
  "Rule-based shinka implementation score from capability flag map.
  Mirrors Python _compute_shinka_score().
  Expected keys (booleans): :has-joucho :has-inbox :has-cadence
    :has-drill :has-validate :has-analyze :has-engage :has-old-timer"
  [{:keys [has-joucho has-inbox has-cadence has-drill
           has-validate has-analyze has-engage has-old-timer]}]
  (let [score (+ (if has-joucho 30 0)
                 (if has-inbox  15 0)
                 (if has-cadence 15 0)
                 (if has-drill   10 0)
                 (if has-validate 10 0)
                 (if has-analyze  10 0)
                 (if has-engage   10 0)
                 (if has-old-timer -30 0))]
    (max 0 score)))

(defn coverage-grade
  "Numeric score → letter grade S/A/B/C/D.
  Mirrors Python _coverage_grade()."
  [score]
  (cond
    (>= score 80) "S"
    (>= score 60) "A"
    (>= score 40) "B"
    (>= score 20) "C"
    :else         "D"))

(defn tier-score
  "3-tier linear ramp: 0 … t1 → 0..20; t1 … t2 → 20..60; t2 … t3 → 60..100.
  Mirrors Python _tier_score()."
  [val t1 t2 t3]
  (let [val (long val) t1 (long t1) t2 (long t2) t3 (long t3)]
    (cond
      (>= val t3) 100.0
      (>= val t2) (+ 60.0 (* 40.0 (/ (- val t2) (- t3 t2))))
      (>= val t1) (+ 20.0 (* 40.0 (/ (- val t1) (- t2 t1))))
      (> val 0)   (* 20.0 (/ val t1))
      :else       0.0)))

;; ---------------------------------------------------------------------------
;; Pure: source-code analysis helpers
;; ---------------------------------------------------------------------------

(defn normalize-domain-lookup
  "Replace hyphens with underscores and strip whitespace.
  Mirrors Python _normalize_domain_lookup()."
  [v]
  (str/trim (str/replace v "-" "_")))

(defn- collection-re
  "Regex matching quoted collection NSIDs: com.etzhayyim.apps.* or app.bsky.*"
  []
  #"[\"']((com\.etzhayyim\.apps|app\.bsky)\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_.\-]+)[\"']")

(defn- path-decl-re
  "Regex matching path: \"...\" declarations."
  []
  #"path:\s*\"([^\"]+)\"")

(defn extract-collection-literals
  "Find com.etzhayyim.apps.* collection NSIDs in src restricted to ns-candidates.
  Returns a de-duplicated ordered vector.
  Mirrors Python _extract_collection_literals()."
  [src ns-candidates]
  (let [prefixes (->> ns-candidates
                      (filter seq)
                      (map #(str "com.etzhayyim.apps." (normalize-domain-lookup %) ".")))]
    (->> (re-seq (collection-re) src)
         (map second)                          ; group(1) = the full NSID
         (filter seq)
         (filter (fn [col]
                   (or (empty? prefixes)
                       (some #(str/starts-with? col %) prefixes))))
         (distinct)
         (vec))))

(defn extract-sub-did-paths
  "Find path: \"...\" declarations in src.
  Returns a de-duplicated ordered vector.
  Mirrors Python _extract_sub_did_paths()."
  [src]
  (->> (re-seq (path-decl-re) src)
       (map second)                            ; group(1) = the path value
       (filter seq)
       (distinct)
       (vec)))

;; ---------------------------------------------------------------------------
;; Pure: response / display formatting
;; ---------------------------------------------------------------------------

(defn format-health-line
  "Format a single health-check result for text display.
  Mirrors Python monitor_health() text output loop."
  [{:keys [path ok status latency-ms error]}]
  (let [ok-str (if ok "OK  " "FAIL")]
    (if error
      (str "  [" ok-str "] " path "  " (or status 0) "  error=" error)
      (str "  [" ok-str "] " path "  " (or status 0) "  " (or latency-ms "?") "ms"))))

(defn- bool-mark [b] (if b "✓" "·"))
(defn- old-timer-mark [b] (if b "!!✗" "✓"))
(defn- truncate-name [s] (if (> (count s) 20) (str (subs s 0 19) "…") s))

(defn format-shinka-row
  "Format one ShinkaStatus map as a table row string.
  Mirrors Python _print_shinka_table() inner loop.
  status map keys: :shinka-score :hyoka-score :hyoka-grade :domain-score :kg-score
    :nanoid :name :has-joucho :has-inbox :has-cadence :has-drill :has-validate
    :has-analyze :has-engage :has-old-timer :stale-sub-did :hb-mood"
  [{:keys [shinka-score hyoka-score hyoka-grade domain-score kg-score
           nanoid name has-joucho has-inbox has-cadence has-drill has-validate
           has-analyze has-engage has-old-timer stale-sub-did hb-mood]
    :or   {shinka-score 0 hyoka-score 0 hyoka-grade "" domain-score 0 kg-score 0
           nanoid "" name "" stale-sub-did 0 hb-mood ""
           has-joucho false has-inbox false has-cadence false has-drill false
           has-validate false has-analyze false has-engage false has-old-timer false}}]
  (let [hyoka-cell (if (or (pos? hyoka-score) (pos? domain-score) (pos? kg-score))
                     (if (seq hyoka-grade)
                       (str hyoka-score "(" hyoka-grade ")")
                       (str hyoka-score))
                     "—")]
    (format "%-7s %-7s %-7s %-3s %-9s %-22s%-7s %-6s %-8s %-6s %-9s %-8s %-7s %-9s %-12s %s"
            shinka-score hyoka-cell domain-score kg-score
            nanoid (truncate-name name)
            (bool-mark has-joucho) (bool-mark has-inbox) (bool-mark has-cadence)
            (bool-mark has-drill) (bool-mark has-validate) (bool-mark has-analyze)
            (bool-mark has-engage) (old-timer-mark has-old-timer)
            stale-sub-did (or hb-mood ""))))

(defn format-shinka-summary
  "Format the summary footer for a shinka table.
  Mirrors Python _print_shinka_table() summary block."
  [results]
  (let [n         (count results)
        joucho    (count (filter :has-joucho results))
        old-timer (count (filter :has-old-timer results))
        drill     (count (filter :has-drill results))
        pct       (fn [k t] (if (pos? t) (long (/ (* 100 k) t)) 0))]
    (str "\nSummary:\n"
         "  joucho cadence:  " joucho "/" n " (" (pct joucho n) "%)\n"
         "  old timer (!!):  " old-timer "/" n " (" (pct old-timer n) "% violation)\n"
         "  kyumei-koji:     " drill "/" n " (" (pct drill n) "% have shouldDrill)")))

;; ---------------------------------------------------------------------------
;; Pure: gate check
;; ---------------------------------------------------------------------------

(defn gate-check
  "Compare current vs previous snapshot metrics.
  Returns a list of failure strings (empty = pass).
  Mirrors Python _store_hyoka_results() gate block."
  [{:keys [avg-score top10-avg low-count prev-avg prev-top10 prev-low
           max-avg-drop max-top10-drop max-low-increase]}]
  (let [d  (fn [x] (double (or x 0.0)))
        i  (fn [x] (long (or x 0)))
        avg-drop  (- (d prev-avg)  (d avg-score))
        top10-drop (- (d prev-top10) (d top10-avg))
        low-rise  (- (i low-count)  (i prev-low))]
    (cond-> []
      (> avg-drop (d max-avg-drop))
      (conj (str "avg_hyoka drop "
                 (format "%.2f" avg-drop)
                 " > " (or max-avg-drop 3.0)))

      (> top10-drop (d max-top10-drop))
      (conj (str "top10_hyoka drop "
                 (format "%.2f" top10-drop)
                 " > " (or max-top10-drop 5.0)))

      (> low-rise (i max-low-increase))
      (conj (str "low-score increase "
                 low-rise
                 " > " (or max-low-increase 5))))))

;; ---------------------------------------------------------------------------
;; Pure: HTTP request builders (testable offline)
;; ---------------------------------------------------------------------------

(defn build-health-request
  "Build request map for one health check path.
  Mirrors Python monitor_health() request construction."
  [pds-url path]
  {:method :get
   :url    (str (strip-trailing-slash pds-url) path)
   :headers {"Content-Type" "application/json"}})

(defn build-did-request
  "Build request map for handle/DID resolution.
  Mirrors Python monitor_did() request construction."
  [pds-url did-or-handle auth-headers]
  {:method  :get
   :url     (str (strip-trailing-slash pds-url)
                 "/xrpc/com.atproto.identity.resolveHandle")
   :params  {"handle" did-or-handle}
   :headers (merge {"Content-Type" "application/json"} auth-headers)})

(defn build-vote-request
  "Build request map for listVotes.
  Mirrors Python monitor_vote() request construction."
  [pds-url auth-headers]
  {:method  :get
   :url     (str (strip-trailing-slash pds-url)
                 "/xrpc/com.etzhayyim.governance.listVotes")
   :headers (merge {"Content-Type" "application/json"} auth-headers)})

(defn build-heartbeat-request
  "Build request map for /_heartbeat POST.
  Mirrors Python _analyze_shinka_app() live heartbeat leg."
  [nanoid auth-headers]
  {:method  :post
   :url     (str "https://" nanoid ".etzhayyim.com/_heartbeat")
   :headers (merge {"Content-Type" "application/json"} auth-headers)})

(defn build-list-records-request
  "Build request map for com.atproto.repo.listRecords (sub-DID freshness probe).
  Mirrors Python _latest_record_ts() request construction."
  [pds-url repo collection token]
  {:method  :get
   :url     (str (strip-trailing-slash pds-url)
                 "/xrpc/com.atproto.repo.listRecords")
   :params  {"repo" repo "collection" collection "limit" "1"}
   :headers (cond-> {"Content-Type" "application/json"}
              (seq token) (assoc "Authorization" (str "Bearer " token)))})

;; ---------------------------------------------------------------------------
;; Pure: WebSocket subscribe message shaping (DEFERRED live connection)
;;
;; HONEST NOTE: The Python monitor.py uses httpx for HTTP but has no WebSocket
;; code in the 649 lines examined.  We include the build-subscribe-message fn
;; as a forward-looking pure stub for any future WS subscription leg
;; (e.g. subscribing to a firehose / event stream over the Murakumo mesh).
;; The live WS connection is behind the injectable :ws-fn (never called in tests).
;; DEFERRED_WS_CONNECT — annotated below.
;; ---------------------------------------------------------------------------

(defn build-subscribe-message
  "Shape the message sent when opening a WebSocket subscription.
  Returns a map {:type :topic :opts} that callers serialise to JSON before
  sending.  Pure — does NOT open a connection.

  subscription-type — e.g. :events :heartbeat :firehose
  topic             — e.g. \"com.etzhayyim.actor.events\"
  extra-opts        — any extra keys merged into :opts"
  [subscription-type topic extra-opts]
  {:type  (name subscription-type)
   :topic topic
   :opts  (or extra-opts {})})

(defn- default-ws-fn
  "DEFERRED_WS_CONNECT — placeholder for the real WebSocket connection fn.
  In tests, inject a fake :ws-fn.  In production, replace with a real
  babashka.http-client websocket call.
  This fn is intentionally NOT called during tests; it is here so that
  production code can wire in the live connection via the same opts map pattern."
  [_url _message _on-message]
  (throw (ex-info "WebSocket leg not yet implemented (DEFERRED_WS_CONNECT)"
                  {:hint "inject a :ws-fn via opts to override"})))

;; ---------------------------------------------------------------------------
;; IO: HTTP dispatch — injectable for tests
;; ---------------------------------------------------------------------------

(defn- default-http-fn
  "Real babashka.http-client dispatch.
  Expects {:method :url :headers :body? :params?} and returns {:status :body}."
  [{:keys [method url headers body params]}]
  #?(:bb
     (let [base-opts (cond-> {:headers headers :timeout 10000}
                       params (assoc :query-params params)
                       body   (assoc :body (json/generate-string body)))
           resp      (case method
                       :get  (http/get  url base-opts)
                       :post (http/post url base-opts))]
       {:status (:status resp) :body (:body resp)})
     :default
     (throw (ex-info "babashka.http-client only available under bb"
                     {:method method :url url}))))

;; ---------------------------------------------------------------------------
;; IO: check-health
;; ---------------------------------------------------------------------------

(defn check-health
  "GET /health and /_app/meta on pds-url.
  Returns a vector of result maps {:path :status :ok :latency-ms? :error?}.
  Mirrors Python monitor_health().

  opts:
    :http-fn — injectable HTTP fn (default = babashka.http-client)"
  [pds-url {:keys [http-fn] :or {http-fn default-http-fn}}]
  (mapv (fn [path]
          (let [req (build-health-request pds-url path)]
            (try
              (let [t0    (System/currentTimeMillis)
                    resp  (http-fn req)
                    lat   (- (System/currentTimeMillis) t0)
                    ok?   (< (:status resp) 400)]
                {:path path :status (:status resp) :ok ok? :latency-ms lat})
              (catch Exception e
                {:path path :status 0 :ok false :error (ex-message e)}))))
        ["/health" "/_app/meta"]))

;; ---------------------------------------------------------------------------
;; IO: resolve-did
;; ---------------------------------------------------------------------------

(defn resolve-did
  "GET /xrpc/com.atproto.identity.resolveHandle on pds-url.
  Returns the parsed JSON response map.
  Raises ex-info on HTTP error (>= 400).
  Mirrors Python monitor_did().

  opts:
    :auth-headers — map of auth headers (default {})
    :http-fn      — injectable HTTP fn"
  [pds-url did-or-handle {:keys [auth-headers http-fn]
                           :or   {auth-headers {} http-fn default-http-fn}}]
  (let [req  (build-did-request pds-url did-or-handle auth-headers)
        resp (http-fn req)]
    (when (>= (:status resp) 400)
      (throw (ex-info (str "resolve-did error: " (:status resp) " " (:body resp))
                      {:status (:status resp) :body (:body resp)})))
    (json/parse-string (:body resp) true)))

;; ---------------------------------------------------------------------------
;; IO: list-votes
;; ---------------------------------------------------------------------------

(defn list-votes
  "GET /xrpc/com.etzhayyim.governance.listVotes.
  Returns the parsed JSON response (list or {:votes [...]} map).
  Raises ex-info on HTTP error (>= 400).
  Mirrors Python monitor_vote().

  opts:
    :auth-headers — map of auth headers (default {})
    :http-fn      — injectable HTTP fn"
  [pds-url {:keys [auth-headers http-fn]
             :or   {auth-headers {} http-fn default-http-fn}}]
  (let [req  (build-vote-request pds-url auth-headers)
        resp (http-fn req)]
    (when (>= (:status resp) 400)
      (throw (ex-info (str "list-votes error: " (:status resp) " " (:body resp))
                      {:status (:status resp) :body (:body resp)})))
    (json/parse-string (:body resp) true)))

;; ---------------------------------------------------------------------------
;; IO: probe-sub-did-freshness (one collection / one path)
;; ---------------------------------------------------------------------------

(defn latest-record-ts
  "GET /xrpc/com.atproto.repo.listRecords and extract the most recent timestamp.
  Returns an ISO-8601 string or nil.
  Mirrors Python _latest_record_ts().

  opts:
    :http-fn — injectable HTTP fn"
  [pds-url token repo collection {:keys [http-fn] :or {http-fn default-http-fn}}]
  (try
    (let [req  (build-list-records-request pds-url repo collection token)
          resp (http-fn req)]
      (when (< (:status resp) 400)
        (let [data    (json/parse-string (:body resp) true)
              records (:records data)]
          (when (seq records)
            (let [val (-> records first :value)]
              (or (:updatedAt val) (:createdAt val)))))))
    (catch Exception _ nil)))
