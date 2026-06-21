#!/usr/bin/env bb
;; kaiyaku 解約 — real-service cancellation-procedure CATALOG loader + validator.
(ns kaiyaku.methods.catalog
  "catalog.cljc — kaiyaku 解約 R1 cancellation-procedure catalog (ADR-2606112201 R1).

  The R1 DATA leg. R0's 縁-ledger is 9 synthetic ties; this loads the
  `data/cancel-procedures.kotoba.edn` catalog of REAL services + their disclosed
  解約/退会 procedures, so a severance plan can carry the actual self-submit
  steps + cost-of-severance (notice / 違約金) instead of a placeholder.

  This namespace is a clean standard-EDN consumer (real :proc/* keywords, read
  with clojure.edn) — NOT the Python-parity string-keyword ledger parser in
  analyze.cljc. It is decoupled: the catalog is a REFERENCE the plan/driver
  consult by svc-id, not a ledger.

  HONESTY GATES (enforced by validate, proven by tests):
    G3 — derive-tier mirrors plan/select-tier EXACTLY; a :browser stance of
      :prohibited / :unknown can NEVER yield T2 (validate raises on a T2 claim
      over a non-:permitted browser stance). self-submit-steps may contain NO
      detection-evasion verb.
    G8 — every entry carries :proc/notice-days + :proc/penalty-jpy (the
      disclosed cost-of-severance, surfaced into the plan, never planned around).
    G6 — every entry is :operator-verified false (a :representative disclosed
      SHAPE, not a live ToS assertion; an operator must verify before live use).
    N1 — every entry is a SERVICE (svc-id), never a person.

  Deterministic; pure fns; file I/O only at the #?(:clj …) load edge. Portable .cljc."
  (:require [clojure.string :as str]
            #?(:clj [clojure.edn :as edn])
            #?(:clj [clojure.java.io :as io])))

;; G3 — the same unrepresentable set as plan/make-step. A disclosed official
;; procedure never contains one of these; validate refuses an entry that does.
(def evasion-tokens
  #{"captcha-solve" "proxy-rotate" "stealth" "rate-limit-bypass"
    "fingerprint-spoof" "ip-rotate" "anti-bot-bypass"})

(def required-keys
  [:proc/svc-id :proc/name :proc/category :proc/region :proc/cancel
   :proc/notice-days :proc/penalty-jpy :proc/self-submit-steps
   :proc/disclosed-source :proc/operator-verified :proc/sourcing])

;; ── load (file edge) ────────────────────────────────────────────────────────

#?(:clj
   (defn load-file*
     "Read the catalog EDN → vector of :proc/* entry maps. File I/O only here."
     [path]
     (edn/read-string (slurp (str path)))))

(defn by-id
  "svc-id → entry map."
  [entries]
  (into {} (map (juxt :proc/svc-id identity)) entries))

;; ── tier derivation (MUST mirror plan/select-tier) ──────────────────────────

(defn derive-tier
  "Safest-first adapter tier for a catalog entry — byte-identical logic to
  methods/plan.cljc select-tier, on real-keyword values:
    cancel api :available → T1 · browser :permitted → T2 · else → T3.
  A :prohibited / :unknown browser stance can never reach T2 (G3)."
  [entry]
  (let [cancel (or (:proc/cancel entry) {})]
    (cond
      (= (:api cancel) :available)     "T1"
      (= (:browser cancel) :permitted) "T2"
      :else                            "T3")))

(defn ->svc-node
  "Convert a catalog entry into the ledger's STRING-keyword :svc/* node shape
  (the methods/ tree's house format), so plan/select-tier can run on it directly
  — this is the bridge the cross-consistency test exercises."
  [entry]
  (let [c (:proc/cancel entry)]
    {":svc/id" (:proc/svc-id entry)
     ":svc/label" (:proc/name entry)
     ":svc/notice-days" (:proc/notice-days entry)
     ":svc/penalty-jpy" (:proc/penalty-jpy entry)
     ":svc/cancel" {":api" (str (:api c))
                    ":browser" (str (:browser c))
                    ":self-submit" (boolean (:self-submit c))}}))

;; ── validate (the honesty gates, in code) ───────────────────────────────────

(defn- step-text [steps] (str/lower-case (str/join " " (map str steps))))

(defn validate-entry
  "Returns a vector of error strings for one entry (empty = ok)."
  [entry]
  (let [errs (transient [])
        sid (:proc/svc-id entry)
        cancel (:proc/cancel entry)
        browser (:browser cancel)]
    (doseq [k required-keys]
      (when-not (contains? entry k)
        (conj! errs (str sid ": missing " k))))
    ;; G3 — a non-:permitted browser stance must not derive T2
    (when (and (= "T2" (derive-tier entry)) (not= browser :permitted))
      (conj! errs (str sid ": G3 — tier T2 over a non-:permitted browser stance " (pr-str browser))))
    ;; G3 — no evasion verb in the disclosed steps
    (let [txt (step-text (:proc/self-submit-steps entry))]
      (doseq [tok evasion-tokens]
        (when (str/includes? txt tok)
          (conj! errs (str sid ": G3 — evasion token '" tok "' in self-submit-steps")))))
    ;; G8 — cost-of-severance must be numbers
    (when-not (number? (:proc/notice-days entry))
      (conj! errs (str sid ": G8 — notice-days must be a number")))
    (when-not (number? (:proc/penalty-jpy entry))
      (conj! errs (str sid ": G8 — penalty-jpy must be a number")))
    ;; G6 — representative + unverified at R0
    (when (not= false (:proc/operator-verified entry))
      (conj! errs (str sid ": G6 — operator-verified must be false at R0 (:representative catalog)")))
    (when (not= :representative (:proc/sourcing entry))
      (conj! errs (str sid ": sourcing must be :representative at R0")))
    (persistent! errs)))

(defn validate
  "Validate the whole catalog. Returns {:ok? bool :errors [..]}."
  [entries]
  (let [errs (vec (mapcat validate-entry entries))]
    {:ok? (empty? errs) :errors errs}))

;; ── coverage report ─────────────────────────────────────────────────────────

(defn coverage
  "Honest catalog coverage: counts by tier / region / category, and verified vs
  unverified (always 0 verified at R0 — surfaced, not hidden)."
  [entries]
  {:total (count entries)
   :by-tier (frequencies (map derive-tier entries))
   :by-region (frequencies (map :proc/region entries))
   :by-category (frequencies (map :proc/category entries))
   :operator-verified (count (filter :proc/operator-verified entries))
   :with-cost-of-severance (count (filter #(or (pos? (:proc/notice-days %))
                                               (pos? (:proc/penalty-jpy %))) entries))})

(defn coverage-report
  "Markdown coverage summary (honest about the operator-verified gap)."
  [entries]
  (let [c (coverage entries)]
    (str "# kaiyaku cancellation-procedure catalog — coverage (R1, :representative)\n\n"
         "- total services: " (:total c) "\n"
         "- by tier: " (pr-str (:by-tier c)) "\n"
         "- by region: " (pr-str (:by-region c)) "\n"
         "- with disclosed cost-of-severance (notice/違約金): " (:with-cost-of-severance c) "\n"
         "- **operator-verified: " (:operator-verified c) " / " (:total c)
         "** (G6: every entry must be operator-verified before live use)\n")))

#?(:clj
   (defn -main
     "CLI: validate the catalog + print coverage (file I/O at the edge)."
     [& argv]
     (let [here (-> *file* io/file .getParentFile .getParentFile)
           path (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                  (io/file (first argv))
                  (io/file here "data" "cancel-procedures.kotoba.edn"))
           entries (load-file* path)
           {:keys [ok? errors]} (validate entries)]
       (print (coverage-report entries))
       (if ok?
         (do (println "validate: OK (" (count entries) "entries)") 0)
         (do (println "validate: FAIL")
             (doseq [e errors] (println "  -" e))
             1)))))
