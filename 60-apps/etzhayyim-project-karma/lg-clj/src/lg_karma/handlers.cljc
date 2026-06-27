(ns lg-karma.handlers
  "lg-karma task-handler registry — the swap seam (actor injection boundary)
  for the 45 `kotodama.primitives.karma*` task handlers wrapped by `server.py`.

  Faithful clj port of the TASKS dict in `lg/lg_karma/server.py` (ADR-2606280030).

  DEVIATION (load-bearing, intentional): the Python `TASKS` dict binds each NSID
  to a NATIVE python primitive (`task_karma_*`) that talks IPFS / Filecoin / an
  EVM anchor contract / a zk verifier / a RisingWave (psycopg) ledger. None of
  those substrates are representable in a charter-clean clj twin:

    * RisingWave / psycopg is FORBIDDEN by the substrate boundary
      (state belongs on the kotoba Datom log, ADR-2605312345); and
    * IPFS / Filecoin / chain / zk are native side-effecting deps (no bb impl).

  So — exactly as the wave-1 actor-swap pattern prescribes — each handler is an
  INJECTABLE boundary fn. The default registry binds every task to `unwired`
  (returns a structured `{:unwired …}` stub, never throws), so the graphs and
  the whole dispatch surface (/runs, /xrpc, NSID map) load + invoke under bb
  with zero native deps. A deployment rebinds `*handlers*` (or swaps individual
  entries) to wire the real primitives — same shape as Store/Advisor injection
  in the three reference actors.

  The graph TOPOLOGY (START → execute → END), the NSID→graph map and the request
  dispatch are the load-bearing port; the primitive bodies stay in the deployed
  python runtime, which COEXISTS (py_removed=0)."
  (:require [clojure.string :as str]))

;; ── the 45 task names (last NSID segment), in `server.py` TASKS order ────────
;; full NSID = (str nsid-prefix name).  graph name = this `name` verbatim
;; (Python: nsid.rsplit(".", 1)[-1]).

(def nsid-prefix "com.etzhayyim.apps.karma.")

(def task-names
  ["inputValidate" "floorGate" "edgePersist" "organismDissolve" "witnessPersist"
   "ipfsFindUnpinned" "ipfsPinBatch" "atrepoFindUnlifted" "atrepoLiftBatch"
   "anchorComputeRoot" "anchorSubmitTx" "anchorBacklinkEdges" "ipfsVerifyRandom"
   "coverageSnapshot" "rebirthPrecheck" "rebirthForfeit" "rebirthSeverFollows"
   "rebirthWipeAgents" "rebirthEmerge"
   "agentEvaluate"
   "daoFindVoters" "daoOpenArbitration" "daoCastVote" "daoFinalize" "daoSweepExpired"
   "wbtBalanceGet" "wbtTransfer" "wbtForfeitToCommons"
   "witnessInviteFanOut" "witnessRespondToInvitation" "witnessSweepExpired"
   "zkRebirthVerify" "zkRebirthProofLookup"
   "filecoinProposeBatch" "filecoinRenewExpiring" "filecoinStatusGet"
   "organismSpawn" "organismTick" "organismTickBatch" "organismCheckpoint"
   "organismResume" "organismHarvest" "organismDissolveRuntime"
   "cohortFission" "cohortFissionScan"])

(defn nsid-for [name] (str nsid-prefix name))

;; ── default boundary: every native primitive is "unwired" ───────────────────

(defn unwired
  "Default handler for an un-injected native primitive. Takes the kwargs map and
  returns a structured stub (never throws) so the graph resolves to a `:result`
  rather than an `:error`. Deployment swaps this for the real primitive."
  [name]
  (fn [input]
    {:unwired name
     :note (str "native kotodama primitive '" name "' not wired in the clj twin "
                "(substrate boundary: IPFS/Filecoin/chain/zk/RisingWave) — inject "
                "via lg-karma.handlers/*handlers*")
     :echo input}))

(def default-handlers
  "graph-name → handler fn. Default = unwired stub for all 45 tasks."
  (into {} (map (fn [n] [n (unwired n)])) task-names))

(def ^:dynamic *handlers*
  "The active handler registry — rebind (or merge a real primitive in) to swap."
  default-handlers)

(defn handler-for
  "Resolve the active handler for a graph name (nil if unknown)."
  [name]
  (get *handlers* name))

(defn clip [s n] (let [s (str s)] (subs s 0 (min (long n) (count s)))))

(defn unwired?
  "True when `result` is the structured unwired stub (helps tests/ops detect a
  not-yet-injected primitive without inspecting strings)."
  [result]
  (and (map? result) (contains? result :unwired)))

(defn ensure-str [x] (if (string? x) x (str x)))
(defn blank-name? [n] (str/blank? (ensure-str n)))
