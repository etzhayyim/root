;; ported from 70-tools/e7m-dataset/src/e7m_dataset/subdataset.py (unit_refactor stage 0)
;; DataLad subdataset orchestration helpers.
(ns e7m-dataset.src.e7m-dataset.subdataset
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare superdataset-rel repo-root superdataset-path subdataset-path ensure-subdataset import-files save-subdataset copy-to-local-store all)

(def superdataset-rel (java.nio.file.Paths/get "90-docs/baien/datasets"))

(defn repo-root []
  (.repo-root-from-cwd))

;; TODO: port-failed unit superdataset_path (assembled-lint error)
;; def superdataset_path() -> Path:
;;     return _repo_root() / SUPERDATASET_REL
(defn superdataset-path [& _]
  (throw (ex-info "TODO: port-failed" {:from "superdataset_path"})))

;; TODO: port-failed unit subdataset_path (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpw9dnyonp/scratch.clj:3:4: er)
;; def subdataset_path(name: str) -> Path:
;;     return superdataset_path() / name
(defn subdataset-path [& _]
  (throw (ex-info "TODO: port-failed" {:from "subdataset_path"})))

;; TODO: port-failed unit ensure_subdataset (assembled-lint error)
;; def ensure_subdataset(name: str, paths: Paths) -> Path:
;;     """Create-or-get the subdataset; init the directory remote on first
;;     create. Idempotent."""
;;     sub = subdataset_path(name)
;;     if sub.exists() and (sub / ".datalad").exists():
;;         return sub
;;     super_path = superdataset_path()
;;     sub.parent.mkdir(parents=True, exist_ok=True)
;;     subprocess.run(
;;         ["datalad", "create", "-d", str(super_path), str(sub)],
;;         check=True,
;;     )
;;     subprocess.run(
;;         ["git", "-C", str(sub), "config", "annex.backend", "SHA256E"],
;;         check=True,
;;     )
;;     remote_root = paths.subdataset_annex_dir(name)
;;     remote_root.mkdir(parents=True, exist_ok=True)
;;     subprocess.run(
;;         [
;;             "git", "-C", str(sub), "annex", "initremote", "local-store",
;;             "type=directory", f"directory={remote_root}",
;;             "encryption=none", "chunk=64MiB",
;;         ],
;;         check=True,
;;     )
;;     return sub
(defn ensure-subdataset [& _]
  (throw (ex-info "TODO: port-failed" {:from "ensure_subdataset"})))

;; TODO: port-failed unit import_files (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpc3d21xer/scratch.clj:4:9: wa)
;; def import_files(sub: Path, staging_dir: Path, *, move: bool = True) -> int:
;;     """Copy/move files from `staging_dir` into the subdataset tree
;;     (preserving relative paths). Returns the number of files placed."""
;;     count = 0
;;     for src in staging_dir.rglob("*"):
;;         if not src.is_file():
;;             continue
;;         rel = src.relative_to(staging_dir)
;;         dst = sub / rel
;;         if dst.exists():
;;             # idempotent: skip identical-size files
;;             if dst.stat().st_size == src.stat().st_size:
;;                 continue
;;             dst.unlink()
;;         dst.parent.mkdir(parents=True, exist_ok=True)
;;         if move:
;;             shutil.move(str(src), str(dst))
;;         else:
;;             shutil.copy2(src, dst)
;;         count += 1
;;     return count
(defn import-files [& _]
  (throw (ex-info "TODO: port-failed" {:from "import_files"})))

;; TODO: port-failed unit save_subdataset (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpyuec_h_b/scratch.clj:3:18: w)
;; def save_subdataset(sub: Path, message: str) -> str:
;;     """`datalad save -m <message>` and return the resulting commit sha."""
;;     subprocess.run(
;;         ["datalad", "save", "-d", str(sub), "-m", message],
;;         check=True,
;;     )
;;     sha = subprocess.check_output(
;;         ["git", "-C", str(sub), "rev-parse", "HEAD"], text=True
;;     ).strip()
;;     return sha
(defn save-subdataset [& _]
  (throw (ex-info "TODO: port-failed" {:from "save_subdataset"})))

(defn copy-to-local-store [sub jobs]
  (let [args (str "git -C " (clojure.string/replace sub "\\" "/") " annex copy . --to=local-store --jobs=" jobs)]
    (throw (ex-info "TODO: port" {:from "copy-to-local-store"}))))

(def __all__ ["SUPERDATASET_REL" "copy-to-local-store" "ensure-subdataset" "import-files" "save-subdataset" "subdataset-path" "superdataset-path"])

