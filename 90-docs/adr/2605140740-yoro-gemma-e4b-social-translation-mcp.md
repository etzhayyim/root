---
id: adr-2605140740-yoro-gemma-e4b-social-translation-mcp
title: YORO Gemma E4B social post translation and MCP facade
status: active
doc_type: adr
topic: yoro-i18n
authoritative: true
last_verified: 2026-05-14
authoritative_for:
  - yoro.etzhayyim.com social post translation worker topology
  - yoro social translation MCP tool exposure
  - scheduled target language set for yoro post backfill
related:
  - adr-0077-translation-link-topology
  - adr-0042
  - adr-2605102100-keiei-llm-vultr-cpu-inference
supersedes: []
superseded_by: []
---

# Context

YORO social posts need sibling `app.bsky.feed.post` translations linked by
`com.etzhayyim.apps.media_gamers.record.translationLink` records, per
ADR-0077. The earlier translation-link topology defined the record shape and
read path, but did not pin the live yoro worker, MCP exposure, Gemma model
route, or scheduled language sweep.

The May 2026 operational requirement expanded from the initial
Japanese / Chinese / Korean / Spanish sweep to Indian languages and
Arabic-region minority languages. The live worker must remain bounded because
Gemma E4B can spend multiple minutes on some Indic scripts before producing
the final translated text.

# Decision

Use the `yoro-actors` namespace worker set as the canonical runtime for yoro
social translation:

- `Deployment/yoro-actor-langserver-worker` registers
  `yoro.social.translatePost` and `yoro.social.translatePostBatch`.
- `CronJob/yoro-social-translation` performs a bounded every-four-hour sweep
  (`47 */4 * * *`) with `MAX_TRANSLATIONS=2`.
- The model route is the cluster-local Keiei LLM E4B backend:
  `http://keiei-llm-e4b.keiei-llm.svc.cluster.local:8080/v1/chat/completions`
  with `etzhayyim_LLM_MODEL=gemma-4-E4B-it`.
- The active image verified on 2026-05-14 is
  `ghcr.io/etzhayyim/kotodama:yoro-translation-i18n5-653ce4e7159-20260514072956-amd64`.
- Translation calls use an explicit language label in the prompt, deterministic
  temperature, `max_tokens=1200`, and `YORO_TRANSLATION_LLM_TIMEOUT_SEC=300`.

The scheduled target language set is:

```text
ja,zh-Hans,ko,es,hi,bn,ta,te,mr,ur,gu,kn,ml,pa,ar,fa,he,ku,ckb,zgh,kab,ps,sd,am,ti
```

The LangServer/manual backfill target list may include additional broad
languages:

```text
en,fr,de,pt,id,vi,th,it,nl,tr,pl,uk
```

# MCP Surface

`yoro-mcp-adapter` exposes the translation route as MCP tools:

- `yoro.social.translatePost`
- `yoro.social.translatePostBatch`

The cluster-local endpoint is:

```text
http://yoro-mcp-adapter.yoro-actors.svc.cluster.local:8080/mcp
```

`tools/list` returns both translation tools. External unauthenticated requests
to `https://yoro.etzhayyim.com/mcp` and `https://atproto.etzhayyim.com/mcp` are expected
to be denied at the edge (`403`) unless the caller satisfies the public MCP
auth policy.

MCP remains a facade. It does not directly write PDS records. Tool responses
route callers to BPMN / LangServer execution:

- `com.etzhayyim.yoro.translatePost -> yoro.social.translatePost`
- `com.etzhayyim.yoro.translatePostBatch -> yoro.social.translatePostBatch`

The translation worker writes translated sibling posts and
`translationLink` records through the governed actor path.

# Consequences

Positive:

- yoro post translation has a single live worker topology instead of ad hoc
  scripts.
- MCP discovery exposes the translation capability without granting direct
  MCP write authority.
- The language set now covers Japanese, Chinese, Korean, Spanish, major Indian
  languages, Arabic-region languages, and selected minority languages.
- The bounded sweep avoids E4B timeout cascades while still backfilling
  continuously.

Risks and constraints:

- Gemma E4B latency is language-dependent; Tamil and Marathi smoke validation
  required the 1200-token / 300-second ceiling.
- Some transliterations remain model-quality issues, not transport failures.
- Increasing `MAX_TRANSLATIONS` should be treated as an operational change and
  validated against E4B latency first.

# Verification

Verified on 2026-05-14:

- `Deployment/yoro-actor-langserver-worker`: `1/1` ready.
- `CronJob/yoro-social-translation`: schedule `47 */4 * * *`.
- MCP `tools/list` returned `yoro.social.translatePost` and
  `yoro.social.translatePostBatch`.
- Smoke job `yoro-social-translation-i18n5-smoke-20260514073354` completed
  with `attempted=2`, `translated=2`, `failed=0`.
- Successful smoke translations included Tamil (`ta`) and Marathi (`mr`).
- Unit tests for yoro social translation passed: `37 passed`.
