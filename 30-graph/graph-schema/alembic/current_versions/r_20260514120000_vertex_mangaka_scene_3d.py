"""vertex_mangaka_scene_3d — ADR-2605141200 mangaka 3D scene composition schema

Revision ID: r_20260514120000
Revises: r_20260513010000
"""
from alembic import op

revision = "r_20260514120000"
down_revision = "r_20260513010000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(open(
        "30-graph/graph-schema/sql_migrations/20260514120000_vertex_mangaka_scene_3d.up.sql"
    ).read())


def downgrade() -> None:
    op.execute(open(
        "30-graph/graph-schema/sql_migrations/20260514120000_vertex_mangaka_scene_3d.down.sql"
    ).read())
