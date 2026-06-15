#!/usr/bin/env bb
;; Working Clojure port of methods/social.py.
(ns kosatsu.methods.social
  "social.clj — 高札 (kosatsu) DRY-RUN social posts. ADR-2606072000.

  Projects the aggregate divergence/agreement findings into member-signable, NON-adjudicating
  dry-run posts. G8: status is always ':dry-run' (never published; outward-gated). G9: every
  post opens with the mirror/competing-claim disclaimer and never speaks AS an authority.
  G7: the server never signs — a real post requires a member signature (server-held-key false).
  G2: a post reports who-designated-whom + disagreement, never a verdict.

  Reuses weave.cljc public fns:
    w/report         — full aggregate report (agreement_index / divergence / ...)
    w/agreement-index — contested/unanimous/single_asserter counts + contested_ratio
    w/divergence-all  — per-subject divergence, contested-first

  Stdlib only. Deterministic.
  Run:  bb --classpath 20-actors 20-actors/kosatsu/methods/social.clj"
  (:require [kosatsu.methods.weave :as w]
            [kosatsu.methods.edn :as e]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

(def MIRROR_PREFIX
  "[mirror · not a verdict] kosatsu reports, attributed, what public authorities themselves posted; a designation is asserter-relative. ")

;; ── Python list string representation ────────────────────────────────────────

(defn- py-str-list
  "Render a Clojure vector as Python's str(list) output.
  e.g. ['eu-council', 'us-ofac'] — single-quoted items, comma-space separated."
  [v]
  (str "[" (str/join ", " (map #(str "'" % "'") v)) "]"))

(defn- list-or-dash
  "Replicate Python's `d['key'] or '—'` semantics:
  if the list is empty (falsey in Python), return '—'; otherwise return py-str-list."
  [v]
  (if (seq v) (py-str-list v) "—"))

;; ── _post ────────────────────────────────────────────────────────────────────

(defn -post
  "Build a dry-run networkPost record. The structural fields are const-locked (G2/G7/G8/G9).
  Raises if sources < 2 (G3)."
  [post-id subject body sources]
  (when (< (count sources) 2)
    (throw (ex-info "G3: a post needs ≥2 primary-source citations" {})))
  {":post/id"                  post-id
   ":post/subject"             subject
   ":post/body"                (str MIRROR_PREFIX body)
   ":post/status"              ":dry-run"          ;; G8 — never :published at R0
   ":post/is-mirror"           true                ;; G9
   ":post/non-adjudicating-notice" true            ;; G2
   ":post/server-held-key"     false               ;; G7 — member signs, not the server
   ":post/sources"             sources})

;; ── posts ────────────────────────────────────────────────────────────────────

(defn posts
  "Build dry-run networkPost records from the woven graph:
  1. A summary post (agreement_index counts).
  2. One post per CONTESTED subject (non-contested subjects are skipped).
  Deterministic — divergence-all is contested-first."
  ([g] (posts g nil))
  ([g ts]
   (let [r  (w/report g ts)
         ai (get r "agreement_index")
         summary (-post
                  "post-summary"
                  "designation divergence summary"
                  (str "Across " (get ai "designated_subjects") " designated subjects: "
                       (get ai "contested") " contested "
                       "(jurisdictions disagree), " (get ai "unanimous") " unanimous, "
                       (get ai "single_asserter") " single-asserter. "
                       "Contested-ratio " (get ai "contested_ratio") ".")
                  ["https://ofac.treasury.gov/" "https://www.sanctionsmap.eu/"])
         contested-posts
         (reduce
          (fn [acc d]
            (if (not= (get d "class") "contested")
              acc
              (conj acc
                    (-post
                     (str "post-" (get d "subject"))
                     (str (get d "subject") " — contested designation")
                     (str (get d "subject") ": listed by " (py-str-list (get d "listing"))
                          "; delisted by " (list-or-dash (get d "delisted"))
                          "; no designation from " (list-or-dash (get d "silent"))
                          ". The same subject is treated differently "
                          "across jurisdictions — that divergence is the fact, not a verdict.")
                     ["https://ofac.treasury.gov/" "https://www.sanctionsmap.eu/"]))))
          []
          (w/divergence-all g ts))]
     (vec (concat [summary] contested-posts)))))

;; ── main ────────────────────────────────────────────────────────────────────

(defn main [& _argv]
  (let [seed (e/load-edn (io/file (actor-root) "data" "seed-designation-graph.kotoba.edn"))
        g    (w/weave seed)]
    (doseq [p (posts g)]
      (println (str "[" (-> (get p ":post/status") (str/replace #"^:" "")) "] "
                    (get p ":post/subject") "\n  " (get p ":post/body") "\n")))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
