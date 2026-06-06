# kotoba-e2e — CLAUDE notes

Browser-only-kotoba e2e harness. **langgraph + browser-use + Murakumo LLM.**

## Hard rules

- **Murakumo-only inference (ADR-2605215000).** Build LLM clients ONLY via
  `murakumo.make_llm()`; it runs `assert_murakumo_only()` first. Never add an
  OpenAI/Anthropic/Vertex/Bedrock/RunPod base URL or vendor key path. The guard is
  an allowlist (loopback / `*.murakumo.etzhayyim.com` / private LAN) — extend the
  allowlist only for genuine fleet nodes.
- **No server-held key.** The harness reads the loopback gateway bearer from env /
  Keychain; it never embeds a key.
- **Read-only against prod.** The deterministic layer only navigates + observes.
  The agentic task prompt forbids login / posting / irreversible clicks; keep it so.

## Layout

- `murakumo.py`  — Murakumo LLM factory + charter guard (pure parts testable).
- `signals.py`   — pure pass/fail over captured signals (the verification contract).
- `browser.py`   — Playwright driver; goto → SW-ready → reload → capture (controlled load).
- `agent.py`     — browser-use Agent (Murakumo) + gateway liveness probe.
- `graph.py`     — LangGraph StateGraph (capture→assert→[llm_judge→agent]→report);
                   inline-pipeline fallback when langgraph absent.
- `run.py`       — CLI; exit 0 iff deterministic CORE checks pass.
- `tests/`       — offline unit tests (no browser, no LLM): 12/12 green.

## The contract (signals.py)

CORE (gates exit): `sw_active`, `blocks_hydrated` (fresh fetch OR `x-kotoba-src`∈
{blocks,idb,seed} on an SW-served response), `no_risingwave_reads` (no feed read to
`atproto.etzhayyim.com`). QUALITY: `feed_served_by_sw`, `skeleton_lifecycle`,
`posts_rendered`.

## Gotchas

- On a warm reload the SW serves from IndexedDB without re-fetching blocks — so
  `blocks_hydrated` relies on the `x-kotoba-src` response header, not a fresh fetch.
- Python 3.14: playwright installs fine; `playwright install chromium` is required
  once. browser-use/langgraph are only needed for the agentic layer.
- Murakumo gateway is frequently down locally; the LLM nodes self-skip, so the
  deterministic verdict still stands.
