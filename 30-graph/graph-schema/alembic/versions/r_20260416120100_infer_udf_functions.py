"""No-op replacement for dead Kysely migration 20260416120100_infer_udf_functions."""

from __future__ import annotations

from alembic import op


revision = "r_20260416120100_infer_udf_functions"
down_revision = "r_20260416120000_infer_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().exec_driver_sql("SET RW_IMPLICIT_FLUSH = true")


def downgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql("SET RW_IMPLICIT_FLUSH = true")
    conn.exec_driver_sql("DROP FUNCTION IF EXISTS gmm_fit")
    conn.exec_driver_sql("DROP FUNCTION IF EXISTS segment_hash")
    conn.exec_driver_sql("DROP FUNCTION IF EXISTS posterior_update")
    conn.exec_driver_sql("DROP FUNCTION IF EXISTS cosine_similarity")
    conn.exec_driver_sql("FLUSH")
