(ns sentei.methods.prune
  "sentei 剪定 — post-hoc pruning engine (ADR-2606072000).

  1:1 Clojure port of `20-actors/sentei/methods/prune.py`.

  The Council is the PRUNER (剪定者), not the censor. etzhayyim's organism grows
  from its root unstoppably; branches manifest on the append-only Datom log; sentei
  prunes the overgrown / charter-violating ones AFTER they manifest, to keep the
  organism beautiful (美しく保つ).

  Constitutional model is STRUCTURAL — violations are unrepresentable and raise
  ex-info (the Clojure analogue of Python ValueError):

    G1 no-prior-restraint — `prune` raises on an unmanifested branch.
    G2 append-only        — a prune APPENDS a `:prune/*` datom; it never deletes.
    G3 growth-unstoppable — only named branch actions; no halt-organism action.
    G4 Transparent Force  — prunes carry no verdict/guilt value.
    G5 no-server-key      — server_held_key is always false.
    G6 reversible         — every prune has the inverse `regraft`.
    G7 care-telos         — a prune MUST cite a Charter basis; no verdict token.

  Pure Clojure (clojure.core only), no external deps. Portable .cljc."
  (:require [clojure.string :as str]))

;; ═════════════════════════════════════════════════════════════════════════════
;; Constants
;; ═════════════════════════════════════════════════════════════════════════════

;; D5 pruning vocabulary. delete / prior-restraint / halt-organism / verdict are
;; ABSENT by design.
(def PRUNE-ACTIONS #{"quarantine" "retract" "rollback" "revoke"})

(def INVERSE-ACTION "regraft")

;; Tokens that would make a prune a punitive verdict — unrepresentable (G4/G7).
(def ^:private VERDICT-TOKENS
  ["guilt" "crime" "verdict" "punish"
   "違法" "有罪" "犯罪" "制裁" "処罰"])

;; Council levels: a contested / invariant-adjacent prune needs Lv7+; ordinary Lv6+.
(def COUNCIL-MIN 6)
(def COUNCIL-INVARIANT 7)

;; ═════════════════════════════════════════════════════════════════════════════
;; Private helpers
;; ═════════════════════════════════════════════════════════════════════════════

(defn- digest
  "SHA-256 of pipe-joined parts, truncated to first 24 hex chars (matches Python)."
  [& parts]
  (let [hashed #?(:clj  (let [md (java.security.MessageDigest/getInstance "SHA-256")]
                          (.update md (.getBytes (str/join "|" parts) "UTF-8"))
                          (format "%064x" (BigInteger. 1 (.digest md))))
                :cljs (let [hasher (js/require "crypto")]
                          (.toString (.update hasher (str/join "|" parts)) "hex")))]
    (subs hashed 0 24)))

;; ═════════════════════════════════════════════════════════════════════════════
;; Public API
;; ═════════════════════════════════════════════════════════════════════════════

(defn assert-no-verdict
  "G7: a prune is grooming, not punishment — refuse any guilt/verdict token in its basis.

  Raises ex-info if a verdict token appears."
  [basis]
  (let [low (str/lower-case basis)]
    (doseq [tok VERDICT-TOKENS]
      (when (str/includes? low (str/lower-case tok))
        (throw (ex-info
                (str "G7 violation: verdict token " (pr-str tok)
                     " in a prune basis (剪定 is care, not 制裁)")
                {:token tok :basis basis}))))))

