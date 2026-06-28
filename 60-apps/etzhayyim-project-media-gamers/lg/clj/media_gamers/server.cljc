(ns media-gamers.server
  "media-gamers server registry + XRPC dispatch — clj twin of server.py.

  Port scope: the python `server.py` is a FastAPI app. Building a full HTTP
  server in bb is out of scope for the graph port; what is ported here is the
  load-bearing dispatch LOGIC the python smoke tests assert on:
    - GRAPHS              registry (name → compiled langgraph-clj graph)
    - nsid->assistant     NSID → assistant_id mapping
    - camel->snake + xrpc-input->graph-input  (the XRPC body key transform)
    - invoke-graph        run a registered graph once (≈ /xrpc/{nsid})
  A FastAPI/HTTP transport on top of this is a follow-up (note in PR).

  pokopia_research is a thin re-export of a kotodama python graph
  (`kotodama.langgraph_graphs.pokopia_research_agent_loop/build_graph`); it has
  no clj twin yet (kotodama itself is unported). It stays in the registry as a
  declared name so the NSID map + langgraph.json parity hold; invoking it from
  clj is gated until kotodama is ported (coexist)."
  (:require [clojure.string :as str]
            #?(:clj [media-gamers.graphs.health :as health])
            #?(:clj [media-gamers.graphs.ingest-charts :as ingest-charts])
            #?(:clj [media-gamers.graphs.guide-generator :as guide-generator])
            #?(:clj [media-gamers.graphs.autopilot :as autopilot])
            #?(:clj [langgraph.graph :as g])))

;; Declared graph names — parity with langgraph.json `graphs` keys + server.py GRAPHS.
(def graph-names
  #{"health" "ingest_charts" "guide_generator" "autopilot" "pokopia_research"})

(def nsid->assistant
  {"com.etzhayyim.apps.media_gamers.health"          "health"
   "com.etzhayyim.apps.media_gamers.ingestCharts"    "ingest_charts"
   "com.etzhayyim.apps.media_gamers.generateGuide"   "guide_generator"
   "com.etzhayyim.apps.media_gamers.autopilot"       "autopilot"
   "com.etzhayyim.apps.media_gamers.researchPokopia" "pokopia_research"})

#?(:clj
   (def graphs
     "Registry of compiled langgraph-clj graphs (clj-ported ones). pokopia_research
     is intentionally absent from the compiled map (coexist w/ unported kotodama);
     its name is still a declared graph (`graph-names`)."
     (delay {"health"          @health/graph
             "ingest_charts"   @ingest-charts/graph
             "guide_generator" @guide-generator/graph
             "autopilot"       @autopilot/graph})))

(defn camel->snake
  "Port of `_camel_to_snake`."
  [s]
  (->> (str s)
       (map-indexed (fn [i ch]
                      (if (and (Character/isUpperCase ^char ch) (pos? i))
                        (str "_" (Character/toLowerCase ^char ch))
                        (str (Character/toLowerCase ^char ch)))))
       (apply str)))

(defn xrpc-input->graph-input
  "Port of `_xrpc_input_to_graph_input` — camelCase body keys → snake_case keyword
  keys (clj graphs read kebab keys, so we also kebab them)."
  [body]
  (into {} (map (fn [[k v]]
                  [(keyword (str/replace (camel->snake (name k)) "_" "-")) v]))
        (or body {})))

#?(:clj
   (defn invoke-graph
     "Run one registered graph by assistant_id (≈ /runs). Returns the final state."
     [assistant-id input]
     (if-let [cg (get @graphs assistant-id)]
       (g/invoke cg input)
       (throw (ex-info (str "unknown graph: " assistant-id) {:assistant-id assistant-id})))))

#?(:clj
   (defn xrpc
     "Port of `/xrpc/{nsid}` dispatch: NSID → assistant → invoke. Throws ex-info
     {:status 404} for an unknown NSID, mirroring the python HTTPException."
     [nsid body]
     (let [assistant (nsid->assistant nsid)]
       (when-not assistant
         (throw (ex-info (str "unknown NSID: " nsid) {:status 404 :nsid nsid})))
       (invoke-graph assistant (xrpc-input->graph-input body)))))
