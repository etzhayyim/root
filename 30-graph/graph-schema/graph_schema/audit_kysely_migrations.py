from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from graph_schema.kysely_to_alembic import ALEMBIC_VERSIONS_DIR, extract, revision_id


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "migrations"


@dataclass
class MigrationAudit:
    total: int
    tests: list[str]
    static_or_empty: list[str]
    auto_convertible: list[str]
    blocked: list[str]
    alembic_generated: list[str]
    missing_alembic: list[str]
    dynamic: list[str]
    errors: dict[str, str]
    dynamic_patterns: dict[str, list[str]]


def function_body(src: str, function_name: str) -> str:
    match = re.search(rf"export\s+async\s+function\s+{function_name}\s*\([^)]*\)[^{{]*\{{", src)
    if not match:
        return ""
    start = match.end()
    depth = 1
    i = start
    while i < len(src):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[start:i]
        i += 1
    raise ValueError(f"unclosed {function_name} function")


def has_dynamic_sql_template(body: str) -> bool:
    pos = 0
    while True:
        start = body.find("sql`", pos)
        if start == -1:
            return False
        i = start + 4
        chars: list[str] = []
        while i < len(body):
            ch = body[i]
            if ch == "\\":
                i += 2
                continue
            if ch == "`":
                break
            chars.append(ch)
            i += 1
        if i >= len(body):
            raise ValueError("unclosed sql template")
        if "${" in "".join(chars):
            return True
        pos = i + 1


def sql_templates(body: str) -> list[str]:
    templates: list[str] = []
    pos = 0
    while True:
        start = body.find("sql`", pos)
        if start == -1:
            return templates
        i = start + 4
        chars: list[str] = []
        while i < len(body):
            ch = body[i]
            if ch == "\\":
                if i + 1 < len(body):
                    chars.append(body[i])
                    chars.append(body[i + 1])
                    i += 2
                    continue
            if ch == "`":
                templates.append("".join(chars))
                pos = i + 1
                break
            chars.append(ch)
            i += 1
        else:
            raise ValueError("unclosed sql template")


def dynamic_pattern(body: str) -> str:
    kinds: set[str] = set()
    for template in sql_templates(body):
        if "${" not in template:
            continue
        for expr in re.findall(r"\$\{([^}]*)\}", template):
            expr = expr.strip()
            if expr.startswith("sql.raw"):
                kinds.add("raw")
            elif expr.startswith("sql.lit"):
                kinds.add("lit")
            elif expr.startswith("sql.join"):
                kinds.add("join")
            elif expr.startswith("sql.val"):
                kinds.add("val")
            elif expr:
                kinds.add("bound-value")
            else:
                kinds.add("empty")
    return "+".join(sorted(kinds)) or "dynamic"


def audit() -> MigrationAudit:
    tests: list[str] = []
    static_or_empty: list[str] = []
    auto_convertible: list[str] = []
    blocked: list[str] = []
    alembic_generated: list[str] = []
    missing_alembic: list[str] = []
    dynamic: list[str] = []
    dynamic_patterns: dict[str, list[str]] = {}
    errors: dict[str, str] = {}

    files = sorted(MIGRATIONS_DIR.glob("*.ts"))
    for path in files:
        if path.name.endswith(".test.ts"):
            tests.append(path.name)
            continue
        try:
            src = path.read_text(encoding="utf-8")
            body = function_body(src, "up") + "\n" + function_body(src, "down")
            if has_dynamic_sql_template(body):
                dynamic.append(path.name)
                dynamic_patterns.setdefault(dynamic_pattern(body), []).append(path.name)
            else:
                static_or_empty.append(path.name)
            try:
                extract(path)
                auto_convertible.append(path.name)
            except Exception:
                blocked.append(path.name)
            if (ALEMBIC_VERSIONS_DIR / f"{revision_id(path.stem)}.py").exists():
                alembic_generated.append(path.name)
            else:
                missing_alembic.append(path.name)
        except Exception as exc:
            errors[path.name] = str(exc)
    return MigrationAudit(
        len(files),
        tests,
        static_or_empty,
        auto_convertible,
        blocked,
        alembic_generated,
        missing_alembic,
        dynamic,
        errors,
        dynamic_patterns,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify legacy Kysely migrations for Alembic conversion.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dynamic", action="store_true", help="Print only dynamic migration filenames.")
    parser.add_argument("--blocked", action="store_true", help="Print migration filenames that still need manual conversion.")
    parser.add_argument("--missing-alembic", action="store_true", help="Print migration filenames without Alembic revisions.")
    parser.add_argument("--convertible", action="store_true", help="Print migration paths that the Alembic converter can handle.")
    parser.add_argument("--patterns", action="store_true", help="Print dynamic migration counts by interpolation pattern.")
    parser.add_argument("--static", action="store_true", help="Print only static/no-op migration paths.")
    args = parser.parse_args()

    result = audit()
    if args.dynamic:
        print("\n".join(result.dynamic))
        return
    if args.blocked:
        print("\n".join(result.blocked))
        return
    if args.missing_alembic:
        print("\n".join(result.missing_alembic))
        return
    if args.convertible:
        print("\n".join(f"migrations/{name}" for name in result.auto_convertible))
        return
    if args.patterns:
        for pattern, files in sorted(result.dynamic_patterns.items(), key=lambda item: (-len(item[1]), item[0])):
            print(f"{pattern}: {len(files)}")
            for name in files[:10]:
                print(f"  {name}")
            if len(files) > 10:
                print(f"  ... {len(files) - 10} more")
        return
    if args.static:
        print("\n".join(f"migrations/{name}" for name in result.static_or_empty))
        return
    if args.json:
        print(json.dumps(asdict(result), indent=2))
        return

    print(f"total: {result.total}")
    print(f"test files: {len(result.tests)}")
    print(f"static/no-op convertible: {len(result.static_or_empty)}")
    print(f"alembic auto-convertible: {len(result.auto_convertible)}")
    print(f"converter manual/static-capture required: {len(result.blocked)}")
    print(f"alembic generated: {len(result.alembic_generated)}")
    print(f"missing alembic revisions: {len(result.missing_alembic)}")
    print(f"dynamic manual: {len(result.dynamic)}")
    print(f"errors: {len(result.errors)}")


if __name__ == "__main__":
    main()
