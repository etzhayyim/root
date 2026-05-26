"""vertex_telecom_local_mesh_submarine.

Adds graph coverage for local wireless mesh and submarine cable inventory:
Bluetooth/BLE devices and mesh nodes, WLAN 802.11s-style mesh links, and
submarine cable systems with landing stations, repeaters, route segments, and
repair events.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260524190000_vertex_telecom_local_mesh_submarine"
down_revision = "r_20260515170000_mv_ameno_credits_balance"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260524190000_vertex_telecom_local_mesh_submarine.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260524190000_vertex_telecom_local_mesh_submarine.down.sql"),
    )
