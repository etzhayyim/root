(ns lg-webmk.audit
  "Fire-and-forget BPMN generic.audit.emit shim (clj port of audit.py).

  httpx → babashka.http-client; JSON → cheshire. The POST is best-effort:
  any failure is logged and swallowed (non-fatal), exactly like the Python.
  Honors LG_AUDIT_DISABLED=1 (the test harness sets it)."
  (:require [cheshire.core :as json]
            [babashka.http-client :as http]))

(defn- env [k default] (or (System/getenv k) default))

(def ^:private dispatcher-url
  (let [u (env "BPMN_DISPATCHER_INTERNAL_URL"
               "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080")]
    (if (clojure.string/ends-with? u "/") (subs u 0 (dec (count u))) u)))

(def ^:private internal-secret
  (clojure.string/trim (env "BPMN_DISPATCHER_INTERNAL_SECRET" "")))

(def ^:private audit-timeout-ms
  (long (* 1000 (Double/parseDouble (env "LG_AUDIT_TIMEOUT_SEC" "3.0")))))

(defn audit-disabled? []
  (= "1" (env "LG_AUDIT_DISABLED" "0")))

(defn emit-audit!
  "Synchronous best-effort emit. Returns nil. Never throws."
  [{:keys [actor activity object-id object-type attributes]}]
  (when-not (audit-disabled?)
    (try
      (let [payload {:actor actor :activity activity :objectId object-id
                     :objectType object-type :attributes (or attributes {})}
            headers (cond-> {"Content-Type" "application/json"}
                      (seq internal-secret) (assoc "x-internal-trust" internal-secret))]
        (http/post (str dispatcher-url "/xrpc/com.etzhayyim.generic.audit.emit")
                   {:headers headers
                    :body (json/generate-string payload)
                    :timeout audit-timeout-ms
                    :throw false}))
      (catch Exception e
        (binding [*out* *err*]
          (println "audit.emit failed (non-fatal):" (.getMessage e) "| activity=" activity))))
    nil))

(defn emit-audit-bg
  "Fire-and-forget: schedules emit-audit! on a future (asyncio.create_task analogue)."
  [m]
  (future (emit-audit! m)))
