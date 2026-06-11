# com.etzhayyim.moushibumi.* — Lexicons

Lexicons for **申文 (moushibumi)** — the citizen democratic-participation
concierge Tier-B actor (`did:web:moushibumi.etzhayyim.com`, ADR-2605312400).

R0 scaffold: schema skeletons only; no cell reads/writes these until Council
ratification (R1+).

| Lexicon | Purpose | Cell |
|---|---|---|
| `participationTarget` | Coded election/petition/public-comment target registry (organ/channel/根拠法令/様式/期限/紹介議員-flag; `verificationStatus` gates submission, G14) | `target_registry` |
| `participationMatch` | Neutral proactive open-opportunity match for a consenting member | `opportunity_match` |
| `participationSession` | Member-facing 案内/伴走 session (steps + checklist) | `intake` + `compose` |
| `voiceDraft` | Drafted 請願書 / 意見 (drafting-assist, NOT 作成代理 — G5) | `compose` |
| `submissionRecord` | Submission record (`member-self-submit` default / `agent-on-behalf` gated 代行) | `submit` |
| `statusTrack` | 採択/不採択 + agency §43 考え方 公示 outcome | `status_track` |

## Constitutional invariants encoded in these schemas

- **G3 election-neutrality**: `channelKind=election-info` is INFO-ONLY (no
  submission); `participationMatch.rationale` is neutral, no partisan framing;
  no candidate/party/vote field anywhere.
- **G4 own-voice-only**: every record carries `memberDid` + a `consentRef`.
- **G5 UPL**: `voiceDraft.assistMode` admits only `drafting-assist` (作成代理
  unrepresentable); legal characterization → chigiri.
- **G6 PII + political-opinion confidentiality**: content never inline — records
  hold `encrypted*Ref` / `outcomeRef` pointers into `com.etzhayyim.encrypted.*`
  (ADR-2605181100); political belief is APPI §2 special-care.
- **G8 non-fabrication**: `participationTarget.legalBasis` + `.provenance`
  required; `voiceDraft.memberConfirmed` gates submission.
- **G14 verified-target-only**: `participationTarget.verificationStatus` gates
  `moushibumi_submit`.
- **G15 member-self-submission default**: `submissionRecord.mode` defaults to
  `member-self-submit`; `agent-on-behalf` requires `councilGateRef`.
- **G13 stateAlignedFlag**: pass-through field on every record.

See the ADR for the full gate set (G1–G15) and non-goals (N1–N13).
