"""briefing_templates_en — English section renderers (mirrors briefing_templates.py).

Used when state["language"] starts with "en". Same DEFAULT_SECTIONS order +
same SECTION_TITLE keys; only the rendered prose changes.

Cross-jurisdiction targets: INTERPOL IPSG Lyon, Europol The Hague,
FBI Cyber Division, NCA NCCU, AFP, BKA, RCMP NC3, etc.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, List


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


SECTION_TITLE_EN: Dict[str, str] = {
    "cover":               "Cover",
    "executive_summary":   "1. Executive Summary",
    "use_case":            "2. Use Cases",
    "architecture":        "3. Architecture (Edge-only / pod-only RW separation)",
    "data_residency":      "4. Data Residency (Face Templates in JP On-Prem GPU)",
    "warrant_gate":        "5. Warrant Gate (queryPerson requires warrant/enquiry)",
    "human_review":        "6. Human Review (human_review_gate is mandatory)",
    "audit_retention":     "7. Audit Log Retention (7-year statutory)",
    "international_scope": "8. International LEA Scope (INTERPOL 196 members)",
    "phase_status":        "9. Phase Status + Milestones",
    "operating_entity":    "10. Operating Entity (amanomibashira / contractor Gftd Japan)",
    "compliance_frameworks": "11. Compliance (APPI / Police Act / NPA Notice R6)",
    "design_adrs":         "12. Design ADR Digest",
    "next_steps":          "13. Next Steps",
    "faq":                 "14. FAQ",
    "appendix_references": "Appendix: References",
}


def render_cover(facts: Dict[str, Any], briefing_no: str) -> str:
    return (
        f"# {facts.get('title', '(no title)')}\n"
        f"## {briefing_no}\n\n"
        f"| Field | Value |\n"
        f"|---|---|\n"
        f"| Operating entity | {facts.get('operatingEntity', 'amanomibashira')} |\n"
        f"| Vendor (contractor) | {facts.get('vendor', 'Gftd Japan株式会社')} |\n"
        f"| Target agency | {facts.get('targetAgencyName', facts.get('targetAgencyPath', '(unset)'))} |\n"
        f"| TLP | {facts.get('tlp', 'AMBER')} |\n"
        f"| Language | {facts.get('language', 'en')} |\n"
        f"| Issued | {_now_iso()[:10]} |\n"
        f"| Version | v{facts.get('version', 1)} |\n"
    )


def render_executive_summary(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["executive_summary"]
    summary = facts.get("executiveSummary", "")
    return (
        f"## {title}\n\n"
        f"{summary}\n\n"
        f"This briefing summarises the malak.surveillance capability cluster — open-vocabulary "
        f"camera scene search + warrant-gated person re-identification + B2G agency-outreach — "
        f"for {facts.get('targetAgencyName', 'the addressee agency')}. The operating entity is "
        f"**{facts.get('operatingEntity', 'amanomibashira')}** (Japan), with technical implementation "
        f"contracted to **{facts.get('vendor', 'Gftd Japan')}**. All design judgements visible here "
        f"are anchored to ADRs (Architecture Decision Records) and stored graph-natively in RisingWave.\n"
    )


def render_use_case(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["use_case"]
    pitch = facts.get("useCasePitch", "interpolCooperation")
    pitch_map = {
        "fraud":               "Fraud-network mule re-identification (organised crime, transnational scams)",
        "missingPerson":       "Missing-person investigation support (with family consent + LE request)",
        "streetCrime":         "Open-vocabulary scene search for street crime (clothing/object/action attributes)",
        "cyberOps":            "Physical movement tracing for cybercriminal actors (e.g. ransomware-affiliate travel)",
        "interpolCooperation": "Cross-border tracking support tied to INTERPOL Red/Blue/Green/Purple notices",
    }
    return (
        f"## {title}\n\n"
        f"Primary use case: **{pitch_map.get(pitch, pitch)}**\n\n"
        f"Secondary: scene-description search (no person identification) is non-warrant; it is used to "
        f"narrow time/place windows. Person re-identification is on a strictly separated path with "
        f"warrant/enquiry-letter input as a hard precondition at both the edge and orchestration layers.\n"
    )


def render_architecture(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["architecture"]
    return (
        f"## {title}\n\n"
        f"Per ADR-2605111200 (CF Worker = Edge Layer; RisingWave connections only from K8s pods):\n\n"
        f"```\n"
        f"[police LAN] --mTLS--> [CF Worker malak.gftd.ai (edge)] --XRPC--> [bpmn-dispatcher (k8s, JP)]\n"
        f"                                                                       |\n"
        f"                               +-------------------------------------+---+\n"
        f"                               |                                         |\n"
        f"                               v                                         v\n"
        f"                       [LangGraph Server (Granian L3)]             [pyzeebe worker]\n"
        f"                               |                                         |\n"
        f"                               v  inference                              v  INSERT/SELECT\n"
        f"                       [murakumo on-prem (JP DC, NVIDIA)]          [RisingWave Vultr LAX]\n"
        f"```\n\n"
        f"- Face templates / video frames / OCR run only on the on-prem JP GPU pod\n"
        f"- Text LLM (scene-query parser + outreach draft) runs on RunPod US-KS-2 (text-only, no PII)\n"
        f"- CF Worker is stateless and has no Hyperdrive binding (Edge-only invariant, ADR-2605111200)\n"
    )


def render_data_residency(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["data_residency"]
    return (
        f"## {title}\n\n"
        f"{facts.get('dataResidency', 'Face templates are AES-256-GCM-encrypted at rest inside the JP on-prem GPU pod.')}\n\n"
        f"| Data class | Storage | Encryption |\n"
        f"|---|---|---|\n"
        f"| Raw clip (mp4) | R2 bucket (police-only, 90-day retention) | Transport TLS only |\n"
        f"| Face template | murakumo on-prem (JP) | AES-256-GCM + wrapped key + kid |\n"
        f"| Scene CLIP embedding | murakumo on-prem (JP) | plaintext (low identifiability) |\n"
        f"| Person ReID embedding | murakumo on-prem (JP) | plaintext (low identifiability) |\n"
        f"| Audit log | RW + S3 archive | append-only, 7-year retention |\n\n"
        f"Cross-border restriction: the master key is constrained to Japan; no service outside JP — "
        f"including overseas inference providers — can decrypt a face template. Reference: "
        f"_working/malak/surveillance/MURAKUMO-DOMESTIC-CONSTRAINT.md.\n"
    )


def render_warrant_gate(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["warrant_gate"]
    return (
        f"## {title}\n\n"
        f"`ai.gftd.apps.malak.queryPerson` (known-person re-identification) is hard-gated at THREE layers:\n\n"
        f"```\nrequest body MUST include legalBasis.warrantRef OR legalBasis.enquiryRef\n```\n\n"
        f"If both are empty the edge-layer `src/app.ts:preflightGate` returns **HTTP 403** before the "
        f"request reaches the orchestrator. The pyzeebe handler then re-validates (defense-in-depth), "
        f"and the LangGraph chain finally rejects again at its first conditional edge. By contrast, "
        f"`queryScene` (scene-description only, no person identification) requires no warrant and runs "
        f"under the standard administrative-investigation framework.\n"
    )


def render_human_review(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["human_review"]
    return (
        f"## {title}\n\n"
        f"Top-1 auto-adoption is **architecturally impossible**. The `human_review_gate` node sits as a "
        f"Conditional edge in the LangGraph chain; without a recorded `reviewSurveillanceMatches` entry, "
        f"the chain cannot advance to `exportSurveillanceEvidence`. Any judgement that could lead to "
        f"investment, arrest, or other coercive action requires investigator review on record.\n"
    )


def render_audit_retention(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["audit_retention"]
    return (
        f"## {title}\n\n"
        f"Every operation (warrant reference, operator DID, mTLS fingerprint, IP, latency) is recorded "
        f"append-only. Statutory retention: **7 years**, stored in `vertex_malak_surveillance_audit_event`, "
        f"with SHA-256 chain verification to prevent tampering.\n"
    )


def render_international_scope(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["international_scope"]
    return (
        f"## {title}\n\n"
        f"Seeded coverage: all **196 INTERPOL member countries** (National Central Bureaus) plus "
        f"primary federal LEAs of major partners. The seed lives in "
        f"`60-apps/ai-gftd-project-states/data/gov/{{cc}}/lea.ndjson`:\n\n"
        f"- Tier 1 (52 entries): INTERPOL HQ (IPSG Lyon) + Europol + UNODC + FATF + G7 + Five Eyes\n"
        f"- Tier 2 (51 entries): G20 + key Asia (KOR/SGP/HKG/IND/BRA, etc.)\n"
        f"- Tier 3 (169 entries): remaining INTERPOL members (stubs, enriched during Phase 1)\n\n"
        f"**Cooperation-status tagging**: countries under EU/US/UK sanctions or whose LEA cooperation is "
        f"restricted by international agreements (e.g. AFG/MMR/IRN/SYR/RUS/BLR/LBY/YEM/SDN/SSD/IRQ) are "
        f"hard-excluded from the outreach pipeline. See ADR-2605091400 §LEA scope.\n"
    )


def render_phase_status(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["phase_status"]
    phase_status = facts.get("phaseStatus", "Phase 0 (started 2026-05-13, legal triage in progress)")
    return (
        f"## {title}\n\n"
        f"Current: **{phase_status}**\n\n"
        f"| Phase | Target | Status |\n"
        f"|---|---|---|\n"
        f"| Phase 0 — legal/design | Go/No-Go 2026-08-01 | in progress (CLO triage due 2026-06-01) |\n"
        f"| Phase 1 — NPA briefings + INTERPOL contact | 2026-08 onwards | pending |\n"
        f"| Phase 2 — prefectural-police pilots (3) | 2026-09 to 2027-03 | pending |\n"
        f"| Phase 3 — JC3 joint procurement | 2027-Q1 | pending |\n"
        f"| Phase 4 — 47-prefecture + international rollout | 2027-Q2 onwards | pending |\n\n"
        f"Detail: `_working/malak/surveillance/PHASE-1-LAUNCH-READINESS.md`.\n"
    )


def render_operating_entity(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["operating_entity"]
    return (
        f"## {title}\n\n"
        f"| Role | Entity |\n"
        f"|---|---|\n"
        f"| Operating entity | **{facts.get('operatingEntity', 'amanomibashira')}** |\n"
        f"| Vendor (contractor) | **{facts.get('vendor', 'Gftd Japan株式会社')}** |\n"
        f"| Personal-data controller (APPI) | amanomibashira |\n"
        f"| Face-template custodian | amanomibashira CLO |\n"
        f"| Incident contact | privacy@gftd.ai (24h) |\n"
        f"| Counterparty in any police agreement | amanomibashira (Gftd Japan disclosed as sub-contractor) |\n"
    )


def render_compliance_frameworks(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["compliance_frameworks"]
    frameworks: List[str] = facts.get("complianceFrameworks") or [
        "APPI — Act on the Protection of Personal Information (revised 2019/2021)",
        "Police Act (Keisatsu-hou) — operational basis for JP prefectural police",
        "NPA Notice R6 (public-comment draft) — procurement standards for police-facing AI",
        "Telecommunications Business Act §4 — secrecy-of-communication (audio is dropped at ingest)",
        "Code of Criminal Procedure §321 — chain-of-custody evidentiary framework",
        "Anti-Spam Act (Tokutei Denshi Mail Ho) §3 — opt-in regime for outreach",
        "National Public Service Ethics Code — gift/benefit prohibition guardrails",
        "PPC Biometric Guidelines (draft) — face template = sensitive personal data class",
        "INTERPOL Constitution Art. 32 — NCB cooperation",
        "EU AI Act (where applicable, EU partners)",
        "FATF Recommendations — AML follow-on (financial-crime joint operations)",
    ]
    body = "\n".join(f"- {f}" for f in frameworks)
    return (
        f"## {title}\n\n"
        f"The design is built to comply with the following frameworks:\n\n"
        f"{body}\n\n"
        f"A monthly external-counsel retainer is scoped for Phase 1 to perform a 30-day audit + design "
        f"impact assessment immediately after the NPA R6 Notice is finalised.\n"
    )


def render_design_adrs(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["design_adrs"]
    adrs: List[str] = facts.get("designAdrs") or [
        "ADR-2605091400 — MCP as cell membrane (XRPC = internal cytoplasmic wire)",
        "ADR-2605111200 — CF Worker = Edge-Only; RisingWave only from k8s pods",
        "ADR-2605010000 — RunPod 6000 Ada (LLM inference SSoT, text-only)",
        "ADR-0048 — RisingWave Vultr + B2 primary",
        "ADR-0036 — 3-Tier Write (Social / Domain / State)",
        "ADR-0095 — Simplified 3-layer identity + RW canonical columns",
        "ADR-2605080600 — LangGraph Server + Granian L3 Runtime",
        "ADR-2605082000 — LangGraph Graph-Definition-as-Data",
        "ADR-2605082200 — PyZeebe Handler Thin Dispatcher Contract",
    ]
    body = "\n".join(f"- {a}" for a in adrs)
    return (
        f"## {title}\n\n"
        f"Principal design judgements referenced by this brief:\n\n"
        f"{body}\n"
    )


def render_next_steps(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["next_steps"]
    return (
        f"## {title}\n\n"
        f"1. If of interest, we would value a 45-minute technical briefing (in person at IPSG Lyon or "
        f"   via secure video) at your convenience.\n"
        f"2. A 10-page supplementary brief on the post-NPA-R6 audit protocol is in preparation.\n"
        f"3. We anticipate proposing a joint-pilot framework with three Japanese prefectural police "
        f"   forces (Kanagawa / Osaka / Fukuoka) in Phase 2.\n\n"
        f"Contact: malak-surveillance@gftd.ai (amanomibashira side).\n"
    )


def render_faq(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["faq"]
    return (
        f"## {title}\n\n"
        f"### Q1. Where are face templates stored?\n"
        f"On-prem GPU pod inside Japan only. AES-256-GCM at rest; master key is geofenced to JP; "
        f"egress to Cloudflare or any non-Japanese inference provider is blocked at the protocol level.\n\n"
        f"### Q2. Can person identification be run without a warrant?\n"
        f"No. `queryPerson` is hard-gated at three layers (edge / pyzeebe / LangGraph). Without "
        f"`legalBasis.warrantRef` or `legalBasis.enquiryRef`, the edge worker returns HTTP 403 "
        f"and the request never reaches the orchestrator.\n\n"
        f"### Q3. Is auto-adoption of the top-1 match possible?\n"
        f"No. A `reviewSurveillanceMatches` record from a human investigator is required as a "
        f"LangGraph Conditional-edge precondition for `exportSurveillanceEvidence`.\n\n"
        f"### Q4. Is audio captured?\n"
        f"No. Audio streams are physically dropped at the ffmpeg ingest layer (secrecy-of-communication compliance).\n\n"
        f"### Q5. Which countries are covered in the international scope?\n"
        f"All 196 INTERPOL member NCBs are seeded. Countries under sanctions or with restricted "
        f"cooperation are tagged and hard-excluded from outreach.\n\n"
        f"### Q6. What happens when NPA Notice R6 is finalised?\n"
        f"Within 30 days of publication, the external counsel monthly retainer triggers an audit + "
        f"design-impact assessment. If conflict is found, live deploys are paused until redesign.\n\n"
        f"### Q7. What is the relationship between amanomibashira and Gftd Japan?\n"
        f"amanomibashira is the operating entity (legal counterparty); Gftd Japan is the engineering "
        f"contractor (disclosed as sub-contractor in any police agreement).\n\n"
        f"### Q8. Retention periods?\n"
        f"Raw clips: 90 days after case closure / face templates: 1 year after case resolution then "
        f"physically deleted (no soft-delete) / audit logs: 7 years (statutory).\n"
    )


def render_appendix_references(facts: Dict[str, Any], briefing_no: str) -> str:
    title = SECTION_TITLE_EN["appendix_references"]
    return (
        f"## {title}\n\n"
        f"- `_working/malak/surveillance/DESIGN.md` — full system design\n"
        f"- `_working/malak/surveillance/COMPLIANCE-MEMO.md` — legal guard + CLO triage register\n"
        f"- `_working/malak/surveillance/MURAKUMO-DOMESTIC-CONSTRAINT.md` — domestic-residency design\n"
        f"- `_working/malak/surveillance/LEAD-PIPELINE-SEED.md` — outreach pipeline plan\n"
        f"- `_working/malak/surveillance/PHASE-1-LAUNCH-READINESS.md` — Phase-1 launch checklist\n"
        f"- `30-graph/graph-schema/migrations/20260513140000_vertex_malak_surveillance_lea_org.ts` — RW LEA schema\n"
        f"- `30-graph/graph-schema/migrations/20260513150000_vertex_malak_briefing.ts` — briefing graph schema\n"
        f"- `60-apps/ai-gftd-project-malak/CLAUDE.md` — capability clusters\n"
    )


DOC_RENDERERS = {
    "cover":               render_cover,
    "executive_summary":   render_executive_summary,
    "use_case":            render_use_case,
    "architecture":        render_architecture,
    "data_residency":      render_data_residency,
    "warrant_gate":        render_warrant_gate,
    "human_review":        render_human_review,
    "audit_retention":     render_audit_retention,
    "international_scope": render_international_scope,
    "phase_status":        render_phase_status,
    "operating_entity":    render_operating_entity,
    "compliance_frameworks": render_compliance_frameworks,
    "design_adrs":         render_design_adrs,
    "next_steps":          render_next_steps,
    "faq":                 render_faq,
    "appendix_references": render_appendix_references,
}
