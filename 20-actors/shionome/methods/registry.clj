#!/usr/bin/env bb
;; Working Clojure port of methods/registry.py.
(ns shionome.methods.registry
  "registry.clj — 潮目 (shionome) public-source registry access. ADR-2606072200.

  Loads registry/sources.seed.json and exposes the source catalog to the ingest path:
    - load-registry / source-ids
    - get-source(source-id) — throws ex-info if absent (mirrors Python KeyError)
    - sourcing-for(source-id) — G11 honesty DRIVEN BY the registry: a record from a VERIFIED
      source may be :authoritative; from an unverified-seed source it stays :representative.
      An unknown source id is treated conservatively as :representative (never auto-authoritative).
    - assert-source-allowed — Charter Rider §2(e)/N5 commercial market-data deny-list as a
      reusable RUNTIME guard (mirrors the SOURCE_DENY check baked into weave's validate-flow/
      validate-snapshot).

  Reuses shionome.methods.weave/SOURCE-DENY and shionome.methods.weave/source-denied (both
  public `def`/`defn` in weave.cljc — no inline needed).

  Run:  bb --classpath 20-actors 20-actors/shionome/methods/registry.clj"
  (:require [shionome.methods.weave :as w]
            [cheshire.core :as json]
            [clojure.java.io :as io]))

;; ── path resolution (mirrors registry.py: parents[1] / "registry" / "sources.seed.json") ──
(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

(def ^:private REG-PATH
  (delay (io/file (actor-root) "registry" "sources.seed.json")))

;; ── load / lookup ────────────────────────────────────────────────────────────────

(defn load-registry
  "Read and parse registry/sources.seed.json (JSON). Accepts an optional path string/File.
  Mirrors registry.py load_registry(path)."
  ([] (load-registry (str @REG-PATH)))
  ([path]
   (json/parse-string (slurp path))))

(defn source-ids
  "Return the list of sourceId strings from the registry.
  Mirrors registry.py source_ids()."
  []
  (mapv #(get % "sourceId") (get (load-registry) "sources")))

(defn get-source
  "Return the source record map for source-id, or throw ex-info if absent.
  Mirrors registry.py get_source(source_id) — KeyError becomes ex-info."
  [source-id]
  (or (first (filter #(= (get % "sourceId") source-id)
                     (get (load-registry) "sources")))
      (throw (ex-info (str "no such source " (pr-str source-id)) {:source-id source-id}))))

(defn sourcing-for
  "G11 — :authoritative only when the registry marks the source verified; else :representative.
  An unknown source id is treated conservatively as :representative (never auto-authoritative).
  Mirrors registry.py sourcing_for(source_id)."
  [source-id]
  (try
    (let [status (get (get-source source-id) "verificationStatus" "")]
      (if (= status "verified") ":authoritative" ":representative"))
    (catch clojure.lang.ExceptionInfo _
      ":representative")))

(defn assert-source-allowed
  "Charter Rider §2(e)/N5 — raise if any text cites a commercial market-data terminal.
  Reusable runtime guard (mirror of the SOURCE_DENY check baked into weave's
  validate-flow/validate-snapshot). Mirrors registry.py assert_source_allowed(*texts).
  Uses weave/source-denied (public in weave.cljc) which returns \"\" if clean or the
  offending token if prohibited."
  [& texts]
  (let [d (w/source-denied (vec texts))]
    (when (seq d)
      (throw (ex-info (str "Rider §2(e)/N5: " (pr-str d)
                           " is a prohibited commercial market-data terminal")
                      {:denied d})))))

(defn -main [& _argv]
  (println (str "shionome registry: " (count (source-ids)) " sources loaded"))
  (println (str "  sourcing us-fred → " (sourcing-for "us-fred")))
  (println (str "  sourcing unknown → " (sourcing-for "no-such-source"))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
