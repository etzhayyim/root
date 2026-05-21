# ai-gftd-project-briefing — WebRTC Multi-Actor Meeting

> **T2 Logical Actor**: Manifest-driven (`20-actors/briefing/actor-manifest.jsonld`). **PII Tier 3** (recordings).

`briefing.gftd.ai` (nanoid: `w3olw1pf`) — WebRTC meeting with multi-actor convo project: transcriber + translator + recorder + summarizer.

## Lexicons
`briefing/` (3 files): meeting, transcript, summary, recording.

## Multi-actor composition
```
Project: "Briefing: daily-standup" (convoId)
├── did:web:briefing.gftd.ai:actor:transcriber  (Whisper STT)
├── did:web:briefing.gftd.ai:actor:translator   (LLM)
├── did:web:briefing.gftd.ai:actor:recorder     (R2)
└── did:web:briefing.gftd.ai:actor:summarizer   (LLM)
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
