(ns ibuki.methods.test-charter-invariants
  "test-charter-invariants — 息吹 (ibuki) charter invariants across every home.
  ADR-2606101200. Clojure port of `methods/test_charter_invariants.py`.

  The gates this package must keep, each enforced structurally (unrepresentable, not
  configured):
    G6 Murakumo-only inference (ADR-2605215000)   — infer allowlist
    G7 no-server-key (ADR-2605231525)             — drainer envelopes + submit injection
    G8 outward-gated                              — :post/status :dry-run / :drain/status :prepared
    N7 no parallel substrate                      — kotoba Datom log only, no SQL/RW requires
    非終末論 append-only                           — :db/add only, no retract anywhere

  Tests that exercise modules NOT yet ported to Clojure (member-submit, perception,
  receipts, kotoba-bridge, kaizen-outcomes) remain Python-only in
  `test_charter_invariants.py`; the source scans here cover the PORTED .cljc surface."
  (:require [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is]]
            [ibuki.methods.datoms :as datoms]
            [ibuki.methods.digest :as digest]
            [ibuki.methods.drainer :as drainer]
            [ibuki.methods.infer :as infer]
            [ibuki.methods.joucho :as joucho]
            [ibuki.methods.kaizen-feedback :as kaizen-feedback]
            [ibuki.methods.symbiosis :as symbiosis]))

(def ^:private source-names
  ["autorun" "datoms" "digest" "drainer" "ecosystem" "health" "heartbeat"
   "infer" "joucho" "kaizen_feedback" "quorum" "symbiosis"])

(defn- all-source
  "name → source text for every ported (non-test) .cljc in ibuki/methods."
  []
  (into {} (map (fn [n]
                  [n (slurp (io/resource (str "ibuki/methods/" n ".cljc")))]))
        source-names))

(defn- tmpdir []
  (str (java.nio.file.Files/createTempDirectory
        "ibuki-charter" (make-array java.nio.file.attribute.FileAttribute 0))))

(defn- thrown-msg
  "Run f, return the ex message it throws (nil if it does not throw)."
  [f]
  (try (f) nil
       (catch Exception e (ex-message e))))

;; ── G6 Murakumo-only ───────────────────────────────────────────────────────

(deftest g6-only-murakumo-hosts-in-allowlist
  (is (every? #{"127.0.0.1:4000" "localhost:4000" "192.168.1.70:8077"
                "192.168.1.70:11434" "127.0.0.1:11434" "localhost:11434"}
              infer/murakumo-allowed-hosts)))

