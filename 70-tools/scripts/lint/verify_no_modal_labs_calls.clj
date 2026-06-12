;; ported from 70-tools/scripts/lint/verify_no_modal_labs_calls.py (unit_refactor stage 0)
;; CI grep gate — forbid Modal Labs server references in kotoba_murakumo source.
(ns scripts.lint.verify-no-modal-labs-calls
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare package-root find-violations main)

;; TODO: port-failed unit _PACKAGE_ROOT (assembled-lint error)
;; _PACKAGE_ROOT = Path("40-engine/kotoba/py/kotoba_murakumo/kotoba_murakumo")
;; _VIOLATION_RE = re.compile(
;;     r"(?:\bhttps?://(?:api\.)?modal\.com\b"
;;     r"|\bapi\.modal\.com\b"
;;     r"|\bmodal\.com/[A-Za-z0-9_\-/]+"
;;     r"|\bfrom\s+modal\s+import\b"
;;     r"|\bimport\s+modal\s*$"
;;     r"|\bimport\s+modal\s+as\b)",
;;     re.MULTILINE,
;; )
;; _EXTS = {".py"}
(def package-root nil) ;; TODO: port-failed const

;; TODO: port-failed unit find_violations (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpvycox5cs/scratch.clj:4:14: e)
;; def find_violations(root: Path) -> list[tuple[Path, int, str]]:
;;     findings: list[tuple[Path, int, str]] = []
;;     pkg = root / _PACKAGE_ROOT
;;     if not pkg.exists():
;;         # Repo layout sanity check; not a violation by itself.
;;         print(f"warning: {pkg} not found (expected when running outside repo)",
;;               file=sys.stderr)
;;         return findings
;; 
;;     for path in sorted(pkg.rglob("*")):
;;         if not path.is_file() or path.suffix not in _EXTS:
;;             continue
;;         try:
;;             text = path.read_text(encoding="utf-8")
;;         except (OSError, UnicodeDecodeError):
;;             continue
;;         for m in _VIOLATION_RE.finditer(text):
;;             line_no = text[: m.start()].count("\n") + 1
;;             findings.append((path.relative_to(root), line_no, m.group(0)))
;;     return findings
(defn find-violations [& _]
  (throw (ex-info "TODO: port-failed" {:from "find_violations"})))

;; TODO: port-failed unit main (assembled-lint error)
;; def main() -> int:
;;     parser = argparse.ArgumentParser(description=__doc__)
;;     parser.add_argument(
;;         "--root",
;;         default=Path(__file__).resolve().parents[3],
;;         type=Path,
;;         help="repo root (default: auto-detect from script location)",
;;     )
;;     args = parser.parse_args()
;; 
;;     findings = find_violations(args.root)
;;     if not findings:
;;         print("no-modal-labs-calls gate: clean (kotoba_murakumo runtime "
;;               "source does not reference modal.com / api.modal.com / modal import)")
;;         return 0
;; 
;;     print("ADR-2605282000 N1 violation: kotoba_murakumo source references "
;;           "Modal Labs (forbidden per Murakumo-only invariant ADR-2605215000):",
;;           file=sys.stderr)
;;     for path, line_no, match in findings:
;;         print(f"  {path}:{line_no}: {match!r}", file=sys.stderr)
;;     return 1
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

