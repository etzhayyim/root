;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hoshimori/methods/analyze.py (unit_refactor stage 0)
;; hoshimori 星守 — edge-primary orbital-congestion analyzer over the orbit graph.
(ns root.hoshimori.methods.analyze
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare tok tokens atom end parse read-edn regime-weight load analyze rank report-md main)

;; TODO: port-failed unit _TOK (bb-compile unmapped)
;; _TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
(def tok nil) ;; TODO: port-failed const

;; TODO: port-failed unit _tokens (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpjbxyiyu9/scratch.clj:3:51: w)
;; def _tokens(s: str):
;;     for m in _TOK.finditer(s):
;;         t = m.group(1)
;;         if t is not None:
;;             yield t
(defn tokens [& _]
  (throw (ex-info "TODO: port-failed" {:from "_tokens"})))

;; TODO: port-failed unit _atom (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmptyflhr9x/scratch.clj:21:1: e)
;; def _atom(t: str):
;;     if t.startswith('"'):
;;         return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
;;     if t == 'true':  return True
;;     if t == 'false': return False
;;     if t == 'nil':   return None
;;     if t.startswith(':'):
;;         return t
;;     try:
;;         return int(t)
;;     except ValueError:
;;         try:
;;             return float(t)
;;         except ValueError:
;;             return t
(defn atom [& _]
  (throw (ex-info "TODO: port-failed" {:from "_atom"})))

;; TODO: port-failed unit _END (assembled-lint error)
;; _END = object()
(def end nil) ;; TODO: port-failed const

;; TODO: port-failed unit _parse (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpq90u3ym4/scratch.clj:5:13: e)
;; def _parse(it):
;;     t = next(it)
;;     if t == '[':
;;         out = []
;;         while (x := _parse(it)) is not _END:
;;             out.append(x)
;;         return out
;;     if t == '{':
;;         out = {}
;;         while (k := _parse(it)) is not _END:
;;             out[k] = _parse(it)
;;         return out
;;     if t in (']', '}'):
;;         return _END
;;     return _atom(t)
(defn parse [& _]
  (throw (ex-info "TODO: port-failed" {:from "_parse"})))

;; TODO: port-failed unit read_edn (assembled-lint error)
;; def read_edn(text: str):
;;     return _parse(_tokens(text))
(defn read-edn [& _]
  (throw (ex-info "TODO: port-failed" {:from "read_edn"})))

;; TODO: port-failed unit REGIME_WEIGHT (bb-compile unmapped)
;; REGIME_WEIGHT = {":leo-low": 1.0, ":sso": 0.9, ":geo": 0.8, ":leo-high": 0.7,
;;                  ":meo": 0.6, ":heo": 0.4}
;; HAZARD_KINDS = {":congests", ":imperils"}
;; STEWARDSHIP_KINDS = {":remediates", ":deconflicts", ":deorbits"}
;; DEPENDENCY_KINDS = {":depends-on"}
(def regime-weight nil) ;; TODO: port-failed const

;; TODO: port-failed unit load (assembled-lint error)
;; def load(path: pathlib.Path):
;;     """Return (nodes_by_id, edges) from an orbit EDN graph."""
;;     forms = read_edn(path.read_text(encoding="utf-8"))
;;     nodes, edges = {}, []
;;     for f in forms:
;;         if not isinstance(f, dict):
;;             continue
;;         if ":organism/id" in f:
;;             nodes[f[":organism/id"]] = f
;;         elif ":en/from" in f and ":en/to" in f:
;;             edges.append(f)
;;     return nodes, edges
(defn load [& _]
  (throw (ex-info "TODO: port-failed" {:from "load"})))

;; TODO: port-failed unit analyze (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpeizo3ro6/scratch.clj:10:13: )
;; def analyze(nodes: dict, edges: list):
;;     """Edge-primary integrals (computed on read; transient — N1/G2).
;; 
;;     congestion[shell]   = Σ incident inbound hazard/occupancy load × disclosed regime weight
;;     stewardship[node]   = Σ incident inbound :remediates/:deconflicts/:deorbits load
;;     fragility[node]     = Σ incident :depends-on load (service ↔ regime cascade risk)
;;     congestion_out[src] = Σ outbound hazard/occupancy load (the 取-holder occupying/imperiling)
;;     """
;;     congestion = defaultdict(float)
;;     stewardship = defaultdict(float)
;;     fragility = defaultdict(float)
;;     congestion_out = defaultdict(float)
;; 
;;     for e in edges:
;;         kind = e.get(":en/kind")
;;         load_ = float(e.get(":en/orbit-load", 0.0) or 0.0)
;;         src, dst = e.get(":en/from"), e.get(":en/to")
;;         if kind in HAZARD_KINDS:
;;             shell = nodes.get(dst, {})
;;             w = REGIME_WEIGHT.get(shell.get(":shell/regime"), 0.6)
;;             congestion[dst] += load_ * w
;;             congestion_out[src] += load_
;;         elif kind in STEWARDSHIP_KINDS:
;;             stewardship[dst] += load_
;;         elif kind in DEPENDENCY_KINDS:
;;             fragility[src] += load_
;;             fragility[dst] += load_
;; 
;;     return {
;;         "congestion": dict(congestion),
;;         "stewardship": dict(stewardship),
;;         "fragility": dict(fragility),
;;         "congestion_out": dict(congestion_out),
;;     }
(defn analyze [& _]
  (throw (ex-info "TODO: port-failed" {:from "analyze"})))

