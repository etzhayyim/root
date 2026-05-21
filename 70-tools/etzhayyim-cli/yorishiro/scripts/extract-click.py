#!/usr/bin/env python3
"""extract-click.py — Python AST walker that emits a yorishiro kami manifest
from a Click-based source repo.

Usage:
    python3 extract-click.py <source-path> --kami-id bin:<name> --binary <bin>
                             [--module <pkg.cli>] [--entry <cli_attr>]

Output: a kami manifest JSON (same shape as 00-contracts/kami/*.kami.json,
consumed by the binary-cli generator path) on stdout.

What it looks for:
  - functions decorated with @click.command(), @<group>.command(),
    or @click.group()
  - each function's @click.option(...) and @click.argument(...) decorators
  - option flag literals (--flag), types (int/bool/str/float), defaults,
    required-ness, help strings

What it skips (Phase 2.5 v0):
  - dynamic decorators (anything not statically introspectable)
  - argparse / cobra / clap (Phase 2.5.1+)
  - multi-value / nargs / callback options (degraded to plain string)

The output is fed into the same binary-cli emitter (since the wrapped
binary, once the source repo is installed, is just a normal executable).
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
        ops.extend(extract_commands_from(tree, path))

    if not ops:
        print(
            f"extract-click: no @click.command / @click.group functions found under {src}. "
            "Phase 2.5 v0 supports Click only; argparse / cobra / clap land in 2.5.1.",
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


def extract_commands_from(tree: ast.AST, _path: Path) -> list[dict[str, Any]]:
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
