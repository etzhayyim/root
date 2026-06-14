;; analyze.clj — 弾正 (danjo) non-adjudicating discrepancy-observation analyzer.
;;
;; Clojure port of analyze.py (ADR-2605301600), Wave 1 of the clj-native migration
;; (ADR-2606142300). Runs the OPEN detector heuristics in the method-pack
;; (v1-jp-seed.json) over a PUBLIC procurement corpus and emits
;; danjo.discrepancyObservation records — FACTUAL cross-reference patterns over the
;; public record, NEVER a finding of wrongdoing. The censor's EYE, never the SWORD.
;;
;; Every observation, by construction:
;;   G4 — :danjo.obs/non-adjudicating true; no verdict/guilt/wrongdoing field is representable
;;        (a structural self-check RAISES if such a key creeps in);
;;   G5 — ≥2 sourceRecordCids (a primary-public-record citation is mandatory);
;;   G6 — methodNoteCid present (the public audits the open detector, not only its output);
;;   G4 — carries the method's knownFalsePositiveModes (why a hit is NOT, by itself, evidence).
;;
;; This R0/R1 implements `single-bidder-streak` concretely; the other six method notes are
;; metadata. Live ingest of real pinned gov.dataset.* records + named-party publication are
;; G3/G10-gated. Output is BYTE-IDENTICAL with analyze.py: `method_cid` reproduces Python's
;; json.dumps(method, sort_keys=True, separators=(",",":")) — note the Python DEFAULT
;; ensure_ascii=True, so non-ASCII is escaped \uXXXX (distinct from budget_ledger's encoder),
;; reproduced here by `canonical-json-ascii`. stdlib + cheshire (bundled in bb) only.
(ns root.danjo.methods.analyze
  (:require [cheshire.core :as json]
            [clojure.string :as str]
            [clojure.java.io :as io])
  (:import [java.security MessageDigest]))

(def forbidden-verdict-fields
  "G4 — a field whose name implies a VERDICT must never appear on an observation."
  ["verdict" "guilt" "guilty" "wrongdoing" "finding" "culprit" "illegal" "crime" "sanction"])

;; ── Python-compatible canonical JSON, ensure_ascii=TRUE (json.dumps default) ──────
;; sorted keys · no whitespace · non-ASCII (and 0x7f) escaped \uXXXX · Python string escapes.
(defn- esc-str-ascii
  [^String s]
  (let [sb (StringBuilder.)]
    (.append sb \")
    (doseq [c s]
      (cond
        (= c \")          (.append sb "\\\"")
        (= c \\)          (.append sb "\\\\")
        (= c \newline)    (.append sb "\\n")
        (= c \return)     (.append sb "\\r")
        (= c \tab)        (.append sb "\\t")
        (= c \backspace)  (.append sb "\\b")
        (= c \formfeed)   (.append sb "\\f")
        (< (int c) 0x20)  (.append sb (format "\\u%04x" (int c)))
        (> (int c) 0x7e)  (.append sb (format "\\u%04x" (int c)))
        :else             (.append sb c)))
    (.append sb \")
    (.toString sb)))

(defn canonical-json-ascii
  "Canonical JSON byte-for-byte equal to Python json.dumps(sort_keys=True,
   separators=(\",\",\":\")) with the DEFAULT ensure_ascii=True."
  [x]
  (cond
    (map? x)        (str "{"
                         (->> x
                              (sort-by (fn [[k _]] (if (keyword? k) (name k) (str k))))
                              (map (fn [[k v]]
                                     (str (esc-str-ascii (if (keyword? k) (name k) (str k)))
                                          ":" (canonical-json-ascii v))))
                              (str/join ","))
                         "}")
    (sequential? x) (str "[" (str/join "," (map canonical-json-ascii x)) "]")
    (string? x)     (esc-str-ascii x)
    (boolean? x)    (if x "true" "false")
    (integer? x)    (str x)
    (nil? x)        "null"
    :else           (throw (ex-info (str "canonical-json-ascii: unsupported type " (type x)) {:value x}))))

(defn- sha256-hex
  [^String s]
  (let [d (.digest (MessageDigest/getInstance "SHA-256") (.getBytes s "UTF-8"))]
    (apply str (map #(format "%02x" (bit-and (int %) 0xff)) d))))

(defn load-json
  [path]
  (json/parse-string (slurp (io/file path))))

(defn method-cid
  "Deterministic content id for an open method note (G6 reference). Byte-identical w/ analyze.py."
  [method]
  (str "method:" (get method "methodId" "?") ":"
       (subs (sha256-hex (canonical-json-ascii method)) 0 12)))

(defn- months-between
  [d1 d2]
  (let [y1 (Integer/parseInt (subs d1 0 4)) m1 (Integer/parseInt (subs d1 5 7))
        y2 (Integer/parseInt (subs d2 0 4)) m2 (Integer/parseInt (subs d2 5 7))]
    (Math/abs (+ (* (- y2 y1) 12) (- m2 m1)))))

(defn- pairs-in-order
  "Group records by (contractingAuthority, awardeeLei) preserving first-seen order (Python dict)."
  [records]
  (let [res (reduce (fn [acc r]
                      (let [k [(get r "contractingAuthority") (get r "awardeeLei")]]
                        (if (contains? (:groups acc) k)
                          (update-in acc [:groups k] conj r)
                          (-> acc (update :order conj k) (assoc-in [:groups k] [r])))))
                    {:order [] :groups {}} records)]
    (map (fn [k] [k (get-in res [:groups k])]) (:order res))))

(defn detect-single-bidder-streak
  "Find (authority, awardee) pairs with ≥minConsecutive consecutive single-bid awards inside a
   rolling windowMonths. A FACT about the public record — single-bid procurement is lawful."
  [records params]
  (let [min-consec   (int (get params "minConsecutive" 5))
        window       (int (get params "windowMonths" 24))
        require-flag (boolean (get params "requireSingleBidFlag" true))
        hits         (atom [])]
    (doseq [[[auth awardee] recs0] (pairs-in-order records)]
      (let [recs   (sort-by #(get % "awardDate" "") recs0)
            run    (atom [])
            flush! (fn []
                     (let [rr @run]
                       (when (and (>= (count rr) min-consec)
                                  (<= (months-between (get (first rr) "awardDate")
                                                      (get (last rr) "awardDate"))
                                      window))
                         (swap! hits conj {:authority auth :awardee awardee
                                           :cids (mapv #(get % "cid") rr) :count (count rr)}))))]
        (doseq [r recs]
          (let [single? (and (= 1 (get r "bidCount"))
                             (if require-flag (boolean (get r "singleBidFlag" false)) true))]
            (if single?
              (swap! run conj r)
              (do (flush!) (reset! run [])))))
        (flush!)))
    @hits))

(defn build-observation
  "Assemble a danjo.discrepancyObservation. RAISES if the structural invariants
   (≥2 source cids, method ref present) are not met — non-adjudication is structural."
  [hit method]
  (let [cids (:cids hit)]
    (when (< (count cids) 2)
      (throw (ex-info "G5: discrepancyObservation requires ≥2 sourceRecordCids" {:cids cids})))
    (let [mcid (method-cid method)
          _    (when (str/blank? mcid)
                 (throw (ex-info "G6: discrepancyObservation requires a methodNoteCid" {})))
          obs  {:type                    "danjo.discrepancyObservation"
                :category                (or (get method "appliesToCategory") (get method "methodId"))
                :nonAdjudicatingNotice   true
                :observedPattern         (format "%d consecutive single-bid awards from %s to %s within the method window"
                                                 (:count hit) (:authority hit) (:awardee hit))
                :sourceRecordCids        cids
                :methodNoteCid           mcid
                :knownFalsePositiveModes (get method "knownFalsePositiveModes" [])
                :sourcing                ":representative"}]
      ;; G4 structural self-check: no verdict field may have crept in.
      (doseq [k (keys obs)]
        (when (some #(str/includes? (str/lower-case (name k)) %) forbidden-verdict-fields)
          (throw (ex-info (str "G4: verdict field " (pr-str k) " is unrepresentable") {:key k}))))
      obs)))

(defn run-all
  "Run every IMPLEMENTED detector over the corpus. (R0/R1: single-bidder-streak.)"
  [corpus methodpack]
  (let [records (get corpus "procurementRecords" [])
        by-id   (into {} (map (fn [m] [(get m "methodId") m]) (get methodpack "methods" [])))]
    (if-let [m (get by-id "single-bidder-streak")]
      (let [params (json/parse-string (get m "thresholdParams" "{}"))]
        (mapv #(build-observation % m) (detect-single-bidder-streak records params)))
      [])))

(defn render-edn
  [observations]
  (let [header [";; danjo-observations.kotoba.edn — danjo.discrepancyObservation records."
                ";; G4 nonAdjudicatingNotice=true (FACT, never a verdict) · G5 ≥2 sourceRecordCids"
                ";; · G6 methodNoteCid. The censor's EYE, never the SWORD. Named-party publication"
                ";; G10 + 1 SBT=1 vote gated. DERIVED :representative. ADR-2605301600." "" "["]
        lines  (map (fn [o]
                      (let [cids (str/join " " (map #(str "\"" % "\"") (:sourceRecordCids o)))]
                        (str " {:danjo.obs/category :" (:category o)
                             " :danjo.obs/non-adjudicating true "
                             ":danjo.obs/pattern \"" (:observedPattern o) "\" "
                             ":danjo.obs/source-record-cids [" cids "] "
                             ":danjo.obs/method-note-cid \"" (:methodNoteCid o) "\" "
                             ":danjo.obs/sourcing :representative}")))
                    observations)]
    (str (str/join "\n" (concat header lines ["]"])) "\n")))

(defn -main
  [& args]
  (let [argv   (vec args)
        idx    (fn [flag] (let [i (.indexOf argv flag)] (when (>= i 0) (nth argv (inc i)))))
        corpus (load-json (or (idx "--corpus") "../data/corpus.seed.json"))
        meths  (load-json (or (idx "--methods") "v1-jp-seed.json"))
        obs    (run-all corpus meths)]
    (when-let [outdir (idx "--out")]
      (.mkdirs (io/file outdir))
      (spit (io/file outdir "danjo-observations.kotoba.edn") (render-edn obs)))
    (println (format "danjo: %d procurement records, %d open methods → %d discrepancy observation(s)"
                     (count (get corpus "procurementRecords" []))
                     (count (get meths "methods" []))
                     (count obs)))
    (doseq [o obs]
      (println (format "  [%s] %s (%d sources, non-adjudicating)"
                       (:category o) (:observedPattern o) (count (:sourceRecordCids o)))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
