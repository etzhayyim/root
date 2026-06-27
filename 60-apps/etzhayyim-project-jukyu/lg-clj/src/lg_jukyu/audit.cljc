(ns lg-jukyu.audit
  "Fire-and-forget BPMN `generic.audit.emit` shim — clj port of
  `lg/lg_jukyu/audit.py` (ADR-2606280030).

  The Python version POSTs to the in-cluster bpmn-dispatcher as a detached
  asyncio task (best-effort, never fatal). This port keeps the audit edge
  INJECTABLE via `*audit-sink*` (default: no-op, parity with the fire-and-forget
  semantics) so graphs verify under bb without a dispatcher. Wiring the sink to
  a real dispatcher (babashka.http-client) is a deployment-layer concern — the
  Python pod remains the live audit emitter and COEXISTS."
  (:require [clojure.string :as str]))

(def app-did (or (System/getenv "JUKYU_APP_DID") "did:web:jukyu.etzhayyim.com"))
(def audit-disabled? (= "1" (System/getenv "LG_AUDIT_DISABLED")))

(def ^:dynamic *audit-sink*
  "Injectable audit sink. Default: no-op. Contract: (event-map) -> any.
  event-map = {:actor :activity :objectId :objectType :attributes}."
  (fn [_event] nil))

(defn emit-audit
  "Mirror of emit_audit_bg: build the BPMN event and hand it to `*audit-sink*`.
  Returns nil (fire-and-forget). Honours LG_AUDIT_DISABLED=1."
  [{:keys [actor activity object-id object-type attributes]}]
  (when-not audit-disabled?
    (try
      (*audit-sink* {:actor      (or actor app-did)
                     :activity   activity
                     :objectId   object-id
                     :objectType object-type
                     :attributes (or attributes {})})
      (catch Exception _ nil)))
  nil)

(defn default-http-sink
  "Optional real sink: POST `com.etzhayyim.generic.audit.emit` to the BPMN
  dispatcher (best-effort). Deployment layer may `(alter-var-root #'*audit-sink*
  (constantly (default-http-sink)))`."
  []
  (let [base    (-> (or (System/getenv "BPMN_DISPATCHER_INTERNAL_URL")
                        "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080")
                    (str/replace #"/+$" ""))
        secret  (some-> (System/getenv "BPMN_DISPATCHER_INTERNAL_SECRET") str/trim)
        timeout (long (* 1000 (Double/parseDouble (or (System/getenv "LG_AUDIT_TIMEOUT_SEC") "3.0"))))]
    (fn [event]
      (try
        (let [post     (requiring-resolve 'babashka.http-client/post)
              generate (requiring-resolve 'cheshire.core/generate-string)
              headers  (cond-> {"Content-Type" "application/json"}
                         (seq secret) (assoc "x-internal-trust" secret))]
          (post (str base "/xrpc/com.etzhayyim.generic.audit.emit")
                {:headers headers :timeout timeout :body (generate event)}))
        (catch Exception _ nil)))))
