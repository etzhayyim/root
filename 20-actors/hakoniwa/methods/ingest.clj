;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hakoniwa/methods/ingest.py (unit_refactor stage 0)
;; hakoniwa 箱庭 — REAL PUBLIC-entity ingest → enriched box → kotoba EDN + content-address.
(ns root.hakoniwa.methods.ingest
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare ua entitydata-url fetch-entity label p31 prop-targets h u generate-personas build-box fmt node-order to-edn main)

(def UA "etzhayyim-hakoniwa/0.1 (+https://etzhayyim.com; public-entity ingest)")
(def TIMEOUT 20)
(def COHORTS (set [":prepared-anchor" ":cautious-commuter" ":skeptic" ":connector" ":newcomer"]))

;; TODO: port-failed unit _entitydata_url (bb-compile error)
;; def _entitydata_url(base: str, qid: str) -> str:
;;     return base.rstrip("/") + "/" + qid + ".json"
(defn entitydata-url [& _]
  (throw (ex-info "TODO: port-failed" {:from "_entitydata_url"})))

;; TODO: port-failed unit fetch_entity (assembled-lint error)
;; def fetch_entity(base: str, qid: str) -> dict:
;;     """Fetch one Wikidata entity record (PUBLIC, no auth). Returns the entity sub-dict."""
;;     req = urllib.request.Request(_entitydata_url(base, qid),
;;                                  headers={"User-Agent": UA, "Accept": "application/json"})
;;     with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
;;         doc = json.loads(r.read().decode("utf-8"))
;;     return doc["entities"][qid]
(defn fetch-entity [& _]
  (throw (ex-info "TODO: port-failed" {:from "fetch_entity"})))

(defn _label [ent]
  (let [labels (get ent "labels" {})]
    (some (fn [lang]
             (if (contains? labels lang)
               (get-in labels [lang "value"])
               nil))
           ["en" "ja"])
    (or (get ent "id") "?")))

;; TODO: port-failed unit _p31 (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp11sfqv_3/scratch.clj:5:15: e)
;; def _p31(ent: dict) -> list[str]:
;;     out = []
;;     for claim in ent.get("claims", {}).get("P31", []):
;;         try:
;;             out.append(claim["mainsnak"]["datavalue"]["value"]["id"])
;;         except (KeyError, TypeError):
;;             continue
;;     return out
(defn p31 [& _]
  (throw (ex-info "TODO: port-failed" {:from "_p31"})))

;; TODO: port-failed unit _prop_targets (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmplqx1zphi/scratch.clj:5:15: e)
;; def _prop_targets(ent: dict, pid: str) -> list[str]:
;;     out = []
;;     for claim in ent.get("claims", {}).get(pid, []):
;;         try:
;;             out.append(claim["mainsnak"]["datavalue"]["value"]["id"])
;;         except (KeyError, TypeError):
;;             continue
;;     return out
(defn prop-targets [& _]
  (throw (ex-info "TODO: port-failed" {:from "_prop_targets"})))

;; TODO: port-failed unit _h (assembled-lint error)
;; def _h(*parts) -> int:
;;     return int.from_bytes(hashlib.sha256(":".join(map(str, parts)).encode()).digest()[:6], "big")
(defn h [& _]
  (throw (ex-info "TODO: port-failed" {:from "_h"})))

(defn u [*parts]
  (/ (mod (h *parts) 100000) 100000.0))

