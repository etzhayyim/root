;; ported from 20-actors/kanjo/methods/analyze.py (unit_refactor stage 0)
;; kanjō 勘定 — analyze cell (stdlib only).
(ns kanjo.methods.analyze
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare here load-company-meta meta load fact-key by-company-year derive-metrics metric aggregates fmt-money pct report edn-dump v main)

;; TODO: port-failed unit HERE (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmptnjag5s6/scratch.clj:2:1: er)
;; HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
;; COMPANY_META = {
;;     "org.corp.jp.toyota":    ("Toyota Motor",      ":automotive",  "JP"),
;;     "org.corp.jp.sony":      ("Sony Group",        ":electronics", "JP"),
;;     "org.corp.jp.nintendo":  ("Nintendo",          ":consumer",    "JP"),
;;     "org.corp.us.apple":     ("Apple",             ":electronics", "US"),
;;     "org.corp.us.microsoft": ("Microsoft",         ":software",    "US"),
;; }
;; KABUTO_SEED = os.path.join(HERE, "..", "kabuto", "data", "seed-public-companies.kotoba.edn")
;; CCY_SYM = {":jpy": "¥", ":usd": "$", ":eur": "€", ":gbp": "£"}
(def here nil) ;; TODO: port-failed const

;; TODO: port-failed unit load_company_meta (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpnx28ayox/scratch.clj:3:23: w)
;; def load_company_meta():
;;     """Join kabuto's :company graph (SSoT) for name/sector/country; fall back to inlined meta.
;; 
;;     Returns {company-id: (name, sector-keyword, country)}. kabuto wins where present so the two
;;     actors never disagree on a company's sector/jurisdiction (shared org.corp.* id space)."""
;;     meta = dict(COMPANY_META)
;;     if os.path.exists(KABUTO_SEED):
;;         try:
;;             for r in kanjo_edn.read_file(KABUTO_SEED):
;;                 cid = r.get(":company/id")
;;                 if not cid:
;;                     continue
;;                 meta[cid] = (
;;                     r.get(":company/name", meta.get(cid, (cid,))[0]),
;;                     r.get(":company/sector", meta.get(cid, (None, ":unknown"))[1]),
;;                     r.get(":company/country", meta.get(cid, (None, None, "?"))[2]),
;;                 )
;;         except Exception:
;;             pass  # kabuto seed unreadable → inlined fallback (analyze stays self-contained)
;;     return meta
(defn load-company-meta [& _]
  (throw (ex-info "TODO: port-failed" {:from "load_company_meta"})))

(def meta (load-company-meta))

(defn load [path]
  (let [rows (kanjo-edn/read-file path)
        filings (reduce (fn [acc r]
                          (if (contains? r ":fin.filing/id")
                            (assoc acc (:fin.filing/id r) r)
                            acc))
                        {} rows)
        facts (filter (fn [r] (contains? r ":fin.fact/id")) rows)]
    [filings facts]))

(defn fact-key [f]
  {:company (get f ":fin.fact/company") :filing-id (if false nil)})

;; TODO: port-failed unit by_company_year (assembled-lint error)
;; def by_company_year(facts):
;;     """{company: {fy: {concept(no colon): (value, unit, scale)}}}"""
;;     out = {}
;;     for f in facts:
;;         if f.get(":fin.fact/context") != ":consolidated":
;;             continue
;;         co = f[":fin.fact/company"]
;;         # fiscal year = the year the period ends (from period-end ISO date)
;;         fy = int(f[":fin.fact/period-end"][:4])
;;         concept = f[":fin.fact/concept"].lstrip(":")
;;         out.setdefault(co, {}).setdefault(fy, {})[concept] = (
;;             float(f[":fin.fact/value"]), f[":fin.fact/unit"], f[":fin.fact/scale"])
;;     return out
(defn by-company-year [& _]
  (throw (ex-info "TODO: port-failed" {:from "by_company_year"})))

