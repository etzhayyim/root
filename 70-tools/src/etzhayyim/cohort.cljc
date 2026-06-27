;; etzhayyim.cohort — Cohort management (Clojure/bb port of cohort.py).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/cohort.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     build-gen-segment      — construct segment map {pcfL1 role industry seniority locale k}
;;     compute-dashboard      — fission stats from cohort list
;;     build-coverage-matrix  — 2D matrix[rv][cv] from cohorts
;;     find-gaps              — cells below min-count in matrix
;;     compute-snapshot-agg   — group cohorts by axes, count per key
;;     diff-snapshots         — total delta between two snapshot data maps
;;     parse-segment-arg      — @file → JSON string, else raw string parse
;;     render-lineage-tree    — ASCII tree from chain list
;;
;;   IO (request-shaping verified via injectable HTTP fn, not live calls):
;;     build-gen-request      — shape for com.etzhayyim.cohort.gen POST
;;     build-list-request     — shape for com.etzhayyim.cohort.list GET
;;     build-inspect-request  — shape for com.etzhayyim.cohort.getById GET
;;     build-fission-request  — shape for com.etzhayyim.cohort.fission POST
;;     build-lineage-request  — shape for com.etzhayyim.cohort.lineage GET
;;     build-forest-request   — shape for com.etzhayyim.cohort.forest GET
;;     build-snap-request     — shape for com.etzhayyim.cohort.snap POST
;;     build-diff-request     — shape for com.etzhayyim.cohort.diff GET
;;     build-drift-request    — shape for com.etzhayyim.cohort.drift GET
;;
;; INJECTABLE HTTP CLIENT:
;;   Every IO fn that makes network calls accepts :http-fn in opts.
;;   Default = real babashka.http-client; tests inject a fake.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.cohort)(println :ok)"

(ns etzhayyim.cohort
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.http-client :as http])))

;; ---------------------------------------------------------------------------
;; Pure: build-gen-segment
;; ---------------------------------------------------------------------------

(defn build-gen-segment
  "Build a cohort generation segment map.
  Mirrors Python build_segment() in cohort_gen.
  Returns a map with :pcf-l1, :role, :industry, :seniority, :locale, :k."
  [pcf-l1 role industry seniority locale k]
  {:pcf-l1    pcf-l1
   :role       role
   :industry   industry
   :seniority  seniority
   :locale     locale
   :k          k})

;; ---------------------------------------------------------------------------
;; Pure: compute-dashboard
;; ---------------------------------------------------------------------------

