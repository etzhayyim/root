;; vote.clj — 扶持 (fuchi) R1(b): real 1 SBT = 1 vote with a 48h timelock.
;;
;; Clojure port of vote.py (ADR-2606052300 R1), Wave 1 of the clj-native migration
;; (ADR-2606142300). A real ballot tally (replaces analyze's R0 `yes > no` shortcut):
;;   - **1 SBT = 1 vote** — each member DID casts exactly ONE ballot (a duplicate is rejected at
;;     cast time); every ballot has weight 1 (no token-weighted plutocracy).
;;   - **no-server-key** — a :server voter is unrepresentable; ballots are member-signed (G9).
;;   - **48h timelock** — a tally is not FINALIZABLE before opened-at + timelock; a ballot cast
;;     outside the window is not counted.
;;   - **quorum** — a minimum of participating ballots is required, else rejected (never
;;     auto-accepted on a thin vote).
;; Time is an integer hour stamp (passed in; the script clock is unavailable by design). stdlib only.
(ns fuchi.methods.vote
  (:require [clojure.string :as str]
            [fuchi.methods.live-gate :as lg]))

(def default-timelock-h 48)
(def default-quorum 3)
(def choices #{"yes" "no" "abstain"})

(defn- kw [v] (-> (str (or v "")) (str/replace #"^:+" "") (str/split #"/") last str/lower-case))

(defn make-ballot
  "Construct a ballot, enforcing 1 SBT = 1 vote (weight 1), no-server-key, and a valid choice."
  [{:keys [voter-did choice cast-at weight server-held-key] :or {weight 1 server-held-key false}}]
  (when (not= 1 weight) (throw (ex-info "1 SBT = 1 vote INVARIANT: ballot weight must be 1" {})))
  (when server-held-key (throw (ex-info "no-server-key INVARIANT (G9): a ballot is member-signed" {})))
  (let [v (str/lower-case (str voter-did))]
    (when (or (some #(str/starts-with? v %) ["server" "did:server" ":server"]) (#{"server" "anon"} v))
      (throw (ex-info "G9/G4: a :server / :anon voter is unrepresentable" {:voter voter-did}))))
  (when-not (choices (kw choice)) (throw (ex-info (str "ballot choice " (pr-str choice) " not in " choices) {})))
  {:voter-did voter-did :choice (kw choice) :cast-at (long cast-at) :weight 1 :server-held-key false})

(defn cast
  "Append a ballot, enforcing 1 SBT = 1 vote (a duplicate voter DID is rejected)."
  [ballots ballot]
  (when (some #(= (:voter-did %) (:voter-did ballot)) ballots)
    (throw (ex-info (str "1 SBT = 1 vote: " (:voter-did ballot) " has already voted") {})))
  (conj (vec ballots) ballot))

(defn ballots-from-seed
  "Build ballots from seed maps; rejects duplicate voters (1 SBT = 1 vote)."
  [records]
  (reduce (fn [acc r]
            (cast acc (make-ballot {:voter-did (get r :ballot/voter (get r "voter" "?"))
                                    :choice    (kw (get r :ballot/choice (get r "choice" "yes")))
                                    :cast-at   (long (get r :ballot/cast-at (get r "cast_at" 0)))})))
          [] records))

(defn tally
  "Tally a vote. Only ballots cast within [opened-at, opened-at+timelock] count."
  ([ballots opened-at now] (tally ballots opened-at now default-timelock-h default-quorum))
  ([ballots opened-at now timelock-h quorum]
   (let [close      (+ opened-at timelock-h)
         in-window  (filter #(<= opened-at (:cast-at %) close) ballots)
         yes        (count (filter #(= "yes" (kw (:choice %))) in-window))
         no         (count (filter #(= "no" (kw (:choice %))) in-window))
         abstain    (count (filter #(= "abstain" (kw (:choice %))) in-window))
         participating (+ yes no)
         finalizable (>= now close)
         quorum-met (>= participating quorum)
         outcome (cond
                   (not finalizable) "pending"
                   (not quorum-met)  "rejected"          ; never auto-accept on a thin vote
                   (> yes no)        "accepted"
                   :else             "rejected")]
     {:yes yes :no no :abstain abstain :voters (count in-window)
      :opened-at opened-at :close close :now now :timelock-h timelock-h
      :quorum quorum :quorum-met quorum-met :finalizable finalizable :outcome outcome})))

(defn finalize
  "Strict finalize — RAISES if the 48h timelock has not elapsed (no early close)."
  ([ballots opened-at now] (finalize ballots opened-at now default-timelock-h default-quorum))
  ([ballots opened-at now timelock-h quorum]
   (when (< now (+ opened-at timelock-h))
     (throw (ex-info (str "timelock INVARIANT: cannot finalize before " (+ opened-at timelock-h)
                          "h (now=" now "h, window=" timelock-h "h)") {})))
   (tally ballots opened-at now timelock-h quorum)))

(defn finalize-binding
  "Finalize a vote as BINDING (the on-chain outcome). The 48h timelock still applies strictly, so
   the gate cannot short-circuit it. Returns the tally annotated :binding true."
  ([ballots opened-at now gate] (finalize-binding ballots opened-at now gate default-timelock-h default-quorum))
  ([ballots opened-at now gate timelock-h quorum]
   (lg/require-gate gate)                                 ; R2: autonomous, always passes
   (assoc (finalize ballots opened-at now timelock-h quorum)
          :binding true :ratified-by (:operator-did gate) :council-level (:council-level gate))))
