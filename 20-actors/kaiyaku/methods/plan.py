#!/usr/bin/env python3
"""kaiyaku 解約 — severance-plan builder (dry-run only at R0).

ADR-2606112200. Turns a :sever / :review decision on a tie into a concrete severance
plan routed through the safest adapter tier (the karakuri ServiceOp tiering,
ADR-2606039200):

  T1 official-API cancel      — service publishes a cancellation API
  T2 ToS-permitted browser    — browser-use headless plan over the MEMBER's OWN
                                session; refused by construction when the service
                                browser stance is :prohibited or :unknown (G3)
  T3 self-submit procedure    — generated checklist / 解約通知文 the member submits
                                THEMSELVES (the toritsugi/kurashimori default-self-submit
                                pattern); always available

CONSTITUTIONAL (read before any change):
  G3 — ToS-honest, NO detection-evasion: evasion verbs (captcha-solve, proxy-rotate,
    stealth, rate-limit-bypass, fingerprint-spoof) are structurally unrepresentable —
    _make_step() raises on them. A :prohibited/:unknown browser stance falls to T3,
    never "tries anyway".
  G5/G6 — severance is DESTRUCTIVE: every plan requires member-sig + explicit dry-run
    confirm; execute() raises at R0 (live execution = Council Lv6+ + operator gate).
  G8 — cost-of-severance honesty: notice period / 違約金 are carried into the plan and
    shown to the member; kaiyaku never plans around a contractual obligation.

Pure stdlib — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 plan.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze  # noqa: E402

EVASION_VERBS = {"captcha-solve", "proxy-rotate", "stealth", "rate-limit-bypass",
                 "fingerprint-spoof", "ip-rotate", "anti-bot-bypass"}

PLANNABLE = {":sever", ":review-cascade"}


def _make_step(verb: str, detail: str) -> dict:
    """The only step constructor. Evasion verbs are unrepresentable (G3)."""
    if verb in EVASION_VERBS:
        raise ValueError(f"G3: detection-evasion verb '{verb}' is unrepresentable in kaiyaku")
    return {"verb": verb, "detail": detail, "mode": "dry-run"}


def select_tier(svc: dict) -> str:
    """Safest-first adapter routing (karakuri ADR-2606039200 pattern)."""
    cancel = svc.get(":svc/cancel", {}) or {}
    if cancel.get(":api") == ":available":
        return "T1"
    if cancel.get(":browser") == ":permitted":
        return "T2"
    return "T3"  # :prohibited / :unknown browser stance refuses T2 by construction


def build_plan(svc: dict, tie: dict) -> dict:
    """One severance plan for one tie. Dry-run only; never executes."""
    rec = tie["recommendation"]
    if rec not in PLANNABLE:
        raise ValueError(f"not plannable: recommendation {rec} (only {sorted(PLANNABLE)})")
    tier = select_tier(svc)
    steps = []
    if tie["dependents"]:
        for d in tie["dependents"]:
            steps.append(_make_step("rehome-dependency",
                                    f"move {d} off {tie['svc']} (SSO/payment) BEFORE severing"))
    if tier == "T1":
        steps.append(_make_step("api-cancel", f"call the published cancellation API of {tie['svc']}"))
    elif tier == "T2":
        steps.append(_make_step("browser-cancel",
                                f"browser-use plan over the member's OWN session on {tie['svc']} "
                                f"(ToS-permitted surface only)"))
    else:
        steps.append(_make_step("self-submit",
                                f"generate 解約/退会 procedure + notice text for {tie['svc']}; "
                                f"the MEMBER submits it themselves"))
    steps.append(_make_step("export-own-data", f"T3 portability export of the member's own data "
                                               f"from {tie['svc']} before closure"))
    steps.append(_make_step("confirm-closure", "verify the service confirms 解約/退会 (email/record)"))
    return {
        "svc": tie["svc"],
        "svc_label": tie["svc_label"],
        "tier": tier,
        "recommendation": rec,
        "steps": steps,
        # G8 cost-of-severance honesty — carried, never planned around
        "notice_days": svc.get(":svc/notice-days", 0),
        "penalty_jpy": svc.get(":svc/penalty-jpy", 0),
        # G5 destructive gates — required before ANY live execution
        "requires": {"member_sig": True, "dry_run_confirm": True,
                     "council_lv6_operator_gate": True},
        "mode": "dry-run",
    }


def plans(nodes: dict, edges: list) -> list:
    res = analyze(nodes, edges)
    out = []
    for tie in res["ties"]:
        if tie["recommendation"] in PLANNABLE:
            out.append(build_plan(nodes[tie["svc"]], tie))
    return out


def execute(plan: dict):  # noqa: ARG001 — signature is the contract
    """R0: live execution is Council Lv6+ + operator + member-sig gated (G5/G6)."""
    raise RuntimeError("kaiyaku R0: live severance execution is gated (G5/G6) — dry-run only")


def report(ps: list) -> str:
    L = ["# kaiyaku severance plans (dry-run — G5/G6 gated)", ""]
    for p in ps:
        sev = (f" · notice {p['notice_days']}d · penalty ¥{p['penalty_jpy']:,}"
               if (p["notice_days"] or p["penalty_jpy"]) else "")
        L.append(f"## {p['svc_label']} — {p['tier']} ({p['recommendation']}){sev}")
        for i, s in enumerate(p["steps"], 1):
            L.append(f"{i}. [{s['verb']}] {s['detail']}")
        L.append("")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-en-ledger.kotoba.edn"
    out = here / "out"
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    nodes, edges = load(seed)
    ps = plans(nodes, edges)
    out.mkdir(parents=True, exist_ok=True)
    (out / "severance-plans.md").write_text(report(ps), encoding="utf-8")
    print(f"kaiyaku: {len(ps)} severance plans (dry-run) → {out / 'severance-plans.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
