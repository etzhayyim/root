"""Alembic baseline for SQLAlchemy-managed graph schema migrations."""

from __future__ import annotations

from alembic import op


revision = "202605070000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET RW_IMPLICIT_FLUSH = true")


def downgrade() -> None:
    op.execute("SET RW_IMPLICIT_FLUSH = true")
