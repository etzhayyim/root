(ns lg-pregel.graphs.outlook-triage
  "pregel `outlook_triage` graph — Outlook email triage resident worker.

  Faithful clj twin of the Python graph `kotodama.agents.outlook_triage:
  outlook_triage_graph` (imported by `lg/lg_pregel/server.py`, ADR-2606280030).

  NOTE: the real classifier lives in the *external* `kotodama` package
  (`40-engine/kotoba/crates/kotoba-kotodama/py`, a separate west project that is
  NOT vendored into this app), so its internal topology is not reachable here.
  This twin preserves the registry entry + the actor containment shape: a single
  intelligence node confined to ONE step (1 run = 1 operation), behind an
  INJECTABLE seam (`*triage*`) that the deployment swaps for the Murakumo
  loopback classifier (ADR-2605215000). The load-bearing port for this app is the
  server dispatch surface (`lg-pregel.server`); the Python pod stays the deployed
  runtime and COEXISTS."
  (:require [langgraph.graph :as g]))

(def ^:dynamic *triage*
  "Injectable triage node. Default echoes the graph id + marks the run handled so
  the topology verifies offline; production rebinds to the Murakumo-loopback
  classifier + governor."
  (fn [state] (assoc state :graph "outlook_triage" :ok true)))

(defn node-triage [state] (*triage* state))

(defn build
  "Compile the outlook_triage StateGraph (START → triage → END)."
  []
  (-> (g/state-graph)
      (g/add-node :triage node-triage)
      (g/set-entry-point :triage)
      (g/set-finish-point :triage)
      (g/compile-graph)))

(def GRAPH (build))
