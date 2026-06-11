"""browser-use agentic layer — LLM-driven browser exploration via Murakumo.

This is the "agentic" half the design calls for: an LLM (Murakumo, NEVER a
commercial endpoint — see murakumo.py) drives a real browser through a
natural-language task and reports what it observed. It complements the
deterministic Playwright signal capture in browser.py.

Gated: requires `browser-use` installed AND the Murakumo gateway reachable. When
either is absent the caller skips this node (the deterministic layer still runs).
"""

from __future__ import annotations

from . import murakumo

# Default exploration task — phrased so a small Murakumo model (gemma4) can follow
# it. The agent's job is SEMANTIC confirmation, not the hard network assertions
# (those are deterministic in signals.py).
DEFAULT_TASK = (
    "Open the page. Wait for the social feed to load. "
    "Confirm a feed of short posts is visible (each with author + text). "
    "Report how many posts you can see and the text of the first one. "
    "Do not log in, do not post, do not click any irreversible button."
)


async def run_agent_task(url: str, task: str | None = None, *, max_steps: int = 12) -> dict:
    """Run a browser-use Agent (Murakumo LLM) against `url`. Returns a verdict dict.

    Raises if browser-use is unavailable or the LLM cannot be built (the charter
    guard in make_llm runs first, so a commercial endpoint can never be used).
    """
    from browser_use import Agent  # type: ignore

    llm = murakumo.make_llm()
    full_task = f"Go to {url}. {task or DEFAULT_TASK}"
    agent = Agent(task=full_task, llm=llm)
    result = await agent.run(max_steps=max_steps)
    # browser-use result objects vary across versions; stringify defensively.
    text = ""
    try:
        text = result.final_result() if hasattr(result, "final_result") else str(result)
    except Exception:
        text = str(result)
    return {"ran": True, "summary": text}


async def murakumo_reachable(timeout: float = 4.0) -> bool:
    """Best-effort liveness probe of the Murakumo gateway (no LLM call)."""
    import urllib.request

    url = murakumo.base_url().rstrip("/") + "/models"
    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {murakumo.resolve_api_key()}"})
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (loopback only)
            return r.status == 200
    except Exception:
        return False
