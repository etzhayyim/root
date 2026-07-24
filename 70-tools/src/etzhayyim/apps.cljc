;; etzhayyim.apps — App status checker (Clojure/bb port of apps.py).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/apps.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     infer-app-name-from-collections — extract app name from collection NSIDs
;;     coverage-grade                  — letter grade from numeric score (S/A/B/C/D)
;;     tier-score                      — tiered linear-interpolation score (0–100)
;;     score-domain-static-src         — score app domain knowledge from source string
;;     extract-sources-from-src        — extract sourceUrl / caseDbUrl / legislationUrl patterns
;;     kyumei-grade                    — alias for coverage-grade
;;     compute-coverage-scores         — aggregate domain/live/xrpc/did into overall
;;     build-coverage-report           — assemble the full coverage report map
;;
;;   IO (request-shaping verified via injectable HTTP fn, not live calls):
;;     build-list-apps-request         — shape for com.etzhayyim.apps.listApps GET
;;     build-list-records-request      — shape for com.atproto.repo.listRecords GET
;;     build-health-request            — shape for app /health GET
;;     build-meta-request              — shape for app /_app/meta GET
;;     build-xrpc-coverage-request     — shape for app /xrpc/…coverageStats POST
;;     list-pds-records               — IO: paginated record fetch from PDS
;;     check-app-health               — IO: /health + /_app/meta check
;;     xrpc-coverage-stats            — IO: XRPC self-eval call
;;
;; INJECTABLE HTTP CLIENT:
;;   Every IO fn accepts an optional :http-fn.
;;   Default = real babashka.http-client; tests inject a fake.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.apps)(println :ok)"

(ns etzhayyim.apps
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.http-client :as http])))

;; ---------------------------------------------------------------------------
;; Pure: coverage-grade / kyumei-grade
;; ---------------------------------------------------------------------------

(defn coverage-grade
  "Map a numeric score (0–100) to a letter grade.
  Mirrors Python _coverage_grade()."
  [score]
  (cond
    (>= score 80) "S"
    (>= score 60) "A"
    (>= score 40) "B"
    (>= score 20) "C"
    :else         "D"))

(def kyumei-grade
  "Alias for coverage-grade. Mirrors Python _kyumei_grade()."
  coverage-grade)

;; ---------------------------------------------------------------------------
;; Pure: tier-score
;; ---------------------------------------------------------------------------

(defn tier-score
  "Tiered linear-interpolation score.
  n=0 → 0; n≥hi → 100; lo≤n<mid → [20,60); mid≤n<hi → [60,100).
  Mirrors Python _tier_score()."
  [n lo mid hi]
  (cond
    (<= n 0)  0.0
    (>= n hi) 100.0
    (>= n mid) (+ 60.0 (* 40.0 (/ (- n mid) (max (- hi mid) 1))))
    :else      (+ 20.0 (* 40.0 (/ (- n lo) (max (- mid lo) 1))))))

;; ---------------------------------------------------------------------------
;; Pure: infer-app-name-from-collections
;; ---------------------------------------------------------------------------

