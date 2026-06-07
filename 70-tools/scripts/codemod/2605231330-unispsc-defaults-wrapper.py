"""
Wrap each broken agent's compiled graph in a DefaultsWrapper that
pre-fills missing TypedDict fields per the agent's own schema.

The gemini-emitted graphs assume their full State dict is supplied on
``invoke()``, but the cell-runner / XRPC façade pass only what the caller
provided. Empty input → KeyError as soon as the first node reads
``state['purity']`` etc.

Per-file AST surgery would be invasive across 4,255+ files. Instead we
wrap the compiled graph at module level — a thin proxy that:

  1. Intercepts ``invoke(input_state, …)``
  2. Merges ``input_state`` over a per-agent ``_DEFAULTS`` dict whose
     keys + types come from the file's ``TypedDict`` declaration
  3. Delegates everything else (``stream``, ``builder``, ``ainvoke``,
     ``get_state`` …) to the inner CompiledStateGraph via ``__getattr__``

Defaults are inferred from the TypedDict annotation:

  ============= ==========
  Annotation    Default
  ============= ==========
  str           ""
  int           0
  float         0.0
  bool          False
  list / List   []
  dict / Dict   {}
  Annotated[X]  default for X (recursive)
  Optional[X]   None
  else          None
  ============= ==========

Usage::

    cd 40-engine/kotoba/crates/kotoba-kotodama/py
    uv run python ../../../70-tools/scripts/codemod/2605231330-unispsc-defaults-wrapper.py --dry-run
    uv run python ../../../70-tools/scripts/codemod/2605231330-unispsc-defaults-wrapper.py
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_DIR = (
    REPO_ROOT / "20-actors" / "kotodama" / "py" / "src"
    / "kotodama" / "langgraph_graphs" / "unispsc_agents"
)

MARKER = "# codemod-2605231330-defaults-wrapper"


def _default_for_annotation(node: ast.expr | None) -> str:
    """Return a Python source-code literal default for an annotation node."""
    if node is None:
        return "None"
    if isinstance(node, ast.Name):
        return {
            "str": '""',
            "int": "0",
            "float": "0.0",
            "bool": "False",
            "list": "[]",
            "List": "[]",
            "dict": "{}",
            "Dict": "{}",
            "set": "set()",
            "Set": "set()",
            "tuple": "()",
            "Tuple": "()",
        }.get(node.id, "None")
    if isinstance(node, ast.Subscript):
        v = node.value
        outer = v.id if isinstance(v, ast.Name) else (
            v.attr if isinstance(v, ast.Attribute) else ""
        )
        outer_l = outer.lower()
        if outer_l in {"list", "sequence", "iterable"}:
            return "[]"
        if outer_l in {"dict", "mapping"}:
            return "{}"
        if outer_l in {"set", "frozenset"}:
            return "set()"
        if outer_l in {"tuple"}:
            return "()"
        if outer_l == "optional":
            return "None"
        if outer_l == "annotated":
            # Annotated[X, …] → use X
            inner = node.slice
            if isinstance(inner, ast.Tuple) and inner.elts:
                return _default_for_annotation(inner.elts[0])
            return _default_for_annotation(inner)
        if outer_l == "union":
            # Pick None if Union contains NoneType-ish; else first arm.
            inner = node.slice
            if isinstance(inner, ast.Tuple):
                for elt in inner.elts:
                    if isinstance(elt, ast.Constant) and elt.value is None:
                        return "None"
                if inner.elts:
                    return _default_for_annotation(inner.elts[0])
            return "None"
        return "None"
    if isinstance(node, ast.Attribute):
        # e.g. typing.List → treat like List
        return _default_for_annotation(ast.Name(id=node.attr, ctx=ast.Load()))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        # PEP 604: `str | None` → "None" if a None side else default of left
        if (isinstance(node.right, ast.Constant) and node.right.value is None) or (
            isinstance(node.left, ast.Constant) and node.left.value is None
        ):
            return "None"
        return _default_for_annotation(node.left)
    return "None"


def _find_typeddict_fields(tree: ast.AST) -> dict[str, str]:
    """Walk module AST, find first TypedDict subclass, return {field: default_src}."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Match `class X(TypedDict)` or `class X(TypedDict, total=False)` etc.
        is_td = False
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "TypedDict":
                is_td = True
                break
            if isinstance(base, ast.Attribute) and base.attr == "TypedDict":
                is_td = True
                break
        if not is_td:
            continue
        out: dict[str, str] = {}
        for body in node.body:
            if isinstance(body, ast.AnnAssign) and isinstance(body.target, ast.Name):
                out[body.target.id] = _default_for_annotation(body.annotation)
        if out:
            return out
    return {}


