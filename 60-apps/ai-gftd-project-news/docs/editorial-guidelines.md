# Editorial Guidelines (news.etzhayyim.com)

## Purpose
- Keep category coverage consistent across Japanese and English output.
- Reduce speculation while preserving analytical depth.
- Make source provenance and update cadence explicit.

## Core Rules
- Prefer primary sources (issuer press releases, regulator notices, financial filings, OEM announcements).
- If only secondary sources exist, label the claim as secondary and avoid escalation language.
- Avoid time-sensitive claims unless a dated source is cited in the JSON-LD metadata.
- No medical, legal, or investment advice. Summarize; do not instruct.
- Use canonical terms from the normalization dictionary for tags and categories.

## Article Types
- News: time-bound, source-linked, minimal analysis. Focus on “what changed”.
- Analysis: evergreen patterns, avoid hard dates unless essential.
- Primer: baseline context, definitions, and key players. No forecasting.

## Language & Tone
- Use neutral, factual phrasing. Avoid superlatives without data.
- In Japanese output, keep company/product names in their official form; add kana only if widely used.
- In English output, prefer industry-standard acronyms only after first expansion.

## Required Metadata Checks
- `headline` aligns with `articleSection` (news vs analysis vs primer).
- `about` contains canonical entities and taxonomy tags.
- `citation` or `source` list exists when referencing numbers, dates, or rankings.

## Category-Specific Guardrails

### C5 Medical Devices
- Use regulator categories (PMDA, FDA, MDR) when describing approvals.
- Avoid efficacy claims. State study design and phase if cited.
- Include risk language only if the source does.

### C11 Tourism / Inbound
- Prefer official stats (JNTO, MLIT, local tourism bureaus).
- Separate macro indicators from individual venue performance.
- Avoid political interpretation in travel data summaries.

### C9 Music / VTuber / Live Entertainment
- Revenue or audience numbers require a direct source.
- Distinguish platform announcements from artist/agency statements.
- Avoid implying endorsements without explicit confirmation.

### Japanese Food (M5 Quality Guardrails)
- Distinguish regional cuisine, ingredient origin, and brand claims.
- Avoid medical/health benefit statements unless sourced.
- If citing trends, include the data source and date.
- Do not generalize from a single restaurant or event.

## Review Checklist
- Canonical terms applied (see `lexicon/normalization.json`).
- Claims mapped to at least one source or marked as interpretation.
- No prohibited advice language.
- Category-specific guardrails respected.
