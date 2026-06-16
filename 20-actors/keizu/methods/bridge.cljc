(ns keizu.methods.bridge
  "bridge.cljc — 系図 (keizu) cross-actor compose: danjo + kanae → keizu :rel/:money. ADR-2606066000.
  1:1 Clojure port of `methods/bridge.py`.

  keizu sits atop its siblings (CLAUDE.md): it can compose **danjo** cross-reference links and
  **kanae** fiscal-flow edges into its own relation graph. This bridge is a PURE mapping +
  validation step — offline only; live sibling ingest is G8-gated.

  The load-bearing property: every imported record is run through keizu's OWN gates
  (`weave/validate-rel` / `validate-money`), so a sibling CANNOT smuggle a charter violation into
  keizu. A danjo category that reads like a verdict, or a kanae edge with <2 sources, is REFUSED at
  the import boundary — defense in depth for G2 (non-adjudicating) and G3 (≥2 sources).

  House style: Python ':…' keyword strings stay strings; VERDICT-TOKENS / kw* / validate-* reused
  from the keizu.methods.weave sibling; string-keyed maps; pure fns. Omits the Python __main__ demo.

  Stdlib only."
  (:require [keizu.methods.weave :as w]))

;; kanae fundFlowEdge flow types → keizu money kinds (factual disclosed flows only).
(def KANAE-FLOW-TO-KIND
  {"appropriation" "budget-outlay"
   "outlay" "budget-outlay"
   "subaward" "subsidy"
   "subsidy" "subsidy"
   "grant" "grant"
   "aid" "grant"
   "transfer" "grant"
   "loan" "grant"
   "procurement" "procurement-award"
   "award" "procurement-award"})

;; danjo crossReferenceLink link types → keizu factual rel kinds. NOTE: danjo is itself
;; non-adjudicating, but the bridge re-asserts the gate (a verdict-ish category is refused).
(def DANJO-LINK-TO-KIND
  {"awardee-officer-ubo-link" "co-membership"
   "officer-edge" "co-membership"
   "appointment" "appointment"
   "advisory" "advisory-role"
   "revolving-door" "revolving-door"
   "donor-recipient" "funding-tie"
   "procurement-award" "procurement-award"
   "statement-attribution" "statement-attribution"})

(defn- kw* [v] (#'w/kw* v))

(defn- non-blank-sources [sources]
  (vec (filter #(seq (clojure.string/trim (str %))) (or sources []))))

(defn bridge-kanae-flow
  "kanae fundFlowEdge → validated keizu :money datom. Raises on an unknown flow type or a
  keizu-gate violation (G2/G3)."
  [edge]
  (let [flow (kw* (get edge "flowType" (get edge ":flowType" "")))]
    (when-not (contains? KANAE-FLOW-TO-KIND flow)
      (throw (ex-info (str "bridge: unknown kanae flowType " (pr-str flow)
                           " — refuse to guess (sourcing-honesty)") {})))
    (let [sources (non-blank-sources (or (get edge "sources") (get edge "sourceCids") []))
          m {":money/id" (str "kanae:" (str (get edge "id" (get edge "edgeId" "?"))))
             ":money/payer" (get edge "donor" (get edge "from" ""))
             ":money/payee" (get edge "recipient" (get edge "to" ""))
             ":money/kind" (str ":" (get KANAE-FLOW-TO-KIND flow))
             ":money/amount" (double (get edge "amount" 0.0))
             ":money/currency" (get edge "currency" "")
             ":money/as-of" (long (get edge "asOf" 0))
             ":money/sourcing" ":representative"   ;; an imported sibling record is representative (G11)
             ":money/sources" sources}]
      (w/validate-money m)   ;; keizu's own G2/G3 gate — the import cannot bypass it
      m)))

(defn bridge-danjo-crossref
  "danjo crossReferenceLink → validated keizu :rel datom. A verdict-bearing category is
  refused (G2 defense in depth); an under-sourced link is refused (G3)."
  [link]
  (let [raw-kind (kw* (get link "linkType" (get link "category" (get link "kind" ""))))]
    (when (some #(= % raw-kind) w/VERDICT-TOKENS)
      (throw (ex-info (str "bridge: danjo category " (pr-str raw-kind)
                           " is a verdict — refused at import (G2)") {})))
    (when-not (contains? DANJO-LINK-TO-KIND raw-kind)
      (throw (ex-info (str "bridge: unmapped danjo link type " (pr-str raw-kind)
                           " — refuse to guess") {})))
    (let [sources (non-blank-sources (or (get link "sourceRecordCids") (get link "sources") []))
          r {":rel/id" (str "danjo:" (str (get link "id" (get link "linkId" "?"))))
             ":rel/source" (get link "from" (get link "source" ""))
             ":rel/target" (get link "to" (get link "target" ""))
             ":rel/kind" (str ":" (get DANJO-LINK-TO-KIND raw-kind))
             ":rel/weight" (double (get link "weight" 1.0))
             ":rel/as-of" (long (get link "asOf" 0))
             ":rel/non-adjudicating-notice" true
             ":rel/sourcing" ":representative"
             ":rel/sources" sources}]
      (w/validate-rel r)     ;; keizu's own G2/G3 gate
      r)))

(defn bridge-batch
  "Compose a mixed sibling batch → keizu datoms. Each record validated; the whole batch
  fails if any record violates a keizu gate (no partial smuggling)."
  [batch]
  {"money" (mapv bridge-kanae-flow (get batch "kanae" []))
   "rels" (mapv bridge-danjo-crossref (get batch "danjo" []))})
