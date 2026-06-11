#!/usr/bin/env python3
"""tate 盾 — disadvantageous-clause scanner over the member's OWN contracts / ToS.

ADR-2606112300. Matches the member's contract texts (consumer ToS / credit-card member
agreement / B2B 法人契約) against the coded clause-pattern registry and emits FLAGS:
pattern + DISCLOSED statutory anchor + risk + route (kurashimori rights / kaiyaku
severance / professional referral). 不利な契約をしていないか — surfaced, not adjudicated.

CONSTITUTIONAL (read before any change):
  G1 — member-principal, own documents only. tate scans documents the MEMBER is party
    to and supplies (R0 = synthetic seed). Never a third party's contracts.
  G2 — non-adjudicating (UPL). A flag is {pattern, anchor, risk, route} — a pointer to
    a DISCLOSED statute, never a validity verdict. There is no :flag/verdict; report
    language stays "可能性 — 専門家確認".
  G5 — context honesty. Consumer-protection anchors (消費者契約法 etc.) are NEVER
    applied to :b2b documents — B2B has materially fewer protections and routes
    referral-forward instead.

Pure stdlib — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 terms_scan.py [docs.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, pathlib
from collections import defaultdict

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


HERE = pathlib.Path(__file__).resolve().parent.parent
RISK_ORDER = {":high": 0, ":mid": 1, ":info": 2}


def load_patterns(path: pathlib.Path | None = None) -> list:
    path = path or HERE / "data" / "clause-patterns.edn"
    return [f for f in read_edn(path.read_text(encoding="utf-8")) if ":clause/id" in f]


def load_docs(path: pathlib.Path | None = None):
    path = path or HERE / "data" / "seed-member-docs.edn"
    forms = read_edn(path.read_text(encoding="utf-8"))
    docs = [f for f in forms if isinstance(f, dict) and ":doc/id" in f]
    notices = [f for f in forms if isinstance(f, dict) and ":notice/id" in f]
    return docs, notices


def scan_doc(doc: dict, patterns: list) -> list:
    """Flags for one document. G5: pattern context must match the document context.
    G10: pattern jurisdiction must match the document jurisdiction (default :jp for
    R0 back-compat) — a 消費者契約法 anchor can never fire on a US doc and vice versa."""
    flags = []
    text = doc.get(":doc/text", "").casefold()  # case-insensitive — sentence-initial capitals must not hide a clause
    ctx = doc.get(":doc/context")
    juris = doc.get(":doc/jurisdiction", ":jp")
    for p in patterns:
        if p[":clause/context"] != ctx:
            continue  # G5 — consumer anchors never cross into :b2b and vice versa
        if p.get(":clause/jurisdiction", ":jp") != juris:
            continue  # G10 — anchors never cross jurisdictions
        hit = next((k for k in p[":clause/keywords"] if k.casefold() in text), None)
        if hit is None:
            continue
        flags.append({
            "doc": doc[":doc/id"],
            "doc_label": doc.get(":doc/label", doc[":doc/id"]),
            "jurisdiction": juris,
            "clause": p[":clause/id"],
            "clause_label": p[":clause/label"],
            "matched": hit,
            "risk": p[":clause/risk"],
            "anchor": p[":clause/anchor"],          # DISCLOSED pointer — never a verdict (G2)
            "route": p[":clause/route"],
            "disclosed": True,
            "verify_current_law": True,
        })
    flags.sort(key=lambda f: (RISK_ORDER.get(f["risk"], 9), f["clause"]))
    return flags


def scan(docs: list, patterns: list):
    flags = [f for d in docs for f in scan_doc(d, patterns)]
    by_route = defaultdict(int)
    for f in flags:
        by_route[f["route"]] += 1
    return {"flags": flags,
            "docs_scanned": len(docs),
            "counts_by_route": dict(sorted(by_route.items()))}


def report(res: dict) -> str:
    L = ["# tate 盾 — 不利条項 readout (non-adjudicating, G2)", ""]
    L.append(f"- docs scanned: {res['docs_scanned']} · flags: {len(res['flags'])} · "
             f"routes: {res['counts_by_route']}")
    L.append("")
    L.append("| doc | juris | clause | risk | 開示アンカー | route |")
    L.append("|---|---|---|---|---|---|")
    for f in res["flags"]:
        L.append(f"| {f['doc_label']} | {f['jurisdiction']} | {f['clause_label']} | {f['risk']} "
                 f"| {f['anchor']} | {f['route']} |")
    L.append("")
    L.append("各フラグは「該当する **可能性** のある条項パターン + 開示済み法令アンカー」です。"
             "有効/無効の判断はしません — 高リスクは法テラス・弁護士会の専門家確認へ (G2 UPL)。")
    return "\n".join(L) + "\n"


def main(argv):
    docs_path = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") else None
    out = HERE / "out"
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    docs, _ = load_docs(docs_path)
    res = scan(docs, load_patterns())
    out.mkdir(parents=True, exist_ok=True)
    (out / "clause-readout.md").write_text(report(res), encoding="utf-8")
    print(f"tate: {len(res['flags'])} clause flags over {res['docs_scanned']} docs "
          f"→ {out / 'clause-readout.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
