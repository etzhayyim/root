"""CLO role graph — Phase 3 of the keiei layer (shadow mode).

Human seat: k.bakshi@gftd.co.jp (Kunal Bakshi). Shadow mode.
ADR 2605101200 §3 row=clo.

Class C = autonomous (compliance digest, ToS draft, redlines on internal docs).
Class B = blocking human confirm (k.bakshi ratifies + a.nakamura/CEO sign).
Class A = always escalate to CEO 河崎 with blocking wait.

Lens:
  - Compliance: APPI / GDPR / 景表法 / 特電法 / CAN-SPAM / PECR / 個情法
  - Contract review: NDA / MSA / SOW / LoI / DPA / DocuSign envelope status
  - IP: copyright, patent, trade secret, open-source license obligations
  - atproto OAuth wire-format = snake_case (ADR-2604231821)
  - BCI counsel + Mode B Rule 36 (ruling deadline 2026-05-23)
  - Cold outreach: never auto-send with [PARTNER_NAME] placeholder unfilled
  - malak.surveillance Phase 1 G2 gate = external counsel contract signed
  - Vendor↔principal boundary (Gftd Japan vendor, amanomibashira principal)
"""

from __future__ import annotations

from ._pipeline import DecideRequest, register


def _hook(req: DecideRequest) -> tuple[str, list[str]]:
    system = (
        "You are AI-CLO at amanomibashira, in shadow mode. Human seat: "
        "Kunal Bakshi (k.bakshi@gftd.co.jp). You are Kunal's chief-of-"
        "staff, not external counsel of record. "
        "Operating entity = amanomibashira (sole principal). Gftd Japan "
        "(corp 9007-2846) = vendor only. SOW/MSA signatory must reflect "
        "this — never sign 河崎 as Gftd Japan officer on amanomibashira "
        "business and vice versa. "
        "Active threads: BCI counsel Mode B Rule 36 ruling deadline "
        "2026-05-23; Nishith / lawfirm.gftd.ai cold outreach (PARTNER_NAME "
        "placeholder rule); malak.surveillance Phase 1 G2 = external "
        "counsel contract signed before live RW write; consent-helper "
        "review for financial-action drafts from AI-CFO; consent for "
        "hire/fire/comp from AI-CHRO. "
        "Compliance frame: APPI (個情法) / GDPR / 景表法 / 特電法 / "
        "CAN-SPAM 16 CFR 316.5 / PECR Reg 23 / 5 CFR 2635 / UK Bribery "
        "Act / EU Staff Reg 11a / NPA R6 公開草案 / PPC 生体識別子ガイド"
        "ライン草案. Surface the specific clause when relevant. "
        "atproto OAuth wire-format MUST be snake_case (ADR-2604231821) — "
        "any drift = compliance violation. "
        "Class A = escalate to 河崎. Class B = blocking confirm from "
        "k.bakshi (and CEO/COO countersign as needed). Class C = "
        "autonomous (compliance digest, internal redlines, ToS draft). "
        "Be concise (<=8 lines). Cite statute / ADR / contract clause. "
        "Risk-averse but specific — flag the precise failure mode."
    )

    ctx: list[str] = []
    s = req.summary.lower()

    # Contract types.
    if any(k in s for k in ("nda", "mutual nda", "non-disclosure")):
        ctx.append("lens.nda=mutual preferred; 5y term cap; carve-outs for residuals; choice-of-law check")
    if any(k in s for k in ("msa", "master services", "sow", "statement of work")):
        ctx.append("lens.msa-sow=signatory = amanomibashira (not Gftd Japan); IP assignment clause; termination rights")
    if any(k in s for k in ("loi", "letter of intent", "term sheet")):
        ctx.append("lens.loi=non-binding sections explicit; exclusivity window bounded; 河崎 ratifies")
    if any(k in s for k in ("dpa", "data processing agreement", "data processor")):
        ctx.append("lens.dpa=GDPR Art 28 mandatory clauses; SCC for cross-border; sub-processor list")
    if any(k in s for k in ("docusign", "envelope", "countersign")):
        ctx.append("lens.docusign=verify signatory authority before send; archive executed PDF to vault")

    # Compliance.
    if any(k in s for k in ("appi", "個情法", "個人情報", "pii", "personal data")):
        ctx.append("lens.appi-pii=ADR-0018 PII Tier 3; cohort-first; never raw on public AT records")
    if any(k in s for k in ("gdpr", "eu data", "europe", "data subject")):
        ctx.append("lens.gdpr=Art 6 lawful basis; Art 14 disclosure on EU outreach; SCC for transfer")
    if any(k in s for k in ("景表法", "no.1", "best-in-class", "guarantee", "substantiation")):
        ctx.append("lens.keihyo=景表法 substantiation; AI-CMO must redact unverifiable claim")
    if any(k in s for k in ("can-spam", "特電法", "opt-out", "unsubscribe")):
        ctx.append("lens.email-law=postal address footer + unsubscribe link mandatory")

    # Outreach discipline (with AI-COO).
    if any(k in s for k in ("cold outreach", "outreach to partner", "[partner_name]",
                            "placeholder", "personalize", "nishith")):
        ctx.append("lens.outreach-discipline=never auto-send with [PARTNER_NAME] unfilled; 外弁 confirm before Nishith #1")

    # BCI / Rule 36.
    if any(k in s for k in ("bci", "rule 36", "mode b")):
        ctx.append("lens.bci=Mode B Rule 36 ruling deadline 2026-05-23; k.bakshi owner; surface delay risk")

    # IP / open-source.
    if any(k in s for k in ("license", "open source", "oss", "lgpl", "agpl", "mit",
                            "apache", "spdx", "copyleft")):
        ctx.append("lens.oss=verify SPDX + obligation chain; LGPL-3.0 = SpiffWorkflow constraint (ADR-2605081200)")
    if any(k in s for k in ("patent", "trade secret", "trademark", "tm",
                            "copyright", "©")):
        ctx.append("lens.ip=ownership chain; assignment language; vendor↔principal clarity")

    # OAuth / wire-format.
    if any(k in s for k in ("oauth", "atproto oauth", "dpop", "snake_case", "camelcase")):
        ctx.append("lens.oauth-wire=atproto OAuth = snake_case wire (ADR-2604231821); never camelCase")

    # malak.surveillance G2 gate.
    if any(k in s for k in ("malak", "surveillance", "lea", "interpol",
                            "警察", "biometric", "face template")):
        ctx.append("lens.malak-G2=Phase 1 G2 = external counsel contract signed; face template = 国内拘束 (ADR-0018)")

    # Regulatory inquiry / subpoena.
    if any(k in s for k in ("subpoena", "warrant", "law enforcement", "regulator",
                            "ppc", "regulatory inquiry")):
        ctx.append("lens.lea-inquiry=preserve evidence; k.bakshi lead; CEO 河崎 informed; no unilateral response")

    # Employment-law adjacent (with AI-CHRO).
    if any(k in s for k in ("employment", "労基", "労働契約法", "termination",
                            "wrongful", "discrimination")):
        ctx.append("lens.employment=co-review with AI-CHRO; 労基法 §15/§20; document audit trail")

    return system, ctx


register("clo", _hook)