;; TODO: port-failed unit derive_metrics (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpyqtclri7/scratch.clj:26:1: e)
;; def derive_metrics(cy):
;;     """→ list of :fin.metric dicts (all :synthesized)."""
;;     metrics = []
;;     mi = metric_inputs()
;;     for co, years in cy.items():
;;         for fy, concepts in years.items():
;;             vals = {k: v[0] for k, v in concepts.items()}
;;             for kind, (num, den) in mi.items():
;;                 if num in vals and den in vals and vals[den] != 0:
;;                     metrics.append(_metric(co, fy, kind, vals[num] / vals[den],
;;                                            f"{num}/{den}"))
;;             # YoY growth vs the immediately prior fiscal year, if present
;;             prev = years.get(fy - 1)
;;             if prev:
;;                 for kind, concept in (("revenue-yoy", "revenue"),
;;                                       ("operating-income-yoy", "operating-income"),
;;                                       ("net-income-yoy", "net-income")):
;;                     if concept in vals and concept in {k: v[0] for k, v in prev.items()}:
;;                         p = prev[concept][0]
;;                         if p != 0:
;;                             metrics.append(_metric(co, fy, kind, (vals[concept] - p) / p,
;;                                                    f"{concept}[{fy}] vs {concept}[{fy-1}]"))
;;     return metrics
(defn derive-metrics [& _]
  (throw (ex-info "TODO: port-failed" {:from "derive_metrics"})))

;; TODO: port-failed unit _metric (assembled-lint error)
;; def _metric(co, fy, kind, value, basis):
;;     return {
;;         ":fin.metric/id": f"metric.{co}.{fy}.{kind}",
;;         ":fin.metric/company": co,
;;         ":fin.metric/fiscal-year": fy,
;;         ":fin.metric/kind": ":" + kind,
;;         ":fin.metric/value": round(value, 4),
;;         ":fin.metric/basis": basis,
;;         ":fin.metric/sourcing": ":synthesized",
;;     }
(defn metric [& _]
  (throw (ex-info "TODO: port-failed" {:from "_metric"})))

;; TODO: port-failed unit aggregates (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpl8c6ed70/scratch.clj:2:1: er)
;; def aggregates(cy):
;;     """Σ revenue per (sector, currency) — coverage-honest; NEVER cross-currency summed (no FX in R0)."""
;;     aggs = {}
;;     for co, years in cy.items():
;;         sector = META.get(co, ("", ":unknown", ""))[1]
;;         for fy, concepts in years.items():
;;             if "revenue" not in concepts:
;;                 continue
;;             val, unit, _scale = concepts["revenue"]
;;             key = (sector, unit, fy)
;;             a = aggs.setdefault(key, {"sum": 0.0, "n": 0})
;;             a["sum"] += val
;;             a["n"] += 1
;;     out = []
;;     for (sector, unit, fy), a in sorted(aggs.items()):
;;         out.append({
;;             ":fin.agg/id": f"agg.sector.{sector.lstrip(':')}.{unit.lstrip(':')}.{fy}.revenue",
;;             ":fin.agg/dimension": ":sector",
;;             ":fin.agg/key": sector.lstrip(":"),
;;             ":fin.agg/fiscal-year": fy,
;;             ":fin.agg/concept": ":revenue",
;;             ":fin.agg/sum": a["sum"],
;;             ":fin.agg/n": a["n"],
;;             ":fin.agg/sourcing": ":synthesized",
;;         })
;;     return out
(defn aggregates [& _]
  (throw (ex-info "TODO: port-failed" {:from "aggregates"})))

;; TODO: port-failed unit fmt_money (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp8gjgalr6/scratch.clj:3:18: w)
;; def fmt_money(v, unit, scale=":millions"):
;;     sym = CCY_SYM.get(unit, unit.lstrip(":").upper() + " ")
;;     # value is in millions; show tn / bn for readability
;;     if scale == ":millions":
;;         if abs(v) >= 1_000_000:
;;             return f"{sym}{v/1_000_000:.2f}tn"
;;         if abs(v) >= 1_000:
;;             return f"{sym}{v/1_000:.1f}bn"
;;     return f"{sym}{v:,.0f}m"
(defn fmt-money [& _]
  (throw (ex-info "TODO: port-failed" {:from "fmt_money"})))

(defn pct [x]
  (str (format "%.1f%%" (* x 100))))

