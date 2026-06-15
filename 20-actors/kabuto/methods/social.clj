#!/usr/bin/env bb
;; Working Clojure port of methods/social.py (pure composer + Charter gate; live G11 leg is operator-only).
(ns kabuto.methods.social
  "kabuto 兜 — atproto-compatible social post composer + Charter-Rider gate (ADR-2606022000).

  Composes app.bsky.feed.post-shaped records from the company / supply-edge / intel-report graph.
  AGGREGATE-FIRST + non-adjudicating (G3/G4): post bodies state public facts + computed
  concentration only; every body passes a Charter Rider §2(a)-(h) deny-scan before it is eligible
  to publish. OUTWARD-GATED (G11): live publication (KABUTO_LIVE_POST=1 + KOTOBA_ENDPOINT +
  operator auth) is an operator-only leg — the clj port carries the pure composer + gate + dry-run;
  the live HTTP write stays out of the clj surface (no-server-key / no external I/O here).

  Run:  bb --classpath 20-actors 20-actors/kabuto/methods/social.clj [seed.edn] [--limit N]"
  (:require [kabuto.methods.kabuto-edn :as e]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))
(def actor-did "did:web:etzhayyim.com:actor:kabuto")

;; Minimal local Charter Rider §2(a)-(h) deny-scan (the canonical scanner is
;; etzhayyim_organism.sensors.charter_rider.scan(); this is a dependency-free stand-in).
(def ^:private charter-deny
  ["weapon design" "covert force" "how to attack" "where to cut"
   "child sexual" "non-consensual" "gore for" "ad network" "adsense"])

(defn charter-rider-clean
  "True iff `text` trips none of the Charter Rider §2 deny patterns (lower-cased substring)."
  [text]
  (let [t (str/lower-case text)]
    (not-any? #(str/includes? t %) charter-deny)))

(defn rkey [subject-id]
  (let [md (java.security.MessageDigest/getInstance "SHA-256")
        hx (apply str (map #(format "%02x" (bit-and % 0xff)) (.digest md (.getBytes (str subject-id) "UTF-8"))))]
    (str "kabuto-" (subs hx 0 13))))

(defn- now []
  (str (.format (java.time.format.DateTimeFormatter/ofPattern "yyyy-MM-dd'T'HH:mm:ss")
                (java.time.LocalDateTime/now (java.time.ZoneOffset/UTC)))
       ".000Z"))

(defn post-record [text langs]
  {"$type" "app.bsky.feed.post"
   "text" (subs text 0 (min 300 (count text)))
   "langs" (or (seq langs) ["en"])
   "createdAt" (now)})

(defn compose
  "Return a seq of [subject-id kind text] — aggregate-first, public-facts-only."
  [companies edges report-summary]
  (concat
   (when (and report-summary (seq report-summary))
     [["kabuto.report.supply-concentration" "intel-report"
       (str "kabuto 兜 supply-chain concentration map (aggregate-first, public record): "
            report-summary
            " — a redundancy/accountability map, not a target-list. #supplychain")]])
   (for [edge (take 8 (sort-by #(- (double (or (:supply.edge/criticality %) 0.0))) edges))]
     (let [s (:supply.edge/from edge) c (:supply.edge/to edge)
           sn (get-in companies [s :company/name] s)
           cn (get-in companies [c :company/name] c)
           commodity (str/replace (str (or (:supply.edge/commodity edge) :unknown)) #"^:" "")
           crit (:supply.edge/criticality edge)]
       [(:supply.edge/id edge) "supply-edge"
        (str "Disclosed supply dependency (public record): " cn " relies on " sn
             " for " commodity " (est. concentration " crit "). Diversify to build resilience. "
             "#supplychain #" commodity)]))))

(defn main [& argv]
  (let [args (vec argv)
        li (.indexOf args "--limit")
        limit (if (>= li 0) (Integer/parseInt (nth args (inc li))) 9)
        limit-val (when (>= li 0) (nth args (inc li)))
        seed (or (first (remove #(or (str/starts-with? % "--") (= % limit-val)) args))
                 (str (io/file (actor-root) "data" "seed-public-companies.kotoba.edn")))
        g (e/classify (e/load-edn seed))
        posts (compose (:companies g) (:edges g) "top jurisdictions (see intel-report)")]
    (println (str "kabuto.social: mode=DRY-RUN actor=" actor-did " (live posting is the G11 operator leg)"))
    (let [n (reduce (fn [n [sid _kind text]]
                      (if (>= n limit) n
                        (if-not (charter-rider-clean text)
                          (do (println (str "  [SKIP charter §2] " sid)) n)
                          (let [uri (str "at://" actor-did "/app.bsky.feed.post/" (rkey sid))]
                            (println (str "  [dry-run] " uri))
                            (inc n)))))
                    0 posts)]
      (println (format "kabuto.social: %d post(s) composed (dry-run); charter-scan applied to every body." n)))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
