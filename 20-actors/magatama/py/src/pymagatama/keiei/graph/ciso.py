"""CISO role graph — Phase 3 of the keiei layer (shadow mode).

Human seat: n.takahashi@gftd.works. Shadow mode.
ADR 2605101200 §3 row=ciso.

Class C = autonomous (threat-ledger triage, scam-intake pipeline, evidence
        capture orchestration, internal incident digest).
Class B = blocking human confirm (n.takahashi ratifies; CEO 河崎 informed
        on incident-disclosure-bound items).
Class A = always escalate to CEO 河崎 + n.takahashi with blocking wait.

Lens:
  - malak.surveillance hard invariants (8): face template 国内拘束 /
    warrant gate / two-stage approval / opt-in source / business-hour /
    audio drop / 7-year audit / no-soft-delete
  - threat-ledger pattern (`_working/malak/THREAT-LEDGER.md`)
  - scam-intake LangGraph chain (email/sms/line/intel 4-source → PEGEL)
  - leedsil / bitnest / 中銘貿易 / chuumei investigation TTP map
  - Vault zero-knowledge invariant (no plaintext / vaultKey on server)
  - ADR-0018 PII Tier 3 + cohort-first
  - Keychain primary + 1Password mirror credential storage
  - Evidence chain-of-custody for police submission
"""

from __future__ import annotations

from ._pipeline import DecideRequest, register


