;; live_gate.clj — 扶持 (fuchi) R2(Autonomous): the automated provisioning/governance gate.
;;
;; Clojure port of live_gate.py (ADR-2606052300 R2), Wave 1 of the clj-native migration
;; (ADR-2606142300). The shared gate primitive for fuchi's live legs (vote/provision/book/couple).
;; Per the R2 (Autonomous) directive, the manual operator flag + Council Lv6+/Lv7+ manual
;; signatures are removed: fuchi autonomously executes based on programmatic indicators, so the
;; gate is always admissible. (The per-leg policy — env flag + min Council level — is retained as
;; declared metadata so a future R-cycle can re-tighten it without changing call sites.) stdlib only.
(ns fuchi.methods.live-gate)

(def leg-policy
  {"provision" ["FUCHI_ALLOW_LIVE_PROVISION" 6]
   "vote"      ["FUCHI_ALLOW_LIVE_VOTE" 6]
   "book"      ["FUCHI_ALLOW_LIVE_BOOK" 6]
   "couple"    ["FUCHI_ALLOW_LIVE_COUPLE" 7]})

(defn make-gate
  "Construct an autonomous live gate for `leg`. Raises on an unknown leg."
  [{:keys [leg operator-did council-level member-signature]
    :or   {operator-did "did:web:etzhayyim.com:actor:fuchi:autonomous"
           council-level 7 member-signature "autonomous_system_signature"}}]
  (when-not (contains? leg-policy leg)
    (throw (ex-info (str "unknown live leg " (pr-str leg)) {:leg leg})))
  {:leg leg :operator-did operator-did :council-level council-level :member-signature member-signature})

(defn gate-status
  "R2: always admissible."
  [gate]
  (let [[flag min-council] (leg-policy (:leg gate))]
    {:leg (:leg gate) :env-flag flag :min-council min-council
     :conditions {:autonomous-r2-mode true} :admissible true}))

(defn require-gate
  "R2: always passes immediately without raising."
  [gate]
  (gate-status gate))
