(ns tate.methods.datom-emit
  "tate 盾 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).
  1:1 Clojure port of `methods/datom_emit.py`.

  GROUND (durable, op :add) — the member's docs/notices (synthetic at R0) + the coded
  registries (clause patterns + procedures). DERIVED (transient, :bond/is-transient true)
  — clause flags + response-plan status, computed on READ, never stored as ground (G2).

  House style: data maps stay string-keyed; ':…' keyword strings stay strings; file I/O
  only behind #?(:clj …). The Python __main__ demo printer is omitted."
  (:require [clojure.string :as str]
            [tate.methods.terms-scan :as ts]
            [tate.methods.respond-plan :as rp]))

(def DOC-ATTRS [":doc/label" ":doc/jurisdiction" ":doc/context" ":doc/sourcing"])
(def NOTICE-ATTRS [":notice/label" ":notice/jurisdiction" ":notice/channel"
                   ":notice/claim-jpy" ":notice/claim-amount" ":notice/claim-currency"
                   ":notice/sourcing"])
(def CLAUSE-ATTRS [":clause/label" ":clause/jurisdiction" ":clause/context" ":clause/risk"
                   ":clause/anchor" ":clause/route" ":clause/verify-current-law"])
(def PROC-ATTRS [":proc/label" ":proc/jurisdiction" ":proc/verify-current-law"])

(defn- fmt-g
  "Python f-string `{v:g}` for floats — strip trailing zeros, like the general format."
  [v]
  (let [d (double v)]
    (if (== d (Math/rint d))
      (str (long d))
      (let [s (str d)] s))))

(defn- fmt [v]
  (cond
    (true? v) "true"
    (false? v) "false"
    (nil? v) "nil"
    (string? v) (if (str/starts-with? v ":")
                  v
                  (str "\"" (-> v (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")) "\""))
    (and (number? v) (not (integer? v))) (fmt-g v)
    :else (str v)))

(defn emit
  ([] (emit 1))
  ([tx]
   (let [[docs notices] (ts/load-docs)
         patterns (ts/load-patterns)
         procs (rp/load-procs)
         res (ts/scan docs patterns)
         ps (rp/plans notices procs)
         L (transient [])]
     (conj! L ";; tate 盾 — GENERATED kotoba Datom log (ADR-2606112301). DO NOT hand-edit.")
     (conj! L ";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
     (conj! L ";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (G2).")
     (conj! L "")
     (conj! L ";; ── GROUND: registries (disclosed shapes)")
     (doseq [p patterns, a CLAUSE-ATTRS]
       (when (contains? p a)
         (conj! L (str "[" (fmt (get p ":clause/id")) " " a " " (fmt (get p a)) " " tx " :add]"))))
     (doseq [p procs, a PROC-ATTRS]
       (when (contains? p a)
         (conj! L (str "[" (fmt (get p ":proc/id")) " " a " " (fmt (get p a)) " " tx " :add]"))))
     (conj! L "")
     (conj! L ";; ── GROUND: member docs/notices (synthetic at R0 — G1)")
     (doseq [d docs, a DOC-ATTRS]
       (when (contains? d a)
         (conj! L (str "[" (fmt (get d ":doc/id")) " " a " " (fmt (get d a)) " " tx " :add]"))))
     (doseq [n notices, a NOTICE-ATTRS]
       (when (contains? n a)
         (conj! L (str "[" (fmt (get n ":notice/id")) " " a " " (fmt (get n a)) " " tx " :add]"))))
     (conj! L "")
     (conj! L ";; ── DERIVED (transient — flags/plans computed on read, G2)")
     (doseq [[i f] (map-indexed vector (get res "flags"))]
       (let [eid (fmt (format "flag:%03d" i))]
         (conj! L (str "[" eid " :bond/is-transient true " tx " :add]"))
         (conj! L (str "[" eid " :tate/doc " (fmt (get f "doc")) " " tx " :add]"))
         (conj! L (str "[" eid " :tate/clause " (fmt (get f "clause")) " " tx " :add]"))
         (conj! L (str "[" eid " :tate/risk " (get f "risk") " " tx " :add]"))
         (conj! L (str "[" eid " :tate/route " (get f "route") " " tx " :add]"))))
     (doseq [p ps]
       (let [eid (fmt (str "plan:" (get p "notice")))]
         (conj! L (str "[" eid " :bond/is-transient true " tx " :add]"))
         (conj! L (str "[" eid " :tate/status " (get p "status") " " tx " :add]"))
         (conj! L (str "[" eid " :tate/options " (count (get p "options")) " " tx " :add]"))))
     (conj! L "")
     (conj! L (str ";; flags=" (count (get res "flags")) " plans=" (count ps)))
     (str (str/join "\n" (persistent! L)) "\n"))))
