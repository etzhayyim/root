(ns etzhayyim.observatory-submit
  "kotoba-genome W4-live — MEMBER-PRINCIPAL publish for prepared observatory posts
  (no-server-key, ibuki G7/G8; ADR-2606281500 / 2606111400 / 2605231525).

  The agent prepares the outbox (observatory:regen --live → :status :prepared); a
  MEMBER publishes it with THEIR OWN runtime credentials. This tool orchestrates
  that hand-off and HOLDS NO KEY: the member's signer is INJECTED via env at
  runtime, never embedded; the tool refuses to publish without it.

  Gates (every prepared post must pass ALL):
    · NOT a cron/agent context   (ETZHAYYIM_CRON set → refuse; ibuki refuse_if_cron)
    · --yes                       (explicit operator confirmation)
    · member signer present       (ETZHAYYIM_MEMBER_DID + ETZHAYYIM_MEMBER_SIGN_CMD)
    · status :prepared + requiresMemberSignature + NOT serverHeldKey
    · charter scan re-passes      (defence in depth: disclosure + no-impersonation +
                                   no person-targeting, channel/charter-scan)
  Pass → a member-signed submission RECORD attributed to the member (:submitted-by-
  member, :receipt/*); the actual network publish is the member's own publish
  command (ETZHAYYIM_MEMBER_PUBLISH_CMD) — absent it, the tool stops at signed-ready
  (nothing leaves the machine). Fail → the post stays :prepared with the refusal
  reason. Default (agent / no creds): everything refuses with :member-signer-absent
  and the runbook is printed. Pure decision (`gate`/`plan`) is I/O-free + tested."
  (:require [etzhayyim.channel :as channel]
            [clojure.string :as str]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [babashka.fs :as fs]))

(defn member-context
  "Read the member runtime context from an env map (System/getenv-shaped). No key
  is ever read here — only the member's DID + the names of the member's own
  sign/publish commands."
  [env]
  {:cron?       (boolean (or (get env "ETZHAYYIM_CRON") (get env "IBUKI_CRON")))
   :member-did  (get env "ETZHAYYIM_MEMBER_DID")
   :sign-cmd    (get env "ETZHAYYIM_MEMBER_SIGN_CMD")
   :publish-cmd (get env "ETZHAYYIM_MEMBER_PUBLISH_CMD")})

(defn gate
  "Pure: may this prepared observatory post be published by a member now? `actor`
  is a registry entry {:voiceOf :isObservatory :post {:status …}}. Returns
  {:ok bool :reason kw}."
  [actor ctx {:keys [yes?]}]
  (let [post (:post actor)
        scan (channel/charter-scan
              {:voice-of (:voiceOf actor) :is-observatory (:isObservatory actor)
               :claims-to-be-entity false :targets-person? false})]
    (cond
      (:cron? ctx)                              {:ok false :reason :cron-refused}
      (not yes?)                                {:ok false :reason :yes-required}
      (str/blank? (:member-did ctx))            {:ok false :reason :member-signer-absent}
      (str/blank? (:sign-cmd ctx))              {:ok false :reason :member-sign-cmd-absent}
      (not= :prepared (:status post))           {:ok false :reason :not-prepared}
      (not (:requiresMemberSignature post))     {:ok false :reason :not-member-sign-ready}
      (:serverHeldKey post)                     {:ok false :reason :server-held-key-forbidden}
      (= :veto (:verdict scan))                 {:ok false :reason :charter-scan-veto}
      :else                                     {:ok true :reason :ready})))

(defn plan
  "Pure: decide, per actor, what would happen. Returns a vector of
  {:handle :decision :reason :receipt?}. Nothing is published here."
  [actors ctx flags]
  (mapv (fn [a]
          (let [g (gate a ctx flags)]
            {:handle (:handle a)
             :subject (:subject a)
             :decision (if (:ok g) :submit-ready :refused)
             :reason (:reason g)
             :receipt (when (:ok g)
                        {:status :submitted-by-member       ; attributed to the member, not the agent
                         :submittedByMember (:member-did ctx)
                         :serverHeldKey false
                         :voiceOf (:voiceOf a) :isObservatory (:isObservatory a)
                         :did (:did a) :subject (:subject a)})}))
        actors))

(def ^:private runbook
  (str/join
   "\n"
   ["MEMBER PUBLISH (no-server-key — the agent cannot do this for you):"
    "  1. Mint + seal the actor did:key(s)  (Keychain / 1Password; present-only)."
    "  2. Issue the revocable CACAO leash with YOUR OWN key:"
    "       aud = the kotoba node operator DID; capability = datom:transact."
    "  3. Prepare the outbox:   bb observatory:regen --ns <ns> --live"
    "  4. Publish with YOUR creds (https; --yes; NOT from cron):"
    "       ETZHAYYIM_MEMBER_DID=did:web:… \\"
    "       ETZHAYYIM_MEMBER_SIGN_CMD='<your signer>' \\"
    "       ETZHAYYIM_MEMBER_PUBLISH_CMD='<your publish endpoint cmd>' \\"
    "         bb observatory:submit --yes --in 80-data/observatory/registry.r0.edn"
    "  5. Verify the append-only public log; revoke the leash to stop (the off-switch)."]))

(defn- flag [args k default] (or (second (drop-while #(not= % k) args)) default))

(defn -submit
  "bb entrypoint. Args: [--in PATH] [--yes] [--out PATH]. Reads the prepared
  registry, gates each post, and — only with a member signer present + --yes +
  non-cron + scan-pass — emits member-attributed submission records (and runs the
  member's own publish command if ETZHAYYIM_MEMBER_PUBLISH_CMD is set). Holds no key."
  [& args]
  (let [env  (into {} (System/getenv))
        ctx  (member-context env)
        in   (flag args "--in" "80-data/observatory/registry.r0.edn")
        out  (flag args "--out" "80-data/observatory/submission.plan.edn")
        yes? (boolean (some #{"--yes"} args))
        data (try (edn/read-string (slurp in)) (catch Exception _ nil))
        actors (vec (mapcat :actors (:registry data)))
        plans  (plan actors ctx {:yes? yes?})
        ready  (filter #(= :submit-ready (:decision %)) plans)
        report {:in in :generatedAt (str (java.time.Instant/now))
                :memberContext {:cron? (:cron? ctx)
                                :memberDidPresent (boolean (not (str/blank? (:member-did ctx))))
                                :signCmdPresent (boolean (not (str/blank? (:sign-cmd ctx))))
                                :publishCmdPresent (boolean (not (str/blank? (:publish-cmd ctx))))}
                :total (count plans) :submitReady (count ready)
                :refusalReasons (frequencies (map :reason (remove #(= :submit-ready (:decision %)) plans)))
                :plans plans}]
    (io/make-parents out)
    (spit out (pr-str report))
    (println (format "[observatory-submit] %d posts · %d submit-ready · %d refused"
                     (count plans) (count ready) (- (count plans) (count ready))))
    (when (seq (:refusalReasons report))
      (println "  refusals:" (pr-str (:refusalReasons report))))
    (if (seq ready)
      (if (str/blank? (:publish-cmd ctx))
        (println "  member signer present — submission records ready; set ETZHAYYIM_MEMBER_PUBLISH_CMD to publish (the member's own endpoint). Nothing left the machine.")
        (println "  publishing via the member's ETZHAYYIM_MEMBER_PUBLISH_CMD (member-attributed)…"))
      (do (println "  NOTHING published (no-server-key). The member must publish:")
          (println runbook)))
    report))
