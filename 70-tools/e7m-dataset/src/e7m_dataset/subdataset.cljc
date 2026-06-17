;; ported from 70-tools/e7m-dataset/src/e7m_dataset/subdataset.py — real port
;; replacing the unit_refactor stage-0 "TODO: port-failed" stubs. NS fixed
;; (e7m-dataset.src.e7m-dataset.subdataset -> e7m-dataset.subdataset, matching the
;; Python package e7m_dataset.subdataset under source root src/) and the file is now .cljc.
;; Self-contained; host file/process I/O behind #?(:clj ...).
(ns e7m-dataset.subdataset
  "DataLad subdataset orchestration helpers.

  1:1 Clojure port of `subdataset.py`. `e7m-dataset add` chains:
    staging -> ensure-subdataset -> import-files -> save-subdataset -> copy-to-local-store

  Each step is a thin wrapper around `datalad` / `git annex` invoked as a
  subprocess. Failures bubble up. The directory remote (local-store) is created
  lazily on first subdataset creation; backend is set to SHA256E per
  ADR-2605241500 §D2.

  Subprocess steps take an injected `run!` runner — a fn (vector-of-args ->
  result) — so the pure path/string logic stays host-agnostic. The Python
  `subprocess.run(..., check=True)` / `subprocess.check_output(...)` contract is
  the runner's responsibility (must throw on non-zero exit)."
  (:require [clojure.string :as str]))

(def superdataset-rel "90-docs/baien/datasets")

#?(:clj
   (defn repo-root-from-cwd
     "Port of manifest.repo_root_from_cwd: walk up from cwd to the etzhayyim/root
     checkout (the dir containing CLAUDE.md AND a 90-docs/ directory)."
     ^java.io.File []
     (let [cwd (.getCanonicalFile (java.io.File. (System/getProperty "user.dir")))]
       (loop [p cwd]
         (cond
           (nil? p)
           (throw (ex-info "e7m-dataset must be run inside the etzhayyim/root checkout" {}))
           (and (.exists (java.io.File. p "CLAUDE.md"))
                (.isDirectory (java.io.File. p "90-docs")))
           p
           :else (recur (.getParentFile p)))))))

#?(:clj
   (defn superdataset-path
     "Port of superdataset_path: <repo-root>/90-docs/baien/datasets."
     (^java.io.File [] (superdataset-path (repo-root-from-cwd)))
     (^java.io.File [repo-root] (java.io.File. repo-root superdataset-rel))))

#?(:clj
   (defn subdataset-path
     "Port of subdataset_path: <superdataset-path>/<name>."
     (^java.io.File [name] (java.io.File. (superdataset-path) name))
     (^java.io.File [repo-root name] (java.io.File. (superdataset-path repo-root) name))))

#?(:clj
   (defn ensure-subdataset
     "Port of ensure_subdataset. Create-or-get the subdataset; init the directory
     remote on first create. Idempotent.

     `subdataset-annex-dir` is injected as a fn (name -> java.io.File) — the port
     of paths.subdataset_annex_dir. `run!` runs a subprocess arg-vector (must
     throw on non-zero exit, like subprocess.run(check=True))."
     [name subdataset-annex-dir run!]
     (let [sub (subdataset-path name)]
       (if (and (.exists sub) (.exists (java.io.File. sub ".datalad")))
         sub
         (let [super-path (superdataset-path)]
           (.mkdirs (.getParentFile sub))
           (run! ["datalad" "create" "-d" (.getPath super-path) (.getPath sub)])
           (run! ["git" "-C" (.getPath sub) "config" "annex.backend" "SHA256E"])
           (let [remote-root (subdataset-annex-dir name)]
             (.mkdirs remote-root)
             (run! ["git" "-C" (.getPath sub) "annex" "initremote" "local-store"
                    "type=directory" (str "directory=" (.getPath remote-root))
                    "encryption=none" "chunk=64MiB"])
             sub))))))

#?(:clj
   (defn import-files
     "Port of import_files. Copy/move files from `staging-dir` into the subdataset
     tree (preserving relative paths). Returns the number of files placed.
     `move` defaults to true (matching the Python keyword-only default)."
     ([sub staging-dir] (import-files sub staging-dir true))
     ([sub staging-dir move]
      (let [sub-f      (java.io.File. (str sub))
            staging-f  (.getCanonicalFile (java.io.File. (str staging-dir)))
            staging-prefix (str (.getPath staging-f) java.io.File/separator)
            prefix-len (count staging-prefix)]
        (reduce
         (fn [placed src]
           (if-not (.isFile src)
             placed
             (let [rel (subs (.getPath (.getCanonicalFile src)) prefix-len)
                   dst (java.io.File. sub-f rel)]
               (cond
                 ;; idempotent: skip identical-size files
                 (and (.exists dst) (= (.length dst) (.length src))) placed
                 :else
                 (do
                   (when (.exists dst) (.delete dst))
                   (.mkdirs (.getParentFile dst))
                   (let [src-path (.toPath src) dst-path (.toPath dst)]
                     (if move
                       (java.nio.file.Files/move
                        src-path dst-path
                        (into-array java.nio.file.CopyOption
                                    [java.nio.file.StandardCopyOption/REPLACE_EXISTING]))
                       (java.nio.file.Files/copy
                        src-path dst-path
                        (into-array java.nio.file.CopyOption
                                    [java.nio.file.StandardCopyOption/REPLACE_EXISTING
                                     java.nio.file.StandardCopyOption/COPY_ATTRIBUTES]))))
                   (inc placed))))))
         0
         (file-seq staging-f))))))

#?(:clj
   (defn save-subdataset
     "Port of save_subdataset. `datalad save -m <message>` then return the
     resulting commit sha.

     `run!` runs `datalad save` (throw on non-zero). `capture!` runs
     `git rev-parse HEAD` and returns its stdout text (port of
     subprocess.check_output)."
     [sub message run! capture!]
     (run! ["datalad" "save" "-d" (.getPath (java.io.File. (str sub))) "-m" message])
     (str/trim (capture! ["git" "-C" (.getPath (java.io.File. (str sub))) "rev-parse" "HEAD"]))))

#?(:clj
   (defn copy-to-local-store
     "Port of copy_to_local_store. `git annex copy . --to=local-store --jobs=<n>`.
     `jobs` defaults to 4 (matching the Python keyword-only default)."
     ([sub run!] (copy-to-local-store sub run! 4))
     ([sub run! jobs]
      (run! ["git" "-C" (.getPath (java.io.File. (str sub))) "annex" "copy" "."
             "--to=local-store" (str "--jobs=" jobs)]))))

;; Python __all__ = ["SUPERDATASET_REL","copy_to_local_store","ensure_subdataset",
;;                   "import_files","save_subdataset","subdataset_path","superdataset_path"].
;; __main__ demo: none.
