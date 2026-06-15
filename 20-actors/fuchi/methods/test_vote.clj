;; test_vote.clj — 扶持 vote: 1 SBT=1 vote + 48h timelock + quorum, parity with vote.py;
;; + live-gate R2. Run via `bb test:fuchi`. ADR-2606142300.
(ns fuchi.methods.test-vote
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [fuchi.methods.vote :as v]
            [fuchi.methods.live-gate :as lg]))

(defn- mk [voter choice at] (v/make-ballot {:voter-did voter :choice choice :cast-at at}))

(def ^:private ballots
  (-> [] (v/cast (mk "v1" "yes" 110)) (v/cast (mk "v2" "yes" 120))
         (v/cast (mk "v3" "no" 130))  (v/cast (mk "v5" "abstain" 140))
         (v/cast (mk "v4" "yes" 200))))                    ; v4 outside the [100,148] window

(deftest tally-window-quorum-outcome
  (testing "only in-window ballots count; quorum + yes>no → accepted (golden from vote.py)"
    (let [t (v/tally ballots 100 150)]                     ; close=148, now=150 finalizable
      (is (= 2 (:yes t)))
      (is (= 1 (:no t)))
      (is (= 1 (:abstain t)))
      (is (= 4 (:voters t)))                               ; v4@200 excluded
      (is (= 148 (:close t)))
      (is (true? (:quorum-met t)))
      (is (true? (:finalizable t)))
      (is (= "accepted" (:outcome t))))))

(deftest pending-before-timelock
  (testing "before the 48h window closes the outcome is pending (never early)"
    (is (= "pending" (:outcome (v/tally ballots 100 120))))
    (is (false? (:finalizable (v/tally ballots 100 120))))))

(deftest thin-vote-rejected
  (testing "quorum not met → rejected, never auto-accepted"
    (let [thin (-> [] (v/cast (mk "a" "yes" 110)) (v/cast (mk "b" "yes" 120)))]
      (is (= "rejected" (:outcome (v/tally thin 100 150)))))))   ; 2 < quorum 3

(deftest one-sbt-one-vote
  (testing "a duplicate voter DID is rejected at cast time (1 SBT = 1 vote)"
    (is (thrown? Exception (v/cast ballots (mk "v1" "no" 125))))))

(deftest ballot-invariants
  (testing "weight 1, no-server-key, no :server/:anon voter, valid choice"
    (is (thrown? Exception (v/make-ballot {:voter-did "z" :choice "yes" :cast-at 1 :weight 2})))
    (is (thrown? Exception (v/make-ballot {:voter-did "z" :choice "yes" :cast-at 1 :server-held-key true})))
    (is (thrown? Exception (v/make-ballot {:voter-did "server" :choice "yes" :cast-at 1})))
    (is (thrown? Exception (v/make-ballot {:voter-did "did:server:x" :choice "yes" :cast-at 1})))
    (is (thrown? Exception (v/make-ballot {:voter-did "anon" :choice "yes" :cast-at 1})))
    (is (thrown? Exception (v/make-ballot {:voter-did "z" :choice "maybe" :cast-at 1})))
    (is (= "yes" (:choice (v/make-ballot {:voter-did "z" :choice ":yes" :cast-at 1}))))))   ; colon stripped

(deftest finalize-strict-timelock
  (testing "finalize RAISES before the timelock; succeeds after"
    (is (thrown? Exception (v/finalize ballots 100 120)))        ; 120 < 148
    (is (= "accepted" (:outcome (v/finalize ballots 100 150))))))

(deftest finalize-binding-r2
  (testing "binding finalize via the R2 autonomous gate; timelock still strict"
    (let [g  (lg/make-gate {:leg "vote"})
          fb (v/finalize-binding ballots 100 150 g)]
      (is (= "accepted" (:outcome fb)))
      (is (true? (:binding fb)))
      (is (= 7 (:council-level fb)))
      (is (thrown? Exception (v/finalize-binding ballots 100 120 g))))))  ; gate can't bypass timelock

(deftest live-gate-r2
  (testing "live-gate: known legs admissible (R2 autonomous); unknown leg raises"
    (is (true? (:admissible (lg/gate-status (lg/make-gate {:leg "provision"})))))
    (is (= 7 (second (lg/leg-policy "couple"))))             ; couple needs Lv7
    (is (thrown? Exception (lg/make-gate {:leg "bribe"})))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'fuchi.methods.test-vote)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