def _hook(req: DecideRequest) -> tuple[str, list[str]]:
    system = (
        "You are AI-CISO at amanomibashira, in shadow mode. Human seat: "
        "n.takahashi@gftd.works. You are 髙橋's chief-of-staff. "
        "Operating entity = amanomibashira; vendor = Gftd Japan. "
        "Security frame: zero-trust, least-privilege, defense-in-depth. "
        "Reference invariants: Vault zero-knowledge (vault.gftd.ai stores "
        "ciphertext + wrapped keys + metadata only — never plaintext / "
        "raw vaultKey / memberDeviceKey on server); macOS Keychain primary "
        "+ 1Password mirror for local secrets; gftd Vault + 1Password + "
        "Bitwarden for shared credentials; ADR-0018 PII Tier 3 + cohort-"
        "first. "
        "malak.surveillance hard rules (8 invariants): face template = "
        "国内拘束 / warrant gate on queryPerson / two-stage approval on "
        "exportSurveillanceEvidence (supervisor + sectionChief) / opt-in "
        "source whitelist (4 種) / business-hour (09:00-17:00 JST 平日) / "
        "audio drop / 7-year audit retention / no soft-delete (`_alive` "
        "禁止). Phase 1 launch = 2026-08-01, gates G1/G2/G3 ALL GREEN. "
        "Threat-ledger pattern: every confirmed actor/incident appended "
        "to `_working/malak/THREAT-LEDGER.md` + `_working/malak/INTEGRATED-"
        "EVIDENCE-REPORT.md`. Append-only. Never edit prior rows. "
        "Active investigations to preserve continuity on: 高橋宏之 案件 "
        "(村上世彰なりすまし投資詐欺、¥79M loss, 12 mule accounts, leedsil/"
        "bitnest/Leeds Securities, 中銘貿易株式会社 法人番号 6180001145250, "
        "神奈川県警磯子署松村刑事 R5.11.27 受理). "
        "Class A = blocking escalate to 河崎 + 髙橋 — major incident, "
        "data breach, regulatory inquiry, LEA contact. Class B = blocking "
        "confirm from 髙橋 (incident disclosure, public statement, third-"
        "party data share). Class C = autonomous (digest, triage, "
        "evidence capture, scam-intake pipeline tick). "
        "Be concise (<=8 lines). Surface the specific attacker vector / "
        "control failure / blast radius. Paranoid but specific. Cite "
        "ledger seq / ADR / file path. Recommend, don't hedge."
    )

    ctx: list[str] = []
    s = req.summary.lower()

    # malak.surveillance / mehikari invariants.
    if any(k in s for k in ("malak", "surveillance", "mehikari", "queryperson",
                            "scenesearch", "personsearch", "exportsurveillance")):
        ctx.append("lens.malak-rules=8 hard invariants (face=国内拘束 / warrant / two-stage / opt-in / business-hour / audio-drop / 7y audit / no soft-delete)")
    if any(k in s for k in ("face template", "biometric", "顔特徴量")):
        ctx.append("lens.face-template=国内拘束 (ADR-2605131500); never leave JP infra; AES-256-GCM at rest")
    if any(k in s for k in ("warrant", "令状")):
        ctx.append("lens.warrant=queryPerson hard-gated; warrantId or enquiryId required at edge+pyzeebe+LangGraph")

    # Threat ledger / scam intake / pursuit.
    if any(k in s for k in ("scam-intake", "scam_intake", "trap message",
                            "trap_message", "yoro feed", "android adb")):
        ctx.append("lens.scam-intake=LangGraph chain (email/sms/line/intel 4-source) → PEGEL tick → vertex_malak_trap_message")
    if any(k in s for k in ("threat ledger", "threat-ledger", "evidence-report",
                            "evidence report")):
        ctx.append("lens.threat-ledger=_working/malak/THREAT-LEDGER.md append-only; cite seq in artefact")
    if any(k in s for k in ("leedsil", "bitnest", "leeds securities", "村上世彰",
                            "中銘貿易", "iktagroup", "ikta")):
        ctx.append("lens.investigation=高橋宏之 案件 chain-of-custody; cite INTEGRATED-EVIDENCE-REPORT.md; 神奈川県警磯子署松村刑事 escalation path")

    # Vault zero-knowledge.
    if any(k in s for k in ("vault.gftd", "vaultkey", "ephemeral key",
                            "wrapped", "ciphertext", "redact")):
        ctx.append("lens.vault-zk=no plaintext/vaultKey on server; redactVaultResponse enforced; MCP returns metadata only")

    # Credential / secret handling.
    if any(k in s for k in ("keychain", "1password", "bitwarden", "secret",
                            "credential", "api key", "token rotation",
                            "agent-token")):
        ctx.append("lens.credentials=Keychain primary + 1Password mirror; .env fallback only ($HOME/.gftd/*.env, chmod 600); never hardcode")

    # PII / privacy.
    if any(k in s for k in ("pii", "個人情報", "personal data", "tier 3", "cohort")):
        ctx.append("lens.pii=ADR-0018 Tier 3; cohort-first; never raw on Bluesky public records")

    # Incident / outage / breach.
    if any(k in s for k in ("breach", "incident", "p1", "sev1", "outage",
                            "compromise", "exfil", "ransomware", "ddos")):
        ctx.append("lens.incident=Class B disclosure path; preserve evidence; CEO 河崎 + 髙橋 + AI-CLO immediate informed")

    # Auth / OAuth / DPoP.
    if any(k in s for k in ("oauth", "dpop", "service auth", "session",
                            "jwt", "atproto auth")):
        ctx.append("lens.auth=atproto OAuth snake_case wire (ADR-2604231821); DPoP key handling; revoke + introspect path live")
    if any(k in s for k in ("did:plc", "did:web", "did rotate", "key rotation")):
        ctx.append("lens.did-rotate=self-hosted did:plc (ADR-0014); rotate via PDS handler; never expose privKey")

    # Network / infra security.
    if any(k in s for k in ("firewall", "ingress", "egress", "wireguard",
                            "tailscale", "vpn", "tunnel")):
        ctx.append("lens.network=zero-trust; CF Tunnel preferred over open ingress; lateral movement check")
    if any(k in s for k in ("k8s", "kubernetes", "kubectl", "rbac", "service account")):
        ctx.append("lens.k8s=RBAC least-privilege; surface SA token expiry; defer kubectl exec to y-nishino")

    # LEA / law enforcement interaction (co-with AI-CLO).
    if any(k in s for k in ("警察", "policing", "law enforcement", "subpoena",
                            "搜查", "捜査", "対策本部")):
        ctx.append("lens.lea=co-route with AI-CLO; preserve chain-of-custody; CEO informed; never unilateral disclosure")

    return system, ctx


register("ciso", _hook)
