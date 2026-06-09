#!/usr/bin/env python3
"""tsumugi 紡ぎ — Murakumo-only intel narration (local-dev twin of deploy/agent.py).

ADR-2606092000 + ADR-2605215000 (Murakumo-only inference) + G6.

A LangGraph-SHAPED pipeline (load → analyze → build-prompt → infer → emit) that narrates
the scale (A) + 旗 banner (B) intel as a terse aggregate observation. The `infer` node
routes ONLY through the Murakumo fleet (LiteLLM gateway, default 127.0.0.1:4000; EVO-X2 LAN
192.168.1.70; per-node Ollama gemma3:4b / the Maxwell weight) — an external LLM host is
REFUSED (G6 / Charter substrate boundary). Dry-run by default; a real call needs the operator
gate AND the fleet reachable. No published social post (G7).

This is the stdlib twin that runs + tests OFFLINE. The canonical in-WASM Murakumo path is
`deploy/agent.py` (kotoba_langgraph → KotobaLLM → host MURAKUMO_DEFAULT_MODEL), built via
componentize-py and run on a live kotoba node (mirrors himawari/deploy/agent.py).

Usage:
    python3 narrate.py                 # dry-run: builds the prompt, writes out/narration.dryrun.md
    TSUMUGI_MURAKUMO_GATE=1 TSUMUGI_OPERATOR_DID=did:web:… python3 narrate.py   # real Murakumo call
"""
from __future__ import annotations
import sys, os, json, pathlib, urllib.request, urllib.error
from urllib.parse import urlparse

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import analyze_scale as A      # noqa: E402
import analyze_banner as Bnr   # noqa: E402

# ── Murakumo-only invariant (G6 / ADR-2605215000) ─────────────────────────────────────────
MURAKUMO_BASE_URL = os.environ.get("MURAKUMO_BASE_URL", "http://127.0.0.1:4000")
MURAKUMO_MODEL = os.environ.get("MURAKUMO_MODEL", "gemma3:4b")   # Maxwell (Gemma 4 E4B) = target weight
# the ONLY hosts a religious-corp inference call may reach (loopback LiteLLM + EVO-X2 LAN);
# extendable via env for other fleet nodes, but NEVER an external provider.
_FLEET_HOSTS = {"127.0.0.1", "localhost", "::1", "192.168.1.70"}
_FLEET_HOSTS |= {h.strip() for h in os.environ.get("MURAKUMO_ALLOWED_HOSTS", "").split(",") if h.strip()}

SYSTEM_PROMPT = (
    "You are tsumugi, a terse power-dynamics intel narrator for a religious non-profit. "
    "You are given AGGREGATE, edge-primary readouts of (A) 産官学報 cross-sector concentration "
    "by locality and (B) declared ideology/faction camps. Narrate in at most 4 sentences. "
    "HARD RULES: mirror-not-target (this is an openness/resilience map, never a target-list); "
    "non-adjudicating (state concentration/alignment as structural fact — NEVER 'corruption', "
    "'collusion', 'extremist', or any verdict); aggregate-only (never name or imply a private "
    "individual — only institutions and public seats appear); plural (note bridges/pluralism). "
    "No preamble, no recommendation to act against anyone."
)


def _assert_murakumo(base_url: str):
    """G6 — refuse any inference host that is not the Murakumo fleet."""
    host = (urlparse(base_url).hostname or "").lower()
    if host not in _FLEET_HOSTS:
        raise ValueError(
            f"G6 / ADR-2605215000 breach: inference host {host!r} is not the Murakumo fleet "
            f"{sorted(_FLEET_HOSTS)}. Religious-corp inference is Murakumo-only — external "
            "providers (OpenAI/Anthropic-direct/RunPod/Vertex/Bedrock) are prohibited.")


