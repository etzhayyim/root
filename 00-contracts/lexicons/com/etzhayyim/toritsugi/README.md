# com.etzhayyim.toritsugi.* — Lexicons

Lexicons for **取次 (toritsugi)** — the citizen-facing government-procedure
concierge Tier-B actor (`did:web:toritsugi.etzhayyim.com`, ADR-2605312030).

R0 scaffold: schema skeletons only; no cell reads/writes these until Council
ratification (R1+).

| Lexicon | Purpose | Cell |
|---|---|---|
| `procedure` | Coded government/municipal procedure registry entry (窓口/所管/様式/必要書類/手数料/法定処理期間/根拠法令/channel; `verificationStatus` gates submission, G14) | `procedure_registry` |
| `benefitMatch` | Proactive eligibility match for a consenting member (OWN data) — the LINE-like notify | `eligibility_match` |
| `procedureGuide` | Member-facing 案内/伴走 session (steps + 必要書類 checklist) | `intake` + `guide` |
| `applicationDraft` | Assisted form draft artifact (member-owned; input-assist, NOT 作成代理 — G5) | `draft` |
| `submissionRecord` | Submission record (`member-self-submit` default / `agent-on-behalf` gated 代行) | `submit` |
| `statusTrack` | 処理状況 + 法定処理期間 clock + result + appeal pointer | `status_track` |

## Constitutional invariants encoded in these schemas

- **G3 own-procedure-only**: every record carries `memberDid` + a `consentRef`.
- **G5 行政書士法/UPL**: `applicationDraft.assistMode` admits only `input-assist`
  (作成代理 is unrepresentable); legal/tax characterization routes to chigiri /
  toritate.
- **G6 PII confidentiality**: PII never inline — records hold
  `encrypted*Ref` / `resultRef` pointers into `com.etzhayyim.encrypted.*`
  (ADR-2605181100).
- **G8 non-fabrication**: `procedure.legalBasis` + `procedure.provenance` are
  required; `applicationDraft.memberConfirmed` gates submission.
- **G14 verified-procedure-only**: `procedure.verificationStatus` gates
  `toritsugi_submit`.
- **G15 member-self-submission default**: `submissionRecord.mode` defaults to
  `member-self-submit`; `agent-on-behalf` requires `councilGateRef`.
- **G13 stateAlignedFlag**: pass-through field on every record.

See the ADR for the full gate set (G1–G15) and non-goals (N1–N14).
