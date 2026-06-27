;; etzhayyim.actor-publish — `bb actor:publish <name>` orchestrator.
;;
;; ADR-2606231200. Idempotent pipeline that takes one actor from
;; 20-actors/<name>/ to a published, DID-bearing, aozora-registerable unit:
;;
;;   1. josh-split   monorepo prefix 20-actors/<name> -> com-etzhayyim-<name>
;;   2. gh-repo      ensure public github.com/etzhayyim/com-etzhayyim-<name>
;;   3. did-web      generate a STATIC /.well-known/did.json (+ .nojekyll) at the
;;                   repo's GitHub Pages root, served as
;;                   etzhayyim.github.io/com-etzhayyim-<name>/.well-known/did.json
;;                   (ADR addendum 2026-06-24: no custom domain, no CF Worker, no
;;                   dynamic generation — the apex Worker is org-DID only)
;;   4. kotoba-rad   mint RID + did:key, append sovereign identity to the log
;;   5. aozora       write the actor profile to the PDS (Option B e.write)
;;
;; DRY-RUN BY DEFAULT. Side-effecting steps (gh/git push/wrangler/pds write) run
;; ONLY with --apply; without it the step is planned + logged, nothing mutates.
;; no-server-key: this tool never holds a signing key — kotoba-rad signing and
;; the PDS write are member/operator-key legs, surfaced as planned commands.
;;
;; clj/bb per the repo "Operational code = clj/bb over the kotoba Datom log"
;; rule; shelling to system binaries (git/gh) via babashka.process is allowed.

(ns etzhayyim.actor-publish
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [cheshire.core :as json]
            [babashka.process :as p]
            [etzhayyim.kotoba-rad :as rad]
            [etzhayyim.kotoba-rad-sign :as rad-sign]))

(def org "etzhayyim")
(defn repo-name [actor] (str "com-" org "-" actor))
(defn prefix [actor] (str "20-actors/" actor))

;; ── manifest ────────────────────────────────────────────────────────────────

(defn manifest-path
  "Locate the actor manifest. Utility/older actors use `actor-manifest.jsonld`;
   the clj-native flagship actors (kaname/tsumugi/ibuki…) use `manifest.jsonld`
   (no `triggers`, lexicons listed under `:lexicons`). Prefer the former, fall
   back to the latter."
  [actor]
  (let [a (io/file (str (prefix actor) "/actor-manifest.jsonld"))
        m (io/file (str (prefix actor) "/manifest.jsonld"))]
    (cond (.exists a) a (.exists m) m :else a)))

(defn read-manifest [actor]
  (let [f (manifest-path actor)]
    (when (.exists f) (json/parse-string (slurp f) true))))

