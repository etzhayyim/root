(ns etzhayyim.registry.register
  "Holochain-iso actor registration WITH the validating membrane (phase 2).

   Registration is now gated by a real membrane, exactly as the kotoba-dht
   validating DHT prescribes (ADR-2606011330 / 2606111400):

     1. AGENT mints its key → did:key, authors a SIGNED genesis on its own
        kotoba source-chain (content-addressed; the genesis :cid is its address).
     2. MEMBRANE PROOF — an existing SBT MEMBER issues a CACAO vouch (signs a
        capability {iss=member, aud=agent, att, exp}). No self-admission: the
        Sybil boundary is 'an existing member must vouch'.
     3. WITNESS QUORUM — N validators (the DHT neighbourhood) each independently
        run the DNA rules (self-sig ok · vouch ok & iss∈roster · handle unique ·
        shape ok) and emit a SIGNED attestation (:valid) or a SIGNED WARRANT
        (:invalid + reason). The genesis is durable iff ≥ threshold attestations.
     4. DHT replication — the entry is held by the r validator-nodes whose ids
        are XOR-closest to the genesis :cid.

   The registry MV counts ONLY quorum-validated agents — an emergent fold, and
   one that REJECTS un-vouched / duplicate actors (demonstrated below)."
  (:require [etzhayyim.registry.agent :as ag]
            [kotoba.datom :as kd]
            [clojure.string :as str]
            [clojure.pprint]
            [clojure.java.io :as io])
  (:import [java.util Base64]
           [java.math BigInteger]))

(def out-dir "../public/kotoba/agents")
(def quorum-threshold 2)        ; 2-of-3 validators
(def dht-r 2)                   ; replication factor

(defn- b64 [^bytes b] (.encodeToString (Base64/getEncoder) b))

;; ── CACAO membrane vouch (member → agent) ───────────────────────────────────
(defn- vouch-preimage [iss aud att exp]
  (kd/canonical-json {"att" att "aud" aud "exp" exp "iss" iss}))

(defn issue-vouch
  "An SBT member signs a capability vouching for a new agent."
  [member-kp member-did agent-did]
  (let [att "register@etzhayyim/actor-registry"
        exp 1788000000]
    {:iss member-did :aud agent-did :att att :exp exp
     :sig (ag/sign member-kp (vouch-preimage member-did agent-did att exp))}))

(defn- vouch-valid?
  "Validator's check of a CACAO vouch: member signature valid AND issuer is a
   real SBT member AND audience is this agent."
  [vouch agent-did member-roster]
  (and vouch
       (= (:aud vouch) agent-did)
       (contains? member-roster (:iss vouch))
       (ag/verify (:iss vouch)
                  (vouch-preimage (:iss vouch) (:aud vouch) (:att vouch) (:exp vouch))
                  (:sig vouch))))

;; ── DNA validation rules → attestation | warrant ────────────────────────────
(defn- warrant-preimage [cid verdict reason]
  (kd/canonical-json {"cid" cid "reason" reason "verdict" verdict}))

(defn validate
  "One validator runs the DNA rules over a genesis. Returns a signed attestation
   (:valid) or a signed warrant (:invalid + reason). `seen-handles` is the
   validator's view of already-validated handles (uniqueness)."
  [{:keys [validator-kp validator-did member-roster seen-handles]} agent]
  (let [{:keys [agent/did agent/handle membrane]} agent
        {:keys [datoms cid author-sig]} (first (:chain agent))
        reason (cond
                 (not (ag/verify did cid author-sig))                  "bad-self-sig"
                 (not (vouch-valid? (:vouch membrane) did member-roster)) "no-member-vouch"
                 (contains? seen-handles handle)                       "duplicate-handle"
                 (not= cid (kd/tx-cid datoms ""))                      "bad-content-address"
                 :else nil)]
    (if reason
      {:validator validator-did :verdict "invalid" :reason reason
       :sig (ag/sign validator-kp (warrant-preimage cid "invalid" reason))}
      {:validator validator-did :verdict "valid"
       :sig (ag/sign validator-kp cid)})))

