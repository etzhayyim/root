(ns lg-organism.audit
  "Append-only audit ledger for the organism dispatcher.

  The Python server honours `LG_AUDIT_DISABLED` to switch the worker audit trail
  off in tests. This namespace provides the same toggle plus an in-memory
  append-only log (the actor `不変台帳` core: every commit/hold is recorded for
  traceability / data sovereignty). The default sink is in-process; production
  swaps `*sink*` for a kotoba-Datom-log appender. Disabled ⇒ a no-op so the live
  pod's behaviour is never altered by the twin."
  (:require [clojure.string :as str]))

(defn- env [k] #?(:clj (System/getenv k) :cljs nil))

(defn disabled?
  "True when LG_AUDIT_DISABLED is set to a truthy value (parity with server.py)."
  []
  (let [v (env "LG_AUDIT_DISABLED")]
    (boolean (and v (not (str/blank? v)) (not= "0" v) (not= "false" (str/lower-case v))))))

(def ^:private ledger (atom []))

(def ^:dynamic *sink*
  "Injectable audit appender. Default appends to the in-memory `ledger` atom.
  Rebind to a kotoba-Datom-log writer in production."
  (fn [entry] (swap! ledger conj entry)))

(defn record!
  "Append one audit entry {:assistant :input :status :ts}. No-op when disabled.
  Returns the entry (or nil when disabled)."
  [assistant input status]
  (when-not (disabled?)
    (let [entry {:assistant assistant
                 :input input
                 :status status
                 :ts #?(:clj (System/currentTimeMillis) :cljs (.now js/Date))}]
      (*sink* entry)
      entry)))

(defn entries [] @ledger)
(defn reset-ledger! [] (reset! ledger []))
