(ns lg-animeka.audit
  "Fire-and-forget BPMN `generic.audit.emit` shim — clj port of `audit.py`.

  The Python emits one OCEL event per node to bpmn-dispatcher's
  `com.etzhayyim.generic.audit.emit`. The dispatch is fire-and-forget: a
  failure to emit MUST NOT block the graph node (audit loss is logged, never
  raised — the LangGraph state checkpoint is the source of truth).

  Here `*emit*` is an injectable seam: the default is a no-op (audit disabled
  unless a dispatcher is wired), and a `default-http-emit` is provided that
  POSTs to the dispatcher via babashka.http-client when configured. Graph nodes
  call `emit-audit-bg!` exactly where the Python calls `emit_audit_bg(...)`."
  (:require [clojure.string :as str]))

(def dispatcher-url
  (-> (or #?(:clj (System/getenv "BPMN_DISPATCHER_INTERNAL_URL") :default nil)
          "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080")
      (str/replace #"/+$" "")))

(def internal-secret
  (str/trim (or #?(:clj (System/getenv "BPMN_DISPATCHER_INTERNAL_SECRET") :default nil) "")))

(def audit-timeout-sec
  #?(:clj (Double/parseDouble (or (System/getenv "LG_AUDIT_TIMEOUT_SEC") "3.0")) :default 3.0))

(def audit-disabled?
  (= "1" (or #?(:clj (System/getenv "LG_AUDIT_DISABLED") :default nil) "0")))

(defn default-http-emit
  "POST one OCEL event to the dispatcher. Never throws (parity with the Python
  try/except that only logs)."
  [{:keys [actor activity object-id object-type attributes]}]
  #?(:clj
     (try
       (let [post (requiring-resolve 'babashka.http-client/post)
             gen  (requiring-resolve 'cheshire.core/generate-string)]
         (post (str dispatcher-url "/xrpc/com.etzhayyim.generic.audit.emit")
               {:headers (cond-> {"Content-Type" "application/json"}
                           (seq internal-secret) (assoc "x-internal-trust" internal-secret))
                :timeout (long (* 1000 audit-timeout-sec))
                :body (gen {:actor actor :activity activity
                            :objectId object-id :objectType object-type
                            :attributes (or attributes {})})})
         nil)
       (catch Exception _ nil))
     :default nil))

;; Default seam = no-op (audit disabled unless a dispatcher emitter is injected).
;; Rebind to `default-http-emit` (or a stub in tests) to capture emissions.
(def ^:dynamic *emit* (fn [_event] nil))

(defn emit-audit-bg!
  "Fire-and-forget OCEL emission. Returns nil. Honours LG_AUDIT_DISABLED.
  Keyword args mirror the Python `emit_audit_bg(actor=,activity=,object_id=,
  object_type=,attributes=)`."
  [& {:keys [actor activity object-id object-type attributes]}]
  (when-not audit-disabled?
    (try (*emit* {:actor actor :activity activity :object-id object-id
                  :object-type object-type :attributes (or attributes {})})
         (catch #?(:clj Exception :default :default) _ nil)))
  nil)