;; ── kotoba-dht XOR-distance neighbourhood ───────────────────────────────────
(defn- hex->bi [h] (BigInteger. ^String h 16))
(defn- node-id [validator-did] (kd/*sha256-hex* validator-did))   ; 64-hex DHT id

(defn dht-replicas
  "The r validator-nodes whose ids are XOR-closest to the genesis :cid."
  [cid validators r]
  (let [target (hex->bi (subs cid 1))]            ; strip the 'b' CID prefix
    (->> validators
         (map (fn [v] {:did (:validator-did v)
                       :node-id (node-id (:validator-did v))}))
         (sort-by (fn [{:keys [node-id]}] (.xor (hex->bi node-id) target)))
         (take r)
         (mapv :node-id))))

;; ── genesis authoring (agent self-publishes, then membrane validates) ───────
(defn- genesis-datoms [did handle kp]
  [(kd/add did ":actor/handle" handle)
   (kd/add did ":actor/dna-cid" (str "bafyrei-dna-" handle))
   (kd/add did ":actor/genesis-key" (b64 (ag/raw-pubkey kp)))
   (kd/add did ":actor/registered-via" "source-chain-genesis")])

(defn author-genesis
  "Agent mints its key, authors+signs its genesis, attaches the member vouch."
  [handle member-kp member-did]
  (let [kp (ag/gen-keypair)
        did (ag/did-key kp)
        datoms (kd/normalize-datoms (genesis-datoms did handle kp))
        cid (kd/tx-cid datoms "")]
    {:agent/did did :agent/handle handle :dna/cid (str "bafyrei-dna-" handle)
     :chain [{:seq 0 :prev "" :datoms datoms :cid cid
              :author-sig (ag/sign kp cid)}]
     :membrane {:vouch (when member-kp (issue-vouch member-kp member-did did))}}))

(defn run-membrane
  "Submit a genesis to the validator quorum + DHT. Returns the agent doc with
   attestations / warrants / quorum verdict / dht replicas attached."
  [agent validators member-roster seen-handles all-validators]
  (let [cid (get-in agent [:chain 0 :cid])
        verdicts (mapv #(validate (assoc % :member-roster member-roster
                                         :seen-handles seen-handles)
                                  agent)
                       validators)
        atts (filterv #(= "valid" (:verdict %)) verdicts)
        warrants (filterv #(= "invalid" (:verdict %)) verdicts)
        met? (>= (count atts) quorum-threshold)]
    (-> agent
        (assoc-in [:membrane :attestations] atts)
        (assoc-in [:membrane :warrants] warrants)
        (assoc-in [:membrane :quorum]
                  {:threshold quorum-threshold :valid-count (count atts) :met? met?})
        (assoc :dht {:r dht-r :replicas (dht-replicas cid all-validators dht-r)}))))

(defn- write-edn! [path data]
  (io/make-parents path)
  (spit path (with-out-str (clojure.pprint/pprint data))))

;; ── the roster: valid (vouched) + two adversarial rejections ────────────────
(defn -main [& _]
  (let [;; 3 SBT members (can vouch) + 3 validators (DHT neighbourhood)
        members (repeatedly 3 (fn [] (let [kp (ag/gen-keypair)] {:kp kp :did (ag/did-key kp)})))
        member-roster (set (map :did members))
        validators (mapv (fn [_] (let [kp (ag/gen-keypair)]
                                   {:validator-kp kp :validator-did (ag/did-key kp)}))
                         (range 3))
        m0 (first members)
        ;; valid agents — each vouched by a real member
        valid (mapv #(author-genesis % (:kp m0) (:did m0))
                    ["busshi" "ugachi" "mimamori" "kaname" "jinushi"])
        ;; adversarial: NO member vouch (Sybil) + DUPLICATE handle
        rogue (author-genesis "rogue-sybil" nil nil)
        dup   (author-genesis "busshi" (:kp m0) (:did m0))   ; handle already taken
        submissions (concat valid [rogue dup])]
    (println "\nHolochain-iso registration · 3 validators, quorum" quorum-threshold "· membrane = SBT-member CACAO vouch\n")
    ;; run each submission through the membrane, threading uniqueness state
    (loop [pending submissions, seen #{}, docs [], n 0]
      (if (empty? pending)
        ;; ── emit everything ──
        (let [validated (filterv #(get-in % [:membrane :quorum :met?]) docs)
              file-of (fn [d] (str (:agent/handle d)
                                   (if (get-in d [:membrane :quorum :met?]) "" "-rejected")))]
          (doseq [d docs]
            (write-edn! (str out-dir "/" (file-of d) ".agent.kotoba.edn") d))
          (write-edn! (str out-dir "/member-roster.kotoba.edn")
                      {:roster/members (vec member-roster) :roster/note "SBT members who may vouch"})
          (write-edn! (str out-dir "/validator-set.kotoba.edn")
                      {:validators/set (mapv (fn [v] {:did (:validator-did v)
                                                      :node-id (node-id (:validator-did v))}) validators)
                       :validators/quorum quorum-threshold})
          (write-edn! (str out-dir "/registry-mv.kotoba.edn")
                      {:mv/name "actor-registry-genesis"
                       :mv/spec "MvRegistry fold over QUORUM-VALIDATED genesis entries"
                       :mv/count (count validated)
                       :mv/rejected (- (count docs) (count validated))
                       :mv/index (mapv (fn [d]
                                         {:handle (:agent/handle d)
                                          :did (:agent/did d)
                                          :file (file-of d)
                                          :head-cid (get-in d [:chain 0 :cid])
                                          :validated? (get-in d [:membrane :quorum :met?])
                                          :reasons (vec (distinct (map :reason (get-in d [:membrane :warrants]))))})
                                       docs)
                       :mv/note "emergent fold; un-vouched / duplicate actors are REJECTED by the membrane"})
          (println (format "\nregistry MV: %d validated · %d rejected (written to %s/)"
                           (count validated) (- (count docs) (count validated)) out-dir))
          nil)
        ;; ── process one submission ──
        (let [a (first pending)
              handle (:agent/handle a)
              doc (run-membrane a validators member-roster seen validators)
              met? (get-in doc [:membrane :quorum :met?])
              q (get-in doc [:membrane :quorum])
              warrants (get-in doc [:membrane :warrants])]
          (println (format "  %-12s %s  quorum %d/%d %s%s  dht-replicas:%d"
                           handle (subs (:agent/did a) 0 22)
                           (:valid-count q) (count validators)
                           (if met? "✓ VALIDATED" "✗ REJECTED")
                           (if (seq warrants) (str " [" (str/join "," (distinct (map :reason warrants))) "]") "")
                           (count (get-in doc [:dht :replicas]))))
          (recur (rest pending)
                 (if met? (conj seen handle) seen)
                 (conj docs doc)
                 (inc n)))))))

(defn- write-edn! [path data]
  (io/make-parents path)
  (spit path (with-out-str (clojure.pprint/pprint data))))
