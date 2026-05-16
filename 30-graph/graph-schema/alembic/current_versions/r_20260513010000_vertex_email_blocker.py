"""vertex_email_blocker — blocker-aware email workflow schema

Revision ID: r_20260513010000
Revises: r_20260512141000
"""
from alembic import op

revision = "r_20260513010000"
down_revision = "r_20260512141000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(open(
        "30-graph/graph-schema/sql_migrations/20260513010000_vertex_email_blocker.up.sql"
    ).read())


def downgrade() -> None:
    op.execute(open(
        "30-graph/graph-schema/sql_migrations/20260513010000_vertex_email_blocker.down.sql"
    ).read())
