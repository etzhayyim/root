#!/usr/bin/env bb
;; Working Clojure port of methods/bridge.py.
(ns keizu.methods.bridge
  "bridge.clj — 系図 (keizu) cross-actor compose: danjo + kanae → keizu :rel/:money. ADR-2606066000.

  keizu sits atop its siblings (CLAUDE.md): it can compose **danjo** cross-reference links and
  **kanae** fiscal-flow edges into its own relation graph. This bridge is a PURE mapping +
  validation step — offline only; live sibling ingest is G8-gated.

  The load-bearing property: every imported record is run through keizu's OWN gates
  (`weave/validate-rel` / `validate-money`), so a sibling CANNOT smuggle a charter violation into
  keizu. A danjo category that reads like a verdict, or a kanae edge with <2 sources, is REFUSED at
  the import boundary — defense in depth for G2 (non-adjudicating) and G3 (≥2 sources).

  Stdlib only.

  Run:  bb --classpath 20-actors 20-actors/keizu/methods/bridge.clj"
  (:require [keizu.methods.weave :as w]
            [clojure.string :as str]))

;; ── kw* (inlined from weave.cljc — the function is private there, so we replicate it here) ──
;; Mirrors weave.cljc's `kw*` exactly (which in turn mirrors weave.py's `_kw`):
;;   str(v or "").lstrip(":") → split("/")[-1].lower()
(defn- kw*
  "Normalize an edn keyword/string to a bare lowercase token (':rel/kind' → 'kind').
  Inlined mirror of weave.cljc `kw*` (private there). Do NOT modify independently."
  [v]
  (let [s (-> (str (or v "")) (str/replace #"^:+" ""))]
    (-> (last (str/split s #"/" -1)) (str/lower-case))))

;; kanae fundFlowEdge flow types → keizu money kinds (factual disclosed flows only).
(def KANAE-FLOW-TO-KIND
  {"appropriation" "budget-outlay"
   "outlay"        "budget-outlay"
   "subaward"      "subsidy"
   "subsidy"       "subsidy"
   "grant"         "grant"
   "aid"           "grant"
   "transfer"      "grant"
   "loan"          "grant"
   "procurement"   "procurement-award"
   "award"         "procurement-award"})

;; danjo crossReferenceLink link types → keizu factual rel kinds. NOTE: danjo is itself
;; non-adjudicating, but the bridge re-asserts the gate (a verdict-ish category is refused).
(def DANJO-LINK-TO-KIND
  {"awardee-officer-ubo-link" "co-membership"
   "officer-edge"             "co-membership"
   "appointment"              "appointment"
   "advisory"                 "advisory-role"
   "revolving-door"           "revolving-door"
   "donor-recipient"          "funding-tie"
   "procurement-award"        "procurement-award"
   "statement-attribution"    "statement-attribution"})

(defn bridge-kanae-flow
  "kanae fundFlowEdge → validated keizu :money datom. Raises on an unknown flow type or a
  keizu-gate violation (G2/G3)."
  [edge]
  (let [flow (kw* (get edge "flowType" (get edge ":flowType" "")))
        _ (when-not (contains? KANAE-FLOW-TO-KIND flow)
            (throw (ex-info (str "bridge: unknown kanae flowType " (pr-str flow)
                                 " — refuse to guess (sourcing-honesty)")
                            {:flow flow})))
        sources (vec (filter #(seq (str/trim (str %)))
                             (or (get edge "sources") (get edge "sourceCids") [])))
        m {":money/id"       (str "kanae:" (str (get edge "id" (get edge "edgeId" "?"))))
           ":money/payer"    (get edge "donor" (get edge "from" ""))
           ":money/payee"    (get edge "recipient" (get edge "to" ""))
           ":money/kind"     (str ":" (get KANAE-FLOW-TO-KIND flow))
           ":money/amount"   (double (get edge "amount" 0.0))
           ":money/currency" (get edge "currency" "")
           ":money/as-of"    (long (get edge "asOf" 0))
           ":money/sourcing" ":representative"   ; an imported sibling record is representative (G11)
           ":money/sources"  sources}]
    (w/validate-money m)   ; keizu's own G2/G3 gate — the import cannot bypass it
    m))

(defn bridge-danjo-crossref
  "danjo crossReferenceLink → validated keizu :rel datom. A verdict-bearing category is
  refused (G2 defense in depth); an under-sourced link is refused (G3)."
  [link]
  (let [raw-kind (kw* (get link "linkType" (get link "category" (get link "kind" ""))))]
    (when (some #(= raw-kind %) w/VERDICT-TOKENS)
      (throw (ex-info (str "bridge: danjo category " (pr-str raw-kind)
                           " is a verdict — refused at import (G2)")
                      {:kind raw-kind})))
    (when-not (contains? DANJO-LINK-TO-KIND raw-kind)
      (throw (ex-info (str "bridge: unmapped danjo link type " (pr-str raw-kind)
                           " — refuse to guess")
                      {:kind raw-kind})))
    (let [sources (vec (filter #(seq (str/trim (str %)))
                               (or (get link "sourceRecordCids") (get link "sources") [])))
          r {":rel/id"                   (str "danjo:" (str (get link "id" (get link "linkId" "?"))))
             ":rel/source"               (get link "from" (get link "source" ""))
             ":rel/target"               (get link "to" (get link "target" ""))
             ":rel/kind"                 (str ":" (get DANJO-LINK-TO-KIND raw-kind))
             ":rel/weight"               (double (get link "weight" 1.0))
             ":rel/as-of"                (long (get link "asOf" 0))
             ":rel/non-adjudicating-notice" true
             ":rel/sourcing"             ":representative"
             ":rel/sources"              sources}]
      (w/validate-rel r)     ; keizu's own G2/G3 gate
      r)))

(defn bridge-batch
  "Compose a mixed sibling batch → keizu datoms. Each record validated; the whole batch
  fails if any record violates a keizu gate (no partial smuggling)."
  [batch]
  (let [out (atom {"money" [] "rels" []})]
    (doseq [e (get batch "kanae" [])]
      (swap! out update "money" conj (bridge-kanae-flow e)))
    (doseq [l (get batch "danjo" [])]
      (swap! out update "rels" conj (bridge-danjo-crossref l)))
    @out))

(defn -main [& _argv]
  (let [demo {"kanae" [{"id" "f1" "flowType" "appropriation" "donor" "jp-mof" "payee" "jp-meti"
                         "recipient" "jp-meti" "amount" 1.0e9 "currency" "JPY" "asOf" 20250401
                         "sources" ["https://www.mof.go.jp/a" "https://www.mof.go.jp/b"]}]
               "danjo" [{"id" "x1" "linkType" "awardee-officer-ubo-link" "from" "jp-vendor-x"
                         "to" "jp-fsc-biz-1" "asOf" 20250215
                         "sourceRecordCids" ["cid:aaa" "cid:bbb"]}]}
        out  (bridge-batch demo)]
    (println (str "# keizu bridge — kanae→money=" (count (get out "money"))
                  " danjo→rels=" (count (get out "rels")) " (all validated)"))
    (doseq [m (get out "money")]
      (println (str "  money " (get m ":money/id") " " (get m ":money/kind") " " (get m ":money/amount"))))
    (doseq [r (get out "rels")]
      (println (str "  rel   " (get r ":rel/id") " " (get r ":rel/kind") " " (get r ":rel/source") " → " (get r ":rel/target"))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
