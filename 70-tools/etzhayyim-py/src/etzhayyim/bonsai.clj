;; ported from 70-tools/etzhayyim-py/src/etzhayyim/bonsai.py (unit_refactor stage 0)
;; bonsai — Workspace growth/prune analysis (ADR-2605080100, ADR-2605091300).
(ns etzhayyim-py.src.etzhayyim.bonsai
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare prune-tiers bonsai-node bonsai-report skip-dirs classify-tier score-node scan-workspace bonsai bonsai-scan bonsai-prune bonsai-status bonsai-canopy bonsai-growth bonsai-release)

(def prune-tiers ["fruit" "flower" "leaf" "branch" "trunk" "seed"])
(def tier-hints {"fruit" ["TODO" "FIXME" "HACK" "TEMP" "xxx"]
                "flower" ["test_" "_test" ".spec." ".test."]
                "leaf" [".md" ".txt" ".yaml" ".yml" ".toml"]
                "branch" [".ts" ".py" ".go"]
                "trunk" ["kotodama.jsonld" "wrangler.jsonc" "pyproject.toml"]
                "seed" ["deps.toml" "CLAUDE.md"]})
(def re-todo (clojure.string/regex-replace-all "(TODO|FIXME|HACK|TEMP|XXX)" nil :case-insensitive))
(def re-dead-code (clojure.string/regex-replace-all "//\\s*(?:dead|unused|legacy|deprecated)\\b" nil :case-insensitive))

(def bonsai-node-to-dict (fn [this]
  {:path (:path this)
   :tier (:tier this)
   :lines (:lines this)
   :prune-score (:prune_score this)
   :signals (:signals this)}))

