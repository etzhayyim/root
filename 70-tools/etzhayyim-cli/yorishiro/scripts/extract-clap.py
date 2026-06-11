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
            "extract-clap: no Command::new builder calls or #[derive(Parser)] "
            "structs matched. Author the kami manifest by hand and use "
            "--from binary-cli instead.",
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


# ── Derive-style support (Phase 2.5.4.1) ───────────────────────────────────
#
# Matches blocks like:
#   #[derive(Parser, Debug)]
#   #[command(name = "my-cli", about = "...", version = "1.0")]
#   struct Cli {
#       /// Doc comment becomes help text.
#       input: String,
#
#       #[arg(long, short = 'v', help = "Enable verbose")]
#       verbose: bool,
#
#       #[arg(long, default_value = "10")]
#       count: i32,
#   }
#
# And for subcommands:
#   #[derive(Subcommand, Debug)]
#   enum Commands {
#       Run { /* fields */ },
#       Init { /* fields */ },
#   }

DERIVE_STRUCT_RE = re.compile(
    r"#\[\s*derive\s*\(([^)]*)\)\s*\]"
    r"(?P<attrs>(?:\s*#\[\s*command\s*\([^\)]*\)\s*\])*)"
    r"\s*(?:pub\s+)?struct\s+(?P<name>\w+)\s*\{(?P<body>[^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
    re.MULTILINE | re.DOTALL,
)
DERIVE_ENUM_RE = re.compile(
    r"#\[\s*derive\s*\(([^)]*)\)\s*\]"
    r"\s*(?:pub\s+)?enum\s+(?P<name>\w+)\s*\{(?P<body>[^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
    re.MULTILINE | re.DOTALL,
)
CMD_NAME_RE = re.compile(r'name\s*=\s*"(?P<v>[^"]+)"')
CMD_ABOUT_RE = re.compile(r'about\s*=\s*"(?P<v>[^"]+)"')

# Match a single struct field with its preceding attributes / doc comments.
# We split the struct body manually because the regex would otherwise be
# unmanageable.
FIELD_ATTR_RE = re.compile(r"#\[\s*arg\s*\((?P<attrs>[^)]*)\)\s*\]")
DOC_COMMENT_RE = re.compile(r"^\s*///\s?(?P<v>.*)$", re.MULTILINE)

# Rust → JSON type map.
RUST_TYPE_TO_JSON = {
    "String": "string",
    "&str": "string",
    "i8": "integer", "i16": "integer", "i32": "integer", "i64": "integer", "isize": "integer",
    "u8": "integer", "u16": "integer", "u32": "integer", "u64": "integer", "usize": "integer",
    "f32": "number", "f64": "number",
    "bool": "boolean",
}


def _extract_derive_from_text(text: str) -> list[dict[str, Any]]:
    # Build a map of subcommand enum names → variant ops (each variant
    # becomes one op). Then for each Parser struct, emit its own op AND
    # any subcommand variants referenced via `#[command(subcommand)]`.
    enums: dict[str, list[dict[str, Any]]] = {}
    for m in DERIVE_ENUM_RE.finditer(text):
        if "Subcommand" not in m.group(1):
            continue
        enum_name = m.group("name")
        enums[enum_name] = _parse_enum_variants(m.group("body"))

    ops: list[dict[str, Any]] = []
    for m in DERIVE_STRUCT_RE.finditer(text):
        if "Parser" not in m.group(1):
            continue
        cmd_attrs = m.group("attrs") or ""
        name = m.group("name")
        op_name = name
        about = name
        name_m = CMD_NAME_RE.search(cmd_attrs)
        about_m = CMD_ABOUT_RE.search(cmd_attrs)
        if name_m:
            op_name = name_m.group("v")
        if about_m:
            about = about_m.group("v")
        fields_argv, subcmd_enum = _parse_struct_fields(m.group("body"))
        if subcmd_enum and subcmd_enum in enums:
            # Emit one op per enum variant; the parent struct's args
            # become common args prepended to each variant op.
            common_argv = fields_argv
            for variant_name, variant_argv in enums[subcmd_enum]:
                merged: list[dict[str, Any]] = []
                positional_index = 0
                for arg in (*common_argv, *variant_argv):
                    if arg["kind"] == "positional":
                        arg = {**arg, "position": positional_index}
                        positional_index += 1
                    merged.append(arg)
                ops.append({
                    "name": variant_name.lower(),
                    "summary": f"{op_name} {variant_name.lower()}",
                    "description": about,
                    "argv": merged,
                    "stdout_capture": True,
                    "stderr_capture": True,
                    "exit_code_ok": [0],
                    "timeout_seconds": 300,
                })
        else:
            ops.append({
                "name": op_name,
                "summary": about,
                "description": about,
                "argv": fields_argv,
                "stdout_capture": True,
                "stderr_capture": True,
                "exit_code_ok": [0],
                "timeout_seconds": 300,
            })
    return ops