(defn compute-dashboard
  "Compute fission dashboard stats from a sequence of cohort maps.
  Each cohort map should have :kind, :pcfL1, :role, :industry, :locale keys.
  Returns {:total :fissioned :base :fission-rate
            :axis-pcf-l1 :axis-role :axis-industry :axis-locale}."
  [cohorts]
  (let [total      (count cohorts)
        fissioned  (count (filter #(= "fissioned" (:kind %)) cohorts))
        base       (- total fissioned)
        rate       (if (pos? total)
                     (double (/ fissioned total))
                     0.0)]
    {:total        total
     :fissioned    fissioned
     :base         base
     :fission-rate rate
     :axis-pcf-l1  (count (distinct (keep :pcfL1 cohorts)))
     :axis-role     (count (distinct (keep :role cohorts)))
     :axis-industry (count (distinct (keep :industry cohorts)))
     :axis-locale   (count (distinct (keep :locale cohorts)))}))

;; ---------------------------------------------------------------------------
;; Pure: build-coverage-matrix
;; ---------------------------------------------------------------------------

(defn build-coverage-matrix
  "Build a 2D coverage matrix from cohorts.
  row-ax and col-ax are key names (e.g. :role, :pcfL1) to group by.
  Returns {:matrix {rv {cv count}} :rows [rv...] :cols [cv...]}."
  [cohorts row-ax col-ax]
  (let [matrix (reduce
                (fn [m c]
                  (let [rv (get c row-ax)
                        cv (get c col-ax)]
                    (if (and rv cv)
                      (update-in m [rv cv] (fnil inc 0))
                      m)))
                {}
                cohorts)
        rows   (sort (keys matrix))
        cols   (sort (distinct (mapcat keys (vals matrix))))]
    {:matrix matrix
     :rows   (vec rows)
     :cols   (vec cols)}))

;; ---------------------------------------------------------------------------
;; Pure: find-gaps
;; ---------------------------------------------------------------------------

(defn find-gaps
  "Find (row, col) cells where matrix count < min-count.
  matrix is {rv {cv count}}, rows and cols are vectors.
  Returns a vector of {:row rv :col cv :count n} maps."
  [matrix rows cols min-count]
  (vec
   (for [rv rows
         cv cols
         :let [n (get-in matrix [rv cv] 0)]
         :when (< n min-count)]
     {:row rv :col cv :count n})))

;; ---------------------------------------------------------------------------
;; Pure: compute-snapshot-agg
;; ---------------------------------------------------------------------------

(defn compute-snapshot-agg
  "Aggregate cohorts by a tuple of axis keys.
  axes is a seq of keys to combine into a pipe-separated group key.
  Returns a map of {group-key count}."
  [cohorts axes]
  (reduce
   (fn [m c]
     (let [k (str/join "|" (map #(str (get c %)) axes))]
       (update m k (fnil inc 0))))
   {}
   cohorts))

;; ---------------------------------------------------------------------------
;; Pure: diff-snapshots
;; ---------------------------------------------------------------------------

(defn diff-snapshots
  "Compute the delta of total cohorts between two snapshot data maps.
  Each snapshot map should have a :total key (or \"total\" string key).
  Returns {:from-total :to-total :delta :from-ts :to-ts}."
  [from-data to-data]
  (let [from-total (or (:total from-data) (get from-data "total") 0)
        to-total   (or (:total to-data)   (get to-data "total")   0)
        from-ts    (or (:timestamp from-data) (get from-data "timestamp") "")
        to-ts      (or (:timestamp to-data)   (get to-data "timestamp")   "")]
    {:from-total from-total
     :to-total   to-total
     :delta      (- to-total from-total)
     :from-ts    from-ts
     :to-ts      to-ts}))

;; ---------------------------------------------------------------------------
;; Pure: parse-segment-arg
;; ---------------------------------------------------------------------------

(defn parse-segment-arg
  "Parse a segment argument string.
  If the string starts with '@', read JSON from that file path (using read-fn).
  Otherwise parse the string as JSON directly.
  read-fn defaults to slurp.
  Returns the parsed data map or nil on failure."
  ([arg] (parse-segment-arg arg nil))
  ([arg {:keys [read-fn] :or {read-fn slurp}}]
   (when (seq arg)
     (try
       (if (str/starts-with? arg "@")
         (let [path (subs arg 1)]
           (json/parse-string (read-fn path) true))
         (json/parse-string arg true))
       (catch Exception _
         nil)))))

;; ---------------------------------------------------------------------------
;; Pure: render-lineage-tree
;; ---------------------------------------------------------------------------

(defn render-lineage-tree
  "Render a lineage chain as ASCII tree lines.
  chain is a seq of maps with :nanoid and :name (or 'nanoid'/'name') keys.
  Returns a vector of display strings."
  [chain]
  (let [items (vec chain)
        n     (count items)]
    (vec
     (map-indexed
      (fn [i item]
        (let [nanoid (or (:nanoid item) (get item "nanoid") "")
              name   (or (:name item)   (get item "name")   "")
              last?  (= i (dec n))
              prefix (if last? "└── " "├── ")]
          (str prefix nanoid "  " name)))
      items))))

;; ---------------------------------------------------------------------------
;; IO: default-http-fn
;; ---------------------------------------------------------------------------

(defn- default-http-fn
  "Real babashka.http-client dispatch."
  [{:keys [method url headers params body]}]
  #?(:bb
     (let [opts (cond-> {:headers (or headers {}) :timeout 30000}
                  params (assoc :query-params params)
                  body   (assoc :body (json/generate-string body)))
           resp (case method
                  :get    (http/get    url opts)
                  :post   (http/post   url opts)
                  :patch  (http/patch  url opts)
                  :delete (http/delete url opts))]
       {:status (:status resp) :body (:body resp)})
     :default
     (throw (ex-info "babashka.http-client only available under bb"
                     {:method method :url url}))))

;; ---------------------------------------------------------------------------
;; IO: build-auth-headers
;; ---------------------------------------------------------------------------

(defn- build-auth-headers
  "Build Authorization + Content-Type headers from token string."
  [token]
  (cond-> {"Content-Type" "application/json"}
    (seq token) (assoc "Authorization" (str "Bearer " token))))

;; ---------------------------------------------------------------------------
;; IO request-shaping: build-* return {:method :url :headers :body/:params}
;; ---------------------------------------------------------------------------

(defn build-gen-request
  "Shape for com.etzhayyim.cohort.gen POST.
  segment-map is from build-gen-segment.
  Returns request map."
  [pds-url token segment-map]
  {:method  :post
   :url     (str pds-url "/xrpc/com.etzhayyim.cohort.gen")
   :headers (build-auth-headers token)
   :body    {:pcfL1     (:pcf-l1 segment-map)
             :role      (:role segment-map)
             :industry  (:industry segment-map)
             :seniority (:seniority segment-map)
             :locale    (:locale segment-map)
             :k         (:k segment-map)}})

(defn build-list-request
  "Shape for com.etzhayyim.cohort.list GET.
  opts: :pcf-l1, :role, :industry, :locale, :limit (default 100)."
  [pds-url token {:keys [pcf-l1 role industry locale limit]
                   :or   {limit 100}}]
  {:method  :get
   :url     (str pds-url "/xrpc/com.etzhayyim.cohort.list")
   :headers (build-auth-headers token)
   :params  (cond-> {"limit" (str limit)}
              (seq pcf-l1)   (assoc "pcfL1" pcf-l1)
              (seq role)      (assoc "role" role)
              (seq industry)  (assoc "industry" industry)
              (seq locale)    (assoc "locale" locale))})

(defn build-inspect-request
  "Shape for com.etzhayyim.cohort.getById GET."
  [pds-url token cohort-id]
  {:method  :get
   :url     (str pds-url "/xrpc/com.etzhayyim.cohort.getById")
   :headers (build-auth-headers token)
   :params  {"id" cohort-id}})

(defn build-fission-request
  "Shape for com.etzhayyim.cohort.fission POST.
  opts: :k (fission factor), :dry-run? (default false)."
  [pds-url token cohort-id {:keys [k dry-run?]
                              :or   {k 2 dry-run? false}}]
  {:method  :post
   :url     (str pds-url "/xrpc/com.etzhayyim.cohort.fission")
   :headers (build-auth-headers token)
   :body    {:id     cohort-id
             :k      k
             :dryRun dry-run?}})

(defn build-lineage-request
  "Shape for com.etzhayyim.cohort.lineage GET."
  [pds-url token cohort-id]
  {:method  :get
   :url     (str pds-url "/xrpc/com.etzhayyim.cohort.lineage")
   :headers (build-auth-headers token)
   :params  {"id" cohort-id}})

(defn build-forest-request
  "Shape for com.etzhayyim.cohort.forest GET.
  opts: :pcf-l1 filter (optional)."
  [pds-url token {:keys [pcf-l1]}]
  {:method  :get
   :url     (str pds-url "/xrpc/com.etzhayyim.cohort.forest")
   :headers (build-auth-headers token)
   :params  (cond-> {} (seq pcf-l1) (assoc "pcfL1" pcf-l1))})

(defn build-snap-request
  "Shape for com.etzhayyim.cohort.snap POST.
  opts: :axes (vector of axis names)."
  [pds-url token {:keys [axes]}]
  {:method  :post
   :url     (str pds-url "/xrpc/com.etzhayyim.cohort.snap")
   :headers (build-auth-headers token)
   :body    {:axes (or axes [])}})

(defn build-diff-request
  "Shape for com.etzhayyim.cohort.diff GET.
  opts: :from (timestamp string), :to (timestamp string)."
  [pds-url token {:keys [from to]}]
  {:method  :get
   :url     (str pds-url "/xrpc/com.etzhayyim.cohort.diff")
   :headers (build-auth-headers token)
   :params  (cond-> {}
              (seq from) (assoc "from" from)
              (seq to)   (assoc "to" to))})

(defn build-drift-request
  "Shape for com.etzhayyim.cohort.drift GET."
  [pds-url token]
  {:method  :get
   :url     (str pds-url "/xrpc/com.etzhayyim.cohort.drift")
   :headers (build-auth-headers token)
   :params  {}})

;; ---------------------------------------------------------------------------
;; IO: fetch-cohorts
;; ---------------------------------------------------------------------------

(defn fetch-cohorts
  "Fetch cohorts via com.etzhayyim.cohort.list.
  Returns vector of cohort maps or throws on HTTP error."
  [pds-url token filter-opts {:keys [http-fn]
                               :or   {http-fn default-http-fn}}]
  (let [req  (build-list-request pds-url token filter-opts)
        resp (http-fn req)]
    (when (>= (:status resp) 400)
      (throw (ex-info (str "cohort.list HTTP " (:status resp))
                      {:status (:status resp) :body (:body resp)})))
    (let [data (json/parse-string (:body resp) true)]
      (vec (or (:cohorts data) (if (sequential? data) data []))))))

;; ---------------------------------------------------------------------------
;; IO: gen-cohort (dry-run aware)
;; ---------------------------------------------------------------------------

(defn gen-cohort
  "Generate a new cohort via com.etzhayyim.cohort.gen.
  With :dry-run? true, returns the request shape without making a network call.
  Returns the response data map (or request shape on dry-run)."
  [pds-url token segment-map {:keys [dry-run? http-fn]
                               :or   {dry-run? false http-fn default-http-fn}}]
  (let [req (build-gen-request pds-url token segment-map)]
    (if dry-run?
      {:dry-run true :request req}
      (let [resp (http-fn req)]
        (when (>= (:status resp) 400)
          (throw (ex-info (str "cohort.gen HTTP " (:status resp))
                          {:status (:status resp) :body (:body resp)})))
        (json/parse-string (:body resp) true)))))

;; ---------------------------------------------------------------------------
;; CLI entrypoint (JVM/bb only) — mirrors the Python click group `cohort`
;; (cohort.py). `gen --dry-run` runs for real (build-gen-segment, prints the
;; segment, exactly like Python). Read-only network commands (list/get/stats/
;; dashboard/coverage/gap/forest/lineage/lineage-stats/evidence/snapshot) need a
;; live PDS + auth and are GUARDED no-ops. Mutating POSTs (create/seed/fission/
;; emit/repair-edge) are GUARDED. `bootstrap` mirrors Python's Go-binary notice.
;; ---------------------------------------------------------------------------

#?(:clj
   (do
     (def ^:private read-subs
       #{"list" "get" "stats" "dashboard" "coverage" "gap" "forest"
         "lineage" "lineage-stats" "evidence" "snapshot"})
     (def ^:private write-subs
       #{"create" "seed" "emit" "repair-edge"})
     (def ^:private cohort-bool-flags #{"--json" "--dry-run"})

     (defn- coh-parse-opts [args]
       (loop [a args pos [] opts {}]
         (if (empty? a)
           [pos opts]
           (let [t (first a)]
             (cond
               (contains? cohort-bool-flags t) (recur (rest a) pos (assoc opts t true))
               (str/starts-with? t "-")        (recur (drop 2 a) pos (assoc opts t (second a)))
               :else                           (recur (rest a) (conj pos t) opts))))))

     (defn- usage []
       (println "usage: cohort <sub> [args] [--opts]")
       (println "  offline: gen --dry-run [--pcf-l1 .. --role .. -k N], diff <a.json> <b.json>, drift [--dir D]")
       (println "  read (guarded, network): list get stats dashboard coverage gap forest lineage lineage-stats evidence snapshot")
       (println "  write (guarded, network): create seed fission emit repair-edge")
       (println "  bootstrap (Go binary)"))

     (defn -main [& args]
       (let [sub (first args)
             [pos opts] (coh-parse-opts (rest args))]
         (cond
           (nil? sub) (usage)

           (= sub "gen")
           (let [seg (build-gen-segment (get opts "--pcf-l1" "") (get opts "--role" "")
                                        (get opts "--industry" "") (get opts "--seniority" "")
                                        (get opts "--locale" "ja")
                                        (try (Integer/parseInt (get opts "-k" "50")) (catch Exception _ 50)))]
             (if (get opts "--dry-run")
               ;; Python dry-run prints the segment JSON-LD and returns.
               (println (json/generate-string seg {:pretty true}))
               (println (str "cohort gen (guarded, no-op): would POST com.etzhayyim.cohort.seed with "
                             (json/generate-string seg) ". Add --dry-run to preview, or run the Python CLI for live seed."))))

           (= sub "fission")
           (let [did (get opts "--did" "")]
             (if (get opts "--dry-run")
               (println (str "dry-run: would fission cohort " did))
               (println (str "cohort fission (guarded, no-op): would POST com.etzhayyim.cohort.fission did=" did
                             ". Add --dry-run, or run the Python CLI for live fission."))))

           (= sub "diff")
           (let [[a b] pos]
             (if (and a b (.exists (java.io.File. ^String a)) (.exists (java.io.File. ^String b)))
               (let [d (diff-snapshots (json/parse-string (slurp a) true)
                                       (json/parse-string (slurp b) true))]
                 (if (get opts "--json")
                   (println (json/generate-string d {:pretty true}))
                   (println (str "  from=" (:from-ts d) "  to=" (:to-ts d)
                                 "  total_delta=" (:delta d)))))
               (binding [*out* *err*] (println "cohort diff: needs two existing snapshot JSON files: <a> <b>"))))

           (= sub "drift")
           (let [dir (get opts "--dir" "data/cohort-coverage")
                 d (java.io.File. ^String dir)]
             (if-not (.exists d)
               (binding [*out* *err*] (println (str "snapshot dir not found: " dir)))
               (let [files (sort (filter #(str/ends-with? (.getName ^java.io.File %) ".json")
                                         (seq (.listFiles d))))]
                 (if (< (count files) 2)
                   (binding [*out* *err*] (println "need at least 2 snapshots for drift analysis"))
                   (let [a (json/parse-string (slurp (first files)) true)
                         b (json/parse-string (slurp (last files)) true)
                         delta (diff-snapshots a b)]
                     (println (str "  drift: " (:from-ts delta) " → " (:to-ts delta)
                                   "  total_delta=" (:delta delta)
                                   "  over " (count files) " snapshots")))))))

           (= sub "bootstrap")
           (binding [*out* *err*]
             (println (str "cohort bootstrap reads deps.toml [[cohort_actors]] and requires the Go binary. "
                           "Run: etzhayyim cohort bootstrap")))

           (contains? read-subs sub)
           (println (str "cohort " sub " (guarded): read-only XRPC over a live PDS + auth — "
                         "not contacted in verify. Request-shaping (build-list/inspect/lineage/…-request) "
                         "and parsing (compute-dashboard/build-coverage-matrix/find-gaps) are available."))

           (contains? write-subs sub)
           (println (str "cohort " sub " (guarded, no-op): would POST com.etzhayyim.cohort." sub
                         " (network). Run the Python CLI for the live mutation."))

           :else
           (do (binding [*out* *err*] (println (str "cohort: unknown subcommand: " sub)))
               (usage)))))))