;; TODO: port-failed unit _rank (assembled-lint error)
;; def _rank(d: dict, nodes: dict, limit: int = 20):
;;     rows = sorted(d.items(), key=lambda kv: -kv[1])[:limit]
;;     return [(nid, nodes.get(nid, {}).get(":organism/label", nid), v) for nid, v in rows]
(defn rank [& _]
  (throw (ex-info "TODO: port-failed" {:from "_rank"})))

;; TODO: port-failed unit report_md (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmprmdz6w4a/scratch.clj:2:30: w)
;; def report_md(nodes: dict, edges: list, res: dict) -> str:
;;     n_shell = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":shell")
;;     n_op = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":operator")
;;     n_haz = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":hazard")
;;     auth = sum(1 for n in nodes.values() if n.get(":organism/sourcing") == ":authoritative")
;; 
;;     L = []
;;     L.append("# hoshimori 星守 — orbital-congestion stewardship report (shell-aggregate)\n")
;;     L.append("> **G1 — STEWARDSHIP map, NEVER a targeting / interception aid.** No precise "
;;              "predictive ephemeris (no interception-grade state vector); readouts are "
;;              "orbital-shell / regime-aggregate. The 取-holder is the hazard/occupancy; the "
;;              "bearer is the regime + the public services on it; the routing is stewardship "
;;              "(orbital sustainability). Regime defs + named public debris EVENTS are DISCLOSED "
;;              "(N3). Congestion lives only on edges, integrated on read (N1). Mirrors only "
;;              "already-public catalogs.\n")
;;     L.append(f"**Graph**: {len(nodes)} nodes ({n_shell} shells · {n_op} operators · "
;;              f"{n_haz} hazards) · {len(edges)} 縁 · {auth}/{len(nodes)} :authoritative\n")
;; 
;;     L.append("\n## Congestion concentration — regimes bearing the most crowding/collision risk\n")
;;     L.append("_Σ incident inbound hazard/occupancy load × disclosed regime weight; routed to stewardship._\n")
;;     L.append("| rank | shell | regime | congestion |")
;;     L.append("|---:|---|:--:|---:|")
;;     for i, (nid, label, v) in enumerate(_rank(res["congestion"], nodes), 1):
;;         reg = nodes.get(nid, {}).get(":shell/regime", "—") or "—"
;;         L.append(f"| {i} | {label} | {reg.lstrip(':')} | {v:.3f} |")
;; 
;;     L.append("\n## Occupancy / hazard concentration — 取-holders crowding or imperiling orbit\n")
;;     L.append("_Σ outbound occupancy/hazard load; routed to deconfliction + debris remediation._\n")
;;     L.append("| rank | source | load |")
;;     L.append("|---:|---|---:|")
;;     for i, (nid, label, v) in enumerate(_rank(res["congestion_out"], nodes), 1):
;;         L.append(f"| {i} | {label} | {v:.3f} |")
;; 
;;     L.append("\n## Stewardship buffers — remediation / deconfliction / disposal (the 守り)\n")
;;     L.append("| rank | node | stewardship-buffer |")
;;     L.append("|---:|---|---:|")
;;     for i, (nid, label, v) in enumerate(_rank(res["stewardship"], nodes, 12), 1):
;;         L.append(f"| {i} | {label} | {v:.3f} |")
;; 
;;     L.append("\n## Service-dependency fragility — public utilities exposed to a regime's loss\n")
;;     L.append("| rank | node | fragility |")
;;     L.append("|---:|---|---:|")
;;     for i, (nid, label, v) in enumerate(_rank(res["fragility"], nodes, 10), 1):
;;         L.append(f"| {i} | {label} | {v:.3f} |")
;; 
;;     L.append("\n---\n_hoshimori 星守 · ADR-2606073600 · mirror-only · stewardship-routed · "
;;              "non-adjudicating · no-targeting · edge-primary. Live catalog ingest is "
;;              "G7/Council-gated._\n")
;;     return "\n".join(L)
(defn report-md [& _]
  (throw (ex-info "TODO: port-failed" {:from "report_md"})))

;; TODO: port-failed unit main (assembled-lint error)
;; def main(argv):
;;     here = pathlib.Path(__file__).resolve().parent.parent
;;     seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
;;         else here / "data" / "seed-orbit-graph.kotoba.edn"
;;     outdir = here / "out"
;;     if "--out" in argv:
;;         outdir = pathlib.Path(argv[argv.index("--out") + 1])
;;     outdir.mkdir(parents=True, exist_ok=True)
;; 
;;     nodes, edges = load(seed)
;;     res = analyze(nodes, edges)
;;     (outdir / "congestion-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
;;     print(f"hoshimori: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'congestion-report.md'}")
;;     top = _rank(res["congestion"], nodes, 1)
;;     if top:
;;         print(f"  top congestion concentration: {top[0][1]} ({top[0][2]:.3f})")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