(deftest g6-commercial-inference-unrepresentable
  (is (str/includes?
       (str (thrown-msg #(infer/assert-murakumo "https://api.openai.com/v1/chat/completions")))
       "Murakumo"))
  (is (str/includes?
       (str (thrown-msg #(infer/narrate "t" "c" "calm" "x"
                                        {:endpoint "https://api.runpod.ai/v2/x/run"})))
       "Murakumo")))

(deftest g6-no-commercial-provider-strings-in-source
  (doseq [[name src] (all-source)
          banned ["api.openai.com" "runpod" "bedrock" "vertexai"
                  "generativelanguage.googleapis"]]
    (is (not (str/includes? (str/lower-case src) banned))
        (str name " references " banned))))

;; ── G7 no-server-key ───────────────────────────────────────────────────────

(deftest g7-server-never-signs
  (let [env (drainer/envelope {"v" 1 "ts" 1 "actorDid" "did:web:x" "mood" "calm"
                               "contentSourceKind" "k" "text" "t"
                               "lexicon" "app.bsky.feed.post" "createdAt" "2026-06-10"})]
    (is (false? (get env "serverHeldKey")))
    (is (true? (get env "requiresMemberSignature")))
    (is (str/includes? (str (thrown-msg #(drainer/submit [env]))) "no member signer"))))

(deftest g7-drainer-has-no-network-or-credential-path
  (let [src (get (all-source) "drainer")]
    (doseq [needle ["urllib" "http-client" "http.client" "socket" "getenv" "environ"]]
      (is (not (str/includes? src needle))
          (str "drainer must be offline + credential-free: " needle)))))

;; ── G8 outward-gated ───────────────────────────────────────────────────────

(deftest g8-published-status-unwritable
  (let [dir (tmpdir)
        q (str dir "/q.ndjson")]
    (spit q (str "{\"v\":1,\"ts\":1,\"actorDid\":\"did:web:x\",\"mood\":\"calm\","
                 "\"contentSourceKind\":\"k\",\"text\":\"t\","
                 "\"lexicon\":\"app.bsky.feed.post\",\"createdAt\":\"2026-06-10\"}\n"))
    (let [out (drainer/drain q {:as-of 1 :beat 1})
          statuses (set (for [[_op _e a v] (:datoms out) :when (= a ":drain/status")] v))]
      (is (= #{":prepared"} statuses))))
  (let [src (all-source)]
    (is (not (str/includes? (get src "drainer") "\":published\"")))
    (is (not (str/includes? (get src "autorun") "\":published\"")))))

(deftest g8-autorun-post-status-literal-is-dry-run
  (is (str/includes? (get (all-source) "autorun")
                     "\":post/status\" \":dry-run\"")))

;; ── N7 no parallel substrate ───────────────────────────────────────────────

(deftest n7-no-parallel-substrate-requires
  (doseq [[name src] (all-source)
          banned ["psycopg" "sqlalchemy" "risingwave" "kysely" "sqlite"
                  "duckdb" "lancedb"]]
    (is (not (str/includes? (str/lower-case src) banned))
        (str name " pulls in a parallel substrate: " banned))))

;; ── 非終末論 append-only ───────────────────────────────────────────────────

(deftest append-only-no-retract-representable
  (doseq [[name src] (all-source)]
    (is (not (str/includes? src ":db/retract"))
        (str name " makes retraction representable (非終末論)")))
  (let [d (datoms/add "e" ":a/b" 1)]
    (is (= ":db/add" (nth d 0)))))

;; ── closed vocabularies ────────────────────────────────────────────────────

(deftest closed-vocabularies-raise-not-guess
  (let [base (joucho/scores)]
    (is (str/includes? (str (thrown-msg #(joucho/fold-event base ":event/invented" base)))
                       "closed vocab")))
  (let [dir (tmpdir)
        p (str dir "/o.ndjson")]
    (spit p "{\"proposalId\":\"p\",\"rule\":\"r\",\"outcome\":\"deployed\"}\n")
    (is (str/includes? (str (thrown-msg #(kaizen-feedback/read-outcomes p)))
                       "closed vocab"))))

;; ── 共生 member-principal draw ─────────────────────────────────────────────

(deftest symbiosis-draw-is-member-principal-keyfree
  ;; A commons draw can only happen by a MEMBER (injected signer + operator ack); ibuki
  ;; holds no key and never auto-draws the colony's gift on a human's behalf.
  (is (str/includes?
       (str (thrown-msg #(symbiosis/draw [] 1 {:member "did:web:x" :beat 1 :as-of 1})))
       "no member signer"))
  (is (str/includes?
       (str (thrown-msg #(symbiosis/draw [] 1 {:member "did:web:x" :beat 1 :as-of 1
                                               :member-signer identity})))
       "operator_ack"))
  (let [src (get (all-source) "symbiosis")]
    (doseq [needle ["urllib" "password" "accessJwt" "Authorization"]]
      (is (not (str/includes? src needle))
          (str "symbiosis must stay key-free + offline: " needle)))))

;; ── colony digest (G6 + G8) ────────────────────────────────────────────────

(deftest digest-is-murakumo-only-and-dry-run
  ;; The colony digest reasons via the Murakumo fleet ONLY (G6) and reports DRY-RUN only
  ;; (G8): :published is unrepresentable, exactly like organism posts.
  (let [src (get (all-source) "digest")]
    (is (not (str/includes? src "\":published\"")))
    (is (str/includes? src "\":dry-run\""))
    (doseq [banned ["api.openai.com" "runpod" "bedrock" "http://" "https://"]]
      (is (not (str/includes? (str/lower-case src) banned))
          (str "digest must route inference via ibuki.methods.infer: " banned)))))

(deftest infer-text-enforces-murakumo-allowlist
  (is (str/includes?
       (str (thrown-msg
             #(infer/infer-text "p" "fallback"
                                {:endpoint "https://api.openai.com/v1/chat/completions"})))
       "Murakumo")))

;; ── stdlib-only (require surface) ──────────────────────────────────────────

(deftest stdlib-only-require-surface
  ;; Every namespace a ported module requires is either platform (clojure.*), the ibuki
  ;; method family, the shared kotoba.datom substrate, or a bb built-in (cheshire /
  ;; babashka.*) — no third-party dependency enters the organism (the Python suite proves
  ;; the same over `import`).
  (doseq [[name src] (all-source)
          ns-token (map second (re-seq #"\[\s*([a-zA-Z][\w\-]*(?:\.[\w\-]+)+)" src))]
    (is (some #(str/starts-with? ns-token %)
              ["clojure." "ibuki.methods." "kotoba." "cheshire." "babashka."])
        (str name " requires third-party namespace " ns-token))))

;; NOTE — Python-only invariants (their modules are not yet ported to Clojure):
;;   test_g7_member_submission_is_member_principal_only   (member_submit.py)
;;   test_perception_is_readonly_allowlisted              (perception.py)
;;   test_receipts_never_assert_published                 (receipts.py)
;;   test_kotoba_bridge_targets_the_fleet_only            (kotoba_bridge.py)
;;   test_kaizen_outcomes_is_operator_principal_readonly  (kaizen_outcomes.py)
;; They remain covered by `test_charter_invariants.py`.
