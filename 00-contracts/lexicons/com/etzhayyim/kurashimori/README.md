# com.etzhayyim.kurashimori.* — Lexicons

Lexicons for **暮らし守 (kurashimori)** — the citizen consumer-protection
concierge Tier-B actor (`did:web:kurashimori.etzhayyim.com`, ADR-2605312500).

R0 scaffold: schema skeletons only; no cell reads/writes these until Council
ratification (R1+).

| Lexicon | Purpose | Cell |
|---|---|---|
| `remedyTarget` | Coded consumer-remedy registry (remedy kind/根拠法令/日数/様式/channel/escalation; `verificationStatus` gates send, G14) | `remedy_registry` |
| `complaintSession` | Member-facing self-help session (steps + checklist) | `intake` |
| `coolingOffAssessment` | Informational cooling-off window computation (`isLegalOpinion` const false — G5) | `cooloff_check` |
| `remedyDraft` | Drafted 通知/苦情 (`assistMode` = drafting-assist only — G5) | `compose` |
| `dispatchRecord` | Dispatch record (`member-self-send` default / `agent-on-behalf` gated 代行) | `send` |
| `statusTrack` | Merchant response / refund / window clock | `status_track` |
| `escalationReferral` | Route to 消費生活センター / ADR / chigiri+counsel | `escalation` |

## Constitutional invariants encoded in these schemas

- **G5 UPL / 司法書士法 / 弁護士法**: `coolingOffAssessment.isLegalOpinion` is
  const **false** (date-computation, never a legal opinion); `remedyDraft.assistMode`
  admits only `drafting-assist` (作成代理 unrepresentable); representation routes
  to chigiri via `escalationReferral`.
- **G3 own-matter-only**: every record carries `memberDid` + a `consentRef`.
- **G6 PII confidentiality**: contract/complaint content never inline — records
  hold `encrypted*Ref` / `outcomeRef` / `receiptRef` pointers into
  `com.etzhayyim.encrypted.*` (ADR-2605181100).
- **G8 non-fabrication**: `remedyTarget.legalBasis` + `.provenance` required;
  `memberConfirmed` gates send. A wrong cooling-off `statutoryWindowDays` is harmful.
- **G10 lawful + non-harassment**: `dispatchRecord.channel` is a lawful channel
  set; drafts use non-threatening language.
- **G14 verified-remedy-only**: `remedyTarget.verificationStatus` gates `kurashimori_send`.
- **G15 member-self-action default**: `dispatchRecord.mode` defaults to
  `member-self-send`; `agent-on-behalf` requires `councilGateRef`.
- **G13 stateAlignedFlag**: pass-through field on every record.

See the ADR for the full gate set (G1–G15) and non-goals (N1–N13).