(defn bonsai-report-to-dict [this]
  {:evaluated-at (:evaluated-at this)
   :total-files (:total-files this)
   :total-lines (:total-lines this)
   :tier-counts (:tier-counts this)
   :prune-candidates (map #(bonsai-node-to-dict %) (:prune-candidates this))
   :growth-score (:growth-score this)})

;; TODO: port-failed unit _SKIP_DIRS (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpcf5gmjzg/scratch.clj:2:77: e)
;; _SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build", ".langgraph_api"}
;; _SOURCE_EXTS = {".ts", ".py", ".go", ".rs", ".svelte"}
;; _IGNORE_EXTS = {".lock", ".pckl", ".pyc", ".wasm"}
(def skip-dirs nil) ;; TODO: port-failed const

;; TODO: port-failed unit _classify_tier (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpas94_oat/scratch.clj:6:15: w)
;; def _classify_tier(path: Path) -> str:
;;     name = path.name
;;     for tier, hints in _TIER_HINTS.items():
;;         if any(hint in name for hint in hints):
;;             return tier
;;     if path.suffix in _SOURCE_EXTS:
;;         return "branch"
;;     if path.suffix in {".md", ".txt", ".yaml", ".yml", ".toml", ".json"}:
;;         return "leaf"
;;     return "leaf"
(defn classify-tier [& _]
  (throw (ex-info "TODO: port-failed" {:from "_classify_tier"})))

;; TODO: port-failed unit _score_node (assembled-lint error)
;; def _score_node(path: Path, content: str) -> tuple[int, list[str]]:
;;     signals = []
;;     score = 0
;; 
;;     todos = _RE_TODO.findall(content)
;;     if todos:
;;         score += min(len(todos) * 10, 30)
;;         signals.append(f"{len(todos)} TODO/FIXME")
;; 
;;     dead = _RE_DEAD_CODE.findall(content)
;;     if dead:
;;         score += 20
;;         signals.append("dead code comments")
;; 
;;     lines = content.count("\n")
;;     if lines == 0:
;;         score += 40
;;         signals.append("empty file")
;;     elif lines < 5:
;;         score += 20
;;         signals.append(f"trivial ({lines} lines)")
;; 
;;     if re.search(r'(?:^|_)(deprecated|legacy|old|backup|bak)(?:_|$|\.)', path.name, re.IGNORECASE):
;;         score += 30
;;         signals.append("legacy name")
;; 
;;     return min(score, 100), signals
(defn score-node [& _]
  (throw (ex-info "TODO: port-failed" {:from "_score_node"})))

;; TODO: port-failed unit scan_workspace (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp75ljq4bc/scratch.clj:0:0: er)
;; def scan_workspace(ws: Path, prune_threshold: int = 50) -> BonsaiReport:
;;     tier_counts: dict[str, int] = {t: 0 for t in PRUNE_TIERS}
;;     nodes: list[BonsaiNode] = []
;;     total_lines = 0
;; 
;;     for p in ws.rglob("*"):
;;         if not p.is_file():
;;             continue
;;         if any(d in p.parts for d in _SKIP_DIRS):
;;             continue
;;         if p.suffix in _IGNORE_EXTS:
;;             continue
;; 
;;         tier = _classify_tier(p)
;;         tier_counts[tier] = tier_counts.get(tier, 0) + 1
;; 
;;         if p.suffix not in _SOURCE_EXTS:
;;             continue
;; 
;;         try:
;;             content = p.read_text(errors="replace")
;;         except OSError:
;;             continue
;; 
;;         lines = content.count("\n")
;;         total_lines += lines
;;         prune_score, signals = _score_node(p, content)
;; 
;;         rel = str(p.relative_to(ws))
;;         nodes.append(BonsaiNode(path=rel, tier=tier, lines=lines,
;;                                 prune_score=prune_score, signals=signals))
;; 
;;     candidates = sorted(
;;         [n for n in nodes if n.prune_score >= prune_threshold],
;;         key=lambda n: n.prune_score, reverse=True,
;;     )
;; 
;;     total_files = sum(tier_counts.values())
;;     fruit_count = tier_counts.get("fruit", 0) + tier_counts.get("flower", 0)
;;     growth_score = max(0, 100 - int(fruit_count / max(total_files, 1) * 100))
;; 
;;     return BonsaiReport(
;;         evaluated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
;;         total_files=total_files,
;;         total_lines=total_lines,
;;         tier_counts=tier_counts,
;;         prune_candidates=candidates,
;;         growth_score=growth_score,
;;     )
(defn scan-workspace [& _]
  (throw (ex-info "TODO: port-failed" {:from "scan_workspace"})))

;; TODO: port-failed unit bonsai (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp5ukmsgj0/scratch.clj:4:15: w)
;; def bonsai(ctx: click.Context, workspace_dir: str | None, json_out: bool) -> None:
;;     """Bonsai growth/prune workspace analysis (ADR-2605080100)."""
;;     if ctx.invoked_subcommand is not None:
;;         return
;;     ws = _resolve_root(workspace_dir)
;;     report = scan_workspace(ws)
;;     if json_out:
;;         click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
;;     else:
;;         click.echo(f"bonsai: growth={report.growth_score}  files={report.total_files}  "
;;                    f"lines={report.total_lines}")
;;         click.echo("  tiers: " + "  ".join(
;;             f"{t}={report.tier_counts.get(t, 0)}" for t in PRUNE_TIERS
;;         ))
;;         if report.prune_candidates:
;;             click.echo(f"  prune candidates: {len(report.prune_candidates)}")
(defn bonsai [& _]
  (throw (ex-info "TODO: port-failed" {:from "bonsai"})))

;; TODO: port-failed unit bonsai_scan (assembled-lint error)
;; def bonsai_scan(workspace_dir: str | None, json_out: bool) -> None:
;;     """Scan workspace growth metrics."""
;;     ws = _resolve_root(workspace_dir)
;;     report = scan_workspace(ws)
;;     if json_out:
;;         click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
;;     else:
;;         click.echo(f"files={report.total_files}  lines={report.total_lines}  "
;;                    f"growth={report.growth_score}")
(defn bonsai-scan [& _]
  (throw (ex-info "TODO: port-failed" {:from "bonsai_scan"})))

;; TODO: port-failed unit bonsai_prune (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpyfhewt2p/scratch.clj:2:1: er)
;; def bonsai_prune(workspace_dir: str | None, json_out: bool, threshold: int, top: int) -> None:
;;     """List top prune candidates."""
;;     ws = _resolve_root(workspace_dir)
;;     report = scan_workspace(ws, prune_threshold=threshold)
;;     candidates = report.prune_candidates[:top]
;;     if json_out:
;;         click.echo(json.dumps([n.to_dict() for n in candidates], ensure_ascii=False, indent=2))
;;     else:
;;         if not candidates:
;;             click.echo("  no prune candidates above threshold")
;;         for n in candidates:
;;             signals = ", ".join(n.signals)
;;             click.echo(f"  [{n.prune_score:3d}] [{n.tier:6}] {n.path}  ({signals})")
(defn bonsai-prune [& _]
  (throw (ex-info "TODO: port-failed" {:from "bonsai_prune"})))

;; TODO: port-failed unit bonsai_status (assembled-lint error)
;; def bonsai_status(workspace_dir: str | None, json_out: bool) -> None:
;;     """Overall bonsai ecosystem health."""
;;     ws = _resolve_root(workspace_dir)
;;     report = scan_workspace(ws)
;;     health = "healthy" if report.growth_score >= 70 else "needs pruning" if report.growth_score >= 40 else "overgrown"
;;     if json_out:
;;         click.echo(json.dumps({
;;             "health": health,
;;             "growth_score": report.growth_score,
;;             "prune_candidates": len(report.prune_candidates),
;;         }, ensure_ascii=False, indent=2))
;;     else:
;;         click.echo(f"bonsai status: {health}  growth={report.growth_score}  "
;;                    f"prune_candidates={len(report.prune_candidates)}")
(defn bonsai-status [& _]
  (throw (ex-info "TODO: port-failed" {:from "bonsai_status"})))

(defn bonsai-canopy [min-eta max-eta status-filter limit json-out]
  (throw (ex-info "bonsai canopy requires direct Kotoba/Datomic access (etzhayyimdb). Use the Go binary: etzhayyim bonsai canopy" {})))

(defn bonsai-growth [growth-type limit json-out]
  (throw (ex-info "bonsai growth requires direct Kotoba/Datomic access (etzhayyimdb). Use the Go binary: etzhayyim bonsai growth" {})))

(defn bonsai-release [actor-did json-out yes]
  (throw (ex-info "bonsai release requires direct Kotoba/Datomic access (etzhayyimdb). Use the Go binary: etzhayyim bonsai release"
                {:actor-did actor-did :json-out json-out :yes yes})))

