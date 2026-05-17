"""Extractor v2 — adds state_key inference from node body usage.

In addition to TypedDict subclass scanning, we walk each *_node async function's
body for:
  - return {...} Dict literals: collect all string-constant keys (writes)
  - state.get("X") / state["X"] / state.setdefault("X"): collect (reads)

Final state_keys = union(declared, written, read), preserving declared order
where possible, with newly-inferred keys appended.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

PKG_ROOT = Path("/Users/junkawasaki/github/etzhayyim/root/20-actors/magatama/py/src/pymagatama/langgraph_graphs")


def _const_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _func_dotted(name_node: ast.AST, module: str) -> str | None:
    if isinstance(name_node, ast.Name):
        return f"{module}:{name_node.id}"
    return None


def _scan_state_keys_in_func(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Walk fn body for return {...}, state.get/[]/setdefault."""
    keys: set[str] = set()
    for node in ast.walk(fn):
        # return {...}
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            for k in node.value.keys:
                s = _const_str(k)
                if s:
                    keys.add(s)
        # state.get("X") / state.setdefault("X")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "state"
                and node.func.attr in ("get", "setdefault", "pop")
                and node.args
            ):
                s = _const_str(node.args[0])
                if s:
                    keys.add(s)
        # state["X"]
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "state"
        ):
            s = _const_str(node.slice)
            if s:
                keys.add(s)
    return keys


def extract(module_path: Path) -> dict:
    src = module_path.read_text()
    tree = ast.parse(src)
    module_dotted = f"pymagatama.langgraph_graphs.{module_path.stem}"

    # Collected keys from sources (declared + inferred).
    declared_keys: list[str] = []
    inferred_keys: set[str] = set()

    # 1. TypedDict subclasses
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ClassDef)
            and any(
                (isinstance(b, ast.Name) and b.id == "TypedDict")
                or (isinstance(b, ast.Attribute) and b.attr == "TypedDict")
                for b in node.bases
            )
        ):
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    if stmt.target.id not in declared_keys:
                        declared_keys.append(stmt.target.id)

    # 2. Walk all top-level functions (looking for *_node, *_gate, build_graph)
    build_fn = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "build_graph":
                build_fn = node
            elif node.name.endswith("_node") or node.name.endswith("_gate"):
                inferred_keys |= _scan_state_keys_in_func(node)

    if build_fn is None:
        return {"module": module_dotted, "error": "no build_graph"}

    # 3. Build topology spec from build_graph (same as v1)
    entry: str | None = None
    edges: list[dict] = []
    conditional_edges: list[dict] = []
    node_bindings: list[dict] = []

    for stmt in ast.walk(build_fn):
        if not isinstance(stmt, ast.Call) or not isinstance(stmt.func, ast.Attribute):
            continue
        method = stmt.func.attr

        if method == "set_entry_point" and stmt.args:
            entry = _const_str(stmt.args[0])

        elif method == "add_node" and len(stmt.args) >= 2:
            nid = _const_str(stmt.args[0])
            ref = _func_dotted(stmt.args[1], module_dotted)
            if nid and ref:
                node_bindings.append({"node_id": nid, "kind": "py_primitive", "ref": ref})

        elif method == "add_edge" and len(stmt.args) >= 2:
            src = _const_str(stmt.args[0])
            d = stmt.args[1]
            dst = "END" if (isinstance(d, ast.Name) and d.id == "END") else _const_str(d)
            if src and dst:
                edges.append({"from": src, "to": dst})

        elif method == "add_conditional_edges" and len(stmt.args) >= 3:
            from_id = _const_str(stmt.args[0])
            router = _func_dotted(stmt.args[1], module_dotted)
            paths_node = stmt.args[2]
            paths: dict = {}
            if isinstance(paths_node, ast.Dict):
                for k, v in zip(paths_node.keys, paths_node.values):
                    key = _const_str(k)
                    val = "END" if (isinstance(v, ast.Name) and v.id == "END") else _const_str(v)
                    if key and val:
                        paths[key] = val
            if from_id and router and paths:
                conditional_edges.append({"from": from_id, "router": router, "paths": paths})

    if not entry:
        return {"module": module_dotted, "error": "no entry"}
    if not node_bindings:
        return {"module": module_dotted, "error": "no add_node calls"}

    # 4. Final state_keys = declared (preserved) + inferred (appended)
    final_keys = list(declared_keys)
    for k in sorted(inferred_keys):
        if k not in final_keys:
            final_keys.append(k)
    if not final_keys:
        final_keys = ["input", "output", "ok", "error"]

    spec = {"state_keys": final_keys, "entry": entry, "edges": edges}
    if conditional_edges:
        spec["conditional_edges"] = conditional_edges

    return {
        "module": module_dotted,
        "spec": spec,
        "node_bindings": node_bindings,
        "_keys_declared": declared_keys,
        "_keys_inferred": sorted(inferred_keys),
    }


if __name__ == "__main__":
    out = []
    skipped = []
    for f in sorted(PKG_ROOT.glob("*.py")):
        if f.name.startswith("_"):
            continue
        try:
            r = extract(f)
        except Exception as e:
            r = {"module": f.stem, "error": f"{type(e).__name__}: {e}"}
        if "error" in r:
            skipped.append({"file": f.name, "error": r["error"]})
        else:
            out.append({"file": f.name, **r})
    print(json.dumps({"extracted": len(out), "skipped": len(skipped),
                      "rows": out, "skip_reasons": skipped}, indent=2))
