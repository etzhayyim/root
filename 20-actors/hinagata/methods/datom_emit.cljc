(ns hinagata.methods.datom-emit
  "hinagata 雛形 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).
  1:1 Clojure port of `methods/datom_emit.py` (ADR-2606111954).

  Projects the legal-template-commons graph into append-only kotoba Datoms [e a v tx op] — the
  first-class canonical state. GROUND (op :add, durable) = one datom per (entity, attribute,
  value) for nodes + :en/* 縁. DERIVED (:bond/is-transient) = edge-primary integrals computed
  on read (N1/G2), emitted in a clearly-flagged transient block.

  G1: a COMMONS of public openly-licensed templates — never advice; statute links are DISCLOSED
  structural facts, never verdicts (N3).

  House style: ':…' strings stay strings; pure fns; file I/O only behind #?(:clj …). Requires
  the good analyze.cljc sibling (load-file*/analyze) at the CLI edge. Python `__main__` writer
  is behind #?(:clj …)."
  (:require [clojure.string :as str]))

;; attributes promoted from each node/edge map into ground datoms (stable order = determinism)
(def node-attrs
  [":lt/kind" ":lt/label" ":lt/sourcing" ":lt/links"
   ":template/title" ":template/lang" ":template/license" ":template/version"
   ":template/stance" ":template/body-cid"
   ":clause/role" ":clause/optionality"
   ":statute/citation" ":statute/instrument" ":statute/jurisdiction" ":statute/url"
   ":jurisdiction/code" ":jurisdiction/system"
   ":concept/code" ":license/spdx"])

(def edge-attrs
  [":en/from" ":en/to" ":en/kind" ":en/binding-load" ":en/force" ":en/sourcing"])

(defn- fmt-g
  "Python `f\"{v:g}\"` for a float: up to 6 significant digits, trailing zeros stripped, and
  exponent form for very small/large magnitudes — matched here for the values this emitter
  sees (binding-loads in [0,1] and groundedness integrals)."
  [^double v]
  (cond
    (zero? v) "0"
    :else
    (let [s (String/format java.util.Locale/ROOT "%.6g" (object-array [v]))
          ;; strip trailing zeros in the fractional/mantissa part like %g does
          s (if (str/includes? s "e")
              (let [[mant exp] (str/split s #"e")
                    mant (if (str/includes? mant ".")
                           (str/replace (str/replace mant #"0+$" "") #"\.$" "")
                           mant)
                    ;; normalize exponent: %g gives e+NN / e-NN; python g gives e-05 etc.
                    exp (let [sign (subs exp 0 1)
                              digits (str/replace (subs exp 1) #"^0+(?=\d)" "")
                              digits (if (< (count digits) 2) (str "0" digits) digits)]
                          (str sign digits))]
                (str mant "e" exp))
              (if (str/includes? s ".")
                (str/replace (str/replace s #"0+$" "") #"\.$" "")
                s))]
      s)))

(defn- fmt
  "Port of _fmt(v): bool/nil literals, ':' strings raw, other strings JSON-quoted, floats %g."
  [v]
  (cond
    (true? v) "true"
    (false? v) "false"
    (nil? v) "nil"
    (string? v) (if (str/starts-with? v ":")
                  v
                  (str "\"" (-> v (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")) "\""))
    (and (number? v) (not (integer? v))) (fmt-g (double v))
    :else (str v)))

(defn emit
  "Port of emit(nodes, edges, res, tx). Returns the EDN datom-log text. `nodes` must iterate in
  EDN read order (use analyze/node-vals-style ordering); pass an ordered seq of [id node] pairs
  as `node-pairs` to guarantee determinism."
  ([node-pairs edges res] (emit node-pairs edges res 1))
  ([node-pairs edges res tx]
   (let [L (transient [])
         P (fn [s] (conj! L s))]
     (P ";; hinagata 雛形 — GENERATED kotoba Datom log (ADR-2606111954). DO NOT hand-edit.")
     (P ";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
     (P ";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (N1/G2).")
     (P ";; G1: a COMMONS of public openly-licensed templates — never advice; statute links")
     (P ";; are DISCLOSED structural facts (this clause cites this article), never verdicts (N3).")
     (P "[")

     ;; ── GROUND: node datoms (insertion order)
     (doseq [[nid n] node-pairs]
       (doseq [a node-attrs]
         (when (and (contains? n a) (some? (get n a)))
           (P (str "[" (fmt nid) " " a " " (fmt (get n a)) " " tx " :add]")))))

     ;; ── GROUND: edge datoms
     (doseq [e edges]
       (let [eid (str "en." (get e ":en/from") "."
                      (str/replace (str (get e ":en/kind")) #"^:" "") "."
                      (get e ":en/to"))]
         (doseq [a edge-attrs]
           (when (and (contains? e a) (some? (get e a)))
             (P (str "[" (fmt eid) " " a " " (fmt (get e a)) " " tx " :add]"))))))

     ;; ── DERIVED (transient — NOT persisted; N1/G2)
     (P ";; ── DERIVED readouts (transient; integral of incident 縁, computed on read) ──")
     (letfn [(ranked [m] (sort-by (fn [[nid v]] [(- (double v)) nid]) m))]
       (doseq [[nid v] (ranked (get res "grounded"))]
         (P (str "[" (fmt nid) " :bond/groundedness " (fmt-g (double v)) " " tx " :derived] ;; :bond/is-transient true")))
       (doseq [[nid v] (ranked (get res "reuse"))]
         (P (str "[" (fmt nid) " :bond/reusability " (fmt-g (double v)) " " tx " :derived] ;; :bond/is-transient true")))
       (doseq [[nid v] (ranked (get res "statute_pull"))]
         (P (str "[" (fmt nid) " :bond/statute-pull " (fmt-g (double v)) " " tx " :derived] ;; :bond/is-transient true"))))

     (P "]")
     (str (str/join "\n" (persistent! L)) "\n"))))

#?(:clj
   (defn -main
     "CLI entry: emit the kotoba Datom log for a seed EDN graph (file I/O at the edge)."
     [& argv]
     (let [argv (vec argv)
           load-file* (requiring-resolve 'hinagata.methods.analyze/load-file*)
           analyze (requiring-resolve 'hinagata.methods.analyze/analyze)
           node-vals (requiring-resolve 'hinagata.methods.analyze/node-vals)
           here (-> *file* clojure.java.io/file .getParentFile .getParentFile)
           seed (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                  (clojure.java.io/file (first argv))
                  (clojure.java.io/file here "data" "seed-legal-template-graph.kotoba.edn"))
           outdir (if (some #{"--out"} argv)
                    (clojure.java.io/file (nth argv (inc (.indexOf argv "--out"))))
                    (clojure.java.io/file here "out"))
           tx (if (some #{"--tx"} argv) (Long/parseLong (nth argv (inc (.indexOf argv "--tx")))) 1)
           {:keys [nodes edges]} (load-file* seed)
           res (analyze nodes edges)
           node-pairs (mapv (fn [n] [(get n ":lt/id") n]) (node-vals nodes))]
       (.mkdirs outdir)
       (spit (clojure.java.io/file outdir "legal-template-datoms.kotoba.edn")
             (emit node-pairs edges res tx))
       (println (str "hinagata datom log → "
                     (clojure.java.io/file outdir "legal-template-datoms.kotoba.edn")
                     " (" (count nodes) " nodes + " (count edges) " 縁, tx=" tx ")"))
       0)))
