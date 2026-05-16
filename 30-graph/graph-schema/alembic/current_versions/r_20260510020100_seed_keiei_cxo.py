"""seed_keiei_cxo — seed 9 ideal/virtual CXO roles + agents + profiles + edges.

Drop-then-insert (re-runnable). Mirror of `pymagatama.keiei.roles.ROLES`
SSoT. Edit one ⇒ edit the other.

Operating entity = amanomibashira. Vendor = Gftd Japan. ADR 2605101200.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510020100_seed_keiei_cxo"
down_revision = "r_20260510020000_vertex_keiei_cxo"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510020100_seed_keiei_cxo.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510020100_seed_keiei_cxo.down.sql"))
