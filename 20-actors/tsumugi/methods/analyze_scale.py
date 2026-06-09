#!/usr/bin/env python3
"""tsumugi 紡ぎ — (A) scale-agnostic 産官学報 power-concentration analyzer.

ADR-2606092000 · vocab = 00-contracts/schemas/power-scale-ontology.kotoba.edn

Reads a kotoba-EDN scale-power graph (:pwr/* nodes + :tie/* 縁) and computes, EDGE-PRIMARY
and AGGREGATE-FIRST, how tightly each LOCALITY and each SCALE weaves its 産官学報
(industry/government/academia/press) sectors together — the cross-sector concentration,
routed to OPENING. It is a structural map, never a verdict and never a target-list.

Constitutional (read power-scale-ontology header):
  S1 edge-primary — concentration = integral of incident cross-sector :tie/grasping-load;
     there is NO per-node score (validator raises if :pwr/power-score etc. appears).
  S2 person-excluded — :pwr/standing ∈ {:institutional :public-seat}; :private-person raises.
  S5 non-adjudicating — verdict tokens (癒着/談合/capture…) unrepresentable; validator raises.

Pure stdlib (pywasm-ready). Usage:
    python3 analyze_scale.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SEED = ACTOR_DIR / "data" / "seed-scale-power.kotoba.edn"

# ── minimal EDN reader (vectors [], maps {}, :keyword, "string", num, bool, nil) ──────────
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
_END = object()

def _tokens(s):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t

def _atom(t):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':  return True
    if t == 'false': return False
    if t == 'nil':   return None
    if t.startswith(':'):
        return t
    try:    return int(t)
    except ValueError:
        try: return float(t)
        except ValueError: return t

def _parse(it):
    t = next(it)
    if t == '[':
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == '{':
        out = {}
        while (k := _parse(it)) is not _END:
            out[k] = _parse(it)
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)

def read_edn(text):
    return _parse(_tokens(text))

# ── closed vocabs (mirror the ontology :db/allowed) ───────────────────────────────────────
SECTORS = [":san", ":kan", ":gaku", ":hou", ":min", ":kin"]
SECTOR_JA = {":san": "産", ":kan": "官", ":gaku": "学", ":hou": "報", ":min": "民", ":kin": "金"}
SCALES = [":global", ":supranational", ":national", ":regional", ":municipal",
          ":local", ":intra-org"]
COLLECTIVE_KINDS = [":org", ":region", ":municipality", ":community", ":intra-org-faction",
                    ":academic-clique", ":keiretsu", ":advisory-body"]
COLLECTIVE_JA = {":org": "組織/企業単位", ":region": "地域(県)", ":municipality": "市区町村",
                 ":community": "コミュニティ", ":intra-org-faction": "社内派閥",
                 ":academic-clique": "学閥", ":keiretsu": "系列", ":advisory-body": "審議会"}
STANDINGS = [":institutional", ":public-seat"]
TIE_KINDS = [":custodies", ":depends-on", ":funds", ":awards", ":seats-on",
             ":co-member", ":supplies", ":covers", ":employs", ":follows"]
# S5/S1 forbidden tokens (verdict + per-node score attrs)
VERDICT_TOKENS = {":corruption", ":collusion", ":capture", ":癒着", ":汚職",
                  ":談合", ":guilt", ":不正"}
FORBIDDEN_NODE_ATTRS = {":pwr/power-score", ":pwr/influence", ":pwr/rank", ":pwr/score"}


def load(seed_path=DEFAULT_SEED):
    """Read + validate the scale-power graph. Returns (nodes, ties). Raises on gate breach."""
    records = read_edn(pathlib.Path(seed_path).read_text(encoding="utf-8"))
    nodes, ties = {}, []
    for r in records:
        if not isinstance(r, dict):
            continue
        if ":pwr/id" in r:
            _validate_node(r)
            nodes[r[":pwr/id"]] = r
        elif ":tie/id" in r:
            _validate_tie(r)
            ties.append(r)
    return nodes, ties


def _validate_node(n):
    # S1 — no per-node score attr may exist
    for a in n:
        if a in FORBIDDEN_NODE_ATTRS:
            raise ValueError(f"S1 breach: per-node score attr {a} on {n.get(':pwr/id')} "
                             "(concentration is edge-primary; integral computed on read)")
    # S2 — person-exclusion
    st = n.get(":pwr/standing")
    if st not in STANDINGS:
        raise ValueError(f"S2 breach: :pwr/standing {st!r} on {n.get(':pwr/id')} "
                         f"not in {STANDINGS} (private persons unrepresentable; seats only)")
    if n.get(":pwr/scale") not in SCALES:
        raise ValueError(f"closed-vocab breach: :pwr/scale {n.get(':pwr/scale')!r} on {n.get(':pwr/id')}")
    if n.get(":pwr/sector") not in SECTORS:
        raise ValueError(f"closed-vocab breach: :pwr/sector {n.get(':pwr/sector')!r} on {n.get(':pwr/id')}")
    ck = n.get(":pwr/collective-kind")
    if ck is not None and ck not in COLLECTIVE_KINDS:
        raise ValueError(f"closed-vocab breach: :pwr/collective-kind {ck!r} on {n.get(':pwr/id')}")


def _validate_tie(t):
    k = t.get(":tie/kind")
    if k in VERDICT_TOKENS:
        raise ValueError(f"S5 breach: verdict token {k} as :tie/kind on {t.get(':tie/id')} "
                         "(concentration is structural, never a verdict)")
    if k not in TIE_KINDS:
        raise ValueError(f"closed-vocab breach: :tie/kind {k!r} on {t.get(':tie/id')}")
    srcs = t.get(":tie/sources") or []
    if not isinstance(srcs, list) or len(srcs) < 2:
        raise ValueError(f"S4 breach: :tie/sources on {t.get(':tie/id')} has <2 public citations")
    gl = t.get(":tie/grasping-load")
    if not isinstance(gl, (int, float)) or not (0.0 <= gl <= 1.0):
        raise ValueError(f"range breach: :tie/grasping-load {gl!r} on {t.get(':tie/id')} ∉ [0,1]")


def analyze(nodes, ties):
    """Compute aggregate-first, edge-primary concentration. Returns a deterministic dict."""
    sector_of = {nid: n.get(":pwr/sector") for nid, n in nodes.items()}
    locality_of = {nid: n.get(":pwr/locality") for nid, n in nodes.items()}
    scale_of = {nid: n.get(":pwr/scale") for nid, n in nodes.items()}

    # per-locality cross-sector readout (S3 aggregate-first)
    loc = {}
    for t in ties:
        f, to = t.get(":tie/from"), t.get(":tie/to")
        if f not in nodes or to not in nodes:
            continue
        lf, lt = locality_of[f], locality_of[to]
        sf, st = sector_of[f], sector_of[to]
        gl = float(t.get(":tie/grasping-load", 0.0))
        if lf == lt:  # a within-locality tie contributes to that locality's fabric
            d = loc.setdefault(lf, {"sectors": set(), "cross_load": 0.0,
                                    "cross_ties": 0, "all_load": 0.0, "all_ties": 0})
            d["sectors"].update([sf, st])
            d["all_load"] += gl; d["all_ties"] += 1
            if sf != st:  # cross-SECTOR (産↔官↔学↔報) is the 産官学報 weave
                d["cross_load"] += gl; d["cross_ties"] += 1

    localities = []
    for lname, d in loc.items():
        diversity = len(d["sectors"])
        concentration = round(d["cross_load"] * diversity, 4)  # edge-primary integral × breadth
        localities.append({
            "locality": lname,
            "sector_diversity": diversity,
            "sectors": sorted(SECTOR_JA.get(s, s) for s in d["sectors"]),
            "cross_sector_load": round(d["cross_load"], 4),
            "cross_sector_ties": d["cross_ties"],
            "concentration": concentration,
        })
    localities.sort(key=lambda x: (-x["concentration"], x["locality"]))

    # per-scale aggregate
    scale_agg = {}
    for t in ties:
        f, to = t.get(":tie/from"), t.get(":tie/to")
        if f not in nodes or to not in nodes:
            continue
        gl = float(t.get(":tie/grasping-load", 0.0))
        for s in {scale_of[f], scale_of[to]}:
            d = scale_agg.setdefault(s, {"load": 0.0, "ties": 0})
            d["load"] += gl; d["ties"] += 1
    scales = sorted(({"scale": s, "load": round(d["load"], 4), "ties": d["ties"]}
                     for s, d in scale_agg.items()),
                    key=lambda x: (-x["load"], x["scale"]))

    # cross-sector brokers — entities whose incident ties span the most OTHER sectors (S3, seat/org id only)
    span = {}
    for t in ties:
        f, to = t.get(":tie/from"), t.get(":tie/to")
        if f not in nodes or to not in nodes:
            continue
        gl = float(t.get(":tie/grasping-load", 0.0))
        for a, b in ((f, to), (to, f)):
            if sector_of[a] != sector_of[b]:
                d = span.setdefault(a, {"sectors": set(), "load": 0.0})
                d["sectors"].add(sector_of[b]); d["load"] += gl
    brokers = sorted(({"id": nid, "label": nodes[nid].get(":pwr/label"),
                       "sector": SECTOR_JA.get(sector_of[nid], sector_of[nid]),
                       "bridges_to": sorted(SECTOR_JA.get(s, s) for s in d["sectors"]),
                       "span": len(d["sectors"]), "cross_load": round(d["load"], 4)}
                      for nid, d in span.items()),
                     key=lambda x: (-x["span"], -x["cross_load"], x["id"]))

    # per-collective-kind aggregate (粒度: 組織/地域/コミュニティ/社内派閥/学閥) — S3 aggregate
    ck_of = {nid: n.get(":pwr/collective-kind") for nid, n in nodes.items()}
    ck_agg = {}
    for t in ties:
        f, to = t.get(":tie/from"), t.get(":tie/to")
        if f not in nodes or to not in nodes:
            continue
        gl = float(t.get(":tie/grasping-load", 0.0))
        for nid in {f, to}:
            ck = ck_of.get(nid)
            if ck:
                d = ck_agg.setdefault(ck, {"load": 0.0, "nodes": set()})
                d["load"] += gl; d["nodes"].add(nid)
    collective_kinds = sorted(({"kind": ck, "ja": COLLECTIVE_JA.get(ck, ck),
                                "node_count": len(d["nodes"]), "load": round(d["load"], 4)}
                               for ck, d in ck_agg.items()),
                              key=lambda x: (-x["load"], x["kind"]))

    # cross-scale VERTICAL integration — follow :pwr/parent chains; how one org's power
    # threads THROUGH scales (国→県→市→社内). Edge-primary load aggregated per family (S1/S3).
    parent_of = {nid: n.get(":pwr/parent") for nid, n in nodes.items()}

    def _root_of(nid):
        cur, seen = nid, set()
        while True:
            p = parent_of.get(cur)
            if not p or p in seen:
                return cur
            seen.add(cur)
            if p not in nodes:   # parent referenced but not itself a node → the family root key
                return p
            cur = p

    nload = {}
    for t in ties:
        gl = float(t.get(":tie/grasping-load", 0.0))
        for x in (t.get(":tie/from"), t.get(":tie/to")):
            if x in nodes:
                nload[x] = nload.get(x, 0.0) + gl
    fam = {}
    for nid, n in nodes.items():
        r = _root_of(nid)
        d = fam.setdefault(r, {"scales": set(), "localities": set(), "members": 0, "load": 0.0})
        d["scales"].add(scale_of.get(nid)); d["localities"].add(locality_of.get(nid))
        d["members"] += 1; d["load"] += nload.get(nid, 0.0)
    vertical = sorted(({"root": r, "label": (nodes[r].get(":pwr/label") if r in nodes else r),
                        "scale_span": len(d["scales"]),
                        "scales": sorted(s for s in d["scales"] if s),
                        "locality_span": len(d["localities"]), "members": d["members"],
                        "load": round(d["load"], 4)}
                       for r, d in fam.items() if len(d["scales"]) >= 2),
                      key=lambda x: (-x["scale_span"], -x["locality_span"], -x["load"], x["root"]))

    return {"localities": localities, "scales": scales, "brokers": brokers,
            "collective_kinds": collective_kinds, "vertical": vertical,
            "node_count": len(nodes), "tie_count": len(ties)}


def render_report(result):
    L = ["# tsumugi (A) — scale-agnostic 産官学報 concentration",
         "",
         "> **Map, not target. Aggregate-first. Person-excluded (seats only). Non-adjudicating.**",
         "> Concentration is the EDGE-PRIMARY integral of cross-sector co-location, routed to OPENING.",
         "> Co-location density is a structural fact — never a verdict (癒着/談合 unrepresentable).",
         "",
         f"nodes: {result['node_count']} · ties: {result['tie_count']}",
         "",
         "## Localities by 産官学報 cross-sector concentration",
         "",
         "| locality | sectors woven | diversity | cross-load | concentration |",
         "|---|---|---|---|---|"]
    for x in result["localities"]:
        L.append(f"| {x['locality']} | {' '.join(x['sectors'])} | {x['sector_diversity']} | "
                 f"{x['cross_sector_load']} | **{x['concentration']}** |")
    L += ["", "## Scales (same lens, every scale)", "",
          "| scale | incident load | ties |", "|---|---|---|"]
    for x in result["scales"]:
        L.append(f"| {x['scale']} | {x['load']} | {x['ties']} |")
    if result.get("collective_kinds"):
        L += ["", "## Granularity (粒度: 組織/地域/コミュニティ/社内派閥/学閥)", "",
              "| collective-kind | nodes | incident load |", "|---|---|---|"]
        for x in result["collective_kinds"]:
            L.append(f"| {x['ja']} (`{x['kind']}`) | {x['node_count']} | {x['load']} |")
    if result.get("vertical"):
        L += ["", "## Vertically-integrated organizations (跨-scale 縦の集中 — :pwr/parent chains)", "",
              "| organization (root) | scale span | scales | localities | incident load |",
              "|---|---|---|---|---|"]
        for x in result["vertical"][:10]:
            L.append(f"| {x['label']} | **{x['scale_span']}** | {' '.join(x['scales'])} | "
                     f"{x['locality_span']} | {x['load']} |")
    L += ["", "## Cross-sector brokers (seat/org, never a person)", "",
          "| id | sector | bridges to | span | cross-load |", "|---|---|---|---|---|"]
    for x in result["brokers"][:10]:
        L.append(f"| `{x['id']}` | {x['sector']} | {' '.join(x['bridges_to'])} | "
                 f"{x['span']} | {x['cross_load']} |")
    return "\n".join(L) + "\n"


def render_graph_edn(result):
    """Emit per-locality computed readouts as datoms (S1 — readout, not a stored node score)."""
    L = [";; tsumugi (A) scale-graph — GENERATED; computed-on-read readouts (S1).",
         ";; concentration is a per-LOCALITY aggregate, NOT a per-node score. Do not hand-edit.",
         "["]
    for x in result["localities"]:
        L.append(f' {{:scale.cluster/locality "{x["locality"]}" '
                 f':scale.cluster/sector-diversity {x["sector_diversity"]} '
                 f':scale.cluster/cross-sector-load {x["cross_sector_load"]} '
                 f':scale.cluster/concentration {x["concentration"]}}}')
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    seed = args[0] if args else DEFAULT_SEED
    out = pathlib.Path(ACTOR_DIR / "out")
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    out.mkdir(parents=True, exist_ok=True)
    nodes, ties = load(seed)
    result = analyze(nodes, ties)
    (out / "scale-report.md").write_text(render_report(result), encoding="utf-8")
    (out / "scale-graph.kotoba.edn").write_text(render_graph_edn(result), encoding="utf-8")
    top = result["localities"][0] if result["localities"] else None
    if top:
        print(f"[tsumugi/scale] top locality: {top['locality']} "
              f"(diversity {top['sector_diversity']}, concentration {top['concentration']}) "
              f"→ out/scale-report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