def _parse_struct_fields(body: str) -> tuple[list[dict[str, Any]], str | None]:
    """Parse a Rust struct body. Returns (argv, optional subcommand enum name)."""
    argv: list[dict[str, Any]] = []
    subcmd_enum: str | None = None
    # Split body by commas at top-level (naive — works for well-formed
    # field blocks). Keep doc-comment lines + attribute lines + field
    # together by accumulating until we see the field colon.
    lines = body.split("\n")
    buffer: list[str] = []
    positional_index = 0
    for line in lines:
        stripped = line.rstrip(",").strip()
        if not stripped:
            continue
        buffer.append(line)
        # Heuristic: a complete field ends with a comma or a non-attribute
        # final line containing `name: Type`.
        if (":" in stripped and not stripped.startswith("#") and not stripped.startswith("///")):
            chunk = "\n".join(buffer)
            buffer = []
            parsed = _parse_field(chunk, positional_index)
            if parsed is None:
                continue
            kind, arg, enum_ref = parsed
            if enum_ref:
                subcmd_enum = enum_ref
                continue
            if kind == "positional":
                positional_index += 1
            argv.append(arg)
    return argv, subcmd_enum


def _parse_field(chunk: str, positional_index: int) -> tuple[str, dict[str, Any], str | None] | None:
    # `#[command(subcommand)]` then `field: EnumName,` means the field's
    # type is an enum we previously parsed → return its name as enum_ref.
    if re.search(r"#\[\s*command\s*\(\s*subcommand\s*\)\s*\]", chunk):
        m = re.search(r"(\w+)\s*:\s*(\w+)", chunk)
        if m:
            return ("subcommand", {}, m.group(2))
        return None

    # Doc comments → help text
    doc_lines = [d.group("v") for d in DOC_COMMENT_RE.finditer(chunk)]
    doc = " ".join(s.strip() for s in doc_lines if s.strip())

    arg_attr = FIELD_ATTR_RE.search(chunk)
    field_m = re.search(r"(\w+)\s*:\s*(Option<\s*)?(\w+)", chunk)
    if not field_m:
        return None
    field_name = field_m.group(1)
    is_option = field_m.group(2) is not None
    raw_type = field_m.group(3)
    json_type = RUST_TYPE_TO_JSON.get(raw_type, "string")

    long_flag = None
    short_flag = None
    default = None
    help_str = doc
    action = None
    required_attr = None

    if arg_attr:
        attrs = arg_attr.group("attrs")
        # `long` → flag, derived from field name
        if re.search(r"\blong\b", attrs):
            long_flag = field_name.replace("_", "-")
        long_named = re.search(r'long\s*=\s*"(?P<v>[^"]+)"', attrs)
        if long_named:
            long_flag = long_named.group("v")
        short_simple = re.search(r"\bshort\b(?!\s*=)", attrs)
        short_named = re.search(r"short\s*=\s*'(?P<v>.)'", attrs)
        if short_simple and not short_named:
            short_flag = field_name[0]
        if short_named:
            short_flag = short_named.group("v")
        default_m = re.search(r'default_value\s*=\s*"(?P<v>[^"]*)"', attrs)
        if default_m:
            default = default_m.group("v")
        help_m = re.search(r'help\s*=\s*"(?P<v>[^"]*)"', attrs)
        if help_m:
            help_str = help_m.group("v") or help_str
        action_m = re.search(r"action\s*=\s*ArgAction::(?P<v>\w+)", attrs)
        if action_m:
            action = action_m.group("v")
        required_m = re.search(r"required\s*=\s*(true|false)", attrs)
        if required_m:
            required_attr = required_m.group(1) == "true"

    # Decide kind. Heuristic: bool fields without long/short are flags
    # (clap conventionally treats them as `--field`); other no-attribute
    # fields are positionals.
    if action in ("SetTrue", "SetFalse"):
        json_type = "boolean"
        long_flag = long_flag or field_name.replace("_", "-")
    is_flag = bool(long_flag or short_flag) or json_type == "boolean"

    if is_flag:
        flag = f"--{long_flag}" if long_flag else f"-{short_flag}"
        arg: dict[str, Any] = {
            "kind": "flag",
            "name": field_name,
            "flag": flag,
            "type": json_type,
        }
        if default is not None:
            arg["default"] = _coerce(default, json_type)
        if help_str:
            arg["description"] = help_str
        if required_attr is True:
            arg["required"] = True
        return ("flag", arg, None)

    arg = {
        "kind": "positional",
        "name": field_name,
        "position": positional_index,
        "required": not is_option and required_attr is not False,
        "type": json_type,
    }
    if default is not None:
        arg["default"] = _coerce(default, json_type)
    if help_str:
        arg["description"] = help_str
    return ("positional", arg, None)