def build_prompt(scale_result: dict, banner_result: dict) -> str:
    """Compose the Charter-safe USER prompt from aggregate readouts only (no per-person data)."""
    top_loc = scale_result["localities"][:5]
    top_ck = scale_result.get("collective_kinds", [])[:6]
    top_brokers = scale_result["brokers"][:5]
    camps = banner_result["camps"][:5]
    bridges = banner_result["bridges"][:5]
    lines = ["(A) 産官学報 concentration — top localities:"]
    for x in top_loc:
        lines.append(f"  - {x['locality']}: sectors {' '.join(x['sectors'])} "
                     f"(diversity {x['sector_diversity']}, concentration {x['concentration']})")
    if top_ck:
        lines.append("(A) granularity (粒度) — incident load by collective-kind:")
        for x in top_ck:
            lines.append(f"  - {x['ja']}: {x['node_count']} nodes, load {x['load']}")
    lines.append("(A) top cross-sector brokers (seat/org ids):")
    for x in top_brokers:
        lines.append(f"  - {x['id']} ({x['sector']} → {' '.join(x['bridges_to'])}, span {x['span']})")
    lines.append("(B) declared camps by reach:")
    for c in camps:
        lines.append(f"  - {c['label']} (kind {c['kind']}, reach {c['reach']}, {c['member_count']} members)")
    lines.append("(B) bridges (entities flying ≥2 banners — pluralism):")
    for b in bridges:
        lines.append(f"  - {b['label']}: {' · '.join(b['banners'])}")
    return "\n".join(lines)


def infer(prompt: str, *, gate: bool, base_url: str = MURAKUMO_BASE_URL,
          model: str = MURAKUMO_MODEL, timeout: float = 30.0):
    """The `infer` node. Returns (text, status). status ∈ {'dry-run','ok','unreachable'}.

    G6: ALWAYS asserts the host is Murakumo (even in dry-run, so a misconfig is caught early).
    A real call fires only when `gate` is true (operator gate) AND the fleet answers."""
    _assert_murakumo(base_url)
    if not gate:
        return None, "dry-run"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": prompt}],
        "temperature": 0.2, "max_tokens": 320,
    }).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip(), "ok"
    except (urllib.error.URLError, OSError, KeyError, json.JSONDecodeError) as e:
        return None, f"unreachable: {str(e)[:120]}"


def run(gate: bool | None = None, out: pathlib.Path | None = None) -> dict:
    """The LangGraph-shaped pipeline. Returns a state dict (deterministic up to infer)."""
    if gate is None:
        gate = os.environ.get("TSUMUGI_MURAKUMO_GATE") == "1"
    out = out or (ACTOR_DIR / "out")
    out.mkdir(parents=True, exist_ok=True)
    scale_result = A.analyze(*A.load())
    banner_result = Bnr.analyze(*Bnr.load())
    prompt = build_prompt(scale_result, banner_result)
    text, status = infer(prompt, gate=gate)
    # G7 — dry-run artifact always written; a published post is NOT emitted here.
    (out / "narration.dryrun.md").write_text(
        f"<!-- tsumugi Murakumo narration — model={MURAKUMO_MODEL} via {MURAKUMO_BASE_URL} "
        f"(G6 Murakumo-only); status={status}; published=false (G7) -->\n\n"
        f"## SYSTEM\n{SYSTEM_PROMPT}\n\n## USER (aggregate intel)\n{prompt}\n"
        + (f"\n## MURAKUMO OUTPUT\n{text}\n" if text else ""), encoding="utf-8")
    if text:
        (out / "narration.md").write_text(text + "\n", encoding="utf-8")
    return {"status": status, "prompt": prompt, "narrative": text, "published": False}


def main(argv):
    gate = "--live" in argv or os.environ.get("TSUMUGI_MURAKUMO_GATE") == "1"
    st = run(gate=gate)
    print(f"[tsumugi/narrate] status={st['status']} · model={MURAKUMO_MODEL} via "
          f"{MURAKUMO_BASE_URL} · published={st['published']} → out/narration.dryrun.md")
    if st["status"].startswith("unreachable"):
        print("  (Murakumo fleet not reachable — dry-run prompt written; "
              "run on a fleet host with TSUMUGI_MURAKUMO_GATE=1 for a live narration)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
