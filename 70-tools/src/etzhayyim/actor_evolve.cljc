;; etzhayyim.actor-evolve — `bb actor:evolve <name>` git lifecycle for an actor.
;;
;; ADR-2606241500 (this PR). The C-axis (self-evolution) companion to
;; actor:publish (ADR-2606231200): an actor evolves BOTH its CODE
;; (20-actors/<name>/**) and its DATA (80-data/<name>/** + its kotoba-rad
;; identity journal) through ordinary git — branch → encrypt-secrets → commit →
;; push → PR create → merge — with its secrets carried as sops+age ciphertext
;; (etzhayyim.sops-age) so a credential is NEVER committed in the clear.
;;
;; Each evolution is also recorded as a `:rad/evolution` datom on the actor's
;; sovereign identity log and the data-log head is re-attested (sigref) with the
;; member's key — so the same content-addressed, signed identity that names the
;; actor (kotoba-rad RID/did:key) also witnesses every code+data step.
;;
;; DRY-RUN BY DEFAULT. `--apply` permits local mutation (encrypt + branch +
;; commit + identity append). The OUTWARD legs are separately gated:
;;   --push   git push the branch        (needs --apply)
;;   --pr     gh pr create               (needs --apply --push)
;;   --merge  gh pr merge --squash       (needs --apply --push --pr)
;; no-server-key: push/PR/merge use the MEMBER's gh+git creds; signing uses the
;; member's Keychain key. This tool holds nothing.
;;
;; clj/bb per the repo rule; git/gh/sops are shelled via babashka.process.

(ns etzhayyim.actor-evolve
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [babashka.process :as p]
            [etzhayyim.kotoba.datom :as d]
            [etzhayyim.kotoba.log :as log]
            [etzhayyim.kotoba-rad :as rad]
            [etzhayyim.kotoba-rad-sign :as rad-sign]
            [etzhayyim.sops-age :as sops]
            [etzhayyim.actor-publish :as pub]))

(defn code-prefix [actor] (str "20-actors/" actor))
(defn data-prefix [actor] (str "80-data/" actor))
(defn secrets-dir  [actor] (str "20-actors/" actor "/secrets"))

(defn slugify [s]
  (-> (or s "evolve") str/lower-case
      (str/replace #"[^a-z0-9]+" "-") (str/replace #"(^-+|-+$)" "")
      (#(if (str/blank? %) "evolve" (subs % 0 (min 40 (count %)))))))

;; ── secrets: encrypt plaintext under secrets/ before anything is staged ──────

(def ^:private structured-exts #{"env" "yaml" "yml" "json" "edn" "txt"})

(defn plaintext-secrets
  "Plaintext secret files under the actor's secrets/ dir (i.e. files that are NOT
   already `.enc.*` and carry a known secret extension). These must be encrypted
   (or are git-ignored) — never committed raw."
  [actor]
  (let [dir (io/file (secrets-dir actor))]
    (when (.isDirectory dir)
      (->> (file-seq dir)
           (filter #(.isFile %))
           (map #(.getPath %))
           (remove #(str/includes? % ".enc."))
           (filter #(structured-exts (last (str/split % #"\."))))
           sort))))

(defn encrypt-secrets!
  "Encrypt every plaintext secret to its `.enc.*` sibling. Returns a seq of
   {:in :out :recipients}. No-op (empty) when there are none."
  [actor apply?]
  (for [in (plaintext-secrets actor)]
    (let [out (sops/enc-path in)]
      (if apply?
        (sops/encrypt-file! actor in out)
        {:in in :out out :recipients (sops/recipients-for actor) :planned true}))))

;; ── git helpers ──────────────────────────────────────────────────────────────

(defn- git [& args] (apply p/sh "git" args))
(defn- git-ok? [& args] (zero? (:exit (apply git args))))

(defn current-branch []
  (str/trim (str (:out (git "rev-parse" "--abbrev-ref" "HEAD")))))

(defn tracked-paths
  "Pathspecs to stage: code + data + identity journal + .sops.yaml. Only those
   that exist, so `git add` never errors on an absent tree."
  [actor]
  (->> [(code-prefix actor)
        (data-prefix actor)
        (str rad/journal-dir "/" actor ".identity.journal.edn")
        ".sops.yaml"]
       (filter #(.exists (io/file %)))
       vec))

;; ── identity: record the evolution + re-attest the signed head ───────────────

(defn record-evolution!
  "Append a `:rad/evolution` datom (entity = RID) describing this step and a
   fresh sigref re-attesting the data-log head. Signed iff the member key is in
   Keychain (pub-hex known). Returns {:rid :head :signed? :appended}."
  [actor genesis branch message pubkey-hex apply?]
  (let [path (rad/journal-path actor)
        rid* (rad/rid genesis)
        value (str branch "|" (slugify message))]
    (if-not apply?
      {:rid rid* :planned true :value value}
      (let [existing (log/read-log path)
            tx (inc (log/max-tx existing))
            ev (d/datom rid* :rad/evolution value tx)
            after (conj (vec existing) ev)
            head (log/head-cid after)
            sign-fn (when pubkey-hex (rad-sign/sign-fn-for-actor actor pubkey-hex))
            {:keys [by sig]} (when sign-fn (sign-fn head))
            sigs (rad/sigref-datom rid* head (or by (:rad/did-web genesis)) sig tx)]
        (log/append! path (into [ev] sigs))
        {:rid rid* :head head :signed? (boolean sig) :appended (inc (count sigs))}))))

;; ── driver ───────────────────────────────────────────────────────────────────

(defn evolve-one
  [actor {:keys [apply? push? pr? merge? message pubkey-hex]}]
  (let [manifest (pub/read-manifest actor)
        _ (when-not manifest
            (throw (ex-info (str "no manifest for " actor) {:actor actor})))
        genesis (pub/manifest->genesis actor manifest :pubkey-hex pubkey-hex)
        branch (str "evolve/" actor "/" (slugify message))
        mode (if apply? "APPLY" "DRY-RUN")]
    (println (format "▶ actor:evolve %s  (%s)  branch=%s" actor mode branch))

    ;; 0. bind the actor's age recipient to its sovereign identity (if a key is
    ;;    in Keychain and the journal doesn't yet declare it) — encryption
    ;;    identity recorded on the same content-addressed log as the signing one.
    (when apply?
      (when-let [kr (and (not (sops/journal-recipient actor))
                         (sops/keychain-recipient actor))]
        (let [r (sops/record-recipient! actor genesis kr)]
          (println "  [kotoba-rad] bound :rad/age-recipient" kr
                   (str "(appended=" (:appended r) ")")))))

    ;; 1. secrets → ciphertext (+ keep .sops.yaml current)
    (let [secs (encrypt-secrets! actor apply?)]
      (when apply? (sops/gen-sops-yaml!))
      (doseq [s secs]
        (println "  [secrets] " (:in s) "->" (:out s)
                 (str "(" (str/join "," (:recipients s)) ")")))
      (when (empty? secs) (println "  [secrets]  none under" (secrets-dir actor)))
      (when-let [leftover (and apply? (seq (plaintext-secrets actor)))]
        ;; plaintext still present (it is git-ignored, just warn it won't be committed)
        (println "  [secrets]  NOTE plaintext kept locally (git-ignored):"
                 (str/join " " leftover))))

    ;; 2. branch
    (let [paths (tracked-paths actor)]
      (if apply?
        (do (git "checkout" "-B" branch)
            (println "  [git]      checkout -B" branch))
        (println "  [git]      PLAN: git checkout -B" branch))

      ;; 3. stage code + data + identity + .sops.yaml (scoped pathspec)
      (if apply?
        (do (apply git "add" "--" paths)
            (println "  [git]      add" (str/join " " paths)))
        (println "  [git]      PLAN: git add --" (str/join " " paths)))

      ;; 4. record the evolution on the sovereign identity log (data + sig)
      (let [ev (record-evolution! actor genesis branch message pubkey-hex apply?)]
        (println "  [kotoba-rad]" (if (:planned ev)
                                    (str "PLAN: append :rad/evolution to "
                                         (rad/journal-path actor))
                                    (str "evolution head=" (:head ev)
                                         " signed=" (:signed? ev))))
        ;; re-stage the journal now that the evolution datom landed
        (when apply?
          (git "add" "--" (str rad/journal-dir "/" actor ".identity.journal.edn"))))

      ;; 5. commit
      (let [msg (or message (str "evolve(" actor "): code + data"))
            full (str msg "\n\nrad: " (rad/rad-uri genesis)
                      "\nActor self-evolution via bb actor:evolve (ADR-2606241500).")]
        (if apply?
          ;; the index already holds ONLY our scoped paths (isolated worktree);
          ;; commit it. Empty index => non-zero exit, surfaced below.
          (let [{:keys [exit out err]} (git "commit" "-m" full)]
            (println "  [git]      commit exit=" exit
                     (when (seq (str out)) (str " | " (str/trim (str out))))
                     (when (and (pos? exit) (seq (str err))) (str " | " (str/trim (str err))))))
          (println "  [git]      PLAN: git commit -m" (pr-str msg))))

      ;; 6. push / PR / merge (each separately gated)
      (let [repo (str "etzhayyim/" (pub/repo-name actor))]
        (when push?
          (if apply?
            (let [{:keys [exit]} (git "push" "-u" "origin" branch)]
              (println "  [git]      push exit=" exit))
            (println "  [git]      PLAN: git push -u origin" branch)))
        (when pr?
          (if (and apply? push?)
            (let [{:keys [exit out err]}
                  (p/sh "gh" "pr" "create" "--base" "main" "--head" branch
                        "--title" (or message (str "evolve(" actor ")"))
                        "--body" (str "Actor self-evolution (code+data) for `" actor
                                      "`.\n\nrad: " (rad/rad-uri genesis)))]
              (println "  [gh]       pr create exit=" exit
                       (str " | " (str/trim (str (if (zero? exit) out err))))))
            (println "  [gh]       PLAN: gh pr create --base main --head" branch)))
        (when merge?
          (if (and apply? push? pr?)
            (let [{:keys [exit out err]}
                  (p/sh "gh" "pr" "merge" branch "--squash" "--delete-branch")]
              (println "  [gh]       pr merge exit=" exit
                       (str " | " (str/trim (str (if (zero? exit) out err))))))
            (println "  [gh]       PLAN: gh pr merge" branch "--squash --delete-branch"))))

      (println (format "✔ %s  rad=%s  branch=%s\n" actor (rad/rad-uri genesis) branch))
      {:actor actor :branch branch :rad-uri (rad/rad-uri genesis)})))

(defn -main [& args]
  (let [flags (set (filter #(str/starts-with? % "--") args))
        msg (some->> args (filter #(str/starts-with? % "--message="))
                     first (drop (count "--message=")) (apply str) not-empty)
        opts {:apply? (contains? flags "--apply")
              :push?  (contains? flags "--push")
              :pr?    (contains? flags "--pr")
              :merge? (contains? flags "--merge")
              :message msg
              :pubkey-hex (some->> args (filter #(str/starts-with? % "--pubkey="))
                                   first (drop 9) (apply str) not-empty)}
        actors (remove #(str/starts-with? % "--") args)]
    (when (empty? actors)
      (println "usage: bb actor:evolve <name> [--message=<m>] [--apply] [--push] [--pr] [--merge] [--pubkey=<hex>]")
      (System/exit 2))
    (doseq [a actors] (evolve-one a opts))))
