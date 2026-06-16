;; ported from 20-actors/himotoki/methods/request.py — real port replacing the
;; unit_refactor stage-0 "TODO: port-failed" stub. NS also fixed:
;; root.himotoki.methods.request -> himotoki.methods.request (20-actors is the bb
;; source root, so the actor.method shape resolves; the root.* prefix never did).
;;
;; Self-contained (own minimal JSON reader, no cheshire/data.json) — the seed
;; registry is JSON, read at the file I/O edge only.
;;
;; The Python `__main__` argv demo/printer (main) is omitted: it is a CLI driver
;; (argv parsing + stdout) outside the pure port surface the tests exercise.
(ns himotoki.methods.request
  "request.py — himotoki 繙き DSAR/FOIA disclosure-request DRAFT generator (R0/R1, offline).
  1:1 Clojure port of `methods/request.py`.

  Turns a consenting member's own-data request against a coded disclosureTarget into a
  ready-to-send request DRAFT — never a live dispatch. Structural charter invariants:
  G3 DSAR own-data-only · G4 true-requester/no-pretext · G6 PII as encrypted envelope ref
  (never plaintext) · G8 no mass-filing · G14 verify-before-dispatch · G10 outbound-gated.

  House style: disclosureTarget records stay string-keyed maps, byte-for-byte the same
  shapes Python json.loads produced. The Python `__main__` argv CLI driver is omitted."
  (:require [clojure.string :as str]
            #?(:clj [clojure.java.io :as io])))

;; ── minimal JSON reader (subset sufficient for the disclosureTarget seed) ──────
;; Mirrors danjo.methods.budget-ledger's self-contained reader: maps string-keyed,
;; integers → long, literals true/false/null → true/false/nil — Python json.loads' shapes.
(declare json-value)

(defn- skip-ws [^String s i]
  (loop [i i]
    (if (and (< i (count s))
             (contains? #{\space \tab \newline \return} (nth s i)))
      (recur (inc i))
      i)))

(defn- json-string [^String s i]
  (loop [i (inc i), sb (StringBuilder.)]
    (let [c (nth s i)]
      (cond
        (= c \") [(.toString sb) (inc i)]
        (= c \\)
        (let [e (nth s (inc i))]
          (case e
            \" (do (.append sb \") (recur (+ i 2) sb))
            \\ (do (.append sb \\) (recur (+ i 2) sb))
            \/ (do (.append sb \/) (recur (+ i 2) sb))
            \b (do (.append sb \backspace) (recur (+ i 2) sb))
            \f (do (.append sb \formfeed) (recur (+ i 2) sb))
            \n (do (.append sb \newline) (recur (+ i 2) sb))
            \r (do (.append sb \return) (recur (+ i 2) sb))
            \t (do (.append sb \tab) (recur (+ i 2) sb))
            \u (let [cp (Integer/parseInt (subs s (+ i 2) (+ i 6)) 16)]
                 (.append sb (char cp))
                 (recur (+ i 6) sb))
            (do (.append sb e) (recur (+ i 2) sb))))
        :else (do (.append sb c) (recur (inc i) sb))))))

(defn- json-number [^String s i]
  (let [end (loop [j i]
              (if (and (< j (count s))
                       (contains? #{\0 \1 \2 \3 \4 \5 \6 \7 \8 \9 \+ \- \. \e \E} (nth s j)))
                (recur (inc j))
                j))
        tok (subs s i end)]
    [(if (some #{\. \e \E} tok) (Double/parseDouble tok) (Long/parseLong tok)) end]))

(defn- json-array [^String s i]
  (loop [i (skip-ws s (inc i)), out []]
    (if (= (nth s i) \])
      [out (inc i)]
      (let [[v i] (json-value s i)
            i (skip-ws s i)]
        (if (= (nth s i) \,)
          (recur (skip-ws s (inc i)) (conj out v))
          [(conj out v) (inc i)])))))

(defn- json-object [^String s i]
  (loop [i (skip-ws s (inc i)), out {}]
    (if (= (nth s i) \})
      [out (inc i)]
      (let [[k i] (json-string s i)
            i (skip-ws s i)
            [v i] (json-value s (skip-ws s (inc i)))
            out (assoc out k v)
            i (skip-ws s i)]
        (if (= (nth s i) \,)
          (recur (skip-ws s (inc i)) out)
          [out (inc i)])))))

(defn- json-value [^String s i]
  (let [i (skip-ws s i)
        c (nth s i)]
    (cond
      (= c \{) (json-object s i)
      (= c \[) (json-array s i)
      (= c \") (json-string s i)
      (= c \t) [true (+ i 4)]
      (= c \f) [false (+ i 5)]
      (= c \n) [nil (+ i 4)]
      :else (json-number s i))))

(defn parse-json
  "Parse the first JSON value in text → Clojure data (maps string-keyed)."
  [text]
  (first (json-value text 0)))

;; ── constants (mirror request.py) ─────────────────────────────────────────────
(def MAX-BATCH 5)                        ; G8 — no mass-filing / agency flooding
(def ^:private DSAR-REGIME-PREFIXES
  ["gdpr" "ccpa" "cpra" "appi" "lgpd" "pipeda" "pdpa" "pipl"])
(def ^:private FORBIDDEN-PRETEXT-FIELDS
  ["pretext" "sockpuppet" "impersonat" "alias" "false-identity"])

;; ── default registry path (…/himotoki/methods/request.cljc → up 2 = himotoki) ──
#?(:clj
   (def ^:private default-registry
     (-> *file* io/file .getParentFile .getParentFile
         (io/file "registry" "targets.seed.json"))))

(defn load-registry
  "Return {targetId target}. targetId = '<organization>:<regime>' (stable, human)."
  ([] #?(:clj (load-registry default-registry)
         :cljs (throw (ex-info "load-registry needs an explicit path under cljs" {}))))
  ([path]
   (let [d (parse-json (slurp (str path)))]
     (reduce (fn [out t]
               (assoc out (str (get t "organization") ":" (get t "regime")) t))
             {}
             (get d "targets" [])))))

(defn- starts-with-any?
  "Mirror Python str.startswith(tuple): true if s starts with any prefix."
  [s prefixes]
  (boolean (some #(str/starts-with? s %) prefixes)))

(defn is-dsar
  "DSAR (own-data) vs FOIA (public records), inferred from the regime."
  [target]
  (let [regime (str/lower-case (str (get target "regime" "")))]
    (cond
      (starts-with-any? regime DSAR-REGIME-PREFIXES) true
      (or (str/includes? regime "foia")
          (str/includes? regime "情報公開")
          (str/ends-with? regime "-foia")) false
      :else (boolean (some #(starts-with-any? (str/lower-case (str %)) DSAR-REGIME-PREFIXES)
                           (get target "altRegimes" []))))))

(defn is-verified [target]
  (= (str (get target "verificationStatus" "")) "verified"))

(defn build-request
  "Build a disclosure-request draft. RAISES on a charter violation (G3/G4/G6)."
  [target member]
  (let [requester (or (get member "requesterDid") "")]
    (when (= requester "")
      (throw (ex-info "G4: every request must identify the true requester DID (no pretext)" {})))
    ;; G4 — no pretext/sockpuppet field may be supplied.
    (doseq [k (keys member)]
      (let [kl (str/lower-case (str k))]
        (when (some #(str/includes? kl %) FORBIDDEN-PRETEXT-FIELDS)
          (throw (ex-info (str "G4: pretext field " (pr-str k)
                               " is unrepresentable; the true requester must file") {})))))
    (let [dsar (is-dsar target)]
      (when (and dsar (not (true? (get member "ownDataOnly"))))
        (throw (ex-info "G3: a DSAR is own-data-only; member must assert ownDataOnly=true" {})))
      ;; G6 — the member's PII must be an encrypted envelope ref, never plaintext.
      (let [env (or (get member "subjectEnvelopeRef") "")]
        (when-not (str/starts-with? env "com.etzhayyim.encrypted:")
          (throw (ex-info (str "G6: member identity must be a com.etzhayyim.encrypted:* envelope ref, "
                               "never plaintext PII in the draft") {})))
        (doseq [forbidden ["name" "email" "address" "phone"]]
          (when (and (contains? member forbidden) (get member forbidden))
            (throw (ex-info (str "G6: plaintext PII " (pr-str forbidden)
                                 " must not be in the request; use the envelope") {}))))
        {"type"                  "himotoki.disclosureRequest"
         "kind"                  (if dsar "DSAR" "FOIA")
         "regime"                (get target "regime")
         "organization"          (get target "organization")
         "jurisdiction"          (get target "jurisdiction")
         "channelType"           (get target "channelType")
         "requesterDid"          requester                 ; G4 — true requester
         "subjectEnvelopeRef"    env                       ; G6 — encrypted, never plaintext
         "ownDataOnly"           (boolean dsar)            ; G3
         "statutoryDeadlineDays" (get target "statutoryDeadlineDays")
         "targetVerified"        (is-verified target)      ; G14 input
         "dispatchReady"         false                     ; never ready at R0 (G10/G14)
         "sourcing"              ":representative"}))))

(defn can-dispatch
  "G14 + G10: a draft may be transmitted ONLY against a verified target AND with the
  operator gate. Returns [allowed reason-if-refused]."
  [target operator-gate]
  (cond
    (not (is-verified target))
    [false (str "G14: target is unverified-seed / stale; verify (and re-check within the "
                "freshness window) before any dispatch")]
    (not operator-gate)
    [false "G10: live dispatch needs HIMOTOKI_OPERATOR_GATE=1 (Council + operator)"]
    :else [true ""]))

(defn build-batch
  "Build drafts for several targets. RAISES (G8) if more than MAX-BATCH — no mass-filing."
  [target-ids member registry]
  (when (> (count target-ids) MAX-BATCH)
    (throw (ex-info (str "G8: no mass-filing — at most " MAX-BATCH
                         " targets per batch, got " (count target-ids)) {})))
  (mapv (fn [t] (build-request (get registry t) member)) target-ids))

(defn- bool-lower
  "Mirror Python str(bool).lower(): true → \"true\", false → \"false\"."
  [v]
  (if v "true" "false"))

(defn render-edn [drafts]
  (let [header [";; himotoki-request-drafts.kotoba.edn — disclosure-request DRAFTS (never dispatched)."
                ";; G3 own-data-only DSAR · G4 true-requester (no pretext) · G6 PII = encrypted"
                ";; envelope ref (never plaintext) · G14 dispatch refused vs unverified target ·"
                ";; G10 outbound-gated. DERIVED :representative. ADR-2605302130." "" "["]
        lines (mapv (fn [d]
                      (str " {:himotoki.req/kind :" (get d "kind")
                           " :himotoki.req/regime \"" (get d "regime") "\" "
                           ":himotoki.req/organization \"" (get d "organization") "\" "
                           ":himotoki.req/requester-did \"" (get d "requesterDid") "\" "
                           ":himotoki.req/subject-envelope-ref \"" (get d "subjectEnvelopeRef") "\" "
                           ":himotoki.req/own-data-only " (bool-lower (get d "ownDataOnly")) " "
                           ":himotoki.req/target-verified " (bool-lower (get d "targetVerified")) " "
                           ":himotoki.req/dispatch-ready false :himotoki.req/sourcing :representative}"))
                    drafts)]
    (str (str/join "\n" (concat header lines ["]"])) "\n")))
