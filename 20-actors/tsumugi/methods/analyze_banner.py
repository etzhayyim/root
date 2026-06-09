#!/usr/bin/env python3
"""tsumugi 紡ぎ — (B / 旗 hata) ideology / faction (意識的 power-camp) analyzer.

ADR-2606092000 · vocab = 00-contracts/schemas/banner-ontology.kotoba.edn

Reads a kotoba-EDN banner graph (:banner/* standards + :ent/* public entities + :flies/*
alignment 縁) and computes, EDGE-PRIMARY and AGGREGATE-FIRST, the present-day camps —
which public entities openly fly which banners, how banners descend from historical
thought-streams, and which entities BRIDGE camps (pluralism). A mirror of declared public
alignment, never a ranking of conviction and never a thought-registry.

THE THOUGHT-POLICING GUARD (read banner-ontology header) — enforced here as ValueError:
  H1 public-declared basis only — :flies/basis ∈ {self-declared,public-stated,voting-record,
     formal-membership}; :inferred/:suspected/:imputed/:alleged RAISE.
  H2 non-adjudicating — threat tokens (:extremist/:過激/…) unrepresentable; RAISE.
  H3 edge-primary — alignment on :flies/* only; no :ent/ideology-score (RAISE if present).
  H4 person-excluded — :flies/who must be institutional/public-seat/self; private RAISE.
  H6 plural — entities may fly many banners; multi-banner entities are BRIDGES, not anomalies.
  H7 sourcing — every :flies carries ≥2 public citations; under-sourced RAISES.

Pure stdlib (pywasm-ready). Usage:
    python3 analyze_banner.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SEED = ACTOR_DIR / "data" / "seed-banner.kotoba.edn"

# ── minimal EDN reader ────────────────────────────────────────────────────────────────────
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
BANNER_KINDS = [":political-platform", ":doctrinal", ":school-of-thought", ":policy-stance"]
ENT_STANDINGS = [":institutional", ":public-seat", ":self"]
FLIES_BASES = [":self-declared", ":public-stated", ":voting-record", ":formal-membership"]
# H2 threat tokens + H1 inference tokens + H3 forbidden node attrs
THREAT_TOKENS = {":extremist", ":radical", ":dangerous", ":過激", ":危険思想",
                 ":反社会", ":terrorist", ":テロ"}
INFER_TOKENS = {":inferred", ":suspected", ":imputed", ":alleged"}
FORBIDDEN_ENT_ATTRS = {":ent/ideology-score", ":ent/conviction", ":ent/leaning",
                       ":ent/loyalty", ":banner/threat-level", ":banner/verdict"}


def load(seed_path=DEFAULT_SEED):
    """Read + validate the banner graph. Returns (banners, ents, flies). Raises on breach."""
    records = read_edn(pathlib.Path(seed_path).read_text(encoding="utf-8"))
    banners, ents, flies = {}, {}, []
    for r in records:
        if not isinstance(r, dict):
            continue
        if ":banner/id" in r:
            _validate_banner(r)
            banners[r[":banner/id"]] = r
        elif ":ent/id" in r:
            _validate_ent(r)
            ents[r[":ent/id"]] = r
        elif ":flies/id" in r:
            flies.append(r)
    for f in flies:
        _validate_flies(f, banners, ents)
    return banners, ents, flies


def _validate_banner(b):
    k = b.get(":banner/kind")
    if k in THREAT_TOKENS:
        raise ValueError(f"H2 breach: threat token {k} as :banner/kind on {b.get(':banner/id')} "
                         "(a banner is a standard flown, never a danger-classification)")
    if k not in BANNER_KINDS:
        raise ValueError(f"closed-vocab breach: :banner/kind {k!r} on {b.get(':banner/id')}")
    for a in b:
        if a in FORBIDDEN_ENT_ATTRS:
            raise ValueError(f"H2/H3 breach: forbidden attr {a} on {b.get(':banner/id')}")


def _validate_ent(e):
    for a in e:
        if a in FORBIDDEN_ENT_ATTRS:
            raise ValueError(f"H3 breach: per-entity score attr {a} on {e.get(':ent/id')} "
                             "(alignment is edge-primary; no score-of-conviction)")
    st = e.get(":ent/standing")
    if st not in ENT_STANDINGS:
        raise ValueError(f"H4 breach: :ent/standing {st!r} on {e.get(':ent/id')} not in "
                         f"{ENT_STANDINGS} (private persons unrepresentable; not a belief registry)")


def _validate_flies(f, banners, ents):
    basis = f.get(":flies/basis")
    if basis in INFER_TOKENS:
        raise ValueError(f"H1 breach: inference basis {basis} on {f.get(':flies/id')} "
                         "(only on-the-record public declarations; no imputed ideology)")
    if basis not in FLIES_BASES:
        raise ValueError(f"closed-vocab breach: :flies/basis {basis!r} on {f.get(':flies/id')}")
    who = f.get(":flies/who")
    if who not in ents:
        raise ValueError(f"dangling :flies/who {who!r} on {f.get(':flies/id')}")
    if ents[who].get(":ent/standing") not in ENT_STANDINGS:
        raise ValueError(f"H4 breach: {who} is not institutional/public-seat/self")
    if f.get(":flies/banner") not in banners:
        raise ValueError(f"dangling :flies/banner {f.get(':flies/banner')!r} on {f.get(':flies/id')}")
    srcs = f.get(":flies/sources") or []
    if not isinstance(srcs, list) or len(srcs) < 2:
        raise ValueError(f"H7 breach: :flies/sources on {f.get(':flies/id')} has <2 public citations")
    w = f.get(":flies/weight")
    if not isinstance(w, (int, float)) or not (0.0 <= w <= 1.0):
        raise ValueError(f"range breach: :flies/weight {w!r} on {f.get(':flies/id')} ∉ [0,1]")


def analyze(banners, ents, flies):
    """Compute aggregate-first camps + bridges + genealogy. Deterministic dict."""
    # per-banner reach = integral of incident :flies weights (H3 edge-primary). H5: a self
    # node's inbound-only banner is disclosure, excluded from the projected-over-others camps.
    reach = {bid: {"weight": 0.0, "fliers": []} for bid in banners}
    ent_banners = {}
    for f in flies:
        bid, who = f.get(":flies/banner"), f.get(":flies/who")
        inbound_self = bool(f.get(":flies/inbound-only")) and ents[who].get(":ent/standing") == ":self"
        reach[bid]["weight"] += float(f.get(":flies/weight", 0.0))
        reach[bid]["fliers"].append({"who": who, "label": ents[who].get(":ent/label"),
                                     "basis": f.get(":flies/basis"),
                                     "weight": float(f.get(":flies/weight", 0.0)),
                                     "inbound_only": inbound_self})
        if not inbound_self:  # H5 — etzhayyim's own banner is not a camp it recruits others into
            ent_banners.setdefault(who, set()).add(bid)

    camps = sorted(({"banner": bid, "label": banners[bid].get(":banner/label"),
                     "kind": banners[bid].get(":banner/kind"),
                     "thought_stream": banners[bid].get(":banner/thought-stream"),
                     "reach": round(d["weight"], 4),
                     "member_count": len([x for x in d["fliers"] if not x["inbound_only"]]),
                     "fliers": sorted(d["fliers"], key=lambda x: (-x["weight"], x["who"]))}
                    for bid, d in reach.items()),
                   key=lambda x: (-x["reach"], x["banner"]))

    # H6 — bridges: entities flying ≥2 banners (pluralism, surfaced positively)
    bridges = sorted(({"ent": who, "label": ents[who].get(":ent/label"),
                       "banners": sorted(bs), "span": len(bs)}
                      for who, bs in ent_banners.items() if len(bs) >= 2),
                     key=lambda x: (-x["span"], x["ent"]))

    # genealogy — banner ← historical thought-stream (ADR-2606061500)
    genealogy = sorted(({"banner": bid, "label": b.get(":banner/label"),
                         "stream": b.get(":banner/thought-stream")}
                        for bid, b in banners.items() if b.get(":banner/thought-stream")),
                       key=lambda x: x["banner"])

    return {"camps": camps, "bridges": bridges, "genealogy": genealogy,
            "banner_count": len(banners), "ent_count": len(ents), "flies_count": len(flies)}


def render_report(result):
    L = ["# tsumugi (B / 旗 hata) — declared ideology / faction camps",
         "",
         "> **Mirror of DECLARED public alignment. Non-adjudicating. Person-excluded. Plural.**",
         "> Alignment is EDGE-PRIMARY (no score-of-conviction). Basis is always on-the-record",
         "> (self-declared / public-stated / vote / membership) — never imputed. A banner is a",
         "> standard flown, NEVER a danger-classification. etzhayyim discloses its OWN banner.",
         "",
         f"banners: {result['banner_count']} · entities: {result['ent_count']} · "
         f"alignments: {result['flies_count']}",
         "",
         "## Camps by reach (Σ declared-alignment weight)",
         "",
         "| banner | kind | ← stream | reach | members |",
         "|---|---|---|---|---|"]
    for c in result["camps"]:
        L.append(f"| {c['label']} | {c['kind']} | {c['thought_stream'] or '—'} | "
                 f"**{c['reach']}** | {c['member_count']} |")
    L += ["", "## Bridges (H6 — entities flying ≥2 banners = pluralism, not anomaly)", "",
          "| entity | banners | span |", "|---|---|---|"]
    for b in result["bridges"]:
        L.append(f"| {b['label']} | {' · '.join(b['banners'])} | {b['span']} |")
    if not result["bridges"]:
        L.append("| (none) | | |")
    L += ["", "## Genealogy — present banner ← historical thought-stream (ADR-2606061500)", "",
          "| banner | ← stream |", "|---|---|"]
    for g in result["genealogy"]:
        L.append(f"| {g['label']} | {g['stream']} |")
    return "\n".join(L) + "\n"


def render_graph_edn(result):
    L = [";; tsumugi (B / 旗) banner-graph — GENERATED; computed-on-read readouts (H3).",
         ";; reach is a per-BANNER aggregate of edge weights, NOT a per-entity score. No hand-edit.",
         "["]
    for c in result["camps"]:
        L.append(f' {{:banner.camp/banner "{c["banner"]}" '
                 f':banner.camp/reach {c["reach"]} '
                 f':banner.camp/members {c["member_count"]}}}')
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    seed = args[0] if args else DEFAULT_SEED
    out = pathlib.Path(ACTOR_DIR / "out")
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    out.mkdir(parents=True, exist_ok=True)
    banners, ents, flies = load(seed)
    result = analyze(banners, ents, flies)
    (out / "banner-report.md").write_text(render_report(result), encoding="utf-8")
    (out / "banner-graph.kotoba.edn").write_text(render_graph_edn(result), encoding="utf-8")
    top = result["camps"][0] if result["camps"] else None
    if top:
        print(f"[tsumugi/banner] top camp: {top['label']} (reach {top['reach']}, "
              f"{top['member_count']} members) · {len(result['bridges'])} bridges "
              f"→ out/banner-report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
