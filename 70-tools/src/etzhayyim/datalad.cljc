;; etzhayyim.datalad — DataLad / git-annex integration for the kotoba CLI.
;;
;; Completes the storage pipeline: git → datalad → kotoba (CID) → kotobase.net → ipfs → B2.
;; This namespace bridges the gap between DataLad's annex-managed large files and the
;; kotoba content-addressing layer (CIDv1). It lets the validator and CID computation
;; work transparently on both regular git files and DataLad annex files.
;;
;; Design: shells out to `datalad` / `git-annex` system binaries via babashka.process
;; (allowed per CLAUDE.md "Operational code = clj/bb" rule — same category as git/ipfs).
;; All logic is Clojure; the system binaries are invoked, not reimplemented.
;;
;; Pipeline:
;;   1. git        — code + manifest + RAD journal + small data (<100MB)
;;   2. datalad    — git-annex manages large files; git sees only the annex key (pointer)
;;   3. kotoba     — CIDv1 computed from the actual content (resolving annex if needed)
;;   4. kotobase.net — IPFS pinning service (bb kotobase:pin, already implemented)
;;   5. ipfs       — P2P content-addressed retrieval (CID = content hash)
;;   6. B2         — Backblaze S3-compatible cold storage (datalad special remote backend)

(ns etzhayyim.datalad
  (:require [clojure.java.io :as io]
            [clojure.string :as str]
            [babashka.process :as p]))

;; ── annex detection ─────────────────────────────────────────────────────────

(defn annex-symlink?
  "True if <path> is a git-annex managed symlink (i.e. a DataLad annex file whose
   content lives under .git/annex/objects/ and may need to be fetched from a remote)."
  [path]
  (try
    (let [f (io/file path)]
      (and (.exists f)
           (java.nio.file.Files/isSymbolicLink (.toPath f))
           (str/includes? (str (.readSymbolicLink (.toPath f)))
                          ".git/annex/objects")))
    (catch Exception _ false)))

(defn annex-content-path
  "If <path> is an annex symlink, return the resolved content path under
   .git/annex/objects/. Returns nil for regular files."
  [path]
  (try
    (when (annex-symlink? path)
      (let [link (str (.readSymbolicLink (.toPath (io/file path))))]
        (if (str/starts-with? link "/")
          link
          (str (.getParent (io/file path)) "/" link))))
    (catch Exception _ nil)))

(defn annex-content-present?
  "True if the annex content is locally available (the annex object file exists).
   False if the content is only a pointer (needs datalad get)."
  [path]
  (if-let [resolved (annex-content-path path)]
    (.exists (io/file resolved))
    true))  ; regular file — always present

;; ── datalad operations (shell out) ──────────────────────────────────────────

(defn- datalad-sh
  "Run a datalad command, return {:exit :out :err}. Throws on non-zero exit
   unless :allow-fail? is passed."
  [args & {:keys [allow-fail?]}]
  (let [cmd (into ["datalad"] args)
        {:keys [exit out err]} (apply p/sh cmd)]
    (if (and (not allow-fail?) (not (zero? exit)))
      (throw (ex-info (str "datalad failed: " (str/join " " args)
                           " exit=" exit " err=" (str/trim (str err)))
                      {:cmd cmd :exit exit}))
      {:exit exit :out (str/trim (str out)) :err (str/trim (str err))})))

(defn annex-get!
  "datalad get <path> — retrieve the actual content of an annex file from a
   remote (B2, local). Returns true on success."
  [path]
  (if (annex-symlink? path)
    (do (println "  datalad get" path)
        (zero? (:exit (datalad-sh ["get" "--"] [path] :allow-fail? true))))
    true))  ; regular file — nothing to get

(defn annex-drop!
  "datalad drop <path> — free local disk space by dropping the content (the
   annex pointer remains in git). Returns true on success."
  [path]
  (if (annex-symlink? path)
    (do (println "  datalad drop" path)
        (zero? (:exit (datalad-sh ["drop" "--no-check" "--"] [path] :allow-fail? true))))
    true))