(defn manifest->genesis
  "Derive the kotoba-rad genesis block from the actor manifest.
   did:web is normalized to the github.io PATH form
   (did:web:etzhayyim.github.io:com-etzhayyim-<name>; ADR-2606231200 addendum
   2026-06-24), so the DID resolves to the actor repo's STATIC GitHub Pages
   did.json — no custom domain, no dynamic generation.
   The collection NSID is the first declared collection/lexicon minus its final
   record-type segment: `actor-manifest.jsonld` lists it under
   :triggers/:subscribeRepos/:collections, `manifest.jsonld` under :lexicons."
  [actor manifest & {:keys [pubkey-hex]}]
  (let [coll (or (-> manifest :triggers :subscribeRepos :collections first)
                 (-> manifest :lexicons first))
        ns* (when coll (str/join "." (butlast (str/split coll #"\."))))]
    (rad/genesis-block
     {:name actor
      :did-web (str "did:web:etzhayyim.github.io:" (repo-name actor))
      :delegates (when pubkey-hex [(rad/did-key pubkey-hex)])
      :threshold 1
      :repo (str "github.com/" org "/" (repo-name actor))
      :pds "https://pds.etzhayyim.com"
      :collection (or ns* (str "com.etzhayyim.apps." actor))})))

;; ── step helpers (dry-run aware) ────────────────────────────────────────────

(defn- sh [apply? & args]
  (let [cmd (vec args)]
    (if apply?
      (let [{:keys [exit out err]} (apply p/sh cmd)]
        {:cmd cmd :exit exit :out (str/trim (str out)) :err (str/trim (str err))})
      {:cmd cmd :planned true})))

(defn- log-step [n title m]
  (println (format "  [%d] %s" n title))
  (println "      " (if (:planned m)
                      (str "PLAN: " (str/join " " (:cmd m)))
                      (str "exit=" (:exit m)
                           (when (seq (:out m)) (str " | " (:out m)))
                           (when (seq (:err m)) (str " | err: " (:err m))))))
  m)

;; ── steps ───────────────────────────────────────────────────────────────────

(defn step-josh-split
  "Stage the per-actor view. Real bidirectional sync is josh-proxy serving the
   workspace.josh filter (50-infra/josh/RUNBOOK.md); here we surface the
   equivalent `git subtree split` that seeds/refreshes the mirror branch."
  [actor apply?]
  (log-step 1 (str "josh/subtree split " (prefix actor))
            (sh apply? "git" "subtree" "split" "--prefix" (prefix actor)
                "-b" (str "mirror/" (repo-name actor)))))

(defn step-gh-repo [actor apply?]
  (let [r (repo-name actor)
        exists (sh apply? "gh" "repo" "view" (str org "/" r))]
    (if (and apply? (zero? (:exit exists)))
      (log-step 2 (str "gh repo exists " r) exists)
      (log-step 2 (str "gh repo create " r " (public)")
                (sh apply? "gh" "repo" "create" (str org "/" r)
                    "--public" "--description"
                    (str "etzhayyim actor: " actor " (aozora.app)"))))))

(defn step-did-web [actor manifest apply? pubkey-hex]
  (let [genesis (manifest->genesis actor manifest :pubkey-hex pubkey-hex)
        ;; pass the genesis did:web through so the doc `id` == the genesis DID
        ;; (single source of truth — never re-derive a divergent string).
        doc (rad/did-web-doc {:name actor :did-web (:rad/did-web genesis)
                              :genesis genesis :pubkey-hex pubkey-hex})
        out (str (prefix actor) "/.well-known/did.json")
        ;; .nojekyll: GitHub Pages' Jekyll ignores dot-prefixed paths, so without
        ;; this the static /.well-known/did.json (and the actor's *.wasm) are not
        ;; served. The bytes are served raw — exactly what did:web + wasm need.
        nojekyll (str (prefix actor) "/.nojekyll")]
    (when apply?
      (io/make-parents (io/file out))
      (spit out (str (json/generate-string doc {:pretty true}) "\n"))
      (spit nojekyll ""))
    (log-step 3 (str "static did:web doc -> " out " (+ .nojekyll)")
              {:planned (not apply?) :cmd ["write" out (str (count (str doc)) "B")
                                           "+" nojekyll]})
    {:genesis genesis :did-doc-path out :nojekyll-path nojekyll}))

(defn step-kotoba-rad [actor genesis apply? pubkey-hex]
  ;; no-server-key: a signer is built ONLY if the member's key is in Keychain
  ;; (and the pubkey is known); otherwise publish unsigned (pilot/--no-network).
  (let [sign-fn (when (and pubkey-hex apply?)
                  (rad-sign/sign-fn-for-actor actor pubkey-hex))
        res (when apply? (rad/publish-identity! actor genesis {:sign-fn sign-fn}))]
    (log-step 4 (str "kotoba-rad RID " (rad/rid genesis)
                     (cond apply? "" pubkey-hex " (will sign if key in Keychain)"
                           :else " (unsigned: no --pubkey)"))
              (if res
                {:exit 0 :out (str (:rad-uri res) " head=" (:head res)
                                   " signed=" (:signed? res))}
                {:planned true :cmd ["kotoba-rad/publish-identity!" actor
                                     (rad/rad-uri genesis)
                                     (if pubkey-hex "sign-if-keychain" "unsigned")]}))
    (assoc (or res {}) :rid (rad/rid genesis) :rad-uri (rad/rad-uri genesis))))

(defn step-aozora
  "Plan the PDS profile write (Option B `e.write`). Actual write is the
   member/operator-key leg — surfaced as the command, executed out-of-band."
  [actor genesis apply?]
  (let [coll (-> genesis :rad/aozora :collection)
        profile-coll (str coll ".profile")]
    (log-step 5 (str "aozora PDS profile write " profile-coll)
              {:planned true
               :cmd ["@etzhayyim/sdk" "e.write"
                     (str "collection=" profile-coll)
                     (str "did=" (:rad/did-web genesis))
                     "rkey=self" "<- member/operator key (no-server-key)"]})
    {:collection profile-coll}))

;; ── driver ──────────────────────────────────────────────────────────────────

(defn publish-one [actor {:keys [apply? pubkey-hex]}]
  (let [manifest (read-manifest actor)]
    (when-not manifest
      (throw (ex-info (str "no actor-manifest.jsonld for " actor) {:actor actor})))
    (println (format "▶ actor:publish %s  (%s)"
                     actor (if apply? "APPLY" "DRY-RUN")))
    (step-josh-split actor apply?)
    (step-gh-repo actor apply?)
    (let [{:keys [genesis]} (step-did-web actor manifest apply? pubkey-hex)
          did (:rad/did-web genesis)
          rad-res (step-kotoba-rad actor genesis apply? pubkey-hex)
          aoz (step-aozora actor genesis apply?)]
      (println (format "✔ %s  rad=%s  repo=%s  did=%s\n"
                       actor (:rad-uri rad-res) (repo-name actor) did))
      {:actor actor :rid (:rid rad-res) :rad-uri (:rad-uri rad-res)
       :repo (repo-name actor) :did did
       :aozora-collection (:collection aoz)})))

(defn -main [& args]
  (let [flags (set (filter #(str/starts-with? % "--") args))
        opts {:apply? (contains? flags "--apply")
              :pubkey-hex (some->> args (filter #(str/starts-with? % "--pubkey=")) first
                                   (drop 9) (apply str) not-empty)}
        actors (remove #(str/starts-with? % "--") args)]
    (when (empty? actors)
      (println "usage: bb actor:publish <name> [<name>...] [--apply] [--pubkey=<hex>]")
      (System/exit 2))
    (doseq [a actors] (publish-one a opts))))
