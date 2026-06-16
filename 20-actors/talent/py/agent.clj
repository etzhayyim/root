#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (talent privacy-first talent/profile actor).
(ns talent.py.agent
  "talent — kotoba-native cohort-first talent registry langgraph actor (kotoba WASM cell).

  ADR-2606072600. Replaces the legacy RisingWave-backed registry with self-sovereign,
  hard-deletable profiles + k-anonymous cohort stats on the kotoba Datom log.

  Hard invariants structurally unrepresentable:
    G1 self-sovereign    — a profile write requires caller DID == subject DID.
    G3 signal-e2e        — identifying fields must be 'signal:v1:{ciphertext}'.
    G2 k-anonymity       — a cohort below k members is suppressed.
    G4 hard-delete       — forget_self removes the Datom; no soft-delete flag.

  Run:  bb --classpath 20-actors 20-actors/talent/py/agent.clj")

;; ── constants ──────────────────────────────────────────────────────────────────

(def IDENTIFYING_FIELDS
  ["fullName" "email" "phone" "address" "dateOfBirth" "governmentId"])

(def ENC_PREFIX "signal:v1:")

(def ALLOWED_ENRICHMENT
  #{"orcid" "github-public" "public-credential-registry"})

(def PROHIBITED_SOURCES
  #{"linkedin" "indeed" "glassdoor" "purchased-list" "scraped-db"})

(def K_ANONYMITY 5)

(def ^:private _ENRICHABLE_FIELDS
  ["skills" "links" "credentials" "publications"])

;; ── SHA-256 helper (byte-identical to Python hashlib.sha256) ─────────────────

(defn- sha256-hex
  "SHA-256 hex digest over UTF-8 bytes — matches Python hashlib.sha256(s.encode()).hexdigest()."
  [^String s]
  (let [md (java.security.MessageDigest/getInstance "SHA-256")
        bs (.digest md (.getBytes s "UTF-8"))]
    (apply str (map #(format "%02x" (bit-and % 0xff)) bs))))

;; ── is_encrypted (G3) ────────────────────────────────────────────────────────

(defn is_encrypted
  "True iff a field value is Signal-E2E ciphertext (G3).
  Matches agent.py: isinstance(value, str) and value.startswith(ENC_PREFIX)."
  [value]
  (and (string? value) (.startsWith ^String value ENC_PREFIX)))

;; ── subject_hash ──────────────────────────────────────────────────────────────

(defn subject_hash
  "Deterministic hash of the subject DID — the self path profile:{hash}.
  Matches agent.py: hashlib.sha256(subject_did.encode()).hexdigest()[:16]."
  [subject-did]
  (subs (sha256-hex subject-did) 0 16))

;; ── register_self (G1 self-sovereign, G3 signal-e2e) ─────────────────────────

(defn register_self
  "Register a SELF-SOVEREIGN profile. Refuses unless caller == subject (G1). Refuses any
  plaintext identifying field (G3). Refuses a prohibited enrichment source (G1). Returns a
  registered profile keyed by the subject-DID hash."
  [caller-did subject-did profile]
  (cond
    (not= caller-did subject-did)
    {"state" "refused"
     "reason" "third-party registration forbidden — caller must be the subject (G1)"}

    :else
    (let [pii-refusal (some (fn [f]
                              (let [v (get profile f)]
                                (when (and v (not (is_encrypted v)))
                                  {"state" "refused"
                                   "reason" (str "identifying field " (pr-str f)
                                                 " must be signal:v1: ciphertext (G3)")})))
                            IDENTIFYING_FIELDS)]
      (if pii-refusal
        pii-refusal
        (let [src (get profile "enrichmentSource")]
          (if (and src (not (contains? ALLOWED_ENRICHMENT src)))
            {"state" "refused"
             "reason" (str "enrichment source " (pr-str src)
                           " not in public-consent allowlist (G1)")}
            (let [h (subject_hash subject-did)]
              {"state" "registered"
               "profile" (merge profile
                                {"subjectDidHash" h
                                 "registeredBy"   caller-did})})))))))

;; ── ingest_external (G1 no-scraping) ─────────────────────────────────────────

(defn ingest_external
  "Any attempt to ingest from a commercial/scraped candidate source is refused (G1)."
  [source]
  (cond
    (contains? PROHIBITED_SOURCES source)
    {"state" "refused"
     "reason" (str "prohibited candidate source " (pr-str source)
                   " (G1) — license notwithstanding")}

    (not (contains? ALLOWED_ENRICHMENT source))
    {"state" "refused"
     "reason" (str "source " (pr-str source)
                   " not in public-consent allowlist (G1)")}

    :else
    {"state"  "allowed"
     "source" source
     "note"   "enrichment only attaches to a self-registered profile"}))

;; ── cohort_stats (G2 k-anonymity) ────────────────────────────────────────────

(defn cohort_stats
  "Aggregate a cohort (ISCO × country). If the cohort has fewer than k members it is
  SUPPRESSED (G2). Otherwise returns size + top non-identifying skills."
  ([isco country profiles]
   (cohort_stats isco country profiles K_ANONYMITY))
  ([isco country profiles k]
   (let [members (filter #(and (= (get % "isco") isco)
                                (= (get % "country") country))
                          profiles)
         n       (count members)]
     (if (< n k)
       {"suppressed" true
        "reason"     (str "cohort below k=" k " (G2 k-anonymity)")
        "count"      nil}
       (let [skill-counts (reduce (fn [acc p]
                                    (reduce (fn [a s] (update a s (fnil inc 0)))
                                            acc
                                            (get p "skills" [])))
                                  {}
                                  members)
             top          (->> (seq skill-counts)
                               (sort-by (fn [[s c]] [(- c) s]))
                               (take 10)
                               (map first))]
         {"suppressed" false
          "count"      n
          "topSkills"  (vec top)
          "cohortDid"  (str "did:web:talent.etzhayyim.com:cohort:" isco ":" country)})))))

;; ── forget_self (G4 GDPR Art 17 hard delete) ─────────────────────────────────

(defn forget_self
  "GDPR Art 17 cascade HARD delete (G4). Refuses unless caller == subject. Removes the
  profile Datom entirely — does NOT set a soft-delete flag (there is none)."
  [caller-did subject-did store]
  (if (not= caller-did subject-did)
    {"state" "refused"
     "reason" "only the subject may forget their own profile (G1/G4)"}
    (let [h    (subject_hash subject-did)
          kept (vec (filter #(not= (get % "subjectDidHash") h) store))]
      {"state"       "forgotten"
       "store"       kept
       "hardDeleted" (- (count store) (count kept))})))

;; ── attach_enrichment (G1 self-sovereign, G3 signal-e2e) ─────────────────────

(defn attach_enrichment
  "Attach public-consent enrichment to the subject's OWN profile. Refuses unless
  caller == subject (G1) and the source is allowed (G1). Only non-identifying fields
  may be enriched; any identifying field must still be Signal-E2E ciphertext (G3)."
  [caller-did subject-did profile source fields]
  (cond
    (not= caller-did subject-did)
    {"state" "refused"
     "reason" "enrichment attaches to the subject's OWN profile only (G1)"}

    (not (contains? ALLOWED_ENRICHMENT source))
    {"state" "refused"
     "reason" (str "enrichment source " (pr-str source)
                   " not in public-consent allowlist (G1)")}

    :else
    (let [pii-refusal (some (fn [f]
                              (when (and (contains? fields f)
                                         (not (is_encrypted (get fields f))))
                                {"state" "refused"
                                 "reason" (str "enrichment cannot add plaintext identifying field "
                                               (pr-str f) " (G3)")}))
                            IDENTIFYING_FIELDS)]
      (if pii-refusal
        pii-refusal
        (let [merged (reduce (fn [m f]
                               (if (contains? fields f)
                                 (let [existing (vec (get m f []))
                                       updated  (reduce (fn [acc v]
                                                          (if (some #{v} acc)
                                                            acc
                                                            (conj acc v)))
                                                        existing
                                                        (get fields f))]
                                   (assoc m f updated))
                                 m))
                             (into {} profile)
                             _ENRICHABLE_FIELDS)
              provenance (vec (conj (vec (get merged "enrichmentProvenance" [])) source))]
          {"state"   "enriched"
           "profile" (assoc merged "enrichmentProvenance" provenance)})))))

;; ── list_occupations (G2 — existence not disclosed below k) ──────────────────

(defn list_occupations
  "Public listing of ISCO×country cohorts. A cohort below k is NOT listed at all (G2).
  Returns sorted {isco, country, count} for cohorts meeting k."
  ([profiles]
   (list_occupations profiles K_ANONYMITY))
  ([profiles k]
   (let [counts (reduce (fn [acc p]
                          (let [key [(get p "isco") (get p "country")]]
                            (update acc key (fnil inc 0))))
                        {}
                        profiles)
         out    (for [[[isco country] n] counts :when (>= n k)]
                  {"isco" isco "country" country "count" n})]
     (vec (sort-by (fn [c] [(get c "isco") (get c "country")]) out)))))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────

(defn main [& _]
  (println "subject_hash(did:plc:alice):" (subject_hash "did:plc:alice"))
  (println "is_encrypted(signal:v1:abc):" (is_encrypted "signal:v1:abc"))
  (println "is_encrypted(plain):" (is_encrypted "plain"))
  (println "register_self (self):"
           (get (register_self "did:plc:alice" "did:plc:alice" {"isco" "2512" "country" "JP"})
                "state"))
  (println "register_self (third-party):"
           (get (register_self "did:plc:bob" "did:plc:alice" {}) "state")))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
