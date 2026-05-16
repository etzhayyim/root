"""Converted from Kysely migration 20260416320000_collection_mappings_tentai_i18n_asfis_chizai_maps."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260416320000_collection_mappings_tentai_i18n_asfis_chizai_ma"
down_revision = 'r_20260416310000_world_total_calibration_tunnel_handotai_tentai'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260416320000_collection_mappings_tentai_i18n_asfis_chizai_maps.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260416320000_collection_mappings_tentai_i18n_asfis_chizai_maps.down.sql"))
