"""kafun real-world outreach pipeline + Japanese stakeholder seed.

Adds:
  * Satellite imagery / canopy detection (vertex_kafun_satellite_tile,
    vertex_kafun_canopy_segment + edge_kafun_canopy_in_tile).
  * Cadastral / landowner (vertex_kafun_cadastral_parcel, vertex_kafun_landowner
    + edge_kafun_canopy_in_parcel, edge_kafun_parcel_owned_by).
  * Stakeholder graph (vertex_kafun_stakeholder + edge_kafun_landowner_member_of,
    edge_kafun_outreach_sent_to).
  * MVs: mv_kafun_unattributed_canopy / mv_kafun_owner_outreach_funnel /
    mv_kafun_stakeholder_coverage / mv_kafun_canopy_pref_year.
  * Seed: ~30 Japanese stakeholders + 5-node sub-DAG extension (L0-1a..d, L1-0).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510020000_kafun_satellite_landowner_stakeholder"
down_revision = "r_20260510010000_vertex_agent_topo_and_kafun_concrete"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510020000_kafun_satellite_landowner_stakeholder.up.sql"))
    execute_sql_text(op.get_bind(), _read("20260510020100_kafun_seed_stakeholders_and_subdag.up.sql"))


def downgrade() -> None:
    raise NotImplementedError("kafun outreach schema is forward-only")