;; TODO: port-failed unit report (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmph7c19mt3/scratch.clj:2:1: er)
;; def report(filings, facts, cy, metrics, aggs):
;;     L = []
;;     A = L.append
;;     sources = sorted({f[":fin.filing/source"] for f in filings.values()})
;;     companies = sorted(cy.keys())
;;     A("# kanjō 勘定 — 決算 (financial-disclosure) intel report")
;;     A("")
;;     A("> Aggregate-first, **non-adjudicating** (G2), **no investment advice** (G4). Every figure is")
;;     A("> either disclosed by the company in a primary filing (EDINET / EDGAR) or a transparent ratio")
;;     A("> of two disclosed figures (`:synthesized`, G5). This is a transparency map, never a verdict")
;;     A("> or a recommendation. Seed cohort is `:representative` — see honesty note.")
;;     A("")
;;     A("## Coverage")
;;     A("")
;;     A(f"- **Filings**: {len(filings)} · **Facts**: {len(facts)} · **Companies**: {len(companies)} · "
;;       f"**Metrics derived**: {len(metrics)}")
;;     A(f"- **Primary-disclosure sources**: {', '.join(s.lstrip(':') for s in sources)} "
;;       f"(all Tier-A per ADR-2605263800 §2 — NO 四季報 / no paid terminal, G1)")
;;     A(f"- **Sourcing**: every fact `:representative` in this seed (headline figures, rounded). "
;;       f"Authoritative line-item XBRL = G7 operator-gated (`ingest.py`).")
;;     A("")
;;     A("## Per-company FY2024 (as disclosed + derived ratios)")
;;     A("")
;;     A("| Company | Ctry | Revenue | Op income | Net income | Op margin | Net margin | ROE | Equity ratio |")
;;     A("|---|---|--:|--:|--:|--:|--:|--:|--:|")
;;     for co in companies:
;;         years = cy[co]
;;         fy = max(years.keys())
;;         c = years[fy]
;;         name, _sector, ctry = META.get(co, (co, "", "?"))
;;         unit = c.get("revenue", (0, ":usd", ":millions"))[1]
;;         rev = fmt_money(c["revenue"][0], unit) if "revenue" in c else "—"
;;         opi = fmt_money(c["operating-income"][0], unit) if "operating-income" in c else "—"
;;         ni = fmt_money(c["net-income"][0], unit) if "net-income" in c else "—"
;;         mm = {m[":fin.metric/kind"]: m[":fin.metric/value"]
;;               for m in metrics if m[":fin.metric/company"] == co and m[":fin.metric/fiscal-year"] == fy}
;;         opm = pct(mm[":operating-margin"]) if ":operating-margin" in mm else "—"
;;         nm = pct(mm[":net-margin"]) if ":net-margin" in mm else "—"
;;         roe = pct(mm[":roe"]) if ":roe" in mm else "—"
;;         eq = pct(mm[":equity-ratio"]) if ":equity-ratio" in mm else "—"
;;         A(f"| {name} | {ctry} | {rev} | {opi} | {ni} | {opm} | {nm} | {roe} | {eq} |")
;;     A("")
;;     A("_Margins/ROE are `:synthesized` ratios of disclosed figures. Revenue shown in the filing's own")
;;     A("currency — kanjō does NOT FX-convert in R0, so figures across currencies are NOT comparable as-is._")
;;     A("")
;;     yoy = [m for m in metrics if m[":fin.metric/kind"].endswith("-yoy")]
;;     if yoy:
;;         A("## Year-over-year (as-of history — 非終末論, prior facts retained)")
;;         A("")
;;         A("| Company | FY | Revenue YoY | Op income YoY | Net income YoY |")
;;         A("|---|--:|--:|--:|--:|")
;;         byco = {}
;;         for m in yoy:
;;             byco.setdefault((m[":fin.metric/company"], m[":fin.metric/fiscal-year"]), {})[m[":fin.metric/kind"]] = m[":fin.metric/value"]
;;         for (co, fy), kinds in sorted(byco.items()):
;;             name = META.get(co, (co,))[0]
;;             r = pct(kinds[":revenue-yoy"]) if ":revenue-yoy" in kinds else "—"
;;             o = pct(kinds[":operating-income-yoy"]) if ":operating-income-yoy" in kinds else "—"
;;             n = pct(kinds[":net-income-yoy"]) if ":net-income-yoy" in kinds else "—"
;;             A(f"| {name} | {fy} | {r} | {o} | {n} |")
;;         A("")
;;     A("## Sector aggregates (coverage-honest — read against `n`, never a market total; G3/G5)")
;;     A("")
;;     A("| Sector | Currency | FY | Σ revenue | n companies |")
;;     A("|---|---|--:|--:|--:|")
;;     for a in aggs:
;;         unit = ":" + a[":fin.agg/id"].split(".")[-3]
;;         A(f"| {a[':fin.agg/key']} | {unit.lstrip(':').upper()} | {a[':fin.agg/fiscal-year']} | "
;;           f"{fmt_money(a[':fin.agg/sum'], unit)} | {a[':fin.agg/n']} |")
;;     A("")
;;     A("> Σ is bounded by what is ingested — it is NOT the sector's market total. Cross-currency sums")
;;     A("> are deliberately NOT computed (no FX layer in R0). Absence of a company ≠ zero.")
;;     A("")
;;     A("## Honesty (R0)")
;;     A("")
;;     A("- Bounded `:representative` seed of a few real filers (JP EDINET + US EDGAR). \"Register ALL")
;;     A("  companies' 決算\" is the **R1** goal — full EDINET/EDGAR-universe XBRL parse is **G7** Council +")
;;     A("  operator gated (`ingest.py`).")
;;     A("- Figures are publicly-documented HEADLINE numbers, rounded — not the authoritative line-item XBRL.")
;;     A("- 経常利益 (`:ordinary-income`) is JGAAP-only; it is recorded where filed (Nintendo) but is NOT")
;;     A("  cross-compared to US-GAAP / IFRS filers (concept_map note).")
;;     A("- kanjō does not forecast (no 業績予想 — that is exactly what the prohibited 四季報 adds), does not")
;;     A("  rate, value, or advise. It records what was disclosed and the arithmetic of it.")
;;     return "\n".join(L) + "\n"
(defn report [& _]
  (throw (ex-info "TODO: port-failed" {:from "report"})))

