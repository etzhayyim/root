(ns kaiyaku.agent
  "kaiyaku 解約 — the Clojure LangGraph actor (ADR-2606112201, cljc port on
  langgraph-clj).

      :ingest → :analyze → :plan → ‖interrupt‖ :approve → :rehearse → END

  The interrupt BEFORE :approve is the G5 member-sig gate in graph form: the
  graph halts with the dry-run plans on the thread's checkpoint; the MEMBER
  reviews them (human-in-the-loop) and resumes with {:approved [svc-id …]}.
  Only member-approved plans proceed — T2 plans are REHEARSED against the
  injected surface (R0: pure-data mock; live = G6-gated, not wired), T1/T3
  plans are emitted as prepared handoffs.

  Datomic premise: with a langgraph datomic-checkpointer every superstep is a
  checkpoint datom, and with a :history-conn every sub-agent action is an
  action datom — the whole 解約 session is a queryable audit trail (G9)."
  (:require [langgraph.graph :as g]
            [kaiyaku.ledger :as ledger]
            [kaiyaku.analyze :as analyze]
            [kaiyaku.plan :as plan]
            [kaiyaku.datoms :as datoms]
            [kaiyaku.executor :as executor]))

(defn- rehearse-one [{:keys [model browser-for computer-for history-conn max-steps]} p]
  (case (:tier p)
    "T2" (if-let [b (and browser-for (browser-for (:svc p)))]
           (executor/rehearse-browser!
            {:model model :browser b :plan p
             :history-conn history-conn :max-steps (or max-steps 12)})
           (if-let [c (and computer-for (computer-for (:svc p)))]
             (executor/rehearse-desktop!
              {:model model :computer c :plan p
               :history-conn history-conn :max-steps (or max-steps 12)})
             {:svc (:svc p) :tier "T2" :mode :dry-run :done false
              :note "no rehearsal surface injected — plan emitted only"}))
    "T1" {:svc (:svc p) :tier "T1" :mode :dry-run :done false
          :note "official-API cancel PREPARED — live call is G6-gated (Council Lv6+ + operator + member-sig)"}
    {:svc (:svc p) :tier "T3" :mode :dry-run :done false
     :note "self-submit 解約/退会 procedure generated — the MEMBER submits it themselves"}))

(defn build-actor
  "Compiles the kaiyaku actor graph.

  opts: {:model        ChatModel for T2 sub-agents (tests: langchain mock-model;
                       node deploys: executor/murakumo-model — G4)
         :browser-for  (fn [svc-id] → IBrowser | nil)  ; injected rehearsal surface
         :computer-for (fn [svc-id] → IComputer | nil) ; desktop-app surface
         :checkpointer langgraph checkpointer — REQUIRED: the member-sig
                       interrupt lives on the thread's checkpoint (G5)
         :history-conn optional datom action log for sub-agents (G9)
         :max-steps    sub-agent step budget}"
  [{:keys [checkpointer] :as opts}]
  (when-not checkpointer
    (throw (ex-info "G5: a checkpointer is required — the member-sig approval gate is a checkpointed interrupt"
                    {:gate :g5})))
  (-> (g/state-graph
       {:channels {:ledger-edn {}
                   :ledger     {}
                   :readout    {}
                   :plans      {:default []}
                   :approved   {:default []}
                   :rehearsals {:reducer (fnil into []) :default []}
                   :datoms     {:default []}}})
      (g/add-node :ingest
                  (fn [{:keys [ledger-edn]}]
                    {:ledger (ledger/parse ledger-edn)}))
      (g/add-node :analyze
                  (fn [{:keys [ledger]}]
                    {:readout (analyze/analyze ledger)}))
      (g/add-node :plan
                  (fn [{:keys [ledger readout]}]
                    {:plans  (plan/plans ledger readout)
                     :datoms (datoms/datoms ledger readout)}))
      (g/add-node :approve
                  ;; Runs only AFTER the interrupt resume carrying the member's
                  ;; approval (G5); narrows the plan set to the approved svc ids.
                  (fn [{:keys [plans approved]}]
                    {:plans (vec (filter (comp (set approved) :svc) plans))}))
      (g/add-node :rehearse
                  (fn [{:keys [plans]}]
                    {:rehearsals (mapv #(rehearse-one opts %) plans)}))
      (g/set-entry-point :ingest)
      (g/add-edge :ingest :analyze)
      (g/add-edge :analyze :plan)
      (g/add-edge :plan :approve)
      (g/add-edge :approve :rehearse)
      (g/compile-graph {:checkpointer checkpointer
                        :interrupt-before #{:approve}
                        :recursion-limit 50})))

(defn run-until-approval
  "Phase 1: ledger → readout → dry-run plans, halting at the member-sig gate.
  → run* result with :status :interrupted; plans at (-> out :state :plans)."
  [actor ledger-edn thread-id]
  (g/run* actor {:ledger-edn ledger-edn} {:thread-id thread-id}))

(defn resume-with-approval
  "Phase 2: the MEMBER's approval (svc ids) resumes the graph through
  :approve → :rehearse. Member-sig VERIFICATION is the membrane's duty
  upstream (WebAuthn / EIP-712); this graph models the gate itself."
  [actor thread-id approved-svc-ids]
  (g/run* actor {:approved (vec approved-svc-ids)}
          {:thread-id thread-id :resume? true}))