WRAPPER_TEMPLATE = '''

{marker}
_DEFAULTS_2605231330 = {{
{kv_lines}
}}


class _DefaultsWrapper2605231330:
    """Pre-fills missing TypedDict fields before delegating to the compiled graph."""

    __slots__ = ("_inner", "_defaults")

    def __init__(self, inner, defaults):
        self._inner = inner
        self._defaults = defaults

    def _merge(self, input_state):
        if not isinstance(input_state, dict):
            return input_state
        merged = dict(self._defaults)
        merged.update(input_state)
        return merged

    def invoke(self, input_state, config=None, **kwargs):
        merged = self._merge(input_state)
        if config is None:
            return self._inner.invoke(merged, **kwargs)
        return self._inner.invoke(merged, config=config, **kwargs)

    async def ainvoke(self, input_state, config=None, **kwargs):
        merged = self._merge(input_state)
        if config is None:
            return await self._inner.ainvoke(merged, **kwargs)
        return await self._inner.ainvoke(merged, config=config, **kwargs)

    def stream(self, input_state, config=None, **kwargs):
        merged = self._merge(input_state)
        if config is None:
            return self._inner.stream(merged, **kwargs)
        return self._inner.stream(merged, config=config, **kwargs)

    async def astream(self, input_state, config=None, **kwargs):
        merged = self._merge(input_state)
        if config is None:
            async for chunk in self._inner.astream(merged, **kwargs):
                yield chunk
            return
        async for chunk in self._inner.astream(merged, config=config, **kwargs):
            yield chunk

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_inner"), name)


graph = _DefaultsWrapper2605231330(graph, _DEFAULTS_2605231330)
'''


def render_wrapper(defaults: dict[str, str]) -> str:
    if not defaults:
        return ""
    kv = ",\n".join(f"    {k!r}: {v}" for k, v in defaults.items())
    return WRAPPER_TEMPLATE.format(marker=MARKER, kv_lines=kv)


def patch_text(text: str) -> tuple[str, bool, int]:
    """Returns (new_text, changed, fields_count)."""
    if MARKER in text:
        return text, False, 0
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text, False, 0
    fields = _find_typeddict_fields(tree)
    if not fields:
        return text, False, 0
    # Detect `graph = X.compile()` exists at module level (codemod 1310/1320
    # already ensured this). If not, skip.
    has_graph_assign = False
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and t.id == "graph":
                has_graph_assign = True
                break
    if not has_graph_assign:
        return text, False, 0
    new = text.rstrip() + render_wrapper(fields)
    return new, True, len(fields)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--manifest", default="/tmp/etz-broken-agents.jsonl")
    parser.add_argument("--all", action="store_true",
                        help="apply to every preserved agent, not just manifest-broken")
    args = parser.parse_args()

    # Build target set from manifest (KeyError + DictAttr).
    targets: set[str] | None = None
    if not args.all:
        mf = Path(args.manifest)
        if mf.exists():
            targets = set()
            for line in mf.read_text().splitlines():
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                etype = rec.get("etype", "")
                msg = rec.get("msg", "")
                if etype == "KeyError":
                    targets.add(rec["code"])
                elif etype == "AttributeError" and "'dict' object has no attribute" in msg:
                    targets.add(rec["code"])
                elif etype == "TypeError" and "NoneType" in msg:
                    targets.add(rec["code"])
            print(f"manifest target set = {len(targets)} codes")

    rewritten = 0
    skipped_marker = 0
    skipped_no_td = 0
    total_fields = 0
    samples = []
    t0 = time.time()
    files = sorted(p for p in AGENTS_DIR.iterdir() if p.name.startswith("c") and p.suffix == ".py")
    for p in files:
        code = p.stem[1:]
        if targets is not None and code not in targets:
            continue
        original = p.read_text()
        new, changed, fields_count = patch_text(original)
        if not changed:
            if MARKER in original:
                skipped_marker += 1
            else:
                skipped_no_td += 1
            continue
        if not args.dry_run:
            p.write_text(new)
        rewritten += 1
        total_fields += fields_count
        if len(samples) < 3:
            samples.append((code, fields_count))

    print(f"rewritten          = {rewritten}")
    print(f"skipped (already)  = {skipped_marker}")
    print(f"skipped (no TD)    = {skipped_no_td}")
    print(f"total fields added = {total_fields}")
    print(f"samples            = {samples}")
    print(f"elapsed            = {time.time() - t0:.2f}s")
    if args.dry_run:
        print("(dry-run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
