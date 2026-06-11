#!/usr/bin/env python3
"""extract-cobra.py — heuristic Go cobra command extractor (Phase 2.5.3).

Emits a yorishiro kami manifest (same JSON shape as extract-click.py) by
regex-scanning Go source files for `&cobra.Command{ Use: "...", Short:
"...", ... }` literals and nearby `.Flags().XxxVar(&var, "name", default,
"help")` calls.

This is intentionally HEURISTIC — full Go AST parsing requires the
`go/ast` toolchain which we don't depend on. The output is "best effort":
- Commands with dynamic Use values (e.g. `Use: fmt.Sprintf(...)`) are skipped.
- Subcommand wiring via cmd.AddCommand is not reconstructed.
- Each command's flags are best-effort matched within +/- 80 lines.

For non-trivial cobra apps, author the kami manifest by hand at
00-contracts/kami/<name>.kami.json and use --from binary-cli instead.

Usage:
    python3 extract-cobra.py <source-path> --kami-id bin:<name> --binary <bin>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# <cmdVar> = &cobra.Command{ … }  or  var <cmdVar> = &cobra.Command{ … }
COMMAND_RE = re.compile(
    r"(?:var\s+)?(?P<var>\w+)\s*=\s*&?cobra\.Command\s*\{(?P<body>[^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
    re.MULTILINE,
)

USE_RE = re.compile(r'\bUse:\s*"(?P<use>[^"]+)"')
SHORT_RE = re.compile(r'\bShort:\s*"(?P<short>[^"]+)"')
LONG_RE = re.compile(r'\bLong:\s*"(?P<long>[^"\\]*(?:\\.[^"\\]*)*)"', re.MULTILINE)

# <cmdVar>.Flags().XxxVar(&var, "flag-name", default, "help text")
# <cmdVar>.PersistentFlags().XxxVarP(&var, "flag-name", "f", default, "help text")
FLAG_RE = re.compile(
    r"(?P<owner>\w+)\.(?:Persistent)?Flags\(\)\.(?P<fn>String|Int|Bool|Int64|Float64|Uint|Uint64)VarP?\("
    r"\s*&\w+\s*,\s*\"(?P<flag>[^\"]+)\"\s*,"
    r"(?:\s*\"(?P<short>[^\"]?)\"\s*,)?"
    r"\s*(?P<default>[^,]+)\s*,"
    r"\s*\"(?P<help>[^\"]*)\""
    r"\s*\)"
)

# <cmdVar>.Args = cobra.ExactArgs(N) / cobra.MinimumNArgs(N) / cobra.MaximumNArgs(N)
ARGS_RE = re.compile(r"(?P<owner>\w+)\.Args\s*=\s*cobra\.(?P<kind>Exact|Minimum|Maximum)N?Args\((?P<n>\d+)\)")

# <cmdVar>.Args = cobra.NoArgs / cobra.ArbitraryArgs / cobra.OnlyValidArgs
ARGS_NO_N_RE = re.compile(r"(?P<owner>\w+)\.Args\s*=\s*cobra\.(?P<kind>NoArgs|ArbitraryArgs|OnlyValidArgs)\b")

# <cmdVar>.Args = cobra.RangeArgs(min, max)
ARGS_RANGE_RE = re.compile(r"(?P<owner>\w+)\.Args\s*=\s*cobra\.RangeArgs\((?P<min>\d+)\s*,\s*(?P<max>\d+)\)")

# Track <parent>.AddCommand(<child>) so persistent flags can be inherited
ADD_CMD_RE = re.compile(r"(?P<parent>\w+)\.AddCommand\(\s*(?P<child>\w+)\s*\)")


GO_TYPE_TO_JSON = {
    "String": "string",
    "Int": "integer",
    "Int64": "integer",
    "Uint": "integer",
    "Uint64": "integer",
    "Float64": "number",
    "Bool": "boolean",
}


def main() -> int:
    ap = argparse.ArgumentParser(prog="extract-cobra")
    ap.add_argument("source", help="Path to a Go file or directory")
    ap.add_argument("--kami-id", required=True)
    ap.add_argument("--binary", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--version-flag", default="--version")
    args = ap.parse_args()

    files = _collect_go_files(Path(args.source).resolve())
    if not files:
        print(f"extract-cobra: no .go files under {args.source}", file=sys.stderr)
        return 1

    ops: list[dict[str, Any]] = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        ops.extend(_extract_from_text(text))

    if not ops:
        print(
            "extract-cobra: no cobra.Command literals matched. Author the kami "
            "manifest by hand and use --from binary-cli instead.",
            file=sys.stderr,
        )
        return 2

    manifest = {
        "kami": {
            "id": args.kami_id,
            "binary": args.binary,
            "description": args.description or f"Auto-extracted (cobra heuristic) from {args.source}",
            "version_flag": args.version_flag,
        },
        "ops": ops,
    }
    json.dump(manifest, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


def _collect_go_files(p: Path) -> list[Path]:
    if p.is_file() and p.suffix == ".go":
        return [p]
    if p.is_dir():
        skip = {".git", "vendor", "node_modules", "testdata", "_archive"}
        out: list[Path] = []
        for sub in p.rglob("*.go"):
            if any(part in skip for part in sub.parts):
                continue
            if sub.name.endswith("_test.go"):
                continue
            out.append(sub)
        return sorted(out)
    return []


def _extract_from_text(text: str) -> list[dict[str, Any]]:
    # 1st pass: collect commands by Go variable name (rootCmd / greetCmd / …).
    commands: dict[str, dict[str, Any]] = {}
    for m in COMMAND_RE.finditer(text):
        var = m.group("var")
        body = m.group("body")
        use_m = USE_RE.search(body)
        if not use_m:
            continue
        use = use_m.group("use").split()[0]
        short = SHORT_RE.search(body)
        long_m = LONG_RE.search(body)
        commands[var] = {
            "name": use,
            "summary": short.group("short") if short else use,
            "description": long_m.group("long") if long_m else (short.group("short") if short else use),
            "flags": [],
            "args": [],
            "is_persistent": [],  # flags scoped Persistent on this var
        }

    # 2nd pass: scope flags to owning variable.
    for m in FLAG_RE.finditer(text):
        owner = m.group("owner")
        if owner not in commands:
            continue
        is_persistent = "PersistentFlags" in m.group(0)
        fn = m.group("fn")
        flag = m.group("flag")
        default_raw = m.group("default").strip()
        help_str = m.group("help")
        json_t = GO_TYPE_TO_JSON.get(fn, "string")
        arg: dict[str, Any] = {
            "kind": "flag",
            "name": flag.replace("-", "_"),
            "flag": f"--{flag}",
            "type": json_t,
        }
        default = _parse_go_default(default_raw, json_t)
        if default is not None:
            arg["default"] = default
        if help_str:
            arg["description"] = help_str
        commands[owner]["flags"].append(arg)
        if is_persistent:
            commands[owner]["is_persistent"].append(arg)

    for m in ARGS_RE.finditer(text):
        owner = m.group("owner")
        if owner not in commands:
            continue
        n = int(m.group("n"))
        kind = m.group("kind")
        for i in range(n):
            commands[owner]["args"].append(
                {
                    "kind": "positional",
                    "name": f"arg{i}",
                    "position": i,
                    "required": kind != "Maximum",
                    "type": "string",
                    "description": f"Positional argument {i} (cobra {kind}NArgs).",
                }
            )

    for m in ARGS_NO_N_RE.finditer(text):
        owner = m.group("owner")
        if owner not in commands:
            continue
        kind = m.group("kind")
        # NoArgs: zero positionals (explicit). ArbitraryArgs / OnlyValidArgs:
        # variable count — emit one optional generic positional so the
        # lexicon at least documents that args exist.
        if kind == "NoArgs":
            commands[owner].setdefault("no_args_explicit", True)
            continue
        commands[owner]["args"].append(
            {
                "kind": "positional",
                "name": "args_rest",
                "position": 0,
                "required": False,
                "type": "string",
                "description": f"Variable positional args (cobra {kind}).",
            }
        )

    for m in ARGS_RANGE_RE.finditer(text):
        owner = m.group("owner")
        if owner not in commands:
            continue
        mn = int(m.group("min"))
        mx = int(m.group("max"))
        for i in range(mx):
            commands[owner]["args"].append(
                {
                    "kind": "positional",
                    "name": f"arg{i}",
                    "position": i,
                    "required": i < mn,
                    "type": "string",
                    "description": f"Positional argument {i} (cobra RangeArgs({mn}, {mx})).",
                }
            )

    # 3rd pass: parent → child PersistentFlags inheritance via AddCommand.
    parents: dict[str, str] = {}  # child -> parent
    for m in ADD_CMD_RE.finditer(text):
        parents[m.group("child")] = m.group("parent")

    def collect_persistent(child: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        cursor = parents.get(child)
        while cursor and cursor in commands:
            out = commands[cursor]["is_persistent"] + out
            cursor = parents.get(cursor)
        return out

    ops: list[dict[str, Any]] = []
    for var, c in commands.items():
        inherited = collect_persistent(var)
        argv = [*inherited, *[f for f in c["flags"] if f not in c["is_persistent"]], *c["args"]]
        # If this is a parent root command, expose its own persistent flags too
        # (so calling `rootcmd --verbose` is documented).
        if var not in parents and c["is_persistent"]:
            argv = [*c["is_persistent"], *[f for f in c["flags"] if f not in c["is_persistent"]], *c["args"]]
        ops.append(
            {
                "name": c["name"],
                "summary": c["summary"],
                "description": c["description"],
                "argv": _renumber_positionals(argv),
                "stdout_capture": True,
                "stderr_capture": True,
                "exit_code_ok": [0],
                "timeout_seconds": 300,
            }
        )
    return ops


def _renumber_positionals(argv: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    pos = 0
    for arg in argv:
        if arg.get("kind") == "positional":
            arg = {**arg, "position": pos}
            pos += 1
        out.append(arg)
    return out


def _parse_go_default(raw: str, json_t: str) -> Any:
    if raw in ('""', "''"):
        return ""
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw == "true":
        return True
    if raw == "false":
        return False
    if json_t in ("integer", "number"):
        try:
            return int(raw) if json_t == "integer" else float(raw)
        except ValueError:
            return None
    return None


if __name__ == "__main__":
    sys.exit(main())
