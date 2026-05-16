"""CFO role graph — Phase 2 of the keiei layer.

Vacant seat. Primary mode, but **financial-action gated**.
ADR 2605101200 §3 row=cfo, §4 hard rule "no autonomous spend ever".

Class C = autonomous (read-only analysis: burn-rate calc, variance, draft).
Class B = primary-mode autonomous-with-24h-auto-disclose for *non-monetary*
        decisions (e.g. classification, accounting policy memo). Any
        action_kind in {spend, charge, wire, payroll, sign-legal} is force-
        gated to human confirm by `roles.gate()` regardless of mode.
Class A = always escalate to CEO 河崎 + COO a.nakamura (blocking).

Lens:
  - burn-rate vs $123/mo Vultr cluster savings target (ADR-0048)
  - RunPod 6000 Ada unified pod LLM spend (ADR-2605010000)
  - Stripe / Omise charge approval workflow → consent helper, never direct
  - Wire / payroll → Smart Wallet ERC725 root or bank; draft-only
  - 法人税 / 消費税 / 源泉 reporting cadence
  - audit-trail integrity: every Class B decision MUST land in CXO-LEDGER
"""

from __future__ import annotations

from ._pipeline import DecideRequest, register


def _hook(req: DecideRequest) -> tuple[str, list[str]]:
    system = (
        "You are AI-CFO at amanomibashira. Vacant human seat — primary mode, "
        "but financial-action gated. Operating entity = amanomibashira; "
        "vendor = Gftd Japan株式会社. "
        "HARD RULE: you MUST NOT initiate payments, wires, Stripe charges, "
        "Omise charges, payroll runs, or sign legal/financial documents. "
        "You may only: analyse cost data, draft budget memos, compute "
        "burn-rate / runway / unit economics, flag variance vs plan, prepare "
        "consent-helper requests for human approval. "
        "Reference points: Vultr VKE LAX $241/mo (ADR-0048, $123/mo savings "
        "vs Linode); RunPod 6000 Ada LLM pod (ADR-2605010000); Murakumo "
        "fleet legacy LAN spend; B2 storage 7.63 TiB. "
        "Class A = always escalate to CEO 河崎 + COO a.nakamura with blocking "
        "wait. Class B (non-monetary) = autonomous + 24h auto-disclose. "
        "Class B touching money = denied at gate, draft + human confirm only. "
        "Be concise (<=8 lines). Surface the failure mode (variance, fraud "
        "vector, runway risk). Cite ADR / SSoT file. Recommend, don't hedge."
    )

    ctx: list[str] = []
    s = req.summary.lower()
    a = (req.action_kind or "").lower()

    # Hard-gate triggers — make it obvious why the gate will refuse if
    # action_kind is set to one of these.
    if a in {"spend", "charge", "wire", "payroll", "sign-legal"}:
        ctx.append(
            f"lens.gate=financial-action ({a}) — draft-only, will require "
            "human confirm via consent-helper. Do not attempt direct execution."
        )

    # Cost / cloud spend lens.
    if any(k in s for k in ("vultr", "linode", "runpod", "cloud", "cluster", "node")):
        ctx.append("lens.cloud-burn=compare against ADR-0048 baseline ($241/mo Vultr LAX, $123/mo savings target)")
    if any(k in s for k in ("llm", "inference", "gpu", "6000 ada", "a40", "h100")):
        ctx.append("lens.inference-cost=ADR-2605010000 unified pod cost model; per-1M-token rate")
    if any(k in s for k in ("b2", "backblaze", "storage", "iceberg")):
        ctx.append("lens.storage-cost=B2 sole provider since 2026-04-22; watch per-account rps quota (incident 2026-04-25)")

    # Revenue / receivable lens.
    if any(k in s for k in ("stripe", "omise", "charge", "invoice", "ar", "receivable", "subscription")):
        ctx.append("lens.revenue=consent-helper required for charge; no direct gateway call from AI-CFO")
    if any(k in s for k in ("docusign", "sow", "loi", "msa", "nda", "contract")):
        ctx.append("lens.contract=sign-legal gated; draft + a-nakamura/k-bakshi countersign + CEO ratify")

    # Tax / compliance lens.
    if any(k in s for k in ("法人税", "消費税", "源泉", "tax", "withholding", "消費")):
        ctx.append("lens.tax=cadence-driven; defer execution to a.nakamura (COO finance ops)")
    if any(k in s for k in ("payroll", "給与", "社保", "労保")):
        ctx.append("lens.payroll=payroll-gated; coordinate with AI-CHRO; CEO ratifies before run")

    # Audit / ledger lens — every CFO Class B output MUST be cited.
    if any(k in s for k in ("ledger", "audit", "報告", "disclose", "monthly", "quarterly")):
        ctx.append("lens.audit=cite CXO-LEDGER seq; 24h auto-disclose mailer covers Class B")

    # Budget / planning lens.
    if any(k in s for k in ("budget", "burn", "runway", "forecast", "variance", "予算", "燃焼")):
        ctx.append("lens.planning=runway = cash / monthly_burn; flag <12 month runway to CEO immediately")

    return system, ctx


register("cfo", _hook)
