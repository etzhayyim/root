#!/usr/bin/env python3
"""subaru 昴 — connectivity link-budget analyzer over the constellation graph.

ADR-2606162355. Reads a kotoba-EDN constellation graph (:organism/* nodes + :en/* 縁 over the
constellation-ontology) and computes — deterministically, pure stdlib — the per-link budget
margin and the G1 surveillance-unrepresentability check. This is the engineering core the other
methods import.

  link margin (dB) = EIRP − path-loss + G/T − required-C/N   (per :link)

CONSTITUTIONAL (read before any change):
  G1 — connectivity COMMONS, NEVER a surveillance / targeting / military-C2 platform. There is
    NO deep-packet-inspection, user-geolocation-as-product, or targeting-relay attribute — the
    schema omits them and check_g1 refuses any graph that introduces one. Service is keyed to
    :service-area (aggregate region), never to a tracked person.
  G2 — no person-tracking; subscriber content is E2E-encrypted ciphertext routed but unread.
  G8 — sourcing honesty. Numbers are representative engineering estimates.

Pure stdlib (no numpy) — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 link_budget.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, pathlib

# ── minimal EDN reader (subset: vectors [], maps {}, :keyword, "string", num, bool, nil)
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':  return True
    if t == 'false': return False
    if t == 'nil':   return None
    if t.startswith(':'):
        return t
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


_END = object()


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


def read_edn(text: str):
    return _parse(_tokens(text))


# G1 — attributes that would turn the constellation into a surveillance / targeting platform.
# None of these may EVER appear (the schema omits them; this is the runtime backstop).
BANNED_ATTRS = (":link/inspect", ":link/dpi", ":user/location", ":subscriber/geo",
                ":relay/targeting", ":traffic/retain", ":content/plaintext")
# G3 — the ONLY admissible entitlement kinds (no subscription / ad-supported member).
COMMONS_ENTITLEMENT = {":social-security-level-0", ":sbt-internal"}


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from a constellation EDN graph."""
    forms = read_edn(path.read_text(encoding="utf-8"))
    nodes, edges = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":organism/id" in f:
            nodes[f[":organism/id"]] = f
        elif ":en/from" in f and ":en/to" in f:
            edges.append(f)
    return nodes, edges


def check_g1(nodes: dict):
    """G1/G3: connectivity commons — no surveillance/targeting attr, no for-profit entitlement.

    Raises ValueError on any banned attribute or non-commons entitlement kind.
    """
    for nid, n in nodes.items():
        for b in BANNED_ATTRS:
            if b in n:
                raise ValueError(f"G1 violation: surveillance/targeting attr {b} on {nid}")
        if n.get(":organism/kind") == ":entitlement":
            k = n.get(":entitlement/kind")
            if k not in COMMONS_ENTITLEMENT:
                raise ValueError(f"G3 violation: non-commons entitlement {k} on {nid}")
        # service must be keyed to an aggregate region, never to a person
        if n.get(":organism/kind") == ":service-area" and not n.get(":area/region"):
            raise ValueError(f"G1 violation: service-area {nid} lacks an aggregate :area/region")
    return True


def link_budget(nodes: dict, edges: list):
    """Per-link margin (computed on read; transient — N1)."""
    check_g1(nodes)
    rows = []
    for n in nodes.values():
        if n.get(":organism/kind") != ":link":
            continue
        eirp = float(n.get(":link/eirp-dbw", 0.0))
        ploss = float(n.get(":link/path-loss-db", 0.0))
        gt = float(n.get(":link/gt-dbk", 0.0))
        req = float(n.get(":link/required-cn-db", 0.0))
        margin = eirp - ploss + gt - req
        rows.append({"link": n[":organism/id"], "label": n.get(":organism/label"),
                     "band": n.get(":link/band"), "kind": n.get(":link/kind"),
                     "margin_db": margin})
    rows.sort(key=lambda r: r["margin_db"])
    return {"links": rows, "min_margin_db": rows[0]["margin_db"] if rows else 0.0,
            "all_closed": all(r["margin_db"] > 0 for r in rows)}


def report_md(nodes, edges, res) -> str:
    L = ["# subaru 昴 — connectivity link-budget report\n"]
    L.append("> **G1 — connectivity COMMONS, NEVER a surveillance / targeting / military-C2 "
             "platform.** No DPI, no user-geolocation-as-product, no targeting relay; service "
             "keyed to aggregate :service-area, never a person. **G2** content E2E-encrypted "
             "(routed, unread). **G8** representative engineering estimates.\n")
    L.append("\n## Per-link budget (margin = EIRP − path-loss + G/T − required-C/N, on read)\n")
    L.append("| link | band | margin (dB) | closed? |")
    L.append("|---|:--:|---:|:--:|")
    for r in res["links"]:
        L.append(f"| {r['label']} | {str(r['band']).lstrip(':')} | {r['margin_db']:.1f} | "
                 f"{'✅' if r['margin_db'] > 0 else '❌'} |")
    L.append(f"\n**Minimum margin: {res['min_margin_db']:.1f} dB** — "
             f"{'✅ all links close' if res['all_closed'] else '❌ a link does not close'}\n")
    L.append("\n---\n_subaru 昴 · ADR-2606162355 · connectivity-commons · no-surveillance · "
             "cash≡0 §1.16 in-kind · representative estimates. Live ops Council-gated._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-constellation.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    res = link_budget(nodes, edges)
    (outdir / "link-budget-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"subaru link-budget: {len(res['links'])} links, min margin "
          f"{res['min_margin_db']:.1f} dB → {outdir/'link-budget-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
