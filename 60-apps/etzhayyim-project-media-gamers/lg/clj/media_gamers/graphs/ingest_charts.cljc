(ns media-gamers.graphs.ingest-charts
  "media-gamers `ingest_charts` graph — clj twin of graphs/ingest_charts.py.
  NSID: com.etzhayyim.apps.media_gamers.ingestCharts
  Cron: 0 9 * * 1 (Monday 09:00 UTC).

  Topology preserved: START → fetch → persist → analyze → audit → END.

  Port notes:
    - httpx GET steamspy → babashka.http-client; JSON → cheshire.
    - LLM analyze → Murakumo loopback (media-gamers.llm/chat).
    - persist: the python node wrote `vertex_game_chart_snapshot` /
      `vertex_game_chart_analysis` rows into RisingWave (psycopg). RisingWave is
      a PROHIBITED substrate (ADR-2605262130); the clj twin instead builds
      content-addressable kotoba EAVT datoms (pure `entries->datoms` /
      `analysis->datoms`) and returns the snapshot count. Appending to the live
      kotoba Datom log is a gated operator leg (deferred) — the loop itself does
      no DB write. Topology + counts are faithful."
  (:require [clojure.string :as str]
            [media-gamers.llm :as llm]
            [media-gamers.audit :as audit]
            #?(:clj [babashka.http-client :as http])
            #?(:clj [cheshire.core :as json])
            #?(:clj [langgraph.graph :as g])))

(defn- getenv [k default]
  #?(:clj (or (System/getenv k) default) :default default))

(defn app-did [] (getenv "MEDIA_GAMERS_APP_DID" "did:web:media-gamers.etzhayyim.com"))

(def steamspy-top2w-url "https://steamspy.com/api.php?request=top100in2weeks")

(defn week-start-utc []
  #?(:clj (.format (java.time.format.DateTimeFormatter/ofPattern "yyyy-MM-dd")
                   (java.time.LocalDate/now (java.time.ZoneOffset/UTC)))
     :default ""))

(defn- as-int [v] (try (long (Math/floor (double (cond (number? v) v
                                                       (string? v) (Double/parseDouble v)
                                                       :else 0))))
                       (catch Exception _ 0)))

(defn- name-or-str [k] (if (keyword? k) (name k) (str k)))

(defn parse-entries
  "Pure: SteamSpy dict {appid → info} → top-20 entries by players_2weeks desc.
  Port of the comprehension+sort in `_node_fetch`."
  [data]
  (->> data
       (filter (fn [[_ info]] (map? info)))
       (map (fn [[appid info]]
              {:appid (str (name-or-str appid))
               :name (str (get info :name (get info "name" "")))
               :players_2weeks (as-int (or (:players_2weeks info) (get info "players_2weeks") 0))
               :positive (as-int (or (:positive info) (get info "positive") 0))
               :negative (as-int (or (:negative info) (get info "negative") 0))
               :genre (str (or (:genre info) (get info "genre") ""))
               :developer (str (or (:developer info) (get info "developer") ""))
               :publisher (str (or (:publisher info) (get info "publisher") ""))}))
       (sort-by :players_2weeks >)
       (take 20)
       vec))

(defn entries->datoms
  "Charter-aligned replacement for the RW INSERT: build kotoba EAVT datoms for
  each chart-snapshot entry (one entity per appid+week)."
  [entries week-start]
  (vec (mapcat (fn [e]
                 (let [eid (str "chart-snapshot:" (:appid e) ":" week-start)]
                   [[:db/add eid :media_gamers.chart/appid (:appid e)]
                    [:db/add eid :media_gamers.chart/week-start week-start]
                    [:db/add eid :media_gamers.chart/name (:name e)]
                    [:db/add eid :media_gamers.chart/players-2weeks (:players_2weeks e)]
                    [:db/add eid :media_gamers.chart/positive (:positive e)]
                    [:db/add eid :media_gamers.chart/negative (:negative e)]
                    [:db/add eid :media_gamers.chart/genre (:genre e)]]))
               entries)))

(defn analysis->datoms [week-start analysis-ja analysis-en insight-tags]
  (let [eid (str "chart-analysis:" week-start)]
    [[:db/add eid :media_gamers.chart-analysis/week-start week-start]
     [:db/add eid :media_gamers.chart-analysis/analysis-ja analysis-ja]
     [:db/add eid :media_gamers.chart-analysis/analysis-en analysis-en]
     [:db/add eid :media_gamers.chart-analysis/insight-tags insight-tags]]))

;; ── nodes ───────────────────────────────────────────────────────────────────

#?(:clj
   (defn node-fetch [_state]
     (let [ws (week-start-utc)]
       (try
         (let [r (http/get steamspy-top2w-url {:timeout 30000 :throw false})]
           (if (>= (:status r) 400)
             {:ok false :error (str "steamspy http " (:status r)) :week-start ws}
             {:entries (parse-entries (json/parse-string (:body r) true))
              :week-start ws :ok true}))
         (catch Exception exc
           {:ok false :error (subs (str exc) 0 (min 200 (count (str exc)))) :week-start ws})))))

