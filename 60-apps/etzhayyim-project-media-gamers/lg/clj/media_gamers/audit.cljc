(ns media-gamers.audit
  "Fire-and-forget OCEL audit shim — clj twin of audit.py's
  `emit_audit` / `emit_audit_bg`.

  Port notes:
    - httpx.AsyncClient → babashka.http-client.
    - asyncio.create_task (fire-and-forget) → a future (clj). The python
      contract is preserved: emit failure is logged-not-raised, audit loss is
      acceptable (the LangGraph checkpoint / kotoba Datom log is the source of
      truth for resumability).
    - LG_AUDIT_DISABLED=1 short-circuits, identical to python."
  (:require [clojure.string :as str]
            #?(:clj [babashka.http-client :as http])
            #?(:clj [cheshire.core :as json])))

(defn- getenv [k default]
  #?(:clj (or (System/getenv k) default) :default default))

(defn dispatcher-url []
  (-> (getenv "BPMN_DISPATCHER_INTERNAL_URL"
              "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080")
      str (str/replace #"/+$" "")))

(defn disabled? [] (= "1" (getenv "LG_AUDIT_DISABLED" "0")))

(defn audit-timeout-ms []
  #?(:clj (long (* 1000 (Double/parseDouble (getenv "LG_AUDIT_TIMEOUT_SEC" "3.0"))))
     :default 3000))

(defn audit-payload
  "Pure builder for the `generic.audit.emit` OCEL event body (testable without I/O)."
  [{:keys [actor activity object-id object-type attributes]}]
  {:actor actor
   :activity activity
   :objectId object-id
   :objectType object-type
   :attributes (or attributes {})})

#?(:clj
   (defn emit-audit
     "Port of `emit_audit` — POST one OCEL event; failure logged, never raised."
     [opts]
     (when-not (disabled?)
       (let [secret (str/trim (getenv "BPMN_DISPATCHER_INTERNAL_SECRET" ""))
             headers (cond-> {"Content-Type" "application/json"}
                       (seq secret) (assoc "x-internal-trust" secret))
             url (str (dispatcher-url) "/xrpc/com.etzhayyim.generic.audit.emit")]
         (try
           (http/post url {:body (json/generate-string (audit-payload opts))
                           :headers headers :timeout (audit-timeout-ms) :throw false})
           nil
           (catch Exception e
             (binding [*out* *err*]
               (println "audit.emit failed (non-fatal):" (str e)
                        "| activity=" (:activity opts) "id=" (:object-id opts)))
             nil))))))

#?(:clj
   (defn emit-audit-bg
     "Port of `emit_audit_bg` — schedule emit-audit on a background future."
     [opts]
     (future (emit-audit opts))))
