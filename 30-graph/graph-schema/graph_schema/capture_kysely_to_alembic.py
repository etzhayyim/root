from __future__ import annotations

import argparse
import json
import pprint
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from graph_schema.kysely_to_alembic import ALEMBIC_VERSIONS_DIR, MIGRATIONS_DIR, revision_id


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_SCRIPT = ROOT / "scripts" / "capture-kysely-migration.mjs"
REPO_ROOT = ROOT.parents[1]


@dataclass(frozen=True)
class CapturedMigration:
    name: str
    up: list[dict[str, Any]]
    down: list[dict[str, Any]]


def capture(path: Path) -> CapturedMigration:
    parent_contracts = REPO_ROOT.parent / "00-contracts"
    with tempfile.TemporaryDirectory(prefix="graph-schema-capture-"):
        created_link = False
        if not parent_contracts.exists() and (REPO_ROOT / "00-contracts").exists():
            parent_contracts.symlink_to(REPO_ROOT / "00-contracts", target_is_directory=True)
            created_link = True
        try:
            proc = subprocess.run(
                ["node", "--loader=ts-node/esm", str(CAPTURE_SCRIPT), str(path)],
                cwd=ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
            )
        finally:
            if created_link:
                parent_contracts.unlink()
    payload = json.loads(proc.stdout)
    return CapturedMigration(payload["name"], payload["up"], payload["down"])


def render_alembic_file(migration: CapturedMigration, *, down_revision: str | None) -> str:
    revision = revision_id(migration.name)
    up = pprint.pformat(migration.up, width=100, sort_dicts=False)
    down = pprint.pformat(migration.down, width=100, sort_dicts=False)
    return f'''"""Captured from Kysely migration {migration.name}."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "{revision}"
down_revision = {down_revision!r}
branch_labels = None
depends_on = None

UP = {up}

DOWN = {down}


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
'''


def write_alembic_file(migration: CapturedMigration, *, down_revision: str | None) -> Path:
    ALEMBIC_VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    target = ALEMBIC_VERSIONS_DIR / f"{revision_id(migration.name)}.py"
    target.write_text(render_alembic_file(migration, down_revision=down_revision), encoding="utf-8")
    return target


def resolve_migration(item: str) -> Path:
    path = Path(item)
    if path.exists():
        return path
    path = MIGRATIONS_DIR / item
    if path.suffix != ".ts":
        path = path.with_suffix(".ts")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture Kysely migrations into Alembic Python bind statements.")
    parser.add_argument("migration", nargs="+", help="Migration file path or stem under migrations/")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--down-revision")
    parser.add_argument("--no-chain", action="store_true")
    args = parser.parse_args()

    down_revision = args.down_revision
    for item in args.migration:
        path = resolve_migration(item)
        migration = capture(path)
        if args.write:
            write_alembic_file(migration, down_revision=down_revision)
        mode = "wrote" if args.write else "checked"
        print(
            f"{mode} {migration.name}: {len(migration.up)} up statements, "
            f"{len(migration.down)} down statements, down_revision={down_revision!r}"
        )
        if args.write and not args.no_chain:
            down_revision = revision_id(migration.name)


if __name__ == "__main__":
    main()