;; TODO: port-failed unit edn_dump (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmphpmdewc7/scratch.clj:4:87: i)
;; def edn_dump(metrics, aggs):
;;     L = [";; kanjō 勘定 — derived financial metrics + aggregates (GENERATED by analyze.py)",
;;          ";; ADR-2606032000 · all :synthesized (G5) — NEVER re-ingested as disclosed facts.",
;;          "["]
;;     for m in metrics:
;;         L.append(" {" + " ".join(f"{k} {_v(v)}" for k, v in m.items()) + "}")
;;     for a in aggs:
;;         L.append(" {" + " ".join(f"{k} {_v(v)}" for k, v in a.items()) + "}")
;;     L.append("]")
;;     return "\n".join(L) + "\n"
(defn edn-dump [& _]
  (throw (ex-info "TODO: port-failed" {:from "edn_dump"})))

;; TODO: port-failed unit _v (assembled-lint error)
;; def _v(v):
;;     if isinstance(v, str):
;;         return v if v.startswith(":") else '"' + v.replace('"', '\\"') + '"'
;;     if isinstance(v, bool):
;;         return "true" if v else "false"
;;     return repr(v)
(defn v [& _]
  (throw (ex-info "TODO: port-failed" {:from "_v"})))

;; TODO: port-failed unit main (assembled-lint error)
;; def main():
;;     src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "data", "seed-financial-facts.kotoba.edn")
;;     filings, facts = load(src)
;;     cy = by_company_year(facts)
;;     metrics = derive_metrics(cy)
;;     aggs = aggregates(cy)
;;     outdir = os.path.join(HERE, "out")
;;     os.makedirs(outdir, exist_ok=True)
;;     with open(os.path.join(outdir, "intel-report.md"), "w") as f:
;;         f.write(report(filings, facts, cy, metrics, aggs))
;;     with open(os.path.join(outdir, "financial-metrics.kotoba.edn"), "w") as f:
;;         f.write(edn_dump(metrics, aggs))
;;     print(f"kanjō analyze: {len(filings)} filings · {len(facts)} facts · {len(cy)} companies · "
;;           f"{len(metrics)} metrics · {len(aggs)} aggregates")
;;     print(f"  → out/intel-report.md")
;;     print(f"  → out/financial-metrics.kotoba.edn")
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

