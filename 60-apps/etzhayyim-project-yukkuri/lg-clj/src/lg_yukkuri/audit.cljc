(ns lg-yukkuri.audit
  "Fire-and-forget BPMN `generic.audit.emit` shim — clj port of
  `lg/lg_yukkuri/audit.py` (ADR-2606280030).

  The Python posts to the in-cluster bpmn-dispatcher via httpx; here the emit is
  an INJECTABLE dynamic var (`*emit*`) defaulting to a no-op, exactly mirroring
  the Python `LG_AUDIT_DISABLED` path. The default HTTP emitter
  (`http-emit`) uses babashka.http-client + cheshire and is wired only when a
  dispatcher URL is configured. Audit is best-effort: failures are swallowed
  (the Python wraps the post in try/except and logs a warning)."
  (:require [clojure.string :as str]))

(def dispatcher-url
  (-> (or (System/getenv "BPMN_DISPATCHER_INTERNAL_URL")
          "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080")
      (str/replace #"/+$" "")))

(def internal-secret (str/trim (or (System/getenv "BPMN_DISPATCHER_INTERNAL_SECRET") "")))
(def audit-timeout-sec (Double/parseDouble (or (System/getenv "LG_AUDIT_TIMEOUT_SEC") "3.0")))
(def audit-disabled? (= "1" (or (System/getenv "LG_AUDIT_DISABLED") "0")))

(defn http-emit
  "Default real emitter: POST the ActivityStreams-ish payload to the
  bpmn-dispatcher `generic.audit.emit` XRPC. Best-effort; returns nil."
  [payload]
  (try
    (let [post     (requiring-resolve 'babashka.http-client/post)
          generate (requiring-resolve 'cheshire.core/generate-string)
          headers  (cond-> {"Content-Type" "application/json"}
                     (seq internal-secret) (assoc "x-internal-trust" internal-secret))]
      (post (str dispatcher-url "/xrpc/com.etzhayyim.generic.audit.emit")
            {:headers headers
             :timeout (long (* 1000 audit-timeout-sec))
             :body    (generate payload)})
      nil)
    (catch Exception _ nil)))

(def ^:dynamic *emit*
  "Injectable sink. Default = no-op unless an emitter is wired by deployment.
  Tests rebind this to capture audit events."
  (fn [_payload] nil))

(defn emit-audit-bg
  "Mirror of `audit.emit_audit_bg`: build the payload and hand it to `*emit*`
  fire-and-forget. No-op when LG_AUDIT_DISABLED. Always returns nil so audit
  nodes can `(emit-audit-bg ...)` then return {}."
  [{:keys [actor activity object-id object-type attributes]}]
  (when-not audit-disabled?
    (*emit* {:actor      actor
             :activity   activity
             :objectId   object-id
             :objectType object-type
             :attributes (or attributes {})}))
  nil)
