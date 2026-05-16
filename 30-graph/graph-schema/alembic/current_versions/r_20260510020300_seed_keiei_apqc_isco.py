"""seed_keiei_apqc_isco — fill APQC PCF L1 + ISCO-08 columns and edges.

Re-INSERTs into vertex_keiei_role with the 5 new columns from
20260510020200 filled. Also seeds 20 owns_apqc edges (primary +
participates + consults) and 9 isco edges (one per role).

Operating entity = amanomibashira. Vendor = Gftd Japan. ADR 2605101200.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510020300_seed_keiei_apqc_isco"
down_revision = "r_20260510020200_keiei_apqc_isco_binding"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510020300_seed_keiei_apqc_isco.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510020300_seed_keiei_apqc_isco.down.sql"))