(defn infer-app-name-from-collections
  "Extract the app name segment from a list of collection NSIDs.
  Looks for com.etzhayyim.apps.<name>.* pattern (split on '.').
  Returns the first match or empty string.
  Mirrors Python _infer_app_name_from_collections()."
  [cols]
  (or (some (fn [col]
              (let [parts (str/split col #"\.")]
                (when (and (>= (count parts) 5)
                           (= (take 3 parts) '("com" "etzhayyim" "apps")))
                  (nth parts 3))))
            cols)
      ""))

;; ---------------------------------------------------------------------------
;; Pure: extract-sources-from-src
;; ---------------------------------------------------------------------------

(defn extract-sources-from-src
  "Extract sourceUrl / caseDbUrl / legislationUrl from a source string.
  Returns up to 20 {:url :format :category} maps.
  Mirrors Python _extract_sources_from_src()."
  [src]
  (let [re   #"(?:sourceUrl|caseDbUrl|legislationUrl)\s*:\s*[\"'](https?://[^\"']+)[\"']"
        urls (map second (re-seq re (str src)))]
    (vec (take 20 (map (fn [url] {:url url :format "http" :category "external"}) urls)))))

;; ---------------------------------------------------------------------------
;; Pure: score-domain-static-src
;; ---------------------------------------------------------------------------

(def ^:private re-sql-label      #"vertex_([a-z0-9_]+)")
(def ^:private re-collection      #"[\"']((?:com\.etzhayyim\.apps|app\.bsky)\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_.\\-]+)[\"']")
(def ^:private re-custom-cmd      #"function cmd([A-Z][a-zA-Z0-9]+)\(\)")
(def ^:private re-template-cmd    #"function cmd_[a-z_]+\(\)")
(def ^:private re-business-rule   #"(?:if|when|require|assert|validate)\s*\([^)]*\)\s*\{")
(def ^:private re-subdid-path     #"path\s*:\s*[\"']([^\"']+)[\"']")
(def ^:private re-source-url      #"(?:sourceUrl|caseDbUrl|legislationUrl)\s*:\s*[\"'](https?://[^\"']+)[\"']")

(defn score-domain-static-src
  "Score an app's domain knowledge from its source string.
  Returns a map with :domain-score :sql-labels :collections :custom-commands
  :template-cmds :business-rules :sub-did-paths :missing :grade.
  Mirrors Python _score_domain_static() pure scoring (without file IO).
  This version accepts the source string directly (IO caller does the file read)."
  [src]
  (let [sql-labels    (vec (distinct (map second (re-seq re-sql-label (str src)))))
        collections   (vec (distinct (map second (re-seq re-collection (str src)))))
        custom-cmds   (vec (distinct (map (fn [[_ name]] (str "function cmd" name)) (re-seq re-custom-cmd (str src)))))
        template-cmds (count (re-seq re-template-cmd (str src)))
        biz-rules     (count (re-seq re-business-rule (str src)))
        sub-paths     (vec (distinct (map second (re-seq re-subdid-path (str src)))))
        lines         (count (str/split-lines (str src)))
        ;; scoring
        sql-score   (min (* (count sql-labels) 10) 30)
        col-score   (min (* (count collections) 10) 20)
        cmd-score   (min (* (count custom-cmds) 5) 15)
        rule-score  (min biz-rules 15)
        line-score  (min (quot lines 100) 10)
        path-score  (min (* (count sub-paths) 3) 5)
        raw         (+ sql-score col-score cmd-score rule-score line-score path-score)
        ;; penalty: no custom commands AND no sql labels AND no collection kinds
        penalty     (if (and (zero? (count custom-cmds))
                             (zero? (count sql-labels))
                             (zero? (count collections)))
                      20 0)
        score       (max 0 (min (- raw penalty) 100))
        ;; missing axes
        missing     (cond-> []
                      (zero? sql-score)  (conj "graph_labels")
                      (zero? col-score)  (conj "collection_kinds")
                      (zero? cmd-score)  (conj "custom_commands")
                      (zero? rule-score) (conj "business_rules")
                      (zero? path-score) (conj "sub_did_paths"))]
    {:domain-score    score
     :sql-labels      sql-labels
     :collections     collections
     :custom-commands custom-cmds
     :template-cmds   template-cmds
     :business-rules  biz-rules
     :sub-did-paths   sub-paths
     :missing         missing
     :grade           (coverage-grade score)}))

;; ---------------------------------------------------------------------------
;; Pure: compute-coverage-scores
;; ---------------------------------------------------------------------------

(defn compute-coverage-scores
  "Compute overall coverage score from individual dimension scores.
  domain-score: 0-100; live-records: count; xrpc-pct: 0-100; live-dids: count.
  Returns {:overall :overall-grade}.
  Mirrors Python apps_coverage() scoring formula."
  [domain-score live-records xrpc-pct live-dids]
  (let [live-pct  (tier-score live-records 1 10 100)
        did-pct   (tier-score live-dids 1 3 10)
        overall   (* 0.40 domain-score)
        overall   (+ overall (* 0.25 live-pct))
        overall   (+ overall (* 0.20 xrpc-pct))
        overall   (+ overall (* 0.15 did-pct))]
    {:overall       (double overall)
     :overall-grade (coverage-grade overall)}))

;; ---------------------------------------------------------------------------
;; IO: default-http-fn
;; ---------------------------------------------------------------------------

(defn- default-http-fn
  "Real babashka.http-client dispatch."
  [{:keys [method url headers body]}]
  #?(:bb
     (let [opts (cond-> {:headers (or headers {}) :timeout 30000}
                  body (assoc :body (json/generate-string body)))
           resp (case method
                  :get  (http/get  url opts)
                  :post (http/post url opts))]
       {:status (:status resp) :body (:body resp)})
     :default
     (throw (ex-info "babashka.http-client only available under bb"
                     {:method method :url url}))))

;; ---------------------------------------------------------------------------
;; IO request-shaping: all return {:method :url :headers :body?}
;; ---------------------------------------------------------------------------

(defn build-list-apps-request
  "Build the HTTP request map for com.etzhayyim.apps.listApps GET.
  Mirrors Python apps() handler."
  [pds-url token]
  {:method  :get
   :url     (str pds-url "/xrpc/com.etzhayyim.apps.listApps")
   :headers (cond-> {}
              (seq token) (assoc "Authorization" (str "Bearer " token)))})

(defn build-list-records-request
  "Build the HTTP request map for com.atproto.repo.listRecords GET.
  Mirrors Python _list_pds_records()."
  [pds-url repo-did collection limit token]
  {:method  :get
   :url     (str pds-url "/xrpc/com.atproto.repo.listRecords")
   :headers (cond-> {}
              (seq token) (assoc "Authorization" (str "Bearer " token)))
   :params  {"repo"       repo-did
             "collection" collection
             "limit"      (str limit)}})

(defn build-health-request
  "Build the HTTP request map for app /health GET.
  Mirrors Python _check_app_health()."
  [base-url]
  {:method  :get
   :url     (str base-url "/health")
   :headers {}})

(defn build-meta-request
  "Build the HTTP request map for app /_app/meta GET.
  Mirrors Python _check_app_health()."
  [base-url]
  {:method  :get
   :url     (str base-url "/_app/meta")
   :headers {}})

(defn build-xrpc-coverage-request
  "Build the HTTP request map for app /xrpc/…coverageStats POST.
  Mirrors Python _xrpc_coverage_stats()."
  [nanoid app-name token]
  (let [url (str "https://" nanoid ".etzhayyim.com/xrpc/com.etzhayyim.apps."
                 (if (seq app-name) app-name nanoid) ".coverageStats")]
    {:method  :post
     :url     url
     :headers (cond-> {"Content-Type" "application/json"}
                (seq token) (assoc "Authorization" (str "Bearer " token)))
     :body    {}}))

;; ---------------------------------------------------------------------------
;; IO: list-pds-records
;; ---------------------------------------------------------------------------

(defn list-pds-records
  "Fetch records from PDS via com.atproto.repo.listRecords.
  Returns vector of record maps (up to limit).
  Mirrors Python _list_pds_records()."
  [pds-url repo-did collection limit {:keys [token http-fn]
                                       :or   {http-fn default-http-fn}}]
  (let [req (-> (build-list-records-request pds-url repo-did collection limit token)
                ;; merge params into URL for HTTP GET
                (dissoc :params)
                (assoc :url (str pds-url "/xrpc/com.atproto.repo.listRecords"
                                 "?repo=" (java.net.URLEncoder/encode (str repo-did) "UTF-8")
                                 "&collection=" (java.net.URLEncoder/encode (str collection) "UTF-8")
                                 "&limit=" limit)))
        resp (http-fn req)]
    (if (>= (:status resp) 400)
      []
      (let [data (json/parse-string (:body resp) true)]
        (if (map? data)
          (vec (get data :records []))
          [])))))

;; ---------------------------------------------------------------------------
;; IO: check-app-health
;; ---------------------------------------------------------------------------

(defn check-app-health
  "Check /health and /_app/meta for a given base-url.
  Returns {:nanoid :name :health-ok :health-code :latency-ms :meta-ok :error}.
  Mirrors Python _check_app_health()."
  [nanoid name base-url {:keys [http-fn]
                          :or   {http-fn default-http-fn}}]
  (let [health-req (build-health-request base-url)]
    (try
      (let [t0         (System/currentTimeMillis)
            resp       (http-fn health-req)
            latency-ms (- (System/currentTimeMillis) t0)
            health-ok  (< (:status resp) 400)
            meta-req   (build-meta-request base-url)
            meta-ok    (try
                         (let [mr (http-fn meta-req)]
                           (< (:status mr) 400))
                         (catch Exception _ false))]
        {:nanoid     nanoid
         :name       name
         :health-ok  health-ok
         :health-code (:status resp)
         :latency-ms (long latency-ms)
         :meta-ok    meta-ok
         :error      ""})
      (catch Exception e
        {:nanoid     nanoid
         :name       name
         :health-ok  false
         :health-code 0
         :latency-ms 0
         :meta-ok    false
         :error      (str (ex-message e))}))))

;; ---------------------------------------------------------------------------
;; IO: xrpc-coverage-stats
;; ---------------------------------------------------------------------------

(defn xrpc-coverage-stats
  "Call the app's XRPC coverageStats endpoint.
  Returns the parsed response map or nil on failure.
  Mirrors Python _xrpc_coverage_stats()."
  [nanoid app-name {:keys [token http-fn]
                    :or   {http-fn default-http-fn}}]
  (let [eff-app-name (if (seq app-name) app-name nanoid)
        req (build-xrpc-coverage-request nanoid eff-app-name token)]
    (try
      (let [resp (http-fn req)]
        (when (= (:status resp) 200)
          (json/parse-string (:body resp) true)))
      (catch Exception _ nil))))

;; ---------------------------------------------------------------------------
;; CLI -main — mirrors the python `apps` click group argv contract:
;;   e7m apps [--json]                         (group: XRPC listApps — network)
;;   e7m apps list [--workspace-dir D] [--json]
;;   e7m apps health --url URL [--nanoid N] [--json]
;;   e7m apps coverage <nanoid> [--pds URL] [--json]
;;   e7m apps kyumei-koji <nanoid> [--fast] [--json]
;; list/coverage/kyumei run the PURE scoring legs for real over local files
;; (no network). The live PDS/XRPC legs (list-pds-records / xrpc-coverage-stats)
;; are read-only IO and are not exercised here (treated as live=0).
;; ---------------------------------------------------------------------------

(defn- apps-parse
  [args bool-flags]
  (loop [a (seq args) pos [] flags {}]
    (if-not a
      [pos flags]
      (let [t (first a)]
        (cond
          (and (str/starts-with? t "--") (contains? bool-flags (subs t 2)))
          (recur (next a) pos (assoc flags (subs t 2) true))
          (str/starts-with? t "--")
          (recur (nnext a) pos (assoc flags (subs t 2) (fnext a)))
          :else
          (recur (next a) (conj pos t) flags))))))

(defn- kotodama-files
  "Seq of kotodama.jsonld java.io.File under root."
  [root]
  (filter #(= "kotodama.jsonld" (.getName ^java.io.File %))
          (file-seq (java.io.File. (str root)))))

(defn- read-jsonld [^java.io.File f]
  (try (json/parse-string (slurp f) true) (catch Exception _ nil)))

(defn- find-app-dir
  "Find the dir of the app whose kotodama.jsonld :nanoid matches, under root/60-apps."
  [root nanoid]
  (some (fn [f] (let [d (read-jsonld f)]
                  (when (= (get d :nanoid) nanoid)
                    {:name (get d :name nanoid)
                     :did  (get d :did (str "did:web:" nanoid ".etzhayyim.com"))
                     :dir  (.getParent ^java.io.File f)})))
        (kotodama-files (str root "/60-apps"))))

(defn- read-app-src
  "Read the first existing app.ts-style source under dir, or \"\" if none."
  [dir]
  (or (some (fn [c] (let [f (java.io.File. (str dir "/" c))]
                      (when (.exists f) (try (slurp f) (catch Exception _ nil)))))
            ["src/app.ts" "app.ts" "src/index.ts"])
      ""))

(defn -main [& args]
  (let [[pos flags] (apps-parse args #{"json" "fast"})
        sub   (first pos)
        json? (boolean (get flags "json"))
        root  (or (get flags "workspace-dir") ".")]
    (case sub
      "list"
      (let [apps (->> (kotodama-files (str root "/60-apps"))
                      (keep read-jsonld)
                      (filter #(seq (str (get % :nanoid ""))))
                      (mapv (fn [d] {:nanoid (get d :nanoid "")
                                     :name   (get d :name "")
                                     :performerType (get d :performerType "")})))]
        (if json?
          (println (json/generate-string apps {:pretty true}))
          (do (println (str "apps: " (count apps)))
              (doseq [a apps]
                (println (str "  " (:nanoid a) "  " (:name a) "  [" (:performerType a) "]"))))))

      "health"
      (if-let [url (get flags "url")]
        (let [st (check-app-health (or (get flags "nanoid") "") "" url {})]
          (if json?
            (println (json/generate-string st {:pretty true}))
            (println (str "  [" (if (:health-ok st) "OK  " "FAIL") "] " url "  "
                          (:health-code st) "  " (:latency-ms st) "ms"
                          (when (seq (:error st)) (str "  " (:error st)))))))
        (println "usage: apps health --url URL [--nanoid N] [--json]"))

      "coverage"
      (if-let [nanoid (second pos)]
        (let [app   (find-app-dir root nanoid)
              src   (read-app-src (:dir app))
              dom   (score-domain-static-src src)
              scores (compute-coverage-scores (:domain-score dom) 0 0.0 0)
              report {:nanoid nanoid
                      :name   (or (:name app) nanoid)
                      :did    (or (:did app) (str "did:web:" nanoid ".etzhayyim.com"))
                      :domain-score (:domain-score dom)
                      :domain-grade (:grade dom)
                      :collections  (:collections dom)
                      :sql-labels   (:sql-labels dom)
                      :sub-did-paths (:sub-did-paths dom)
                      :live-records 0
                      :overall-score (:overall scores)
                      :overall-grade (:overall-grade scores)
                      :note "static-only (live PDS/XRPC legs not exercised here)"}]
          (if json?
            (println (json/generate-string report {:pretty true}))
            (do (println (str "App Coverage Report: " (:name report) " (" nanoid ")"))
                (println (str "DID: " (:did report)))
                (println (str "Overall:      " (:overall-grade report) "  "
                              (format "%.1f" (:overall-score report)) " / 100"))
                (println (str "Domain Score: " (:domain-grade report) "  " (:domain-score report) " / 100"))
                (println (str "Collections:  " (count (:collections report))))
                (println (str "Live Records: 0 (static-only)")))))
        (println "usage: apps coverage <nanoid> [--pds URL] [--json]"))

      "kyumei-koji"
      (if-let [nanoid (second pos)]
        (let [app     (find-app-dir root nanoid)
              src     (read-app-src (:dir app))
              dom     (score-domain-static-src src)
              sources (extract-sources-from-src src)
              cols    (:collections dom)
              paths   (:sub-did-paths dom)
              readiness (min 100.0
                          (double (+ (min (* (count sources) 10) 25)
                                     (* (tier-score 0 1 10 100) 0.40)
                                     (min (* (count paths) 5) 15)
                                     (min (* (count cols) 5) 20))))
              report {:nanoid nanoid
                      :name (or (:name app) nanoid)
                      :did  (or (:did app) (str "did:web:" nanoid ".etzhayyim.com"))
                      :declared-sources sources
                      :collections cols
                      :sub-did-paths paths
                      :readiness-score readiness
                      :readiness-grade (kyumei-grade readiness)
                      :note "static-only (live PDS legs not exercised here)"}]
          (if json?
            (println (json/generate-string report {:pretty true}))
            (do (println (str "Kyumei-Koji Report: " (:name report) " (" nanoid ")"))
                (println (str "DID: " (:did report)))
                (println (str "Readiness:        " (:readiness-grade report) "  "
                              (format "%.1f" (:readiness-score report)) " / 100"))
                (println (str "Declared Sources: " (count sources)))
                (println (str "Collections:      " (count cols)))
                (println (str "Sub-DID Paths:    " (count paths))))))
        (println "usage: apps kyumei-koji <nanoid> [--fast] [--json]"))

      nil
      (println (str "usage: apps [--json] | apps <list|health|coverage|kyumei-koji> [args] [--opts]\n"
                    "  (bare `apps` lists deployed apps via XRPC com.etzhayyim.apps.listApps — "
                    "needs a live PDS; not run here)"))

      (println "usage: apps <list|health|coverage|kyumei-koji> [args] [--opts]"))))
