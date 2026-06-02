# etzhayyim-project-briefing — WebRTC Multi-Actor Meeting

> **T2 Logical Actor**: Manifest-driven (`20-actors/briefing/actor-manifest.jsonld`). **PII Tier 3** (recordings).

`briefing.etzhayyim.com` (nanoid: `w3olw1pf`) — WebRTC meeting with multi-actor convo project: transcriber + translator + recorder + summarizer.

## Lexicons
`briefing/` (3 files): meeting, transcript, summary, recording.

## Multi-actor composition
```
Project: "Briefing: daily-standup" (convoId)
├── did:web:briefing.etzhayyim.com:actor:transcriber  (Whisper STT)
├── did:web:briefing.etzhayyim.com:actor:translator   (LLM)
├── did:web:briefing.etzhayyim.com:actor:recorder     (R2)
└── did:web:briefing.etzhayyim.com:actor:summarizer   (LLM)
```

## cross-actor
- `livecam` — camera input
- `llm` — STT/translate/summarize
- `gmail` — invitation + summary distribution

## Governance (per ADR-0014)
- recording consent: 全参加者 explicit consent (AT records); revocation pauses recording
- retention: default 30日 B2 auto-purge
- transcript PII: LLM filter で redaction、non-participant view 用 sanitized version

## Design
- ADR-0014: PII Tier 3 + Cohort-First Pattern
