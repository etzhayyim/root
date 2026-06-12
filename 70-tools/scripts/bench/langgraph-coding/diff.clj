;; ported from 70-tools/scripts/bench/langgraph-coding/diff.py (unit_refactor stage 0)
;; Compute pass-rate delta between two langgraph-coding result files.
(ns scripts.bench.langgraph-coding.diff
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare load main)

;; TODO: port-failed unit load (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpb0aufg6a/scratch.clj:2:1: wa)
;; def load(path: Path) -> dict[str, dict]:
;;     out: dict[str, dict] = {}
;;     with path.open() as f:
;;         for line in f:
;;             row = json.loads(line)
;;             out[row["id"]] = row
;;     return out
(defn load [& _]
  (throw (ex-info "TODO: port-failed" {:from "load"})))

;; TODO: port-failed unit main (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp9eue_zrv/scratch.clj:2:1: er)
;; def main() -> int:
;;     ap = argparse.ArgumentParser()
;;     ap.add_argument("--baseline", required=True)
;;     ap.add_argument("--new", required=True)
;;     ap.add_argument("--gate-pp", type=float, default=0.0,
;;                     help="exit 1 if delta below this percentage-points")
;;     args = ap.parse_args()
;; 
;;     base = load(Path(args.baseline))
;;     new = load(Path(args.new))
;; 
;;     common = set(base) & set(new)
;;     if not common:
;;         print("[diff] no overlap between baseline and new", file=sys.stderr)
;;         return 2
;; 
;;     base_pass = sum(int(base[i]["passed"]) for i in common)
;;     new_pass = sum(int(new[i]["passed"]) for i in common)
;;     n = len(common)
;;     delta_pp = 100 * (new_pass - base_pass) / n
;; 
;;     by_cat: dict[str, tuple[int, int, int]] = defaultdict(lambda: (0, 0, 0))
;;     for i in common:
;;         cat = base[i].get("category", "?")
;;         b, nw, total = by_cat[cat]
;;         by_cat[cat] = (
;;             b + int(base[i]["passed"]),
;;             nw + int(new[i]["passed"]),
;;             total + 1,
;;         )
;; 
;;     print(f"overall: baseline={base_pass}/{n} new={new_pass}/{n} delta={delta_pp:+.1f}pp")
;;     for cat, (b, nw, total) in sorted(by_cat.items()):
;;         print(f"  {cat:20s}: {b}/{total} → {nw}/{total}  ({100*(nw-b)/total:+.1f}pp)")
;; 
;;     if delta_pp < args.gate_pp:
;;         print(f"\nGATE FAIL: delta {delta_pp:+.1f}pp < required {args.gate_pp}pp", file=sys.stderr)
;;         return 1
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