;; TODO: port-failed unit generate_personas (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp6v1jlqme/scratch.clj:8:25: e)
;; def generate_personas(n: int, topic_id: str, seed: int = 7) -> tuple[list[dict], list[dict]]:
;;     """Generate n SYNTHETIC fictional-archetype personas (G1) deliberating over the topic.
;;     Deterministic (hash-seeded). Returns (persona_nodes, edges: stance + influence)."""
;;     personas, edges = [], []
;;     for i in range(n):
;;         cohort = COHORTS[i % len(COHORTS)]
;;         # cohort-shaped priors with deterministic jitter (no Math.random)
;;         base_sus = {":prepared-anchor": 0.18, ":cautious-commuter": 0.47, ":skeptic": 0.30,
;;                     ":connector": 0.62, ":newcomer": 0.78}[cohort]
;;         base_stance = {":prepared-anchor": 0.82, ":cautious-commuter": 0.53, ":skeptic": 0.20,
;;                        ":connector": 0.50, ":newcomer": 0.44}[cohort]
;;         sus = round(min(0.95, max(0.05, base_sus + (_u(seed, "sus", i) - 0.5) * 0.1)), 3)
;;         stance = round(min(0.95, max(0.05, base_stance + (_u(seed, "st", i) - 0.5) * 0.1)), 3)
;;         pid = f"persona.g{i:02d}"
;;         node = {":sim/id": pid, ":sim/kind": ":persona",
;;                 ":sim/label": f"synthetic archetype {cohort.lstrip(':')} #{i}",
;;                 ":sim/sourcing": ":synthetic", ":persona/synthetic": True,
;;                 ":persona/cohort": cohort, ":persona/susceptibility": sus,
;;                 ":persona/initial-stance": stance}
;;         if cohort == ":connector":
;;             node[":persona/weight"] = 1.5
;;         personas.append(node)
;;         edges.append({":en/from": pid, ":en/to": topic_id, ":en/kind": ":holds-stance",
;;                       ":en/weight": stance, ":en/sourcing": ":synthetic"})
;;     # influence web: each persona is influenced by 2 deterministic others (small-world)
;;     for i in range(n):
;;         for k in range(2):
;;             j = _h(seed, "inf", i, k) % n
;;             if j != i:
;;                 w = round(0.3 + _u(seed, "w", i, k) * 0.5, 3)
;;                 edges.append({":en/from": f"persona.g{j:02d}", ":en/to": f"persona.g{i:02d}",
;;                               ":en/kind": ":influences", ":en/weight": w, ":en/sourcing": ":synthetic"})
;;     return personas, edges
(defn generate-personas [& _]
  (throw (ex-info "TODO: port-failed" {:from "generate_personas"})))

