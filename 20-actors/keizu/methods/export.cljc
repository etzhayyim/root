(ns keizu.methods.export
  "export.cljc — 系図 (keizu) → kanae render payload. ADR-2606066000.
  1:1 Clojure port of `methods/export.py`.

  The manifest promise: 'keizu emits the relation/:money datoms kanae visualizes.' This is the
  outbound side of bridge.cljc: it maps keizu fiscal `:money` flows into kanae fundFlowEdge shape and
  packages the aggregate concentration into a JSON-safe render payload (Sankey/treemap-ready).

  Honest scope (G11 + G2): only kanae-representable FISCAL kinds are exported as fund flows
  (procurement / subsidy / grant / outlay). `:political-donation` is NOT a government fiscal flow,
  so it is excluded from the kanae payload and reported as a skip count (no silent drop). Offline,
  deterministic; no live publish (G8).

  House style: Python ':…' keyword strings stay strings; kw* / to-finite-double / to-json reused
  from the keizu.methods.weave sibling; string-keyed maps; pure fns. The Python __main__ demo is
  omitted (the analyze.cljc -main renders the kanae-render.json artifact)."
  (:require [clojure.string :as str]
            [keizu.methods.weave :as w]))

;; keizu money-kind → kanae fundFlowEdge flowType (inverse of bridge.KANAE-FLOW-TO-KIND for the
;; invertible fiscal kinds). political-donation is intentionally absent (not a govt fiscal flow).
(def KEIZU-KIND-TO-KANAE
  {"budget-outlay" "outlay"
   "subsidy" "subsidy"
   "grant" "grant"
   "procurement-award" "procurement"})

(defn- kw* [v] (#'w/kw* v))
(defn- to-finite-double [v id] (#'w/to-finite-double v id))

(defn to-kanae-flow
  "One keizu :money → one kanae fundFlowEdge. Raises if the kind is not a govt fiscal flow."
  [m]
  (let [kind (kw* (get m ":money/kind"))]
    (when-not (contains? KEIZU-KIND-TO-KANAE kind)
      (throw (ex-info (str "export: " (pr-str kind)
                           " is not a kanae fiscal flow (e.g. political-donation excluded)") {})))
    {"edgeId" (str "keizu:" (str (get m ":money/id" "?")))
     "flowType" (get KEIZU-KIND-TO-KANAE kind)
     "donor" (get m ":money/payer" "")
     "recipient" (get m ":money/payee" "")
     "amount" (to-finite-double (get m ":money/amount" 0.0) (get m ":money/id"))
     "currency" (get m ":money/currency" "")
     "asOf" (long (get m ":money/as-of" 0))
     "sources" (vec (get m ":money/sources" []))}))

(defn to-kanae-flows
  "All fiscal :money → kanae flows; non-fiscal kinds (political-donation) skipped + counted."
  [g]
  (let [[flows skipped]
        (reduce (fn [[fs sk] m]
                  (if (contains? KEIZU-KIND-TO-KANAE (kw* (get m ":money/kind")))
                    [(conj fs (to-kanae-flow m)) sk]
                    [fs (conj sk (get m ":money/id"))]))
                [[] []] (get g "money"))]
    {"flows" flows "skipped" skipped "skipped_count" (count skipped)}))

(defn render-payload
  "JSON-safe aggregate concentration for a kanae render (Sankey/treemap-ready). Tuples are
  flattened to [key value] pairs; no sets remain. Carries the mirror/non-adjudicating flags."
  [c]
  {"actor" "keizu"
   "isMirror" true
   "nonAdjudicating" true
   "counts" (into {} (map (fn [k] [k (get c k)])
                          ["node_count" "committee_count" "rel_count"
                           "money_count" "statement_count"]))
   "money_by_payee" (mapv vec (get-in c ["money_concentration" "shares"]))
   "money_by_payer" (mapv vec (get-in c ["payer_concentration" "shares"]))
   "money_hhi" {"payee" (get-in c ["money_concentration" "hhi"])
                "payer" (get-in c ["payer_concentration" "hhi"])}
   "by_jurisdiction" (get c "by_jurisdiction")
   "committee_cross_organ" (get c "committee_cross_organ")
   "cross_committee_seats" (get c "cross_committee_seats")
   "connector_seats" (get c "connector_seats")
   "revolving_door" (get c "revolving_door")
   "award_and_fund" (get c "award_and_fund")
   "statement_index" {"count" (get-in c ["statement_index" "count"])
                      "by_speaker" (mapv vec (get-in c ["statement_index" "by_speaker"]))
                      "by_topic" (get-in c ["statement_index" "by_topic"])}})

(defn- json-sorted
  "json.dumps(..., ensure_ascii=False, sort_keys=True) — recursively sort map keys, then reuse
  the weave to-json scalar/float repr."
  [v]
  (cond
    (map? v) (str "{" (str/join ", " (map (fn [[k val]]
                                            (str (#'w/json-str k) ": " (json-sorted val)))
                                          (sort-by key (seq v)))) "}")
    (sequential? v) (str "[" (str/join ", " (map json-sorted v)) "]")
    :else (w/to-json v)))

(defn render-json
  "The render payload as a JSON string (proves it is fully serializable)."
  [c]
  (json-sorted (render-payload c)))
