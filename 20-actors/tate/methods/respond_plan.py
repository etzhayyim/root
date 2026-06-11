#!/usr/bin/env python3
"""tate 盾 — legal-procedure response planner (個人としての対応支援; dry-run only at R0).

ADR-2606112300. Classifies a notice the member RECEIVED (支払督促 / 少額訴訟呼出 / 訴状 /
行政処分 / 内容証明 / 詐称SMS) against the coded procedure registry and builds a response
plan: DISCLOSED deadline rules, response options (督促異議 / 答弁書 / 通常移行申述 /
審査請求 / 書面回答), a self-submit checklist, and referral triggers.

CONSTITUTIONAL (read before any change):
  G3 — UPL (弁護士法72条). tate maps notice → options; the MEMBER decides and submits
    THEMSELVES. Representation is structurally unrepresentable — _make_option() raises
    on :representation. No individualized legal judgment; options come verbatim from
    the registry.
  G4 — deadline honesty. tate NEVER computes a calendar date. Every deadline is the
    DISCLOSED rule text + statutory anchor + verify-service-date=true (the member
    confirms when they were actually served).
  G6 — 架空請求 guard. Genuine 支払督促/訴状 arrive by 特別送達. A notice claiming a
    court procedure on a channel ≠ the registry's genuine channel is :suspected-fake:
    the plan REFUSES any contact-sender step and routes to tasuke 助 + 警察相談 #9110 +
    消費者ホットライン 188, evidence preserved.
  G7 — referral-forward. High-stakes shapes (本訴, 高額, 執行段階, 重大処分) always carry
    a professional-referral step (法テラス 0570-078374 / 弁護士会 / 認定司法書士).

Pure stdlib — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 respond_plan.py [docs.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from terms_scan import read_edn, load_docs, HERE  # noqa: E402

COURT_KEYWORDS = ("支払督促", "少額訴訟", "訴状", "口頭弁論")
REFERRALS = ["法テラス 0570-078374", "地元弁護士会の法律相談", "認定司法書士 (簡裁・140万円以下)"]
FAKE_HELP = ["tasuke 助 (サイバー犯罪被害支援)", "警察相談専用電話 #9110", "消費者ホットライン 188"]
HIGH_STAKES_JPY = 600000  # 少額訴訟 ceiling (民訴法368条) doubles as the referral line


def load_procs(path: pathlib.Path | None = None) -> list:
    path = path or HERE / "data" / "procedure-registry.edn"
    return [f for f in read_edn(path.read_text(encoding="utf-8")) if ":proc/id" in f]


def _make_option(opt: dict) -> dict:
    """The only option constructor. Representation is unrepresentable (G3/UPL)."""
    if opt.get(":opt/kind") == ":representation":
        raise ValueError("G3/UPL: representation is unrepresentable in tate (弁護士法72条)")
    return {"id": opt[":opt/id"], "kind": opt[":opt/kind"], "label": opt[":opt/label"],
            "mode": "dry-run", "submitted_by": "member"}


def classify(notice: dict, procs: list):
    """(proc, status) — :genuine | :suspected-fake | :unknown."""
    text = notice.get(":notice/text", "")
    channel = notice.get(":notice/channel")
    matched = None
    for p in procs:
        if any(k in text for k in p[":proc/trigger-keywords"]):
            matched = p
            break
    if matched is None:
        # no registry match, but court vocabulary on a non-court channel is the classic 架空請求
        if any(k in text for k in COURT_KEYWORDS) and channel != ":special-service":
            return None, ":suspected-fake"
        return None, ":unknown"
    if matched[":proc/genuine-channel"] == ":special-service" and channel != ":special-service":
        return matched, ":suspected-fake"  # G6 — real court papers come 特別送達 only
    return matched, ":genuine"


def build_plan(notice: dict, procs: list) -> dict:
    proc, status = classify(notice, procs)
    claim = float(notice.get(":notice/claim-jpy", 0) or 0)
    plan = {"notice": notice[":notice/id"],
            "notice_label": notice.get(":notice/label", notice[":notice/id"]),
            "channel": notice.get(":notice/channel"),
            "proc": proc[":proc/id"] if proc else None,
            "status": status,
            "deadlines": [], "options": [], "steps": [], "referrals": [],
            "mode": "dry-run"}

    if status == ":suspected-fake":
        # G6: never contact the sender; preserve evidence; route to help lines
        plan["steps"] = [
            {"verb": "do-not-contact-sender", "detail": "記載の電話番号・URL・口座に一切接触しない",
             "mode": "dry-run"},
            {"verb": "preserve-evidence", "detail": "現物/スクリーンショットを保全 (日時・差出経路)",
             "mode": "dry-run"},
            {"verb": "verify-with-court", "detail": "実在確認は記載先ではなく公的窓口の公開番号で行う "
                                                    "(本物の支払督促・訴状は特別送達で届く)",
             "mode": "dry-run"},
        ]
        plan["referrals"] = list(FAKE_HELP)
        return plan

    if status == ":unknown":
        plan["steps"] = [{"verb": "collect-more", "detail": "文書全文・封筒・送達方法を記録して再分類",
                          "mode": "dry-run"}]
        plan["referrals"] = list(REFERRALS)
        return plan

    # :genuine — DISCLOSED rules verbatim from the registry (G4)
    for dl in proc.get(":proc/deadline-rules", []):
        plan["deadlines"].append({"label": dl[":dl/label"], "rule": dl[":dl/rule"],
                                  "anchor": dl[":dl/anchor"],
                                  "verify_service_date": bool(dl.get(":dl/verify-service-date"))})
    plan["options"] = [_make_option(o) for o in proc.get(":proc/options", [])]
    plan["steps"] = [
        {"verb": "verify-service-date", "detail": "送達/受領日を自分で確認 (期限の起算点)", "mode": "dry-run"},
        {"verb": "draft-response", "detail": "選んだ選択肢の書面雛形を作成 (member が記入・確定)", "mode": "dry-run"},
        {"verb": "self-submit", "detail": "member 本人が提出 (郵送/窓口/オンライン)", "mode": "dry-run"},
        {"verb": "record-to-ledger", "detail": "対応と期限を kotoba Datom log に記録 (G8)", "mode": "dry-run"},
    ]
    plan["referrals"] = list(proc.get(":proc/refer-when", []))
    if claim > HIGH_STAKES_JPY or proc[":proc/id"] == "proc:sojou":
        plan["referrals"] = plan["referrals"] + REFERRALS  # G7 referral-forward
    return plan


def plans(notices: list, procs: list) -> list:
    return [build_plan(n, procs) for n in notices]


def report(ps: list) -> str:
    L = ["# tate 盾 — response plans (dry-run; member self-submit — G3 UPL)", ""]
    for p in ps:
        L.append(f"## {p['notice_label']} — {p['status']}"
                 f"{' (' + p['proc'] + ')' if p['proc'] else ''}")
        for d in p["deadlines"]:
            L.append(f"- 期限ルール [{d['label']}]: {d['rule']} ({d['anchor']}) — 送達日は自分で確認")
        for o in p["options"]:
            L.append(f"- 選択肢: {o['label']}")
        for i, s in enumerate(p["steps"], 1):
            L.append(f"{i}. [{s['verb']}] {s['detail']}")
        if p["referrals"]:
            L.append(f"- 照会先: {', '.join(p['referrals'])}")
        L.append("")
    return "\n".join(L) + "\n"


def main(argv):
    docs_path = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") else None
    out = HERE / "out"
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    _, notices = load_docs(docs_path)
    ps = plans(notices, load_procs())
    out.mkdir(parents=True, exist_ok=True)
    (out / "response-plans.md").write_text(report(ps), encoding="utf-8")
    fake = sum(1 for p in ps if p["status"] == ":suspected-fake")
    print(f"tate: {len(ps)} response plans ({fake} suspected-fake guarded) "
          f"→ {out / 'response-plans.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