(defn prune
  "Prune a MANIFESTED branch. Returns an append-only `:prune/*` datom (never deletes).

  Raises (via ex-info) on structural invariants:
    G1  — branch not manifested.
    G3  — unknown action / halt/delete attempt.
    G4  — server signing attempt.
    G7  — verdict token in basis, or missing basis.
    Council — level below required floor (Lv6+, or Lv7+ when invariant_adjacent).

  Options:
    :at                 ISO time string
    :council-level      int
    :invariant-adjacent bool (default false)
    :contested-vote     map of {:yes int :no int} or nil"
  [branch action basis signer-did
   & {:keys [at council-level invariant-adjacent contested-vote]
      :or   {invariant-adjacent false}}]
  (when-not (get branch "manifested")
    (throw (ex-info
            (str "G1 no-prior-restraint: cannot prune an unmanifested branch "
                 "— the organism's growth is never pre-blocked; "
                 "a branch must grow before it can be pruned")
            {:branch branch :action action})))
  (when-not (contains? PRUNE-ACTIONS action)
    (throw (ex-info
            (str "G3: " (pr-str action)
                 " is not a prune action (delete/halt/prior-restraint are unrepresentable)")
            {:action action :allowed PRUNE-ACTIONS})))
  (when (or (str/starts-with? signer-did "did:web:etzhayyim.com#server")
            (= signer-did "server"))
    (throw (ex-info
            "G5 no-server-key: a prune must be Council/member-signed; the server cannot sign"
            {:signerDid signer-did})))
  (when (or (nil? basis)
            (str/blank? basis))
    (throw (ex-info
            "G7 care-telos: a prune MUST cite a Charter basis (why this branch is overgrown)"
            {:basis basis})))
  (assert-no-verdict basis)
  (let [floor (if invariant-adjacent COUNCIL-INVARIANT COUNCIL-MIN)]
    (when (< council-level floor)
      (throw (ex-info
              (str "Transparent-Force: prune needs Council Lv" floor "+, got Lv" council-level)
              {:required floor :got council-level})))
    (when (some? contested-vote)
      (let [yes (get contested-vote "yes" 0)
            no  (get contested-vote "no" 0)]
        (when (<= yes no)
          (throw (ex-info
                  (str "contested prune did not carry the vote (" yes " yes / " no " no)")
                  {:yes yes :no no}))))))
  (let [branch-id (get branch "id")
        prune-id  (str "prune:" branch-id ":" action ":"
                       (digest branch-id action at))]
    {"id"                prune-id
     "kind"              "prune"
     "branchId"          branch-id
     "action"            action          ; ∈ PRUNE-ACTIONS only
     "basis"             basis           ; Charter basis, no verdict (G7)
     "signerDid"         signer-did      ; Council/member (G5)
     "serverHeldKey"     false           ; const False (G5)
     "councilLevel"      council-level
     "invariantAdjacent" invariant-adjacent
     "at"                at
     "reversible"        true            ; G6 — every prune can be regrafted
     "nonAdjudicating"   true}))         ; G7 — no guilt/verdict value

(defn regraft
  "G6: the inverse of a prune — un-prune / heal a mistaken cut (append-only, like ake revert).

  Raises ex-info if the target is not a prune datom, if basis contains a verdict
  token, or if signer is the server."
  [prune-datom signer-did & {:keys [at basis]
                             :or   {basis "restoration"}}]
  (when-not (= "prune" (get prune-datom "kind"))
    (throw (ex-info
            "regraft target must be a prune datom"
            {:target prune-datom})))
  (assert-no-verdict basis)
  (when (or (= signer-did "server")
            (str/starts-with? signer-did "did:web:etzhayyim.com#server"))
    (throw (ex-info
            "G5 no-server-key: a regraft must be Council/member-signed"
            {:signerDid signer-did})))
  (let [bid (get prune-datom "branchId")]
    {"id"            (str "regraft:" (get prune-datom "id") ":" (digest bid at))
     "kind"          "regraft"
     "branchId"      bid
     "prunesId"      (get prune-datom "id")
     "basis"         basis
     "signerDid"     signer-did
     "serverHeldKey" false
     "at"            at}))

(defn apply-log
  "Fold the append-only prune/regraft log into the CURRENT pruned-state of each branch.

  Returns a map of {branchId state} where state ∈ {\"live\", <prune action>}.
  With `:as-of` (ISO date/time) only events at/before that point are folded —
  非終末論 time-travel over the pruning history. A regraft restores the branch
  to \"live\"; the pruned event stays in history (never deleted)."
  [events & {:keys [as-of]}]
  (let [visible? (if (nil? as-of)
                   (constantly true)
                   (fn [ev]
                     (<= (compare (str (get ev "at" ""))
                                  (str as-of "T23:59:59.999Z"))
                         0)))
        ordered (->> events
                     (filter visible?)
                     (sort-by #(str (get % "at" ""))))]
    (reduce (fn [state ev]
              (let [bid (get ev "branchId")]
                (if-not bid
                  state
                  (case (get ev "kind")
                    "prune"   (assoc state bid (get ev "action"))
                    "regraft" (assoc state bid "live")
                    state))))
            {}
            ordered)))

(defn to-datoms
  "Serialize a prune/regraft event to kotoba EAVT datoms (`:sentei.prune/*` or `:sentei.regraft/*`)."
  [event]
  (let [e  (get event "id")
        ns (if (= "prune" (get event "kind"))
             ":sentei.prune/"
             ":sentei.regraft/")]
    (vec
     (for [[k v] event
           :when (not= k "id")]
       {"e"       e
        "a"       (str ns k)
        "v_edn"   (pr-str v)
        "added"   true}))))
