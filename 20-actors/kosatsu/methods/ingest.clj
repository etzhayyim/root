#!/usr/bin/env bb
;; Working Clojure port of methods/ingest.py.
(ns kosatsu.methods.ingest
  "ingest.clj — 高札 (kosatsu) offline designation membrane. ADR-2606072000.

  Normalizes an authority's PUBLIC designation export (a list of {asserter, subject, measure,
  program, status, posted_at, sources}) into validated `:designation/*` datoms ready for the
  kotoba Datom log. EVERY normalized record passes the same G1..G5/G10 gates as the seed
  (weave.validate-*), so a verdict measure, an asserter-less or etzhayyim-authored designation, a
  non-primary or under-sourced citation, or a missing attribution NOTICE is refused here too.

  `--live` is REFUSED without the G8 gate (Council Lv6+ + operator + member signature). At R0 this
  is an OFFLINE normalizer only: it reads a local JSON file and prints the datoms it WOULD assert.
  It never fetches a remote list and never writes to the log.

  Stdlib only. Deterministic.

  Run:  bb --classpath 20-actors 20-actors/kosatsu/methods/ingest.clj <designations.json>"
  (:require [kosatsu.methods.weave :as w]
            [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(defn- colon-prefix
  "Ensure value starts with ':'. Mirrors Python:
     rec['x'] if str(rec['x']).startswith(':') else ':' + rec['x']"
  [v]
  (let [s (str v)]
    (if (str/starts-with? s ":")
      s
      (str ":" s))))

(defn- colon-prefix-default
  "Same but with a default key and a fallback default value. Mirrors Python:
     rec.get(k, default) if str(rec.get(k, bare-default)).startswith(':') else ':' + rec.get(k, bare-default)
  bare-default is the raw string (without colon), default is what to pass through if present."
  [rec k bare-default]
  (let [raw (get rec k bare-default)]
    (let [s (str raw)]
      (if (str/starts-with? s ":")
        s
        (str ":" s)))))

(defn normalize-designation
  "Map a plain ingest record → a `:designation/*` datom, then VALIDATE it (raises on a gate).
  Port of normalize_designation(rec) in ingest.py."
  [rec]
  (let [d (cond-> {":designation/id"             (get rec "id")
                   ":designation/asserter"        (get rec "asserter")
                   ":designation/subject"         (get rec "subject")
                   ":designation/measure"         (colon-prefix (get rec "measure"))
                   ":designation/program"         (get rec "program" "(unspecified)")
                   ":designation/status"          (colon-prefix-default rec "status" "listed")
                   ":designation/posted-at"       (long (get rec "posted_at"))
                   ":designation/asserted-notice" true
                   ":designation/sourcing"        (colon-prefix-default rec "sourcing" "representative")
                   ":designation/sources"         (vec (get rec "sources" []))}
             ;; lifted_at only if present and non-null
             (and (contains? rec "lifted_at") (some? (get rec "lifted_at")))
             (assoc ":designation/lifted-at" (long (get rec "lifted_at"))))]
    (w/validate-designation d)
    d))

(defn normalize-authority
  "Map a plain ingest record → a `:authority/*` datom, then VALIDATE it (raises on a gate).
  Port of normalize_authority(rec) in ingest.py."
  [rec]
  (let [a {":authority/id"          (get rec "id")
            ":authority/kind"        (colon-prefix (get rec "kind"))
            ":authority/label"       (get rec "label" (get rec "id"))
            ":authority/jurisdiction" (get rec "jurisdiction" "?")
            ":authority/stance"      (get rec "stance")
            ":authority/sourcing"    (colon-prefix-default rec "sourcing" "representative")
            ":authority/sources"     (vec (get rec "sources" []))}]
    (w/validate-authority a)
    a))

(defn normalize-subject
  "Map a plain ingest record → a `:subject/*` datom, then VALIDATE it (raises on a gate).
  Port of normalize_subject(rec) in ingest.py."
  [rec]
  (let [s {":subject/id"           (get rec "id")
            ":subject/kind"         (colon-prefix (get rec "kind"))
            ":subject/label"        (get rec "label" (get rec "id"))
            ":subject/jurisdiction" (get rec "jurisdiction" "(rep)")
            ":subject/sourcing"     (colon-prefix-default rec "sourcing" "representative")}]
    (w/validate-subject s)
    s))

(defn ingest-file
  "Read a local JSON {authorities, subjects, designations}; normalize+validate each. Offline.
  Port of ingest_file(path) in ingest.py."
  [path]
  (let [raw (json/parse-string (slurp (io/file path)))
        out {"authorities"  (mapv normalize-authority  (get raw "authorities" []))
             "subjects"     (mapv normalize-subject    (get raw "subjects" []))
             "designations" (mapv normalize-designation (get raw "designations" []))}]
    out))

(defn -main [& argv]
  (let [args (vec argv)]
    (cond
      (some #{"--live"} args)
      (do
        (binding [*out* *err*]
          (println (str "REFUSED: live designation ingest is G8-gated (Council Lv6+ + operator + member "
                        "signature). kosatsu R0 is an OFFLINE normalizer only — pass a local JSON path.")))
        (System/exit 2))

      (< (count args) 1)
      (do
        (binding [*out* *err*]
          (println "usage: bb ingest.clj <designations.json>   (offline only; --live is refused)"))
        (System/exit 1))

      :else
      (let [out (ingest-file (first args))]
        (println (str "# normalized " (count (get out "authorities")) " authorities, "
                      (count (get out "subjects")) " subjects, "
                      (count (get out "designations")) " designations (offline, NOT written to the log)"))
        (doseq [d (get out "designations")]
          (println (str (get d ":designation/id") " " (get d ":designation/asserter")
                        " → " (get d ":designation/subject")
                        " " (get d ":designation/measure")
                        " " (get d ":designation/status"))))
        (System/exit 0)))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
