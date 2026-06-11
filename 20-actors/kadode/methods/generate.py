#!/usr/bin/env python3
"""kadode 門出 — resignation-document generator + 使者 relay builder (UPL-guarded).

ADR-2606112238. Renders the worker's OWN resignation documents (退職届 / 退職願 / 即時退職通知 /
内容証明 / 有給取得届) deterministically and content-addresses them (kotoba IPFS CIDv1 + SHA-256),
and — for non-negotiating scenarios only — builds a 使者 RELAY record that conveys the worker's
already-formed unilateral resignation to the employer.

// no-server-key: read-only — kadode holds no key and SENDS nothing here. It drafts the worker's
// document and builds an UNSENT relay record; actually transmitting it (email/内容証明/郵送) is a
// G7-gated outward action requiring the worker's consent + operator/Council step.

CONSTITUTIONAL (the defining boundary):
  G1 — 使者 not 代理人. The generated 退職届 states only "一身上の都合により" (personal reasons) —
    it NEVER contains a demand, a negotiation, a severance figure, or a settlement (those are
    法律事務 reserved to lawyers, 弁護士法72条). `build_relay()` REFUSES any scenario that needs
    negotiation and returns the escalation route (union/lawyer) instead. `assert_no_negotiation()`
    rejects negotiation/demand text injected into a free-text field.
  G2 — worker-authored. The document is the worker's own act; missing fields render as explicit
    blanks (［　　］), never invented.
  N3 — non-adjudicating. The document cites its statutory basis (民法627 / 628) as a disclosed
    fact; it never asserts the resignation's enforceability or promises an outcome.

Pure stdlib. Usage:
    python3 generate.py --kind taishoku-todoke --worker 山田太郎 --employer 株式会社ABC \\
        --date 2026-07-15 [--out OUTDIR]
"""
from __future__ import annotations
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, recommend_route, NEGOTIATING_ACTORS  # noqa: E402
from cid import cidv1_raw, sha256_hex  # noqa: E402

# negotiation / demand language that must NEVER enter a kadode-drafted resignation (G1).
# Their presence means the matter is 法律事務 → route to a lawyer / union, not a 使者 relay.
PROHIBITED_NEGOTIATION = [
    "示談", "和解金", "解決金", "慰謝料", "損害賠償を請求", "賠償を求め", "減額交渉",
    "退職金を増", "条件交渉", "交渉して", "請求します", "支払えと", "値引き",
]


def assert_no_negotiation(text: str) -> None:
    """Reject any negotiation/demand language in a worker-supplied free-text field (G1)."""
    hits = [p for p in PROHIBITED_NEGOTIATION if p in (text or "")]
    if hits:
        raise ValueError(
            f"G1 (弁護士法72条): negotiation/demand language is out of scope for a kadode "
            f"document — {hits}. This matter needs a labour union (団体交渉) or a lawyer; "
            f"kadode relays only a unilateral resignation.")


def _f(fields: dict, key: str) -> str:
    v = fields.get(key)
    return str(v) if v not in (None, "") else "［　　］"


