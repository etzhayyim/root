#!/usr/bin/env bb
;; Working Clojure port of methods/ingest.py.
(ns keizu.methods.ingest
  "ingest.clj — 系図 (keizu) offline public-source normalizer. ADR-2606066000.

  Normalizes batches of public-source records (官報 / 政治資金収支報告書 / 調達ポータル /
  Federal Register / USAspending / TED / OECD rosters) into keizu :node/:rel/:money/:committee
  datoms. OFFLINE by default and REFUSES `--live` without the G8 gate (operator attestation +
  KEIZU_ALLOW_LIVE=1) — the yadori/watari pattern.

  Every normalized record is run through the same weave.validate-* gates, so an under-sourced or
  verdict-bearing input is refused here, not silently ingested.

  Stdlib only.

  Run:  bb --classpath 20-actors 20-actors/keizu/methods/ingest.clj"
  (:require [keizu.methods.registry :as r]
            [keizu.methods.weave :as w]
            [clojure.string :as str]))

;; raw node fields that map to canonical :node/* attrs; anything else is carried through as
;; :node/<field> so the validate-node PII / power-score scan (G1/G4/G9) bites on the ingest path.
(def ^:private KNOWN-NODE-FIELDS
  #{"id" "scope" "label" "jurisdiction" "organ" "sources" "sourcing" "sourceId"})

(defn- sourcing-raw
  "G11 — if the record names a registry sourceId, the REGISTRY'S verification status WINS
  (a caller cannot forge :authoritative for an unverified source). Else honor the caller's
  declared sourcing, defaulting to :representative."
  [raw]
  (if (seq (str (get raw "sourceId" "")))
    (r/sourcing-for (get raw "sourceId"))
    (str ":" (str/replace (str (get raw "sourcing" "representative")) #"^:+" ""))))

(defn normalize-node
  "Normalize a public-seat record → validated :node/* datom (raises on G1/G4/G9). Extra raw
  fields are carried through so a smuggled PII / power-score field is caught, not silently dropped."
  [raw]
  (let [node (atom {":node/id"      (get raw "id")
                    ":node/scope"   (str ":" (str/replace (str (get raw "scope" "")) #"^:+" ""))
                    ":node/sourcing" (sourcing-raw raw)})]
    (doseq [k ["label" "jurisdiction" "organ"]]
      (when (seq (str (get raw k "")))
        (swap! node assoc (str ":node/" k) (get raw k))))
    (when (get raw "sources")
      (swap! node assoc ":node/sources"
             (vec (filter #(seq (str/trim (str %))) (get raw "sources")))))
    ;; carry through extra fields so validate-node catches PII/power-score keys
    (doseq [[k v] raw]
      (when-not (contains? KNOWN-NODE-FIELDS k)
        (swap! node assoc (str ":node/" k) v)))
    (w/validate-node @node)
    @node))

(defn normalize-committee
  "Normalize a public committee roster record → :committee/* datom (seats as node ids)."
  [raw]
  (let [committee {":committee/id"          (get raw "id")
                   ":committee/label"       (get raw "label" (get raw "id"))
                   ":committee/jurisdiction" (get raw "jurisdiction" "")
                   ":committee/organ"       (get raw "organ" "")
                   ":committee/members"     (vec (map str (get raw "members" [])))
                   ":committee/term-from"   (long (get raw "term_from" 0))
                   ":committee/sourcing"    (sourcing-raw raw)
                   ":committee/sources"     (vec (filter #(seq (str/trim (str %)))
                                                         (get raw "sources" [])))}]
    (w/validate-committee committee)   ; G1 members + G3 sources/deny + G11 sourcing
    committee))

(defn normalize-rel
  "Normalize a tie record → validated :rel/* datom (raises on a gate)."
  [raw]
  (let [rel {":rel/id"                   (get raw "id")
             ":rel/source"               (get raw "source")
             ":rel/target"               (get raw "target")
             ":rel/kind"                 (str ":" (str/replace (str (get raw "kind")) #"^:+" ""))
             ":rel/weight"               (double (get raw "weight" 1.0))
             ":rel/as-of"                (long (get raw "as_of" 0))
             ":rel/non-adjudicating-notice" true
             ":rel/sourcing"             (sourcing-raw raw)
             ":rel/sources"              (vec (filter #(seq (str/trim (str %)))
                                                      (get raw "sources" [])))}]
    (w/validate-rel rel)
    rel))

(defn normalize-money
  "Normalize a money-flow record → validated :money/* datom (raises on a gate)."
  [raw]
  (let [m {":money/id"       (get raw "id")
            ":money/payer"    (get raw "payer")
            ":money/payee"    (get raw "payee")
            ":money/kind"     (str ":" (str/replace (str (get raw "kind")) #"^:+" ""))
            ":money/amount"   (double (get raw "amount" 0.0))
            ":money/currency" (get raw "currency" "")
            ":money/as-of"    (long (get raw "as_of" 0))
            ":money/sourcing" (sourcing-raw raw)
            ":money/sources"  (vec (filter #(seq (str/trim (str %)))
                                           (get raw "sources" [])))}]
    (w/validate-money m)
    m))

(defn normalize-batch
  "Normalize a mixed offline batch into keizu datoms. Each record validated."
  [batch]
  (let [out (atom {"nodes" [] "committees" [] "rels" [] "money" []})]
    (doseq [n (get batch "nodes" [])]
      (swap! out update "nodes" conj (normalize-node n)))
    (doseq [c (get batch "committees" [])]
      (swap! out update "committees" conj (normalize-committee c)))
    (doseq [r (get batch "rels" [])]
      (swap! out update "rels" conj (normalize-rel r)))
    (doseq [m (get batch "money" [])]
      (swap! out update "money" conj (normalize-money m)))
    @out))

(defn ingest-live
  "G8 — live ingest from government portals is outward-gated. Refuses unless the operator
  gate is set AND an attestation DID is supplied (which still routes to Council Lv6+)."
  [& _args]
  (if (not= (System/getenv "KEIZU_ALLOW_LIVE") "1")
    (throw (ex-info
            (str "keizu R0: live public-source ingest is Council Lv6+ + operator gated (G8). "
                 "Set KEIZU_ALLOW_LIVE=1 + supply an operator attestation DID to proceed (still Council-gated).")
            {}))
    (throw (ex-info "keizu R0: live ingest path not wired — design-only (G8)." {}))))

(defn -main [& argv]
  (if (some #{"--live"} argv)
    (ingest-live)
    (let [sample {"committees" [{"id" "demo-committee" "label" "demo" "jurisdiction" "jp"
                                 "organ" "demo-ministry" "members" ["seat-1" "seat-2"]
                                 "term_from" 20250101 "sources" ["https://example.gov/"]}]
                  "rels"       [{"id" "demo-rel" "source" "seat-1" "target" "demo-committee"
                                 "kind" "committee-membership" "as_of" 20250101
                                 "sources" ["https://example.gov/a" "https://example.gov/b"]}]
                  "money"      [{"id" "demo-money" "payer" "demo-ministry" "payee" "seat-1"
                                 "kind" "procurement-award" "amount" 1.0e6 "currency" "JPY"
                                 "as_of" 20250101 "sources" ["https://example.gov/x" "https://example.gov/y"]}]}
          out (normalize-batch sample)]
      (println (str "# keizu offline normalize — committees=" (count (get out "committees"))
                    " rels=" (count (get out "rels"))
                    " money=" (count (get out "money")) " (all validated)")))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
