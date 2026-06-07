"""
shionome_social_post — DRY-RUN capital-flow social post (shionome).
Resident in Kotoba WASM. Per ADR-2606072200. Mirror (G5), no-trade body scan (G2), member-signed
(G7), dry-run only (G8). Live posting Council Lv6+ + operator + member-signature gated.
"""
from typing import TypedDict
try:
    import wit_world
except ImportError:
    wit_world = None

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shionome_core import draft_dry_run_post  # noqa: E402

_r0_marker = True


class PostState(TypedDict, total=False):
    context: dict
    regime: dict
    post: dict
    refusal: str


def _draft(state: PostState) -> dict:
    ctx = state.get("context", {}) or {}
    reg = state.get("regime") or ctx.get("regime", {})
    sources = ctx.get("sources", [])
    label = reg.get("regime", "indeterminate")
    body = (f"クロスアセット観測: {label} — リスク資産 net {reg.get('risk_net', 0):+.1f}bn / "
            f"安全資産 net {reg.get('safe_net', 0):+.1f}bn。記述であり助言ではありません。")
    try:
        return {"post": draft_dry_run_post(body, sources), "refusal": ""}
    except ValueError as e:
        return {"post": {}, "refusal": str(e)}


_g = StateGraph(PostState)
_g.add_node("draft", _draft)
_g.add_edge(START, "draft")
_g.add_edge("draft", END)
compiled = _g.compile(checkpointer=KotobaCheckpointer())

if wit_world:
    class WitWorld(wit_world.WitWorld):
        def run(self, ctx_cbor: bytes) -> bytes:
            return handle_invoke(ctx_cbor, compiled)