def render(kind: str, fields: dict) -> str:
    """Render a resignation document. `kind` ∈ taishoku-todoke|taishoku-gan|sokuji|naiyo-shomei|yukyu."""
    # any free-text the worker supplies is UPL-scanned before it can reach a document
    assert_no_negotiation(fields.get("note", ""))
    worker, employer = _f(fields, "worker"), _f(fields, "employer")
    dept, position = _f(fields, "department"), _f(fields, "position")
    rdate, sdate = _f(fields, "date"), _f(fields, "submit_date")
    rep = _f(fields, "representative")

    head = {
        "taishoku-todoke": "退職届",
        "taishoku-gan": "退職願",
        "sokuji": "退職届（即時退職）",
        "naiyo-shomei": "退職通知書（内容証明）",
        "yukyu": "年次有給休暇取得届",
    }.get(kind)
    if head is None:
        raise ValueError(f"unknown document kind: {kind}")

    L = [head, ""]
    if kind == "taishoku-todoke":
        L += ["私事、",
              f"このたび一身上の都合により、来る {rdate} をもって退職いたします。", "",
              "（本書面は民法627条1項に基づく、期間の定めのない労働契約の一方的な解約の意思表示です。"
              "使用者の承諾を要しません。）"]
    elif kind == "taishoku-gan":
        L += ["私事、",
              f"このたび一身上の都合により、{rdate} をもって退職いたしたく、お願い申し上げます。"]
    elif kind == "sokuji":
        L += ["私事、",
              f"このたびやむを得ない事由により、{rdate}（本書面到達日）をもって退職いたします。", "",
              "（本書面は民法628条に基づく、やむを得ない事由による労働契約の即時解除の意思表示です。）"]
    elif kind == "naiyo-shomei":
        L += [f"私 {worker} は、貴社との労働契約を、本書面の到達をもって、",
              f"民法627条1項に基づき {rdate} をもって終了する意思を通知いたします。", "",
              "（本書面は退職の意思表示の到達を証明する目的で内容証明郵便により送付するものです。）"]
    elif kind == "yukyu":
        L += [f"労働基準法39条に基づき、退職日（{rdate}）までの間、",
              "保有する年次有給休暇を取得することを届け出ます。"]

    L += ["", f"　　{sdate}", f"　　{dept}　{position}", f"　　{worker}　　㊞", "",
          f"{employer}", f"代表取締役 {rep}　殿", ""]
    return "\n".join(L) + "\n"


def build_relay(scenario_id: str, document: str, worker_did: str, employer_ref: str,
                nodes: dict, edges: list, created_at: str = "1970-01-01T00:00:00Z") -> dict:
    """Build a 使者 (messenger) RELAY record — ONLY for non-negotiating scenarios (G1).

    If the scenario's lawful route is a negotiating one (union/lawyer), kadode REFUSES to relay
    and returns the escalation instead — a 使者 may convey an already-formed declaration, never
    conduct a negotiation (弁護士法72条). The record is UNSENT; transmission is G7-gated."""
    rec = recommend_route(scenario_id, nodes, edges)
    actor = rec.get("route_actor")
    if rec.get("needs_negotiation") or actor in NEGOTIATING_ACTORS:
        return {"$type": "com.etzhayyim.kadode.escalation",
                "scenario": scenario_id, "relayed": False,
                "reason": "この事案は交渉を要するため、kadode は使者として伝達できません "
                          "(G1 / 弁護士法72条)。労働組合または弁護士へ。",
                "escalateTo": rec.get("route"), "escalateActor": actor}
    body = document.encode("utf-8")
    return {"$type": "com.etzhayyim.kadode.resignationRelay",
            "scenario": scenario_id, "relayed": False, "status": "drafted-unsent",
            "role": "messenger-使者", "negotiates": False,
            "workerDid": worker_did, "employerRef": employer_ref,
            "documentCid": cidv1_raw(body), "documentSha256": sha256_hex(body),
            "statutoryBasis": "民法627条1項（一方的解約・承諾不要）",
            "createdAt": created_at,
            "note": "本記録は未送付。実際の伝達（メール/内容証明/郵送）はワーカー同意＋G7承認が必要。"}


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    kind = argv[argv.index("--kind") + 1] if "--kind" in argv else "taishoku-todoke"
    fields = {
        "worker": argv[argv.index("--worker") + 1] if "--worker" in argv else None,
        "employer": argv[argv.index("--employer") + 1] if "--employer" in argv else None,
        "date": argv[argv.index("--date") + 1] if "--date" in argv else None,
        "department": argv[argv.index("--dept") + 1] if "--dept" in argv else None,
    }
    outdir = pathlib.Path(argv[argv.index("--out") + 1]) if "--out" in argv else here / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    doc = render(kind, fields)
    (outdir / f"{kind}.md").write_text(doc, encoding="utf-8")
    print(f"kadode generate: {kind} → {len(doc.encode())} B")
    print(f"  documentCid:    {cidv1_raw(doc.encode())}")
    print(f"  → {outdir/(kind+'.md')} (worker drafts + self-submits; relay is G7-gated)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
