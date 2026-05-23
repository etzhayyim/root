#!/usr/bin/env python3
"""extract-click.py — Python AST walker that emits a yorishiro kami manifest
from a Click or argparse-based source repo.

Usage:
    python3 extract-click.py <source-path> --kami-id bin:<name> --binary <bin>
                             [--framework click|argparse|auto]

Output: a kami manifest JSON (same shape as 00-contracts/kami/*.kami.json,
consumed by the binary-cli generator path) on stdout.

Frameworks (Phase 2.5 / 2.5.1):
  - click   : @click.command / @click.group / @click.option / @click.argument
  - argparse: argparse.ArgumentParser + .add_argument(...) (single-parser
              scripts only — multi-parser / subparser apps degrade to the
              first parser found)
  - auto    : detect by AST imports / decorator names (default)

What it skips:
  - dynamic decorators / metaprogrammed CLIs
  - cobra (Go) / clap (Rust) — separate walkers
  - argparse subparsers
  - Click multi-value / nargs / callback options (degraded to plain string)
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any


def main() -> int:
    ap = argparse.ArgumentParser(prog="extract-click")
    ap.add_argument("source", help="Path to a directory or .py file with Click commands")
    ap.add_argument("--kami-id", required=True, help="kami.id (e.g. bin:cookiecutter)")
    ap.add_argument("--binary", required=True, help="kami.binary (entry-point command name)")
    ap.add_argument("--description", default="", help="Optional kami description")
    ap.add_argument("--version-flag", default="--version", help="Liveness probe flag")
    ap.add_argument(
        "--framework",
        choices=["click", "argparse", "auto"],
        default="auto",
        help="CLI framework to detect (default: auto — heuristic on imports / decorators)",
    )
    args = ap.parse_args()

    src = Path(args.source).resolve()
    files = collect_py_files(src)
    if not files:
        print(f"extract-click: no .py files under {src}", file=sys.stderr)
        return 1

    ops: list[dict[str, Any]] = []
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            print(f"extract-click: skipping {path}: {exc}", file=sys.stderr)
            continue
        framework = args.framework
        if framework == "auto":
            framework = _detect_framework(tree)
        if framework == "click":
            ops.extend(extract_click_commands_from(tree, path))
        elif framework == "argparse":
            ops.extend(extract_argparse_commands_from(tree, path))

    if not ops:
        print(
            f"extract-click: no Click @command / argparse ArgumentParser found under {src}. "
            "cobra / clap walkers land in a separate Phase 2.5.x.",
            file=sys.stderr,
        )
        return 2

    manifest = {
        "kami": {
            "id": args.kami_id,
            "binary": args.binary,
            "description": args.description or f"Auto-extracted from {src}",
            "version_flag": args.version_flag,
        },
        "ops": ops,
    }
    json.dump(manifest, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


def collect_py_files(p: Path) -> list[Path]:
    if p.is_file() and p.suffix == ".py":
        return [p]
    if p.is_dir():
        # Skip common vendor/test/cache dirs to keep the scan fast.
        skip = {".git", ".venv", "venv", "__pycache__", "node_modules", "tests", "test"}
        out: list[Path] = []
        for sub in p.rglob("*.py"):
            if any(part in skip for part in sub.parts):
                continue
            out.append(sub)
        return sorted(out)
    return []


def _detect_framework(tree: ast.AST) -> str:
    """Heuristic: click imports → click; argparse imports → argparse;
    decorator names containing 'command'/'group' → click; bare
    ArgumentParser usage → argparse. Defaults to click if ambiguous.
    """
    saw_click = False
    saw_argparse = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "click":
                saw_click = True
            if node.module == "argparse":
                saw_argparse = True
        elif isinstance(node, ast.Import):
            for n in node.names:
                if n.name == "click":
                    saw_click = True
                if n.name == "argparse":
                    saw_argparse = True
    if saw_click and not saw_argparse:
        return "click"
    if saw_argparse and not saw_click:
        return "argparse"
    return "click"  # tie → click (more common in modern CLIs)


def extract_argparse_commands_from(tree: ast.AST, _path: Path) -> list[dict[str, Any]]:
    """Walk a module for `argparse.ArgumentParser()` + `.add_argument(...)`.

    Scope-aware: parser variables are tracked per-block (top-level body
    or function body) so two functions can each have `parser = ...`
    without colliding.

    Coverage:
      - Phase 2.5.1   — single ArgumentParser, no subparsers ("main" op)
      - Phase 2.5.2   — add_subparsers + add_parser → one op per subparser
                        (parent args prepended as common args)
      - Phase 2.5.2.1 — multiple top-level ArgumentParser calls in the
                        same module → each emits its own op (named by prog=)
    """
    ops: list[dict[str, Any]] = []
    seen_op_names: dict[str, int] = {}

    def _walk_no_funcs(stmt: ast.AST):
        # Yield stmt + descendants, but stop at FunctionDef boundaries
        # so each block_iteration only sees its own scope (sibling /
        # nested functions are handled by their own emit_block call).
        yield stmt
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return  # do not descend into function body
        for child in ast.iter_child_nodes(stmt):
            yield from _walk_no_funcs(child)

    def emit_block(body: list[ast.stmt]) -> None:
        parsers: dict[str, dict[str, Any]] = {}
        first_parser: str | None = None
        subparsers_var: str | None = None
        subparsers: dict[str, dict[str, Any]] = {}
        sub_var_to_name: dict[str, str] = {}

        for stmt in body:
            for node in _walk_no_funcs(stmt):
                if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    target = node.targets[0].id
                    if isinstance(node.value, ast.Call):
                        tail = _attr_tail(node.value.func)
                        if tail == "ArgumentParser":
                            prog = ""
                            desc = ""
                            for kw in node.value.keywords:
                                if kw.arg == "prog" and isinstance(kw.value, ast.Constant):
                                    prog = str(kw.value.value)
                                if kw.arg == "description" and isinstance(kw.value, ast.Constant):
                                    desc = str(kw.value.value)
                            parsers[target] = {"prog": prog, "desc": desc, "add_calls": []}
                            if first_parser is None:
                                first_parser = target
                        elif tail == "add_subparsers" and first_parser is not None:
                            if (
                                isinstance(node.value.func, ast.Attribute)
                                and isinstance(node.value.func.value, ast.Name)
                                and node.value.func.value.id == first_parser
                            ):
                                subparsers_var = target
                        elif tail == "add_parser" and subparsers_var is not None:
                            if (
                                isinstance(node.value.func, ast.Attribute)
                                and isinstance(node.value.func.value, ast.Name)
                                and node.value.func.value.id == subparsers_var
                                and node.value.args
                                and isinstance(node.value.args[0], ast.Constant)
                                and isinstance(node.value.args[0].value, str)
                            ):
                                sub_name = node.value.args[0].value
                                desc = ""
                                for kw in node.value.keywords:
                                    if kw.arg in ("help", "description") and isinstance(kw.value, ast.Constant):
                                        desc = str(kw.value.value) or desc
                                subparsers[sub_name] = {"desc": desc, "add_calls": []}
                                sub_var_to_name[target] = sub_name
                elif (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "add_argument"
                    and isinstance(node.func.value, ast.Name)
                ):
                    owner = node.func.value.id
                    if owner in parsers:
                        parsers[owner]["add_calls"].append(node)
                    elif owner in sub_var_to_name:
                        subparsers[sub_var_to_name[owner]]["add_calls"].append(node)

        if not parsers:
            return

        if subparsers:
            # 2.5.2: parent args prepended.
            common_argv = _argparse_argv(parsers[first_parser]["add_calls"]) if first_parser else []
            for sub_name, sub in subparsers.items():
                sub_argv = _argparse_argv(sub["add_calls"])
                merged: list[dict[str, Any]] = []
                positional_index = 0
                for arg in (*common_argv, *sub_argv):
                    if arg["kind"] == "positional":
                        arg = {**arg, "position": positional_index}
                        positional_index += 1
                    merged.append(arg)
                _push_op(ops, seen_op_names, {
                    "name": sub_name,
                    "summary": sub["desc"] or f"argparse subcommand: {sub_name}",
                    "description": sub["desc"] or f"Auto-extracted from argparse subparser `{sub_name}`.",
                    "argv": merged,
                    "stdout_capture": True,
                    "stderr_capture": True,
                    "exit_code_ok": [0],
                    "timeout_seconds": 300,
                })
            return

        # No subparsers: emit one op per parser in this block.
        # Single-parser blocks always emit op "main" (back-compat with
        # the Phase 2.5.1 contract); multi-parser blocks switch to
        # prog-derived names so siblings don't collide.
        is_multi = sum(1 for p in parsers.values() if p["add_calls"]) > 1
        for idx, (var, p) in enumerate(parsers.items()):
            if not p["add_calls"]:
                continue
            if is_multi:
                base = p["prog"] or f"main_{idx}"
            else:
                base = "main"
            base = base.replace(" ", "_").replace("-", "_")
            _push_op(ops, seen_op_names, {
                "name": base,
                "summary": p["desc"] or p["prog"] or "argparse-extracted command",
                "description": p["desc"] or p["prog"] or f"Auto-extracted from argparse.ArgumentParser ({var}).",
                "argv": _argparse_argv(p["add_calls"]),
                "stdout_capture": True,
                "stderr_capture": True,
                "exit_code_ok": [0],
                "timeout_seconds": 300,
            })

    # Process the module's top-level statements, then each FunctionDef
    # body as its own scope. Nested FunctionDefs are walked too.
    blocks: list[list[ast.stmt]] = []
    if isinstance(tree, ast.Module):
        blocks.append(tree.body)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            blocks.append(node.body)
    for body in blocks:
        emit_block(body)
    return ops


def _push_op(ops: list[dict[str, Any]], seen: dict[str, int], op: dict[str, Any]) -> None:
    name = op["name"]
    count = seen.get(name, 0)
    seen[name] = count + 1
    if count > 0:
        op["name"] = f"{name}_{count}"
    ops.append(op)


def _argparse_argv(calls: list[ast.Call]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    positional_index = 0
    for call in calls:
        a = _argparse_argument_to_arg(call, positional_index)
        if a is None:
            continue
        out.append(a)
        if a["kind"] == "positional":
            positional_index += 1
    return out


def _argparse_argument_to_arg(call: ast.Call, position: int) -> dict[str, Any] | None:
    flags: list[str] = []
    for a in call.args:
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            flags.append(a.value)
    if not flags:
        return None
    is_positional = not flags[0].startswith("-")
    if is_positional:
        name = flags[0]
        out: dict[str, Any] = {
            "kind": "positional",
            "name": name.replace("-", "_"),
            "position": position,
            "required": True,
            "type": "string",
        }
    else:
        long_flag = next((f for f in flags if f.startswith("--")), flags[0])
        name = long_flag.lstrip("-").replace("-", "_")
        out = {"kind": "flag", "name": name, "flag": long_flag, "type": "string"}
    for kw in call.keywords:
        if kw.arg == "type":
            if isinstance(kw.value, ast.Name):
                out["type"] = _python_type_to_json_type(kw.value.id)
            elif isinstance(kw.value, ast.Attribute):
                out["type"] = _python_type_to_json_type(kw.value.attr)
        elif kw.arg == "default" and isinstance(kw.value, ast.Constant) and not isinstance(kw.value.value, (list, tuple, dict)):
            out["default"] = kw.value.value
        elif kw.arg == "required" and isinstance(kw.value, ast.Constant):
            out["required"] = bool(kw.value.value)
        elif kw.arg == "nargs" and isinstance(kw.value, ast.Constant):
            # argparse nargs="?" / "*" make positionals optional; "+" keeps
            # them required (≥1).
            if out["kind"] == "positional" and kw.value.value in ("?", "*"):
                out["required"] = False
        elif kw.arg == "action" and isinstance(kw.value, ast.Constant) and kw.value.value in ("store_true", "store_false"):
            out["type"] = "boolean"
        elif kw.arg == "help" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            out["description"] = kw.value.value
    return out


def extract_click_commands_from(tree: ast.AST, _path: Path) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not _is_click_command(node):
            continue
        op = _command_to_op(node)
        if op is not None:
            ops.append(op)
    return ops


def _is_click_command(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    # Only @click.command() (or @<group>.command()) produces an executable
    # op. @click.group() declares a parent that has no standalone behaviour
    # of its own — its subcommands are the executable ops.
    for deco in fn.decorator_list:
        name = _decorator_callable_tail(deco)
        if name == "command":
            return True
    return False


def _decorator_callable_tail(deco: ast.expr) -> str | None:
    # @click.command()              → 'command'
    # @click.command(name="foo")    → 'command'
    # @click.option("--flag")       → 'option'
    # @cli.command()                → 'command' (cli is some prior group)
    if isinstance(deco, ast.Call):
        return _attr_tail(deco.func)
    if isinstance(deco, ast.Attribute):
        return deco.attr
    if isinstance(deco, ast.Name):
        return deco.id
    return None


def _attr_tail(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Attribute):
        return expr.attr
    if isinstance(expr, ast.Name):
        return expr.id
    return None


def _command_to_op(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any] | None:
    name = fn.name
    summary = ""
    description = ""
    if fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant):
        doc = fn.body[0].value.value
        if isinstance(doc, str):
            summary = doc.strip().splitlines()[0].strip() if doc.strip() else ""
            description = doc.strip()
    argv: list[dict[str, Any]] = []
    positional_index = 0
    for deco in fn.decorator_list:
        kind = _decorator_callable_tail(deco)
        if kind == "option":
            a = _option_to_arg(deco)
            if a is not None:
                argv.append(a)
        elif kind == "argument":
            a = _argument_to_arg(deco, positional_index)
            if a is not None:
                argv.append(a)
                positional_index += 1
    # If the command has no recognised args, still emit it — the wrapped
    # binary may have an interactive prompt or other side effect.
    return {
        "name": name,
        "summary": summary,
        "description": description,
        "argv": argv,
        "stdout_capture": True,
        "stderr_capture": True,
        "exit_code_ok": [0],
        "timeout_seconds": 300,
    }


def _option_to_arg(deco: ast.expr) -> dict[str, Any] | None:
    if not isinstance(deco, ast.Call):
        return None
    flags: list[str] = []
    json_name: str | None = None
    for a in deco.args:
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            flags.append(a.value)
    long_flag = next((f for f in flags if f.startswith("--")), None) or (flags[0] if flags else None)
    if long_flag is None:
        return None
    json_name = long_flag.lstrip("-").replace("-", "_")
    t = "string"
    default: Any = None
    required = False
    help_str = ""
    for kw in deco.keywords:
        if kw.arg == "type" and isinstance(kw.value, ast.Name):
            t = _python_type_to_json_type(kw.value.id)
        elif kw.arg == "type" and isinstance(kw.value, ast.Attribute):
            t = _python_type_to_json_type(kw.value.attr)
        elif kw.arg == "is_flag" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            t = "boolean"
        elif kw.arg == "default" and isinstance(kw.value, ast.Constant):
            default = kw.value.value
        elif kw.arg == "required" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            required = True
        elif kw.arg == "help" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            help_str = kw.value.value
    out: dict[str, Any] = {
        "kind": "flag",
        "name": json_name,
        "flag": long_flag,
        "type": t,
    }
    if default is not None and not isinstance(default, (list, tuple, dict)):
        out["default"] = default
    if required:
        out["required"] = True
    if help_str:
        out["description"] = help_str
    return out


def _argument_to_arg(deco: ast.expr, position: int) -> dict[str, Any] | None:
    if not isinstance(deco, ast.Call):
        return None
    name = None
    for a in deco.args:
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            name = a.value
            break
    if name is None:
        return None
    t = "string"
    required = True
    default: Any = None
    help_str = ""
    for kw in deco.keywords:
        if kw.arg == "type" and isinstance(kw.value, ast.Name):
            t = _python_type_to_json_type(kw.value.id)
        elif kw.arg == "type" and isinstance(kw.value, ast.Attribute):
            t = _python_type_to_json_type(kw.value.attr)
        elif kw.arg == "default" and isinstance(kw.value, ast.Constant):
            default = kw.value.value
        elif kw.arg == "required" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
            required = False
        elif kw.arg == "help" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            help_str = kw.value.value
    out: dict[str, Any] = {
        "kind": "positional",
        "name": name.replace("-", "_"),
        "position": position,
        "required": required,
        "type": t,
    }
    if default is not None and not isinstance(default, (list, tuple, dict)):
        out["default"] = default
    if help_str:
        out["description"] = help_str
    return out


def _python_type_to_json_type(t: str) -> str:
    return {
        "int": "integer",
        "INT": "integer",
        "Integer": "integer",
        "IntRange": "integer",
        "float": "number",
        "FLOAT": "number",
        "Float": "number",
        "bool": "boolean",
        "BOOL": "boolean",
        "str": "string",
        "STRING": "string",
    }.get(t, "string")


if __name__ == "__main__":
    sys.exit(main())
