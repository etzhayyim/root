"""vertex_inbox_triage — inbox triage classification results (pregel 常駐化)

Revision ID: r_20260513200000
Revises: r_20260513010000
"""
from alembic import op

revision = "r_20260513200000"
down_revision = "r_20260513010000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(open(
        "30-graph/graph-schema/sql_migrations/20260513200000_vertex_inbox_triage.up.sql"
    ).read())


def downgrade() -> None:
    op.execute(open(
        "30-graph/graph-schema/sql_migrations/20260513200000_vertex_inbox_triage.down.sql"
    ).read())
