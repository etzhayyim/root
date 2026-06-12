;; ported from 20-actors/kakaku/kotoba/ingest_mcp.py (unit_refactor stage 0)
;; kakaku 価格 — ingest seed.edn into a live kotoba node via MCP.
(ns kakaku.kotoba.ingest-mcp
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare seed strip-comments top-level-entities main)

;; TODO: port-failed unit SEED (assembled-lint error)
;; SEED = os.path.join(os.path.dirname(__file__), "seed.edn")
(def seed nil) ;; TODO: port-failed const

;; TODO: port-failed unit _strip_comments (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpq9mnt6jv/scratch.clj:17:22: )
;; def _strip_comments(s: str) -> str:
;;     out = []
;;     in_str = False
;;     i, n = 0, len(s)
;;     while i < n:
;;         c = s[i]
;;         if in_str:
;;             out.append(c)
;;             if c == '"' and s[i - 1] != "\\":
;;                 in_str = False
;;             i += 1
;;             continue
;;         if c == '"':
;;             in_str = True
;;             out.append(c)
;;             i += 1
;;             continue
;;         if c == ";":
;;             while i < n and s[i] != "\n":
;;                 i += 1
;;             continue
;;         out.append(c)
;;         i += 1
;;     return "".join(out)
(defn strip-comments [& _]
  (throw (ex-info "TODO: port-failed" {:from "_strip_comments"})))

;; TODO: port-failed unit _top_level_entities (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpn6wf9pdu/scratch.clj:3:12: w)
;; def _top_level_entities(s: str):
;;     """Yield each top-level {...} map literal inside the outer [ ... ] vector."""
;;     s = _strip_comments(s)
;;     start = s.find("[")
;;     if start < 0:
;;         return
;;     depth = 0
;;     buf: list = []
;;     in_str = False
;;     for c in s[start + 1:]:
;;         if in_str:
;;             buf.append(c)
;;             if c == '"':
;;                 in_str = False
;;             continue
;;         if c == '"':
;;             in_str = True
;;             buf.append(c)
;;             continue
;;         if c == "{":
;;             depth += 1
;;             buf.append(c)
;;         elif c == "}":
;;             depth -= 1
;;             buf.append(c)
;;             if depth == 0:
;;                 yield "".join(buf).strip()
;;                 buf = []
;;         elif depth > 0:
;;             buf.append(c)
(defn top-level-entities [& _]
  (throw (ex-info "TODO: port-failed" {:from "_top_level_entities"})))

;; TODO: port-failed unit main (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmplx2dgau9/scratch.clj:3:13: w)
;; def main() -> int:
;;     ap = argparse.ArgumentParser()
;;     ap.add_argument("--url", default="http://127.0.0.1:8077")
;;     ap.add_argument("--graph", default="com.etzhayyim.kakaku")
;;     ap.add_argument("--via", default="mcp")
;;     ap.add_argument("--dry-run", action="store_true")
;;     args = ap.parse_args()
;; 
;;     with open(SEED, encoding="utf-8") as f:
;;         raw = f.read()
;;     entities = list(_top_level_entities(raw))
;;     datoms = sum(e.count(" :") + (1 if e.startswith("{:") else 0) for e in entities)
;; 
;;     print(f"   parsed {len(entities)} entities (~{datoms} datoms) from seed.edn → {args.graph}")
;;     if args.dry_run or not os.environ.get("KOTOBA_TOKEN"):
;;         print("   DRY RUN — no writes. Set KOTOBA_TOKEN (operator AT-session JWT) to ingest.")
;;         return 0
;; 
;;     # live ingest path (operator token present) — assert via MCP kotoba_datom_create.
;;     # R0 scaffold: wire to the live MCP endpoint when the operator session is provisioned
;;     # (G11 gates real outward writes). Kept explicit to avoid a silent no-op.
;;     print("   live ingest requested — implement MCP kotoba_datom_create wiring before use (G11).")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

