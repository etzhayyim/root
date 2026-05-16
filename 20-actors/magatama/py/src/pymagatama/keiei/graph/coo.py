"""COO role graph — Phase 3 of the keiei layer (shadow mode).

Human seat: a.nakamura@gftd.co.jp. Shadow mode.
ADR 2605101200 §3 row=coo.

Class C = autonomous (status digest, vendor follow-up draft, queue triage).
Class B = blocking human confirm (a.nakamura ratifies).
Class A = always escalate to CEO 河崎 with blocking wait.

Lens:
  - Vendor provisioning (DocuSign, Stripe, Omise, 1Password vault seats)
  - Track A/B/C ownership map from gftdcojp-revenue pipeline
  - Capacity / bandwidth across y-nishino, k-bakshi, a-nakamura
  - Process discipline: avoid auto-sending cold outreach with placeholders
  - Pre-cutover gating (RisingWave health gate, ADR-2604261900)
  - Vendor↔principal boundary (Gftd Japan vendor, amanomibashira principal)
"""

from __future__ import annotations

from ._pipeline import DecideRequest, register


def _hook(req: DecideRequest) -> tuple[str, list[str]]:
    system = (
        "You are AI-COO at amanomibashira, in shadow mode. Human seat: "
        "a.nakamura@gftd.co.jp. You are 中村's chief-of-staff, not a "
        "stand-in. "
        "Operating entity = amanomibashira; Gftd Japan is vendor — surface "
        "this when ops decisions cross the boundary (SOW signatory, "
        "Stripe merchant of record, employment contract). "
        "Ops focus: execution feasibility, sequencing, bandwidth, vendor "
        "provisioning, queue discipline. Active gftdcojp-revenue ownership: "
        "Track A (k-bakshi BCI outreach, owner a-nakamura), Track B "
        "(RW migration, owner y-nishino), Track C (ConfigMap mount, owner "
        "y-nishino). Don't take ownership away from named owners without "
        "explicit hand-off. "
        "Vendor accounts: DocuSign / Stripe / Omise / 1Password / Bitwarden "
        "/ Microsoft 365 / Vultr / B2 / RunPod. Provisioning gated by "
        "vendor-provisioning-checklist.md. "
        "Process discipline (institutional): no auto-send of cold outreach "
        "with `[PARTNER_NAME]` or similar placeholders unfilled; no "
        "impersonation of external humans via tenant-wide Mail.Send; no RW "
        "DDL/migration without `rw-health-gate.sh` PASS. "
        "Class A = escalate to 河崎. Class B = blocking confirm from "
        "a.nakamura. Class C = autonomous (queue triage, status digest, "
        "internal-only follow-up draft). "
        "Be concise (<=8 lines). Pragmatic, not aspirational. Surface "
        "sequencing risk and missed dependency. Recommend, don't hedge."
    )

    ctx: list[str] = []
    s = req.summary.lower()

    # Track A/B/C status.
    if any(k in s for k in ("track a", "track-a", "k-bakshi outreach", "bci outreach")):
        ctx.append("lens.track-A=owner a.nakamura; outreach to k.bakshi via 1Password share")
    if any(k in s for k in ("track b", "track-b", "rw migration", "risingwave migration", "hyperdrive cutover")):
        ctx.append("lens.track-B=owner y.nishino; requires network-reachable RW; rw-health-gate.sh PASS first")
    if any(k in s for k in ("track c", "track-c", "configmap", "configmap mount", "k8s mount")):
        ctx.append("lens.track-C=owner y.nishino; kubectl access required (claude host has none)")

    # Vendor provisioning.
    if any(k in s for k in ("docusign", "stripe", "omise", "1password", "bitwarden",
                            "vendor account", "merchant of record")):
        ctx.append("lens.vendor=consult vendor-provisioning-checklist.md; a.nakamura is provisioning lead")
    if any(k in s for k in ("vultr", "b2", "runpod", "linode", "cloudflare account")):
        ctx.append("lens.cloud-account=billing → AI-CFO; key custody → Keychain + 1Password mirror")

    # Capacity / bandwidth.
    if any(k in s for k in ("capacity", "bandwidth", "owner", "assign", "delegate",
                            "load", "headcount", "stretched")):
        ctx.append("lens.bandwidth=verify named owner has capacity; do not silently reassign")

    # RisingWave / infra gating.
    if any(k in s for k in ("risingwave", "ddl", "alter", "scale-down",
                            "helm upgrade", "compute floor")):
        ctx.append("lens.rw-gate=rw-health-gate.sh + scaling-contract.yaml + ADR-2604261900 + ADR-0094")

    # Outreach discipline.
    if any(k in s for k in ("cold outreach", "outreach", "[partner_name]",
                            "placeholder", "personalize")):
        ctx.append("lens.outreach-discipline=no auto-send with placeholder unfilled; CEO ratification before live send")

    # SOW / contract signing.
    if any(k in s for k in ("sow", "loi", "msa", "nda", "sign", "countersign",
                            "executed contract")):
        ctx.append("lens.contract-sign=AI-CFO + AI-CLO co-draft; 河崎 signs; never AI-COO direct execute")

    # Status digest / weekly ops.
    if any(k in s for k in ("status", "weekly", "monthly", "digest",
                            "stand-up", "standup", "scrum")):
        ctx.append("lens.digest=Class C autonomous; cite DECISION-LOG iter; bullet-point format")

    return system, ctx


register("coo", _hook)
