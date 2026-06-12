#!/usr/bin/env python3
"""tate 盾 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).

GROUND (durable, op :add) — the member's docs/notices (synthetic at R0) and the coded
registries (clause patterns + procedures: disclosed shapes, not member data).
DERIVED (transient, :bond/is-transient true) — clause flags + response-plan status.
Per G2 a flag/plan is computed on READ and never stored as ground state: a stale
"this clause is risky" pointer can never outlive the registry or the document.

Pure stdlib — runnable inside the tate kotoba pywasm actor (componentize-py).
Usage:
    python3 datom_emit.py [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from terms_scan import load_docs, load_patterns, scan, HERE  # noqa: E402
from respond_plan import load_procs, plans  # noqa: E402

DOC_ATTRS = [":doc/label", ":doc/jurisdiction", ":doc/context", ":doc/sourcing"]
NOTICE_ATTRS = [":notice/label", ":notice/jurisdiction", ":notice/channel",
                ":notice/claim-jpy", ":notice/claim-amount", ":notice/claim-currency",
                ":notice/sourcing"]
CLAUSE_ATTRS = [":clause/label", ":clause/jurisdiction", ":clause/context", ":clause/risk",
                ":clause/anchor", ":clause/route", ":clause/verify-current-law"]
PROC_ATTRS = [":proc/label", ":proc/jurisdiction", ":proc/verify-current-law"]


def _fmt(v) -> str:
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "nil"
    if isinstance(v, str):
        return v if v.startswith(":") else '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def emit(tx: int = 1) -> str:
    docs, notices = load_docs()
    patterns = load_patterns()
    procs = load_procs()
    res = scan(docs, patterns)
    ps = plans(notices, procs)

    L = []
    L.append(";; tate 盾 — GENERATED kotoba Datom log (ADR-2606112301). DO NOT hand-edit.")
    L.append(";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    L.append(";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (G2).")
    L.append("")
    L.append(";; ── GROUND: registries (disclosed shapes)")
    for p in patterns:
        for a in CLAUSE_ATTRS:
            if a in p:
                L.append(f'[{_fmt(p[":clause/id"])} {a} {_fmt(p[a])} {tx} :add]')
    for p in procs:
        for a in PROC_ATTRS:
            if a in p:
                L.append(f'[{_fmt(p[":proc/id"])} {a} {_fmt(p[a])} {tx} :add]')
    L.append("")
    L.append(";; ── GROUND: member docs/notices (synthetic at R0 — G1)")
    for d in docs:
        for a in DOC_ATTRS:
            if a in d:
                L.append(f'[{_fmt(d[":doc/id"])} {a} {_fmt(d[a])} {tx} :add]')
    for n in notices:
        for a in NOTICE_ATTRS:
            if a in n:
                L.append(f'[{_fmt(n[":notice/id"])} {a} {_fmt(n[a])} {tx} :add]')
    L.append("")
    L.append(";; ── DERIVED (transient — flags/plans computed on read, G2)")
    for i, f in enumerate(res["flags"]):
        eid = _fmt(f"flag:{i:03d}")
        L.append(f'[{eid} :bond/is-transient true {tx} :add]')
        L.append(f'[{eid} :tate/doc {_fmt(f["doc"])} {tx} :add]')
        L.append(f'[{eid} :tate/clause {_fmt(f["clause"])} {tx} :add]')
        L.append(f'[{eid} :tate/risk {f["risk"]} {tx} :add]')
        L.append(f'[{eid} :tate/route {f["route"]} {tx} :add]')
    for p in ps:
        eid = _fmt(f"plan:{p['notice']}")
        L.append(f'[{eid} :bond/is-transient true {tx} :add]')
        L.append(f'[{eid} :tate/status {p["status"]} {tx} :add]')
        L.append(f'[{eid} :tate/options {len(p["options"])} {tx} :add]')
    L.append("")
    L.append(f';; flags={len(res["flags"])} plans={len(ps)}')
    return "\n".join(L) + "\n"


def main(argv):
    out = HERE / "out"
    tx = 1
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    if "--tx" in argv:
        tx = int(argv[argv.index("--tx") + 1])
    text = emit(tx)
    out.mkdir(parents=True, exist_ok=True)
    (out / "tate-datoms.kotoba.edn").write_text(text, encoding="utf-8")
    print(f"tate: {text.count(':add')} datoms → {out / 'tate-datoms.kotoba.edn'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
