;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hinagata/methods/publish.py (unit_refactor stage 0)
;; hinagata 雛形 — publish the template commons (content-addressed, anyone may fetch + reuse).
(ns root.hinagata.methods.publish
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare cite-kinds publish main)

(def CITE_KINDS (set [":cites-statute" ":mandated-by"]))

;; TODO: port-failed unit publish (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpl_lxjycy/scratch.clj:47:49: )
;; def publish(nodes: dict, edges: list, outdir: pathlib.Path) -> dict:
;;     bodies = outdir / "bodies"
;;     bodies.mkdir(parents=True, exist_ok=True)
;; 
;;     cites = {}
;;     for e in edges:
;;         if e.get(":en/kind") in CITE_KINDS:
;;             cites.setdefault(e[":en/from"], []).append(e[":en/to"])
;;     has_clause = {}
;;     for e in edges:
;;         if e.get(":en/kind") == ":has-clause":
;;             has_clause.setdefault(e[":en/from"], []).append(e[":en/to"])
;;     governed = {}
;;     for e in edges:
;;         if e.get(":en/kind") == ":governed-by":
;;             governed.setdefault(e[":en/from"], []).append(e[":en/to"])
;; 
;;     templates = [nid for nid in nodes if nodes[nid].get(":lt/kind") == ":template"]
;;     entries = []
;;     for tid in templates:
;;         body = render_document(tid, nodes, edges)
;;         raw = body.encode("utf-8")
;;         cid = cidv1_raw(raw)
;;         (bodies / f"{tid}.md").write_text(body, encoding="utf-8")
;;         # statutes cited anywhere in this template's clauses (the law it rests on)
;;         statutes = []
;;         for cl in has_clause.get(tid, []):
;;             for st in cites.get(cl, []):
;;                 s = nodes.get(st, {})
;;                 statutes.append({"id": st, "citation": s.get(":statute/citation"),
;;                                  "instrument": s.get(":statute/instrument"),
;;                                  "url": s.get(":statute/url")})
;;         t = nodes[tid]
;;         entries.append({
;;             "id": tid,
;;             "title": t.get(":template/title"),
;;             "lang": t.get(":template/lang"),
;;             "license": (t.get(":template/license") or "Apache-2.0") + " + etzhayyim Charter Rider",
;;             "version": t.get(":template/version"),
;;             "stance": str(t.get(":template/stance", "")).lstrip(":"),
;;             "jurisdictions": [nodes.get(j, {}).get(":jurisdiction/code") for j in governed.get(tid, [])],
;;             "bodyCid": cid,
;;             "bodySha256": sha256_hex(raw),
;;             "bytes": len(raw),
;;             "clauseCount": len(has_clause.get(tid, [])),
;;             "statutes": statutes,
;;         })
;; 
;;     manifest = {
;;         "actor": "hinagata",
;;         "adr": "2606111954",
;;         "schema": "legal-template-ontology@0.1.0",
;;         "license": "Apache-2.0 + etzhayyim Charter Rider v3.0",
;;         "note": ("Public legal-document template commons. Every body is content-addressed "
;;                  "(CIDv1 raw/sha2-256) and free to copy + adapt. NOT legal advice (G1)."),
;;         "templateCount": len(entries),
;;         "templates": sorted(entries, key=lambda e: e["id"]),
;;     }
;;     (outdir / "publish-manifest.json").write_text(
;;         json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
;; 
;;     # human index
;;     L = ["# hinagata 雛形 — published legal-template commons\n",
;;          "> Fair, openly-licensed legal-document templates (Apache-2.0 + etzhayyim Charter "
;;          "Rider). Each body is content-addressed — re-derive the CID with `ipfs add "
;;          "--cid-version=1 --raw-leaves` or `methods/cid.py` to verify. **NOT legal advice** "
;;          "(G1); each clause cites the public law it rests on, for traceability.\n",
;;          f"\n**{len(entries)} templates published.**\n",
;;          "\n| template | lang | jurisdiction | clauses | statutes | bodyCid |",
;;          "|---|:--:|:--:|---:|---:|---|"]
;;     for e in sorted(entries, key=lambda e: e["id"]):
;;         jx = ",".join(x for x in e["jurisdictions"] if x) or "—"
;;         L.append(f"| {e['title']} | {e['lang']} | {jx} | {e['clauseCount']} | "
;;                  f"{len(e['statutes'])} | `{e['bodyCid'][:18]}…` |")
;;     L.append("\n---\n_hinagata 雛形 · ADR-2606111954 · commons-not-counsel · G7 outward publish "
;;              "(IPFS pin / IPNS) is the operator add-on._\n")
;;     (outdir / "PUBLISH.md").write_text("\n".join(L), encoding="utf-8")
;;     return manifest
(defn publish [& _]
  (throw (ex-info "TODO: port-failed" {:from "publish"})))

;; TODO: port-failed unit main (zebulun: timed out)
;; def main(argv):
;;     here = pathlib.Path(__file__).resolve().parent.parent
;;     seed = here / "data" / "seed-legal-template-graph.kotoba.edn"
;;     if len(argv) > 1 and not argv[1].startswith("--"):
;;         seed = pathlib.Path(argv[1])
;;     outdir = pathlib.Path(argv[argv.index("--out") + 1]) if "--out" in argv \
;;         else here.parent.parent / "80-data" / "legal-templates"
;;     nodes, edges = load(seed)
;;     m = publish(nodes, edges, outdir)
;;     print(f"hinagata publish → {outdir} ({m['templateCount']} templates content-addressed)")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