(defn node-persist
  "Port of `_node_persist` (RW INSERT → kotoba datoms; returns snapshot_count)."
  [state]
  (if (or (:error state) (empty? (:entries state)))
    {:snapshot-count 0}
    (let [datoms (entries->datoms (:entries state) (:week-start state ""))]
      {:snapshot-count (count (:entries state)) :chart-datoms datoms})))

#?(:clj
   (defn node-analyze [state]
     (let [entries (or (:entries state) [])]
       (if (empty? entries)
         {:analysis-ja "" :analysis-en "" :insight-tags []}
         (let [top5 (take 5 entries)
               context (str/join "\n"
                                 (map-indexed
                                  (fn [i e]
                                    (str (inc i) ". " (:name e)
                                         " (players_2weeks=" (:players_2weeks e)
                                         ", genre=" (:genre e) ")"))
                                  top5))
               raw (llm/chat
                    (str "You are a gaming industry analyst. Analyze the Steam chart data and return JSON: "
                         "{\"analysis_ja\": \"...\", \"analysis_en\": \"...\", \"insight_tags\": [...]}. "
                         "analysis_ja: 2-3 sentences in Japanese. analysis_en: 2-3 sentences in English. "
                         "insight_tags: 3-5 short English tags (e.g. 'action-rpg-dominant', 'indie-surge').")
                    (str "Steam Top 2-week chart (week of " (:week-start state "unknown") "):\n" context)
                    :max-tokens 500 :temp 0.4)
               parsed (try (json/parse-string raw true) (catch Exception _ nil))]
           (if parsed
             {:analysis-ja (str (or (:analysis_ja parsed) ""))
              :analysis-en (str (or (:analysis_en parsed) ""))
              :insight-tags (mapv str (or (:insight_tags parsed) []))}
             {:analysis-ja "" :analysis-en (if (seq raw) (subs raw 0 (min 500 (count raw))) "")
              :insight-tags []}))))))

(defn node-audit [state]
  #?(:clj (audit/emit-audit-bg
           {:actor (app-did)
            :activity "media_gamers.charts.ingest"
            :object-id (str "charts:" (:week-start state "") ":" (quot (System/currentTimeMillis) 1000))
            :object-type "media_gamers.chartSnapshot"
            :attributes {:weekStart (:week-start state)
                         :snapshotCount (:snapshot-count state 0)
                         :insightTags (:insight-tags state [])
                         :ok (:ok state true)
                         :error (:error state)}}))
  {})

#?(:clj
   (defn build []
     (-> (g/state-graph)
         (g/add-node :fetch node-fetch)
         (g/add-node :persist node-persist)
         (g/add-node :analyze node-analyze)
         (g/add-node :audit node-audit)
         (g/add-edge :fetch :persist)
         (g/add-edge :persist :analyze)
         (g/add-edge :analyze :audit)
         (g/set-entry-point :fetch)
         (g/set-finish-point :audit)
         (g/compile-graph))))

#?(:clj (def graph (delay (build))))
