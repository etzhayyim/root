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
            #?(:clj [cheshire.core :as json])))

(def default-config {:url "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080"
                     :disabled? true :timeout-ms 3000 :secret ""})
(def ^:dynamic *config* default-config)
(def ^:dynamic *http-post* nil)

(defn dispatcher-url []
  (-> (:url *config*)
      str (str/replace #"/+$" "")))

(defn disabled? [] (boolean (:disabled? *config*)))

(defn audit-timeout-ms []
  (long (:timeout-ms *config*)))

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
       (let [secret (str/trim (:secret *config*))
             headers (cond-> {"Content-Type" "application/json"}
                       (seq secret) (assoc "x-internal-trust" secret))
             url (str (dispatcher-url) "/xrpc/com.etzhayyim.generic.audit.emit")]
         (try
           (when-not (fn? *http-post*)
             (throw (ex-info "media-gamers audit requires explicit HTTP" {})))
           (*http-post* url {:body (json/generate-string (audit-payload opts))
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
