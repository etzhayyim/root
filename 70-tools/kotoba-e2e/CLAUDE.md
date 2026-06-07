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

## Finding (2026-06-06): SSR blind spot + profile/thread are NOT browser-only

Running the harness against `/profile/<did>` on live etzhayyim.com:
`sw_active ✓`, `no_risingwave_reads ✓ (clean)`, but `feed_served_by_sw ✗ "no feed
read observed"` + `blocks_hydrated ✗`. The home FEED is browser-only (6/6, CSR via
the SW), but **profile + post-thread pages are SSR'd** — yoro's `+page.server.ts`
fetches `getProfile`/`getPostThread` via `PDS_SERVICE` (server-side, RisingWave-
backed) before the HTML reaches the browser, so the SW never intercepts them.

Consequence + limitation:
- The data source of an SSR page is a SERVER-side fetch, invisible to the browser
  — so `no_risingwave_reads` is a **false-clean** for SSR pages (it only sees
  browser network). The harness verifies the CLIENT-side browser-only contract;
  it cannot assert the data source of SSR'd pages.
- This is the next real gap for "kotoba browser-only": the FEED is done; PROFILE
  and THREAD still SSR from RisingWave. Closing it = move those `+page.server.ts`
  loads to CSR + SW (or SSR from the kotoba blocks), which is a yoro architectural
  change (SEO/perf tradeoff per yoro CLAUDE.md), not a quick edit.

A future harness rev could detect SSR (data already in the initial HTML with no
client XRPC) and report "data source not browser-observable (SSR)" instead of a
plain ✗, so SSR pages aren't mistaken for browser-only.

## Gotchas

- On a warm reload the SW serves from IndexedDB without re-fetching blocks — so
  `blocks_hydrated` relies on the `x-kotoba-src` response header, not a fresh fetch.
- Python 3.14: playwright installs fine; `playwright install chromium` is required
  once. browser-use/langgraph are only needed for the agentic layer.
- Murakumo gateway is frequently down locally; the LLM nodes self-skip, so the
  deterministic verdict still stands.
