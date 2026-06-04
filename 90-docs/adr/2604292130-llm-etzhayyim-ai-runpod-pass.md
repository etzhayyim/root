---
id: adr-2604292130
title: llm.etzhayyim.com を Murakumo から分離し RunPod pass-through gateway に固定
status: active
doc_type: adr
topic: inference
authoritative: true
last_verified: 2026-04-29
authoritative_for:
  - llm.etzhayyim.com routing
  - RunPod Gemma4 OpenAI-compatible gateway
  - Murakumo and llm.etzhayyim.com separation
related:
  - adr-2604282100
  - adr-0056
  - adr-2604282300
supersedes: []
superseded_by: []
---

# Context

`llm.etzhayyim.com` had accumulated two conflicting meanings:

- public OpenAI-compatible LLM endpoint for higher-quality Gemma4 generation
- legacy / XRPC LLM actor path that could proxy into `magatama-llm8cf4ai` and the Murakumo LiteLLM fleet

This caused ambiguous routing. In particular, `gemma4-runpod` was advertised at the edge while
`murakumo-serve.etzhayyim.com` did not have the same model registered in its LiteLLM database.
The result was a split-brain path where `/v1/models` and `/v1/chat/completions` could disagree
depending on which Worker or tunnel answered.

# Decision

`llm.etzhayyim.com` is now an independent RunPod pass-through gateway served by
`60-apps/etzhayyim-project-runpod/serve` (`etzhayyim-runpod`).

It must not depend on or proxy to:

- `murakumo-serve.etzhayyim.com`
- `murakumo.etzhayyim.com`
- `magatama-llm8cf4ai`
- `LLM_SERVICE` service binding

The only active public inference path for `llm.etzhayyim.com/v1/*` is:

```text
client
  -> https://llm.etzhayyim.com/v1/chat/completions
  -> etzhayyim-runpod Cloudflare Worker
  -> RunPod Serverless endpoint 3fctheq51haikt
  -> Ollama gemma4:26b-a4b-it-q4_K_M
```

Public model aliases:

- `gemma4-runpod`
- `tier0-runpod`
- `gemma4:26b-a4b-it-q4_K_M`

`llm.etzhayyim.com/xrpc/com.etzhayyim.apps.llm.answerWithKnowledge` is intentionally unsupported on this
gateway and returns `unsupported_route`. RisingWave/BPMN knowledge workflows must use their own
actor route and must not be smuggled through the RunPod gateway.

Murakumo remains a separate inference platform. Its public and internal surfaces are
`murakumo.etzhayyim.com` and `murakumo-serve.etzhayyim.com`; those are not aliases for `llm.etzhayyim.com`.

# Consequences

- `llm.etzhayyim.com` no longer uses Murakumo LiteLLM as a backend or fallback.
- RunPod cold starts and queue delay are part of the `llm.etzhayyim.com` SLO. Callers must use longer
  timeouts for non-streaming requests, or stream where possible.
- Schema-aware RAG can target `gemma4-runpod` without depending on Murakumo model registration.
- Any XRPC workflow previously expecting `llm.etzhayyim.com` to proxy into `magatama-llm8cf4ai` must be
  moved to a dedicated actor hostname or Worker binding.

Verified 2026-04-29:

```bash
curl https://llm.etzhayyim.com/_app/meta
curl -H 'x-magatama-verified: true' https://llm.etzhayyim.com/v1/models
pnpm --dir 30-graph/graph-schema rag:llm -- \
  --query "legal corpus documents for JP jurisdiction" \
  --model gemma4-runpod \
  --top-k 5 \
  --max-tokens 80 \
  --magatama-verified
```

The RAG run returned HTTP 200 from `llm.etzhayyim.com`, model
`gemma4:26b-a4b-it-q4_K_M`, and SQL verifier `ok: true`.

# Alternatives Considered

- **Keep `llm.etzhayyim.com` on Murakumo LiteLLM and add RunPod as a LiteLLM DB model**:
  rejected for this hostname because it keeps public RunPod quality path coupled to Murakumo fleet
  health, LiteLLM DB migrations, and Murakumo tunnel routing.
- **Route `llm.etzhayyim.com` to `magatama-llm8cf4ai` and let that Worker choose backends**:
  rejected because it preserves the ambiguous XRPC + OpenAI surface and allows accidental fallback
  into Murakumo.
- **Expose only `runpod.etzhayyim.com` and retire `llm.etzhayyim.com`**:
  rejected because multiple consumers already use `llm.etzhayyim.com` as the canonical OpenAI-compatible
  LLM endpoint.

# References

- `60-apps/etzhayyim-project-runpod/serve/worker-gateway.ts`
- `60-apps/etzhayyim-project-runpod/serve/wrangler.jsonc`
- `60-apps/etzhayyim-project-runpod/deps.toml`
- `90-docs/260429-rw-schema-aware-rag-eval.md`
