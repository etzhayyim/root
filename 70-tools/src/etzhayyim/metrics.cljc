;; etzhayyim.metrics — BI metrics stub (cljc port, wave 3a).
;;
;; Port of 70-tools/etzhayyim-py/src/etzhayyim/metrics.py
;;
;; metrics.py is almost entirely IO (httpx + auth):
;;   - Every CLI command fires an httpx GET to a PDS XRPC endpoint.
;;   - _auth_headers() calls _load_auth() (reads ~/.config/etzhayyim/auth.json)
;;     and resolve_pds() (calls projector, which may hit a network endpoint).
;;   - There is NO extractable pure math or data-transform logic.
;;
;; Pure-logic ported (minimal but real):
;;   valid-windows     — set of accepted time-window strings
;;   window-valid?     — predicate for time-window parameter validation
;;   metrics-nsid      — build the XRPC NSID for a given metric type
;;   parse-latency     — extract p50/p95/p99 from a raw API response map
;;   parse-throughput  — extract rps/rpm/total from a raw API response map
;;   parse-errors      — extract error-rate/top-errors from a raw API response map
;;   format-summary    — format a metrics summary map as a seq of "key: value" strings
;;
;; IO legs deferred (NOT ported — all are httpx/auth):
;;   _auth_headers     — reads auth file + calls resolve_pds → babashka.fs + http-client
;;   metrics (group)   — GET getSummary XRPC → babashka.http-client
;;   metrics latency   — GET getLatency XRPC → babashka.http-client
;;   metrics throughput— GET getThroughput XRPC → babashka.http-client
;;   metrics errors    — GET getErrorRate XRPC → babashka.http-client
;;
;; NOTE: metrics.py has no significant pure logic.  This namespace documents the
;; IO boundary faithfully and provides the small helpers above so bb tasks that
;; later wrap the XRPC calls can share validation + parsing without re-implementing
;; them.  The IO legs will be added in wave 4 via babashka.http-client.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.metrics :as m])
;;   (m/window-valid? "1h")    ;=> true
;;   (m/metrics-nsid :latency) ;=> "com.etzhayyim.metrics.getLatency"
;;   (m/parse-latency {"p50" 12 "p95" 45 "p99" 120})
;;   ;=> {:p50 12 :p95 45 :p99 120}

(ns etzhayyim.metrics
  (:require [clojure.string :as str]))

;; ── time-window validation ────────────────────────────────────────────────────────

(def valid-windows
  "Accepted time-window parameter strings."
  #{"1h" "24h" "7d" "30d"})

(defn window-valid?
  "Returns true if window is a recognised time-window string."
  [window]
  (boolean (valid-windows (str/trim (or window "")))))

;; ── XRPC NSID builder ────────────────────────────────────────────────────────────

(def ^:private nsid-map
  {:summary    "com.etzhayyim.metrics.getSummary"
   :latency    "com.etzhayyim.metrics.getLatency"
   :throughput "com.etzhayyim.metrics.getThroughput"
   :errors     "com.etzhayyim.metrics.getErrorRate"})

(defn metrics-nsid
  "Return the XRPC NSID for a given metric type keyword.
   metric-type ∈ #{:summary :latency :throughput :errors}
   Returns nil for unknown types."
  [metric-type]
  (get nsid-map metric-type))

(defn metrics-url
  "Build the full XRPC URL for a given pds-base and metric type.
   pds-base = URL string (trailing slash stripped)."
  [pds-base metric-type]
  (let [nsid (metrics-nsid metric-type)]
    (when nsid
      (str (str/replace pds-base #"/+$" "") "/xrpc/" nsid))))

;; ── response parsers ──────────────────────────────────────────────────────────────

(defn parse-latency
  "Extract p50/p95/p99 from a raw latency API response map.
   Returns a map {:p50 num :p95 num :p99 num} — missing keys default to nil.
   The Python CLI simply iterates k,v pairs; this parser is explicit."
  [data]
  {:p50 (get data "p50")
   :p95 (get data "p95")
   :p99 (get data "p99")})

(defn parse-throughput
  "Extract rps/rpm/total from a raw throughput API response map."
  [data]
  {:rps   (get data "rps")
   :rpm   (get data "rpm")
   :total (get data "total")})

(defn parse-errors
  "Extract error-rate and top-errors from a raw error-rate API response map."
  [data]
  {:error-rate  (get data "errorRate")
   :top-errors  (get data "topErrors" [])
   :total-reqs  (get data "totalRequests")})

;; ── formatting helpers ────────────────────────────────────────────────────────────

(defn format-summary
  "Format a raw metrics summary map as a seq of \"key: value\" strings.
   Mirrors the Python CLI: for k, v in data.items(): echo(f'  {k}: {v}')."
  [data]
  (map (fn [[k v]] (str "  " (name k) ": " v))
       (sort-by key data)))

(defn format-latency
  "Format parsed latency results as a seq of strings.
   window = time-window string for the header line."
  [parsed-latency window]
  (let [{:keys [p50 p95 p99]} parsed-latency]
    (cond-> [(str "latency (" window "):")]
      (some? p50) (conj (str "  p50: " p50 "ms"))
      (some? p95) (conj (str "  p95: " p95 "ms"))
      (some? p99) (conj (str "  p99: " p99 "ms")))))