(defn datalad-create!
  "datalad create -c text2git <dataset-dir> — initialize a new DataLad dataset
   inside an existing git repo subdirectory. The text2git configuration annexes
   only large files (text stays in git). Returns the dataset path on success."
  [dataset-dir]
  (println "  datalad create" dataset-dir)
  (datalad-sh ["create" "-c" "text2git" "-D" dataset-dir])
  dataset-dir)

(defn datalad-save!
  "datalad save -m <msg> <path> — save changes to a DataLad dataset (annex-aware
   commit). Large files are automatically annexed; small files stay in git."
  [path message]
  (println "  datalad save" path)
  (datalad-sh ["save" "-m" message "--"] [path]))

(defn datalad-push!
  "datalad push --to <remote> — push annex content to a special remote (e.g. b2).
   The git refs are pushed separately (normal git push)."
  [dataset-dir remote]
  (println "  datalad push" dataset-dir "→" remote)
  (datalad-sh ["push" "-d" dataset-dir "--to" remote]))

(defn annex-whereis
  "git-annex whereis <path> — show which remotes have the content.
   Returns the raw whereis output string (diagnostic)."
  [path]
  (try
    (:out (p/sh ["git-annex" "whereis" path]))
    (catch Exception _ nil)))

;; ── the bridge: transparent CID computation on annex files ──────────────────

(defn with-annex-content
  "Ensure annex content is present, call (f resolved-path), then drop to free
   space. For regular files, call (f path) directly. This is the key bridge:
   it lets CID computation (cid-of-file) work transparently on DataLad datasets.

   Usage:
     (dl/with-annex-content \"80-data/gleif/full.kotoba.edn\"
       (fn [resolved]
         (cid/cid-of-file resolved)))"
  [path f]
  (let [f (if (fn? f) f (constantly nil))]
    (if (annex-symlink? path)
      (let [resolved (annex-content-path path)]
        (when-not (.exists (io/file resolved))
          (annex-get! path))
        (let [result (f (or resolved path))]
          (annex-drop! path)   ; free space — pointer stays in git
          result))
      ;; Regular file — no annex dance needed
      (f path))))

;; ── CLI ─────────────────────────────────────────────────────────────────────

(defn- status-entry [file]
  (let [path (.getPath file)
        annex? (annex-symlink? path)
        present? (annex-content-present? path)]
    {:path path
     :annex annex?
     :content-present present?
     :status (cond
               (not annex?) "git-tracked"
               present? "annex-present"
               :else "annex-absent (needs datalad get)")}))

(defn -main
  "bb kotoba:annex <subcommand> <args>

   Subcommands:
     get <path>     — datalad get (retrieve annex content from B2)
     drop <path>    — datalad drop (free local disk space)
     status [dir]   — show annex state for all *.kotoba.edn under <dir>
     create <dir>   — datalad create (initialize dataset)
     save <path>    — datalad save (annex-aware commit)
     push <dir> <remote> — datalad push (to B2 etc)"
  [& args]
  (let [sub (first args)
        rest-args (rest args)]
    (case sub
      "get"    (let [r (annex-get! (first rest-args))]
                 (println (if r "✓ content retrieved" "✗ failed")))
      "drop"   (let [r (annex-drop! (first rest-args))]
                 (println (if r "✓ content dropped" "✗ failed")))
      "status" (let [dir (or (first rest-args) "80-data")]
                 (println "=== annex status:" dir "===")
                 (->> (file-seq (io/file dir))
                      (filter #(.isFile %))
                      (filter #(str/ends-with? (.getName %) ".kotoba.edn"))
                      (map status-entry)
                      (run! #(println (format "  %-12s %s"
                                              (:status %) (:path %))))))
      "create" (datalad-create! (first rest-args))
      "save"   (datalad-save! (first rest-args)
                              (or (second rest-args) "kotoba:annex save"))
      "push"   (datalad-push! (first rest-args) (or (second rest-args) "b2"))
      (println "usage: bb kotoba:annex <get|drop|status|create|save|push> <args>"))))
