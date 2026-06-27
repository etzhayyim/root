(ns lg-open-patent.graphs.ingest-multi
  "open-patent `ingest_multi` graph — Follow-based multi-jurisdiction patent ingest.

  NSID: com.etzhayyim.apps.openPatent.ingestMulti  (daily cron 0 2 * * *)

  PORT NOTE (ADR-2606280030): the Python `lg/lg_open_patent/graphs/ingest_multi.py`
  is a thin re-export of `kotodama.langgraph_graphs.open_patent_ingest_multi`; that
  kotodama module is NOT vendored in this checkout. This is a faithful port of the
  documented Follow-based ingest architecture (app CLAUDE.md `Ingest Architecture`):

      patent.etzhayyim.com -> AT firehose -> open-patent subscribeRepos
        -> onCommit(com.etzhayyim.apps.openPatent.patent)
             -> enrich (EPO citations, JPO cross-link)
                  -> persist (vertex_open_patent_* -> kotoba Datom log seam)

  Self HTTP pull is forbidden — data arrives only via Follow. Topology here:

      START -> subscribe -> enrich -> persist -> emit_audit -> END

  Boundaries are injectable (rebound in tests):
    *ingest-source*    (cursor) -> {:patents [<map>...] :cursor <next>}
                                  default: nothing wired offline (Follow has no
                                  local firehose), returns {:patents []}.
    *enrich-citations* (patent) -> [<citation-map>...]   default: [] (no EPO/JPO).
    store via lg-open-patent.store/*store* (PatentStore)."
  (:require [langgraph.graph :as g]
            [lg-open-patent.store :as store]))

(def ^:dynamic *ingest-source*
  (fn [_cursor]
    {:patents [] :note "Follow-based ingest: no AT firehose source wired offline"}))

(def ^:dynamic *enrich-citations*
  (fn [_patent] []))

;; ── nodes ─────────────────────────────────────────────────────────────────────

(defn node-subscribe
  "Pull new patent records arriving via the AT firehose Follow (no self HTTP pull)."
  [state]
  (let [res    (*ingest-source* (:cursor state))
        pats   (vec (or (:patents res) []))]
    (cond-> {:patents pats :ingest_cursor (:cursor res)}
      (:note res) (assoc :note (:note res)))))

(defn node-enrich
  "Cross-link EPO/JPO citations for each ingested patent (Follow-enriched)."
  [state]
  (let [cites (->> (:patents state)
                   (mapcat (fn [p] (or (*enrich-citations* p) [])))
                   vec)]
    {:citations cites}))

(defn node-persist
  "Persist patents + citations through the injectable store seam (kotoba Datom log)."
  [state]
  (let [np (store/put-patents!   store/*store* (or (:patents state) []))
        nc (store/put-citations! store/*store* (or (:citations state) []))]
    {:ingested_patents np :ingested_citations nc}))

(defn node-emit-audit
  "Emit the run summary (append-only audit semantics)."
  [state]
  {:ok true
   :summary {:patents   (or (:ingested_patents state) 0)
             :citations (or (:ingested_citations state) 0)}})

(defn build
  "Compile the ingest_multi StateGraph."
  []
  (-> (g/state-graph)
      (g/add-node :subscribe node-subscribe)
      (g/add-node :enrich node-enrich)
      (g/add-node :persist node-persist)
      (g/add-node :emit_audit node-emit-audit)
      (g/add-edge :subscribe :enrich)
      (g/add-edge :enrich :persist)
      (g/add-edge :persist :emit_audit)
      (g/set-entry-point :subscribe)
      (g/set-finish-point :emit_audit)
      (g/compile-graph)))

(def GRAPH (build))
