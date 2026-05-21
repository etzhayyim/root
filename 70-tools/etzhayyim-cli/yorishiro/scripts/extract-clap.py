#!/usr/bin/env python3
"""extract-clap.py — heuristic Rust clap command extractor (Phase 2.5.4).

Builder-style clap only — derive-style (#[derive(Parser)]) is out of scope
for v0. Emits a yorishiro kami manifest (same JSON shape as extract-cobra
+ extract-click).

Looks for:
  - Command::new("name") chains
  - .about("...") / .long_about("...")
  - .arg(Arg::new("name").short('s').long("long").value_parser(...) ...)

For non-trivial clap apps, author the kami manifest by hand and use
--from binary-cli instead.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# Command::new("name")
COMMAND_RE = re.compile(r'Command::new\(\s*"(?P<name>[^"]+)"\s*\)')
# Subcommand::new("name") — clap derive emits these
SUBCMD_RE = re.compile(r'Subcommand::new\(\s*"(?P<name>[^"]+)"\s*\)')

# .about("…") within the same call chain
ABOUT_RE = re.compile(r'\.about\(\s*"(?P<about>[^"]*)"\s*\)')
LONG_ABOUT_RE = re.compile(r'\.long_about\(\s*"(?P<long>[^"]*)"\s*\)')

# Arg::new("flag") + chained modifiers in builder style
# We greedily match the chain up to a closing `)` followed by a sibling
# `.arg(` / `;` / `.subcommand(` etc.
ARG_RE = re.compile(
    r'Arg::new\(\s*"(?P<name>[^"]+)"\s*\)(?P<chain>(?:\s*\.[A-Za-z_]+\([^()]*(?:\([^()]*\))?[^()]*\))*)',
    re.MULTILINE,
)


def main() -> int:
    ap = argparse.ArgumentParser(prog="extract-clap")
    ap.add_argument("source")
    ap.add_argument("--kami-id", required=True)
    ap.add_argument("--binary", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--version-flag", default="--version")
    args = ap.parse_args()

    files = _collect_rs_files(Path(args.source).resolve())
    if not files:
        print(f"extract-clap: no .rs files under {args.source}", file=sys.stderr)
        return 1

    ops: list[dict[str, Any]] = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        ops.extend(_extract_from_text(text))

    if not ops:
        print(
            "extract-clap: no Command::new builder calls matched. Derive-style "
            "(#[derive(Parser)]) is not supported in v0 — author the kami "
            "manifest by hand and use --from binary-cli instead.",
            file=sys.stderr,
        )
        return 2

    manifest = {
        "kami": {
            "id": args.kami_id,
            "binary": args.binary,
            "description": args.description or f"Auto-extracted (clap heuristic) from {args.source}",
            "version_flag": args.version_flag,
        },
        "ops": ops,
    }
    json.dump(manifest, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


def _collect_rs_files(p: Path) -> list[Path]:
    if p.is_file() and p.suffix == ".rs":
        return [p]
    if p.is_dir():
        skip = {".git", "target", "node_modules", "tests", "_archive"}
        out: list[Path] = []
        for sub in p.rglob("*.rs"):
            if any(part in skip for part in sub.parts):
                continue
            out.append(sub)
        return sorted(out)
    return []


def _extract_from_text(text: str) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    # Treat Command::new / Subcommand::new identically.
    matches = list(COMMAND_RE.finditer(text)) + list(SUBCMD_RE.finditer(text))
    if not matches:
        return ops
    matches.sort(key=lambda m: m.start())
    # Use the surrounding ~3000 chars of each Command::new() as its scope.
    for m in matches:
        name = m.group("name")
        start = m.end()
        end = min(len(text), m.end() + 3000)
        scope = text[start:end]
        about = ABOUT_RE.search(scope)
        long_about = LONG_ABOUT_RE.search(scope)
        summary = about.group("about") if about else name
        description = long_about.group("long") if long_about else summary

        argv = _scan_args(scope)
        ops.append(
            {
                "name": name,
                "summary": summary,
                "description": description,
                "argv": argv,
                "stdout_capture": True,
                "stderr_capture": True,
                "exit_code_ok": [0],
                "timeout_seconds": 300,
            }
        )
    return ops


def _scan_args(scope: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    positional_index = 0
    for m in ARG_RE.finditer(scope):
        name = m.group("name")
        chain = m.group("chain") or ""
        long_flag = None
        short_flag = None
        default = None
        help_str = ""
        value_type = "string"
        action = None
        for cm in re.finditer(r'\.long\(\s*"(?P<v>[^"]+)"\s*\)', chain):
            long_flag = cm.group("v")
        for cm in re.finditer(r"\.short\(\s*'(?P<v>.)'\s*\)", chain):
            short_flag = cm.group("v")
        for cm in re.finditer(r'\.default_value\(\s*"(?P<v>[^"]*)"\s*\)', chain):
            default = cm.group("v")
        for cm in re.finditer(r'\.(?:about|help)\(\s*"(?P<v>[^"]*)"\s*\)', chain):
            help_str = cm.group("v")
        for cm in re.finditer(r"\.value_parser\(\s*value_parser!\(\s*(?P<v>\w+)\s*\)", chain):
            t = cm.group("v")
            value_type = {"i32": "integer", "i64": "integer", "u32": "integer", "u64": "integer", "f32": "number", "f64": "number", "bool": "boolean", "String": "string"}.get(t, "string")
        if ".action(ArgAction::SetTrue)" in chain or ".action(ArgAction::Count)" in chain:
            value_type = "boolean"
            action = "store_true"
        is_positional = long_flag is None and short_flag is None
        if is_positional:
            arg: dict[str, Any] = {
                "kind": "positional",
                "name": name.replace("-", "_"),
                "position": positional_index,
                "required": ".required(false)" not in chain,
                "type": value_type,
            }
            positional_index += 1
        else:
            flag = f"--{long_flag}" if long_flag else f"-{short_flag}"
            arg = {
                "kind": "flag",
                "name": name.replace("-", "_"),
                "flag": flag,
                "type": value_type,
            }
            if ".required(true)" in chain:
                arg["required"] = True
        if default is not None:
            if value_type == "integer":
                try:
                    arg["default"] = int(default)
                except ValueError:
                    arg["default"] = default
            elif value_type == "number":
                try:
                    arg["default"] = float(default)
                except ValueError:
                    arg["default"] = default
            elif value_type == "boolean":
                arg["default"] = default.lower() == "true"
            else:
                arg["default"] = default
        if help_str:
            arg["description"] = help_str
        out.append(arg)
    return out


if __name__ == "__main__":
    sys.exit(main())
