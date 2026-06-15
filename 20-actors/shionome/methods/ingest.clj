#!/usr/bin/env bb
;; Working Clojure port of methods/ingest.py.
(ns shionome.methods.ingest
  "ingest.clj — 潮目 (shionome) offline public-source normalizer. ADR-2606072200.

  Normalizes batches of public market-data records (exchange data / fund-flow reports /
  central-bank releases / index providers) into shionome :bucket/:flow/:snap datoms. OFFLINE by
  default and REFUSES `--live` without the G8 gate (operator attestation + SHIONOME_ALLOW_LIVE=1)
  — the keizu/yadori/watari pattern.

  Every normalized record is run through the same weave.validate-* gates, so an under-sourced, a
  NaN-magnitude, or a TRADE/advisory-bearing input is refused here (トレードはしない), not silently
  ingested.

  Stdlib only.

  Run:  bb --classpath 20-actors 20-actors/shionome/methods/ingest.clj"
  (:require [shionome.methods.registry :as r]
            [shionome.methods.weave :as w]
            [clojure.string :as str]))

;; raw bucket fields that map to canonical :bucket/* attrs; anything else is carried through as
;; :bucket/<field> so the validate-bucket PII / rating scan (G1/G2/G4/G9) bites on the ingest path.
(def ^:private KNOWN-BUCKET-FIELDS
  #{"id" "scope" "label" "asset_class" "region" "risk" "sources" "sourcing" "sourceId"})

(defn- sourcing-raw
  "G11 — if the record names a registry sourceId, the REGISTRY'S verification status WINS
  (a caller cannot forge :authoritative for an unverified source). Else honor the caller's
  declared sourcing, defaulting to :representative."
  [raw]
  (if (seq (get raw "sourceId"))
    (r/sourcing-for (get raw "sourceId"))
    (str ":" (str/replace (str (get raw "sourcing" "representative")) #"^:+" ""))))

(defn normalize-bucket
  "Normalize a capital-bucket record → validated :bucket/* datom (raises on G1/G2/G4/G9).
  Extra raw fields are carried through so a smuggled PII / rating field is caught."
  [raw]
  (let [b (atom {":bucket/id"      (get raw "id")
                 ":bucket/scope"   (str ":" (str/replace (str (get raw "scope" "")) #"^:+" ""))
                 ":bucket/sourcing" (sourcing-raw raw)})]
    (doseq [k ["label" "asset_class" "region"]]
      (when (seq (str (get raw k "")))
        (swap! b assoc (str ":bucket/" (str/replace k "_" "-")) (get raw k))))
    (when (seq (str (get raw "risk" "")))
      (swap! b assoc ":bucket/risk" (str ":" (str/replace (str (get raw "risk")) #"^:+" ""))))
    (when (get raw "sources")
      (swap! b assoc ":bucket/sources"
             (vec (filter #(seq (str/trim (str %))) (get raw "sources")))))
    ;; carry through any extra fields so validate-bucket can catch PII / rating / signal / target
    (doseq [[k v] raw]
      (when-not (contains? KNOWN-BUCKET-FIELDS k)
        (swap! b assoc (str ":bucket/" k) v)))
    (w/validate-bucket @b)
    @b))

(defn normalize-flow
  "Normalize a capital-flow record → validated :flow/* datom (raises on a gate)."
  [raw]
  (let [f {":flow/id"            (get raw "id")
           ":flow/source"        (get raw "source" "external")
           ":flow/target"        (get raw "target" "external")
           ":flow/kind"          (str ":" (str/replace (str (get raw "kind")) #"^:+" ""))
           ":flow/magnitude"     (double (get raw "magnitude" 0.0))
           ":flow/unit"          (get raw "unit" "")
           ":flow/no-trade-notice" true
           ":flow/as-of"         (long (get raw "as_of" 0))
           ":flow/sourcing"      (sourcing-raw raw)
           ":flow/sources"       (vec (filter #(seq (str/trim (str %)))
                                              (get raw "sources" [])))}]
    (w/validate-flow f)
    f))

(defn normalize-snapshot
  "Normalize an observed bucket metric → validated :snap/* datom (raises on a gate)."
  [raw]
  (let [s {":snap/id"      (get raw "id")
           ":snap/bucket"  (get raw "bucket")
           ":snap/metric"  (str ":" (str/replace (str (get raw "metric")) #"^:+" ""))
           ":snap/value"   (double (get raw "value" 0.0))
           ":snap/as-of"   (long (get raw "as_of" 0))
           ":snap/sourcing" (sourcing-raw raw)
           ":snap/sources"  (vec (filter #(seq (str/trim (str %)))
                                         (get raw "sources" [])))}]
    (w/validate-snapshot s)
    s))

(defn normalize-batch
  "Normalize a mixed offline batch into shionome datoms. Each record validated."
  [batch]
  (let [out (atom {"buckets" [] "flows" [] "snapshots" []})]
    (doseq [b (get batch "buckets" [])]
      (swap! out update "buckets" conj (normalize-bucket b)))
    (doseq [f (get batch "flows" [])]
      (swap! out update "flows" conj (normalize-flow f)))
    (doseq [s (get batch "snapshots" [])]
      (swap! out update "snapshots" conj (normalize-snapshot s)))
    @out))

(defn ingest-live
  "G8 — live ingest from market-data sources is outward-gated. Refuses unless the operator
  gate is set AND an attestation DID is supplied (which still routes to Council Lv6+)."
  [& _args]
  (if (not= (System/getenv "SHIONOME_ALLOW_LIVE") "1")
    (throw (ex-info
            (str "shionome R0: live market-data ingest is Council Lv6+ + operator gated (G8). "
                 "Set SHIONOME_ALLOW_LIVE=1 + supply an operator attestation DID to proceed (still Council-gated).")
            {}))
    (throw (ex-info "shionome R0: live ingest path not wired — design-only (G8)." {}))))

(defn -main [& argv]
  (if (some #{"--live"} argv)
    (ingest-live)
    (let [sample {"buckets"   [{"id" "demo-eq" "scope" "asset-class" "label" "demo equities"
                                "asset_class" "equities" "region" "us" "risk" "risk"
                                "sources" ["https://www.sec.gov/"]}]
                  "flows"     [{"id" "demo-flow" "source" "external" "target" "demo-eq"
                                "kind" "fund-inflow" "magnitude" 1.5 "unit" "usd-bn" "as_of" 20260601
                                "sources" ["https://www.ici.org/research" "https://fred.stlouisfed.org/"]}]
                  "snapshots" [{"id" "demo-snap" "bucket" "demo-eq" "metric" "return-pct"
                                "value" 1.2 "as_of" 20260601 "sources" ["https://fred.stlouisfed.org/"]}]}
          out (normalize-batch sample)]
      (println (str "# shionome offline normalize — buckets=" (count (get out "buckets"))
                    " flows=" (count (get out "flows"))
                    " snapshots=" (count (get out "snapshots")) " (all validated)")))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
