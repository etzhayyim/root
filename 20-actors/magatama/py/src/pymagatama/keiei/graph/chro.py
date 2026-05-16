"""CHRO role graph — Phase 2 of the keiei layer.

Vacant seat. Primary mode, but **payroll gated**.
ADR 2605101200 §3 row=chro, §4 hard rule "no autonomous hire/fire/comp".

Class C = autonomous (internal comms, scheduling, FAQ, onboarding doc,
        all-hands recap, internal Teams channel post).
Class B = primary-mode autonomous-with-24h-auto-disclose for non-payroll
        HR decisions (policy memo, training plan, performance template).
        Any action_kind in {hire, fire, comp-change, payroll-run} is
        force-gated by `roles.gate()` to human confirm regardless of mode.
Class A = always escalate to CEO 河崎 + COO a.nakamura (blocking).

Lens:
  - 労基法 / 労働契約法 / 社保 / 労保 compliance
  - amanomibashira member roster (CEO 河崎 + 7 employees + vendors)
  - Vendor / contractor boundary — Gftd Japan = vendor, NOT employer
  - Onboarding / off-boarding playbook (a.oda 契約終了 2026-04-20 reference)
  - Internal comms tone: respectful, bilingual JP-EN, no hype
"""

from __future__ import annotations

from ._pipeline import DecideRequest, register


def _hook(req: DecideRequest) -> tuple[str, list[str]]:
    system = (
        "You are AI-CHRO at amanomibashira. Vacant human seat — primary mode, "
        "but payroll gated. Operating entity = amanomibashira; vendor = "
        "Gftd Japan株式会社 (corporate number 9007-2846). "
        "HARD RULE: you MUST NOT initiate hiring offers, terminations, "
        "compensation changes, payroll runs, or sign employment documents. "
        "You may only: draft policy, schedule meetings, post internal comms, "
        "prepare offer/termination memos for human approval via consent-helper. "
        "Vendor/employer boundary: amanomibashira is the operating entity; "
        "Gftd Japan provides vendor capacity — do not conflate the two in "
        "HR memos. Members are amanomibashira-direct (河崎 CEO et al.). "
        "Compliance: 労基法, 労働契約法, 社保, 労保, 個情法. "
        "Reference: a.oda 契約終了 2026-04-20 off-boarding playbook. "
        "Class A = always escalate to CEO 河崎 + COO a.nakamura with blocking "
        "wait. Class B (non-payroll) = autonomous + 24h auto-disclose. "
        "Class B touching payroll/hire/fire/comp = denied at gate, draft + "
        "human confirm only. "
        "Tone: respectful, bilingual JP-EN where appropriate, empathetic, "
        "compliant. No hype. Be concise (<=8 lines). Surface the failure "
        "mode (labor risk, retention risk, compliance gap). Recommend."
    )

    ctx: list[str] = []
    s = req.summary.lower()
    a = (req.action_kind or "").lower()

    # Hard-gate triggers.
    if a in {"hire", "fire", "comp-change", "payroll-run"}:
        ctx.append(
            f"lens.gate=hr-action ({a}) — payroll-gated, will require human "
            "confirm via consent-helper. Do not attempt direct execution."
        )

    # Hiring / firing cues.
    if any(k in s for k in ("hire", "hiring", "offer", "採用", "内定", "雇用")):
        ctx.append("lens.hire=draft offer memo; 労働契約法 §15 明示事項 checklist; CEO ratify")
    if any(k in s for k in ("fire", "termination", "解雇", "退職", "離職", "契約終了")):
        ctx.append("lens.off-board=labor risk; 労基法 §20 30-day notice; a.oda 2026-04-20 playbook")
    if any(k in s for k in ("salary", "comp", "bonus", "raise", "給与", "賞与", "報酬")):
        ctx.append("lens.comp=payroll-gated; coordinate with AI-CFO on funding; CEO ratify")
    if any(k in s for k in ("payroll", "給与計算", "支給")):
        ctx.append("lens.payroll-run=ledger-grade audit trail required; consent-helper + bank reconcile")

    # Compliance cues.
    if any(k in s for k in ("社保", "労保", "社会保険", "労働保険", "厚生年金", "雇用保険")):
        ctx.append("lens.insurance=社保事務手続 — defer execution to a.nakamura (COO)")
    if any(k in s for k in ("労基", "labor", "ot", "残業", "36協定", "時間外")):
        ctx.append("lens.labor=36協定 / 時間外規制 / 健康診断 cadence; surface non-compliance early")
    if any(k in s for k in ("個情法", "pii", "personal data", "個人情報")):
        ctx.append("lens.pii=ADR-0018 PII Tier 3; never include 給与/連絡先/居所 in public artefact")

    # Internal comms cues.
    if any(k in s for k in ("schedule", "meeting", "1:1", "all-hands", "internal", "announce", "通知")):
        ctx.append("lens.comms=Class C autonomous; bilingual where mixed JP-EN audience")
    if any(k in s for k in ("onboard", "オンボーディング", "オリエンテーション")):
        ctx.append("lens.onboard=playbook = welcome packet + Teams channel invite + Keychain seed; coordinate with AI-CTO on tooling access")
    if any(k in s for k in ("training", "research", "study", "研修", "教育")):
        ctx.append("lens.training=Class C autonomous; reuse module catalog; budget impact → AI-CFO confirm")

    # Performance / review cues.
    if any(k in s for k in ("performance", "review", "1on1", "評価", "目標", "okr")):
        ctx.append("lens.perf=draft template Class B; CEO 河崎 ratifies final review outcome")

    return system, ctx


register("chro", _hook)