;; TODO: port-failed unit build_box (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpsqyiaj0i/scratch.clj:52:15: )
;; def build_box(sources: dict, fetched: dict[str, dict]) -> tuple[dict, list, dict]:
;;     """Fold the fetched REAL entities + generated SYNTHETIC personas into one box.
;;     Returns (nodes, edges, provenance). G1: real entities are orgs/topics; persons are dropped."""
;;     person_classes = set(sources.get(":ingest/person-classes", []))
;;     props = sources.get(":ingest/properties", {})
;;     topic = sources.get(":ingest/topic", {})
;;     n_personas = int(sources.get(":ingest/synthetic-personas", 16))
;; 
;;     nodes: dict = {}
;;     edges: list = []
;;     kept, dropped = [], []
;; 
;;     # topic entity (the deliberation anchor) + outcome
;;     topic_id = "entity.topic"
;;     nodes[topic_id] = {":sim/id": topic_id, ":sim/kind": ":entity",
;;                        ":sim/label": topic.get(":topic/label", "public topic"),
;;                        ":sim/sourcing": ":representative",
;;                        ":entity/public-ref": "topic.resilience-commons"}
;;     nodes["outcome.adoption"] = {":sim/id": "outcome.adoption", ":sim/kind": ":outcome",
;;                                  ":sim/label": "synthetic-cohort mean adoption stance",
;;                                  ":sim/sourcing": ":representative", ":outcome/measures": ":all",
;;                                  ":outcome/statistic": ":mean-stance",
;;                                  ":outcome/use": topic.get(":topic/use", ":preparedness")}
;; 
;;     # REAL public entities (G1: orgs/topics only — refuse natural persons)
;;     for spec in sources.get(":ingest/entities", []):
;;         qid = spec.get(":qid")
;;         ent = fetched.get(qid)
;;         if not ent:
;;             continue
;;         p31 = set(_p31(ent))
;;         if p31 & person_classes:
;;             dropped.append({"qid": qid, "reason": "natural-person (P31∈person-classes)"})
;;             continue                                   # G1 — never store a person
;;         eid = f"entity.wd-{qid.lower()}"
;;         nodes[eid] = {":sim/id": eid, ":sim/kind": ":entity", ":sim/label": _label(ent),
;;                       ":sim/sourcing": ":authoritative", ":entity/public-ref": f"wd:{qid}"}
;;         kept.append({"qid": qid, "label": _label(ent), "eid": eid})
;; 
;;     # structural :relates-to edges among the kept entities (closed box)
;;     kept_qids = {k["qid"]: k["eid"] for k in kept}
;;     for spec in sources.get(":ingest/entities", []):
;;         qid = spec.get(":qid")
;;         if qid not in kept_qids or qid not in fetched:
;;             continue
;;         for pname, pid in props.items():
;;             if pname == ":instance-of":
;;                 continue
;;             for tgt in _prop_targets(fetched[qid], pid):
;;                 if tgt in kept_qids:
;;                     edges.append({":en/from": kept_qids[qid], ":en/to": kept_qids[tgt],
;;                                   ":en/kind": ":relates-to", ":en/weight": 1.0,
;;                                   ":en/sourcing": ":authoritative"})
;; 
;;     # generated SYNTHETIC personas deliberating over the topic
;;     personas, pedges = generate_personas(n_personas, topic_id)
;;     for p in personas:
;;         nodes[p[":sim/id"]] = p
;;     edges.extend(pedges)
;; 
;;     # a sonae-style authoritative relay signal entering the box
;;     nodes["signal.relay"] = {":sim/id": "signal.relay", ":sim/kind": ":signal",
;;                              ":sim/label": "official preparedness advisory RELAY (sonae-style)",
;;                              ":sim/sourcing": ":representative",
;;                              ":signal/push": 0.15, ":signal/at-step": 3}
;;     for p in personas[: max(1, len(personas) * 2 // 3)]:
;;         edges.append({":en/from": p[":sim/id"], ":en/to": "signal.relay",
;;                       ":en/kind": ":exposed-to", ":en/weight": 1.0, ":en/sourcing": ":synthetic"})
;; 
;;     provenance = {"source": "wikidata", "kept": kept, "dropped": dropped,
;;                   "n_entities_kept": len(kept), "n_entities_dropped": len(dropped),
;;                   "n_personas": len(personas), "n_nodes": len(nodes), "n_edges": len(edges)}
;;     return nodes, edges, provenance
(defn build-box [& _]
  (throw (ex-info "TODO: port-failed" {:from "build_box"})))

;; TODO: port-failed unit _fmt (assembled-lint error)
;; def _fmt(v) -> str:
;;     if v is True:
;;         return "true"
;;     if v is False:
;;         return "false"
;;     if v is None:
;;         return "nil"
;;     if isinstance(v, str):
;;         return v if v.startswith(":") else json.dumps(v, ensure_ascii=False)
;;     if isinstance(v, float):
;;         return f"{v:g}"
;;     return str(v)
(defn fmt [& _]
  (throw (ex-info "TODO: port-failed" {:from "_fmt"})))

(def NODE_ORDER [":sim/kind" ":sim/label" ":sim/sourcing" ":entity/public-ref"
                  ":persona/synthetic" ":persona/cohort" ":persona/susceptibility"
                  ":persona/initial-stance" ":persona/weight" ":signal/push" ":signal/at-step"
                  ":outcome/measures" ":outcome/statistic" ":outcome/use"])

(def EDGE_ORDER [":en/from" ":en/to" ":en/kind" ":en/weight" ":en/sourcing"])

;; TODO: port-failed unit to_edn (assembled-lint error)
;; def to_edn(nodes: dict, edges: list) -> str:
;;     L = [";; hakoniwa 箱庭 — GENERATED ingested box (ADR-2606111500). DO NOT hand-edit.",
;;          ";; REAL PUBLIC entities (:authoritative, Wikidata CC0) + SYNTHETIC personas (:synthetic, G1).",
;;          ";; No natural persons (P31=Q5 dropped at ingest). No PII. Agents are fictional archetypes.",
;;          "["]
;;     for nid, n in nodes.items():
;;         parts = [f'{{:sim/id {_fmt(nid)}']
;;         for a in NODE_ORDER:
;;             if a in n and n[a] is not None:
;;                 parts.append(f"{a} {_fmt(n[a])}")
;;         L.append(" ".join(parts) + "}")
;;     for e in edges:
;;         parts = ["{"]
;;         parts += [f"{a} {_fmt(e[a])}" for a in EDGE_ORDER if a in e]
;;         L.append(" ".join(parts).replace("{ ", "{") + "}")
;;     L.append("]")
;;     return "\n".join(L) + "\n"
(defn to-edn [& _]
  (throw (ex-info "TODO: port-failed" {:from "to_edn"})))

;; TODO: port-failed unit main (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp_3l7v4dq/scratch.clj:3:8: er)
;; def main(argv):
;;     here = pathlib.Path(__file__).resolve().parent.parent
;;     src_path = here / "data" / "ingest-sources.edn"
;;     if "--sources" in argv:
;;         src_path = pathlib.Path(argv[argv.index("--sources") + 1])
;;     outdir = here / "out"
;;     if "--out" in argv:
;;         outdir = pathlib.Path(argv[argv.index("--out") + 1])
;;     offline = "--offline" in argv
;;     outdir.mkdir(parents=True, exist_ok=True)
;; 
;;     sources = W.read_edn(src_path.read_text(encoding="utf-8"))
;;     base = sources[":ingest/source"][":source/url"]
;;     qids = [s[":qid"] for s in sources[":ingest/entities"]]
;; 
;;     fetched: dict[str, dict] = {}
;;     errors = []
;;     if offline:
;;         fx = here / "tests" / "fixtures" / "wikidata_entities.json"
;;         fetched = json.loads(fx.read_text(encoding="utf-8"))
;;     else:
;;         for qid in qids:
;;             try:
;;                 fetched[qid] = fetch_entity(base, qid)
;;             except (urllib.error.URLError, KeyError, ValueError, TimeoutError, OSError) as e:
;;                 errors.append({"qid": qid, "error": str(e)})
;; 
;;     nodes, edges, prov = build_box(sources, fetched)
;;     W.assert_synthetic(nodes)                          # G1 re-check on the emitted box
;; 
;;     edn = to_edn(nodes, edges)
;;     (outdir / "ingested-box.kotoba.edn").write_text(edn, encoding="utf-8")
;;     box_cid = cidlib.cidv1_raw(edn.encode("utf-8"))
;;     prov.update({"errors": errors, "offline": offline, "box_cid": box_cid, "qids_requested": qids})
;;     (outdir / "ingest-provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=2),
;;                                                    encoding="utf-8")
;;     (outdir / "ingested-box.cid").write_text(box_cid + "\n", encoding="utf-8")
;; 
;;     print(f"hakoniwa ingest: {prov['n_entities_kept']} real entities kept, "
;;           f"{prov['n_entities_dropped']} dropped (G1), {prov['n_personas']} synthetic personas "
;;           f"→ {prov['n_nodes']} nodes / {prov['n_edges']} 縁")
;;     print(f"  box CID {box_cid}  ({'offline fixture' if offline else 'live Wikidata'})")
;;     if errors:
;;         print(f"  ⚠ {len(errors)} fetch error(s) — entity dropped from the bounded slice")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

