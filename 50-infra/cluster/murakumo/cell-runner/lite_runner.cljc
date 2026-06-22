(ns lite-runner
  "lite-runner (bb) — clj/bb node cell-runner (Tier-1 supervisor). 1:1 cljc port of
  `lite_runner.py` (ADR-2606161645 + 2605192415 §7.1), per the repo-wide rule that
  operational/daemon code be clj/bb over the kotoba Datom log.

  THE runtime cutover: one bb supervisor per node. It reads the SAME `cells.edn`
  registry the python runner uses, cron-fires each due cell assigned to this node,
  and records each fire as a `:cell.run/*` tx on a local kotoba ops commit-DAG
  (content-addressed, append-only). The ops log is **byte-identical** to the python
  runner's (same canonical-JSON tx-cid + same EDN line rendering) so the two are
  drop-in interchangeable — that interchangeability is what makes the cutover safe.

  Unlike the python runner (which `importlib`-imports a PYTHON cell module), this fires
  cljc cells NATIVELY (require + resolve the entry var), and can fall back to shelling a
  python cell via babashka.process for any cell not yet ported. No network I/O of its
  own beyond what a cell does; cells hold their own gates; the ops log is the audit trail.

    bb --classpath . -m lite-runner --node issachar --registry cells.edn --cells-root ~/.etzhayyim/cells
    bb --classpath . -m lite-runner --node issachar ... --once     # fire all due cells once and exit"
  (:require [clojure.string :as str]
            [clojure.edn :as edn]
            [cheshire.core :as json]
            [babashka.process :as p]
            [org.httpkit.server :as hk])
  (:import [java.security MessageDigest]
           [java.util Date]
           [java.text SimpleDateFormat]))

(defn- default-clock
  "Real wall-clock tick: {:minute m :stamp \"yyyyMMddHHmm\"}. Mirrors python's
  time.localtime()/strftime. Injectable `clock` overrides this for tests."
  []
  (let [stamp (.format (SimpleDateFormat. "yyyyMMddHHmm") (Date.))]
    {:minute (Integer/parseInt (subs stamp 10 12)) :stamp stamp}))

;; ── cells.edn is real EDN — read it natively (the python runner reimplemented an EDN
;;    parser only because python has no reader; bb has clojure.edn). Datom-log lines
;;    written by either runner are also valid EDN, read back the same way. ──

(defn parse-edn [s] (edn/read-string s))

