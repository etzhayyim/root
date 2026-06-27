;; etzhayyim.sops-age — secrets layer for the kotoba-rad sovereign actor.
;;
;; ADR-2606241500 (this PR). Lets an actor carry SECRETS in git safely so it can
;; evolve code AND data through ordinary git (add/commit/push/PR/merge) without
;; ever committing a plaintext credential. The cipher is sops + age; the age
;; private key lives in macOS Keychain (NOT in the repo, NOT in any
;; etzhayyim-operated server) — the same custody model kotoba-rad uses for its
;; Ed25519 signing key, one service over from it:
;;
;;   etzhayyim.kotoba-rad  -> Ed25519 PKCS8  (SIGN  identity / sigrefs)
;;   etzhayyim.sops-age    -> AGE-SECRET-KEY (DECRYPT secrets)            ← here
;;
;; Two distinct keys (sign vs encrypt) by hygiene; both are MEMBER-held, never
;; platform-held (no-server-key, Charter substrate rule + ADR-2605231525).
;;
;; The actor's age RECIPIENT (its public key) is recorded as a datom on its
;; kotoba-rad identity journal (`:rad/age-recipient`), so the sovereign RID also
;; *declares who can decrypt its secrets* — encryption identity is bound to the
;; same content-addressed identity log as the signing identity. `.sops.yaml` is
;; GENERATED from those journals, so the human-facing `sops` workflow and the
;; sovereign identity never drift.
;;
;; clj/bb per the repo "Operational code = clj/bb over the kotoba Datom log"
;; rule; shelling to system binaries (sops/age/age-keygen/security) via
;; babashka.process is allowed (it is invocation, not authoring logic in shell).

(ns etzhayyim.sops-age
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [babashka.process :as p]
            [etzhayyim.kotoba.datom :as d]
            [etzhayyim.kotoba.log :as log]
            [etzhayyim.kotoba-rad :as rad])
  (:import (java.nio.file Files)
           (java.nio.file.attribute PosixFilePermissions FileAttribute)))

(def keychain-service "etzhayyim.sops-age")
(def org-account
  "Keychain account for the org-wide recovery recipient (operator key). Every
   actor's secrets also encrypt to this so the org can always recover even if an
   actor key is lost — sops multi-recipient, any one key decrypts."
  "__org__")

;; ── Keychain (member age key store; mirrors kotoba-rad-sign) ─────────────────

(defn keychain-read
  "Read the AGE-SECRET-KEY for `account` from macOS Keychain, or nil if absent."
  [account]
  (let [{:keys [exit out]} (p/sh "security" "find-generic-password"
                                 "-s" keychain-service "-a" account "-w")]
    (when (zero? exit) (str/trim (str out)))))

(defn keychain-store!
  "Store an AGE-SECRET-KEY under (keychain-service, account). -U updates."
  [account secret]
  (p/sh "security" "add-generic-password" "-U"
        "-s" keychain-service "-a" account
        "-l" (str "etzhayyim sops-age secret (" account ")")
        "-w" secret))

;; ── age key material ─────────────────────────────────────────────────────────

(defn recipient-of-secret
  "Derive the age recipient (public key, age1…) from an AGE-SECRET-KEY string."
  [secret]
  (let [{:keys [exit out err]} (p/sh {:in secret} "age-keygen" "-y")]
    (if (zero? exit)
      (str/trim (str out))
      (throw (ex-info "age-keygen -y failed" {:err (str/trim (str err))})))))

