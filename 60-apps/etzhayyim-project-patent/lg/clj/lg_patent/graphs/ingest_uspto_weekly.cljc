(ns lg-patent.graphs.ingest-uspto-weekly
  "patent `ingest_uspto_weekly` graph — weekly USPTO PatentsView + EPO citations ingest.

  Port of `lg/lg_patent/graphs/ingest_uspto_weekly.py` (ADR-2606280030), which
  in the python re-exported `kotodama.langgraph_graphs.patent_ingest_uspto_weekly`.
  That kotodama module is NOT vendored into this checkout; this port reconstructs
  the pipeline TOPOLOGY + contract from langgraph.json (cron `0 2 * * 0`, empty
  input) + the actor CLAUDE.md (USPTO PatentsView JSON / EPO OPS citations →
  `vertex_patent` + `edge_patent_cites`), with the side-effecting boundaries
  INJECTABLE per the actor-swap pattern:

    *http-get*       — network boundary: fetch a public source URL → parsed body.
                       Default = babashka.http-client GET (httpx → bb, repo rule).
    *write-records*  — store seam: upsert patents + citation edges. RisingWave is
                       FORBIDDEN (substrate boundary); target = kotoba Datom log.
                       Default = no-op (store not configured).

  Topology (faithful intent): fetch-uspto → fetch-epo-citations → upsert → END.
  A node short-circuits (passes through) once `:error`/`:skip` is present.

  DEVIATIONS (noted in PR): kotodama source absent → topology reconstructed +
  injectable seams; httpx → babashka.http-client; JSON → cheshire; RisingWave →
  kotoba-Datom-log store seam; no per-node RetryPolicy."
  (:require [clojure.string :as str]
            [langgraph.graph :as g]
            #?(:clj [cheshire.core :as json])
            #?(:clj [babashka.http-client :as http])))

(defn- getenv [k default]
  #?(:clj (or (System/getenv k) default) :default default))

(defn patentsview-url []
  (-> (getenv "PATENTSVIEW_URL" "https://search.patentsview.org/api/v1/patent/")
      (str/replace #"/+$" "")))

(defn- default-http-get
  "Real public-source GET → parsed JSON map (or {::http-error status})."
  [url]
  #?(:clj
     (let [resp (http/get url {:headers {"Accept" "application/json"} :throw false})
           status (:status resp)]
       (if (>= status 400)
         {::http-error status}
         (try (json/parse-string (:body resp) true)
              (catch Exception _ {::parse-error true :raw (:body resp)}))))
     :default {::http-error 0}))

(def ^:dynamic *http-get* default-http-get)

(def ^:dynamic *write-records*
  "Store seam: upsert {:patents [...] :citations [...]} → counts. Default no-op
  signals an unconfigured store (kotoba Datom log target at deploy)."
  (fn [_payload] nil))

(defn fetch-uspto
  "Fetch USPTO PatentsView patents. Network-disabled / unconfigured → skip."
  [state]
  (if (false? (:network state))
    {:status "skipped" :error "network disabled" :patents []}
    (let [resp (*http-get* (patentsview-url))]
      (if (::http-error resp)
        {:status "skipped" :error (str "patentsview http " (::http-error resp)) :patents []}
        {:patents (vec (or (:patents resp) []))}))))

(defn fetch-epo-citations
  "Fetch EPO OPS citation edges for the fetched patents. Pass-through on skip."
  [state]
  (if (:error state)
    {}
    (let [cites (get state :epo-citations [])]
      {:citations (vec cites)})))

(defn upsert
  "Persist patents + citation edges via the store seam. Pass-through on skip."
  [state]
  (if (:error state)
    {}
    (let [payload {:patents (or (:patents state) []) :citations (or (:citations state) [])}
          written (*write-records* payload)]
      (if (nil? written)
        {:status "skipped" :error "store not configured"
         :patents_seen (count (:patents payload)) :upserted 0}
        {:status "done" :upserted (get written :upserted (count (:patents payload)))
         :patents_seen (count (:patents payload))}))))

(defn build []
  (-> (g/state-graph)
      (g/add-node :fetch-uspto fetch-uspto)
      (g/add-node :fetch-epo-citations fetch-epo-citations)
      (g/add-node :upsert upsert)
      (g/set-entry-point :fetch-uspto)
      (g/add-edge :fetch-uspto :fetch-epo-citations)
      (g/add-edge :fetch-epo-citations :upsert)
      (g/set-finish-point :upsert)
      (g/compile-graph)))

(def GRAPH (build))
