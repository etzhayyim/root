from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "migrations"
ALEMBIC_VERSIONS_DIR = ROOT / "alembic" / "versions"
SQL_MIGRATIONS_DIR = ROOT / "sql_migrations"


@dataclass(frozen=True)
class ExtractedMigration:
    name: str
    up: list[str]
    down: list[str]


def _find_function_body(src: str, function_name: str) -> str:
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


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _expand_literal_for_loops(body: str) -> str:
    """Expand simple Kysely sql.lit loops into static SQL templates."""

    def replace(match: re.Match[str]) -> str:
        var_name = match.group("var")
        values_src = match.group("values")
        sql_body = match.group("sql")
        values = [item.group("value") for item in re.finditer(r"""["'](?P<value>[^"']*)["']""", values_src)]
        if not values:
            return match.group(0)
        placeholder = "${sql.lit(" + var_name + ")}"
        if placeholder not in sql_body:
            return match.group(0)
        return "\n".join(
            f"await sql`{sql_body.replace(placeholder, _sql_literal(value))}`.execute(db);"
            for value in values
        )

    return re.sub(
        r"for\s*\(\s*const\s+(?P<var>\w+)\s+of\s+\[(?P<values>.*?)\]\s*\)\s*\{\s*"
        r"await\s+sql`(?P<sql>.*?)`\.execute\(db\);\s*"
        r"\}",
        replace,
        body,
        flags=re.DOTALL,
    )


def _extract_sql_templates(body: str) -> list[str]:
    statements: list[str] = []
    i = 0
    while True:
        start = body.find("sql`", i)
        if start == -1:
            return statements
        j = start + 4
        chars: list[str] = []
        while j < len(body):
            ch = body[j]
            if ch == "\\":
                if j + 1 < len(body):
                    chars.append(body[j])
                    chars.append(body[j + 1])
                    j += 2
                    continue
            if ch == "`":
                raw = "".join(chars).strip()
                if "${" in raw:
                    raise ValueError("dynamic sql template cannot be converted automatically")
                if raw:
                    statements.append(raw)
                i = j + 1
                break
            chars.append(ch)
            j += 1
        else:
            raise ValueError("unclosed sql template")


def extract(path: Path) -> ExtractedMigration:
    src = path.read_text(encoding="utf-8")
    return ExtractedMigration(
        name=path.stem,
        up=_extract_sql_templates(_expand_literal_for_loops(_find_function_body(src, "up"))),
        down=_extract_sql_templates(_expand_literal_for_loops(_find_function_body(src, "down"))),
    )


def write_sql_files(migration: ExtractedMigration) -> tuple[Path, Path]:
    SQL_MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    up_path = SQL_MIGRATIONS_DIR / f"{migration.name}.up.sql"
    down_path = SQL_MIGRATIONS_DIR / f"{migration.name}.down.sql"
    up_path.write_text(render_sql_file(migration.up), encoding="utf-8")
    down_path.write_text(render_sql_file(migration.down), encoding="utf-8")
    return up_path, down_path


def render_sql_file(statements: list[str]) -> str:
    if not statements:
        return ""
    return "\n\n".join(statement.rstrip().rstrip(";") + ";" for statement in statements) + "\n"


def revision_id(name: str) -> str:
    cleaned = re.sub(r"[^0-9a-zA-Z_]", "_", name)
    if re.match(r"^\d", cleaned):
        cleaned = f"r_{cleaned}"
    return cleaned[:64]


def write_alembic_file(migration: ExtractedMigration, *, down_revision: str | None) -> Path:
    ALEMBIC_VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    revision = revision_id(migration.name)
    target = ALEMBIC_VERSIONS_DIR / f"{revision}.py"
    content = f'''"""Converted from Kysely migration {migration.name}."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "{revision}"
down_revision = {down_revision!r}
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("{migration.name}.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("{migration.name}.down.sql"))
'''
    target.write_text(content, encoding="utf-8")
    return target


def convert(path: Path, *, write: bool, down_revision: str | None) -> ExtractedMigration:
    migration = extract(path)
    if write:
        write_sql_files(migration)
        write_alembic_file(migration, down_revision=down_revision)
    return migration


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert static Kysely sql`...` migrations to Alembic SQL wrappers.")
    parser.add_argument("migration", nargs="+", help="Migration file path or stem under migrations/")
    parser.add_argument("--write", action="store_true", help="Write sql_migrations/*.sql and alembic/versions/*.py")
    parser.add_argument("--down-revision", help="Alembic down_revision for generated files")
    parser.add_argument(
        "--no-chain",
        action="store_true",
        help="Do not chain multiple generated revisions together.",
    )
    args = parser.parse_args()

    down_revision = args.down_revision
    for item in args.migration:
        path = Path(item)
        if not path.exists():
            path = MIGRATIONS_DIR / item
            if path.suffix != ".ts":
                path = path.with_suffix(".ts")
        migration = convert(path, write=args.write, down_revision=down_revision)
        mode = "wrote" if args.write else "checked"
        print(
            f"{mode} {migration.name}: {len(migration.up)} up statements, "
            f"{len(migration.down)} down statements, down_revision={down_revision!r}"
        )
        if args.write and not args.no_chain:
            down_revision = revision_id(migration.name)


if __name__ == "__main__":
    main()
