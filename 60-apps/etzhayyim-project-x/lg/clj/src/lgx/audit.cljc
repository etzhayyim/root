(ns lgx.audit
  "Fire-and-forget BPMN `generic.audit.emit` shim — clj port of `lg_x/audit.py`.

  Per the original (user choice 2026-05-08): keep the OCEL audit trail by
  dispatching `generic.audit.emit` to bpmn-dispatcher from each LangGraph node.
  Preserves `vertex_repo_commit` OCEL traces / process-mining dashboards / RACI
  evidence without re-implementing the OCEL schema.

  Port notes (ADR-2606280030 / #2612 httpx→bb):
    - httpx.AsyncClient → babashka.http-client (`http/post`)
    - JSON               → cheshire (`json/generate-string`)
    - asyncio.create_task fire-and-forget → `future` (best-effort, never blocks)

  The dispatch is fire-and-forget: a failure to emit MUST NOT block the node.
  Audit loss is logged (to *err*) but never raised."
  (:require [babashka.http-client :as http]
            [cheshire.core :as json]
            [clojure.string :as str]))

(defn- env [k default] (or (System/getenv k) default))

(def ^:private dispatcher-url
  (let [u (env "BPMN_DISPATCHER_INTERNAL_URL"
               "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080")]
    (if (str/ends-with? u "/") (subs u 0 (dec (count u))) u)))

(def ^:private internal-secret
  (str/trim (env "BPMN_DISPATCHER_INTERNAL_SECRET" "")))

(def ^:private audit-timeout-ms
  (long (* 1000 (Double/parseDouble (env "LG_AUDIT_TIMEOUT_SEC" "3.0")))))

(defn- audit-disabled? []
  (= "1" (env "LG_AUDIT_DISABLED" "0")))

(defn emit-audit
  "Send one OCEL event to BPMN dispatcher's `generic.audit.emit` (synchronous,
  best-effort). Failure is logged, never raised — the LangGraph state checkpoint
  is the source of truth for resumability."
  [{:keys [actor activity object-id object-type attributes]}]
  (when-not (audit-disabled?)
    (let [payload {:actor actor
                   :activity activity
                   :objectId object-id
                   :objectType object-type
                   :attributes (or attributes {})}
          headers (cond-> {"Content-Type" "application/json"}
                    (seq internal-secret) (assoc "x-internal-trust" internal-secret))
          url (str dispatcher-url "/xrpc/com.etzhayyim.generic.audit.emit")]
      (try
        (http/post url {:headers headers
                        :body (json/generate-string payload)
                        :timeout audit-timeout-ms
                        :throw false})
        nil
        (catch Exception exc
          (binding [*out* *err*]
            (println (str "audit.emit failed (non-fatal): " (.getMessage exc)
                          " | activity=" activity " id=" object-id)))
          nil)))))

(defn emit-audit-bg
  "Schedule `emit-audit` on a background thread without awaiting it (the clj
  analogue of asyncio.create_task). Returns the future."
  [m]
  (future (emit-audit m)))
