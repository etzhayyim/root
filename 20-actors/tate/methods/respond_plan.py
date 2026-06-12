#!/usr/bin/env python3
"""tate 盾 — legal-procedure response planner (個人としての対応支援; dry-run only at R0/R1).

ADR-2606112301 + worldwide ADR-2606112400. Classifies a notice the member RECEIVED
(支払督促 / 少額訴訟呼出 / 訴状 / 行政処分 / 内容証明 · US summons / small claims ·
European order for payment / Small Claims · UK claim form · DE Mahnbescheid) against
the jurisdiction-keyed procedure registry and builds a response plan: DISCLOSED
deadline rules, response options, a self-submit checklist, and referral triggers.

CONSTITUTIONAL (read before any change):
  G3 — unauthorized practice (弁護士法72条 / state UPL / Legal Services Act 2007 / RDG).
    tate maps notice → options; the MEMBER decides and submits THEMSELVES.
    Representation is structurally unrepresentable — _make_option() raises on
    :representation — in EVERY jurisdiction. Options come verbatim from the registry.
  G4 — deadline honesty. tate NEVER computes a calendar date. Every deadline is the
    DISCLOSED rule text + statutory anchor + verify-service-date=true.
  G6 — fake-notice (架空請求) guard, generalized: each procedure declares its GENUINE
    service channels (JP 特別送達 · US personal service/certified mail · DE förmliche
    Zustellung · UK court post · EU formal service). Court vocabulary on any other
    channel is :suspected-fake: the plan REFUSES any contact-sender step and routes to
    the jurisdiction's fake-help directory (tasuke 助 + #9110/188 · FTC · Action Fraud
    · Polizei Onlinewache …), evidence preserved.
  G7 — referral-forward. High-stakes shapes always carry the jurisdiction's
    professional-referral directory (法テラス · state bar / legal aid · Citizens
    Advice · Verbraucherzentrale · ECC-Net).
  G10 — jurisdiction honesty. Procedures never cross jurisdictions; a notice from a
    jurisdiction outside data/jurisdictions.edn degrades to :unknown-jurisdiction
    honestly (collect + refer) — tate never guesses foreign law.

Pure stdlib — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 respond_plan.py [docs.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from terms_scan import read_edn, load_docs, HERE  # noqa: E402

# fake-guard trip-wires (G6). Wave 17: the vocabulary is DERIVED — every procedure's
# trigger keywords are automatically trip-wires (a newly registered procedure is
# scam-guarded the moment it lands; no manual sync), plus a small curated set of
# generic scam words that are not themselves triggers.
CURATED_TRIPWIRES = ("法院", "법원", "강제집행", "lawsuit", "差押", "garnishment",
                     "Pfändung", "Insolvenz", "Betreibung", "assignation", "juzgado")


def court_vocabulary(procs: list) -> tuple:
    """Curated generics + the union of ALL procedure trigger keywords (derived, G6)."""
    return CURATED_TRIPWIRES + tuple(k for p in procs
                                     for k in p.get(":proc/trigger-keywords", []))
GENERIC_REFERRALS = ["local bar association / legal aid", "認定司法書士 (JPのみ・簡裁140万円以下)"]
PROC_REFERRAL_ALWAYS = {"proc:sojou", "proc:us-summons"}  # 本訴/civil suit — G7


def load_procs(path: pathlib.Path | None = None) -> list:
    path = path or HERE / "data" / "procedure-registry.edn"
    return [f for f in read_edn(path.read_text(encoding="utf-8")) if ":proc/id" in f]


def load_jurisdictions(path: pathlib.Path | None = None) -> dict:
    path = path or HERE / "data" / "jurisdictions.edn"
    return {j[":juris/id"]: j
            for j in read_edn(path.read_text(encoding="utf-8")) if ":juris/id" in j}


def load_us_states(path: pathlib.Path | None = None) -> dict:
    path = path or HERE / "data" / "us-states.edn"
    return {s[":state/id"]: s
            for s in read_edn(path.read_text(encoding="utf-8")) if ":state/id" in s}


def _make_option(opt: dict) -> dict:
    """The only option constructor. Representation is unrepresentable (G3) — globally."""
    if opt.get(":opt/kind") == ":representation":
        raise ValueError("G3/UPL: representation is unrepresentable in tate "
                         "(弁護士法72条 / state UPL / LSA 2007 / RDG)")
    return {"id": opt[":opt/id"], "kind": opt[":opt/kind"], "label": opt[":opt/label"],
            "mode": "dry-run", "submitted_by": "member"}


def _claim(notice: dict) -> float:
    return float(notice.get(":notice/claim-jpy")
                 or notice.get(":notice/claim-amount") or 0)


def classify(notice: dict, procs: list, jurisdictions: dict | None = None):
    """(proc, status) — :genuine | :suspected-fake | :unknown | :unknown-jurisdiction."""
    jurisdictions = jurisdictions or load_jurisdictions()
    juris = notice.get(":notice/jurisdiction", ":jp")
    text = notice.get(":notice/text", "").casefold()  # case-insensitive — SUMMONS ≡ summons
    channel = notice.get(":notice/channel")
    if juris not in jurisdictions:
        return None, ":unknown-jurisdiction"  # G10 — never guess foreign law
    matched = None
    for p in procs:
        if p.get(":proc/jurisdiction", ":jp") != juris:
            continue  # G10 — procedures never cross jurisdictions
        if any(k.casefold() in text for k in p[":proc/trigger-keywords"]):
            matched = p
            break
    if matched is None:
        # court vocabulary on a non-formal channel without a registry match is the
        # classic fake shape (JP 架空請求 / US fake-lawsuit robocall / DE Fake-Inkasso);
        # vocabulary is derived from ALL registered procedures' triggers (wave 17)
        if any(k.casefold() in text for k in court_vocabulary(procs)) \
                and channel in (":sms", ":email", ":mail"):
            return None, ":suspected-fake"
        return None, ":unknown"
    genuine = matched.get(":proc/genuine-channels", [])
    # G6 hardening (wave 5): a DIGITAL channel (SMS/email) is NEVER genuine unless the
    # procedure explicitly declares it — closes the hole where a mail-only procedure
    # (e.g. 行政処分) arriving by SMS would have classified :genuine
    if channel in (":sms", ":email") and channel not in genuine:
        return matched, ":suspected-fake"
    formal_required = any(c != ":mail" for c in genuine)
    if formal_required and channel not in genuine:
        return matched, ":suspected-fake"  # G6 — real court papers use formal service only
    return matched, ":genuine"


def build_plan(notice: dict, procs: list, jurisdictions: dict | None = None) -> dict:
    jurisdictions = jurisdictions or load_jurisdictions()
    juris_id = notice.get(":notice/jurisdiction", ":jp")
    juris = jurisdictions.get(juris_id, {})
    proc, status = classify(notice, procs, jurisdictions)
    plan = {"notice": notice[":notice/id"],
            "notice_label": notice.get(":notice/label", notice[":notice/id"]),
            "jurisdiction": juris_id,
            "channel": notice.get(":notice/channel"),
            "proc": proc[":proc/id"] if proc else None,
            "status": status,
            "deadlines": [], "options": [], "steps": [], "referrals": [],
            "mode": "dry-run"}

    if status == ":suspected-fake":
        # G6: never contact the sender; preserve evidence; route to the jurisdiction's help lines
        plan["steps"] = [
            {"verb": "do-not-contact-sender", "detail": "記載の電話番号・URL・口座に一切接触しない "
                                                        "(never call/click/pay the sender)",
             "mode": "dry-run"},
            {"verb": "preserve-evidence", "detail": "現物/スクリーンショットを保全 (日時・差出経路)",
             "mode": "dry-run"},
            {"verb": "verify-with-court", "detail": "実在確認は記載先ではなく公的窓口の公開番号で行う "
                                                    f"(genuine service: {juris.get(':juris/service-note', '—')})",
             "mode": "dry-run"},
        ]
        plan["referrals"] = list(juris.get(":juris/fake-help",
                                           ["tasuke 助 (サイバー犯罪被害支援)", "local police"]))
        return plan

    if status == ":unknown-jurisdiction":
        # G10: honest degrade — tate carries no registry for this legal system
        plan["steps"] = [
            {"verb": "declare-uncovered", "detail": f"管轄 {juris_id} は tate 未カバー "
                                                    "(coverage_report.py 参照) — 現地法を推測しない",
             "mode": "dry-run"},
            {"verb": "preserve-evidence", "detail": "文書全文・封筒・送達方法を記録", "mode": "dry-run"},
        ]
        plan["referrals"] = list(GENERIC_REFERRALS)
        return plan

    if status == ":unknown":
        plan["steps"] = [{"verb": "collect-more", "detail": "文書全文・封筒・送達方法を記録して再分類",
                          "mode": "dry-run"}]
        plan["referrals"] = list(juris.get(":juris/referrals", GENERIC_REFERRALS))
        return plan

    # :genuine — DISCLOSED rules verbatim from the registry (G4)
    for dl in proc.get(":proc/deadline-rules", []):
        plan["deadlines"].append({"label": dl[":dl/label"], "rule": dl[":dl/rule"],
                                  "anchor": dl[":dl/anchor"],
                                  "critical": bool(dl.get(":dl/critical")),
                                  "verify_service_date": bool(dl.get(":dl/verify-service-date"))})
    # wave 18: catastrophic-if-missed deadlines (徒過で権利消滅: KSchG 3週間 / CH 10日 /
    # AU 21日 / forclusion …) ALWAYS surface first — stable sort keeps registry order otherwise
    plan["deadlines"].sort(key=lambda d: not d["critical"])
    # :us sub-jurisdiction (wave 6): state law is where the real deadline lives — append
    # the DISCLOSED state rule when the state is known; never guess an unknown state (G10)
    if juris_id == ":us":
        state = load_us_states().get(notice.get(":notice/us-state"))
        if state:
            plan["deadlines"].append({
                "label": f"州規則 ({state[':state/label']})",
                "rule": state[":state/answer-rule"]
                        + f" · small claims 上限 ${state[':state/small-claims-usd']:,}",
                "anchor": state[":state/answer-anchor"],
                "critical": False, "verify_service_date": True})
        else:
            plan["deadlines"].append({
                "label": "州規則 (州不明)",
                "rule": "州が特定できないため州規則は提示しない — サモンズ記載の期限と"
                        "当該州の rules of civil procedure を必ず確認 (州差が本体)",
                "anchor": "—", "critical": False, "verify_service_date": True})
    plan["options"] = [_make_option(o) for o in proc.get(":proc/options", [])]
    plan["steps"] = [
        {"verb": "verify-service-date", "detail": "送達/受領日を自分で確認 (期限の起算点)", "mode": "dry-run"},
        {"verb": "draft-response", "detail": "選んだ選択肢の書面雛形を作成 (member が記入・確定)", "mode": "dry-run"},
        {"verb": "self-submit", "detail": "member 本人が提出 (郵送/窓口/オンライン)", "mode": "dry-run"},
        {"verb": "record-to-ledger", "detail": "対応と期限を kotoba Datom log に記録 (G8)", "mode": "dry-run"},
    ]
    plan["referrals"] = list(proc.get(":proc/refer-when", []))
    refer_over = float(juris.get(":juris/refer-over-amount", 0) or 0)
    claim = _claim(notice)
    claim_cur = notice.get(":notice/claim-currency") or \
        ("JPY" if ":notice/claim-jpy" in notice else None)
    juris_cur = juris.get(":juris/refer-over-currency")
    # currency guard (wave 7): an amount is only comparable to the refer-over line in
    # the SAME currency; a foreign-currency claim can't be sized → refer conservatively
    currency_mismatch = bool(claim > 0 and claim_cur and juris_cur and claim_cur != juris_cur)
    over_line = bool(refer_over and not currency_mismatch and claim > refer_over)
    if over_line or currency_mismatch or proc[":proc/id"] in PROC_REFERRAL_ALWAYS:
        if currency_mismatch:
            plan["referrals"] = plan["referrals"] + \
                [f"請求が外貨建て ({claim_cur}) — 金額比較不能のため保守的に専門家照会"]
        plan["referrals"] = plan["referrals"] + list(juris.get(":juris/referrals",
                                                               GENERIC_REFERRALS))  # G7
    return plan


def plans(notices: list, procs: list) -> list:
    jurisdictions = load_jurisdictions()
    return [build_plan(n, procs, jurisdictions) for n in notices]


def report(ps: list) -> str:
    L = ["# tate 盾 — response plans (dry-run; member self-submit — G3 UPL, all jurisdictions)", ""]
    for p in ps:
        L.append(f"## {p['notice_label']} [{p['jurisdiction']}] — {p['status']}"
                 f"{' (' + p['proc'] + ')' if p['proc'] else ''}")
        for d in p["deadlines"]:
            mark = "⚠ " if d.get("critical") else ""
            L.append(f"- {mark}期限ルール [{d['label']}]: {d['rule']} ({d['anchor']}) — 送達日は自分で確認")
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
    import json
    (out / "response-plans.json").write_text(
        json.dumps(ps, ensure_ascii=False, indent=1), encoding="utf-8")  # yoro UI 向け機械可読 (wave 30)
    fake = sum(1 for p in ps if p["status"] == ":suspected-fake")
    unk = sum(1 for p in ps if p["status"] == ":unknown-jurisdiction")
    print(f"tate: {len(ps)} response plans ({fake} suspected-fake guarded, "
          f"{unk} unknown-jurisdiction degraded) → {out / 'response-plans.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