def _coerce(val: str, json_type: str) -> Any:
    if json_type == "integer":
        try:
            return int(val)
        except ValueError:
            return val
    if json_type == "number":
        try:
            return float(val)
        except ValueError:
            return val
    if json_type == "boolean":
        return val.lower() == "true"
    return val


def _parse_enum_variants(body: str) -> list[tuple[str, list[dict[str, Any]]]]:
    """Walk a Subcommand enum's body. Returns [(variant_name, argv), …]."""
    # Strip doc comment lines + line comments so word-tokens inside them
    # don't get mistaken for variants.
    cleaned = re.sub(r"^\s*///.*$", "", body, flags=re.MULTILINE)
    cleaned = re.sub(r"//[^\n]*", "", cleaned)

    out: list[tuple[str, list[dict[str, Any]]]] = []
    # A real variant either ends with a brace block `{...}` or with a
    # comma (or end-of-input). Require one of those terminators so
    # incidental word tokens (e.g. inside an attribute body) don't match.
    block_re = re.compile(
        r"(?P<name>[A-Z]\w*)\s*(?:\{(?P<fields>[^{}]*)\}|,|$)",
        re.MULTILINE,
    )
    seen: set[str] = set()
    for m in block_re.finditer(cleaned):
        name = m.group("name")
        if name in seen:
            continue
        seen.add(name)
        fields = m.group("fields") or ""
        argv: list[dict[str, Any]] = []
        if fields.strip():
            argv, _ = _parse_struct_fields(fields)
        out.append((name, argv))
    return out


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
    # Phase 2.5.4.1 — also handle `#[derive(Parser)]` / `#[derive(Subcommand)]`
    # plus their `#[arg(...)]` / `#[command(...)]` attributes.
    derive_ops = _extract_derive_from_text(text)

    ops: list[dict[str, Any]] = list(derive_ops)
    # Builder-style: Treat Command::new / Subcommand::new identically.
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
