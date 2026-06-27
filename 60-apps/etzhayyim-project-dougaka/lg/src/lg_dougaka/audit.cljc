(ns lg-dougaka.audit
  "Fire-and-forget BPMN `generic.audit.emit` shim — clj twin of lg_dougaka/audit.py
  (ADR-2606280030). httpx → babashka.http-client, JSON → cheshire.

  Behaviour is faithful to the Python original:
    - LG_AUDIT_DISABLED=1 → no-op
    - POST {dispatcher}/xrpc/com.etzhayyim.generic.audit.emit with the OCEL payload
    - x-internal-trust header set only when BPMN_DISPATCHER_INTERNAL_SECRET is present
    - any failure is non-fatal (logged, swallowed)"
  (:require [babashka.http-client :as http]
            [cheshire.core :as json]
            [clojure.string :as str]))

(defn- env [k default] (or (System/getenv k) default))

(defn- dispatcher-url []
  (-> (env "BPMN_DISPATCHER_INTERNAL_URL"
           "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080")
      (str/replace #"/+$" "")))

(defn- internal-secret [] (some-> (System/getenv "BPMN_DISPATCHER_INTERNAL_SECRET")
                                  str/trim))

(defn- timeout-ms []
  (long (* 1000 (Double/parseDouble (env "LG_AUDIT_TIMEOUT_SEC" "3.0")))))

(defn- disabled? [] (= "1" (System/getenv "LG_AUDIT_DISABLED")))

(defn emit-audit
  "Synchronous best-effort emit (non-fatal). opts:
   {:actor :activity :object-id :object-type :attributes}."
  [{:keys [actor activity object-id object-type attributes]}]
  (when-not (disabled?)
    (let [payload {:actor actor
                   :activity activity
                   :objectId object-id
                   :objectType object-type
                   :attributes (or attributes {})}
          secret (internal-secret)
          headers (cond-> {"Content-Type" "application/json"}
                    (seq secret) (assoc "x-internal-trust" secret))
          url (str (dispatcher-url) "/xrpc/com.etzhayyim.generic.audit.emit")]
      (try
        (http/post url {:headers headers
                        :body (json/generate-string payload)
                        :timeout (timeout-ms)})
        nil
        (catch Exception e
          (binding [*out* *err*]
            (println (str "audit.emit failed (non-fatal): " (.getMessage e)
                          " | activity=" activity " id=" object-id)))
          nil)))))

(defn emit-audit-bg
  "Fire-and-forget variant — emit on a future so the caller never blocks
  (mirrors the Python asyncio.create_task background emit). Returns the future."
  [opts]
  (future (emit-audit opts)))
