"""vertex_hubspot — HubSpot CRM ingest schema (8 objects + sync cursor).

Adds T2 domain tables for HubSpot CRM v3 object types (contact / company /
deal / ticket / owner / engagement / line_item / product) plus a per-object
sync cursor for incremental polling.

Driven by 60-apps/etzhayyim-project-hubspot-hb5p0t1n ingest worker
(R/PT15M timer → /crm/v3/objects/{type} paginated, lastmodifieddate filter).

ADRs: 0036 (Hyperdrive direct domain write), 0095 (RLS canonical columns),
      2604251830 (Shannon-Optimal 8-Layer).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510010000_vertex_hubspot"
down_revision = "r_20260510000000_vertex_kafun_langgraph"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510010000_vertex_hubspot.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510010000_vertex_hubspot.down.sql"))
