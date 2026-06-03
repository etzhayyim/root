"""Pytest config + langgraph stub for lg-yatabase unit tests.

The langgraph package is a runtime dep but may not be installed in the
local dev environment. When absent, install a minimal in-memory
StateGraph that supports `add_node`, `add_edge`, `compile`, and
`ainvoke` — enough for the node-level tests we run here.

Mirrors the pattern used by 20-actors/magatama/py/tests/conftest.py.
"""

from __future__ import annotations

import inspect
import sys
import types
from pathlib import Path

# Make lg_yatabase importable.
_lg_root = Path(__file__).resolve().parent.parent
if str(_lg_root) not in sys.path:
    sys.path.insert(0, str(_lg_root))


def _install_langgraph_stub() -> None:
    if "langgraph" in sys.modules:
        try:
            import importlib.util as _ilu  # noqa: PLC0415
            if _ilu.find_spec("langgraph.graph") is not None:
                return
        except (ModuleNotFoundError, ValueError):
            pass

    _END = "__end__"
    _START = "__start__"

    class _CompiledGraph:
        def __init__(self, nodes, edges):
            self._nodes = nodes
            self._edges = edges  # list[(src, dst)]

        def _next(self, current: str) -> str:
            for src, dst in self._edges:
                if src == current:
                    return dst
            return _END

        async def ainvoke(self, state, config=None):
            current = self._next(_START)
            cur = dict(state or {})
            guard = 0
            while current not in (_END, None) and guard < 50:
                guard += 1
                fn = self._nodes.get(current)
                if fn is not None:
                    if inspect.iscoroutinefunction(fn):
                        update = await fn(cur)
                    else:
                        update = fn(cur)
                    if isinstance(update, dict):
                        cur.update(update)
                current = self._next(current)
            return cur

    class _StateGraph:
        def __init__(self, schema=None):
            self._nodes: dict = {}
            self._edges: list = []

        def add_node(self, name, fn):
            self._nodes[name] = fn

        def add_edge(self, src, dst):
            self._edges.append((src, dst))

        def add_conditional_edges(self, *_args, **_kw):
            pass

        def set_entry_point(self, _node):
            pass

        def compile(self):
            return _CompiledGraph(self._nodes, self._edges)

    langgraph_graph = types.ModuleType("langgraph.graph")
    langgraph_graph.StateGraph = _StateGraph         # type: ignore[attr-defined]
    langgraph_graph.END = _END                        # type: ignore[attr-defined]
    langgraph_graph.START = _START                    # type: ignore[attr-defined]
    langgraph = types.ModuleType("langgraph")
    langgraph.graph = langgraph_graph                 # type: ignore[attr-defined]
    sys.modules["langgraph"] = langgraph
    sys.modules["langgraph.graph"] = langgraph_graph


def _install_asyncpg_stub() -> None:
    """asyncpg is a runtime dep but the tests never make real DB calls —
    we monkey-patch fetch/fetchrow/fetchval/execute at the import site
    in each test. A minimal stub satisfies the bmc.db top-level import.
    """
    if "asyncpg" in sys.modules:
        return

    asyncpg = types.ModuleType("asyncpg")

    class _Pool:
        async def close(self):
            pass

    class _Connection:
        pass

    async def _create_pool(*_args, **_kw):
        return _Pool()

    asyncpg.Pool = _Pool                       # type: ignore[attr-defined]
    asyncpg.Connection = _Connection           # type: ignore[attr-defined]
    asyncpg.create_pool = _create_pool         # type: ignore[attr-defined]
    sys.modules["asyncpg"] = asyncpg


_install_langgraph_stub()
_install_asyncpg_stub()
