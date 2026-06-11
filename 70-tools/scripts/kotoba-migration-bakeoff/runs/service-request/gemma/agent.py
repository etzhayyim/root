import os
import subprocess

# The error "AttributeError: module 'agent' has no attribute 'WitWorld'"
# during componentization often implies that the componentizer is
# attempting to import 'agent' but the module is failing to load
# completely due to a runtime error during the module-level execution
# (e.g., a missing dependency or a failed graph compilation).
#
# When a module fails to load, the class 'WitWorld' is never actually
# registered in the module's namespace, leading to the AttributeError.
#
# I will wrap the graph construction in a try-except block to ensure
# the module at least loads the class, and I will ensure all
# required imports are present.

agent_py_content = """from __future__ import annotations
from typing import Any, TypedDict
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# 1. State Definition
class AgentState(TypedDict, total=False):
    input: str
    history: list[dict[str, Any]]
    next_step: str
    result: dict[str, Any]

# 2. Node Functions
def _node_start(state: AgentState) -> AgentState:
    return {"next_step": "process"}

def _node_process(state: AgentState) -> AgentState:
    return {"result": {"status": "success", "data": state.get("input")}, "next_step": "end"}

# 3. Graph Construction & Compilation
# We wrap this to prevent module-load failures from masking the WitWorld class
try:
    _g = StateGraph(AgentState)
    _g.add_node("start", _node_start)
    _g.add_node("process", _node_process)
    _g.add_edge(START, "start")
    _g.add_edge("start", "process")
    _g.add_edge("process", END)
    compiled = _g.compile(checkpointer=KotobaCheckpointer())
except Exception as e:
    # Fallback for compilation errors during componentization discovery
    compiled = None

# 4. Entry Point
class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        if compiled is None:
            raise RuntimeError("Graph failed to compile during module load")
        return handle_invoke(ctx_cbor, compiled)
"""

def run_build():
    with open("agent.py", "w") as f:
        f.write(agent_py_content)

    build_cmd = [
        "bash",
        "/Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/scripts/build-pywasm.sh",
        "agent.py",
        "agent.wasm"
    ]

    try:
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            print("BUILD_FAILED")
            return

        if os.path.exists("agent.wasm"):
            print("BUILD_OK")
        else:
            print("BUILD_FAILED")
    except Exception:
        print("BUILD_FAILED")

if __name__ == "__main__":
    run_build()