(defn load-cells
  "Return the cron-triggered cells assigned to `node` from cells.edn. Port of `load_cells`."
  [registry-path node]
  (let [doc (edn/read-string (slurp registry-path))
        cells (if (map? doc) (get doc :cell []) [])]
    (->> cells
         (filter map?)
         (filter #(= (get % :node) node))
         (filter #(= (get-in % [:trigger :kind]) "cron"))
         vec)))

(defn cron-minute
  "Parse the minute field of a 5-field cron expr → set of minutes (N, */N, *). Port of `cron_minute`."
  [expr]
  (let [field (if (and expr (seq (str/trim (str expr))))
                (first (str/split (str/trim (str expr)) #"\s+"))
                "*")]
    (cond
      (= field "*") (set (range 60))
      (str/starts-with? field "*/") (let [step (Integer/parseInt (subs field 2))]
                                      (set (range 0 60 step)))
      :else (->> (str/split field #",")
                 (filter #(re-matches #"\d+" (str/trim %)))
                 (map #(Integer/parseInt (str/trim %)))
                 set))))

;; ── kotoba ops commit-DAG (content-addressed, append-only) — BYTE-PARITY with python ──

(defn- sha256-hex [^bytes b]
  (let [md (MessageDigest/getInstance "SHA-256")]
    (->> (.digest md b)
         (map #(format "%02x" (bit-and % 0xff)))
         (apply str))))

(defn- canonical
  "Port of `_canonical`: compact, sort_keys JSON of {prev,datoms} as UTF-8 bytes.
  datoms are vectors of STRINGS (matching the python list-of-strings); cheshire over a
  sorted-map gives sorted keys + compact separators, matching json.dumps(sort_keys=True,
  separators=(',',':'))."
  ^bytes [datoms prev]
  (.getBytes ^String (json/generate-string (sorted-map "datoms" datoms "prev" prev)) "UTF-8"))

(defn tx-cid
  "Port of `_tx_cid`: \"b\" + sha256(canonical)."
  ([datoms] (tx-cid datoms ""))
  ([datoms prev] (str "b" (sha256-hex (canonical datoms prev)))))

(defn- read-log
  "Port of `_read_log`: parse each non-comment line of the ops log into a tx map."
  [path]
  (let [f (java.io.File. (str path))]
    (if-not (.exists f)
      []
      (->> (str/split-lines (slurp f))
           (remove #(or (str/blank? %) (str/starts-with? (str/trim %) ";")))
           (mapv edn/read-string)))))

(defn- head
  "Port of `_head`: the last tx's :tx/cid, or \"\"."
  [path]
  (let [txs (read-log path)]
    (if (seq txs) (get (last txs) :tx/cid) "")))

(defn- edn-val
  "Port of `_edn_val`: keyword-strings (\":…\") render bare; other strings JSON-quoted;
  bools → true/false; ints → their digits."
  [v]
  (cond
    (boolean? v) (if v "true" "false")
    (integer? v) (str v)
    (and (number? v)) (str v)
    (string? v) (if (str/starts-with? v ":") v (json/generate-string v))
    :else (json/generate-string (str v))))

(defn append-run
  "Append one :cell.run/* tx to the ops commit-DAG. Port of `append_run` — the written
  line is byte-identical to the python runner's."
  [log-path & {:keys [node cell status detail as-of]}]
  (let [e (str "cell.run." node "." cell "." as-of)
        datoms [[":db/add" e ":cell.run/node" (str ":" node)]
                [":db/add" e ":cell.run/cell" cell]
                [":db/add" e ":cell.run/status" status]
                [":db/add" e ":cell.run/as-of" as-of]
                [":db/add" e ":cell.run/detail" (subs detail 0 (min 200 (count detail)))]]
        prev (head log-path)
        cid (tx-cid datoms prev)
        f (java.io.File. (str log-path))]
    (when-let [parent (.getParentFile f)] (.mkdirs parent))
    (when-not (.exists f)
      (spit f ";; lite_runner ops commit-DAG — append-only. ADR-2606161645.\n"))
    (let [body (->> datoms
                    (map (fn [d] (str "[" (str/join " " (map edn-val d)) "]")))
                    (str/join " "))
          n (inc (count (read-log log-path)))]
      (spit f (str "{:tx/id " n " :tx/as-of " as-of
                   " :tx/prev " (json/generate-string prev)
                   " :tx/cid " (json/generate-string cid)
                   " :tx/datoms [" body "]}\n")
            :append true))
    cid))

;; ── fire a cell ──────────────────────────────────────────────────────────────────

(defn fire-cell
  "Fire a cell. Returns [status detail]. Native cljc path: require the cell's :module ns
  and call its :entry var (default `fire`). A failing cell must NOT kill the supervisor.

  Cutover-safety (ADR-2606221900): the bb runner must behave IDENTICALLY to the python
  runner for the cells that exist today (which are python modules). So firing AUTO-FALLS-BACK:
  it tries the cljc ns natively, and if that ns is simply not on the classpath (a python-only
  cell), it shells the python module exactly as the python runner did — no per-cell annotation
  needed. `:lang \"python\"` forces the python shell explicitly; a cell whose cljc ns loads but
  then THROWS is a real :error (not a fallback)."
  [cell cells-root]
  (let [mod (get cell :module)
        entry-name (get cell :entry "fire")
        fire-python
        (fn []
          (let [r (p/shell {:out :string :err :string :continue true
                            :extra-env {"PYTHONPATH" (str cells-root)}}
                           "python3" "-c"
                           (str "import importlib,sys; m=importlib.import_module('" mod "'); "
                                "r=getattr(m,'" entry-name "')(); print((r or {}).get('cid') or (r or {}).get('head') or 'ok')"))]
            (if (zero? (:exit r))
              [":ok" (let [s (str/trim (:out r))] (subs s 0 (min 16 (count s))))]
              [":error" (str/trim (:err r))])))]
    (if (= (get cell :lang) "python")
      (try (fire-python) (catch Throwable e [":error" (str (.getSimpleName (class e)) ": " (.getMessage e))]))
      ;; native cljc path, with auto-fallback to python when the ns isn't on the classpath
      (let [native (try
                     (require (symbol mod))
                     (let [f (requiring-resolve (symbol mod entry-name))
                           res (f)
                           cid (when (map? res) (or (get res "cid") (get res :cid) (get res "head") (get res :head)))]
                       [":ok" (if cid (subs (str cid) 0 (min 16 (count (str cid)))) "ok")])
                     (catch java.io.FileNotFoundException _ ::not-on-classpath
                       )
                     (catch Throwable e [":error" (str (.getSimpleName (class e)) ": " (.getMessage e))]))]
        (if (= native ::not-on-classpath)
          (try (fire-python) (catch Throwable e [":error" (str (.getSimpleName (class e)) ": " (.getMessage e))]))
          native)))))

;; ── healthz ──────────────────────────────────────────────────────────────────────

(def ^:private state (atom {:node "?" :cells [] :last {}}))

(defn- serve-healthz [port]
  (hk/run-server
   (fn [_req]
     {:status 200
      :headers {"Content-Type" "application/json"}
      :body (json/generate-string (merge {:ok true} @state))})
   {:port (int port) :ip "127.0.0.1"}))

;; ── run loop ──────────────────────────────────────────────────────────────────────

(defn run
  "Cron supervision loop. Port of `run`. `clock` (a 0-arg fn → java.util.Calendar-like
  {:minute :stamp}) is injectable for tests; `once` fires due cells once and returns @state."
  [node registry cells-root ops-log & {:keys [healthz-port once tick clock]
                                       :or {tick 60000}}]
  (let [cells (load-cells registry node)]
    (swap! state assoc :node node :cells (mapv #(get % :name) cells))
    (when healthz-port (serve-healthz healthz-port))
    (loop [fired #{}]
      (let [{:keys [minute stamp]} (if clock (clock) (default-clock))
            due (filter #(contains? (cron-minute (get-in % [:trigger :expr])) minute) cells)
            fired' (reduce
                    (fn [acc c]
                      (let [k [(get c :name) stamp]]
                        (if (contains? acc k)
                          acc
                          (let [as-of (Long/parseLong stamp)
                                [status detail] (fire-cell c cells-root)]
                            (append-run ops-log :node node :cell (get c :name)
                                        :status status :detail detail :as-of as-of)
                            (swap! state assoc-in [:last (get c :name)]
                                   {:status status :detail detail :at stamp})
                            (println (str "lite_runner[" node "] " (get c :name) " " status " " detail))
                            (conj acc k)))))
                    fired due)]
        (if once
          @state
          (do (Thread/sleep tick)
              (recur (if (> (count fired') 256) #{} fired'))))))))

(defn -main [& args]
  (let [once? (boolean (some #{"--once"} args))
        ;; --once is a valueless flag; strip it before pairing the rest into a kv map
        opts (apply hash-map (remove #{"--once"} args))
        node (or (get opts "--node") (System/getenv "ETZHAYYIM_NODE_NAME"))
        registry (get opts "--registry")
        cells-root (get opts "--cells-root")
        ops-log (or (get opts "--ops-log") (str (System/getProperty "user.home") "/.etzhayyim/cells/cell-ops.kotoba.edn"))
        healthz (some-> (get opts "--healthz-port") Integer/parseInt)]
    (when (or (str/blank? (str node)) (str/blank? (str registry)) (str/blank? (str cells-root)))
      (binding [*out* *err*] (println "ERROR: --node (or ETZHAYYIM_NODE_NAME), --registry, --cells-root required"))
      (System/exit 2))
    (run node registry cells-root ops-log
         :healthz-port (when (and healthz (pos? healthz)) healthz)
         :once once?)
    (System/exit 0)))