(defn gen-key
  "Generate a fresh age identity -> {:secret AGE-SECRET-KEY :recipient age1…}.
   Nothing is persisted; the caller stores :secret in Keychain."
  []
  (let [{:keys [exit out err]} (p/sh "age-keygen")
        text (str out)
        secret (some->> (str/split-lines text)
                        (filter #(str/starts-with? % "AGE-SECRET-KEY-"))
                        first str/trim)]
    (when-not (and (zero? exit) secret)
      (throw (ex-info "age-keygen failed" {:err (str/trim (str err))})))
    {:secret secret :recipient (recipient-of-secret secret)}))

;; ── recipient resolution (identity-journal first, Keychain fallback) ─────────

(defn journal-recipient
  "The `:rad/age-recipient` recorded on the actor's kotoba-rad identity journal,
   or nil. This is the SoT for `.sops.yaml` generation."
  [actor]
  (let [logv (log/read-log (rad/journal-path actor))]
    (->> (d/live-datoms logv)
         (filter (fn [[_ a _]] (= a :rad/age-recipient)))
         (map (fn [[_ _ v]] v))
         first)))

(defn keychain-recipient
  "Derive the recipient from the actor's Keychain secret, or nil if no key."
  [account]
  (some-> (keychain-read account) recipient-of-secret))

(defn org-recipient
  "Org-wide recovery recipient: env override, else the Keychain __org__ key."
  []
  (or (not-empty (System/getenv "ETZHAYYIM_AGE_ORG_RECIPIENT"))
      (keychain-recipient org-account)))

(defn recipients-for
  "Recipients an actor's secrets encrypt to: the actor's own recipient + the org
   recovery recipient (deduped, nils dropped). Any one of them can decrypt."
  [actor]
  (->> [(or (journal-recipient actor) (keychain-recipient actor)) (org-recipient)]
       (remove nil?) distinct vec))

;; ── bind the recipient into the sovereign identity log ───────────────────────

(defn record-recipient!
  "Append `:rad/age-recipient` for the actor onto its kotoba-rad identity journal,
   entity = the RID (so the recipient is part of the sovereign identity). `genesis`
   gives the RID; idempotent (no-op if the same recipient is already live)."
  [actor genesis recipient]
  (let [path (rad/journal-path actor)
        e (rad/rid genesis)
        existing (log/read-log path)
        live? (contains? (d/live-datoms existing) [e :rad/age-recipient recipient])]
    (if live?
      {:appended 0 :recipient recipient :rid e}
      (let [tx (inc (log/max-tx existing))]
        (log/append! path [(d/datom e :rad/age-recipient recipient tx)])
        {:appended 1 :recipient recipient :rid e}))))

;; ── sops invocation (decrypt key sourced from Keychain, never disk-resident) ─

(defn- with-key-file
  "Run (f age-key-file-path) with `secret` written to a 0600 temp file, deleted
   afterward. The secret never lives at a stable path on disk."
  [secret f]
  (let [perms (PosixFilePermissions/asFileAttribute
               (PosixFilePermissions/fromString "rw-------"))
        tmp (Files/createTempFile "etzhayyim-age-" ".key"
                                  (into-array FileAttribute [perms]))
        path (str (.toAbsolutePath tmp))]
    (try
      (spit path (str secret "\n"))
      (f path)
      (finally (io/delete-file path true)))))

(defn decrypt-with-secret
  "sops-decrypt `path` using an explicit AGE-SECRET-KEY string. Returns plaintext.
   (The Keychain-sourced public entry point is `decrypt-file`.)"
  [secret path]
  (with-key-file
    secret
    (fn [key-file]
      (let [{:keys [exit out err]}
            (p/sh {:extra-env {"SOPS_AGE_KEY_FILE" key-file "SOPS_CONFIG" "/dev/null"}}
                  "sops" "decrypt" path)]
        (when-not (zero? exit)
          (throw (ex-info "sops decrypt failed" {:err (str/trim (str err)) :path path})))
        (str out)))))

(defn- resolve-secret [actor]
  (or (keychain-read actor) (keychain-read org-account)
      (not-empty (System/getenv "SOPS_AGE_KEY"))
      (throw (ex-info (str "no age secret in Keychain for " actor
                           " (run: bb sops:keygen " actor " --apply)")
                      {:actor actor}))))

(defn- input-type [path]
  (let [ext (last (str/split path #"\."))]
    (case ext
      ("env") "dotenv"
      ("yaml" "yml") "yaml"
      ("json") "json"
      "binary")))

(defn enc-path
  "Plaintext `secrets/foo.env` -> ciphertext `secrets/foo.enc.env` (the form
   `.sops.yaml` path_regex matches and that is safe to commit)."
  [plain]
  (let [i (.lastIndexOf ^String plain ".")]
    (if (neg? i) (str plain ".enc")
        (str (subs plain 0 i) ".enc" (subs plain i)))))

(defn encrypt-file!
  "sops-encrypt `in` to `out` (default (enc-path in)) for the actor's recipients.
   Structured types (env/yaml/json) keep keys visible & encrypt values; anything
   else is encrypted whole as `binary`. Returns {:in :out :recipients :exit}."
  ([actor in] (encrypt-file! actor in (enc-path in)))
  ([actor in out]
   (let [recips (recipients-for actor)
         it (input-type in)]
     (when (empty? recips)
       (throw (ex-info (str "no age recipient for " actor
                            " (run: bb sops:keygen " actor " --apply)")
                       {:actor actor})))
     ;; SOPS_CONFIG=/dev/null bypasses any repo .sops.yaml: recipients come from
     ;; the identity journal (the SoT) via explicit --age, so encryption is
     ;; deterministic even before/without a matching creation_rule. (.sops.yaml
     ;; stays the convenience map for humans running bare `sops`.)
     (let [{:keys [exit err]}
           (p/sh {:extra-env {"SOPS_CONFIG" "/dev/null"}}
                 "sops" "encrypt" "--age" (str/join "," recips)
                 "--input-type" it "--output-type" (if (= it "binary") "json" it)
                 "--output" out in)]
       (when-not (zero? exit)
         (throw (ex-info "sops encrypt failed" {:err (str/trim (str err)) :in in})))
       {:in in :out out :recipients recips :exit exit}))))

(defn decrypt-file
  "sops-decrypt `path` (uses the actor's Keychain age key). Returns plaintext
   string. Read-only; nothing is written to disk except the transient key file."
  [actor path]
  (decrypt-with-secret (resolve-secret actor) path))

;; ── .sops.yaml generation (from the identity journals — SoT) ─────────────────

(defn discover-actor-recipients
  "Scan 80-data/kotoba-rad/*.identity.journal.edn for `:rad/age-recipient`.
   Returns a sorted seq of [actor recipient]."
  []
  (let [dir (io/file rad/journal-dir)]
    (when (.isDirectory dir)
      (->> (.listFiles dir)
           (keep (fn [f]
                   (let [n (.getName f)]
                     (when (str/ends-with? n ".identity.journal.edn")
                       (let [actor (subs n 0 (- (count n) (count ".identity.journal.edn")))]
                         (when-let [r (journal-recipient actor)] [actor r]))))))
           (sort-by first)))))

(defn sops-yaml-text
  "Render `.sops.yaml` creation_rules: one per-actor rule (actor + org recovery
   recipients) then an org-wide fallback for any other `*.enc.*` path."
  [actor->recip org-r]
  (let [rule (fn [actor r]
               (str "  - path_regex: ^20-actors/" actor "/secrets/.*\\.enc\\.[^/]+$\n"
                    "    key_groups:\n"
                    "      - age:\n"
                    (str/join (for [a (->> [r org-r] (remove nil?) distinct)]
                                (str "          - " a "\n")))))
        body (str (str/join (for [[a r] actor->recip] (rule a r)))
                  (when org-r
                    (str "  - path_regex: \\.enc\\.[^/]+$\n"
                         "    key_groups:\n"
                         "      - age:\n"
                         "          - " org-r "\n")))]
    ;; NB: this is YAML (sops parses it) — comments are '#', NOT ';;'.
    (str "# GENERATED by `bb sops:yaml` (etzhayyim.sops-age) — DO NOT hand-edit.\n"
         "# SoT = the per-actor :rad/age-recipient on each kotoba-rad identity\n"
         "# journal (80-data/kotoba-rad/<actor>.identity.journal.edn).\n"
         "# No actor has onboarded a recipient yet. Run `bb sops:keygen <actor> --apply`\n"
         "# then `bb actor:evolve <actor> --apply` to record :rad/age-recipient and\n"
         "# regenerate this file. (encrypt always also passes --age explicitly.)\n"
         (if (str/blank? body)
           "creation_rules: []\n"
           (str "creation_rules:\n" body)))))

(defn gen-sops-yaml!
  "Write `.sops.yaml` from the identity journals. Returns {:path :actors :org?}."
  ([] (gen-sops-yaml! ".sops.yaml"))
  ([out]
   (let [pairs (discover-actor-recipients)
         org-r (org-recipient)]
     (spit out (sops-yaml-text pairs org-r))
     {:path out :actors (mapv first pairs) :org? (boolean org-r)})))

;; ── CLI ──────────────────────────────────────────────────────────────────────

(defn -keygen
  "bb sops:keygen <actor|__org__> [--apply]. Generates an age identity, prints the
   recipient. With --apply stores the secret in Keychain (member key); without,
   prints the secret DRY-RUN (NOT stored)."
  [& args]
  (let [account (first (remove #(str/starts-with? % "--") args))
        apply? (contains? (set args) "--apply")]
    (when-not account
      (println "usage: bb sops:keygen <actor|__org__> [--apply]") (System/exit 2))
    (let [{:keys [secret recipient]} (gen-key)]
      (println "account   " account)
      (println "recipient " recipient)
      (if apply?
        (do (keychain-store! account secret)
            (println "stored    secret in Keychain:" keychain-service "/" account)
            (println "next      bb sops:yaml   (regenerate .sops.yaml)"))
        (do (println "secret    (DRY-RUN, NOT stored — pass --apply):")
            (println secret))))))

(defn -yaml [& _]
  (let [{:keys [path actors org?]} (gen-sops-yaml!)]
    (println "wrote" path "— actors:" (str/join "," actors) "org-recovery:" org?)))

(defn -encrypt [& args]
  (let [[actor in out] (remove #(str/starts-with? % "--") args)]
    (when-not (and actor in)
      (println "usage: bb sops:encrypt <actor> <in> [out]") (System/exit 2))
    (let [r (encrypt-file! actor in (or out (enc-path in)))]
      (println "encrypted" (:in r) "->" (:out r)
               "for" (str/join "," (:recipients r))))))

(defn -decrypt [& args]
  (let [[actor path] (remove #(str/starts-with? % "--") args)]
    (when-not (and actor path)
      (println "usage: bb sops:decrypt <actor> <file.enc.*>") (System/exit 2))
    (print (decrypt-file actor path)) (flush)))
