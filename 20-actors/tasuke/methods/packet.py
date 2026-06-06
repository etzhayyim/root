"""packet.py — 助 (tasuke) victim packet generator: the "誰でも使える" entry point.

Turns a victim's case into a complete, ready-to-print document packet a real person can take
to the police / their bank / a platform. This is the usable surface over the R0 engines:

    python3 packet.py                      # demo: first :representative seed case
    python3 packet.py --case <id>          # a specific seed case by :case/id
    python3 packet.py --file my-case.edn   # the member's OWN case (EDN, same shape as the seed)

It writes, into `out/packet-<caseId>/`:
    00-COVER.md           the action checklist + free public windows + deadlines + ¥0 statement
    NN-<doc-kind>.txt     each member-authored filing, ready to review · sign · submit

Every invariant the engines enforce is preserved here by construction — the cover restates that
the packet is FREE (G1), member-authored + member-submitted (G2/G3), and draft-only at R0 (G9);
`build_packet` runs `report_gen.assert_member_authored` on every document. 助 generates; the
member signs and submits. Stdlib only.
"""

from __future__ import annotations

import argparse
import pathlib

import report_gen as rg
from _edn import load_edn
from triage import triage


def _kw(v) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SEED = _ROOT / "data" / "seed-cybercrime-cases.kotoba.edn"
_OUT = _ROOT / "methods" / "out"
_REGISTRY = None  # lazy window registry


def documents_for_kind(case: dict, kind: str, evidence: list[dict] | None = None) -> list[dict]:
    """The single source of truth for which member-authored documents a scam KIND warrants.

    Always the police core (被害届 / 被害状況報告書 / 証拠目録 / 被害額算定書); plus a bank組戻し
    for money-moved cases, a platform request for account/identity cases, and a recovery plan when
    credentials were exposed.
    """
    ev = evidence or []
    docs = [
        rg.damage_report(case),
        rg.incident_statement(case),
        rg.evidence_index_doc(case, ev),
        rg.damage_calculation(case),
    ]
    if kind == "unauthorized-transfer" or int(case.get(":case/loss-jpy", 0) or 0) > 0 and kind in (
            "investment-scam", "fake-billing", "support-scam"):
        docs.append(rg.bank_freeze_request(case))
    if kind in ("account-takeover", "impersonation", "sns-fraud", "phishing", "leak-extortion"):
        docs.append(rg.platform_request(case, purpose="凍結・復旧"))
    if kind in ("account-takeover", "phishing", "support-scam"):
        docs.append(rg.recovery_plan(case, service=case.get(":case/service", "（対象サービス）")))
    return docs


def _window_registry() -> dict[str, dict]:
    global _REGISTRY
    if _REGISTRY is None:
        seed = load_edn(_SEED)
        _REGISTRY = {w[":registry/window"]: w for w in seed.get(":registry/windows", [])}
    return _REGISTRY


def build_packet(case: dict, evidence: list[dict] | None = None) -> dict:
    """Assemble the full packet for a case. Raises (G1/G7) if the case isn't free/consented."""
    tri = triage(case)                                   # G1/G7 gate
    kind = _kw(tri[":triage/scam-kind"])
    docs = documents_for_kind(case, kind, evidence)
    for d in docs:
        rg.assert_member_authored(d)                     # G1/G2/G3/G9 on every doc
    reg = _window_registry()
    windows = []
    for w in tri[":triage/windows"]:
        r = reg.get(w, {})
        windows.append({"code": _kw(w), "name": r.get(":registry/name", _kw(w)),
                        "contact": r.get(":registry/contact", ""), "basis": r.get(":registry/basis", "")})
    return {
        "caseId": case.get(":case/id", "case"),
        "kind": kind,
        "severity": _kw(tri[":triage/severity"]),
        "cost": tri[":triage/support-cost-jpy"],
        "documents": docs,
        "windows": windows,
        "actions": tri[":triage/actions"],
        "deadlines": tri[":triage/deadlines"],
    }


def _cover(p: dict) -> str:
    out = [f"# 助 (tasuke) 被害対応パケット — {p['caseId']}\n",
           f"**被害類型**: {rg._ja_kind(p['kind'])}　**緊急度**: {p['severity']}　"
           f"**あなたの負担: ¥{p['cost']}（全て無料）**\n",
           "> この一式は **あなた本人が作成・署名・提出** する書類です（助 は作成を手伝うだけで、"
           "提出はあなたが行います）。弁護士費用も利用料も一切かかりません。\n",
           "## まず行うこと（上から順に）\n"]
    out += [f"{i + 1}. {a}" for i, a in enumerate(p["actions"])]
    if p["deadlines"]:
        out.append("\n## ⏰ 期限の注意\n")
        out += [f"- {d}" for d in p["deadlines"]]
    out.append("\n## 無料の相談・通報窓口\n")
    out += [f"- **{w['name']}** — {w['contact']}" + (f"（{w['basis']}）" if w["basis"] else "")
            for w in p["windows"]]
    out.append("\n## 同梱書類（印刷して署名のうえ提出）\n")
    out += [f"- `{i + 1:02d}-{d[':doc/kind'].lstrip(':')}.txt` — 宛先: {d[':doc/addressed-to']}"
            for i, d in enumerate(p["documents"])]
    return "\n".join(out) + "\n"


def write_packet(p: dict, outdir: pathlib.Path | None = None) -> pathlib.Path:
    d = outdir or (_OUT / f"packet-{p['caseId']}")
    d.mkdir(parents=True, exist_ok=True)
    (d / "00-COVER.md").write_text(_cover(p), encoding="utf-8")
    for i, doc in enumerate(p["documents"]):
        (d / f"{i + 1:02d}-{doc[':doc/kind'].lstrip(':')}.txt").write_text(
            doc[":doc/body"], encoding="utf-8")
    return d


def _load_case(args) -> dict:
    if args.file:
        seed = load_edn(pathlib.Path(args.file))
        cases = seed.get(":case/batch", [seed]) if isinstance(seed, dict) else [seed]
    else:
        cases = load_edn(_SEED)[":case/batch"]
    if args.case:
        for c in cases:
            if c.get(":case/id") == args.case:
                return c
        raise SystemExit(f"case {args.case!r} not found")
    return cases[0]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="助 (tasuke) — generate a victim's free document packet")
    ap.add_argument("--case", help=":case/id to generate (from the seed)")
    ap.add_argument("--file", help="an EDN file holding the member's OWN case(s)")
    args = ap.parse_args()
    case = _load_case(args)
    packet = build_packet(case)
    out = write_packet(packet)
    print(_cover(packet))
    print(f"\n→ wrote {len(packet['documents'])} documents to {out}/ (victim cost: ¥{packet['cost']})")
