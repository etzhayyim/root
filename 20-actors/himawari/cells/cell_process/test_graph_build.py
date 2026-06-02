#!/usr/bin/env python3
"""cell_process — StateGraph build/topology tests (ADR-2606021200 / R1 maturation).

In local dev `langgraph` is absent, so `StateGraph is None` and solve() takes the
sequential fallback — leaving `_build_graph()` and the LangGraph branch of solve()
uncovered. These tests inject a minimal fake StateGraph to exercise that branch
and assert the compiled process DAG matches the documented topology:

  init → texture → junction → metallization → flash_iv → gas_abatement
       → {witness | halt}  ;  witness → emit → __end__  ;  halt → __end__

This verifies the graph wiring (node set, linear edges, the G3 gas-abatement
conditional halt) deterministically without a real langgraph dependency.
"""
import importlib.util
import pathlib
import sys

# Register under a unique name in sys.modules BEFORE exec so the cell's
# @dataclass field-type lookups (which read sys.modules[cls.__module__]) resolve.
_MOD_NAME = "himawari_cell_process_cell_g"
_spec = importlib.util.spec_from_file_location(
    _MOD_NAME, pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_MOD_NAME] = _mod
_spec.loader.exec_module(_mod)


class _Compiled:
    def __init__(self, spec):
        self.spec = spec

    def invoke(self, state):
        # sentinel: prove solve() routed through the compiled graph, not the fallback
        return {"invoked_via": "fake_stategraph", "echo": state}


class _FakeStateGraph:
    def __init__(self, _schema):
        self.nodes = {}
        self.edges = []
        self.conditional = []
        self.entry = None

    def add_node(self, name, fn):
        self.nodes[name] = fn

    def add_edge(self, a, b):
        self.edges.append((a, b))

    def add_conditional_edges(self, src, router, mapping):
        self.conditional.append((src, router, mapping))

    def set_entry_point(self, name):
        self.entry = name

    def compile(self):
        return _Compiled(self)


def _restore():
    _mod.StateGraph = None


def test_build_graph_topology():
    _mod.StateGraph = _FakeStateGraph
    try:
        compiled = _mod.CellProcessCell()._build_graph()
        spec = compiled.spec
        expected_nodes = {
            "init", "texture", "junction", "metallization",
            "flash_iv", "gas_abatement", "witness", "emit", "halt",
        }
        assert set(spec.nodes) == expected_nodes, f"node set drift: {set(spec.nodes)}"
        assert spec.entry == "init"
        assert ("init", "texture") in spec.edges
        assert ("flash_iv", "gas_abatement") in spec.edges
        assert ("emit", "__end__") in spec.edges
        assert ("halt", "__end__") in spec.edges
        # the G3 gas-abatement conditional halt
        assert len(spec.conditional) == 1
        src, _router, mapping = spec.conditional[0]
        assert src == "gas_abatement"
        assert mapping == {"witness": "witness", "halt": "halt"}
    finally:
        _restore()


def test_solve_routes_through_compiled_graph():
    _mod.StateGraph = _FakeStateGraph
    try:
        cell = _mod.CellProcessCell()
        out = cell.solve({"waferBatchId": "WAF-1"})
        assert out["invoked_via"] == "fake_stategraph", "solve() must use the compiled graph when StateGraph present"
        # graph is built once and memoized
        assert cell.graph is not None
    finally:
        _restore()


def test_solve_falls_back_when_stategraph_absent():
    _mod.StateGraph = None
    out = _mod.CellProcessCell().solve({"waferBatchId": "WAF-1"})
    # sequential fallback returns a real merged state dict (not the fake sentinel)
    assert isinstance(out, dict) and out.get("invoked_via") != "fake_stategraph"


if __name__ == "__main__":
    import sys

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
