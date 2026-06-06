# kotoba-e2e — browser-only kotoba end-to-end verification

Agentic + deterministic e2e for the browser-only kotoba feed (etzhayyim.com /
yoro.etzhayyim.com). Built from **langgraph + browser-use + LLM inference**, where
inference is **Murakumo-only** (ADR-2605215000) — never a commercial endpoint.

Two layers, orchestrated by a LangGraph `StateGraph`:

| Layer | Needs | Verifies |
|---|---|---|
| **Deterministic** (`browser.py` + `signals.py`) | playwright + chromium | SW active · feed hydrated from content-addressed IPFS blocks · **no RisingWave AppView read** · feed SW-served · boot-skeleton seen→removed · posts rendered |
| **Agentic** (`agent.py` + `graph.py`) | browser-use + Murakumo gateway up | LLM (Murakumo) semantically judges the feed + a browser-use agent explores it |

The deterministic core gates the exit code; the LLM nodes add semantic
confirmation and are **skipped automatically** when the Murakumo gateway
(`127.0.0.1:4000`) is down. LangGraph is optional — if it isn't installed the
harness runs the identical node order as an inline async pipeline.

## Charter compliance (critical)

`murakumo.py` is the single place an LLM client is built. `assert_murakumo_only()`
**refuses** any base URL that is not the loopback gateway / LAN fleet
(`api.openai.com`, `api.anthropic.com`, Vertex, Bedrock, RunPod, … are rejected by
an allowlist, not a denylist). The client is an OpenAI-*compatible* client pointed
at Murakumo's LiteLLM gateway — not at OpenAI. Key resolves from
`KOTOBA_INFERENCE_API_KEY` (env → macOS Keychain `etzhayyim/KOTOBA_INFERENCE_API_KEY`).

## Run

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# deterministic layer (no LLM, no Murakumo needed):
python -m kotoba_e2e.run --url https://etzhayyim.com --no-agent

# full agentic e2e (needs the Murakumo gateway up at 127.0.0.1:4000):
python -m kotoba_e2e.run --url https://etzhayyim.com
python -m kotoba_e2e.run --json          # machine-readable; exit 0 iff core checks pass
```

## Offline tests

```bash
python3 tests/test_signals.py     # pure assertion core (no browser/LLM)
python3 tests/test_murakumo.py    # the Murakumo-only charter guard
```

## Verified

`--no-agent` against live **https://etzhayyim.com** passes all 6 checks
(`sw_active`, `blocks_hydrated` src=blocks, `no_risingwave_reads` clean,
`feed_served_by_sw`, `skeleton_lifecycle`, `posts_rendered`) — empirical proof the
feed renders entirely browser-side from content-addressed blocks with no server.
