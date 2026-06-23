;; etzhayyim.workspace — workspace-level utilities (cljc port).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/workspace.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     build-rsync-command  — assemble ["rsync" ...] argv vector
;;     default-excludes     — the canonical exclusion list
;;
;;   IO (subprocess-shaping verified via injectable :proc-fn, no live calls):
;;     resolve-workspace-root — find workspace root (fs walk)
;;     count-actor-files      — count kotodama.jsonld files
;;     run-sync               — execute rsync via injectable :proc-fn
;;     workspace-status       — print root + actor count
;;
;; INJECTABLE SUBPROCESS CLIENT:
;;   run-sync accepts :proc-fn in opts.
;;   Default = real babashka.process/shell; tests inject a fake.
;;   build-rsync-command returns the argv — tests assert the argv without running.
;;
;; SECURITY:
;;   No secrets at load time.  No network calls.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.workspace)(println :ok)"

(ns etzhayyim.workspace
  (:require [clojure.string :as str]
            #?(:bb [babashka.process :as proc]
               :default [])
            #?(:bb [babashka.fs :as bfs]
               :default [])))

;; ---------------------------------------------------------------------------
;; Constants
;; ---------------------------------------------------------------------------

(def default-excludes
  "Default rsync exclusion patterns — mirrors Python workspace_sync defaults."
  ["node_modules" ".git" "__pycache__" ".venv" "dist" "build"])

;; ---------------------------------------------------------------------------
;; Pure: rsync command builder
;; ---------------------------------------------------------------------------

(defn build-rsync-command
  "Assemble an rsync argv vector.
  opts:
    :workspace-dir — local source path string (trailing / added automatically)
    :remote        — user@host:/path destination
    :excludes      — seq of patterns to --exclude (default-excludes if nil)
    :dry-run       — if truthy, add --dry-run flag
    :delete        — if truthy, add --delete flag

  Returns a vector of strings: ['rsync' '-avz' '--progress' ...].
  Pure: no subprocess / file IO."
  [{:keys [workspace-dir remote excludes dry-run delete]}]
  (let [src-path  (if workspace-dir
                    (str workspace-dir "/")
                    "./")
        excl-list (or (seq excludes) default-excludes)
        base      ["rsync" "-avz" "--progress"]
        with-excl (reduce (fn [acc ex] (conj acc "--exclude" ex))
                          base
                          excl-list)
        with-dr   (if dry-run (conj with-excl "--dry-run") with-excl)
        with-del  (if delete  (conj with-dr "--delete") with-dr)]
    (conj with-del src-path remote)))

;; ---------------------------------------------------------------------------
;; IO: workspace root resolution
;; ---------------------------------------------------------------------------

(defn resolve-workspace-root
  "Return the workspace root as a string.
  If workspace-dir is provided, use it directly.
  Otherwise fall back to the current working directory.
  opts:
    :fs-fn — injectable: (fn [path] → string), default identity"
  [workspace-dir opts]
  (let [fs-fn (or (:fs-fn opts) identity)]
    (fs-fn (or workspace-dir
               (System/getProperty "user.dir")))))

(defn count-actor-files
  "Count kotodama.jsonld files under the 60-apps/ directory.
  opts:
    :fs-fn — injectable: (fn [root-path] → integer count), tests inject a fake."
  [root-path opts]
  (let [fs-fn (:fs-fn opts)]
    (if fs-fn
      (fs-fn root-path)
      #?(:bb (let [apps-dir (str root-path "/60-apps")]
               (if (.exists (java.io.File. apps-dir))
                 (count (filter #(str/ends-with? (str %) "kotodama.jsonld")
                                (file-seq (java.io.File. apps-dir))))
                 0))
         :default 0))))

;; ---------------------------------------------------------------------------
;; IO: rsync execution
;; ---------------------------------------------------------------------------

(defn run-sync
  "Execute the rsync command assembled by build-rsync-command.
  opts:
    :proc-fn — injectable: (fn [argv opts-map] → {:exit int})
               default = real babashka.process/shell dispatch
    :dry-run — passed through to build-rsync-command

  Returns {:exit N} where N is the rsync exit code.
  Throws ex-info if rsync binary not found (:rsync-not-found)."
  [{:keys [workspace-dir remote excludes dry-run delete] :as sync-opts} opts]
  (let [argv    (build-rsync-command sync-opts)
        proc-fn (or (:proc-fn opts)
                    #?(:bb (fn [av _] (proc/shell {:continue true} (str/join " " av)))
                       :default nil))]
    (when (not proc-fn)
      (throw (ex-info "proc-fn required" {})))
    (try
      (proc-fn argv {})
      (catch Exception e
        (if (str/includes? (str (ex-message e)) "No such file")
          (throw (ex-info "rsync not found — install rsync" {:rsync-not-found true}))
          (throw e))))))

;; ---------------------------------------------------------------------------
;; IO: workspace-status print
;; ---------------------------------------------------------------------------

(defn workspace-status
  "Print workspace root + actor count.
  opts:
    :fs-fn        — injectable for count-actor-files (see above)
    :println-fn   — injectable: (fn [s]) default clojure.core/println"
  [workspace-dir opts]
  (let [root       (resolve-workspace-root workspace-dir opts)
        actors     (count-actor-files root opts)
        println-fn (or (:println-fn opts) println)]
    (println-fn (str "workspace: " root))
    (println-fn (str "  actors: " actors))
    {:root root :actors actors}))
